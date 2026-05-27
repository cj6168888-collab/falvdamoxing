import requests
import json

url = "http://localhost:8002/api/smart-chat/generate-document"
data = {"case_id": 1, "document_type": "起诉状"}
headers = {"Content-Type": "application/json"}

try:
    resp = requests.post(url, json=data, headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")