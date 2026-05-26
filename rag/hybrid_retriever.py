import numpy as np
from rag.bm25 import bm25_search, build_bm25_index
from rag.retriever import rag_search
from rag.reranker import rerank


def hybrid_search(query: str, chunks: list[str], top_k: int = 5) -> list[str]:
    build_bm25_index(chunks)

    bm25_results = bm25_search(query, top_k=top_k)
    vector_results = rag_search(query, top_k=top_k)

    seen = set()
    merged = []
    for doc, score in bm25_results:
        doc_key = doc[:100]
        if doc_key not in seen:
            seen.add(doc_key)
            merged.append(doc)
    for doc in vector_results:
        doc_key = doc[:100]
        if doc_key not in seen:
            seen.add(doc_key)
            merged.append(doc)

    if not merged:
        return []

    ranked = rerank(query, merged, top_k=top_k)
    return ranked
