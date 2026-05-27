"""
通用工具模块 - 为所有页面提供共享功能
"""
import streamlit as st
import requests
import os
from datetime import datetime
import json
from typing import Optional, List, Dict, Any
import io

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8002")


# ============ API 基础函数 ============

def check_api() -> bool:
    """检查API连接"""
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except:
        return False


def get_cases() -> List[Dict]:
    """获取案件列表"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/cases", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_case(case_id: int) -> Optional[Dict]:
    """获取案件详情"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/cases/{case_id}", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_case_evidence(case_id: int) -> List[Dict]:
    """获取案件证据"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/evidence/case/{case_id}", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def submit_evidence(case_id: int, evidence_data: Dict) -> Optional[Dict]:
    """提交证据"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/evidence/submit/{case_id}", json=evidence_data, timeout=30)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_evidence(case_id: int) -> List[Dict]:
    """获取证据列表"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/evidence/case/{case_id}", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def delete_evidence(evidence_id: int) -> bool:
    """删除证据"""
    try:
        r = requests.delete(f"{API_BASE_URL}/api/evidence/{evidence_id}", timeout=5)
        return r.status_code == 200
    except:
        return False


def get_generated_documents(case_id: int) -> List[Dict]:
    """获取已生成的文书"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/documents/case/{case_id}/generated", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def generate_document(case_id: int, doc_type: str, custom_prompt: Optional[str] = None) -> Optional[Dict]:
    """生成文书"""
    try:
        data = {"document_type": doc_type}
        if custom_prompt:
            data["custom_prompt"] = custom_prompt
        r = requests.post(
            f"{API_BASE_URL}/api/cases/{case_id}/documents/generate",
            json=data,
            timeout=120
        )
        return r.json() if r.status_code == 200 else None
    except:
        return None


def update_case(case_id: int, data: Dict) -> Optional[Dict]:
    """更新案件"""
    try:
        r = requests.put(f"{API_BASE_URL}/api/cases/{case_id}", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def send_message(case_id: int, message: str, conversation_context: Optional[List] = None) -> Optional[Dict]:
    """发送消息到AI助手"""
    try:
        data = {
            "case_id": case_id,
            "message": message,
            "conversation_context": conversation_context or []
        }
        r = requests.post(f"{API_BASE_URL}/api/v2/assistant/chat", json=data, timeout=120)
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        return {"error": str(e)}


def get_conversation_history(case_id: int, limit: int = 20) -> Dict:
    """获取对话历史"""
    try:
        r = requests.get(
            f"{API_BASE_URL}/api/v2/assistant/conversation-history/{case_id}?limit={limit}",
            timeout=10
        )
        return r.json() if r.status_code == 200 else {"conversations": []}
    except:
        return {"conversations": []}


def analyze_case(case_id: int) -> Optional[Dict]:
    """分析案件"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/cases/{case_id}/analyze", timeout=60)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_strategy(case_id: int) -> Optional[Dict]:
    """获取策略"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/cases/{case_id}/strategy", timeout=60)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_evidence_suggestions(case_id: int) -> Optional[Dict]:
    """获取证据补充建议"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/cases/{case_id}/evidence-suggestions", timeout=60)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_case_deadlines(case_id: int) -> List[Dict]:
    """获取案件时间节点"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/time-control/case/{case_id}/deadlines", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def add_deadline(case_id: int, deadline_data: Dict) -> Optional[Dict]:
    """添加时间节点"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/time-control/case/{case_id}/deadlines", json=deadline_data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_analyses(case_id: int) -> List[Dict]:
    """获取对抗性分析列表"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/adversarial/case/{case_id}/analyses", timeout=10)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def create_analysis(case_id: int, opponent_name: str, opponent_claims: str) -> Optional[Dict]:
    """创建对抗性分析"""
    try:
        data = {
            "opponent_name": opponent_name,
            "opponent_claims": opponent_claims
        }
        r = requests.post(
            f"{API_BASE_URL}/api/adversarial/case/{case_id}/analysis",
            json=data,
            timeout=120
        )
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_opponent_analysis(case_id: int) -> Optional[Dict]:
    """获取对方分析"""
    try:
        r = requests.post(
            f"{API_BASE_URL}/api/adversarial/case/{case_id}/opponent-analysis",
            timeout=120
        )
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_evidence_matrix(case_id: int) -> Optional[Dict]:
    """获取证据矩阵"""
    try:
        r = requests.post(
            f"{API_BASE_URL}/api/adversarial/case/{case_id}/evidence-matrix",
            timeout=120
        )
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_scenario_prediction(case_id: int) -> Optional[Dict]:
    """获取情景预测"""
    try:
        r = requests.post(
            f"{API_BASE_URL}/api/adversarial/case/{case_id}/scenario-prediction",
            timeout=120
        )
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_case_execution(case_id: int) -> Optional[Dict]:
    """获取执行信息"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/cases/{case_id}/execution", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_execution_list() -> List[Dict]:
    """获取执行列表"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/cases/execution/list", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def add_execution_record(case_id: int, record_type: str, description: str, amount: float = 0) -> bool:
    """添加执行记录"""
    try:
        data = {
            "type": record_type,
            "description": description,
            "amount": amount,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        r = requests.post(f"{API_BASE_URL}/api/cases/{case_id}/execution/record", json=data, timeout=10)
        return r.status_code == 200
    except:
        return False


# ============ 导出功能 ============

def export_to_markdown(content: str, title: str = "导出文档") -> str:
    """导出为Markdown格式"""
    header = f"# {title}\n\n导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
    return header + content


def export_to_text(content: str, title: str = "导出文档") -> str:
    """导出为纯文本格式"""
    header = f"{title}\n{'=' * len(title)}\n导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    # 移除Markdown格式符号
    text = content
    text = text.replace('## ', '\n【').replace('**', '').replace('*', '')
    text = text.replace('---', '\n' + '-' * 50)
    text = text.replace('- ', '\n• ')
    text = text.replace('|', ' | ')
    return header + text


def download_markdown(content: str, filename: str):
    """提供Markdown文件下载"""
    st.download_button(
        label="📥 下载 Markdown",
        data=content.encode('utf-8'),
        file_name=f"{filename}.md",
        mime="text/markdown"
    )


def download_text(content: str, filename: str):
    """提供文本文件下载"""
    st.download_button(
        label="📥 下载 TXT",
        data=content.encode('utf-8'),
        file_name=f"{filename}.txt",
        mime="text/plain"
    )


def download_json(data: Dict, filename: str):
    """提供JSON文件下载"""
    st.download_button(
        label="📥 下载 JSON",
        data=json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'),
        file_name=f"{filename}.json",
        mime="application/json"
    )


def show_export_options(content: str, title: str, filename: str):
    """显示导出选项"""
    col1, col2, col3 = st.columns(3)
    with col1:
        download_markdown(export_to_markdown(content, title), filename)
    with col2:
        download_text(export_to_text(content, title), filename)
    with col3:
        download_json({"title": title, "content": content, "export_time": datetime.now().isoformat()}, filename)


# ============ 会话状态管理 ============

def init_case_session_state():
    """初始化案件相关session_state"""
    if "selected_case" not in st.session_state:
        st.session_state.selected_case = None
    if "case_chat_messages" not in st.session_state:
        st.session_state.case_chat_messages = []
    if "supplement_submitted" not in st.session_state:
        st.session_state.supplement_submitted = False
    if "recommended_docs" not in st.session_state:
        st.session_state.recommended_docs = []
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = {}
    if "current_analysis" not in st.session_state:
        st.session_state.current_analysis = None


def select_case():
    """案件选择器"""
    cases = get_cases()
    if not cases:
        st.warning("请先创建案件")
        return None

    case_options = {f"#{c['id']} {c.get('title', '未命名')[:30]}": c for c in cases}
    selected_label = st.selectbox("选择案件", options=list(case_options.keys()))
    selected_case = case_options.get(selected_label)
    if selected_case:
        st.session_state.selected_case = selected_case
    return selected_case


def show_case_selector(sidebar_mode: bool = True):
    """显示案件选择器（可选择侧边栏或主区域）"""
    if sidebar_mode:
        with st.sidebar:
            return select_case()
    else:
        return select_case()


# ============ 显示组件 ============

def show_case_basic_info(case: Dict):
    """显示案件基本信息"""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        status = case.get('status', 'active')
        status_text = {"active": "进行中", "pending": "待处理", "closed": "已结案", "suspended": "已中止"}.get(status, status)
        status_icon = {"active": "🟢", "pending": "🟡", "closed": "⚫", "suspended": "🟠"}.get(status, "⚪")
        st.metric("状态", f"{status_icon} {status_text}")

    with col2:
        case_type = case.get('case_type', '未分类')
        st.metric("案件类型", case_type)

    with col3:
        priority = case.get('priority', 'medium')
        priority_text = {"low": "低", "medium": "中", "high": "高"}.get(priority, priority)
        priority_icon = {"low": "⚪", "medium": "🟡", "high": "🔴"}.get(priority, "⚪")
        st.metric("优先级", f"{priority_icon} {priority_text}")

    with col4:
        project_name = case.get('project_name', '无')
        st.metric("关联项目", project_name)

    with col5:
        claim_amount = case.get('claim_amount', 0)
        try:
            amount_val = float(claim_amount) if claim_amount else 0
        except (ValueError, TypeError):
            amount_val = 0
        if amount_val:
            st.metric("诉讼金额", f"¥{amount_val:,.0f}")
        else:
            st.metric("诉讼金额", "-")


def show_quick_questions(case_id: int):
    """显示快捷问题按钮"""
    st.markdown("#### 🎯 快捷问题")
    quick_questions = [
        ("📋 案件概述", "请简要概述这个案件的核心内容、争议焦点和我方的主要诉求"),
        ("⚖️ 法律分析", "这个案件涉及哪些法律问题？适用哪些法律条文？"),
        ("📊 证据评估", "根据现有证据，分析我方证据是否充分，还缺什么证据？"),
        ("💡 诉讼策略", "基于当前情况，我方应该采取什么诉讼策略？"),
        ("⚠️ 风险提示", "这个案件有哪些主要风险？对方可能采取什么反击手段？"),
        ("🎯 补充建议", "根据目前的案件材料，我还需要补充哪些信息？"),
        ("📝 文书建议", "基于当前分析，建议生成哪些法律文书？"),
        ("🔄 进展追踪", "这个案件目前进展如何？有哪些待处理事项？"),
    ]

    q_cols = st.columns(4)
    for i, (label, question) in enumerate(quick_questions):
        with q_cols[i % 4]:
            if st.button(label, use_container_width=True, key=f"q_{i}"):
                st.session_state.quick_question = question


def show_analysis_display(result: Dict, title: str = "分析结果"):
    """通用分析结果显示组件"""
    st.subheader(f"📊 {title}")

    # 根据结果类型显示不同内容
    if isinstance(result, dict):
        for key, value in result.items():
            if isinstance(value, list) and value:
                with st.expander(f"📌 {key.replace('_', ' ').title()}", expanded=True):
                    for item in value:
                        st.markdown(f"- {item}")
            elif isinstance(value, str) and value:
                with st.expander(f"📄 {key.replace('_', ' ').title()}", expanded=True):
                    st.markdown(value)
    elif isinstance(result, str):
        st.markdown(result)
    else:
        st.json(result)


def show_document_preview(doc_content: str, doc_title: str = "文书预览"):
    """文书预览组件"""
    with st.expander(f"📄 {doc_title}", expanded=True):
        st.markdown(doc_content)


# ============ 数据联动辅助 ============

def get_linked_data(case_id: int) -> Dict[str, Any]:
    """获取案件相关联的所有数据"""
    return {
        "case": get_case(case_id),
        "evidence": get_case_evidence(case_id),
        "documents": get_generated_documents(case_id),
        "deadlines": get_case_deadlines(case_id),
        "execution": get_case_execution(case_id),
        "analyses": get_analyses(case_id),
        "conversation_history": get_conversation_history(case_id),
    }


def show_data_summary(data: Dict[str, Any]):
    """显示数据汇总"""
    st.markdown("#### 📊 数据汇总")

    col1, col2, col3 = st.columns(3)
    with col1:
        evidence_count = len(data.get("evidence", []))
        st.metric("证据数量", evidence_count)
    with col2:
        doc_count = len(data.get("documents", []))
        st.metric("文书数量", doc_count)
    with col3:
        deadline_count = len(data.get("deadlines", []))
        st.metric("时间节点", deadline_count)


# ============ 通用对话组件 ============

def show_chat_interface(case_id: int, messages_key: str = "chat_messages"):
    """通用对话界面组件"""
    # 快捷问题
    show_quick_questions(case_id)

    st.markdown("---")

    # 对话历史
    st.markdown("#### 💬 对话记录")
    if st.session_state.get(messages_key):
        for msg in st.session_state[messages_key]:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(f"**👤 您:** {msg['content']}")
            else:
                with st.chat_message("assistant"):
                    st.markdown(f"**🤖 AI分析:** {msg['content']}")
                    if msg.get("suggestions"):
                        st.markdown("**💡 后续建议:**")
                        for s in msg["suggestions"]:
                            st.markdown(f"- {s}")
                    if msg.get("evidence_gaps"):
                        st.markdown("**📋 证据缺口:**")
                        for g in msg["evidence_gaps"]:
                            st.markdown(f"- {g}")
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

    col_send, col_clear, col_export = st.columns([1, 1, 2])
    with col_send:
        submitted = st.button("📤 发送分析", type="primary", use_container_width=True)
    with col_clear:
        if st.button("🗑️ 清空对话", use_container_width=True):
            st.session_state[messages_key] = []
            st.session_state.quick_question = ""
            st.rerun()
    with col_export:
        if st.button("📥 补充到案件材料", use_container_width=True) and user_input:
            current_case = get_case(case_id)
            if current_case:
                current_desc = current_case.get('description', '')
                new_desc = f"{current_desc}\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 用户补充:\n{user_input}"
                update_case(case_id, {"description": new_desc})
                st.session_state.selected_case = get_case(case_id)
                st.success("已补充到案件材料")
                st.rerun()

    return submitted, user_input


# ============ 页面通用布局 ============

def create_page_layout(title: str, icon: str = "📋"):
    """创建标准页面布局"""
    st.title(f"{icon} {title}")
    st.markdown("---")
    return st


def show_navigation_buttons():
    """显示导航按钮"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📄 文书生成", use_container_width=True):
            st.switch_page("pages/3_文书生成.py")

    with col2:
        if st.button("📋 证据管理", use_container_width=True):
            st.switch_page("pages/7_证据管理.py")

    with col3:
        if st.button("⚔️ 对抗性分析", use_container_width=True):
            st.switch_page("pages/5_对抗性分析.py")

    with col4:
        if st.button("⏰ 时间把控", use_container_width=True):
            st.switch_page("pages/8_时间把控.py")
