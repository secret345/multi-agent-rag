import hashlib
import json
import os
from config import DATA_DIR

USERS_PATH = os.path.join(DATA_DIR, "users.json")


def _load_users() -> dict:
    if os.path.exists(USERS_PATH):
        with open(USERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_users(users: dict):
    os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(phone: str, password: str) -> bool:
    users = _load_users()
    if phone in users:
        return False
    users[phone] = {"password": _hash_password(password)}
    _save_users(users)
    return True


def verify_user(phone: str, password: str) -> bool:
    users = _load_users()
    if phone not in users:
        return False
    return users[phone]["password"] == _hash_password(password)


def reset_password(phone: str, new_password: str) -> bool:
    users = _load_users()
    if phone not in users:
        return False
    users[phone]["password"] = _hash_password(new_password)
    _save_users(users)
    return True


def user_exists(phone: str) -> bool:
    users = _load_users()
    return phone in users
