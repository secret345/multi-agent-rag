from unittest.mock import patch, MagicMock
import pytest


class TestWorkflowRouting:
    @patch("graph.workflow.writer_agent")
    @patch("graph.workflow.rag_agent")
    @patch("graph.workflow.rewrite_query")
    @patch("graph.workflow.planner_agent")
    def test_sales_analysis_routes_to_sql(self, mock_planner, mock_rewriter, mock_rag, mock_writer):
        mock_planner.return_value = {"intent": "sales_analysis", "tasks": []}
        mock_rewriter.return_value = "手机销量多少"
        mock_writer.return_value = "手机销量350台"

        with patch("graph.workflow.sql_agent") as mock_sql:
            mock_sql.return_value = "销量数据: 手机 350台"
            from graph.workflow import app_graph
            result = app_graph.invoke({
                "query": "手机销量多少",
                "doc_index_ids": [],
                "chat_history": [],
            })
            assert result["intent"] == "sales_analysis"
            mock_sql.assert_called_once()

    @patch("graph.workflow.writer_agent")
    @patch("graph.workflow.rag_agent")
    @patch("graph.workflow.rewrite_query")
    @patch("graph.workflow.planner_agent")
    def test_knowledge_query_routes_to_rag(self, mock_planner, mock_rewriter, mock_rag, mock_writer):
        mock_planner.return_value = {"intent": "knowledge_query", "tasks": []}
        mock_rewriter.return_value = "公司成立时间"
        mock_rag.return_value = "公司成立于2020年"
        mock_writer.return_value = "公司成立于2020年。"

        from graph.workflow import app_graph
        result = app_graph.invoke({
            "query": "公司成立时间",
            "doc_index_ids": [],
            "chat_history": [],
        })
        assert result["intent"] == "knowledge_query"
        mock_rag.assert_called_once()

    @patch("graph.workflow.writer_agent")
    @patch("graph.workflow.rag_agent")
    @patch("graph.workflow.rewrite_query")
    @patch("graph.workflow.planner_agent")
    def test_document_analysis_routes_to_doc(self, mock_planner, mock_rewriter, mock_rag, mock_writer):
        mock_planner.return_value = {"intent": "document_analysis", "tasks": []}
        mock_rewriter.return_value = "总结上传的文档"
        mock_rag.return_value = "文档摘要内容"
        mock_writer.return_value = "根据文档..."

        from graph.workflow import app_graph
        result = app_graph.invoke({
            "query": "总结上传的文档",
            "doc_index_ids": ["doc_abc123"],
            "chat_history": [],
        })
        assert result["intent"] == "document_analysis"
        mock_rag.assert_called_once()

    @patch("graph.workflow.writer_agent")
    @patch("graph.workflow.rag_agent")
    @patch("graph.workflow.rewrite_query")
    @patch("graph.workflow.planner_agent")
    def test_unknown_intent_defaults_to_rag(self, mock_planner, mock_rewriter, mock_rag, mock_writer):
        mock_planner.return_value = {"intent": "something_weird", "tasks": []}
        mock_rewriter.return_value = "随便问"
        mock_rag.return_value = "通用回答"
        mock_writer.return_value = "回答内容"

        from graph.workflow import app_graph
        result = app_graph.invoke({
            "query": "随便问",
            "doc_index_ids": [],
            "chat_history": [],
        })
        mock_rag.assert_called_once()
