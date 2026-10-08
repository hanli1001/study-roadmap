# -*- coding: utf-8 -*-
"""量 E:\\项目学习 的语料分布（教练侧自用，不进教材）。
排除：_ref/ 教材、.git、_备份/、__pycache__、.pytest_cache、.idea
"""
import os
import statistics
from datetime import date

ROOT = r"E:\项目学习"
EXCL_DIRS = {"_ref", ".git", "_备份", "__pycache__", ".pytest_cache", ".idea",
             ".playwright-mcp", ".claude"}

rows = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in EXCL_DIRS]
    for fn in filenames:
        p = os.path.join(dirpath, fn)
        try:
            with open(p, "r", encoding="utf-8") as f:
                n = len(f.read())
        except (UnicodeDecodeError, OSError):
            continue
        rows.append((n, os.path.relpath(p, ROOT)))

rows.sort(reverse=True)
chars = [n for n, _ in rows]
total = sum(chars)

print(f"文件数 = {len(rows)}   总字数 = {total:,}")
print(f"最大 = {chars[0]:,}  最小 = {chars[-1]:,}  中位数 = {statistics.median(chars):,.0f}  均值 = {total//len(rows):,}")
print()
print("—— 最大的 8 个 ——")
for n, r in rows[:8]:
    print(f"  {n:>7,}  {r}")
print()
print("—— 分布 ——")
for lo, hi in [(0, 2000), (2000, 5000), (5000, 20000), (20000, 50000), (50000, 10**9)]:
    c = [n for n in chars if lo <= n < hi]
    print(f"  {lo:>6,}–{hi if hi < 10**9 else '∞':>7} 字：{len(c):>3} 个   合计 {sum(c):>9,} 字  "
          f"占比 {sum(c)/total*100:5.1f}%")
print()
print("—— 所有文件 > 20000 字的 ——")
for n, r in rows:
    if n > 20000:
        print(f"  {n:>7,}  {r}")

print()
print("—— 倒推锚点（基准 2026-10-08）——")
today = date(2026, 10, 8)
for label, target in [("2027.03.01 简历必须有东西", date(2027, 3, 1)),
                      ("2028.03.01 考研/就业决策", date(2028, 3, 1)),
                      ("2029.06.30 毕业入职", date(2029, 6, 30))]:
    d = (target - today).days
    print(f"  {label}：{d} 天 = {d/7:.1f} 周")
