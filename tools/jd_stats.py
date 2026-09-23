"""JD 统计器 · 把 `职业探索/JD-20条.md` 里手抄的岗位数据算成结论

用法：
    python tools/jd_stats.py                    # 统计 职业探索/JD-20条.md
    python tools/jd_stats.py 某个文件.md         # 统计别的文件（留作测试用）

它算什么：
    ① 学历要求分布（本科 / 硕士 / 不限）—— 直接回答"本科够不够得着"
    ② 经验要求分布（应届可投几条）—— **最重要的一列**，很多岗位名不是校招入口
    ③ 技能关键词 Top 15 —— 市场要什么，一目了然
    ④ 薪资区间（只统计能解析成数字的）
    ⑤ 城市 / 领域分布 —— 验证"合肥地利"是否成立

设计原则（别改）：
    · **只读不写**：绝不修改你的原始表格，错了也是你自己回去改
    · **空白单独统计**：留空的格子算"没写"，不算"不限"—— 别让猜测污染数据
    · **不猜**：解析不出来的就跳过并如实报告跳过了几条
"""
import re
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else (ROOT / "职业探索" / "JD-20条.md")

# 表头顺序（要和 md 里的表一致）
COLS = ["序号", "领域", "公司", "岗位名", "学历要求", "经验要求",
        "技能关键词", "薪资", "城市", "链接", "抓取日期"]


def parse_rows(text):
    """从 markdown 里抽出数据行。

    只认「第一格是 1~200 的整数」的行 —— 这样能自动跳过表头、分隔线、
    以及文档里那张「示例」表（它的序号写的是"示例"）。
    ⚠️ 别把上界写死成 20：表里超过 20 行时，超出的会被静默丢掉（我踩过这个坑）。
    """
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 8:
            continue
        first = cells[0]
        if not first.isdigit():
            continue
        if not (1 <= int(first) <= 200):
            continue
        rows.append(cells)
    return rows


def norm_edu(s):
    if not s:
        return None
    if "不限" in s or "无要求" in s:
        return "不限"
    for k in ("博士", "硕士", "本科", "大专", "专科"):
        if k in s:
            return k
    return f"其他（{s[:8]}）"


def norm_exp(s):
    if not s:
        return None
    if "应届" in s or "在校" in s or "实习" in s or "无经验" in s or "经验不限" in s:
        return "应届/在校可投"
    if "不限" in s:
        return "不限"
    # 抓 "1-3年" / "3年以上" 这类
    m = re.search(r"(\d+)\s*[-~到]\s*(\d+)", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}年"
    m = re.search(r"(\d+)\s*年", s)
    if m:
        n = int(m.group(1))
        return "1-3年" if n <= 3 else ("3-5年" if n <= 5 else "5年以上")
    return f"其他（{s[:8]}）"


SKILL_SPLIT = re.compile(r"[、,，;；/／|]|\s{2,}")
# 太笼统的词不算"技能"，单列出来
VAGUE = {"python", "java", "c++", "计算机相关专业", "本科及以上", "良好的沟通能力",
         "团队合作", "学习能力强", "责任心强", "人工智能", "大模型", "ai"}


def split_skills(s):
    if not s:
        return []
    parts = [p.strip(" ·•-—()（）") for p in SKILL_SPLIT.split(s)]
    out = []
    for p in parts:
        p = p.strip()
        if len(p) < 2 or len(p) > 24:
            continue
        if p.isdigit():
            continue
        out.append(p)
    return out


def parse_salary(s):
    """把 '15-25K·14薪' / '20k-35k' / '1.5-2.5万' 解析成 (低, 高)，单位 K（千元/月）。"""
    if not s:
        return None
    t = s.lower().replace(" ", "")
    rng = re.search(r"(\d+(?:\.\d+)?)\s*[-~到]\s*(\d+(?:\.\d+)?)", t)
    unit_wan = "万" in t
    try:
        if rng:
            lo, hi = float(rng.group(1)), float(rng.group(2))
        else:
            one = re.search(r"(\d+(?:\.\d+)?)", t)
            if not one:
                return None
            lo = hi = float(one.group(1))
    except ValueError:
        return None
    if unit_wan:
        lo, hi = lo * 10, hi * 10          # 万 → K
    if lo > 1000:                           # 明显是年薪（如 200000）
        lo, hi = lo / 12 / 1000, hi / 12 / 1000
    return (lo, hi)


def bar(n, total, width=22):
    if total <= 0:
        return ""
    filled = round(n / total * width)
    return "█" * filled + "░" * (width - filled)


def main():
    if not SRC.exists():
        raise SystemExit(f"找不到 {SRC} —— 先把采集表建起来。")

    text = SRC.read_text(encoding="utf-8")
    rows = parse_rows(text)

    print("=" * 68)
    print("JD 统计报告")
    print("=" * 68)

    if not rows:
        print("\n⚠️ 表格里还没有数据（序号 1~20 的行都是空的）。")
        print("   先把 `职业探索/JD-20条.md` 第三节的表填几行，再跑这个脚本。")
        return

    n = len(rows)
    filled_rows = sum(1 for r in rows if len(r) > 2 and r[2])   # 「公司」有值才算真填了
    print(f"\n表里有 {n} 行，其中**真正填了内容的 {filled_rows} 条**（目标 20 条）")
    if filled_rows == 0:
        print("\n⚠️ 一条都还没填 —— 下面全是空的，别看了。")
        print("   去 `职业探索/JD-20条.md` 第三节把表填上，再回来跑这个脚本。")
        return

    # 每列非空统计
    print("\n── 填写完整度 ──")
    for i, name in enumerate(COLS):
        filled = sum(1 for r in rows if i < len(r) and r[i])
        flag = "" if filled == n else f"   ← 缺 {n - filled} 条"
        print(f"  {name:<8} {filled}/{n}{flag}")

    # ── ① 学历 ──
    print("\n── ① 学历要求 ──")
    edus = Counter(norm_edu(r[4]) for r in rows if len(r) > 4)
    edus.pop(None, None)
    if not edus:
        print("  （这一列还全是空的）")
    for k, v in edus.most_common():
        print(f"  {k:<12} {v:>2} 条  {bar(v, n)}")

    # ── ② 经验 ──
    print("\n── ② 经验要求（这一列最重要）──")
    exps = Counter(norm_exp(r[5]) for r in rows if len(r) > 5)
    exps.pop(None, None)
    if not exps:
        print("  （这一列还全是空的）")
    for k, v in exps.most_common():
        print(f"  {k:<14} {v:>2} 条  {bar(v, n)}")
    fresh = sum(v for k, v in exps.items() if "应届" in k or k == "不限")
    if exps:
        pct = fresh / sum(exps.values()) * 100
        print(f"\n  → 应届/不限可投：{fresh}/{sum(exps.values())} = {pct:.0f}%")
        if pct < 40:
            print("  ⚠️ 低 —— 说明这些岗位名**不是你的校招入口**，要换关键词重搜。")
        elif pct >= 70:
            print("  ✅ 高 —— 这些岗位名对本科应届是开放的。")

    # ── ③ 技能 ──
    print("\n── ③ 技能关键词 Top 15 ──")
    skills = Counter()
    generic = Counter()
    for r in rows:
        if len(r) > 6:
            for s in split_skills(r[6]):
                if s.lower() in VAGUE:
                    generic[s] += 1          # 不丢，单独记：静默过滤等于骗人
                else:
                    skills[s] += 1
    if not skills:
        print("  （技能列还全是空的）")
    top = skills.most_common(15)
    for k, v in top:
        print(f"  {k:<26} {v:>2} 次  {bar(v, n)}")
    if generic:
        # 这些词太笼统，算出来会误导（人人都写），但必须让你看见被排除了什么
        g = "、".join(f"{k}×{v}" for k, v in generic.most_common())
        print(f"\n  ⓘ 已排除的通用词（不是没统计，是不值得当结论）：{g}")

    # ── ④ 薪资 ──
    print("\n── ④ 薪资（只统计能解析成数字的）──")
    lows, highs, used, skipped = [], [], 0, 0
    per_day = 0
    for r in rows:
        if len(r) > 7 and r[7]:
            if "/天" in r[7] or "／天" in r[7]:
                per_day += 1
            p = parse_salary(r[7])
            if p:
                lows.append(p[0]); highs.append(p[1]); used += 1
            else:
                skipped += 1
    if used:
        lows.sort(); highs.sort()
        mid = lambda a: a[len(a) // 2]
        # 实习按「元/天」计，全职按「K/月」计 —— 两种不能混着比
        unit = "元/天（实习日薪）" if per_day > used / 2 else "K/月"
        print(f"  解析成功 {used} 条，跳过 {skipped} 条（格式不认识，如实报告不猜）")
        print(f"  单位判定：{unit}   ← 按 '含 /天 的条数 > 一半' 判的")
        print(f"  区间中位：{mid(lows):.1f} ~ {mid(highs):.1f}")
        print(f"  最低：{lows[0]:.1f} 起   最高：{highs[-1]:.1f} 止")
        if "元/天" in unit:
            print("  ⚠️ 日薪不能直接当能力差距看 —— 差 2 倍往往只是「本科岗 vs 硕士岗」的差别。")
            print("     把学历列和薪资列对着读，比只看薪资有用。")
    else:
        print("  （薪资列还全是空的，或格式都认不出来）")

    # ── ⑤ 城市 / 领域 ──
    print("\n── ⑤ 城市分布 ──")
    cities = Counter(r[8] for r in rows if len(r) > 8 and r[8])
    for k, v in cities.most_common():
        print(f"  {k:<10} {v:>2} 条  {bar(v, n)}")

    print("\n── ⑥ 领域分布 ──")
    doms = Counter(r[1] for r in rows if len(r) > 1 and r[1])
    for k, v in doms.most_common():
        print(f"  {k:<10} {v:>2} 条  {bar(v, n)}")

    # ── 收尾 ──
    print("\n" + "=" * 68)
    print("下一步（L4 验收）：用一句话回答")
    print("=" * 68)
    print("  「市场要的是 ______，我现在会的是 ______，差在 ______。」")
    print()
    if n < 20:
        print(f"  ⚠️ 还差 {20 - n} 条才到 L3。数据太少时上面的百分比不可靠。")
    print("  这句话写不出来 = 这 20 条白抄了。")


if __name__ == "__main__":
    main()
