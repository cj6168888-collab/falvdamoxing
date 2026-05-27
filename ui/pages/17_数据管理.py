"""
数据导入导出 - 随身律师
支持 JSON 格式的全量备份和恢复
"""
import streamlit as st
import requests
from datetime import datetime
from pathlib import Path
import json

st.set_page_config(page_title="数据管理 - 随身律师", page_icon="💾", layout="wide")

DATA_DIR = Path("d:/www/法律大模型/data")
DATA_DIR.mkdir(exist_ok=True)


def get_statistics():
    """获取统计数据"""
    try:
        from app.db.storage import get_statistics as db_get_stats
        return db_get_stats()
    except:
        return {}


def get_loans():
    """获取借款"""
    try:
        from app.db.storage import get_loans as db_get_loans
        return db_get_loans()
    except:
        return []


def get_projects():
    """获取项目"""
    try:
        from app.db.storage import get_projects as db_get_projects
        return db_get_projects()
    except:
        return []


def get_contracts():
    """获取合同"""
    try:
        from app.db.storage import get_contracts as db_get_contracts
        return db_get_contracts()
    except:
        return []


def get_meetings():
    """获取会议"""
    try:
        from app.db.storage import get_meetings as db_get_meetings
        return db_get_meetings()
    except:
        return []


def get_cases():
    """获取案件"""
    try:
        from app.db.storage import get_cases as db_get_cases
        return db_get_cases()
    except:
        return []


def export_all_data():
    """导出所有数据"""
    try:
        from app.db.storage import export_all_data as db_export
        return db_export()
    except:
        return None


def import_data(data):
    """导入数据"""
    try:
        from app.db.storage import import_data as db_import
        return db_import(data)
    except:
        return False


# ============ 页面 ============
st.title("💾 数据管理中心")
st.markdown("### 数据备份 · 导入恢复 · 安全存储")

# ============ 数据统计 ============
st.markdown("## 📊 数据统计")

stats = get_statistics()
loans = get_loans()
projects = get_projects()
contracts = get_contracts()
meetings = get_meetings()
cases = get_cases()

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("💰 借款记录", len(loans))

with col2:
    st.metric("📁 项目", len(projects))

with col3:
    st.metric("📄 合同", len(contracts))

with col4:
    st.metric("🎙️ 会议", len(meetings))

with col5:
    st.metric("⚖️ 案件", len(cases))

with col6:
    st.metric("💸 借出总额", f"¥{stats.get('lend_total', 0):,.0f}")

st.divider()

# ============ 数据导出 ============
st.markdown("## 📤 数据导出")

st.markdown("### 全量备份")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **导出的数据包括：**
    - 借款记录（含到期提醒）
    - 项目信息
    - 合同列表
    - 会议记录（含录音文件）
    - 案件信息
    """)

with col2:
    if st.button("📥 导出全部数据", use_container_width=True, type="primary"):
        data = export_all_data()
        if data:
            # 保存到文件
            export_file = DATA_DIR / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 提供下载
            st.success(f"✅ 数据已导出！文件：{export_file.name}")

            # 读取文件内容供下载
            with open(export_file, 'r', encoding='utf-8') as f:
                file_content = f.read()

            st.download_button(
                "⬇️ 下载备份文件",
                file_content.encode('utf-8'),
                file_name=f"law_assistant_backup_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            st.warning("暂无数据可导出")

st.divider()

# ============ 数据导入 ============
st.markdown("## 📥 数据导入")

with st.expander("从备份文件导入", expanded=False):
    st.warning("⚠️ 导入会合并现有数据，不会覆盖已有的记录")

    uploaded_file = st.file_uploader("选择备份文件（JSON格式）", type=['json'])

    if uploaded_file:
        try:
            # 读取并验证文件
            file_content = uploaded_file.getvalue().decode('utf-8')
            data_dict = json.loads(file_content)

            st.success("✅ 文件格式正确！")

            # 显示预览信息
            st.markdown("**备份文件包含：**")

            preview_col1, preview_col2, preview_col3 = st.columns(3)

            with preview_col1:
                loan_count = len(data_dict.get('loans', []))
                st.metric("借款记录", loan_count)

            with preview_col2:
                project_count = len(data_dict.get('projects', []))
                st.metric("项目", project_count)

            with preview_col3:
                contract_count = len(data_dict.get('contracts', []))
                st.metric("合同", contract_count)

            if data_dict.get('export_time'):
                st.caption(f"备份时间：{data_dict['export_time'][:19]}")

            if st.button("✅ 确认导入", use_container_width=True, type="primary"):
                if import_data(data_dict):
                    st.success("✅ 数据导入成功！")
                    st.rerun()
                else:
                    st.error("导入失败，请检查文件格式")

        except json.JSONDecodeError:
            st.error("❌ 文件格式错误，请选择有效的JSON文件")
        except Exception as e:
            st.error(f"❌ 导入失败：{str(e)}")

st.divider()

# ============ 分类导出 ============
st.markdown("## 📋 分类导出/导入")

tab1, tab2, tab3, tab4 = st.tabs(["💰 借款", "📁 项目", "📄 合同", "📝 单条记录"])

with tab1:
    st.markdown("### 借款记录导出")

    if loans:
        # 生成借款CSV
        import io
        csv_buffer = io.StringIO()
        csv_buffer.write("序号,借款人,电话,金额,借款日期,到期日期,状态,是否有利息,利息率,担保方式,用途,备注\n")

        for i, loan in enumerate(loans, 1):
            csv_buffer.write(f"{i},{loan.get('borrower_name','')},{loan.get('borrower_phone','')},"
                           f"{loan.get('amount',0)},{loan.get('start_date','')},"
                           f"{loan.get('due_date','')},{loan.get('status','')},"
                           f"{'是' if loan.get('has_interest') else '否'},"
                           f"{loan.get('interest_rate',0)}%,{loan.get('guarantee','')},"
                           f"{loan.get('purpose','')},{loan.get('notes','')}\n")

        st.download_button(
            "📥 导出借款CSV",
            csv_buffer.getvalue().encode('utf-8'),
            file_name=f"借款记录_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("暂无借款记录")

with tab2:
    st.markdown("### 项目导出")

    if projects:
        import io
        csv_buffer = io.StringIO()
        csv_buffer.write("序号,项目名称,分类,金额,开始日期,状态,对方名称,电话,描述\n")

        for i, proj in enumerate(projects, 1):
            csv_buffer.write(f"{i},{proj.get('name','')},{proj.get('category_name','')},"
                           f"{proj.get('amount',0)},{proj.get('start_date','')},"
                           f"{proj.get('status','')},{proj.get('counterparty_name','')},"
                           f"{proj.get('counterparty_phone','')},{proj.get('description','')}\n")

        st.download_button(
            "📥 导出项目CSV",
            csv_buffer.getvalue().encode('utf-8'),
            file_name=f"项目列表_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("暂无项目")

with tab3:
    st.markdown("### 合同导出")

    if contracts:
        import io
        csv_buffer = io.StringIO()
        csv_buffer.write("序号,合同名称,类型,对方,金额,签订日期,到期日期,状态\n")

        for i, con in enumerate(contracts, 1):
            csv_buffer.write(f"{i},{con.get('title','')},{con.get('contract_type','')},"
                           f"{con.get('counterparty','')},{con.get('amount',0)},"
                           f"{con.get('sign_date','')},{con.get('expiry_date','')},"
                           f"{con.get('status','')}\n")

        st.download_button(
            "📥 导出合同CSV",
            csv_buffer.getvalue().encode('utf-8'),
            file_name=f"合同列表_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("暂无合同")

with tab4:
    st.markdown("### 单条记录编辑")

    st.info("如需编辑单条记录，请在对应的功能页面（如借款记录、项目管理）中操作")

st.divider()

# ============ 数据存储位置 ============
st.markdown("## 📂 数据存储位置")

st.markdown(f"""
**本地存储路径：**

```
D:\\www\\法律大模型\\
├── data\\                       # 数据库
│   └── law_assistant.db         # SQLite 数据库
├── loans\\                      # 借款相关文件
├── projects\\                   # 项目文件
├── contracts\\                  # 合同文件
├── meetings\\                   # 会议录音
├── evidence\\                   # 证据文件
└── recordings\\                 # 其他录音
```

**建议：**
1. 定期导出备份数据
2. 将备份文件保存到云盘或移动硬盘
3. 重装系统前记得备份 data 文件夹
""")

st.divider()

# ============ 安全提示 ============
st.markdown("## 🔒 安全提示")

st.success("""
**数据安全建议：**

1. **定期备份** - 建议每周导出一次数据

2. **本地存储** - 所有数据存储在您的本地电脑，不会上传到云端

3. **防止丢失** - 定期将备份文件复制到云盘或移动硬盘

4. **文件保护** - 备份文件包含敏感信息，请妥善保管

5. **迁移数据** - 重装系统前，记得备份整个 data 文件夹
""")

st.divider()
st.caption("💾 数据管理 v1.0 | 随身律师 - 让数据更安全")
