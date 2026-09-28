"""函数卡「路线后半段」增量（2026-09-28 补）。

为什么有这个文件：学员指出「之后可能遇到的函数，为什么全是数据库的内容，我只学习数据库么，
还有 agent 内容等」—— 对。第一版 79 张里数据库占 65%，因为我拿「本周正在上的第 3 课」当了锚，
而他要的是「**之后可能遇到**」。本文件按**他的路线**补齐后半段：

    LLM API → Agent → RAG → 数据(pandas/numpy) → Web 后端(FastAPI)

全部在他**本机 Ollama**（qwen2.5:3b + bge-m3，127.0.0.1:11434）上真跑，不联网：
    · 走 openai SDK（业界标准；换成 DeepSeek/任何一家只改 base_url 两行）
    · 只有 num_ctx / 原生 embedding 走原始 /api/chat —— 因为 SDK 那条路传不了 options

⚠️ 与本机相关的两条既有教训（别再踩，见 `教学进度看板.md` 2.1.1）：
    1. base_url 必须写 127.0.0.1，写 localhost 在 Windows 上会解析到 IPv6 ::1 而连不上（W-28）
    2. 显存吃紧：raw 调用要带 num_ctx（他实测 32768 → runner 崩，且崩后模型继续输出垃圾）

写卡纪律（同主文件）：中文里的引号一律用「」，代码块用 ''' 包（里面全是 " ），
每张卡的代码都会被 build_fn_cards.py 真执行一遍。
"""

PRE = (
    'from openai import OpenAI\n'
    'client = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")\n'
    'MODEL = "qwen2.5:3b"'
)

CARDS_EXTRA: list[dict] = []


def E(cid, cat, stage, name, brief, code, where="", gotcha="", extra="", err=False, pre=PRE):
    CARDS_EXTRA.append(dict(id=cid, lang="py", cat=cat, stage=stage, name=name, brief=brief,
                            code=code.strip("\n"), where=where, gotcha=gotcha, extra=extra,
                            err=err, pre=pre, verify=None))


# ══════════════════════════════════════════════════════════════════════
# ① LLM API（调用级）—— 你的阶段 A 主目标：自己写的 AI 应用
# ══════════════════════════════════════════════════════════════════════
E("llm.client", "LLM API", "阶段A", "建客户端：两行换一家模型",
  "`base_url` 指向谁，就是在用谁家的模型。本机 Ollama 也兼容这套接口",
  '''from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")
print("base_url =", client.base_url)''',
  where="AI 应用的第一行代码；物联网线的「大模型 API」也是它",
  gotcha="⚠️ **base_url 里写 `127.0.0.1`，不要写 `localhost`** —— Windows 上 localhost 会先解析到 IPv6 `::1`，"
         "Ollama 的 `/v1` 在那个地址上连接会被重置（你 09-21 踩过，见 W-28）。`api_key` 用本机 Ollama 时随便填，"
         "换真厂商时必须换成真的 key",
  pre="")

E("llm.chat_min", "LLM API", "阶段A", "最小一次对话",
  "`create` 里两个必填：用哪个模型、说什么话",
  '''r = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "只回两个字：你好"}],
    temperature=0)
print(r.choices[0].message.content)''',
  where="所有 AI 功能的原子操作",
  gotcha="返回的不是字符串，是**对象**：正文在 `r.choices[0].message.content` 里 —— 直接 `print(r)` 会看到一大坨，"
         "这是新手第一个卡点")

E("llm.messages", "LLM API", "阶段A", "messages 到底是什么",
  "一个 list，每个元素是 `{role, content}` 的 dict；role 只有四种",
  '''msgs = [{"role": "system", "content": "你只回答一个数字，不要解释"},
        {"role": "user", "content": "1+1 等于几"}]
r = client.chat.completions.create(model=MODEL, messages=msgs, temperature=0)
print("类型 =", type(msgs).__name__, "长度 =", len(msgs))
print("角色 =", [m["role"] for m in msgs])
print("回答 =", r.choices[0].message.content.strip()[:20])''',
  where="拼上下文、拼历史、拼检索结果，全是在往这个 list 里塞东西",
  gotcha="role 四种：`system`（定规矩）/ `user`（人说的）/ `assistant`（模型说的）/ `tool`（工具结果）。"
         "**写错 role 名字不会报错，模型会当成没看见**")

E("llm.system", "LLM API", "阶段A", "system 与 user 的分工",
  "system 定规矩、user 提要求。同一句话放进 system，行为会变",
  '''q = "评价一下数据库这门课"
a = client.chat.completions.create(model=MODEL, temperature=0, max_tokens=30,
        messages=[{"role": "user", "content": q}]).choices[0].message.content
b = client.chat.completions.create(model=MODEL, temperature=0, max_tokens=30,
        messages=[{"role": "system", "content": "只用四个字回答"},
                  {"role": "user", "content": q}]).choices[0].message.content
print("无 system：", a.strip()[:40])
print("有 system：", b.strip()[:40])''',
  where="控制输出格式/长度/口吻都在这里",
  gotcha="**system 不是必须的**，但它是唯一能稳定约束行为的地方 —— 你 09-21 那个 RAG"
         "「装死」问题（检索对了模型却说没有）就是提示词过防御写的，改 system 才好（W-19）")

E("llm.temperature", "LLM API", "阶段A", "temperature：0 和 1 差在哪",
  "同一个问题问两次，看回答是否稳定",
  '''q = [{"role": "user", "content": "给这门课起一个名字，只给名字"}]
for t in (0, 1):
    outs = set()
    for _ in range(2):
        r = client.chat.completions.create(model=MODEL, messages=q,
                                           temperature=t, max_tokens=12)
        outs.add(r.choices[0].message.content.strip())
    print(f"temperature={t}  两次回答不同 = {len(outs) > 1}  {sorted(outs)}")''',
  where="要可复现的实验（判分、评测）→ 用 0；要创意/多样 → 调高",
  gotcha="**temperature=0 也不保证逐字相同** —— 只能说「更稳定」。所以任何评测都要跑多次取统计，"
         "不能拿单次结果下结论（这点在 Agent 消融实验里已经吃过一次）")

E("llm.max_tokens", "LLM API", "阶段A", "max_tokens：把回答截断",
  "限制生成长度；被截断时 `finish_reason` 会变成 `length`",
  '''r = client.chat.completions.create(model=MODEL, temperature=0, max_tokens=5,
        messages=[{"role": "user", "content": "用三句话介绍杭州"}])
print("内容 =", repr(r.choices[0].message.content))
print("finish_reason =", r.choices[0].finish_reason)''',
  where="控制成本、控制界面长度",
  gotcha="`finish_reason='length'` 就是**被你自己截断的**（不是模型说完了）。做 JSON 输出时被截断 → "
         "`json.loads` 直接炸，这时要调大 max_tokens 而不是去改解析代码")

E("llm.read_response", "LLM API", "阶段A", "从响应里该取哪几个字段",
  "正文、结束原因、token 用量 —— 三个最常用的",
  '''r = client.chat.completions.create(model=MODEL, temperature=0,
        messages=[{"role": "user", "content": "只回：好"}])
print("正文      =", r.choices[0].message.content.strip())
print("结束原因  =", r.choices[0].finish_reason)
print("输入 tokens =", r.usage.prompt_tokens, " 输出 tokens =", r.usage.completion_tokens)''',
  where="算成本、排查「为什么断在半句」都靠它",
  gotcha="`usage` 是**按 token 计费**的依据。本机 Ollama 免费，但换真厂商后这一行就是钱 —— "
         "养成每次都看一眼的习惯")

E("llm.multiturn", "LLM API", "阶段A", "多轮对话：模型其实没有记忆",
  "它每次都只看到你这次发过去的 messages —— 历史要你自己拼",
  '''hist = [{"role": "user", "content": "我叫韩立"}]
r1 = client.chat.completions.create(model=MODEL, messages=hist, temperature=0, max_tokens=20)
print("第 1 轮问它我是谁（它不知道）：",
      client.chat.completions.create(model=MODEL, temperature=0, max_tokens=20,
        messages=hist + [{"role": "user", "content": "我叫什么？"}]).choices[0].message.content.strip()[:24])
hist.append({"role": "assistant", "content": r1.choices[0].message.content})
hist.append({"role": "user", "content": "我叫什么？"})
print("第 2 轮先回灌再问：",
      client.chat.completions.create(model=MODEL, messages=hist, temperature=0,
                                     max_tokens=20).choices[0].message.content.strip()[:24])''',
  where="做聊天界面的核心机制；也是「上下文怎么变长」的根源",
  gotcha="🔑 **模型是无状态的**。忘了回灌 assistant 历史 → 它每一轮都像第一次见你。"
         "反过来，历史越攒越长 → 迟早爆上下文，所以要裁剪（见 `agent.trim`）")

E("llm.stream", "LLM API", "阶段A", "流式输出：一个字一个字吐",
  "`stream=True` 后返回的是**一堆 chunk**，要自己拼起来",
  '''s = client.chat.completions.create(model=MODEL, temperature=0, stream=True,
        messages=[{"role": "user", "content": "用三句话介绍杭州，每句以句号结尾。"}])
parts = [ch.choices[0].delta.content for ch in s if ch.choices[0].delta.content]
print("收到", len(parts), "个 chunk，前 3 个 =", parts[:3])
print("拼起来 =", "".join(parts)[:40])''',
  where="做「AI 边想边显示」的界面必须用它（否则用户盯着空白等 10 秒）",
  gotcha="流式时**没有** `message.content`，只有 `delta.content`；而且最后一块可能是空串，"
         "不加 `if` 判断会拼出一堆 `None`")

E("llm.json", "LLM API", "阶段A", "让模型吐 JSON（然后真解析）",
  "`response_format` 要求 JSON；但模型仍可能加解释文字",
  '''import json
r = client.chat.completions.create(model=MODEL, temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": "输出 JSON：姓名=韩立，年龄=19"}])
txt = r.choices[0].message.content
print("原始返回 =", txt[:50])
d = json.loads(txt)
print("解析后 =", d, type(d).__name__)''',
  where="让模型当「结构化数据生成器」—— 你要喂给下一段程序的必经一步",
  gotcha="模型经常把 JSON 包在 ```json 里。**先 `strip` 掉代码围栏再 `json.loads`**，"
         "并且永远包一层 `try/except` —— 它会偶尔漏个引号，你不该因此整个程序崩")

E("llm.tools", "LLM API", "阶段A", "tools：让模型「要求调用函数」",
  "你给工具清单，模型决定调哪个、参数是什么 —— 但**它不会真的执行**",
  '''tools = [{"type": "function", "function": {
    "name": "get_weather", "description": "查某个城市的天气",
    "parameters": {"type": "object", "properties": {"city": {"type": "string"}},
                   "required": ["city"]}}}]
r = client.chat.completions.create(model=MODEL, temperature=0, tools=tools,
        messages=[{"role": "user", "content": "北京现在几度？用工具查"}])
tc = r.choices[0].message.tool_calls
print("finish_reason =", r.choices[0].finish_reason)
print("要调的工具 =", None if not tc else [(x.function.name, x.function.arguments) for x in tc])''',
  where="Agent 的地基。物联网线的「工具调用」也是这个",
  gotcha="🔑 模型只返回**「我想调 get_weather，参数 {\"city\":\"北京\"}」**这串东西 —— "
         "**真正执行函数的是你的代码**。参数是**字符串**，要 `json.loads` 才是 dict")

E("llm.raw_ollama", "LLM API", "阶段A", "原始 /api/chat：为什么还要会这条路",
  "openai 那条路传不了 `options`（比如 num_ctx），而它决定了你会不会把显存撑爆",
  '''import requests
r = requests.post("http://127.0.0.1:11434/api/chat", timeout=60, json={
    "model": "qwen2.5:3b", "stream": False,
    "messages": [{"role": "user", "content": "只回：收到"}],
    "options": {"temperature": 0, "num_ctx": 4096}}).json()
print("正文 =", r["message"]["content"])
print("本次输出 token =", r["eval_count"], "| 耗时 =", round(r["total_duration"] / 1e9, 2), "秒")''',
  where="你的 `agent_上下文消融.py` 走的就是这条；调本机模型参数必须用它",
  gotcha="⚠️ **`num_ctx` 必须给**：Ollama 默认 32768，你 8G 显存撑爆后 runner 会崩，"
         "**而且崩之后模型照样输出、只是全是垃圾**（你实测每道题都答 23 —— 比报错危险得多）")

E("llm.embed_ollama", "LLM API", "阶段A", "把文本变成向量（bge-m3）",
  "embedding 是语义检索的地基：一段文本 → 1024 个数字",
  '''e = client.embeddings.create(model="bge-m3", input="数据库系统概论")
v = e.data[0].embedding
print("维度 =", len(v), "| 前 3 个数 =", [round(x, 4) for x in v[:3]])
print("类型 =", type(v).__name__)''',
  where="RAG 的第一步；你 09-21 用 bge-m3 把 Recall@1 做到 87%",
  gotcha="**向量不是给人看的** —— 单看某个数没有意义，有意义的是两条向量之间的**夹角**（余弦相似度）。"
         "同一段文本每次算出来的向量是一样的（不像生成），所以**可以缓存**（见 `rag.cache`）")

E("llm.errors", "LLM API", "阶段A", "调用会怎么失败：异常类型 + 重试骨架",
  "连不上、超时、对方返回错误 —— 三种要分开接",
  '''from openai import APIConnectionError, APITimeoutError, APIStatusError
def ask(prompt, tries=2):
    for i in range(tries):
        try:
            return client.chat.completions.create(model=MODEL, temperature=0, timeout=3,
                messages=[{"role": "user", "content": prompt}]).choices[0].message.content
        except (APITimeoutError, APIConnectionError) as e:
            print(f"  第 {i+1} 次失败：{type(e).__name__}")
    return None
print("正常调用 =", ask("只回：好")[:10])
bad = OpenAI(base_url="http://127.0.0.1:9/v1", api_key="x", timeout=2)
try:
    bad.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": "x"}])
except Exception as e:
    print("打不通的地址会抛 =", type(e).__name__)''',
  where="任何要跑一整晚的脚本（评测、消融）都必须有这层",
  gotcha="⚠️ 抄你自己代码里那个坑：**`urllib.error.HTTPError` 是 `URLError` 的子类** —— "
         "先接 URLError 会把「服务器返回 500」误报成「连不上」，完全误导排查方向")

E("llm.prompt_tpl", "LLM API", "阶段A", "提示词模板：把变量拼进问题里",
  "就是 f-string。但要给模型留出「资料区」，别把指令和资料搅在一起",
  '''def build(question, docs):
    资料 = "\\n".join(f"[{i+1}] {d}" for i, d in enumerate(docs))
    return (f"只根据下面资料回答，资料里没有就说不知道。\\n\\n"
            f"【资料】\\n{资料}\\n\\n【问题】{question}")
p = build("数据库课讲什么", ["数据库系统概论讲关系模型和 SQL", "高数讲极限"])
print(p)
print("---")
print("模型答：", client.chat.completions.create(model=MODEL, temperature=0, max_tokens=30,
        messages=[{"role": "user", "content": p}]).choices[0].message.content.strip()[:40])''',
  where="RAG 的最后一步；也是「提示词工程」最朴素的形态",
  gotcha="给资料**编号**（`[1] [2]`）不是装饰 —— 这样你才能要求模型回答时标「依据 [2]」，"
         "出问题时能回溯是哪条资料错了")

# ══════════════════════════════════════════════════════════════════════
# ② Agent —— 看板 2.1.1 已经开线，核心公式 Agent = LLM + 上下文 + 工具
# ══════════════════════════════════════════════════════════════════════
E("agent.tool_schema", "Agent", "阶段A", "工具定义：名字 + 说明 + 参数表",
  "description 写得好不好，直接决定模型会不会用对工具",
  '''import json
def 定义工具(name, desc, props, required):
    return {"type": "function", "function": {"name": name, "description": desc,
            "parameters": {"type": "object", "properties": props, "required": required}}}
t = 定义工具("search_notes", "在本地学习笔记里搜索关键词，返回命中的片段",
             {"keyword": {"type": "string", "description": "要搜的关键词"}}, ["keyword"])
print(json.dumps(t, ensure_ascii=False, indent=1))''',
  where="Agent 的第一块砖；你实验 1-1 里注册的那 4 个工具就是这个结构",
  gotcha="`description` 是给**模型**看的（不是注释！）。写「搜索」这种模糊说明，模型就不知道该什么时候用；"
         "要写清「**什么时候该用、返回什么**」")

E("agent.dispatch", "Agent", "阶段A", "工具分发：名字 → 真函数",
  "模型只给名字和参数，中间这层映射得你自己写",
  '''import json
def 查天气(city):        return f"{city} 晴 26℃"
def 算加法(a, b):        return str(float(a) + float(b))
TOOLS = {"get_weather": 查天气, "add": 算加法}

def 执行(name, args_json):
    fn = TOOLS.get(name)
    if fn is None:
        return f"没有这个工具：{name}"
    try:
        return fn(**json.loads(args_json))
    except Exception as e:
        return f"工具执行失败：{type(e).__name__}: {e}"

print(执行("get_weather", '{"city": "合肥"}'))
print(执行("add", '{"a": 1, "b": 41}'))
print(执行("nope", "{}"))''',
  where="Agent 循环里「模型说要调工具」之后的那一步",
  gotcha="🔑 **参数是 JSON 字符串，要 `json.loads`**；模型还可能给不存在的工具名或缺参数 —— "
         "**工具执行失败必须变成一段文字回灌给模型**，而不是让程序崩。"
         "模型看到「工具执行失败：KeyError」会自己换个参数重试")

E("agent.one_step", "Agent", "阶段A", "一步工具调用：完整闭环",
  "模型要工具 → 你执行 → 把结果回灌 → 模型给最终答案",
  '''import json
TOOLS = [{"type": "function", "function": {"name": "get_weather", "description": "查城市天气",
    "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]
msgs = [{"role": "user", "content": "合肥今天多少度？必须先调工具查，不要猜。"}]
r1 = client.chat.completions.create(model=MODEL, messages=msgs, tools=TOOLS, temperature=0)
call = r1.choices[0].message.tool_calls[0]
msgs.append(r1.choices[0].message)                      # ★ 必须把 assistant 这条也放回去
msgs.append({"role": "tool", "tool_call_id": call.id, "content": "合肥 晴 26℃"})
r2 = client.chat.completions.create(model=MODEL, messages=msgs, temperature=0, max_tokens=30)
print("工具要的参数 =", call.function.arguments)
print("回灌后最终答 =", r2.choices[0].message.content.strip()[:30])''',
  where="Agent 的最小完整闭环；把这段放进 while 就是 Agent 循环",
  gotcha="🔑 **`tool` 这条消息必须带 `tool_call_id`**，而且前面必须先把 `assistant`（含 tool_calls）"
         "那条塞回历史 —— 少任何一条，模型都不知道你在回应哪个调用")

E("agent.loop", "Agent", "阶段A", "Agent 循环骨架（带步数上限）",
  "while：模型 → 要工具就执行回灌 → 不要工具就结束",
  '''import json
TOOLS = [{"type": "function", "function": {"name": "add", "description": "两数相加",
    "parameters": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                   "required": ["a", "b"]}}}]
REAL = {"add": lambda a, b: a + b}
msgs = [{"role": "user", "content": "先算 (17+25)，再把结果加 8。用工具算。"}]
for step in range(1, 5):
    r = client.chat.completions.create(model=MODEL, messages=msgs, tools=TOOLS, temperature=0)
    m = r.choices[0].message
    if not m.tool_calls:
        print(f"第 {step} 步：模型给最终答案 = {m.content.strip()[:40]}")
        break
    msgs.append(m)
    for c in m.tool_calls:
        out = REAL[c.function.name](**json.loads(c.function.arguments))
        print(f"第 {step} 步：调用 {c.function.name}{c.function.arguments} → {out}")
        msgs.append({"role": "tool", "tool_call_id": c.id, "content": str(out)})''',
  where="**这就是 Agent**：LLM + 循环 + 工具。物联网线的「服务组合」和它同构",
  gotcha="⚠️ `for step in range(1, 5)` 那个上限**不是可选项** —— 模型可能反复调同一个工具停不下来，"
         "没有上限就是死循环 + 无限调用（真厂商那边就是无限花钱）")

E("agent.tool_msg", "Agent", "阶段A", "消息序列长什么样（画出来）",
  "一次工具调用会让 messages 长出两条：assistant(带 tool_calls) 和 tool",
  '''import json
TOOLS = [{"type": "function", "function": {"name": "now", "description": "取当前时间",
    "parameters": {"type": "object", "properties": {}}}}]
msgs = [{"role": "user", "content": "现在几点？用工具查"}]
r = client.chat.completions.create(model=MODEL, messages=msgs, tools=TOOLS, temperature=0)
msgs.append(r.choices[0].message)
msgs.append({"role": "tool", "tool_call_id": r.choices[0].message.tool_calls[0].id,
             "content": "2026-09-28 14:32"})
for i, m in enumerate(msgs, 1):
    role = m["role"] if isinstance(m, dict) else m.role
    keys = sorted(m.keys()) if isinstance(m, dict) else "（对象，字段见 assistant 那条）"
    print(f"{i}. role={role:9s} 字段={keys}")''',
  where="调试 Agent 最有效的一招：把 messages 打出来看",
  gotcha="**`assistant` 那条在代码里是对象、在列表里可以是 dict** —— 直接 `json.dumps(msgs)` 会报"
         "「不是 JSON 可序列化」。要排查就 `print(m.model_dump())`（新版 SDK）")

E("agent.trim", "Agent", "阶段A", "上下文裁剪：聊久了必须扔历史",
  "保 system + 最近 N 条；扔掉的只能扔，不能「压缩」",
  '''def trim(msgs, keep=3):
    sys = [m for m in msgs if m["role"] == "system"]
    rest = [m for m in msgs if m["role"] != "system"]
    return sys + rest[-keep:]

hist = [{"role": "system", "content": "你是助手"}] + [
    {"role": "user" if i % 2 else "assistant", "content": f"第{i}句"} for i in range(1, 11)]
out = trim(hist, keep=3)
print("原长 =", len(hist), "→ 裁后 =", len(out))
print("留下 =", [(m["role"], m["content"]) for m in out])''',
  where="长对话、长任务（Agent 跑几十步）迟早撞上",
  gotcha="⚠️ 裁剪会**切断「工具调用 → 工具结果」的配对**（tool 消息的 tool_call_id 找不到对应的 assistant）—— "
         "有些厂商会直接报错。要按「一轮」为单位裁，不要按条数乱切")

E("agent.budget", "Agent", "阶段A", "上下文预算：本机显存是硬约束",
  "同一个问题，给模型多少上下文，直接决定它会不会崩",
  '''import requests
def ask(num_ctx):
    r = requests.post("http://127.0.0.1:11434/api/chat", timeout=120, json={
        "model": "qwen2.5:3b", "stream": False, "options": {"temperature": 0, "num_ctx": num_ctx},
        "messages": [{"role": "user", "content": "只回：好"}]}).json()
    return r.get("message", {}).get("content", "（空）")
for n in (512, 4096):
    print(f"num_ctx={n:5d} → 答 = {ask(n)[:10]}")''',
  where="本机跑模型的必备知识；也是 Agent 消融实验能跑完 100 次调用的原因",
  gotcha="🔑 **上下文不是越大越好**：KV cache 随 num_ctx 线性吃显存。你 8G 显存实测 32768 会崩，"
         "`4096` 之后 30 次突发调用零失败。**判断原则：够放「system + 检索资料 + 最近几轮」就行**")

E("agent.multi_tools", "Agent", "阶段A", "一次返回多个工具调用",
  "模型可以一轮里同时要求调几个工具 —— 你要按顺序都执行完",
  '''import json
TOOLS = [
 {"type": "function", "function": {"name": "get_weather", "description": "查城市天气",
   "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}},
 {"type": "function", "function": {"name": "get_time", "description": "查城市当前时间",
   "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]
r = client.chat.completions.create(model=MODEL, temperature=0, tools=TOOLS,
        messages=[{"role": "user", "content": "合肥和杭州的天气、时间都查一下，两个工具都用"}])
tcs = r.choices[0].message.tool_calls or []
print("这一轮要求调", len(tcs), "个工具：",
      [(c.function.name, json.loads(c.function.arguments)) for c in tcs])''',
  where="用户问「A 和 B 都查一下」时就是这个形态",
  gotcha="**每个 tool_call 都要各自回一条 `role='tool'` 消息**（用各自的 id）。"
         "只回一条、或漏掉某一个 id → 模型会以为那个工具还没跑完，然后重复要求调用它")

E("agent.react", "Agent", "阶段A", "ReAct：先写「想法」再决定动作",
  "强制模型把推理过程说出来，比直接让它调工具更稳",
  '''SYS = ("你是一个会用工具的助手。每次回复必须先写一行「想法：…」（说明你打算怎么做），"
       "再决定是否调用工具。不要跳步。")
r = client.chat.completions.create(model=MODEL, temperature=0, max_tokens=60,
        messages=[{"role": "system", "content": SYS},
                  {"role": "user", "content": "我要把 17 和 25 相加再加 8，你打算分几步做？"}])
print(r.choices[0].message.content.strip()[:120])''',
  where="书上第 1 章的起点思想；调试 Agent 时把想法打出来就知道它哪一步想歪了",
  gotcha="「想法」是**给人和给下一轮用的中间产物**，不是真理 —— 模型写「想法：先查天气」"
         "然后调了别的工具，这种不一致很常见，要靠工具结果回灌把它拽回来")

E("agent.state", "Agent", "阶段A", "把 Agent 的状态存下来",
  "步数、工具调用次数、trace —— 没有它，出了错你只能瞎猜",
  '''import json
state = {"steps": 0, "tool_calls": [], "finished": False}
def step(state, tool_name, result):
    state["steps"] += 1
    state["tool_calls"].append({"step": state["steps"], "tool": tool_name, "result": result})
    if state["steps"] >= 3:
        state["finished"] = True
    return state
step(state, "add", 42); step(state, "add", 50)
print(json.dumps(state, ensure_ascii=False, indent=1))''',
  where="跑评测（你的消融实验）时靠它记录每一步，而不是只看最后答案",
  gotcha="你 09-21 那次「模型崩了却继续输出垃圾、每道题都答 23」能被发现，正是因为**留了每次的原始回答**。"
         "**只记总分，会把「蒙对」藏起来**（那是 W-26 的教训）")

# ══════════════════════════════════════════════════════════════════════
# ③ RAG —— 你已经跑通并且量化过的（Recall@1 87%）
# ══════════════════════════════════════════════════════════════════════
E("rag.chunk", "RAG", "阶段A", "切块：长文本要切开才能检索",
  "按长度切、留一点重叠 —— 重叠是为了不让一句话被切断在两块里",
  '''def chunk(text, size=18, overlap=4):
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i + size])
        if i + size >= len(text):
            break
        i += size - overlap
    return out
doc = "数据库系统概论讲关系模型和SQL语言。索引能加快查询速度。事务保证数据一致性。"
for i, c in enumerate(chunk(doc), 1):
    print(f"{i}. {c}")''',
  where="RAG 第一步。docx/pdf 抽出来的长文本必须切",
  gotcha="块切太小 → 检索到的片段缺上下文，模型答不全；切太大 → 一块里混了好几个主题，"
         "相似度被稀释。**没有标准答案，要拿你的问题去试**")

E("rag.cosine", "RAG", "阶段A", "余弦相似度：两个向量像不像",
  "点积 / 模长乘积；结果在 -1~1，越大越像",
  '''import numpy as np
def cos(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
print("自己 == 自己      =", round(cos([1, 2, 3], [1, 2, 3]), 4))
print("同方向、长度不同  =", round(cos([1, 2, 3], [2, 4, 6]), 4))
print("垂直              =", round(cos([1, 0], [0, 1]), 4))
print("相反              =", round(cos([1, 0], [-1, 0]), 4))''',
  where="所有语义检索的核心运算；你 `rag/01` 里的排序就是它",
  gotcha="**余弦只看方向、不看长度** —— 所以文本长短不影响它，这是它比欧氏距离更适合做文本检索的原因。"
         "但它对「模型本身好不好」无能为力：embedding 差，余弦再准也搜不到")

E("rag.topk", "RAG", "阶段A", "top-k 检索：排序取前 k 条",
  "真实用法：把问题也变成向量，和每条资料算相似度，取最大的 k 个",
  '''import numpy as np
docs = ["数据库系统概论讲关系模型和SQL", "高数讲极限和导数", "膳食指南建议少油少盐"]
q = "SQL 是什么"
# 这里用字符重合度代替真 embedding，只为演示排序逻辑；真实项目换成 bge-m3
score = [len(set(q) & set(d)) / len(set(q) | set(d)) for d in docs]
order = np.argsort(score)[::-1]
for rank, i in enumerate(order[:2], 1):
    print(f"第{rank}名  相似度={score[i]:.4f}  {docs[i]}")''',
  where="RAG 的「检索」就是这十行；换掉打分函数就是真语义检索",
  gotcha="⚠️ 本卡用**字符重合度**代替真 embedding，只为让你看清排序逻辑 —— "
         "**这种「零依赖伪向量」对同义词完全无效**（你 09-21 实测：「免疫」「体虚乏力」全部 0 命中，见 W-18）。"
         "真项目必须上 `bge-m3`")

E("rag.tfidf", "RAG", "阶段A", "TF-IDF：不上模型的检索基线",
  "关键词权重检索。做 RAG 时要拿它当对照，才知道语义检索到底赢了多少",
  '''from sklearn.feature_extraction.text import TfidfVectorizer
docs = ["数据库系统概论讲关系模型和SQL", "高数讲极限和导数", "数据库索引加快查询"]
v = TfidfVectorizer(analyzer="char", ngram_range=(1, 2))
X = v.fit_transform(docs)
print("矩阵形状（文档数 × 特征数）=", X.shape)
q = v.transform(["数据库 索引"])
print("每条得分 =", [round(float(x), 3) for x in (X @ q.T).toarray().ravel()])''',
  where="物联网线的「服务发现」如果不上模型，就是这个；也是论文里常见的 baseline",
  gotcha="`analyzer='char'` 是为中文准备的（中文默认按词切会切错）。**TF-IDF 完全不理解同义词** —— "
         "搜「索引」不会命中「index」，这是它和语义检索的分水岭")

E("rag.assemble", "RAG", "阶段A", "把检索到的资料塞进 prompt",
  "检索 → 拼提示词 → 生成。这一步错了，前面检索再准也白搭",
  '''docs = ["数据库系统概论讲关系模型和 SQL 语言", "索引能加快查询速度"]
q = "为什么要建索引"
ctx = "\\n".join(f"[{i+1}] {d}" for i, d in enumerate(docs))
prompt = f"只根据下面资料回答；资料里没有就说不知道。\\n{ctx}\\n\\n问题：{q}"
print("拼好的提示词 ↓")
print(prompt)
print("模型答：", client.chat.completions.create(model=MODEL, temperature=0, max_tokens=40,
        messages=[{"role": "user", "content": prompt}]).choices[0].message.content.strip()[:50])''',
  where="RAG 的第三步；也是 `rag/02` 干的事",
  gotcha="⚠️ **必须写「资料里没有就说不知道」**，否则模型会拿它自己的知识编 —— 那就不叫 RAG 了。"
         "但这条又不能写太狠：你 09-21 实测过，过度防御的提示词会让模型「装死」（检索明明命中却说没有，见 W-19）")

E("rag.recall", "RAG", "阶段A", "评测检索质量：Recall@k 和 MRR",
  "没有评测的 RAG 只是「感觉还行」—— 你那次量化到 Recall@1 87%",
  '''def recall_at_k(ranks, k):        # ranks: 每条问题的正确资料排在第几名（从 1 开始）
    return sum(1 for r in ranks if r <= k) / len(ranks)
def mrr(ranks):
    return sum(1 / r for r in ranks) / len(ranks)
ranks = [1, 1, 2, 1, 3, 1, 1, 5, 1, 2]     # 10 个问题的正确命中位次
print(f"Recall@1 = {recall_at_k(ranks, 1):.0%}   Recall@3 = {recall_at_k(ranks, 3):.0%}")
print(f"MRR      = {mrr(ranks):.3f}")''',
  where="要向导师/面试官说「我的检索效果是 X%」时，必须有这个数",
  gotcha="**评测集必须是你自己标的**（哪条资料才是正确答案）。用模型自己判断对错 = 自己给自己打分。"
         "你的 RAG 那次是手工标的小集，样本量小 —— 报数字时要一起说样本量，别只报百分比")

E("rag.cache", "RAG", "阶段A", "把向量缓存到本地",
  "embedding 是确定的，算一次就够了 —— 省时间，也省钱",
  '''import json, hashlib, tempfile, os, shutil
def key(t):
    return hashlib.md5(t.encode("utf-8")).hexdigest()[:12]
d = tempfile.mkdtemp(); p = os.path.join(d, "cache.json")
docs = ["数据库系统概论", "高数讲义"]
cache = {key(t): [1, 2, 3] for t in docs}          # 假装这里是真的 1024 维向量
with open(p, "w", encoding="utf-8") as f:
    json.dump(cache, f, ensure_ascii=False)
again = json.load(open(p, encoding="utf-8"))
print("缓存键 =", list(again))
print("命中第一条 =", key("数据库系统概论") in again, "| 维度 =", len(again[key("数据库系统概论")]))
shutil.rmtree(d, ignore_errors=True)''',
  where="你 `rag/_embeddings-cache.json` 就是干这个的（170 KB）",
  gotcha="缓存键要用**文本的 hash**，不要用「第几条」—— 文档一增删，序号全乱，缓存就变成了错答案。"
         "换 embedding 模型时**必须清缓存**（不同模型的向量不可比）")

# ══════════════════════════════════════════════════════════════════════
# ④ 数据（pandas / numpy）—— 物联网线与所有「处理表格」的场景
# ══════════════════════════════════════════════════════════════════════
E("pd.read_csv", "数据", "阶段A", "pandas 读 CSV",
  "两行读进来，形状、列名、前几行立刻能看到",
  '''import pandas as pd, tempfile, os, shutil
d = tempfile.mkdtemp(); p = os.path.join(d, "people.csv")
open(p, "w", encoding="utf-8").write("姓名,年龄,标签\\n王奶奶,78,独居\\n李爷爷,82,糖尿病\\n")
df = pd.read_csv(p, encoding="utf-8")
print("形状（行, 列）=", df.shape)
print("列名 =", list(df.columns))
print(df.to_string(index=False))
shutil.rmtree(d, ignore_errors=True)''',
  where="物联网线要处理老人数据；任何 Excel/CSV 分析的第一步",
  gotcha="⚠️ 中文 CSV 常是 **GBK**：`encoding='utf-8'` 报 `UnicodeDecodeError` 时换 `'gbk'`。"
         "还有 `dtype={'手机号': str}` —— 不然前导 0 和长数字会被 pandas 改掉")

E("pd.select", "数据", "阶段A", "选列 / 按条件筛选",
  "`df[列名]` 取列、`df[布尔条件]` 取行",
  '''import pandas as pd
df = pd.DataFrame({"姓名": ["王奶奶", "李爷爷", "张阿姨"], "年龄": [78, 82, 65],
                   "标签": ["独居", "糖尿病", "独居"]})
print("只取一列 →", list(df["年龄"]))
print("按条件筛 →")
print(df[df["年龄"] > 70].to_string(index=False))
print("两个条件要用 & 并加括号 →", len(df[(df["年龄"] > 70) & (df["标签"] == "独居")]))''',
  where="清洗数据、挑出要分析的那部分",
  gotcha="**多条件必须用 `&` `|`，不能用 `and` `or`**，而且**每个条件都要自己加括号** —— "
         "`df[df.a > 1 & df.b < 2]` 不会报错，只会给你错结果（运算符优先级）")

E("pd.groupby", "数据", "阶段A", "groupby：pandas 里的分堆统计",
  "和第 7 章 SQL 的 `GROUP BY` 是同一件事，只是换了语言",
  '''import pandas as pd
df = pd.DataFrame({"标签": ["独居", "糖尿病", "独居", "糖尿病", "独居"],
                   "年龄": [78, 82, 65, 71, 88]})
g = df.groupby("标签")["年龄"]
print("每组人数 ="); print(g.count().to_string())
print("每组平均 ="); print(g.mean().round(1).to_string())
print("一次算多个 ="); print(g.agg(["count", "mean", "max"]).to_string())''',
  where="统计分布；对应你 SQL 里刚学的 `GROUP BY cid, COUNT(*)`",
  gotcha="`groupby` **默认把分组列变成索引**；想让它留成普通列加 `as_index=False` 或 `.reset_index()`。"
         "忘了这一步，后面 `merge` 会莫名其妙对不上")

E("pd.merge", "数据", "阶段A", "merge：pandas 的 JOIN（和第 3 课一模一样）",
  "参数就是 `left_on` / `right_on` / `how` —— how 就是 INNER / LEFT",
  '''import pandas as pd
老人 = pd.DataFrame({"id": [1, 2, 3], "姓名": ["王奶奶", "李爷爷", "张阿姨"]})
需求 = pd.DataFrame({"老人id": [1, 1, 2], "需求": ["助餐", "陪诊", "助浴"]})
inner = 老人.merge(需求, left_on="id", right_on="老人id", how="inner")
left  = 老人.merge(需求, left_on="id", right_on="老人id", how="left")
print("inner（两边都配上才留）行数 =", len(inner))
print(inner[["姓名", "需求"]].to_string(index=False))
print("left（左边一个都不能丢）行数 =", len(left), "| 没需求的显示 =", left["需求"].isna().sum(), "个 NaN")''',
  where="🔑 **你刚学的 JOIN 直接迁移过来** —— 同一个概念换个语言；物联网线合并两张表靠它",
  gotcha="和 SQL 同一个坑：**`how='left'` 去掉就是 inner，左边的行会整个消失**。"
         "另外 pandas 里 NULL 显示成 `NaN`，判断要用 `isna()` 而不是 `== None`")

E("pd.to_json", "数据", "阶段A", "DataFrame → 喂给模型 / 存盘",
  "转成 dict/list 再 `json.dumps`，就能塞进 prompt 或发出去",
  '''import pandas as pd, json
df = pd.DataFrame({"姓名": ["王奶奶", "李爷爷"], "年龄": [78, 82]})
print("转 dict 列表 =", df.to_dict(orient="records"))
print("紧凑 JSON =", df.to_json(orient="records", force_ascii=False))
print("给模型的表格文本 ↓")
print(df.to_csv(index=False, sep="|").strip())''',
  where="让模型「看」表格数据：最省 token 的方式是 CSV 文本，不是 JSON",
  gotcha="**JSON 比 CSV 费 token**（每个字段名重复一遍）。行数多的时候优先给 CSV。"
         "`to_json` 默认把中文转成 `\\\\uXXXX`，要 `force_ascii=False`")

E("np.vector", "数据", "阶段A", "numpy 向量化：别写 for 循环算数",
  "同样的计算，向量化版本短得多、快得多",
  '''import numpy as np, time
a = np.arange(200_000); b = np.arange(200_000)
t = time.perf_counter(); c1 = [x + y for x, y in zip(a.tolist(), b.tolist())]; t1 = time.perf_counter() - t
t = time.perf_counter(); c2 = a + b; t2 = time.perf_counter() - t
print(f"循环 {t1*1000:.1f} ms   向量化 {t2*1000:.1f} ms   快 {t1/t2:.0f} 倍")
print("结果相同 =", c1[:3] == list(c2[:3]))''',
  where="处理几万条老人数据时，这是「跑得动」和「跑不动」的区别",
  gotcha="**向量化不是「更快的循环」，是「根本不循环」**（底层 C 一次算一批）。"
         "但遇到「这一步依赖上一步结果」的逻辑，向量化写不出来 —— 该用循环就用循环")

E("np.norm", "数据", "阶段A", "归一化：把向量变成单位长度",
  "除以模长。语义检索里提前归一化，后面算相似度就只剩点积",
  '''import numpy as np
v = np.array([3.0, 4.0])
u = v / np.linalg.norm(v)
print("原向量 =", v, " 模长 =", np.linalg.norm(v))
print("单位向量 =", u, " 新模长 =", round(float(np.linalg.norm(u)), 6))
print("归一化后 点积 == 余弦 =", round(float(u @ u), 6))''',
  where="批量检索时先归一化 → 相似度计算退化成一个矩阵乘法，快很多",
  gotcha="**零向量不能归一化**（除以 0 → `nan`），检索时会静默排到最后。"
         "如果某条资料抽出来是空文本，它的向量就是零向量 —— 要先过滤掉")

E("pd.datetime", "数据", "阶段A", "时间列：字符串 → 真时间",
  "`to_datetime` 之后才能排序、算间隔、按月分组",
  '''import pandas as pd
df = pd.DataFrame({"服务日期": ["2026-03-01", "2026-03-15", "2026-04-02"], "时长": [40, 60, 30]})
df["服务日期"] = pd.to_datetime(df["服务日期"])
df["月份"] = df["服务日期"].dt.strftime("%Y-%m")
print(df.to_string(index=False))
print("按月合计时长 ="); print(df.groupby("月份")["时长"].sum().to_string())''',
  where="时间序列分析；你那 52,482 条真实活动数据必然用得上",
  gotcha="**不转 `to_datetime` 就 `.dt` 会报错** —— 字符串没有 `.dt`。"
         "格式不统一（`2026/3/1` 混 `2026-03-01`）时要加 `format='mixed'` 或 `dayfirst=`")

# ══════════════════════════════════════════════════════════════════════
# ⑤ FastAPI —— 你自己的 api.py 就是它；3 条 JD 要后端能力
# ══════════════════════════════════════════════════════════════════════
E("fa.app", "FastAPI", "阶段A", "最小应用 + 一个接口",
  "装饰器写路径，函数返回什么就发什么（dict 自动变 JSON）",
  '''from fastapi import FastAPI
app = FastAPI()
@app.get("/hello")
def hello():
    return {"msg": "你好"}
print("路径表 =", [r.path for r in app.routes if r.path.startswith("/")])
print("方法   =", [sorted(r.methods)[0] for r in app.routes if r.path == "/hello"])''',
  where="你 `../我的练习/api.py` 的骨架；服务器 8009 端口上跑的就是这个",
  gotcha="**返回 dict 就会被自动转成 JSON** —— 你不需要 `json.dumps`。"
         "但返回一个不能序列化的对象（比如 datetime 以外的自定义类）会 500")

E("fa.testclient", "FastAPI", "阶段A", "不启服务器也能测接口",
  "`TestClient` 直接把请求喂给 app —— 你 27 个测试就是这么跑的",
  '''from fastapi import FastAPI
from fastapi.testclient import TestClient
app = FastAPI()
@app.get("/add")
def add(a: int, b: int):
    return {"result": a + b}
c = TestClient(app)
r = c.get("/add", params={"a": 17, "b": 25})
print("状态码 =", r.status_code)
print("返回 JSON =", r.json())
bad = c.get("/add", params={"a": "abc", "b": 1})
print("传错类型 → 状态码 =", bad.status_code, "| 详情里有 =", list(bad.json()["detail"][0].keys()))''',
  where="写测试的正确姿势：不起服务器、不占端口、毫秒级",
  gotcha="**必填参数没传 → 422 不是 400**（FastAPI 的校验错误码是 422）。"
         "另外返回的 `r.json()` 才是 dict，`r.text` 是字符串")

E("fa.pydantic", "FastAPI", "阶段A", "请求体 + 自动校验（Pydantic）",
  "定义模型 → 参数写模型 → 校验、文档、类型全自动",
  '''from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
class 老人需求(BaseModel):
    老人编号: int = Field(gt=0, description="必须正整数")
    需求: list[str] = Field(min_length=1)
    预算: float | None = None
app = FastAPI()
@app.post("/needs")
def add_need(n: 老人需求):
    return {"收到": n.需求, "条数": len(n.需求)}
c = TestClient(app)
print(c.post("/needs", json={"老人编号": 1, "需求": ["助餐"], "预算": 30.0}).json())
print("需求给空列表 →", c.post("/needs", json={"老人编号": 1, "需求": []}).status_code)
print("编号给 0 →", c.post("/needs", json={"老人编号": 0, "需求": ["助餐"]}).status_code)''',
  where="接口的「守门员」；字段一多，手写校验必然出错",
  gotcha="**`预算: float | None = None` 才是可选的**；写成 `预算: float = None` 类型标注就骗人了。"
         "另外字段名用中文是可以的（Python 3 标识符支持），但**发给别人用时会很难受**，慎用")

E("fa.error", "FastAPI", "阶段A", "主动返回错误：HTTPException",
  "业务上「不允许」要自己抛，顺便给前端一句人话",
  '''from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
app = FastAPI()
DB = {1: "王奶奶"}
@app.get("/elder/{eid}")
def get_elder(eid: int):
    if eid not in DB:
        raise HTTPException(status_code=404, detail=f"没有编号为 {eid} 的老人")
    return {"姓名": DB[eid]}
c = TestClient(app)
print("存在 →", c.get("/elder/1").json())
r = c.get("/elder/99")
print("不存在 →", r.status_code, r.json()["detail"])''',
  where="第 2 课那个 404 排查法讲的就是这个；现在你能造 404 了",
  gotcha="**`detail` 会被原样发给调用方** —— 不要把堆栈、SQL、路径塞进去（信息泄露）。"
         "想统一改返回格式，用 `@app.exception_handler`")

E("fa.query", "FastAPI", "阶段A", "路径参数 / 查询参数 / 默认值",
  "路径里的用 `{}`，问号后面的自动变函数参数",
  '''from fastapi import FastAPI
from fastapi.testclient import TestClient
app = FastAPI()
@app.get("/search")
def search(q: str, limit: int = 5, exact: bool = False):
    return {"查": q, "限制": limit, "精确": exact}
c = TestClient(app)
print("/search?q=助餐            →", c.get("/search", params={"q": "助餐"}).json())
print("/search?q=助餐&limit=2    →", c.get("/search", params={"q": "助餐", "limit": 2}).json())
print("不传 q（必填）→ 状态码", c.get("/search").status_code)''',
  where="所有带筛选/分页的接口",
  gotcha="**`limit: int = 5` 写在函数签名里就同时完成了三件事**：类型转换、校验、默认值 —— "
         "这就是 FastAPI 的价值。不写默认值 = 必填，不传就 422")

E("fa.uvicorn", "FastAPI", "阶段A", "把它跑起来（以及线上怎么跑）",
  "`uvicorn` 是服务器；本机开发带 reload，线上不带",
  '''import uvicorn
cfg = uvicorn.Config("main:app", host="127.0.0.1", port=8009, reload=False)
print("host =", cfg.host, "| port =", cfg.port, "| reload =", cfg.reload)
print("app  =", cfg.app)
print("（真启动的命令见卡片下方说明；别在脚本里 run —— 会占住终端）")''',
  where="你服务器上 8009 端口 + Docker 跑的就是它",
  extra="开发时：`uvicorn main:app --reload --port 8009`　｜　线上：`uvicorn main:app --host 0.0.0.0 --port 8009`（去掉 reload）",
  gotcha="⚠️ `uvicorn.run(...)` **会阻塞住当前进程**（一直跑服务器），所以它只该出现在"
         '`if __name__ == "__main__":` 里 —— 否则你 import 这个模块时测试就卡死了。'
         "线上要关掉 `reload`（它靠监控文件变化工作，占资源且不安全）")

E("fa.stream", "FastAPI", "阶段A", "流式返回：把模型的字一个个传给前端",
  "`StreamingResponse` + 生成器；配 `llm.stream` 就是「AI 边写边显示」",
  '''from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient
app = FastAPI()
def gen():
    for piece in ["数据", "库", "很", "有用"]:
        yield piece
@app.get("/chat")
def chat():
    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8")
r = TestClient(app).get("/chat")
print("状态码 =", r.status_code, "| Content-Type =", r.headers["content-type"])
print("拼起来 =", r.text)''',
  where="做 AI 聊天界面的必备件（否则用户要等整段生成完才看到字）",
  gotcha="**生成器里 `yield` 的是字符串/字节，不能 yield dict**。"
         "而且流式一开，就没法再改状态码了 —— 出错只能在流里发一个约定的错误标记")

E("sql.foreign_key", "SQL", "现在", "REFERENCES 外键：写了 ≠ 生效",
  "`sid INTEGER REFERENCES students(id)` 只是**声明**。SQLite 默认**不检查**它 —— 一个不存在的学生照样能选上课，而且**不报错**",
  '''import sqlite3, tempfile, os, shutil
d = tempfile.mkdtemp(); p = os.path.join(d, "t.db")
con = sqlite3.connect(p, isolation_level=None)     # 自动提交：避开"事务里设 pragma 会被忽略"那个坑
for ddl in ["CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT)",
            "INSERT INTO students VALUES (1,'韩立')",
            "CREATE TABLE courses (id INTEGER PRIMARY KEY, name TEXT)",
            "INSERT INTO courses VALUES (1,'数据库')",
            "CREATE TABLE enrollments (sid INTEGER NOT NULL REFERENCES students(id),"
            " cid INTEGER NOT NULL REFERENCES courses(id), PRIMARY KEY (sid, cid))"]:
    con.execute(ddl)

print("① 声明被记下来了吗 =", [(r[3], r[2], r[4]) for r in con.execute("PRAGMA foreign_key_list(enrollments)")])
print("② 默认开关 =", con.execute("PRAGMA foreign_keys").fetchone()[0], "（0 = 关）")
con.execute("INSERT INTO enrollments VALUES (999, 1)")
print("③ 插一个不存在的学生 999 → 进得去，库里 =", con.execute("SELECT * FROM enrollments").fetchall())

con.execute("DELETE FROM enrollments"); con.execute("PRAGMA foreign_keys = ON")
print("④ 打开开关后再插同一条 →", end=" ")
try:
    con.execute("INSERT INTO enrollments VALUES (999, 1)")
except Exception as e:
    print(type(e).__name__, ":", e)
con.close()
c2 = sqlite3.connect(p, isolation_level=None)
print("⑤ 新连接又回到 =", c2.execute("PRAGMA foreign_keys").fetchone()[0], "（每条连接各自，不写进文件）")
c2.close(); shutil.rmtree(d, ignore_errors=True)''',
  where="D8 建表直接用；你 `prescription_db.py` 里写的 FOREIGN KEY 也是同一条规则",
  gotcha="⚠️ **`PRAGMA foreign_keys = ON` 必须每次连上就设一遍** —— 它不写进文件、新连接回到 0。"
         "🔴 更阴的一条：**在未提交的事务里设它会被静默忽略**（读回来还是 0，不报错也不警告）→ "
         "要么 `isolation_level=None`（自动提交），要么先 `commit()` 再设。"
         "已经混进去的脏数据可以用 `PRAGMA foreign_key_check` 事后揪出来。"
         "另：同一条 `CREATE TABLE` 里的 `PRIMARY KEY (sid, cid)` **默认就生效** —— 一行管用一行不管",
  pre="")


# ══════════════════════════════════════════════════════════════════════
# 统计一下覆盖率（给学员看清「这套卡覆盖路线的哪几段」）
# ══════════════════════════════════════════════════════════════════════
def summary() -> dict:
    out: dict[str, int] = {}
    for c in CARDS_EXTRA:
        out[c["cat"]] = out.get(c["cat"], 0) + 1
    return out
