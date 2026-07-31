"""OOP 系统入门 —— 用你 api.py 里的代码当教材"""

# ═══════════════════════════════════════════════════════════
# 第 1 课：你已经写过的类和对象
# ═══════════════════════════════════════════════════════════

# ----- 1.1 你写的 HerbIn 就是一个"类" -----
from pydantic import BaseModel

class HerbIn(BaseModel):
    name: str
    dosage: str

# HerbIn = 类（饼干模具）
# name: str / dosage: str = 模具上的两个"槽位"

# ----- 1.2 这两行在 PyCharm 里跑一下 -----
h = HerbIn(name="麻黄", dosage="三两")   # h 是"对象"（用模具压出的饼干）
print(type(h))     # <class 'HerbIn'>  ← h 是 HerbIn 类造出来的
print(h.name)      # "麻黄"   ← .name 是对象的"属性"
print(h.dosage)    # "三两"

# ----- 1.3 你写的 api.py 里有无数对象 -----
# app = FastAPI(title="...")   → app 是 FastAPI 类造出的对象
# conn = sqlite3.connect(...)  → conn 是 Connection 类造出的对象
# data = PrescriptionIn(...)   → data 是 PrescriptionIn 类造出的对象


# ═══════════════════════════════════════════════════════════
# 第 2 课：类自己造对象（__init__ 构造方法）
# ═══════════════════════════════════════════════════════════

class Fangji:
    """中药方剂类"""

    def __init__(self, name, category, source):
        # __init__ = 构造方法 = "把原材料放进模具压成型"
        # self = 正在被制造的那个对象本身
        print(f"正在制造方剂：{name}")
        self.name = name          # 把 name 刻在这个对象的 name 属性上
        self.category = category
        self.source = source

    def describe(self):
        # 普通方法 = 这个对象能做的事
        # self = 调用这个方法的那个对象
        return f"「{self.name}」出自《{self.source}》，属于{self.category}"


# ----- 在终端跑这段 -----
f = Fangji("麻黄汤", "解表剂", "伤寒论")  # 自动调用 __init__
print(f.name)       # "麻黄汤"     ← 属性
print(f.source)     # "伤寒论"     ← 属性
print(f.describe()) # "「麻黄汤」出自《伤寒论》，属于解表剂"  ← 方法


# ═══════════════════════════════════════════════════════════
# 第 3 课：self 是什么（最关键的一个概念）
# ═══════════════════════════════════════════════════════════

# self = "谁在调我，我就是谁"

f1 = Fangji("麻黄汤", "解表剂", "伤寒论")
f2 = Fangji("桂枝汤", "解表剂", "伤寒论")

print(f1.describe())
# f1 调用 describe → 方法里的 self 就是 f1
# → self.name 就是 "麻黄汤"

print(f2.describe())
# f2 调用 describe → 方法里的 self 就是 f2
# → self.name 就是 "桂枝汤"

# 你只需要知道：哪个对象调方法，self 就指向那个对象


# ═══════════════════════════════════════════════════════════
# 第 4 课：属性 vs 方法
# ═══════════════════════════════════════════════════════════

# 属性 = 对象"是什么"（名词）     → 没有括号，只是取值
# 方法 = 对象"能做什么"（动词）   → 有括号，是调用执行

f = Fangji("麻黄汤", "解表剂", "伤寒论")

# 属性（没有括号）：
f.name       # "麻黄汤"     ← 问：它的名字是什么？
f.category   # "解表剂"     ← 问：它属于什么分类？

# 方法（有括号）：
f.describe() # "「麻黄汤」出自..."  ← 命令：介绍一下你自己！

# 你在 api.py 里一直用的：
# conn.row_factory   ← 属性：连接的"杯型设置项"是什么？
# conn.execute()     ← 方法：去执行一条 SQL
# conn.close()       ← 方法：关掉连接


# ═══════════════════════════════════════════════════════════
# 第 5 课：继承 = 拿已有模具加花纹
# ═══════════════════════════════════════════════════════════

# 原始模具（BaseModel）：能自动 JSON 解析 + 类型校验
# 你的模具（HerbIn）：在 BaseModel 上加 name 和 dosage 两个槽位

# class HerbIn(BaseModel):   # (BaseModel) = "继承 BaseModel 的所有能力"
#     name: str               # 新加 name 槽位
#     dosage: str             # 新加 dosage 槽位

# 自己写一个继承的例子：
class Animal:
    def speak(self):
        return "..."

class Cat(Animal):          # Cat 继承 Animal
    def speak(self):
        return "喵"

class Dog(Animal):          # Dog 继承 Animal
    def speak(self):
        return "汪"

cat = Cat()
dog = Dog()
print(cat.speak())  # "喵"
print(dog.speak())  # "汪"


# ═══════════════════════════════════════════════════════════
# 第 6 课：特殊方法（__双下划线__）
# ═══════════════════════════════════════════════════════════

class Fangji:
    def __init__(self, name):
        print(f"1. __init__ 被调用了: name={name}")
        self.name = name

    def __str__(self):
        return f"方剂: {self.name}"

    def __len__(self):
        return len(self.name)


f = Fangji("麻黄汤")
print(f)       # 方剂: 麻黄汤     ← 自动调了 __str__
print(len(f))  # 3                ← 自动调了 __len__


# ═══════════════════════════════════════════════════════════
# 练习题：改造 prescription_db.py 的 link() 函数为类
# ═══════════════════════════════════════════════════════════

# 你现在 prescription_db.py 里 link() 是个函数。
# 挑战：把它改成一个 Database 类，把 connect/execute/close 封装进去。

# 框架：
class PrescriptionDB:
    def __init__(self, db_path):
        import sqlite3
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        self.conn.close()

    def get_prescription(self, pid):
        """根据 id 查方剂"""
        cur = self.conn.execute(
            "SELECT * FROM prescriptions WHERE id = ?", (pid,)
        )
        row = cur.fetchone()
        if row is None:
            return None
        return dict(row)

    # 你的作业：实现下面两个方法
    # def add_prescription(self, name, category, source, symptoms):
    #     """新增方剂，返回新 id"""
    #     pass

    # def delete_prescription(self, pid):
    #     """删除方剂（先删关联表再删主表），返回是否成功"""
    #     pass


# 使用：
# db = PrescriptionDB("prescriptions.db")
# info = db.get_prescription(1)
# print(info)
# db.close()
