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
VECTORSTORE_DIR = os.path.join(os.path.dirname(__file__), "vectorstore")
