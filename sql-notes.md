# SQL 基础学习笔记

> 2026.07.07-08 · 大一暑假 · SQLite + Python 实战

---

## 一、数据库是什么

数据库 = 有组织的数据存储 + 查询引擎。

| 概念 | 类比 Excel | 实际例子 |
|------|-----------|----------|
| 数据库 (Database) | Excel 文件 | `prescriptions.db`（一个文件） |
| 表 (Table) | 一个 Sheet | `prescriptions` 表、`ingredients` 表 |
| 行 (Row) | 一行数据 | 麻黄汤这一条记录 |
| 列 (Column) | 一列字段 | `name`、`category` 列 |
| 主键 (PRIMARY KEY) | 每行的唯一编号 | `id = 1, 2, 3...` |
| 外键 (FOREIGN KEY) | 跨表引用的约束 | 关联表的 `prescription_id` 必须在方剂表存在 |

## 二、CRUD 四操作

| 操作 | SQL 关键字 | Python 写法 |
|------|-----------|-------------|
| 增 | `INSERT INTO` | `cur.execute("INSERT INTO t VALUES (?)", (val,))` |
| 查 | `SELECT` | `for row in cur.execute("SELECT ..."):` |
| 改 | `UPDATE` | `cur.execute("UPDATE t SET col=? WHERE id=?", (val, id))` |
| 删 | `DELETE` | `cur.execute("DELETE FROM t WHERE id=?", (id,))` |

**`?` 占位符必须用**——防止 SQL 注入。永远不要用 f-string 拼 SQL。

## 三、多对多关系与关联表

方剂 ↔ 药材是典型的**多对多关系**：一首方剂含多味药，一味药出现在多首方剂中。

**不能直接存在方剂表或药材表里，必须用第三张"关联表"。**

```sql
CREATE TABLE prescription_ingredients (
    prescription_id INTEGER,
    ingredient_id INTEGER,
    dosage TEXT,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
)
```

类比：你、微信群和"群成员关系"——关联表就是群成员列表。

## 四、JOIN 联表查询

把多张表按 id 对应关系拼在一起：

```sql
SELECT p.name, i.name, pi.dosage
FROM prescriptions p
JOIN prescription_ingredients pi ON p.id = pi.prescription_id
JOIN ingredients i ON pi.ingredient_id = i.id
```

**执行过程**：数据库一行一行遍历方剂表，带着方剂 id 去关联表匹配，找到的 ingredient_id 再去药材表翻译。

### JOIN 类型

| 类型 | 行为 |
|------|------|
| `JOIN` (INNER JOIN) | 两边都匹配才出结果 |
| `LEFT JOIN` | 左表为主，右表没匹配的填 NULL |

## 五、常用查询模式

```sql
-- 精确筛选
SELECT * FROM prescriptions WHERE category = '解表剂'

-- 反向查（从药材查方剂）
SELECT p.name FROM ingredients i
JOIN prescription_ingredients pi ON i.id = pi.ingredient_id
JOIN prescriptions p ON pi.prescription_id = p.id
WHERE i.name = '甘草'

-- 统计分组
SELECT p.name, COUNT(pi.ingredient_id)
FROM prescriptions p
LEFT JOIN prescription_ingredients pi ON p.id = pi.prescription_id
GROUP BY p.id
```

## 六、Python 操作 SQLite

```python
import sqlite3

conn = sqlite3.connect("database.db")   # 连接（文件自动创建）
cur = conn.cursor()                      # 游标

cur.execute("SQL语句")                   # 执行单条
cur.executemany("SQL", list_of_tuples)   # 批量执行
conn.commit()                            # 确认写入（增删改后必须调）

for row in cur.execute("SELECT ..."):    # 遍历查询结果
    print(row)

conn.close()                             # 用完关闭
```

### commit() 的重要性

`execute(INSERT)` 后数据在"事务"中（临时状态），`commit()` 才真正写入硬盘文件。
类比 Git：execute ≈ `git add`，commit ≈ `git commit`

## 七、常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| UNIQUE constraint failed | 插入了重复值 | 检查列表是否有重复 |
| table has X columns but Y values supplied | INSERT 字段数和值数不匹配 | 检查元组长度 |
| no such table | 表名写错或不存在 | 确认 CREATE TABLE 已执行 |

## 八、本项目数据库

```
prescriptions（方剂）
├── id (PRIMARY KEY)
├── name（方剂名）
├── category（分类）
├── source（出处）
└── symptoms（主治）

ingredients（药材）
├── id (PRIMARY KEY)
└── name（药材名，UNIQUE）

prescription_ingredients（关联表）
├── prescription_id (FOREIGN KEY → prescriptions.id)
├── ingredient_id (FOREIGN KEY → ingredients.id)
└── dosage（用量）
```

当前数据：8 首方剂、37 味药材、48 条关联记录

---

*代码文件：`E:\项目学习\prescription_db.py`*
