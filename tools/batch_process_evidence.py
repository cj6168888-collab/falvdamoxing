# -*- coding: utf-8 -*-
"""
批量处理所有证据 - 上传时自动分析
对案件21的所有证据进行完整的分析处理
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')

from app.db.database import SessionLocal
from app.models.evidence import EvidenceItem, EvidenceStatus
from app.services.evidence_v2 import evidence_service_v2

def process_all_evidence(case_id=None):
    """处理所有未完整分析的证据"""
    db = SessionLocal()

    try:
        # 查询所有证据
        query = db.query(EvidenceItem).filter(EvidenceItem.is_current == True)
        if case_id:
            query = query.filter(EvidenceItem.case_id == case_id)

        evidences = query.all()
        total = len(evidences)

        print(f"\n{'='*60}")
        print(f"开始处理 {total} 个证据...")
        print(f"{'='*60}\n")

        success_count = 0
        skip_count = 0

        for i, evidence in enumerate(evidences, 1):
            print(f"[{i}/{total}] 处理: {evidence.original_filename}")

            # 检查是否已有完整分析
            has_analysis = (
                evidence.evidence_type and
                evidence.credibility_score and
                evidence.credibility_score > 0
            )

            if has_analysis:
                print(f"  ✅ 已有分析，跳过")
                skip_count += 1
                continue

            # 跳过完全没有内容的证据
            if not evidence.extracted_content and not evidence.raw_content:
                print(f"  ⚠️ 无内容，跳过")
                skip_count += 1
                continue

            try:
                # 调用完整的证据处理流程
                result = evidence_service_v2.process_evidence(
                    case_id=evidence.case_id,
                    source_type=evidence.source_type,
                    content=evidence.extracted_content or evidence.raw_content,
                    file_path=evidence.file_path,
                    original_filename=evidence.original_filename,
                    source_party=evidence.source_party
                )

                if result.get('status') == 'success':
                    cls = result.get('classification', {})
                    kw = result.get('keywords', {})
                    print(f"  ✅ 完成 - 分类:{cls.get('type','N/A')} | 关键词:{len(kw.get('keywords',[]))}个")
                    success_count += 1
                elif result.get('status') == 'duplicate':
                    print(f"  ⚠️ 重复证据，跳过")
                    skip_count += 1
                else:
                    print(f"  ❌ 处理失败: {result.get('message', '未知错误')}")

            except Exception as e:
                print(f"  ❌ 异常: {str(e)}")

        print(f"\n{'='*60}")
        print(f"处理完成！成功: {success_count} | 跳过: {skip_count} | 总计: {total}")
        print(f"{'='*60}\n")

        return success_count

    finally:
        db.close()


def process_single_evidence(evidence_id):
    """处理单个证据"""
    db = SessionLocal()

    try:
        evidence = db.query(EvidenceItem).filter(
            EvidenceItem.id == evidence_id,
            EvidenceItem.is_current == True
        ).first()

        if not evidence:
            print(f"未找到证据: {evidence_id}")
            return None

        print(f"\n处理证据: {evidence.original_filename}")
        print(f"文件路径: {evidence.file_path}")
        print(f"内容长度: {len(evidence.extracted_content) if evidence.extracted_content else 0}")

        result = evidence_service_v2.process_evidence(
            case_id=evidence.case_id,
            source_type=evidence.source_type,
            content=evidence.extracted_content or evidence.raw_content,
            file_path=evidence.file_path,
            original_filename=evidence.original_filename,
            source_party=evidence.source_party
        )

        if result.get('status') == 'success':
            print(f"\n✅ 分析完成!")
            print(f"证据ID: {result['evidence']['id']}")
            print(f"分类: {result['classification']['type']}")
            print(f"关键词: {', '.join(result['keywords']['keywords'][:10])}...")

            # 显示摘要
            ev = result['evidence']
            print(f"\n摘要: {ev.get('summary', '')[:200]}...")

        return result

    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("📋 证据批量分析系统")
    print("="*60)
    print("\n1. 处理案件21的所有证据")
    print("2. 处理所有案件的证据")
    print("3. 处理单个证据（需要输入ID）")

    # 默认处理案件21
    print("\n正在处理案件21的所有证据...\n")
    process_all_evidence(case_id=21)
