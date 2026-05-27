# -*- coding: utf-8 -*-
"""端到端测试脚本"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import json
import time
from datetime import datetime

BASE_URL = 'http://localhost:8000'
LOG_FILE = 'debug-535684.log'

# 清空日志
with open(LOG_FILE, 'w', encoding='utf-8') as f:
    f.write('')

def log(msg):
    print('[{}] {}'.format(datetime.now().strftime('%H:%M:%S'), msg))

def log_to_file(msg, data=None):
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            entry = {'timestamp': int(time.time()*1000), 'message': msg, 'data': data or {}}
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except: pass

def test(name, fn):
    try:
        result = fn()
        if result:
            log('[PASS] ' + name)
            return True
        else:
            log('[FAIL] ' + name)
            return False
    except Exception as e:
        log('[FAIL] ' + name + ': ' + str(e)[:80])
        return False

# ===== 测试开始 =====
log('=' * 60)
log('E2E Test Started')
log('=' * 60)

# 测试1: 健康检查
def test_health():
    r = requests.get(BASE_URL + '/health', timeout=5)
    return r.status_code == 200

test('API Health', test_health)

# 测试2: 创建案件
case_id = None
def test_create_case():
    global case_id
    case_data = {
        'title': 'E2E_Test_' + datetime.now().strftime('%H%M%S'),
        'case_type': 'civil',
        'plaintiff': 'Test Plaintiff',
        'defendant': 'Test Defendant',
        'cause': 'Contract Dispute',
        'description': 'E2E test case'
    }
    r = requests.post(BASE_URL + '/api/cases', json=case_data, timeout=10)
    if r.status_code == 200:
        case_id = r.json().get('id')
        log('    Case ID: ' + str(case_id))
        log_to_file('CASE_CREATED', {'case_id': case_id})
        return True
    return False

test('Create Case', test_create_case)

if case_id:
    # 测试3: 提交证据
    evidence_tests = [
        ('Plain Text', 'text', 'Contract content here...'),
        ('JSON Data', 'json', json.dumps({'txn': 'T001', 'amount': 50000})),
        ('Table Format', 'table', 'Date|Method|Amount\n2024-01-15|Transfer|50000'),
    ]
    
    for name, fmt, content in evidence_tests:
        def make_test(n, c):
            def t():
                data = {
                    'case_id': case_id,
                    'name': n,
                    'evidence_type': 'Document',
                    'content': c,
                    'source': 'test',
                    'proof_point': 'test purpose',
                    'custody': 'Plaintiff'
                }
                r = requests.post(BASE_URL + '/api/evidence/submit/' + str(case_id), json=data, timeout=10)
                return r.status_code == 200
            return t
        
        test('Evidence [' + name + ']', make_test(name, content))
    
    # 测试4: 证据完整性检查
    def test_completeness():
        data = {
            'case_id': case_id,
            'case_type': 'Contract',
            'user_claims': ['Claim 1', 'Claim 2'],
            'party_info': {'submitter': 'Plaintiff', 'plaintiff': 'P', 'defendant': 'D'}
        }
        r = requests.post(BASE_URL + '/api/evidence/check-completeness', json=data, timeout=60)
        if r.status_code == 200:
            result = r.json()
            gaps = result.get('gaps', [])
            log('    Gaps found: ' + str(len(gaps)))
            log_to_file('COMPLETENESS', {'gaps': len(gaps)})
            return True
        return False
    
    test('Evidence Completeness', test_completeness)
    
    # 测试5: 统一助手 (使用正确的API路径)
    def test_assistant():
        r = requests.post(BASE_URL + '/api/v2/assistant/chat', 
            json={'case_id': case_id, 'message': 'What should I do with this case?'}, timeout=60)
        if r.status_code == 200:
            result = r.json()
            answer = result.get('answer', '')
            log('    Answer length: ' + str(len(answer)))
            log_to_file('ASSISTANT', {'answer_len': len(answer), 'intent': result.get('intent', '')})
            return True
        return False
    
    test('Assistant Chat', test_assistant)
    
    # 测试6: 案件画像
    def test_profile():
        r = requests.get(BASE_URL + '/api/v2/profile/summary/' + str(case_id), timeout=30)
        if r.status_code == 200:
            result = r.json()
            score = result.get('completeness', {}).get('score', 0)
            log('    Profile score: ' + str(score) + '%')
            log_to_file('PROFILE', {'score': score})
            return True
        return False
    
    test('Case Profile', test_profile)
    
    # 测试7: 快捷操作
    def test_quick_actions():
        r = requests.get(BASE_URL + '/api/v2/assistant/quick-actions/' + str(case_id), timeout=30)
        if r.status_code == 200:
            result = r.json()
            actions = result.get('recommended_actions', [])
            log('    Actions: ' + str(len(actions)))
            log_to_file('QUICK_ACTIONS', {'count': len(actions)})
            return True
        return False
    
    test('Quick Actions', test_quick_actions)

    # 测试8: 对话历史
    def test_history():
        # 先发消息
        requests.post(BASE_URL + '/api/v2/assistant/chat', 
            json={'case_id': case_id, 'message': 'Test message'}, timeout=30)
        time.sleep(0.5)
        
        r = requests.get(BASE_URL + '/api/v2/assistant/conversation-history/' + str(case_id), timeout=30)
        if r.status_code == 200:
            result = r.json()
            total = result.get('total', 0)
            log('    History: ' + str(total) + ' messages')
            return True
        return False
    
    test('Conversation History', test_history)

    # 测试9: 法律分析服务
    log('Testing Legal Analysis Service...')
    try:
        from app.services.legal_analysis import legal_analysis_service
        result = legal_analysis_service.analyze_case(
            query='Loan contract dispute, counterparty breached contract...',
            case_facts='2024-01-01, Borrower borrowed 100,000 RMB, due 2024-06-01, annual rate 12%',
            case_type='Contract',
            user_position='Favorable',
            case_direction='litigate'
        )
        if result:
            analysis = result.get('analysis', '')
            log('    Analysis length: ' + str(len(analysis)) + ' chars')
            log_to_file('LEGAL_ANALYSIS', {'length': len(analysis), 'direction': 'litigate'})
            log('[PASS] Legal Analysis Service')
        else:
            log('[FAIL] Legal Analysis Service: empty result')
    except Exception as e:
        log('[FAIL] Legal Analysis Service: ' + str(e)[:80])
    
    # 测试10: 防护系统
    log('Testing Protection System...')
    try:
        from app.services.legal_protection import LegalAIProtectionSystem
        protection = LegalAIProtectionSystem()
        result = protection.process_query(
            query='What are the legal provisions for private lending?',
            user_case_facts='2024-01, Lender lent 50,000 RMB to Borrower, agreed annual rate 24%',
            user_position='Favorable',
            case_direction='negotiate'
        )
        if result:
            safety = result.get('safety_checks', {})
            checks = [(k, v) for k, v in safety.items()]
            passed = sum(1 for _, v in checks if v)
            log('    Safety checks: ' + str(passed) + '/' + str(len(checks)))
            for k, v in checks:
                log('      ' + k + ': ' + ('OK' if v else 'FAIL'))
            log_to_file('PROTECTION', {'checks': safety})
            log('[PASS] Protection System')
        else:
            log('[FAIL] Protection System: empty result')
    except Exception as e:
        log('[FAIL] Protection System: ' + str(e)[:80])

log('=' * 60)
log('E2E Test Completed')
log('=' * 60)
