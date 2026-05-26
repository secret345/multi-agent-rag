from rag.retriever import rag_search, get_chunks
from rag.hybrid_retriever import hybrid_search


def rag_agent(query: str, index_ids: list[str] | None = None) -> str:
    if index_ids:
        from rag.doc_retriever import doc_search
        all_results = []
        for index_id in index_ids:
            try:
                results = doc_search(query, index_id, top_k=3)
                all_results.extend(results)
            except FileNotFoundError:
                continue
        if not all_results:
            return "未在上传的文档中找到相关内容"
        from rag.reranker import rerank
        ranked = rerank(query, all_results, top_k=5)
        return "\n\n".join(ranked)

    try:
        chunks = get_chunks()
        results = hybrid_search(query, chunks, top_k=5)
    except Exception:
        results = rag_search(query, top_k=3)

    if not results:
        return "未找到相关知识"
    return "\n\n".join(results)
