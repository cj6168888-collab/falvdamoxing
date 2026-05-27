import pytest
from httpx import ASGITransport, AsyncClient

from app.core.tenant_context import TenantContext
from app.app_factory import create_app
from app.db.database import SessionLocal, init_db
from app.models.tenant import Tenant, TenantType
from app.models.user import User, UserRole
from app.services.jwt_auth_service import jwt_auth_service


TEST_TENANT_ID = "pytest-tenant"
TEST_USER_ID = "pytest-user"
TEST_USERNAME = "pytest-admin"
TEST_PASSWORD = "pytest-password"


def _ensure_test_identity() -> dict[str, str]:
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.id == TEST_TENANT_ID).first()
        if not tenant:
            tenant = Tenant(
                id=TEST_TENANT_ID,
                name="Pytest Tenant",
                tenant_type=TenantType.LAW_FIRM,
                slug="pytest-tenant",
                is_active=True,
            )
            db.add(tenant)

        user = db.query(User).filter(User.id == TEST_USER_ID).first()
        if not user:
            user = User(
                id=TEST_USER_ID,
                tenant_id=TEST_TENANT_ID,
                username=TEST_USERNAME,
                email="pytest-admin@example.com",
                password_hash=jwt_auth_service._hash_password(TEST_PASSWORD),
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(user)

        db.commit()
        db.refresh(tenant)
        db.refresh(user)
        tokens = jwt_auth_service._generate_tokens(user, tenant)
        return {"Authorization": f"Bearer {tokens['access_token']}"}
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def initialize_database():
    init_db()


@pytest.fixture(scope="session")
def auth_headers(initialize_database):
    return _ensure_test_identity()


@pytest.fixture(autouse=True)
def tenant_context_for_tests(auth_headers):
    TenantContext.set_tenant(TEST_TENANT_ID)
    TenantContext.set_user(TEST_USER_ID)
    try:
        yield
    finally:
        TenantContext.clear()


@pytest.fixture
def lightweight_app():
    return create_app(include_static_files=False, include_task_handlers=False)


@pytest.fixture
async def client(lightweight_app, auth_headers):
    transport = ASGITransport(app=lightweight_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://localhost:3000",
        headers=auth_headers,
    ) as ac:
        yield ac
