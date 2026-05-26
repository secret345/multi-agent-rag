import os
import faiss
import numpy as np
from config import VECTORSTORE_DIR
from rag.embedding import get_embeddings

DISTANCE_THRESHOLD = 1.5


def _load_doc(index_id: str):
    index_path = os.path.join(VECTORSTORE_DIR, f"{index_id}.index")
    chunks_path = os.path.join(VECTORSTORE_DIR, f"{index_id}.chunks")

    if not os.path.exists(index_path) or not os.path.exists(chunks_path):
        raise FileNotFoundError(f"文档索引不存在: {index_id}")

    index = faiss.read_index(index_path)

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = f.read().split("\n===SPLIT===\n")

    return index, chunks


def doc_search(query: str, index_id: str, top_k: int = 3) -> list[str]:
    index, chunks = _load_doc(index_id)

    query_vec = get_embeddings([query])
    query_array = np.array(query_vec, dtype=np.float32)

    distances, indices = index.search(query_array, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if 0 <= idx < len(chunks) and dist < DISTANCE_THRESHOLD:
            results.append(chunks[idx].strip())

    return results
