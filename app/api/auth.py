"""
认证 API 路由
"""
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

from app.db.database import get_db
from app.services.jwt_auth_service import jwt_auth_service
from app.services.sms_auth_service import (
    PASSWORD_RESET_PURPOSE,
    REGISTER_PURPOSE,
    sms_auth_service,
)
from app.core.auth import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import TenantType

router = APIRouter(prefix="/api/auth", tags=["认证"])


# ========== 请求/响应模型 ==========

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    phone: Optional[str] = None
    sms_code: Optional[str] = Field(default=None, min_length=4, max_length=8)
    full_name: Optional[str] = None
    tenant_name: Optional[str] = None
    tenant_type: str = Field(default="law_firm", description="law_firm 或 enterprise")
    role: str = Field(default="assistant", description="admin/lawyer/assistant/client/viewer")


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    phone: Optional[str] = None
    full_name: Optional[str]
    role: str
    tenant_id: str
    is_active: bool


class AuthResponse(BaseModel):
    success: bool
    user: UserResponse
    tenant: dict
    tokens: TokenResponse


class RefreshResponse(BaseModel):
    success: bool
    tokens: TokenResponse


class CurrentUserResponse(BaseModel):
    user: dict


class RegisterResponse(BaseModel):
    success: bool
    user: Optional[UserResponse] = None
    tenant: Optional[dict] = None
    tokens: Optional[TokenResponse] = None
    error: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class SMSCodeRequest(BaseModel):
    phone: str = Field(..., min_length=8, max_length=32)
    purpose: str = Field(..., description="register 或 password_reset")


class SMSCodeResponse(BaseModel):
    success: bool
    message: str
    expires_in: int
    debug_code: Optional[str] = None


class PhoneRegisterRequest(BaseModel):
    phone: str = Field(..., min_length=8, max_length=32)
    sms_code: str = Field(..., min_length=4, max_length=8)
    password: str = Field(..., min_length=6, max_length=128)
    username: Optional[str] = Field(default=None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    tenant_name: Optional[str] = None
    tenant_type: str = Field(default="law_firm", description="law_firm 或 enterprise")
    role: str = Field(default="assistant", description="admin/lawyer/assistant/client/viewer")


class PasswordResetConfirmRequest(BaseModel):
    phone: str = Field(..., min_length=8, max_length=32)
    sms_code: str = Field(..., min_length=4, max_length=8)
    new_password: str = Field(..., min_length=6, max_length=128)


class SimpleSuccessResponse(BaseModel):
    success: bool
    message: str


def _generate_phone_username(db: Session) -> str:
    for _ in range(10):
        username = f"u_{secrets.token_hex(5)}"
        if not db.query(User).filter(User.username == username).first():
            return username
    return f"u_{secrets.token_urlsafe(8).replace('-', '_')[:16]}"


def _placeholder_email_for_phone(phone: str) -> str:
    return f"phone-{phone}@phone.local.invalid"


# ========== 路由 ==========

@router.post("/sms/send", response_model=SMSCodeResponse)
async def send_sms_code(req: SMSCodeRequest, request: Request, db: Session = Depends(get_db)):
    result = sms_auth_service.request_code(
        db=db,
        raw_phone=req.phone,
        purpose=req.purpose,
        remote_ip=request.client.host if request.client else None,
    )
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])

    return result


@router.post("/register", response_model=RegisterResponse)
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    role = UserRole(req.role) if req.role in [r.value for r in UserRole] else UserRole.ASSISTANT
    tenant_type = TenantType(req.tenant_type) if req.tenant_type in [t.value for t in TenantType] else TenantType.LAW_FIRM

    normalized_phone = None
    if req.phone:
        try:
            normalized_phone = sms_auth_service.normalize_phone(req.phone)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        if not req.sms_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先获取并填写短信验证码")
        if not sms_auth_service.verify_code(db, normalized_phone, REGISTER_PURPOSE, req.sms_code):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码无效或已过期")

    result = jwt_auth_service.register_user(
        db=db,
        username=req.username,
        email=req.email,
        password=req.password,
        full_name=req.full_name,
        phone=normalized_phone,
        role=role,
        tenant_name=req.tenant_name,
        tenant_type=tenant_type,
    )

    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])

    tokens = TokenResponse(**result["tokens"])
    user = UserResponse(**result["user"])

    return RegisterResponse(
        success=True,
        user=user,
        tenant=result["tenant"],
        tokens=tokens,
    )


@router.post("/register/phone", response_model=RegisterResponse)
async def register_with_phone(req: PhoneRegisterRequest, db: Session = Depends(get_db)):
    try:
        phone = sms_auth_service.normalize_phone(req.phone)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not sms_auth_service.verify_code(db, phone, REGISTER_PURPOSE, req.sms_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码无效或已过期")

    role = UserRole(req.role) if req.role in [r.value for r in UserRole] else UserRole.ASSISTANT
    tenant_type = TenantType(req.tenant_type) if req.tenant_type in [t.value for t in TenantType] else TenantType.LAW_FIRM
    username = (req.username or "").strip() or _generate_phone_username(db)
    email = str(req.email) if req.email else _placeholder_email_for_phone(phone)

    result = jwt_auth_service.register_user(
        db=db,
        username=username,
        email=email,
        password=req.password,
        full_name=req.full_name,
        phone=phone,
        role=role,
        tenant_name=req.tenant_name,
        tenant_type=tenant_type,
    )

    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])

    return RegisterResponse(
        success=True,
        user=UserResponse(**result["user"]),
        tenant=result["tenant"],
        tokens=TokenResponse(**result["tokens"]),
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    result = jwt_auth_service.authenticate(db, req.username, req.password)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not result.get("success", True):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=result.get("error", "账户不可用"),
        )

    return {
        "success": True,
        "user": result["user"],
        "tenant": result["tenant"],
        "tokens": result["tokens"],
    }


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    result = jwt_auth_service.refresh_tokens(req.refresh_token)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效或已过期的刷新令牌")

    user_id = result["refresh_payload"]["user_id"]
    user = jwt_auth_service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不可用")

    tenant = jwt_auth_service.get_tenant_by_id(db, user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="租户不存在")

    tokens = jwt_auth_service._generate_tokens(user, tenant)
    return {"success": True, "tokens": tokens}


@router.post("/password-reset/confirm", response_model=SimpleSuccessResponse)
async def confirm_password_reset(req: PasswordResetConfirmRequest, db: Session = Depends(get_db)):
    try:
        phone = sms_auth_service.normalize_phone(req.phone)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码无效或已过期")

    if not sms_auth_service.verify_code(db, phone, PASSWORD_RESET_PURPOSE, req.sms_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码无效或已过期")

    jwt_auth_service.update_password(db, user, req.new_password)
    return {"success": True, "message": "密码已重置，请使用新密码登录"}


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "user": current_user.to_dict(),
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    return {"success": True, "message": "已登出"}
