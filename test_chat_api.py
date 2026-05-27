"""
测试对话 API
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8002"

def test_health():
    """测试健康检查"""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"健康检查: {resp.status_code} - {resp.json()}")
        return resp.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_chat():
    """测试对话 API"""
    try:
        payload = {
            "case_id": 2,
            "message": "你好"
        }
        resp = requests.post(
            f"{BASE_URL}/api/v2/assistant/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"对话 API: {resp.status_code}")
        if resp.status_code != 200:
            print(f"错误响应: {resp.text[:500]}")
        else:
            print(f"成功: {json.dumps(resp.json(), ensure_ascii=False, indent=2)[:500]}")
        return resp.status_code == 200
    except Exception as e:
        print(f"对话 API 失败: {e}")
        return False

if __name__ == "__main__":
    print("=== 测试后端 API ===")
    health_ok = test_health()
    if health_ok:
        test_chat()
    else:
        print("后端服务未运行，请先启动后端")
