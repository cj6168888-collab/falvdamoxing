"""
博凯升华案件 — AI 律师全面分析脚本
逐一运行所有 AI 分析模块，导出完整结果
"""
import sys, os, json, time
sys.path.insert(0, ".")

from datetime import datetime
from app.db.database import SessionLocal
from app.models.case import Case, ChatMessage
from app.models.evidence import EvidenceItem
from app.models.document import GeneratedDocument
from app.services.llm_service import llm_service

OUTPUT_DIR = "bokai_analysis_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
CASE_ID = 1

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def write_output(filename, content):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  -> 已保存: {path} ({len(content)} 字符)")

# ============================================================
# 加载案件数据
# ============================================================
db = SessionLocal()
case = db.query(Case).filter(Case.id == CASE_ID).first()
evidence_items = db.query(EvidenceItem).filter(EvidenceItem.case_id == CASE_ID).all()

print("=" * 60)
print("博凯升华案件 AI 全面分析")
print("=" * 60)
print(f"案件: {case.title}")
print(f"原告: {case.plaintiff}")
print(f"被告: {case.defendant}")
print(f"描述: {(case.description or '')[:200]}")
print(f"证据数: {len(evidence_items)}")

# ============================================================
# 1. 资深律师分析 (Senior Lawyer Analysis)
# ============================================================
log("=== 1. 资深律师分析 ===")
try:
    from app.services.senior_lawyer_engine import senior_lawyer_engine
    result = senior_lawyer_engine.analyze_case(case_id=CASE_ID, analysis_level="deep")
    write_output("01_senior_lawyer_analysis.json", json.dumps(result, ensure_ascii=False, indent=2))
    if isinstance(result, dict) and result.get("analysis"):
        write_output("01_senior_lawyer_analysis.txt", str(result.get("analysis", "")))
    log("资深律师分析完成" if result else "资深律师分析返回空")
except Exception as e:
    log(f"错误: {e}")
    import traceback; traceback.print_exc()

# ============================================================
# 2. LLM 法律分析 (Legal Analysis Pipeline)
# ============================================================
log("=== 2. LLM 法律分析管道 ===")
try:
    from app.services.legal_analysis import legal_analysis_service
    evidence_texts = []
    for ev in evidence_items[:30]:
        content = ev.extracted_content or ev.raw_content or ""
        evidence_texts.append(f"【{ev.original_filename}】\n{content[:2000]}")

    case_context = f"""
案件: {case.title}
原告: {case.plaintiff}
被告: {case.defendant}
类型: {case.case_type}
描述: {(case.description or '')[:3000]}
"""
    messages = [
        {"role": "system", "content": "你是资深法律专家，请对该案件进行全面法律分析。"},
        {"role": "user", "content": f"{case_context}\n\n以下是案件证据摘要:\n" + "\n---\n".join(evidence_texts[:20])}
    ]
    analysis = llm_service.chat(messages, model="qwen-plus")
    write_output("02_llm_legal_analysis.txt", analysis)
    log("LLM法律分析完成")
except Exception as e:
    log(f"错误: {e}")

# ============================================================
# 3. 策略建议 (Legal Strategy)
# ============================================================
log("=== 3. 诉讼策略建议 ===")
try:
    strategy = llm_service.suggest_strategy(
        case_info={
            "title": case.title,
            "case_type": str(case.case_type) if case.case_type else "合同纠纷",
            "plaintiff": case.plaintiff,
            "defendant": case.defendant,
            "description": (case.description or "")[:5000],
        },
        evidence_count=len(evidence_items)
    )
    write_output("03_litigation_strategy.txt", strategy)
    log("策略建议完成")
except Exception as e:
    log(f"错误: {e}")

# ============================================================
# 4. 证据三性分析 (Evidence Three-Natures)
# ============================================================
log("=== 4. 证据三性分析 ===")
try:
    from app.services.evidence_three_natures import evidence_three_natures_service
    key_evidence = [ev for ev in evidence_items if ev.evidence_type in ["CONTRACT", "PAYMENT", "CORRESPONDENCE"]][:10]
    three_natures_results = []
    for ev in key_evidence:
        try:
            content = ev.extracted_content or ev.raw_content or ""
            result = evidence_three_natures_service.analyze_three_natures(
                evidence_name=ev.original_filename or "unknown",
                evidence_type=ev.evidence_type or "OTHER",
                content=content[:8000]
            )
            three_natures_results.append({
                "evidence": ev.original_filename,
                "type": ev.evidence_type,
                "analysis": result
            })
        except Exception as e2:
            three_natures_results.append({"evidence": ev.original_filename, "error": str(e2)})

    write_output("04_evidence_three_natures.json", json.dumps(three_natures_results, ensure_ascii=False, indent=2))
    log(f"三性分析完成: {len(three_natures_results)} 份证据")
except Exception as e:
    log(f"错误: {e}")

# ============================================================
# 5. 对抗分析 (Adversarial Analysis)
# ============================================================
log("=== 5. 对抗分析 ===")
try:
    opponent = llm_service.opponent_analysis(
        case_info={
            "title": case.title,
            "plaintiff": case.plaintiff,
            "defendant": case.defendant,
            "description": (case.description or "")[:5000],
        }
    )
    write_output("05_opponent_analysis.txt", opponent)
    log("对手分析完成")
except Exception as e:
    log(f"错误: {e}")

try:
    scenario = llm_service.scenario_prediction(
        case_info={"title": case.title, "description": (case.description or "")[:5000]},
    )
    write_output("05_scenario_prediction.txt", scenario)
    log("情景预测完成")
except Exception as e:
    log(f"错误: {e}")

# ============================================================
# 6. 出庭抗辩 (Hearing Defense)
# ============================================================
log("=== 6. 出庭抗辩分析 ===")
try:
    from app.services.defense_advisor import defense_advisor
    from app.services.trap_detector import trap_detector

    # 陷阱检测
    test_statements = [
        "你说你付了款，有证据吗？没有银行转账记录我们是不承认的。",
        "这笔钱到底是什么性质？是投资款还是借款？你说清楚。",
        "你作为公司总经理，难道不应该对公司亏损负责吗？",
    ]
    trap_results = []
    for stmt in test_statements:
        result = trap_detector.analyze_statement(stmt)
        trap_results.append({"statement": stmt, "analysis": result})

    write_output("06_trap_detection.json", json.dumps(trap_results, ensure_ascii=False, indent=2))
    log("陷阱检测完成")
except Exception as e:
    log(f"错误: {e}")

# ============================================================
# 7. 文书生成 (Document Generation)
# ============================================================
log("=== 7. 文书生成 ===")
try:
    from app.api.document import document_generator

    case_data = {
        "id": case.id,
        "title": case.title,
        "case_type": str(case.case_type) if case.case_type else "合同纠纷",
        "plaintiff": case.plaintiff,
        "defendant": case.defendant,
        "description": (case.description or "")[:5000],
        "supplement": case.supplement or "",
    }

    doc_types = ["起诉状", "代理词", "证据目录", "质证意见", "辩论提纲"]
    for dtype in doc_types:
        try:
            doc = document_generator.generate(document_type=dtype, case_data=case_data, db=db)
            filename = f"07_{dtype}.txt"
            write_output(filename, doc if doc else "(空)")
        except Exception as e2:
            log(f"  文书生成失败({dtype}): {e2}")

    log("文书生成完成")
except Exception as e:
    log(f"错误: {e}")

# ============================================================
# 8. 证据册导出 (Evidence Book)
# ============================================================
log("=== 8. 证据册生成 ===")
try:
    from app.services.evidence_system import EvidenceBookGenerator
    generator = EvidenceBookGenerator()
    book = generator.generate_book(case_id=CASE_ID, db=db, format="markdown")
    write_output("08_evidence_book.md", book)
    log("证据册生成完成")
except Exception as e:
    log(f"错误: {e}")

# ============================================================
# 9. 案件分析报告 (Case Analysis Report)
# ============================================================
log("=== 9. 综合分析报告 ===")
try:
    from app.services.llm_service import llm_service as ls

    all_evidence_summary = []
    for ev in evidence_items[:50]:
        content = (ev.extracted_content or ev.raw_content or "")[:1000]
        all_evidence_summary.append(f"    - {ev.original_filename} [{ev.evidence_type}]: {content[:200]}")

    report_prompt = f"""请作为资深执业律师，对该案件出具一份完整的《案件综合分析报告》。

案件基本信息：
- 案件名称：{case.title}
- 原告：{case.plaintiff}
- 被告：{case.defendant}
- 案件类型：{case.case_type}
- 案情描述：{(case.description or '')[:3000]}

已收集证据（共{len(evidence_items)}份）：
{chr(10).join(all_evidence_summary[:30])}

请按以下结构出具报告：
一、案件事实梳理
二、法律关系分析
三、证据综合评估
四、争议焦点预判
五、诉讼策略建议
六、风险提示与应对
七、结论与建议"""

    report = ls.chat([
        {"role": "system", "content": "你是一位有20年执业经验的资深律师。出具正式的法律分析报告。"},
        {"role": "user", "content": report_prompt}
    ])
    write_output("09_comprehensive_report.txt", report)
    log("综合分析报告完成")
except Exception as e:
    log(f"错误: {e}")

# ============================================================
# 10. 风险审查 (Risk Review)
# ============================================================
log("=== 10. 合同风险审查 ===")
try:
    from app.services.contract_risk_review import contract_risk_review_service
    contract_evidence = [ev for ev in evidence_items if ev.evidence_type == "CONTRACT"]
    if contract_evidence:
        content = contract_evidence[0].extracted_content or contract_evidence[0].raw_content or ""
        risk = contract_risk_review_service.review(content, case_id=CASE_ID, db=db)
        write_output("10_contract_risk_review.json", json.dumps(risk, ensure_ascii=False, indent=2))
        log("合同风险审查完成")
    else:
        log("无合同类证据，跳过")
except Exception as e:
    log(f"错误: {e}")

# ============================================================
# 11. 导出已生成的文书
# ============================================================
log("=== 11. 导出已有文书 ===")
docs = db.query(GeneratedDocument).filter(GeneratedDocument.case_id == CASE_ID).all()
for d in docs:
    try:
        fname = getattr(d, "title", None) or getattr(d, "filename", None) or f"doc_{d.id}"
        write_output(f"11_existing_{d.id}_{fname}.txt", d.content or "(空)")
    except Exception as e2:
        log(f"  导出失败: {e2}")

db.close()
log("=== 全部分析完成 ===")
print(f"\n所有输出文件保存在: {OUTPUT_DIR}/")
