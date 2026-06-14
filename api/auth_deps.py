import os
import json
import jwt
import datetime
from fastapi import Request, HTTPException, status
from db import get_conn

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 72


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 Token")


def get_current_user(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少认证信息")
    token = auth_header[7:]
    payload = decode_token(token)
    phone = payload.get("sub")
    if not phone:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 Token")
    return phone


def load_user_api_key(phone: str) -> str:
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT settings FROM user_settings WHERE phone=%s", (phone,))
                row = cur.fetchone()
                if not row or not row["settings"]:
                    return ""
                s = row["settings"]
                settings = json.loads(s) if isinstance(s, str) else s
                return settings.get("api_key", "")
        finally:
            conn.close()
    except Exception:
        return ""
