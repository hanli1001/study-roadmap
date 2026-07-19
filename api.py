"""
═══════════════════════════════════════════════════════════
中医方剂 API —— FastAPI 入门教程（零基础版）
═══════════════════════════════════════════════════════════

启动：conda activate prescription-api && uvicorn api:app --reload
测试：浏览器打开 http://localhost:8000/docs

全文主线类比：API = 餐厅服务员
    你（浏览器）点菜 → 服务员（FastAPI）→ 后厨（SQLite）→ 上菜（JSON）
═══════════════════════════════════════════════════════════

【本文件的阅读约定】
  每出现一个你不认识的函数/语法，我都会配上这样的卡片：

  ┌─────────────────────────────────────────────┐
  │ 【函数：xxx()】                              │
  │ 作用：一句话说清它干什么                     │
  │ 原型：函数签名，标出哪些参数必填哪些可选      │
  │ 返回：返回什么类型的东西                     │
  │ 类比：生活里像什么                           │
  │ 陷阱：常见的踩坑原因                         │
  └─────────────────────────────────────────────┘

  第一次出现会给完整卡片，后面再出现只给一句提示。
═══════════════════════════════════════════════════════════
"""

# ╔══════════════════════════════════════════════════════════╗
# ║  第 1 部分：导入 —— 从工具箱里拿工具                     ║
# ╚══════════════════════════════════════════════════════════╝

import sqlite3
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ┌─────────────────────────────────────────────────────────┐
# │ 【语法：import xxx】                                     │
# │ 作用：把别人写好的代码拿过来用                           │
# │ 类比：你要做饭，先去超市买调料——import 就是去超市       │
# │ 规则：import 写在文件最上面，只写一次                    │
# │                                                        │
# │ 【语法：from xxx import yyy】                           │
# │ 作用：只从某个包里拿特定工具，不全部搬过来              │
# │ 类比：不去整个超市，只买一瓶酱油                        │
# │                                                        │
# │ 本例中导入的工具：                                      │
# │   sqlite3       = Python 自带，操作 SQLite 数据库       │
# │   FastAPI       = 创建 Web 应用的核心类                 │
# │   Query         = 处理 URL 问号后面的参数               │
# │   JSONResponse  = 返回 JSON + 指定 HTTP 状态码         │
# └─────────────────────────────────────────────────────────┘


# ╔══════════════════════════════════════════════════════════╗
# ║  第 2 部分：创建 FastAPI 应用实例                        ║
# ╚══════════════════════════════════════════════════════════╝

class HerbIn(BaseModel):
    name: str  # 药材名，必填
    dosage: str  # 用量，必填


class PrescriptionIn(BaseModel):
    name: str  # 方剂名，必填
    category: str  # 分类，必填
    source: str  # 出处，必填
    symptoms: str  # 主治，必填
    herbs: list[HerbIn]  # 药材列表，每个元素是{name: "...", dosage: "..."}

app = FastAPI(title="中医方剂查询 API", version="1.0")

# ┌─────────────────────────────────────────────────────────┐
# │ 【函数：FastAPI()】                                      │
# │ 作用：创建一个 Web 应用对象——所有路由都挂它上面          │
# │ 原型：FastAPI(title="名字", version="版本号")            │
# │       参数都是可选的（不写也行）                         │
# │ 返回：一个 FastAPI 应用实例（赋给 app 变量）             │
# │ 类比：开了一家空餐厅，title 是门口招牌                   │
# │                                                        │
# │ 后续使用：                                              │
# │   @app.get(...)  →  在 app 上加一个接口                  │
# │   uvicorn api:app →  uvicorn 找到文件里的 app 来启动     │
# └─────────────────────────────────────────────────────────┘


# ╔══════════════════════════════════════════════════════════╗
# ║  第 3 部分：get_db() —— 数据库连接工厂                  ║
# ╚══════════════════════════════════════════════════════════╝

def get_db():
    """
    每次 HTTP 请求来了，调用这个函数拿到一个数据库连接。
    请求处理完必须 close() 还回去。

    类比：服务员每次进后厨都拿一个新托盘，出来时把托盘放回架子。
    """
    conn = sqlite3.connect("prescriptions.db")
    conn.row_factory = sqlite3.Row
    return conn

# ┌─────────────────────────────────────────────────────────┐
# │ 【函数：sqlite3.connect(文件路径)】                      │
# │ 作用：打开（或创建）一个 SQLite 数据库文件                 │
# │ 原型：sqlite3.connect("文件名.db")                       │
# │       参数：数据库文件路径（字符串），必填               │
# │ 返回：一个 Connection 对象（"连接手柄"）                  │
# │ 类比：拿到后厨的钥匙                                     │
# │ 陷阱：文件不存在会自动创建，不会报错                     │
# │                                                        │
# │ 【语法：conn.row_factory = sqlite3.Row】                │
# │                                                        │
# │ 先搞清楚两个概念（OOP 基础）：                          │
# │   类(class) = 饼干模具。模具不是饼干，是"造饼干的模板"。 │
# │   对象(object) = 模具压出来的具体饼干。                  │
# │   属性 = 对象上的设置项（conn.row_factory）。            │
# │   方法 = 对象能做的事（conn.execute()）。                │
# │                                                        │
# │ 回到这行代码：                                          │
# │   conn.row_factory = sqlite3.Row                       │
# │   ↑对象  ↑属性           ↑类（模具）                    │
# │                                                        │
# │ 为什么 Row 后面没有括号 ()？                             │
# │   sqlite3.Row   → 把 Row 这个"模具"本身传进去           │
# │   sqlite3.Row() → 调用模具压一个饼干出来（这里不需要）   │
# │   row_factory 要的是"模具"，好让它以后自己压饼干。       │
# │                                                        │
# │ 设置了之后发生什么？                                    │
# │   每次 execute() 查到一行数据时，SQLite 内部会调：       │
# │   sqlite3.Row(cursor, (1,"麻黄汤","解表剂"))            │
# │   用 Row 模具把原始元组压成支持 row["name"] 的 Row 对象  │
# │                                                        │
# │ 作用：让查询结果支持 row["列名"] 取值                    │
# │ 默认：查询结果只能用下标 row[0], row[1]                  │
# │ 设置后：可以用 row["name"] 像字典一样取值                │
# │ 类比：给快递单上的每个格子贴上标签"姓名""电话""地址"     │
# │ 陷阱：不设这个 → row["name"] 报 TypeError               │
# └─────────────────────────────────────────────────────────┘


# ╔══════════════════════════════════════════════════════════╗
# ║  路由 0：GET /    ——   API 目录页                       ║
# ╚══════════════════════════════════════════════════════════╝

@app.get("/")
def root():
    """
    客人进餐厅先看菜单。打开 http://localhost:8000/ 就是这个。

    例题（实际返回的 JSON）：
    {
      "api": "中医方剂查询系统",
      "endpoints": { ... }
    }
    """
    return {
        "api": "中医方剂查询系统",
        "endpoints": {
            "GET /prescriptions": "所有方剂列表",
            "GET /prescriptions/{id}": "单首方剂详情",
            "POST /prescriptions": "新增方剂",
            "GET /herbs": "所有药材列表",
            "GET /herbs/{name}/prescriptions": "药材出现在哪些方剂中",
        },
    }
    #  ↑ FastAPI 自动把这个 dict 转成 JSON 字符串发给浏览器

# ┌─────────────────────────────────────────────────────────┐
# │ 【语法：@app.get("/xxx")  ——  装饰器】                   │
# │                                                        │
# │ 作用：把下面这个函数注册为"处理 GET /xxx 请求的人"       │
# │ 类比：餐厅老板在菜单上贴了一张标签：                     │
# │       "客人点 /prescriptions → 叫张师傅(下面这个函数)"    │
# │                                                        │
# │ 使用规则：                                              │
# │   1. @ 写在函数定义的正上方，不能空行隔开               │
# │   2. 一个函数只能有一个 @app.xxx 装饰器                  │
# │   3. 括号里写 URL 路径，必须是字符串                    │
# │   4. 函数叫什么名字无所谓（FastAPI 不关心）              │
# │                                                        │
# │ 常见变体：                                              │
# │   @app.get("/xxx")     → 处理 GET 请求（查询）          │
# │   @app.post("/xxx")    → 处理 POST 请求（新增）         │
# │   @app.put("/xxx")     → 处理 PUT 请求（修改）          │
# │   @app.delete("/xxx")  → 处理 DELETE 请求（删除）       │
# └─────────────────────────────────────────────────────────┘


# ╔══════════════════════════════════════════════════════════╗
# ║  路由 1：GET /prescriptions    ——   方剂列表             ║
# ╚══════════════════════════════════════════════════════════╝

@app.get("/prescriptions")
def list_prescriptions(
    category: str | None = Query(None)
):
    """返回方剂列表。传 ?category=解表剂 可选筛选。"""

    conn = get_db()

    if category:
        rows = conn.execute(
            "SELECT id, name, category, source, symptoms "
            "FROM prescriptions WHERE category = ?",
            (category,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, name, category, source, symptoms "
            "FROM prescriptions"
        ).fetchall()

    conn.close()
    return [dict(r) for r in rows]

# ┌─────────────────────────────────────────────────────────┐
# │ 【语法：变量: 类型A | 类型B = 默认值】                   │
# │                                                        │
# │ 这是 Python 3.10+ 的"联合类型注解" + "默认参数值"。     │
# │                                                        │
# │ category: str | None = Query(None)                     │
# │ ────────  ──────────   ───────────                     │
# │   参数名   类型标注         默认值                       │
# │                                                        │
# │ 拆解：                                                  │
# │   str | None → 这个参数可以是 str，也可以是 None        │
# │   = Query(None) → 不传这个参数时默认值就是 None          │
# │                                                        │
# │ 调用方式（自动的，FastAPI 处理）：                       │
# │   /prescriptions                  → category = None    │
# │   /prescriptions?category=解表剂   → category = "解表剂" │
# └─────────────────────────────────────────────────────────┘

# ┌─────────────────────────────────────────────────────────┐
# │ 【函数：Query(默认值)】                                  │
# │ 作用：声明"这个参数从 URL 问号后面取"                     │
# │ 原型：Query(default_value)                              │
# │       参数：默认值（不传这个参数时用什么）               │
# │ 返回：FastAPI 内部使用的参数声明对象                     │
# │ 类比：菜单上标了"可选"的配菜                             │
# │ 陷阱：Query() 必须写到默认值的位置（= 右边），不是独立的  │
# │                                                        │
# │ 【对比：路径参数 vs 查询参数】                           │
# │   {pid} 写 URL 路径里 → 函数参数直接写 pid: int         │
# │   ?category= 写 URL 问号后 → 函数参数写 xxx = Query()   │
# └─────────────────────────────────────────────────────────┘

# ┌─────────────────────────────────────────────────────────┐
# │ 【函数：conn.execute(SQL语句, 参数元组)】                │
# │ 作用：把一条 SQL 发给数据库执行                          │
# │ 原型：conn.execute(sql: str, parameters: tuple)          │
# │       第1个参数：SQL 字符串（必填）                      │
# │       第2个参数：替换 ? 占位符的值的元组（可选）         │
# │ 返回：一个 Cursor 对象（可接着调 .fetchall() 等）        │
# │ 类比：服务员对后厨喊："把那道麻黄汤的配料单给我"         │
# │                                                        │
# │ 【占位符规则】                                          │
# │   SQL 里写 ? → 参数元组里按顺序填值                     │
# │   SQL 里有 3 个 ? → 参数元组必须有 3 个元素             │
# │   例：execute("SELECT * FROM t WHERE a=? AND b=?", (x,y))│
# │                                                        │
# │ 【单元素元组陷阱】                                      │
# │   (category)    ← 括号没逗号，Python 认为这是普通括号   │
# │   (category,)   ← 有逗号，Python 认为是单元素元组 ✅    │
# │   报错信息：expected 1 argument, got N                   │
# └─────────────────────────────────────────────────────────┘

# ┌─────────────────────────────────────────────────────────┐
# │ 【函数：.fetchall()】                                    │
# │ 作用：把查询结果全部取出来，一次性返回                    │
# │ 调用方式：conn.execute(...).fetchall()  ← 链式调用       │
# │ 返回：一个列表，里面每个元素是一行（sqlite3.Row 对象）   │
# │       没结果时返回空列表 []（不会报错）                  │
# │ 类比：从仓库里搬一整箱子出来                             │
# │ 对比：fetchone() 只拿第一行，没结果返回 None              │
# └─────────────────────────────────────────────────────────┘

# ┌─────────────────────────────────────────────────────────┐
# │ 【函数：dict(对象)】                                     │
# │ 作用：把其他类型的数据转成字典                           │
# │ 原型：dict(obj)                                          │
# │ 返回：一个 dict                                          │
# │ 本例：dict(sqlite3.Row) → {"id":1, "name":"麻黄汤", ...} │
# │ 类比：把快递单上的手写信息录入电脑系统                    │
# └─────────────────────────────────────────────────────────┘

# ┌─────────────────────────────────────────────────────────┐
# │ 【语法：[表达式 for 变量 in 列表]  ——  列表推导式】      │
# │                                                        │
# │ 作用：把一个列表里的每个元素"加工"后生成新列表            │
# │ 类比：工厂流水线——每个零件进来，加工，新零件出去          │
# │                                                        │
# │ 写法：[dict(r) for r in rows]                           │
# │ 朗读："对于 rows 里的每一行 r，把它变成字典"              │
# │ 等价于：                                                │
# │   result = []                                           │
# │   for r in rows:                                        │
# │       result.append(dict(r))                            │
# │                                                        │
# │ 更多例子（感受一下）：                                   │
# │   输入：[1, 2, 3]                                       │
# │   [x*2  for x in [1,2,3]]   →  [2, 4, 6]    # 每个翻倍 │
# │   [str(x) for x in [1,2,3]]  →  ["1","2","3"] # 转字符串│
# │                                                        │
# │ 陷阱：很多新手会写成 {dict(r) for r in rows}             │
# │       花括号 {} 生成的是集合/字典，不是 JSON 数组！       │
# │       JSON 数组必须用 [] 列表。                          │
# └─────────────────────────────────────────────────────────┘

    # ─── 例题1：curl http://localhost:8000/prescriptions ──
    # 响应（200 OK）：
    # [{"id":1,"name":"麻黄汤","category":"解表剂",...}, ...共8首]

    # ─── 例题2：curl "http://localhost:8000/prescriptions?category=解表剂"
    # 响应（200 OK）：
    # [{"id":1,"name":"麻黄汤",...}, {"id":2,"name":"桂枝汤",...}, {"id":6,"name":"银翘散",...}]


# ╔══════════════════════════════════════════════════════════╗
# ║  路由 2：GET /prescriptions/{pid}                       ║
# ║           "第3号方剂的完整信息，包括药材组成"             ║
# ╚══════════════════════════════════════════════════════════╝

@app.get("/prescriptions/{pid}")
def get_prescription(pid: int):
    """方剂详情 = 基本信息 + 药材列表 + 用量"""

    conn = get_db()

    # 第1步：查方剂本身
    p = conn.execute(
        "SELECT * FROM prescriptions WHERE id = ?", (pid,)
    ).fetchone()

    if p is None:
        conn.close()
        return JSONResponse(
            {"error": f"方剂 {pid} 不存在"},
            status_code=404,
        )

    # 第2步：查药材组成
    herbs = conn.execute(
        """
        SELECT i.name, pi.dosage
        FROM prescription_ingredients pi
        JOIN ingredients i ON pi.ingredient_id = i.id
        WHERE pi.prescription_id = ?
        """,
        (pid,),
    ).fetchall()

    conn.close()

    # 第3步：拼成嵌套结构返回
    return {
        "id": p["id"],
        "name": p["name"],
        "category": p["category"],
        "source": p["source"],
        "symptoms": p["symptoms"],
        "herbs": [
            {"name": h["name"], "dosage": h["dosage"]} for h in herbs
        ],
    }

# ┌─────────────────────────────────────────────────────────┐
# │ 【函数：.fetchone()】                                    │
# │ 作用：只拿查询结果的第一行                               │
# │ 调用：conn.execute(sql, params).fetchone()               │
# │ 返回：一个 Row 对象（有结果时） 或 None（没结果时）       │
# │ 类比：从货架上拿一件商品                                 │
# │ 何时用：按唯一 ID 查单条记录时                           │
# │ 何时不用：查列表/批量时——用 fetchall()                   │
# │                                                        │
# │ fetchone() vs fetchall() 对比：                          │
# │ ┌──────────┬─────────────┬──────────────┐              │
# │ │          │ fetchone()   │ fetchall()   │              │
# │ ├──────────┼─────────────┼──────────────┤              │
# │ │ 返回     │ Row 或 None  │ [Row, Row..] │              │
# │ │ 没结果   │ None         │ []（空列表）  │              │
# │ │ 场景     │ 单条查询     │ 列表查询     │              │
# │ └──────────┴─────────────┴──────────────┘              │
# └─────────────────────────────────────────────────────────┘

# ┌─────────────────────────────────────────────────────────┐
# │ 【函数：JSONResponse(内容, status_code=状态码)】          │
# │ 作用：返回 JSON 数据 + 指定 HTTP 状态码                    │
# │ 原型：JSONResponse(content=dict, status_code=int)        │
# │       第1个参数：要返回的字典（会自动转 JSON）            │
# │       第2个参数：HTTP 状态码（数字），必须显式写          │
# │ 返回：一个 Response 对象（FastAPI 内部处理）              │
# │ 类比：不光端菜，还放一张纸条"404，这菜没了"               │
# │                                                        │
# │ 为什么不用普通 return？                                  │
# │   return {"error":"xxx"} → 状态码默认 200（成功）        │
# │   但"方剂不存在"应该返回 404（Not Found）                │
# │   JSONResponse 让我们能手动指定状态码                    │
# │                                                        │
# │ 常用状态码速记：                                        │
# │   200 = OK（成功）   201 = Created（创建成功）           │
# │   400 = Bad Request（请求有问题）                        │
# │   404 = Not Found（找不到）                              │
# │   500 = Server Error（服务器自己崩了）                   │
# └─────────────────────────────────────────────────────────┘

# ┌─────────────────────────────────────────────────────────┐
# │ 【语法：f"xxx {变量} xxx"  ——  f-string】               │
# │ 作用：把变量的值嵌入到字符串里                            │
# │ 写法：在字符串前加 f，花括号里写变量名                    │
# │ 类比：填空题——{pid} 的位置自动填上 pid 的值               │
# │                                                        │
# │ 例：pid = 99                                            │
# │    f"方剂 {pid} 不存在"  →  "方剂 99 不存在"            │
# │                                                        │
# │ 陷阱：普通字符串不能这样写（前面没有 f）                  │
# │       "方剂 {pid} 不存在"  →  原样输出 {pid}，不会替换   │
# └─────────────────────────────────────────────────────────┘

    # ─── 例题1：curl http://localhost:8000/prescriptions/1 ──
    # 响应（200）：
    # {"id":1,"name":"麻黄汤","herbs":[{"name":"麻黄","dosage":"三两"},...]}

    # ─── 例题2：curl http://localhost:8000/prescriptions/999
    # 响应（404）：{"error": "方剂 999 不存在"}


# ╔══════════════════════════════════════════════════════════╗
# ║  路由 3：GET /herbs    ——   所有药材列表                 ║
# ╚══════════════════════════════════════════════════════════╝

@app.get("/herbs")
def list_herbs():
    """列出数据库中所有药材，按拼音字母排序。"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name FROM ingredients ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

    # ─── 例题：curl http://localhost:8000/herbs ──
    # 响应（200）：[{"id":11,"name":"人参"}, {"id":25,"name":"牛蒡子"}, ...]


# ╔══════════════════════════════════════════════════════════╗
# ║  路由 4：GET /herbs/{name}/prescriptions                ║
# ║          "甘草被用在哪些方剂里？"                        ║
# ╚══════════════════════════════════════════════════════════╝

@app.get("/herbs/{name}/prescriptions")
def herb_prescriptions(name: str):
    """
    反向查询：输入药材名 → 返回哪些方剂用了它。
    和路由 2 方向相反，翻的是同一张关联表。

    分两步：
      1. 确认药材存在（不存在 → 404）
      2. 查关联的方剂
    不分两步"药材名写错了"和"确实没被任何方剂用"就分不清了。
    """

    conn = get_db()

    # 第1步：药材存在吗？
    herb = conn.execute(
        "SELECT id FROM ingredients WHERE name = ?", (name,)
    ).fetchone()

    if herb is None:
        conn.close()
        return JSONResponse(
            {"error": f"药材 '{name}' 不存在"},
            status_code=404,
        )

    # 第2步：查它关联了哪些方剂
    rows = conn.execute(
        """
        SELECT p.id, p.name, pi.dosage
        FROM prescription_ingredients pi
        JOIN prescriptions p ON pi.prescription_id = p.id
        WHERE pi.ingredient_id = ?
        """,
        (herb["id"],),
    ).fetchall()

    conn.close()
    return [
        {"id": r["id"], "name": r["name"], "dosage": r["dosage"]}
        for r in rows
    ]

    # ─── 例题1：curl http://localhost:8000/herbs/甘草/prescriptions
    # 响应（200）：[{"id":1,"name":"麻黄汤","dosage":"一两"}, ... 7首]

    # ─── 例题2：curl http://localhost:8000/herbs/阿莫西林/prescriptions
    # 响应（404）：{"error": "药材 '阿莫西林' 不存在"}


# ╔══════════════════════════════════════════════════════════╗
# ║  第一部分总结：你已经知道的                               ║
# ╚══════════════════════════════════════════════════════════╝

"""
到目前为止，代码里出现的所有"非常规函数"，你应该能回答：

  import xxx        → 干什么的？from xxx import yyy 呢？
  FastAPI()         → 创建了什么？参数有什么用？
  @app.get("/xxx")  → 装饰器是把什么和什么绑在一起？
  sqlite3.connect() → 打开/创建了什么？返回什么？
  row_factory = Row → 设了之后能用什么方式取数据？
  conn.execute()    → 两个参数分别是什么？占位符怎么用？
  .fetchone()       → 返回什么？和 fetchall() 什么时候分别用？
  .fetchall()       → 返回什么？没结果时返回什么？
  dict(row)         → 把 Row 对象转成什么？
  [x for x in list] → 叫什么语法？方括号和花括号的区别？
  Query(None)       → 为什么用这个而不是直接写 None？
  str | None        → | 符号在类型注解里代表什么？
  JSONResponse()    → 和普通 return 有什么区别？
  f"{变量}"          → 字符串前加 f 的作用是什么？
  (category,)       → 单元素元组的逗号为什么不能省？

如果你对其中任何一个还模糊，往上看对应的卡片，或者在终端里
启动 uvicorn 后打开 http://localhost:8000/docs 实际测试。
亲眼看到数据返回比看十遍注释都有用。
"""


# ╔══════════════════════════════════════════════════════════╗
# ║                                                        ║
# ║  你的动手练习：POST /prescriptions                       ║
# ║                                                        ║
# ║  任务：写一个接口，让用户可以通过 POST 请求"点新菜"       ║
# ║                                                        ║
# ║  功能要求：                                              ║
# ║    1. 接收 JSON 数据：{name, category, source, symptoms,║
# ║       herbs: [{name, dosage}, ...]}                     ║
# ║    2. 把方剂信息插入 prescriptions 表                    ║
# ║    3. 把药材关联插入 prescription_ingredients 表         ║
# ║    4. 如果药材名不存在，返回 400 错误                     ║
# ║    5. 用 conn.commit() 确认保存                          ║
# ║    6. 返回 201 Created + 新建方剂的数据                   ║
# ║                                                        ║
# ║  新知识点（等会给你解释）：                               ║
# ║    - @app.post()      ← POST 装饰器                     ║
# ║    - Pydantic 模型     ← 定义请求体的格式和校验           ║
# ║    - conn.commit()    ← 确认写入（和 SQL 课一样）        ║
# ║    - status_code=201  ← 201 = Created                   ║
# ║                                                        ║
# ║  提示：思路和 prescription_db.py 的 link() 函数完全一样，  ║
# ║  只是数据来源从 Python 变量变成了 HTTP 请求的 JSON 体。    ║
# ║                                                        ║
# ╚══════════════════════════════════════════════════════════╝
@app.post("/prescriptions")
def create_prescription(data: PrescriptionIn):
    conn = get_db()

    # 步骤1：校验所有药材是否存在
    for herb in data.herbs:
        exists = conn.execute(
            "SELECT id FROM ingredients WHERE name = ?",
            (herb.name,),
        ).fetchone()
        if exists is None:
            conn.close()
            return JSONResponse(
                {"error": f"药材 '{herb.name}' 不存在"},
                status_code=400,
            )

    # 步骤2：插入方剂（在步骤1循环外面！）
    cur = conn.execute(
        "INSERT INTO prescriptions (name, category, source, symptoms) VALUES (?, ?, ?, ?)",
        (data.name, data.category, data.source, data.symptoms),
    )
    new_id = cur.lastrowid

    # 步骤3：插入关联表（另一个独立的 for 循环）
    for herb in data.herbs:
        row = conn.execute(
            "SELECT id FROM ingredients WHERE name = ?",
            (herb.name,),
        ).fetchone()
        herb_id = row["id"]
        conn.execute(
            "INSERT INTO prescription_ingredients (prescription_id, ingredient_id, dosage) VALUES (?, ?, ?)",
            (new_id, herb_id, herb.dosage),
        )

    # 步骤4：提交 + 返回（在所有循环外面！）
    conn.commit()
    conn.close()
    return JSONResponse(
        {
            "id": new_id,
            "name": data.name,
            "category": data.category,
            "source": data.source,
            "symptoms": data.symptoms,
            "herbs": [{"name": h.name, "dosage": h.dosage} for h in data.herbs],
        },
        status_code=201,
    )

@app.put("/prescriptions/{pid}")
def update_prescription(pid: int, data: PrescriptionIn):
    conn = get_db()
    p=conn.execute('''
    SELECT id from prescriptions
    WHERE id = ?
    ''', (pid,)).fetchone()
    if p is None:
        conn.close()
        return JSONResponse({"error":f"方剂{pid}不存在"}, status_code=404)

    conn.execute('''UPDATE prescriptions 
                 SET name =?,category=?, source=?, symptoms=?
                 WHERE id=?''',(data.name, data.category, data.source, data.symptoms, pid))

    conn.commit()
    conn.close()
    return JSONResponse(
        {
            "id": pid,
            "name": data.name,
            "category": data.category,
            "source": data.source,
            "symptoms": data.symptoms,
        },
        status_code=200,
    )

@app.delete("/prescriptions/{pid}")
def delete_prescription(pid: int,data: PrescriptionIn):
    conn = get_db()
    p = conn.execute('''
                     SELECT id
                     from prescriptions
                     WHERE id = ?
                   ''', (pid,)).fetchone()
    if p is None:
        conn.close()
        return JSONResponse({"error": f"方剂{pid}不存在"}, status_code=404)
    conn.execute('''DELETE FROM prescription_ingredients
                  WHERE prescription_id=?''', (pid,))
    conn.execute('''DELETE FROM prescriptions
                 WHERE id=?''', (pid,))
    conn.commit()
    conn.close()
    return JSONResponse({
            "id": pid,
            "name": data.name,
            "category": data.category,
            "source": data.source,
            "symptoms": data.symptoms,
        },status_code=200)