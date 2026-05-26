import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATA_DIR
from rag.retriever import rag_search, get_chunks
from rag.hybrid_retriever import hybrid_search


def load_eval_data() -> list[dict]:
    path = os.path.join(DATA_DIR, "eval_qa.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_retrieval(eval_data: list[dict], use_hybrid: bool = True) -> dict:
    chunks = get_chunks()
    total = len(eval_data)
    hit = 0
    results = []

    for item in eval_data:
        question = item["question"]
        keywords = item["keywords"]

        if use_hybrid:
            retrieved = hybrid_search(question, chunks, top_k=5)
        else:
            retrieved = rag_search(question, top_k=5)

        retrieved_text = " ".join(retrieved).lower()

        matched = all(any(kw.lower() in retrieved_text for kw in [k]) for k in keywords) if keywords else True
        if matched:
            hit += 1

        results.append({
            "question": question,
            "keywords": keywords,
            "matched": matched,
            "retrieved_preview": [r[:80] for r in retrieved[:2]],
        })

    accuracy = hit / total if total > 0 else 0
    return {
        "total": total,
        "hit": hit,
        "accuracy": round(accuracy * 100, 1),
        "details": results,
    }


def run_evaluation():
    print("=" * 50)
    print("RAG 检索效果评估")
    print("=" * 50)

    eval_data = load_eval_data()

    print(f"\n测试集: {len(eval_data)} 个问题")
    print("-" * 50)

    print("\n[1] 纯向量检索 (FAISS)")
    vector_result = evaluate_retrieval(eval_data, use_hybrid=False)
    print(f"  准确率: {vector_result['accuracy']}% ({vector_result['hit']}/{vector_result['total']})")

    print("\n[2] 混合检索 (BM25 + Vector + Reranker)")
    hybrid_result = evaluate_retrieval(eval_data, use_hybrid=True)
    print(f"  准确率: {hybrid_result['accuracy']}% ({hybrid_result['hit']}/{hybrid_result['total']})")

    improvement = hybrid_result["accuracy"] - vector_result["accuracy"]
    print(f"\n提升: +{improvement}%")

    print("\n" + "=" * 50)
    print("详细结果:")
    print("-" * 50)
    for i, (vd, hd) in enumerate(zip(vector_result["details"], hybrid_result["details"])):
        status = "OK" if hd["matched"] else "MISS"
        print(f"  [{status}] {vd['question']}")
        if not hd["matched"]:
            print(f"        关键词: {hd['keywords']}")


if __name__ == "__main__":
    run_evaluation()
