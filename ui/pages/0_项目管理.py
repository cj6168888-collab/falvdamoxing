"""
项目管理 - 随身律师
项目创建、编辑、关联案件
"""
import streamlit as st
import requests
import os
from datetime import datetime

st.set_page_config(page_title="项目管理 - 随身律师", page_icon="📂", layout="wide")

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8002")


def check_api():
    """检查API连接"""
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except:
        return False


def get_projects():
    """获取项目列表"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/projects/", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_project(project_id):
    """获取项目详情"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/projects/{project_id}", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def create_project(data):
    """创建项目"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/projects/", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def update_project(project_id, data):
    """更新项目"""
    try:
        r = requests.put(f"{API_BASE_URL}/api/projects/{project_id}", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def delete_project(project_id):
    """删除项目"""
    try:
        r = requests.delete(f"{API_BASE_URL}/api/projects/{project_id}", timeout=5)
        return r.status_code == 200
    except:
        return False


def archive_project(project_id):
    """归档项目"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/projects/{project_id}/archive", timeout=5)
        return r.status_code == 200
    except:
        return False


def get_project_stats():
    """获取统计"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/projects/stats/summary", timeout=5)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}


# ============ 项目类型 ============
PROJECT_CATEGORIES = [
    {"id": "lending", "name": "借贷纠纷", "icon": "💰", "desc": "民间借贷、金融借款"},
    {"id": "contract", "name": "合同纠纷", "icon": "📄", "desc": "买卖合同、服务合同"},
    {"id": "tort", "name": "侵权纠纷", "icon": "⚠️", "desc": "人身损害、财产损害"},
    {"id": "marriage", "name": "婚姻家庭", "icon": "💒", "desc": "离婚、继承、抚养"},
    {"id": "labor", "name": "劳动争议", "icon": "👷", "desc": "工资、解雇、社保"},
    {"id": "property", "name": "物权纠纷", "icon": "🏠", "desc": "房产、物业纠纷"},
    {"id": "other", "name": "其他", "icon": "📋", "desc": "其他法律事务"},
]


# ============ API检查 ============
if not check_api():
    st.error("❌ 后端 API 未连接，请先启动服务")
    st.stop()

# ============ 页面标题 ============
st.title("📂 项目管理")
st.markdown("*统一管理您的法律事务项目*")
st.markdown("---")

# ============ 初始化 ============
if "selected_project" not in st.session_state:
    st.session_state.selected_project = None
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# ============ 统计信息 ============
stats = get_project_stats()

col1, col2, col3, col4 = st.columns(4)

with col1:
    total = stats.get('total', 0)
    st.metric("项目总数", total)

with col2:
    active = stats.get('active', 0)
    st.metric("进行中", active)

with col3:
    archived = stats.get('archived', 0)
    st.metric("已归档", archived)

with col4:
    with_amount = stats.get('with_amount', 0)
    st.metric("涉及金额", f"¥{with_amount:,.0f}" if with_amount else "-")

st.markdown("---")

# ============ 侧边栏 ============
with st.sidebar:
    st.header("📂 项目管理")

    projects = get_projects()

    # 筛选
    st.subheader("🔍 筛选")
    category_filter = st.selectbox(
        "项目类型",
        options=["全部"] + [c['name'] for c in PROJECT_CATEGORIES]
    )

    status_filter = st.selectbox(
        "状态",
        options=["全部", "active", "archived"]
    )

    # 筛选后的项目
    filtered_projects = projects
    if category_filter != "全部":
        filtered_projects = [p for p in filtered_projects if p.get('category') == category_filter]
    if status_filter != "全部":
        filtered_projects = [p for p in filtered_projects if p.get('status') == status_filter]

    st.divider()

    # 新建按钮
    if st.button("➕ 新建项目", use_container_width=True):
        st.session_state.show_form = True
        st.session_state.edit_mode = False
        st.session_state.selected_project = None

# ============ 新建/编辑表单 ============
if st.session_state.show_form:
    with st.form("project_form", clear_on_submit=False):
        st.subheader("📝 " + ("编辑项目" if st.session_state.edit_mode else "新建项目"))

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "项目名称",
                value=st.session_state.selected_project.get('name', '') if st.session_state.selected_project else ""
            )

            category = st.selectbox(
                "项目类型",
                options=[c['id'] for c in PROJECT_CATEGORIES],
                format_func=lambda x: next((f"{c['icon']} {c['name']}" for c in PROJECT_CATEGORIES if c['id'] == x), x),
                index=0 if not st.session_state.selected_project else
                      [c['id'] for c in PROJECT_CATEGORIES].index(st.session_state.selected_project.get('category', 'other'))
            )

            amount = st.number_input(
                "涉及金额",
                min_value=0.0,
                value=float(st.session_state.selected_project.get('amount', 0)) if st.session_state.selected_project else 0.0,
                step=1000.0
            )

        with col2:
            start_date = st.date_input(
                "开始日期",
                value=datetime.strptime(st.session_state.selected_project['start_date'], '%Y-%m-%d').date()
                if st.session_state.selected_project and st.session_state.selected_project.get('start_date')
                else datetime.now()
            )

            end_date = st.date_input(
                "结束日期",
                value=datetime.strptime(st.session_state.selected_project['end_date'], '%Y-%m-%d').date()
                if st.session_state.selected_project and st.session_state.selected_project.get('end_date')
                else datetime.now()
            )

            status = st.selectbox(
                "状态",
                options=["active", "pending", "archived"],
                format_func=lambda x: {"active": "进行中", "pending": "待启动", "archived": "已归档"}.get(x, x)
            )

        description = st.text_area(
            "项目描述",
            value=st.session_state.selected_project.get('description', '') if st.session_state.selected_project else "",
            height=80
        )

        col_b1, col_b2, col_b3 = st.columns([1, 1, 1])

        with col_b1:
            submitted = st.form_submit_button("💾 保存", type="primary", use_container_width=True)

        with col_b2:
            cancelled = st.form_submit_button("❌ 取消", use_container_width=True)

        with col_b3:
            if st.session_state.edit_mode and st.session_state.selected_project:
                deleted = st.form_submit_button("🗑️ 删除", use_container_width=True)
            else:
                deleted = False

        if submitted:
            data = {
                "name": name,
                "category": category,
                "amount": amount,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "status": status,
                "description": description
            }

            if st.session_state.edit_mode and st.session_state.selected_project:
                result = update_project(st.session_state.selected_project['id'], data)
                if result:
                    st.success("项目已更新")
                    st.session_state.show_form = False
                    st.rerun()
                else:
                    st.error("更新失败")
            else:
                result = create_project(data)
                if result:
                    st.success("项目已创建")
                    st.session_state.show_form = False
                    st.rerun()
                else:
                    st.error("创建失败")

        if cancelled:
            st.session_state.show_form = False
            st.rerun()

        if deleted:
            if delete_project(st.session_state.selected_project['id']):
                st.success("项目已删除")
                st.session_state.show_form = False
                st.session_state.selected_project = None
                st.rerun()
            else:
                st.error("删除失败")

    st.markdown("---")

# ============ 项目列表 ============
st.subheader(f"📋 项目列表 ({len(filtered_projects)})")

if not filtered_projects:
    st.info("暂无项目，点击左侧「新建项目」创建")
else:
    for project in filtered_projects:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                category_info = next((c for c in PROJECT_CATEGORIES if c['id'] == project.get('category')), None)
                category_text = f"{category_info['icon']} {category_info['name']}" if category_info else "其他"
                status_text = {"active": "🟢", "pending": "🟡", "archived": "⚫"}.get(project.get('status', 'active'), "⚪")

                st.markdown(f"**{status_text} {project.get('name', '未命名项目')}**")
                st.caption(f"{category_text} | 金额: ¥{project.get('amount', 0):,.0f}")

            with col2:
                st.markdown("&nbsp;")
                if st.button("✏️ 编辑", key=f"edit_p_{project['id']}"):
                    st.session_state.show_form = True
                    st.session_state.edit_mode = True
                    st.session_state.selected_project = project
                    st.rerun()

            with col3:
                st.markdown("&nbsp;")
                if st.button("📖 详情", key=f"view_p_{project['id']}"):
                    st.session_state.selected_project = project
                    st.switch_page("pages/1_项目详情.py")

            with col4:
                st.markdown("&nbsp;")
                if st.button("📁 归档", key=f"archive_p_{project['id']}"):
                    if archive_project(project['id']):
                        st.success("已归档")
                        st.rerun()
                    else:
                        st.error("归档失败")

            st.markdown("---")
