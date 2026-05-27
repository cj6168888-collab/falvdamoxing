-- 战役模型数据库迁移脚本
-- 执行时间：2026-04-08

-- 1. 创建 case_claims 表
CREATE TABLE IF NOT EXISTS case_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    claim_type VARCHAR(50),
    amount VARCHAR(100),
    priority INTEGER DEFAULT 3,
    status VARCHAR(50) DEFAULT '待处理',
    required_documents TEXT DEFAULT '[]',
    required_evidence_ids TEXT DEFAULT '[]',
    depends_on TEXT DEFAULT '[]',
    ai_plan_result TEXT,
    ai_evidence_suggestions TEXT DEFAULT '[]',
    ai_document_suggestions TEXT DEFAULT '[]',
    risk_level VARCHAR(20) DEFAULT 'medium',
    risk_notes TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_case_claims_case_id ON case_claims(case_id);

-- 2. 修改 generated_documents 表添加战役关联字段
ALTER TABLE generated_documents ADD COLUMN claim_id INTEGER;
ALTER TABLE generated_documents ADD COLUMN campaign_goal VARCHAR(500);
ALTER TABLE generated_documents ADD COLUMN used_evidence_ids TEXT DEFAULT '[]';
