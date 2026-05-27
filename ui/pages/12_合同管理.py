"""
合同管理 - 关联项目
"""
import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
import uuid

st.set_page_config(page_title="合同管理 - 随身律师", page_icon="📄", layout="wide")

CONTRACTS_DIR = Path("d:/www/法律大模型/contracts")
CONTRACTS_DIR.mkdir(exist_ok=True)


def get_contracts(project_id=None):
    try:
        from app.db.storage import get_contracts as db_get_contracts
        return db_get_contracts(project_id=project_id)
    except:
        return []


def save_contract(data):
    try:
        from app.db.storage import save_contract as db_save_contract
        return db_save_contract(data)
    except:
        return None


def delete_contract(contract_id):
    try:
        from app.db.storage import delete_contract as db_delete_contract
        return db_delete_contract(contract_id)
    except:
        return False


def get_projects():
    try:
        from app.db.storage import get_projects as db_get_projects
        return db_get_projects()
    except:
        return []


# ============ 初始化 ============
if "show_form" not in st.session_state:
    st.session_state.show_form = False


# ============ 页面 ============
st.title("📄 合同管理")
st.markdown("### 合同存档、审核、追踪 — 关联项目统一管理")

# 侧边栏
with st.sidebar:
    st.header("📌 合同管理")

    contracts = get_contracts()
    st.metric("合同总数", len(contracts))

    pending = len([c for c in contracts if c.get('status') == 'pending'])
    active = len([c for c in contracts if c.get('status') == 'active'])
    if pending > 0:
        st.warning(f"🟡 待签署: {pending} 份")
    if active > 0:
        st.info(f"🟢 执行中: {active} 份")

    st.divider()

    # 按项目筛选
    projects = get_projects()
    selected_proj = st.selectbox("筛选项目",
                                options=[None] + [p['id'] for p in projects],
                                format_func=lambda x: "全部" if x is None else next((p['name'] for p in projects if p['id'] == x), ""))

    filter_contracts = get_contracts(project_id=selected_proj) if selected_proj else contracts

    st.divider()

    # 到期提醒
    today = datetime.now().date()
    upcoming = [c for c in filter_contracts if c.get('expiry_date') and
                0 <= (datetime.strptime(c['expiry_date'], '%Y-%m-%d').date() - today).days <= 30]
    if upcoming:
        st.warning(f"🟡 {len(upcoming)} 份即将到期")

    st.divider()

    if st.button("➕ 添加合同", use_container_width=True, type="primary"):
        st.session_state.show_form = True


# 主内容
st.markdown("## 📋 合同列表")

# 空状态引导
if not filter_contracts:
    with st.container():
        col_img, col_text = st.columns([1, 3])
        with col_text:
            st.markdown("""
            ### 📄 还没有合同记录
            
            快速开始管理您的合同：
            
            1. 点击右上角「➕ 添加合同」存档合同
            2. 设置到期日期，系统自动提醒
            3. 关联项目，统一管理
            
            ---
            
            **常见使用场景：**
            - 🏠 租房合同存档
            - 💼 商业合作签约
            - 👷 劳动合同管理
            - 📝 其他协议管理
            """)
            
            if st.button("➕ 添加第一份合同", type="primary", use_container_width=True):
                st.session_state.show_form = True
                st.rerun()
    st.divider()
else:
    for contract in filter_contracts:
        with st.container(border=True):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

            with col1:
                status_icons = {"pending": "📝", "active": "⚡", "expired": "📅", "terminated": "❌"}
                st.markdown(f"{status_icons.get(contract.get('status', 'pending'), '📄')} **{contract.get('title', '未命名')}**")
                st.caption(f"对方: {contract.get('counterparty', '-')}")

                # 关联项目
                if contract.get('project_id'):
                    proj = next((p for p in projects if p['id'] == contract['project_id']), None)
                    if proj:
                        st.caption(f"📁 {proj['name'][:20]}...")

            with col2:
                if contract.get('amount', 0) > 0:
                    st.metric("金额", f"¥{contract['amount']:,.0f}")

            with col3:
                status = contract.get('status', 'pending')
                status_labels = {"pending": "待签署", "active": "执行中", "expired": "已到期", "terminated": "已终止"}
                st.caption(status_labels.get(status, status))

            with col4:
                if contract.get('expiry_date'):
                    exp = datetime.strptime(contract['expiry_date'], '%Y-%m-%d').date()
                    days = (exp - today).days
                    if days < 0:
                        st.error(f"已到期{-days}天")
                    elif days <= 30:
                        st.warning(f"{days}天后")
                    else:
                        st.caption(f"{days}天后")

            with col5:
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✏️", key=f"edit_c_{contract['id']}"):
                        st.session_state.selected_contract = contract['id']
                        st.session_state.show_form = True
                        st.rerun()
                with col_b:
                    if st.button("🗑️", key=f"del_c_{contract['id']}"):
                        delete_contract(contract['id'])
                        st.success("已删除")
                        st.rerun()


# ============ 添加合同 ============
if st.session_state.show_form:
    st.markdown("## 📝 添加合同")

    with st.form("contract_form", clear_on_submit=False):
        st.markdown("#### 👤 我方信息（甲方）")
        my_col1, my_col2 = st.columns(2)
        with my_col1:
            my_name = st.text_input("甲方名称 *", placeholder="您自己或您公司的名称")
            my_phone = st.text_input("联系电话", placeholder="手机或座机")
        with my_col2:
            my_id_type = st.selectbox("身份类型", ["个人", "公司"], index=0)
            my_id = st.text_input("身份证/营业执照", placeholder="甲方证件号")

        st.divider()
        st.markdown("#### 📋 合同基本信息")
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("合同名称 *")
            contract_type = st.selectbox("合同类型", ["租赁合同", "买卖合同", "服务合同", "劳动合同", "合作协议", "借款合同", "其他"])

            # 关联项目
            selected_proj = st.selectbox("关联项目",
                                      options=[None] + [p['id'] for p in projects],
                                      format_func=lambda x: "不关联项目" if x is None else next((p['name'] for p in projects if p['id'] == x), ""))

        with col2:
            counterparty = st.text_input("对方当事人（乙方）*")
            amount = st.number_input("涉及金额", min_value=0.0, step=1000.0)
            status = st.selectbox("状态", ["pending", "active", "expired", "terminated"],
                                 format_func=lambda x: {"pending": "🟡 待签署", "active": "🟢 执行中", "expired": "🟠 已到期", "terminated": "🔴 已终止"}[x])

        st.markdown("#### 👤 对方信息（乙方）")
        opp_col1, opp_col2 = st.columns(2)
        with opp_col1:
            counterparty_phone = st.text_input("联系电话", placeholder="乙方联系电话")
        with opp_col2:
            counterparty_id_type = st.selectbox("乙方身份类型", ["个人", "公司"], index=0)
            counterparty_id = st.text_input("身份证/营业执照", placeholder="乙方证件号")

        col3, col4 = st.columns(2)
        with col3:
            sign_date = st.date_input("签订日期", datetime.now())
            expiry_date = st.date_input("到期日期", datetime.now() + timedelta(days=365))

        with col4:
            contract_no = st.text_input("合同编号（选填）")
            remark = st.text_area("备注")

        notes = st.text_area("合同概述", placeholder="简要描述合同内容...")

        submitted = st.form_submit_button("💾 保存", use_container_width=True, type="primary")

        if submitted:
            if not title:
                st.error("请填写合同名称")
            elif not my_name:
                st.error("请填写甲方（我方）名称")
            elif not counterparty:
                st.error("请填写乙方（对方）名称")
            else:
                contract_id = save_contract({
                    "project_id": selected_proj,
                    "title": title,
                    "contract_type": contract_type,
                    "counterparty": counterparty,
                    "counterparty_phone": counterparty_phone,
                    "counterparty_id_type": counterparty_id_type,
                    "counterparty_id": counterparty_id,
                    "my_name": my_name,
                    "my_phone": my_phone,
                    "my_id_type": my_id_type,
                    "my_id": my_id,
                    "amount": amount,
                    "contract_no": contract_no,
                    "sign_date": sign_date.strftime('%Y-%m-%d'),
                    "expiry_date": expiry_date.strftime('%Y-%m-%d'),
                    "status": status,
                    "notes": notes,
                    "remark": remark
                })
                st.success("✅ 合同已保存！")
                st.session_state.show_form = False
                st.rerun()

        if st.form_submit_button("取消", use_container_width=True):
            st.session_state.show_form = False
            st.rerun()

    st.divider()


# ============ 合同模板 ============
st.markdown("## 📝 常用合同模板")

template_col1, template_col2, template_col3, template_col4 = st.columns(4)

with template_col1:
    st.markdown("### 💼 商业合作")
    st.caption("• 合作协议")
    st.caption("• 股权转让")
    st.caption("• 投资协议")
    if st.button("使用模板", key="tpl_business"):
        st.info("模板功能开发中")

with template_col2:
    st.markdown("### 🏠 房屋租赁")
    st.caption("• 租房合同")
    st.caption("• 买卖合同")
    st.caption("• 定金协议")
    if st.button("使用模板", key="tpl_rental"):
        st.info("模板功能开发中")

with template_col3:
    st.markdown("### 👷 劳动雇佣")
    st.caption("• 劳动合同")
    st.caption("• 劳务协议")
    st.caption("• 保密协议")
    if st.button("使用模板", key="tpl_labor"):
        st.info("模板功能开发中")

with template_col4:
    st.markdown("### 💰 借款相关")
    st.caption("• 借条模板")
    st.caption("• 欠条模板")
    st.caption("• 担保合同")
    if st.button("使用模板", key="tpl_loan"):
        st.info("模板功能开发中")

st.divider()
st.caption("📄 合同管理 v2.0 | 关联项目，全局追踪")
