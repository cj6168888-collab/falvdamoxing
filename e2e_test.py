# -*- coding: utf-8 -*-
"""
法律大模型辅助系统 - 端到端测试脚本
E2E Test for Legal LLM System
"""
import sys
import os
import json
import time
import sqlite3
from datetime import datetime

# 确保 UTF-8 编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 使用完整 Python 路径
PYTHON_EXE = r'C:\Users\LENOVO\AppData\Local\Programs\Python\Python39\python.exe'

BASE_URL = 'http://localhost:8000'
DB_PATH = r'D:\www\法律大模型\legal_system.db'
LOG_FILE = r'D:\www\法律大模型\e2e_test_report.json'

# 测试结果收集
test_results = {
    "timestamp": datetime.now().isoformat(),
    "system": "法律大模型辅助系统",
    "version": "v3.0",
    "tests": []
}

def log(msg, level="INFO"):
    """输出日志"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] [{level}] {msg}")

def add_result(name, passed, details=None, error=None):
    """添加测试结果"""
    result = {
        "name": name,
        "passed": passed,
        "timestamp": datetime.now().isoformat()
    }
    if details:
        result["details"] = details
    if error:
        result["error"] = str(error)[:200]
    test_results["tests"].append(result)
    status = "PASS" if passed else "FAIL"
    log(f"[{status}] {name}", "PASS" if passed else "FAIL")
    if error:
        log(f"  Error: {str(error)[:100]}", "ERROR")

# ============== 测试开始 ==============
log("=" * 60)
log("法律大模型辅助系统 - 端到端测试")
log("=" * 60)
log(f"后端地址: {BASE_URL}")
log(f"数据库: {DB_PATH}")
log("")

# 测试1: 健康检查
log("测试1: API 健康检查")
try:
    import requests
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    if r.status_code == 200:
        add_result("API Health Check", True, r.json())
    else:
        add_result("API Health Check", False, error=f"Status: {r.status_code}")
except Exception as e:
    add_result("API Health Check", False, error=e)

# 测试2: 根路径
log("测试2: 根路径")
try:
    r = requests.get(f"{BASE_URL}/", timeout=10)
    if r.status_code == 200:
        add_result("Root Endpoint", True, r.json())
    else:
        add_result("Root Endpoint", False, error=f"Status: {r.status_code}")
except Exception as e:
    add_result("Root Endpoint", False, error=e)

# 测试3: 数据库连接
log("测试3: 数据库连接和数据检查")
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]

    # 检查记录数
    cursor.execute("SELECT COUNT(*) FROM cases")
    case_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM projects")
    project_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM evidence_items")
    evidence_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM documents")
    doc_count = cursor.fetchone()[0]

    conn.close()

    details = {
        "tables": len(tables),
        "table_list": tables,
        "cases": case_count,
        "projects": project_count,
        "evidence_items": evidence_count,
        "documents": doc_count
    }
    add_result("Database Connection", True, details)
except Exception as e:
    add_result("Database Connection", False, error=e)

# 测试4: 创建案件
log("测试4: 创建测试案件")
case_id = None
try:
    case_data = {
        "title": f"E2E_Test_{datetime.now().strftime('%H%M%S')}",
        "case_type": "civil",
        "plaintiff": "测试原告",
        "defendant": "测试被告",
        "cause": "合同纠纷",
        "description": "端到端测试案件"
    }
    r = requests.post(f"{BASE_URL}/api/cases", json=case_data, timeout=10)
    if r.status_code == 200:
        result = r.json()
        case_id = result.get("id")
        add_result("Create Case", True, {"case_id": case_id})
        log(f"  新建案件ID: {case_id}")
    else:
        add_result("Create Case", False, error=f"Status: {r.status_code}, Response: {r.text[:200]}")
except Exception as e:
    add_result("Create Case", False, error=e)

# 测试5: 查询案件列表
log("测试5: 查询案件列表")
try:
    r = requests.get(f"{BASE_URL}/api/cases", timeout=10)
    if r.status_code == 200:
        result = r.json()
        cases = result if isinstance(result, list) else result.get("cases", [])
        add_result("Get Cases List", True, {"count": len(cases)})
    else:
        add_result("Get Cases List", False, error=f"Status: {r.status_code}")
except Exception as e:
    add_result("Get Cases List", False, error=e)

# 测试6: 证据提交
log("测试6: 提交证据")
evidence_id = None
if case_id:
    try:
        evidence_data = {
            "case_id": case_id,
            "name": "测试证据",
            "evidence_type": "合同",
            "content": "这是一份测试合同，用于端到端测试。金额：10000元",
            "source": "test",
            "proof_point": "证明合同关系",
            "custody": "原告"
        }
        r = requests.post(f"{BASE_URL}/api/evidence/submit/{case_id}", json=evidence_data, timeout=15)
        if r.status_code == 200:
            result = r.json()
            evidence_id = result.get("id")
            add_result("Submit Evidence", True, {"evidence_id": evidence_id})
        else:
            add_result("Submit Evidence", False, error=f"Status: {r.status_code}")
    except Exception as e:
        add_result("Submit Evidence", False, error=e)
else:
    add_result("Submit Evidence", False, error="No case_id available")

# 测试7: 查询项目列表
log("测试7: 查询项目列表")
try:
    r = requests.get(f"{BASE_URL}/api/projects", timeout=10)
    if r.status_code == 200:
        result = r.json()
        projects = result if isinstance(result, list) else result.get("projects", result.get("items", []))
        add_result("Get Projects List", True, {"count": len(projects) if projects else 0})
    else:
        add_result("Get Projects List", False, error=f"Status: {r.status_code}")
except Exception as e:
    add_result("Get Projects List", False, error=e)

# 测试8: 证据完整性检查
log("测试8: 证据完整性检查")
if case_id:
    try:
        check_data = {
            "case_id": case_id,
            "case_type": "合同纠纷",
            "user_claims": ["确认合同关系", "要求支付欠款"],
            "party_info": {"submitter": "原告", "plaintiff": "原告A", "defendant": "被告B"}
        }
        r = requests.post(f"{BASE_URL}/api/evidence/check-completeness", json=check_data, timeout=30)
        if r.status_code == 200:
            result = r.json()
            gaps = result.get("gaps", [])
            add_result("Evidence Completeness Check", True, {"gaps": len(gaps)})
        else:
            add_result("Evidence Completeness Check", False, error=f"Status: {r.status_code}")
    except Exception as e:
        add_result("Evidence Completeness Check", False, error=e)
else:
    add_result("Evidence Completeness Check", False, error="No case_id available")

# 测试9: 案件画像
log("测试9: 案件画像")
if case_id:
    try:
        r = requests.get(f"{BASE_URL}/api/v2/profile/summary/{case_id}", timeout=30)
        if r.status_code == 200:
            result = r.json()
            score = result.get("completeness", {}).get("score", "N/A")
            add_result("Case Profile", True, {"completeness_score": score})
        else:
            add_result("Case Profile", False, error=f"Status: {r.status_code}")
    except Exception as e:
        add_result("Case Profile", False, error=e)
else:
    add_result("Case Profile", False, error="No case_id available")

# 测试10: 快捷操作
log("测试10: 快捷操作")
if case_id:
    try:
        r = requests.get(f"{BASE_URL}/api/v2/assistant/quick-actions/{case_id}", timeout=30)
        if r.status_code == 200:
            result = r.json()
            actions = result.get("recommended_actions", [])
            add_result("Quick Actions", True, {"count": len(actions)})
        else:
            add_result("Quick Actions", False, error=f"Status: {r.status_code}")
    except Exception as e:
        add_result("Quick Actions", False, error=e)
else:
    add_result("Quick Actions", False, error="No case_id available")

# 测试11: 对话历史
log("测试11: 对话历史")
if case_id:
    try:
        # 先发一条消息
        chat_data = {"case_id": case_id, "message": "测试消息"}
        requests.post(f"{BASE_URL}/api/v2/assistant/chat", json=chat_data, timeout=30)
        time.sleep(1)

        # 获取历史
        r = requests.get(f"{BASE_URL}/api/v2/assistant/conversation-history/{case_id}", timeout=30)
        if r.status_code == 200:
            result = r.json()
            total = result.get("total", 0)
            add_result("Conversation History", True, {"messages": total})
        else:
            add_result("Conversation History", False, error=f"Status: {r.status_code}")
    except Exception as e:
        add_result("Conversation History", False, error=e)
else:
    add_result("Conversation History", False, error="No case_id available")

# 测试12: 时间把控
log("测试12: 时间把控 API")
try:
    r = requests.get(f"{BASE_URL}/api/时间把控/deadlines?case_id={case_id or 1}", timeout=10)
    status = r.status_code
    add_result("Time Control API", status == 200, {"status": status})
except Exception as e:
    add_result("Time Control API", False, error=e)

# 测试13: 对抗性分析
log("测试13: 对抗性分析")
if case_id:
    try:
        analysis_data = {
            "case_id": case_id,
            "case_type": "民事",
            "opposing_arguments": "被告主张合同已解除"
        }
        r = requests.post(f"{BASE_URL}/api/对抗性分析/analyze", json=analysis_data, timeout=30)
        if r.status_code == 200:
            result = r.json()
            add_result("Adversarial Analysis", True, {"has_result": bool(result)})
        else:
            add_result("Adversarial Analysis", False, error=f"Status: {r.status_code}")
    except Exception as e:
        add_result("Adversarial Analysis", False, error=e)
else:
    add_result("Adversarial Analysis", False, error="No case_id available")

# 测试14: 报告生成
log("测试14: 报告生成 API")
if case_id:
    try:
        report_data = {
            "case_id": case_id,
            "report_type": "summary"
        }
        r = requests.post(f"{BASE_URL}/api/reports/generate", json=report_data, timeout=30)
        status = r.status_code
        add_result("Report Generation", status in [200, 201], {"status": status})
    except Exception as e:
        add_result("Report Generation", False, error=e)
else:
    add_result("Report Generation", False, error="No case_id available")

# 测试15: 资深律师分析
log("测试15: 资深律师分析")
if case_id:
    try:
        analysis_data = {
            "case_id": case_id,
            "case_type": "民事",
            "case_facts": "原被告签订借款合同，约定借款10万元，期限1年，年利率12%"
        }
        r = requests.post(f"{BASE_URL}/api/senior-analysis/analyze", json=analysis_data, timeout=30)
        if r.status_code == 200:
            result = r.json()
            add_result("Senior Lawyer Analysis", True, {"has_result": bool(result)})
        else:
            add_result("Senior Lawyer Analysis", False, error=f"Status: {r.status_code}")
    except Exception as e:
        add_result("Senior Lawyer Analysis", False, error=e)
else:
    add_result("Senior Lawyer Analysis", False, error="No case_id available")

# 测试16: 法律分析服务（直接调用）
log("测试16: 法律分析服务（Python）")
try:
    # 直接导入并测试服务
    sys.path.insert(0, r'D:\www\法律大模型')
    from app.services.legal_analysis import legal_analysis_service

    result = legal_analysis_service.analyze_case(
        query="民间借贷纠纷，对方逾期还款",
        case_facts="2024年1月1日，出借人借给借款人10万元，约定2024年6月1日还款，年利率12%",
        case_type="Contract",
        user_position="Favorable",
        case_direction="litigate"
    )

    if result:
        analysis = result.get("analysis", "")
        add_result("Legal Analysis Service", True, {"analysis_length": len(analysis)})
    else:
        add_result("Legal Analysis Service", False, error="Empty result")
except Exception as e:
    add_result("Legal Analysis Service", False, error=e)

# 测试17: 权益保护系统
log("测试17: 权益保护系统")
try:
    from app.services.legal_protection import LegalAIProtectionSystem

    protection = LegalAIProtectionSystem()
    result = protection.process_query(
        query="高利贷合同是否有效？",
        user_case_facts="2024年1月，出借人与借款人签订借款合同，约定年利率36%",
        user_position="Favorable",
        case_direction="litigate"
    )

    if result:
        safety = result.get("safety_checks", {})
        passed = sum(1 for v in safety.values() if v)
        add_result("Legal Protection System", True, {"safety_checks_passed": passed, "total": len(safety)})
    else:
        add_result("Legal Protection System", False, error="Empty result")
except Exception as e:
    add_result("Legal Protection System", False, error=e)

# 测试18: 向量数据库 (ChromaDB)
log("测试18: 向量数据库")
try:
    import chromadb
    chroma_path = r'D:\www\法律大模型\data\chroma'

    if os.path.exists(chroma_path):
        client = chromadb.PersistentClient(path=chroma_path)
        collections = client.list_collections()
        add_result("ChromaDB Connection", True, {
            "collections": len(collections),
            "collection_names": [c.name for c in collections]
        })
    else:
        add_result("ChromaDB Connection", False, error="ChromaDB data directory not found")
except Exception as e:
    add_result("ChromaDB Connection", False, error=e)

# 测试19: 期限计算服务
log("测试19: 期限计算服务")
try:
    from app.services.deadline_service import DeadlineService

    service = DeadlineService()
    # 测试一个简单的期限计算
    deadlines = service.calculate_deadline("2024-01-01", "litigation_3year")
    add_result("Deadline Service", True, {"has_result": bool(deadlines)})
except Exception as e:
    add_result("Deadline Service", False, error=e)

# 测试20: 流式报告生成
log("测试20: 流式报告生成 API")
if case_id:
    try:
        report_data = {
            "case_id": case_id,
            "report_type": "full"
        }
        r = requests.post(f"{BASE_URL}/api/reports/stream", json=report_data, timeout=30)
        status = r.status_code
        add_result("Streaming Report", status in [200, 201], {"status": status})
    except Exception as e:
        add_result("Streaming Report", False, error=e)
else:
    add_result("Streaming Report", False, error="No case_id available")

# ============== 测试汇总 ==============
log("")
log("=" * 60)
log("测试汇总")
log("=" * 60)

passed = sum(1 for t in test_results["tests"] if t["passed"])
failed = len(test_results["tests"]) - passed
total = len(test_results["tests"])

log(f"总计测试: {total}")
log(f"通过: {passed} ({passed*100//total}%)")
log(f"失败: {failed} ({failed*100//total}%)")
log("")

# 保存测试报告
with open(LOG_FILE, 'w', encoding='utf-8') as f:
    json.dump(test_results, f, ensure_ascii=False, indent=2)

log(f"测试报告已保存: {LOG_FILE}")
log("")
log("=" * 60)
log("端到端测试完成")
log("=" * 60)

# 返回退出码
sys.exit(0 if failed == 0 else 1)
