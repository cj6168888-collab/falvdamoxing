import requests
import sys

BASE_URL = "http://localhost:8000"

def test_api():
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
    failed = 0
    
    for method, endpoint, name in tests:
        url = f"{BASE_URL}{endpoint}"
        try:
            if method == "GET":
                resp = requests.get(url, timeout=5)
            
            status = resp.status_code
            if status == 200:
                print(f"[PASS] {name}: {endpoint} - {status}")
                passed += 1
            else:
                print(f"[FAIL] {name}: {endpoint} - {status}")
                failed += 1
                try:
                    print(f"  Error: {resp.text[:100]}")
                except:
                    pass
        except Exception as e:
            print(f"[ERROR] {name}: {endpoint} - {e}")
            failed += 1
    
    print(f"\n总计: 通过 {passed}, 失败 {failed}")
    return passed, failed

if __name__ == "__main__":
    try:
        passed, failed = test_api()
        sys.exit(0 if failed == 0 else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)