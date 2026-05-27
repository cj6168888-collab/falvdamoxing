"""
会议/谈判援助 - 关联项目
录音存证 + 专业模板 + 纪要生成
"""
import streamlit as st
from datetime import datetime
from pathlib import Path
import uuid

st.set_page_config(page_title="会议/谈判援助 - 随身律师", page_icon="🎙️", layout="wide")

MEETINGS_DIR = Path("d:/www/法律大模型/meetings")
MEETINGS_DIR.mkdir(exist_ok=True)


def get_meetings(project_id=None, limit=None):
    try:
        from app.db.storage import get_meetings as db_get_meetings
        meetings = db_get_meetings(project_id=project_id)
        if limit:
            return meetings[:limit]
        return meetings
    except:
        return []


def save_meeting(data):
    try:
        from app.db.storage import save_meeting as db_save_meeting
        return db_save_meeting(data)
    except:
        return None


def get_projects():
    try:
        from app.db.storage import get_projects as db_get_projects
        return db_get_projects()
    except:
        return []


# ============ 初始化 ============
if "meeting_session_id" not in st.session_state:
    st.session_state.meeting_session_id = str(uuid.uuid4())
if "audio_files" not in st.session_state:
    st.session_state.audio_files = []


# ============ 页面 ============
st.title("🎙️ 会议/谈判援助")
st.markdown("### 录音存证 · 纪要生成 · 关联项目追踪")

# ============ 侧边栏 ============
with st.sidebar:
    st.header("📌 会议设置")

    mode = st.radio("模式", ["会议/谈判", "出庭抗辩"], horizontal=True, key="meeting_mode")

    st.divider()

    # 关联项目
    projects = get_projects()
    selected_proj = st.selectbox("关联项目",
                              options=[None] + [p['id'] for p in projects],
                              format_func=lambda x: "不关联项目" if x is None else next((p['name'] for p in projects if p['id'] == x), ""),
                              key="meeting_project_select")

    st.divider()

    # 最近会议
    st.subheader("📋 最近会议")
    recent = get_meetings(limit=5)
    if recent:
        for m in recent[:3]:
            st.caption(f"🎙️ {m.get('topic', '会议') or m.get('meeting_type', '会议')[:15]}...")
            st.caption(f"   {m.get('created_at', '')[:10] if m.get('created_at') else '-'}")
    else:
        st.caption("暂无会议记录")

    st.divider()

    if st.button("🔄 新建会议", use_container_width=True):
        st.session_state.meeting_session_id = str(uuid.uuid4())
        st.session_state.audio_files = []
        st.session_state.meeting_content = ""
        st.rerun()


# ============ 主内容 ============
if mode == "会议/谈判":
    # 会议基本信息 - 简化
    with st.expander("📋 会议信息", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            meeting_type = st.selectbox("类型", ["商务谈判", "合同洽谈", "调解协商", "日常会议", "电话沟通"])
            topic = st.text_input("主题", placeholder="简要描述", key="meeting_topic")
        with col2:
            meeting_date = st.date_input("日期", datetime.now(), key="meeting_date")
            participants = st.text_input("参会人员", placeholder="张三、李四", key="meeting_participants")

    st.divider()

    # 录音区域
    st.markdown("### 🎤 录音存证")

    rec_col1, rec_col2, rec_col3 = st.columns([2, 1, 1])

    with rec_col1:
        try:
            audio = st.audio_input("🎤 点击开始录音（仅存证）", key="recorder")
            if audio:
                audio_id = str(uuid.uuid4())
                audio_path = MEETINGS_DIR / f"{audio_id}.webm"
                with open(audio_path, "wb") as f:
                    f.write(audio.getvalue() if hasattr(audio, 'getvalue') else audio)
                st.session_state.audio_files.append({
                    "id": audio_id,
                    "path": str(audio_path),
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                st.success(f"✅ 录音已保存（{len(st.session_state.audio_files)}段）")
        except Exception as e:
            st.warning("浏览器不支持录音，请使用 Chrome 或 Edge")

    with rec_col2:
        st.metric("录音片段", len(st.session_state.audio_files))

    with rec_col3:
        if st.button("📋 生成纪要", use_container_width=True, type="primary"):
            st.session_state.show_generator = "minutes"

    st.divider()

    # 会议记录
    st.markdown("### 📝 会议记录")
    content = st.text_area(
        "记录内容",
        value=st.session_state.get("meeting_content", ""),
        placeholder="【建议格式】\n时间 | 发言人 | 内容要点\n10:00 | 张三 | 开场致辞\n...",
        height=150,
        key="meeting_content_input"
    )

    # 生成按钮
    gen_col1, gen_col2, gen_col3 = st.columns(3)

    with gen_col1:
        if st.button("📋 会议纪要", use_container_width=True):
            st.session_state.generated_doc = {
                "type": "minutes",
                "title": "会议纪要",
                "content": _generate_minutes(meeting_type, topic, str(meeting_date), participants, content)
            }

    with gen_col2:
        if st.button("📄 合同草案", use_container_width=True):
            st.session_state.generated_doc = {
                "type": "contract",
                "title": "合同草案",
                "content": _generate_contract(meeting_type, topic, participants, content)
            }

    with gen_col3:
        if st.button("⚖️ 会议决议", use_container_width=True):
            st.session_state.generated_doc = {
                "type": "resolution",
                "title": "会议决议",
                "content": _generate_resolution(meeting_type, topic, str(meeting_date), participants, content)
            }

    # 保存会议
    st.markdown("---")
    if st.button("💾 保存会议", use_container_width=True):
        meeting_data = {
            "project_id": selected_proj,
            "session_id": st.session_state.meeting_session_id,
            "meeting_type": meeting_type,
            "topic": topic,
            "meeting_date": meeting_date.strftime('%Y-%m-%d'),
            "participants": participants,
            "content": content,
            "audio_files": st.session_state.audio_files,
            "status": "active"
        }
        save_meeting(meeting_data)
        st.success("✅ 会议已保存！")

    # 生成的文档
    if st.session_state.get("generated_doc"):
        st.divider()
        doc = st.session_state.get("generated_doc")
        st.markdown(f"### 📄 {doc['title']}")

        edited = st.text_area("内容（可编辑）", value=doc['content'], height=300, key="doc_edit")

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button("📥 下载",
                             edited.encode('utf-8'),
                             file_name=f"{doc['type']}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                             mime="text/plain", use_container_width=True)
        with col_d2:
            if st.button("❌ 关闭"):
                del st.session_state.generated_doc

    st.divider()

    # 历史录音
    if st.session_state.audio_files:
        st.markdown("### 🎵 本次会议录音")
        for i, af in enumerate(st.session_state.audio_files):
            st.text(f"📼 录音{i+1}: {af['date']}")

else:
    # 出庭抗辩
    st.markdown("### ⚖️ 出庭抗辩援助")

    with st.expander("📋 出庭信息", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            hearing_type = st.selectbox("庭审类型", ["一审", "二审", "再审", "听证"])
            court_role = st.selectbox("我方角色", ["原告", "被告", "第三人"])
        with col2:
            hearing_stage = st.selectbox("当前阶段", ["开庭陈述", "举证质证", "法庭辩论", "最后陈述"])

    st.divider()

    # 录音
    try:
        audio = st.audio_input("🎤 录音庭审过程", key="court_rec")
        if audio:
            audio_id = str(uuid.uuid4())
            audio_path = MEETINGS_DIR / f"court_{audio_id}.webm"
            with open(audio_path, "wb") as f:
                f.write(audio.getvalue() if hasattr(audio, 'getvalue') else audio)
            st.success("✅ 庭审录音已保存")
    except:
        st.warning("浏览器不支持录音")

    st.divider()

    # 文书生成
    st.markdown("### 📝 快速生成文书")
    btn1, btn2 = st.columns(2)

    with btn1:
        with st.container(border=True):
            st.markdown("**📝 开庭陈述 / 最后陈述**")
            st.caption("生成庭审发言模板")
            if st.button("生成", key="btn_opening", use_container_width=True):
                st.session_state.generated_doc = {
                    "type": "opening",
                    "title": "开庭陈述" if hearing_stage == "开庭陈述" else "最后陈述",
                    "content": _generate_opening(court_role, hearing_type) if hearing_stage == "开庭陈述" else _generate_closing(court_role)
                }

    with btn2:
        with st.container(border=True):
            st.markdown("**❓ 交叉询问 / 异议模板**")
            st.caption("生成询问问题和异议表达")
            if st.button("生成", key="btn_questions", use_container_width=True):
                st.session_state.generated_doc = {
                    "type": "questions",
                    "title": "交叉询问与异议",
                    "content": _generate_questions() + "\n\n" + _generate_objections()
                }

    if st.session_state.get("generated_doc"):
        st.divider()
        doc = st.session_state.get("generated_doc")
        st.markdown(f"### 📄 {doc['title']}")
        edited = st.text_area("内容（可编辑）", value=doc['content'], height=300, key="court_doc")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button("📥 下载", edited.encode('utf-8'),
                             file_name=f"{doc['type']}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                             mime="text/plain", use_container_width=True)
        with col_d2:
            if st.button("❌ 关闭"):
                del st.session_state.generated_doc


# ============ 文档生成函数 ============

def _generate_minutes(meeting_type, topic, date, participants, content):
    return f"""# 会议纪要

**类型：** {meeting_type}
**主题：** {topic}
**日期：** {date}
**参会：** {participants if participants else '（待补充）'}

---

## 会议内容

{content if content else '（待记录）'}

## 会议结论

（待补充）

## 下一步行动

| 事项 | 责任人 | 期限 |
|------|--------|------|
| | | |

---

纪要人：__________    审核：__________
"""


def _generate_contract(meeting_type, topic, participants, content):
    content_preview = content[:200] if content else ''
    date_str = datetime.now().strftime('%Y-%m-%d')
    default_participants = '甲方：__________\n乙方：__________'
    return f"""# 合同草案

**合同名称：** {topic or '（待定）'}
**协商日期：** {date_str}

---

## 鉴于条款

甲乙双方于本协议签署之日就【{topic}】事宜进行了友好协商，达成如下共识。

## 双方基本信息

{participants if participants else default_participants}

## 协议内容

（根据会议内容：{content_preview}...）

## 双方权利义务

### 甲方：
1.

### 乙方：
1.

## 违约责任

（待补充）

## 争议解决

（待补充）

---

甲方（签章）：________________
乙方（签章）：________________
日期：________________
"""


def _generate_resolution(meeting_type, topic, date, participants, content):
    return f"""# 会议决议

**会议：** {topic or '会议'}
**日期：** {date}
**参会：** {participants if participants else '（待补充）'}

---

## 决议事项

{content if content else '（待记录）'}

## 表决结果

□ 同意：____人    □ 反对：____人    □ 弃权：____人

## 执行安排

| 序号 | 事项 | 责任人 | 期限 |
|------|------|--------|------|
| 1 | | | |
| 2 | | | |

---

主持人：________________
记录人：________________
"""


def _generate_opening(role, hearing_type):
    return f"""# 开庭陈述（{role}）

审判长/审判员：

{'我是原告' if role == '原告' else '我是被告'}委托代理人______，参加今天的{hearing_type}诉讼活动。现发表如下代理意见：

---

## 一、案件基本情况

（补充案件事实）

## 二、{role}的诉讼请求

（补充具体请求）

## 三、事实与理由

（补充事实依据和法律依据）

---

请法庭依法支持{'原告' if role == '原告' else '被告'}的诉讼请求。

{'原告' if role == '原告' else '被告'}代理人：______
{datetime.now().strftime('%Y')}年{datetime.now().strftime('%m')}月{datetime.now().strftime('%d')}日
"""


def _generate_closing(role):
    return f"""# 最后陈述（{role}）

审判长/审判员：

在庭审即将结束之际，作为{'原告' if role == '原告' else '被告'}代理人，补充陈述如下：

---

## 核心观点

1.
2.

## 恳请事项

恳请法庭在查明案件事实的基础上，依法作出公正判决。

---

{'原告' if role == '原告' else '被告'}代理人：______
{datetime.now().strftime('%Y')}年{datetime.now().strftime('%m')}月{datetime.now().strftime('%d')}日
"""


def _generate_questions():
    return """# 交叉询问问题参考

## 针对证人

1. 请陈述事发当天的具体情况？
2. 你当时所处的位置？
3. 你看到/听到了什么？
4. 证据是如何取得的？

## 常用技巧

- **封闭式提问**：让对方只能回答"是"或"否"
- **时间线确认**：按时间顺序逐项确认
- **矛盾点追问**：发现陈述矛盾时及时追问
"""


def _generate_objections():
    return """# 常用异议表达

## 诱导性提问
"反对，对方提问具有诱导性。"

## 无关性问题
"反对，该问题与本案无关。"

## 重复提问
"反对，属于重复提问。"

## 猜测性陈述
"反对，证人陈述的是主观推测。"

---

*注：实际使用时请根据案件情况调整。*
"""


st.divider()
st.caption("🎙️ 会议/谈判援助 v2.0 | 关联项目，录音存证")
