# -*- coding: utf-8 -*-
"""
同步证据内容到文档表
将EvidenceItem中的OCR内容同步到Document表
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')

from app.db.database import SessionLocal
from app.models.document import Document
from app.models.evidence import EvidenceItem

def sync_evidence_to_documents():
    """将证据内容同步到文档表"""
    db = SessionLocal()

    try:
        # 获取所有证据
        evidences = db.query(EvidenceItem).filter(
            EvidenceItem.is_current == True
        ).all()

        print(f"\n{'='*60}")
        print(f"开始同步 {len(evidences)} 个证据到文档表...")
        print(f"{'='*60}\n")

        success = 0
        skipped = 0
        errors = 0

        for ev in evidences:
            # 查找对应的文档
            doc = db.query(Document).filter(
                Document.case_id == ev.case_id,
                Document.filename == ev.original_filename
            ).first()

            if not doc:
                # 尝试按文件名模糊匹配
                docs = db.query(Document).filter(
                    Document.case_id == ev.case_id,
                    Document.filename.like(f'%{ev.original_filename[:20]}%')
                ).all()
                if docs:
                    doc = docs[0]

            if not doc:
                print(f"[跳过] {ev.original_filename} - 未找到对应文档")
                skipped += 1
                continue

            # 检查证据是否有有效内容
            has_content = (
                ev.extracted_content and
                len(ev.extracted_content) > 100 and
                not ev.extracted_content.startswith('[PDF') and
                not ev.extracted_content.startswith('[扫描件') and
                '识别失败' not in ev.extracted_content
            )

            if not has_content:
                print(f"[跳过] {ev.original_filename} - 证据内容无效")
                skipped += 1
                continue

            # 检查文档内容是否需要更新
            doc_needs_update = (
                not doc.content or
                len(doc.content) < 100 or
                doc.content.startswith('[PDF') or
                '识别失败' in doc.content or
                doc.content.startswith('[扫描件')
            )

            if not doc_needs_update:
                print(f"[已有] {ev.original_filename} - 文档内容已有效")
                skipped += 1
                continue

            # 更新文档内容
            try:
                doc.content = ev.extracted_content
                doc.content_summary = ev.summary or ev.extracted_content[:500]

                # 更新doc_type
                type_map = {
                    'CONTRACT': '合同',
                    'CORRESPONDENCE': '函件',
                    'PAYMENT': '支付凭证',
                    'IDENTITY': '身份证明',
                    'AUDIO_VIDEO': '视听资料',
                    'DOCUMENT': '书证',
                    'OTHER': '其他'
                }
                if ev.evidence_type:
                    doc.doc_type = type_map.get(ev.evidence_type, ev.evidence_type)

                db.commit()
                print(f"[更新] {ev.original_filename} - {len(ev.extracted_content)}字符")
                success += 1

            except Exception as e:
                db.rollback()
                print(f"[错误] {ev.original_filename} - {str(e)}")
                errors += 1

        print(f"\n{'='*60}")
        print(f"同步完成！成功: {success} | 跳过: {skipped} | 错误: {errors}")
        print(f"{'='*60}\n")

        # 验证结果
        print("验证同步结果...")
        docs = db.query(Document).filter(Document.case_id == 21).all()
        valid_count = 0
        for d in docs:
            if d.content and len(d.content) > 100 and not d.content.startswith('[PDF') and '识别失败' not in d.content:
                valid_count += 1
        print(f"案件21文档: {valid_count}/{len(docs)} 有有效内容")

    finally:
        db.close()

if __name__ == "__main__":
    sync_evidence_to_documents()
