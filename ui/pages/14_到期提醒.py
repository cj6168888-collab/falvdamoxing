"""
到期提醒 - 随身律师
借款、合同等到期提醒
"""
import streamlit as st
import requests
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="到期提醒 - 随身律师", page_icon="⏰", layout="wide")

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8002")


def check_api():
    """检查API连接"""
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except:
        return False


def get_loans():
    """获取借款记录"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/loans/", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_contracts():
    """获取合同"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/contracts/", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_cases():
    """获取案件"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/cases", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def get_upcoming_reminders(days=30):
    """获取即将到期的提醒"""
    reminders = []
    today = datetime.now().date()

    # 借款提醒
    loans = get_loans()
    for loan in loans:
        if loan.get('due_date') and loan.get('status') != 'settled':
            due_date = datetime.strptime(loan['due_date'], '%Y-%m-%d').date()
            days_left = (due_date - today).days

            if days_left <= days:
                reminders.append({
                    "type": "loan",
                    "title": f"借款: {loan.get('borrower_name', '未知')}",
                    "amount": loan.get('amount', 0),
                    "due_date": due_date,
                    "days_left": days_left,
                    "direction": loan.get('direction', 'lend'),
                    "id": loan.get('id'),
                    "status": "overdue" if days_left < 0 else "urgent" if days_left <= 7 else "warning" if days_left <= 30 else "upcoming"
                })

    # 合同到期提醒
    contracts = get_contracts()
    for contract in contracts:
        if contract.get('expiry_date'):
            expiry_date = datetime.strptime(contract['expiry_date'], '%Y-%m-%d').date()
            days_left = (expiry_date - today).days

            if days_left <= days:
                reminders.append({
                    "type": "contract",
                    "title": f"合同: {contract.get('title', '未知')}",
                    "amount": contract.get('amount', 0),
                    "due_date": expiry_date,
                    "days_left": days_left,
                    "id": contract.get('id'),
                    "status": "overdue" if days_left < 0 else "urgent" if days_left <= 7 else "warning" if days_left <= 30 else "upcoming"
                })

    # 按状态和天数排序
    status_order = {"overdue": 0, "urgent": 1, "warning": 2, "upcoming": 3}
    reminders.sort(key=lambda x: (status_order.get(x['status'], 4), x['days_left']))

    return reminders


# ============ API检查 ============
if not check_api():
    st.error("❌ 后端 API 未连接，请先启动服务")
    st.stop()

# ============ 页面标题 ============
st.title("⏰ 到期提醒")
st.markdown("*借款、合同等重要时间节点提醒*")
st.markdown("---")

# ============ 获取提醒 ============
today = datetime.now().date()
reminders = get_upcoming_reminders(days=90)

# 分类统计
overdue = [r for r in reminders if r['status'] == 'overdue']
urgent = [r for r in reminders if r['status'] == 'urgent']
warning = [r for r in reminders if r['status'] == 'warning']
upcoming = [r for r in reminders if r['status'] == 'upcoming']

# ============ 统计概览 ============
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.error(f"🚨 已逾期: {len(overdue)}")
with col2:
    st.warning(f"🔴 7日内: {len(urgent)}")
with col3:
    st.info(f"🟠 30日内: {len(warning)}")
with col4:
    st.success(f"🟡 90日内: {len(upcoming)}")

st.markdown("---")

# ============ 筛选 ============
col1, col2 = st.columns([1, 3])

with col1:
    filter_type = st.selectbox(
        "类型筛选",
        options=["全部", "loan", "contract"],
        format_func=lambda x: {"全部": "全部", "loan": "借款", "contract": "合同"}.get(x, x)
    )

with col2:
    filter_days = st.slider(
        "显示天数范围",
        min_value=7,
        max_value=90,
        value=30,
        step=7
    )

# 应用筛选
filtered_reminders = reminders
if filter_type != "全部":
    filtered_reminders = [r for r in filtered_reminders if r['type'] == filter_type]

st.markdown("---")

# ============ 提醒列表 ============
st.subheader(f"📋 待办提醒 ({len(filtered_reminders)})")

if not filtered_reminders:
    st.success("✅ 暂无即将到期的提醒，一切正常！")
else:
    for reminder in filtered_reminders:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                # 状态图标
                status_icons = {
                    "overdue": "🚨",
                    "urgent": "🔴",
                    "warning": "🟠",
                    "upcoming": "🟡"
                }
                status_icon = status_icons.get(reminder['status'], "❓")

                type_icon = "💰" if reminder['type'] == 'loan' else "📄"

                st.markdown(f"**{status_icon} {type_icon} {reminder['title']}**")

                amount = reminder.get('amount', 0)
                if amount > 0:
                    st.caption(f"金额: ¥{amount:,.2f}")

                due_date = reminder['due_date']
                if isinstance(due_date, str):
                    due_date = datetime.strptime(due_date, '%Y-%m-%d').date()

                st.caption(f"到期日: {due_date.strftime('%Y-%m-%d')}")

            with col2:
                days_left = reminder['days_left']
                if days_left < 0:
                    st.markdown(f"**🚨 逾期{-days_left}天**")
                elif days_left == 0:
                    st.markdown("**🔴 今天**")
                else:
                    st.markdown(f"**⏰ {days_left}天后**")

            with col3:
                if st.button("查看", key=f"view_{reminder['type']}_{reminder['id']}"):
                    if reminder['type'] == 'loan':
                        st.switch_page("pages/11_借款记录.py")
                    else:
                        st.switch_page("pages/12_合同管理.py")

            with col4:
                if st.button("标记", key=f"done_{reminder['type']}_{reminder['id']}"):
                    st.info("标记功能开发中")

            st.markdown("---")

# ============ 日历视图 ============
st.subheader("📅 到期日历")

# 简化日历显示 - 显示未来30天的到期情况
if reminders:
    days_to_show = 30
    calendar_data = []

    for day_offset in range(days_to_show):
        check_date = today + timedelta(days=day_offset)
        day_reminders = [r for r in reminders if r['due_date'] == check_date]

        if day_reminders:
            day_str = check_date.strftime("%m-%d")
            weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][check_date.weekday()]

            calendar_data.append({
                "date": day_str,
                "weekday": weekday,
                "count": len(day_reminders),
                "reminders": day_reminders
            })

    if calendar_data:
        for item in calendar_data:
            with st.expander(f"📅 {item['date']} {item['weekday']} ({item['count']}项)"):
                for r in item['reminders']:
                    st.markdown(f"- {r['title']}")
    else:
        st.info("未来30天内暂无到期事项")

# ============ 返回按钮 ============
st.divider()
if st.button("⬅️ 返回工作台", use_container_width=True):
    st.switch_page("ui/app.py")
