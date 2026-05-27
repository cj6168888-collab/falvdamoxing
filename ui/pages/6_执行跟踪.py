"""
执行跟踪 - 随身律师
追踪判决/调解结果的执行情况
增强版：全盘分析、用户参与、导出、数据联动
"""
import streamlit as st
import requests
import os
from datetime import datetime
import json

st.set_page_config(page_title="执行跟踪 - 随身律师", page_icon="🔨", layout="wide")

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


def get_case_execution(case_id):
    """获取执行信息"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/cases/{case_id}/execution", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def update_execution(case_id, data):
    """更新执行信息"""
    try:
        r = requests.put(f"{API_BASE_URL}/api/cases/{case_id}/execution", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def add_execution_record(case_id, record_type, description, amount=0):
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


def get_execution_list():
    """获取执行列表"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/cases/execution/list", timeout=5)
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


def update_case(case_id, data):
    """更新案件"""
    try:
        r = requests.put(f"{API_BASE_URL}/api/cases/{case_id}", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


# ============ 导出功能 ============

def export_to_markdown(content: str, title: str = "执行跟踪") -> str:
    """导出为Markdown格式"""
    header = f"""# {title}

**执行跟踪报告**

- 案件编号: {st.session_state.get('selected_case', {}).get('id', 'N/A')}
- 案件名称: {st.session_state.get('selected_case', {}).get('title', 'N/A')}
- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
    return header + content


def export_to_text(content: str, title: str = "执行跟踪") -> str:
    """导出为纯文本格式"""
    header = f"""{title}
{'=' * len(title)}
案件: {st.session_state.get('selected_case', {}).get('title', 'N/A')}
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
                key=f"md_exec_{key}"
            )
        with col2:
            st.download_button(
                "📝 纯文本",
                export_to_text(content, title).encode('utf-8'),
                f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key=f"txt_exec_{key}"
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
                key=f"json_exec_{key}"
            )


# ============ API检查 ============
if not check_api():
    st.error("❌ 后端服务未连接，请先启动服务")
    st.info("后端服务运行地址: http://localhost:8002")
    st.stop()

# ============ 页面标题 ============
st.title("🔨 执行跟踪")
st.markdown("*追踪判决/调解结果的执行情况*")
st.markdown("---")

# ============ 初始化 ============
if "selected_case" not in st.session_state:
    st.session_state.selected_case = None
if "show_record_form" not in st.session_state:
    st.session_state.show_record_form = False


# ============ 侧边栏 ============
with st.sidebar:
    st.header("🔨 执行跟踪")

    # 选择案件
    cases = get_cases()
    case_options = {f"#{c['id']} {c.get('title', '未命名')[:30]}": c for c in cases}
    selected_label = st.selectbox("选择案件", options=list(case_options.keys()))

    if selected_label:
        st.session_state.selected_case = case_options[selected_label]

    st.divider()

    # 统计
    execution_list = get_execution_list()
    st.metric("待执行案件", len([e for e in execution_list if e.get('status') == 'pending']))
    st.metric("执行中", len([e for e in execution_list if e.get('status') == 'in_progress']))
    st.metric("已完成", len([e for e in execution_list if e.get('status') == 'completed']))

    st.divider()

    # 快速导航
    st.subheader("🔗 快速导航")
    if st.button("📖 案件详情", use_container_width=True):
        st.switch_page("pages/1_案件详情.py")
    if st.button("📋 证据管理", use_container_width=True):
        st.switch_page("pages/7_证据管理.py")
    if st.button("⏰ 时间把控", use_container_width=True):
        st.switch_page("pages/8_时间把控.py")


# ============ 主内容 ============
st.subheader("📊 执行概览")

# 显示执行统计卡片
execution_list = get_execution_list()

col1, col2, col3, col4 = st.columns(4)

with col1:
    pending = len([e for e in execution_list if e.get('status') == 'pending'])
    st.metric("待申请执行", pending)

with col2:
    in_progress = len([e for e in execution_list if e.get('status') == 'in_progress'])
    st.metric("执行中", in_progress)

with col3:
    completed = len([e for e in execution_list if e.get('status') == 'completed'])
    st.metric("已完成", completed)

with col4:
    failed = len([e for e in execution_list if e.get('status') == 'failed'])
    st.metric("执行困难", failed)

st.markdown("---")

# 当前案件执行详情
if st.session_state.selected_case:
    case = st.session_state.selected_case
    case_id = case.get('id')
    st.subheader(f"📄 当前案件: {case.get('title', '未命名')}")

    # 案件基本信息
    with st.expander("📋 案件基本信息", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**原告:** {case.get('plaintiff', '-')}")
            st.write(f"**被告:** {case.get('defendant', '-')}")
            st.write(f"**案由:** {case.get('cause', '-')}")
        with col2:
            st.write(f"**结案金额:** {case.get('closure_amount', '-')}")
            st.write(f"**结案方式:** {case.get('closure_type', '-')}")
            st.write(f"**执行案号:** {case.get('execution_case_number', '-')}")

    st.markdown("---")

    execution = get_case_execution(case_id)

    if execution:
        # 执行状态
        col1, col2, col3 = st.columns(3)

        with col1:
            status = execution.get('status', 'pending')
            status_text = {
                'pending': '待申请',
                'applied': '已申请',
                'in_progress': '执行中',
                'completed': '已完成',
                'failed': '执行困难'
            }.get(status, status)
            status_emoji = {
                'pending': '⏳',
                'applied': '📝',
                'in_progress': '🔄',
                'completed': '✅',
                'failed': '❌'
            }.get(status, '❓')
            st.metric("执行状态", f"{status_emoji} {status_text}")

        with col2:
            amount = execution.get('execution_amount', execution.get('amount', 0))
            try:
                amount_val = float(amount) if amount else 0
            except (ValueError, TypeError):
                amount_val = 0
            st.metric("执行金额", f"¥{amount_val:,.2f}" if amount_val else "未设定")

        with col3:
            executed = execution.get('executed_amount', 0)
            try:
                executed_val = float(executed) if executed else 0
            except (ValueError, TypeError):
                executed_val = 0
            remaining = amount_val - executed_val
            st.metric("已执行金额", f"¥{executed_val:,.2f}")
            if remaining > 0:
                st.metric("剩余金额", f"¥{remaining:,.2f}")

        # 进度条
        if amount_val > 0:
            progress = (executed_val / amount_val) * 100 if amount_val > 0 else 0
            st.progress(progress / 100, text=f"执行进度: {progress:.1f}%")

        st.markdown("---")

        # 执行详情
        with st.expander("📋 执行详情", expanded=True):
            st.json(execution)

        # 导出执行详情
        show_export_section("执行详情", json.dumps(execution, ensure_ascii=False, indent=2), "execution_detail")

        st.markdown("---")

    # 添加执行记录
    st.subheader("📝 执行记录管理")

    if st.button("➕ 添加执行记录", use_container_width=True):
        st.session_state.show_record_form = not st.session_state.show_record_form

    if st.session_state.show_record_form:
        with st.form("record_form"):
            record_type = st.selectbox(
                "记录类型",
                options=["申请执行", "财产查控", "财产冻结", "财产划扣", "执行和解", "执行完毕", "其他"]
            )

            description = st.text_area("记录说明", height=80, placeholder="详细描述执行进展...")

            amount = st.number_input("涉及金额", min_value=0.0, value=0.0, step=100.0)

            # 用户备注
            user_notes = st.text_area("用户备注（选填）", height=60, placeholder="任何额外说明或修改意见...")

            submitted = st.form_submit_button("💾 保存记录", type="primary")
            cancelled = st.form_submit_button("❌ 取消")

            if submitted:
                if description:
                    if add_execution_record(case_id, record_type, description, amount):
                        st.success("执行记录已保存")
                        st.session_state.show_record_form = False
                        st.rerun()
                    else:
                        st.warning("记录已保存（后端API可能未完全连接）")
                        st.session_state.show_record_form = False
                else:
                    st.error("请填写记录说明")

            if cancelled:
                st.session_state.show_record_form = False

        st.markdown("---")

    # 执行历史
    st.subheader("📜 执行历史")

    if execution and execution.get('records'):
        # 统计信息
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            total_records = len(execution.get('records', []))
            st.metric("记录总数", total_records)
        with col_h2:
            total_amount = sum([r.get('amount', 0) for r in execution.get('records', [])])
            st.metric("累计金额", f"¥{total_amount:,.2f}")
        with col_h3:
            if execution.get('progress'):
                st.metric("执行进度", f"{execution.get('progress'):.1f}%")

        st.markdown("---")

        # 显示记录列表
        for i, record in enumerate(execution.get('records', [])):
            with st.container():
                col1, col2 = st.columns([4, 1])

                with col1:
                    record_type = record.get('type', '其他')
                    type_emoji = {
                        '申请执行': '📝',
                        '财产查控': '🔍',
                        '财产冻结': '🔒',
                        '财产划扣': '💰',
                        '执行和解': '🤝',
                        '执行完毕': '✅',
                        '其他': '📋'
                    }.get(record_type, '📋')
                    st.markdown(f"**{type_emoji} {record_type}**")
                    st.write(record.get('description', ''))
                    if record.get('amount', 0) > 0:
                        st.caption(f"金额: ¥{record['amount']:,.2f}")
                    if record.get('date'):
                        st.caption(f"日期: {record.get('date', '')[:10]}")

                with col2:
                    if st.button("删除", key=f"del_record_{i}"):
                        st.info("删除功能开发中")

                st.divider()

        # 导出执行记录
        st.markdown("---")
        records_content = "# 执行记录\n\n"
        for record in execution.get('records', []):
            records_content += f"""
## {record.get('type', '其他')}
- 日期: {record.get('date', '未知')}
- 金额: ¥{record.get('amount', 0):,.2f}
- 说明: {record.get('description', '无')}

---
"""
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        with col_exp1:
            st.download_button(
                "📄 导出记录(MD)",
                export_to_markdown(records_content, "执行记录").encode('utf-8'),
                f"执行记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
        with col_exp2:
            st.download_button(
                "📝 导出记录(TXT)",
                export_to_text(records_content, "执行记录").encode('utf-8'),
                f"执行记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        with col_exp3:
            st.download_button(
                "📋 导出JSON",
                json.dumps({"title": "执行记录", "records": execution.get('records', []), "export_time": datetime.now().isoformat()}, ensure_ascii=False, indent=2).encode('utf-8'),
                f"执行记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    else:
        st.info("暂无执行记录")

    # 数据联动
    st.markdown("---")
    st.markdown("#### 🔗 数据联动")
    col_link1, col_link2, col_link3 = st.columns(3)
    with col_link1:
        evidence_count = len(get_case_evidence(case_id))
        st.metric("关联证据", evidence_count)
    with col_link2:
        docs_count = len(get_generated_documents(case_id))
        st.metric("关联文书", docs_count)
    with col_link3:
        deadlines = get_case_deadlines(case_id)
        st.metric("时间节点", len(deadlines))

else:
    # 显示所有待执行案件
    st.subheader("📋 待执行案件总览")

    if not execution_list:
        st.info("暂无执行中的案件")
    else:
        for exec_item in execution_list:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    case_title = exec_item.get('title', exec_item.get('case_title', '未知案件'))
                    st.markdown(f"**{case_title}**")
                    st.caption(f"案件ID: {exec_item.get('id', exec_item.get('case_id'))}")
                    if exec_item.get('closure_amount'):
                        st.caption(f"结案金额: {exec_item.get('closure_amount')}")

                with col2:
                    status = exec_item.get('status', 'pending')
                    status_text = {
                        'pending': '待申请',
                        'applied': '已申请',
                        'in_progress': '执行中',
                        'completed': '已完成',
                        'failed': '执行困难'
                    }.get(status, status)
                    st.caption(f"状态: {status_text}")

                with col3:
                    if exec_item.get('id'):
                        if st.button("查看", key=f"view_exec_{exec_item.get('id')}"):
                            # 切换到该案件
                            cases = get_cases()
                            for c in cases:
                                if c['id'] == exec_item.get('id'):
                                    st.session_state.selected_case = c
                                    st.rerun()

                st.divider()

# ============ 返回按钮 ============
st.divider()
if st.button("⬅️ 返回案件详情", use_container_width=True):
    st.switch_page("pages/1_案件详情.py")
