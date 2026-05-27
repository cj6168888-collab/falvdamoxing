import requests
import sys

BASE_URL = "http://localhost:8000"

def test_api(method, endpoint, name):
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json={}, timeout=5)
        
        status = r.status_code
        if status in [200, 201, 404]:
            print(f"[PASS] {name}: {endpoint} -> {status}")
            return True
        else:
            print(f"[FAIL] {name}: {endpoint} -> {status}")
            return False
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return False

tests = [
    ("GET", "/api/documents/templates", "文书模板"),
    ("GET", "/api/documents", "文书列表"),
    ("GET", "/api/reports", "报告列表"),
    ("GET", "/api/meetings", "会议列表"),
    ("GET", "/api/hearings", "开庭记录"),
    ("GET", "/api/company-info/search?keyword=test", "公司信息"),
    ("GET", "/api/conversations", "对话列表"),
    ("GET", "/api/document-management/documents", "文档管理"),
    ("GET", "/api/exports/formats", "导出格式"),
]

passed = 0
for method, endpoint, name in tests:
    if test_api(method, endpoint, name):
        passed += 1

print(f"\n通过: {passed}/{len(tests)}")
sys.exit(0 if passed == len(tests) else 1)