import time
from typing import TypedDict
from langgraph.graph import StateGraph, END

from agents.planner import planner_agent
from agents.rewriter import rewrite_query
from agents.sql_agent import sql_agent
from agents.rag_agent import rag_agent
from agents.writer import writer_agent
from utils.logger import TraceLogger


class AgentState(TypedDict):
    query: str
    rewritten_query: str
    intent: str
    tasks: list[str]
    context: str
    answer: str
    doc_index_ids: list[str]
    chat_history: list[dict]
    trace: object


def _timed_call(node_name: str, func, *args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    duration = (time.time() - start) * 1000
    return result, duration


def planner_node(state: AgentState) -> dict:
    (result, duration) = _timed_call("planner", planner_agent, state["query"])
    trace: TraceLogger = state.get("trace") or TraceLogger()
    trace.log("planner", state["query"], str(result), duration)
    return {"intent": result["intent"], "tasks": result.get("tasks", []), "trace": trace}


def rewriter_node(state: AgentState) -> dict:
    (rewritten, duration) = _timed_call(
        "rewriter", rewrite_query, state["query"], state.get("chat_history", [])
    )
    trace: TraceLogger = state["trace"]
    trace.log("rewriter", state["query"], rewritten, duration)
    return {"rewritten_query": rewritten}


def sql_node(state: AgentState) -> dict:
    query = state.get("rewritten_query", state["query"])
    (data, duration) = _timed_call("sql_agent", sql_agent, query)
    trace: TraceLogger = state["trace"]
    trace.log("sql_agent", query, data, duration)
    return {"context": data}


def rag_node(state: AgentState) -> dict:
    query = state.get("rewritten_query", state["query"])
    (data, duration) = _timed_call("rag_agent", rag_agent, query)
    trace: TraceLogger = state["trace"]
    trace.log("rag_agent", query, data, duration)
    return {"context": data}


def doc_node(state: AgentState) -> dict:
    query = state.get("rewritten_query", state["query"])
    (data, duration) = _timed_call(
        "doc_agent", rag_agent, query, index_ids=state.get("doc_index_ids", [])
    )
    trace: TraceLogger = state["trace"]
    trace.log("doc_agent", query, data, duration)
    return {"context": data}


def writer_node(state: AgentState) -> dict:
    (answer, duration) = _timed_call(
        "writer", writer_agent, state["query"], state["context"], chat_history=state.get("chat_history")
    )
    trace: TraceLogger = state["trace"]
    trace.log("writer", state["query"], answer, duration)
    return {"answer": answer}


def route_by_intent(state: AgentState) -> str:
    if state["intent"] == "sales_analysis":
        return "sql"
    if state["intent"] == "document_analysis":
        return "doc"
    return "rag"


workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("rewriter", rewriter_node)
workflow.add_node("sql", sql_node)
workflow.add_node("rag", rag_node)
workflow.add_node("doc", doc_node)
workflow.add_node("writer", writer_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "rewriter")
workflow.add_conditional_edges("rewriter", route_by_intent, {"sql": "sql", "rag": "rag", "doc": "doc"})
workflow.add_edge("sql", "writer")
workflow.add_edge("rag", "writer")
workflow.add_edge("doc", "writer")
workflow.add_edge("writer", END)

app_graph = workflow.compile()
