"""pytest 共享 fixture —— 让测试用「临时数据库」，不碰你的 prescriptions.db

为什么要这个文件（第 4 课讲过的概念在这里落地）：
  问题：原来的 test_api.py 直接连 prescriptions.db
        → test_create 会真的往你的库里插一条数据
        → 万一中途 assert 失败，插进去的数据就留下来了（污染）
        → 而且 assert len(...) == 8 这种数字，会随库里数据变化而失效
  解决：每个测试都用一个「全新的、空的、内存里的」数据库
        → 跑多少次结果都一样（可重复）
        → 跑完自动消失（不污染）
        → 想插多少数据自己说了算（可控）

用法：
  pytest                      # 跑全部
  pytest -v                   # 看每个测试名
  pytest -k "搜索"            # 只跑名字含"搜索"的
"""
import sqlite3

import pytest
from fastapi.testclient import TestClient

import api


# ── 一份可复用的建表 + 示例数据 SQL（注意：只当"数据"用，不解释中医语义）──
SCHEMA = """
CREATE TABLE prescriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    source TEXT,
    symptoms TEXT
);
CREATE TABLE ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE prescription_ingredients (
    prescription_id INTEGER,
    ingredient_id INTEGER,
    dosage TEXT,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);
INSERT INTO prescriptions (name, category, source, symptoms) VALUES
    ('甲', '一类', '书A', '症状甲'),
    ('乙', '一类', '书A', '症状乙'),
    ('丙', '二类', '书B', '症状丙');
INSERT INTO ingredients (name) VALUES ('甘'), ('苦'), ('辛');
INSERT INTO prescription_ingredients VALUES (1, 1, '三两'), (1, 2, '一两'), (2, 1, '二两');
"""


@pytest.fixture
def db(monkeypatch):
    """给每个测试一个全新的内存数据库，并把 api 里的连接函数换成它。

    关键点 1（跨线程）：TestClient 在另一个线程处理请求 → 必须 check_same_thread=False
    关键点 2（每次新连接）：api.py 的接口结尾会 conn.close()，
        所以 fixture 必须"每次调用返回一个新连接"，而不能共用一个连接 —— 否则第一次
        请求就把连接关掉，后面的请求会报 "Cannot operate on a closed database"。
        办法：共享缓存的内存库（cache=shared），它允许多个连接看到同一份内存数据。
    """
    import uuid
    real_connect = sqlite3.connect          # ⚠️ 必须先存下来：api.sqlite3 就是全局 sqlite3 模块，
                                            # 打补丁后若再写 sqlite3.connect(...) 会自己调自己 → 无限递归
    name = f"file:testdb_{uuid.uuid4().hex}?mode=memory&cache=shared"
    keeper = real_connect(name, uri=True, check_same_thread=False)
    keeper.row_factory = sqlite3.Row        # 测试里也要能按列名取值（如 row["id"]）
    keeper.executescript(SCHEMA)
    keeper.commit()

    def fake_connect(*args, **kwargs):
        c = real_connect(name, uri=True, check_same_thread=False)
        c.row_factory = sqlite3.Row      # api.py 里也是这么设的（能用列名取值）
        return c

    monkeypatch.setattr(api.sqlite3, "connect", fake_connect)
    yield keeper
    keeper.close()


@pytest.fixture
def client(db):
    """需要 HTTP 客户端的测试就用这个（它自动带上干净数据库）。"""
    return TestClient(api.app)


@pytest.fixture
def sample_id(db):
    """刚建好的库里，第一条数据的 id（避免到处写魔法数字 1）。"""
    return db.execute("SELECT id FROM prescriptions ORDER BY id LIMIT 1").fetchone()["id"]
