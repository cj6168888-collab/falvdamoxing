"""Create or update a deterministic API user for staging load tests."""

from __future__ import annotations

import argparse
from pathlib import Path
import secrets
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import app.models  # noqa: F401 - register SQLAlchemy models
from app.db.database import SessionLocal
from app.models.tenant import Tenant, TenantType
from app.models.user import User, UserRole
from app.services.jwt_auth_service import jwt_auth_service


def seed_user(
    *,
    username: str,
    password: str,
    email: str,
    phone: str,
    tenant_slug: str,
    tenant_name: str,
) -> None:
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
        if not tenant:
            tenant = Tenant(
                id=secrets.token_urlsafe(16),
                name=tenant_name,
                tenant_type=TenantType.LAW_FIRM,
                slug=tenant_slug,
                is_active=True,
                is_verified=True,
            )
            db.add(tenant)
            db.flush()

        user = db.query(User).filter(User.username == username).first()
        password_hash = jwt_auth_service._hash_password(password)
        if not user:
            user = User(
                id=secrets.token_urlsafe(16),
                tenant_id=tenant.id,
                username=username,
                email=email,
                phone=phone,
                password_hash=password_hash,
                role=UserRole.ADMIN,
                is_active=True,
                is_email_verified=True,
            )
            db.add(user)
        else:
            user.tenant_id = tenant.id
            user.email = email
            user.phone = phone
            user.password_hash = password_hash
            user.role = UserRole.ADMIN
            user.is_active = True
            user.is_email_verified = True

        db.commit()
        print(f"Seeded load-test user: {username}")
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed a staging load-test user.")
    parser.add_argument("--username", default="loadtest-admin")
    parser.add_argument("--password", default="loadtest-password-123456")
    parser.add_argument("--email", default="loadtest-admin@example.test")
    parser.add_argument("--phone", default="13900000001")
    parser.add_argument("--tenant-slug", default="loadtest-tenant")
    parser.add_argument("--tenant-name", default="Load Test Tenant")
    args = parser.parse_args()

    seed_user(
        username=args.username,
        password=args.password,
        email=args.email,
        phone=args.phone,
        tenant_slug=args.tenant_slug,
        tenant_name=args.tenant_name,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
