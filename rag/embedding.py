from dashscope import TextEmbedding
from config import get_api_key, EMBEDDING_MODEL


def get_embeddings(texts: list[str], batch_size: int = 10) -> list[list[float]]:
    api_key = get_api_key()
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY 未设置，请在侧边栏填入或在 .env 文件中配置")

    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = TextEmbedding.call(
            model=EMBEDDING_MODEL,
            input=batch,
            api_key=api_key,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Embedding 调用失败: {response.code} - {response.message}")
        all_embeddings.extend(item["embedding"] for item in response.output["embeddings"])

    return all_embeddings


