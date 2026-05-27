import bcrypt
from db import get_conn


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _is_bcrypt_hash(hashed: str) -> bool:
    return hashed.startswith("$2")


def register_user(phone: str, password: str) -> bool:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT phone FROM users WHERE phone=%s", (phone,))
            if cur.fetchone():
                return False
            cur.execute(
                "INSERT INTO users (phone, password_hash) VALUES (%s, %s)",
                (phone, _hash_password(password)),
            )
        conn.commit()
        return True
    finally:
        conn.close()


def verify_user(phone: str, password: str) -> bool:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE phone=%s", (phone,))
            row = cur.fetchone()
            if not row:
                return False

            stored = row["password_hash"]

            if _is_bcrypt_hash(stored):
                return bcrypt.checkpw(password.encode(), stored.encode())

            # Legacy SHA-256 migration
            import hashlib
            old_hash = hashlib.sha256(password.encode()).hexdigest()
            if old_hash == stored:
                new_hash = _hash_password(password)
                cur.execute(
                    "UPDATE users SET password_hash=%s WHERE phone=%s",
                    (new_hash, phone),
                )
                conn.commit()
                return True
            return False
    finally:
        conn.close()


def reset_password(phone: str, new_password: str) -> bool:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT phone FROM users WHERE phone=%s", (phone,))
            if not cur.fetchone():
                return False
            cur.execute(
                "UPDATE users SET password_hash=%s WHERE phone=%s",
                (_hash_password(new_password), phone),
            )
        conn.commit()
        return True
    finally:
        conn.close()


def user_exists(phone: str) -> bool:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE phone=%s", (phone,))
            return cur.fetchone() is not None
    finally:
        conn.close()
