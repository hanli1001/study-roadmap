# FastAPI 学习笔记

> 2026.07 · 大一暑假 · 第一个完整 REST API

---

## 一、API 是什么

类比：**API = 餐厅服务员**

```
浏览器/前端 ──HTTP请求──▶ FastAPI ──SQL──▶ SQLite ──▶ 返回 JSON
(客人点菜)              (服务员)    (后厨)      (上菜)
```

你的数据库只能本地访问。API 是数据库的前台窗口——发 HTTP 请求，拿 JSON 数据。

---

## 二、HTTP 方法 ↔ SQL 操作

| HTTP 方法 | 装饰器 | SQL | 用途 | 示例 |
|-----------|--------|-----|------|------|
| GET | `@app.get()` | SELECT | 查询 | `GET /prescriptions/3` |
| POST | `@app.post()` | INSERT | 新增 | `POST /prescriptions` + JSON 请求体 |
| PUT | `@app.put()` | UPDATE | 修改 | `PUT /prescriptions/3` + JSON 请求体 |
| DELETE | `@app.delete()` | DELETE | 删除 | `DELETE /prescriptions/3` |

CRUD = Create + Read + Update + Delete

---

## 三、最小骨架

```python
from fastapi import FastAPI

app = FastAPI()                    # 创建应用（开餐厅）

@app.get("/")                      # 注册路由（菜单上添菜）
def root():                        # 处理函数（点这道菜就叫这个师傅）
    return {"hello": "world"}      # dict → FastAPI 自动转 JSON
```

启动：`uvicorn 文件名:app变量 --reload`
示例：`uvicorn api:app --reload` → http://localhost:8000

---

## 四、路由规则

### 4.1 匹配顺序（踩过坑）

FastAPI **从上到下**匹配，第一个命中就处理。

```python
# ✅ 正确：具体路径在前，通配路径在后
@app.get("/prescriptions/search")      # 精确匹配 "search"
@app.get("/prescriptions/{pid}")       # 通配兜底

# ❌ 错误：通配在前，search 永远被拦截
@app.get("/prescriptions/{pid}")       # {pid} 匹配一切包括 "search"
@app.get("/prescriptions/search")      # 永远执行不到
```

**规则：带 `{xxx}` 的放最后。**

### 4.2 路径参数 vs 查询参数

| | 路径参数 `{pid}` | 查询参数 `?key=value` |
|------|-----------------|---------------------|
| URL 写法 | `/xxx/3` | `/xxx?key=val` |
| 用途 | 指定是哪一个 | 筛选/排序/分页 |
| Python 写法 | `pid: int` | `key: str = Query(None)` |
| 必填性 | 必填 | Query(None)=可选, Query(...)=必填 |

---

## 五、Pydantic 数据模型

### 5.1 定义"登记表"

```python
from pydantic import BaseModel

class HerbIn(BaseModel):
    name: str      # 药材名，必填
    dosage: str    # 用量，必填

class PrescriptionIn(BaseModel):
    name: str              # 方剂名，必填
    category: str          # 分类，必填
    source: str            # 出处，必填
    symptoms: str          # 主治，必填
    herbs: list[HerbIn]    # 药材列表
```

`BaseModel` 自动做三件事：JSON → Python 对象、类型校验、文档生成。

### 5.2 使用

```python
@app.post("/prescriptions")
def create(data: PrescriptionIn):
    data.name           # "麻黄汤"      ← 点出来，不是 data["name"]
    data.herbs          # [HerbIn对象, ...]
    data.herbs[0].name  # "麻黄"
```

---

## 六、数据库操作模板

### 通用流程

```python
conn = get_db()                              # 连接
rows = conn.execute(sql, params).fetchall()  # 执行
conn.close()                                 # 关闭（提前 return 也要关）
return [dict(r) for r in rows]               # 转 JSON
```

### 写操作必须 commit

```
execute(INSERT) = 填转账单
commit()       = 签字确认 → 真正写入硬盘（不签就白干）
```

### 取刚插入行的 id

```python
cur = conn.execute("INSERT INTO ...")
new_id = cur.lastrowid
```

---

## 七、错误处理

### 404 检查

```python
p = conn.execute("SELECT * FROM t WHERE id = ?", (pid,)).fetchone()
if p is None:
    conn.close()    # 先关门再 return
    return JSONResponse({"error": "不存在"}, status_code=404)
```

### 常用状态码

| 码 | 含义 | 何时用 |
|----|------|--------|
| 200 | OK | GET/PUT/DELETE 成功 |
| 201 | Created | POST 新增成功 |
| 400 | Bad Request | 请求数据有问题 |
| 404 | Not Found | 查不到 |
| 422 | 校验失败 | Pydantic 自动返回 |

---

## 八、语法速查

| 语法 | 作用 |
|------|------|
| `@app.get("/path")` | 注册 GET 路由 |
| `pid: int` | 路径参数（自动转类型） |
| `Query(None)` | 可选查询参数 |
| `Query(...)` | 必填查询参数 |
| `JSONResponse(dict, status_code=N)` | 自定义状态码返回 |
| `cur.lastrowid` | 刚插入行的 id |
| `conn.commit()` | 确认写入（类比 git commit） |
| `[dict(r) for r in rows]` | Row 列表 → 字典列表 |
| `f"%{keyword}%"` | LIKE 模糊搜索模式 |

---

## 九、自动文档

| 文档 | 地址 | 用途 |
|------|------|------|
| Swagger UI | `/docs` | 交互式测试 |
| ReDoc | `/redoc` | 只读文档 |

你不写前端，FastAPI 白送这两个页面——靠你的类型注解自动生成。

---

## 十、OOP 基础（遇到就学）

| 概念 | Python | 类比 |
|------|--------|------|
| 类 (class) | `int`, `FastAPI`, `HerbIn` | 饼干模具 |
| 对象 (object) | `3`, `app`, `data` | 模具压出的饼干 |
| 属性 | `conn.row_factory` | 对象上的设置项 |
| 方法 | `conn.execute()`, `name.upper()` | 对象能做的事 |
| 继承 | `class X(BaseModel):` | 拿已有模具加花纹 |

---

## 十一、踩坑记录

| 坑 | 原因 | 解决 |
|----|------|------|
| `{...}` 是 Python 真值 Ellipsis | Python 认 `...` 为对象 | return 里不写占位符 |
| `/search` 被 `{pid}` 拦截 | 通配路由写在前面 | 具体路径放前，通配放后 |
| `execute()` 忘加 `.fetchall()` | execute 返回游标非结果 | 链式写全 |
| 缩进错误嵌套 for 循环 | Python 靠缩进判层级 | for 结束后退回同级 |
| 单元素元组 `(x)` | 缺逗号当普通括号 | 写成 `(x,)` |
| PowerShell 中文乱码 | 默认编码非 UTF-8 | 浏览器测试或 /docs |

---

## 十二、本项目接口

| 方法 | URL | 功能 |
|------|-----|------|
| GET | `/` | 目录 |
| GET | `/prescriptions` | 列表（可选 `?category=`） |
| GET | `/prescriptions/search` | 模糊搜索（`?keyword=`） |
| GET | `/prescriptions/{pid}` | 详情+药材 |
| POST | `/prescriptions` | 新增 |
| PUT | `/prescriptions/{pid}` | 修改 |
| DELETE | `/prescriptions/{pid}` | 删除 |
| GET | `/herbs` | 药材列表 |
| GET | `/herbs/{name}/prescriptions` | 反向查方剂 |

---

*代码：`api.py` · 数据库：`prescriptions.db`*
