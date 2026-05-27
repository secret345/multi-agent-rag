import secrets
import time
from datetime import datetime

_code_store: dict[str, dict] = {}
_rate_limit: dict[str, list[float]] = {}

_MAX_SEND_PER_MINUTE = 3
_MAX_VERIFY_ATTEMPTS = 5
_CODE_EXPIRY_SECONDS = 300


def _check_rate_limit(phone: str, key: str, max_count: int, window: float) -> bool:
    """Return True if within rate limit, False if exceeded."""
    now = time.time()
    if key not in _rate_limit:
        _rate_limit[key] = []
    # Remove expired entries
    _rate_limit[key] = [t for t in _rate_limit[key] if now - t < window]
    if len(_rate_limit[key]) >= max_count:
        return False
    _rate_limit[key].append(now)
    return True


def generate_code(phone: str) -> str | None:
    """Generate a verification code. Returns None if rate limited."""
    if not _check_rate_limit(phone, f"send:{phone}", _MAX_SEND_PER_MINUTE, 60):
        return None
    code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    _code_store[phone] = {
        "code": code,
        "expires_at": time.time() + _CODE_EXPIRY_SECONDS,
        "attempts": 0,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return code


def send_sms(phone: str, code: str) -> bool:
    # 模拟发送短信，实际替换为阿里云 SMS / Twilio 调用
    print(f"[SMS] 向 {phone} 发送验证码：{code}")
    return True


def verify_code(phone: str, code: str) -> bool:
    record = _code_store.get(phone)
    if not record:
        return False
    if time.time() > record["expires_at"]:
        _code_store.pop(phone, None)
        return False
    record["attempts"] += 1
    if record["attempts"] > _MAX_VERIFY_ATTEMPTS:
        _code_store.pop(phone, None)
        return False
    if not secrets.compare_digest(record["code"], code):
        return False
    _code_store.pop(phone, None)
    return True
