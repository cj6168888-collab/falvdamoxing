"""
文书生成 - 随身律师
基于案件材料生成法律文书
增强版：全盘生成、用户参与、导出、数据联动
"""
import streamlit as st
import requests
import os
import json
from datetime import datetime

st.set_page_config(page_title="文书生成 - 随身律师", page_icon="📝", layout="wide")

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
    except Exception as e:
        print(f"Generate document error: {e}")
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


# ============ 导出功能 ============

def export_to_markdown(content: str, title: str = "文书") -> str:
    """导出为Markdown格式"""
    header = f"""# {title}

**法律文书自动生成**

- 案件编号: {st.session_state.get('selected_case', {}).get('id', 'N/A')}
- 案件名称: {st.session_state.get('selected_case', {}).get('title', 'N/A')}
- 文书类型: {title}
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
    return header + content


def export_to_text(content: str, title: str = "文书") -> str:
    """导出为纯文本格式"""
    header = f"""{title}
{'=' * len(title)}
案件: {st.session_state.get('selected_case', {}).get('title', 'N/A')}
文书类型: {title}
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
                key=f"md_doc_{key}"
            )
        with col2:
            st.download_button(
                "📝 纯文本",
                export_to_text(content, title).encode('utf-8'),
                f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key=f"txt_doc_{key}"
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
                key=f"json_doc_{key}"
            )


# ============ API检查 ============
if not check_api():
    st.error("❌ 后端 API 未连接，请先启动服务")
    st.info("后端服务运行地址: http://localhost:8002")
    st.stop()

# ============ 页面标题 ============
st.title("📝 文书生成")
st.markdown("*基于案件材料智能生成法律文书*")
st.markdown("---")

# ============ 初始化 ============
if "selected_case" not in st.session_state:
    st.session_state.selected_case = None
if "generated_content" not in st.session_state:
    st.session_state.generated_content = None
if "user_modifications" not in st.session_state:
    st.session_state.user_modifications = {}


# ============ 侧边栏 ============
with st.sidebar:
    st.header("📌 文书生成")

    # 选择案件
    cases = get_cases()
    case_options = {f"#{c['id']} {c.get('title', '未命名')[:30]}": c for c in cases}
    selected_label = st.selectbox("选择案件", options=list(case_options.keys()))

    if selected_label:
        st.session_state.selected_case = case_options[selected_label]

    st.divider()

    # 统计
    if st.session_state.selected_case:
        docs = get_generated_documents(st.session_state.selected_case['id'])
        st.metric("已生成文书", len(docs))

    st.divider()

    # 模板列表
    st.subheader("📚 文书模板")
    templates = get_templates()
    for t in templates[:5]:
        st.caption(f"• {t.get('name', '未命名')}")

    st.divider()

    # 快速导航
    st.subheader("🔗 快速导航")
    if st.button("📖 案件详情", use_container_width=True):
        st.switch_page("pages/1_案件详情.py")
    if st.button("📋 证据管理", use_container_width=True):
        st.switch_page("pages/7_证据管理.py")


# ============ 主内容 ============
if not st.session_state.selected_case:
    st.warning("请先在左侧选择案件")
    st.info("或者前往「案件管理」创建案件")
else:
    case = st.session_state.selected_case
    case_id = case.get('id')
    st.subheader(f"📄 当前案件: {case.get('title', '未命名')}")

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

    # 文书类型选择
    st.subheader("📋 选择文书类型")

    col1, col2, col3 = st.columns(3)

    doc_types = [
        {"id": "起诉状", "icon": "⚔️", "desc": "民事起诉状", "category": "诉讼文书"},
        {"id": "答辩状", "icon": "🛡️", "desc": "民事答辩状", "category": "诉讼文书"},
        {"id": "上诉状", "icon": "📤", "desc": "民事上诉状", "category": "诉讼文书"},
        {"id": "申请书", "icon": "📝", "desc": "财产保全申请书", "category": "程序文书"},
        {"id": "代理词", "icon": "📋", "desc": "诉讼代理词", "category": "诉讼文书"},
        {"id": "和解协议", "icon": "🤝", "desc": "和解协议书", "category": "协议文书"},
        {"id": "证据目录", "icon": "📑", "desc": "证据材料目录", "category": "证据文书"},
        {"id": "律师函", "icon": "📨", "desc": "律师函", "category": "函件文书"},
        {"id": "申请执行", "icon": "🔨", "desc": "执行申请书", "category": "执行文书"},
    ]

    selected_type = None

    # 按类别分组显示
    st.markdown("#### 📁 诉讼文书")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(f"⚔️ 起诉状\n民事起诉状", key="doc_piqis", use_container_width=True):
            selected_type = "民事诉讼起诉状"
    with col2:
        if st.button(f"🛡️ 答辩状\n民事答辩状", key="doc_dabian", use_container_width=True):
            selected_type = "被告答辩状"
    with col3:
        if st.button(f"📤 上诉状\n民事上诉状", key="doc_shangsu", use_container_width=True):
            selected_type = "民事上诉状"

    st.markdown("#### 📁 程序与执行文书")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(f"📝 申请书\n财产保全", key="doc_baquan", use_container_width=True):
            selected_type = "财产保全申请书"
    with col2:
        if st.button(f"🔨 申请执行\n执行申请", key="doc_zhixing", use_container_width=True):
            selected_type = "执行申请书"
    with col3:
        if st.button(f"📋 代理词\n诉讼代理", key="doc_daili", use_container_width=True):
            selected_type = "诉讼代理词"

    st.markdown("#### 📁 协议与函件")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(f"🤝 和解协议", key="doc_hejie", use_container_width=True):
            selected_type = "和解协议书"
    with col2:
        if st.button(f"📨 律师函", key="doc_lvshi", use_container_width=True):
            selected_type = "律师函"
    with col3:
        if st.button(f"📑 证据目录", key="doc_zhengju", use_container_width=True):
            selected_type = "证据材料目录"

    st.markdown("---")

    # 生成文书
    if selected_type:
        st.subheader(f"✍️ 生成 {selected_type}")

        # 补充要求
        st.markdown("#### 📝 补充要求（可选）")
        custom_prompt = st.text_area(
            "您对这份文书有什么特殊要求或需要强调的内容？",
            placeholder="例如：重点说明违约金的计算方式、强调对方违约的具体事实...",
            height=80,
            key="custom_prompt_area"
        )

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            generate_btn = st.button("🚀 开始生成", type="primary", use_container_width=True)

        with col2:
            if st.button("📋 查看历史文书", use_container_width=True):
                st.session_state.show_history = True

        with col3:
            if st.button("💾 保存修改", use_container_width=True):
                st.success("修改已保存")

        if generate_btn:
            with st.spinner(f"正在生成{selected_type}，请稍候（可能需要几分钟）..."):
                result = generate_document(case_id, selected_type, custom_prompt)

                if result:
                    st.success(f"✅ {selected_type}生成成功！")

                    # 显示生成的文书
                    content = result.get('content', result.get('text', '暂无内容'))

                    # 存储生成的文书内容
                    st.session_state.generated_content = {
                        'type': selected_type,
                        'content': content,
                        'custom_prompt': custom_prompt,
                        'result': result
                    }

                    # 显示文书内容
                    with st.expander("📄 生成的文书内容", expanded=True):
                        st.markdown(content)

                    # 导出选项
                    show_export_section(selected_type, content, selected_type)

                    # 用户修改区域
                    st.markdown("---")
                    st.subheader("✏️ 用户修改意见")

                    user_feedback = st.text_area(
                        "您对生成的文书有什么修改意见？",
                        placeholder="请详细说明需要修改或补充的内容...",
                        height=80,
                        key="doc_feedback"
                    )

                    col_save1, col_save2 = st.columns(2)
                    with col_save1:
                        if st.button("💾 保存反馈到案件", use_container_width=True):
                            if user_feedback:
                                current_case = get_case(case_id)
                                if current_case:
                                    current_desc = current_case.get('description', '')
                                    feedback_entry = f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 【文书反馈-{selected_type}】\n{user_feedback}"
                                    update_case(case_id, {"description": current_desc + feedback_entry})
                                    st.success("反馈已保存到案件材料")
                            else:
                                st.warning("请填写修改意见")

                    with col_save2:
                        if st.button("🔄 重新生成", use_container_width=True):
                            st.rerun()
                else:
                    st.error(f"❌ {selected_type}生成失败，请检查后端服务是否正常运行")

    # 显示之前生成的文书内容（如果存在）
    if st.session_state.generated_content:
        st.markdown("---")
        st.subheader("📄 最近生成的文书")

        gen = st.session_state.generated_content
        with st.expander(f"📄 {gen['type']}", expanded=True):
            st.markdown(gen['content'])
            show_export_section(gen['type'], gen['content'], "recent")

    st.markdown("---")

    # 历史文书
    st.subheader("📁 历史文书")

    docs = get_generated_documents(case_id)

    if not docs:
        st.info("暂无已生成的文书")
    else:
        for doc in docs[:15]:
            with st.container():
                col1, col2, col3 = st.columns([4, 1, 1])

                with col1:
                    doc_type = doc.get('document_type', '未知')
                    created = doc.get('created_at', '')[:10] if doc.get('created_at') else ''
                    st.markdown(f"**{doc_type}**")
                    st.caption(f"生成时间: {created}")

                with col2:
                    content = doc.get('content', doc.get('text', ''))
                    if content and st.button("查看", key=f"view_doc_{doc.get('id')}"):
                        st.session_state.viewing_doc = doc

                with col3:
                    if content:
                        show_export_section(f"文书_{doc.get('id')}", content, f"saved_doc_{doc.get('id')}")

                # 显示查看的文书
                if st.session_state.get('viewing_doc') and st.session_state.viewing_doc.get('id') == doc.get('id'):
                    st.markdown("### 文书内容：")
                    st.markdown(content)

                    # 用户修改意见
                    st.markdown("#### ✏️ 修改意见")
                    modify_text = st.text_area(
                        "请输入您的修改意见：",
                        value=st.session_state.user_modifications.get(doc.get('id'), ''),
                        placeholder="输入需要修改的内容...",
                        height=60,
                        key=f"modify_{doc.get('id')}"
                    )
                    if st.button("💾 保存修改", key=f"save_modify_{doc.get('id')}"):
                        st.session_state.user_modifications[doc.get('id')] = modify_text
                        # 保存到案件
                        current_case = get_case(case_id)
                        if current_case and modify_text:
                            current_desc = current_case.get('description', '')
                            feedback_entry = f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 【历史文书修改-{doc_type}】\n{modify_text}"
                            update_case(case_id, {"description": current_desc + feedback_entry})
                            st.success("修改已保存")
                    show_export_section("历史文书", content, f"history_{doc.get('id')}")

                st.markdown("---")

# ============ 返回按钮 ============
st.divider()
if st.button("⬅️ 返回案件详情", use_container_width=True):
    st.switch_page("pages/1_案件详情.py")
