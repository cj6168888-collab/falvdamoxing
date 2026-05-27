"""
进度追踪 - 随身律师
追踪案件处理进度和里程碑
"""
import streamlit as st
import requests
import os
from datetime import datetime

st.set_page_config(page_title="进度追踪 - 随身律师", page_icon="📊", layout="wide")

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


def get_case_progress(case_id):
    """获取案件进度"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/case/{case_id}/progress", timeout=5)
        if r.status_code == 200:
            return r.json()
        # Fallback: try the senior analysis API
        r2 = requests.get(f"{API_BASE_URL}/api/senior-analysis/case/{case_id}/progress", timeout=5)
        return r2.json() if r2.status_code == 200 else {}
    except:
        return {}


def get_scenarios(case_id):
    """获取情景预测"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/case/{case_id}/scenarios", timeout=10)
        if r.status_code == 200:
            return r.json()
        r2 = requests.get(f"{API_BASE_URL}/api/senior-analysis/case/{case_id}/scenarios", timeout=10)
        return r2.json() if r2.status_code == 200 else []
    except:
        return []


def get_milestones(case_id):
    """获取里程碑"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/case/{case_id}/milestones", timeout=5)
        if r.status_code == 200:
            return r.json()
        r2 = requests.get(f"{API_BASE_URL}/api/senior-analysis/case/{case_id}/milestones", timeout=5)
        return r2.json() if r2.status_code == 200 else []
    except:
        return []


def update_milestone(milestone_id, data):
    """更新里程碑"""
    try:
        r = requests.put(f"{API_BASE_URL}/api/case/milestone/{milestone_id}", json=data, timeout=5)
        if r.status_code == 200:
            return True
        r2 = requests.put(f"{API_BASE_URL}/api/senior-analysis/milestone/{milestone_id}", json=data, timeout=5)
        return r2.status_code == 200
    except:
        return False


# ============ 案件阶段 ============
CASE_STAGES = [
    {"id": "consultation", "name": "咨询阶段", "icon": "💬", "color": "blue"},
    {"id": "evidence", "name": "证据收集", "icon": "📋", "color": "green"},
    {"id": "filing", "name": "立案阶段", "icon": "📝", "color": "orange"},
    {"id": "preparation", "name": "庭前准备", "icon": "📚", "color": "purple"},
    {"id": "hearing", "name": "开庭审理", "icon": "⚖️", "color": "red"},
    {"id": "judgment", "name": "判决阶段", "icon": "📜", "color": "gray"},
    {"id": "execution", "name": "执行阶段", "icon": "🔨", "color": "darkred"},
    {"id": "closed", "name": "已结案", "icon": "✅", "color": "green"},
]


# ============ API检查 ============
if not check_api():
    st.error("❌ 后端服务未连接")
    st.stop()

# ============ 页面标题 ============
st.title("📊 进度追踪")
st.markdown("*追踪案件处理进度和关键里程碑*")
st.markdown("---")

# ============ 初始化 ============
if "selected_case" not in st.session_state:
    st.session_state.selected_case = None

# ============ 侧边栏 ============
with st.sidebar:
    st.header("📊 进度追踪")

    # 选择案件
    cases = get_cases()
    case_options = {f"#{c['id']} {c.get('title', '未命名')[:30]}": c for c in cases}
    selected_label = st.selectbox("选择案件", options=list(case_options.keys()))

    if selected_label:
        st.session_state.selected_case = case_options[selected_label]

    st.divider()

    # 进度概览
    if st.session_state.selected_case:
        case = st.session_state.selected_case
        progress = get_case_progress(case['id'])
        current_stage = progress.get('current_stage', 'consultation')
        progress_percent = progress.get('progress', 0)

        stage_info = next((s for s in CASE_STAGES if s['id'] == current_stage), CASE_STAGES[0])

        st.subheader("📍 当前阶段")
        st.markdown(f"{stage_info['icon']} **{stage_info['name']}**")

        # 进度条
        st.progress(progress_percent / 100, text=f"{progress_percent}%")

# ============ 主内容 ============
if not st.session_state.selected_case:
    st.warning("请先在左侧选择案件")
    st.info("或者前往「案件管理」创建案件")
else:
    case = st.session_state.selected_case
    st.subheader(f"📊 当前案件: {case.get('title', '未命名')}")

    # 获取进度数据
    progress = get_case_progress(case['id'])
    milestones = get_milestones(case['id'])
    scenarios = get_scenarios(case['id'])

    st.markdown("---")

    # 阶段进度可视化
    st.subheader("🗺️ 案件阶段")

    # 显示阶段进度
    current_stage = progress.get('current_stage', 'consultation')
    current_idx = [s['id'] for s in CASE_STAGES].index(current_stage) if current_stage in [s['id'] for s in CASE_STAGES] else 0

    cols = st.columns(len(CASE_STAGES))

    for i, (col, stage) in enumerate(zip(cols, CASE_STAGES)):
        with col:
            if i < current_idx:
                icon = "✅"
            elif i == current_idx:
                icon = stage['icon']
            else:
                icon = "⬜"

            st.markdown(f"**{icon}**")
            st.caption(stage['name'][:4])

    st.markdown("---")

    # 进度统计
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_milestones = len(milestones)
        completed = len([m for m in milestones if m.get('status') == 'completed'])
        st.metric("里程碑", f"{completed}/{total_milestones}")

    with col2:
        upcoming = len([m for m in milestones if m.get('status') == 'pending'])
        st.metric("待完成", upcoming)

    with col3:
        overdue = len([m for m in milestones if m.get('status') == 'overdue'])
        st.metric("已逾期", overdue)

    with col4:
        scenarios_count = len(scenarios)
        st.metric("情景预测", scenarios_count)

    st.markdown("---")

    # 里程碑详情
    st.subheader("📍 里程碑详情")

    if not milestones:
        st.info("暂无里程碑数据")
    else:
        for milestone in milestones:
            status = milestone.get('status', 'pending')
            status_icons = {
                'completed': '✅',
                'pending': '⏳',
                'in_progress': '🔄',
                'overdue': '🚨'
            }
            status_names = {
                'completed': '已完成',
                'pending': '待完成',
                'in_progress': '进行中',
                'overdue': '已逾期'
            }

            with st.container():
                col1, col2, col3 = st.columns([4, 1, 1])

                with col1:
                    st.markdown(f"**{status_icons.get(status, '❓')} {milestone.get('name', '未命名')}**")
                    due_date = milestone.get('due_date', '')
                    if due_date:
                        st.caption(f"截止: {due_date[:10] if len(due_date) > 10 else due_date}")
                    if milestone.get('description'):
                        st.caption(milestone['description'][:50] + "..." if len(str(milestone.get('description', ''))) > 50 else milestone.get('description', ''))

                with col2:
                    st.markdown(f"**{status_names.get(status, status)}**")

                with col3:
                    if status != 'completed':
                        if st.button("完成", key=f"done_m_{milestone.get('id')}"):
                            if update_milestone(milestone['id'], {"status": "completed"}):
                                st.success("已标记完成")
                                st.rerun()
                            else:
                                st.error("更新失败")

                st.markdown("---")

    # 情景预测
    st.subheader("🔮 情景预测")

    if not scenarios:
        st.info("暂无情景预测数据")
    else:
        for scenario in scenarios[:3]:
            probability = scenario.get('probability', 0)
            with st.expander(f"📌 {scenario.get('title', '情景')} ({probability:.0%})"):
                st.write(scenario.get('description', ''))

                if scenario.get('suggestions'):
                    st.markdown("**建议:**")
                    for s in scenario['suggestions']:
                        st.markdown(f"- {s}")

# ============ 返回按钮 ============
st.divider()
if st.button("⬅️ 返回案件详情", use_container_width=True):
    st.switch_page("pages/1_案件详情.py")
