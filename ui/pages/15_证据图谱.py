"""
证据图谱 - 随身律师 V2
可视化证据关系、证据状态统计、智能问答引导
"""
import streamlit as st
import requests
import os
import json

st.set_page_config(page_title="证据图谱V2 - 随身律师", page_icon="🔗", layout="wide")

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


def get_evidence_graph(case_id):
    """获取证据图谱数据"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/evidence-graph/evidence/list", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_graph_summary():
    """获取图谱摘要"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/evidence-graph/summary", timeout=5)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}


def get_graph_statistics():
    """获取统计信息"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/evidence-graph/statistics", timeout=5)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}


def get_evidence_types():
    """获取证据类型"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/evidence-graph/types", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_relationship_types():
    """获取关系类型"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/evidence-graph/relationship-types", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def analyze_evidence(evidence_data):
    """分析证据"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/evidence-graph/evidence/analyze", json=evidence_data, timeout=30)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def analyze_relationships(case_id):
    """分析证据关系"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/evidence-graph/relationships/analyze", json={"case_id": case_id}, timeout=60)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_graph_data():
    """获取图谱可视化数据"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/evidence-graph/graph/data", timeout=5)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}


def get_evidence_context(evidence_id):
    """获取证据上下文"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/evidence-qa/evidence/{evidence_id}/context", timeout=5)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}


# ============ 证据类型定义 ============
EVIDENCE_TYPES = [
    {"id": "contract", "name": "合同协议", "icon": "📄", "color": "#4CAF50"},
    {"id": "invoice", "name": "票据凭证", "icon": "🧾", "color": "#2196F3"},
    {"id": "correspondence", "name": "函件通信", "icon": "✉️", "color": "#9C27B0"},
    {"id": "identification", "name": "身份证明", "icon": "🪪", "color": "#FF9800"},
    {"id": "communication", "name": "通讯记录", "icon": "💬", "color": "#00BCD4"},
    {"id": "witness", "name": "证人证言", "icon": "👤", "color": "#795548"},
    {"id": "appraisal", "name": "鉴定意见", "icon": "🔬", "color": "#607D8B"},
    {"id": "video_audio", "name": "视听资料", "icon": "🎬", "color": "#E91E63"},
    {"id": "other", "name": "其他证据", "icon": "📎", "color": "#9E9E9E"},
]


# ============ API检查 ============
if not check_api():
    st.error("❌ 后端 API 未连接，请先启动服务")
    st.stop()

# ============ 页面标题 ============
st.title("🔗 证据图谱 V2")
st.markdown("*可视化证据关系网络 — 直观展示证据之间的关联*")
st.markdown("---")

# ============ 初始化 ============
if "selected_case" not in st.session_state:
    st.session_state.selected_case = None
if "graph_view" not in st.session_state:
    st.session_state.graph_view = "network"  # network, timeline, statistics

# ============ 侧边栏 ============
with st.sidebar:
    st.header("🔗 证据图谱")

    # 选择案件
    cases = get_cases()
    case_options = {f"#{c['id']} {c.get('title', '未命名')[:30]}": c for c in cases}
    selected_label = st.selectbox("选择案件", options=list(case_options.keys()))

    if selected_label:
        st.session_state.selected_case = case_options[selected_label]

    st.divider()

    # 图谱统计
    if st.session_state.selected_case:
        stats = get_graph_statistics()
        st.metric("证据总数", stats.get('total', 0))
        st.metric("关系数", stats.get('relationships', 0))
    else:
        st.metric("证据总数", 0)
        st.metric("关系数", 0)

    st.divider()

    # 视图切换
    st.subheader("📊 视图切换")
    view_options = ["network", "statistics", "timeline"]
    view_labels = ["🔗 关系网络", "📈 类型统计", "📅 时间线"]
    view_index = st.radio("视图", options=range(len(view_options)), format_func=lambda x: view_labels[x])

    st.divider()

    # 分析工具
    st.subheader("🔧 分析工具")

    if st.button("🔗 分析关系", use_container_width=True):
        st.session_state.show_analysis = True

    if st.button("❓ 诊断缺口", use_container_width=True):
        st.session_state.show_diagnosis = True

# ============ 主内容 ============
if not st.session_state.selected_case:
    st.warning("请先在左侧选择案件")
    st.info("或者前往「案件管理」创建案件")
else:
    case = st.session_state.selected_case
    st.subheader(f"🔗 当前案件: {case.get('title', '未命名')}")

    # 获取图谱数据
    graph_data = get_graph_data()
    evidence_list = get_evidence_graph(case['id'])

    st.markdown("---")

    # ============ 关系网络视图 ============
    if view_index == 0:  # network
        st.subheader("🔗 证据关系网络")

        # 检查是否有可视化库
        try:
            import plotly.graph_objects as go
            import pandas as pd

            if graph_data and graph_data.get('nodes'):
                # 创建网络图
                import math
                nodes = graph_data.get('nodes', [])
                edges = graph_data.get('edges', [])

                # 创建节点位置
                pos = {}
                for i, node in enumerate(nodes):
                    angle = 2 * math.pi * i / len(nodes)
                    pos[node['id']] = (0.5 + 0.4 * math.cos(angle), 0.5 + 0.4 * math.sin(angle))

                # 创建边
                edge_x = []
                edge_y = []
                for edge in edges:
                    if edge['source'] in pos and edge['target'] in pos:
                        edge_x.extend([pos[edge['source']][0], pos[edge['target']][0], None])
                        edge_y.extend([pos[edge['source']][1], pos[edge['target']][1], None])

                # 绘制边
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=1, color='#888'),
                    hoverinfo='none',
                    mode='lines'
                ))

                # 绘制节点
                node_x = [pos[n['id']][0] for n in nodes]
                node_y = [pos[n['id']][1] for n in nodes]

                # 获取节点颜色
                node_colors = []
                for node in nodes:
                    ev_type = next((t for t in EVIDENCE_TYPES if t['id'] == node.get('type')), None)
                    node_colors.append(ev_type['color'] if ev_type else '#9E9E9E')

                fig.add_trace(go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers+text',
                    hoverinfo='text',
                    text=[n.get('name', '')[:15] for n in nodes],
                    textposition="top center",
                    marker=dict(
                        size=20,
                        color=node_colors,
                        line=dict(width=2, color='white')
                    )
                ))

                fig.update_layout(
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(l=0, r=0, t=0, b=0),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    height=500
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无证据关系数据，请先添加证据")

        except ImportError:
            st.info("需要安装 plotly 库来显示关系图")
            st.code("pip install plotly")

        # 证据列表
        st.subheader("📋 证据列表")

        if not evidence_list:
            st.info("暂无证据，请先在证据管理中添加")
        else:
            for evidence in evidence_list:
                ev_type = next((t for t in EVIDENCE_TYPES if t['id'] == evidence.get('type')), None)
                type_icon = ev_type['icon'] if ev_type else "📎"
                type_name = ev_type['name'] if ev_type else "其他"

                with st.expander(f"{type_icon} {evidence.get('name', '未命名')} ({type_name})"):
                    st.json(evidence)

    # ============ 统计视图 ============
    elif view_index == 1:  # statistics
        st.subheader("📈 证据统计")

        stats = get_graph_statistics()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("证据总数", stats.get('total', 0))
        with col2:
            st.metric("关系总数", stats.get('relationships', 0))
        with col3:
            st.metric("证据类型", len(stats.get('by_type', {})))
        with col4:
            completeness = stats.get('completeness', 0)
            st.metric("完整度", f"{completeness:.0%}")

        st.markdown("---")

        # 按类型统计
        st.subheader("📊 证据类型分布")

        types_data = stats.get('by_type', {})

        if types_data:
            try:
                import plotly.express as px

                df_data = [{"类型": t['name'], "数量": t['count']} for t in [
                    {"name": k, "count": v} for k, v in types_data.items()
                ]]

                fig = px.pie(df_data, values='数量', names='类型', title='证据类型分布')
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                for t_name, t_count in types_data.items():
                    st.markdown(f"- **{t_name}**: {t_count}个")
        else:
            st.info("暂无统计数据")

        st.markdown("---")

        # 证据状态
        st.subheader("📋 证据状态")

        status_data = stats.get('by_status', {})

        if status_data:
            for status, count in status_data.items():
                status_info = {
                    'verified': ('✅ 已验证', 'green'),
                    'pending': ('⏳ 待验证', 'yellow'),
                    'rejected': ('❌ 需补充', 'red')
                }.get(status, (status, 'gray'))

                st.markdown(f"{status_info[0]} **{status}**: {count}个")

    # ============ 时间线视图 ============
    else:  # timeline
        st.subheader("📅 证据时间线")

        timeline_data = evidence_list  # 假设按时间排序

        if not timeline_data:
            st.info("暂无时间线数据")
        else:
            for evidence in timeline_data:
                ev_type = next((t for t in EVIDENCE_TYPES if t['id'] == evidence.get('type')), None)
                type_icon = ev_type['icon'] if ev_type else "📎"

                created = evidence.get('created_at', '')[:10] if evidence.get('created_at') else '未知日期'

                with st.container():
                    col1, col2 = st.columns([1, 4])

                    with col1:
                        st.markdown(f"**{created}**")

                    with col2:
                        st.markdown(f"{type_icon} **{evidence.get('name', '未命名')}**")
                        st.caption(evidence.get('description', '')[:100] if evidence.get('description') else '')

                    st.markdown("---")

# ============ 分析功能 ============
if st.session_state.get("show_analysis"):
    with st.expander("🔗 关系分析", expanded=True):
        if st.button("开始分析", type="primary"):
            with st.spinner("分析中..."):
                result = analyze_relationships(st.session_state.selected_case['id'])
                if result:
                    st.success("分析完成")
                    st.json(result)
                else:
                    st.info("暂无可用数据")

        if st.button("关闭"):
            st.session_state.show_analysis = False

if st.session_state.get("show_diagnosis"):
    with st.expander("❓ 证据缺口诊断", expanded=True):
        st.info("诊断功能开发中")
        if st.button("关闭"):
            st.session_state.show_diagnosis = False

# ============ 返回按钮 ============
st.divider()
if st.button("⬅️ 返回证据管理", use_container_width=True):
    st.switch_page("pages/7_证据管理.py")
