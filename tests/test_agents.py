import json
from unittest.mock import patch, MagicMock
import pytest


class TestPlannerAgent:
    @patch("agents.planner.call_llm")
    def test_sales_intent(self, mock_llm):
        mock_llm.return_value = json.dumps({
            "intent": "sales_analysis",
            "tasks": ["query sales data"]
        })
        from agents.planner import planner_agent
        result = planner_agent("手机销量多少")
        assert result["intent"] == "sales_analysis"

    @patch("agents.planner.call_llm")
    def test_knowledge_intent(self, mock_llm):
        mock_llm.return_value = json.dumps({
            "intent": "knowledge_query",
            "tasks": ["answer question"]
        })
        from agents.planner import planner_agent
        result = planner_agent("公司成立时间")
        assert result["intent"] == "knowledge_query"

    @patch("agents.planner.call_llm")
    def test_invalid_json_fallback(self, mock_llm):
        mock_llm.return_value = "这不是JSON"
        from agents.planner import planner_agent
        result = planner_agent("随便问")
        assert result["intent"] == "knowledge_query"

    @patch("agents.planner.call_llm")
    def test_invalid_intent_fallback(self, mock_llm):
        mock_llm.return_value = json.dumps({
            "intent": "unknown_intent",
            "tasks": ["something"]
        })
        from agents.planner import planner_agent
        result = planner_agent("随便问")
        assert result["intent"] == "knowledge_query"


class TestSqlAgent:
    def test_generate_sql(self):
        import agents.sql_agent as sa
        with patch.object(sa, "call_llm") as mock_llm:
            mock_llm.side_effect = [
                "SELECT product, SUM(quantity) as total FROM sales GROUP BY product ORDER BY total DESC LIMIT 1",
                "销量最高的产品是手机，总销量为XXX台。"
            ]
            result = sa.sql_agent("哪个产品卖得最好")
            assert isinstance(result, str)
            assert len(result) > 0


class TestRewriter:
    @patch("agents.rewriter.call_llm")
    def test_rewrite_with_history(self, mock_llm):
        mock_llm.return_value = "笔记本的销量是多少"
        from agents.rewriter import rewrite_query
        history = [
            {"role": "user", "content": "手机销量多少"},
            {"role": "assistant", "content": "手机销量为350台"},
        ]
        result = rewrite_query("那笔记本呢", history)
        assert result == "笔记本的销量是多少"

    @patch("agents.rewriter.call_llm")
    def test_no_history_returns_original(self, mock_llm):
        from agents.rewriter import rewrite_query
        result = rewrite_query("手机销量多少", [])
        assert result == "手机销量多少"
        mock_llm.assert_not_called()


class TestWriter:
    @patch("agents.writer.call_llm")
    def test_writer_with_history(self, mock_llm):
        mock_llm.return_value = "根据数据，笔记本总销量为235台。"
        from agents.writer import writer_agent
        result = writer_agent(
            "笔记本销量多少",
            "笔记本销量数据...",
            chat_history=[
                {"role": "user", "content": "手机销量多少"},
                {"role": "assistant", "content": "手机销量350台"},
            ]
        )
        assert "笔记本" in result
