import os
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from api.auth_deps import get_current_user
from db import get_conn
from config import WRITABLE_DIR, VECTORSTORE_DIR
from rag.doc_indexer import build_doc_index

router = APIRouter()


def _sanitize_filename(name: str) -> str:
    name = os.path.basename(name)
    name = name.replace("..", "")
    if not name or name.startswith("."):
        name = "unnamed"
    return name


def _user_dir(phone: str) -> str:
    path = os.path.join(WRITABLE_DIR, "users", phone)
    os.makedirs(os.path.join(path, "uploads"), exist_ok=True)
    return path


@router.get("")
def list_documents(phone: str = Depends(get_current_user)):
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT index_id, filename FROM user_documents WHERE phone=%s",
                    (phone,),
                )
                return {"documents": cur.fetchall()}
        finally:
            conn.close()
    except Exception:
        return {"documents": []}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), phone: str = Depends(get_current_user)):
    safe_name = _sanitize_filename(file.filename)
    user_dir = _user_dir(phone)
    save_path = os.path.join(user_dir, "uploads", safe_name)

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    index_id = f"doc_{uuid.uuid4().hex[:8]}"
    build_doc_index(save_path, index_id)

    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO user_documents (phone, index_id, filename) VALUES (%s, %s, %s)",
                    (phone, index_id, safe_name),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        raise HTTPException(status_code=500, detail="保存文档记录失败")

    return {"index_id": index_id, "filename": safe_name}


@router.delete("/{index_id}")
def delete_document(index_id: str, phone: str = Depends(get_current_user)):
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT filename FROM user_documents WHERE phone=%s AND index_id=%s",
                    (phone, index_id),
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="文档不存在")
                filename = row["filename"]

                upload_path = os.path.join(_user_dir(phone), "uploads", filename)
                if os.path.exists(upload_path):
                    os.remove(upload_path)

                for ext in [".index", ".chunks"]:
                    p = os.path.join(VECTORSTORE_DIR, f"{index_id}{ext}")
                    if os.path.exists(p):
                        os.remove(p)

                cur.execute(
                    "DELETE FROM user_documents WHERE phone=%s AND index_id=%s",
                    (phone, index_id),
                )
            conn.commit()
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="删除失败")

    return {"message": "ok"}
