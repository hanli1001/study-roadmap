"""路径引用检查器：把工作区里所有"指向文件的引用"抠出来，逐个验证目标存在。

为什么需要它：这个工作区里到处是交叉引用（教案指向 `.py`、`改动路线.md` 指向产出文件、
HTML 互相 `<a href>`）。**整理目录时最大的风险不是搬错，是搬完之后没人发现哪条引用断了** ——
断掉的引用不会报错，只会让人以后点不开或找不到文件。

它同时能当"体检"用：任何时候跑一次，就知道有没有悬空引用。

用法：
    python tools/check_paths.py --save     # 存基线（整理目录**之前**先跑这个）
    python tools/check_paths.py            # 与基线比，只报**新增**的悬空引用（重点看这个）
    python tools/check_paths.py --list     # 连存量悬空也全列出来

⚠️ 为什么强调"差分"：基线里本来就有 89 条"悬空"，其中大半是误报 ——
   命令示例（`ls -l script.sh`）、网站名（`roadmap.sh`）、玩笑例子（`论文_最终版.docx`）、
   以及**要求学员在自己服务器上创建的**文件（`check_errors.sh`）。
   拿绝对值当门禁会一直红。**真正要盯的只有一件事：我搬完文件之后，有没有多出新的断链。**

判据（宁可漏报，不误报）：
    · .md   里 `反引号包起来的东西`、[文字](链接)、以及裸写的 xxx.md/xxx.py
    · .html 里 href="..." / src="..."
    · 目标能在**两种基准**下任一命中就算存在 —— ① 相对该文件所在目录 ② 相对工作区根目录
      （文档里既有 `导出/x.json` 这种相对根写法，也有 `../交互演示/y.js` 这种相对文件写法）
    · 跳过：外链、锚点、目录本身、明显是"示例/占位"的（含 `*`、`<`、`{`、`YYYY`、`xxx`）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Windows 控制台默认 GBK，打印 🔴/✅ 会 UnicodeEncodeError 直接崩（2026-10-02 实测踩到）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"_ref", ".git", "_备份", "__pycache__", ".idea", ".playwright-mcp",
             ".pytest_cache", ".ruff_cache", "node_modules"}
EXTS = "json|html|docx|yaml|jpeg|md|py|pdf|txt|js|css|db|ini|yml|png|jpg|csv|sh|sql"

# 引用形态
PAT_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
PAT_HTML_REF = re.compile(r'(?:href|src)="([^"#?]+)')
PAT_BARE = re.compile(rf"[\w\u4e00-\u9fff][\w\u4e00-\u9fff./\\-]*\.(?:{EXTS})(?![\w])")
# ⚠️ 首个字符类故意**不含 `-`**：允许连字符开头会把文件名尾部误当成路径
#    （实测：账本里 `诺奖与我的方向-2026-09-28.md` 被抠出 `-2026-10-02.md` 两条假断链）
# ⚠️ 2026-10-05 **去掉空格**：字符类里带空格会让它把**前面的词一起吃进去** ——
#    实测 `git add main.py`、`locate api.py` 这种"命令 + 文件名"整串被当成一条路径，
#    于是 60 条基线悬空里**有 15 条是这种假阳性**。本仓**没有任何带空格的文件名**，
#    所以那个空格从来没起过好作用，只在制造噪音并**掩盖真信号**。
#    去掉后同位置会从正确的词首重新匹配（`python tools/jd_stats.py` → `tools/jd_stats.py`）。
BAD_CHARS = set("*<>{}$|")


def files() -> list[Path]:
    out = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        if p.name.endswith((".bak",)) or ".bak-" in p.name:
            continue
        if p.suffix.lower() in (".md", ".html"):
            out.append(p)
    return sorted(out)


def strip_fences(txt: str) -> str:
    """把 markdown 的围栏代码块整段挖掉。

    为什么要挖：代码块里是**命令和示例**（`python tools/x.py`、`COPY requirements.txt`、
    `git add main.py`），它们长得像路径但根本不是路径引用 —— 不挖掉，
    检查器的输出会被这类噪声占满，真正断掉的引用反而看不见。
    """
    out, inside = [], False
    for line in txt.splitlines():
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


def refs_of(p: Path) -> set[str]:
    txt = p.read_text(encoding="utf-8", errors="replace")
    if p.suffix.lower() == ".md":
        txt = strip_fences(txt)
    found: set[str] = set()
    if p.suffix.lower() == ".html":
        found |= set(PAT_HTML_REF.findall(txt))
        # HTML 注释里的示例路径不算
    else:
        found |= set(PAT_MD_LINK.findall(txt))
        # 反引号里的路径
        # ⚠️ 2026-10-05：**含空格的一律不算路径**。本仓**没有任何带空格的文件名**，
        #    所以 `` `git add main.py` `` / `` `locate api.py` `` / `` `cargo` `` 这种
        #    "命令 + 文件名"整串被当成路径**必然是误报**。
        #    实测：60 条基线悬空里 **15 条**是它 —— 噪声大到会**掩盖真断链**。
        for span in re.findall(r"`([^`\n]+)`", txt):
            s = span.strip()
            if " " in s:
                continue
            if re.search(rf"\.(?:{EXTS})$", s) or re.search(rf"\.(?:{EXTS})[\s#]", s):
                found.add(s)
        found |= set(PAT_BARE.findall(txt))
    return found


def normalize(s: str) -> str | None:
    s = s.strip().strip("`").strip()
    if ".bak-" in s:                            # 备份件名（README.md.bak-20260928-x）
        return None                             # 真身是 .bak-…，会被截成 README.md 误报
    s = s.replace("\\", "/")                     # ⚠️ 归一化必须在下面这些判断**之前**
    if "_备份/" in s:                            # _备份/ 本就在 SKIP_DIRS 里，不该被检
        return None
    if not s or s.startswith(("http://", "https://", "www.", "mailto:", "data:", "#", "//")):
        return None
    if any(c in s for c in BAD_CHARS):          # 通配/占位/模板
        return None
    if "YYYY" in s or "xxx" in s.lower() or "待" in s:
        return None
    if re.match(r"^[A-Za-z]:\\?$", s):          # 光秃秃的盘符
        return None
    return s.replace("\\", "/")


def abs_win(rel: str) -> Path | None:
    """把 `E:/项目学习/x.py` 这种绝对路径还原成 Path（直接判存在，不走相对解析）。"""
    m = re.match(r"^([A-Za-z]):/(.*)$", rel)
    if not m:
        return None
    return Path(m.group(1) + ":/" + m.group(2))


def exists_anywhere(rel: str, from_file: Path) -> bool:
    win = abs_win(rel)
    if win is not None:
        return win.exists()
    cand = []
    c1 = (from_file.parent / rel)
    c2 = (ROOT / rel)
    c3 = (ROOT.parent / rel)          # 跨工作区写法：相对 E:\ 的 `项目学习/x.md`、`物联网/…`
    for c in (c1, c2, c3):
        try:
            c = c.resolve()
        except OSError:
            continue
        cand.append(c)
        if c.exists():
            return True
    # 只写了文件名（不含目录）→ 允许"全库找同名文件"，因为那是"提名字"不是"指路径"
    if "/" not in rel:
        return any(p.name == rel for p in ROOT.rglob(rel) if p.is_file())
    # ⚠️ 带目录的引用**不再兜底**：它明确指了位置，位置错了就是断了。
    #    （这条是本工具的命门：兜底太宽会把"搬断的引用"也判成通过。）
    return False


BASELINE = Path(__file__).with_name("_paths_baseline.json")


def main() -> int:
    show_all = "--list" in sys.argv
    save = "--save" in sys.argv
    total = 0
    dangling: list[tuple[Path, str]] = []
    for p in files():
        for r in sorted(refs_of(p)):
            n = normalize(r)
            if n is None:
                continue
            total += 1
            if not exists_anywhere(n, p):
                dangling.append((p.relative_to(ROOT), n))

    by_file: dict[str, list[str]] = {}
    for f, r in dangling:
        by_file.setdefault(str(f), []).append(r)

    import json
    # ⚠️ 键用**文件名（不含目录）**，不用相对路径 ——
    #    2026-09-28 踩过：整理目录后所有被搬文件的历史误报都换了前缀，
    #    于是 26 条"新增"里 25 条是假的，真问题（1 条绝对路径没改到）差点被淹掉。
    now = {"total": total,
           "dangling": sorted(f"{Path(f).name}|{r}" for f, r in dangling)}
    if save:
        BASELINE.write_text(json.dumps(now, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"已存基线 → {BASELINE.name}（检查 {total} 条，悬空 {len(now['dangling'])} 条）")
        return 0
    if BASELINE.exists():
        old = set(json.loads(BASELINE.read_text(encoding="utf-8"))["dangling"])
        added = sorted(set(now["dangling"]) - old)
        gone = sorted(old - set(now["dangling"]))
        print(f"与基线比：悬空 {len(old)} → {len(now['dangling'])}")
        print(f"  🔴 新增 {len(added)} 条" + ("（这就是被搬断的引用）" if added else " —— 一条都没断 ✅"))
        for a in added:
            f, r = a.split("|", 1)
            print(f"      ✗ {f}  →  {r}")
        if gone:
            print(f"  🟢 修好/消失 {len(gone)} 条")
        if show_all:
            print("")
            print("全部存量悬空：")
            for f in sorted(by_file):
                print(f"  {f}")
                for r in sorted(set(by_file[f])):
                    print(f"      ✗ {r}")
        return 1 if added else 0

    print(f"扫了 {len(files())} 个文件（.md/.html），检查引用 {total} 条")
    print(f"悬空引用：{len(dangling)} 条，分布在 {len(by_file)} 个文件里\n")
    if show_all:
        for f in sorted(by_file):
            print(f"  {f}")
            for r in sorted(set(by_file[f])):
                print(f"      ✗ {r}")
    else:
        for f in sorted(by_file)[:15]:
            print(f"  {f}")
            for r in sorted(set(by_file[f]))[:6]:
                print(f"      ✗ {r}")
        if len(by_file) > 15:
            print(f"  …… 还有 {len(by_file) - 15} 个文件（加 --list 看全）")
    return 1 if dangling else 0


if __name__ == "__main__":
    sys.exit(main())
