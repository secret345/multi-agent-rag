import streamlit as st
st.set_page_config(page_title="企业数据分析助手", page_icon="📊", layout="wide")

import pandas as pd
import plotly.express as px
import uuid
import json
import os
import re
from graph.workflow import app_graph
from agents.writer import writer_agent_stream
from config import DATA_DIR, WRITABLE_DIR, VECTORSTORE_DIR
from rag.doc_indexer import build_doc_index
from auth.user_auth import register_user, verify_user, reset_password, user_exists
from auth.sms_service import generate_code, send_sms, verify_code
from db import get_conn, init_db

try:
    init_db()
except Exception:
    pass


def _sanitize_filename(name: str) -> str:
    """Sanitize uploaded filename to prevent path traversal."""
    name = os.path.basename(name)
    name = name.replace("..", "")
    if not name or name.startswith("."):
        name = "unnamed"
    return name


def _user_dir() -> str:
    return st.session_state.get("user_data_dir", os.path.join(WRITABLE_DIR, "users", "anonymous"))


def load_user_settings() -> dict:
    phone = st.session_state.get("user_phone", "")
    if not phone:
        return {}
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT settings FROM user_settings WHERE phone=%s", (phone,))
                row = cur.fetchone()
                return row["settings"] if row else {}
        finally:
            conn.close()
    except Exception:
        return {}


def save_user_settings(settings: dict):
    phone = st.session_state.get("user_phone", "")
    if not phone:
        return
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO user_settings (phone, settings) VALUES (%s, %s) "
                    "ON DUPLICATE KEY UPDATE settings=VALUES(settings)",
                    (phone, json.dumps(settings, ensure_ascii=False)),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def load_chat_history() -> list:
    phone = st.session_state.get("user_phone", "")
    if not phone:
        return []
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT messages FROM chat_history WHERE phone=%s", (phone,))
                row = cur.fetchone()
                return row["messages"] if row else []
        finally:
            conn.close()
    except Exception:
        return []


def save_chat_history(messages: list):
    phone = st.session_state.get("user_phone", "")
    if not phone:
        return
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chat_history (phone, messages) VALUES (%s, %s) "
                    "ON DUPLICATE KEY UPDATE messages=VALUES(messages)",
                    (phone, json.dumps(messages, ensure_ascii=False)),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def load_user_documents() -> list:
    phone = st.session_state.get("user_phone", "")
    if not phone:
        return []
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT index_id, filename FROM user_documents WHERE phone=%s",
                    (phone,),
                )
                return cur.fetchall()
        finally:
            conn.close()
    except Exception:
        return []


def save_user_document(index_id: str, filename: str):
    phone = st.session_state.get("user_phone", "")
    if not phone:
        return
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO user_documents (phone, index_id, filename) VALUES (%s, %s, %s)",
                    (phone, index_id, filename),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def delete_user_document(index_id: str):
    phone = st.session_state.get("user_phone", "")
    if not phone:
        return
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM user_documents WHERE phone=%s AND index_id=%s",
                    (phone, index_id),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def render_message(msg: dict):
    intent = msg.get("intent", "")
    with st.chat_message("user"):
        st.write(msg["query"])
    with st.chat_message("assistant"):
        if intent == "sales_analysis":
            st.write(msg["answer"])
            csv_path = os.path.join(DATA_DIR, "sales.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.caption("原始数据")
                    st.dataframe(df, use_container_width=True)
                with col2:
                    st.caption("销量统计")
                    summary = df.groupby("product")["quantity"].sum().reset_index()
                    fig = px.bar(summary, x="product", y="quantity", color="product",
                                 labels={"product": "产品", "quantity": "销量"},
                                 text_auto=True)
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
        elif intent == "document_analysis":
            doc_names = msg.get("doc_filenames", [])
            st.caption(f"文档分析: {', '.join(doc_names)}")
            st.write(msg["answer"])
        else:
            st.write(msg["answer"])


def is_valid_phone(phone: str) -> bool:
    return bool(re.match(r"^1[3-9]\d{9}$", phone))


def auth_page():
    st.title("企业数据分析助手")

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"
    if "reset_phone" not in st.session_state:
        st.session_state.reset_phone = ""
    if "reset_step" not in st.session_state:
        st.session_state.reset_step = 1

    tab_login, tab_register, tab_reset = st.tabs(["登录", "注册", "忘记密码"])

    with tab_login:
        st.subheader("手机号 + 密码登录")
        login_phone = st.text_input("手机号", key="login_phone")
        login_pwd = st.text_input("密码", type="password", key="login_pwd")
        if st.button("登录", key="btn_login"):
            if not is_valid_phone(login_phone):
                st.error("请输入正确的手机号")
            elif not login_pwd:
                st.error("请输入密码")
            elif verify_user(login_phone, login_pwd):
                st.session_state.authenticated = True
                st.session_state.user_phone = login_phone
                st.rerun()
            else:
                st.error("手机号或密码错误")

    with tab_register:
        st.subheader("注册新账号")
        reg_phone = st.text_input("手机号", key="reg_phone")
        reg_pwd = st.text_input("密码", type="password", key="reg_pwd")
        reg_pwd2 = st.text_input("确认密码", type="password", key="reg_pwd2")
        if st.button("注册", key="btn_register"):
            if not is_valid_phone(reg_phone):
                st.error("请输入正确的手机号")
            elif len(reg_pwd) < 6:
                st.error("密码至少6位")
            elif reg_pwd != reg_pwd2:
                st.error("两次密码不一致")
            elif user_exists(reg_phone):
                st.error("该手机号已注册")
            else:
                register_user(reg_phone, reg_pwd)
                st.success("注册成功，请登录")

    with tab_reset:
        st.subheader("重置密码")
        if st.session_state.reset_step == 1:
            reset_phone = st.text_input("注册手机号", key="reset_phone_input")
            if st.button("发送验证码", key="btn_send_code"):
                if not is_valid_phone(reset_phone):
                    st.error("请输入正确的手机号")
                elif not user_exists(reset_phone):
                    st.error("该手机号未注册")
                else:
                    code = generate_code(reset_phone)
                    if code is None:
                        st.error("发送过于频繁，请稍后再试")
                    else:
                        send_sms(reset_phone, code)
                        st.session_state.reset_phone = reset_phone
                        st.session_state.reset_step = 2
                        st.success("验证码已发送（模拟模式，查看控制台）")
                        st.rerun()

        elif st.session_state.reset_step == 2:
            st.info(f"验证码已发送至 {st.session_state.reset_phone}")
            st.caption("模拟模式：验证码打印在控制台，请查看终端输出")
            input_code = st.text_input("6位验证码", key="input_code")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("验证", key="btn_verify"):
                    if verify_code(st.session_state.reset_phone, input_code):
                        st.session_state.reset_step = 3
                        st.success("验证成功")
                        st.rerun()
                    else:
                        st.error("验证码错误或已过期")
            with col2:
                if st.button("重新发送", key="btn_resend"):
                    code = generate_code(st.session_state.reset_phone)
                    if code is None:
                        st.error("发送过于频繁，请稍后再试")
                    else:
                        send_sms(st.session_state.reset_phone, code)
                        st.success("验证码已重新发送")

        elif st.session_state.reset_step == 3:
            new_pwd = st.text_input("新密码", type="password", key="new_pwd")
            new_pwd2 = st.text_input("确认新密码", type="password", key="new_pwd2")
            if st.button("重置密码", key="btn_reset"):
                if len(new_pwd) < 6:
                    st.error("密码至少6位")
                elif new_pwd != new_pwd2:
                    st.error("两次密码不一致")
                else:
                    reset_password(st.session_state.reset_phone, new_pwd)
                    st.success("密码重置成功，请登录")
                    st.session_state.reset_step = 1
                    st.session_state.reset_phone = ""
                    st.rerun()

    return False


def check_auth():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    auth_page()
    return False


if not check_auth():
    st.stop()

# Ensure user directory is set and belongs to the current user
current_phone = st.session_state.get("user_phone", "anonymous")
cached_owner = st.session_state.get("data_owner")
user_changed = cached_owner != current_phone

if user_changed:
    st.session_state.data_owner = current_phone
    st.session_state.user_data_dir = os.path.join(WRITABLE_DIR, "users", current_phone)
    os.makedirs(st.session_state.user_data_dir, exist_ok=True)
    os.makedirs(os.path.join(st.session_state.user_data_dir, "uploads"), exist_ok=True)

# Auto-build knowledge index if missing (first deploy on Streamlit Cloud)
from config import get_api_key
from rag.retriever import _load as _load_retriever
try:
    _load_retriever()
except FileNotFoundError:
    if get_api_key():
        with st.spinner("首次启动，正在构建知识库索引..."):
            from rag.indexer import build_index
            build_index()
    else:
        st.warning("请先在侧边栏填入 DashScope API Key 以构建知识库索引")

# Reload documents and messages when user changes
if user_changed or "documents" not in st.session_state:
    st.session_state.documents = load_user_documents()
if user_changed or "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

# Load saved API key when user changes
if user_changed:
    settings = load_user_settings()
    st.session_state.user_api_key = settings.get("api_key", "")
    st.session_state.last_saved_api_key = settings.get("api_key", "")

st.title("企业数据分析助手")
st.caption(f"欢迎，{st.session_state.get('user_phone', '')}")

with st.sidebar:
    st.header("API 设置")
    user_key = st.text_input(
        "DashScope API Key（留空则使用系统默认）",
        type="password",
        key="user_api_key",
        placeholder="sk-xxxxxxxx",
    )
    # Auto-save API key when changed
    current_key = st.session_state.get("user_api_key", "")
    if current_key != st.session_state.get("last_saved_api_key", ""):
        save_user_settings({"api_key": current_key})
        st.session_state.last_saved_api_key = current_key

    st.divider()
    st.header("文档上传")
    uploaded_files = st.file_uploader(
        "上传文档进行分析（支持多文件）",
        type=["txt", "pdf", "docx"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        existing_names = {d["filename"] for d in st.session_state.documents}
        for uploaded_file in uploaded_files:
            safe_name = _sanitize_filename(uploaded_file.name)
            if safe_name in existing_names:
                continue
            with st.spinner(f"正在索引 {safe_name}..."):
                save_path = os.path.join(_user_dir(), "uploads", safe_name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                index_id = f"doc_{uuid.uuid4().hex[:8]}"
                build_doc_index(save_path, index_id)
            st.session_state.documents.append({
                "index_id": index_id,
                "filename": safe_name,
            })
            existing_names.add(safe_name)
            save_user_document(index_id, safe_name)
            st.success(f"'{safe_name}' 索引完成")

    if st.session_state.documents:
        st.subheader("已上传文档")
        for i, doc in enumerate(st.session_state.documents):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.caption(doc["filename"])
            with col2:
                if st.button("x", key=f"del_{i}"):
                    upload_path = os.path.join(_user_dir(), "uploads", doc["filename"])
                    if os.path.exists(upload_path):
                        os.remove(upload_path)
                    for ext in [".index", ".chunks"]:
                        p = os.path.join(VECTORSTORE_DIR, f"{doc['index_id']}{ext}")
                        if os.path.exists(p):
                            os.remove(p)
                    delete_user_document(doc["index_id"])
                    st.session_state.documents.pop(i)
                    st.rerun()

    st.divider()
    if st.button("清空对话记录"):
        st.session_state.messages = []
        save_chat_history([])
        st.rerun()

    st.divider()
    if st.button("退出登录"):
        st.session_state.authenticated = False
        st.session_state.user_phone = ""
        st.rerun()

for msg in st.session_state.messages:
    render_message(msg)

query = st.chat_input("请输入你的问题")

if query:
    with st.chat_message("user"):
        st.write(query)

    with st.chat_message("assistant"):
        with st.spinner("AI 思考中..."):
            chat_history = []
            for msg in st.session_state.messages:
                chat_history.append({"role": "user", "content": msg["query"]})
                chat_history.append({"role": "assistant", "content": msg["answer"]})

            result = app_graph.invoke({
                "query": query,
                "doc_index_ids": [d["index_id"] for d in st.session_state.documents],
                "chat_history": chat_history,
            })

        intent = result["intent"]
        trace = result.get("trace")

        if trace:
            with st.expander("调用链路", expanded=False):
                st.code(trace.summary(), language=None)

        if intent == "sales_analysis":
            answer = st.write_stream(writer_agent_stream(query, result["context"], chat_history))
            csv_path = os.path.join(DATA_DIR, "sales.csv")
            df = pd.read_csv(csv_path)
            col1, col2 = st.columns([1, 1])
            with col1:
                st.caption("原始数据")
                st.dataframe(df, use_container_width=True)
            with col2:
                st.caption("销量统计")
                summary = df.groupby("product")["quantity"].sum().reset_index()
                fig = px.bar(summary, x="product", y="quantity", color="product",
                             labels={"product": "产品", "quantity": "销量"},
                             text_auto=True)
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        elif intent == "document_analysis":
            doc_names = [d["filename"] for d in st.session_state.documents]
            st.caption(f"文档分析: {', '.join(doc_names)}")
            answer = st.write_stream(writer_agent_stream(query, result["context"], chat_history))

        else:
            answer = st.write_stream(writer_agent_stream(query, result["context"], chat_history))

    if not answer:
        answer = result.get("answer", "")
    msg = {"query": query, "intent": intent, "answer": answer}
    if intent == "document_analysis":
        msg["doc_filenames"] = [d["filename"] for d in st.session_state.documents]
    st.session_state.messages.append(msg)
    save_chat_history(st.session_state.messages)
