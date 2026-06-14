import asyncio
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from graph.workflow import app_graph
from config import set_user_api_key
from api.auth_deps import get_current_user, load_user_api_key
from api.auth_router import router as auth_router
from api.chat_router import router as chat_router
from api.docs_router import router as docs_router
from api.settings_router import router as settings_router

app = FastAPI(title="Multi-Agent RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def inject_api_key_middleware(request: Request, call_next):
    """Inject per-user API key into contextvars before request handling."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            from api.auth_deps import decode_token
            token = auth_header[7:]
            payload = decode_token(token)
            phone = payload.get("sub", "")
            if phone:
                user_key = load_user_api_key(phone)
                set_user_api_key(user_key)
        except Exception:
            pass
    response = await call_next(request)
    return response


app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(docs_router, prefix="/api/documents", tags=["documents"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])


class AskRequest(BaseModel):
    query: str
    chat_history: list[dict] = []
    doc_index_ids: list[str] = []


@app.get("/")
def root():
    return {"status": "running"}


@app.post("/ask")
async def ask(req: AskRequest):
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
