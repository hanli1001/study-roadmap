# -*- coding: utf-8 -*-
"""D8 作业 · 第三轮复查（2026-10-05）—— 只查一件事：外键到底生效了没有。

跑法：python -X utf8 我的练习/_批改-D8-三轮.py
只读 + 内存库，不动你的 D8.db。
"""
import io, os, re, sqlite3, subprocess, sys, contextlib, pathlib

HERE = pathlib.Path(__file__).resolve().parent
HW = HERE / "D8作业.py"


def hr(t):
    print("\n" + "=" * 70)
    print(t)
    print("=" * 70)


STUDENTS = [('张三', '高一'), ('李四', '高三'), ('牛二', '高三'), ('李三', '高一'), ('张贾瑞', '高二')]
COURSES = [('语文',), ('数学',), ('英语',), ('物理',), ('化学',), ('生物',)]
DDL_SC = """CREATE TABLE student_course(
course_id INTEGER  NOT NULL REFERENCES course(id),
student_id INTEGER  NOT NULL REFERENCES students(id),
primary key (course_id, student_id))"""


def build(pragma_when, con):
    """pragma_when: 'none' | 'after_connect' | 'in_loop'（复刻作业里的位置）"""
    cur = con.cursor()
    if pragma_when == "after_connect":
        print("   [记录] 执行这行 PRAGMA 的瞬间：conn.in_transaction =", con.in_transaction)
        cur.execute("PRAGMA foreign_keys = ON")
    cur.execute("CREATE TABLE students(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name TEXT NOT NULL, class_name TEXT NOT NULL)")
    cur.execute("CREATE TABLE course(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name TEXT NOT NULL)")
    cur.execute(DDL_SC)
    cur.executemany("INSERT INTO students(name,class_name) VALUES (?,?)", STUDENTS)
    cur.executemany("INSERT INTO course(name) VALUES (?)", COURSES)
    return cur


# ─────────────────────────────────────────────── 0
hr("0. 原样跑你的脚本")
r = subprocess.run([sys.executable, "-X", "utf8", str(HW)], capture_output=True,
                   text=True, encoding="utf-8", errors="replace", cwd=os.path.expanduser("~"))
print("退出码 =", r.returncode, "｜ stderr =", repr(r.stderr.strip()) or "（空）")
print("最后一行 =", r.stdout.strip().splitlines()[-1][:90], "...")


# ─────────────────────────────────────────────── 1
hr("1. D8.db 里现在有什么约束（外键声明落盘了吗）")
c = sqlite3.connect(HERE / "D8.db")
print("foreign_key_list(student_course)：")
for row in c.execute("PRAGMA foreign_key_list(student_course)"):
    print("   ", row)
print("当前连接 foreign_keys =", c.execute("PRAGMA foreign_keys").fetchone()[0], "（0=关，这是每个连接各自的开关，不写进文件）")
print()
print("外键开着时查违规行 PRAGMA foreign_key_check：", end=" ")
c.execute("PRAGMA foreign_keys = ON")
print(c.execute("PRAGMA foreign_key_check").fetchall() or "[] —— 现有 15 行数据全部合规")
c.close()


# ─────────────────────────────────────────────── 2
hr("2. 🔴 关键实验：你那行 PRAGMA 写在了循环里 —— 它生效了吗")
con = sqlite3.connect(":memory:")
cur = build("in_loop", con)
print("插完学生和课程之后 —— 事务是否已经开着：conn.in_transaction =", con.in_transaction)
cur.execute("PRAGMA foreign_keys = ON")          # ← 作业第 44 行就写在这（循环体里）
print("执行 PRAGMA foreign_keys = ON 之后，读回来 =",
      cur.execute("PRAGMA foreign_keys").fetchone()[0], "  ← 0 就是没生效")
print()
try:
    cur.execute("INSERT INTO student_course(course_id, student_id) VALUES (99, 1)")
    got = cur.execute("SELECT * FROM student_course WHERE course_id=99").fetchall()
    print("于是插一条 course_id=99（这门课根本不存在）：静默成功 →", got)
    print("  => 外键没拦，脏数据进库了")
except Exception as e:
    print("插 course_id=99 ->", type(e).__name__, "->", e)
con.close()


# ─────────────────────────────────────────────── 3
hr("3. 对照：同一行 PRAGMA 挪到「连接刚建、事务还没开」的位置")
con = sqlite3.connect(":memory:")
cur = build("after_connect", con)
print("跑完建表和插入之后 conn.in_transaction =", con.in_transaction)
print("读回来 foreign_keys =", cur.execute("PRAGMA foreign_keys").fetchone()[0])
try:
    cur.execute("INSERT INTO student_course(course_id, student_id) VALUES (99, 1)")
    print("插 course_id=99 -> 静默成功（不该）")
except Exception as e:
    print("插 course_id=99 ->", type(e).__name__, "->", e)
print()
print("同一条合法插入（course_id=1）仍然正常：", end=" ")
cur.execute("INSERT INTO student_course(course_id, student_id) VALUES (1, 1)")
print(cur.execute("SELECT * FROM student_course").fetchall())
con.close()


# ─────────────────────────────────────────────── 4
hr("4. 把你那行挪个位置，脚本输出会变吗（应该完全不变）")
src = HW.read_text(encoding="utf-8")
src2 = src.replace('Path(__file__).with_name("D8.db")', '":memory:"')
src2 = src2.replace('    for i in course_name:\n        cur.execute("PRAGMA foreign_keys = ON")\n',
                    '    for i in course_name:\n')
src2, n = re.subn(r"(cur = conn\.cursor\(\))",
                  r"\1\ncur.execute('PRAGMA foreign_keys = ON')", src2)
print("挪动处数 =", n, "｜ 循环里那行已移除：", "PRAGMA" not in src2.split("def link")[1].split("link(")[0])
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    exec(compile(src2, "moved", "exec"), {"__name__": "__main__"})
mine = [l for l in buf.getvalue().strip().splitlines() if l.strip()][-1]
his = r.stdout.strip().splitlines()[-1]
print("挪过之后最后一行 == 他现在的最后一行：", mine == his)
if mine != his:
    print("  挪后：", mine[:110])
    print("  现在：", his[:110])
