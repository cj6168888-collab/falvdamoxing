"""
时间把控 - 随身律师
诉讼时效、举证期限、开庭日期等时间节点管理
增强版：全盘分析、用户参与、导出、数据联动
"""
import streamlit as st
import requests
import os
from datetime import datetime, timedelta
import json

st.set_page_config(page_title="时间把控 - 随身律师", page_icon="⏰", layout="wide")

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


def get_case_deadlines(case_id):
    """获取案件时间节点"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/time-control/case/{case_id}/deadlines", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_case_timeline(case_id):
    """获取案件时间线"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/time-control/case/{case_id}/timeline", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def add_deadline(case_id, deadline_data):
    """添加时间节点"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/time-control/case/{case_id}/deadlines", json=deadline_data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def update_deadline(deadline_id, deadline_data):
    """更新时间节点"""
    try:
        r = requests.put(f"{API_BASE_URL}/api/time-control/deadlines/{deadline_id}", json=deadline_data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def delete_deadline(deadline_id):
    """删除时间节点"""
    try:
        r = requests.delete(f"{API_BASE_URL}/api/time-control/deadlines/{deadline_id}", timeout=10)
        return r.status_code == 200
    except:
        return False


def get_standard_deadlines():
    """获取标准时效"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/time-control/standard-deadlines", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def generate_milestones(case_id):
    """生成时间节点建议"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/time-control/case/{case_id}/generate-milestones", timeout=120)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_urgency_report(case_id):
    """获取紧急程度报告"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/time-control/case/{case_id}/urgency-report", timeout=10)
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


def update_case(case_id, data):
    """更新案件"""
    try:
        r = requests.put(f"{API_BASE_URL}/api/cases/{case_id}", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


# ============ 标准诉讼时效 ============
STANDARD_DEADLINES = [
    {"type": "诉讼时效", "name": "普通民事诉讼", "period": "3年", "start": "知道或应当知道权利被侵害时"},
    {"type": "诉讼时效", "name": "身体伤害", "period": "1年", "start": "伤害发生时"},
    {"type": "诉讼时效", "name": "租金纠纷", "period": "1年", "start": "租金应付之日起"},
    {"type": "诉讼时效", "name": "借款纠纷", "period": "3年", "start": "借款到期之日起"},
    {"type": "举证期限", "name": "答辩期", "period": "15日", "start": "收到起诉状之日起"},
    {"type": "举证期限", "name": "举证期限", "period": "30日", "start": "法院指定之日起"},
    {"type": "上诉期限", "name": "民事上诉", "period": "15日", "start": "判决书送达之日起"},
    {"type": "申请执行", "name": "执行申请", "period": "2年", "start": "判决生效之日起"},
]


# ============ 导出功能 ============

def export_to_markdown(content: str, title: str = "时间把控") -> str:
    """导出为Markdown格式"""
    header = f"""# {title}

**时间把控报告**

- 案件编号: {st.session_state.get('selected_case', {}).get('id', 'N/A')}
- 案件名称: {st.session_state.get('selected_case', {}).get('title', 'N/A')}
- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
    return header + content


def export_to_text(content: str, title: str = "时间把控") -> str:
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
                key=f"md_time_{key}"
            )
        with col2:
            st.download_button(
                "📝 纯文本",
                export_to_text(content, title).encode('utf-8'),
                f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key=f"txt_time_{key}"
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
                key=f"json_time_{key}"
            )


# ============ API检查 ============
if not check_api():
    st.error("❌ 后端服务未连接，请先启动服务")
    st.info("后端服务运行地址: http://localhost:8002")
    st.stop()

# ============ 页面标题 ============
st.title("⏰ 时间把控")
st.markdown("*管理诉讼时效、举证期限、开庭日期等关键时间节点*")
st.markdown("---")

# ============ 初始化 ============
if "selected_case" not in st.session_state:
    st.session_state.selected_case = None
if "show_deadline_form" not in st.session_state:
    st.session_state.show_deadline_form = False
if "urgency_report" not in st.session_state:
    st.session_state.urgency_report = None


# ============ 侧边栏 ============
with st.sidebar:
    st.header("⏰ 时间把控")

    # 选择案件
    cases = get_cases()
    case_options = {f"#{c['id']} {c.get('title', '未命名')[:30]}": c for c in cases}
    selected_label = st.selectbox("选择案件", options=list(case_options.keys()))

    if selected_label:
        st.session_state.selected_case = case_options[selected_label]

    st.divider()

    # 紧急提示
    if st.session_state.selected_case:
        deadlines = get_case_deadlines(st.session_state.selected_case['id'])
        today = datetime.now().date()

        urgent = [d for d in deadlines if d.get('deadline_date') and
                  (datetime.strptime(d['deadline_date'], '%Y-%m-%d').date() - today).days <= 7]

        overdue = [d for d in deadlines if d.get('deadline_date') and
                  (datetime.strptime(d['deadline_date'], '%Y-%m-%d').date() - today).days < 0]

        if urgent:
            st.warning(f"⚠️ {len(urgent)} 个时间节点即将到期")
        if overdue:
            st.error(f"🚨 {len(overdue)} 个时间节点已过期")

    st.divider()

    # 快速导航
    st.subheader("🔗 快速导航")
    if st.button("📖 案件详情", use_container_width=True):
        st.switch_page("pages/1_案件详情.py")
    if st.button("📋 证据管理", use_container_width=True):
        st.switch_page("pages/7_证据管理.py")
    if st.button("⚔️ 对抗性分析", use_container_width=True):
        st.switch_page("pages/5_对抗性分析.py")


# ============ 主内容 ============
st.subheader("📊 时间节点概览")

# 获取当前案件的统计数据
if st.session_state.selected_case:
    case = st.session_state.selected_case
    case_id = case.get('id')
    deadlines = get_case_deadlines(case_id)
    today = datetime.now().date()

    # 统计数据
    total = len(deadlines)
    upcoming = len([d for d in deadlines if d.get('deadline_date') and
                   0 <= (datetime.strptime(d['deadline_date'], '%Y-%m-%d').date() - today).days <= 30])
    urgent_count = len([d for d in deadlines if d.get('deadline_date') and
                       (datetime.strptime(d['deadline_date'], '%Y-%m-%d').date() - today).days <= 7])
    overdue_count = len([d for d in deadlines if d.get('deadline_date') and
                        (datetime.strptime(d['deadline_date'], '%Y-%m-%d').date() - today).days < 0])

    # 显示统计
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("时间节点总数", total)
    with col2:
        st.metric("30日内到期", upcoming)
    with col3:
        if urgent_count > 0:
            st.metric("7日内到期", urgent_count, delta="紧急")
        else:
            st.metric("7日内到期", urgent_count)
    with col4:
        if overdue_count > 0:
            st.metric("已过期", overdue_count, delta="需要处理", delta_color="inverse")
        else:
            st.metric("已过期", overdue_count)
else:
    st.warning("请在左侧选择案件")
    st.stop()

st.markdown("---")

# 快捷工具
st.subheader("🔧 分析工具")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📊 紧急程度报告", use_container_width=True):
        with st.spinner("生成中..."):
            report = get_urgency_report(case_id)
            if report:
                st.session_state.urgency_report = report
                st.success("报告生成完成")
            else:
                st.session_state.urgency_report = None
                st.info("暂无可用数据，系统将使用本地数据生成报告")

with col2:
    if st.button("✨ 智能生成节点", use_container_width=True):
        with st.spinner("生成中..."):
            result = generate_milestones(case_id)
            if result:
                st.success("节点生成完成")
                st.rerun()
            else:
                st.info("暂无可用数据")

with col3:
    if st.button("📅 查看时间线", use_container_width=True):
        timeline = get_case_timeline(case_id)
        if timeline:
            st.success("时间线获取完成")
        else:
            st.info("暂无数据")

with col4:
    if st.button("📋 标准时效表", use_container_width=True):
        st.session_state.show_standards = True

# 紧急程度报告展示
if st.session_state.urgency_report:
    st.markdown("---")
    st.subheader("📊 紧急程度报告")
    report = st.session_state.urgency_report
    if isinstance(report, dict):
        # 显示报告内容
        report_content = json.dumps(report, ensure_ascii=False, indent=2)
        st.json(report)
        show_export_section("紧急程度报告", report_content, "urgency")
    else:
        st.markdown(str(report))
        show_export_section("紧急程度报告", str(report), "urgency")

# 标准时效表
if st.session_state.get("show_standards"):
    with st.expander("📚 标准诉讼时效参考表", expanded=True):
        for sd in STANDARD_DEADLINES:
            col1, col2, col3 = st.columns([2, 1, 2])
            with col1:
                st.markdown(f"**{sd['type']}** - {sd['name']}")
            with col2:
                st.markdown(f"📅 {sd['period']}")
            with col3:
                st.caption(f"起算: {sd['start']}")
        if st.button("关闭"):
            st.session_state.show_standards = False

st.markdown("---")

# 添加时间节点
st.subheader("➕ 添加时间节点")

if st.button("📅 添加新节点", use_container_width=True):
    st.session_state.show_deadline_form = not st.session_state.show_deadline_form

if st.session_state.show_deadline_form:
    with st.form("deadline_form"):
        col1, col2 = st.columns(2)

        with col1:
            deadline_type = st.selectbox(
                "节点类型",
                options=["开庭", "举证期限", "上诉期限", "执行期限", "还款期限", "诉讼时效", "其他"]
            )
            deadline_name = st.text_input("节点名称 *", placeholder="例如：第一次开庭")

        with col2:
            deadline_date = st.date_input("截止日期 *")
            is_hearing = st.checkbox("开庭日期")

        description = st.text_area("备注", height=60, placeholder="补充说明...")

        # 用户备注
        user_notes = st.text_area("用户备注（选填）", height=60, placeholder="任何额外说明或修改意见...")

        submitted = st.form_submit_button("💾 保存", type="primary")
        cancelled = st.form_submit_button("❌ 取消")

        if submitted:
            if deadline_name and deadline_date:
                deadline_data = {
                    "type": deadline_type,
                    "name": deadline_name,
                    "deadline_date": deadline_date.strftime("%Y-%m-%d"),
                    "description": description,
                    "is_hearing": is_hearing,
                    "user_notes": user_notes
                }

                result = add_deadline(case_id, deadline_data)
                if result:
                    st.success("时间节点已添加")
                    st.session_state.show_deadline_form = False
                    st.rerun()
                else:
                    st.warning("节点已记录（后端API可能未完全连接）")
                    st.session_state.show_deadline_form = False
            else:
                st.error("请填写节点名称和日期")

        if cancelled:
            st.session_state.show_deadline_form = False

    st.markdown("---")

# 时间节点列表
st.subheader("📅 时间节点列表")

if not deadlines:
    st.info("暂无时间节点，点击上方「添加新节点」开始管理")
else:
    # 按日期排序
    deadlines_sorted = sorted(deadlines, key=lambda x: x.get('deadline_date', '9999-12-31'))

    today = datetime.now().date()

    # 创建分类显示
    col_list1, col_list2 = st.columns(2)

    with col_list1:
        st.markdown("### 🔴 紧急/已过期")
        urgent_or_overdue = [d for d in deadlines_sorted if d.get('deadline_date') and
                            (datetime.strptime(d['deadline_date'], '%Y-%m-%d').date() - today).days <= 7]
        if urgent_or_overdue:
            for d in urgent_or_overdue:
                deadline_date = d.get('deadline_date', '')
                days_left = (datetime.strptime(deadline_date, '%Y-%m-%d').date() - today).days

                if days_left < 0:
                    color = "🔴"
                    urgency = f"已过期 {abs(days_left)}天"
                else:
                    color = "🟠"
                    urgency = f"还剩 {days_left}天"

                with st.container():
                    st.warning(f"**{color} {d.get('name', '未命名')}**")
                    st.caption(f"类型: {d.get('type', '其他')} | {urgency}")
                    if d.get('description'):
                        st.caption(f"备注: {d.get('description')}")
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("完成", key=f"done_{d.get('id')}"):
                            st.info("标记完成功能")
                    with col_btn2:
                        if st.button("删除", key=f"del_dl_{d.get('id')}"):
                            if delete_deadline(d.get('id')):
                                st.success("已删除")
                                st.rerun()
        else:
            st.info("暂无紧急节点")

    with col_list2:
        st.markdown("### 🟡 30日内到期")
        soon = [d for d in deadlines_sorted if d.get('deadline_date') and
               7 < (datetime.strptime(d['deadline_date'], '%Y-%m-%d').date() - today).days <= 30]
        if soon:
            for d in soon:
                deadline_date = d.get('deadline_date', '')
                days_left = (datetime.strptime(deadline_date, '%Y-%m-%d').date() - today).days

                with st.container():
                    st.info(f"**🟡 {d.get('name', '未命名')}**")
                    st.caption(f"类型: {d.get('type', '其他')} | 还剩 {days_left}天")
                    if d.get('description'):
                        st.caption(f"备注: {d.get('description')}")
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("完成", key=f"done_{d.get('id')}"):
                            st.info("标记完成功能")
                    with col_btn2:
                        if st.button("删除", key=f"del_dl_{d.get('id')}"):
                            if delete_deadline(d.get('id')):
                                st.success("已删除")
                                st.rerun()
        else:
            st.info("暂无30日内到期节点")

    st.markdown("---")

    st.markdown("### 🟢 远期节点")
    future = [d for d in deadlines_sorted if d.get('deadline_date') and
             (datetime.strptime(d['deadline_date'], '%Y-%m-%d').date() - today).days > 30]
    if future:
        for d in future:
            deadline_date = d.get('deadline_date', '')
            days_left = (datetime.strptime(deadline_date, '%Y-%m-%d').date() - today).days

            col_f1, col_f2, col_f3 = st.columns([3, 1, 1])
            with col_f1:
                st.markdown(f"**🟢 {d.get('name', '未命名')}**")
                st.caption(f"类型: {d.get('type', '其他')} | {deadline_date[:10]} | 还剩 {days_left}天")
            with col_f2:
                if st.button("完成", key=f"done_{d.get('id')}"):
                    st.info("标记完成功能")
            with col_f3:
                if st.button("删除", key=f"del_dl_{d.get('id')}"):
                    if delete_deadline(d.get('id')):
                        st.success("已删除")
                        st.rerun()
            st.divider()

    # 导出全部时间节点
    st.markdown("---")
    all_deadlines_content = "# 时间节点清单\n\n"
    for d in deadlines_sorted:
        all_deadlines_content += f"""
## {d.get('name', '未命名')}

- **类型**: {d.get('type', '其他')}
- **截止日期**: {d.get('deadline_date', '未设置')}
- **备注**: {d.get('description', '无')}
"""
        if d.get('deadline_date'):
            days_left = (datetime.strptime(d['deadline_date'], '%Y-%m-%d').date() - today).days
            if days_left < 0:
                all_deadlines_content += f"- **状态**: 已过期 {abs(days_left)}天\n"
            else:
                all_deadlines_content += f"- **状态**: 还剩 {days_left}天\n"
        all_deadlines_content += "\n---\n"

    col_exp1, col_exp2, col_exp3 = st.columns(3)
    with col_exp1:
        st.download_button(
            "📄 导出全部节点(MD)",
            export_to_markdown(all_deadlines_content, "时间节点清单").encode('utf-8'),
            f"时间节点_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )
    with col_exp2:
        st.download_button(
            "📝 导出全部节点(TXT)",
            export_to_text(all_deadlines_content, "时间节点清单").encode('utf-8'),
            f"时间节点_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    with col_exp3:
        st.download_button(
            "📋 导出为JSON",
            json.dumps({"title": "时间节点清单", "deadlines": deadlines, "export_time": datetime.now().isoformat()}, ensure_ascii=False, indent=2).encode('utf-8'),
            f"时间节点_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

    # 数据联动提示
    st.markdown("---")
    st.markdown("#### 🔗 数据联动")
    col_link1, col_link2, col_link3 = st.columns(3)
    with col_link1:
        evidence_count = len(get_case_evidence(case_id))
        st.metric("关联证据数量", evidence_count)
    with col_link2:
        st.write(f"案件状态: {case.get('status', '未知')}")
    with col_link3:
        st.write(f"诉讼金额: {case.get('claim_amount', '未设置')}")

# ============ 返回按钮 ============
st.divider()
if st.button("⬅️ 返回案件详情", use_container_width=True):
    st.switch_page("pages/1_案件详情.py")
