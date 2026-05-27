"""
知识库问答页面 - 简洁易用的法律问答
增强版：全盘分析、用户参与、导出、数据联动
"""
import streamlit as st
import requests
import os
from datetime import datetime
import json

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8002")

st.set_page_config(page_title="知识库问答", page_icon="💬")


def check_api():
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except:
        return False


def get_cases():
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


def update_case(case_id, data):
    """更新案件"""
    try:
        r = requests.put(f"{API_BASE_URL}/api/cases/{case_id}", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_case_evidence(case_id):
    """获取案件证据"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/evidence/case/{case_id}", timeout=5)
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


def get_case_deadlines(case_id):
    """获取案件时间节点"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/time-control/case/{case_id}/deadlines", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def send_question(case_id, question):
    try:
        r = requests.post(
            f"{API_BASE_URL}/api/cases/{case_id}/ask",
            json={"question": question},
            timeout=300
        )
        if r.status_code == 200:
            return r.json().get("answer", "")
        else:
            return f"请求失败: {r.status_code}"
    except requests.exceptions.Timeout:
        return "请求超时，请稍后重试"
    except Exception as e:
        return f"错误: {str(e)}"


# ============ 导出功能 ============

def export_to_markdown(content: str, title: str = "知识问答") -> str:
    """导出为Markdown格式"""
    header = f"""# {title}

**法律知识问答记录**

- 案件编号: {st.session_state.get('current_case_id', 'N/A')}
- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
    return header + content


def export_to_text(content: str, title: str = "知识问答") -> str:
    """导出为纯文本格式"""
    header = f"""{title}
{'=' * len(title)}
案件编号: {st.session_state.get('current_case_id', 'N/A')}
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
                key=f"md_qa_{key}"
            )
        with col2:
            st.download_button(
                "📝 纯文本",
                export_to_text(content, title).encode('utf-8'),
                f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key=f"txt_qa_{key}"
            )
        with col3:
            st.download_button(
                "📋 JSON",
                json.dumps({
                    "title": title,
                    "content": content,
                    "case_id": st.session_state.get('current_case_id'),
                    "export_time": datetime.now().isoformat()
                }, ensure_ascii=False, indent=2).encode('utf-8'),
                f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key=f"json_qa_{key}"
            )


# API 检查
if not check_api():
    st.error("❌ 后端服务未连接")
    st.info("请确保后端服务正在运行")
    st.stop()

st.title("💬 知识库问答")
st.markdown("*基于案件材料的法律智能问答*")
st.markdown("---")

# 初始化消息历史
if "qa_messages" not in st.session_state:
    st.session_state.qa_messages = []
if "current_case_id" not in st.session_state:
    st.session_state.current_case_id = None

# ============ 侧边栏 ============
with st.sidebar:
    st.header("📌 知识库问答")

    # 选择案件
    cases = get_cases()
    if not cases:
        st.warning("⚠️ 请先创建案件")
    else:
        case_options = {f"#{c['id']} {c.get('title', '未命名')[:30]}": c['id'] for c in cases}
        selected = st.selectbox("选择案件", options=list(case_options.keys()))
        current_case_id = case_options[selected]
        st.session_state.current_case_id = current_case_id

        # 案件统计
        st.divider()
        st.subheader("📊 案件数据")

        evidence = get_case_evidence(current_case_id)
        docs = get_generated_documents(current_case_id)
        deadlines = get_case_deadlines(current_case_id)

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("证据", len(evidence))
        with col_s2:
            st.metric("文书", len(docs))

        st.metric("时间节点", len(deadlines))

        st.divider()

        # 快速导航
        st.subheader("🔗 快速导航")
        if st.button("📖 案件详情", use_container_width=True):
            st.switch_page("pages/1_案件详情.py")
        if st.button("📄 文书生成", use_container_width=True):
            st.switch_page("pages/3_文书生成.py")
        if st.button("📋 证据管理", use_container_width=True):
            st.switch_page("pages/7_证据管理.py")
        if st.button("⚔️ 对抗性分析", use_container_width=True):
            st.switch_page("pages/5_对抗性分析.py")
        if st.button("⏰ 时间把控", use_container_width=True):
            st.switch_page("pages/8_时间把控.py")

        st.divider()

        # 导出对话
        st.subheader("📥 导出")
        if st.button("📄 导出全部对话", use_container_width=True):
            st.session_state.show_qa_export = True


# ============ 主内容 ============
if "current_case_id" not in st.session_state or not st.session_state.current_case_id:
    st.warning("⚠️ 请先在侧边栏选择案件")
    st.stop()

current_case_id = st.session_state.current_case_id
case_data = None

# 获取案件数据
cases = get_cases()
if cases:
    case_data = next((c for c in cases if c['id'] == current_case_id), None)

if case_data:
    # 案件信息
    st.subheader(f"📋 当前案件: {case_data.get('title', '未命名')}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.write(f"**原告:** {case_data.get('plaintiff', '-')}")
    with col2:
        st.write(f"**被告:** {case_data.get('defendant', '-')}")
    with col3:
        st.write(f"**案由:** {case_data.get('cause', '-')}")
    with col4:
        st.write(f"**金额:** {case_data.get('claim_amount', '-')}")

    st.markdown("---")

# 问题模板
st.markdown("#### 🎯 快捷问题")

cols = st.columns(4)
templates = [
    ("📋 案件概述", "请简要概述这个案件的核心内容和争议焦点，进行全面分析"),
    ("⚖️ 法律分析", "这个案件涉及哪些法律问题？请适用哪些法律条文？请深度分析"),
    ("📊 证据评估", "现有证据能否支持我方主张？还缺什么证据？请给出完整评估"),
    ("💡 诉讼建议", "我方应该采取什么诉讼策略？请给出详细建议"),
    ("⚠️ 风险提示", "这个案件有哪些主要风险？对方可能采取什么反击手段？请全面分析"),
    ("🎯 补充建议", "根据目前的案件材料，我还需要补充哪些信息？请给出完整建议"),
    ("📝 文书建议", "基于当前分析，建议生成哪些法律文书？请说明每种文书的作用"),
    ("🔄 进展追踪", "这个案件目前进展如何？有哪些待处理事项？请给出时间线"),
]

for i, (name, question) in enumerate(templates):
    with cols[i % 4]:
        if st.button(name, use_container_width=True, key=f"qa_template_{i}"):
            st.session_state.question_input = question

st.markdown("---")

# 问答区域
st.markdown("#### 💬 问答对话")

# 显示历史消息
for idx, msg in enumerate(st.session_state.qa_messages):
    role = "user" if msg["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(msg["content"])
        # 添加导出按钮
        if msg["role"] == "assistant" and msg.get("content"):
            show_export_section(f"问答记录_{idx+1}", msg['content'], f"qa_{idx}")

st.markdown("---")

# 输入框
if "question_input" not in st.session_state:
    st.session_state.question_input = ""

user_input = st.text_input(
    "💭 输入问题：",
    value=st.session_state.question_input,
    placeholder="输入您的问题（可针对案件、法律、证据等提问）...",
    key="question_input_widget",
    on_change=None
)

# 用户反馈区域
with st.expander("✏️ 用户反馈（选填）", expanded=False):
    user_feedback = st.text_area(
        "您对AI回答有什么意见或修改建议？",
        placeholder="请详细说明...",
        height=60,
        key="qa_feedback"
    )

col_send, col_clear, col_save = st.columns([1, 1, 2])

with col_send:
    submitted = st.button("📤 发送", type="primary", use_container_width=True)

with col_clear:
    if st.button("🗑️ 清空"):
        st.session_state.qa_messages = []
        st.session_state.question_input = ""
        st.rerun()

with col_save:
    if st.button("📥 保存到案件"):
        if user_input:
            current_case = get_case(current_case_id)
            if current_case:
                current_desc = current_case.get('description', '')
                feedback_note = f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 【知识问答】\n问题: {user_input}"
                if user_feedback:
                    feedback_note += f"\n用户反馈: {user_feedback}"
                update_case(current_case_id, {"description": current_desc + feedback_note})
                st.success("已保存到案件材料")
        else:
            st.warning("请先输入问题")

if submitted and user_input:
    st.session_state.question_input = ""
    st.session_state.qa_messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("🤔 AI深度分析中（可能需要几分钟）..."):
        answer = send_question(current_case_id, user_input)

    if answer and not answer.startswith("错误"):
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state.qa_messages.append({"role": "assistant", "content": answer})

        # 显示导出选项
        with st.expander("📥 导出此回答", expanded=False):
            show_export_section(f"AI回答_{len(st.session_state.qa_messages)}", answer, "single_answer")
    else:
        st.error(f"获取回答失败: {answer}")

# 显示导出对话（如果点击了导出按钮）
if st.session_state.get("show_qa_export") and st.session_state.qa_messages:
    st.markdown("---")
    st.subheader("📥 导出全部对话")

    all_qa_content = "# 知识问答对话记录\n\n"
    for msg in st.session_state.qa_messages:
        role = "用户" if msg["role"] == "user" else "AI"
        all_qa_content += f"\n## {role}:\n\n{msg['content']}\n\n---\n"

    col_exp1, col_exp2, col_exp3 = st.columns(3)
    with col_exp1:
        st.download_button(
            "📄 Markdown",
            export_to_markdown(all_qa_content, "知识问答对话记录").encode('utf-8'),
            f"知识问答_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )
    with col_exp2:
        st.download_button(
            "📝 纯文本",
            export_to_text(all_qa_content, "知识问答对话记录").encode('utf-8'),
            f"知识问答_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    with col_exp3:
        st.download_button(
            "📋 JSON",
            json.dumps({
                "title": "知识问答对话记录",
                "case_id": current_case_id,
                "messages": st.session_state.qa_messages,
                "export_time": datetime.now().isoformat()
            }, ensure_ascii=False, indent=2).encode('utf-8'),
            f"知识问答_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# ============ 返回按钮 ============
st.divider()
if st.button("⬅️ 返回案件详情", use_container_width=True):
    st.switch_page("pages/1_案件详情.py")
