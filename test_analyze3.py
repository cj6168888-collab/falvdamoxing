import requests

try:
    r = requests.post("http://localhost:8000/api/cases/1/analyze", timeout=180)
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"Error: {r.text[:1000]}")
    else:
        print("Success!")
        print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")
