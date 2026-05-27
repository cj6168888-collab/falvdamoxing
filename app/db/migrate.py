"""
证据系统 V2 数据库迁移
包括：证据项表、证据关系表、证据事实表、去重记录表、关键词索引表
对话系统 V2 表：会话表、消息表、澄清记录表、问题分析表
报告系统 V2 表：报告大纲表、章节表、引用表、缓存表
"""

import sqlite3
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.config import settings


def migrate():
    db_url = settings.database_url
    
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        if db_path.startswith("./"):
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path[2:])
    else:
        db_path = db_url
    
    if not os.path.exists(db_path):
        db_path = "legal_system.db"
    
    print(f"证据系统V2 数据库路径: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cases'")
    if not cursor.fetchone():
        print("案件表不存在，跳过迁移")
        conn.close()
        return

    # ============ 证据系统 V2 表 ============

    # 证据项表 V2
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_items_v2 (
            id TEXT PRIMARY KEY,
            case_id INTEGER NOT NULL,
            source_type TEXT DEFAULT 'file',
            original_filename TEXT,
            display_name TEXT,
            file_path TEXT,
            file_hash TEXT,
            content_hash TEXT,
            raw_content TEXT,
            extracted_content TEXT,
            summary TEXT,
            evidence_number TEXT,
            search_keywords TEXT,
            related_claims TEXT,
            evidence_type TEXT DEFAULT 'OTHER',
            proves_facts TEXT,
            source_party TEXT DEFAULT '己方',
            credibility_score REAL DEFAULT 0.0,
            authenticity_score REAL DEFAULT 0.0,
            reliability_score REAL DEFAULT 0.0,
            consistency_score REAL DEFAULT 0.0,
            corroboration_score REAL DEFAULT 0.0,
            credibility_analysis TEXT,
            keywords TEXT,
            entity_tags TEXT,
            fact_tags TEXT,
            user_corrections TEXT,
            ai_corrections_acknowledged INTEGER DEFAULT 0,
            usage_direction TEXT,
            usage_annotations TEXT,
            usage_tags TEXT,
            is_highlighted INTEGER DEFAULT 0,
            highlight_reason TEXT,
            safety_level TEXT DEFAULT 'safe',
            safety_warnings TEXT,
            adverse_impact_analysis TEXT,
            is_warning_ignored INTEGER DEFAULT 0,
            ignored_reason TEXT,
            safety_reviewed INTEGER DEFAULT 0,
            safety_reviewed_by TEXT,
            safety_reviewed_at TIMESTAMP,
            version INTEGER DEFAULT 1,
            is_current INTEGER DEFAULT 1,
            previous_version_id TEXT,
            version_notes TEXT,
            page_count INTEGER DEFAULT 0,
            page_numbers TEXT,
            language TEXT DEFAULT 'zh-CN',
            file_size INTEGER,
            status TEXT DEFAULT '待处理',
            processing_notes TEXT,
            related_evidence_ids TEXT,
            contradicted_evidence_ids TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            indexed_at TIMESTAMP,
            processed_at TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
        )
    """)
    print("[OK] evidence_items_v2 表创建成功")

    # 证据关系表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_relationships_v2 (
            id TEXT PRIMARY KEY,
            case_id INTEGER NOT NULL,
            from_evidence_id TEXT NOT NULL,
            to_evidence_id TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            strength REAL DEFAULT 50.0,
            analysis_note TEXT,
            citation_text TEXT,
            confidence REAL DEFAULT 0.5,
            reasoning TEXT,
            is_auto_generated INTEGER DEFAULT 1,
            is_confirmed INTEGER DEFAULT 0,
            confirmed_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE,
            FOREIGN KEY (from_evidence_id) REFERENCES evidence_items_v2 (id) ON DELETE CASCADE,
            FOREIGN KEY (to_evidence_id) REFERENCES evidence_items_v2 (id) ON DELETE CASCADE
        )
    """)
    print("[OK] evidence_relationships_v2 表创建成功")

    # 证据事实表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_facts (
            id TEXT PRIMARY KEY,
            case_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            fact_type TEXT,
            importance TEXT DEFAULT 'normal',
            dispute_level TEXT DEFAULT 'undisputed',
            supporting_evidence_ids TEXT,
            contradicting_evidence_ids TEXT,
            evidence_ids TEXT,
            coverage_score REAL DEFAULT 0.0,
            strength_score REAL DEFAULT 0.0,
            keywords TEXT,
            entity_tags TEXT,
            analysis_note TEXT,
            risk_points TEXT,
            source_type TEXT DEFAULT 'manual',
            linked_thread_id INTEGER,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
        )
    """)
    print("[OK] evidence_facts 表创建成功")

    # 证据去重记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_duplicate_check (
            id TEXT PRIMARY KEY,
            case_id INTEGER NOT NULL,
            new_evidence_hash TEXT,
            new_filename TEXT,
            existing_evidence_id TEXT,
            file_hash_match INTEGER DEFAULT 0,
            content_similarity REAL DEFAULT 0.0,
            is_duplicate INTEGER DEFAULT 0,
            duplicate_status TEXT DEFAULT 'new',
            suggested_action TEXT,
            user_decision TEXT,
            confirmed_by TEXT,
            confirmed_at TIMESTAMP,
            confirmation_note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
        )
    """)
    print("[OK] evidence_duplicate_check 表创建成功")

    # 证据关键词索引表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_keyword_index (
            id TEXT PRIMARY KEY,
            case_id INTEGER NOT NULL,
            keyword TEXT NOT NULL,
            normalized_keyword TEXT,
            synonyms TEXT,
            evidence_ids TEXT,
            fact_ids TEXT,
            occurrence_count INTEGER DEFAULT 0,
            evidence_count INTEGER DEFAULT 0,
            is_auto_generated INTEGER DEFAULT 1,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
        )
    """)
    print("[OK] evidence_keyword_index 表创建成功")

    # ============ 对话系统 V2 表 ============

    # 对话会话表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_sessions (
            id TEXT PRIMARY KEY,
            case_id INTEGER NOT NULL,
            session_type TEXT DEFAULT 'qa',
            title TEXT,
            description TEXT,
            status TEXT DEFAULT 'active',
            is_pinned INTEGER DEFAULT 0,
            context_summary TEXT,
            key_entities TEXT,
            primary_intent TEXT,
            intent_confidence REAL DEFAULT 0.0,
            overall_clarity REAL DEFAULT 0.0,
            clarity_dimensions TEXT,
            message_count INTEGER DEFAULT 0,
            clarification_count INTEGER DEFAULT 0,
            final_answer TEXT,
            answer_type TEXT,
            confidence REAL DEFAULT 0.0,
            referenced_evidence_ids TEXT,
            suggested_evidence_ids TEXT,
            evidence_gaps TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_message_at TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
        )
    """)
    print("[OK] conversation_sessions 表创建成功")

    # 对话消息表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT DEFAULT 'text',
            entities TEXT,
            intent TEXT,
            referenced_evidence_ids TEXT,
            cited_sources TEXT,
            is_satisfactory INTEGER,
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES conversation_sessions (id) ON DELETE CASCADE
        )
    """)
    print("[OK] conversation_messages 表创建成功")

    # 澄清记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clarification_records (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            original_question TEXT NOT NULL,
            dimension TEXT,
            priority TEXT DEFAULT 'normal',
            reason TEXT,
            clarifying_questions TEXT,
            selected_question TEXT,
            status TEXT DEFAULT 'pending',
            user_answer TEXT,
            resolved_at TIMESTAMP,
            affects_answer INTEGER DEFAULT 1,
            impact_on_clarity REAL DEFAULT 0.0,
            is_auto_generated INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES conversation_sessions (id) ON DELETE CASCADE
        )
    """)
    print("[OK] clarification_records 表创建成功")

    # 问题分析表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS question_analyses (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            original_question TEXT NOT NULL,
            question_hash TEXT,
            intent TEXT,
            intent_confidence REAL DEFAULT 0.0,
            intent_reasoning TEXT,
            entities TEXT,
            relation_graph TEXT,
            ambiguous_entities TEXT,
            clarity_score REAL DEFAULT 0.0,
            dimension_scores TEXT,
            clarity_reasoning TEXT,
            clarification_needed INTEGER DEFAULT 0,
            clarification_dimensions TEXT,
            clarifying_questions TEXT,
            answer_type TEXT,
            answer_strategy TEXT,
            key_points_covered TEXT,
            evidence_gaps TEXT,
            suggested_evidence TEXT,
            confidence REAL DEFAULT 0.0,
            quality_score REAL DEFAULT 0.0,
            processing_time REAL DEFAULT 0.0,
            model_used TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES conversation_sessions (id) ON DELETE CASCADE
        )
    """)
    print("[OK] question_analyses 表创建成功")

    # ============ 报告系统 V2 表 ============

    # 报告大纲表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_outlines (
            id TEXT PRIMARY KEY,
            case_id INTEGER NOT NULL,
            report_type TEXT NOT NULL,
            title TEXT,
            description TEXT,
            total_sections INTEGER DEFAULT 0,
            completed_sections INTEGER DEFAULT 0,
            failed_sections INTEGER DEFAULT 0,
            status TEXT DEFAULT 'PLANNING',
            outline_data TEXT,
            metadata TEXT,
            generation_config TEXT,
            max_tokens_per_section INTEGER DEFAULT 4000,
            total_tokens INTEGER DEFAULT 0,
            processing_time REAL DEFAULT 0.0,
            error_message TEXT,
            version INTEGER DEFAULT 1,
            is_current INTEGER DEFAULT 1,
            previous_version_id TEXT,
            cached_content TEXT,
            cache_expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
        )
    """)
    print("[OK] report_outlines 表创建成功")

    # 报告章节表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_sections (
            id TEXT PRIMARY KEY,
            outline_id TEXT NOT NULL,
            section_index INTEGER NOT NULL,
            title TEXT NOT NULL,
            subtitle TEXT,
            content TEXT,
            summary TEXT,
            key_points TEXT,
            main_conclusions TEXT,
            source_evidence_ids TEXT,
            cited_laws TEXT,
            generation_prompt TEXT,
            model_response TEXT,
            tokens_used INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            confidence_score REAL DEFAULT 0.0,
            completeness_score REAL DEFAULT 0.0,
            dependencies TEXT,
            dependent_sections TEXT,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            last_retry_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (outline_id) REFERENCES report_outlines (id) ON DELETE CASCADE
        )
    """)
    print("[OK] report_sections 表创建成功")

    # 章节引用表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS section_references (
            id TEXT PRIMARY KEY,
            outline_id TEXT NOT NULL,
            source_section_id TEXT NOT NULL,
            target_section_id TEXT NOT NULL,
            reference_type TEXT DEFAULT 'cross_reference',
            reference_text TEXT,
            reference_context TEXT,
            source_position TEXT,
            target_position TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (outline_id) REFERENCES report_outlines (id) ON DELETE CASCADE
        )
    """)
    print("[OK] section_references 表创建成功")

    # 报告缓存表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_cache (
            id TEXT PRIMARY KEY,
            case_id INTEGER NOT NULL,
            cache_key TEXT NOT NULL UNIQUE,
            report_type TEXT NOT NULL,
            content TEXT,
            metadata TEXT,
            access_count INTEGER DEFAULT 0,
            last_accessed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            outline_id TEXT,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
        )
    """)
    print("[OK] report_cache 表创建成功")

    # ============ 创建索引 ============
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_v2_case ON evidence_items_v2(case_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_v2_hash ON evidence_items_v2(content_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_v2_type ON evidence_items_v2(evidence_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_v2_case ON evidence_relationships_v2(case_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_sess_case ON conversation_sessions(case_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_msg_sess ON conversation_messages(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clar_sess ON clarification_records(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_outline_case ON report_outlines(case_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_section_outline ON report_sections(outline_id)")
    print("[OK] 索引创建成功")

    conn.commit()
    conn.close()
    print("\n[SUCCESS] 证据系统V2、对话系统V2、报告系统V2 数据库表创建完成！")

    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cases'")
    if not cursor.fetchone():
        print("案件表不存在，跳过迁移")
        conn.close()
        return

    # ============ 创建函件表 ============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            direction TEXT NOT NULL,
            letter_type TEXT DEFAULT 'other',
            title TEXT NOT NULL,
            reference_number TEXT,
            sender TEXT,
            recipient TEXT,
            letter_date TIMESTAMP,
            received_date TIMESTAMP,
            deadline TIMESTAMP,
            responded_date TIMESTAMP,
            reply_required TEXT DEFAULT 'optional',
            reply_requirement_reason TEXT,
            response_deadline_days INTEGER,
            legal_basis TEXT,
            urgent_level TEXT DEFAULT 'none',
            is_overdue BOOLEAN DEFAULT 0,
            days_until_deadline INTEGER,
            content_summary TEXT,
            key_demands TEXT,
            risks TEXT,
            is_replied BOOLEAN DEFAULT 0,
            reply_content TEXT,
            reply_approved BOOLEAN,
            draft_reply TEXT,
            related_letter_id INTEGER,
            attachments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE,
            FOREIGN KEY (related_letter_id) REFERENCES letters (id)
        )
    """)
    print("[OK] letters 表创建成功")

    # ============ 创建法律期限表 ============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS legal_deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            deadline_type TEXT NOT NULL,
            deadline_name TEXT NOT NULL,
            deadline_category TEXT,
            legal_basis TEXT,
            duration_days INTEGER,
            description TEXT,
            start_date TIMESTAMP,
            deadline_date TIMESTAMP,
            extended_deadline TIMESTAMP,
            status TEXT DEFAULT 'pending',
            is_mandatory BOOLEAN DEFAULT 1,
            can_extend BOOLEAN DEFAULT 0,
            extension_days INTEGER,
            related_event TEXT,
            related_document_id INTEGER,
            ai_suggestions TEXT,
            risk_warning TEXT,
            completion_checklist TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
        )
    """)
    print("[OK] legal_deadlines 表创建成功")

    # ============ 创建里程碑模板表 ============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS milestone_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            case_type TEXT,
            milestones TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] milestone_templates 表创建成功")

    # ============ 创建案件时间线表 ============
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS case_timelines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_name TEXT NOT NULL,
            event_date TIMESTAMP NOT NULL,
            event_description TEXT,
            related_deadline_id INTEGER,
            related_letter_id INTEGER,
            related_document_id INTEGER,
            related_milestone_id INTEGER,
            importance TEXT DEFAULT 'normal',
            is_milestone BOOLEAN DEFAULT 0,
            ai_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE,
            FOREIGN KEY (related_deadline_id) REFERENCES legal_deadlines (id),
            FOREIGN KEY (related_letter_id) REFERENCES letters (id)
        )
    """)
    print("[OK] case_timelines 表创建成功")

    # ============ 为 cases 表添加新的关系字段 ============
    # 注意：这些字段通过关系表关联，不需要直接添加列

    # ============ 出庭抗辩辅助相关表 ============

    # 庭审记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hearing_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            hearing_type TEXT DEFAULT 'first_trial',
            hearing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            location TEXT,
            case_number TEXT,
            status TEXT DEFAULT 'preparing',
            current_phase TEXT,
            is_live BOOLEAN DEFAULT 0,
            participants TEXT,
            full_transcript TEXT,
            key_points TEXT,
            traps_detected TEXT,
            evidence_timing_suggestions TEXT,
            overall_strategy_evaluation TEXT,
            live_suggestions TEXT,
            current_recommendation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
        )
    """)
    print("[OK] hearing_records 表创建成功")

    # 庭审发言记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hearing_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER NOT NULL,
            statement_type TEXT DEFAULT 'statement',
            speaker_role TEXT NOT NULL,
            speaker_name TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sequence INTEGER DEFAULT 0,
            content TEXT NOT NULL,
            original_content TEXT,
            is_trap BOOLEAN DEFAULT 0,
            trap_type TEXT,
            trap_description TEXT,
            target_statement_id INTEGER,
            suggested_response TEXT,
            response_strategy TEXT,
            related_evidence_ids TEXT,
            emotional_tone TEXT,
            is_hostile BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (record_id) REFERENCES hearing_records (id) ON DELETE CASCADE
        )
    """)
    print("[OK] hearing_statements 表创建成功")

    # 证据使用记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_uses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER NOT NULL,
            evidence_name TEXT NOT NULL,
            evidence_document_id INTEGER,
            presented_by TEXT NOT NULL,
            timing TEXT DEFAULT 'wait_better_moment',
            suggested_timing TEXT,
            actual_timing TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason_for_timing TEXT,
            impact_score REAL,
            was_effective BOOLEAN,
            effect_description TEXT,
            context TEXT,
            opposing_reaction TEXT,
            judge_reaction TEXT,
            ai_analysis TEXT,
            improvement_suggestions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (record_id) REFERENCES hearing_records (id) ON DELETE CASCADE
        )
    """)
    print("[OK] evidence_uses 表创建成功")

    # 庭审预警表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hearing_warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER NOT NULL,
            warning_type TEXT NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            details TEXT,
            related_statement_id INTEGER,
            related_evidence_id INTEGER,
            urgency TEXT DEFAULT 'medium',
            auto_dismiss BOOLEAN DEFAULT 1,
            dismiss_after_seconds INTEGER DEFAULT 30,
            is_read BOOLEAN DEFAULT 0,
            is_dismissed BOOLEAN DEFAULT 0,
            dismissed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (record_id) REFERENCES hearing_records (id) ON DELETE CASCADE
        )
    """)
    print("[OK] hearing_warnings 表创建成功")

    # 说话指南表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS speaking_guides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            applicable_situations TEXT,
            speaker_roles TEXT,
            description TEXT,
            what_to_say TEXT,
            what_not_to_say TEXT,
            key_points TEXT,
            templates TEXT,
            expected_effect TEXT,
            risks TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] speaking_guides 表创建成功")

    # 案件专属说话策略表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS case_speaking_strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            opening_statement TEXT,
            key_arguments TEXT,
            evidence_presentation_order TEXT,
            anticipated_opposing_arguments TEXT,
            responses_to_opposing_arguments TEXT,
            forbidden_statements TEXT,
            risky_statements TEXT,
            timing_guidance TEXT,
            phase_strategies TEXT,
            is_approved BOOLEAN DEFAULT 0,
            version TEXT DEFAULT '1.0',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
        )
    """)
    print("[OK] case_speaking_strategies 表创建成功")

    # ============ 上诉流程相关表 ============

    # 上诉记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appeal_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            appeal_type TEXT DEFAULT 'first_to_second',
            appeal_reason TEXT DEFAULT 'legal_error',
            original_case_number TEXT,
            original_court TEXT,
            original_judge TEXT,
            original_judgment_date TIMESTAMP,
            original_judgment_content TEXT,
            appellant_type TEXT,
            appellant_name TEXT,
            judgment_received_date TIMESTAMP,
            appeal_deadline TIMESTAMP,
            appeal_submitted_date TIMESTAMP,
            appeal_accepted_date TIMESTAMP,
            hearing_date TIMESTAMP,
            appeal_decision_date TIMESTAMP,
            status TEXT DEFAULT 'preparing',
            days_remaining INTEGER,
            is_overdue BOOLEAN DEFAULT 0,
            appeal_petition TEXT,
            appeal_facts TEXT,
            new_evidence_list TEXT,
            original_evidence_used TEXT,
            appeal_requests TEXT,
            original_requests TEXT,
            modified_requests TEXT,
            grounds_of_appeal TEXT,
            opposing_arguments TEXT,
            key_disputes TEXT,
            strategy TEXT,
            key_arguments TEXT,
            evidence_plan TEXT,
            milestones TEXT,
            decision TEXT,
            decision_type TEXT,
            favorable_outcome BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
        )
    """)
    print("[OK] appeal_records 表创建成功")

    # 上诉期限表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appeal_deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appeal_record_id INTEGER NOT NULL,
            deadline_type TEXT NOT NULL,
            deadline_name TEXT NOT NULL,
            deadline_date TIMESTAMP,
            description TEXT,
            legal_basis TEXT,
            status TEXT DEFAULT 'pending',
            days_remaining INTEGER,
            is_mandatory BOOLEAN DEFAULT 1,
            reminder_days TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appeal_record_id) REFERENCES appeal_records (id) ON DELETE CASCADE
        )
    """)
    print("[OK] appeal_deadlines 表创建成功")

    # 上诉论点表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appeal_arguments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appeal_record_id INTEGER NOT NULL,
            argument_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            original_finding TEXT,
            appeal_finding TEXT,
            discrepancy TEXT,
            supporting_evidence TEXT,
            counter_evidence TEXT,
            legal_basis TEXT,
            reasoning TEXT,
            expected_opposition TEXT,
            counter_response TEXT,
            importance TEXT DEFAULT 'medium',
            success_probability REAL,
            is_key_argument BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'draft',
            ai_suggestions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appeal_record_id) REFERENCES appeal_records (id) ON DELETE CASCADE
        )
    """)
    print("[OK] appeal_arguments 表创建成功")

    # 上诉材料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appeal_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appeal_record_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            document_name TEXT NOT NULL,
            description TEXT,
            source TEXT,
            status TEXT DEFAULT 'pending',
            is_required BOOLEAN DEFAULT 1,
            related_document_id INTEGER,
            purpose TEXT,
            content_summary TEXT,
            key_points TEXT,
            ai_summary TEXT,
            ai_suggestions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appeal_record_id) REFERENCES appeal_records (id) ON DELETE CASCADE
        )
    """)
    print("[OK] appeal_documents 表创建成功")

    # 二审答辩策略表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS second_trial_strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appeal_record_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            target_arguments TEXT,
            defense_points TEXT,
            defense_reasoning TEXT,
            supporting_evidence TEXT,
            counter_evidence TEXT,
            legal_basis TEXT,
            expected_outcome TEXT,
            favorable_arguments TEXT,
            is_approved BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appeal_record_id) REFERENCES appeal_records (id) ON DELETE CASCADE
        )
    """)
    print("[OK] second_trial_strategies 表创建成功")

    conn.commit()
    conn.close()
    print("\n[SUCCESS] 上诉流程相关表创建完成！")

    # ============ 战役模型 case_claims ============
    print("\n[INFO] 开始创建战役表...")
    
    # 确保连接仍然打开
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
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
        )
    """)
    print("[OK] case_claims 表创建成功")
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_case_claims_case_id ON case_claims(case_id)')
    print("[OK] case_claims 索引创建成功")
    
    # 检查 generated_documents 表是否有新字段
    cursor.execute("PRAGMA table_info(generated_documents)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    if 'claim_id' not in existing_columns:
        cursor.execute('ALTER TABLE generated_documents ADD COLUMN claim_id INTEGER')
        print("[OK] generated_documents 添加 claim_id 字段")
    
    if 'campaign_goal' not in existing_columns:
        cursor.execute('ALTER TABLE generated_documents ADD COLUMN campaign_goal VARCHAR(500)')
        print("[OK] generated_documents 添加 campaign_goal 字段")
    
    if 'used_evidence_ids' not in existing_columns:
        cursor.execute("ALTER TABLE generated_documents ADD COLUMN used_evidence_ids TEXT DEFAULT '[]'")
        print("[OK] generated_documents 添加 used_evidence_ids 字段")
    
    conn.commit()
    conn.close()
    print("\n[SUCCESS] 战役表创建完成！")


if __name__ == "__main__":
    migrate()
