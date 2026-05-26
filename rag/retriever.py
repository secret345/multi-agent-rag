import os
import faiss
import numpy as np
from config import VECTORSTORE_DIR
from rag.embedding import get_embeddings

_index = None
_chunks = None

DISTANCE_THRESHOLD = 1.5


def _load():
    global _index, _chunks

    index_path = os.path.join(VECTORSTORE_DIR, "knowledge.index")
    chunks_path = os.path.join(VECTORSTORE_DIR, "knowledge.chunks")

    if not os.path.exists(index_path) or not os.path.exists(chunks_path):
        raise FileNotFoundError("向量索引不存在，请先运行 python -m rag.indexer 构建")

    _index = faiss.read_index(index_path)

    with open(chunks_path, "r", encoding="utf-8") as f:
        _chunks = f.read().split("\n===SPLIT===\n")


def get_chunks() -> list[str]:
    if _chunks is None:
        _load()
    return _chunks


def rag_search(query: str, top_k: int = 3) -> list[str]:
    global _index, _chunks

    if _index is None:
        _load()

    query_vec = get_embeddings([query])
    query_array = np.array(query_vec, dtype=np.float32)

    distances, indices = _index.search(query_array, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if 0 <= idx < len(_chunks) and dist < DISTANCE_THRESHOLD:
            results.append(_chunks[idx].strip())

    return results
