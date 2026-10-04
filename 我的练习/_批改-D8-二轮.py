# -*- coding: utf-8 -*-
"""D8 作业 · 第二轮复查（2026-10-05）

跑法：python -X utf8 我的练习/_批改-D8-二轮.py
只读 + 一次性内存库，不动你的 D8.db。
"""
import io, os, re, sqlite3, subprocess, sys, contextlib, pathlib

HERE = pathlib.Path(__file__).resolve().parent
HW = HERE / "D8作业.py"


def hr(t):
    print("\n" + "=" * 70)
    print(t)
    print("=" * 70)


# ─────────────────────────────────────────────── 0
hr("0. 原样跑你的脚本（而且是从别的目录跑的）")
r = subprocess.run([sys.executable, "-X", "utf8", str(HW)],
                   capture_output=True, text=True, encoding="utf-8",
                   errors="replace", cwd=os.path.expanduser("~"))
print("退出码 =", r.returncode, "（0 = 跑通了，没有异常）")
print("标准错误输出：", repr(r.stderr.strip()) or "（空）")
print("最后一行输出 =", r.stdout.strip().splitlines()[-1])


# ─────────────────────────────────────────────── 1
hr("1. 直接查你的 D8.db：三张表长什么样、各几行")
c = sqlite3.connect(HERE / "D8.db")
for name, sql in c.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
    print("---", name)
    print(re.sub(r"\s+", " ", sql))
print()
for t in ("students", "course", "student_course"):
    print(f"  {t:16s} {c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:3d} 行")
print()
print("外键声明（PRAGMA foreign_key_list）：", c.execute("PRAGMA foreign_key_list(student_course)").fetchall() or "【一条都没有】")
print("外键开关（PRAGMA foreign_keys）   ：", c.execute("PRAGMA foreign_keys").fetchone()[0], "（0 = 关）")


# ─────────────────────────────────────────────── 2
hr("2. 独立核对：不看你的 SQL，从 link() 的参数手算出应有的 15 条关系")
pairs = [("张三", ["语文", "数学", "英语"]), ("李四", ["语文", "数学", "物理"]),
         ("牛二", ["数学", "物理", "化学"]), ("李三", ["数学", "生物", "化学"]),
         ("张贾瑞", ["语文", "数学", "化学"])]
sid = {n: i for i, (n, _) in enumerate([("张三", 0), ("李四", 0), ("牛二", 0), ("李三", 0), ("张贾瑞", 0)], 1)}
cid = {n: i for i, n in enumerate(["语文", "数学", "英语", "物理", "化学", "生物"], 1)}
want = sorted((cid[cn], sid[sn]) for sn, cns in pairs for cn in cns)
got = sorted(c.execute("SELECT course_id, student_id FROM student_course").fetchall())
print("手算应有：", len(want), "条")
print("库里实有：", len(got), "条")
print("完全一致：", want == got)
if want != got:
    print("  只在应有里的：", [p for p in want if p not in got])
    print("  只在库里的  ：", [p for p in got if p not in want])

hr("2b. 逐行核对 JOIN 结果（他的 SQL，WHERE c.name = \"数学\"）")
q = '''SELECT c.name, s.name, s.class_name FROM course c
       JOIN student_course s_c ON c.id = s_c.course_id
       JOIN students s ON s_c.student_id = s.id
       WHERE c.name = "数学"'''
rows = c.execute(q).fetchall()
true_cls = dict(pairs) and {n: cl for n, cl in [("张三", "高一"), ("李四", "高三"), ("牛二", "高三"), ("李三", "高一"), ("张贾瑞", "高二")]}
print(f"{'课程':6s}{'学生':8s}{'JOIN 给的班级':14s}{'名册里的班级':12s}一致?")
for cn, sn, cl in rows:
    ok = "✅" if true_cls[sn] == cl else "❌"
    print(f"{cn:6s}{sn:8s}{cl:14s}{true_cls[sn]:12s}{ok}")
print(f"\n共 {len(rows)} 行，全部与名册一致：", all(true_cls[sn] == cl for _, sn, cl in rows))
print("（对比第一轮：那时 class_name 是抄进绳子表的，改一次名册就对不上；现在它是 JOIN 出来的）")


# ─────────────────────────────────────────────── 3
hr("3. 顺手发现：WHERE c.name = \"数学\" 用的是双引号")
m = sqlite3.connect(":memory:")
m.execute("CREATE TABLE course(id INTEGER PRIMARY KEY, name TEXT)")
m.execute("INSERT INTO course VALUES (1,'数学'),(2,'语文')")
print("A) 表里没有叫 数学 的列 —— 现在能跑：")
print("   ", m.execute('SELECT * FROM course WHERE name = "数学"').fetchall())
m.execute('ALTER TABLE course ADD COLUMN "数学" INTEGER DEFAULT 0')
m.execute('UPDATE course SET "数学" = 9 WHERE id = 2')
print("B) 只要有人加了一列真的叫 数学 —— 同一条 SQL：")
print("   ", m.execute('SELECT * FROM course WHERE name = "数学"').fetchall(), " ← 变成空结果，而且不报错")
print("   原因：SQLite 优先把 \"...\" 当**列名**；找不到同名列才退化成字符串（历史兼容行为）")
print()
print("   正确：单引号 ", m.execute("SELECT * FROM course WHERE name = '数学'").fetchall())
print("   更好：占位符 ", m.execute("SELECT * FROM course WHERE name = ?", ("数学",)).fetchall())


# ─────────────────────────────────────────────── 4
hr("4. 把外键那两条加回去，会不会弄坏你现在的脚本？")
src = HW.read_text(encoding="utf-8")
src = src.replace('Path(__file__).with_name("D8.db")', '":memory:"')
before = src
src = src.replace("""CREATE TABLE student_course(
course_id INTEGER,
student_id INTEGER,
primary key (course_id, student_id))""",
                  """CREATE TABLE student_course(
course_id INTEGER NOT NULL REFERENCES course(id),
student_id INTEGER NOT NULL REFERENCES students(id),
primary key (course_id, student_id))""")
print("改到建表语句：", "成功" if src != before else "❌ 没匹配上（作业改过了？）")
if src != before:
    src = re.sub(r"(cur = conn\.cursor\(\))", r"\1\ncur.execute('PRAGMA foreign_keys = ON')", src)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(src, "with_fk", "exec"), {"__name__": "__main__"})
    out = [l for l in buf.getvalue().strip().splitlines() if l.strip()]
    print("加约束后跑出来的最后一行：")
    print("   ", out[-1])
    print("=> 跟你现在的结果一模一样 ⇒ 加约束不用改你任何数据")
print()
n = sqlite3.connect(":memory:"); n.execute("PRAGMA foreign_keys = ON")
n.execute("CREATE TABLE course(id INTEGER PRIMARY KEY)")
n.execute("CREATE TABLE sc(course_id INTEGER NOT NULL REFERENCES course(id))")
n.execute("INSERT INTO course VALUES (1)")
n.execute("INSERT INTO sc VALUES (1)")
print("外键开着时：插 course_id=1（存在）  -> 成功")
try:
    n.execute("INSERT INTO sc VALUES (99)")
    print("外键开着时：插 course_id=99（不存在）-> 成功（不该）")
except Exception as e:
    print("外键开着时：插 course_id=99（不存在）->", type(e).__name__, "->", e)


# ─────────────────────────────────────────────── 5
hr("5. 自查清单第 2 题要的两个数")
qw = '''SELECT c.name, s.name, s.class_name FROM course c
        JOIN student_course s_c ON c.id = s_c.course_id
        JOIN students s ON s_c.student_id = s.id'''
print("绳子表 student_course 行数        =", c.execute("SELECT COUNT(*) FROM student_course").fetchone()[0])
print("同一条 JOIN 不加 WHERE 跑出来      =", len(c.execute(qw).fetchall()), "行")
print("加 WHERE c.name=\"数学\" 之后         =", len(rows), "行")
print("=> 两数相等，说明这一轮**没有配不上的行**（第一轮是 5 → 4，少一行）")
c.close()
