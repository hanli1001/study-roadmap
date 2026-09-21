"""RAG 演示 ③ · 评估：检索到底行不行（Recall@k / MRR）

用法：python rag/03_评估检索质量.py
前置：先跑过 01 脚本（生成 _embeddings-cache.json）

为什么这个脚本最重要（路线 v3 的原话）：
    "RAG 的评估与可观测能力，是 AI 工程师与'会调 API'的分水岭"
—— 没有它，你只能凭感觉说"好像还行"；有了它，你能说"Recall@3 = 100%，比上一版高了 X%"。

它做的事：
    ① 准备一套"问题 → 正确文档"的测试集（这就是评估的地基：ground truth）
    ② 对每个问题检索 top-k
    ③ 算三个指标：
         Recall@k —— 该找到的，在 top-k 里出现了吗（漏检率）
         MRR     —— 正确答案平均排在第几位（越靠前越好）
         命中率   —— top-1 就是正确答案的比例
    ④ 把失败案例列出来 —— 失败案例比分数更有价值
"""
import json
import math
import sqlite3
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "prescriptions.db"
CACHE = Path(__file__).resolve().parent / "_embeddings-cache.json"
OLLAMA = "http://127.0.0.1:11434"
EMB_MODEL = "bge-m3"


# ─────────────── ① 测试集（ground truth）───────────────
# 规则：每条 = (用户可能怎么问, 期望检索到哪几首之一)
# ⚠️ 这套题是我根据现有数据手工标的，属于"最小可用测试集"；
#    真实项目里测试集要由业务方/使用者来标，而且至少上百条才有统计意义。
TEST_SET = [
    ("免疫",                    ["四君子汤"]),
    ("免疫力差",                ["四君子汤"]),
    ("体虚乏力",                ["四君子汤"]),
    ("增强体质",                ["四君子汤"]),
    ("气虚",                    ["四君子汤"]),
    ("没力气面色差",             ["四君子汤", "四物汤"]),
    ("失眠头晕",                ["四物汤"]),
    ("睡不好脸色不好",           ["四物汤"]),
    ("血虚",                    ["四物汤"]),
    ("受凉了没汗还发烧",         ["麻黄汤"]),
    ("怕冷又出汗",              ["桂枝汤"]),
    ("肚子不舒服想吐",           ["藿香正气散"]),
    ("嗓子痛咳嗽",              ["银翘散"]),
    ("忽冷忽热没胃口",           ["小柴胡汤"]),
    ("发高烧口渴",              ["白虎汤"]),
]


def embed(texts, model=EMB_MODEL):
    out = []
    for t in texts:
        req = urllib.request.Request(
            f"{OLLAMA}/api/embeddings",
            data=json.dumps({"model": model, "prompt": t}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            out.append(json.loads(r.read())["embedding"])
    return out


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def load_docs():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    docs = [
        {"name": r["name"],
         "text": f"{r['name']}（{r['category'] or ''}·{r['source'] or ''}）：{r['symptoms'] or ''}"}
        for r in conn.execute("SELECT name, category, source, symptoms FROM prescriptions ORDER BY id")
    ]
    conn.close()
    return docs


def rank(question, docs, vectors):
    """返回按相似度降序排列的文档名列表。"""
    qv = embed([question])[0]
    return [d["name"] for d, _ in sorted(
        ((d, cosine(qv, v)) for d, v in zip(docs, vectors)), key=lambda x: -x[1])]


def main():
    docs = load_docs()
    vectors = json.loads(CACHE.read_text(encoding="utf-8"))["vectors"]
    assert len(vectors) == len(docs)

    print(f"测试集：{len(TEST_SET)} 个问题 · 知识库：{len(docs)} 条 · 模型：{EMB_MODEL}\n")

    Ks = [1, 3, 5]
    recall = {k: 0 for k in Ks}
    hit1 = 0
    rr_sum = 0.0
    failures = []
    rows = []

    for q, expected in TEST_SET:
        order = rank(q, docs, vectors)
        pos = next((i + 1 for i, n in enumerate(order) if n in expected), None)
        if pos:
            rr_sum += 1 / pos
            for k in Ks:
                if pos <= k:
                    recall[k] += 1
            if pos == 1:
                hit1 += 1
        else:
            failures.append((q, expected, order[:3]))
        rows.append((q, expected, pos, order[0]))

    print("=" * 74)
    print(f"{'问题':<20}{'期望':<14}{'实际排名':<10}{'top-1 实际命中':<16}")
    print("=" * 74)
    for q, exp, pos, top1 in rows:
        flag = "✅" if pos == 1 else ("🟡" if pos else "❌")
        print(f"{q:<20}{'/'.join(exp):<14}{flag + (str(pos) if pos else '未命中'):<12}{top1:<16}")

    n = len(TEST_SET)
    print("\n" + "=" * 74)
    print("指标（这几个词以后你会天天见）")
    print("=" * 74)
    for k in Ks:
        print(f"  Recall@{k} = {recall[k]}/{n} = {recall[k] / n:.0%}   "
              f"（该找到的，有多少在 top-{k} 里）")
    print(f"  MRR      = {rr_sum / n:.3f}          （1/排名 的平均值，满分 1.0）")
    print(f"  命中率    = {hit1}/{n} = {hit1 / n:.0%}      （正确答案正好排第一的比例）")

    if failures:
        print("\n❌ 失败案例（比分数更值钱，要逐条看）")
        for q, exp, got in failures:
            print(f"  问「{q}」期望 {exp}，实际 top-3 是 {got}")
    else:
        print("\n✅ 没有漏检（Recall@5 = 100%）")

    print("""
下一步该怎么用这套东西（这才是"会评估"的意思）：
  1. **改一版就重跑一次**：换切片方式、换模型、加同义词表 → 看 Recall/MRR 是升还是降
     没有这个对照，你改配置就是凭感觉
  2. **分数不是终点**：Recall@3=100% 不代表答得好 —— 还要评"生成"那一段
     （答得对不对、有没有编、引用准不准）→ 那才是 Ragas 的完整能力
  3. **测试集要长**：15 条只能看趋势；上百条才能看出 5% 的差别
""")


if __name__ == "__main__":
    main()
