"""
借款记录 - 随身律师
管理借入借出记录，到期提醒
"""
import streamlit as st
import requests
import os
from datetime import datetime

st.set_page_config(page_title="借款记录 - 随身律师", page_icon="💰", layout="wide")

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8002")


def check_api():
    """检查API连接"""
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except:
        return False


def get_loans(direction=None):
    """获取借款记录"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/loans/", timeout=5)
        loans = r.json() if r.status_code == 200 else []
        if direction:
            loans = [l for l in loans if l.get('direction') == direction]
        return loans
    except:
        return []


def get_loan(loan_id):
    """获取单条记录"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/loans/{loan_id}", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def create_loan(data):
    """创建借款记录"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/loans/", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def update_loan(loan_id, data):
    """更新借款记录"""
    try:
        r = requests.put(f"{API_BASE_URL}/api/loans/{loan_id}", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def delete_loan(loan_id):
    """删除记录"""
    try:
        r = requests.delete(f"{API_BASE_URL}/api/loans/{loan_id}", timeout=5)
        return r.status_code == 200
    except:
        return False


def get_projects():
    """获取项目列表"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/projects/", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


# ============ API检查 ============
if not check_api():
    st.error("❌ 后端 API 未连接，请先启动服务")
    st.stop()

# ============ 页面标题 ============
st.title("💰 借款记录")
st.markdown("*管理借入借出，记录每一笔资金往来*")
st.markdown("---")

# ============ 初始化 ============
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
if "selected_loan" not in st.session_state:
    st.session_state.selected_loan = None

# ============ 统计数据 ============
loans = get_loans()
today = datetime.now().date()

# 分类统计
lend_loans = [l for l in loans if l.get('direction') == 'lend']
borrow_loans = [l for l in loans if l.get('direction') == 'borrow']

lend_amount = sum(l.get('amount', 0) for l in lend_loans)
borrow_amount = sum(l.get('amount', 0) for l in borrow_loans)

# 到期统计
overdue_loans = []
upcoming_loans = []

for loan in loans:
    if loan.get('due_date') and loan.get('status') != 'settled':
        due_date = datetime.strptime(loan['due_date'], '%Y-%m-%d').date()
        days_left = (due_date - today).days

        if days_left < 0:
            overdue_loans.append(loan)
        elif days_left <= 30:
            upcoming_loans.append(loan)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("借出金额", f"¥{lend_amount:,.2f}")
with col2:
    st.metric("借入金额", f"¥{borrow_amount:,.2f}")
with col3:
    st.metric("到期提醒", len(upcoming_loans))
with col4:
    st.metric("已逾期", len(overdue_loans))

st.markdown("---")

# ============ 侧边栏 ============
with st.sidebar:
    st.header("💰 借款记录")

    # 统计
    st.metric("总记录", len(loans))
    st.metric("借出", len(lend_loans))
    st.metric("借入", len(borrow_loans))

    st.divider()

    # 筛选
    st.subheader("🔍 筛选")
    direction_filter = st.selectbox(
        "方向",
        options=["全部", "lend", "borrow"],
        format_func=lambda x: {"全部": "全部", "lend": "借出", "borrow": "借入"}.get(x, x)
    )

    status_filter = st.selectbox(
        "状态",
        options=["全部", "active", "settled", "overdue"],
        format_func=lambda x: {"全部": "全部", "active": "进行中", "settled": "已结清", "overdue": "已逾期"}.get(x, x)
    )

    # 筛选后的记录
    filtered_loans = loans
    if direction_filter != "全部":
        filtered_loans = [l for l in filtered_loans if l.get('direction') == direction_filter]
    if status_filter != "全部":
        filtered_loans = [l for l in filtered_loans if l.get('status') == status_filter]

    st.divider()

    # 新建按钮
    if st.button("➕ 添加记录", use_container_width=True):
        st.session_state.show_form = True
        st.session_state.edit_mode = False
        st.session_state.selected_loan = None

# ============ 新建/编辑表单 ============
if st.session_state.show_form:
    projects = get_projects()

    with st.form("loan_form", clear_on_submit=False):
        st.subheader("💰 " + ("编辑借款记录" if st.session_state.edit_mode else "添加借款记录"))

        col1, col2 = st.columns(2)

        with col1:
            direction = st.selectbox(
                "借款方向",
                options=["lend", "borrow"],
                format_func=lambda x: {"lend": "💸 借出", "borrow": "💵 借入"}.get(x, x),
                index=0 if not st.session_state.selected_loan else ["lend", "borrow"].index(st.session_state.selected_loan.get('direction', 'lend'))
            )

            borrower_name = st.text_input(
                "对方姓名/名称",
                value=st.session_state.selected_loan.get('borrower_name', '') if st.session_state.selected_loan else ""
            )

            amount = st.number_input(
                "金额",
                min_value=0.0,
                value=float(st.session_state.selected_loan.get('amount', 0)) if st.session_state.selected_loan else 0.0,
                step=100.0
            )

        with col2:
            start_date = st.date_input(
                "借款日期",
                value=datetime.strptime(st.session_state.selected_loan['start_date'], '%Y-%m-%d').date()
                if st.session_state.selected_loan and st.session_state.selected_loan.get('start_date')
                else today
            )

            due_date = st.date_input(
                "到期日期",
                value=datetime.strptime(st.session_state.selected_loan['due_date'], '%Y-%m-%d').date()
                if st.session_state.selected_loan and st.session_state.selected_loan.get('due_date')
                else today + timedelta(days=30)
            )

            has_interest = st.checkbox(
                "有利息",
                value=bool(st.session_state.selected_loan.get('has_interest')) if st.session_state.selected_loan else False
            )

        if has_interest:
            col_i1, col_i2 = st.columns(2)
            with col_i1:
                interest_rate = st.number_input(
                    "利率(%)",
                    min_value=0.0,
                    value=float(st.session_state.selected_loan.get('interest_rate', 0)) if st.session_state.selected_loan else 0.0,
                    step=0.1
                )
            with col_i2:
                interest_type = st.selectbox(
                    "计息方式",
                    options=["single", "compound"],
                    format_func=lambda x: {"single": "单利", "compound": "复利"}.get(x, x)
                )
        else:
            interest_rate = 0
            interest_type = None

        project_id = st.selectbox(
            "关联项目（可选）",
            options=[None] + [p['id'] for p in projects],
            format_func=lambda x: "无" if x is None else next((p['name'] for p in projects if p['id'] == x), "")
        )

        notes = st.text_area("备注", value=st.session_state.selected_loan.get('notes', '') if st.session_state.selected_loan else "", height=60)

        col_b1, col_b2, col_b3 = st.columns([1, 1, 1])

        with col_b1:
            submitted = st.form_submit_button("💾 保存", type="primary", use_container_width=True)

        with col_b2:
            cancelled = st.form_submit_button("❌ 取消", use_container_width=True)

        with col_b3:
            if st.session_state.edit_mode and st.session_state.selected_loan:
                deleted = st.form_submit_button("🗑️ 删除", use_container_width=True)
            else:
                deleted = False

        if submitted:
            data = {
                "direction": direction,
                "borrower_name": borrower_name,
                "amount": amount,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "due_date": due_date.strftime("%Y-%m-%d"),
                "has_interest": has_interest,
                "interest_rate": interest_rate if has_interest else 0,
                "interest_type": interest_type if has_interest else None,
                "project_id": project_id,
                "notes": notes
            }

            if st.session_state.edit_mode and st.session_state.selected_loan:
                result = update_loan(st.session_state.selected_loan['id'], data)
                if result:
                    st.success("记录已更新")
                    st.session_state.show_form = False
                    st.rerun()
                else:
                    st.error("更新失败")
            else:
                result = create_loan(data)
                if result:
                    st.success("记录已添加")
                    st.session_state.show_form = False
                    st.rerun()
                else:
                    st.error("添加失败")

        if cancelled:
            st.session_state.show_form = False
            st.rerun()

        if deleted:
            if delete_loan(st.session_state.selected_loan['id']):
                st.success("记录已删除")
                st.session_state.show_form = False
                st.session_state.selected_loan = None
                st.rerun()
            else:
                st.error("删除失败")

    st.markdown("---")

# ============ 借款列表 ============
st.subheader(f"📋 借款记录 ({len(filtered_loans)})")

if not filtered_loans:
    st.info("暂无借款记录，点击左侧「添加记录」创建")
else:
    for loan in filtered_loans:
        with st.container():
            direction = loan.get('direction', 'lend')
            direction_icon = "💸" if direction == 'lend' else "💵"
            direction_text = "借出" if direction == 'lend' else "借入"

            amount = loan.get('amount', 0)
            status = loan.get('status', 'active')

            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.markdown(f"**{direction_icon} {loan.get('borrower_name', '未知')}**")
                st.caption(f"金额: ¥{amount:,.2f} | {direction_text}")

                if loan.get('due_date'):
                    due = loan['due_date'][:10] if len(loan['due_date']) > 10 else loan['due_date']
                    days_left = (datetime.strptime(loan['due_date'], '%Y-%m-%d').date() - today).days

                    if days_left < 0:
                        st.caption(f"🚨 已逾期 {-days_left} 天 | 到期: {due}")
                    elif days_left == 0:
                        st.caption(f"🔴 今天到期")
                    elif days_left <= 7:
                        st.caption(f"🟠 {days_left}天后到期 | {due}")
                    else:
                        st.caption(f"到期: {due}")

            with col2:
                status_text = {"active": "🟢 进行中", "settled": "✅ 已结清", "overdue": "🚨 已逾期"}.get(status, status)
                st.markdown(f"**{status_text}**")

            with col3:
                if st.button("✏️", key=f"edit_loan_{loan['id']}"):
                    st.session_state.show_form = True
                    st.session_state.edit_mode = True
                    st.session_state.selected_loan = loan
                    st.rerun()

            with col4:
                if st.button("🗑️", key=f"del_loan_{loan['id']}"):
                    if delete_loan(loan['id']):
                        st.success("已删除")
                        st.rerun()
                    else:
                        st.error("删除失败")

            st.markdown("---")

# 辅助函数
from datetime import timedelta
