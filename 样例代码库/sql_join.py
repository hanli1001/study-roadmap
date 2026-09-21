"""样例代码库 · SQL JOIN：和交互演示同一套例子

配套：交互演示/JOIN配对过程.html、第3课-数据模型与JOIN.md
用法：python 样例代码库/sql_join.py
说明：用内存数据库跑，不碰工作区任何文件。
"""
import sqlite3

conn = sqlite3.connect(":memory:")
cur = conn.cursor()
cur.executescript("""
CREATE TABLE persons (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE groups  (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE group_members (uid INTEGER, gid INTEGER, joined TEXT);
INSERT INTO persons VALUES (7,'小明'),(9,'小红');
INSERT INTO groups  VALUES (1,'高数自习'),(2,'游戏开黑');
INSERT INTO group_members VALUES (7,1,'2026-03-01'),(9,1,'2026-03-02'),(7,2,'2026-04-11');
""")

def q(tag, sql):
    """跑一条 SQL 并打印结果 —— 自己改 SQL 里的数字，看输出怎么变。"""
    print(f"\n--- {tag} ---")
    rows = list(cur.execute(sql))
    print(f"（{len(rows)} 行）")
    for r in rows:
        print("   ", r)
    return rows

# ① 最小可运行：三个表，一条 JOIN
q("1号群的成员名字", """
SELECT persons.name, groups.name
FROM groups
JOIN group_members ON groups.id = group_members.gid
JOIN persons       ON group_members.uid = persons.id
WHERE groups.id = 1
""")

# ② 输入 → 输出：把 WHERE 的数字改掉，行数就变
for gid in (1, 2, 3):
    rows = q(f"换参数：WHERE groups.id = {gid}", f"""
    SELECT persons.name FROM groups
    JOIN group_members ON groups.id = group_members.gid
    JOIN persons       ON group_members.uid = persons.id
    WHERE groups.id = {gid}
    """)
    if not rows:
        print("    ↑ 0 行：这个群要么不存在，要么没人加 —— 但 SQL 不会报错")

# ③ 边界情况：错配 / NULL / 空值
q("错配：拿群 id 去对人 id（id 不重叠 → 0 行）", """
SELECT persons.name FROM groups
JOIN group_members ON groups.id = group_members.uid
JOIN persons       ON group_members.uid = persons.id
""")

cur.execute("INSERT INTO groups VALUES (3,'没人加的群')")
q("LEFT JOIN：没人加的群也保住了（右边填 NULL）", """
SELECT groups.name, persons.name
FROM groups
LEFT JOIN group_members ON groups.id = group_members.gid
LEFT JOIN persons       ON group_members.uid = persons.id
""")

q("同一个查询去掉 LEFT（'没人加的群'整行消失）", """
SELECT groups.name, persons.name
FROM groups
JOIN group_members ON groups.id = group_members.gid
JOIN persons       ON group_members.uid = persons.id
""")

# ④ 你自己写（复制去改，别直接看答案）
print("""
===================== 轮到你了 =====================
① 查出 2 号群的成员名字（把 WHERE 的数字改掉就跑通了）
② 查出"小明"在哪些群里（起点换成 persons）
③ 数一数每个群有多少人（提示：COUNT(*) + GROUP BY groups.id）
   写不出来时：先单独跑 SELECT * FROM group_members; 看绳子长什么样
====================================================
""")

conn.close()
