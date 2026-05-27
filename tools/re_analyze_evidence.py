# -*- coding: utf-8 -*-
"""
重新分析所有未完成分类的证据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')

from app.db.database import SessionLocal
from app.models.evidence import EvidenceItem

def analyze_all_evidence():
    """分析所有证据"""
    db = SessionLocal()

    try:
        # 查找所有证据
        all_evidence = db.query(EvidenceItem).filter(
            EvidenceItem.is_current == True
        ).all()

        total = len(all_evidence)
        print(f"\n{'='*60}")
        print(f"重新分析所有 {total} 个证据...")
        print(f"{'='*60}\n")

        from app.services.evidence_v2 import evidence_service_v2

        success = 0
        skipped = 0
        errors = 0

        for i, ev in enumerate(all_evidence, 1):
            # 强制刷新所有证据以确保内容是最新的
            force = True

            print(f"[{i}/{total}] 分析: {ev.original_filename}")

            try:
                result = evidence_service_v2.analyze_evidence(
                    evidence_id=ev.id,
                    force_refresh=True  # 强制刷新
                )

                if result.get('status') == 'success':
                    print(f"  ✅ 完成 - 类型:{result.get('classification',{}).get('type')} | 关键词:{len(result.get('keywords',[]))}个")
                    success += 1
                else:
                    print(f"  ⚠️ {result.get('message', '未知')}")
                    errors += 1

            except Exception as e:
                print(f"  ❌ 错误: {str(e)}")
                errors += 1

        print(f"\n{'='*60}")
        print(f"完成！成功: {success} | 跳过: {skipped} | 错误: {errors} | 总计: {total}")
        print(f"{'='*60}\n")

        # 验证结果
        print("\n验证分析结果...")
        with_type = db.query(EvidenceItem).filter(
            EvidenceItem.is_current == True,
            EvidenceItem.evidence_type.isnot(None)
        ).count()

        with_keywords = db.query(EvidenceItem).filter(
            EvidenceItem.is_current == True,
            EvidenceItem.keywords.isnot(None)
        ).count()

        print(f"已分类: {with_type}/{total}")
        print(f"有关键词: {with_keywords}/{total}")

    finally:
        db.close()

if __name__ == "__main__":
    analyze_all_evidence()
