import os
import faiss
import numpy as np
from config import DATA_DIR, VECTORSTORE_DIR
from rag.embedding import get_embeddings
from rag.chunking import recursive_split
from rag.bm25 import save_bm25_index


def build_index(source_file: str = "knowledge.txt"):
    source_path = os.path.join(DATA_DIR, source_file)

    if not os.path.exists(source_path):
        raise FileNotFoundError(f"知识文件不存在: {source_path}")

    with open(source_path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = recursive_split(text, chunk_size=500, chunk_overlap=50)
    chunks = [c.strip() for c in chunks if c.strip()]

    if not chunks:
        raise ValueError("知识文件为空")

    embeddings = get_embeddings(chunks)
    vectors = np.array(embeddings, dtype=np.float32)

    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)

    index_path = os.path.join(VECTORSTORE_DIR, "knowledge.index")
    chunks_path = os.path.join(VECTORSTORE_DIR, "knowledge.chunks")

    faiss.write_index(index, index_path)

    with open(chunks_path, "w", encoding="utf-8") as f:
        f.write("\n===SPLIT===\n".join(chunks))

    save_bm25_index(chunks, "knowledge")
    print(f"索引构建完成，共 {len(chunks)} 个文本块（含 BM25 + FAISS）")


if __name__ == "__main__":
    build_index()
