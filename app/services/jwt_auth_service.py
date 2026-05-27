"""
JWT 认证服务 - 数据库持久化版本
"""
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from dataclasses import asdict
import hashlib
import secrets
import jwt

from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType, SubscriptionPlan, SubscriptionStatus
from app.config import settings


class JWTAuthService:
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: [
            "case_read", "case_edit", "case_delete",
            "evidence_upload", "evidence_delete",
            "document_generate", "document_export",
            "deadline_manage", "team_manage", "settings",
        ],
        UserRole.LAWYER: [
            "case_read", "case_edit",
            "evidence_upload", "evidence_delete",
            "document_generate", "document_export",
            "deadline_manage",
        ],
        UserRole.ASSISTANT: [
            "case_read", "case_edit",
            "evidence_upload",
            "document_generate",
        ],
        UserRole.CLIENT: [
            "case_read",
            "evidence_upload",
        ],
        UserRole.VIEWER: [
            "case_read",
        ],
    }

    def __init__(self, secret_key: Optional[str] = None):
        resolved_secret = secret_key or settings.jwt_secret
        if not resolved_secret and settings.app_env.lower() == "production":
            raise RuntimeError("JWT_SECRET must be set when APP_ENV=production")

        self.secret_key = resolved_secret or secrets.token_urlsafe(32)
        self.algorithm = "HS256"
        self.token_expiry = timedelta(days=7)
        self.refresh_expiry = timedelta(days=30)

    # ========== Token 管理 ==========

    def _generate_tokens(self, user: User, tenant: Tenant) -> Dict:
        now = datetime.utcnow()

        access_payload = {
            "user_id": user.id,
            "tenant_id": tenant.id,
            "username": user.username,
            "role": user.role.value,
            "tenant_type": tenant.tenant_type.value,
            "type": "access",
            "exp": now + self.token_expiry,
            "iat": now,
        }
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)

        refresh_payload = {
            "user_id": user.id,
            "type": "refresh",
            "exp": now + self.refresh_expiry,
            "iat": now,
        }
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": int(self.token_expiry.total_seconds()),
        }

    def verify_token(self, token: str) -> Optional[Dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    def refresh_tokens(self, refresh_token: str) -> Optional[Dict]:
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != "refresh":
                return None
            return {"refresh_payload": payload}
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    # ========== 密码管理 ==========

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,
        )
        return salt + pwd_hash.hex()

    @staticmethod
    def _verify_password(password: str, stored_hash: str) -> bool:
        try:
            salt = stored_hash[:32]
            stored_pwd_hash = stored_hash[32:]
            pwd_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                100000,
            )
            return pwd_hash.hex() == stored_pwd_hash
        except Exception:
            return False

    # ========== 用户管理 ==========

    def register_user(
        self,
        db: Session,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        role: UserRole = UserRole.ASSISTANT,
        tenant_id: Optional[str] = None,
        tenant_name: Optional[str] = None,
        tenant_type: TenantType = TenantType.LAW_FIRM,
    ) -> Dict:
        duplicate_checks = [User.username == username, User.email == email]
        if phone:
            duplicate_checks.append(User.phone == phone)

        existing = db.query(User).filter(or_(*duplicate_checks)).first()
        if existing:
            return {"success": False, "error": "用户名、邮箱或手机号已被注册"}

        user_id = secrets.token_urlsafe(16)
        password_hash = self._hash_password(password)

        if not tenant_id:
            tenant_id = secrets.token_urlsafe(16)
            tenant_slug = self._generate_unique_slug(db, tenant_name or username)
            tenant = Tenant(
                id=tenant_id,
                name=tenant_name or username,
                tenant_type=tenant_type,
                slug=tenant_slug,
            )
            db.add(tenant)
            role = UserRole.ADMIN
        else:
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                return {"success": False, "error": "租户不存在"}

        user = User(
            id=user_id,
            tenant_id=tenant_id,
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            phone=phone,
            role=role,
        )
        db.add(user)
        db.commit()

        tokens = self._generate_tokens(user, tenant)
        return {
            "success": True,
            "user": user.to_dict(),
            "tenant": tenant.to_dict(),
            "tokens": tokens,
        }

    def authenticate(self, db: Session, username: str, password: str) -> Optional[Dict]:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = db.query(User).filter(User.email == username).first()
        if not user:
            user = db.query(User).filter(User.phone == username).first()
        if not user:
            return None

        if not self._verify_password(password, user.password_hash):
            return None

        if not user.is_active:
            return None

        tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
        if not tenant or not tenant.is_active:
            return None

        user.last_login_at = datetime.utcnow()
        db.commit()

        tokens = self._generate_tokens(user, tenant)
        return {
            "success": True,
            "user": user.to_dict(),
            "tenant": tenant.to_dict(),
            "tokens": tokens,
        }

    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def get_tenant_by_id(self, db: Session, tenant_id: str) -> Optional[Tenant]:
        return db.query(Tenant).filter(Tenant.id == tenant_id).first()

    def update_password(self, db: Session, user: User, new_password: str) -> None:
        user.password_hash = self._hash_password(new_password)
        user.updated_at = datetime.utcnow()
        db.commit()

    @staticmethod
    def _generate_slug(name: str) -> str:
        import re
        slug = re.sub(r"[^\w\s-]", "", name.lower())
        slug = re.sub(r"[-\s]+", "-", slug).strip("-")
        return slug or secrets.token_urlsafe(8)

    def _generate_unique_slug(self, db: Session, name: str) -> str:
        base_slug = self._generate_slug(name)[:90]
        slug = base_slug
        for suffix in range(2, 1000):
            if not db.query(Tenant.id).filter(Tenant.slug == slug).first():
                return slug
            slug = f"{base_slug}-{suffix}"

        return f"{base_slug}-{secrets.token_urlsafe(6).lower()}"

    def get_role_permissions(self, role: UserRole) -> List[str]:
        return self.ROLE_PERMISSIONS.get(role, [])


jwt_auth_service = JWTAuthService()
