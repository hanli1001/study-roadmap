"""第 3 课配套 · 微信群演示：关系模型 + JOIN 执行过程

配套教案：第3课-数据模型与JOIN.md
用法：python 第3课-微信群演示.py
说明：全部只读打印，用内存数据库，不写任何文件。
"""
import sqlite3

conn = sqlite3.connect(":memory:")   # 内存库：跑完就没了，不污染工作区
cur = conn.cursor()

# ---------- 建三张表（对应教案 ③ 画图推导）----------
cur.executescript("""
CREATE TABLE persons (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL,
    phone TEXT
);

CREATE TABLE groups (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- 第三张表 = "绳子表"：它的每一行 = 一条关系，不是一个人
CREATE TABLE group_members (
    uid    INTEGER,
    gid    INTEGER,
    joined TEXT,
    FOREIGN KEY (uid) REFERENCES persons(id),
    FOREIGN KEY (gid) REFERENCES groups(id)
);

INSERT INTO persons VALUES (7, '小明', '138...'), (9, '小红', '139...');
INSERT INTO groups  VALUES (1, '高数自习'), (2, '游戏开黑');
INSERT INTO group_members VALUES
    (7, 1, '2026-03-01'),
    (9, 1, '2026-03-02'),
    (7, 2, '2026-04-11');
""")

def show(title, sql):
    print(f"\n--- {title} ---")
    print("SQL:", " ".join(sql.split()))
    rows = list(cur.execute(sql))
    if not rows:
        print("  (0 行 —— 没有任何一行配对成功)")
    for r in rows:
        print("  ", r)
    return rows

print("=" * 64)
print("演示 1：先看'绳子表'里到底有什么（只有数字，没有名字）")
print("=" * 64)
show("group_members 全部内容", "SELECT * FROM group_members")

print("\n" + "=" * 64)
print("演示 2：正确写法 —— 1 号群的成员名字")
print("=" * 64)
print("执行过程：")
print("  ① 从 groups 拿出 1 行                     -> (1, 高数自习)")
print("  ② 拿 1 去 group_members.gid 一行行比      -> 命中 (7,1)/(9,1)，(7,2) 不要")
print("  ③ 每条命中的行，拿 uid 去 persons.id 换名字 -> 7→小明, 9→小红")
print("  ④ 拼成一行交出去")
rows = show("正确 JOIN", """
SELECT persons.name, groups.name
FROM groups
JOIN group_members ON groups.id = group_members.gid
JOIN persons       ON group_members.uid = persons.id
WHERE groups.id = 1
""")
print(f"  注意：结果 {len(rows)} 行 —— 行数不是表里的行数，是'配对成功'的次数")

print("\n" + "=" * 64)
print("演示 3：错配的常见结果 —— 一行都配不上（空，且不报错）")
print("=" * 64)
show("错误 ON: groups.id = group_members.uid（拿群 id 去对人 id）", """
SELECT persons.name, groups.name
FROM groups
JOIN group_members ON groups.id = group_members.uid
JOIN persons       ON group_members.uid = persons.id
""")
print("  → 0 行，能跑，不报错。所以 JOIN 查出来是空的，先怀疑 ON，别怀疑数据丢了")
print("  → 但'空'只是其中一种结果，看演示 4")

print("\n" + "=" * 64)
print("演示 4：危险情况 —— 错得刚刚好，反而给你'像对的数据'")
print("=" * 64)
print("原因：persons.id 和 group_members.gid 的 id 空间重叠了。")
print("为了演示，这里把 persons 的 id 排成 1/2 —— 现实中很常见：")
print("  任何'两套从 1 开始编号'的表（换个库、重新灌数据、id 密集）都会这样。")
cur.execute("DELETE FROM persons")
cur.execute("UPDATE group_members SET uid = gid")   # 只为了让 id 空间重叠, 便于演示
cur.execute("INSERT INTO persons VALUES (1, '小明', '138...'), (2, '小红', '139...')")
show("错误 ON: persons.id = group_members.gid（把 gid 当 uid 用）", """
SELECT persons.name, group_members.joined
FROM persons
JOIN group_members ON persons.id = group_members.gid
""")
print("  看起来完全合理 —— 但这是把'群 id'当成'人 id'配出来的假数据。")
print("  它不报错、不为空，甚至行数也可能正好对；只有人工核对内容才发现。")

print("\n" + "=" * 64)
print("所以：JOIN 要核对的不是语法，是【配对对不对】")
print("=" * 64)
print("诊断三步（可背）：")
print("  ① 单独数绳子表：SELECT * FROM group_members WHERE gid = 1;   -> 这里 2 行")
print("  ② 再数 JOIN 的结果行数                                       -> 这里 2 行")
print("  ③ 一致 ≠ 对！还要挑一行人工核对内容（演示 4 就是一致但全错）")
print("  ④ 明显对不上（空 / 多很多）-> 几乎一定是 ON 写错")

conn.close()
