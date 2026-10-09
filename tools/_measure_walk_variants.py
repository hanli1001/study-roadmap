# -*- coding: utf-8 -*-
"""变式题的实测答案：同一棵目录树，三种走法的代价各是多少。"""
import os

ROOT = r"E:\项目学习"
PRUNE = {".git", "_ref", "_备份", "__pycache__", ".pytest_cache", ".idea", ".venv"}


def walk(prune, collect_txt=False):
    dirs_n = files_n = txt_n = chars = 0
    biggest = (0, "")
    for root, dirs, files in os.walk(ROOT):
        if prune:
            dirs[:] = [d for d in dirs if d not in PRUNE]
        dirs_n += 1
        for f in files:
            files_n += 1
            if collect_txt:
                p = os.path.join(root, f)
                try:
                    t = open(p, encoding="utf-8").read()
                except (UnicodeDecodeError, OSError):
                    continue
                txt_n += 1
                chars += len(t)
                if len(t) > biggest[0]:
                    biggest = (len(t), os.path.relpath(p, ROOT))
    return dirs_n, files_n, txt_n, chars, biggest


print("=== 走法 A：GPT 教你的那版（什么都不剪）===")
a = walk(False)
print(f"  遍历到的目录 {a[0]}")
print(f"  文件条目     {a[1]}")

print()
print("=== 走法 B：只加一行 dirs[:] = [...] ===")
b = walk(True)
print(f"  遍历到的目录 {b[0]}")
print(f"  文件条目     {b[1]}")

print()
print("=== 走法 C：B + 只统计能按 utf-8 读出来的文本 ===")
c = walk(True, collect_txt=True)
print(f"  能当语料的文本文件 {c[2]}")
print(f"  总字数             {c[3]:,}")
print(f"  最大的一个         {c[4][0]:,} 字  {c[4][1]}")

print()
print(f"⇒ A → B：文件条目 {a[1]} → {b[1]}（{(1-b[1]/a[1])*100:.1f}% 被剪掉）")
print(f"⇒ B → C：能读的只占 {(c[2]/b[1])*100:.1f}%（其余是二进制 / 编码不对）")
print(f"⇒ A → C：{a[1]} → {c[2]}，差 {a[1]/c[2]:.0f} 倍")

print()
print("=== 那 83 个「读不动」的到底是什么 ===")
import collections
bad = collections.Counter()
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in PRUNE]
    for f in files:
        p = os.path.join(root, f)
        try:
            open(p, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError) as e:
            bad[(os.path.splitext(f)[1].lower() or "(无后缀)", type(e).__name__)] += 1
for (ext, err), n in bad.most_common():
    print(f"  {ext:<10} {err:<20} {n}")
print(f"  合计 {sum(bad.values())}")
