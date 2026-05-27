import requests
import traceback

try:
    r = requests.post("http://localhost:8000/api/cases/1/analyze", timeout=60)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
