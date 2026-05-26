import random
import time
from datetime import datetime

_code_store: dict[str, dict] = {}


def generate_code(phone: str) -> str:
    code = "".join([str(random.randint(0, 9)) for _ in range(6)])
    _code_store[phone] = {
        "code": code,
        "expires_at": time.time() + 300,
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
    if record["code"] != code:
        return False
    _code_store.pop(phone, None)
    return True
