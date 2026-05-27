"""
法律大模型辅助系统 - Streamlit 主应用
随身律师 - 人人都有专属法律顾问
工作台模式 - 精简高效
"""
import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta

# 页面配置
st.set_page_config(
    page_title="随身律师 - 工作台",
    page_icon="⚖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 配置（可通过环境变量 API_BASE_URL 覆盖，默认本地开发端口）
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8002")


def check_api_status():
    """检查 API 是否可用"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        st.session_state.api_error = "无法连接到后端服务，请确保服务已启动"
        return False
    except requests.exceptions.Timeout:
        st.session_state.api_error = "连接超时，后端服务响应过慢"
        return False
    except Exception as e:
        st.session_state.api_error = f"连接错误: {str(e)}"
        return False


def get_cases():
    """获取案件列表"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/cases", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError:
        st.session_state.api_error = "无法获取案件列表：无法连接到后端服务"
    except requests.exceptions.Timeout:
        st.session_state.api_error = "无法获取案件列表：请求超时"
    except Exception as e:
        st.session_state.api_error = f"获取案件失败: {str(e)}"
    return []


def get_projects():
    """获取项目列表"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/projects/", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError:
        st.session_state.api_error = "无法获取项目列表：无法连接到后端服务"
    except requests.exceptions.Timeout:
        st.session_state.api_error = "无法获取项目列表：请求超时"
    except Exception as e:
        st.session_state.api_error = f"获取项目失败: {str(e)}"
    return []


def get_loans():
    """获取借款记录"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/loans/", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError:
        st.session_state.api_error = "无法获取借款记录：无法连接到后端服务"
    except requests.exceptions.Timeout:
        st.session_state.api_error = "无法获取借款记录：请求超时"
    except Exception as e:
        st.session_state.api_error = f"获取借款记录失败: {str(e)}"
    return []


def get_contracts():
    """获取合同列表"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/contracts/", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError:
        st.session_state.api_error = "无法获取合同列表：无法连接到后端服务"
    except requests.exceptions.Timeout:
        st.session_state.api_error = "无法获取合同列表：请求超时"
    except Exception as e:
        st.session_state.api_error = f"获取合同列表失败: {str(e)}"
    return []


def get_upcoming_reminders():
    """获取即将到期的提醒"""
    reminders = []
    loans = get_loans()
    contracts = get_contracts()

    today = datetime.now().date()

    # 借款提醒
    for loan in loans:
        if loan.get('due_date'):
            due_date = datetime.strptime(loan['due_date'], '%Y-%m-%d').date() if isinstance(loan['due_date'], str) else loan['due_date']
            days_left = (due_date - today).days

            if days_left < 0:
                status = "overdue"
                priority = "high"
            elif days_left <= 7:
                status = "soon"
                priority = "medium"
            else:
                continue

            reminders.append({
                "type": "loan",
                "title": f"借款: {loan.get('borrower_name', '未知')}",
                "amount": loan.get('amount', 0),
                "due_date": due_date,
                "days_left": days_left,
                "status": status,
                "priority": priority,
                "id": loan.get('id')
            })

    # 合同到期提醒
    for contract in contracts:
        if contract.get('expiry_date'):
            expiry_date = datetime.strptime(contract['expiry_date'], '%Y-%m-%d').date() if isinstance(contract['expiry_date'], str) else contract['expiry_date']
            days_left = (expiry_date - today).days

            if days_left <= 30 and days_left >= 0:
                reminders.append({
                    "type": "contract",
                    "title": f"合同: {contract.get('title', '未知')}",
                    "due_date": expiry_date,
                    "days_left": days_left,
                    "status": "warning",
                    "priority": "medium",
                    "id": contract.get('id')
                })

    # 按优先级排序
    priority_order = {"high": 0, "medium": 1, "low": 2}
    reminders.sort(key=lambda x: (priority_order.get(x['priority'], 2), x['days_left']))

    return reminders[:10]


# ============ 状态初始化 ============
if "current_case_id" not in st.session_state:
    st.session_state.current_case_id = None
if "current_project_id" not in st.session_state:
    st.session_state.current_project_id = None


# ============ 侧边栏 - 精简版 ============
with st.sidebar:
    st.title("⚖ 随身律师")

    # API 状态 - 增加详细诊断
    api_ok = check_api_status()
    if api_ok:
        st.success("✅ 系统就绪")
    else:
        st.error("⚠️ 后台未连接")
        st.caption("请确保后端服务已启动")
        with st.expander("诊断帮助"):
            st.code("cd d:\\www\\法律大模型")
            st.code("python run.py")
            st.caption("或单独启动后端:")
            st.code("python -m uvicorn app.main:app --port 8000")

    st.divider()

    # 快捷入口
    st.subheader("📌 快捷入口")

    if st.button("💰 借款", use_container_width=True):
        st.switch_page("pages/11_借款记录.py")

    if st.button("📄 合同", use_container_width=True):
        st.switch_page("pages/12_合同管理.py")

    if st.button("🎙 会议", use_container_width=True):
        st.switch_page("pages/10_会议谈判援助.py")

    if st.button("⚔ 分析", use_container_width=True):
        st.switch_page("pages/5_对抗性分析.py")

    st.divider()

    # 风险统计 - 简化
    reminders = get_upcoming_reminders()
    overdue_count = len([r for r in reminders if r['status'] == 'overdue'])
    warning_count = len([r for r in reminders if r['status'] in ['soon', 'warning']])

    if overdue_count > 0:
        st.error(f"🔴 {overdue_count} 项逾期")
    elif warning_count > 0:
        st.warning(f"🟡 {warning_count} 项待处理")
    else:
        st.success("🟢 暂无风险")

    st.divider()

    # 帮助
    st.caption("💡 随时咨询")


# ============ 主页面 - 工作台模式 ============
st.title("⚖ 工作台")
st.caption("您的专属法律事务管理中枢")

# ============ 快速统计 ============
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

loans = get_loans()
contracts = get_contracts()
projects = get_projects()
today = datetime.now().date()

# 计算统计数据
overdue_loans = [l for l in loans if l.get('due_date') and 
                  datetime.strptime(l['due_date'], '%Y-%m-%d').date() < today and 
                  l.get('status') != 'settled']
upcoming_loans = [l for l in loans if l.get('due_date') and 
                   0 <= (datetime.strptime(l['due_date'], '%Y-%m-%d').date() - today).days <= 7]
overdue_count = len(overdue_loans)
total_amount = sum(l.get('amount', 0) for l in loans if l.get('direction') == 'lend')
active_projects = len([p for p in projects if p.get('status') == 'active'])

with col_stat1:
    st.metric("💰 借款总额", f"¥{total_amount:,.0f}")
with col_stat2:
    st.metric("📊 活跃项目", active_projects)
with col_stat3:
    delta_color = "normal" if overdue_count == 0 else "inverse"
    st.metric("⚠️ 逾期", overdue_count, delta=overdue_count if overdue_count > 0 else None, delta_color=delta_color)
with col_stat4:
    st.metric("📅 即将到期", len(upcoming_loans))

st.divider()

# ============ 快捷操作区 ============
st.markdown("### 🎯 快捷操作")

action_col1, action_col2, action_col3, action_col4 = st.columns(4)

with action_col1:
    with st.container(border=True):
        st.markdown("#### 💰 借款")
        st.caption("记录借出/借入资金")
        if st.button("➕ 记一笔", use_container_width=True, type="primary"):
            st.switch_page("pages/11_借款记录.py")

with action_col2:
    with st.container(border=True):
        st.markdown("#### 📄 合同")
        st.caption("存档和管理合同")
        if st.button("➕ 添加合同", use_container_width=True, type="primary"):
            st.switch_page("pages/12_合同管理.py")

with action_col3:
    with st.container(border=True):
        st.markdown("#### 📁 项目")
        st.caption("统一管理法律事务")
        if st.button("➕ 新建项目", use_container_width=True, type="primary"):
            st.switch_page("pages/0_项目管理.py")

with action_col4:
    with st.container(border=True):
        st.markdown("#### 🎙 会议")
        st.caption("记录谈判存证")
        if st.button("➕ 新建会议", use_container_width=True, type="primary"):
            st.switch_page("pages/10_会议谈判援助.py")

st.divider()

# ============ 待办事项 ============
left_col, right_col = st.columns(2)

with left_col:
    st.markdown("### ⚠️ 逾期/即将到期")
    
    urgent_items = []
    
    # 逾期借款
    for loan in overdue_loans[:3]:
        due_date = datetime.strptime(loan['due_date'], '%Y-%m-%d').date()
        days = (today - due_date).days
        urgent_items.append({
            "icon": "💸",
            "title": loan.get('borrower_name', '未知'),
            "desc": f"逾期 {abs(days)} 天 | ¥{loan.get('amount', 0):,.0f}",
            "type": "loan",
            "id": loan['id']
        })
    
    # 即将到期
    for loan in upcoming_loans[:3]:
        due_date = datetime.strptime(loan['due_date'], '%Y-%m-%d').date()
        days = (due_date - today).days
        urgent_items.append({
            "icon": "⏰",
            "title": loan.get('borrower_name', '未知'),
            "desc": f"剩余 {days} 天 | ¥{loan.get('amount', 0):,.0f}",
            "type": "loan",
            "id": loan['id']
        })
    
    if urgent_items:
        for item in urgent_items:
            with st.container(border=True):
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.markdown(f"{item['icon']} **{item['title']}**")
                    st.caption(item['desc'])
                with col_b:
                    if st.button("处理", key=f"quick_{item['type']}_{item['id']}"):
                        st.switch_page("pages/11_借款记录.py")
    else:
        st.success("🎉 暂无紧急事项")

with right_col:
    st.markdown("### 📋 最近项目")
    
    if projects:
        for project in projects[:4]:
            with st.container(border=True):
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    status_icon = {"active": "⚡", "pending": "🕐", "closed": "✅", "disputed": "⚠️"}.get(project.get('status', 'active'), "📁")
                    st.markdown(f"{status_icon} **{project.get('name', '未命名')[:15]}**")
                    st.caption(project.get('category_name', project.get('category', '')))
                with col_b:
                    st.button("→", key=f"goto_proj_{project['id']}")
    else:
        st.info("暂无项目，点击上方新建")

st.divider()

# ============ 辅助工具折叠 ============
with st.expander("🛠 全部工具", expanded=False):
    tool_col1, tool_col2, tool_col3, tool_col4 = st.columns(4)
    
    tools = [
        ("⚔ 对抗性分析", "pages/5_对抗性分析.py", "诉讼策略分析"),
        ("📋 证据管理", "pages/7_证据管理.py", "证据收集整理"),
        ("📊 进度追踪", "pages/4_进度追踪.py", "案件进度跟踪"),
        ("📝 文书生成", "pages/3_文书生成.py", "法律文书起草"),
        ("💬 知识库问答", "pages/2_知识库问答.py", "法律问题咨询"),
        ("⏰ 期限把控", "pages/8_时间把控.py", "重要期限提醒"),
        ("👨‍⚖️ 出庭抗辩", "pages/9_出庭抗辩.py", "庭审辅助"),
        ("📈 合同模板", "pages/16_合同模板.py", "合同范本"),
    ]
    
    for i, (name, page, desc) in enumerate(tools):
        with [tool_col1, tool_col2, tool_col3, tool_col4][i % 4]:
            st.caption(f"**{name}**")
            st.caption(desc)
            if st.button("打开", key=f"tool_{i}"):
                st.switch_page(page)

# ============ 底部 ============
st.divider()
st.markdown("""
<div style="text-align: center; color: gray;">
随身律师 v3.0 | 让法律服务触手可及<br>
</div>
""", unsafe_allow_html=True)
