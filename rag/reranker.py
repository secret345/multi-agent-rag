from llm import call_llm

_reranker_model = None
_reranker_failed = False


def _get_reranker():
    global _reranker_model, _reranker_failed
    if _reranker_failed:
        return None
    if _reranker_model is None:
        try:
            from sentence_transformers import CrossEncoder
            _reranker_model = CrossEncoder("BAAI/bge-reranker-v2-m3", max_length=512)
        except Exception:
            _reranker_failed = True
            return None
    return _reranker_model


def _local_rerank(query: str, documents: list[str], top_k: int = 3) -> list[str] | None:
    """用 bge-reranker 模型重排，失败返回 None。"""
    model = _get_reranker()
    if model is None:
        return None
    try:
        pairs = [(query, doc[:512]) for doc in documents]
        scores = model.predict(pairs)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [documents[i] for i in ranked_indices[:top_k]]
    except Exception:
        return None


def _llm_rerank(query: str, documents: list[str], top_k: int = 3) -> list[str]:
    """LLM 重排（降级方案）。"""
    doc_list = "\n".join([f"[{i}] {doc[:300]}" for i, doc in enumerate(documents)])

    prompt = f"""你是一个文档相关性排序专家。根据用户问题，对以下文档按相关性从高到低排序。

用户问题：{query}

文档列表：
{doc_list}

要求：
- 只输出最相关的 {top_k} 个文档编号，用逗号分隔
- 例如：2,0,1
- 只输出编号，不要任何解释"""

    result = call_llm(prompt).strip()

    try:
        indices = [int(x.strip()) for x in result.split(",")]
        ranked = []
        for idx in indices:
            if 0 <= idx < len(documents):
                ranked.append(documents[idx])
        if ranked:
            return ranked[:top_k]
    except (ValueError, IndexError):
        pass

    return documents[:top_k]


def rerank(query: str, documents: list[str], top_k: int = 3) -> list[str]:
    if len(documents) <= top_k:
        return documents

    # 优先用本地 reranker，失败则降级到 LLM
    result = _local_rerank(query, documents, top_k)
    if result is not None:
        return result

    return _llm_rerank(query, documents, top_k)
