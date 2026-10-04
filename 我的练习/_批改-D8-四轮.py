# -*- coding: utf-8 -*-
"""D8 作业 · 第四轮复查（2026-10-05）—— `DROP TABLE` 为什么报 FOREIGN KEY constraint failed

跑法：python -X utf8 我的练习/_批改-D8-四轮.py
实验用内存库 + 一份 D8.db 的临时副本，不动你的真库。
"""
import io, re, shutil, sqlite3, subprocess, sys, contextlib, pathlib

HERE = pathlib.Path(__file__).resolve().parent
HW = HERE / "D8作业.py"
TMP = HERE / "_批改-D8-四轮-临时.db"


def hr(t):
    print("\n" + "=" * 70)
    print(t)
    print("=" * 70)


STUDENTS = [('张三', '高一'), ('李四', '高三'), ('牛二', '高三'), ('李三', '高一'), ('张贾瑞', '高二')]
COURSES = [('语文',), ('数学',), ('英语',), ('物理',), ('化学',), ('生物',)]
DDL = [
    "CREATE TABLE students(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name TEXT NOT NULL, class_name TEXT NOT NULL)",
    "CREATE TABLE course(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, name TEXT NOT NULL)",
    """CREATE TABLE student_course(course_id INTEGER NOT NULL REFERENCES course(id),
       student_id INTEGER NOT NULL REFERENCES students(id), primary key (course_id, student_id))""",
]
DROPS_HIS = ["DROP TABLE IF EXISTS students", "DROP TABLE IF EXISTS course", "DROP TABLE IF EXISTS student_course"]
DROPS_FIX = ["DROP TABLE IF EXISTS student_course", "DROP TABLE IF EXISTS students", "DROP TABLE IF EXISTS course"]


def prior_run(con, fill=True):
    """搭出「上一次已经跑过」的库：三张表 + 外键声明 + 数据"""
    for d in DDL:
        con.execute(d)
    con.executemany("INSERT INTO students(name,class_name) VALUES (?,?)", STUDENTS)
    con.executemany("INSERT INTO course(name) VALUES (?)", COURSES)
    if fill:
        cid = {n: i for i, n in enumerate([x[0] for x in COURSES], 1)}
        sid = {n: i for i, n in enumerate([x[0] for x in STUDENTS], 1)}
        pairs = [("张三", ["语文", "数学", "英语"]), ("李四", ["语文", "数学", "物理"]),
                 ("牛二", ["数学", "物理", "化学"]), ("李三", ["数学", "生物", "化学"]),
                 ("张贾瑞", ["语文", "数学", "化学"])]
        con.executemany("INSERT INTO student_course VALUES (?,?)",
                        [(cid[c], sid[s]) for s, cs in pairs for c in cs])
    con.commit()


# ─────────────────────────────────────────────── 0
hr("0. 复现你的报错（外键开着 + 库里还有上回的 15 行）")
con = sqlite3.connect(":memory:")
prior_run(con)
con.execute("PRAGMA foreign_keys = ON")
print("库里现状：student_course =", con.execute("SELECT COUNT(*) FROM student_course").fetchone()[0], "行")
for sql in DROPS_HIS:
    try:
        con.execute(sql)
        print("  ", sql, "-> 成功")
    except Exception as e:
        print("  ", sql, "->", type(e).__name__, "->", e)
        break
con.close()


# ─────────────────────────────────────────────── 1
hr("1. 关键区分：拦你的是「那 15 行」还是「外键声明」本身？")
con = sqlite3.connect(":memory:")
prior_run(con)
con.execute("PRAGMA foreign_keys = ON")
con.execute("DELETE FROM student_course")      # 只把绳子表删空，声明一条没动
print("把 student_course 删空之后（外键声明还在）：")
print("  foreign_key_list 仍然是：", len(con.execute("PRAGMA foreign_key_list(student_course)").fetchall()), "条")
try:
    con.execute("DROP TABLE IF EXISTS students")
    print("  DROP TABLE students -> 成功了")
    print("  => 拦你的是「绳子表里指向学生的那些行」，不是那句 REFERENCES")
except Exception as e:
    print("  DROP TABLE students ->", type(e).__name__, "->", e)
con.close()
print()
print("SQLite 的规矩：DROP TABLE 若在外键开启时执行，会先做一次隐式 DELETE 把表删空；")
print("这次隐式 DELETE 撞上了 student_course 里指向它的行 → IntegrityError。")


# ─────────────────────────────────────────────── 2
hr("2. 修法一：换 DROP 顺序 —— 先删绳子表，再删两张主表")
con = sqlite3.connect(":memory:")
prior_run(con)
con.execute("PRAGMA foreign_keys = ON")
for sql in DROPS_FIX:
    try:
        con.execute(sql)
        print("  ", sql, "-> 成功")
    except Exception as e:
        print("  ", sql, "->", type(e).__name__, "->", e)
con.close()


# ─────────────────────────────────────────────── 3
hr("3. 对照：外键关着的时候，你原来的顺序照样能过（所以这不是新 bug）")
con = sqlite3.connect(":memory:")
prior_run(con)
print("  PRAGMA foreign_keys =", con.execute("PRAGMA foreign_keys").fetchone()[0], "（关着）")
for sql in DROPS_HIS:
    con.execute(sql)
print("  原顺序三个 DROP 全部成功 —— 因为约束根本没在管事")
con.close()
print()
print("=> 报错不是「加了外键把代码搞坏了」，而是「约束终于生效了，暴露出清理顺序本来就不对」。")
print("   以前能过，只是因为外键一直是关的。")


# ─────────────────────────────────────────────── 4
hr("4. 为什么今天才撞到：空库时 DROP IF EXISTS 是空操作")
con = sqlite3.connect(":memory:")
con.execute("PRAGMA foreign_keys = ON")
for sql in DROPS_HIS:
    con.execute(sql)
print("  全新库（一张表都没有）+ 外键开着 → 三个 DROP 全过（IF EXISTS 直接跳过）")
print("  ⇒ 只有「库里已经有上一次的数据」时才会撞。你之前几次跑，pragma 从没真生效过，所以没撞。")
con.close()


# ─────────────────────────────────────────────── 5
hr("5. 用你真正的 D8.db 副本验一遍修好的版本（连跑两次）")
shutil.copy(HERE / "D8.db", TMP)                # 复制你现在这个「有 15 行」的库
src = HW.read_text(encoding="utf-8")
src = src.replace('Path(__file__).with_name("D8.db")', repr(str(TMP)))
before = src
src = src.replace("\n".join(f'cur.execute("{s}")' for s in DROPS_HIS),
                  "\n".join(f'cur.execute("{s}")' for s in DROPS_FIX))
print("只改了 DROP 的三行顺序：", src != before)
for run in (1, 2):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(src, f"fixed_run{run}", "exec"), {"__name__": "__main__"})
        out = [l for l in buf.getvalue().strip().splitlines() if l.strip()]
        print(f"  第 {run} 次跑：成功，最后一行 = {out[-1][:78]}...")
    except Exception as e:
        print(f"  第 {run} 次跑：{type(e).__name__} -> {e}")
c = sqlite3.connect(TMP)
print("  跑完库里：students", c.execute("SELECT COUNT(*) FROM students").fetchone()[0],
      "/ course", c.execute("SELECT COUNT(*) FROM course").fetchone()[0],
      "/ student_course", c.execute("SELECT COUNT(*) FROM student_course").fetchone()[0], "行")
c.close()
TMP.unlink(missing_ok=True)
print("  （临时副本已删，你的 D8.db 一个字没动）")
