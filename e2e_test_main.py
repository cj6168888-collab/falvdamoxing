# 法律大模型辅助系统 - 端到端测试
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
REPORT_FILE = "e2e_test_result.md"

class E2ETest:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.warnings = []

    def test(self, name, method, endpoint, expected_status=200, data=None, description=""):
        url = f"{BASE_URL}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=60)
            elif method == "PUT":
                response = requests.put(url, json=data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, timeout=30)
            else:
                raise ValueError(f"Unknown method: {method}")

            success = response.status_code == expected_status

            result = {
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "description": description
            }

            if success:
                self.passed += 1
                print(f"[PASS] {name}")
                try:
                    result["response"] = response.json()
                except:
                    result["response"] = response.text[:200]
            else:
                self.failed += 1
                print(f"[FAIL] {name} (Expected {expected_status}, got {response.status_code})")
                result["error"] = response.text[:500]
                self.warnings.append(f"{name}: {response.text[:200]}")

            self.results.append(result)
            return result

        except requests.exceptions.Timeout:
            self.failed += 1
            print(f"[TIMEOUT] {name} - Timeout")
            self.results.append({
                "name": name, "method": method, "endpoint": endpoint,
                "success": False, "error": "Request timeout"
            })
            return None
        except requests.exceptions.ConnectionError as e:
            self.failed += 1
            print(f"[ERROR] {name} - Connection Error")
            self.results.append({
                "name": name, "method": method, "endpoint": endpoint,
                "success": False, "error": f"Connection error: {str(e)}"
            })
            return None
        except Exception as e:
            self.failed += 1
            print(f"[ERROR] {name} - Error: {e}")
            self.results.append({
                "name": name, "method": method, "endpoint": endpoint,
                "success": False, "error": str(e)
            })
            return None

    def run_all_tests(self):
        print("=" * 60)
        print("法律大模型辅助系统 - 端到端测试")
        print("=" * 60)
        print()

        # 1. 系统健康检查
        print("\n[1] 系统健康检查")
        print("-" * 40)
        self.test("系统健康检查", "GET", "/health", expected_status=200)

        # 2. 项目管理 API 测试
        print("\n[2] 项目管理 API (/api/projects)")
        print("-" * 40)
        self.test("获取项目列表", "GET", "/api/projects/", expected_status=200)
        self.test("创建项目", "POST", "/api/projects/", data={
            "name": "E2E测试项目",
            "project_type": "商业合作",
            "description": "端到端测试项目"
        })

        # 3. 案件管理 API 测试
        print("\n[3] 案件管理 API (/api/cases)")
        print("-" * 40)
        self.test("获取案件列表", "GET", "/api/cases", expected_status=200)
        self.test("创建案件", "POST", "/api/cases", data={
            "title": "E2E测试案件",
            "case_type": "合同纠纷",
            "description": "端到端测试案件",
            "status": "pending"
        })

        # 4. 证据管理 API 测试
        print("\n[4] 证据管理 API (/api/evidence)")
        print("-" * 40)
        self.test("获取证据列表", "GET", "/api/evidence/case/1", expected_status=200)

        # 5. 对抗性分析 API 测试
        print("\n[5] 对抗性分析 API")
        print("-" * 40)
        self.test("获取对抗性分析列表", "GET", "/api/adversarial-analysis/list", expected_status=404)

        # 6. 时间把控 API 测试
        print("\n[6] 时间把控 API")
        print("-" * 40)
        self.test("获取时间线", "GET", "/api/time-control/timeline/1", expected_status=404)

        # 7. 文书管理 API 测试
        print("\n[7] 文书管理 API (/api/documents)")
        print("-" * 40)
        self.test("获取文书模板", "GET", "/api/documents/templates", expected_status=200)
        self.test("获取文书列表", "GET", "/api/documents", expected_status=200)

        # 8. 知识库 API 测试
        print("\n[8] 知识库 API")
        print("-" * 40)
        self.test("获取洞察分析", "GET", "/api/insights/1", expected_status=404)

        # 9. 报告生成 API 测试
        print("\n[9] 报告生成 API (/api/reports)")
        print("-" * 40)
        self.test("获取报告列表", "GET", "/api/reports", expected_status=200)

        # 10. 会议管理 API 测试
        print("\n[10] 会议管理 API (/api/meetings)")
        print("-" * 40)
        self.test("获取会议列表", "GET", "/api/meetings", expected_status=200)

        # 11. 开庭记录 API 测试
        print("\n[11] 开庭记录 API (/api/hearings)")
        print("-" * 40)
        self.test("获取开庭记录列表", "GET", "/api/hearings", expected_status=200)

        # 12. 公司信息 API 测试
        print("\n[12] 公司信息 API (/api/company-info)")
        print("-" * 40)
        self.test("获取公司信息", "GET", "/api/company-info/search?keyword=测试", expected_status=200)

        # 13. 对话 API 测试
        print("\n[13] 对话 API (/api/conversations)")
        print("-" * 40)
        self.test("获取对话列表", "GET", "/api/conversations", expected_status=200)

        # 14. 资深律师分析 API 测试
        print("\n[14] 资深律师分析 API")
        print("-" * 40)
        self.test("获取资深分析列表", "GET", "/api/senior-analysis/list", expected_status=404)

        # 15. 文档管理 API 测试
        print("\n[15] 文档管理 API (/api/document-management)")
        print("-" * 40)
        self.test("获取文档列表", "GET", "/api/document-management", expected_status=200)

        # 16. 案件结构 API 测试
        print("\n[16] 案件结构 API (/api/case-structure)")
        print("-" * 40)
        self.test("获取案件结构", "GET", "/api/case-structure/1", expected_status=404)

        # 17. 证据图谱 API 测试
        print("\n[17] 证据图谱 API (/api/evidence/graph)")
        print("-" * 40)
        self.test("获取证据图谱", "GET", "/api/evidence/graph/1", expected_status=404)

        # 18. 证据问答 API 测试
        print("\n[18] 证据问答 API")
        print("-" * 40)
        self.test("证据问答", "POST", "/api/evidence/qa", data={
            "evidence_id": "1", "question": "测试问题"
        }, expected_status=200)

        # 19. 导出 API 测试
        print("\n[19] 导出 API (/api/exports)")
        print("-" * 40)
        self.test("获取导出格式", "GET", "/api/exports/formats", expected_status=200)

        # 20. 案件画像 API 测试
        print("\n[20] 案件画像 API (/api/profiles)")
        print("-" * 40)
        self.test("获取案件画像", "GET", "/api/profiles/1", expected_status=404)

        # 21. 证据引导 API 测试
        print("\n[21] 证据引导 API")
        print("-" * 40)
        self.test("获取证据引导", "GET", "/api/evidence/guide/init/1", expected_status=404)

        # 22. 智能助手 API 测试
        print("\n[22] 智能助手 API (/api/v2/assistant)")
        print("-" * 40)
        self.test("智能助手", "POST", "/api/v2/assistant/chat", data={
            "message": "你好", "case_id": 1
        }, expected_status=200)

        # 打印总结
        print("\n" + "=" * 60)
        print("测试结果总结")
        print("=" * 60)
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print(f"总计: {self.passed + self.failed}")
        if self.passed + self.failed > 0:
            print(f"通过率: {self.passed * 100 / (self.passed + self.failed):.1f}%")

        if self.warnings:
            print("\n警告:")
            for w in self.warnings[:10]:
                print(f"  - {w[:100]}")

        self.generate_report()
        return self.passed, self.failed

    def generate_report(self):
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write("# 法律大模型辅助系统 - 端到端测试报告\n\n")
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## 测试结果总结\n\n")
            f.write(f"| 指标 | 值 |\n")
            f.write(f"|------|-----|\n")
            f.write(f"| 通过 | {self.passed} |\n")
            f.write(f"| 失败 | {self.failed} |\n")
            f.write(f"| 通过率 | {self.passed * 100 / (self.passed + self.failed) if self.passed + self.failed > 0 else 0:.1f}% |\n\n")
            f.write("## 详细测试结果\n\n")
            for r in self.results:
                status = "[PASS]" if r["success"] else "[FAIL]"
                f.write(f"### {status} {r['name']}\n\n")
                f.write(f"- 方法: {r['method']}\n")
                f.write(f"- 端点: {r['endpoint']}\n")
                f.write(f"- 期望状态: {r.get('expected_status', 'N/A')}\n")
                f.write(f"- 实际状态: {r.get('actual_status', 'N/A')}\n")
                if r.get('description'):
                    f.write(f"- 说明: {r['description']}\n")
                if r.get('error'):
                    f.write(f"- 错误: {r['error'][:200]}\n")
                f.write("\n")
            if self.warnings:
                f.write("## 警告列表\n\n")
                for w in self.warnings:
                    f.write(f"- {w}\n")
        print(f"\n报告已保存到: {REPORT_FILE}")


if __name__ == "__main__":
    tester = E2ETest()
    passed, failed = tester.run_all_tests()
    exit(0 if failed == 0 else 1)
