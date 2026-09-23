"""函数卡生成器：卡上的代码与输出**全部真跑一遍**，再生成 `交互演示/_函数卡数据.js`。

为什么要这么绕（而不是我直接手写一个 HTML）：
    手写的"示例输出"是幻觉重灾区 —— 看着合理、跑起来报错。
    所以唯一事实源是**这个文件**：卡片的讲解文字 + 示例代码都写在这里，
    代码由本脚本真的执行（SQL 跑内存库，Python 跑真解释器），把**真实输出**一起烘进 JS。
    卡片页面上每条输出旁都标 [实测]，就是它。

用法：
    python tools/build_fn_cards.py            # 跑全部 → 写 JS + 打印统计（ASCII，避免 GBK 控制台乱码）
    python tools/build_fn_cards.py --check    # 只跑不写，看有没有期望外的失败

改了卡片：改这个文件 → 重跑 → 刷新网页。不要手改 `_函数卡数据.js`（会被覆盖）。
"""
from __future__ import annotations

import contextlib
import io
import json
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "交互演示" / "_函数卡数据.js"

# ══════════════════════════════════════════════════════════════════════
# 沙盒数据库：每个 SQL 卡都跑在一个**全新的内存库**上（互不污染）
# 两张样板：① 选修课报名（= 本周 D8 作业的样板）② 微信群（第 3 课推导用）
#   特意让 students.id 与 courses.id 都从 1 开始 —— 这样"ON 写反了照样出数据"
#   这个静默错误才演示得出来（教案 ④ 里那个实测反例）。
# ══════════════════════════════════════════════════════════════════════
SEED = """
CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT NOT NULL, class TEXT);
INSERT INTO students VALUES
  (1,'韩立','讯飞班'),(2,'小明','讯飞班'),(3,'小红','计科1班'),(4,'小刚','计科1班'),(5,'小美','计科1班');
CREATE TABLE courses (id INTEGER PRIMARY KEY, name TEXT NOT NULL, credit INTEGER);
INSERT INTO courses VALUES
  (1,'数据库',3),(2,'高数',5),(3,'机器学习',2),(4,'体育',1),(5,'英语',2);
CREATE TABLE enrollments (sid INTEGER, cid INTEGER, grade REAL);
INSERT INTO enrollments VALUES
  (1,1,88.5),(1,2,76),(2,1,92),(2,3,81),(3,5,59),(4,4,NULL);

CREATE TABLE persons (id INTEGER PRIMARY KEY, name TEXT);
INSERT INTO persons VALUES (7,'小明'),(9,'小红'),(11,'小刚');
CREATE TABLE groups (id INTEGER PRIMARY KEY, name TEXT);
INSERT INTO groups VALUES (1,'高数自习'),(2,'游戏开黑'),(3,'考研互助');
CREATE TABLE group_members (uid INTEGER, gid INTEGER, joined TEXT);
INSERT INTO group_members VALUES (7,1,'2026-03-01'),(9,1,'2026-03-02'),(7,2,'2026-04-11');
"""

CARDS: list[dict] = []


def C(cid, lang, cat, stage, name, brief, code,
      where="", gotcha="", verify=None, err=False, extra=""):
    """登记一张卡。

    cid   卡 id（跨文件引用用，别改）
    lang  sql | py
    cat   SQL | sqlite3 | 标准库 | 内置 | 第三方
    stage 本周 | 本月 | 以后   ← 决定"现在要不要会"
    code  示例代码（会被真的执行）
    err   True = 这张卡故意演示报错（跑挂了不算失败）
    """
    CARDS.append(dict(id=cid, lang=lang, cat=cat, stage=stage, name=name, brief=brief,
                      code=code.strip("\n"), where=where, gotcha=gotcha,
                      verify=verify, err=err, extra=extra))


# ══════════════════════════════════════════════════════════════════════
# SQL 卡（cat=SQL）
# ══════════════════════════════════════════════════════════════════════
C("sql.skeleton", "sql", "SQL", "本周", "SELECT … FROM …",
  "所有查询的骨架：先说「要哪几列」，再说「从哪张表」",
  "SELECT name, class FROM students;",
  where="第3课① · 任何一条 SQL 都长这样",
  gotcha="`SELECT *` 能跑但别常用 —— 列的顺序以后会变，代码会悄悄错位")

C("sql.where", "sql", "SQL", "本周", "WHERE",
  "先在脑子里选出全部，再一条条筛掉不要的",
  "SELECT name, class FROM students WHERE class = '讯飞班';",
  where="第3课 · 筛选；D8 作业至少要用一次",
  gotcha="筛完只剩 2 行不是因为「表里只有 2 行」，是 WHERE 把它们筛掉了")

C("sql.on_vs_where", "sql", "SQL", "本周", "ON / WHERE 分工",
  "ON = 怎么配对（横着拼），WHERE = 要哪些（竖着筛）",
  "SELECT s.name, e.cid\nFROM students s\nJOIN enrollments e ON s.id = e.sid\nWHERE e.cid = 1;",
  where="第3课④ · 全课最该分清的一对",
  gotcha="把 `e.cid = 1` 挪到 ON 里，INNER JOIN 结果一样 —— 但换成 LEFT JOIN 就天差地别（留在 ON 里 = 右表筛完再拼，放 WHERE 里 = 拼完再筛，会把 NULL 行筛掉）")

C("sql.order_by", "sql", "SQL", "本月", "ORDER BY",
  "排序；默认升序，DESC 反过来",
  "SELECT s.name, e.grade\nFROM enrollments e JOIN students s ON s.id = e.sid\nORDER BY e.grade DESC;",
  where="出榜单 / 看最大的那个",
  gotcha="NULL 在 SQLite 里排在最前（DESC 时排最后）—— 想让它垫底要写 `ORDER BY grade IS NULL, grade DESC`")

C("sql.limit", "sql", "SQL", "本月", "LIMIT / OFFSET",
  "只要前 N 条 / 跳过前 N 条（分页就靠它）",
  "SELECT name, credit FROM courses ORDER BY credit DESC LIMIT 2;",
  where="Top-N 排行榜；翻页",
  gotcha="`LIMIT` 没有 `ORDER BY` 时顺序是**未定义**的 —— 每次跑可能不一样")

C("sql.distinct", "sql", "SQL", "本月", "DISTINCT",
  "一行里多个列都相同才算重复，去重后只剩一种",
  "SELECT DISTINCT class FROM students;",
  where='「有几种」而不是「有几条」',
  gotcha="`COUNT(DISTINCT 列)` 才是「数几种」；`COUNT(*)` 数的是行数")

C("sql.and_or", "sql", "SQL", "本月", "AND / OR 的优先级",
  "AND 比 OR 先算 —— 所以 OR 两边一定要加括号",
  "SELECT name, class FROM students\nWHERE (class = '讯飞班' OR class = '计科1班') AND name <> '小红';",
  where="多条件筛选",
  gotcha="不加括号会变成「讯飞班的人，或者（计科1班且不叫小红的人）」—— 结果多出来的人你还不一定看得出来")

C("sql.in", "sql", "SQL", "本月", "IN",
  "一个字段对一串值，比写一堆 OR 干净",
  "SELECT name FROM students WHERE class IN ('讯飞班', '计科1班');",
  where="按一批 id 批量查（爬虫/接口返回的 id 列表）",
  gotcha="`NOT IN` 遇到 NULL 会整体变空 —— 子查询里可能有 NULL 时别用")

C("sql.between", "sql", "SQL", "本月", "BETWEEN",
  "区间筛选，**两头都算在内**",
  "SELECT name, credit FROM courses WHERE credit BETWEEN 2 AND 5;",
  where="按时间/分数区间查",
  gotcha="`BETWEEN 2 AND 5` = `>= 2 AND <= 5`（含 5）—— 差一个边界是常见 off-by-one")

C("sql.like", "sql", "SQL", "本月", "LIKE 通配",
  "`%` = 任意多个字符，`_` = 正好一个字符",
  "SELECT id, name FROM courses WHERE name LIKE '_数';",
  where="模糊搜索 / 清洗数据时找脏值",
  gotcha="SQLite 的 LIKE 对 ASCII **大小写不敏感**，对中文当然无所谓 —— 但换成 PostgreSQL 就敏感了")

C("sql.count", "sql", "SQL", "本周", "COUNT(*) / COUNT(列)",
  "COUNT(*) 数行；COUNT(列) 只数**这一列不是 NULL** 的行",
  "SELECT COUNT(*) AS rows_all, COUNT(grade) AS rows_graded FROM enrollments;",
  where="第3课⑥ 诊断第一步：单独数绳子表",
  gotcha="两者不一样就说明这列有 NULL —— 这个差值本身就是线索，不是 bug")

C("sql.count_distinct", "sql", "SQL", "本月", "COUNT(DISTINCT 列)",
  "数「有几种」，不是「有几条」",
  "SELECT COUNT(*) AS rows_all, COUNT(DISTINCT cid) AS kinds FROM enrollments;",
  where="统计去重后的数量（多少门课被选过）",
  gotcha="`COUNT(DISTINCT a, b)` 在 SQLite 里是**语法错误**，多列去重得用子查询")

C("sql.aggregate", "sql", "SQL", "本月", "SUM / AVG / MIN / MAX / ROUND",
  "五个聚合函数，NULL 一律不参与计算",
  "SELECT ROUND(AVG(grade), 1) AS avg_g, MAX(grade) AS top, MIN(grade) AS low\nFROM enrollments WHERE grade IS NOT NULL;",
  where="算总分/均分；第7章预习要用",
  gotcha="`AVG` 忽略 NULL，所以分母是「有分数的行数」而不是总行数 —— 拿不准就先 `COUNT(*)` 和 `COUNT(列)` 都打出来看")

C("sql.group_by", "sql", "SQL", "本月", "GROUP BY",
  "把行按某列分成堆，每堆出一行（聚合函数的分母就变成「这一堆」）",
  "SELECT cid, COUNT(*) AS n FROM enrollments GROUP BY cid ORDER BY n DESC;",
  where="第7章预习 · 每个群的成员数这种「分堆统计」",
  gotcha="SELECT 里只能出现**分组列 + 聚合函数**，出现别的列时 SQLite 不报错但会随便挑一行给你（别的数据库直接报错）")

C("sql.having", "sql", "SQL", "本月", "HAVING",
  "筛「堆」。WHERE 筛行、发生在分组前，HAVING 筛堆、发生在分组后",
  "SELECT cid, COUNT(*) AS n FROM enrollments GROUP BY cid HAVING COUNT(*) > 1;",
  where="第7章预习 · 「选课人数 > 1 的课」",
  gotcha="写成 `WHERE COUNT(*) > 1` 会直接报错 —— 因为 WHERE 执行时还没分组，没有「每堆」这个概念")

C("sql.where_aggregate_err", "sql", "SQL", "本月", "坑：WHERE 里用聚合函数",
  "WHERE 比 GROUP BY 先执行，所以它根本看不到 COUNT(*)",
  "SELECT cid FROM enrollments WHERE COUNT(*) > 1 GROUP BY cid;",
  where="报错现场",
  gotcha="看到 `misuse of aggregate function` 就一个动作：把条件从 WHERE 挪到 HAVING",
  err=True)

C("sql.coalesce", "sql", "SQL", "本月", "IFNULL / COALESCE",
  "NULL 换个默认值再显示（NULL 参与算术会让整行变 NULL）",
  "SELECT sid, cid, IFNULL(grade, 0) AS grade FROM enrollments;",
  where="配 LEFT JOIN 用：没匹配上的那侧全是 NULL",
  gotcha="别用 `IFNULL(grade,0)` 去「修」平均值 —— 用 0 冒充「没考」会把均分拉低，该用 `WHERE grade IS NOT NULL`")

C("sql.null_eq_trap", "sql", "SQL", "本月", "坑：`= NULL` 永远查不出东西",
  "NULL 的意思是「不知道」，所以「等不等于不知道」的答案是「我也不知道」",
  "SELECT sid, cid FROM enrollments WHERE grade = NULL;",
  where="查「没填的那几条」时最常踩",
  gotcha="要判 NULL 只能用 `IS NULL` / `IS NOT NULL` —— 这个坑**不报错、只是静默返回 0 行**")

C("sql.is_null", "sql", "SQL", "本月", "IS NULL / IS NOT NULL",
  "判断「这格是不是空的」唯一正确写法",
  "SELECT sid, cid FROM enrollments WHERE grade IS NULL;",
  where="找脏数据 / 找漏填的记录",
  gotcha="反过来记住：`WHERE grade <> 80` **也不会**把 NULL 的行选出来（NULL 不满足任何比较）")

C("sql.case_when", "sql", "SQL", "以后", "CASE WHEN",
  "SQL 里的 if-else，可以放在 SELECT 里造一个新列",
  "SELECT name, CASE WHEN credit >= 3 THEN 'major' ELSE 'minor' END AS weight\nFROM courses;",
  where="给数据打标签（分数段/等级），打标后直接喂给模型",
  gotcha="不写 `ELSE` 时默认是 NULL，不是原值")

C("sql.cast", "sql", "SQL", "以后", "CAST",
  "改类型。SQLite 类型松，但拼接/比较时该转还得转",
  "SELECT CAST('42' AS INTEGER) + 1 AS n, CAST(3.7 AS INTEGER) AS i;",
  where="从文本里提出来的数字要参与计算时",
  gotcha="`CAST(3.7 AS INTEGER)` 是**截断**不是四舍五入（得 3）；要四舍五入用 `ROUND`")

C("sql.string_fn", "sql", "SQL", "以后", "UPPER / LOWER / LENGTH",
  "大小写与长度。注意 LENGTH 数的是**字符**，不是字节",
  "SELECT UPPER('abc') AS u, LOWER('ABC') AS l, LENGTH('数据库') AS n;",
  where="数据清洗；校验字段长度",
  gotcha="`LENGTH('数据库')` = 3（SQLite 数字符），但 `LENGTH(CAST('数据库' AS BLOB))` = 9 —— 中文是 3 字节")

C("sql.substr_replace", "sql", "SQL", "以后", "SUBSTR / REPLACE / TRIM",
  "截取、替换、去首尾空格 —— 清洗三件套",
  "SELECT SUBSTR('2026-09-24', 1, 4) AS y, REPLACE('a-b', '-', '/') AS r, TRIM('  x  ') AS t;",
  where="日志/网页文本清洗",
  gotcha="SQLite 的 `SUBSTR` 下标**从 1 开始**（Python 从 0 开始），`SUBSTR(s, 1, 4)` 才是钱 4 个字符")

C("sql.date_fn", "sql", "SQL", "以后", "date('now') / strftime",
  "SQLite 没有专门的日期类型，日期就是文本，靠这些函数算",
  "SELECT date('now') AS today, strftime('%Y-%m', 'now') AS ym,\n       CAST(julianday('now') - julianday('2026-09-21') AS INTEGER) AS days;",
  where="按天统计；算「距今几天」",
  gotcha="`date('now')` 取的是 **UTC** —— 想按北京时间算要写 `date('now','+8 hours')`")

C("sql.group_concat", "sql", "SQL", "以后", "GROUP_CONCAT",
  "把一堆行的某列拼成一个字符串（默认用逗号）",
  "SELECT cid, GROUP_CONCAT(sid) AS sids FROM enrollments GROUP BY cid;",
  where='「这个群都有谁」 —— 一行拿到全部成员',
  gotcha="拼接顺序不保证；要固定顺序得先在外面排序（SQLite 3.44+ 才支持 `GROUP_CONCAT(x ORDER BY y)`）")

C("sql.join2", "sql", "SQL", "本周", "JOIN … ON（两表）",
  "拿一边的 id 去另一边配对，配对成功才出一行",
  "SELECT s.name, e.cid\nFROM students s\nJOIN enrollments e ON s.id = e.sid;",
  where="第3课④ · 本课核心",
  gotcha="结果行数 = **配对成功的次数**，不是任何一张表的行数")

C("sql.join3", "sql", "SQL", "本周", "三表 JOIN（中间那张是「绳子」）",
  "行数由中间那张绳子表说了算；两头都只是「换名字」",
  "SELECT s.name AS student, c.name AS course, e.grade\nFROM students s\nJOIN enrollments e ON s.id = e.sid\nJOIN courses     c ON e.cid = c.id;",
  where="第3课④ · 第6章换皮就是把它改名",
  gotcha="三张表的顺序可以换，但**每一句 ON 必须紧跟着它要拼的那张表**")

C("sql.join_alias", "sql", "SQL", "本周", "坑：两边都有 id，不给表起别名",
  "两张表都有 `id` 列时，`ON students.id = courses.id` 里的 id 到底是谁的？",
  "SELECT id, name FROM students JOIN courses ON students.id = courses.id;",
  where="报错现场 —— 别名就是为了解决它",
  gotcha="`ambiguous column name` 的正确解法是给表起别名然后写全：`s.id`、`c.id`",
  err=True)

C("sql.join_wrong_zero", "sql", "SQL", "本周", "坑①：ON 接反 → 0 行（不报错）",
  "groups.id 是 1/2/3，group_members.uid 是 7/9/7 —— 一个都对不上",
  "SELECT persons.name AS person, groups.name AS grp\nFROM groups\nJOIN group_members ON groups.id = group_members.uid\nJOIN persons       ON group_members.gid = persons.id;",
  where="第3课④ 实测反例 1（低危：空的一眼看得出来）",
  gotcha="**JOIN 查出空表时的第一反应应该是「怀疑 ON」，而不是「数据没了」**")

C("sql.join_wrong_fake", "sql", "SQL", "本周", "坑②：id 重叠 → 照样出数据（最危险）",
  "students.id 和 courses.id 都从 1 开始，接反了照样配得上 —— 于是给你一张看着完全合理的假表",
  "SELECT s.name AS student, c.name AS course\nFROM students s\nJOIN enrollments e ON s.id = e.cid\nJOIN courses     c ON e.sid = c.id;",
  where="第3课④ 实测反例 2（🔴 高危：静默错误）",
  gotcha="「不为空」**绝不等于**「对」。唯一的防线是**挑一行人工核对内容**——这张表里有**根本没选课的小美**、还有对不上课的小红，一眼就能看出不对")

C("sql.fake_proof", "sql", "SQL", "本周", "证明它到底错在哪：行数一样，内容不同",
  "同一批数据，正确写法和接反写法**都出 6 行**；真正差的是其中 2 行的内容",
  """SELECT
 (SELECT COUNT(*) FROM (
    SELECT s.name, c.name FROM students s
      JOIN enrollments e ON s.id = e.sid JOIN courses c ON e.cid = c.id
    EXCEPT
    SELECT s.name, c.name FROM students s
      JOIN enrollments e ON s.id = e.cid JOIN courses c ON e.sid = c.id
 )) AS missing_in_wrong,
 (SELECT COUNT(*) FROM (
    SELECT s.name, c.name FROM students s
      JOIN enrollments e ON s.id = e.cid JOIN courses c ON e.sid = c.id
    EXCEPT
    SELECT s.name, c.name FROM students s
      JOIN enrollments e ON s.id = e.sid JOIN courses c ON e.cid = c.id
 )) AS rows_that_are_fake;""",
  where="第3课④ 那张假数据卡的下半句 —— 用 SQL 自己证明",
  gotcha="左边 = 正确结果里有、接反结果里没有的（**漏了 2 行**）；右边 = 接反结果凭空多出来的（**假了 2 行**）。⇒ 只数行数永远发现不了，必须看内容")

C("sql.diagnose", "sql", "SQL", "本周", "诊断三步：先数绳子，再数结果",
  "① 单独数绳子表 ② 数 JOIN 结果 ③ 两数一致不算过关，再挑一行核对内容",
  "SELECT (SELECT COUNT(*) FROM enrollments) AS rope_rows,\n       (SELECT COUNT(*) FROM students s JOIN enrollments e ON s.id = e.sid) AS join_rows;",
  where="第3课⑥ · 本课最实用的迁移技能",
  gotcha="数字对不上（空 / 多很多）→ 几乎一定是 ON；数字**对得上**也可能内容错（id 重叠时）")

C("sql.left_join", "sql", "SQL", "本周", "LEFT JOIN",
  "左表一行都不能丢；右表配不上就整行填 NULL",
  "SELECT s.name, e.cid, e.grade\nFROM students s LEFT JOIN enrollments e ON s.id = e.sid;",
  where="第3课⑤ 换皮3 · 统计时最常见",
  gotcha="把 `LEFT` 去掉，**没选课的人会整个消失** —— 人数从 5 变 4，而且不报错")

C("sql.inner_vs_left", "sql", "SQL", "本周", "INNER vs LEFT：差在哪一行",
  "同一条查询，只差 `LEFT` 四个字母，结果少一行",
  "SELECT s.name FROM students s JOIN enrollments e ON s.id = e.sid;",
  where="对照上一张卡看：5 个人变成了 4 个人，小美没了",
  gotcha="要「一个都不漏」的清单（点名、对账、覆盖率）时必须 LEFT")

C("sql.subquery", "sql", "SQL", "以后", "子查询",
  "把一条 SELECT 的结果当另一条的条件用",
  "SELECT name FROM courses\nWHERE id IN (SELECT cid FROM enrollments WHERE grade > 85);",
  where="两步查询懒得写两遍时",
  gotcha="`IN (子查询)` 里如果出现 NULL，`NOT IN` 会整体返回空 —— 拿不准就用 `EXISTS`")

C("sql.union", "sql", "SQL", "以后", "UNION",
  "上下摞两条结果集；UNION 去重，UNION ALL 不去重（也更快）",
  "SELECT name FROM students WHERE class = '讯飞班'\nUNION\nSELECT name FROM students WHERE id <= 3;",
  where="合并两张结构相同的表（比如两个月的日志）",
  gotcha="两边**列数必须一样**，列名以第一条为准 —— 列对不齐时不报错，只会悄悄错位")

C("sql.tables", "sql", "SQL", "本周", "看这个库有哪些表",
  "不用装数据库工具，一条 SQL 就能看清家底",
  "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name;",
  where="第3课① 「这库里一共几张表」那道题的正确做法",
  gotcha="`sqlite_master` 是 SQLite 专有；MySQL 里叫 `SHOW TABLES`")

C("sql.pragma", "sql", "SQL", "本周", "看一张表的结构",
  "列名、类型、是否主键，一条 PRAGMA 全给你",
  "PRAGMA table_info(enrollments);",
  where="忘了列名时先看这个，别猜",
  gotcha="`PRAGMA` 不是标准 SQL（且不吃 `?` 占位符）—— 表名只能拼字符串，只用于自己写死的表名")

C("sql.create_table", "sql", "SQL", "本周", "CREATE TABLE",
  "并列三件事：列定义、主键、外键约束",
  "CREATE TABLE enrollments_new (\n    sid   INTEGER NOT NULL REFERENCES students(id),\n    cid   INTEGER NOT NULL REFERENCES courses(id),\n    grade REAL,\n    PRIMARY KEY (sid, cid)\n);",
  where="第3课③ · D8 作业的第一件事",
  gotcha="**复合主键** `PRIMARY KEY (sid, cid)` 直接防住「同一个人重复选同一门课」—— 比在 Python 里查一遍再插可靠",
  verify="PRAGMA table_info(enrollments_new);")

C("sql.insert", "sql", "SQL", "本周", "INSERT INTO",
  "列名写全，值用 `?` 占位（Python 里）",
  "INSERT INTO students (id, name, class) VALUES (6, '小七', '计科1班');",
  where="D8 作业：插 3 行数据",
  gotcha="列名和值**数量必须一致**，否则报 `table has N columns but M values were supplied`",
  verify="SELECT * FROM students WHERE id = 6;")

C("sql.update", "sql", "SQL", "本月", "UPDATE … WHERE",
  "改数据。**没有 WHERE 就是改全表**（没有撤销）",
  "UPDATE enrollments SET grade = 90 WHERE sid = 3 AND cid = 5;",
  where="补分数、改状态",
  gotcha="养成习惯：先把 `WHERE` 那段单拎出来 `SELECT` 一遍，确认命中行数，再改成 UPDATE",
  verify="SELECT sid, cid, grade FROM enrollments WHERE sid = 3 AND cid = 5;")

C("sql.delete", "sql", "SQL", "本月", "DELETE FROM … WHERE",
  "删行。同样：**没有 WHERE 就是清空整张表**",
  "DELETE FROM students WHERE id = 5;",
  where="删脏数据",
  gotcha="删之前先 `SELECT COUNT(*)`；真删表用 `DROP TABLE`（连表结构一起没）",
  verify="SELECT COUNT(*) AS left_rows FROM students;")

# ══════════════════════════════════════════════════════════════════════
# Python · sqlite3（cat=sqlite3）
# ══════════════════════════════════════════════════════════════════════
C("py.sqlite_skeleton", "py", "sqlite3", "本周", "六行骨架：连接 → 游标 → 执行 → 取 → 关",
  "连 Python 和数据库的全部动作就这六行",
  """import sqlite3
conn = sqlite3.connect(":memory:")          # 文件路径；:memory: = 内存库
cur  = conn.cursor()
cur.execute("CREATE TABLE t (x)")
cur.execute("INSERT INTO t VALUES (1), (2)")
conn.commit()                               # 写操作必须 commit
for row in cur.execute("SELECT x FROM t"):
    print(row)
conn.close()""",
  where="第3课 · 所有 SQL 作业的外壳",
  gotcha="`commit()` 忘写的后果见下一张卡 —— 它和 `close()` 是**两件事**")

C("py.sqlite_commit", "py", "sqlite3", "本周", "commit() vs close()：谁在丢数据",
  "P-014 的实测：换一个连接去读，看数据还在不在",
  """import sqlite3, tempfile, os, shutil
d = tempfile.mkdtemp(); p = os.path.join(d, "k.db")

c = sqlite3.connect(p); c.execute("CREATE TABLE t(x)")
c.execute("INSERT INTO t VALUES (1)")
c.close()                                   # 只 close，不 commit
c2 = sqlite3.connect(p)
print("commit ✗ / close ✓  → 另一个连接读到", c2.execute("SELECT COUNT(*) FROM t").fetchone()[0], "行")
c2.close()

c = sqlite3.connect(p); c.execute("INSERT INTO t VALUES (2)")
c.commit(); c.close()                       # 先 commit，再 close
c2 = sqlite3.connect(p)
print("commit ✓ / close ✓  → 另一个连接读到", c2.execute("SELECT COUNT(*) FROM t").fetchone()[0], "行")
c2.close(); shutil.rmtree(d, ignore_errors=True)""",
  where="第3课① 检索题（当场答错的那道）· P-014",
  gotcha="**丢数据的凶手是 `commit`，不是 `close`。** `close()` 忘写的代价是占资源（见下张卡），不是丢数据")

C("py.sqlite_close", "py", "sqlite3", "本周", "close() 忘了写会怎样",
  "连接不关 → 文件被锁住 → 连删都删不掉",
  """import sqlite3, tempfile, os, shutil
d = tempfile.mkdtemp(); p = os.path.join(d, "k.db")
c = sqlite3.connect(p); c.execute("CREATE TABLE t(x)"); c.commit()
try:
    os.remove(p)                            # 连接还开着，Windows 不让删
    print("删掉了（没锁）")
except PermissionError as e:
    print("PermissionError:", e)
c.close()
os.remove(p)                                # 关掉之后再删就成功了
print("close 之后再删：成功")
shutil.rmtree(d, ignore_errors=True)""",
  where="P-014 的另一半：close 的真实代价",
  gotcha="Linux/Mac 上删得掉，**只有 Windows 会当场报 `WinError 32`** —— 所以这个坑在 Windows 上反而更容易被发现")

C("py.sqlite_fetch", "py", "sqlite3", "本周", "fetchone / fetchall / 直接遍历",
  "三种取结果的方式，选中一条就不可能再回头",
  """import sqlite3
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE t(x)")
conn.executemany("INSERT INTO t VALUES (?)", [(1,), (2,), (3,)])
cur = conn.cursor()
cur.execute("SELECT x FROM t")
print("fetchone →", cur.fetchone())         # 拿走第 1 行，游标前移
print("fetchall →", cur.fetchall())         # 剩下的全拿走
cur.execute("SELECT x FROM t")
print("遍历     →", [r[0] for r in cur])
conn.close()""",
  where="取查询结果",
  gotcha="游标是**一次性**的：`fetchone()` 之后再 `fetchall()` 拿不到已经取走的那行。要重复用就把结果存进 list")

C("py.sqlite_executemany", "py", "sqlite3", "本周", "executemany() 批量插入",
  "一次插 20 行，别写 20 条 execute",
  """import sqlite3
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE s(name TEXT, score REAL)")
rows = [("小明", 88.5), ("小红", 92.0), ("小刚", 76.5)]
conn.executemany("INSERT INTO s VALUES (?, ?)", rows)
conn.commit()
print(conn.execute("SELECT COUNT(*) FROM s").fetchone()[0], "行")
for r in conn.execute("SELECT * FROM s ORDER BY score DESC"):
    print(r)
conn.close()""",
  where="灌测试数据 / 批量写爬下来的数据",
  gotcha="参数是**一个可迭代对象**，每项对应一条语句；写成 `executemany(sql, (1,2))` 会把它当成两行单列")

C("py.sqlite_param", "py", "sqlite3", "本周", "`?` 占位符（防注入）",
  "值永远走参数，不要用 f-string 拼进 SQL",
  """import sqlite3
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE t(name TEXT)"); conn.execute("INSERT INTO t VALUES ('小明')")
who = "小明' OR '1'='1"                     # 想注入的人会这么输
n = conn.execute("SELECT COUNT(*) FROM t WHERE name = ?", (who,)).fetchone()[0]
print("参数化（对）→", n, "行")
bad = "SELECT COUNT(*) FROM t WHERE name = '%s'" % who
n2 = conn.execute(bad).fetchone()[0]
print("拼字符串（错）→", n2, "行")
conn.close()""",
  where="所有带用户输入的查询",
  gotcha="**单元素也必须写成 `(who,)`** —— 少了逗号 `(who)` 只是个字符串，会被当成一个可迭代对象逐字符拆开，报 `Incorrect number of bindings`")

C("py.sqlite_row", "py", "sqlite3", "本周", "row_factory：按列名取值",
  "设一次 `row_factory`，之后 `row['name']` 就能用",
  """import sqlite3
conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row          # ← 就这一行
conn.execute("CREATE TABLE s(id INTEGER, name TEXT)")
conn.execute("INSERT INTO s VALUES (1, '小明')")
row = conn.execute("SELECT id, name FROM s").fetchone()
print("按下标 →", row[0], row[1])
print("按列名 →", row['id'], row['name'])
print("变字典 →", dict(row))
conn.close()""",
  where="结果列一多，下标就记不住了",
  gotcha="`row_factory` 设在 **connection** 上，不是 cursor 上（设 cursor 上是另一套写法）")

C("py.sqlite_with", "py", "sqlite3", "以后", "with：自动 commit / rollback",
  "`with conn:` 出块时自动提交，出异常自动回滚 —— 但**不会关连接**",
  """import sqlite3
conn = sqlite3.connect(":memory:")
with conn:                                  # 成功 → 自动 commit
    conn.execute("CREATE TABLE t(x)")
    conn.execute("INSERT INTO t VALUES (1)")
try:
    with conn:                              # 失败 → 自动 rollback
        conn.execute("INSERT INTO t VALUES (2)")
        raise ValueError("假装中途出错")
except ValueError as e:
    print("捕获到：", e)
print("表里剩", conn.execute("SELECT COUNT(*) FROM t").fetchone()[0], "行")
conn.close()""",
  where="写多步操作时不想每步都 commit",
  gotcha="`with conn:` ≠ `with sqlite3.connect() as conn:`。后者出块时**会关连接**，很多教程混着讲")

C("py.sqlite_error", "py", "sqlite3", "以后", "捕获数据库错误",
  "`IntegrityError` 是约束被违反，`OperationalError` 是表/列名写错",
  """import sqlite3
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE s(id INTEGER PRIMARY KEY, name TEXT UNIQUE)")
conn.execute("INSERT INTO s VALUES (1, '小明')")
try:
    conn.execute("INSERT INTO s VALUES (2, '小明')")   # name 重复
except sqlite3.IntegrityError as e:
    print("IntegrityError →", e)
try:
    conn.execute("SELECT * FROM 不存在的表")
except sqlite3.OperationalError as e:
    print("OperationalError →", e)
conn.close()""",
  where="爬虫/批量写数据时，重复行不该让整个程序崩",
  gotcha="两个异常都继承自 `sqlite3.Error`，图省事可以只 `except sqlite3.Error`；但**不要裸 `except:`** —— 会把键盘中断也吞掉")

# ══════════════════════════════════════════════════════════════════════
# Python · 标准库（cat=标准库）
# ══════════════════════════════════════════════════════════════════════
C("py.json_dumps", "py", "标准库", "本月", "json.dumps",
  "Python 对象 → JSON 字符串（接口/存盘都用它）",
  """import json
d = {"name": "韩立", "score": 88.5, "tags": ["python", "sql"]}
print(json.dumps(d, ensure_ascii=False))
print(json.dumps(d, ensure_ascii=False, indent=2))""",
  where="调大模型 API 的请求体；把结果存成文件",
  gotcha="`ensure_ascii=False` 不加，中文会变成 `\\u97e9\\u7acb` —— 能用但没法看")

C("py.json_loads", "py", "标准库", "本月", "json.loads",
  "JSON 字符串 → Python 对象（大模型返回的就是个字符串）",
  """import json
s = '{"answer": 42, "ok": true, "items": [1, 2]}'
d = json.loads(s)
print(type(d).__name__, d["answer"], d["ok"], d["items"][1])
print("访问不存在的键 →", end=" ")
try:
    d["nope"]
except KeyError as e:
    print("KeyError", e)""",
  where="解析接口/大模型返回",
  gotcha="`loads` 吃字符串，`load` 吃文件对象 —— 差一个 s 是两种用法，报错信息很像（都叫 JSONDecodeError）")

C("py.json_file", "py", "标准库", "本月", "json.dump / json.load 直接读写文件",
  "省掉 open 那一步",
  """import json, tempfile, os, shutil
d = tempfile.mkdtemp(); p = os.path.join(d, "out.json")
with open(p, "w", encoding="utf-8") as f:
    json.dump({"n": 3, "who": "韩立"}, f, ensure_ascii=False)
with open(p, encoding="utf-8") as f:
    print("读回来 →", json.load(f))
shutil.rmtree(d, ignore_errors=True)""",
  where="把中间结果存盘，下次不用重跑",
  gotcha="**一定要写 `encoding='utf-8'`** —— Windows 默认编码不是 utf-8，中文会乱码或直接 `UnicodeEncodeError`")

C("py.open_read", "py", "标准库", "本月", "with open(...) 读文件",
  "`with` 会自动关文件，不用手动 close",
  """import tempfile, os, shutil
d = tempfile.mkdtemp(); p = os.path.join(d, "a.txt")
open(p, "w", encoding="utf-8").write("第一行\\n第二行\\n")
with open(p, encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        print(i, line.rstrip())          # rstrip 去掉行尾换行
shutil.rmtree(d, ignore_errors=True)""",
  where="读日志/读 txt 语料",
  gotcha="`line` 自带 `\\n`，直接 print 会多一个空行 —— 要么 `rstrip()`，要么 print 时加 `end=''`")

C("py.open_write", "py", "标准库", "本月", "open(..., 'w') 写文件",
  "`w` 覆盖、`a` 追加，都要显式写编码",
  """import tempfile, os, shutil
d = tempfile.mkdtemp(); p = os.path.join(d, "log.txt")
with open(p, "w", encoding="utf-8") as f:
    f.write("第一次\\n")
with open(p, "a", encoding="utf-8") as f:      # a = 追加，不会覆盖
    f.write("第二次\\n")
print(open(p, encoding="utf-8").read().strip())
shutil.rmtree(d, ignore_errors=True)""",
  where="记运行日志 / 导出结果",
  gotcha="**`'w'` 会立刻清空原文件** —— 想追加却写了 `'w'`，上一次的结果就没了（且没有提示）")

C("py.os_path", "py", "标准库", "本月", "os.path.join / exists",
  "拼路径永远用 join，别手写 `+ '/' +`",
  """import os
p = os.path.join("E:\\\\项目学习", "交互演示", "函数卡.html")
print(p)
print("存在吗 →", os.path.exists(p))
print("目录名 →", os.path.dirname(p))
print("文件名 →", os.path.basename(p))
print("扩展名 →", os.path.splitext(p)[1])""",
  where="所有涉及文件路径的代码",
  gotcha="`os.path.join('E:\\\\a', '/b')` 里第二个参数带开头的斜杠时，**前面的路径会被整个丢掉** —— 得到 `/b`")

C("py.os_makedirs", "py", "标准库", "本月", "os.makedirs(..., exist_ok=True)",
  "建多层目录；`exist_ok=True` 让「已存在」不报错",
  """import os, tempfile, shutil
d = tempfile.mkdtemp()
target = os.path.join(d, "导出", "2026-09")
os.makedirs(target, exist_ok=True)
os.makedirs(target, exist_ok=True)          # 第二次不报错
print("建好了 →", os.path.isdir(target))
shutil.rmtree(d, ignore_errors=True)""",
  where="写文件前确保目录存在（爬虫存图、导出报告）",
  gotcha="不写 `exist_ok=True`，跑第二遍就 `FileExistsError` —— 这是「只在第二次运行才炸」的经典 bug")

C("py.os_listdir", "py", "标准库", "本月", "os.listdir / glob 过滤",
  "列目录，再按后缀筛",
  """import os, tempfile, shutil
d = tempfile.mkdtemp()
for n in ["a.txt", "b.txt", "c.csv"]:
    open(os.path.join(d, n), "w").close()
names = os.listdir(d)
print("全部 →", sorted(names))
print("只要 txt →", sorted(n for n in names if n.endswith(".txt")))
shutil.rmtree(d, ignore_errors=True)""",
  where="批量处理一个文件夹里的文件",
  gotcha="`listdir` 给的是**文件名**不是完整路径 —— 要打开它得再 `join` 一次（这是最常见的「文件找不到」原因）")

C("py.pathlib", "py", "标准库", "以后", "pathlib.Path",
  "同一件事的现代写法：`/` 拼路径、`.suffix` 取后缀",
  """from pathlib import Path
p = Path("E:/项目学习") / "交互演示" / "函数卡.html"
print(p)
print("后缀 →", p.suffix, "｜ 名字 →", p.stem, "｜ 父目录 →", p.parent.name)
print("存在吗 →", p.exists(), "｜ 是文件吗 →", p.is_file())""",
  where="新写的脚本（老代码里 os.path 也常见，两种都要能读）",
  gotcha="`Path` 对象不能直接丢给老函数当字符串用 —— 必要时 `str(p)`")

C("py.re_findall", "py", "标准库", "本月", "re.findall",
  "在一段文本里捞出所有符合模式的片段",
  """import re
text = "订单 A1001 金额 88 元；订单 A1002 金额 192 元"
print("所有订单号 →", re.findall(r"A\\d{4}", text))
print("所有数字   →", re.findall(r"\\d+", text))
print("成对取     →", re.findall(r"(A\\d{4}).*?(\\d+) 元", text))""",
  where="从网页/日志里提取字段",
  gotcha="模式字符串前面**一定要加 r**（原始字符串）—— 不加的话 `\\d` 会被 Python 先当成转义字符处理")

C("py.re_search", "py", "标准库", "本月", "re.search + 分组",
  "只找第一个；用括号分组把想要的部分单独取出来",
  """import re
m = re.search(r"(\\d{4})-(\\d{2})-(\\d{2})", "今天是 2026-09-24 周四")
if m:
    print("整段 →", m.group(0))
    print("年 →", m.group(1), "｜ 月 →", m.group(2), "｜ 日 →", m.group(3))
    print("命名分组写法 →", re.search(r"(?P<y>\\d{4})", "2026").group("y"))
print("没找到时 →", re.search(r"zzz", "abc"))""",
  where="解析日期、版本号、URL 参数",
  gotcha="`re.search` 找不到时返回 **None**，直接 `.group()` 会 `AttributeError` —— 先 `if m:`")

C("py.re_sub", "py", "标准库", "本月", "re.sub",
  "按模式替换（清洗文本的主力）",
  """import re
s = "价格：￥1,299.00 元  （含税）"
print(re.sub(r"[￥,]", "", s))
print(re.sub(r"\\s+", " ", s).strip())
print(re.sub(r"(\\d+)\\.(\\d+)", r"\\2.\\1", "3.14"))     # 分组反向引用""",
  where="清洗爬下来的文本 / 归一化输入",
  gotcha="`re.sub` 默认**替换所有**匹配；只想换第一个要加 `count=1`")

C("py.datetime_now", "py", "标准库", "本月", "datetime.now() / strftime",
  "取当前时间，格式化成字符串",
  """from datetime import datetime
now = datetime.now()
print("原样 →", now)
print("常用 →", now.strftime("%Y-%m-%d %H:%M:%S"))
print("文件名用 →", now.strftime("%Y%m%d-%H%M"))
print("星期日历 →", now.strftime("%Y-%m-%d %A"))""",
  where="给导出文件起名；记日志时间戳",
  gotcha="Windows 上 `strftime('%Y-%m-%d')` 没问题，但**文件名里不能有 `:`** —— `%H:%M` 直接拿去当文件名会失败")

C("py.datetime_strptime", "py", "标准库", "本月", "strptime：字符串 → 时间",
  "把文本日期变成能计算的对象（转回来才能减）",
  """from datetime import datetime
d = datetime.strptime("2026-09-21", "%Y-%m-%d")
print("解析 →", d, type(d).__name__)
print("换一种格式 →", d.strftime("%Y年%m月%d日"))
try:
    datetime.strptime("2026/09/21", "%Y-%m-%d")
except ValueError as e:
    print("格式对不上 →", e)""",
  where="算复习到期日 / 算实习倒计时",
  gotcha="格式串必须和输入**严格一致**（`2026/09/21` 配 `%Y-%m-%d` 会报 `does not match format`）")

C("py.timedelta", "py", "标准库", "本月", "timedelta：日期加减",
  "算差几天、N 天后是哪天",
  """from datetime import date, timedelta
anchor = date(2026, 9, 23)                  # 你的倒推起点
for n in (1, 3, 7, 30):
    print(f"第 {n:>2} 天 →", anchor + timedelta(days=n))
gap = date(2027, 3, 1) - anchor
print("到 2027.03 还有", gap.days, "天 ≈", gap.days // 7, "周")""",
  where="1-3-7-30 复习日程；倒推链",
  gotcha="`date - date` 得到 `timedelta`，取天数用 `.days`；`//7` 是**向下取整**的周数（不是四舍五入）")

C("py.counter", "py", "标准库", "以后", "collections.Counter",
  "数词频，一行搞定（比手写字典 +1 干净）",
  """from collections import Counter
words = "数据 数据库 数据 模型 数据库 数据".split()
c = Counter(words)
print(c)
print("前三 →", c.most_common(3))
print("'数据' 出现 →", c["数据"], "次")
print("没出现过的词 →", c["不存在"], "次（不报错，返回 0）")""",
  where="统计标签分布 / 看数据里哪类最多",
  gotcha="取不存在的键返回 **0 而不是 KeyError** —— 好处是省事，坏处是拼错词也照样得 0，不报错")

C("py.defaultdict", "py", "标准库", "以后", "defaultdict(list)：分组",
  "按 key 把东西塞进不同的桶，不用先判断 key 在不在",
  """from collections import defaultdict
rows = [("讯飞班", "韩立"), ("计科1班", "小红"), ("讯飞班", "小明")]
g = defaultdict(list)
for cls, name in rows:
    g[cls].append(name)
print(dict(g))
print("不存在的班 →", g["不存在"], "（自动建了空 list）")""",
  where="把一堆 (分类, 内容) 聚成 {分类: [内容]}",
  gotcha="读一个不存在的 key 会**顺手创建它** —— 遍历时边读边写会报 `dictionary changed size during iteration`")

C("py.random", "py", "标准库", "以后", "random.choice / sample / randint",
  "抽一个、抽几个不重复的、抽一个整数",
  """import random
random.seed(42)                             # 固定种子 → 结果可复现
print("抽一个 →", random.choice(["A", "B", "C"]))
print("抽2个不重复 →", random.sample(range(1, 50), 2))
print("1~6 的整数 →", random.randint(1, 6))
random.shuffle(lst := [1, 2, 3, 4])
print("打乱 →", lst)""",
  where="造测试数据 / 切分训练集",
  gotcha="`random.seed(42)` 是**可复现**的关键 —— 不设种子，同样的代码每次都出不同结果，bug 就复现不了")

C("py.requests_sig", "py", "第三方", "以后", "requests.get（只看签名）",
  "HTTP 请求最常用的库。这条**只实测了签名**，没联网",
  """import inspect, requests
print("requests", requests.__version__)
print("get", inspect.signature(requests.get))
print("post 有 params/data/json →",
      all(k in inspect.signature(requests.post).parameters for k in ("params", "data", "json")))""",
  where="之后调接口 / 爬虫 / 调大模型 API",
  gotcha="⚠️ 这段**没有真的发请求**（不允许联网实测）。用法要点：`resp.status_code` 判断成败、`resp.json()` 取 JSON、`resp.text` 取原文、`timeout=` 一定要给（不给会永久挂住）",
  extra="[外源] 未联网验证")

C("py.pandas_sig", "py", "第三方", "以后", "pandas.read_csv（只看签名）",
  "读表格数据的事实标准。同样**只实测了签名**",
  """import inspect, pandas as pd
print("pandas", pd.__version__)
print("read_csv", inspect.signature(pd.read_csv))
df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
print(df.to_string(index=False))""",
  where="之后做数据分析 / 处理表格数据",
  gotcha="⚠️ 只验证了 DataFrame 构造，**没有真读 csv 文件**。要点：`encoding='utf-8'`（中文 csv 常是 `gbk`）、`dtype=` 防手机号被当数字",
  extra="[外源] 未读实际文件")

# ══════════════════════════════════════════════════════════════════════
# Python · 常用内置（cat=内置）
#   说明：内置函数**不做成"要背"的卡**（这工作区已关掉那条线）——
#   只留"写代码时天天撞到"的十来个，当**查询用**，不当背诵材料。
# ══════════════════════════════════════════════════════════════════════
C("bi.len_range", "py", "内置", "以后", "len / range",
  "len 数长度；range 造一串数字（Python 里**从 0 开始、不含结尾**）",
  """s = "数据库"
print("len →", len(s), "｜ range(3) →", list(range(3)), "｜ range(1,4) →", list(range(1, 4)))
print("倒着数 →", list(range(3, 0, -1)))
for i in range(len(s)):
    print(i, s[i])""",
  where="到处都在用",
  gotcha="`range(1, 5)` 是 1,2,3,4（**没有 5**）—— 差一个数的 bug 八成来自这里")

C("bi.enumerate", "py", "内置", "以后", "enumerate",
  "边遍历边拿到序号，别自己维护计数器",
  """for i, name in enumerate(["小明", "小红"], start=1):
    print(i, name)
print("不加 start →", list(enumerate("ab")))""",
  where="要「第几条」的时候",
  gotcha="`enumerate(x, start=1)` 才是从 1 开始；默认从 **0** 开始")

C("bi.zip", "py", "内置", "以后", "zip",
  "把两个列表按位置配对，一次遍历两个",
  """names = ["小明", "小红", "小刚"]
scores = [88, 92, 76]
for n, s in zip(names, scores):
    print(n, s)
print("配对成字典 →", dict(zip(names, scores)))
print("长度不等时 →", list(zip([1, 2, 3], "ab")))""",
  where="两个来源的数据要一起处理",
  gotcha="长度不等时**按短的截断，不报错** —— 数据对不齐时会静默丢数据（Python 3.10+ 可用 `strict=True` 让它报错）")

C("bi.sorted_key", "py", "内置", "本月", "sorted(key=…)",
  "排序的万能钥匙：`key` 决定「按什么排」",
  """rows = [("小明", 88.5), ("小红", 92.0), ("小刚", 76.5)]
print("按分数 →", sorted(rows, key=lambda r: r[1], reverse=True))
d = {"b": 2, "a": 3, "c": 1}
print("字典按值排 →", sorted(d.items(), key=lambda kv: kv[1]))
print("多级排序 →", sorted(rows, key=lambda r: (-r[1], r[0])))""",
  where="排行榜 / 按时间排日志 / 结果稳定输出",
  gotcha="`key=` 收到的是**函数**，写 `key=r[1]` 会直接报错；`list.sort()` 是原地改，`sorted()` 返回新列表")

C("bi.sum_min_max", "py", "内置", "以后", "sum / min / max",
  "三个聚合内置，都能配 `key=` 和默认值",
  """nums = [3, 1, 4, 1, 5]
print("sum →", sum(nums), "｜ min →", min(nums), "｜ max →", max(nums))
print("带初值 →", sum(nums, 100))
print("空列表 →", sum([]), end=" / ")
try:
    min([])
except ValueError as e:
    print("min 报错：", e)
print("按 key 取最大 →", max(["aa", "bbb", "c"], key=len))""",
  where="算总分、找最长的那条",
  gotcha="`sum([])` 是 0，但 **`min([])` / `max([])` 会报 ValueError** —— 空列表要先用 `default=`（3.4+）或自己判断")

C("bi.any_all", "py", "内置", "以后", "any / all",
  "一串条件里「有没有一个真的」 / 「是不是全都真」",
  """nums = [2, 4, 6, 8]
print("全是偶数 →", all(n % 2 == 0 for n in nums))
print("有大于 5 的 →", any(n > 5 for n in nums))
print("空列表的默认 →", any([]), all([]))""",
  where="批量校验（检查所有字段都非空）",
  gotcha="空列表时 `all([])` 是 **True**（「全都满足」在逻辑上成立）—— 拿它当「数据没问题」的判断会漏掉空数据的情况")

C("bi.type_cast", "py", "内置", "本月", "int / float / str 类型转换",
  "输入永远是字符串，要算就得先转",
  """print(int("42") + 1, float("3.5") * 2, str(42) + "!")
print("取整 →", int(3.9), "（截断不是四舍五入）｜ round →", round(3.9))
print("转不了会炸 →", end=" ")
try:
    int("abc")
except ValueError as e:
    print("ValueError:", e)""",
  where="读用户输入、读文件里的数字",
  gotcha="`int(3.9)` 是 **3**（截断）；要四舍五入用 `round()`。`int('3.5')` 也会报错，得先 `float()`")

C("bi.fstring", "py", "内置", "本月", "f-string 格式化",
  "在字符串里直接写变量，还能控制小数位和对齐",
  """name, score = "韩立", 88.4567
print(f"{name} 的分数是 {score}")
print(f"保留两位 → {score:.2f}")
print(f"百分比   → {score / 100:.1%}")
print(f"右对齐   → |{name:>8}|｜左对齐 → |{name:<8}|｜补零 → {7:03d}")""",
  where="拼日志、拼输出的每一处",
  gotcha="f-string 只在字符串**前面有 f** 时生效；`\\n` 在 f-string 里是换行，但**表达式里不能有反斜杠**（3.12 前）")

# ══════════════════════════════════════════════════════════════════════
# 执行 + 输出
# ══════════════════════════════════════════════════════════════════════
def disp_w(s: str) -> int:
    """显示宽度：中日韩全角字符算 2 格，等宽字体里才对得齐。"""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s: str, w: int) -> str:
    return s + " " * max(0, w - disp_w(s))


def fmt_rows(cols: list[str], rows: list[tuple]) -> str:
    """把查询结果排成等宽文本表（中文对齐靠 disp_w）。"""
    cells = [[("NULL" if v is None else str(v)) for v in r] for r in rows]
    widths = [disp_w(c) for c in cols]
    for r in cells:
        for i, v in enumerate(r):
            widths[i] = max(widths[i], disp_w(v))
    head = " | ".join(pad(c, widths[i]) for i, c in enumerate(cols))
    sep = "-+-".join("-" * w for w in widths)
    body = [" | ".join(pad(v, widths[i]) for i, v in enumerate(r)) for r in cells]
    return "\n".join([head, sep, *body, f"（{len(rows)} 行）"])


def run_sql(code: str, verify: str | None) -> str:
    con = sqlite3.connect(":memory:")
    try:
        con.executescript(SEED)
        cur = con.cursor()
        cur.execute(code)
        if verify:
            cur.execute(verify)
        if cur.description:
            return fmt_rows([d[0] for d in cur.description], cur.fetchall())
        return f"-- 影响 {cur.rowcount} 行"
    finally:
        con.close()


def run_py(code: str) -> str:
    buf = io.StringIO()
    ns = {"__name__": "__card__"}
    with contextlib.redirect_stdout(buf):
        exec(compile(code, "<card>", "exec"), ns)
    return buf.getvalue().rstrip("\n")


def main() -> int:
    check_only = "--check" in sys.argv
    bad: list[str] = []
    for c in CARDS:
        try:
            c["out"] = run_sql(c["code"], c["verify"]) if c["lang"] == "sql" else run_py(c["code"])
            c["ok"] = True
            if c["err"]:
                bad.append(f"{c['id']}: expected an error but it ran fine")
        except Exception as e:                                   # noqa: BLE001
            c["out"] = f"{type(e).__name__}: {e}"
            c["ok"] = False
            if not c["err"]:
                bad.append(f"{c['id']}: {type(e).__name__}: {e}")

    ids = [c["id"] for c in CARDS]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        bad.append(f"duplicate ids: {sorted(dup)}")

    n_err = sum(1 for c in CARDS if c["err"])
    by_cat: dict[str, int] = {}
    by_stage: dict[str, int] = {}
    for c in CARDS:
        by_cat[c["cat"]] = by_cat.get(c["cat"], 0) + 1
        by_stage[c["stage"]] = by_stage.get(c["stage"], 0) + 1

    print(f"cards={len(CARDS)}  ran_ok={sum(1 for c in CARDS if c['ok'])}  "
          f"on_purpose_errors={n_err}")
    print("by_cat   " + "  ".join(f"{k}={v}" for k, v in sorted(by_cat.items())))
    print("by_stage " + "  ".join(f"{k}={v}" for k, v in sorted(by_stage.items())))
    if bad:
        print("\n!! UNEXPECTED FAILURES")
        for b in bad:
            print("  -", b)
    if check_only:
        return 1 if bad else 0

    payload = json.dumps(CARDS, ensure_ascii=False, indent=1)
    OUT.write_text(
        "/* 自动生成 —— 不要手改这个文件！\n"
        "   事实源：tools/build_fn_cards.py（卡片文字 + 示例代码）\n"
        "   这里是它真跑一遍之后的输出，每张卡带 ok / out 两个字段。\n"
        "   重跑：python tools/build_fn_cards.py */\n"
        f"window.LAB_FN_CARDS = {payload};\n",
        encoding="utf-8")
    print(f"\nwrote {OUT.name}  {OUT.stat().st_size} bytes")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
