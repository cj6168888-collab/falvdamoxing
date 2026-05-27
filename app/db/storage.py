"""
数据存储模块 — 已弃用 (DEPRECATED)

此模块为旧版存储层，使用原始 sqlite3 连接独立的 law_assistant.db。
新代码请使用 SQLAlchemy ORM 模型（app/models/）和 app/db/database.py。

合同 API → 已迁移至 app/models/contract.py + ORM
借款 API → 已迁移至 app/models/loan.py + ORM
项目相关 → 使用 app/models/project.py 中的 ProjectContract 等模型

此文件仅保留以支持可能的旧数据读取，不再用于新功能。
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

DB_DIR = Path("d:/www/法律大模型/data")
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "law_assistant.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # 设置 UTF-8 编码以支持中文
    conn.execute("PRAGMA encoding = 'UTF-8'")
    return conn


def init_database():
    """初始化数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 项目表（核心）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            category_name TEXT,
            amount REAL DEFAULT 0,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'active',
            description TEXT,
            key_terms TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 借款记录表（关联项目）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            direction TEXT NOT NULL,
            borrower_name TEXT NOT NULL,
            borrower_phone TEXT,
            borrower_id TEXT,
            lender_name TEXT,
            amount REAL NOT NULL,
            start_date TEXT NOT NULL,
            due_date TEXT,
            has_interest INTEGER DEFAULT 0,
            interest_rate REAL DEFAULT 0,
            interest_type TEXT,
            guarantee TEXT,
            purpose TEXT,
            repayment_method TEXT,
            notes TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
        )
    """)

    # 合同表（关联项目）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT NOT NULL,
            contract_type TEXT,
            counterparty TEXT,
            amount REAL DEFAULT 0,
            sign_date TEXT,
            expiry_date TEXT,
            status TEXT DEFAULT 'pending',
            content TEXT,
            file_path TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
        )
    """)

    # 会议记录表（关联项目）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            project_id INTEGER,
            meeting_type TEXT,
            topic TEXT,
            meeting_date TEXT,
            participants TEXT,
            content TEXT,
            minutes TEXT,
            contract_draft TEXT,
            resolution TEXT,
            audio_files TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
        )
    """)

    # 当事人信息表（存储我方和对方信息）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            party_role TEXT NOT NULL,
            party_type TEXT,
            legal_role TEXT,
            name TEXT NOT NULL,
            phone TEXT,
            id_card TEXT,
            address TEXT,
            notes TEXT,
            role_effective_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    # 证据表（关联项目和案件）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            case_id INTEGER,
            evidence_type TEXT,
            title TEXT NOT NULL,
            description TEXT,
            file_path TEXT,
            file_name TEXT,
            file_size INTEGER,
            importance TEXT DEFAULT 'normal',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
            FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE SET NULL
        )
    """)

    # 案件表（关联项目）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT NOT NULL,
            case_type TEXT,
            case_no TEXT,
            court TEXT,
            plaintiff TEXT,
            defendant TEXT,
            claim_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            filing_date TEXT,
            hearing_date TEXT,
            description TEXT,
            strategy TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
        )
    """)

    # 提醒表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            source_type TEXT NOT NULL,
            source_id INTEGER NOT NULL,
            reminder_date TEXT NOT NULL,
            reminder_type TEXT,
            title TEXT NOT NULL,
            content TEXT,
            is_sent INTEGER DEFAULT 0,
            sent_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_loans_project ON loans(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contracts_project ON contracts(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_project ON meetings(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_project ON evidence(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_project ON cases(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_project ON reminders(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_loans_due_date ON loans(due_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_date ON reminders(reminder_date)")

    # 身份历史记录表（追踪身份转换）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS party_role_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            party_id INTEGER,
            old_role TEXT,
            new_role TEXT,
            change_reason TEXT,
            changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (party_id) REFERENCES parties(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# ============ 项目操作 ============

def save_project(data: dict) -> int:
    """保存项目"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO projects (
            name, category, category_name, amount, start_date, end_date, status,
            counterparty_name, counterparty_phone, counterparty_id, counterparty_address,
            description, key_terms, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('name'), data.get('category'), data.get('category_name'),
        data.get('amount', 0), data.get('start_date'), data.get('end_date'),
        data.get('status', 'active'), data.get('counterparty_name'),
        data.get('counterparty_phone'), data.get('counterparty_id'),
        data.get('counterparty_address'), data.get('description'),
        data.get('key_terms'), data.get('notes')
    ))

    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return project_id


def update_project(project_id: int, data: dict) -> bool:
    """更新项目"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE projects SET
            name = ?, category = ?, category_name = ?, amount = ?,
            start_date = ?, end_date = ?, status = ?,
            counterparty_name = ?, counterparty_phone = ?, counterparty_id = ?,
            counterparty_address = ?, description = ?, key_terms = ?, notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        data.get('name'), data.get('category'), data.get('category_name'),
        data.get('amount'), data.get('start_date'), data.get('end_date'),
        data.get('status'), data.get('counterparty_name'),
        data.get('counterparty_phone'), data.get('counterparty_id'),
        data.get('counterparty_address'), data.get('description'),
        data.get('key_terms'), data.get('notes'), project_id
    ))

    conn.commit()
    conn.close()
    return True


def delete_project(project_id: int) -> bool:
    """删除项目（关联数据不删除，仅解除关联）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE loans SET project_id = NULL WHERE project_id = ?", (project_id,))
    cursor.execute("UPDATE contracts SET project_id = NULL WHERE project_id = ?", (project_id,))
    cursor.execute("UPDATE meetings SET project_id = NULL WHERE project_id = ?", (project_id,))
    cursor.execute("UPDATE evidence SET project_id = NULL WHERE project_id = ?", (project_id,))
    cursor.execute("UPDATE cases SET project_id = NULL WHERE project_id = ?", (project_id,))
    cursor.execute("UPDATE reminders SET project_id = NULL WHERE project_id = ?", (project_id,))
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    return True


# ============ 当事人信息操作 ============

def save_party(data: dict) -> int:
    """保存当事人信息"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO parties (
            project_id, party_role, party_type, legal_role, name, phone, id_card, address, notes,
            role_effective_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('project_id'), data.get('party_role'), data.get('party_type'),
        data.get('legal_role'), data.get('name'), data.get('phone'), data.get('id_card'),
        data.get('address'), data.get('notes'), data.get('role_effective_date')
    ))

    party_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return party_id


def update_party(party_id: int, data: dict) -> bool:
    """更新当事人信息"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE parties SET
            party_type = ?, legal_role = ?, name = ?, phone = ?, id_card = ?,
            address = ?, notes = ?, role_effective_date = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        data.get('party_type'), data.get('legal_role'), data.get('name'), data.get('phone'),
        data.get('id_card'), data.get('address'), data.get('notes'), data.get('role_effective_date'),
        party_id
    ))

    conn.commit()
    conn.close()
    return True


def delete_party(party_id: int) -> bool:
    """删除当事人信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM parties WHERE id = ?", (party_id,))
    conn.commit()
    conn.close()
    return True


def get_parties(project_id: int, party_role: str = None) -> List[dict]:
    """获取项目的当事人信息"""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM parties WHERE project_id = ?"
    params = [project_id]

    if party_role:
        sql += " AND party_role = ?"
        params.append(party_role)

    sql += " ORDER BY created_at DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_party_by_role(project_id: int, party_role: str) -> Optional[dict]:
    """根据角色获取当事人信息"""
    parties = get_parties(project_id, party_role)
    return parties[0] if parties else None


def update_party_legal_role(project_id: int, party_role: str, new_legal_role: str, reason: str = None) -> bool:
    """更新当事人法律身份（同时记录历史）"""
    party = get_party_by_role(project_id, party_role)
    if not party:
        return False

    old_legal_role = party.get('legal_role')

    # 更新当前身份
    update_party(party['id'], {'legal_role': new_legal_role})

    # 记录身份转换历史
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO party_role_history (project_id, party_id, old_role, new_role, change_reason)
        VALUES (?, ?, ?, ?, ?)
    """, (project_id, party['id'], old_legal_role, new_legal_role, reason))
    conn.commit()
    conn.close()

    return True


def get_party_role_history(project_id: int) -> List[dict]:
    """获取身份转换历史"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.*, p.name as party_name
        FROM party_role_history h
        LEFT JOIN parties p ON h.party_id = p.id
        WHERE h.project_id = ?
        ORDER BY h.changed_at DESC
    """, (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def upsert_party(project_id: int, party_role: str, data: dict) -> int:
    """更新或创建当事人信息"""
    existing = get_party_by_role(project_id, party_role)
    if existing:
        # 如果传递了legal_role，使用新的；否则保留旧的
        if 'legal_role' not in data:
            data['legal_role'] = existing.get('legal_role')
        update_party(existing['id'], data)
        return existing['id']
    else:
        data['project_id'] = project_id
        data['party_role'] = party_role
        return save_party(data)


def get_projects(category: str = None, status: str = None) -> List[dict]:
    """获取项目列表"""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM projects WHERE 1=1"
    params = []

    if category:
        sql += " AND category = ?"
        params.append(category)

    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY updated_at DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_project(project_id: int) -> Optional[dict]:
    """获取单个项目（包含当事人信息）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    project = dict(row)

    # 获取当事人信息
    cursor.execute("SELECT * FROM parties WHERE project_id = ?", (project_id,))
    parties = cursor.fetchall()
    conn.close()

    # 整理当事人信息
    for party in parties:
        p = dict(party)
        if p['party_role'] == 'user':
            project['user_party'] = p
        elif p['party_role'] == 'counterparty':
            project['counterparty_party'] = p

    return project


# ============ 借款操作 ============

def save_loan(data: dict) -> int:
    """保存借款"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO loans (
            project_id, direction, borrower_name, borrower_phone, borrower_id, lender_name,
            amount, start_date, due_date, has_interest, interest_rate,
            interest_type, guarantee, purpose, repayment_method, notes, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('project_id'),
        data.get('direction', 'lend'),
        data.get('borrower_name'),
        data.get('borrower_phone'),
        data.get('borrower_id'),
        data.get('lender_name'),
        data.get('amount', 0),
        data.get('start_date'),
        data.get('due_date'),
        1 if data.get('has_interest') else 0,
        data.get('interest_rate', 0),
        data.get('interest_type'),
        data.get('guarantee'),
        data.get('purpose'),
        data.get('repayment_method'),
        data.get('notes'),
        data.get('status', 'active')
    ))

    loan_id = cursor.lastrowid

    # 创建到期提醒
    if data.get('due_date'):
        create_reminder(
            project_id=data.get('project_id'),
            source_type='loan',
            source_id=loan_id,
            reminder_date=data.get('due_date'),
            reminder_type='due',
            title=f"借款到期: {data.get('borrower_name')}",
            content=f"金额: ¥{data.get('amount', 0):,.2f}"
        )

    conn.commit()
    conn.close()
    return loan_id


def update_loan(loan_id: int, data: dict) -> bool:
    """更新借款"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE loans SET
            project_id = ?, direction = ?, borrower_name = ?, borrower_phone = ?,
            borrower_id = ?, lender_name = ?, amount = ?, start_date = ?, due_date = ?,
            has_interest = ?, interest_rate = ?, interest_type = ?, guarantee = ?,
            purpose = ?, repayment_method = ?, notes = ?, status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        data.get('project_id'), data.get('direction'), data.get('borrower_name'),
        data.get('borrower_phone'), data.get('borrower_id'), data.get('lender_name'),
        data.get('amount'), data.get('start_date'), data.get('due_date'),
        1 if data.get('has_interest') else 0, data.get('interest_rate'),
        data.get('interest_type'), data.get('guarantee'), data.get('purpose'),
        data.get('repayment_method'), data.get('notes'), data.get('status'), loan_id
    ))

    conn.commit()
    conn.close()
    return True


def delete_loan(loan_id: int) -> bool:
    """删除借款"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM loans WHERE id = ?", (loan_id,))
    cursor.execute("DELETE FROM reminders WHERE source_type='loan' AND source_id = ?", (loan_id,))
    conn.commit()
    conn.close()
    return True


def get_loans(project_id: int = None, status: str = None, direction: str = None) -> List[dict]:
    """获取借款记录"""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM loans WHERE 1=1"
    params = []

    if project_id:
        sql += " AND project_id = ?"
        params.append(project_id)

    if status:
        sql += " AND status = ?"
        params.append(status)

    if direction:
        sql += " AND direction = ?"
        params.append(direction)

    sql += " ORDER BY created_at DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# ============ 合同操作 ============

def save_contract(data: dict) -> int:
    """保存合同"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO contracts (
            project_id, title, contract_type, counterparty, amount,
            sign_date, expiry_date, status, content, file_path, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('project_id'),
        data.get('title'),
        data.get('contract_type'),
        data.get('counterparty'),
        data.get('amount', 0),
        data.get('sign_date'),
        data.get('expiry_date'),
        data.get('status', 'pending'),
        data.get('content'),
        data.get('file_path'),
        data.get('notes')
    ))

    contract_id = cursor.lastrowid

    if data.get('expiry_date'):
        create_reminder(
            project_id=data.get('project_id'),
            source_type='contract',
            source_id=contract_id,
            reminder_date=data.get('expiry_date'),
            reminder_type='due',
            title=f"合同到期: {data.get('title')}",
            content="合同即将到期"
        )

    conn.commit()
    conn.close()
    return contract_id


def update_contract(contract_id: int, data: dict) -> bool:
    """更新合同"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE contracts SET
            project_id = ?, title = ?, contract_type = ?, counterparty = ?,
            amount = ?, sign_date = ?, expiry_date = ?, status = ?,
            content = ?, file_path = ?, notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        data.get('project_id'), data.get('title'), data.get('contract_type'),
        data.get('counterparty'), data.get('amount'), data.get('sign_date'),
        data.get('expiry_date'), data.get('status'), data.get('content'),
        data.get('file_path'), data.get('notes'), contract_id
    ))

    conn.commit()
    conn.close()
    return True


def delete_contract(contract_id: int) -> bool:
    """删除合同"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))
    conn.commit()
    conn.close()
    return True


def get_contracts(project_id: int = None, status: str = None) -> List[dict]:
    """获取合同"""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM contracts WHERE 1=1"
    params = []

    if project_id:
        sql += " AND project_id = ?"
        params.append(project_id)

    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY created_at DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# ============ 会议操作 ============

def save_meeting(data: dict) -> int:
    """保存会议"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO meetings (
            project_id, session_id, meeting_type, topic, meeting_date,
            participants, content, minutes, contract_draft, resolution,
            audio_files, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('project_id'),
        data.get('session_id'),
        data.get('meeting_type'),
        data.get('topic'),
        data.get('meeting_date'),
        data.get('participants'),
        data.get('content'),
        data.get('minutes'),
        data.get('contract_draft'),
        data.get('resolution'),
        json.dumps(data.get('audio_files', [])),
        data.get('status', 'active')
    ))

    meeting_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return meeting_id


def update_meeting(meeting_id: int, data: dict) -> bool:
    """更新会议"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE meetings SET
            project_id = ?, meeting_type = ?, topic = ?, meeting_date = ?,
            participants = ?, content = ?, minutes = ?, contract_draft = ?,
            resolution = ?, audio_files = ?, status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        data.get('project_id'), data.get('meeting_type'), data.get('topic'),
        data.get('meeting_date'), data.get('participants'), data.get('content'),
        data.get('minutes'), data.get('contract_draft'), data.get('resolution'),
        json.dumps(data.get('audio_files', [])), data.get('status'), meeting_id
    ))

    conn.commit()
    conn.close()
    return True


def get_meetings(project_id: int = None, limit: int = 50) -> List[dict]:
    """获取会议"""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM meetings WHERE 1=1"
    params = []

    if project_id:
        sql += " AND project_id = ?"
        params.append(project_id)

    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        item = dict(row)
        if item.get('audio_files'):
            item['audio_files'] = json.loads(item['audio_files'])
        results.append(item)

    return results


# ============ 证据操作 ============

def save_evidence(data: dict) -> int:
    """保存证据"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO evidence (
            project_id, case_id, evidence_type, title, description,
            file_path, file_name, file_size, importance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('project_id'),
        data.get('case_id'),
        data.get('evidence_type'),
        data.get('title'),
        data.get('description'),
        data.get('file_path'),
        data.get('file_name'),
        data.get('file_size'),
        data.get('importance', 'normal')
    ))

    evidence_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return evidence_id


def update_evidence(evidence_id: int, data: dict) -> bool:
    """更新证据"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE evidence SET
            project_id = ?, case_id = ?, evidence_type = ?, title = ?,
            description = ?, file_path = ?, file_name = ?, file_size = ?,
            importance = ?
        WHERE id = ?
    """, (
        data.get('project_id'), data.get('case_id'), data.get('evidence_type'),
        data.get('title'), data.get('description'), data.get('file_path'),
        data.get('file_name'), data.get('file_size'), data.get('importance'),
        evidence_id
    ))

    conn.commit()
    conn.close()
    return True


def delete_evidence(evidence_id: int) -> bool:
    """删除证据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM evidence WHERE id = ?", (evidence_id,))
    conn.commit()
    conn.close()
    return True


def get_evidence(project_id: int = None, case_id: int = None) -> List[dict]:
    """获取证据"""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM evidence WHERE 1=1"
    params = []

    if project_id:
        sql += " AND project_id = ?"
        params.append(project_id)

    if case_id:
        sql += " AND case_id = ?"
        params.append(case_id)

    sql += " ORDER BY created_at DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# ============ 案件操作 ============

def save_case(data: dict) -> int:
    """保存案件"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cases (
            project_id, title, case_type, case_no, court, plaintiff, defendant,
            claim_amount, status, filing_date, hearing_date,
            description, strategy, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('project_id'),
        data.get('title'),
        data.get('case_type'),
        data.get('case_no'),
        data.get('court'),
        data.get('plaintiff'),
        data.get('defendant'),
        data.get('claim_amount', 0),
        data.get('status', 'pending'),
        data.get('filing_date'),
        data.get('hearing_date'),
        data.get('description'),
        data.get('strategy'),
        data.get('notes')
    ))

    case_id = cursor.lastrowid

    if data.get('hearing_date'):
        create_reminder(
            project_id=data.get('project_id'),
            source_type='case',
            source_id=case_id,
            reminder_date=data.get('hearing_date'),
            reminder_type='due',
            title=f"开庭提醒: {data.get('title')}",
            content="请做好准备出庭"
        )

    conn.commit()
    conn.close()
    return case_id


def update_case(case_id: int, data: dict) -> bool:
    """更新案件"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cases SET
            project_id = ?, title = ?, case_type = ?, case_no = ?, court = ?,
            plaintiff = ?, defendant = ?, claim_amount = ?, status = ?,
            filing_date = ?, hearing_date = ?, description = ?, strategy = ?,
            notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        data.get('project_id'), data.get('title'), data.get('case_type'),
        data.get('case_no'), data.get('court'), data.get('plaintiff'),
        data.get('defendant'), data.get('claim_amount'), data.get('status'),
        data.get('filing_date'), data.get('hearing_date'), data.get('description'),
        data.get('strategy'), data.get('notes'), case_id
    ))

    conn.commit()
    conn.close()
    return True


def get_cases(project_id: int = None, status: str = None) -> List[dict]:
    """获取案件"""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM cases WHERE 1=1"
    params = []

    if project_id:
        sql += " AND project_id = ?"
        params.append(project_id)

    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY updated_at DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# ============ 提醒操作 ============

def create_reminder(
    project_id: int,
    source_type: str,
    source_id: int,
    reminder_date: str,
    reminder_type: str,
    title: str,
    content: str = None
) -> int:
    """创建提醒"""
    conn = get_db_connection()
    cursor = conn.cursor()

    reminder_dates = []
    try:
        base_date = datetime.strptime(reminder_date, '%Y-%m-%d')
        for days_before in [7, 3, 1, 0]:
            if days_before == 0:
                reminder_dates.append(reminder_date)
            else:
                remind_date = base_date - timedelta(days=days_before)
                if remind_date.date() >= datetime.now().date():
                    reminder_dates.append(remind_date.strftime('%Y-%m-%d'))
    except:
        reminder_dates = [reminder_date]

    reminder_ids = []
    for rdate in reminder_dates:
        cursor.execute("""
            INSERT INTO reminders (
                project_id, source_type, source_id, reminder_date, reminder_type, title, content
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (project_id, source_type, source_id, rdate, reminder_type, title, content))
        reminder_ids.append(cursor.lastrowid)

    conn.commit()
    conn.close()
    return reminder_ids[0] if reminder_ids else 0


def get_upcoming_reminders(project_id: int = None, days: int = 30) -> List[dict]:
    """获取即将到来的提醒"""
    conn = get_db_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

    sql = "SELECT * FROM reminders WHERE reminder_date >= ? AND reminder_date <= ? AND is_sent = 0"
    params = [today, end_date]

    if project_id:
        sql += " AND project_id = ?"
        params.append(project_id)

    sql += " ORDER BY reminder_date ASC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_overdue_reminders(project_id: int = None) -> List[dict]:
    """获取已逾期提醒"""
    conn = get_db_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')

    sql = "SELECT * FROM reminders WHERE reminder_date < ? AND is_sent = 0"
    params = [today]

    if project_id:
        sql += " AND project_id = ?"
        params.append(project_id)

    sql += " ORDER BY reminder_date ASC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def mark_reminder_sent(reminder_id: int) -> bool:
    """标记提醒已发送"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reminders SET is_sent = 1, sent_at = CURRENT_TIMESTAMP WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()
    return True


# ============ 统计数据 ============

def get_statistics() -> dict:
    """获取统计数据"""
    conn = get_db_connection()
    cursor = conn.cursor()

    stats = {}

    cursor.execute("SELECT COUNT(*) as count, SUM(amount) as total FROM loans WHERE direction='lend'")
    row = cursor.fetchone()
    stats['lend_count'] = row['count']
    stats['lend_total'] = row['total'] or 0

    cursor.execute("SELECT COUNT(*) as count, SUM(amount) as total FROM loans WHERE direction='borrow'")
    row = cursor.fetchone()
    stats['borrow_count'] = row['count']
    stats['borrow_total'] = row['total'] or 0

    cursor.execute("SELECT COUNT(*) as count FROM projects WHERE status IN ('active', 'pending')")
    row = cursor.fetchone()
    stats['active_projects'] = row['count']

    cursor.execute("SELECT COUNT(*) as count FROM contracts WHERE status='pending'")
    row = cursor.fetchone()
    stats['pending_contracts'] = row['count']

    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) as count FROM reminders WHERE reminder_date < ? AND is_sent = 0", (today,))
    row = cursor.fetchone()
    stats['overdue_reminders'] = row['count']

    conn.close()
    return stats


# ============ 数据导出/导入 ============

def export_all_data() -> dict:
    """导出所有数据"""
    return {
        'export_time': datetime.now().isoformat(),
        'projects': get_projects(),
        'loans': get_loans(),
        'contracts': get_contracts(),
        'meetings': get_meetings(),
        'cases': get_cases()
    }


def import_data(data: dict) -> bool:
    """导入数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if 'projects' in data:
            for project in data['projects']:
                cursor.execute("""
                    INSERT INTO projects (name, category, category_name, amount, start_date,
                        end_date, status, counterparty_name, counterparty_phone, counterparty_id,
                        counterparty_address, description, key_terms, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project.get('name'), project.get('category'), project.get('category_name'),
                    project.get('amount', 0), project.get('start_date'), project.get('end_date'),
                    project.get('status', 'active'), project.get('counterparty_name'),
                    project.get('counterparty_phone'), project.get('counterparty_id'),
                    project.get('counterparty_address'), project.get('description'),
                    project.get('key_terms'), project.get('notes')
                ))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Import error: {e}")
        return False


# 初始化
init_database()
