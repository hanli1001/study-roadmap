# -*- coding: utf-8 -*-
"""D8 作业批改探针 —— 把作业里每一处可疑点单独跑一遍，取真实输出。"""
import sqlite3

def hr(t):
    print("\n" + "=" * 70)
    print(t)
    print("=" * 70)

# ---------------------------------------------------------------- 0
hr("0. 崩溃之后，为什么表在、数据没了")
import os
db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_批改-D8-事务.db")
if os.path.exists(db):
    try:
        os.remove(db)
    except PermissionError:
        pass
c = sqlite3.connect(db)
print("刚连上            in_transaction =", c.in_transaction)
c.execute("CREATE TABLE t(x)")
print("执行 DDL(CREATE)  in_transaction =", c.in_transaction, " <- DDL 不进事务，直接落盘")
c.execute("INSERT INTO t VALUES (1)")
print("执行 DML(INSERT)  in_transaction =", c.in_transaction, " <- DML 才开事务")
del c                                   # 模拟脚本崩溃：连接被回收，没人 commit
c = sqlite3.connect(db)
print("崩溃后重连 —— 表还在吗：", [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")])
print("崩溃后重连 —— 数据还有吗：", c.execute("SELECT * FROM t").fetchall())
c.close()

# ---------------------------------------------------------------- 1
hr("1. 单看第 1 条 REFERENCES courses(id)：父表不存在会怎样")
c = sqlite3.connect(":memory:")
c.execute("PRAGMA foreign_keys = ON")
c.execute("CREATE TABLE student_course(course_id INTEGER NOT NULL REFERENCES courses(id))")
print("建表：成功（建表时 SQLite 不检查父表是否存在）")
try:
    c.execute("INSERT INTO student_course VALUES (1)")
    print("插入：成功")
except Exception as e:
    print("插入：", type(e).__name__, "->", e)
try:
    print("foreign_key_check：", c.execute("PRAGMA foreign_key_check").fetchall())
except Exception as e:
    print("foreign_key_check：", type(e).__name__, "->", e)

# ---------------------------------------------------------------- 2
hr("2. 主键里混进 class_name，还能防住重复选课吗")
c = sqlite3.connect(":memory:")
c.execute("CREATE TABLE students(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, class_name TEXT NOT NULL)")
c.execute("INSERT INTO students(name,class_name) VALUES ('张三','高一')")
c.execute("""CREATE TABLE sc(pk3 INTEGER, sid INTEGER, class_name TEXT)""")
c.execute("""CREATE TABLE sc3(course_id INTEGER, student_id INTEGER, class_name TEXT, PRIMARY KEY(course_id, student_id, class_name))""")
c.execute("INSERT INTO sc3 VALUES (1,1,'高一')")
try:
    c.execute("INSERT INTO sc3 VALUES (1,1,'高一')")
    print("重复插同一门课：成功了（防不住）")
except Exception as e:
    print("重复插同一门课：", type(e).__name__, "->", e)
try:
    c.execute("INSERT INTO sc3 VALUES (1,1,'高二')")
    print("同一个人同一门课、class_name 写别的：成功了 <- 主键被 class_name 撑开了")
except Exception as e:
    print("同一个人同一门课、class_name 写别的：", type(e).__name__, "->", e)

# ---------------------------------------------------------------- 3
hr("3. 只修掉前面 3 个语法错、不动顺序错 —— 会发生什么")
c = sqlite3.connect(":memory:")
c.execute("CREATE TABLE students(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, class_name TEXT NOT NULL)")
c.execute("CREATE TABLE course(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
c.execute("""CREATE TABLE student_course(
course_id INTEGER, student_id INTEGER, class_name TEXT,
PRIMARY KEY (course_id, student_id, class_name))""")
students = [('张三','高一'), ('李四','高三'), ('牛二','高三'), ('李三','高一'), ('张贾瑞','高二')]
courses = [('语文',), ('数学',), ('英语',), ('物理',), ('化学',), ('生物',)]
c.executemany("INSERT INTO students(name,class_name) VALUES (?,?)", students)
c.executemany("INSERT INTO course(name) VALUES (?)", courses)

# 固定下来，模拟"每人随机选一门课"（这里写死成一次具体的随机结果：3,0,5,2,4）
picks = [3, 0, 5, 2, 4]
for s, rn in zip(students, picks):
    sid = c.execute("SELECT id FROM students WHERE name=?", (s[0],)).fetchone()[0]
    class_name = s[1]
    cid = c.execute("SELECT id FROM course WHERE name=?", (courses[rn][0],)).fetchone()[0]
    # ↓↓↓ 作业里就是这样写的：列写 (course_id, student_id)，值给 (sid, course_id)
    c.execute("INSERT INTO student_course(course_id, student_id, class_name) VALUES (?,?,?)",
              (sid, cid, class_name))

print("绳子表 student_course 全部行：")
for r in c.execute("SELECT * FROM student_course"):
    print("   ", r)
n_rope = c.execute("SELECT COUNT(*) FROM student_course").fetchone()[0]
print("绳子表行数 =", n_rope)
print()
print("作业第 3 条查询实际会跑到什么：")
print("   它写的是 SELECT * FROM student_courses  ->  表名不存在")
print()
print("假设改成正确的表名，再配一条 JOIN：")
q = """SELECT sc.course_id, s.name, co.name, sc.class_name
       FROM student_course sc
       JOIN students s ON sc.student_id = s.id
       JOIN course  co ON sc.course_id = co.id"""
rows = c.execute(q).fetchall()
print("   ", "course_id | 学生   | 课程 | class_name")
for r in rows:
    print("   ", r)
print("JOIN 出来行数 =", len(rows), " ← 绳子表是", n_rope, "行")
missing = [r for r in c.execute("SELECT student_id FROM student_course") if not c.execute("SELECT 1 FROM students WHERE id=?", r).fetchone()]
print("绳子表里指向不存在学生的行：", missing)

# ---------------------------------------------------------------- 4
hr("4. 循环里那段 if/else 到底走了哪一边")
b = -1
taken = {"if": 0, "else": 0}
for rn in range(6):
    b = -1                      # ← 作业里这行在循环体内部
    if rn != b:
        taken["if"] += 1
    else:
        taken["else"] += 1
    b = rn
print("rn 从 0 到 5 各跑一次，if 分支进入次数 =", taken["if"], " else 分支进入次数 =", taken["else"])
print("=> else 分支是死代码，永远走不到；b = rn 这行也没用（下一轮开头又被 -1 覆盖）")

# ---------------------------------------------------------------- 5
hr("5. class_name 抄进绳子表之后：改一次名册，两份数据就对不上了")
c = sqlite3.connect(":memory:")
c.execute("CREATE TABLE students(id INTEGER PRIMARY KEY, name TEXT NOT NULL, class_name TEXT NOT NULL)")
c.execute("CREATE TABLE course(id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
c.execute("CREATE TABLE sc(course_id INTEGER, student_id INTEGER, class_name TEXT, PRIMARY KEY(course_id, student_id, class_name))")
c.execute("INSERT INTO students VALUES (1,'张三','高一')")
c.execute("INSERT INTO course VALUES (1,'语文')")
c.execute("INSERT INTO sc VALUES (1,1,'高一')")
print("分班时： students 说", c.execute("SELECT class_name FROM students WHERE id=1").fetchone()[0],
      "／ sc 说", c.execute("SELECT class_name FROM sc WHERE student_id=1").fetchone()[0])
c.execute("UPDATE students SET class_name='高二' WHERE id=1")     # 张三升了一级
print("张三升到高二，只改了名册这一处（这是唯一正确的改法）：")
print("   students 说", c.execute("SELECT class_name FROM students WHERE id=1").fetchone()[0],
      "／ sc 说", c.execute("SELECT class_name FROM sc WHERE student_id=1").fetchone()[0], " <- 假的")
print("   而且 SQL 不会告诉你哪一份对：两份都是普通文本，谁也不指向谁")
print()
print("对照：绳子表只留两列（course_id, student_id），班级要用时现 JOIN 出来")
c.execute("CREATE TABLE sc2(course_id INTEGER NOT NULL, student_id INTEGER NOT NULL, PRIMARY KEY(course_id, student_id))")
c.execute("INSERT INTO sc2 VALUES (1,1)")
r = c.execute("SELECT s.name, s.class_name, co.name FROM sc2 JOIN students s ON sc2.student_id=s.id JOIN course co ON sc2.course_id=co.id").fetchall()
print("   名册改完，JOIN 出来立刻是新的：", r)

