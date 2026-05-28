"""
法律知识库数据库迁移脚本
创建法条、司法解释、判例、诉讼规则、文书模板等表
"""
import sqlite3
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.config import settings


def migrate_legal_knowledge_db():
    db_url = settings.database_url

    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        if db_path.startswith("./"):
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path[2:])
    else:
        db_path = db_url

    if not os.path.exists(db_path):
        db_path = "legal_system.db"

    print(f"法律知识库数据库路径: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # ============ 法条表 ============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS legal_articles (
            id TEXT PRIMARY KEY,
            law_name TEXT NOT NULL,
            article_number TEXT NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            chapter TEXT,
            category TEXT,
            effective_date TEXT,
            is_valid INTEGER DEFAULT 1,
            supersedes TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_law_name ON legal_articles(law_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_law_category ON legal_articles(category)")
    print("[OK] legal_articles 表创建成功")

    # ============ 司法解释表 ============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS judicial_interpretations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            doc_number TEXT,
            content TEXT NOT NULL,
            related_law_id TEXT,
            effective_date TEXT,
            is_valid INTEGER DEFAULT 1,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_interp_title ON judicial_interpretations(title)")
    print("[OK] judicial_interpretations 表创建成功")

    # ============ 指导性案例表 ============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guiding_cases (
            id TEXT PRIMARY KEY,
            case_number TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            court TEXT,
            case_type TEXT,
            summary TEXT,
            full_text TEXT,
            keywords TEXT,
            related_articles TEXT,
            publish_date TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_case_type ON guiding_cases(case_type)")
    print("[OK] guiding_cases 表创建成功")

    # ============ 诉讼费用规则表 ============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS litigation_costs (
            id TEXT PRIMARY KEY,
            cost_type TEXT NOT NULL,
            calculation_rule TEXT NOT NULL,
            base_law_id TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] litigation_costs 表创建成功")

    # ============ 管辖权规则表 ============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jurisdiction_rules (
            id TEXT PRIMARY KEY,
            rule_type TEXT NOT NULL,
            description TEXT,
            condition TEXT,
            base_law_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] jurisdiction_rules 表创建成功")

    # ============ 文书模板表 ============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_templates (
            id TEXT PRIMARY KEY,
            template_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            required_fields TEXT,
            applicable_cases TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_template_type ON document_templates(template_type)")
    print("[OK] document_templates 表创建成功")

    # ============ 合同模板表 ============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contract_templates (
            id TEXT PRIMARY KEY,
            contract_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            essential_clauses TEXT,
            risk_clauses TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contract_type ON contract_templates(contract_type)")
    print("[OK] contract_templates 表创建成功")

    conn.commit()
    conn.close()
    print("\n[SUCCESS] 法律知识库数据库表创建完成！")


if __name__ == "__main__":
    migrate_legal_knowledge_db()
