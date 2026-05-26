from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph.workflow import app_graph

app = FastAPI(title="Multi-Agent RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    query: str
    chat_history: list[dict] = []
    doc_index_ids: list[str] = []


@app.get("/")
def root():
    return {"status": "running"}


@app.post("/ask")
async def ask(req: AskRequest):
    result = app_graph.invoke({
        "query": req.query,
        "chat_history": req.chat_history,
        "doc_index_ids": req.doc_index_ids,
    })
    trace = result.get("trace")
    return {
        "query": req.query,
        "intent": result["intent"],
        "answer": result["answer"],
        "trace": trace.summary() if trace else "",
    }
