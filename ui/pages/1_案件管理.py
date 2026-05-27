"""
案件管理 - 随身律师
案件创建、编辑、查询、删除
"""
import streamlit as st
import requests
import os
from datetime import datetime

st.set_page_config(page_title="案件管理 - 随身律师", page_icon="📁", layout="wide")

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8002")


def check_api():
    """检查API连接"""
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except:
        return False


def get_cases():
    """获取案件列表"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/cases", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_case(case_id):
    """获取单个案件"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/cases/{case_id}", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def create_case(data):
    """创建案件"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/cases", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def update_case(case_id, data):
    """更新案件"""
    try:
        r = requests.put(f"{API_BASE_URL}/api/cases/{case_id}", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def delete_case(case_id):
    """删除案件"""
    try:
        r = requests.delete(f"{API_BASE_URL}/api/cases/{case_id}", timeout=5)
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


# ============ API检查 ============
if not check_api():
    st.error("⚠️ 后端 API 未连接，请先启动服务")
    st.info("后端服务运行地址: http://localhost:8002")
    st.stop()

# ============ 页面标题 ============
st.title("📁 案件管理")
st.markdown("---")

# ============ 初始化 ============
if "selected_case" not in st.session_state:
    st.session_state.selected_case = None
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# ============ 侧边栏 ============
with st.sidebar:
    st.header("📌 案件管理")

    cases = get_cases()
    projects = get_projects()

    # 统计
    active_cases = [c for c in cases if c.get('status') != 'closed']
    closed_cases = [c for c in cases if c.get('status') == 'closed']

    st.metric("案件总数", len(cases))
    st.metric("进行中", len(active_cases))
    st.metric("已结案", len(closed_cases))

    st.divider()

    # 筛选
    st.subheader("🔍 筛选")
    status_filter = st.selectbox(
        "状态",
        options=["全部", "active", "pending", "closed"],
        format_func=lambda x: {"全部": "全部", "active": "进行中", "pending": "待处理", "closed": "已结案"}.get(x, x)
    )

    # 项目筛选
    project_options = ["全部"] + [p['name'] for p in projects]
    project_filter = st.selectbox("项目", options=project_options)

    # 筛选后的案件
    filtered_cases = cases
    if status_filter != "全部":
        filtered_cases = [c for c in filtered_cases if c.get('status') == status_filter]
    if project_filter != "全部":
        filtered_cases = [c for c in filtered_cases if c.get('project_name') == project_filter]

    st.divider()

    # 新建按钮
    if st.button("➕ 新建案件", use_container_width=True):
        st.session_state.show_form = True
        st.session_state.edit_mode = False
        st.session_state.selected_case = None
        st.rerun()

# ============ 新建/编辑表单 ============
if st.session_state.show_form:
    with st.form("case_form", clear_on_submit=False):
        st.subheader("📝 " + ("编辑案件" if st.session_state.edit_mode else "新建案件"))

        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("案件标题", value=st.session_state.selected_case.get('title', '') if st.session_state.selected_case else "")
            case_type = st.selectbox(
                "案件类型",
                options=["合同纠纷", "侵权纠纷", "债务纠纷", "婚姻家庭", "继承纠纷", "劳动争议", "知识产权", "其他"],
                index=0
            )
            project_id = st.selectbox(
                "关联项目",
                options=[None] + [p['id'] for p in projects],
                format_func=lambda x: "无" if x is None else next((p['name'] for p in projects if p['id'] == x), "")
            )

        with col2:
            status_options = ["active", "pending", "closed"]
            current_status = st.session_state.selected_case.get('status', 'active') if st.session_state.selected_case else 'active'
            # 处理不在列表中的状态
            try:
                status_index = status_options.index(current_status)
            except ValueError:
                status_index = 0
            status = st.selectbox(
                "状态",
                options=status_options,
                index=status_index
            )
            priority = st.selectbox(
                "优先级",
                options=["low", "medium", "high"],
                format_func=lambda x: {"low": "低", "medium": "中", "high": "高"}.get(x, x)
            )

        description = st.text_area("案件描述", value=st.session_state.selected_case.get('description', '') if st.session_state.selected_case else "", height=100)

        col_b1, col_b2, col_b3 = st.columns([1, 1, 1])

        with col_b1:
            submitted = st.form_submit_button("💾 保存", use_container_width=True)
        with col_b2:
            canceled = st.form_submit_button("❌ 取消", use_container_width=True)
        with col_b3:
            if st.session_state.edit_mode and st.session_state.selected_case:
                deleted = st.form_submit_button("🗑️ 删除", use_container_width=True)
            else:
                deleted = False

        if submitted:
            data = {
                "title": title,
                "case_type": case_type,
                "status": status,
                "priority": priority,
                "description": description,
                "project_id": project_id
            }

            if st.session_state.edit_mode and st.session_state.selected_case:
                result = update_case(st.session_state.selected_case['id'], data)
                if result:
                    st.success("案件已更新")
                    st.session_state.show_form = False
                    st.rerun()
                else:
                    st.error("更新失败")
            else:
                result = create_case(data)
                if result:
                    st.success("案件已创建")
                    st.session_state.show_form = False
                    st.rerun()
                else:
                    st.error("创建失败")

        if canceled:
            st.session_state.show_form = False
            st.rerun()

        if deleted:
            if delete_case(st.session_state.selected_case['id']):
                st.success("案件已删除")
                st.session_state.show_form = False
                st.session_state.selected_case = None
                st.rerun()
            else:
                st.error("删除失败")

    st.markdown("---")

# ============ 案件列表 ============
st.subheader(f"📋 案件列表 ({len(filtered_cases)})")

if not filtered_cases:
    st.info("暂无案件，点击左侧「新建案件」创建")
else:
    # 显示案件卡片
    for case in filtered_cases:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                status_icon = {"active": "🟢", "pending": "🟡", "closed": "⚫"}.get(case.get('status', 'active'), "⚪")
                priority_color = {"low": "⚪", "medium": "🟡", "high": "🔴"}.get(case.get('priority', 'medium'), "⚪")

                st.markdown(f"**{status_icon} {case.get('title', '未命名案件')}** {priority_color}")
                st.caption(f"类型: {case.get('case_type', '未分类')} | 项目: {case.get('project_name', '无')}")

            with col2:
                st.markdown("&nbsp;")
                if st.button("✏️ 编辑", key=f"edit_{case['id']}"):
                    st.session_state.show_form = True
                    st.session_state.edit_mode = True
                    st.session_state.selected_case = case
                    st.rerun()

            with col3:
                st.markdown("&nbsp;")
                if st.button("📖 详情", key=f"view_{case['id']}"):
                    st.session_state.selected_case = case
                    st.switch_page("pages/1_案件详情.py")

            st.markdown("---")
