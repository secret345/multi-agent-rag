import json
import os
import bcrypt
from config import WRITABLE_DIR

USERS_PATH = os.path.join(WRITABLE_DIR, "users.json")


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
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _is_bcrypt_hash(hashed: str) -> bool:
    return hashed.startswith("$2")


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

    stored = users[phone]["password"]

    if _is_bcrypt_hash(stored):
        return bcrypt.checkpw(password.encode(), stored.encode())

    # Legacy SHA-256 migration: verify old hash, then upgrade to bcrypt
    import hashlib
    old_hash = hashlib.sha256(password.encode()).hexdigest()
    if old_hash == stored:
        users[phone]["password"] = _hash_password(password)
        _save_users(users)
        return True
    return False


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
