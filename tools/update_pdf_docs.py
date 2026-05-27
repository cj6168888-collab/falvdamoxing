# -*- coding: utf-8 -*-
"""
批量更新所有PDF证据的文档内容
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')

from app.db.database import SessionLocal
from app.models.document import Document
from app.models.evidence import EvidenceItem

def update_all_pdf_documents():
    """更新所有PDF证据到文档表"""
    db = SessionLocal()

    try:
        # 获取所有PDF证据
        pdf_evidences = db.query(EvidenceItem).filter(
            EvidenceItem.is_current == True,
            EvidenceItem.original_filename.like('%.pdf%')
        ).all()

        print(f"\n{'='*60}")
        print(f"更新 {len(pdf_evidences)} 个PDF证据到文档表...")
        print(f"{'='*60}\n")

        success = 0
        skipped = 0
        errors = 0

        # 类型映射
        type_map = {
            'CONTRACT': '合同',
            'CORRESPONDENCE': '函件',
            'PAYMENT': '支付凭证',
            'IDENTITY': '身份证明',
            'AUDIO_VIDEO': '视听资料',
            'DOCUMENT': '书证',
            'OTHER': '其他'
        }

        for ev in pdf_evidences:
            # 查找对应文档
            doc = db.query(Document).filter(
                Document.case_id == ev.case_id,
                Document.filename == ev.original_filename
            ).first()

            if not doc:
                print(f"[跳过] {ev.original_filename} - 未找到文档")
                skipped += 1
                continue

            # 检查证据是否有有效OCR内容
            if not ev.extracted_content or len(ev.extracted_content) < 100:
                print(f"[跳过] {ev.original_filename} - 无OCR内容")
                skipped += 1
                continue

            try:
                # 检查是否需要更新
                needs_update = (
                    not doc.content or
                    '[PDF文档]' in doc.content or
                    '识别失败' in doc.content or
                    doc.content.startswith('[扫描件')
                )

                if not needs_update:
                    print(f"[已有] {ev.original_filename} - 内容有效")
                    skipped += 1
                    continue

                # 更新文档内容
                doc.content = ev.extracted_content
                doc.content_summary = ev.summary or ev.extracted_content[:500]
                if ev.evidence_type:
                    doc.doc_type = type_map.get(ev.evidence_type, '其他')

                db.commit()
                print(f"[更新] {ev.original_filename} - {len(ev.extracted_content)}字符")
                success += 1

            except Exception as e:
                db.rollback()
                print(f"[错误] {ev.original_filename} - {str(e)}")
                errors += 1

        print(f"\n{'='*60}")
        print(f"更新完成！成功: {success} | 跳过: {skipped} | 错误: {errors}")
        print(f"{'='*60}\n")

        # 验证结果
        print("验证PDF文档...")
        pdf_docs = db.query(Document).filter(
            Document.case_id == 21,
            Document.filename.like('%.pdf%')
        ).all()

        valid_count = 0
        for d in pdf_docs:
            if d.content and '[PDF文档]' not in d.content and '识别失败' not in d.content:
                valid_count += 1
                print(f"  ✅ {d.filename}: {len(d.content)}字符")
            else:
                print(f"  ⚠️ {d.filename}: 内容无效")

        print(f"\nPDF文档有效: {valid_count}/{len(pdf_docs)}")

    finally:
        db.close()

if __name__ == "__main__":
    update_all_pdf_documents()
