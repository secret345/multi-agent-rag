import os
import contextvars
from dotenv import load_dotenv

load_dotenv()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

LLM_MODEL = "qwen-max"
EMBEDDING_MODEL = "text-embedding-v3"

# Per-request API key storage (injected by FastAPI middleware via set_user_api_key)
_user_api_key_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("user_api_key", default="")


def set_user_api_key(key: str) -> None:
    """Set the per-request user API key. Called by FastAPI middleware."""
    _user_api_key_ctx.set(key)


def get_api_key() -> str:
    """Return per-request user key, or fall back to the global env key."""
    ctx_key = _user_api_key_ctx.get("").strip()
    if ctx_key:
        return ctx_key
    return DASHSCOPE_API_KEY or ""


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
WRITABLE_DIR = DATA_DIR
os.makedirs(WRITABLE_DIR, exist_ok=True)

VECTORSTORE_DIR = os.path.join(WRITABLE_DIR, "vectorstore")
os.makedirs(VECTORSTORE_DIR, exist_ok=True)
