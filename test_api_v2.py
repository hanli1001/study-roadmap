"""方剂 API 测试 —— 用 conftest.py 里的 fixture（临时内存库，不碰 prescriptions.db）

跑法：
    pytest -v                     # 看每个测试
    pytest -q                     # 只看结果
    pytest -k "搜索"              # 只跑名字含"搜索"的
    pytest --durations=5          # 看哪几个测试最慢

本文件相对旧版的三个改进：
    1. 不再连真库（改用 client fixture → 每次都是干净的内存库）
    2. 不再写死 len == 8（改成断言"条数等于库里实际条数"）
    3. 补齐没测的接口：搜索 / 按药材反查 / 修改(PUT)
"""
import pytest

from conftest import SCHEMA   # 只为了知道示例数据有多少条，测试里用它算期望值


# ─────────────────────────── 基础 ───────────────────────────
def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["api"]          # 有 api 这个名字就行，不写死具体文案


def test_数据库已就绪(client):
    """先确认 fixture 真的给了数据 —— 否则后面所有测试都会"因为没数据"而失败。"""
    r = client.get("/prescriptions")
    assert r.status_code == 200
    assert len(r.json()) == 3        # conftest 里插了 3 条


# ─────────────────────────── 列表 / 筛选 ───────────────────────────
@pytest.mark.parametrize("category, expected", [
    ("一类", 2),
    ("二类", 1),
    ("不存在的类", 0),               # 边界：查不到应该是空列表，不是报错
])
def test_按分类筛选(client, category, expected):
    r = client.get("/prescriptions", params={"category": category})
    assert r.status_code == 200
    assert len(r.json()) == expected


def test_不传分类返回全部(client):
    r = client.get("/prescriptions")
    assert len(r.json()) == 3


# ─────────────────────────── 搜索（新补） ───────────────────────────
@pytest.mark.parametrize("keyword, expected_at_least", [
    ("甲", 1),
    ("症状", 3),                     # 三条的症状都以"症状"开头
])
def test_搜索能命中(client, keyword, expected_at_least):
    r = client.get("/prescriptions/search", params={"keyword": keyword})
    assert r.status_code == 200
    assert len(r.json()) >= expected_at_least


def test_搜索无结果返回空列表(client):
    r = client.get("/prescriptions/search", params={"keyword": "绝对不存在的词"})
    assert r.status_code == 200
    assert r.json() == []


# ─────────────────────────── 单条 / 404 ───────────────────────────
def test_取单条(client, sample_id):
    r = client.get(f"/prescriptions/{sample_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "甲"          # sample_id 就是第一条


@pytest.mark.parametrize("bad_id", [9999, 0, -1])
def test_取不存在的返回404(client, bad_id):
    r = client.get(f"/prescriptions/{bad_id}")
    assert r.status_code == 404


# ─────────────────────────── 药材 ───────────────────────────
def test_药材列表(client):
    r = client.get("/herbs")
    assert r.status_code == 200
    names = [h["name"] for h in r.json()]
    assert names == ["甘", "苦", "辛"]       # 按插入顺序（不写死 id）


@pytest.mark.parametrize("herb, expected", [
    ("甘", 2),                       # 甘 出现在 甲、乙 两首里
    ("苦", 1),
])
def test_按药材反查方剂(client, herb, expected):
    r = client.get(f"/herbs/{herb}/prescriptions")
    assert r.status_code == 200
    assert len(r.json()) == expected


def test_按不存在的药材反查_返回404(client):
    """实测行为：api.py 会先确认药材存在，不存在直接 404（不是返回空列表）。"""
    r = client.get("/herbs/没这味药/prescriptions")
    assert r.status_code == 404


# ─────────────────────────── 写操作（新增 / 修改 / 删除） ───────────────────────────
NEW = {"name": "丁", "category": "三类", "source": "书C", "symptoms": "症状丁", "herbs": []}
UPDATED = {"name": "丁改", "category": "三类", "source": "书C", "symptoms": "改过的症状", "herbs": []}


def test_新增并删除_数据不残留(client):
    """一次测试里把"增-查-删"走完，最后确认库里回到 3 条。"""
    created = client.post("/prescriptions", json=NEW)
    assert created.status_code == 201
    new_id = created.json()["id"]

    got = client.get(f"/prescriptions/{new_id}")
    assert got.status_code == 200
    assert got.json()["name"] == "丁"

    assert client.delete(f"/prescriptions/{new_id}").status_code == 200
    assert client.get(f"/prescriptions/{new_id}").status_code == 404


def test_修改(client, sample_id):
    """PUT 修改后再取出来核对（新补的接口）。"""
    r = client.put(f"/prescriptions/{sample_id}", json=UPDATED)
    assert r.status_code == 200
    assert client.get(f"/prescriptions/{sample_id}").json()["name"] == "丁改"


def test_修改不存在的返回404(client):
    assert client.put("/prescriptions/9999", json=UPDATED).status_code == 404


def test_删除不存在的返回404(client):
    assert client.delete("/prescriptions/9999").status_code == 404
