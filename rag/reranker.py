from llm import call_llm


def rerank(query: str, documents: list[str], top_k: int = 3) -> list[str]:
    if len(documents) <= top_k:
        return documents

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
