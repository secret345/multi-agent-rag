import os
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import pandas as pd
from api.auth_deps import get_current_user
from db import get_conn
from graph.workflow import app_graph
from agents.writer import writer_agent_stream
from config import DATA_DIR

router = APIRouter()


class ChatHistoryRequest(BaseModel):
    messages: list


class AskRequest(BaseModel):
    query: str
    chat_history: list[dict] = []
    doc_index_ids: list[str] = []


@router.get("/history")
def get_chat_history(phone: str = Depends(get_current_user)):
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT messages FROM chat_history WHERE phone=%s", (phone,))
                row = cur.fetchone()
                if not row or not row["messages"]:
                    return {"messages": []}
                m = row["messages"]
                return {"messages": json.loads(m) if isinstance(m, str) else m}
        finally:
            conn.close()
    except Exception:
        return {"messages": []}


@router.put("/history")
def save_chat_history(req: ChatHistoryRequest, phone: str = Depends(get_current_user)):
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chat_history (phone, messages) VALUES (%s, %s) "
                    "ON DUPLICATE KEY UPDATE messages=VALUES(messages)",
                    (phone, json.dumps(req.messages, ensure_ascii=False)),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        raise HTTPException(status_code=500, detail="保存失败")
    return {"message": "ok"}


@router.delete("/history")
def clear_chat_history(phone: str = Depends(get_current_user)):
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chat_history (phone, messages) VALUES (%s, %s) "
                    "ON DUPLICATE KEY UPDATE messages=VALUES(messages)",
                    (phone, json.dumps([], ensure_ascii=False)),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        raise HTTPException(status_code=500, detail="清空失败")
    return {"message": "ok"}


@router.post("/ask")
async def ask_stream(req: AskRequest, phone: str = Depends(get_current_user)):
    """SSE streaming endpoint: runs LangGraph then streams writer output."""
    result = await asyncio.to_thread(
        app_graph.invoke,
        {
            "query": req.query,
            "chat_history": req.chat_history,
            "doc_index_ids": req.doc_index_ids,
        },
    )

    intent = result["intent"]
    trace = result.get("trace")
    context = result["context"]

    async def event_generator():
        meta = {"type": "meta", "intent": intent, "trace": trace.summary() if trace else ""}
        yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"

        for chunk in writer_agent_stream(req.query, context, req.chat_history):
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/ask-sync")
async def ask_sync(req: AskRequest, phone: str = Depends(get_current_user)):
    """Non-streaming fallback."""
    result = await asyncio.to_thread(
        app_graph.invoke,
        {
            "query": req.query,
            "chat_history": req.chat_history,
            "doc_index_ids": req.doc_index_ids,
        },
    )
    trace = result.get("trace")
    return {
        "query": req.query,
        "intent": result["intent"],
        "answer": result["answer"],
        "trace": trace.summary() if trace else "",
    }


@router.get("/sales-data")
def get_sales_data(phone: str = Depends(get_current_user)):
    csv_path = os.path.join(DATA_DIR, "sales.csv")
    if not os.path.exists(csv_path):
        return {"columns": [], "rows": [], "summary": []}
    df = pd.read_csv(csv_path)
    summary = df.groupby("product")["quantity"].sum().reset_index()
    return {
        "columns": list(df.columns),
        "rows": df.to_dict(orient="records"),
        "summary": summary.to_dict(orient="records"),
    }
