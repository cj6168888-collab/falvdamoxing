"""
短信验证码服务
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.sms_verification import SMSVerificationCode
from app.models.user import User

logger = logging.getLogger(__name__)


REGISTER_PURPOSE = "register"
PASSWORD_RESET_PURPOSE = "password_reset"
SUPPORTED_PURPOSES = {REGISTER_PURPOSE, PASSWORD_RESET_PURPOSE}


class SMSAuthService:
    """手机号验证码签发、发送和校验。"""

    _PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")

    def normalize_phone(self, raw_phone: str) -> str:
        phone = re.sub(r"[\s\-()]", "", raw_phone or "")
        if phone.startswith("+86"):
            phone = phone[3:]
        elif phone.startswith("86") and len(phone) == 13:
            phone = phone[2:]

        if not self._PHONE_PATTERN.fullmatch(phone):
            raise ValueError("请输入有效的中国大陆手机号")
        return phone

    def request_code(
        self,
        db: Session,
        raw_phone: str,
        purpose: str,
        remote_ip: Optional[str] = None,
    ) -> Dict:
        if purpose not in SUPPORTED_PURPOSES:
            return {"success": False, "error": "不支持的短信验证码用途"}

        try:
            phone = self.normalize_phone(raw_phone)
        except ValueError as exc:
            return {"success": False, "error": str(exc)}

        user = db.query(User).filter(User.phone == phone).first()
        if purpose == REGISTER_PURPOSE and user:
            return {"success": False, "error": "手机号已被注册"}

        ttl_seconds = max(60, int(settings.sms_code_ttl_minutes) * 60)

        if purpose == PASSWORD_RESET_PURPOSE and not user:
            return {
                "success": True,
                "message": "如果手机号已注册，验证码将发送到该手机号",
                "expires_in": ttl_seconds,
            }

        now = datetime.utcnow()
        recent = (
            db.query(SMSVerificationCode)
            .filter(
                SMSVerificationCode.phone == phone,
                SMSVerificationCode.purpose == purpose,
            )
            .order_by(SMSVerificationCode.sent_at.desc())
            .first()
        )
        cooldown = max(0, int(settings.sms_code_resend_seconds))
        if recent and recent.sent_at and (now - recent.sent_at).total_seconds() < cooldown:
            retry_after = cooldown - int((now - recent.sent_at).total_seconds())
            return {
                "success": False,
                "error": f"验证码发送过于频繁，请 {retry_after} 秒后再试",
                "retry_after": retry_after,
            }

        code = self._generate_code()
        record = SMSVerificationCode(
            phone=phone,
            purpose=purpose,
            code_hash=self._hash_code(phone, purpose, code),
            remote_ip=remote_ip,
            sent_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
        db.add(record)

        try:
            self._send_sms(phone, code, purpose)
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.exception("Failed to send SMS verification code")
            return {"success": False, "error": f"短信发送失败: {exc}"}

        response = {
            "success": True,
            "message": (
                "如果手机号已注册，验证码将发送到该手机号"
                if purpose == PASSWORD_RESET_PURPOSE
                else "验证码已发送"
            ),
            "expires_in": ttl_seconds,
        }
        if self._should_return_debug_code():
            response["debug_code"] = code
        return response

    def verify_code(
        self,
        db: Session,
        raw_phone: str,
        purpose: str,
        code: str,
        consume: bool = True,
    ) -> bool:
        try:
            phone = self.normalize_phone(raw_phone)
        except ValueError:
            return False

        now = datetime.utcnow()
        record = (
            db.query(SMSVerificationCode)
            .filter(
                SMSVerificationCode.phone == phone,
                SMSVerificationCode.purpose == purpose,
                SMSVerificationCode.consumed_at.is_(None),
                SMSVerificationCode.expires_at > now,
            )
            .order_by(SMSVerificationCode.created_at.desc())
            .first()
        )
        if not record:
            return False

        max_attempts = max(1, int(settings.sms_code_max_attempts))
        if record.attempts >= max_attempts:
            return False

        submitted_hash = self._hash_code(phone, purpose, (code or "").strip())
        matched = hmac.compare_digest(submitted_hash, record.code_hash)
        record.attempts += 1
        if matched and consume:
            record.consumed_at = now
        db.commit()
        return matched

    def _generate_code(self) -> str:
        length = max(4, min(8, int(settings.sms_code_length)))
        upper = 10 ** length
        return f"{secrets.randbelow(upper):0{length}d}"

    def _hash_code(self, phone: str, purpose: str, code: str) -> str:
        secret = settings.jwt_secret or "development-sms-secret"
        message = f"{phone}:{purpose}:{code}".encode("utf-8")
        return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

    def _send_sms(self, phone: str, code: str, purpose: str) -> None:
        message = self._build_message(code, purpose)
        provider = (settings.sms_provider or "console").lower()

        if provider == "console":
            logger.info("SMS code for %s [%s]: %s", phone, purpose, code)
            return

        if provider == "http":
            if not settings.sms_http_endpoint:
                raise RuntimeError("SMS_HTTP_ENDPOINT 未配置")
            headers = {}
            if settings.sms_http_token:
                headers["Authorization"] = f"Bearer {settings.sms_http_token}"
            payload = {
                "phone": phone,
                "code": code,
                "purpose": purpose,
                "message": message,
            }
            response = httpx.post(
                settings.sms_http_endpoint,
                json=payload,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            return

        raise RuntimeError(f"不支持的短信供应商: {settings.sms_provider}")

    @staticmethod
    def _build_message(code: str, purpose: str) -> str:
        action = "注册账号" if purpose == REGISTER_PURPOSE else "找回密码"
        return f"您的法律大模型辅助系统验证码为 {code}，用于{action}，5分钟内有效。"

    @staticmethod
    def _should_return_debug_code() -> bool:
        if settings.sms_debug_return_code is not None:
            return bool(settings.sms_debug_return_code)
        return settings.app_env.lower() != "production"


sms_auth_service = SMSAuthService()
