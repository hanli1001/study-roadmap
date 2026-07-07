"""中医方剂数据库 - JOIN 联表查询"""
import sqlite3

conn = sqlite3.connect("prescriptions.db")
cur = conn.cursor()

# 1. 删旧表重建（因为结构变了）
cur.execute("DROP TABLE IF EXISTS prescription_ingredients")
cur.execute("DROP TABLE IF EXISTS ingredients")
cur.execute("DROP TABLE IF EXISTS prescriptions")

# 2. 建三张表
cur.execute("""
    CREATE TABLE prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        source TEXT,
        symptoms TEXT
    )
""")

cur.execute("""
    CREATE TABLE ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE   -- UNIQUE = 不重复
    )
""")

cur.execute("""
    CREATE TABLE prescription_ingredients (
        prescription_id INTEGER,
        ingredient_id INTEGER,
        dosage TEXT,                 -- 用量如"三两"、"9g"
        FOREIGN KEY (prescription_id) REFERENCES prescriptions(id),
        FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
    )
""")

# 3. 插入方剂
fangji = [
    ("麻黄汤", "解表剂", "伤寒论", "外感风寒表实证：恶寒发热、无汗而喘"),
    ("桂枝汤", "解表剂", "伤寒论", "外感风寒表虚证：头痛发热、汗出恶风"),
    ("小柴胡汤", "和解剂", "伤寒论", "少阳证：往来寒热、胸胁苦满、不欲饮食"),
    ("白虎汤", "清热剂", "伤寒论", "阳明气分热盛：大热、大汗、大渴、脉洪大"),
    ("四君子汤", "补益剂", "太平惠民和剂局方", "脾胃气虚：面色萎白、四肢无力"),
    ("银翘散","解表剂"," 温病条辨","温病初起：发热无汗、头痛口渴、咳嗽咽痛"),
    ("四物汤","补益剂","太平惠民和剂局方","营血虚滞：心悸失眠、头晕目眩、面色无华"),
    ("藿香正气散","祛湿剂","太平惠民和剂局方","外感风寒、内伤湿滞：恶寒发热、头痛、胸膈满闷、腹痛呕吐")
]
cur.executemany(
    "INSERT INTO prescriptions (name, category, source, symptoms) VALUES (?, ?, ?, ?)",
    fangji,
)

# 4. 插入药材
yaocai = [
    "麻黄", "桂枝", "杏仁", "甘草", "白芍", "生姜", "大枣",
    "柴胡", "黄芩", "人参", "半夏", "石膏", "知母", "粳米",
    "白术", "茯苓", "党参", "金银花", "连翘", "薄荷", "荆芥", "淡豆豉",
    "牛蒡子", "桔梗", "竹叶", "当归", "川芎", "熟地黄",
    "藿香", "紫苏", "白芷", "陈皮", "厚朴",
]
cur.executemany("INSERT INTO ingredients (name) VALUES (?)", [(y,) for y in yaocai])

# 5. 插入配方关联（方剂-药材-用量）
def link(fangji_name, ingredients_dosage):
    """辅助函数：给方剂关联药材"""
    cur.execute("SELECT id FROM prescriptions WHERE name = ?", (fangji_name,))
    pid = cur.fetchone()[0]
    for ing_name, dosage in ingredients_dosage:
        cur.execute("SELECT id FROM ingredients WHERE name = ?", (ing_name,))
        iid = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO prescription_ingredients VALUES (?, ?, ?)",
            (pid, iid, dosage),
        )

link("麻黄汤", [("麻黄", "三两"), ("桂枝", "二两"), ("杏仁", "七十个"), ("甘草", "一两")])
link("桂枝汤", [("桂枝", "三两"), ("白芍", "三两"), ("甘草", "二两"), ("生姜", "三两"), ("大枣", "十二枚")])
link("小柴胡汤", [("柴胡", "半斤"), ("黄芩", "三两"), ("人参", "三两"), ("半夏", "半升"), ("甘草", "三两"), ("生姜", "三两"), ("大枣", "十二枚")])
link("白虎汤", [("石膏", "一斤"), ("知母", "六两"), ("甘草", "二两"), ("粳米", "六合")])
link("四君子汤", [("人参", "一两"), ("白术", "一两"), ("茯苓", "一两"), ("甘草", "一两")])
link("银翘散", [("金银花", "一两"), ("连翘", "一两"), ("薄荷", "六钱"), ("荆芥", "四钱"), ("淡豆豉",
  "五钱"), ("牛蒡子", "六钱"), ("桔梗", "六钱"), ("甘草", "二钱"), ("竹叶", "四钱")])
link("四物汤", [("当归", "三钱"), ("川芎", "二钱"), ("白芍", "三钱"), ("熟地黄", "四钱")])
link("藿香正气散", [("藿香", "三两"), ("紫苏", "一两"), ("白芷", "一两"), ("半夏", "二两"), ("陈皮",
  "二两"), ("茯苓", "一两"), ("白术", "二两"), ("厚朴", "二两"), ("桔梗", "一两"), ("甘草", "二两"),
  ("生姜", "三片"), ("大枣", "一枚")])

conn.commit()
print("数据已就绪\n")

# 6. JOIN 联表查询 —— 这才是今天的重点
print("===== 每首方剂包含哪些药材？ =====")
query = """
    SELECT p.name, i.name, pi.dosage
    FROM prescriptions p
    JOIN prescription_ingredients pi ON p.id = pi.prescription_id
    JOIN ingredients i ON pi.ingredient_id = i.id
    ORDER BY p.id, pi.rowid
"""
for row in cur.execute(query):
    print(f"  {row[0]:　<6s} → {row[1]:　<4s}（{row[2]}）")

# 7. 反过来查：甘草用在哪些方剂中？
print("\n===== 甘草出现在哪些方剂中？ =====")
query2 = """
    SELECT p.name, pi.dosage
    FROM ingredients i
    JOIN prescription_ingredients pi ON i.id = pi.ingredient_id
    JOIN prescriptions p ON pi.prescription_id = p.id
    WHERE i.name = '甘草'
"""
for row in cur.execute(query2):
    print(f"  {row[0]}（用量：{row[1]}）")

# 8. 统计每首方剂的药材数量
print("\n===== 每首方剂的药材数 =====")
for row in cur.execute("""
    SELECT p.name, COUNT(pi.ingredient_id)
    FROM prescriptions p
    LEFT JOIN prescription_ingredients pi ON p.id = pi.prescription_id
    GROUP BY p.id
"""):
    print(f"  {row[0]}：{row[1]} 味药")

conn.close()
print("\n完成")
