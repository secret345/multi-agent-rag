from unittest.mock import patch, MagicMock
import pytest


class TestHybridSearch:
    @patch("rag.hybrid_retriever.rerank")
    @patch("rag.hybrid_retriever.rag_search")
    @patch("rag.hybrid_retriever.bm25_search")
    @patch("rag.hybrid_retriever.build_bm25_index")
    def test_merges_results_from_both_sources(self, mock_build, mock_bm25, mock_vector, mock_rerank):
        mock_bm25.return_value = [("doc A from bm25", 2.5), ("doc B from bm25", 1.8)]
        mock_vector.return_value = ["doc C from vector", "doc A from bm25"]
        mock_rerank.return_value = ["doc A from bm25", "doc C from vector", "doc B from bm25"]

        from rag.hybrid_retriever import hybrid_search
        result = hybrid_search("test query", ["chunk1", "chunk2"], top_k=3)

        mock_build.assert_called_once()
        mock_bm25.assert_called_once()
        mock_vector.assert_called_once()
        mock_rerank.assert_called_once()
        assert len(result) == 3

    @patch("rag.hybrid_retriever.rerank")
    @patch("rag.hybrid_retriever.rag_search")
    @patch("rag.hybrid_retriever.bm25_search")
    @patch("rag.hybrid_retriever.build_bm25_index")
    def test_deduplicates_by_first_100_chars(self, mock_build, mock_bm25, mock_vector, mock_rerank):
        shared_prefix = "x" * 100
        doc_a = shared_prefix + " version A extra content"
        doc_a2 = shared_prefix + " version B extra content"

        mock_bm25.return_value = [(doc_a, 2.0)]
        mock_vector.return_value = [doc_a2, "completely different doc"]
        mock_rerank.side_effect = lambda q, docs, top_k: docs[:top_k]

        from rag.hybrid_retriever import hybrid_search
        result = hybrid_search("test", [], top_k=5)

        # doc_a and doc_a2 share first 100 chars, so only one should pass dedup
        assert len(result) == 2

    @patch("rag.hybrid_retriever.rerank")
    @patch("rag.hybrid_retriever.rag_search")
    @patch("rag.hybrid_retriever.bm25_search")
    @patch("rag.hybrid_retriever.build_bm25_index")
    def test_empty_results(self, mock_build, mock_bm25, mock_vector, mock_rerank):
        mock_bm25.return_value = []
        mock_vector.return_value = []

        from rag.hybrid_retriever import hybrid_search
        result = hybrid_search("no match", [], top_k=5)

        assert result == []
        mock_rerank.assert_not_called()

    @patch("rag.hybrid_retriever.rerank")
    @patch("rag.hybrid_retriever.rag_search")
    @patch("rag.hybrid_retriever.bm25_search")
    @patch("rag.hybrid_retriever.build_bm25_index")
    def test_bm25_results_prioritized(self, mock_build, mock_bm25, mock_vector, mock_rerank):
        mock_bm25.return_value = [("bm25 doc", 3.0)]
        mock_vector.return_value = ["vector doc"]
        mock_rerank.side_effect = lambda q, docs, top_k: docs[:top_k]

        from rag.hybrid_retriever import hybrid_search
        result = hybrid_search("test", [], top_k=5)

        # BM25 results should come first in the merged list
        assert result[0] == "bm25 doc"
        assert result[1] == "vector doc"
