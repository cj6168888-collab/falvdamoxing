"""
出庭抗辩 - 随身律师
庭审准备、发言提纲、质证意见
"""
import streamlit as st
import requests
import os
from datetime import datetime

st.set_page_config(page_title="出庭抗辩 - 随身律师", page_icon="🎙", layout="wide")

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


def get_hearings(case_id):
    """获取庭审记录"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/hearing/case/{case_id}/hearings", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def create_hearing(case_id, hearing_data):
    """创建庭审"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/hearing/case/{case_id}/hearing", json=hearing_data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def generate_opening_statement(case_id):
    """生成开庭发言"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/hearing/case/{case_id}/opening-statement", timeout=60)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def generate_closing_statement(case_id):
    """生成结案陈词"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/hearing/case/{case_id}/closing-statement", timeout=60)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def generate_cross_examination(case_id):
    """生成质证提纲"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/hearing/case/{case_id}/cross-examination", timeout=60)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_speaking_guides():
    """获取发言指南"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/hearing/speaking-guides", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def realtime_analysis(evidence_text):
    """实时质证分析"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/hearing/realtime-analysis", json={"evidence": evidence_text}, timeout=30)
        return r.json() if r.status_code == 200 else None
    except:
        return None


# ============ 庭审流程 ============
HEARING_FLOW = [
    {"stage": "开场", "name": "宣布开庭", "duration": "2分钟", "icon": "🔔"},
    {"stage": "陈述", "name": "原告陈述", "duration": "10分钟", "icon": "📢"},
    {"stage": "答辩", "name": "被告答辩", "duration": "10分钟", "icon": "🛡️"},
    {"stage": "举证", "name": "举证质证", "duration": "20分钟", "icon": "📋"},
    {"stage": "询问", "name": "法庭询问", "duration": "15分钟", "icon": "❓"},
    {"stage": "辩论", "name": "法庭辩论", "duration": "20分钟", "icon": "⚔️"},
    {"stage": "最后陈述", "name": "最后陈述", "duration": "5分钟", "icon": "🎤"},
    {"stage": "休庭", "name": "宣布休庭", "duration": "-", "icon": "⏸️"},
]


# ============ API检查 ============
if not check_api():
    st.error("❌ 后端服务未连接")
    st.stop()

# ============ 页面标题 ============
st.title("🎙 出庭抗辩")
st.markdown("*庭审准备、发言提纲、质证意见 — 让每一次发言都有准备*")
st.markdown("---")

# ============ 初始化 ============
if "selected_case" not in st.session_state:
    st.session_state.selected_case = None
if "current_statement" not in st.session_state:
    st.session_state.current_statement = None

# ============ 侧边栏 ============
with st.sidebar:
    st.header("🎙 出庭抗辩")

    # 选择案件
    cases = get_cases()
    case_options = {f"#{c['id']} {c.get('title', '未命名')[:30]}": c for c in cases}
    selected_label = st.selectbox("选择案件", options=list(case_options.keys()))

    if selected_label:
        st.session_state.selected_case = case_options[selected_label]

    st.divider()

    # 庭审流程参考
    st.subheader("📋 庭审流程")
    for step in HEARING_FLOW:
        st.caption(f"{step['icon']} {step['name']} ({step['duration']})")

    st.divider()

    # 发言指南
    st.subheader("📚 发言指南")
    guides = get_speaking_guides()
    for guide in guides[:3]:
        st.caption(f"• {guide.get('title', '未命名')}")

# ============ 主内容 ============
if not st.session_state.selected_case:
    st.warning("请先在左侧选择案件")
    st.info("或者前往「案件管理」创建案件")
else:
    case = st.session_state.selected_case
    st.subheader(f"🎙 当前案件: {case.get('title', '未命名')}")

    # 庭审统计
    hearings = get_hearings(case['id'])
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("庭审次数", len(hearings))

    with col2:
        completed = len([h for h in hearings if h.get('status') == 'completed'])
        st.metric("已完成", completed)

    with col3:
        upcoming = len([h for h in hearings if h.get('status') == 'scheduled'])
        st.metric("待开庭", upcoming)

    st.markdown("---")

    # 庭审准备工具
    st.subheader("🛠️ 庭审准备工具")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📢 开庭发言**")
        st.caption("生成原告/被告开庭发言稿")
        if st.button("生成开庭发言", use_container_width=True):
            with st.spinner("生成中..."):
                result = generate_opening_statement(case['id'])
                if result:
                    st.session_state.current_statement = ("opening", result)
                    st.success("生成完成")
                else:
                    st.info("暂无可用数据")

    with col2:
        st.markdown("**🎤 结案陈词**")
        st.caption("生成总结性结案陈词")
        if st.button("生成结案陈词", use_container_width=True):
            with st.spinner("生成中..."):
                result = generate_closing_statement(case['id'])
                if result:
                    st.session_state.current_statement = ("closing", result)
                    st.success("生成完成")
                else:
                    st.info("暂无可用数据")

    with col3:
        st.markdown("**❓ 质证提纲**")
        st.caption("生成对对方证据的质证意见")
        if st.button("生成质证提纲", use_container_width=True):
            with st.spinner("生成中..."):
                result = generate_cross_examination(case['id'])
                if result:
                    st.session_state.current_statement = ("cross", result)
                    st.success("生成完成")
                else:
                    st.info("暂无可用数据")

    st.markdown("---")

    # 显示生成的内容
    if st.session_state.current_statement:
        statement_type, content = st.session_state.current_statement

        type_names = {
            "opening": "开庭发言",
            "closing": "结案陈词",
            "cross": "质证提纲"
        }

        st.subheader(f"📝 {type_names.get(statement_type, '发言稿')}")

        with st.expander("查看生成的内容", expanded=True):
            if isinstance(content, dict):
                st.markdown(content.get('content', content.get('text', str(content))))
            elif isinstance(content, str):
                st.markdown(content)
            else:
                st.json(content)

        if st.button("💾 复制到剪贴板"):
            st.info("复制功能开发中")

        if st.button("❌ 清除"):
            st.session_state.current_statement = None
            st.rerun()

    st.markdown("---")

    # 实时质证分析
    st.subheader("⚡ 实时质证分析")

    evidence_text = st.text_area(
        "输入需要质证的证据内容",
        placeholder="粘贴对方提供的证据材料...",
        height=120
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        analyze_btn = st.button("🔍 分析质证要点", type="primary", use_container_width=True)

    with col2:
        if st.button("🗑️ 清空", use_container_width=True):
            st.rerun()

    if analyze_btn and evidence_text:
        with st.spinner("分析中..."):
            result = realtime_analysis(evidence_text)
            if result:
                st.success("分析完成")

                with st.expander("📊 质证分析结果", expanded=True):
                    st.json(result)
            else:
                st.error("分析失败")

    st.markdown("---")

    # 庭审历史
    st.subheader("📜 庭审历史")

    hearings = get_hearings(case['id'])

    if not hearings:
        st.info("暂无庭审记录")
    else:
        for hearing in hearings[:5]:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    hearing_date = hearing.get('hearing_date', '')[:10] if hearing.get('hearing_date') else '未设定'
                    status = hearing.get('status', 'scheduled')
                    status_text = {'scheduled': '待开庭', 'completed': '已完成', 'cancelled': '已取消'}.get(status, status)
                    status_icon = {'scheduled': '📅', 'completed': '✅', 'cancelled': '❌'}.get(status, '❓')

                    st.markdown(f"**{status_icon} {hearing_date} 庭审**")
                    st.caption(f"状态: {status_text}")

                with col2:
                    if st.button("查看", key=f"view_h_{hearing.get('id')}"):
                        st.session_state.viewing_hearing = hearing

                with col3:
                    if st.button("发言", key=f"prep_h_{hearing.get('id')}"):
                        st.info("庭审准备功能开发中")

                st.markdown("---")

# ============ 返回按钮 ============
st.divider()
if st.button("⬅️ 返回案件详情", use_container_width=True):
    st.switch_page("pages/1_案件详情.py")
