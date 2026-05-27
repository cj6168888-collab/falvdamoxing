import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Test evidence list API
resp = requests.get('http://localhost:8002/api/v2/evidence-graph/evidence/list', params={'case_id': 1})
print(f'Status: {resp.status_code}')
data = resp.json()
print(f'Total: {data["total"]}')
# Show first 3 evidence items with Chinese names
for item in data['evidence_list'][:3]:
    print(f'  - {item["original_filename"]} | {item["evidence_type_name"]} | {item["source_party"]}')

# Check Content-Type header
print(f'\nContent-Type: {resp.headers.get("content-type", "NOT SET")}')
