import requests

# Test with verbose output
try:
    r = requests.post("http://localhost:8000/api/cases/1/analyze", timeout=60)
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"Error response: {r.text[:2000]}")
except Exception as e:
    print(f"Exception: {e}")
