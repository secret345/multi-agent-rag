from llm import call_llm
from rag.bm25 import bm25_search, build_bm25_index
from rag.retriever import rag_search
from rag.reranker import rerank

RRF_K = 60  # RRF 常数，业界默认值


def _hyde_expand(query: str) -> str:
    """HyDE: 用 LLM 生成假设性回答，用于向量检索。"""
    prompt = f"""请根据以下问题，写一段简短的回答（2-3句话）。不需要完全准确，只需提供一个可能的答案方向。

问题：{query}

回答："""
    try:
        return call_llm(prompt).strip()
    except Exception:
        return query  # 降级：LLM 失败则用原始 query


def _rrf_merge(bm25_results: list[tuple[str, float]], vector_results: list[tuple[str, float]], top_k: int = 5) -> list[str]:
    """RRF 融合：按排名加权合并两路检索结果。"""
    scores: dict[str, float] = {}

    for rank, (doc, _) in enumerate(bm25_results):
        doc_key = doc[:100]
        scores[doc_key] = scores.get(doc_key, 0.0) + 1.0 / (RRF_K + rank + 1)

    for rank, (doc, _) in enumerate(vector_results):
        doc_key = doc[:100]
        scores[doc_key] = scores.get(doc_key, 0.0) + 1.0 / (RRF_K + rank + 1)

    # 保留原始文本（优先用 BM25 的，因为关键词更完整）
    doc_text_map: dict[str, str] = {}
    for doc, _ in bm25_results:
        doc_key = doc[:100]
        doc_text_map[doc_key] = doc
    for doc, _ in vector_results:
        doc_key = doc[:100]
        if doc_key not in doc_text_map:
            doc_text_map[doc_key] = doc

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_text_map[key] for key, _ in ranked[:top_k]]


def hybrid_search(query: str, chunks: list[str] | None = None, top_k: int = 5) -> list[str]:
    if chunks is None:
        from rag.retriever import get_chunks
        chunks = get_chunks()

    build_bm25_index(chunks)

    # Step 1: BM25 用原始 query
    bm25_results = bm25_search(query, top_k=top_k)

    # Step 2: HyDE 扩展后做向量检索
    hyde_query = _hyde_expand(query)
    vector_results = rag_search(hyde_query, top_k=top_k, return_scores=True)

    # Step 3: RRF 融合
    merged = _rrf_merge(bm25_results, vector_results, top_k=top_k * 2)

    if not merged:
        return []

    # Step 4: Rerank
    ranked = rerank(query, merged, top_k=top_k)
    return ranked
