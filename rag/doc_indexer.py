import os
import faiss
import numpy as np
from config import VECTORSTORE_DIR
from rag.embedding import get_embeddings
from rag.doc_parser import parse_document
from rag.chunking import recursive_split


def build_doc_index(file_path: str, index_id: str) -> str:
    text = parse_document(file_path)

    chunks = recursive_split(text, chunk_size=500, chunk_overlap=50)
    chunks = [c.strip() for c in chunks if c.strip()]

    if not chunks:
        raise ValueError("文档内容为空，无法构建索引")

    embeddings = get_embeddings(chunks)
    vectors = np.array(embeddings, dtype=np.float32)

    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)

    index_path = os.path.join(VECTORSTORE_DIR, f"{index_id}.index")
    chunks_path = os.path.join(VECTORSTORE_DIR, f"{index_id}.chunks")

    faiss.write_index(index, index_path)

    with open(chunks_path, "w", encoding="utf-8") as f:
        f.write("\n===SPLIT===\n".join(chunks))

    return index_id
