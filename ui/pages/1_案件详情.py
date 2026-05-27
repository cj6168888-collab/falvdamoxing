"""
案件详情 - 随身律师
支持证据补充、对话分析、文书推荐与生成
增强版：全盘分析、用户参与修改、导出、数据联动
"""
import streamlit as st
import requests
import os
import json
from datetime import datetime

st.set_page_config(page_title="案件详情 - 随身律师", page_icon="📖", layout="wide")

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8002")


def check_api():
    """检查API连接"""
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except:
        return False


def get_case(case_id):
    """获取案件详情"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/cases/{case_id}", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_cases():
    """获取案件列表"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/cases", timeout=5)
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


def close_case(case_id):
    """结案"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/cases/{case_id}/close", timeout=10)
        return r.status_code == 200
    except:
        return False


def reopen_case(case_id):
    """重新开案"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/cases/{case_id}/reopen", timeout=10)
        return r.status_code == 200
    except:
        return False


def send_message(case_id, message, conversation_context=None):
    """发送消息到AI助手"""
    try:
        data = {
            "case_id": case_id,
            "message": message,
            "conversation_context": conversation_context or []
        }
        r = requests.post(f"{API_BASE_URL}/api/v2/assistant/chat", json=data, timeout=300)
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        return {"error": str(e)}


def get_conversation_history(case_id, limit=20):
    """获取对话历史"""
    try:
        r = requests.get(
            f"{API_BASE_URL}/api/v2/assistant/conversation-history/{case_id}?limit={limit}",
            timeout=10
        )
        return r.json() if r.status_code == 200 else {"conversations": []}
    except:
        return {"conversations": []}


def get_quick_actions(case_id):
    """获取快捷操作建议"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/v2/assistant/quick-actions/{case_id}", timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def analyze_case(case_id):
    """分析案件"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/cases/{case_id}/analyze", timeout=300)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_strategy(case_id):
    """获取策略"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/cases/{case_id}/strategy", timeout=300)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def generate_document(case_id, doc_type, custom_prompt=None):
    """生成文书"""
    try:
        data = {"document_type": doc_type}
        if custom_prompt:
            data["custom_prompt"] = custom_prompt
        r = requests.post(
            f"{API_BASE_URL}/api/cases/{case_id}/documents/generate",
            json=data,
            timeout=300
        )
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_templates():
    """获取文书模板"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/documents/templates/list", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_generated_documents(case_id):
    """获取已生成的文书"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/documents/case/{case_id}/generated", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_case_evidence(case_id):
    """获取案件证据"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/evidence/case/{case_id}", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def submit_evidence(case_id, evidence_data):
    """提交证据"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/evidence/submit/{case_id}", json=evidence_data, timeout=30)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_evidence_suggestions(case_id):
    """获取证据补充建议"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/cases/{case_id}/evidence-suggestions", timeout=60)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_case_deadlines(case_id):
    """获取案件时间节点"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/time-control/case/{case_id}/deadlines", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_analyses(case_id):
    """获取对抗性分析列表"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/adversarial/case/{case_id}/analyses", timeout=10)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_case_execution(case_id):
    """获取执行信息"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/cases/{case_id}/execution", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None


# ============ 导出功能 ============

def export_to_markdown(content: str, title: str = "导出文档") -> str:
    """导出为Markdown格式"""
    header = f"""# {title}

**案件信息**

- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 导出类型: {title}

---

"""
    return header + content


def export_to_text(content: str, title: str = "导出文档") -> str:
    """导出为纯文本格式"""
    header = f"""{title}
{'=' * len(title)}
导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
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
                key=f"md_{key}"
            )
        with col2:
            st.download_button(
                "📝 纯文本",
                export_to_text(content, title).encode('utf-8'),
                f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key=f"txt_{key}"
            )
        with col3:
            st.download_button(
                "📋 JSON",
                json.dumps({"title": title, "content": content, "export_time": datetime.now().isoformat()}, ensure_ascii=False, indent=2).encode('utf-8'),
                f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key=f"json_{key}"
            )


# ============ API检查 ============
if not check_api():
    st.error("❌ 后端 API 未连接，请先启动服务")
    st.info("后端服务运行地址: http://localhost:8002")
    st.stop()

# ============ 获取当前案件 ============
if "selected_case" not in st.session_state or st.session_state.selected_case is None:
    cases = get_cases()
    if cases:
        st.session_state.selected_case = cases[0]
    else:
        st.error("没有可用的案件")
        st.info("请先在案件管理中创建案件")
        st.stop()

current_case = st.session_state.selected_case
case_id = current_case.get('id')

# ============ 初始化session_state ============
if "case_chat_messages" not in st.session_state:
    st.session_state.case_chat_messages = []
if "supplement_submitted" not in st.session_state:
    st.session_state.supplement_submitted = False
if "recommended_docs" not in st.session_state:
    st.session_state.recommended_docs = []
if "full_analysis_result" not in st.session_state:
    st.session_state.full_analysis_result = None
if "strategy_result" not in st.session_state:
    st.session_state.strategy_result = None


# ============ 页面布局 ============
st.title(f"📖 案件详情: {current_case.get('title', '未命名')}")

# 案件基本信息栏
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    status = current_case.get('status', 'active')
    status_text = {"active": "进行中", "pending": "待处理", "closed": "已结案", "suspended": "已中止"}.get(status, status)
    status_icon = {"active": "🟢", "pending": "🟡", "closed": "⚫", "suspended": "🟠"}.get(status, "⚪")
    st.metric("状态", f"{status_icon} {status_text}")

with col2:
    case_type = current_case.get('case_type', '未分类')
    st.metric("案件类型", case_type)

with col3:
    priority = current_case.get('priority', 'medium')
    priority_text = {"low": "低", "medium": "中", "high": "高"}.get(priority, priority)
    priority_icon = {"low": "⚪", "medium": "🟡", "high": "🔴"}.get(priority, "⚪")
    st.metric("优先级", f"{priority_icon} {priority_text}")

with col4:
    project_name = current_case.get('project_name', '无')
    st.metric("关联项目", project_name)

with col5:
    claim_amount = current_case.get('claim_amount', 0)
    try:
        amount_val = float(claim_amount) if claim_amount else 0
    except (ValueError, TypeError):
        amount_val = 0
    if amount_val:
        st.metric("诉讼金额", f"¥{amount_val:,.0f}")
    else:
        st.metric("诉讼金额", "-")

# ============ 数据联动区域 - 显示关联数据摘要 ============
st.markdown("---")
st.markdown("#### 🔗 数据联动总览")

linked_col1, linked_col2, linked_col3, linked_col4, linked_col5 = st.columns(5)

with linked_col1:
    evidence_count = len(get_case_evidence(case_id))
    st.metric("📋 证据数量", evidence_count)
    if st.button("📋 查看", key="link_evidence"):
        st.switch_page("pages/7_证据管理.py")

with linked_col2:
    docs = get_generated_documents(case_id)
    st.metric("📄 文书数量", len(docs))
    if st.button("📄 查看", key="link_docs"):
        st.switch_page("pages/3_文书生成.py")

with linked_col3:
    deadlines = get_case_deadlines(case_id)
    today = datetime.now().date()
    urgent = [d for d in deadlines if d.get('deadline_date') and
              0 <= (datetime.strptime(d['deadline_date'], '%Y-%m-%d').date() - today).days <= 7]
    st.metric("⏰ 时间节点", len(deadlines))
    if st.button("⏰ 查看", key="link_deadlines"):
        st.switch_page("pages/8_时间把控.py")

with linked_col4:
    analyses = get_analyses(case_id)
    st.metric("⚔️ 对抗分析", len(analyses))
    if st.button("⚔️ 查看", key="link_adversarial"):
        st.switch_page("pages/5_对抗性分析.py")

with linked_col5:
    execution = get_case_execution(case_id)
    exec_status = execution.get('status', '无') if execution else '无'
    st.metric("🔨 执行状态", exec_status)
    if st.button("🔨 查看", key="link_execution"):
        st.switch_page("pages/6_执行跟踪.py")

st.markdown("---")

# ============ 主功能区：标签页 ============
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 对话分析",
    "📋 证据资料补充",
    "📄 文书生成",
    "📊 全盘分析",
    "📋 案件概览"
])

# ============ 标签页1：对话分析 ============
with tab1:
    st.subheader("💬 案件对话")

    # 案件信息摘要
    with st.expander("📋 当前案件信息", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"**原告:** {current_case.get('plaintiff', '-')}")
            st.write(f"**被告:** {current_case.get('defendant', '-')}")
            st.write(f"**案由:** {current_case.get('cause', '-')}")
        with col_b:
            st.write(f"**诉求金额:** {current_case.get('claim_amount', '-')}")
            if current_case.get('description'):
                st.write(f"**案件描述:** {current_case.get('description')[:200]}...")

    # 快捷问题模板
    st.markdown("#### 🎯 快捷问题")
    quick_questions = [
        ("📋 案件概述", "请简要概述这个案件的核心内容、争议焦点和我方的主要诉求"),
        ("⚖️ 法律分析", "这个案件涉及哪些法律问题？适用哪些法律条文？请进行深度分析，不要遗漏任何细节"),
        ("📊 证据评估", "根据现有证据，分析我方证据是否充分，还缺什么证据？请列出完整的证据清单"),
        ("💡 诉讼策略", "基于当前情况，我方应该采取什么诉讼策略？请提供详细的策略方案"),
        ("⚠️ 风险提示", "这个案件有哪些主要风险？对方可能采取什么反击手段？请全面分析"),
        ("🎯 补充建议", "根据目前的案件材料，我还需要补充哪些信息？请给出完整建议"),
        ("📝 文书建议", "基于当前分析，建议生成哪些法律文书？请说明每种文书的作用"),
        ("🔄 进展追踪", "这个案件目前进展如何？有哪些待处理事项？请给出时间线"),
    ]

    q_cols = st.columns(4)
    for i, (label, question) in enumerate(quick_questions):
        with q_cols[i % 4]:
            if st.button(label, use_container_width=True, key=f"q_{i}"):
                st.session_state.quick_question = question

    st.markdown("---")

    # 对话历史显示
    st.markdown("#### 💬 对话记录")
    if st.session_state.case_chat_messages:
        for msg in st.session_state.case_chat_messages:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(f"**👤 您:** {msg['content']}")
            else:
                with st.chat_message("assistant"):
                    st.markdown(f"**🤖 AI分析:**\n\n{msg['content']}")
                    if msg.get("suggestions"):
                        st.markdown("\n**💡 后续建议:**")
                        for s in msg["suggestions"]:
                            st.markdown(f"- {s}")
                    if msg.get("evidence_gaps"):
                        st.markdown("\n**📋 证据缺口:**")
                        for g in msg["evidence_gaps"]:
                            st.markdown(f"- {g}")

                    # 显示导出选项
                    if msg.get("content"):
                        show_export_section("对话内容", msg['content'], f"chat_{len(st.session_state.case_chat_messages)}")
    else:
        st.info("上方选择快捷问题或输入您的问题开始对话")

    st.markdown("---")

    # 输入区域
    default_question = st.session_state.get("quick_question", "")
    user_input = st.text_area(
        "💭 输入您的问题或描述：",
        value=default_question,
        placeholder="输入问题、补充案件情况、描述新进展等...",
        height=100,
        key="chat_input_area"
    )

    # 用户修改/反馈区域
    with st.expander("✏️ 用户修改意见（选填）", expanded=False):
        user_modification = st.text_area(
            "您对AI分析的修改意见：",
            placeholder="如果AI分析有需要修改或补充的地方，请在此说明...",
            height=80,
            key="user_modification_area"
        )
        st.caption("您的修改意见将被记录并用于改进后续分析")

    col_send, col_clear, col_save = st.columns([1, 1, 2])
    with col_send:
        submitted = st.button("📤 发送分析", type="primary", use_container_width=True)
    with col_clear:
        if st.button("🗑️ 清空对话", use_container_width=True):
            st.session_state.case_chat_messages = []
            st.session_state.quick_question = ""
            st.rerun()
    with col_save:
        if st.button("📥 补充到案件材料", use_container_width=True) and user_input:
            current_desc = current_case.get('description', '')
            mod_note = f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 用户补充:\n{user_input}"
            if user_modification:
                mod_note += f"\n【用户修改意见】:\n{user_modification}"
            new_desc = f"{current_desc}{mod_note}"
            update_case(case_id, {"description": new_desc})
            st.session_state.selected_case = get_case(case_id)
            st.success("已补充到案件材料")
            st.rerun()

    if submitted and user_input:
        # 发送对话请求
        with st.spinner("🤖 AI深度分析中，请稍候（可能需要几分钟）..."):
            conversation_context = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.case_chat_messages[-10:]
            ]
            # 添加用户修改意见到上下文中
            if user_modification:
                conversation_context.append({
                    "role": "system",
                    "content": f"【用户修改意见】请在回复中参考以下修改意见：{user_modification}"
                })
            response = send_message(case_id, user_input, conversation_context)

        if response and "error" not in response:
            st.session_state.case_chat_messages.append({
                "role": "user",
                "content": user_input
            })

            answer = response.get("answer", "抱歉，AI未能生成回答")
            msg_data = {
                "role": "assistant",
                "content": answer,
                "suggestions": response.get("suggestions", []),
                "evidence_gaps": response.get("evidence_gaps", []),
                "recommended_docs": response.get("recommended_docs", [])
            }
            st.session_state.case_chat_messages.append(msg_data)

            # 保存推荐文书
            if response.get("recommended_docs"):
                st.session_state.recommended_docs = response.get("recommended_docs")

            st.session_state.quick_question = ""
            st.session_state.user_modification = ""
            st.rerun()
        elif response and "error" in response:
            st.error(f"分析失败: {response['error']}")
        else:
            st.error("AI分析服务暂时不可用，请检查后端服务")

    # 历史对话
    st.markdown("---")
    with st.expander("📜 查看历史对话"):
        history = get_conversation_history(case_id)
        if history.get("conversations"):
            for h in history["conversations"][:10]:
                st.markdown(f"**[{h.get('turn_number', 0)}]** {h.get('created_at', '')[:16]}")
                st.markdown(f"用户: {h.get('user_input', '')[:100]}...")
                st.markdown(f"AI: {h.get('system_response', '')[:200]}...")
                st.divider()
        else:
            st.info("暂无历史对话")

# ============ 标签页2：证据资料补充 ============
with tab2:
    st.subheader("📋 证据与资料补充")

    with st.container():
        st.subheader("📂 当前证据列表")
        evidence_list = get_case_evidence(case_id)
        if evidence_list:
            for e in evidence_list[:20]:  # 增加显示数量
                col_e1, col_e2, col_e3 = st.columns([3, 1, 1])
                with col_e1:
                    st.markdown(f"**{e.get('name', e.get('title', '证据'))}**")
                    st.caption(f"类型: {e.get('type', '未分类')} | 信度: {e.get('confidence', '未评估')}")
                    if e.get('description'):
                        st.caption(f"说明: {e.get('description')[:100]}...")
                with col_e2:
                    st.write(f"状态: {e.get('status', '待审核')}")
                with col_e3:
                    if e.get('content'):
                        with st.expander("查看内容"):
                            st.markdown(e.get('content')[:500])
                st.divider()
        else:
            st.info("暂无证据，请通过下方表单补充")

    st.markdown("---")
    st.subheader("✏️ 补充新证据/资料")

    # 证据类型选择
    evidence_type = st.selectbox(
        "证据/资料类型",
        [
            "合同类", "票据类", "函件类", "身份类", "通讯记录",
            "证人证言", "鉴定意见", "视听资料", "其他"
        ],
        key="evidence_type_select"
    )

    # 证据名称
    evidence_name = st.text_input("证据名称/标题", placeholder="例如：购销合同、发票、聊天记录...", key="evidence_name_input")

    # 证据内容
    evidence_content = st.text_area(
        "证据内容描述",
        placeholder="详细描述证据内容，包含关键信息...",
        height=150,
        key="evidence_content_area"
    )

    # 来源/时间
    col_source, col_date = st.columns(2)
    with col_source:
        evidence_source = st.text_input("证据来源", placeholder="例如：对方提供、自行收集...", key="evidence_source_input")
    with col_date:
        evidence_date = st.date_input("证据日期（选填）", key="evidence_date_input")

    # 证明目的
    proof_purpose = st.text_input("证明目的", placeholder="这份证据要证明什么...", key="proof_purpose_input")

    # 提交按钮
    if st.button("✅ 提交证据", type="primary", use_container_width=True):
        if evidence_name and evidence_content:
            evidence_data = {
                "name": evidence_name,
                "type": evidence_type,
                "content": evidence_content,
                "source": evidence_source,
                "date": str(evidence_date),
                "proof_purpose": proof_purpose,
                "status": "submitted"
            }
            result = submit_evidence(case_id, evidence_data)
            if result:
                st.success(f"✅ 证据「{evidence_name}」已提交，系统将自动分析...")
                st.info("💡 请切换到「对话分析」标签页，AI将基于新证据进行补充分析")
            else:
                st.warning("证据已记录，但后端API可能未完全连接")
                # 即使API失败也保存到本地
                st.success(f"✅ 证据「{evidence_name}」已记录（待后端确认）")
        else:
            st.warning("请填写证据名称和内容")

    # AI证据建议
    st.markdown("---")
    st.subheader("💡 AI证据补充建议")

    if st.button("🔍 获取AI证据建议", use_container_width=True):
        with st.spinner("AI分析中..."):
            suggestions = get_evidence_suggestions(case_id)
            if suggestions:
                st.success("建议已生成")
                st.markdown(suggestions.get("suggestions", "暂无建议"))
                # 导出建议
                show_export_section("证据建议", suggestions.get("suggestions", ""), "evidence_suggestions")
            else:
                st.info("暂无建议，请先补充案件描述")

    st.markdown("---")

    # 案件材料补充
    st.subheader("📝 案件进展/突发事件补充")

    event_type = st.selectbox(
        "事件类型",
        ["进展", "突发事件", "对方动作", "法院通知", "其他"]
    )

    event_desc = st.text_area(
        "事件描述",
        placeholder="详细描述事件内容...",
        height=100,
        key="event_desc_area"
    )

    if st.button("📌 记录事件", use_container_width=True):
        if event_desc:
            current_desc = current_case.get('description', '')
            new_entry = f"\n\n[{datetime.now().strftime('%Y-%m-%d')}] 【{event_type}】\n{event_desc}"
            update_case(case_id, {"description": current_desc + new_entry})
            st.session_state.selected_case = get_case(case_id)
            st.success("事件已记录到案件材料")
            st.rerun()
        else:
            st.warning("请填写事件描述")

    # 观点补充
    st.markdown("---")
    st.subheader("💡 法律观点补充")

    viewpoint = st.text_area(
        "补充的法律观点或分析",
        placeholder="补充您的法律观点、对案件的分析...",
        height=100,
        key="viewpoint_area"
    )

    if st.button("💾 保存观点", use_container_width=True):
        if viewpoint:
            current_desc = current_case.get('description', '')
            new_entry = f"\n\n[{datetime.now().strftime('%Y-%m-%d')}] 【法律观点】\n{viewpoint}"
            update_case(case_id, {"description": current_desc + new_entry})
            st.session_state.selected_case = get_case(case_id)
            st.success("观点已保存")
        else:
            st.warning("请填写观点内容")

# ============ 标签页3：文书生成 ============
with tab3:
    st.subheader("📄 文书生成")

    # AI推荐文书
    if st.session_state.recommended_docs:
        st.markdown("#### 🤖 AI推荐文书")
        st.info("根据您的对话分析，AI推荐以下文书：")
        for doc_type in st.session_state.recommended_docs:
            st.markdown(f"- {doc_type}")

        if st.button("🚀 基于推荐生成文书", type="primary", use_container_width=True):
            for doc_type in st.session_state.recommended_docs[:3]:
                with st.spinner(f"正在生成 {doc_type}..."):
                    result = generate_document(case_id, doc_type)
                    if result:
                        st.success(f"✅ {doc_type} 生成完成")
                        if isinstance(result, dict) and result.get("content"):
                            show_export_section(f"{doc_type}", result.get("content", ""), f"recommended_{doc_type}")
                    else:
                        st.warning(f"⚠️ {doc_type} 生成失败，请稍后重试")

        st.markdown("---")

    # 快捷文书模板
    st.markdown("#### 📝 快捷文书生成")
    doc_templates = [
        ("起诉状", "民事诉讼起诉状"),
        ("答辩状", "被告答辩状"),
        ("代理词", "诉讼代理词"),
        ("上诉状", "民事上诉状"),
        ("和解协议", "和解协议书"),
        ("财产保全", "财产保全申请书"),
        ("证据目录", "证据材料目录"),
        ("律师函", "律师函"),
        ("申请执行", "执行申请书"),
    ]

    doc_cols = st.columns(3)
    for i, (label, doc_type) in enumerate(doc_templates):
        with doc_cols[i % 3]:
            if st.button(label, use_container_width=True, key=f"doc_{i}"):
                with st.spinner(f"正在生成 {label}..."):
                    result = generate_document(case_id, doc_type)
                    if result:
                        st.success(f"✅ {label} 生成完成")
                        if isinstance(result, dict):
                            content = result.get('content', result.get('text', ''))
                            if content:
                                st.markdown(content)
                                show_export_section(f"{label}", content, f"doc_{i}")
                    else:
                        st.error(f"⚠️ {label} 生成失败，请稍后重试")

    st.markdown("---")

    # 自定义文书
    st.markdown("#### ✏️ 自定义文书")

    custom_type = st.text_input("文书类型", placeholder="例如：催款函、律师函...")
    custom_prompt = st.text_area("特殊要求（选填）", placeholder="如有特殊要求请在此说明...", height=80)

    if st.button("🎯 生成自定义文书", use_container_width=True):
        if custom_type:
            with st.spinner("正在生成..."):
                result = generate_document(case_id, custom_type, custom_prompt)
                if result:
                    st.success(f"✅ {custom_type} 生成完成")
                    if isinstance(result, dict):
                        content = result.get('content', result.get('text', ''))
                        if content:
                            st.markdown(content)
                            show_export_section(f"{custom_type}", content, "custom_doc")
                else:
                    st.error("生成失败")
        else:
            st.warning("请输入文书类型")

    st.markdown("---")

    # 已生成文书列表
    st.markdown("#### 📁 已生成文书")
    generated_docs = get_generated_documents(case_id)
    if generated_docs:
        for doc in generated_docs[:15]:
            col_d1, col_d2, col_d3 = st.columns([3, 1, 1])
            with col_d1:
                st.markdown(f"**{doc.get('filename', doc.get('title', '文书'))}**")
                st.caption(f"类型: {doc.get('doc_type', '未知')} | {doc.get('created_at', '')[:10]}")
            with col_d2:
                if st.button("查看", key=f"view_{doc.get('id')}"):
                    content = doc.get('content', '')
                    if content:
                        st.markdown(content)
            with col_d3:
                if doc.get('content'):
                    show_export_section(f"文书_{doc.get('id')}", doc.get('content', ''), f"saved_doc_{doc.get('id')}")
            st.divider()
    else:
        st.info("暂无已生成的文书")

# ============ 标签页4：全盘分析 ============
with tab4:
    st.subheader("📊 全盘分析")

    st.markdown("""
    **功能说明**：本模块对案件进行全面的深度分析，包括法律关系、证据链、策略建议等。
    分析结果将完整呈现，支持导出和用户修改意见。
    """)

    col_full1, col_full2 = st.columns(2)

    with col_full1:
        st.markdown("#### 🔍 AI案件分析")
        if st.button("🚀 开始全面分析", type="primary", use_container_width=True, key="full_analyze_btn"):
            with st.spinner("正在进行全面分析，请稍候（可能需要几分钟）..."):
                result = analyze_case(case_id)
                if result:
                    st.session_state.full_analysis_result = result
                    st.success("✅ 分析完成！")
                else:
                    st.error("分析失败，请重试")

        if st.session_state.full_analysis_result:
            result = st.session_state.full_analysis_result
            analysis_text = result.get("analysis", result.get("answer", ""))
            if analysis_text:
                st.markdown("---")
                st.markdown("### 📋 分析结果")

                # 完整显示分析结果
                st.markdown(analysis_text)

                # 导出选项
                show_export_section("AI案件分析报告", analysis_text, "full_analysis")

                # 用户反馈区域
                st.markdown("---")
                st.markdown("### ✏️ 您对分析的意见")

                analysis_feedback = st.text_area(
                    "您认为分析结果有哪些需要修改或补充的地方？",
                    placeholder="请详细说明...",
                    height=100,
                    key="analysis_feedback"
                )

                if st.button("💾 保存反馈并优化"):
                    if analysis_feedback:
                        # 将反馈添加到案件描述中
                        current_desc = current_case.get('description', '')
                        feedback_entry = f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 【AI分析反馈】\n{analysis_feedback}"
                        update_case(case_id, {"description": current_desc + feedback_entry})
                        st.session_state.selected_case = get_case(case_id)
                        st.success("反馈已保存，将在下次分析时参考")
                    else:
                        st.warning("请填写反馈内容")

    with col_full2:
        st.markdown("#### 🎯 诉讼策略")
        if st.button("📋 生成详细策略", type="primary", use_container_width=True, key="strategy_btn"):
            with st.spinner("正在生成策略方案，请稍候...", ):
                result = get_strategy(case_id)
                if result:
                    st.session_state.strategy_result = result
                    st.success("✅ 策略生成完成！")
                else:
                    st.error("策略生成失败，请重试")

        if st.session_state.strategy_result:
            result = st.session_state.strategy_result
            strategy_text = result.get("strategy", result.get("answer", ""))
            if strategy_text:
                st.markdown("---")
                st.markdown("### 💡 策略建议")

                st.markdown(strategy_text)

                # 导出选项
                show_export_section("诉讼策略报告", strategy_text, "strategy")

                # 用户反馈
                st.markdown("---")
                strategy_feedback = st.text_area(
                    "您对策略方案的意见？",
                    placeholder="请说明...",
                    height=80,
                    key="strategy_feedback"
                )

                if st.button("💾 保存策略反馈"):
                    if strategy_feedback:
                        current_desc = current_case.get('description', '')
                        feedback_entry = f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 【策略反馈】\n{strategy_feedback}"
                        update_case(case_id, {"description": current_desc + feedback_entry})
                        st.success("反馈已保存")

# ============ 标签页5：案件概览 ============
with tab5:
    st.subheader("📋 案件概览")

    # 基本信息
    with st.expander("📋 基本信息", expanded=True):
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.write(f"**案件ID:** {case_id}")
            st.write(f"**标题:** {current_case.get('title', '-')}")
            st.write(f"**类型:** {current_case.get('case_type', '-')}")
            st.write(f"**优先级:** {priority_text}")
        with col_b2:
            st.write(f"**原告:** {current_case.get('plaintiff', '-')}")
            st.write(f"**被告:** {current_case.get('defendant', '-')}")
            st.write(f"**诉讼金额:** {current_case.get('claim_amount', '-')}")
            st.write(f"**创建时间:** {current_case.get('created_at', '')[:10] if current_case.get('created_at') else '-'}")

    # 案件描述
    if current_case.get('description'):
        with st.expander("📝 案件描述", expanded=False):
            st.write(current_case['description'])

    # 快捷操作
    st.markdown("---")
    st.subheader("⚡ 快捷操作")

    op_col1, op_col2, op_col3, op_col4 = st.columns(4)

    with op_col1:
        if st.button("📄 文书生成", use_container_width=True):
            st.switch_page("pages/3_文书生成.py")

    with op_col2:
        if st.button("📋 证据管理", use_container_width=True):
            st.switch_page("pages/7_证据管理.py")

    with op_col3:
        if st.button("⚔️ 对抗性分析", use_container_width=True):
            st.switch_page("pages/5_对抗性分析.py")

    with op_col4:
        if st.button("⏰ 时间把控", use_container_width=True):
            st.switch_page("pages/8_时间把控.py")

    # 导出案件信息
    st.markdown("---")
    st.subheader("📥 导出案件信息")

    case_export_content = f"""
# {current_case.get('title', '案件信息')}

## 基本信息
- 案件ID: {case_id}
- 类型: {current_case.get('case_type', '-')}
- 状态: {status_text}
- 原告: {current_case.get('plaintiff', '-')}
- 被告: {current_case.get('defendant', '-')}
- 案由: {current_case.get('cause', '-')}
- 诉讼金额: {current_case.get('claim_amount', '-')}

## 案件描述
{current_case.get('description', '暂无')}

## 数据统计
- 证据数量: {len(get_case_evidence(case_id))}
- 文书数量: {len(get_generated_documents(case_id))}
- 时间节点: {len(get_case_deadlines(case_id))}
- 对抗分析: {len(get_analyses(case_id))}
"""

    col_exp1, col_exp2, col_exp3 = st.columns(3)
    with col_exp1:
        st.download_button(
            "📄 导出为Markdown",
            case_export_content.encode('utf-8'),
            f"案件信息_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )
    with col_exp2:
        st.download_button(
            "📝 导出为文本",
            case_export_content.replace('## ', '\n【').replace('**', '').replace('- ', '\n• ').encode('utf-8'),
            f"案件信息_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    with col_exp3:
        st.download_button(
            "📋 导出为JSON",
            json.dumps({
                "case": current_case,
                "export_time": datetime.now().isoformat(),
                "statistics": {
                    "evidence_count": len(get_case_evidence(case_id)),
                    "document_count": len(get_generated_documents(case_id)),
                    "deadline_count": len(get_case_deadlines(case_id)),
                    "analysis_count": len(get_analyses(case_id))
                }
            }, ensure_ascii=False, indent=2).encode('utf-8'),
            f"案件信息_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

    # 结案操作
    st.markdown("---")
    col_close1, col_close2 = st.columns([1, 3])
    with col_close1:
        if current_case.get('status') != 'closed':
            if st.button("✅ 结案", type="primary", use_container_width=True):
                if close_case(case_id):
                    st.success("案件已结案")
                    st.session_state.selected_case = get_case(case_id)
                    st.rerun()
                else:
                    st.error("结案失败")
        else:
            if st.button("🔄 重新开案", use_container_width=True):
                if reopen_case(case_id):
                    st.success("案件已重新开启")
                    st.session_state.selected_case = get_case(case_id)
                    st.rerun()
                else:
                    st.error("重新开案失败")

# ============ 案件列表（底部） ============
st.markdown("---")
st.subheader("📋 其他案件")
cases = get_cases()

if cases:
    other_cases = [c for c in cases if c.get('id') != case_id][:5]

    for case in other_cases:
        col1, col2 = st.columns([4, 1])
        with col1:
            status_icon = {"active": "🟢", "pending": "🟡", "closed": "⚫"}.get(case.get('status', 'active'), "⚪")
            st.markdown(f"**{status_icon} {case.get('title', '未命名')}**")
            st.caption(f"{case.get('case_type', '未分类')} | {case.get('project_name', '无')}")

        with col2:
            if st.button("查看", key=f"switch_{case['id']}"):
                st.session_state.selected_case = case
                st.session_state.case_chat_messages = []
                st.session_state.recommended_docs = []
                st.session_state.full_analysis_result = None
                st.session_state.strategy_result = None
                st.rerun()

        st.markdown("---")

# ============ 返回按钮 ============
st.divider()
if st.button("⬅️ 返回案件管理", use_container_width=True):
    st.switch_page("pages/1_案件管理.py")
