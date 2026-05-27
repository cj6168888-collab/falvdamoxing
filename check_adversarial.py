# -*- coding: utf-8 -*-
import requests
import json

print('=' * 60)
print('Adversarial Analysis Function Check')
print('=' * 60)

base_url = 'http://localhost:8002'

# 1. Check server health
print('\n[1] Server Health Check')
try:
    r = requests.get(f'{base_url}/health', timeout=5)
    print(f'    /health: {r.status_code}')
except Exception as e:
    print(f'    /health: Error - {e}')

# 2. Check adversarial routes
print('\n[2] Adversarial API Routes')
r = requests.get(f'{base_url}/openapi.json', timeout=5)
data = r.json()
paths = data.get('paths', {})

adversarial_paths = [p for p in paths.keys() if 'adversarial' in p.lower()]
print(f'    Total: {len(adversarial_paths)} routes')

# 3. Test endpoints
print('\n[3] Endpoint Tests')
tests = [
    ('GET', '/api/adversarial/case/1/analyses', None),
    ('POST', '/api/adversarial/case/1/opponent-analysis', {}),
    ('POST', '/api/adversarial/case/1/evidence-matrix', {}),
    ('POST', '/api/adversarial/case/1/scenario-prediction', {}),
    ('POST', '/api/adversarial/case/1/automated-plan', {}),
    ('POST', '/api/adversarial/case/1/debate-stream', {}),
]

for method, path, body in tests:
    try:
        if method == 'GET':
            r = requests.get(f'{base_url}{path}', timeout=5)
        else:
            r = requests.post(f'{base_url}{path}', json=body or {}, timeout=10)
        status = r.status_code
        if status == 200:
            print(f'    {method} {path}: OK ({status})')
        elif status == 405:
            print(f'    {method} {path}: Method Not Allowed ({status})')
        elif status == 404:
            print(f'    {method} {path}: Not Found ({status})')
        else:
            print(f'    {method} {path}: {status}')
    except Exception as e:
        print(f'    {method} {path}: Error')

# 4. Check database records
print('\n[4] Database Analysis Records')
r = requests.get(f'{base_url}/api/adversarial/case/1/analyses', timeout=5)
if r.status_code == 200:
    analyses = r.json()
    print(f'    Case 1 has {len(analyses)} analysis records')
    if analyses:
        latest = analyses[-1]
        title = latest.get('title', 'No title')
        phase = latest.get('analysis_phase', 'Unknown')
        is_current = latest.get('is_current', False)
        print(f'    Latest: {title}')
        print(f'    Phase: {phase}')
        print(f'    Is Current: {is_current}')

print('\n' + '=' * 60)
print('Check Complete')
print('=' * 60)
