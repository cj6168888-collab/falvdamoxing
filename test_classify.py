"""测试证据分类"""
import sys
sys.path.insert(0, '.')

from app.services.evidence_v2 import EvidenceServiceV2

# 创建服务实例
service = EvidenceServiceV2()

# 测试内容
test_content = """
致：XX公司
关于：XX合同履行通知

贵司与我司于2025年7月23日签订了《合作协议》，约定我司向贵司提供法律服务。

根据合同约定，贵司应于2026年3月5日前支付服务费用6000元，但贵司至今未支付。

请贵司在收到本函后5日内支付欠款，否则我司将采取法律行动追究违约责任。

此致
XX律师事务所
2026年3月11日
"""

print("测试证据分类...")
result = service._classify_evidence_sync(test_content, 1)
print(f"分类结果: {result}")