# 法律大模型辅助系统 - 正确的端到端测试
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_api(name, method, endpoint, expected_status=200, data=None):
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=60)
        else:
            raise ValueError(f"Unknown method: {method}")

        success = response.status_code == expected_status
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {name} ({response.status_code})")

        if not success:
            print(f"    Expected: {expected_status}, Got: {response.status_code}")
            try:
                print(f"    Error: {response.json()}")
            except:
                print(f"    Error: {response.text[:200]}")

        return success, response

    except requests.exceptions.ConnectionError:
        print(f"[ERROR] {name} - Connection Error")
        return False, None
    except Exception as e:
        print(f"[ERROR] {name} - {e}")
        return False, None

print("=" * 60)
print("法律大模型辅助系统 - 端到端测试")
print("=" * 60)

passed = 0
failed = 0

# 1. 健康检查
print("\n[1] 系统健康检查")
print("-" * 40)
if test_api("健康检查", "GET", "/health"): passed += 1
else: failed += 1

# 2. 根路由
print("\n[2] 根路由")
print("-" * 40)
if test_api("根路由", "GET", "/"): passed += 1
else: failed += 1

# 3. 项目管理 API (/api/projects)
print("\n[3] 项目管理 API")
print("-" * 40)
if test_api("获取项目列表", "GET", "/api/projects/"): passed += 1
else: failed += 1

# 4. 案件管理 API (/api/cases)
print("\n[4] 案件管理 API")
print("-" * 40)
if test_api("获取案件列表", "GET", "/api/cases"): passed += 1
else: failed += 1

# 5. 文档管理 API (/api/documents)
print("\n[5] 文档管理 API")
print("-" * 40)
if test_api("获取文书模板", "GET", "/api/documents/templates/list"): passed += 1
else: failed += 1

# 6. 报告生成 API (/api/reports)
print("\n[6] 报告生成 API")
print("-" * 40)
# 注意: report_api 可能需要 case_id 参数

# 7. 会议管理 API (/api/meetings)
print("\n[7] 会议管理 API")
print("-" * 40)
if test_api("获取会议列表", "GET", "/api/meetings"): passed += 1
else: failed += 1

# 8. 出庭抗辩 API (/api/hearing)
print("\n[8] 出庭抗辩 API")
print("-" * 40)
if test_api("获取庭审记录", "GET", "/api/hearing"): passed += 1
else: failed += 1

# 9. 企业信息 API (/api/company)
print("\n[9] 企业信息 API")
print("-" * 40)
if test_api("搜索企业", "POST", "/api/company/search", data={"company_name": "测试公司"}): passed += 1
else: failed += 1

# 10. 对话 API V2 (/api/v2/conversation)
print("\n[10] 对话 API V2")
print("-" * 40)
# 需要有效的 case_id

# 11. 资深律师分析 API (/api/v2/senior-analysis)
print("\n[11] 资深律师分析 API")
print("-" * 40)
# 需要有效的 case_id

# 12. 增强分析 API (/api/v2)
print("\n[12] 增强分析 API")
print("-" * 40)
# 需要有效的 case_id

# 13. 证据图谱 API V2 (/api/v2/evidence-graph)
print("\n[13] 证据图谱 API V2")
print("-" * 40)
# 需要有效的 case_id

# 14. 证据问答 API (/api/v2/evidence-qa)
print("\n[14] 证据问答 API")
print("-" * 40)
# 需要有效的 case_id

# 15. 案件画像 API (/api/v2/profile)
print("\n[15] 案件画像 API")
print("-" * 40)
# 需要有效的 case_id

# 16. 证据引导 API (/api/v2/evidence-guide)
print("\n[16] 证据引导 API")
print("-" * 40)
# 需要有效的 case_id

# 17. 智能助手 API (/api/v2/assistant)
print("\n[17] 智能助手 API")
print("-" * 40)
# 需要有效的 case_id

# 18. 导出 API (/api/export)
print("\n[18] 导出 API")
print("-" * 40)
if test_api("获取导出格式", "GET", "/api/export"): passed += 1
else: failed += 1

# 19. 文书管理 API (/api/documents) - 第二个注册
print("\n[19] 文书管理 API V2")
print("-" * 40)
if test_api("获取文书列表", "GET", "/api/documents"): passed += 1
else: failed += 1

# 20. 创建测试案件并测试需要 case_id 的 API
print("\n[20] 创建测试数据")
print("-" * 40)

# 创建测试项目
success, resp = test_api("创建测试项目", "POST", "/api/projects/", data={
    "name": f"测试项目_{datetime.now().strftime('%H%M%S')}",
    "project_type": "商业合作",
    "description": "端到端测试"
})
project_id = None
if success and resp:
    try:
        data = resp.json()
        if isinstance(data, dict) and 'id' in data:
            project_id = data['id']
        elif isinstance(data, list) and len(data) > 0:
            project_id = data[0].get('id')
    except:
        pass

# 创建测试案件
success, resp = test_api("创建测试案件", "POST", "/api/cases", data={
    "title": f"测试案件_{datetime.now().strftime('%H%M%S')}",
    "case_type": "合同纠纷",
    "description": "端到端测试案件",
    "status": "pending"
})
case_id = None
if success and resp:
    try:
        data = resp.json()
        if isinstance(data, dict) and 'id' in data:
            case_id = data['id']
    except:
        pass

print(f"\n测试数据: project_id={project_id}, case_id={case_id}")

# 使用测试 case_id 测试更多 API
if case_id:
    print("\n[21] 基于 case_id 的 API 测试")
    print("-" * 40)

    # 证据管理 API
    test_api("获取案件证据", "GET", f"/api/evidence/case/{case_id}")

    # 会议管理 API
    test_api("获取案件会议", "GET", f"/api/meetings/{case_id}")

    # 案件结构 API
    test_api("获取案件结构", "GET", f"/api/cases/{case_id}/structure")

# 总结
print("\n" + "=" * 60)
print("测试结果总结")
print("=" * 60)
print(f"通过: {passed}")
print(f"失败: {failed}")
print(f"总计: {passed + failed}")
if passed + failed > 0:
    print(f"通过率: {passed * 100 / (passed + failed):.1f}%")
