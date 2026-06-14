import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.auth_deps import get_current_user
from db import get_conn

router = APIRouter()


class UpdateSettingsRequest(BaseModel):
    api_key: str = ""


@router.get("")
def get_settings(phone: str = Depends(get_current_user)):
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT settings FROM user_settings WHERE phone=%s", (phone,))
                row = cur.fetchone()
                if not row or not row["settings"]:
                    return {"api_key": ""}
                s = row["settings"]
                settings = json.loads(s) if isinstance(s, str) else s
                return {"api_key": settings.get("api_key", "")}
        finally:
            conn.close()
    except Exception:
        return {"api_key": ""}


@router.put("")
def update_settings(req: UpdateSettingsRequest, phone: str = Depends(get_current_user)):
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO user_settings (phone, settings) VALUES (%s, %s) "
                    "ON DUPLICATE KEY UPDATE settings=VALUES(settings)",
                    (phone, json.dumps({"api_key": req.api_key}, ensure_ascii=False)),
                )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        raise HTTPException(status_code=500, detail="保存设置失败")
    return {"message": "ok"}
