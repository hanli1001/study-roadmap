# -*- coding: utf-8 -*-
"""批改单证据：跑学员的 catch.py，把它的输出数出来。

为什么要有它（2026-10-09）：
    批改单里那个关键结论 —— 「他跑出来的 11,990 个文件条目里，98.1% 是该排除的」——
    第一次是我用一段**临时脚本**数出来的，随后就删了。那等于**结论留档、证据没留档**，
    下次有人问「98.1% 怎么来的」只能重写一遍。所以把它固化成可重跑的脚本。

用法：
    python -X utf8 tools/_analyze_catch_output.py
    python -X utf8 tools/_analyze_catch_output.py --dump   # 顺便把原始输出写到 E:\\Temp

只跑学员那个脚本的**只读部分**（os.walk + print）；它会顺带执行他文件里的
两行 os.makedirs(..., exist_ok=True) —— 目标已存在，是空操作，不会改任何东西。
"""
from __future__ import annotations

import collections
import os
import pathlib
import subprocess
import sys
import tempfile

TARGET = pathlib.Path(r"E:\ask-my-notes\rag\catch.py")   # 学员交件
CORPUS = r"E:\项目学习"                                    # 语料根（他自己写死在脚本里）
JUNK = {"_ref", ".git", ".idea", ".pytest_cache", ".playwright-mcp",
        ".claude", "__pycache__", "_备份", ".venv"}


def main() -> int:
    if not TARGET.exists():
        print(f"找不到交件：{TARGET}")
        return 2

    r = subprocess.run([sys.executable, "-X", "utf8", str(TARGET)],
                       capture_output=True, text=True, encoding="utf-8")
    lines = (r.stdout or "").split("\n")
    print(f"跑 {TARGET}")
    print(f"  exit = {r.returncode}")
    if r.stderr.strip():
        print(f"  stderr = {r.stderr.strip()[:300]}")
    if "--dump" in sys.argv:
        d = pathlib.Path(tempfile.gettempdir()) / "catch_out.txt"
        d.write_text(r.stdout or "", encoding="utf-8")
        print(f"  原始输出 → {d}")

    # 他的输出是 3 行一组：目录 / dirs / files
    files: list[str] = []
    roots = 0
    for i in range(0, len(lines) - 2, 3):
        head = lines[i]
        if not head.startswith(CORPUS):
            continue
        roots += 1
        try:
            fs = eval(lines[i + 2])          # noqa: S307 —— 自己脚本的输出，非外部输入
        except Exception:
            continue
        if isinstance(fs, list):
            files += [os.path.join(head, str(f)) for f in fs]

    tot = len(files)
    print(f"  总行数 {len(lines)} · 目录 {roots} · 文件条目 {tot}")
    if not tot:
        return 1

    c = collections.Counter()
    for p in files:
        c[os.path.relpath(p, CORPUS).split(os.sep)[0]] += 1

    print("\n--- 按顶层目录 ---")
    for k, v in c.most_common(8):
        flag = "  ← 该排除" if k in JUNK else ""
        print(f"  {k:<22} {v:>6}  {v/tot*100:5.1f}%{flag}")

    zhi = sum(v for k, v in c.items() if k in JUNK)
    print(f"\n⇒ 该排除的        {zhi} / {tot} = {zhi/tot*100:.1f}%")
    print(f"⇒ 他自己的内容    {tot-zhi} / {tot} = {(tot-zhi)/tot*100:.1f}%")

    e = collections.Counter(os.path.splitext(p)[1].lower() or "(无后缀)" for p in files)
    print("\n--- 按后缀 top 8 ---")
    for k, v in e.most_common(8):
        print(f"  {k:<14} {v:>6}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
