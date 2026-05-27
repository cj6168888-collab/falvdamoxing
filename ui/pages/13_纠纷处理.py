"""
纠纷处理 - 关联项目
证据收集、诉求分析、诉讼准备
"""
import streamlit as st
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="纠纷处理 - 随身律师", page_icon="⚠️", layout="wide")

# 获取项目根目录
APP_DIR = Path(__file__).parent.parent.absolute()

# ============ 法律身份定义 ============
LEGAL_ROLES = {
    "plaintiff": {"label": "原告", "icon": "⚔️", "color": "red", "desc": "发起诉讼的一方，主张自己的权利"},
    "defendant": {"label": "被告", "icon": "🛡️", "color": "blue", "desc": "被起诉的一方，需要进行答辩"},
    "guarantor": {"label": "担保人", "icon": "🤝", "color": "orange", "desc": "为债务提供担保的一方"},
    "witness": {"label": "证人", "icon": "👁️", "color": "gray", "desc": "了解案件事实的第三人"},
    "related_party": {"label": "关联方", "icon": "🔗", "color": "purple", "desc": "与案件有利害关系的第三方"},
    "appellant": {"label": "上诉人", "icon": "📤", "color": "green", "desc": "对一审判决提起上诉的一方"},
    "appellee": {"label": "被上诉人", "icon": "📥", "color": "teal", "desc": "被提起上诉的一方"},
}

# 根据法律身份返回不同的法律协助提示
LEGAL_ASSISTANCE_BY_ROLE = {
    "plaintiff": {
        "title": "⚔️ 原告法律协助",
        "items": [
            "起草起诉状，明确诉讼请求",
            "收集和整理支持诉求的证据",
            "分析被告可能的抗辩理由并准备应对",
            "申请财产保全，防止被告转移资产",
            "估算诉讼成本和预期收益"
        ]
    },
    "defendant": {
        "title": "🛡️ 被告法律协助",
        "items": [
            "审查起诉状的合法性和事实依据",
            "准备答辩状，针对原告主张逐项反驳",
            "分析是否存在反诉机会",
            "收集证明不存在侵权/违约的证据",
            "考虑和解方案和谈判策略"
        ]
    },
    "guarantor": {
        "title": "🤝 担保人法律协助",
        "items": [
            "审查担保合同的有效性和范围",
            "了解主债务的履行情况",
            "分析行使追偿权的条件和时机",
            "准备代位求偿的证据材料",
            "评估承担担保责任后的风险"
        ]
    },
    "witness": {
        "title": "👁️ 证人法律协助",
        "items": [
            "整理所知悉的案件事实",
            "准备书面证词或出庭作证",
            "了解作证的权利和义务",
            "注意保护个人隐私信息",
            "配合司法机关调查取证"
        ]
    },
    "related_party": {
        "title": "🔗 关联方法律协助",
        "items": [
            "明确自身的法律地位和利益关系",
            "分析案件结果对自身的潜在影响",
            "考虑是否需要申请参加诉讼",
            "准备支持自身立场的事实和证据",
            "必要时提出独立的诉讼请求"
        ]
    },
    "appellant": {
        "title": "📤 上诉人法律协助",
        "items": [
            "分析一审判决的错误之处",
            "准备上诉状和新证据",
            "明确上诉请求和理由",
            "评估二审改判的可能性",
            "准备开庭陈述和辩论要点"
        ]
    },
    "appellee": {
        "title": "📥 被上诉人法律协助",
        "items": [
            "审查上诉状的合法性和事实依据",
            "准备答辩状，针对上诉理由逐项反驳",
            "收集支持一审判决的证据和理由",
            "必要时提出反上诉或补充陈述",
            "评估维持原判或部分改判的概率"
        ]
    }
}


def switch_to_page(page_filename):
    """切换到指定页面 - 兼容 Windows 和 Linux"""
    page_path = f"pages/{page_filename}"
    st.switch_page(page_path)


def get_projects():
    try:
        from app.db.storage import get_projects as db_get_projects
        return db_get_projects()
    except:
        return []


def save_project(data):
    try:
        from app.db.storage import save_project as db_save_project
        return db_save_project(data)
    except:
        return None


def update_project(project_id, data):
    try:
        from app.db.storage import update_project as db_update_project
        return db_update_project(project_id, data)
    except:
        return None


def get_cases(project_id=None):
    try:
        from app.db.storage import get_cases as db_get_cases
        return db_get_cases(project_id=project_id)
    except:
        return []


def save_case(data):
    try:
        from app.db.storage import save_case as db_save_case
        return db_save_case(data)
    except:
        return None


def get_loans(project_id=None):
    try:
        from app.db.storage import get_loans as db_get_loans
        return db_get_loans(project_id=project_id)
    except:
        return []


def get_contracts(project_id=None):
    try:
        from app.db.storage import get_contracts as db_get_contracts
        return db_get_contracts(project_id=project_id)
    except:
        return []


# ============ 案件处理方向定义 ============
CASE_DIRECTIONS = {
    "negotiate": {
        "label": "🤝 友好协商",
        "desc": "优先沟通，寻求和平解决方案",
        "color": "green",
        "icon": "🤝"
    },
    "mediate": {
        "label": "⚖️ 调解优先",
        "desc": "通过第三方调解化解纠纷",
        "color": "blue",
        "icon": "⚖️"
    },
    "litigate": {
        "label": "⚔️ 诉讼解决",
        "desc": "通过法院诉讼维护权益",
        "color": "red",
        "icon": "⚔️"
    },
    "contain": {
        "label": "🛡️ 战略防守",
        "desc": "控制损失，等待时机",
        "color": "orange",
        "icon": "🛡️"
    },
    "retreat": {
        "label": "🔙 适时退让",
        "desc": "评估风险后选择让步",
        "color": "gray",
        "icon": "🔙"
    }
}

# ============ 初始化 ============
if "dispute_step" not in st.session_state:
    st.session_state.dispute_step = 1

# 初始化案件处理方向
if "case_direction" not in st.session_state:
    st.session_state.case_direction = "mediate"


# ============ 页面 ============
st.title("⚠️ 纠纷处理中心")
st.markdown("### 系统化处理纠纷 — 关联项目，全程追踪")

# ============ 侧边栏 ============
with st.sidebar:
    st.header("📌 纠纷向导")

    steps = [
        "① 选择/创建项目",
        "② 关联相关记录",
        "③ 收集证据",
        "④ 分析诉求",
        "⑤ 生成材料"
    ]

    for i, step in enumerate(steps, 1):
        if st.session_state.dispute_step == i:
            st.success(f"**{step}** ←")
        elif st.session_state.dispute_step > i:
            st.caption(f"✅ {step}")
        else:
            st.caption(f"○ {step}")

    st.divider()

    # 案件处理方向选择
    st.subheader("🎯 处理方向")
    current_dir = st.session_state.get('case_direction', 'mediate')
    current_dir_info = CASE_DIRECTIONS.get(current_dir, CASE_DIRECTIONS['mediate'])

    st.markdown(f"**{current_dir_info['icon']} {current_dir_info['label']}**")
    st.caption(f"_{current_dir_info['desc']}_")

    # 快速切换方向
    with st.expander("🔄 切换方向"):
        for dir_key, dir_info in CASE_DIRECTIONS.items():
            if st.button(f"{dir_info['icon']} {dir_info['label']}", key=f"dir_{dir_key}", use_container_width=True):
                st.session_state.case_direction = dir_key
                st.rerun()

    st.divider()

    # 已有案件
    st.subheader("📋 进行中案件")
    cases = get_cases()
    if cases:
        for case in cases[:3]:
            st.caption(f"⚠️ {case.get('title', '未命名')[:15]}...")
    else:
        st.caption("暂无案件")

    st.divider()

    if st.button("🔄 重新开始", use_container_width=True):
        st.session_state.dispute_step = 1
        st.session_state.selected_project_id = None
        st.rerun()


# ============ 主内容 ============

# Step 1: 选择/创建项目
if st.session_state.dispute_step == 1:
    st.markdown("## Step 1: 选择或创建项目")

    projects = get_projects()

    if projects:
        st.markdown("### 📁 选择已有项目")

        cols = st.columns(3)
        for i, proj in enumerate(projects):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"**📁 {proj.get('name', '未命名')}**")
                    st.caption(f"类型: {proj.get('category_name', proj.get('category', '未知'))}")
                    st.caption(f"状态: {proj.get('status', 'active')}")
                    if st.button("选择", key=f"sel_proj_{proj['id']}"):
                        st.session_state.selected_project_id = proj['id']
                        st.session_state.dispute_step = 2
                        st.rerun()

        st.markdown("---")

    st.markdown("### ➕ 或创建新项目")

    with st.form("new_project_form", clear_on_submit=True):
        st.markdown("#### 👤 我方信息（设置您的法律身份）")

        # 法律身份选择
        legal_role_options = list(LEGAL_ROLES.keys())
        legal_role_labels = [f"{LEGAL_ROLES[r]['icon']} {LEGAL_ROLES[r]['label']}" for r in legal_role_options]

        col_role, col_type = st.columns([2, 1])
        with col_role:
            selected_legal_role = st.selectbox(
                "**您的法律身份 ***",
                options=legal_role_options,
                format_func=lambda x: f"{LEGAL_ROLES[x]['icon']} {LEGAL_ROLES[x]['label']}",
                index=0,
                help="您在此案件中扮演的角色"
            )
            # 显示身份说明
            st.caption(f"💡 {LEGAL_ROLES[selected_legal_role]['desc']}")

        plaintiff_col1, plaintiff_col2 = st.columns(2)
        with plaintiff_col1:
            plaintiff_name = st.text_input("姓名/名称 *", placeholder="您自己的姓名或公司名称")
            plaintiff_phone = st.text_input("联系电话", placeholder="手机或座机")
        with plaintiff_col2:
            plaintiff_id_type = st.selectbox("身份类型", ["个人", "公司"], index=0)
            plaintiff_id = st.text_input("身份证/营业执照", placeholder="便于后续维权")

        st.divider()
        st.markdown("#### 📋 项目信息")

        col1, col2 = st.columns(2)
        with col1:
            proj_name = st.text_input("项目名称 *", placeholder="如：张三借款追讨、李四合同纠纷")
        with col2:
            proj_category = st.selectbox("项目类型", ["debt", "contract", "labor", "property", "other"],
                                       format_func=lambda x: {"debt": "💰 债务纠纷", "contract": "📄 合同纠纷", "labor": "👷 劳动纠纷", "property": "🏠 房产纠纷", "other": "🚗 其他"}[x])

        st.markdown("#### 👤 被告信息（对方）")
        opp_col1, opp_col2 = st.columns(2)
        with opp_col1:
            opposite = st.text_input("被告姓名/名称 *", placeholder="对方当事人的姓名或公司名称")
            opposite_phone = st.text_input("联系电话", placeholder="手机或座机")
        with opp_col2:
            opposite_id_type = st.selectbox("身份类型", ["个人", "公司"], index=0)
            opposite_id = st.text_input("身份证/营业执照", placeholder="便于后续维权")

        description = st.text_area("案情简述（选填）", placeholder="简要描述背景...")

        submitted = st.form_submit_button("创建项目并继续", use_container_width=True, type="primary")

        if submitted:
            if not proj_name:
                st.error("请填写项目名称")
            elif not plaintiff_name:
                st.error("请填写原告（您）的姓名/名称")
            elif not opposite:
                st.error("请填写被告（对方）的姓名/名称")
            else:
                category_names = {"debt": "💰 债务", "contract": "📄 合同", "labor": "👷 劳动", "property": "🏠 房产", "other": "🚗 其他"}
                project_id = save_project({
                    "name": proj_name,
                    "category": proj_category,
                    "category_name": category_names[proj_category],
                    "description": description,
                    "status": "disputed"
                })

                if project_id:
                    # 保存我方信息（包含法律身份）
                    try:
                        from app.db.storage import upsert_party
                        upsert_party(project_id, 'user', {
                            'party_type': plaintiff_id_type,
                            'legal_role': selected_legal_role,
                            'name': plaintiff_name,
                            'phone': plaintiff_phone,
                            'id_card': plaintiff_id
                        })
                        upsert_party(project_id, 'counterparty', {
                            'party_type': opposite_id_type,
                            'name': opposite,
                            'phone': opposite_phone,
                            'id_card': opposite_id
                        })
                    except Exception as e:
                        st.warning(f"当事人信息保存失败: {e}")

                    # 根据法律身份提供不同提示
                    role_info = LEGAL_ROLES.get(selected_legal_role, {})
                    st.success(f"✅ 项目已创建！您的身份：{role_info.get('icon', '')} {role_info.get('label', '')}")

                    # 显示基于身份的法律协助建议
                    assistance = LEGAL_ASSISTANCE_BY_ROLE.get(selected_legal_role, {})
                    if assistance:
                        with st.expander(f"{assistance.get('title', '法律协助')}", expanded=True):
                            for item in assistance.get('items', []):
                                st.markdown(f"- {item}")

                    st.session_state.selected_project_id = project_id
                    st.session_state.selected_legal_role = selected_legal_role
                    st.session_state.dispute_step = 2
                    st.rerun()
                else:
                    st.error("项目创建失败，请重试")

# Step 2: 关联相关记录
elif st.session_state.dispute_step == 2:
    project_id = st.session_state.get("selected_project_id")
    project = next((p for p in get_projects() if p['id'] == project_id), None)

    st.markdown(f"## Step 2: 关联相关记录")

    if project:
        st.markdown(f"当前项目：**{project.get('name', '未命名')}**")

        # 获取当前法律身份
        current_legal_role = st.session_state.get('selected_legal_role')
        if not current_legal_role:
            try:
                from app.db.storage import get_party_by_role
                party = get_party_by_role(project_id, 'user')
                if party:
                    current_legal_role = party.get('legal_role', 'plaintiff')
            except:
                current_legal_role = 'plaintiff'

        # 显示当前身份和转换按钮
        if current_legal_role:
            role_info = LEGAL_ROLES.get(current_legal_role, {})
            st.info(f"📌 当前法律身份：{role_info.get('icon', '')} **{role_info.get('label', current_legal_role)}**")

            # 身份转换功能
            with st.expander("🔄 转换法律身份"):
                st.markdown("**选择新的身份：**")
                new_role = st.selectbox(
                    "切换为",
                    options=list(LEGAL_ROLES.keys()),
                    format_func=lambda x: f"{LEGAL_ROLES[x]['icon']} {LEGAL_ROLES[x]['label']}",
                    key="new_legal_role_select"
                )

                reason = st.text_input("转换原因（选填）", placeholder="如：案件角色变化、发现新证据...")

                if st.button("确认转换", type="primary"):
                    try:
                        from app.db.storage import update_party_legal_role
                        update_party_legal_role(project_id, 'user', new_role, reason)
                        st.session_state.selected_legal_role = new_role
                        st.success(f"✅ 身份已转换为：{LEGAL_ROLES[new_role]['icon']} {LEGAL_ROLES[new_role]['label']}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"转换失败: {e}")

            # 显示基于身份的法律协助
            assistance = LEGAL_ASSISTANCE_BY_ROLE.get(current_legal_role, {})
            if assistance:
                with st.expander(f"📋 {assistance.get('title', '法律协助')}", expanded=False):
                    for item in assistance.get('items', []):
                        st.markdown(f"- {item}")

    # 关联借款
    st.markdown("### 💰 关联借款记录")
    loans = get_loans()
    if loans:
        for loan in loans:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{loan.get('borrower_name', '未知')}**")
                    st.caption(f"金额: ¥{loan.get('amount', 0):,.2f}")
                with col2:
                    if loan.get('project_id') == project_id:
                        st.success("已关联")
                    else:
                        if st.button("关联", key=f"link_loan_{loan['id']}"):
                            from app.db.storage import update_loan
                            update_loan(loan['id'], {"project_id": project_id})
                            st.rerun()
                with col3:
                    if st.button("跳过", key=f"skip_loan_{loan['id']}"):
                        pass

    # 关联合同
    st.markdown("### 📄 关联合同")
    contracts = get_contracts()
    if contracts:
        for contract in contracts:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{contract.get('title', '未知合同')}**")
                    st.caption(f"金额: ¥{contract.get('amount', 0):,.2f}")
                with col2:
                    if contract.get('project_id') == project_id:
                        st.success("已关联")
                    else:
                        if st.button("关联", key=f"link_con_{contract['id']}"):
                            from app.db.storage import update_contract
                            update_contract(contract['id'], {"project_id": project_id})
                            st.rerun()
                with col3:
                    if st.button("跳过", key=f"skip_con_{contract['id']}"):
                        pass

    st.markdown("""
    ---

    💡 **没有找到相关记录？** 可以跳过此步骤，直接进入证据收集。
    """)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 上一步", use_container_width=True):
            st.session_state.dispute_step = 1
            st.rerun()
    with col2:
        if st.button("下一步 ➡️", use_container_width=True, type="primary"):
            st.session_state.dispute_step = 3
            st.rerun()

# Step 3: 收集证据
elif st.session_state.dispute_step == 3:
    st.markdown("## Step 3: 收集证据")

    evidence_templates = {
        "debt": ["借条/欠条", "转账凭证", "聊天记录", "电话录音", "催款记录"],
        "contract": ["合同原件", "补充协议", "履行记录", "往来函件"],
        "labor": ["劳动合同", "工资流水", "社保记录", "考勤记录"],
        "default": ["关键证据1", "关键证据2", "辅助证据"]
    }

    ev_type = "default"
    if st.session_state.get("selected_project_id"):
        project = next((p for p in get_projects() if p['id'] == st.session_state.get("selected_project_id")), None)
        if project:
            ev_type = project.get('category', 'default')

    evidence_list = evidence_templates.get(ev_type, evidence_templates["default"])

    st.markdown(f"### 📋 {ev_type.upper()} 纠纷常用证据")

    for i, ev in enumerate(evidence_list):
        col1, col2, col3 = st.columns([1, 4, 1])
        with col1:
            checked = st.checkbox("", key=f"ev_{i}")
        with col2:
            st.markdown(f"**{ev}**")
        with col3:
            uploaded = st.file_uploader("上传", key=f"up_ev_{i}", label_visibility="collapsed")

    st.markdown("---")

    st.markdown("### 💡 证据建议")

    advice = {
        "debt": "1. **借条是关键**：规范的借条是最有力的证据\n2. **转账优于现金**：银行转账有记录\n3. **聊天记录要完整**：保留完整对话",
        "contract": "1. **合同原件最重要**：务必保留签署的原件\n2. **履行记录要保存**：发货单、签收单等",
        "labor": "1. **劳动合同是基础**：未签合同可主张双倍工资\n2. **工资流水最可靠**：银行流水是最有力的证据"
    }

    st.info(advice.get(ev_type, "请根据案件情况收集相关证据。"))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 上一步", use_container_width=True):
            st.session_state.dispute_step = 2
            st.rerun()
    with col2:
        if st.button("下一步 ➡️", use_container_width=True, type="primary"):
            st.session_state.dispute_step = 4
            st.rerun()

# Step 4: 分析诉求
elif st.session_state.dispute_step == 4:
    st.markdown("## Step 4: 分析诉求")

    # 获取当前法律身份
    project_id = st.session_state.get("selected_project_id")
    current_legal_role = st.session_state.get('selected_legal_role', 'plaintiff')
    if not current_legal_role and project_id:
        try:
            from app.db.storage import get_party_by_role
            party = get_party_by_role(project_id, 'user')
            if party:
                current_legal_role = party.get('legal_role', 'plaintiff')
        except:
            current_legal_role = 'plaintiff'

    # 显示当前身份
    role_info = LEGAL_ROLES.get(current_legal_role, {})
    st.info(f"📌 当前法律身份：{role_info.get('icon', '')} {role_info.get('label', current_legal_role)}")

    # ============ 案件处理方向选择 ============
    st.markdown("### 🎯 选择案件处理方向")
    st.caption("不同的处理方向会影响系统给出的建议、文书风格和策略重点")

    # 当前选择显示
    current_direction = st.session_state.get('case_direction', 'mediate')
    current_dir_info = CASE_DIRECTIONS.get(current_direction, CASE_DIRECTIONS['mediate'])

    col_dir_title, col_dir_desc = st.columns([3, 5])
    with col_dir_title:
        st.markdown(f"#### {current_dir_info['icon']} {current_dir_info['label']}")
    with col_dir_desc:
        st.caption(current_dir_info['desc'])

    # 方向选项卡片
    st.markdown("**请选择处理方向：**")

    # 创建方向选项卡片
    dir_cols = st.columns(len(CASE_DIRECTIONS))
    direction_select = current_direction

    for idx, (dir_key, dir_info) in enumerate(CASE_DIRECTIONS.items()):
        with dir_cols[idx]:
            # 高亮当前选中
            if dir_key == current_direction:
                border_color = "blue"
            else:
                border_color = "gray"

            with st.container(border=True):
                # 方向图标和名称
                selected = st.radio(
                    f"{dir_info['icon']} {dir_info['label']}",
                    options=[dir_key],
                    index=0,
                    key=f"dir_radio_{dir_key}",
                    label_visibility="collapsed"
                )

                # 描述
                st.caption(dir_info['desc'], help=dir_info['desc'])

                # 选中时显示
                if st.session_state.get(f"dir_selected_{dir_key}", False):
                    st.success(f"✅ 已选择: {dir_info['label']}")

    # 使用单选按钮组选择方向
    st.markdown("---")
    st.markdown("**或从下方选择：**")

    direction_options = [f"{d['icon']} {d['label']}" for d in CASE_DIRECTIONS.values()]
    direction_keys = list(CASE_DIRECTIONS.keys())

    selected_radio = st.radio(
        "案件处理方向",
        options=direction_keys,
        format_func=lambda x: f"{CASE_DIRECTIONS[x]['icon']} {CASE_DIRECTIONS[x]['label']} - {CASE_DIRECTIONS[x]['desc']}",
        index=direction_keys.index(current_direction),
        horizontal=True
    )

    if selected_radio != current_direction:
        st.session_state.case_direction = selected_radio
        st.rerun()

    # 方向详细说明
    st.markdown("---")
    selected_dir_info = CASE_DIRECTIONS.get(st.session_state.case_direction, CASE_DIRECTIONS['mediate'])

    with st.expander(f"📖 {selected_dir_info['label']} 详细说明", expanded=True):
        direction_details = {
            "negotiate": """
**适用场景：** 双方关系尚可，希望保持良好合作，不想撕破脸

**文书风格：** 温和、礼貌、尊重对方
- 使用"恳请"、"烦请"、"希望"等礼貌用语
- 强调互谅互让、合作共赢

**风险提示：**
- 对方可能借协商拖延时间
- 协商过程注意保留证据
- 协商不成果断转入其他方式
            """,
            "mediate": """
**适用场景：** 双方分歧较大，需要第三方调解

**文书风格：** 中性、务实、专业
- 理性表达诉求
- 愿意合理让步
- 强调效率和时间成本

**风险提示：**
- 调解协议需司法确认才有强制执行力
- 调解不成可能延误时机
- 调解中注意保护自身权益
            """,
            "litigate": """
**适用场景：** 其他方式无效，必须通过诉讼维护权益

**文书风格：** 坚定、有力、据理力争
- 全面陈述有利事实
- 穷尽法律依据
- 态度坚决，寸步不让

**风险提示：**
- 诉讼周期较长、成本较高
- 存在败诉风险
- 判决执行可能困难
            """,
            "contain": """
**适用场景：** 证据不足或形势不利，先稳固防守

**文书风格：** 专业、审慎、稳重
- 不主动激化矛盾
- 强调程序合规
- 保留权利但不进攻

**风险提示：**
- 过于保守可能丧失主动权
- 密切关注对方动向
- 时效风险需特别关注
            """,
            "retreat": """
**适用场景：** 评估后认为退让损失更小

**文书风格：** 克制、理性、务实
- 避免强硬措辞
- 表达让步诚意
- 强调协议可执行性

**风险提示：**
- 让步后不能反悔
- 评估对方履约能力
- 协议条款要明确具体
            """
        }
        st.markdown(direction_details.get(st.session_state.case_direction, ""))

    st.markdown("### 🎯 明确您的诉求")

    # 根据法律身份显示不同的诉求选项
    claim_options_by_role = {
        "plaintiff": ["要求还款", "要求支付利息", "要求赔偿损失", "要求继续履行", "要求解除合同"],
        "defendant": ["请求驳回原告全部诉讼请求", "请求驳回原告部分诉讼请求", "提出反诉", "要求原告赔偿损失", "要求调解和解"],
        "guarantor": ["要求主债务人履行债务", "行使追偿权", "要求减免担保责任", "主张担保无效"],
        "witness": ["申请作证费用", "保护个人隐私", "申请出庭保护"],
        "related_party": ["申请参加诉讼", "提出独立请求", "主张自身权益"],
        "appellant": ["请求撤销原判", "请求改判", "请求发回重审"],
        "appellee": ["请求维持原判", "答辩驳回上诉", "必要时提出反上诉"]
    }

    claim_options = claim_options_by_role.get(current_legal_role, claim_options_by_role["plaintiff"])

    selected_claims = []
    for claim in claim_options:
        if st.checkbox(f"☑️ {claim}", key=f"claim_{claim}"):
            selected_claims.append(claim)

    # 根据身份显示不同的金额相关提示
    if current_legal_role in ["defendant"]:
        st.markdown("### 💰 诉讼金额（如果被反诉）")
    else:
        st.markdown("### 💰 金额诉求")

    col1, col2 = st.columns(2)
    with col1:
        claim_amount = st.number_input("诉求金额（元）", min_value=0.0, step=1000.0)
    with col2:
        st.text_input("其他诉求", placeholder="如：律师费、诉讼费")

    st.divider()

    st.markdown("### 👤 对方信息")

    opp_col1, opp_col2 = st.columns(2)
    with opp_col1:
        opp_name = st.text_input("对方姓名/名称")
        opp_phone = st.text_input("联系电话")
    with opp_col2:
        opp_address = st.text_input("地址")
        opp_id = st.text_input("身份证/营业执照（选填）")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 上一步", use_container_width=True):
            st.session_state.dispute_step = 3
            st.rerun()
    with col2:
        if st.button("下一步 ➡️", use_container_width=True, type="primary"):
            st.session_state.dispute_step = 5
            st.rerun()

# Step 5: 生成材料
elif st.session_state.dispute_step == 5:
    st.markdown("## Step 5: 生成诉讼材料")

    # 获取当前法律身份
    project_id = st.session_state.get("selected_project_id")
    current_legal_role = st.session_state.get('selected_legal_role', 'plaintiff')
    if not current_legal_role and project_id:
        try:
            from app.db.storage import get_party_by_role
            party = get_party_by_role(project_id, 'user')
            if party:
                current_legal_role = party.get('legal_role', 'plaintiff')
        except:
            current_legal_role = 'plaintiff'

    # 显示当前身份和处理方向
    role_info = LEGAL_ROLES.get(current_legal_role, {})
    direction_info = CASE_DIRECTIONS.get(st.session_state.get('case_direction', 'mediate'), CASE_DIRECTIONS['mediate'])

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"📌 当前法律身份：{role_info.get('icon', '')} {role_info.get('label', current_legal_role)}")
    with col2:
        st.info(f"🎯 当前处理方向：{direction_info.get('icon', '')} {direction_info.get('label', current_legal_role)}")

    st.markdown("### 📄 选择需要生成的材料")

    # 根据法律身份显示不同的文书选项
    docs_by_role = {
        "plaintiff": [
            {"key": "complaint", "icon": "📝", "name": "起诉状", "desc": "向法院提交", "func": "_generate_complaint"},
            {"key": "demand", "icon": "📧", "name": "催款函", "desc": "催促还款", "func": "_generate_demand"},
            {"key": "lawyer", "icon": "⚖️", "name": "律师函", "desc": "法律警告", "func": "_generate_lawyer"},
            {"key": "evidence", "icon": "📋", "name": "证据目录", "desc": "整理证据", "func": "_generate_evidence"}
        ],
        "defendant": [
            {"key": "defense", "icon": "🛡️", "name": "答辩状", "desc": "回应起诉", "func": "_generate_defense"},
            {"key": "counterclaim", "icon": "⚔️", "name": "反诉状", "desc": "提出反诉", "func": "_generate_counterclaim"},
            {"key": "mediation", "icon": "🤝", "name": "和解协议", "desc": "调解方案", "func": "_generate_mediation"},
            {"key": "evidence", "icon": "📋", "name": "证据目录", "desc": "整理证据", "func": "_generate_evidence"}
        ],
        "guarantor": [
            {"key": "recourse", "icon": "🔄", "name": "追偿申请书", "desc": "代位求偿", "func": "_generate_recourse"},
            {"key": "demand", "icon": "📧", "name": "催告函", "desc": "催促还款", "func": "_generate_guarantor_demand"},
            {"key": "evidence", "icon": "📋", "name": "证据目录", "desc": "整理证据", "func": "_generate_evidence"}
        ],
        "witness": [
            {"key": "statement", "icon": "📝", "name": "书面证词", "desc": "准备证言", "func": "_generate_witness_statement"},
            {"key": "application", "icon": "📄", "name": "出庭申请", "desc": "申请作证", "func": "_generate_witness_application"}
        ],
        "related_party": [
            {"key": "intervention", "icon": "📝", "name": "参加诉讼申请", "desc": "申请参加", "func": "_generate_intervention"},
            {"key": "evidence", "icon": "📋", "name": "证据目录", "desc": "整理证据", "func": "_generate_evidence"}
        ],
        "appellant": [
            {"key": "appeal", "icon": "📤", "name": "上诉状", "desc": "提起上诉", "func": "_generate_appeal"},
            {"key": "evidence", "icon": "📋", "name": "补充证据", "desc": "新证据材料", "func": "_generate_evidence"}
        ],
        "appellee": [
            {"key": "response", "icon": "📥", "name": "答辩意见", "desc": "回应上诉", "func": "_generate_appellee_response"},
            {"key": "cross_appeal", "icon": "⚔️", "name": "交叉上诉", "desc": "必要时", "func": "_generate_cross_appeal"}
        ]
    }

    docs = docs_by_role.get(current_legal_role, docs_by_role["plaintiff"])
    cols = st.columns(min(4, len(docs)))

    current_direction = st.session_state.get('case_direction', 'mediate')

    for i, doc in enumerate(docs):
        with cols[i % 4]:
            st.markdown(f"### {doc['icon']} {doc['name']}")
            st.caption(doc['desc'])
            if st.button(f"生成", key=f"gen_{doc['key']}", use_container_width=True):
                func = globals().get(doc['func'])
                if func:
                    # 传递方向参数给生成函数
                    try:
                        content = func(direction=current_direction)
                    except TypeError:
                        content = func()
                    st.session_state.generated_doc = {"type": doc['name'], "content": content, "direction": current_direction}

    if st.session_state.get("generated_doc"):
        st.divider()
        doc = st.session_state.get("generated_doc")
        st.markdown(f"### 📄 {doc['type'].upper()}")

        edited = st.text_area("内容（可编辑）", value=doc['content'], height=400, key="doc_edit")

        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.download_button("📥 下载", edited.encode('utf-8'),
                             file_name=f"{doc['type']}_{datetime.now().strftime('%Y%m%d')}.txt",
                             mime="text/plain", use_container_width=True)
        with col_d2:
            st.button("📋 继续生成", use_container_width=True)
        with col_d3:
            if st.button("✅ 完成", use_container_width=True):
                st.balloons()
                st.success("材料已准备就绪！")

    st.divider()

    # 保存为案件
    project_id = st.session_state.get("selected_project_id")
    if project_id and not get_cases(project_id):
        if st.button("⚠️ 保存为案件", use_container_width=True, type="primary"):
            claim_amount = st.number_input("诉求金额", min_value=0.0, step=1000.0, key="case_amount")
            if st.button("确认保存"):
                project = next((p for p in get_projects() if p['id'] == project_id), None)
                if project:
                    case_data = {
                        "project_id": project_id,
                        "case_type": project.get('category', 'other'),
                        "title": project.get('name', '纠纷案件'),
                        "defendant": project.get('counterparty_name', ''),
                        "claim_amount": claim_amount,
                        "status": "pending"
                    }
                    save_case(case_data)
                    update_project(project_id, {"status": "disputed"})
                    st.success("✅ 案件已保存！")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 上一步", use_container_width=True):
            st.session_state.dispute_step = 4
            st.rerun()
    with col2:
        if st.button("🏠 返回首页", use_container_width=True):
            st.switch_page("app.py")  # 返回主页面


# ============ 文档生成函数 ============

# 语气风格定义（根据处理方向）
TONE_STYLES = {
    "negotiate": {
        "name": "友好协商",
        "greeting": ["您好", "烦请", "恳请"],
        "body": ["考虑到双方长期合作关系", "本着互谅互让的原则", "希望贵方能够理解"],
        "action": ["烦请尽快确认", "恳请予以配合", "烦请回复"],
        "closing": ["感谢理解与支持", "期待您的积极回应", "祝好"]
    },
    "mediate": {
        "name": "调解优先",
        "greeting": ["您好", "为妥善解决争议", "经慎重考虑"],
        "body": ["鉴于双方存在分歧", "为避免诉累", "在合理范围内愿意让步"],
        "action": ["建议协商调解方案", "如同意调解请回复", "期待通过调解解决"],
        "closing": ["希望双方理性对待", "共同寻求解决方案", "感谢配合"]
    },
    "litigate": {
        "name": "诉讼解决",
        "greeting": ["郑重函告", "依据法律规定"],
        "body": ["经查，贵方已构成违约", "根据《民法典》第X条规定", "贵方应当承担违约责任"],
        "action": ["限X日内履行义务", "否则将依法追究法律责任", "保留进一步法律行动的权利"],
        "closing": ["据此维权", "依法维护合法权益", "追究到底"]
    },
    "contain": {
        "name": "战略防守",
        "greeting": ["致函说明", "依法告知"],
        "body": ["特此说明", "按合同约定", "保留依法追诉的权利"],
        "action": ["请核实相关情况", "如有异议请书面回复", "将依法处理"],
        "closing": ["感谢配合", "依法依规处理", "按程序进行"]
    },
    "retreat": {
        "name": "适时退让",
        "greeting": ["经慎重考虑", "协商解决"],
        "body": ["考虑到实际情况", "为尽快解决争议", "愿意作出适当让步"],
        "action": ["如同意此方案请确认", "请在X日前回复", "期待达成共识"],
        "closing": ["感谢理解", "期待友好解决", "合作愉快"]
    }
}


def _get_tone_style(direction: str) -> dict:
    """获取指定方向的语气风格"""
    return TONE_STYLES.get(direction, TONE_STYLES["mediate"])


def _generate_complaint(direction: str = "litigate"):
    return f"""
民事起诉状

原告：[您的姓名]    性别：    民族：
住所地：
电话：

被告：[对方姓名/名称]
住所地：
电话：

---

诉讼请求

1. 请求判令被告偿还借款人民币____元；
2. 请求判令被告支付利息____元；
3. 请求判令被告承担本案诉讼费用。

---

事实与理由

____年__月__日，被告因____向原告借款人民币____元，约定于____年__月__日归还。

借款到期后，被告未能按约还款，虽经原告多次催要，被告均以各种理由推脱，至今未还。

---

证据清单

1. 借条____份；
2. 转账凭证____份；
3. 聊天记录____份。

---

此致

________人民法院

起诉人（签名）：____________
{datetime.now().strftime('%Y年%m月%d日')}
"""


def _generate_demand(direction: str = "mediate"):
    """生成催款函，根据处理方向调整语气"""
    tone = _get_tone_style(direction)

    # 根据不同方向选择不同的语气模板
    templates = {
        "negotiate": f"""
催款函（友好协商版）

致：____（对方姓名/名称）

{tone['greeting'][0]}：

我方于____年__月__日因____欠付贵方款项人民币____元，约定还款日期为____年__月__日。

{tone['body'][0]}，特此与您沟通还款事宜。

截至目前，贵方共欠付我方款项本金____元，利息____元，合计____元。

{tone['action'][0]}，在收到本函后尽快与我方联系，商议还款方案。

{tone['closing'][0]}！

催款方：____________
{datetime.now().strftime('%Y年%m月%d日')}

---
📌 注：如有任何还款困难，欢迎与我方协商分期还款或其他解决方案。
""",
        "mediate": f"""
催款函（调解优先版）

致：____（对方姓名/名称）

{tone['greeting'][0]}：

关于贵方欠付我方款项人民币____元事宜，经与贵方多次沟通未果，现正式函告。

{tone['body'][0]}，为避免诉累，我方愿意与贵方协商调解解决。

欠款明细：
- 本金：____元
- 利息：____元
- 合计：____元

{tone['action'][0]}，在收到本函后____日内回复协商。

{tone['closing'][0]}。

催款方：____________
{datetime.now().strftime('%Y年%m月%d日')}
""",
        "litigate": f"""
催款函（诉讼警告版）

致：____（对方姓名/名称）

{tone['greeting'][0]}：

贵方于____年__月__日欠付我方款项人民币____元，至今未还。

{tone['body'][0]}：
- 《民法典》第577条规定：当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担违约责任。

欠款明细：
- 本金：____元
- 利息：____元
- 合计：____元

{tone['action'][0]}，偿还全部欠款。

{tone['closing'][0]}。

催款方：____________
{datetime.now().strftime('%Y年%m月%d日')}

---
⚠️ 逾期不还，我方将依法向人民法院提起诉讼，追究贵方的法律责任。
""",
        "contain": f"""
还款事项告知函

致：____（对方姓名/名称）

{tone['greeting'][0]}：

关于贵方欠付我方款项人民币____元事宜，现正式告知。

{tone['body'][0]}，请贵方核实相关情况。

欠款明细：
- 本金：____元
- 利息：____元
- 合计：____元

{tone['action'][0]}。

{tone['closing'][0]}。

催款方：____________
{datetime.now().strftime('%Y年%m月%d日')}
""",
        "retreat": f"""
还款协商函

致：____（对方姓名/名称）

{tone['greeting'][0]}：

关于贵方欠付我方款项人民币____元事宜，现与您协商解决。

{tone['body'][0]}，我方愿意作出以下让步：
- 本金____元照实计算
- 利息____元减免至____元
- 合计____元

{tone['action'][0]}，在收到本函后____日内确认方案。

{tone['closing'][0]}。

催款方：____________
{datetime.now().strftime('%Y年%m月%d日')}

---
📌 如贵方一次性还款困难，我方也可协商分期还款方案。
"""
    }

    return templates.get(direction, templates["mediate"])


def _generate_lawyer(direction: str = "litigate"):
    """生成律师函，根据处理方向调整语气"""
    tone = _get_tone_style(direction)

    templates = {
        "negotiate": f"""
律师函（友好协商版）

[XX]律师事务所

致：____先生/女士

{tone['greeting'][0]}：

本律师接受[委托人]的委托，就贵方拖欠债务事宜，与您友好沟通。

贵方于____年__月__日向委托人借款/签订合同____，涉及金额人民币____元。

{tone['body'][0]}，本律师建议双方通过友好协商解决此事。

{tone['action'][0]}，在收到本函后与委托人积极沟通，寻求双方都能接受的解决方案。

{tone['closing'][0]}。

[XX]律师事务所
承办律师：____________
{datetime.now().strftime('%Y年%m月%d日')}
""",
        "mediate": f"""
律师函（调解优先版）

[XX]律师事务所

致：____先生/女士

{tone['greeting'][0]}：

本律师接受[委托人]的委托，就贵方拖欠债务事宜，郑重致函。

贵方于____年__月__日向委托人借款/签订合同____，涉及金额人民币____元。

{tone['body'][0]}，为避免诉累，本律师建议双方通过调解解决争议。

{tone['action'][0]}，在收到本函后____日内与委托人协商调解方案。

{tone['closing'][0]}。

[XX]律师事务所
承办律师：____________
{datetime.now().strftime('%Y年%m月%d日')}
""",
        "litigate": f"""
律师函（诉讼警告版）

[XX]律师事务所

致：____先生/女士

{tone['greeting'][0]}：

本律师接受[委托人]的委托，就贵方拖欠债务事宜，郑重致函如下：

贵方于____年__月__日向委托人借款/签订合同____，涉及金额人民币____元。

{tone['body'][0]}：
1. 贵方的行为已构成违约
2. 依据《民法典》第577条，贵方应承担违约责任
3. 本律师将依法追究贵方的法律责任

{tone['action'][0]}，在收到本函之日起____日内，主动与委托人联系解决此事。

{tone['closing'][0]}。

[XX]律师事务所
承办律师：____________
{datetime.now().strftime('%Y年%m月%d日')}

---
⚠️ 逾期不解决，本律师将代理委托人向人民法院提起诉讼，届时产生的一切法律后果由贵方承担。
""",
        "contain": f"""
律师函（事务告知版）

[XX]律师事务所

致：____先生/女士

{tone['greeting'][0]}：

本律师接受[委托人]的委托，就相关法律事项，函告如下：

贵方于____年__月__日向委托人借款/签订合同____，涉及金额人民币____元。

{tone['body'][0]}。

{tone['action'][0]}。

[XX]律师事务所
承办律师：____________
{datetime.now().strftime('%Y年%m月%d日')}
""",
        "retreat": f"""
律师函（协商解决版）

[XX]律师事务所

致：____先生/女士

{tone['greeting'][0]}：

本律师接受[委托人]的委托，就贵方拖欠债务事宜，与您协商解决。

贵方于____年__月__日向委托人借款/签订合同____，涉及金额人民币____元。

{tone['body'][0]}，委托人愿意作出适当让步：
- 本金____元照实计算
- 利息____元减免至____元
- 合计____元

{tone['action'][0]}，在收到本函后____日内确认方案。

{tone['closing'][0]}。

[XX]律师事务所
承办律师：____________
{datetime.now().strftime('%Y年%m月%d日')}

---
📌 如贵方一次性还款困难，委托人也愿意协商分期还款方案。
"""
    }

    return templates.get(direction, templates["litigate"])


def _generate_evidence():
    return """
证据目录

| 序号 | 证据名称 | 证明内容 | 页码 |
|------|----------|----------|------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

提交人（签名）：____________
日期：____________
"""


def _generate_defense():
    """被告答辩状"""
    return f"""
民事答辩状

答辩人（被告）：[您的姓名/名称]
住所地：
电话：

被答辩人（原告）：[对方姓名/名称]

---

答辩请求

1. 请求驳回原告的全部诉讼请求；
2. 本案诉讼费用由原告承担。

---

事实与理由

一、关于原告诉称的借款事实，答辩人认为：

____年__月__日，答辩人与原告之间____（说明实际情况）。

二、原告的诉讼请求缺乏事实和法律依据：

1. ____________________；
2. ____________________。

三、即使存在借款关系，原告主张的金额也存在错误：

____________________。

---

证据清单

1. 证据名称____份，证明：____；
2. 证据名称____份，证明：____。

---

此致

________人民法院

答辩人（签名）：____________
{datetime.now().strftime('%Y年%m月%d日')}
"""


def _generate_counterclaim():
    """反诉状"""
    return f"""
反诉状

反诉人（本案被告）：[您的姓名/名称]
被反诉人（本案原告）：[对方姓名/名称]

---

反诉请求

1. 请求判令被反诉人赔偿反诉人损失人民币____元；
2. 请求判令被反诉人支付____；
3. 本诉与反诉诉讼费用由被反诉人承担。

---

事实与理由

____年__月__日，被反诉人因____（说明事实）。

被反诉人的行为给反诉人造成了以下损失：

1. ____________________；
2. ____________________。

---

证据清单

1. ____________________；
2. ____________________。

---

此致

________人民法院

反诉人（签名）：____________
{datetime.now().strftime('%Y年%m月%d日')}
"""


def _generate_mediation(direction: str = "mediate"):
    """和解协议，根据处理方向调整语气"""
    tone = _get_tone_style(direction)

    templates = {
        "negotiate": f"""
和解协议（友好协商版）

甲方（债权人）：[您的姓名/名称]
乙方（债务人）：[对方姓名/名称]

---

一、导言

{tone['body'][0]}，经双方友好协商，就债务偿还事宜达成如下协议：

二、债务确认

1. 乙方确认欠付甲方款项共计人民币____元；
2. 上述款项包括本金____元，利息____元。

三、还款方案（友好协商）

考虑到乙方实际困难，甲方同意乙方分期还款：
1. 乙方承诺于____年__月__日前偿还人民币____元；
2. 剩余款项于____年__月__日前全部还清。

四、利息减免

{tone['body'][1]}，甲方同意减免部分利息，实际应还总额为人民币____元。

五、违约责任

如乙方未按约定履行还款义务：
1. 甲方有权要求乙方一次性偿还全部剩余款项；
2. 双方应继续友好协商解决。

六、其他约定

1. 协议执行期间，双方保持良好沟通；
2. ____________________。

七、协议效力

本协议基于双方平等自愿原则签订，自双方签字盖章之日起生效。本协议一式两份，双方各执一份，具有同等法律效力。

---

甲方（签名）：____________    乙方（签名）：____________

日期：{datetime.now().strftime('%Y年%m月%d日')}
""",
        "mediate": f"""
和解协议（调解版）

甲方（债权人）：[您的姓名/名称]
乙方（债务人）：[对方姓名/名称]
调解方（第三方）：____________________

---

一、调解背景

{tone['body'][0]}，经调解，就债务偿还事宜达成如下协议：

二、债务确认

1. 乙方确认欠付甲方款项共计人民币____元；
2. 上述款项包括本金____元，利息____元。

三、调解方案

{tone['body'][1]}：
1. 乙方承诺于____年__月__日前偿还人民币____元；
2. 剩余款项于____年__月__日前全部还清。

四、违约责任

如乙方未按约定履行还款义务，乙方同意：
1. 立即偿还全部剩余款项；
2. 按约定支付违约金。

五、调解条款

1. 双方确认调解协议的效力；
2. 如一方违约，另一方可申请司法确认。

六、协议效力

本协议自双方签字盖章之日起生效。本协议一式三份，甲方、乙方、调解方各执一份，具有同等法律效力。

---

甲方（签名）：____________    乙方（签名）：____________    调解方（签名）：____________

日期：{datetime.now().strftime('%Y年%m月%d日')}
""",
        "litigate": f"""
和解协议（诉讼和解版）

甲方（债权人）：[您的姓名/名称]
乙方（债务人）：[对方姓名/名称]

---

一、和解背景

{tone['body'][0]}，就债务偿还事宜达成如下协议，以避免诉讼：

二、债务确认

1. 乙方确认欠付甲方款项共计人民币____元；
2. 上述款项包括本金____元，利息____元。

三、和解方案

1. 乙方承诺于____年__月__日前偿还人民币____元；
2. 剩余款项于____年__月__日前全部还清。

四、严格违约责任

如乙方未按约定履行还款义务，乙方同意：
1. 立即偿还全部剩余款项；
2. 按日万分之五支付违约金；
3. 承担甲方因追偿债务而产生的一切费用（包括但不限于律师费、诉讼费）。

五、法律保留

{tone['action'][2]}，甲方保留依法追究乙方法律责任的权利。

六、协议效力

本协议自双方签字盖章之日起生效。本协议一式两份，双方各执一份，具有同等法律效力。

---

甲方（签名）：____________    乙方（签名）：____________

日期：{datetime.now().strftime('%Y年%m月%d日')}
""",
        "contain": f"""
和解协议（稳健版）

甲方（债权人）：[您的姓名/名称]
乙方（债务人）：[对方姓名/名称]

---

一、导言

{tone['body'][0]}，就债务偿还事宜达成如下协议：

二、债务确认

1. 乙方确认欠付甲方款项共计人民币____元；
2. 上述款项包括本金____元，利息____元。

三、还款方案

1. 乙方承诺于____年__月__日前偿还人民币____元；
2. 剩余款项于____年__月__日前全部还清。

四、违约责任

如乙方未按约定履行还款义务：
1. 甲方有权要求乙方一次性偿还全部剩余款项；
2. {tone['action'][2]}。

五、其他约定

{tone['body'][1]}。

六、协议效力

本协议自双方签字盖章之日起生效。本协议一式两份，双方各执一份，具有同等法律效力。

---

甲方（签名）：____________    乙方（签名）：____________

日期：{datetime.now().strftime('%Y年%m月%d日')}
""",
        "retreat": f"""
和解协议（让步版）

甲方（债权人）：[您的姓名/名称]
乙方（债务人）：[对方姓名/名称]

---

一、导言

{tone['body'][0]}，经充分协商，就债务偿还事宜达成如下协议：

二、债务确认

1. 乙方确认欠付甲方款项共计人民币____元；
2. 上述款项包括本金____元，利息____元。

三、让步方案

{tone['body'][1]}，甲方同意作出以下让步：
1. 本金____元照实计算；
2. 原利息____元减免至____元；
3. 和解总额为人民币____元。

四、还款方案

1. 乙方承诺于____年__月__日前偿还人民币____元；
2. 剩余款项于____年__月__日前全部还清。

五、违约责任

如乙方未按约定履行还款义务：
1. 甲方有权要求乙方偿还全部原债务金额（包括已减免的利息）；
2. 乙方放弃对利息减免的一切抗辩权利。

六、其他约定

1. 乙方承诺有履约能力；
2. ____________________。

七、协议效力

本协议自双方签字盖章之日起生效。本协议一式两份，双方各执一份，具有同等法律效力。

---

甲方（签名）：____________    乙方（签名）：____________

日期：{datetime.now().strftime('%Y年%m月%d日')}

---
⚠️ 重要提示：本协议签订后，如乙方违约，甲方有权按原债务金额追偿，请乙方谨慎履约。
"""
    }

    return templates.get(direction, templates["mediate"])


def _generate_recourse():
    """担保人追偿申请书"""
    return f"""
追偿权申请书

申请人（担保人）：[您的姓名/名称]
住所地：
电话：

被申请人（主债务人）：[对方姓名/名称]

---

申请事项

请求被申请人偿还申请人已代为清偿的债务人民币____元及相应利息。

---

事实与理由

一、担保关系

申请人为被申请人与债权人之间的____（借款/债务）提供担保，担保方式为____（保证/抵押/质押），担保期限为____。

二、代偿事实

因被申请人未能按期履行还款义务，申请人于____年__月__日代被申请人偿还了人民币____元，包括本金____元和利息____元。

三、法律依据

根据《民法典》第七百条的规定，保证人承担保证责任后，有权在其承担保证责任的范围内向债务人追偿。

---

证据清单

1. 担保合同原件____份；
2. 代偿凭证____份；
3. 债权人出具的代偿证明____份。

---

此致

________人民法院

申请人（签名）：____________
{datetime.now().strftime('%Y年%m月%d日')}
"""


def _generate_guarantor_demand():
    """担保人催告函"""
    return f"""
催告函

致：____（主债务人）

[您的姓名/名称]（担保人）特此函告：

一、债务情况

您于____年__月__日向债权人借款人民币____元，借款期限至____年__月__日。本人为该借款提供担保。

二、还款风险

截至发函之日，您尚未履行还款义务。若您继续拖延，债权人将要求担保人承担担保责任。

三、郑重催告

请您在收到本函之日起____日内：
1. 履行还款义务，偿还全部欠款及利息；
2. 或者与债权人/担保人协商还款方案。

四、法律后果

若您仍未履行，根据法律规定，担保人承担担保责任后，有权向您追偿全部款项，并可能追究您的法律责任。

特此函告！

担保人：[您的姓名/名称]
{datetime.now().strftime('%Y年%m月%d日')}
"""


def _generate_witness_statement():
    """证人书面证词"""
    return f"""
证人证词

证人姓名：____________
性别：____    出生日期：____年__月__日
身份证号：____________
住所地：____________
联系电话：____________

---

证人与当事人关系

证人系____（原告/被告/第三人/其他关系），与本案当事人____（存在/不存在）利害关系。

---

所了解案件事实

本人亲眼目睹/耳闻/了解以下与本案相关的事实：

1. 时间：____年__月__日
   地点：____________
   事实经过：____________________
   在场人员：____________________

2. ____________________

3. ____________________

---

证据来源

本证词所陈述的事实系证人本人____（亲眼目睹/亲身经历/经人告知），不存在虚假陈述。

---

证词效力

证人承诺：以上证词真实有效，如有不实，愿承担相应的法律责任。

---

证人（签名）：____________

日期：{datetime.now().strftime('%Y年%m月%d日')}
"""


def _generate_witness_application():
    """证人出庭作证申请书"""
    return f"""
证人出庭作证申请书

申请人：____________
身份证号：____________
住所地：____________

---

申请事项

请求法院准许申请人作为证人出庭作证。

---

申请理由

申请人了解本案的相关事实，具体为：

____年__月__日，在____（地点），申请人目睹/经历了以下事实：

____________________

____________________

为了查明案件事实，维护司法公正，申请人请求出庭作证，如实陈述所了解的情况。

---

此致

________人民法院

申请人（签名）：____________
{datetime.now().strftime('%Y年%m月%d日')}
"""


def _generate_intervention():
    """第三人参加诉讼申请书"""
    return f"""
第三人参加诉讼申请书

申请人：____________
住所地：____________
电话：____________

---

申请事项

请求以____（有独立请求权/无独立请求权）第三人的身份参加本案诉讼。

---

申请理由

一、申请人与本案的利害关系

申请人与本案存在以下利害关系：

1. ____________________；
2. ____________________。

二、申请人的独立请求

（如为有独立请求权第三人）

申请人认为，原告/被告的诉讼请求____（损害/涉及）了申请人的合法权益。具体来说：

1. ____________________；
2. ____________________。

三、参加诉讼的必要性

为查明案件事实，维护申请人的合法权益，避免与本案产生法律上的利害冲突，申请人有必要参加本案诉讼。

---

证据清单

1. 证明申请人与本案有利害关系的证据____份；
2. 支持申请人独立请求的证据____份。

---

此致

________人民法院

申请人（签名）：____________
{datetime.now().strftime('%Y年%m月%d日')}
"""


def _generate_appeal():
    """上诉状"""
    return f"""
上诉状

上诉人（原审____）：[您的姓名/名称]
被上诉人（原审____）：[对方姓名/名称]

---

上诉请求

1. 请求撤销____人民法院（____）____号民事判决的第____项；
2. 请求改判____；
3. （如要求发回重审）请求发回____人民法院重审。

---

上诉理由

一、原判决认定事实错误

原审判决认定____，与事实不符。实际情况是：

____________________。

二、原判决适用法律错误

原审判决适用《____》第____条，认为____，但该规定应当理解为____，因此原审判决适用法律存在错误。

三、新证据（如有）

上诉人在二审中提交以下新证据：

____________________。

四、其他上诉理由

____________________。

---

证据清单

1. 新证据名称____，证明：____；
2. 其他证据名称____，证明：____。

---

此致

________中级人民法院

上诉人（签名）：____________
{datetime.now().strftime('%Y年%m月%d日')}
"""


def _generate_appellee_response():
    """被上诉人答辩意见"""
    return f"""
答辩意见

答辩人（被上诉人）：[您的姓名/名称]
上诉人（原审____）：[对方姓名/名称]

---

答辩请求

1. 请求维持____人民法院（____）____号民事判决；
2. 驳回上诉人的全部上诉请求。

---

事实与理由

一、关于原审判决认定的事实

原审判决认定的事实清楚，证据充分：

____________________。

二、关于上诉人的上诉理由

1. 上诉人称____，与事实不符。实际情况是____。

2. 上诉人援引的法律规定《____》第____条，适用于本案。

三、关于新证据

（如有新证据）

上诉人提交的新证据____，不足以推翻原审判决，因为：

____________________。

四、其他答辩意见

____________________。

---

此致

________中级人民法院

答辩人（签名）：____________
{datetime.now().strftime('%Y年%m月%d日')}
"""


def _generate_cross_appeal():
    """交叉上诉状（被上诉人同时提出上诉）"""
    return f"""
交叉上诉状

上诉人（原审被告/被上诉人）：[您的姓名/名称]
被上诉人（原审原告/上诉人）：[对方姓名/名称]

---

上诉请求

1. 请求变更____人民法院（____）____号民事判决第____项，改判____；
2. （如有）请求支持上诉人的以下上诉请求：
   - ____________________；
   - ____________________。

---

上诉理由

一、原审判决存在的错误

____________________。

二、上诉人的合法权利

____________________。

三、新证据（如有）

____________________。

---

证据清单

1. ____________________；
2. ____________________。

---

此致

________中级人民法院

上诉人（签名）：____________
{datetime.now().strftime('%Y年%m月%d日')}
"""


st.divider()
st.caption("⚠️ 纠纷处理中心 v3.0 | 支持多角色，全程追踪")
