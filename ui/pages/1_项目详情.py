"""
项目详情 - 随身律师
项目详细信息和关联数据
"""
import streamlit as st
import requests
import os
from datetime import datetime

st.set_page_config(page_title="项目详情 - 随身律师", page_icon="📂", layout="wide")

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8002")


def check_api():
    """检查API连接"""
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except:
        return False


def get_project(project_id):
    """获取项目详情"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/projects/{project_id}", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_projects():
    """获取项目列表"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/projects/", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def update_project(project_id, data):
    """更新项目"""
    try:
        r = requests.put(f"{API_BASE_URL}/api/projects/{project_id}", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_project_documents(project_id):
    """获取项目文档"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/projects/{project_id}/documents", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_project_communications(project_id):
    """获取项目沟通记录"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/projects/{project_id}/communications", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_project_milestones(project_id):
    """获取项目里程碑"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/projects/{project_id}/milestones", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_project_evidence(project_id):
    """获取项目证据"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/projects/{project_id}/evidence", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_project_contracts(project_id):
    """获取项目合同"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/projects/{project_id}/contracts", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_project_risks(project_id):
    """获取项目风险"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/projects/{project_id}/risks", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


# ============ 项目类型 ============
PROJECT_CATEGORIES = [
    {"id": "lending", "name": "借贷纠纷", "icon": "💰"},
    {"id": "contract", "name": "合同纠纷", "icon": "📄"},
    {"id": "tort", "name": "侵权纠纷", "icon": "⚠️"},
    {"id": "marriage", "name": "婚姻家庭", "icon": "💒"},
    {"id": "labor", "name": "劳动争议", "icon": "👷"},
    {"id": "property", "name": "物权纠纷", "icon": "🏠"},
    {"id": "other", "name": "其他", "icon": "📋"},
]


# ============ API检查 ============
if not check_api():
    st.error("❌ 后端 API 未连接，请先启动服务")
    st.stop()

# ============ 获取当前项目 ============
if "selected_project" not in st.session_state or st.session_state.selected_project is None:
    projects = get_projects()
    if projects:
        st.session_state.selected_project = projects[0]
    else:
        st.error("没有可用的项目")
        st.info("请先在项目管理中创建项目")
        st.stop()

current_project = st.session_state.selected_project
project_id = current_project.get('id')

# ============ 页面标题 ============
st.title(f"📂 项目详情: {current_project.get('name', '未命名')}")

# ============ 项目基本信息 ============
col1, col2, col3, col4 = st.columns(4)

with col1:
    category = current_project.get('category', 'other')
    category_info = next((c for c in PROJECT_CATEGORIES if c['id'] == category), PROJECT_CATEGORIES[-1])
    st.metric("项目类型", f"{category_info['icon']} {category_info['name']}")

with col2:
    amount = current_project.get('amount', 0)
    st.metric("涉及金额", f"¥{amount:,.2f}" if amount else "-")

with col3:
    status = current_project.get('status', 'active')
    status_text = {"active": "🟢 进行中", "pending": "🟡 待启动", "archived": "⚫ 已归档"}.get(status, status)
    st.metric("状态", status_text)

with col4:
    start_date = current_project.get('start_date', '')
    if start_date:
        st.metric("开始日期", start_date[:10])
    else:
        st.metric("开始日期", "-")

st.markdown("---")

# ============ 项目描述 ============
if current_project.get('description'):
    with st.expander("📝 项目描述", expanded=True):
        st.write(current_project['description'])

st.markdown("---")

# ============ 关联数据概览 ============
st.subheader("📊 关联数据")

col1, col2, col3, col4 = st.columns(4)

with col1:
    documents = get_project_documents(project_id)
    st.metric("📄 文档", len(documents))

with col2:
    contracts = get_project_contracts(project_id)
    st.metric("📑 合同", len(contracts))

with col3:
    evidence = get_project_evidence(project_id)
    st.metric("📋 证据", len(evidence))

with col4:
    milestones = get_project_milestones(project_id)
    st.metric("🎯 里程碑", len(milestones))

st.markdown("---")

# ============ 快捷操作 ============
st.subheader("⚡ 快捷操作")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📄 合同管理", use_container_width=True):
        st.switch_page("pages/12_合同管理.py")

with col2:
    if st.button("💰 借款记录", use_container_width=True):
        st.switch_page("pages/11_借款记录.py")

with col3:
    if st.button("📋 证据管理", use_container_width=True):
        st.switch_page("pages/7_证据管理.py")

with col4:
    if st.button("📊 进度追踪", use_container_width=True):
        st.switch_page("pages/4_进度追踪.py")

st.markdown("---")

# ============ 详细信息 ============
tab1, tab2, tab3, tab4 = st.tabs(["📄 文档", "📑 合同", "📋 证据", "🎯 里程碑"])

with tab1:
    st.subheader("📄 项目文档")

    if not documents:
        st.info("暂无文档")
    else:
        for doc in documents[:10]:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{doc.get('name', '未命名')}**")
                    st.caption(f"类型: {doc.get('type', '其他')}")
                with col2:
                    if st.button("查看", key=f"view_doc_{doc.get('id')}"):
                        st.info("文档查看功能开发中")
                st.markdown("---")

with tab2:
    st.subheader("📑 项目合同")

    if not contracts:
        st.info("暂无合同")
    else:
        for contract in contracts:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{contract.get('title', '未命名')}**")
                    st.caption(f"金额: ¥{contract.get('amount', 0):,.2f}")
                with col2:
                    status = contract.get('status', 'pending')
                    status_text = {"pending": "🟡 待签署", "active": "🟢 执行中", "completed": "✅ 已完成"}.get(status, status)
                    st.markdown(status_text)
                with col3:
                    if st.button("查看", key=f"view_contract_{contract.get('id')}"):
                        st.info("合同详情功能开发中")
                st.markdown("---")

with tab3:
    st.subheader("📋 项目证据")

    if not evidence:
        st.info("暂无证据")
    else:
        for ev in evidence:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{ev.get('name', '未命名')}**")
                    st.caption(f"类型: {ev.get('type', '其他')}")
                with col2:
                    if st.button("查看", key=f"view_evidence_{ev.get('id')}"):
                        st.info("证据详情功能开发中")
                st.markdown("---")

with tab4:
    st.subheader("🎯 里程碑")

    if not milestones:
        st.info("暂无里程碑")
    else:
        for milestone in milestones:
            status = milestone.get('status', 'pending')
            status_icons = {"completed": "✅", "pending": "⏳", "in_progress": "🔄", "overdue": "🚨"}
            status_icon = status_icons.get(status, "❓")

            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{status_icon} {milestone.get('name', '未命名')}**")
                    if milestone.get('due_date'):
                        st.caption(f"截止: {milestone['due_date'][:10]}")
                with col2:
                    if status != 'completed':
                        if st.button("完成", key=f"done_mile_{milestone.get('id')}"):
                            st.info("标记完成功能开发中")
                st.markdown("---")

# ============ 项目列表 ============
st.divider()
st.subheader("📂 其他项目")

projects = get_projects()
other_projects = [p for p in projects if p.get('id') != project_id]

if other_projects:
    for proj in other_projects[:5]:
        col1, col2 = st.columns([4, 1])
        with col1:
            category_info = next((c for c in PROJECT_CATEGORIES if c['id'] == proj.get('category')), PROJECT_CATEGORIES[-1])
            st.markdown(f"**{category_info['icon']} {proj.get('name', '未命名')}**")
            st.caption(f"金额: ¥{proj.get('amount', 0):,.2f}")
        with col2:
            if st.button("切换", key=f"switch_proj_{proj['id']}"):
                st.session_state.selected_project = proj
                st.rerun()
        st.markdown("---")

# ============ 返回按钮 ============
st.divider()
if st.button("⬅️ 返回项目管理", use_container_width=True):
    st.switch_page("pages/0_项目管理.py")
