import os
import math
import json
import jieba
from collections import Counter
from config import VECTORSTORE_DIR

_stopwords = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}

_tokenized_corpus: list[list[str]] | None = None
_doc_chunks: list[str] | None = None
_idf: dict[str, float] | None = None


def _tokenize(text: str) -> list[str]:
    tokens = jieba.lcut(text)
    return [t for t in tokens if t.strip() and t not in _stopwords]


def _bm25_index_path(name: str = "knowledge") -> str:
    return os.path.join(VECTORSTORE_DIR, f"{name}.bm25")


def save_bm25_index(chunks: list[str], name: str = "knowledge"):
    tokenized = [_tokenize(c) for c in chunks]

    df: dict[str, int] = {}
    for tokens in tokenized:
        for t in set(tokens):
            df[t] = df.get(t, 0) + 1
    n = len(tokenized)
    idf = {t: math.log((n - df_t + 0.5) / (df_t + 0.5) + 1) for t, df_t in df.items()}

    data = {
        "chunks": chunks,
        "tokenized": tokenized,
        "idf": idf,
    }
    path = _bm25_index_path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def load_bm25_index(name: str = "knowledge") -> bool:
    global _tokenized_corpus, _doc_chunks, _idf
    path = _bm25_index_path(name)
    if not os.path.exists(path):
        return False
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _doc_chunks = data["chunks"]
    _tokenized_corpus = data["tokenized"]
    _idf = data["idf"]
    return True


def build_bm25_index(chunks: list[str], name: str = "knowledge"):
    global _tokenized_corpus, _doc_chunks, _idf
    if load_bm25_index(name):
        return
    _doc_chunks = chunks
    _tokenized_corpus = [_tokenize(c) for c in chunks]

    df: dict[str, int] = {}
    for tokens in _tokenized_corpus:
        for t in set(tokens):
            df[t] = df.get(t, 0) + 1
    n = len(_tokenized_corpus)
    _idf = {t: math.log((n - df_t + 0.5) / (df_t + 0.5) + 1) for t, df_t in df.items()}

    save_bm25_index(chunks, name)


def _bm25_score(query_tokens: list[str], doc_tokens: list[str], k1: float = 1.5, b: float = 0.75) -> float:
    if not _idf or not _doc_chunks:
        return 0.0
    doc_len = len(doc_tokens)
    avg_dl = sum(len(t) for t in _tokenized_corpus) / len(_tokenized_corpus) if _tokenized_corpus else 1
    tf = Counter(doc_tokens)
    score = 0.0
    for qt in query_tokens:
        if qt not in _idf:
            continue
        f = tf.get(qt, 0)
        idf = _idf[qt]
        numerator = f * (k1 + 1)
        denominator = f + k1 * (1 - b + b * doc_len / avg_dl)
        score += idf * numerator / denominator
    return score


def bm25_search(query: str, top_k: int = 5) -> list[tuple[str, float]]:
    if _tokenized_corpus is None or _doc_chunks is None:
        raise RuntimeError("BM25 索引未构建，请先调用 build_bm25_index")

    query_tokens = _tokenize(query)
    scores = []
    for i, doc_tokens in enumerate(_tokenized_corpus):
        score = _bm25_score(query_tokens, doc_tokens)
        scores.append((_doc_chunks[i], score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]
