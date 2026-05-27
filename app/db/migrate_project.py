"""
项目相关数据库表迁移脚本
"""
import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

db_path = "d:/www/法律大模型/legal_system.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 项目主表
cursor.execute('''
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    name TEXT NOT NULL,
    project_type TEXT,
    description TEXT,
    user_role TEXT,
    counterpart_name TEXT,
    counterpart_type TEXT,
    counterpart_contact TEXT,
    start_date TIMESTAMP,
    expected_end_date TIMESTAMP,
    actual_end_date TIMESTAMP,
    status TEXT DEFAULT 'planning',
    current_phase TEXT,
    amount TEXT,
    currency TEXT DEFAULT 'CNY',
    related_projects TEXT,
    related_cases TEXT,
    risk_level TEXT DEFAULT 'low',
    risk_factors TEXT,
    risk_warnings TEXT,
    progress REAL DEFAULT 0,
    legal_analysis TEXT,
    legal_advice TEXT,
    contract_review TEXT,
    suggested_documents TEXT,
    milestones TEXT,
    reminders TEXT,
    is_archived INTEGER DEFAULT 0,
    is_favorite INTEGER DEFAULT 0,
    tags TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
print('[OK] projects 表创建成功')

# 项目文档表
cursor.execute('''
CREATE TABLE IF NOT EXISTS project_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    doc_type TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    source TEXT,
    received_date TIMESTAMP,
    content TEXT,
    content_summary TEXT,
    ai_review TEXT,
    risk_points TEXT,
    favorable_clauses TEXT,
    unfavorable_clauses TEXT,
    suggested_amendments TEXT,
    status TEXT DEFAULT 'draft',
    version TEXT DEFAULT '1.0',
    previous_version_id INTEGER,
    file_path TEXT,
    file_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
)
''')
print('[OK] project_documents 表创建成功')

# 项目里程碑表
cursor.execute('''
CREATE TABLE IF NOT EXISTS project_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    milestone_type TEXT,
    phase TEXT,
    planned_date TIMESTAMP,
    actual_date TIMESTAMP,
    status TEXT DEFAULT 'pending',
    ai_reminder TEXT,
    legal_tips TEXT,
    related_document_id INTEGER,
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
)
''')
print('[OK] project_milestones 表创建成功')

# 往来记录表
cursor.execute('''
CREATE TABLE IF NOT EXISTS project_communications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    communication_type TEXT NOT NULL,
    direction TEXT NOT NULL,
    subject TEXT,
    content TEXT,
    full_content TEXT,
    counterpart_name TEXT,
    counterpart_role TEXT,
    communication_date TIMESTAMP,
    recorded_by TEXT,
    ai_summary TEXT,
    key_points TEXT,
    promises_made TEXT,
    disputes_raised TEXT,
    evidence_value TEXT DEFAULT 'low',
    is_key_evidence INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
)
''')
print('[OK] project_communications 表创建成功')

# 证据材料表
cursor.execute('''
CREATE TABLE IF NOT EXISTS project_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    evidence_type TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    source TEXT,
    obtained_date TIMESTAMP,
    content TEXT,
    content_summary TEXT,
    probative_value TEXT DEFAULT 'medium',
    authenticity TEXT DEFAULT 'unknown',
    legality TEXT DEFAULT 'legal',
    ai_analysis TEXT,
    usage_suggestions TEXT,
    risk_warnings TEXT,
    related_events TEXT,
    related_communications TEXT,
    status TEXT DEFAULT 'collected',
    is_key_evidence INTEGER DEFAULT 0,
    file_path TEXT,
    completeness REAL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
)
''')
print('[OK] project_evidence 表创建成功')

# 法律建议表
cursor.execute('''
CREATE TABLE IF NOT EXISTS project_legal_advices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    advice_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    applicable_phase TEXT,
    applicable_situation TEXT,
    urgency TEXT DEFAULT 'medium',
    is_read INTEGER DEFAULT 0,
    is_acted INTEGER DEFAULT 0,
    action_taken TEXT,
    action_date TIMESTAMP,
    model_used TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
)
''')
print('[OK] project_legal_advices 表创建成功')

# 项目事件表
cursor.execute('''
CREATE TABLE IF NOT EXISTS project_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    event_date TIMESTAMP NOT NULL,
    importance TEXT DEFAULT 'normal',
    ai_analysis TEXT,
    legal_significance TEXT,
    suggestions TEXT,
    related_milestone_id INTEGER,
    related_communication_id INTEGER,
    related_evidence_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
)
''')
print('[OK] project_events 表创建成功')

# 合同管理表
cursor.execute('''
CREATE TABLE IF NOT EXISTS project_contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    contract_type TEXT,
    contract_name TEXT NOT NULL,
    contract_number TEXT,
    party_a TEXT,
    party_b TEXT,
    amount TEXT,
    currency TEXT DEFAULT 'CNY',
    signing_date TIMESTAMP,
    effective_date TIMESTAMP,
    expiration_date TIMESTAMP,
    status TEXT DEFAULT 'draft',
    key_terms TEXT,
    favorable_terms TEXT,
    unfavorable_terms TEXT,
    risk_clauses TEXT,
    performance_status TEXT,
    performance_records TEXT,
    ai_review TEXT,
    risk_level TEXT DEFAULT 'medium',
    overall_evaluation TEXT,
    current_version TEXT DEFAULT '1.0',
    versions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
)
''')
print('[OK] project_contracts 表创建成功')

# 风险记录表
cursor.execute('''
CREATE TABLE IF NOT EXISTS project_risks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    risk_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    severity TEXT DEFAULT 'medium',
    probability TEXT DEFAULT 'medium',
    impact TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'identified',
    mitigation_plan TEXT,
    preventive_measures TEXT,
    contingency_plan TEXT,
    related_clause TEXT,
    related_event_id INTEGER,
    is_monitored INTEGER DEFAULT 1,
    monitor_frequency TEXT DEFAULT 'weekly',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
)
''')
print('[OK] project_risks 表创建成功')

# 项目转案件映射表
cursor.execute('''
CREATE TABLE IF NOT EXISTS project_case_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    case_id INTEGER,
    conversion_reason TEXT,
    conversion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    migrated_documents TEXT,
    migrated_evidence TEXT,
    migrated_communications TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
)
''')
print('[OK] project_case_mappings 表创建成功')

conn.commit()
conn.close()
print('[SUCCESS] 项目相关表全部创建成功！')
