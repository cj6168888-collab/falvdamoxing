"""
对抗性分析 - 随身律师
分析对方当事人的诉讼策略和弱点
增强版：全盘分析、用户参与、导出、数据联动
"""
import streamlit as st
import requests
import os
from datetime import datetime
import json

st.set_page_config(page_title="对抗性分析 - 随身律师", page_icon="⚔️", layout="wide")

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
    """获取案件详情"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/cases/{case_id}", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_analyses(case_id):
    """获取分析列表"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/对抗性分析/case/{case_id}/analyses", timeout=10)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def create_analysis(case_id, opponent_name, opponent_claims):
    """创建对抗性分析"""
    try:
        data = {
            "opponent_name": opponent_name,
            "opponent_claims": opponent_claims
        }
        r = requests.post(
            f"{API_BASE_URL}/api/对抗性分析/case/{case_id}/analysis",
            json=data,
            timeout=300
        )
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_opponent_analysis(case_id):
    """获取对方分析"""
    try:
        r = requests.post(
            f"{API_BASE_URL}/api/对抗性分析/case/{case_id}/opponent-analysis",
            timeout=300
        )
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_evidence_matrix(case_id):
    """获取证据矩阵"""
    try:
        r = requests.post(
            f"{API_BASE_URL}/api/对抗性分析/case/{case_id}/evidence-matrix",
            timeout=300
        )
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_scenario_prediction(case_id):
    """获取情景预测"""
    try:
        r = requests.post(
            f"{API_BASE_URL}/api/对抗性分析/case/{case_id}/scenario-prediction",
            timeout=300
        )
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_evidence(case_id):
    """获取证据列表"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/evidence/case/{case_id}", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def update_case(case_id, data):
    """更新案件"""
    try:
        r = requests.put(f"{API_BASE_URL}/api/cases/{case_id}", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


# ============ 导出功能 ============

def export_to_markdown(content: str, title: str = "对抗性分析") -> str:
    """导出为Markdown格式"""
    header = f"""# {title}

**对抗性分析报告**

- 案件编号: {st.session_state.get('selected_case', {}).get('id', 'N/A')}
- 案件名称: {st.session_state.get('selected_case', {}).get('title', 'N/A')}
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
    return header + content


def export_to_text(content: str, title: str = "对抗性分析") -> str:
    """导出为纯文本格式"""
    header = f"""{title}
{'=' * len(title)}
案件: {st.session_state.get('selected_case', {}).get('title', 'N/A')}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'-' * 50}

"""
    text = content
    text = text.replace('## ', '\n【').replace('**', '').replace('*', '')
    text = text.replace('---', '\n' + '-' * 50)
    text = text.replace('- ', '\n• ')
    return header + text


def show_export_section(title: str, content: str, key: str):
    """显示导出选项区域"""
    with st.expander(f"📥 导出 {title}", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                "📄 Markdown",
                export_to_markdown(content, title).encode('utf-8'),
                f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                key=f"md_adv_{key}"
            )
        with col2:
            st.download_button(
                "📝 纯文本",
                export_to_text(content, title).encode('utf-8'),
                f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key=f"txt_adv_{key}"
            )
        with col3:
            st.download_button(
                "📋 JSON",
                json.dumps({
                    "title": title,
                    "content": content,
                    "case_id": st.session_state.get('selected_case', {}).get('id'),
                    "case_name": st.session_state.get('selected_case', {}).get('title'),
                    "export_time": datetime.now().isoformat()
                }, ensure_ascii=False, indent=2).encode('utf-8'),
                f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key=f"json_adv_{key}"
            )


# ============ API检查 ============
if not check_api():
    st.error("❌ 后端服务未连接，请先启动服务")
    st.info("后端服务运行地址: http://localhost:8002")
    st.stop()

# ============ 页面标题 ============
st.title("⚔️ 对抗性分析")
st.markdown("*知己知彼，百战不殆 — 分析对方策略，寻找突破口*")
st.markdown("---")

# ============ 初始化 ============
if "selected_case" not in st.session_state:
    st.session_state.selected_case = None
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "opponent_analysis_result" not in st.session_state:
    st.session_state.opponent_analysis_result = None
if "evidence_matrix_result" not in st.session_state:
    st.session_state.evidence_matrix_result = None
if "scenario_prediction_result" not in st.session_state:
    st.session_state.scenario_prediction_result = None


# ============ 侧边栏 ============
with st.sidebar:
    st.header("⚔️ 对抗性分析")

    # 选择案件
    cases = get_cases()
    case_options = {f"#{c['id']} {c.get('title', '未命名')[:30]}": c for c in cases}
    selected_label = st.selectbox("选择案件", options=list(case_options.keys()))

    if selected_label:
        st.session_state.selected_case = case_options[selected_label]

    st.divider()

    # 历史分析
    if st.session_state.selected_case:
        analyses = get_analyses(st.session_state.selected_case['id'])
        st.subheader(f"📊 历史分析 ({len(analyses)})")

        for a in analyses[:5]:
            st.caption(f"• {a.get('created_at', '')[:10]} - {a.get('opponent_name', '未知')}")

    st.divider()

    # 分析选项说明
    st.subheader("🔧 分析工具")
    st.markdown("""
    - **对方分析**: 从对手角度分析其诉讼策略
    - **证据矩阵**: 双方证据攻防对比
    - **情景预测**: 预测案件可能的走向
    - **完整分析**: 综合以上所有分析
    """)


# ============ 主内容 ============
if not st.session_state.selected_case:
    st.warning("请先在左侧选择案件")
    st.info("或者前往「案件管理」创建案件")
else:
    case = st.session_state.selected_case
    case_id = case.get('id')

    st.subheader(f"⚔️ 当前案件: {case.get('title', '未命名')}")

    # 案件基本信息
    with st.expander("📋 案件基本信息", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**原告:** {case.get('plaintiff', '-')}")
            st.write(f"**被告:** {case.get('defendant', '-')}")
        with col2:
            st.write(f"**案由:** {case.get('cause', '-')}")
            st.write(f"**诉讼金额:** {case.get('claim_amount', '-')}")

    st.markdown("---")

    # 对方当事人信息
    st.subheader("👤 对方当事人信息")

    with st.form("opponent_form"):
        col1, col2 = st.columns(2)

        with col1:
            opponent_name = st.text_input(
                "对方当事人名称",
                placeholder="例如：XXX公司/张三"
            )

        with col2:
            opponent_type = st.selectbox(
                "当事人类型",
                options=["个人", "企业", "政府机关", "其他"]
            )

        opponent_claims = st.text_area(
            "对方主张/诉求",
            placeholder="描述对方的主要诉讼请求和理由...",
            height=100
        )

        submitted = st.form_submit_button("🔍 开始全面分析", type="primary", use_container_width=True)

    st.markdown("---")

    # 分析结果展示
    if submitted or any([st.session_state.analysis_result, st.session_state.opponent_analysis_result]):
        st.subheader("📊 分析结果")

        if submitted:
            with st.spinner("正在进行对抗性全面分析（可能需要几分钟）..."):
                # 1. 基础对抗性分析
                result = create_analysis(case_id, opponent_name, opponent_claims)
                if result:
                    st.session_state.analysis_result = result

                # 2. 对方分析
                opp_result = get_opponent_analysis(case_id)
                if opp_result:
                    st.session_state.opponent_analysis_result = opp_result

                # 3. 证据矩阵
                matrix_result = get_evidence_matrix(case_id)
                if matrix_result:
                    st.session_state.evidence_matrix_result = matrix_result

                # 4. 情景预测
                scenario_result = get_scenario_prediction(case_id)
                if scenario_result:
                    st.session_state.scenario_prediction_result = scenario_result

        # 标签页展示分析结果
        if any([st.session_state.analysis_result, st.session_state.opponent_analysis_result,
                st.session_state.evidence_matrix_result, st.session_state.scenario_prediction_result]):

            tab1, tab2, tab3, tab4 = st.tabs([
                "🎯 弱点与策略",
                "👤 对方分析",
                "📊 证据矩阵",
                "🔮 情景预测"
            ])

            # 弱点与策略
            with tab1:
                st.markdown("### 🎯 对方弱点与应对策略")
                if st.session_state.analysis_result:
                    result = st.session_state.analysis_result

                    # 弱点分析
                    st.markdown("#### ⚠️ 对方弱点")
                    weaknesses = result.get('weaknesses', result.get('opponent_weaknesses', []))
                    if isinstance(weaknesses, list) and weaknesses:
                        for i, w in enumerate(weaknesses):
                            if isinstance(w, dict):
                                st.warning(f"**{i+1}. {w.get('title', '弱点')}**\n{w.get('description', str(w))}")
                            else:
                                st.warning(f"**{i+1}.** {w}")
                    elif weaknesses:
                        st.markdown(weaknesses)
                    else:
                        st.info("暂无弱点分析数据")

                    # 应对策略
                    st.markdown("\n#### 💡 应对策略")
                    strategies = result.get('strategies', result.get('counter_strategies', []))
                    if isinstance(strategies, list) and strategies:
                        for i, s in enumerate(strategies):
                            if isinstance(s, dict):
                                st.success(f"**{i+1}. {s.get('title', '策略')}**\n{s.get('description', str(s))}")
                            else:
                                st.success(f"**{i+1}.** {s}")
                    elif strategies:
                        st.markdown(strategies)

                    # 我方优势
                    st.markdown("\n#### 💪 我方优势")
                    advantages = result.get('advantages', result.get('our_advantages', []))
                    if isinstance(advantages, list) and advantages:
                        for a in advantages:
                            if isinstance(a, dict):
                                st.markdown(f"- **{a.get('title', '优势')}**: {a.get('description', str(a))}")
                            else:
                                st.markdown(f"- {a}")
                    elif advantages:
                        st.markdown(advantages)

                    # 风险提示
                    st.markdown("\n#### ⚠️ 风险提示")
                    risks = result.get('risks', [])
                    if isinstance(risks, list) and risks:
                        for r in risks:
                            if isinstance(r, dict):
                                st.error(f"⚠️ **{r.get('title', '风险')}**: {r.get('description', str(r))}")
                            else:
                                st.error(f"⚠️ {r}")
                    elif risks:
                        st.markdown(risks)

                    # 导出选项
                    full_content = f"""
# 对抗性分析报告

## 对方弱点
{json.dumps(weaknesses, ensure_ascii=False, indent=2) if isinstance(weaknesses, list) else weaknesses}

## 应对策略
{json.dumps(strategies, ensure_ascii=False, indent=2) if isinstance(strategies, list) else strategies}

## 我方优势
{json.dumps(advantages, ensure_ascii=False, indent=2) if isinstance(advantages, list) else advantages}

## 风险提示
{json.dumps(risks, ensure_ascii=False, indent=2) if isinstance(risks, list) else risks}
"""
                    show_export_section("对抗性分析报告", full_content, "main_analysis")

                    # 用户反馈
                    st.markdown("\n---")
                    st.subheader("✏️ 您对分析的意见")
                    feedback = st.text_area(
                        "您认为分析结果有哪些需要修改或补充的地方？",
                        placeholder="请详细说明...",
                        height=80,
                        key="analysis_feedback"
                    )
                    if st.button("💾 保存反馈"):
                        if feedback:
                            current_case = get_case(case_id)
                            if current_case:
                                current_desc = current_case.get('description', '')
                                feedback_entry = f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 【对抗性分析反馈】\n{feedback}"
                                update_case(case_id, {"description": current_desc + feedback_entry})
                                st.success("反馈已保存")
                else:
                    st.info("暂无分析数据")

            # 对方分析
            with tab2:
                st.markdown("### 👤 对方分析")
                if st.session_state.opponent_analysis_result:
                    opp_result = st.session_state.opponent_analysis_result
                    if isinstance(opp_result, dict):
                        for key, value in opp_result.items():
                            if value:
                                st.markdown(f"\n#### {key.replace('_', ' ').title()}")
                                if isinstance(value, list):
                                    for item in value:
                                        if isinstance(item, dict):
                                            st.markdown(f"- **{item.get('title', '')}**: {item.get('description', str(item))}")
                                        else:
                                            st.markdown(f"- {item}")
                                else:
                                    st.markdown(value)
                        show_export_section("对方分析", json.dumps(opp_result, ensure_ascii=False, indent=2), "opponent")
                    else:
                        st.markdown(str(opp_result))
                        show_export_section("对方分析", str(opp_result), "opponent")
                else:
                    st.info("请先提交对方信息进行分析")

            # 证据矩阵
            with tab3:
                st.markdown("### 📊 证据矩阵")
                if st.session_state.evidence_matrix_result:
                    matrix = st.session_state.evidence_matrix_result
                    if isinstance(matrix, dict):
                        st.json(matrix)
                        show_export_section("证据矩阵", json.dumps(matrix, ensure_ascii=False, indent=2), "matrix")
                    elif isinstance(matrix, str):
                        st.markdown(matrix)
                        show_export_section("证据矩阵", matrix, "matrix")
                    else:
                        st.json(matrix)
                        show_export_section("证据矩阵", json.dumps(matrix, ensure_ascii=False, indent=2), "matrix")
                else:
                    st.info("请先提交对方信息进行分析")

            # 情景预测
            with tab4:
                st.markdown("### 🔮 情景预测")
                if st.session_state.scenario_prediction_result:
                    scenario = st.session_state.scenario_prediction_result
                    if isinstance(scenario, dict):
                        # 显示预测结果
                        scenarios = scenario.get('scenarios', scenario.get('predictions', []))
                        if isinstance(scenarios, list):
                            for i, s in enumerate(scenarios):
                                probability = s.get('probability', 'N/A') if isinstance(s, dict) else 'N/A'
                                st.markdown(f"\n#### 情景 {i+1} {'（最可能）' if i == 0 else ''}")
                                if isinstance(s, dict):
                                    st.markdown(f"**描述**: {s.get('description', str(s))}")
                                    if s.get('probability'):
                                        st.progress(float(str(s.get('probability', '50')).replace('%', '')) / 100 if '%' in str(s.get('probability', '50')) else float(s.get('probability', 50)) / 100)
                                    if s.get('recommended_action'):
                                        st.markdown(f"**建议行动**: {s.get('recommended_action')}")
                                else:
                                    st.markdown(str(s))
                        show_export_section("情景预测", json.dumps(scenario, ensure_ascii=False, indent=2), "scenario")
                    else:
                        st.markdown(str(scenario))
                        show_export_section("情景预测", str(scenario), "scenario")
                else:
                    st.info("请先提交对方信息进行分析")

    # 快捷分析工具
    st.markdown("---")
    st.subheader("🔧 快捷分析工具（单项分析）")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("👤 对方全面分析", use_container_width=True):
            with st.spinner("进行对方分析（可能需要几分钟）..."):
                opp_result = get_opponent_analysis(case_id)
                if opp_result:
                    st.session_state.opponent_analysis_result = opp_result
                    st.success("分析完成！")
                    st.rerun()
                else:
                    st.info("暂无可用数据")

    with col2:
        if st.button("📊 证据矩阵分析", use_container_width=True):
            with st.spinner("分析证据矩阵（可能需要几分钟）..."):
                matrix = get_evidence_matrix(case_id)
                if matrix:
                    st.session_state.evidence_matrix_result = matrix
                    st.success("分析完成！")
                    st.rerun()
                else:
                    st.info("暂无可用数据")

    with col3:
        if st.button("🔮 情景预测", use_container_width=True):
            with st.spinner("进行情景预测（可能需要几分钟）..."):
                prediction = get_scenario_prediction(case_id)
                if prediction:
                    st.session_state.scenario_prediction_result = prediction
                    st.success("预测完成！")
                    st.rerun()
                else:
                    st.info("暂无可用数据")

    with col4:
        if st.button("📋 弱点与策略", use_container_width=True):
            with st.spinner("分析弱点与策略（可能需要几分钟）..."):
                evidence = get_evidence(case_id)
                opponent_claims = case.get('defendant', '') + " " + case.get('cause', '')
                result = create_analysis(case_id, case.get('defendant', '对方'), opponent_claims)
                if result:
                    st.session_state.analysis_result = result
                    st.success("分析完成！")
                    st.rerun()
                else:
                    st.info("暂无可用数据")

    st.markdown("---")

    # 历史分析列表
    st.subheader("📜 历史分析记录")
    analyses = get_analyses(case_id)
    if analyses:
        for a in analyses:
            with st.expander(f"📋 {a.get('created_at', '')[:10]} - {a.get('opponent_name', '未知')}"):
                st.json(a)
                if a.get('content'):
                    st.markdown(a.get('content'))
                show_export_section("历史分析", json.dumps(a, ensure_ascii=False, indent=2), f"history_{a.get('id')}")
    else:
        st.info("暂无历史分析记录")

# ============ 返回按钮 ============
st.divider()
if st.button("⬅️ 返回案件详情", use_container_width=True):
    st.switch_page("pages/1_案件详情.py")
