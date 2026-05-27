"""
时间管理 - 随身律师
日程管理、待办事项、时间统计
"""
import streamlit as st
import requests
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="时间管理 - 随身律师", page_icon="📅", layout="wide")

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


def get_meetings():
    """获取会议记录"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/meeting/records", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def create_meeting(data):
    """创建会议"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/meeting/records", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_case_checklist(case_id):
    """获取案件待办清单"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/time-control/case/{case_id}/checklist", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


# ============ API检查 ============
if not check_api():
    st.error("❌ 后端 API 未连接，请先启动服务")
    st.stop()

# ============ 页面标题 ============
st.title("📅 时间管理")
st.markdown("*日程管理、待办事项、会议记录*")
st.markdown("---")

# ============ 初始化 ============
if "selected_case" not in st.session_state:
    st.session_state.selected_case = None
if "show_meeting_form" not in st.session_state:
    st.session_state.show_meeting_form = False

# ============ 侧边栏 ============
with st.sidebar:
    st.header("📅 时间管理")

    # 选择案件
    cases = get_cases()
    case_options = {f"#{c['id']} {c.get('title', '未命名')[:30]}": c for c in cases}
    selected_label = st.selectbox("选择案件（可选）", options=["无"] + list(case_options.keys()))

    if selected_label != "无":
        st.session_state.selected_case = case_options[selected_label]
    else:
        st.session_state.selected_case = None

    st.divider()

    # 今日概览
    st.subheader("📊 今日概览")
    today = datetime.now().date()

    meetings = get_meetings()
    today_meetings = [m for m in meetings if m.get('date', '')[:10] == str(today)]

    st.metric("今日会议", len(today_meetings))

    if st.session_state.selected_case:
        checklist = get_case_checklist(st.session_state.selected_case['id'])
        pending_tasks = [c for c in checklist if not c.get('completed')]
        st.metric("待办事项", len(pending_tasks))

    st.divider()

    # 快捷添加
    if st.button("➕ 添加会议", use_container_width=True):
        st.session_state.show_meeting_form = True

# ============ 主内容 ============
# 今日日程
st.subheader("📅 今日日程")

today = datetime.now().date()
meetings = get_meetings()
today_meetings = [m for m in meetings if m.get('date', '')[:10] == str(today)]

if not today_meetings:
    st.info("今日暂无日程安排")
else:
    for meeting in today_meetings:
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])

            with col1:
                meeting_time = meeting.get('time', '00:00')
                st.markdown(f"**{meeting_time}**")

            with col2:
                st.markdown(f"**{meeting.get('title', '未命名会议')}**")
                if meeting.get('description'):
                    st.caption(meeting['description'][:50] + "..." if len(str(meeting.get('description', ''))) > 50 else meeting.get('description', ''))

            with col3:
                meeting_type = meeting.get('type', 'other')
                type_names = {
                    'negotiation': '谈判',
                    'hearing': '庭审',
                    'mediation': '调解',
                    'consultation': '咨询',
                    'other': '其他'
                }
                st.caption(type_names.get(meeting_type, meeting_type))

            st.markdown("---")

# 添加会议表单
if st.session_state.show_meeting_form:
    with st.form("meeting_form"):
        st.subheader("➕ 添加新日程")

        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("日程标题", placeholder="例如：与对方当事人谈判")
            meeting_type = st.selectbox(
                "日程类型",
                options=["negotiation", "hearing", "mediation", "consultation", "other"],
                format_func=lambda x: {
                    "negotiation": "💬 谈判",
                    "hearing": "⚖️ 庭审",
                    "mediation": "🤝 调解",
                    "consultation": "💼 咨询",
                    "other": "📋 其他"
                }.get(x, x)
            )

        with col2:
            meeting_date = st.date_input("日期", value=today)
            meeting_time = st.time_input("时间", value=datetime.now().time())

        description = st.text_area("备注", height=60)

        submitted = st.form_submit_button("💾 保存", type="primary")
        cancelled = st.form_submit_button("❌ 取消")

        if submitted:
            data = {
                "title": title,
                "type": meeting_type,
                "date": meeting_date.strftime("%Y-%m-%d"),
                "time": meeting_time.strftime("%H:%M"),
                "description": description,
                "case_id": st.session_state.selected_case['id'] if st.session_state.selected_case else None
            }

            result = create_meeting(data)
            if result:
                st.success("日程已添加")
                st.session_state.show_meeting_form = False
                st.rerun()
            else:
                st.error("添加失败")

        if cancelled:
            st.session_state.show_meeting_form = False

    st.markdown("---")

# 待办事项
st.subheader("📋 待办事项")

if st.session_state.selected_case:
    checklist = get_case_checklist(st.session_state.selected_case['id'])

    if not checklist:
        st.info("暂无待办事项")
    else:
        for item in checklist:
            col1, col2 = st.columns([4, 1])

            with col1:
                completed = item.get('completed', False)
                checkbox_label = f"~~{item.get('title', '未命名')}~~" if completed else item.get('title', '未命名')
                st.checkbox(checkbox_label, value=completed, key=f"check_{item.get('id')}")

                if item.get('due_date'):
                    due = datetime.strptime(item['due_date'], '%Y-%m-%d').date()
                    days_left = (due - today).days

                    if days_left < 0:
                        st.caption(f"⚠️ 已逾期 {-days_left} 天 | 截止: {item['due_date'][:10]}")
                    elif days_left == 0:
                        st.caption("🔴 今天到期")
                    else:
                        st.caption(f"截止: {item['due_date'][:10]} ({days_left}天后)")

            with col2:
                st.markdown("&nbsp;")

            st.markdown("---")
else:
    st.info("请先选择案件以查看待办事项")

# 时间统计
st.subheader("📈 时间统计")

col1, col2, col3 = st.columns(3)

with col1:
    this_week = [m for m in meetings if m.get('date', '')[:7] == str(today)[:7]]
    st.metric("本周日程", len(this_week))

with col2:
    this_month = [m for m in meetings if m.get('date', '')[:7] == str(today)[:7]]
    st.metric("本月日程", len(this_month))

with col3:
    # 简化统计
    st.metric("总日程", len(meetings))

# ============ 返回按钮 ============
st.divider()
if st.button("⬅️ 返回案件详情", use_container_width=True):
    st.switch_page("pages/1_案件详情.py")
