import requests
import sys
import time

# Try both ports
for port in [8000, 8888]:
    try:
        r = requests.get(f"http://localhost:{port}/health", timeout=2)
        if r.status_code == 200:
            BASE_URL = f"http://localhost:{port}"
            print(f"Server found on port {port}")
            break
    except:
        continue
else:
    print("ERROR: Server not running on any port")
    sys.exit(1)

def test_api(method, endpoint, name, expected_status=200):
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json={}, timeout=5)
        
        status = r.status_code
        if status == expected_status or (expected_status == 404 and status in [404, 200]):
            print(f"[PASS] {name}: {endpoint} -> {status}")
            return True
        else:
            print(f"[FAIL] {name}: {endpoint} -> {status} (expected {expected_status})")
            return False
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return False

tests = [
    ("GET", "/health", "健康检查"),
    ("GET", "/api/documents/templates", "文书模板"),
    ("GET", "/api/documents", "文书列表"),
    ("GET", "/api/reports", "报告列表"),
    ("GET", "/api/meetings", "会议列表"),
    ("GET", "/api/hearings", "开庭记录"),
    ("GET", "/api/company-info/search?keyword=test", "公司信息"),
    ("GET", "/api/conversations", "对话列表"),
    ("GET", "/api/document-management/documents", "文档管理"),
    ("GET", "/api/exports/formats", "导出格式"),
    ("POST", "/api/evidence/qa", "证据问答"),
]

passed = 0
for method, endpoint, name in tests:
    if test_api(method, endpoint, name):
        passed += 1

print(f"\n通过: {passed}/{len(tests)}")
sys.exit(0 if passed == len(tests) else 1)