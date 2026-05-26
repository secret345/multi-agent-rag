from llm import call_llm, call_llm_stream


def _build_prompt(query: str, context: str, chat_history: list[dict] | None = None) -> str:
    history_text = ""
    if chat_history:
        for msg in chat_history[-6:]:
            role = "用户" if msg.get("role") == "user" else "助手"
            history_text += f"{role}: {msg.get('content', '')}\n"

    return f"""你是企业知识助手。基于以下上下文和对话历史回答用户问题。

{"对话历史：" + chr(10) + history_text if history_text else ""}
用户问题：{query}

上下文：
{context}

要求：
- 使用中文
- 回答准确简洁
- 上下文没有的信息不要编造
- 如果对话历史中有相关信息，可以引用"""


def writer_agent(query: str, context: str, chat_history: list[dict] | None = None) -> str:
    prompt = _build_prompt(query, context, chat_history)
    return call_llm(prompt)


def writer_agent_stream(query: str, context: str, chat_history: list[dict] | None = None):
    prompt = _build_prompt(query, context, chat_history)
    return call_llm_stream(prompt)
