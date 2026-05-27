import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import auth as auth_api
from app.config import settings
from app.models.sms_verification import SMSVerificationCode
from app.models.tenant import Tenant
from app.models.user import User
from app.services.sms_auth_service import REGISTER_PURPOSE, sms_auth_service


@pytest.fixture
def auth_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Tenant.__table__.create(bind=engine)
    User.__table__.create(bind=engine)
    SMSVerificationCode.__table__.create(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    monkeypatch.setattr(settings, "sms_provider", "console")
    monkeypatch.setattr(settings, "sms_debug_return_code", True)
    monkeypatch.setattr(settings, "sms_code_resend_seconds", 0)

    try:
        yield db
    finally:
        db.close()


def test_sms_code_is_hashed_consumable_and_single_use(auth_db):
    result = sms_auth_service.request_code(auth_db, "13800138000", REGISTER_PURPOSE)

    assert result["success"] is True
    assert result["debug_code"]

    record = auth_db.query(SMSVerificationCode).one()
    assert record.code_hash != result["debug_code"]

    assert sms_auth_service.verify_code(auth_db, "13800138000", REGISTER_PURPOSE, result["debug_code"]) is True
    assert sms_auth_service.verify_code(auth_db, "13800138000", REGISTER_PURPOSE, result["debug_code"]) is False


@pytest.mark.asyncio
async def test_phone_registration_login_and_password_reset(lightweight_app, auth_db):
    def override_get_db():
        try:
            yield auth_db
        finally:
            pass

    lightweight_app.dependency_overrides[auth_api.get_db] = override_get_db

    transport = ASGITransport(app=lightweight_app)
    async with AsyncClient(transport=transport, base_url="http://localhost:3000") as client:
        send_register = await client.post(
            "/api/auth/sms/send",
            json={"phone": "13800138001", "purpose": "register"},
        )
        assert send_register.status_code == 200
        register_code = send_register.json()["debug_code"]

        register = await client.post(
            "/api/auth/register/phone",
            json={
                "phone": "13800138001",
                "sms_code": register_code,
                "password": "old-secret",
                "tenant_name": "测试律所",
                "tenant_type": "law_firm",
            },
        )
        assert register.status_code == 200
        assert register.json()["user"]["phone"] == "13800138001"

        old_login = await client.post(
            "/api/auth/login",
            json={"username": "13800138001", "password": "old-secret"},
        )
        assert old_login.status_code == 200

        send_reset = await client.post(
            "/api/auth/sms/send",
            json={"phone": "13800138001", "purpose": "password_reset"},
        )
        assert send_reset.status_code == 200
        reset_code = send_reset.json()["debug_code"]

        reset = await client.post(
            "/api/auth/password-reset/confirm",
            json={
                "phone": "13800138001",
                "sms_code": reset_code,
                "new_password": "new-secret",
            },
        )
        assert reset.status_code == 200

        failed_old_login = await client.post(
            "/api/auth/login",
            json={"username": "13800138001", "password": "old-secret"},
        )
        assert failed_old_login.status_code == 401

        new_login = await client.post(
            "/api/auth/login",
            json={"username": "13800138001", "password": "new-secret"},
        )
        assert new_login.status_code == 200

        send_second_register = await client.post(
            "/api/auth/sms/send",
            json={"phone": "13800138002", "purpose": "register"},
        )
        assert send_second_register.status_code == 200
        second_register_code = send_second_register.json()["debug_code"]

        second_register = await client.post(
            "/api/auth/register/phone",
            json={
                "phone": "13800138002",
                "sms_code": second_register_code,
                "password": "second-secret",
                "tenant_name": "测试律所",
                "tenant_type": "law_firm",
            },
        )
        assert second_register.status_code == 200

        slugs = [tenant.slug for tenant in auth_db.query(Tenant).all()]
        assert len(slugs) == len(set(slugs))

    lightweight_app.dependency_overrides.clear()
