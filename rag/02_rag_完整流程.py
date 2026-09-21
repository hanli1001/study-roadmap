"""RAG 演示 ② · 完整流程：检索 + 生成（Ollama bge-m3 + qwen2.5:3b）

用法：python rag/02_rag_完整流程.py
前置：Ollama 在跑，且已装 bge-m3 与 qwen2.5:3b

这是 RAG 的全貌 —— 注意它其实只有 5 步：
    ① 检索：用 bge-m3 找出最相关的 k 条资料（复用 01 的向量缓存）
    ② 拼提示词：把资料 + 用户问题 + 规则塞进一个 prompt
    ③ 生成：交给 qwen2.5:3b
    ④ 把答案和"引用来源"一起返回
    ⑤ （进阶）把没检索到的情况老实说出来，而不是编

本脚本刻意保留了一个"坑的演示"：
    同一个问题，问"不看资料"和"看资料"两个版本 —— 差别就是 RAG 的全部价值。
"""
import json
import math
import sqlite3
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "prescriptions.db"
CACHE = Path(__file__).resolve().parent / "_embeddings-cache.json"
OLLAMA = "http://127.0.0.1:11434"
EMB_MODEL = "bge-m3"
LLM_MODEL = "qwen2.5:3b"
TOP_K = 3


def _post(path, payload, timeout=180):
    req = urllib.request.Request(
        f"{OLLAMA}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def embed_one(text, model=EMB_MODEL):
    return _post("/api/embeddings", {"model": model, "prompt": text})["embedding"]


def generate(prompt, model=LLM_MODEL, temperature=0.2):
    """让大模型生成回答。temperature 调低 = 少发挥、更贴资料。"""
    res = _post("/api/generate", {
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": temperature},
    })
    return res["response"].strip()


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def load_docs():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    docs = [
        {"id": r["id"], "name": r["name"],
         "text": f"{r['name']}（{r['category'] or ''}·{r['source'] or ''}）：{r['symptoms'] or ''}"}
        for r in conn.execute("SELECT id, name, category, source, symptoms FROM prescriptions ORDER BY id")
    ]
    conn.close()
    return docs


def retrieve(question, docs, vectors, k=TOP_K):
    """RAG 的 R：把问题变向量，找最像的 k 条。"""
    qv = embed_one(question)
    scored = sorted(((d, cosine(qv, v)) for d, v in zip(docs, vectors)), key=lambda x: -x[1])
    return scored[:k]


def build_prompt(question, hits):
    """RAG 最关键的 10 行：提示词怎么写，决定模型是"装死"还是"会答又会推"。

    ⚠️ 这一版是**实测调出来的**（见 _run-02 的对照实验）：
       写着"资料里没有足够信息就直说"的严格版 → 明明检索对了，模型却回"资料里没有提到"
       改成"资料里有的就要用来回答" → 同一份资料，正确回答并标注 [1]
       教训：提示词太防御 = 模型变懒；要**既鼓励用资料、又保留"没有就说没有"的底线**
    """
    context = "\n".join(f"[{i+1}] {d['text']}" for i, (d, _) in enumerate(hits))
    return f"""根据下面提供的资料回答用户的问题。

资料：
{context}

问题：{question}

要求：
1. 资料里与该问题相关的信息，直接用来回答，别客气
2. 回答正文里不要写 [编号]（就正常说话）；只在**整段回答的最后一行**单独写一行：依据：[编号]
3. 只有当资料确实与问题无关时，才回答"资料里没有提到"，并且不要编造

回答："""


def ask_no_rag(question):
    """对照组：不检索、不给资料，直接问模型。"""
    return generate(f"请回答这个问题：{question}", temperature=0.2)


def main():
    docs = load_docs()
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    vectors = cache["vectors"]
    assert len(vectors) == len(docs), "向量缓存和文档数量不一致，请先跑 01 脚本"

    print(f"知识库 {len(docs)} 条 · 向量 {len(vectors[0])} 维 · "
          f"检索模型 {EMB_MODEL} · 生成模型 {LLM_MODEL}\n")

    questions = [
        "体质差容易累，有什么方子适合？",   # 字面查不到，语义能查到
        "脾气虚怎么调？",                  # 字面接近
        "失眠头晕用什么？",                # 对应四物汤
        "这个方子能治癌症吗？",             # 资料里根本没有 → 看它会不会编（关键测试）
    ]

    for q in questions:
        print("=" * 70)
        print(f"👤 问题：{q}")
        print("=" * 70)

        hits = retrieve(q, docs, vectors)
        print("① 检索到的资料（top-%d）：" % TOP_K)
        for i, (d, s) in enumerate(hits, 1):
            print(f"   [{i}] {d['name']:10s} 相似度 {s:.3f}   {d['text'][:34]}…")

        t0 = time.perf_counter()
        rag_answer = generate(build_prompt(q, hits))
        t1 = time.perf_counter()
        print(f"\n② RAG 回答（{t1 - t0:.1f} 秒）：「{rag_answer}」")

        # 只看前两个正常问题做对照，省时间也省 token
        if "癌症" not in q and "调" not in q:
            t2 = time.perf_counter()
            bare = ask_no_rag(q)
            t3 = time.perf_counter()
            print(f"\n③ 对照·不看资料直接问（{t3 - t2:.1f} 秒）：「{bare[:120]}」")
        print()

    print("=" * 70)
    print("""
看结果时重点看这四件事：

1. **② 的回答里有没有 [编号]** —— 有编号 = 它能溯源；这正是路线 v3 反复强调的
   "MVP 阶段就要能溯源引用"。
2. **"癌症"那个问题**：资料里完全没有 → 好的 RAG 应该回答"资料里没有提到"。
   如果它开始讲药效，那就是**幻觉** —— 这时要回去改提示词（不是换更大的模型）。
3. **① 的相似度排序**比绝对值重要：top-1 对不对，比 0.61 是高是低更值得看。
4. **③ 对照组**：不看资料的模型，答案可能"听起来更全面"，但**没有任何依据** ——
   这就是 RAG 存在的理由，也是它和"直接问 ChatGPT"的本质差别。

接下来该做的（按重要性排）：
  ① 评估：准备一套"问题 → 正确答案"的测试集，量 top-k 的命中率（这就是 Ragas 干的事）
  ② 切片策略：现在一条方剂=一个 chunk；如果文档变长（比如整本教材），要重新设计切法
  ③ 可观测：把每次检索命中了什么、花了多久记下来（Langfuse 干的事）
""")


if __name__ == "__main__":
    main()
