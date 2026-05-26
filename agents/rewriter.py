from llm import call_llm


def rewrite_query(query: str, chat_history: list[dict]) -> str:
    if not chat_history:
        return query

    history_text = ""
    for msg in chat_history[-6:]:
        role = "用户" if msg.get("role") == "user" else "助手"
        history_text += f"{role}: {msg.get('content', '')}\n"

    prompt = f"""你是一个查询重写器。根据对话历史，将用户的最新问题重写为一个独立、完整的查询。
如果用户的问题已经是完整的，直接返回原问题。

对话历史：
{history_text}
用户最新问题：{query}

要求：
- 将代词（这、那、它、上面、前面等）替换为实际指代的对象
- 补充缺失的上下文信息
- 只输出重写后的查询，不要任何解释"""

    result = call_llm(prompt)
    rewritten = result.strip()
    return rewritten if rewritten else query
