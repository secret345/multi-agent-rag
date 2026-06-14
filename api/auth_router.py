import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from auth.user_auth import register_user, verify_user, reset_password, user_exists
from auth.sms_service import generate_code, send_sms, verify_code
from api.auth_deps import create_access_token

router = APIRouter()

PHONE_REGEX = re.compile(r"^1[3-9]\d{9}$")


class RegisterRequest(BaseModel):
    phone: str
    password: str


class LoginRequest(BaseModel):
    phone: str
    password: str


class SendCodeRequest(BaseModel):
    phone: str


class VerifyCodeRequest(BaseModel):
    phone: str
    code: str


class ResetPasswordRequest(BaseModel):
    phone: str
    code: str
    new_password: str


@router.post("/register")
def register(req: RegisterRequest):
    if not PHONE_REGEX.match(req.phone):
        raise HTTPException(status_code=400, detail="请输入正确的手机号")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")
    if user_exists(req.phone):
        raise HTTPException(status_code=400, detail="该手机号已注册")
    register_user(req.phone, req.password)
    return {"message": "注册成功"}


@router.post("/login")
def login(req: LoginRequest):
    if not PHONE_REGEX.match(req.phone):
        raise HTTPException(status_code=400, detail="请输入正确的手机号")
    if not verify_user(req.phone, req.password):
        raise HTTPException(status_code=401, detail="手机号或密码错误")
    token = create_access_token({"sub": req.phone})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/reset-password/send-code")
def send_reset_code(req: SendCodeRequest):
    if not PHONE_REGEX.match(req.phone):
        raise HTTPException(status_code=400, detail="请输入正确的手机号")
    if not user_exists(req.phone):
        raise HTTPException(status_code=400, detail="该手机号未注册")
    code = generate_code(req.phone)
    if code is None:
        raise HTTPException(status_code=429, detail="发送过于频繁，请稍后再试")
    send_sms(req.phone, code)
    return {"message": "验证码已发送"}


@router.post("/reset-password/verify")
def verify_reset_code(req: VerifyCodeRequest):
    if not verify_code(req.phone, req.code):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")
    return {"message": "验证成功"}


@router.post("/reset-password/confirm")
def confirm_reset_password(req: ResetPasswordRequest):
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")
    if not verify_code(req.phone, req.code):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")
    reset_password(req.phone, req.new_password)
    return {"message": "密码重置成功"}
