"""RAG 演示 ① · 真 embedding 语义检索（Ollama bge-m3 + 你的方剂库）

对应路线 v3 阶段 A 的预热项「Ollama + 中文 embedding + 相似检索」。
配套：交互演示/RAG①-检索三档对比.html

用法：python rag/01_embedding_检索.py
     （先确保 Ollama 在跑：ollama list 能看到 bge-m3）

它做的事（RAG 的前半段）：
    ① 从 prescriptions.db 读文档
    ② 用 bge-m3 把每条文档变成向量（embedding），缓存到本地
    ③ 把"用户的问题"也变成向量
    ④ 算余弦相似度，取最像的 top-k
    ⑤ 和"字面匹配"对照 —— 看字面 0 命中的问题，语义能不能找到
"""
import json
import math
import sqlite3
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "prescriptions.db"
CACHE = Path(__file__).resolve().parent / "_embeddings-cache.json"
OLLAMA = "http://127.0.0.1:11434"
MODEL = "bge-m3"


# ─────────────────────── Ollama 调用 ───────────────────────
def embed(texts, model=MODEL):
    """把一批文本变成向量。返回 list[list[float]]。"""
    out = []
    for t in texts:
        req = urllib.request.Request(
            f"{OLLAMA}/api/embeddings",
            data=json.dumps({"model": model, "prompt": t}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                out.append(json.loads(r.read())["embedding"])
        except urllib.error.URLError as e:
            raise SystemExit(
                f"连不上 Ollama（{e}）。先在终端跑 `ollama list` 确认服务在跑，"
                f"再用 `ollama pull {model}` 装模型。"
            )
    return out


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


# ─────────────────────── 文档（你的真实数据）───────────────────────
def load_docs():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    docs = []
    for row in conn.execute("SELECT id, name, category, source, symptoms FROM prescriptions ORDER BY id"):
        # 一条方剂 = 一段可检索的文本（这就是 RAG 里的 chunk）
        text = (
            f"{row['name']}（{row['category'] or ''}·{row['source'] or ''}）："
            f"{row['symptoms'] or ''}"
        )
        docs.append({"id": row["id"], "name": row["name"], "text": text})
    conn.close()
    return docs


def literal_hits(docs, q):
    return [d["name"] for d in docs if q in d["text"]]


def main():
    t_start = time.perf_counter()
    docs = load_docs()
    print(f"知识库：{len(docs)} 条（来自 {DB.name}）")

    # ② 算向量（有缓存就用缓存，避免每次重算）
    if CACHE.exists():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
        if cache.get("model") == MODEL and len(cache.get("vectors", [])) == len(docs):
            vectors = cache["vectors"]
            print(f"向量：用缓存（{CACHE.name}）")
        else:
            cache = None
    else:
        cache = None

    if cache is None:
        t0 = time.perf_counter()
        vectors = embed([d["text"] for d in docs])
        t1 = time.perf_counter()
        CACHE.write_text(json.dumps({"model": MODEL, "vectors": vectors}, ensure_ascii=False),
                         encoding="utf-8")
        print(f"向量：现算 {len(vectors)} 条，耗时 {t1 - t0:.2f} 秒"
              f"（每条 {(t1 - t0) / len(vectors) * 1000:.0f} ms），已缓存 → {CACHE.name}")

    dim = len(vectors[0])
    print(f"向量维度：{dim}（bge-m3 的维度；每条文本变成 {dim} 个数字）")

    # 要试的问题：前几个是"字面查不到"的，最后两个是字面能查到的
    questions = [
        "免疫",                        # 字面 0 命中
        "免疫力差",                    # 字面 0 命中
        "体虚乏力",                    # 字面 0 命中
        "增强体质",                    # 字面 0 命中
        "肚子不舒服还呕吐",             # 字面 0 命中
        "气虚",                        # 字面能命中（对照）
    ]

    print("\n" + "=" * 68)
    print("对照实验：字面匹配 vs 语义检索（top-3）")
    print("=" * 68)
    for q in questions:
        lit = literal_hits(docs, q)
        t0 = time.perf_counter()
        qv = embed([q])[0]
        t1 = time.perf_counter()
        scored = sorted(
            ((d["name"], cosine(qv, v)) for d, v in zip(docs, vectors)),
            key=lambda x: -x[1],
        )[:3]
        print(f"\n问：「{q}」    （问题向量化 {(t1 - t0) * 1000:.0f} ms）")
        print(f"  字面匹配 : {lit if lit else '0 条  ← 查不到'}")
        for name, s in scored:
            bar = "█" * max(1, int(s * 20))
            print(f"  语义 top  : {name:10s} {s:.3f} {bar}")

    print("\n" + "=" * 68)
    print(f"总耗时 {time.perf_counter() - t_start:.2f} 秒")
    print("=" * 68)
    print("""
读这个结果要看三件事：
  1. 「免疫」「体虚乏力」这类字面 0 命中的问题，语义检索能不能把**四君子汤**排到前面
     → 能，就说明"用户用自己的词提问"这条路走得通（这是 RAG 的立足点）
  2. 相似度的**绝对值**别当结论：0.6 是高是低，取决于模型和语料，
     要看的是"排序对不对"（top-1 是不是正确答案）
  3. 这就是 RAG 的 R（Retrieval）。下一步是把 top-k 的内容拼进提示词，交给 qwen2.5:3b 生成回答

⚠️ 诚实边界：本脚本只做**检索**，还没有"生成"这一步 —— 所以它不会"回答问题"，
   只会告诉你"哪几条最相关"。生成是 02 号脚本的事。
""")


if __name__ == "__main__":
    main()
