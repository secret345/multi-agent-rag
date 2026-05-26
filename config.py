import os
from dotenv import load_dotenv

load_dotenv()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

if not DASHSCOPE_API_KEY:
    try:
        import streamlit as st
        DASHSCOPE_API_KEY = st.secrets.get("DASHSCOPE_API_KEY", "")
    except Exception:
        pass

LLM_MODEL = "qwen-max"
EMBEDDING_MODEL = "text-embedding-v3"

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Streamlit Cloud uses ephemeral filesystem; writable data goes to /tmp
IS_CLOUD = os.environ.get("STREAMLIT_SHARING_MODE") == "true" or not os.access(
    os.path.join(os.path.dirname(__file__), "data"), os.W_OK
)
WRITABLE_DIR = "/tmp/multi_agent_rag" if IS_CLOUD else DATA_DIR
os.makedirs(WRITABLE_DIR, exist_ok=True)

VECTORSTORE_DIR = os.path.join(WRITABLE_DIR, "vectorstore")
os.makedirs(VECTORSTORE_DIR, exist_ok=True)
