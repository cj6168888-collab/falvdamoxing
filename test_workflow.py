import requests
import json

BASE_URL = "http://localhost:8002"

def test_apis():
    print("=" * 60)
    print("API 测试脚本")
    print("=" * 60)
    
    # 1. 健康检查
    print("\n[1] 健康检查")
    r = requests.get(f"{BASE_URL}/health")
    print(f"  状态: {r.status_code} - {r.json()}")
    
    # 2. 获取案件列表
    print("\n[2] 获取案件列表")
    r = requests.get(f"{BASE_URL}/api/cases")
    print(f"  状态: {r.status_code}")
    if r.status_code == 200:
        cases = r.json()
        print(f"  案件数量: {len(cases) if isinstance(cases, list) else 'N/A'}")
        if cases and len(cases) > 0:
            case_id = cases[0].get('id')
            print(f"  测试用案件ID: {case_id}")
        else:
            case_id = 1
            print(f"  无案件，使用默认ID: {case_id}")
    else:
        print(f"  错误: {r.text[:200]}")
        case_id = 1
    
    # 3. 获取案件详情
    print(f"\n[3] 获取案件 {case_id} 详情")
    r = requests.get(f"{BASE_URL}/api/cases/{case_id}")
    print(f"  状态: {r.status_code}")
    if r.status_code == 200:
        case = r.json()
        print(f"  案件名: {case.get('title', 'N/A')}")
        print(f"  原告: {case.get('plaintiff', 'N/A')}")
        print(f"  被告: {case.get('defendant', 'N/A')}")
    
    # 4. 获取战役列表
    print(f"\n[4] 获取战役列表")
    r = requests.get(f"{BASE_URL}/api/claims/case/{case_id}")
    print(f"  状态: {r.status_code}")
    if r.status_code == 200:
        claims = r.json()
        print(f"  战役数量: {len(claims)}")
        for c in claims:
            print(f"    - {c.get('title')} ({c.get('status')})")
    
    # 5. 案情分析测试
    print(f"\n[5] 案情分析测试")
    test_data = {
        "case_id": case_id,
        "user_message": "对方欠我10万元，有借条和转账记录，要求对方还款并支付违约金",
        "chat_history": []
    }
    r = requests.post(f"{BASE_URL}/api/smart-chat/case-analysis", json=test_data)
    print(f"  状态: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        print(f"  分析类型: {result.get('analysis_type')}")
        print(f"  响应: {result.get('response', '')[:100]}...")
        print(f"  建议战役: {len(result.get('suggested_claims', []))}个")
    else:
        print(f"  错误: {r.text[:300]}")
    
    # 6. 获取证据列表
    print(f"\n[6] 获取证据列表")
    r = requests.get(f"{BASE_URL}/api/evidence/case/{case_id}")
    print(f"  状态: {r.status_code}")
    if r.status_code == 200:
        evidence = r.json()
        print(f"  证据数量: {len(evidence) if isinstance(evidence, list) else 'N/A'}")
    
    # 7. 获取已生成文书
    print(f"\n[7] 获取已生成文书")
    r = requests.get(f"{BASE_URL}/api/document-management/case/{case_id}/generated")
    print(f"  状态: {r.status_code}")
    if r.status_code == 200:
        docs = r.json()
        print(f"  文书数量: {len(docs) if isinstance(docs, list) else 'N/A'}")
    
    # 8. 生成文书测试
    print(f"\n[8] 生成文书测试")
    doc_data = {
        "case_id": case_id,
        "document_type": "起诉状",
        "claim_id": None
    }
    r = requests.post(f"{BASE_URL}/api/smart-chat/generate-document", json=doc_data)
    print(f"  状态: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        print(f"  文书ID: {result.get('document_id')}")
        print(f"  证据数: {result.get('evidence_count')}")
        print(f"  消息: {result.get('message', '')[:50]}...")
    else:
        print(f"  错误: {r.text[:200]}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_apis()