"""
迁移脚本：将 documents 表中的证据数据迁移到 evidence_items_v2 表

问题根因：
- 前端调用 V2 API（查询 evidence_items_v2 表），但该表为空
- 实际证据数据在 documents 表（161条记录）
- 上传流程只创建 Document 记录，从未创建 EvidenceItem 记录

此脚本：
1. 从 documents 表读取所有证据类文档
2. 去重（同一文件多次上传只保留一条）
3. 创建对应的 EvidenceItem 记录
4. 自动分类、提取关键词、生成摘要
"""
import sys
import os
import hashlib
import re
import uuid

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.models.document import Document
from app.models.evidence import (
    EvidenceItem, EvidenceSourceType, EvidenceSourceParty, EvidenceStatus
)
from app.services.evidence_v2 import EvidenceServiceV2


def doc_type_to_source_party(doc_type: str) -> str:
    """根据文档类型判断来源方"""
    if not doc_type:
        return EvidenceSourceParty.OUR_SIDE.value
    if "对方" in doc_type or "被告" in doc_type:
        return EvidenceSourceParty.OPPONENT.value
    if "法院" in doc_type or "裁定" in doc_type:
        return EvidenceSourceParty.COURT.value
    return EvidenceSourceParty.OUR_SIDE.value


def doc_type_to_evidence_type(doc_type: str) -> str:
    """将文档类型映射到证据类型"""
    if not doc_type:
        return "OTHER"
    mapping = {
        "合同": "CONTRACT",
        "协议": "CONTRACT",
        "函件": "CORRESPONDENCE",
        "律师函": "CORRESPONDENCE",
        "发票": "PAYMENT",
        "收据": "PAYMENT",
        "转账": "PAYMENT",
        "身份证": "IDENTITY",
        "营业执照": "IDENTITY",
        "录音": "AUDIO_VIDEO",
        "录像": "AUDIO_VIDEO",
        "判决": "DOCUMENT",
        "裁定": "DOCUMENT",
    }
    for key, ev_type in mapping.items():
        if key in doc_type:
            return ev_type
    return "OTHER"


def migrate_documents(case_id: int = None):
    """
    迁移证据数据
    
    Args:
        case_id: 如果指定，只迁移该案件的证据；否则迁移所有
    """
    db = SessionLocal()
    service = EvidenceServiceV2()
    
    try:
        # 查询需要迁移的文档
        query = db.query(Document)
        if case_id:
            query = query.filter(Document.case_id == case_id)
        
        docs = query.all()
        print(f"找到 {len(docs)} 个文档记录")
        
        # 过滤出证据类文档
        evidence_doc_types = ["证据", "合同", "函件", "章程", "协议"]
        evidence_docs = []
        for doc in docs:
            if doc.doc_type:
                is_evidence = any(t in doc.doc_type for t in evidence_doc_types)
                if is_evidence:
                    evidence_docs.append(doc)
        
        print(f"其中 {len(evidence_docs)} 个是证据类文档")
        
        # 按文件路径去重
        seen_paths = set()
        unique_docs = []
        for doc in evidence_docs:
            if doc.stored_path and doc.stored_path not in seen_paths:
                seen_paths.add(doc.stored_path)
                unique_docs.append(doc)
            elif not doc.stored_path:
                # 没有存储路径的也保留（可能是手动录入的）
                unique_docs.append(doc)
        
        print(f"去重后 {len(unique_docs)} 个唯一证据")
        
        # 检查已存在的证据记录（避免重复迁移）
        existing_evidence = db.query(EvidenceItem).filter(
            EvidenceItem.case_id == (case_id if case_id else unique_docs[0].case_id if unique_docs else 0),
            EvidenceItem.is_current == True
        ).all()
        
        # 构建已存在的文件路径集合
        existing_paths = {e.file_path for e in existing_evidence if e.file_path}
        print(f"已存在 {len(existing_paths)} 条证据记录")
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        for doc in unique_docs:
            try:
                # 跳过已迁移的
                if doc.stored_path in existing_paths:
                    skipped_count += 1
                    continue
                
                # 检查文件是否存在
                file_exists = doc.stored_path and os.path.exists(doc.stored_path)
                
                # 提取内容
                content = doc.content or ""
                
                # 创建 EvidenceItem
                evidence = EvidenceItem(
                    id=str(uuid.uuid4()),
                    case_id=doc.case_id,
                    source_type=EvidenceSourceType.FILE.value,
                    original_filename=doc.filename,
                    file_path=doc.stored_path if file_exists else None,
                    raw_content=content,
                    extracted_content=content if len(content) > 50 else "",
                    source_party=doc_type_to_source_party(doc.doc_type),
                    evidence_type=doc_type_to_evidence_type(doc.doc_type),
                    status=EvidenceStatus.PROCESSED.value,
                    file_size=doc.file_size,
                    processed_at=doc.created_at,
                )
                
                # 生成内容哈希
                if content:
                    evidence.generate_content_hash()
                
                # 生成文件哈希
                if file_exists:
                    evidence.generate_file_hash()
                
                # 生成摘要
                evidence.summary = service._generate_summary(content) if content else doc.content_summary or ""
                
                # 分类
                if content:
                    classification = service._classify_evidence_sync(content, doc.case_id)
                    evidence.evidence_type = classification['type']
                    evidence.proves_facts = classification['facts']
                    
                    # 关键词提取
                    keywords_result = service._extract_keywords_sync(content)
                    evidence.keywords = keywords_result['keywords']
                    evidence.entity_tags = keywords_result['entities']
                
                db.add(evidence)
                migrated_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"  迁移失败 [{doc.filename}]: {e}")
        
        db.commit()
        
        print(f"\n迁移完成:")
        print(f"  成功: {migrated_count}")
        print(f"  跳过: {skipped_count}")
        print(f"  失败: {error_count}")
        
        # 验证
        final_count = db.query(EvidenceItem).filter(
            EvidenceItem.case_id == (case_id if case_id else 1),
            EvidenceItem.is_current == True
        ).count()
        print(f"\n案件 {case_id or 1} 现在共有 {final_count} 条证据记录")
        
        return {
            "migrated": migrated_count,
            "skipped": skipped_count,
            "errors": error_count
        }
        
    except Exception as e:
        db.rollback()
        print(f"迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
    finally:
        db.close()


if __name__ == "__main__":
    case_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if case_id:
        print(f"开始迁移案件 {case_id} 的证据...")
    else:
        print("开始迁移所有证据...")
    
    result = migrate_documents(case_id)
    
    if "error" in result:
        print(f"\n迁移失败: {result['error']}")
        sys.exit(1)
    else:
        print("\n迁移成功！")
