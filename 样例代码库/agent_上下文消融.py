"""Agent 实验 ① · 本地 Agent 循环 + 上下文消融（零成本版）

对应《深入理解 AI Agent》（李博杰）第 1 章核心公式：

        Agent = LLM + 上下文 + 工具

配套：交互演示/Agent核心公式-上下文消融.html
参考：_ref/ai-agent-book-README.md（书的主页）、_ref/LEARNING-zh.md（书的学习建议）

用法：python 样例代码库/agent_上下文消融.py
     （先确保 Ollama 在跑：ollama list 能看到 qwen2.5:3b）

────────────────────────────────────────────────────────────
它做的事（把书里的"消融实验"缩到最小）

书里实验 1-1 的做法是：跑一个真 Agent，然后**故意抽掉上下文的某个组件**，
看任务成功率怎么掉。掉得越狠，说明那个组件越关键。

这里用你本机就能跑的 qwen2.5:3b 复刻同一件事，抽掉 4 个组件各跑一遍：
    ① 完整           —— 基准线
    ② 砍掉工具定义   —— 模型根本不知道有工具可用
    ③ 砍掉工具结果   —— 工具调了，但结果没回灌给模型
    ④ 砍掉系统提示   —— 模型不知道自己的身份和输出要求
    ⑤ 砍掉历史       —— 多步任务里"上一句"丢了

四道题的答案都藏在工具背后（模型不可能靠记忆答对），所以**判分是代码做的，
不靠感觉**。前 3 道单步（工具返回即答案），第 4 道两步（要先查两次再作差）。

⚠️ 已经踩到的真坑（留着别删）：
   qwen2.5:3b 在多工具多轮场景下会**算对却报错**——实测它调 `计算(47+23)`
   拿到返回 70，然后开口写「一共50人报名」。换标准 OpenAI 端点 + 正确
   tool_call_id 复现结果完全一致 → 是模型缺陷，不是消息格式问题。
   这正是书里第 1 章那句话的活体演示：能跑的 Demo 与可靠产品的差距在 Harness。
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request

# Windows 控制台默认 GBK，中文会炸；强制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OLLAMA = "http://127.0.0.1:11434"
MODEL = "qwen2.5:3b"
NUM_CTX = 4096         # ★ 关键：Ollama 默认开 32768 上下文，KV cache 白吃一大片显存。
                       #   实测本机 RTX 5060 Laptop 8G 里只有约 2.7G 空闲，
                       #   模型要 3.36G → 顶着跑几十次后 runner 直接崩
                       #   （"model runner has unexpectedly stopped"）。压到 4096 就稳了。
MAX_STEPS = 6          # 硬上限：循环绝不能没有终点
CALL_TIMEOUT = 90      # 单次模型调用
CALL_RETRY = 3         # 单次调用失败重试次数（Ollama 偶发 500 / runner 重启）
TOTAL_BUDGET = 900     # 整个脚本的墙钟预算（秒），超了就停
REPEATS = 5            # 每个消融组每题重复几次

# 为什么要重复：首轮只跑 1 遍时，「完整」组一次 4/4、一次 2/4（同样温度=0）。
# 单次运行的差异会盖过真实的效应 —— 这是书里第 7 章「评估」的核心教训：
# 没有重复和统计，你分不清「设计带来的提升」和「随机波动」。


# ─────────────────────── 藏在工具背后的数据 ───────────────────────
# 模型不可能"记得"这些数字 —— 必须调工具才拿得到。
#
# ⚠️ 为什么围棋是 31 而不是最初的 23（这是实测逼出来的修正）：
#    「砍掉工具结果」组里模型 5/5 次都答 23 —— 连真值 61 的摄影题也答 23。
#    说明 **23 是它没有数据时的默认猜测**，而围棋真值恰好等于 23，
#    那一格就成了「蒙对」，不是有效信号 → 等于这道题在该组失效。
#    换掉它，四道题的答案才都"猜不到"。
ENROLL = {"街舞": 47, "围棋": 31, "摄影": 61, "烘焙": 38, "篮球": 55}


def tool_查询报名(course: str) -> str:
    if course in ENROLL:
        return f"{course} 当前报名 {ENROLL[course]} 人"
    return f"没有找到课程「{course}」"


def tool_计算(expression: str) -> str:
    """只允许数字和四则运算，防止 eval 变任意代码执行。"""
    if not re.fullmatch(r"[0-9+\-*/(). ]+", expression or ""):
        return f"表达式「{expression}」含非法字符，只支持数字和 + - * / ( )"
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))  # noqa: S307
    except Exception as e:
        return f"算不出来：{e}"


TOOLS = {                          # 名字 → 函数
    "查询报名": tool_查询报名,
    "计算": tool_计算,
}

# 工具定义（要喂给模型的那份"说明书"）
TOOL_SPEC = [
    {"type": "function", "function": {
        "name": "查询报名",
        "description": "查询某门选修课当前有多少人报名",
        "parameters": {"type": "object", "properties": {
            "course": {"type": "string", "description": "课程名，如 街舞"}},
            "required": ["course"]}}},
    {"type": "function", "function": {
        "name": "计算",
        "description": "做四则运算，返回结果",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string", "description": "如 47+23"}},
            "required": ["expression"]}}},
]

# ⚠️ 系统提示改过一版（实测逼出来的）：
#    原来多写了一句「算数也请用计算工具」，结果基准线在两步题上 0/5 ——
#    3B 模型被这句推进了它驾驭不了的路径（调 计算 时传「被减数-减数」这种中文表达式，
#    连续失败），而**砍掉整段系统提示**后同一道题 5/5 全对（它自己心算 61-55=6）。
#    一句"贴心"的提示词反而害了它 —— 这正是书里 Harness「约束」那一环要讨论的事。
SYSTEM = (
    "你是一个办事的助手。需要数据时必须调用工具，不要凭空回答。"
    "得出结果后，用一句话回答，并把最终数字写出来。"
)


def _unwrap_args(args, accepted):
    """把模型包错的参数拆出来。

    实测 qwen2.5:3b 至少会吐三种形状（同一份工具定义、同一个模型，反复跑都会变）：
        {"course": "摄影"}                              ← 正常
        {"object": None, "arguments": {"course": "摄影"}} ← 信封 + 垃圾键
        {"object": {"course": "摄影"}}                    ← 键名换成了 object
    所以**不能猜键名**：只要本层没出现我要的参数，就往里层递归找，
    找到哪个嵌套字典里装着它，就用哪个。
    """
    if not isinstance(args, dict):
        return {}
    if accepted & set(args):                 # 本层就有需要的参数 → 用它
        return args
    for v in args.values():                  # 否则往里层找
        if isinstance(v, dict):
            inner = _unwrap_args(v, accepted)
            if accepted & set(inner):
                return inner
    return args


def call_tool(name, args):
    """调用工具。**永远不要因为参数格式怪就崩** —— 把错误当工具结果回灌给模型，
    让它自己改（这正是真 Agent 的做法，也是书里 Harness「纠正」那一环）。"""
    import inspect

    fn_impl = TOOLS.get(name)
    if fn_impl is None:
        return f"没有这个工具：{name}"

    accepted = set(inspect.signature(fn_impl).parameters)
    args = _unwrap_args(args if isinstance(args, dict) else {}, accepted)
    unknown = set(args) - accepted
    args = {k: v for k, v in args.items() if k in accepted}
    if not args and accepted:
        return (f"工具 {name} 需要参数 {sorted(accepted)}，你传来的键不认识"
                f"（收到的是 {sorted(unknown) or '空'}）。请重新调用并带上正确参数。")
    try:
        return fn_impl(**args)
    except Exception as e:
        return f"工具 {name} 执行出错：{type(e).__name__}: {e}"


# ─────────────────────── 四道题 + 客观判分 ───────────────────────
# 前 3 道单步：工具的返回就是答案，模型只需如实转述。
# 第 4 道两步：要先查两次再作差 —— 专门用来暴露"多步收口"问题。
TASKS = [
    {"name": "单查·摄影", "q": "选修课「摄影」现在有多少人报名？只回答数字。", "want": "61"},
    {"name": "单查·围棋", "q": "选修课「围棋」现在有多少人报名？只回答数字。", "want": "31"},
    {"name": "单查·烘焙", "q": "选修课「烘焙」现在有多少人报名？只回答数字。", "want": "38"},
    {"name": "两步·求差", "q": "「摄影」比「篮球」多多少人报名？", "want": "6"},
]


def judge(answer: str, want: str) -> bool:
    """判分：答案里出现正确数字即算过（容忍模型多说话）。
    用数字边界匹配，避免 61 里的 6 被误判成对。"""
    return re.search(rf"(?<![\d.]){re.escape(want)}(?![\d.])", answer or "") is not None


# ─────────────────────── Ollama 调用 ───────────────────────
def chat(messages, tools):
    """调一次模型。带重试 —— Ollama 的 runner 偶发 500（显存吃紧时会重启），
    一次抖动不该让整个实验报废。"""
    body = {"model": MODEL, "messages": messages, "stream": False,
            "options": {"temperature": 0, "num_ctx": NUM_CTX}}
    if tools:
        body["tools"] = tools
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    last_err = None
    for attempt in range(CALL_RETRY):
        req = urllib.request.Request(f"{OLLAMA}/api/chat", data=data,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=CALL_TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # ★ HTTPError 是 URLError 的子类：不先单独接住，就会被误报成"连不上"
            last_err = f"HTTP {e.code} {e.reason}"
            try:
                detail = json.loads(e.read().decode("utf-8")).get("error", "")
                if detail:
                    last_err += f" —— {detail}"
            except Exception:
                pass
        except urllib.error.URLError as e:
            last_err = f"连接失败 {e.reason}"
        time.sleep(2 * (attempt + 1))          # 退避，给 runner 喘口气
    raise SystemExit(
        f"连续 {CALL_RETRY} 次调用失败：{last_err}\n"
        f"  排查：① `ollama list` 看服务在不在；② `ollama ps` 看模型有没有加载；"
        f"③ 显存不够就关掉占显存的程序再试。"
    )


def run_one(task, mode, trace, t0):
    """跑一道题。mode 决定抽掉哪个上下文组件。返回 (是否答对, 工具调用次数, 最终回答)。"""
    msgs = []
    if mode != "砍掉系统提示":
        msgs.append({"role": "system", "content": SYSTEM})
    msgs.append({"role": "user", "content": task["q"]})

    tools_arg = None if mode == "砍掉工具定义" else TOOL_SPEC
    answer = ""

    for _step in range(MAX_STEPS):
        # 预算检查放进步内：否则单个任务最坏能吃掉 MAX_STEPS × CALL_TIMEOUT
        if time.time() - t0 > TOTAL_BUDGET:
            return False, len(trace), answer or "<超预算中断>"

        resp = chat(msgs, tools_arg)
        msg = resp.get("message", {}) or {}
        calls = msg.get("tool_calls") or []
        answer = (msg.get("content") or "").strip() or answer

        if not calls:
            break                                   # 模型不再要工具 → 收工

        msgs.append({"role": "assistant", "content": msg.get("content") or "",
                     "tool_calls": calls})

        for c in calls:
            fn = (c.get("function") or {})
            name, args = fn.get("name"), (fn.get("arguments") or {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            result = call_tool(name, args)
            trace.append(f"{name}({args}) → {result}")

            # ★ 消融点：砍掉工具结果 = 回灌空字符串，模型看不到数据
            content = "" if mode == "砍掉工具结果" else result
            msgs.append({"role": "tool", "content": content,
                         "tool_name": name or ""})

        # ★ 消融点：砍掉历史 = 每步只留 system + 最初的问题 + 最新一条
        if mode == "砍掉历史":
            keep = [m for m in msgs if m["role"] == "system"]
            keep.append({"role": "user", "content": task["q"]})
            keep.append(msgs[-1])
            msgs = keep
    else:
        # 步数用尽还没收口：补一次"只许回答、不许调工具"的机会。
        # 不补这一下会**冤枉模型**（实测：工具已经算出 70，判分却读到它上一轮的胡话）。
        # 这一步对所有消融组一视同仁（都不给 tools），不污染对照。
        if time.time() - t0 <= TOTAL_BUDGET:
            resp = chat(msgs, None)
            answer = (resp.get("message", {}).get("content") or "").strip() or answer

    return judge(answer, task["want"]), len(trace), answer


MODES = ["完整", "砍掉工具定义", "砍掉工具结果", "砍掉系统提示", "砍掉历史"]


def main():
    n_task = len(TASKS)
    total_per_arm = n_task * REPEATS
    print("=" * 72)
    print(f"Agent 上下文消融实验   模型={MODEL}（本地 Ollama，零成本）")
    print(f"公式：Agent = LLM + 上下文 + 工具")
    print(f"{n_task} 道题 × {REPEATS} 次重复 = 每组 {total_per_arm} 个样本 × {len(MODES)} 个消融组")
    print(f"判分由代码完成，不看模型脸色")
    print("=" * 72)

    t0 = time.time()
    table = {}          # mode → {题目名: 命中次数}

    for mode in MODES:
        print(f"\n▶ 消融组：{mode}")
        counts = {t["name"]: 0 for t in TASKS}
        for r in range(REPEATS):
            for task in TASKS:
                if time.time() - t0 > TOTAL_BUDGET:
                    print(f"  ⏱ 总预算 {TOTAL_BUDGET}s 用完，停止后续实验")
                    break
                trace = []
                try:
                    ok, steps, answer = run_one(task, mode, trace, t0)
                except SystemExit:
                    raise
                except Exception as e:
                    ok, steps, answer = False, len(trace), f"<异常 {type(e).__name__}: {e}>"
                if ok:
                    counts[task["name"]] += 1
                flag = "✅" if ok else "❌"
                # 只打细节的第一轮，后面几轮压缩成一行，避免刷屏
                print(f"  {flag} 第{r+1}轮 {task['name']:<10} 期望 {task['want']:<3} "
                      f"工具 {steps} 次  回答：{answer[:44] or '(空)'}")
                if r == 0:
                    for line in trace[:4]:
                        print(f"        · {line[:76]}")
            if time.time() - t0 > TOTAL_BUDGET:
                break
        table[mode] = counts

    # ─────────── 汇总：先看矩阵（哪道题在哪个消融组挂的），再看总分 ───────────
    print("\n" + "=" * 72)
    print(f"结果矩阵   行=消融组   列=题目   格子=命中次数/{REPEATS}")
    print("=" * 72)
    w = 12
    print("  " + f"{'消融组':<14}" + "".join(f"{t['name']:<{w}}" for t in TASKS) + " 总分")
    print("  " + "-" * (14 + w * n_task + 8))
    base = None
    for mode, counts in table.items():
        cells = "".join(f"{counts[t['name']]}/{REPEATS}".ljust(w) for t in TASKS)
        got = sum(counts.values())
        if mode == "完整":
            base = got
            note = "  ← 基准线"
        elif base is not None:
            diff = got - base          # got 比基准线低 → diff 是负数 → 叫"掉"
            if diff < 0:
                note = f"  掉 {-diff} 题"
            elif diff > 0:
                note = f"  反高 {diff} 题"
            else:
                note = "  无变化"
        else:
            note = ""
        print(f"  {mode:<14}{cells} {got}/{total_per_arm}{note}")

    print(f"\n总耗时 {time.time()-t0:.0f}s")
    print("读法：掉得越多 → 被抽掉的那个上下文组件越关键。逐列看还能看出")
    print("      「哪一类任务依赖哪一类上下文」（比如两步题才吃历史）。")
    print("注意：格子里的数字不是 0 或满格时，说明**结果本身带噪声**，")
    print("      这时只有差得很大的组才值得下结论 —— 这正是评估的意义。")
    print("对照书中第 1 章：能跑的 Demo 与可靠产品之间的差距在 Harness，不在模型。")


if __name__ == "__main__":
    main()
