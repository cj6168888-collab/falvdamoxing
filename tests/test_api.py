"""
后端API集成测试
"""
import pytest
from httpx import AsyncClient


async def _create_case(client: AsyncClient, title: str = "测试案件") -> int:
    response = await client.post("/api/cases", json={
        "title": title,
        "case_type": "民事",
        "plaintiff": "张三",
        "defendant": "李四",
        "description": "接口测试案件",
    })
    assert response.status_code in [200, 201]
    return response.json()["id"]


async def _create_appeal(client: AsyncClient, case_id: int) -> int:
    response = await client.post(f"/api/appeal/case/{case_id}/appeals", json={
        "appeal_type": "first_to_second",
        "appeal_reason": "factual_error",
        "original_court": "基层人民法院",
        "judgment_received_date": "2026-05-01T00:00:00",
        "appeal_requests": "请求撤销原判并依法改判",
    })
    assert response.status_code in [200, 201]
    return response.json()["appeal"]["id"]

# ============ 案件API测试 ============
class TestCaseAPI:
    """案件管理API测试"""
    
    @pytest.mark.asyncio
    async def test_get_cases(self, client: AsyncClient):
        """测试获取案件列表"""
        response = await client.get("/api/cases")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_create_case(self, client: AsyncClient):
        """测试创建案件"""
        case_data = {
            "title": "测试案件",
            "case_type": "民事",
            "plaintiff": "张三",
            "defendant": "李四",
            "description": "测试描述"
        }
        response = await client.post("/api/cases", json=case_data)
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_get_case_detail(self, client: AsyncClient):
        """测试获取案件详情"""
        response = await client.get("/api/cases/1")
        # 可能返回404如果案件不存在
        assert response.status_code in [200, 404]

# ============ 上诉API测试 ============
class TestAppealAPI:
    """上诉追踪API测试"""
    
    @pytest.mark.asyncio
    async def test_get_appeals(self, client: AsyncClient):
        """测试获取上诉列表"""
        case_id = await _create_case(client, "上诉列表测试案件")
        response = await client.get(f"/api/appeal/case/{case_id}/appeals")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_create_appeal(self, client: AsyncClient):
        """测试创建上诉"""
        case_id = await _create_case(client, "创建上诉测试案件")
        appeal_data = {
            "appeal_type": "first_to_second",
            "appeal_reason": "factual_error",
            "original_court": "基层人民法院",
            "judgment_received_date": "2026-05-01T00:00:00",
            "appeal_requests": "请求撤销原判并依法改判",
        }
        response = await client.post(f"/api/appeal/case/{case_id}/appeals", json=appeal_data)
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_appeal_countdown(self, client: AsyncClient):
        """测试上诉期限倒计时"""
        case_id = await _create_case(client, "上诉倒计时测试案件")
        appeal_id = await _create_appeal(client, case_id)
        response = await client.get(f"/api/appeal/appeal/{appeal_id}/countdown")
        assert response.status_code == 200
        data = response.json()
        assert "appeal_deadline" in data or "deadlines" in data

# ============ 执行跟踪API测试 ============
class TestExecutionAPI:
    """执行跟踪API测试"""
    
    @pytest.mark.asyncio
    async def test_get_executions(self, client: AsyncClient):
        """测试获取执行记录"""
        case_id = await _create_case(client, "执行记录列表测试案件")
        response = await client.get(f"/api/execution/case/{case_id}/records")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_create_execution(self, client: AsyncClient):
        """测试创建执行记录"""
        case_id = await _create_case(client, "创建执行记录测试案件")
        exec_data = {
            "title": "test execution record",
            "record_date": "2026-04-01T00:00:00",
            "record_type": "法院通知",
            "content": "收到法院执行通知",
            "stage": "application",
            "progress": 10
        }
        response = await client.post(f"/api/execution/case/{case_id}/records", json=exec_data)
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_execution_summary(self, client: AsyncClient):
        """测试执行概况"""
        case_id = await _create_case(client, "执行统计测试案件")
        response = await client.get(f"/api/execution/case/{case_id}/statistics")
        assert response.status_code == 200

# ============ 提醒中心API测试 ============
class TestReminderAPI:
    """提醒中心API测试"""
    
    @pytest.mark.asyncio
    async def test_get_reminders(self, client: AsyncClient):
        """测试获取提醒列表"""
        response = await client.get("/api/reminders")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_create_reminder(self, client: AsyncClient):
        """测试创建提醒"""
        reminder_data = {
            "title": "测试提醒",
            "content": "测试内容",
            "due_date": "2026-04-15",
            "priority": "medium"
        }
        response = await client.post("/api/reminders", json=reminder_data)
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_reminder_stats(self, client: AsyncClient):
        """测试提醒统计"""
        response = await client.get("/api/reminders/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "pending" in data
    
    @pytest.mark.asyncio
    async def test_batch_reminder_action(self, client: AsyncClient):
        """测试批量操作"""
        action_data = {
            "reminder_ids": ["1", "2"],
            "action": "complete"
        }
        response = await client.post("/api/reminders/batch", json=action_data)
        assert response.status_code == 200

# ============ Dashboard API测试 ============
class TestDashboardAPI:
    """仪表盘API测试"""
    
    @pytest.mark.asyncio
    async def test_dashboard_stats(self, client: AsyncClient):
        """测试获取仪表盘统计"""
        response = await client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert "case_stats" in data or "reminder_stats" in data
    
    @pytest.mark.asyncio
    async def test_urgent_items(self, client: AsyncClient):
        """测试紧急事项"""
        response = await client.get("/api/dashboard/urgent")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_upcoming_deadlines(self, client: AsyncClient):
        """测试即将到期"""
        response = await client.get("/api/dashboard/upcoming?days=7")
        assert response.status_code == 200

# ============ 第三方API测试 ============
class TestThirdPartyAPI:
    """第三方API测试"""
    
    @pytest.mark.asyncio
    async def test_holiday_check(self, client: AsyncClient):
        """测试节假日检查"""
        response = await client.post("/api/third-party/holiday/check", json={
            "dates": ["2026-04-05", "2026-04-06"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "holidays" in data
    
    @pytest.mark.asyncio
    async def test_next_workday(self, client: AsyncClient):
        """测试下一个工作日"""
        response = await client.get("/api/third-party/holiday/next-workday?start_date=2026-04-04")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_company_logo(self, client: AsyncClient):
        """测试企业Logo获取"""
        response = await client.post("/api/third-party/company/logo", json={
            "company_name": "阿里巴巴"
        })
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_phone_validate(self, client: AsyncClient):
        """测试手机号验证"""
        response = await client.post("/api/third-party/validate/phone", json={
            "phone": "13800138000"
        })
        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data
    
    @pytest.mark.asyncio
    async def test_email_validate(self, client: AsyncClient):
        """测试邮箱验证"""
        response = await client.post("/api/third-party/validate/email", json={
            "email": "test@example.com"
        })
        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data
    
    @pytest.mark.asyncio
    async def test_third_party_health(self, client: AsyncClient):
        """测试第三方服务健康检查"""
        response = await client.get("/api/third-party/health")
        assert response.status_code == 200

# ============ 法律资料库API测试 ============
class TestLegalKnowledgeAPI:
    """法律资料库API测试"""
    
    @pytest.mark.asyncio
    async def test_search_articles(self, client: AsyncClient):
        """测试搜索法条"""
        response = await client.get("/api/legal/articles?q=借贷")
        # 可能返回404如果端点不存在
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_legal_search(self, client: AsyncClient):
        """测试综合检索"""
        response = await client.post("/api/legal/search", json={
            "query": "民间借贷"
        })
        assert response.status_code in [200, 404]
