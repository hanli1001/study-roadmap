"""一次性：整理工作区目录（2026-09-28）。

学员要求：「整理项目文件目录，现在看着太乱了」。实测根目录 **78 个条目**，其中 18 个是
`*.bak-*` 备份（gitignore 的，纯噪音）、15 个是他 7 月写的 FastAPI 练习、14 个是历次课的材料。

设计原则（为什么这么分）：
    · **天天要用的放根目录，不埋深**：`改动路线 / 教学进度看板 / 时间线账本 / 每周目标 /
      PRODUCT / learning-roadmap` 留在根 —— 埋进子目录只会让他多两次点击，那不叫整理。
    · **按"这是什么"分，不按时间分**：`课程/`（历次课的教案与课堂记录）、
      `我的练习/`（他自己写的代码与笔记）、`职业探索/`（已有的职业调研文件夹，把两份调研并进去）。
    · **`_备份/` 收所有 `.bak-*`**；缓存目录直接删（能重新生成）。
    · 已经成型的 `交互演示 / 每周书 / 打印资料 / 周目标存档 / tools / rag / Linux / 样例代码库`
      **一律不动** —— 它们内部有大量相对链接，搬了只赔不赚。

搬完必须证明「没搬断引用」：靠 `tools/check_paths.py` 的差分
（搬之前 `--save` 存基线，搬完比对，**新增悬空必须为 0**）。

用法：python tools/_reorg_once.py          # 真搬
      python tools/_reorg_once.py --dry    # 只看要动什么
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MOVES: dict[str, list[str]] = {
    "课程": [
        "第1课-装好Python写下第一行程序.md",
        "第3课-数据模型与JOIN.md",
        "第3课-微信群演示.py",
        "第3课-实跑输出-20260923.txt",
        "第4课-函数与参数.md",
        "语言速查-第0课.md",
        "教案SQL校验-20260920.txt",
        "JOIN诊断-校验-20260920.txt",
        "演示脚本-实跑输出-20260920.txt",
        "分组统计-校验.txt",
        "唤醒.py",
        "算法.py",
        "teaching-methodology.md",
        "teaching-methodology-v3-交互式微课.md",
    ],
    "我的练习": [
        "api.py", "delete.py", "oop-basics.py", "prescription_db.py", "prescriptions.db",
        "test_api.py", "test_api_v2.py", "conftest.py", "pytest.ini",
        "Dockerfile", "requirements.txt",
        "sql-notes.md", "fastapi-notes.md", "docker-notes.md", "learning-note.md",
    ],
    "职业探索": [
        "政策与趋势-20260921.md",
        "职业方向评估-20260921.md",
    ],
}

DEL_DIRS = ["__pycache__", ".pytest_cache", ".ruff_cache"]
# 记录用：搬完后要把引用改成这些新位置
REWRITE_SUFFIX = {".md", ".py", ".ini", ".txt", ".yml", ".yaml", ".json"}


def move(src: Path, dst: Path, dry: bool) -> str:
    """搬一个文件。⚠️ 2026-09-28 踩过的坑：这个函数一开始只把 `shutil.move` 用 dry 挡住了，
    **`git mv` 照样执行** —— 于是"试运行"真的搬了文件（结果：职业探索/ 那 2 个文件被搬走）。
    dry 必须挡住**每一个**副作用，不能只挡一半。"""
    if dry:
        return "试运行"
    r = subprocess.run(["git", "mv", str(src), str(dst)], cwd=ROOT,
                       capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode == 0:
        return "git mv"
    shutil.move(str(src), str(dst))             # 未跟踪的文件 git mv 会失败
    return "mv(未跟踪)"


def main() -> int:
    dry = "--dry" in sys.argv
    log: list[str] = []

    # ── ① 建目录 + 搬文件（同目录内成对搬，保持相对关系）
    for folder, names in MOVES.items():
        d = ROOT / folder
        if not dry:
            d.mkdir(exist_ok=True)
        for n in names:
            src = ROOT / n
            if not src.exists():
                log.append(f"  [跳过] {n} 不存在")
                continue
            log.append(f"  [{move(src, d / n, dry)}] {n}  →  {folder}/")
            if dry:
                continue

    # ── ② 所有 .bak-* 收进 _备份/
    baks = sorted(p for p in ROOT.glob("*.bak-*") if p.is_file())
    baks += sorted(p for p in ROOT.glob("*.bak") if p.is_file())
    if not dry:
        (ROOT / "_备份").mkdir(exist_ok=True)
    for b in baks:
        log.append(f"  [mv] {b.name}  →  _备份/")
        if not dry:
            shutil.move(str(b), str(ROOT / "_备份" / b.name))

    # ── ③ 删缓存目录（能重新生成）
    for c in DEL_DIRS:
        if (ROOT / c).exists():
            log.append(f"  [rm -r] {c}/（缓存，会重新生成）")
            if not dry:
                shutil.rmtree(ROOT / c, ignore_errors=True)

    print(f"{'（试运行）' if dry else ''}共 {len(log)} 个动作：")
    print("\n".join(log))

    if dry:
        return 0

    # ── ④ 改引用：把"旧写法"换成"从引用者自己的新位置算出来的相对路径"
    #    注意：**被搬动的文件自己也要改** —— 例如 课程/第3课-数据模型与JOIN.md 里
    #    原来裸写 `../我的练习/prescriptions.db`（当时都在根目录），搬完必须变成 `../我的练习/prescriptions.db`。
    newdir = {n: f for f, names in MOVES.items() for n in names}
    edited: dict[str, int] = {}
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in REWRITE_SUFFIX:
            continue
        if any(part in {"_ref", ".git", "_备份", "__pycache__", ".idea",
                        ".playwright-mcp"} for part in p.relative_to(ROOT).parts):
            continue
        if p.name in newdir and p.parent != ROOT / newdir[p.name]:
            continue                              # 理论上不会发生，保险
        txt = p.read_text(encoding="utf-8", errors="replace")
        orig, hits = txt, 0
        for n, folder in newdir.items():
            if n == p.name and p.parent.name == folder:
                continue                          # 自己引用自己，不用改
            new_rel = os.path.relpath(ROOT / folder / n, p.parent).replace("\\", "/")
            if new_rel == n:
                continue
            esc = re.escape(n)
            for pat, rep in ((rf"`{esc}`", f"`{new_rel}`"),
                             (rf"\]\({esc}\)", f"]({new_rel})")):
                txt, k = re.subn(pat, rep, txt)
                hits += k
            for old in (f"项目学习\\{n}", f"项目学习/{n}"):
                if old in txt:
                    k = txt.count(old)
                    txt = txt.replace(old, old.replace(n, f"{folder}/{n}"))
                    hits += k
        if txt != orig:
            p.write_text(txt, encoding="utf-8")
            edited[str(p.relative_to(ROOT))] = hits
    print(f"\n改了引用的文件：{len(edited)} 个（共 {sum(edited.values())} 处）")
    for f in sorted(edited):
        print(f"  · {f}  ({edited[f]} 处)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
