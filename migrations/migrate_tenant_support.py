"""
数据迁移脚本 - 为现有数据添加多租户支持

使用方法:
    python -m migrations.migrate_tenant_support

此脚本将:
1. 创建 default 租户
2. 为所有现有数据添加 tenant_id = "default"
3. 创建 admin 用户
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import secrets


def run_migration():
    from app.db.database import SessionLocal, engine, Base
    from app.models import __all__ as all_models

    db = SessionLocal()

    try:
        print("=" * 60)
        print("  多租户支持数据迁移")
        print("=" * 60)
        print()

        # 1. 检查是否已有租户
        from app.models.tenant import Tenant
        existing = db.query(Tenant).first()
        if existing:
            print(f"[跳过] 租户已存在: {existing.name} (id={existing.id})")
            default_tenant = existing
        else:
            # 创建 default 租户
            default_tenant_id = "default"
            default_tenant = Tenant(
                id=default_tenant_id,
                name="默认租户",
                tenant_type="law_firm",
                slug="default",
                plan="free",
                description="系统默认租户，现有数据迁移至此",
            )
            db.add(default_tenant)
            db.commit()
            print(f"[创建] 默认租户: id={default_tenant_id}")

        # 2. 检查是否已有用户
        from app.models.user import User
        existing_user = db.query(User).first()
        if existing_user:
            print(f"[跳过] 用户已存在: {existing_user.username}")
        else:
            import hashlib, secrets as sec
            password_hash = hashlib.pbkdf2_hmac(
                "sha256",
                b"admin123",  # 默认密码，请立即修改！
                sec.token_hex(16).encode(),
                100000,
            ).hex()
            password_hash = sec.token_hex(16) + password_hash

            admin_user = User(
                id="default-admin",
                tenant_id=default_tenant.id,
                username="admin",
                email="admin@local",
                password_hash=password_hash,
                full_name="系统管理员",
                role="admin",
            )
            db.add(admin_user)
            db.commit()
            print(f"[创建] 管理员用户: admin / admin123 (请立即修改密码!)")

        # 3. 为 Case 添加 tenant_id 列
        from sqlalchemy import inspect, text
        inspector = inspect(engine)

        models_need_tenant = [
            ("cases", "case"),
            ("parties", "case"),
            ("documents", "document"),
            ("reminders", "reminder"),
            ("chat_messages", "case"),
            ("letters", "letter"),
            ("legal_deadlines", "letter"),
            ("case_timelines", "letter"),
            ("hearing_records", "hearing"),
            ("appeal_records", "appeal"),
            ("execution_tracking", "case"),
            ("projects", "project"),
            ("project_documents", "project"),
            ("project_milestones", "project"),
            ("project_communications", "project"),
            ("project_evidence", "project"),
            ("project_legal_advices", "project"),
            ("project_events", "project"),
            ("project_contracts", "project"),
            ("project_risks", "project"),
        ]

        tables_to_update = [
            "cases", "parties", "documents", "reminders", "chat_messages",
            "letters", "legal_deadlines", "case_timelines",
            "hearing_records", "appeal_records", "execution_tracking",
            "projects", "generated_documents", "document_suggestions",
            "evidence_items_v2", "evidence_relationships",
            "reminders", "meeting_records", "case_finances",
            "expense_records",
        ]

        with engine.connect() as conn:
            for table in tables_to_update:
                columns = [c["name"] for c in inspector.get_columns(table)]
                if "tenant_id" not in columns:
                    try:
                        conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN tenant_id VARCHAR(36)'))
                        conn.execute(text(f'UPDATE "{table}" SET tenant_id = "default"'))
                        conn.commit()
                        print(f"[迁移] {table}: 添加 tenant_id 列并设为 'default'")
                    except Exception as e:
                        print(f"[跳过] {table}: {e}")
                else:
                    # 确保已有数据的 tenant_id 不为空
                    try:
                        conn.execute(text(f'UPDATE "{table}" SET tenant_id = "default" WHERE tenant_id IS NULL'))
                        conn.commit()
                    except:
                        pass

        # 4. 验证迁移结果
        print()
        print("=" * 60)
        print("  迁移验证")
        print("=" * 60)

        tables_with_tenant = []
        tables_missing_tenant = []
        for table in tables_to_update:
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(f'SELECT COUNT(*) as total, SUM(CASE WHEN tenant_id IS NULL THEN 1 ELSE 0 END) as missing FROM "{table}"'))
                    row = result.fetchone()
                    if row:
                        total, missing = row[0], row[1] or 0
                        if total > 0:
                            tables_with_tenant.append((table, total, missing))
                        else:
                            tables_missing_tenant.append(table)
            except:
                pass

        print()
        print("已迁移的表:")
        for table, total, missing in tables_with_tenant:
            status = "OK" if missing == 0 else f"WARNING: {missing} 条数据缺少 tenant_id"
            print(f"  {table}: {total} 条记录, {status}")

        if tables_missing_tenant:
            print()
            print("空表（未迁移）:")
            for table in tables_missing_tenant:
                print(f"  {table}")

        print()
        print("=" * 60)
        print("  迁移完成!")
        print("=" * 60)
        print()
        print("后续步骤:")
        print("  1. 使用 /api/auth/login 验证认证功能")
        print("  2. 在前端添加登录页面（当前使用假 token）")
        print("  3. 现有数据已迁移到 default 租户")
        print("  4. 新租户可通过 /api/auth/register 注册")
        print()

    except Exception as e:
        print(f"[错误] 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
