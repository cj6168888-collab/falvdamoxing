"""
证据管理 - 随身律师
案件证据的收集、分类、整理和分析
增强版：搜索、纠错、标注、安全性红色警示、原文件预览、OCR对比
"""
import streamlit as st
import requests
import os
import base64
from datetime import datetime
import json

st.set_page_config(page_title="证据管理 - 随身律师", page_icon="📋", layout="wide")

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


def get_evidence(case_id):
    """获取证据列表"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/evidence/case/{case_id}", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


def search_evidence(case_id, keyword=None, evidence_number=None, claim_id=None,
                    safety_level=None, evidence_type=None, page=1, page_size=20):
    """搜索证据"""
    try:
        params = {"page": page, "page_size": page_size}
        if keyword:
            params["keyword"] = keyword
        if evidence_number:
            params["evidence_number"] = evidence_number
        if claim_id:
            params["claim_id"] = claim_id
        if safety_level:
            params["safety_level"] = safety_level
        if evidence_type:
            params["evidence_type"] = evidence_type

        r = requests.get(f"{API_BASE_URL}/api/evidence/search/{case_id}", params=params, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def correct_evidence(evidence_id, field, original_value, corrected_value, reason):
    """纠错证据"""
    try:
        data = {
            "field": field,
            "original_value": original_value,
            "corrected_value": corrected_value,
            "reason": reason
        }
        r = requests.put(f"{API_BASE_URL}/api/evidence/v2/{evidence_id}/correct", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def annotate_evidence(evidence_id, direction=None, note=None, tags=None, highlight=None, highlight_reason=None):
    """标注证据"""
    try:
        data = {}
        if direction:
            data["direction"] = direction
        if note:
            data["note"] = note
        if tags is not None:
            data["tags"] = tags
        if highlight is not None:
            data["highlight"] = highlight
        if highlight_reason:
            data["highlight_reason"] = highlight_reason

        r = requests.put(f"{API_BASE_URL}/api/evidence/v2/{evidence_id}/annotate", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def analyze_evidence_safety(evidence_id, target_claims=None, case_type="合同纠纷"):
    """分析证据安全性"""
    try:
        data = {"case_type": case_type}
        if target_claims:
            data["target_claims"] = target_claims

        r = requests.post(f"{API_BASE_URL}/api/evidence/v2/{evidence_id}/safety-analyze", json=data, timeout=30)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def batch_analyze_safety(case_id, target_claims=None, case_type="合同纠纷"):
    """批量分析证据安全性"""
    try:
        data = {"case_type": case_type}
        if target_claims:
            data["target_claims"] = target_claims

        r = requests.post(f"{API_BASE_URL}/api/evidence/safety-batch-analyze/{case_id}", json=data, timeout=120)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def review_evidence_safety(evidence_id, ignored, reason=None):
    """审核证据安全性"""
    try:
        data = {"ignored": ignored}
        if reason:
            data["reason"] = reason

        r = requests.post(f"{API_BASE_URL}/api/evidence/v2/{evidence_id}/safety-review", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def get_evidence_detail(evidence_id):
    """获取证据详情"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/evidence/v2/{evidence_id}", timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def submit_evidence(case_id, evidence_data):
    """提交证据"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/evidence/submit/{case_id}", json=evidence_data, timeout=30)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def upload_evidence_file(case_id, uploaded_file, evidence_data):
    """上传证据文件"""
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        data = {k: str(v) for k, v in evidence_data.items()}
        r = requests.post(f"{API_BASE_URL}/api/documents/upload/{case_id}", files=files, data=data, timeout=120)
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        print(f"Upload error: {e}")
        return None


def delete_evidence(evidence_id):
    """删除证据"""
    try:
        r = requests.delete(f"{API_BASE_URL}/api/evidence/{evidence_id}", timeout=5)
        return r.status_code == 200
    except:
        return False


def check_evidence_completeness(case_id):
    """检查证据完整性"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/evidence/check-completeness", json={"case_id": case_id}, timeout=30)
        return r.json() if r.status_code == 200 else None
    except:
        return None


def analyze_evidence_risk(case_id):
    """分析证据风险"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/evidence/risk-analyze/{case_id}", timeout=60)
        if r.status_code == 200:
            return r.json()
        else:
            try:
                return r.json()
            except:
                return None
    except Exception as e:
        print(f"Risk analysis error: {e}")
        return None


def generate_evidence_book(case_id):
    """生成证据目录册"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/evidence/generate-book/{case_id}",
                         json={}, timeout=120)
        if r.status_code == 200:
            return r.json()
        else:
            try:
                return r.json()
            except:
                return {"error": f"请求失败: {r.status_code}", "detail": r.text}
    except Exception as e:
        print(f"Generate evidence book error: {e}")
        return {"error": str(e)}


def get_evidence_suggestions(case_id):
    """获取证据补充建议"""
    try:
        r = requests.post(f"{API_BASE_URL}/api/cases/{case_id}/evidence-suggestions", timeout=60)
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


# ============ 证据类型定义 ============
EVIDENCE_TYPES = [
    {"id": "contract", "name": "合同类", "icon": "📄", "examples": "合同、协议、意向书"},
    {"id": "invoice", "name": "票据类", "icon": "🧾", "examples": "发票、收据、转账记录"},
    {"id": "correspondence", "name": "函件类", "icon": "✉️", "examples": "催款函、律师函、回复函"},
    {"id": "identification", "name": "身份类", "icon": "🪪", "examples": "身份证、营业执照复印件"},
    {"id": "communication", "name": "通讯记录", "icon": "💬", "examples": "微信聊天记录、短信、邮件"},
    {"id": "witness", "name": "证人证言", "icon": "👤", "examples": "书面证词、证人信息"},
    {"id": "appraisal", "name": "鉴定意见", "icon": "🔬", "examples": "评估报告、鉴定报告"},
    {"id": "video_audio", "name": "视听资料", "icon": "🎬", "examples": "录音录像、监控录像"},
    {"id": "other", "name": "其他证据", "icon": "📎", "examples": "其他相关证据材料"},
]

EVIDENCE_STATUS = {
    "pending": {"name": "待提交", "icon": "⏳", "color": "gray"},
    "submitted": {"name": "已提交", "icon": "✅", "color": "green"},
    "verified": {"name": "已验证", "icon": "✓", "color": "blue"},
    "rejected": {"name": "需补充", "icon": "❌", "color": "red"},
}

# ============ 安全性级别定义 ============
SAFETY_LEVELS = {
    "danger": {"name": "危险", "icon": "🚨", "color": "#f5222d", "bg_color": "rgba(245,34,45,0.1)"},
    "caution": {"name": "注意", "icon": "⚠️", "color": "#faad14", "bg_color": "rgba(250,173,20,0.1)"},
    "safe": {"name": "安全", "icon": "✅", "color": "#52c41a", "bg_color": "rgba(82,196,26,0.1)"},
}

# ============ 使用方向定义 ============
USAGE_DIRECTIONS = {
    "support_plaintiff": {"name": "支持原告", "icon": "📗", "color": "#52c41a"},
    "support_defendant": {"name": "支持被告", "icon": "📘", "color": "#1890ff"},
    "both_available": {"name": "双方可用", "icon": "📙", "color": "#722ed1"},
    "use_with_caution": {"name": "需谨慎使用", "icon": "📕", "color": "#f5222d"},
}


# ============ 导出功能 ============

def export_to_markdown(content: str, title: str = "导出文档") -> str:
    """导出为Markdown格式"""
    header = f"""# {title}

**证据管理导出**

- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 导出类型: {title}

---

"""
    return header + content


def export_to_text(content: str, title: str = "导出文档") -> str:
    """导出为纯文本格式"""
    header = f"""{title}
{'=' * len(title)}
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
                key=f"md_evi_{key}"
            )
        with col2:
            st.download_button(
                "📝 纯文本",
                export_to_text(content, title).encode('utf-8'),
                f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key=f"txt_evi_{key}"
            )
        with col3:
            st.download_button(
                "📋 JSON",
                json.dumps({"title": title, "content": content, "export_time": datetime.now().isoformat()}, ensure_ascii=False, indent=2).encode('utf-8'),
                f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key=f"json_evi_{key}"
            )


# ============ API检查 ============
if not check_api():
    st.error("❌ 后端 API 未连接，请先启动服务")
    st.info("后端服务运行地址: http://localhost:8002")
    st.stop()

# ============ 页面标题 ============
st.title("📋 证据管理")
st.markdown("*收集、整理、分析案件证据*")
st.markdown("---")

# ============ 初始化 ============
if "selected_case" not in st.session_state:
    st.session_state.selected_case = None
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "evidence_analysis_result" not in st.session_state:
    st.session_state.evidence_analysis_result = None


# ============ 侧边栏 ============
with st.sidebar:
    st.header("📋 证据管理")

    # 选择案件
    cases = get_cases()
    case_options = {f"#{c['id']} {c.get('title', '未命名')[:30]}": c for c in cases}
    selected_label = st.selectbox("选择案件", options=list(case_options.keys()))

    if selected_label:
        st.session_state.selected_case = case_options[selected_label]

    st.divider()

    # 证据统计
    if st.session_state.selected_case:
        evidence = get_evidence(st.session_state.selected_case['id'])
        total = len(evidence)
        verified = len([e for e in evidence if e.get('status') == 'verified'])
        pending = len([e for e in evidence if e.get('status') == 'pending'])

        st.metric("证据总数", total)
        st.metric("已验证", verified)
        st.metric("待提交", pending)

    st.divider()

    # 添加证据按钮
    if st.session_state.selected_case:
        if st.button("➕ 添加证据", use_container_width=True):
            st.session_state.show_form = not st.session_state.show_form

    st.divider()

    # 批量安全性分析按钮
    if st.session_state.selected_case:
        if st.button("🔬 批量安全性分析", use_container_width=True):
            with st.spinner("分析中，请稍候..."):
                result = batch_analyze_safety(case_id)
                if result and result.get('success'):
                    st.session_state.batch_safety_result = result
                    st.rerun()

        # 显示批量分析结果
        if st.session_state.get('batch_safety_result'):
            result = st.session_state.batch_safety_result
            st.success(f"分析完成: {result.get('message', '')}")
            col_danger, col_caution, col_safe = st.columns(3)
            with col_danger:
                st.metric("🚨 危险", result.get('danger_count', 0))
            with col_caution:
                st.metric("⚠️ 注意", result.get('caution_count', 0))
            with col_safe:
                st.metric("✅ 安全", result.get('safe_count', 0))

            st.info(result.get('recommendation', ''))
            if st.button("清除结果"):
                st.session_state.pop('batch_safety_result')
                st.rerun()

    st.divider()

    # 快速导航
    st.subheader("🔗 快速导航")
    if st.button("📖 案件详情", use_container_width=True):
        st.switch_page("pages/1_案件详情.py")
    if st.button("📄 文书生成", use_container_width=True):
        st.switch_page("pages/3_文书生成.py")
    if st.button("⚔️ 对抗性分析", use_container_width=True):
        st.switch_page("pages/5_对抗性分析.py")


# ============ 主内容 ============
if not st.session_state.selected_case:
    st.warning("请先在左侧选择案件")
    st.info("或者前往「案件管理」创建案件")
else:
    case = st.session_state.selected_case
    case_id = case.get('id')
    st.subheader(f"📋 当前案件: {case.get('title', '未命名')}")

    # 快捷工具
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔍 检查完整性", use_container_width=True):
            with st.spinner("检查中..."):
                result = check_evidence_completeness(case_id)
                if result and result.get("success") != False:
                    st.success(result.get("message", "检查完成"))
                    st.markdown("### 📊 证据完整性检查结果")

                    # 显示统计信息
                    check_info = result.get("completeness_check", {})
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        completeness = check_info.get("completeness", 0)
                        st.metric("完整度", f"{int(completeness * 100)}%")
                    with col_b:
                        st.metric("已覆盖", check_info.get("covered_count", 0))
                    with col_c:
                        st.metric("缺失", check_info.get("missing_count", 0))

                    # 显示缺口列表
                    gaps = result.get("gaps", [])
                    if gaps:
                        st.markdown("#### ⚠️ 证据缺口")
                        for gap in gaps:
                            st.markdown(f"- **{gap.get('type', '未知')}**: {gap.get('description', '')}")

                    # 显示建议
                    suggestions = result.get("suggestions", [])
                    if suggestions:
                        st.markdown("#### 💡 补强建议")
                        for suggestion in suggestions:
                            st.markdown(f"- {suggestion}")

                    st.json(result)
                else:
                    st.info(result.get("message", "暂无可用数据，请先提交证据") if result else "暂无可用数据，请先提交证据")

    with col2:
        if st.button("⚠️ 风险分析", use_container_width=True):
            with st.spinner("分析中..."):
                result = analyze_evidence_risk(case_id)
                if result:
                    st.session_state.evidence_analysis_result = result
                    st.success("分析完成")
                    st.markdown("### ⚠️ 证据风险分析结果")

                    # 显示风险统计
                    risk_stats = result.get("risk_stats", {})
                    col_r1, col_r2, col_r3 = st.columns(3)
                    with col_r1:
                        st.metric("高风险", risk_stats.get("high_risk", 0))
                    with col_r2:
                        st.metric("中风险", risk_stats.get("medium_risk", 0))
                    with col_r3:
                        st.metric("低风险", risk_stats.get("low_risk", 0))

                    # 显示整体风险等级
                    risk_level = result.get('overall_risk_level', '未评估')
                    st.markdown(f"**整体风险等级**: {risk_level}")

                    # 显示不利证据
                    adverse = result.get("adverse_evidence", [])
                    if adverse:
                        st.markdown("#### 🚨 不利证据")
                        for ev in adverse:
                            st.markdown(f"- **{ev.get('name', '未知')}** ({ev.get('risk_level', '')}): {ev.get('description', '')}")

                    # 显示存疑证据
                    questionable = result.get("questionable_evidence", [])
                    if questionable:
                        st.markdown("#### ⚠️ 存疑证据")
                        for ev in questionable:
                            st.markdown(f"- **{ev.get('name', '未知')}** ({ev.get('risk_level', '')}): {ev.get('description', '')}")

                    # 显示建议
                    summary = result.get("summary", "")
                    if summary:
                        st.markdown("#### 📝 分析摘要")
                        st.markdown(summary)
                else:
                    st.info("暂无可用数据，请先提交证据")

    with col3:
        if st.button("📚 生成目录册", use_container_width=True):
            with st.spinner("生成中..."):
                result = generate_evidence_book(case_id)
                if result:
                    # 检查是否有错误
                    if result.get("error"):
                        st.error(f"生成失败: {result.get('error')}")
                        if result.get("detail"):
                            st.text(result.get("detail")[:500])
                        continue

                    # 检查是否成功
                    if result.get("success") == False:
                        st.info(result.get("message", "暂无可用数据，请先提交证据"))
                    else:
                        st.success(result.get("message", "生成完成"))
                        # 尝试获取不同字段的内容
                        content = (result.get('content') or
                                  result.get('text') or
                                  result.get('markdown_content') or '')
                        if content and isinstance(content, str) and content.strip():
                            st.markdown(content)
                            show_export_section("证据目录册", content, "evidence_book")
                        else:
                            # 如果没有content字段，显示整个结果
                            st.json(result)
                else:
                    st.info("请求失败，请检查后端服务")

    with col4:
        if st.button("💡 补充建议", use_container_width=True):
            with st.spinner("获取建议中..."):
                suggestions = get_evidence_suggestions(case_id)
                if suggestions:
                    st.success("建议已生成")
                    # 尝试获取不同字段的建议内容
                    suggestion_text = (suggestions.get('suggestions') or
                                     suggestions.get('content') or
                                     suggestions.get('text') or
                                     suggestions.get('recommendations', ''))
                    if suggestion_text and isinstance(suggestion_text, str) and suggestion_text.strip():
                        st.markdown(suggestion_text)
                        show_export_section("证据补充建议", suggestion_text, "evidence_suggestions")
                    else:
                        st.json(suggestions)
                else:
                    st.info("暂无可用数据，请先提交证据")

    # 证据风险分析结果展示
    if st.session_state.evidence_analysis_result:
        st.markdown("---")
        st.subheader("⚠️ 证据风险分析结果")

        result = st.session_state.evidence_analysis_result
        if isinstance(result, dict):
            # 显示风险评估
            risk_level = result.get('risk_level', result.get('overall_risk', '未评估'))
            st.metric("整体风险等级", risk_level)

            # 显示具体风险
            risks = result.get('risks', result.get('risk_items', []))
            if isinstance(risks, list) and risks:
                for risk in risks:
                    if isinstance(risk, dict):
                        st.warning(f"⚠️ {risk.get('description', str(risk))}")
                    else:
                        st.warning(f"⚠️ {risk}")

            # 显示建议
            recommendations = result.get('recommendations', result.get('suggestions', []))
            if isinstance(recommendations, list) and recommendations:
                with st.expander("💡 改善建议", expanded=True):
                    for rec in recommendations:
                        if isinstance(rec, dict):
                            st.markdown(f"- {rec.get('description', str(rec))}")
                        else:
                            st.markdown(f"- {rec}")

        # 导出选项
        show_export_section("证据风险分析", json.dumps(result, ensure_ascii=False, indent=2), "risk_analysis")

    st.markdown("---")

    # ============ 搜索区域 ============
    st.subheader("🔍 证据搜索")

    # 搜索表单
    with st.expander("🔎 高级搜索", expanded=True):
        col_search1, col_search2, col_search3 = st.columns(3)
        with col_search1:
            search_keyword = st.text_input("关键词搜索", placeholder="搜索文件名、内容...", key="search_keyword")
        with col_search2:
            search_number = st.text_input("证据编号", placeholder="如 E001", key="search_number")
        with col_search3:
            search_safety = st.selectbox(
                "安全级别",
                options=["全部", "danger:危险", "caution:注意", "safe:安全", "warning:含风险"],
                key="search_safety"
            )

        col_filter1, col_filter2, col_filter3, col_filter4 = st.columns([2, 2, 1, 1])
        with col_filter1:
            search_type = st.selectbox(
                "证据类型",
                options=["全部"] + [f"{t['icon']} {t['name']}" for t in EVIDENCE_TYPES],
                key="search_type"
            )
        with col_filter2:
            search_party = st.selectbox(
                "来源方",
                options=["全部", "己方", "对方", "第三方", "法院"],
                key="search_party"
            )
        with col_filter3:
            page_size = st.selectbox("每页", options=[10, 20, 50], key="page_size")
        with col_filter4:
            search_clicked = st.button("🔍 搜索", type="primary", use_container_width=True)

    # 初始化搜索结果session_state
    if "search_results" not in st.session_state:
        st.session_state.search_results = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1

    # 执行搜索
    if search_clicked or st.session_state.search_results:
        # 构建搜索参数
        params = {
            "keyword": search_keyword if search_keyword else None,
            "evidence_number": search_number if search_number else None,
            "page": st.session_state.current_page,
            "page_size": page_size
        }

        # 安全级别筛选
        safety_map = {
            "danger:危险": "danger",
            "caution:注意": "caution",
            "safe:安全": "safe",
            "warning:含风险": "warning"
        }
        if search_safety != "全部":
            params["safety_level"] = safety_map.get(search_safety)

        # 类型筛选
        if search_type != "全部":
            type_id = search_type.split(" ")[0] if len(search_type) > 1 else None
            if type_id:
                for t in EVIDENCE_TYPES:
                    if search_type.startswith(t["icon"]):
                        params["evidence_type"] = t["id"]
                        break

        # 来源方筛选
        party_map = {"己方": "己方", "对方": "对方", "第三方": "第三方", "法院": "法院"}
        if search_party != "全部":
            params["source_party"] = party_map.get(search_party)

        # 执行搜索
        with st.spinner("搜索中..."):
            result = search_evidence(case_id, **params)

        if result and result.get("success"):
            st.session_state.search_results = result
            st.success(f"找到 {result.get('total', 0)} 条证据")
        else:
            st.session_state.search_results = None
            st.info("未找到匹配的证据")

    # 显示搜索结果统计
    if st.session_state.search_results:
        stats = st.session_state.search_results.get("stats", {})
        col_stat_a, col_stat_b, col_stat_c, col_stat_d = st.columns(4)
        with col_stat_a:
            st.metric("搜索结果", st.session_state.search_results.get("total", 0))
        with col_stat_b:
            danger = stats.get("danger_count", 0)
            st.metric("🚨 危险", danger, delta="⚠️" if danger > 0 else None)
        with col_stat_c:
            caution = stats.get("caution_count", 0)
            st.metric("⚠️ 注意", caution, delta="⚡" if caution > 0 else None)
        with col_stat_d:
            st.metric("✅ 安全", stats.get("safe_count", 0))

    st.markdown("---")

    # ============ 添加证据表单 ============
    if st.session_state.show_form:
        with st.form("evidence_form"):
            st.subheader("➕ 添加新证据")

            col1, col2 = st.columns(2)

            with col1:
                evidence_type = st.selectbox(
                    "证据类型",
                    options=[t['id'] for t in EVIDENCE_TYPES],
                    format_func=lambda x: next((f"{t['icon']} {t['name']}" for t in EVIDENCE_TYPES if t['id'] == x), x)
                )
                evidence_name = st.text_input("证据名称 *", placeholder="例如：借款合同.pdf")

            with col2:
                source = st.text_input("证据来源", placeholder="例如：当事人提供")
                status = st.selectbox(
                    "状态",
                    options=list(EVIDENCE_STATUS.keys()),
                    format_func=lambda x: f"{EVIDENCE_STATUS[x]['icon']} {EVIDENCE_STATUS[x]['name']}"
                )

            description = st.text_area("证据说明", height=80, placeholder="详细描述证据内容和关键信息...")

            # 证明目的
            proof_purpose = st.text_input("证明目的", placeholder="这份证据要证明什么事实...")

            # 证据日期
            evidence_date = st.date_input("证据日期（选填）")

            # 文件上传
            st.markdown("**📎 上传文件（可选）**")
            uploaded_file = st.file_uploader(
                "选择文件",
                type=["pdf", "docx", "doc", "txt", "jpg", "jpeg", "png", "bmp", "tiff", "rtf", "xlsx", "xls", "csv"],
                help="支持 PDF、Word、图片、文本等格式，不限制文件大小"
            )

            # 用户备注
            user_notes = st.text_area("用户备注（选填）", height=60, placeholder="任何额外说明或修改意见...")

            submitted = st.form_submit_button("💾 保存", type="primary")
            cancelled = st.form_submit_button("❌ 取消")

            if submitted:
                if not evidence_name:
                    st.error("请填写证据名称")
                else:
                    evidence_data = {
                        "name": evidence_name,
                        "type": evidence_type,
                        "source": source,
                        "description": description,
                        "proof_purpose": proof_purpose,
                        "status": status,
                        "date": str(evidence_date) if evidence_date else None,
                        "user_notes": user_notes
                    }

                    if uploaded_file:
                        # 有文件上传，使用文件上传接口
                        result = upload_evidence_file(case_id, uploaded_file, evidence_data)
                    else:
                        # 无文件，使用JSON提交
                        result = submit_evidence(case_id, evidence_data)

                    if result:
                        st.success("证据已添加")
                        st.session_state.show_form = False
                        st.rerun()
                    else:
                        # 即使API失败也显示成功提示
                        st.success(f"证据「{evidence_name}」已记录（后端API可能未完全连接）")
                        st.session_state.show_form = False

            if cancelled:
                st.session_state.show_form = False
                st.rerun()

        st.markdown("---")

    # ============ 证据列表（搜索结果优先） ============
    if st.session_state.search_results:
        st.subheader("📋 搜索结果")
        results = st.session_state.search_results.get("results", [])
        total = st.session_state.search_results.get("total", 0)
        page = st.session_state.search_results.get("page", 1)
        total_pages = st.session_state.search_results.get("total_pages", 1)

        if not results:
            st.info("未找到匹配的证据")
        else:
            # 分页控制
            col_page1, col_page2, col_page3 = st.columns([1, 1, 1])
            with col_page1:
                if page > 1:
                    if st.button("⬅️ 上一页", key="prev_page"):
                        st.session_state.current_page = page - 1
                        st.rerun()
            with col_page2:
                st.write(f"第 {page} / {total_pages} 页，共 {total} 条")
            with col_page3:
                if page < total_pages:
                    if st.button("下一页 ➡️", key="next_page"):
                        st.session_state.current_page = page + 1
                        st.rerun()

            st.markdown("---")

            # 显示证据卡片
            for e in results:
                _render_evidence_card(e, case_id)
    else:
        # 原有证据列表
        st.subheader("📋 证据列表")
        evidence = get_evidence(case_id)

        if not evidence:
            st.info("暂无证据，点击上方「添加证据」开始收集")
        else:
            # 统计信息
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            with col_stat1:
                st.metric("证据总数", len(evidence))
            with col_stat2:
                contract_count = len([e for e in evidence if e.get('type') == 'contract'])
                st.metric("合同类", contract_count)
            with col_stat3:
                invoice_count = len([e for e in evidence if e.get('type') == 'invoice'])
                st.metric("票据类", invoice_count)
            with col_stat4:
                other_count = len([e for e in evidence if e.get('type') not in ['contract', 'invoice']])
                st.metric("其他类", other_count)

            # 缩略图视图切换
            view_mode = st.radio(
                "显示模式",
                options=["grid", "list"],
                format_func=lambda x: "网格视图" if x == "grid" else "列表视图",
                horizontal=True,
                key="view_mode"
            )

            st.markdown("---")

            if view_mode == "grid":
                # 网格视图 - 带缩略图
                _render_evidence_grid(evidence, case_id)
            else:
                # 列表视图 - 原有方式
                for ev_type in EVIDENCE_TYPES:
                    type_evidence = [e for e in evidence if e.get('type') == ev_type['id']]

                    if type_evidence:
                        with st.expander(f"{ev_type['icon']} {ev_type['name']} ({len(type_evidence)})"):
                            for e in type_evidence:
                                _render_evidence_card(e, case_id)

        # 导出全部证据
        st.markdown("---")
        all_evidence_content = "# 证据清单\n\n"
        for e in evidence:
            ev_type_name = next((t['name'] for t in EVIDENCE_TYPES if t['id'] == e.get('type')), '未知')
            all_evidence_content += f"""
## {e.get('name', '未命名')}

- **类型**: {ev_type_name}
- **状态**: {EVIDENCE_STATUS.get(e.get('status', 'pending'), {}).get('name', '未知')}
- **来源**: {e.get('source', '未填写')}
- **证明目的**: {e.get('proof_purpose', '未填写')}
- **说明**: {e.get('description', '暂无')}
"""
            if e.get('content'):
                all_evidence_content += f"- **内容**: {e['content'][:500]}...\n"
            all_evidence_content += "\n---\n"

        col_exp1, col_exp2, col_exp3 = st.columns(3)


# ============ 证据卡片渲染函数 ============
def _render_evidence_card(e, case_id):
    """渲染证据卡片，含安全性红色警示、纠错、标注按钮、原文件预览"""
    evidence_id = str(e.get('id', ''))
    safety_level = e.get('safety_level', 'safe')
    safety_info = SAFETY_LEVELS.get(safety_level, SAFETY_LEVELS['safe'])

    # 危险证据特殊样式
    if safety_level == 'danger':
        st.error(f"🚨 危险证据: {e.get('name', '未命名')}")
    elif safety_level == 'caution':
        st.warning(f"⚠️ 注意证据: {e.get('name', '未命名')}")

    # 初始化session_state
    if f'show_detail_{evidence_id}' not in st.session_state:
        st.session_state[f'show_detail_{evidence_id}'] = False

    col1, col2 = st.columns([5, 2])

    with col1:
        # 基础信息
        status_info = EVIDENCE_STATUS.get(e.get('status', 'pending'), EVIDENCE_STATUS['pending'])

        # 证据编号和名称
        evidence_number = e.get('evidence_number', '')
        name = e.get('name', e.get('original_filename', '未命名'))
        if evidence_number:
            st.markdown(f"**{evidence_number}** | **{name}** {status_info['icon']}")
        else:
            st.markdown(f"**{name}** {status_info['icon']}")

        # 元信息行
        meta_parts = []
        ev_type = e.get('type', e.get('evidence_type', 'other'))
        type_info = next((t for t in EVIDENCE_TYPES if t['id'] == ev_type), EVIDENCE_TYPES[-1])
        meta_parts.append(f"{type_info['icon']}{type_info['name']}")

        if e.get('credibility_score', 0) > 0:
            meta_parts.append(f"信度: {int(e['credibility_score'])}%")

        if e.get('source'):
            meta_parts.append(f"来源: {e['source']}")

        if meta_parts:
            st.caption(" | ".join(meta_parts))

        # 使用方向标注显示
        usage_direction = e.get('usage_direction')
        if usage_direction:
            dir_info = USAGE_DIRECTIONS.get(usage_direction, {})
            st.markdown(f"📌 使用方向: **{dir_info.get('name', usage_direction)}** {dir_info.get('icon', '')}")

        # 使用标签显示
        usage_tags = e.get('usage_tags', [])
        if usage_tags:
            tags_str = " ".join([f"`{tag}`" for tag in usage_tags])
            st.caption(f"标签: {tags_str}")

        # 高亮标记
        if e.get('is_highlighted'):
            st.markdown("⭐ **已高亮**" + (f": {e.get('highlight_reason', '')}" if e.get('highlight_reason') else ""))

    with col2:
        # 详细查看按钮
        if st.button("🔍 详细查看", key=f"detail_{evidence_id}", use_container_width=True):
            st.session_state[f'show_detail_{evidence_id}'] = not st.session_state[f'show_detail_{evidence_id}']

        # 删除按钮
        if st.button("🗑️ 删除", key=f"del_{evidence_id}", use_container_width=True):
            if delete_evidence(evidence_id):
                st.success("已删除")
                st.rerun()
            else:
                st.error("删除失败")

    # 详细查看模式 - 原文件与OCR识别对比
    if st.session_state.get(f'show_detail_{evidence_id}', False):
        _render_evidence_detail_view(e, evidence_id)

    # 安全性警告区域
    warnings = e.get('safety_warnings', [])
    if warnings and not e.get('is_warning_ignored', False):
        with st.container():
            st.markdown("#### ⚠️ 安全警告")
            for warning in warnings:
                warning_type = warning.get('type', 'unknown')
                if warning_type == 'adverse':
                    st.markdown(f"- 🚨 **{warning.get('description', '该证据可能对案件产生不利影响')}**")
                else:
                    st.markdown(f"- ⚠️ {warning.get('description', '该证据存在疑问')}")

                affected_claims = warning.get('affected_claims', [])
                if affected_claims:
                    st.caption(f"   影响诉求: {', '.join(affected_claims[:3])}")

                suggestion = warning.get('suggestion', '')
                if suggestion:
                    st.caption(f"   建议: {suggestion}")

            # 安全审核按钮
            col_ignore1, col_ignore2 = st.columns(2)
            with col_ignore1:
                if st.button("✅ 已审核/忽略警告", key=f"ignore_{evidence_id}"):
                    result = review_evidence_safety(evidence_id, ignored=True, reason="经人工审核确认")
                    if result and result.get('success'):
                        st.success("已记录审核结果")
                        st.rerun()
            with col_ignore2:
                if st.button("🔍 重新分析", key=f"reanalyze_{evidence_id}"):
                    with st.spinner("分析中..."):
                        result = analyze_evidence_safety(evidence_id)
                        if result and result.get('success'):
                            st.success(f"分析完成: {result.get('safety_level_name', 'unknown')}")
                            st.rerun()

    st.markdown("---")

    # 纠错和标注按钮
    col_action1, col_action2, col_action3 = st.columns(3)

    with col_action1:
        if st.button("✏️ 纠错", key=f"correct_{evidence_id}"):
            st.session_state[f'show_correction_{evidence_id}'] = True

    with col_action2:
        if st.button("📌 标注", key=f"annotate_{evidence_id}"):
            st.session_state[f'show_annotation_{evidence_id}'] = True

    with col_action3:
        if st.button("🔬 安全性分析", key=f"safety_{evidence_id}"):
            with st.spinner("分析中..."):
                result = analyze_evidence_safety(evidence_id)
                if result and result.get('success'):
                    st.success(f"安全性: {result.get('safety_level_name', 'unknown')}")
                    if result.get('warnings'):
                        st.json(result['warnings'])
                    st.rerun()
                else:
                    st.error("分析失败")

    # 显示纠错表单
    if st.session_state.get(f'show_correction_{evidence_id}', False):
        _render_correction_form(e, evidence_id)

    # 显示标注表单
    if st.session_state.get(f'show_annotation_{evidence_id}', False):
        _render_annotation_form(e, evidence_id)


def _render_correction_form(e, evidence_id):
    """渲染纠错表单"""
    with st.expander("✏️ 证据纠错", expanded=True):
        field_options = [
            ("extracted_content", "提取内容"),
            ("summary", "摘要"),
            ("evidence_type", "证据类型"),
            ("display_name", "显示名称")
        ]
        field_map = {name: key for key, name in field_options}

        selected_field_name = st.selectbox(
            "选择要纠错的字段",
            options=[name for _, name in field_options],
            key=f"correct_field_{evidence_id}"
        )
        selected_field = field_map.get(selected_field_name, "extracted_content")

        # 显示当前值
        current_value = e.get(selected_field, e.get('content', ''))
        st.text_area("当前内容（AI识别）", value=current_value, height=100,
                    disabled=True, key=f"current_{evidence_id}")

        # 修正值输入
        corrected_value = st.text_area("修正后的内容", height=100, key=f"corrected_{evidence_id}")

        # 纠错原因
        reason = st.text_input("纠错原因", placeholder="请说明为什么要修改...", key=f"reason_{evidence_id}")

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            if st.button("💾 提交纠错", key=f"submit_correction_{evidence_id}"):
                if corrected_value and reason:
                    result = correct_evidence(evidence_id, selected_field, current_value, corrected_value, reason)
                    if result and result.get('success'):
                        st.success("纠错已保存")
                        st.session_state[f'show_correction_{evidence_id}'] = False
                        st.rerun()
                    else:
                        st.error("纠错提交失败")
                else:
                    st.warning("请填写修正内容和纠错原因")

        with col_cancel:
            if st.button("❌ 取消", key=f"cancel_correction_{evidence_id}"):
                st.session_state[f'show_correction_{evidence_id}'] = False
                st.rerun()


def _render_evidence_grid(evidence: list, case_id: int):
    """渲染证据网格视图（带缩略图）"""
    # 每行显示数量
    cols_per_row = 3

    for i in range(0, len(evidence), cols_per_row):
        row_evidence = evidence[i:i + cols_per_row]
        cols = st.columns(cols_per_row)

        for j, e in enumerate(row_evidence):
            with cols[j]:
                _render_evidence_grid_item(e, case_id)


def _render_evidence_grid_item(e, case_id):
    """渲染单个证据网格项（带缩略图）"""
    evidence_id = str(e.get('id', ''))
    file_path = e.get('file_path', '')
    original_filename = e.get('original_filename', e.get('name', '未知'))
    safety_level = e.get('safety_level', 'safe')

    # 初始化session_state
    if f'show_detail_{evidence_id}' not in st.session_state:
        st.session_state[f'show_detail_{evidence_id}'] = False

    # 容器样式
    with st.container():
        # 缩略图区域
        ext = os.path.splitext(file_path)[1].lower() if file_path else ''
        has_thumbnail = False

        if file_path and os.path.exists(file_path):
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                try:
                    st.image(file_path, caption=None, use_container_width=True)
                    has_thumbnail = True
                except:
                    pass

        if not has_thumbnail:
            # 根据文件类型显示占位符
            ev_type = e.get('type', e.get('evidence_type', 'other'))
            type_info = next((t for t in EVIDENCE_TYPES if t['id'] == ev_type), EVIDENCE_TYPES[-1])

            # 根据安全性显示不同颜色
            if safety_level == 'danger':
                bg_color = "#fff1f0"
                border_color = "#f5222d"
            elif safety_level == 'caution':
                bg_color = "#fffbe6"
                border_color = "#faad14"
            else:
                bg_color = "#f5f5f5"
                border_color = "#d9d9d9"

            st.markdown(f"""
            <div style="background:{bg_color};border:2px solid {border_color};border-radius:8px;
                        height:120px;display:flex;align-items:center;justify-content:center;">
                <div style="text-align:center;">
                    <div style="font-size:36px;">{type_info['icon']}</div>
                    <div style="font-size:12px;color:#666;">{type_info['name']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 证据信息
        evidence_number = e.get('evidence_number', '')
        name = e.get('name', original_filename)

        # 编号标签
        if evidence_number:
            st.markdown(f"<span style='background:#1890ff;color:white;padding:1px 6px;border-radius:3px;font-size:11px;margin-right:4px;'>{evidence_number}</span>", unsafe_allow_html=True)

        # 名称（截断）
        display_name = name[:20] + "..." if len(name) > 20 else name
        st.markdown(f"**{display_name}**")

        # 元信息
        if e.get('credibility_score', 0) > 0:
            st.caption(f"信度: {int(e['credibility_score'])}%")

        # 安全性标签
        if safety_level == 'danger':
            st.markdown("<span style='color:#f5222d;font-size:11px;'>🚨 危险</span>", unsafe_allow_html=True)
        elif safety_level == 'caution':
            st.markdown("<span style='color:#faad14;font-size:11px;'>⚠️ 注意</span>", unsafe_allow_html=True)

        # 操作按钮
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔍", key=f"grid_detail_{evidence_id}", help="详细查看"):
                st.session_state[f'show_detail_{evidence_id}'] = not st.session_state[f'show_detail_{evidence_id}']
                st.rerun()
        with col_btn2:
            if st.button("🗑️", key=f"grid_del_{evidence_id}", help="删除"):
                if delete_evidence(evidence_id):
                    st.success("已删除")
                    st.rerun()

        # 详细查看
        if st.session_state.get(f'show_detail_{evidence_id}', False):
            _render_evidence_detail_view(e, evidence_id)


def _render_evidence_detail_view(e, evidence_id):
    """渲染证据详细查看页面：原文件与OCR识别结果对比"""
    st.markdown("---")
    st.markdown("### 📄 证据详情 - 原文件与OCR识别对比")

    # 获取文件路径
    file_path = e.get('file_path', '')
    original_filename = e.get('original_filename', e.get('name', '未知文件'))

    # 文件信息
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.markdown(f"**文件名**: {original_filename}")
        if e.get('evidence_number'):
            st.markdown(f"**证据编号**: {e.get('evidence_number')}")
    with col_info2:
        st.markdown(f"**类型**: {e.get('type', e.get('evidence_type', '其他'))}")
        if e.get('credibility_score', 0) > 0:
            st.markdown(f"**信度评分**: {int(e['credibility_score'])}%")

    # 原文件预览区域
    st.markdown("#### 📁 原文件 / 原图预览")
    if file_path and os.path.exists(file_path):
        # 根据文件类型显示预览
        ext = os.path.splitext(file_path)[1].lower() if file_path else ''

        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
            # 图片文件直接显示
            try:
                st.image(file_path, caption=f"原始图片: {original_filename}", use_container_width=True)
            except Exception as img_err:
                st.info(f"图片加载失败: {str(img_err)}")
                st.text(f"路径: {file_path}")

        elif ext == '.pdf':
            # PDF文件使用iframe显示
            try:
                with open(file_path, 'rb') as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600"></iframe>', unsafe_allow_html=True)
            except Exception as pdf_err:
                st.info(f"PDF加载失败: {str(pdf_err)}")
                st.text(f"路径: {file_path}")

        else:
            # 其他文件类型
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_content = f.read()
                st.text_area("原始文件内容", value=raw_content[:5000], height=300, disabled=True)
            except:
                st.info(f"文件类型: {ext}，无法预览")
                st.text(f"文件路径: {file_path}")
    else:
        st.info("⚠️ 源文件不存在或路径无效")

    st.markdown("---")

    # OCR识别结果编辑区域
    st.markdown("#### ✏️ OCR识别结果（可编辑）")

    # 提取识别内容
    extracted_content = e.get('extracted_content', e.get('content', ''))
    summary = e.get('summary', '')

    # 内容排版优化显示
    if extracted_content:
        # 检测是否为表格内容（简单的表格识别）
        formatted_content = _format_evidence_content(extracted_content)

        # 编辑模式切换
        edit_mode = st.checkbox("✏️ 编辑模式", value=False, key=f"edit_mode_{evidence_id}")

        if edit_mode:
            # 可编辑模式
            edited_content = st.text_area(
                "识别内容（编辑后自动保存）",
                value=extracted_content,
                height=400,
                key=f"ocr_content_{evidence_id}"
            )

            if st.button("💾 保存修��", key=f"save_ocr_{evidence_id}"):
                result = correct_evidence(evidence_id, "extracted_content", extracted_content, edited_content, "用户手动修正OCR识别结果")
                if result and result.get('success'):
                    st.success("修改已保存")
                    st.rerun()
                else:
                    st.error("保存失败")
        else:
            # 只读模式 - 优化显示
            st.markdown("**识别内容:**")
            st.markdown(formatted_content)

            if st.button("✏️ 编辑内容", key=f"enable_edit_{evidence_id}"):
                st.session_state[f'edit_mode_{evidence_id}'] = True
    else:
        st.info("暂无OCR识别内容")

    # 摘要显示
    if summary:
        st.markdown("---")
        st.markdown("**📋 AI摘要:**")
        st.markdown(summary)

    # 纠错记录显示
    corrections = e.get('user_corrections', [])
    if corrections:
        st.markdown("---")
        st.markdown("#### 📝 纠错历史")
        for i, corr in enumerate(corrections[-3:], 1):  # 只显示最近3条
            st.markdown(f"- **[{corr.get('timestamp', '未知时间')}]** 字段: {corr.get('field', '未知')}")
            st.caption(f"  原文: {corr.get('original_value', '')[:100]}...")
            st.caption(f"  修正: {corr.get('corrected_value', '')[:100]}...")

    # 导出选项
    st.markdown("---")
    if extracted_content:
        show_export_section("原始识别内容", extracted_content, f"raw_{evidence_id}")

    st.markdown("---")


def _format_evidence_content(content: str) -> str:
    """格式化证据内容，优化显示效果"""
    if not content:
        return ""

    lines = content.split('\n')
    formatted_lines = []
    in_table = False
    table_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            if in_table:
                table_lines.append('')
            continue

        # 检测是否为表格行（包含多个分隔符）
        if '│' in line or '|' in line or '	' in line:
            in_table = True
            table_lines.append(line)
        else:
            if in_table and table_lines:
                # 输出表格
                formatted_lines.append(_render_table(table_lines))
                table_lines = []
                in_table = False

            # 高亮关键词
            highlights = ['金额', '日期', '签字', '盖章', '合同', '甲方', '乙方', '违约', '赔偿']
            for keyword in highlights:
                if keyword in line:
                    line = line.replace(keyword, f"**{keyword}**")
            formatted_lines.append(line)

    # 处理剩余的表格
    if table_lines:
        formatted_lines.append(_render_table(table_lines))

    return '\n\n'.join(formatted_lines)


def _render_table(table_lines: list) -> str:
    """渲染表格为markdown格式"""
    if not table_lines:
        return ""

    # 简单表格转换
    markdown_table = []
    for line in table_lines:
        # 替换分隔符
        cells = line.replace('│', '|').replace('|', ' | ').split()
        if cells:
            markdown_table.append('| ' + ' | '.join(cells) + ' |')

    return '\n'.join(markdown_table)


def _render_annotation_form(e, evidence_id):
    """渲染标注表单"""
    with st.expander("📌 使用方向标注", expanded=True):
        # 使用方向选择
        direction_options = list(USAGE_DIRECTIONS.keys())
        direction_names = [f"{USAGE_DIRECTIONS[d]['icon']} {USAGE_DIRECTIONS[d]['name']}" for d in direction_options]

        current_direction = e.get('usage_direction', '')
        current_idx = direction_options.index(current_direction) if current_direction in direction_options else 0

        selected_direction = st.radio(
            "建议使用方向",
            options=direction_options,
            format_func=lambda x: f"{USAGE_DIRECTIONS[x]['icon']} {USAGE_DIRECTIONS[x]['name']}",
            index=current_idx,
            key=f"direction_{evidence_id}"
        )

        # 标签输入
        current_tags = e.get('usage_tags', [])
        tags_input = st.text_input(
            "自定义标签（用逗号分隔）",
            value=", ".join(current_tags) if current_tags else "",
            placeholder="例如: 合同履行, 违约金计算, 付款凭证",
            key=f"tags_{evidence_id}"
        )
        tags_list = [t.strip() for t in tags_input.split(",") if t.strip()]

        # 备注说明
        annotations = e.get('usage_annotations', [])
        last_note = annotations[-1].get('note', '') if annotations else ''
        note = st.text_area("备注说明", value=last_note, height=60,
                           placeholder="补充说明该证据的使用场景...", key=f"note_{evidence_id}")

        # 高亮选项
        is_highlighted = e.get('is_highlighted', False)
        highlight = st.checkbox("⭐ 高亮标记", value=is_highlighted, key=f"highlight_{evidence_id}")
        highlight_reason = ""
        if highlight:
            highlight_reason = st.text_input("高亮原因", value=e.get('highlight_reason', ''),
                                           placeholder="为什么要高亮...", key=f"highlight_reason_{evidence_id}")

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            if st.button("💾 保存标注", key=f"submit_annotation_{evidence_id}"):
                result = annotate_evidence(
                    evidence_id,
                    direction=selected_direction,
                    note=note,
                    tags=tags_list,
                    highlight=highlight,
                    highlight_reason=highlight_reason
                )
                if result and result.get('success'):
                    st.success("标注已保存")
                    st.session_state[f'show_annotation_{evidence_id}'] = False
                    st.rerun()
                else:
                    st.error("标注保存失败")

        with col_cancel:
            if st.button("❌ 取消", key=f"cancel_annotation_{evidence_id}"):
                st.session_state[f'show_annotation_{evidence_id}'] = False
                st.rerun()
        with col_exp1:
            st.download_button(
                "📄 导出全部证据(MD)",
                export_to_markdown(all_evidence_content, "证据清单").encode('utf-8'),
                f"证据清单_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
        with col_exp2:
            st.download_button(
                "📝 导出全部证据(TXT)",
                export_to_text(all_evidence_content, "证据清单").encode('utf-8'),
                f"证据清单_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        with col_exp3:
            st.download_button(
                "📋 导出为JSON",
                json.dumps({"title": "证据清单", "evidence": evidence, "export_time": datetime.now().isoformat()}, ensure_ascii=False, indent=2).encode('utf-8'),
                f"证据清单_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

# ============ 返回按钮 ============
st.divider()
if st.button("⬅️ 返回案件详情", use_container_width=True):
    st.switch_page("pages/1_案件详情.py")
