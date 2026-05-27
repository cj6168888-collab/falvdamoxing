-- ============================================================
-- 法律大模型辅助系统 - PostgreSQL 数据库初始化脚本
-- ⚠️ 已过时 (DEPRECATED)— 表结构与当前 ORM 模型不匹配
-- 请使用 app/db/migrate_all.py 进行数据库初始化/migration
-- 用途: docker-compose.prod.yml 中 postgres 服务的初始化
-- 使用: docker-compose up -d postgres 自动执行
-- ============================================================

-- ============================================================
-- 1. 扩展
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 模糊搜索支持

-- ============================================================
-- 2. 案件表 (cases)
-- ============================================================
CREATE TABLE IF NOT EXISTS cases (
    id SERIAL PRIMARY KEY,
    case_number VARCHAR(100) UNIQUE,
    case_type VARCHAR(50) NOT NULL DEFAULT '民事',          -- 民事/刑事/行政/仲裁
    case_status VARCHAR(50) NOT NULL DEFAULT '收案',
    case_name VARCHAR(500),
    description TEXT,

    -- 当事人
    plaintiff VARCHAR(500),
    defendant VARCHAR(500),
    third_party TEXT,                                      -- 追加第三人(biz-7)
    court VARCHAR(200),
    judge VARCHAR(200),

    -- 金额
    amount DECIMAL(15,2),
    estimated_cost DECIMAL(15,2),

    -- 期限
    filing_date DATE,
    hearing_date TIMESTAMP,
    judgment_date DATE,
    appeal_deadline DATE,                                  -- 上诉期限
    litigation_limitation DATE,                            -- 诉讼时效截止(3年, biz-1)

    -- 状态扩展 (biz-13)
    -- SUSPENDED: 案件中止; DORMANT: 案件休眠

    -- 元数据
    tags TEXT,                                             -- JSON 字符串
    metadata JSONB,
    created_by VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(case_status);
CREATE INDEX IF NOT EXISTS idx_cases_type ON cases(case_type);
CREATE INDEX IF NOT EXISTS idx_cases_filing_date ON cases(filing_date);
CREATE INDEX IF NOT EXISTS idx_cases_litigation_limitation ON cases(litigation_limitation);
CREATE INDEX IF NOT EXISTS idx_cases_hearing_date ON cases(hearing_date);

-- ============================================================
-- 3. 文档表 (documents)
-- ============================================================
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,

    filename VARCHAR(500) NOT NULL,
    stored_path VARCHAR(1000) NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,

    -- 内容提取
    content TEXT,
    content_summary TEXT,

    -- 向量索引
    vector_id VARCHAR(200),
    is_indexed INTEGER DEFAULT 0,

    -- 元数据
    doc_type VARCHAR(100),                                 -- 合同/证据/判决书等
    tags TEXT,                                             -- JSON
    uploaded_by VARCHAR(200),                              -- bugfix-4

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_case_id ON documents(case_id);
CREATE INDEX IF NOT EXISTS idx_documents_vector_id ON documents(vector_id);
CREATE INDEX IF NOT EXISTS idx_documents_is_indexed ON documents(is_indexed);

-- ============================================================
-- 4. 证据表 (evidence_items)
-- ============================================================
CREATE TABLE IF NOT EXISTS evidence_items (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,

    -- 基本信息
    name VARCHAR(500) NOT NULL,
    evidence_type VARCHAR(100) NOT NULL,                   -- CONTRACT/CORRESPONDENCE/PAYMENT等
    source VARCHAR(100),                                   -- FILE/TEXT/INPUT

    -- 来源方
    source_party VARCHAR(100),                             -- 举证方
    custody_party VARCHAR(100),                            -- 保管方

    -- 内容
    content TEXT,
    content_hash VARCHAR(64),                              -- 内容哈希(去重)

    -- 证明力
    credibility_score DECIMAL(5,2) DEFAULT 0.5,           -- 0-1
    strength_factors TEXT,                                 -- JSON: 影响证明力因素

    -- 关系
    proves_facts TEXT,                                     -- JSON: 能证明的事实
    related_evidence TEXT,                                -- JSON: 关联证据ID列表

    -- 状态
    status VARCHAR(50) DEFAULT 'pending',                  -- pending/analyzed/verified/questionable
    is_duplicate INTEGER DEFAULT 0,

    -- 三性分析 (biz-5)
    authenticity_analysis TEXT,
    legality_analysis TEXT,
    relevance_analysis TEXT,
    three_natures_conclusion TEXT,

    -- 元数据
    tags TEXT,                                            -- JSON
    metadata JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evidence_case_id ON evidence_items(case_id);
CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence_items(evidence_type);
CREATE INDEX IF NOT EXISTS idx_evidence_content_hash ON evidence_items(content_hash);
CREATE INDEX IF NOT EXISTS idx_evidence_status ON evidence_items(status);

-- 证据关系表
CREATE TABLE IF NOT EXISTS evidence_relationships (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    source_evidence_id INTEGER REFERENCES evidence_items(id) ON DELETE CASCADE,
    target_evidence_id INTEGER REFERENCES evidence_items(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50),                        -- SUPPORT/CONTRADICT/SUPPLEMENT/ELABORATE
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_er_case_id ON evidence_relationships(case_id);
CREATE INDEX IF NOT EXISTS idx_er_source ON evidence_relationships(source_evidence_id);
CREATE INDEX IF NOT EXISTS idx_er_target ON evidence_relationships(target_evidence_id);

-- 证据事实表
CREATE TABLE IF NOT EXISTS evidence_facts (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    fact_description TEXT NOT NULL,
    supporting_evidence_ids TEXT,                         -- JSON: 支持该事实的证据ID列表
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ef_case_id ON evidence_facts(case_id);

-- 证据关键词索引
CREATE TABLE IF NOT EXISTS evidence_keyword_index (
    id SERIAL PRIMARY KEY,
    evidence_id INTEGER REFERENCES evidence_items(id) ON DELETE CASCADE,
    keyword VARCHAR(200) NOT NULL,
    frequency INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_eki_keyword ON evidence_keyword_index USING gin(keyword gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_eki_evidence_id ON evidence_keyword_index(evidence_id);

-- ============================================================
-- 5. 法律期限表 (legal_deadlines)
-- ============================================================
CREATE TABLE IF NOT EXISTS legal_deadlines (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,

    deadline_type VARCHAR(100) NOT NULL,                   -- litigation/arbitration/evidence/appeal等
    description VARCHAR(500),
    start_date DATE,
    end_date DATE,
    days INTEGER,                                          -- 期限天数(仲裁4年 biz-2)

    -- 节假日处理(biz-3)
    holidays_excluded INTEGER DEFAULT 0,
    adjusted_end_date DATE,                                -- 节假日调整后的截止日

    priority VARCHAR(20) DEFAULT 'medium',                 -- high/medium/low
    status VARCHAR(50) DEFAULT 'pending',                  -- pending/active/expired/completed
    reminder_sent INTEGER DEFAULT 0,

    -- 举证期限精确化(biz-4)
    -- 普通程序: 30日; 简易程序: 15日; 小额诉讼: 7日

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ld_case_id ON legal_deadlines(case_id);
CREATE INDEX IF NOT EXISTS idx_ld_end_date ON legal_deadlines(end_date);
CREATE INDEX IF NOT EXISTS idx_ld_status ON legal_deadlines(status);
CREATE INDEX IF NOT EXISTS idx_ld_type ON legal_deadlines(deadline_type);

-- ============================================================
-- 6. 里程碑表 (milestones)
-- ============================================================
CREATE TABLE IF NOT EXISTS milestones (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,

    milestone_id VARCHAR(100) NOT NULL,
    title VARCHAR(500),
    phase VARCHAR(50),                                    -- 阶段
    description TEXT,

    status VARCHAR(50) DEFAULT 'pending',                  -- pending/in_progress/completed/skipped/overdue
    priority VARCHAR(20) DEFAULT 'medium',

    due_date DATE,
    completed_date DATE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_milestones_case_id ON milestones(case_id);
CREATE INDEX IF NOT EXISTS idx_milestones_status ON milestones(status);
CREATE INDEX IF NOT EXISTS idx_milestones_due_date ON milestones(due_date);

-- ============================================================
-- 7. 提醒表 (reminders)
-- ============================================================
CREATE TABLE IF NOT EXISTS reminders (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,

    reminder_type VARCHAR(50) NOT NULL,                   -- deadline/material_missing/hearing/evidence/risk等
    title VARCHAR(500) NOT NULL,
    content TEXT,
    priority VARCHAR(20) DEFAULT 'medium',                 -- high/medium/low

    deadline_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',                 -- pending/sent/acknowledged/overdue

    -- 多渠道提醒(biz-12)
    channels TEXT,                                        -- JSON: ["email","sms","wechat","dingtalk","in_app"]

    sent_at TIMESTAMP,
    acknowledged_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reminders_case_id ON reminders(case_id);
CREATE INDEX IF NOT EXISTS idx_reminders_deadline ON reminders(deadline_date);
CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status);

-- ============================================================
-- 8. 对话会话表 (conversation_sessions)
-- ============================================================
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,

    session_type VARCHAR(50) DEFAULT 'qa',                 -- qa/analysis/clarification/strategy/document
    status VARCHAR(50) DEFAULT 'active',                  -- active/completed/archived/expired

    -- 意图识别
    primary_intent VARCHAR(100),
    intent_confidence DECIMAL(5,2),

    -- 澄清机制(biz-7)
    clarification_status VARCHAR(50) DEFAULT 'none',      -- none/pending/completed
    clarification_record TEXT,                             -- JSON

    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cs_case_id ON conversation_sessions(case_id);
CREATE INDEX IF NOT EXISTS idx_cs_status ON conversation_sessions(status);

-- 对话消息表
CREATE TABLE IF NOT EXISTS conversation_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES conversation_sessions(id) ON DELETE CASCADE,

    role VARCHAR(20) NOT NULL,                            -- user/assistant/system
    content TEXT NOT NULL,
    metadata JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cm_session_id ON conversation_messages(session_id);

-- ============================================================
-- 9. 对抗性分析表 (adversarial_analyses)
-- ============================================================
CREATE TABLE IF NOT EXISTS adversarial_analyses (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,

    analysis_phase VARCHAR(50) NOT NULL,                   -- 协商/诉前准备/诉讼/审理/上诉/执行
    analysis_type VARCHAR(100),                            -- 对手分析/攻防矩阵/情景预测等

    content TEXT,
    metadata JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_aa_case_id ON adversarial_analyses(case_id);
CREATE INDEX IF NOT EXISTS idx_aa_phase ON adversarial_analyses(analysis_phase);

-- ============================================================
-- 10. 项目表 (projects)
-- ============================================================
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_type VARCHAR(100) NOT NULL,                    -- 商业合作/劳动合同/合同纠纷等
    project_name VARCHAR(500),
    project_status VARCHAR(50) DEFAULT '筹划中',
    project_phase VARCHAR(100),

    description TEXT,
    counterparty VARCHAR(500),
    contract_amount DECIMAL(15,2),

    start_date DATE,
    end_date DATE,

    tags TEXT,                                             -- JSON
    metadata JSONB,
    created_by VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(project_status);
CREATE INDEX IF NOT EXISTS idx_projects_type ON projects(project_type);

-- 项目里程碑
CREATE TABLE IF NOT EXISTS project_milestones (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(500),
    phase VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    due_date DATE,
    completed_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pm_project_id ON project_milestones(project_id);

-- 项目合同
CREATE TABLE IF NOT EXISTS project_contracts (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    contract_name VARCHAR(500),
    contract_type VARCHAR(100),
    amount DECIMAL(15,2),
    sign_date DATE,
    parties TEXT,
    key_terms TEXT,
    risks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pc_project_id ON project_contracts(project_id);

-- 项目风险
CREATE TABLE IF NOT EXISTS project_risks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    risk_type VARCHAR(100),
    description TEXT,
    severity VARCHAR(20),                                -- high/medium/low
    mitigation TEXT,
    status VARCHAR(50) DEFAULT 'identified',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pr_project_id ON project_risks(project_id);

-- 项目事件
CREATE TABLE IF NOT EXISTS project_events (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    event_type VARCHAR(100),
    description TEXT,
    event_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pe_project_id ON project_events(project_id);

-- 项目通信
CREATE TABLE IF NOT EXISTS project_communications (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    direction VARCHAR(20),                               -- incoming/outgoing
    letter_type VARCHAR(100),
    subject VARCHAR(500),
    content TEXT,
    letter_date DATE,
    reply_deadline DATE,
    reply_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pc_project_id ON project_communications(project_id);

-- 项目转案件
CREATE TABLE IF NOT EXISTS project_to_case (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    case_id INTEGER REFERENCES cases(id) ON DELETE SET NULL,
    reason TEXT,
    converted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ptc_project_id ON project_to_case(project_id);
CREATE INDEX IF NOT EXISTS idx_ptc_case_id ON project_to_case(case_id);

-- ============================================================
-- 11. 报告表 (reports)
-- ============================================================
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,

    report_type VARCHAR(100) NOT NULL,                     -- ANALYSIS/STRATEGY/FULL_ANALYSIS/EVIDENCE_REPORT等
    title VARCHAR(500),
    status VARCHAR(50) DEFAULT 'PLANNING',                 -- PLANNING/GENERATING/VALIDATING/COMPLETED/PARTIAL/FAILED

    content TEXT,
    sections JSONB,                                        -- 分段生成结果

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_case_id ON reports(case_id);
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);

-- ============================================================
-- 12. 开庭表 (hearings)
-- ============================================================
CREATE TABLE IF NOT EXISTS hearings (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,

    hearing_type VARCHAR(50) DEFAULT 'first_trial',       -- first_trial/second_trial/retrial/arbitration等
    hearing_date TIMESTAMP NOT NULL,
    court VARCHAR(200),
    judge VARCHAR(200),
    clerk VARCHAR(200),

    -- 出席方
    plaintiff_present INTEGER DEFAULT 0,
    defendant_present INTEGER DEFAULT 0,
    plaintiff_lawyer VARCHAR(200),
    defendant_lawyer VARCHAR(200),

    -- 记录
    record_summary TEXT,
    key_points TEXT,
    trap_warnings TEXT,                                   -- 陷阱预警
    evidence_usage TEXT,                                  -- 证据使用时机

    status VARCHAR(50) DEFAULT 'scheduled',              -- scheduled/in_progress/completed/cancelled
    next_hearing_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_hearings_case_id ON hearings(case_id);
CREATE INDEX IF NOT EXISTS idx_hearings_date ON hearings(hearing_date);

-- 庭审记录
CREATE TABLE IF NOT EXISTS hearing_records (
    id SERIAL PRIMARY KEY,
    hearing_id INTEGER REFERENCES hearings(id) ON DELETE CASCADE,
    speaker_role VARCHAR(50),                             -- judge/clerk/plaintiff/defendant/lawyer等
    speaker_name VARCHAR(200),
    content TEXT NOT NULL,
    segment_type VARCHAR(50),                            -- question/answer/statement/objection/ruling
    is_trap INTEGER DEFAULT 0,                           -- 陷阱标记
    trap_type VARCHAR(100),                               -- 陷阱类型
    timing_advice VARCHAR(100),                           -- 使用时机建议
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_hr_hearing_id ON hearing_records(hearing_id);

-- ============================================================
-- 13. 上诉表 (appeals)
-- ============================================================
CREATE TABLE IF NOT EXISTS appeals (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,

    appeal_type VARCHAR(50) DEFAULT 'first_to_second',   -- first_to_second/second_to_retrial/retrial
    appeal_reason VARCHAR(100),                          -- factual_error/legal_error/procedural等

    appeal_status VARCHAR(50) DEFAULT '准备中',
    appeal_date DATE,
    deadline_date DATE,                                  -- 上诉期限(15日)

    -- 上诉人/被上诉人
    appellant VARCHAR(500),
    appellee VARCHAR(500),

    -- 内容
    appeal_request TEXT,
    appeal_reason_detail TEXT,
    new_evidence TEXT,
    response TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_appeals_case_id ON appeals(case_id);
CREATE INDEX IF NOT EXISTS idx_appeals_deadline ON appeals(deadline_date);

-- ============================================================
-- 14. 函件表 (letters)
-- ============================================================
CREATE TABLE IF NOT EXISTS letters (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,

    direction VARCHAR(20) NOT NULL,                      -- incoming/outgoing
    letter_type VARCHAR(100),                            -- lawyer_letter/demand_letter/notice等
    subject VARCHAR(500),
    content TEXT,

    -- 对方信息
    sender VARCHAR(500),
    recipient VARCHAR(500),

    letter_date DATE,
    reply_required INTEGER DEFAULT 0,
    reply_deadline DATE,
    reply_content TEXT,
    reply_date DATE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_letters_case_id ON letters(case_id);
CREATE INDEX IF NOT EXISTS idx_letters_reply_deadline ON letters(reply_deadline);
CREATE INDEX IF NOT EXISTS idx_letters_direction ON letters(direction);

-- ============================================================
-- 15. 质证记录表 (cross_examinations) - biz-7
-- ============================================================
CREATE TABLE IF NOT EXISTS cross_examinations (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    evidence_id INTEGER REFERENCES evidence_items(id) ON DELETE CASCADE,

    examination_type VARCHAR(50) NOT NULL,               -- authenticity/legality/relevance/comprehensive
    result VARCHAR(50),                                  -- accept/object/partially_accept

    -- 质疑内容
    objection_content TEXT,
    opposing_response TEXT,
    court_ruling TEXT,

    -- 三性分析
    authenticity_opinion TEXT,
    legality_opinion TEXT,
    relevance_opinion TEXT,
    final_opinion TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ce_case_id ON cross_examinations(case_id);
CREATE INDEX IF NOT EXISTS idx_ce_evidence_id ON cross_examinations(evidence_id);

-- ============================================================
-- 16. 证据分析表 (evidence_analysis) - biz-5
-- ============================================================
CREATE TABLE IF NOT EXISTS evidence_analysis (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    evidence_id INTEGER REFERENCES evidence_items(id) ON DELETE CASCADE,

    analysis_type VARCHAR(100),                          -- three_natures/completeness/credibility

    -- 证据三性分析 (biz-5)
    authenticity_analysis TEXT,
    authenticity_score DECIMAL(5,2),
    legality_analysis TEXT,
    legality_score DECIMAL(5,2),
    relevance_analysis TEXT,
    relevance_score DECIMAL(5,2),
    comprehensive_analysis TEXT,
    comprehensive_score DECIMAL(5,2),

    -- 完整性检查 (bugfix-2)
    completeness_check TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ea_case_id ON evidence_analysis(case_id);
CREATE INDEX IF NOT EXISTS idx_ea_evidence_id ON evidence_analysis(evidence_id);

-- ============================================================
-- 17. 权限/用户表 (auth) - biz-11
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(200) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    role VARCHAR(50) DEFAULT 'user',                     -- admin/lawyer/assistant/user
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- 团队共享 (biz-11)
CREATE TABLE IF NOT EXISTS team_members (
    id SERIAL PRIMARY KEY,
    team_id VARCHAR(100) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',                   -- owner/admin/member/viewer
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tm_team_id ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_tm_user_id ON team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_tm_case_id ON team_members(case_id);

-- ============================================================
-- 18. JWT令牌黑名单 (auth)
-- ============================================================
CREATE TABLE IF NOT EXISTS token_blacklist (
    id SERIAL PRIMARY KEY,
    jti VARCHAR(100) UNIQUE NOT NULL,                   -- JWT ID
    revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tb_jti ON token_blacklist(jti);

-- ============================================================
-- 19. 通知记录表 (notifications) - biz-12
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    case_id INTEGER REFERENCES cases(id) ON DELETE SET NULL,

    notification_type VARCHAR(50),                        -- email/sms/wechat/dingtalk/in_app
    channel VARCHAR(50),
    title VARCHAR(500),
    content TEXT,

    status VARCHAR(50) DEFAULT 'pending',               -- pending/sent/failed/read
    sent_at TIMESTAMP,
    read_at TIMESTAMP,

    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_case_id ON notifications(case_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);

-- ============================================================
-- 20. 案件报告关联表
-- ============================================================
CREATE TABLE IF NOT EXISTS case_reports (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    report_id INTEGER REFERENCES reports(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cr_case_id ON case_reports(case_id);
CREATE INDEX IF NOT EXISTS idx_cr_report_id ON case_reports(report_id);

-- ============================================================
-- 21. 案件文书关联表
-- ============================================================
CREATE TABLE IF NOT EXISTS case_documents (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    document_type VARCHAR(100),                          -- 起诉状/答辩状/代理词/上诉状等
    content TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cd_case_id ON case_documents(case_id);

-- ============================================================
-- 22. 审计日志表
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id INTEGER,
    changes JSONB,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_al_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_al_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_al_created_at ON audit_logs(created_at);

-- ============================================================
-- 完成
-- ============================================================
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully. All % tables created.', 22;
END $$;
