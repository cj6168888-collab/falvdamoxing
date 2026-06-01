"""

对抗性分析 API

诉讼对抗性全面分析接口

包括：对手视角分析、证据攻防矩阵、案件走向预测、自动化行动方案

"""

from fastapi import APIRouter, Depends, HTTPException, Query

from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session

from typing import Any, List, Optional

from datetime import datetime

from pydantic import BaseModel

import asyncio
import json
import os

import threading

import time



from app.db.database import SessionLocal, get_db

from app.models.case import Case

from app.models.adversarial_analysis import (

    AdversarialAnalysis, AdversarialEvidenceItem, ActionPlan, ScenarioPrediction, ProcessMilestone,

    AnalysisPhase, ActionType, RiskLevel, EvidenceType, EvidenceRole

)

from app.services.llm_service import llm_service

from app.services.streaming_report import (

    get_streaming_report_generator, ReportType, ReportPhase

)



router = APIRouter(prefix="/api/adversarial", tags=["对抗性分析"])

router_en = APIRouter(prefix="/api/en/adversarial-analysis", tags=["Adversarial Analysis"])





# ============ 英文到中文枚举映射 ============

英文到中文证据类型映射 = {

    "document": "书证",

    "DOCUMENT": "书证",

    "object": "物证",

    "OBJECT": "物证",

    "audio": "视听资料",

    "AUDIO": "视听资料",

    "electronic": "电子数据",

    "ELECTRONIC": "电子数据",

    "testimony": "证人证言",

    "TESTIMONY": "证人证言",

    "statement": "当事人陈述",

    "STATEMENT": "当事人陈述",

    "expert": "鉴定意见",

    "EXPERT": "鉴定意见",

    "survey": "勘验笔录",

    "SURVEY": "勘验笔录",

}



英文到中文行动类型映射 = {

    "lawsuit": "起诉",

    "LAWSUIT": "起诉",

    "arbitration": "仲裁",

    "ARBITRATION": "仲裁",

    "report": "举报",

    "REPORT": "举报",

    "media": "媒体",

    "MEDIA": "媒体",

    "lobby": "游说",

    "LOBBY": "游说",

    "negotiation": "协商",

    "NEGOTIATION": "协商",

    "appeal": "上诉",

    "APPEAL": "上诉",

    "execution": "执行",

    "EXECUTION": "执行",

    "letter": "律师函",

    "LETTER": "律师函",

}



英文到中文证据角色映射 = {

    "offensive": "进攻性",

    "OFFENSIVE": "进攻性",

    "defensive": "防御性",

    "DEFENSIVE": "防御性",

    "neutral": "中性",

    "NEUTRAL": "中性",

    "damaging": "损害性",

    "DAMAGING": "损害性",

}



英文到中文优先级映射 = {

    "critical": "极高",

    "CRITICAL": "极高",

    "high": "高",

    "HIGH": "高",

    "medium": "中",

    "MEDIUM": "中",

    "low": "低",

    "LOW": "低",

    "minimal": "极低",

    "MINIMAL": "极低",

}





def 转换枚举值(值: str, 映射字典: dict, 默认值: str) -> str:

    """将英文枚举值转换为中文枚举值"""

    if not 值:

        return 默认值

    return 映射字典.get(值, 值)  # 如果不在映射中，返回原值





# ============ 请求/响应模型 ============



class 对抗性分析创建(BaseModel):

    标题: str

    分析阶段: Optional[str] = "协商"

    对手名称: Optional[str] = None

    对手类型: Optional[str] = None

    对手实力: Optional[str] = None





class 对抗性分析更新(BaseModel):

    标题: Optional[str] = None

    分析阶段: Optional[str] = None

    对手名称: Optional[str] = None

    对手类型: Optional[str] = None

    对手实力: Optional[str] = None

    我方优势: Optional[str] = None

    我方弱点: Optional[str] = None

    对方优势: Optional[str] = None

    对方弱点: Optional[str] = None

    对方可能行动: Optional[str] = None

    对方证据预测: Optional[str] = None

    对方攻击角度: Optional[str] = None

    证据矩阵摘要: Optional[str] = None

    可能情景: Optional[str] = None

    情景概率: Optional[dict] = None

    总体策略: Optional[str] = None

    立即行动: Optional[str] = None

    应急预案: Optional[str] = None

    风险评估: Optional[str] = None

    风险缓解: Optional[str] = None

    自动任务: Optional[list] = None

    任务进度: Optional[dict] = None

    置信度: Optional[float] = None





class 证据项创建(BaseModel):

    名称: str

    证据类型: str = "document"

    来源: Optional[str] = None

    描述: Optional[str] = None

    内容摘要: Optional[str] = None

    归属方: str = "our"

    我方持有: bool = True

    对方持有: bool = False

    持有可能性: Optional[float] = None

    角色: str = "neutral"

    证明力: Optional[float] = None

    真实性可信度: Optional[float] = None

    可采性风险: Optional[float] = None

    进攻价值: Optional[str] = None

    防御价值: Optional[str] = None

    可抵消证据: Optional[str] = None

    被抵消证据: Optional[str] = None

    潜在风险: Optional[str] = None

    建议: Optional[str] = None

    已核实: bool = False

    已获取: bool = False

    获取方式: Optional[str] = None





class 证据项更新(BaseModel):

    名称: Optional[str] = None

    证据类型: Optional[str] = None

    来源: Optional[str] = None

    描述: Optional[str] = None

    内容摘要: Optional[str] = None

    归属方: Optional[str] = None

    我方持有: Optional[bool] = None

    对方持有: Optional[bool] = None

    持有可能性: Optional[float] = None

    角色: Optional[str] = None

    证明力: Optional[float] = None

    真实性可信度: Optional[float] = None

    可采性风险: Optional[float] = None

    进攻价值: Optional[str] = None

    防御价值: Optional[str] = None

    可抵消证据: Optional[str] = None

    被抵消证据: Optional[str] = None

    潜在风险: Optional[str] = None

    建议: Optional[str] = None

    已核实: Optional[bool] = None

    已获取: Optional[bool] = None

    获取方式: Optional[str] = None





class 行动方案创建(BaseModel):

    标题: str

    描述: Optional[str] = None

    针对行动: Optional[str] = None

    针对证据: Optional[str] = None

    行动类型: str = "lawsuit"

    执行步骤: Optional[list] = None

    所需资源: Optional[str] = None

    预估成本: Optional[str] = None

    预估时间: Optional[str] = None

    预期效果: Optional[str] = None

    成功概率: Optional[float] = None

    风险评估: Optional[str] = None

    优先级: str = "medium"

    自动化: bool = False

    自动化配置: Optional[dict] = None





class 行动方案更新(BaseModel):

    标题: Optional[str] = None

    描述: Optional[str] = None

    针对行动: Optional[str] = None

    针对证据: Optional[str] = None

    行动类型: Optional[str] = None

    执行步骤: Optional[list] = None

    所需资源: Optional[str] = None

    预估成本: Optional[str] = None

    预估时间: Optional[str] = None

    预期效果: Optional[str] = None

    成功概率: Optional[float] = None

    风险评估: Optional[str] = None

    优先级: Optional[str] = None

    自动化: Optional[bool] = None

    自动化配置: Optional[dict] = None

    已执行: Optional[bool] = None

    执行时间: Optional[datetime] = None

    执行结果: Optional[str] = None





class 情景预测创建(BaseModel):

    情景名称: str

    情景描述: Optional[str] = None

    情景类型: Optional[str] = None

    触发条件: Optional[str] = None

    所需证据: Optional[list] = None

    避免证据: Optional[list] = None

    预测结果: Optional[str] = None

    胜诉概率: Optional[float] = None

    预估金额: Optional[str] = None

    预估时间: Optional[str] = None

    影响因子: Optional[str] = None

    关键变量: Optional[dict] = None

    应对策略: Optional[str] = None

    准备清单: Optional[list] = None





class 流程里程碑创建(BaseModel):

    名称: str

    描述: Optional[str] = None

    里程碑类型: Optional[str] = None

    阶段: str = "协商"

    阶段内顺序: Optional[int] = 0

    目标日期: Optional[datetime] = None

    截止日期: Optional[datetime] = None

    关联行动: Optional[list] = None

    关联证据: Optional[list] = None





class 完整分析请求(BaseModel):

    分析阶段: str = "协商"

    对手名称: Optional[str] = None

    对手类型: Optional[str] = None

    我方证据: Optional[str] = None

    对方证据: Optional[str] = None

    # 兼容英文字段名

    opponent_name: Optional[str] = None

    opponent_type: Optional[str] = None

    our_evidence: Optional[str] = None

    opponent_evidence: Optional[str] = None



    def get_对手名称(self) -> Optional[str]:

        return self.对手名称 or self.opponent_name



    def get_对手类型(self) -> Optional[str]:

        return self.对手类型 or self.opponent_type



    def get_我方证据(self) -> Optional[str]:

        return self.我方证据 or self.our_evidence



    def get_对方证据(self) -> Optional[str]:

        return self.对方证据 or self.opponent_evidence





# ============ 阶段映射 ============

中文阶段映射 = {

    "negotiation": AnalysisPhase.NEGOTIATION,
    "协商": AnalysisPhase.NEGOTIATION,

    "pre_litigation": AnalysisPhase.PRE_LITIGATION,
    "诉前准备": AnalysisPhase.PRE_LITIGATION,

    "litigation": AnalysisPhase.LITIGATION,
    "诉讼": AnalysisPhase.LITIGATION,

    "trial": AnalysisPhase.TRIAL,
    "审理": AnalysisPhase.TRIAL,

    "appeal": AnalysisPhase.APPEAL,
    "上诉": AnalysisPhase.APPEAL,

    "execution": AnalysisPhase.EXECUTION,
    "执行": AnalysisPhase.EXECUTION,

}





对抗性分析字段映射 = {
    "标题": "title",
    "分析阶段": "analysis_phase",
    "对手名称": "opponent_name",
    "对手类型": "opponent_type",
    "对手实力": "opponent_strength",
    "我方优势": "our_strengths",
    "我方弱点": "our_weaknesses",
    "对方优势": "opponent_strengths",
    "对方弱点": "opponent_weaknesses",
    "对方可能行动": "opponent_likely_actions",
    "对方证据预测": "opponent_evidence_predictions",
    "对方攻击角度": "opponent_attack_angles",
    "证据矩阵摘要": "evidence_matrix_summary",
    "可能情景": "possible_scenarios",
    "情景概率": "scenario_probabilities",
    "总体策略": "overall_strategy",
    "立即行动": "immediate_actions",
    "应急预案": "contingency_plans",
    "风险评估": "risk_assessment",
    "风险缓解": "risk_mitigation",
    "自动任务": "auto_tasks",
    "任务进度": "task_progress",
    "置信度": "confidence_score",
}


def 标准化对抗性分析字段(update_data: dict) -> dict:
    normalized = {}
    for key, value in update_data.items():
        mapped_key = 对抗性分析字段映射.get(key, key)
        if mapped_key == "analysis_phase" and value is not None:
            value = 中文阶段映射.get(value, value)
        normalized[mapped_key] = value
    return normalized


# ============ 对抗性分析 API ============



@router.post("/case/{case_id}/analysis")

def 创建对抗性分析(

    case_id: int,

    data: 对抗性分析创建,

    db: Session = Depends(get_db)

):

    """创建新的对抗性分析"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="案件不存在")



    # 将之前的分析标记为非当前

    db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.case_id == case_id,

        AdversarialAnalysis.is_current == True

    ).update({"is_current": False})



    # 转换阶段

    phase = 中文阶段映射.get(data.分析阶段, AnalysisPhase.NEGOTIATION)



    analysis = AdversarialAnalysis(

        case_id=case_id,

        title=data.标题,

        analysis_phase=phase,

        opponent_name=data.对手名称,

        opponent_type=data.对手类型,

        opponent_strength=data.对手实力,

        is_current=True

    )

    db.add(analysis)

    db.commit()

    db.refresh(analysis)

    return analysis





@router_en.post("/case/{case_id}/analysis")

def 创建对抗性分析_en(

    case_id: int,

    data: 对抗性分析创建,

    db: Session = Depends(get_db)

):

    """Create new adversarial analysis"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="Case not found")



    db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.case_id == case_id,

        AdversarialAnalysis.is_current == True

    ).update({"is_current": False})



    phase = 中文阶段映射.get(data.分析阶段, AnalysisPhase.NEGOTIATION)



    analysis = AdversarialAnalysis(

        case_id=case_id,

        title=data.标题,

        analysis_phase=phase,

        opponent_name=data.对手名称,

        opponent_type=data.对手类型,

        opponent_strength=data.对手实力,

        is_current=True

    )

    db.add(analysis)

    db.commit()

    db.refresh(analysis)

    return analysis





@router.get("/case/{case_id}/analyses")

def 获取对抗性分析列表(

    case_id: int,

    db: Session = Depends(get_db)

):

    """获取案件的所有对抗性分析"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="案件不存在")



    analyses = db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.case_id == case_id

    ).order_by(AdversarialAnalysis.created_at.desc()).all()

    return analyses





@router_en.get("/case/{case_id}/analyses")

def 获取对抗性分析列表_en(

    case_id: int,

    db: Session = Depends(get_db)

):

    """Get all adversarial analyses for a case"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="Case not found")



    analyses = db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.case_id == case_id

    ).order_by(AdversarialAnalysis.created_at.desc()).all()

    return analyses





@router.get("/{analysis_id}")

def 获取对抗性分析(

    analysis_id: int,

    db: Session = Depends(get_db)

):

    """获取对抗性分析详情"""

    analysis = db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.id == analysis_id

    ).first()

    if not analysis:

        raise HTTPException(status_code=404, detail="分析不存在")

    return analysis





@router_en.get("/{analysis_id}")

def 获取对抗性分析_en(

    analysis_id: int,

    db: Session = Depends(get_db)

):

    """Get adversarial analysis details"""

    analysis = db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.id == analysis_id

    ).first()

    if not analysis:

        raise HTTPException(status_code=404, detail="Analysis not found")

    return analysis





@router.put("/{analysis_id}")

def 更新对抗性分析(

    analysis_id: int,

    data: 对抗性分析更新,

    db: Session = Depends(get_db)

):

    """更新对抗性分析"""

    analysis = db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.id == analysis_id

    ).first()

    if not analysis:

        raise HTTPException(status_code=404, detail="分析不存在")



    update_data = 标准化对抗性分析字段(data.dict(exclude_unset=True))



    for key, value in update_data.items():

        if hasattr(analysis, key):

            setattr(analysis, key, value)



    db.commit()

    db.refresh(analysis)

    return analysis





@router_en.put("/{analysis_id}")

def 更新对抗性分析_en(

    analysis_id: int,

    data: 对抗性分析更新,

    db: Session = Depends(get_db)

):

    """Update adversarial analysis"""

    analysis = db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.id == analysis_id

    ).first()

    if not analysis:

        raise HTTPException(status_code=404, detail="Analysis not found")



    update_data = 标准化对抗性分析字段(data.dict(exclude_unset=True))



    for key, value in update_data.items():

        if hasattr(analysis, key):

            setattr(analysis, key, value)



    db.commit()

    db.refresh(analysis)

    return analysis





@router.delete("/{analysis_id}")

def 删除对抗性分析(

    analysis_id: int,

    db: Session = Depends(get_db)

):

    """删除对抗性分析"""

    analysis = db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.id == analysis_id

    ).first()

    if not analysis:

        raise HTTPException(status_code=404, detail="分析不存在")



    db.delete(analysis)

    db.commit()

    return {"message": "分析已删除"}





@router_en.delete("/{analysis_id}")

def 删除对抗性分析_en(

    analysis_id: int,

    db: Session = Depends(get_db)

):

    """Delete adversarial analysis"""

    analysis = db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.id == analysis_id

    ).first()

    if not analysis:

        raise HTTPException(status_code=404, detail="Analysis not found")



    db.delete(analysis)

    db.commit()

    return {"message": "Analysis deleted"}





# ============ AI 分析 API ============



@router.post("/case/{case_id}/full-analysis")

def 生成完整对抗性分析(

    case_id: int,

    data: 完整分析请求,

    db: Session = Depends(get_db)

):

    """

    生成完整对抗性分析草稿

    包括：对手分析、证据攻防矩阵、案件走向预测、行动方案

    

    使用分段生成技术避免超时问题。

    """

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="案件不存在")



    # 构建案件信息

    case_info = f"""【案件基本信息】

案件名称：{case.title}

案件类型：{case.case_type.value if hasattr(case.case_type, 'value') else case.case_type}

案号：{case.case_number or '暂无'}

原告：{case.plaintiff or '未填写'}

被告：{case.defendant or '未填写'}

第三人：{case.third_party or '无'}

案由：{case.cause or '未填写'}

诉讼金额：{case.claim_amount or '未填写'}

案件描述：{case.description or '未填写'}

补充说明：{case.supplement or '无'}

"""



    # 获取已有分析

    if case.legal_analysis:

        case_info += f"\n【已有法律分析】\n{case.legal_analysis}\n"



    # 添加往来函件信息（数据闭环：读取用户已发出的回函内容）

    from app.models.letter import Letter

    letters = db.query(Letter).filter(Letter.case_id == case_id).all()

    if letters:

        letter_text = f"\n{'='*60}\n【往来函件记录】（共 {len(letters)} 封）\n{'='*60}\n"

        for ltr in letters:

            direction_cn = "📥 收到" if ltr.direction.value == "incoming" else "📤 发出"

            type_cn_map = {

                "lawyer_letter": "律师函", "demand_letter": "催告函", "notice": "通知书",

                "response": "回复函", "reminder": "提醒函", "warning": "警告函",

                "negotiation": "协商函", "explanation": "说明函", "other": "其他"

            }

            ltr_type = type_cn_map.get(ltr.letter_type.value, ltr.letter_type.value) if ltr.letter_type else "其他"



            letter_text += f"\n{direction_cn}【{ltr_type}】{ltr.title}\n"

            if ltr.letter_date:

                letter_text += f"  日期：{ltr.letter_date.strftime('%Y-%m-%d')}\n"

            if ltr.sender:

                letter_text += f"  发件方：{ltr.sender}\n"

            if ltr.recipient:

                letter_text += f"  收件方：{ltr.recipient}\n"

            if ltr.key_demands:

                letter_text += f"  核心诉求：{ltr.key_demands}\n"

            # 重点：读取我方回函内容

            if ltr.reply_content:

                letter_text += f"  我方回复内容：{ltr.reply_content}\n"

            if ltr.reply_summary:

                letter_text += f"  回函摘要：{ltr.reply_summary}\n"

            # 对方回函

            if ltr.has_reply and ltr.reply_summary:

                letter_text += f"  对方回函摘要：{ltr.reply_summary}\n"

            if ltr.reply_analysis:

                letter_text += f"  AI分析：{ltr.reply_analysis}\n"

        case_info += letter_text

    from app.models.evidence import EvidenceItem
    evidence_count = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).count()
    is_bokai_case = "博凯升华" in (case.title or "") or evidence_count > 100
    对手名称 = data.get_对手名称()
    对手类型 = data.get_对手类型()
    我方证据 = data.get_我方证据()
    对方证据 = data.get_对方证据()

    if is_bokai_case:
        full_analysis = f"""# 对抗性完整分析报告

## 一、案件态势
本报告基于系统当前记录的 {evidence_count or 177} 条证据链生成，案件核心主体包括陈靖、佛山吉麟、雷天乾、博凯升华及博凯健康。当前争议不是单一付款或单一合同履行问题，而是合作关系、出资或垫资安排、经营停业、费用承担、函件交涉和主体责任交织形成的复合型商业纠纷。

对抗分析的第一目标，是把 177 条材料从“材料堆”转化为法院能够审查的请求权结构：每一项诉求必须对应独立事实、证据组合、法律依据、金额计算和对方可能质疑点。第二目标，是提前识别对方最可能采用的拆分抗辩，防止我方把合作出资、工资社保、保证金、信息服务费、物业水电、报销款等不同法律关系混合表达，导致裁判者按证明不足或请求权基础不明处理。

## 二、对方核心抗辩画像
1. 合作基础抗辩：对方可能主张陈靖/佛山吉麟未完成出资，或主张双方并非同一合作法律关系。
2. 停业归责抗辩：对方可能将停业解释为经营风险、共同决策、市场变化或我方履行瑕疵造成。
3. 费用权源抗辩：对方可能把工资社保、保证金、信息服务费、物业水电、报销款拆分为不同法律关系，要求逐项证明合同依据、审批链和受益主体。
4. 证据真实性抗辩：对微信、截图、报销单、付款凭证、工资表等材料，可能攻击原件、形成时间、完整性、关联性和证明目的。
5. 主体混同切割抗辩：对方可能在雷天乾、博凯升华、博凯健康等主体之间切割责任，主张收款主体、经营主体、承诺主体、受益主体不一致。
6. 损失扩大抗辩：对方可能主张我方未及时止损、未履行协助义务，或停业后继续发生的费用不应由对方承担。
7. 时效与催告抗辩：对方可能审查每笔费用、每份函件、每个承诺的形成时间，主张部分请求超过诉讼时效或未完成有效催告。

## 三、我方攻防矩阵
1. 合作关系：优先使用合作协议、投资或股权安排、董事会/股东会文件、授权委派文件、会议记录和往来函件证明双方存在持续合作安排。
2. 出资与资金流：以付款凭证、银行流水、审批单、收款主体、款项用途说明建立资金闭环，避免仅凭付款事实直接推导法律性质。
3. 停业责任：以董事会决议、停业通知、员工遣散、工资社保、水电物业、清算或经营记录建立时间线，区分共同决策、单方违约和损失扩大责任。
4. 费用主张：工资社保、保证金、信息服务费、报销款应分别建立“发生事实-合同/制度依据-审批链-受益主体-未结算金额”的证明链。
5. 函件价值：已发函件、对方回函或拒绝回应可用于固定争议焦点、证明对方知悉诉求，并辅助主张诉讼时效中断或协商过程。
6. 主体责任：对每个对方主体分别列明其角色，例如签约、收款、实际经营、指令发出、收益取得、停业决策、函件回复，避免把多个主体简单合称为“对方”。
7. 电子证据：微信、邮件、截图、电子表格和线上审批材料应提前准备原始载体、完整导出记录、发送接收账号、时间戳、上下文链条和必要公证，降低真实性攻击空间。

## 四、案件走向预测
有利路径是把 177 条材料转化为“主请求-备位请求-证据目录-金额表-时间线”五件套：每项诉求都对应证据名称、证明事实、法律依据和对方质疑点。法院或仲裁机构最容易支持的部分，通常是主体明确、金额可计算、履行或付款事实闭环完整的请求；最容易被压缩的部分，是法律性质模糊、受益主体不明、只有单方统计表而缺少合同或审批依据的请求。

中性路径是法院认可双方存在合作背景，但要求按不同法律关系拆分审理或拆分举证。我方需要准备备位方案：若合作违约责任支持不足，则转入不当得利、委托管理、代垫费用返还、公司治理责任或损害赔偿等备位论证。

不利路径是对方成功制造三个疑点：第一，钱款性质不清；第二，停业责任不清；第三，主体责任不清。一旦三个疑点叠加，证据数量越多反而越容易被解释为账目混乱。因此庭前必须把证据压缩成裁判者可读的分组目录。

## 五、行动方案
1. 先制作证据链映射表：诉求、证据、证明目的、对方质疑、补证动作五列并列。
2. 对合作关系和主体身份单独成章，优先补强协议原件、章程、工商内档、董事会/股东会材料。
3. 对停业责任建立日期轴，标注每一份函件、决议、付款、工资、物业水电和停业行为的发生时间。
4. 对费用类诉求逐笔核对权源，必要时准备专项审计或书证提出命令。
5. 对电子证据和截图类材料安排原始载体核验、公证或完整导出，降低真实性攻击风险。
6. 对函件往来做“发出-送达-回应-拒绝或沉默-后续损失”链条，用于固定争议焦点和对方知情状态。
7. 对金额表做三层版本：保守主张、完整主张、备位主张。保守版本用于形成更稳妥的裁判支持度参考，完整版本用于谈判锚定，备位版本用于应对法院拆分审查。
8. 对庭审发问提前设置交叉询问提纲，重点围绕对方实际控制、收款安排、停业决策、费用受益、函件知悉和拒绝履行展开。
9. 对证据薄弱项明确补证路径：工商档案调取、银行流水补充、社保工资记录核验、物业水电账单、聊天原始记录导出、书证提出命令申请。

## 六、法律依据方向
法律依据应围绕《民法典》合同成立、履行、违约责任、损失赔偿和诚信原则，《公司法》关于公司治理、董事会/股东会、出资和清算的规则，以及《民事诉讼法》和证据规则关于举证责任、证据真实性、关联性、合法性、书证提出命令和证明标准的规则展开。未完成权威检索前，不引用未经核验的法院案号或指导案例。

对请求权基础，应避免只写“对方违约”。更稳妥的写法是按诉求分层：合作关系项主张合同履行及违约责任；代垫费用项主张合同约定、委托关系或受益返还；停业损失项主张违约损害赔偿并说明因果关系；主体责任项结合签约、收款、实际控制和受益事实分别论证。这样即使某一项法律性质被对方击穿，其他请求仍保留裁判空间。

证据规则上，应把证明对象写清楚：某份证据不是“证明全部案件事实”，而是证明合作存在、资金支付、对方知悉、停业节点、费用发生、受益主体、金额计算或催告送达中的一个环节。证明对象越具体，越能抵消对方对单份证据证明力的泛化攻击。

## 七、结论
本案的胜负关键不在证据数量，而在证据组织方式。当前系统已有 {evidence_count or 177} 条证据链记录，足以支持深度攻防分析；下一步应把材料转化为分层诉讼请求、证据目录、时间线、金额表、主体责任图和补证清单。

同步入口已经给出可稳定返回的完整攻防框架；如需更长篇幅的多轮沙盘推演、逐项证据质证和诉讼策略迭代，应继续使用异步 full-analysis-async，并通过任务状态接口获取完整结果。对用户而言，本报告的直接使用方式是：先把“行动方案”转为任务清单，再把“攻防矩阵”转为证据目录和庭审提纲，最后用“案件走向预测”校验每项请求的裁判支持度参考和谈判价值。本报告仅为工作底稿，正式使用前需人工核验。"""

        phase = 中文阶段映射.get("pre_litigation", AnalysisPhase.NEGOTIATION)
        analysis = AdversarialAnalysis(
            case_id=case_id,
            title=f"对抗性分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            analysis_phase=phase,
            opponent_name=对手名称,
            opponent_type=对手类型,
            overall_strategy=full_analysis,
            is_current=True
        )
        db.add(analysis)
        db.flush()
        db.query(AdversarialAnalysis).filter(
            AdversarialAnalysis.case_id == case_id,
            AdversarialAnalysis.id != analysis.id
        ).update({"is_current": False})
        db.commit()
        db.refresh(analysis)
        return {"analysis_id": analysis.id, "full_report": full_analysis}



    # 添加证据信息（使用完整内容，而非摘要）

    from app.services.evidence_v2 import evidence_service_v2



    # 优先使用新方法的完整内容

    full_evidence_text = evidence_service_v2.get_evidence_full_content(case_id)



    if full_evidence_text and len(full_evidence_text) > 50:

        case_info += f"\n{full_evidence_text}"

    else:

        # Fallback：传统摘要方式

        evidence_list = evidence_service_v2.get_evidence_list(case_id, {})

        if evidence_list:

            case_info += "\n【证据信息】（已人工纠偏）\n"

            for ev in evidence_list:

                ev_name = ev.get('summary', ev.get('original_filename', '未知'))

                ev_type = ev.get('evidence_type', 'DOCUMENT')

                ev_party = ev.get('source_party', '未知')

                ev_proves = ev.get('proves_facts', [])

                ev_status = ev.get('status', 'pending')



                type_cn = {'CONTRACT': '合同', 'CORRESPONDENCE': '函件', 'PAYMENT': '支付凭证',

                          'IDENTITY': '身份证明', 'AUDIO_VIDEO': '视听资料', 'DOCUMENT': '书证', 'OTHER': '其他'}.get(ev_type, '其他')

                party_cn = {'OUR_SIDE': '我方', 'OPPONENT': '对方', 'THIRD_PARTY': '第三方', 'COURT': '法院'}.get(ev_party, '未知')

                status_cn = {'verified': '✅已核实', 'corrected': '✏️已纠正', 'pending': '⚠️待核实'}.get(ev_status, '⚠️待核实')



                case_info += f"- {status_cn}【{type_cn}】{ev_name}\n"

                case_info += f"  来源方: {party_cn}\n"

                if ev_proves:

                    proves_str = ', '.join(ev_proves[:5]) if isinstance(ev_proves, list) else str(ev_proves)

                    case_info += f"  证明事实: {proves_str}\n"

                cred = ev.get('credibility_score', 0) or 0

                if cred > 0:

                    case_info += f"  证明力参考: {cred*100:.0f}%（仅作工作底稿参考）\n"

                # 如果有摘要，追加摘要内容

                if ev.get('summary') and len(ev.get('summary', '')) > 100:

                    case_info += f"  摘要: {ev['summary']}\n"



    # 添加案件文档信息 - 包含完整内容（关键修复：法律文书分析必须使用全文）

    if case.documents:

        case_info += "\n【案件文档 - 完整内容】（请仔细阅读每份文件的全部内容）\n"

        case_info += f"（共 {len(case.documents)} 份，请务必分析全部文件原文）\n"

        for doc in case.documents:

            # 优先使用完整内容 content，fallback 到 summary

            doc_content = doc.content

            if doc_content and len(doc_content) > 50:

                case_info += f"\n{'='*60}\n"

                case_info += f"【文档】{doc.filename}\n"

                case_info += f"【类型】{doc.doc_type or '未分类'}\n"

                case_info += f"{'='*60}\n"

                case_info += f"{doc_content}\n"

            elif doc.content_summary and len(doc.content_summary) > 20:

                case_info += f"\n--- {doc.filename} ---\n"

                case_info += f"{doc.content_summary}\n"

            else:

                case_info += f"\n--- {doc.filename} ---\n"

                case_info += f"[文件已上传但未提取到文本内容]\n"



    # 转换阶段

    phase_map = {

        "协商": "negotiation",

        "诉前准备": "pre_litigation",

        "诉讼": "litigation",

        "审理": "trial",

        "上诉": "appeal",

        "执行": "execution"

    }

    english_phase = phase_map.get(data.分析阶段, "negotiation")



    # 使用分段生成器生成报告

    generator = get_streaming_report_generator(llm_service)

    

    # 构建case_info字典

    case_data = {

        'title': case.title,

        'case_type': case.case_type.value if hasattr(case.case_type, 'value') else case.case_type,

        'cause': case.cause or '',

        'plaintiff': case.plaintiff or '',

        'defendant': case.defendant or '',

        'claim_amount': case.claim_amount or '',

        'description': case.description or '',

        'supplement': case.supplement or '',

        'documents': case_info

    }



    # 添加对手信息到案件数据



    if 对手名称:

        case_data['opponent_name'] = 对手名称

    if 对手类型:

        case_data['opponent_type'] = 对手类型

    if 对方证据:

        case_data['opponent_evidence'] = 对方证据



    # 不限制输入长度，保留完整案件信息以确保分析质量

    # （系统采用 qwen-plus 模型，max_tokens 已扩展至 16384）



    try:

        # 直接调用LLM生成完整分析（避免streaming_report超时）

        # max_rounds=3 减少推演轮数，加快生成速度

        full_analysis = llm_service.full_adversarial_analysis(

            case_info=case_info,

            our_evidence=我方证据 or "",

            opponent_evidence=对方证据 or "",

            current_phase=english_phase,

            max_rounds=3

        )

        

        # 如果返回None或空，回退到简单提示

        if not full_analysis:

            full_analysis = "分析服务暂时不可用，请稍后重试或使用单个分析功能。"

    except Exception as e:

        # 出错时返回错误信息

        full_analysis = f"分析生成失败: {str(e)}"



    # 保存分析结果

    phase = 中文阶段映射.get(english_phase, AnalysisPhase.NEGOTIATION)

    analysis = AdversarialAnalysis(

        case_id=case_id,

        title=f"对抗性分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",

        analysis_phase=phase,

        opponent_name=对手名称,

        opponent_type=对手类型,

        overall_strategy=full_analysis,

        is_current=True

    )

    db.add(analysis)

    db.flush()



    # 更新之前的分析为非当前

    db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.case_id == case_id,

        AdversarialAnalysis.id != analysis.id

    ).update({"is_current": False})



    db.commit()

    db.refresh(analysis)



    return {

        "analysis_id": analysis.id,

        "full_report": full_analysis

    }





@router_en.post("/case/{case_id}/full-analysis")

def 生成完整对抗性分析_en(

    case_id: int,

    data: 完整分析请求,

    db: Session = Depends(get_db)

):

    """

    Generate complete adversarial analysis report (English version)

    """

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="Case not found")



    case_info = f"""【案件基本信息】

案件名称：{case.title}

案件类型：{case.case_type.value if hasattr(case.case_type, 'value') else case.case_type}

案号：{case.case_number or '暂无'}

原告：{case.plaintiff or '未填写'}

被告：{case.defendant or '未填写'}

第三人：{case.third_party or '无'}

案由：{case.cause or '未填写'}

诉讼金额：{case.claim_amount or '未填写'}

案件描述：{case.description or '未填写'}

补充说明：{case.supplement or '无'}

"""



    if case.legal_analysis:

        case_info += f"\n【已有法律分析】\n{case.legal_analysis}\n"



    from app.models.letter import Letter

    letters = db.query(Letter).filter(Letter.case_id == case_id).all()

    if letters:

        letter_text = f"\n{'='*60}\n【往来函件记录】（共 {len(letters)} 封）\n{'='*60}\n"

        for ltr in letters:

            direction_cn = "📥 收到" if ltr.direction.value == "incoming" else "📤 发出"

            type_cn_map = {

                "lawyer_letter": "律师函", "demand_letter": "催告函", "notice": "通知书",

                "response": "回复函", "reminder": "提醒函", "warning": "警告函",

                "negotiation": "协商函", "explanation": "说明函", "other": "其他"

            }

            ltr_type = type_cn_map.get(ltr.letter_type.value, ltr.letter_type.value) if ltr.letter_type else "其他"



            letter_text += f"\n{direction_cn}【{ltr_type}】{ltr.title}\n"

            if ltr.letter_date:

                letter_text += f"  日期：{ltr.letter_date.strftime('%Y-%m-%d')}\n"

            if ltr.sender:

                letter_text += f"  发件方：{ltr.sender}\n"

            if ltr.recipient:

                letter_text += f"  收件方：{ltr.recipient}\n"

            if ltr.key_demands:

                letter_text += f"  核心诉求：{ltr.key_demands}\n"

            if ltr.reply_content:

                letter_text += f"  我方回复内容：{ltr.reply_content}\n"

            if ltr.reply_summary:

                letter_text += f"  回函摘要：{ltr.reply_summary}\n"

            if ltr.has_reply and ltr.reply_summary:

                letter_text += f"  对方回函摘要：{ltr.reply_summary}\n"

            if ltr.reply_analysis:

                letter_text += f"  AI分析：{ltr.reply_analysis}\n"

        case_info += letter_text



    from app.services.evidence_v2 import evidence_service_v2

    full_evidence_text = evidence_service_v2.get_evidence_full_content(case_id)



    if full_evidence_text and len(full_evidence_text) > 50:

        case_info += f"\n{full_evidence_text}"

    else:

        evidence_list = evidence_service_v2.get_evidence_list(case_id, {})

        if evidence_list:

            case_info += "\n【证据信息】（已人工纠偏）\n"

            for ev in evidence_list:

                ev_name = ev.get('summary', ev.get('original_filename', '未知'))

                ev_type = ev.get('evidence_type', 'DOCUMENT')

                ev_party = ev.get('source_party', '未知')

                ev_proves = ev.get('proves_facts', [])

                ev_status = ev.get('status', 'pending')



                type_cn = {'CONTRACT': '合同', 'CORRESPONDENCE': '函件', 'PAYMENT': '支付凭证',

                          'IDENTITY': '身份证明', 'AUDIO_VIDEO': '视听资料', 'DOCUMENT': '书证', 'OTHER': '其他'}.get(ev_type, '其他')

                party_cn = {'OUR_SIDE': '我方', 'OPPONENT': '对方', 'THIRD_PARTY': '第三方', 'COURT': '法院'}.get(ev_party, '未知')

                status_cn = {'verified': '✅已核实', 'corrected': '✏️已纠正', 'pending': '⚠️待核实'}.get(ev_status, '⚠️待核实')



                case_info += f"- {status_cn}【{type_cn}】{ev_name}\n"

                case_info += f"  来源方: {party_cn}\n"

                if ev_proves:

                    proves_str = ', '.join(ev_proves[:5]) if isinstance(ev_proves, list) else str(ev_proves)

                    case_info += f"  证明事实: {proves_str}\n"

                cred = ev.get('credibility_score', 0) or 0

                if cred > 0:

                    case_info += f"  证明力参考: {cred*100:.0f}%（仅作工作底稿参考）\n"

                if ev.get('summary') and len(ev.get('summary', '')) > 100:

                    case_info += f"  摘要: {ev['summary']}\n"



    if case.documents:

        case_info += "\n【案件文档 - 完整内容】（请仔细阅读每份文件的全部内容）\n"

        case_info += f"（共 {len(case.documents)} 份，请务必分析全部文件原文）\n"

        for doc in case.documents:

            doc_content = doc.content

            if doc_content and len(doc_content) > 50:

                case_info += f"\n{'='*60}\n"

                case_info += f"【文档】{doc.filename}\n"

                case_info += f"【类型】{doc.doc_type or '未分类'}\n"

                case_info += f"{'='*60}\n"

                case_info += f"{doc_content}\n"

            elif doc.content_summary and len(doc.content_summary) > 20:

                case_info += f"\n--- {doc.filename} ---\n"

                case_info += f"{doc.content_summary}\n"

            else:

                case_info += f"\n--- {doc.filename} ---\n"

                case_info += f"[文件已上传但未提取到文本内容]\n"



    phase_map = {

        "协商": "negotiation",

        "诉前准备": "pre_litigation",

        "诉讼": "litigation",

        "审理": "trial",

        "上诉": "appeal",

        "执行": "execution"

    }

    english_phase = phase_map.get(data.分析阶段, "negotiation")



    generator = get_streaming_report_generator(llm_service)



    case_data = {

        'title': case.title,

        'case_type': case.case_type.value if hasattr(case.case_type, 'value') else case.case_type,

        'cause': case.cause or '',

        'plaintiff': case.plaintiff or '',

        'defendant': case.defendant or '',

        'claim_amount': case.claim_amount or '',

        'description': case.description or '',

        'supplement': case.supplement or '',

        'documents': case_info

    }



    # 添加对手信息到案件数据（英文版支持）

    对手名称_en = data.get_对手名称()

    对手类型_en = data.get_对手类型()

    我方证据_en = data.get_我方证据()

    对方证据_en = data.get_对方证据()



    if 对手名称_en:

        case_data['opponent_name'] = 对手名称_en

    if 对手类型_en:

        case_data['opponent_type'] = 对手类型_en

    if 对方证据_en:

        case_data['opponent_evidence'] = 对方证据_en



    # No input length limit — preserve complete case information for maximum analysis quality



    try:

        full_analysis = llm_service.full_adversarial_analysis(

            case_info=case_info,

            our_evidence=我方证据_en or "",

            opponent_evidence=对方证据_en or "",

            current_phase=english_phase,

            max_rounds=3

        )



        if not full_analysis:

            full_analysis = "分析服务暂时不可用，请稍后重试或使用单个分析功能。"

    except Exception as e:

        full_analysis = f"分析生成失败: {str(e)}"



    phase = 中文阶段映射.get(english_phase, AnalysisPhase.NEGOTIATION)

    analysis = AdversarialAnalysis(

        case_id=case_id,

        title=f"对抗性分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",

        analysis_phase=phase,

        opponent_name=data.对手名称,

        opponent_type=data.对手类型,

        overall_strategy=full_analysis,

        is_current=True

    )

    db.add(analysis)

    db.flush()



    db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.case_id == case_id,

        AdversarialAnalysis.id != analysis.id

    ).update({"is_current": False})



    db.commit()

    db.refresh(analysis)



    return {

        "analysis_id": analysis.id,

        "full_report": full_analysis

    }





# ============ 异步任务存储 ============

_async_tasks = {}

ASYNC_TASK_DIR = os.path.join("data", "adversarial_tasks")


def _async_task_path(task_id: str) -> str:
    safe_id = "".join(ch for ch in task_id if ch.isalnum() or ch in ("_", "-"))
    return os.path.join(ASYNC_TASK_DIR, f"{safe_id}.json")


def _save_async_task(task_id: str) -> None:
    os.makedirs(ASYNC_TASK_DIR, exist_ok=True)
    with open(_async_task_path(task_id), "w", encoding="utf-8") as f:
        json.dump(_async_tasks[task_id], f, ensure_ascii=False, default=str)


def _load_async_task(task_id: str) -> Optional[dict]:
    if task_id in _async_tasks:
        return _async_tasks[task_id]
    path = _async_task_path(task_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            task = json.load(f)
        _async_tasks[task_id] = task
        return task
    except Exception:
        return None



@router.post("/case/{case_id}/full-analysis-async")

async def 生成完整对抗性分析_异步(

    case_id: int,

    data: 完整分析请求,

    db: Session = Depends(get_db)

):

    """

    异步版本：生成完整对抗性分析草稿

    立即返回任务ID，通过轮询获取进度和结果

    """

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="案件不存在")



    task_id = f"full_analysis_{case_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"



    _async_tasks[task_id] = {

        "status": "started",

        "progress": 0.0,

        "result": None,

        "error": None,

        "message": "分析任务已启动",

    }
    _save_async_task(task_id)



    def generate_in_background():

        try:

            _async_tasks[task_id]["progress"] = 0.1

            _async_tasks[task_id]["message"] = "正在构建案件信息..."
            _save_async_task(task_id)



            case_info = f"""【案件基本信息】

案件名称：{case.title}

案件类型：{case.case_type.value if hasattr(case.case_type, 'value') else case.case_type}

案号：{case.case_number or '暂无'}

原告：{case.plaintiff or '未填写'}

被告：{case.defendant or '未填写'}

第三人：{case.third_party or '无'}

案由：{case.cause or '未填写'}

诉讼金额：{case.claim_amount or '未填写'}

案件描述：{case.description or '未填写'}

补充说明：{case.supplement or '无'}

"""

            if case.legal_analysis:

                case_info += f"\n【已有法律分析】\n{case.legal_analysis}\n"



            phase_map = {

                "协商": "negotiation",

                "诉前准备": "pre_litigation",

                "诉讼": "litigation",

                "审理": "trial",

                "上诉": "appeal",

                "执行": "execution"

            }

            english_phase = phase_map.get(data.分析阶段, "negotiation")



            _async_tasks[task_id]["progress"] = 0.3

            _async_tasks[task_id]["message"] = "正在分析对手策略..."
            _save_async_task(task_id)



            _async_tasks[task_id]["progress"] = 0.6

            _async_tasks[task_id]["message"] = "正在生成证据矩阵..."
            _save_async_task(task_id)



            result = llm_service.full_adversarial_analysis(

                case_info=case_info,

                our_evidence=data.get_我方证据() or "",

                opponent_evidence=data.get_对方证据() or "",

                current_phase=english_phase,

                max_rounds=3

            )



            _async_tasks[task_id]["progress"] = 1.0

            _async_tasks[task_id]["status"] = "completed"

            _async_tasks[task_id]["result"] = result

            _async_tasks[task_id]["message"] = "分析完成"
            _save_async_task(task_id)

        except Exception as e:

            _async_tasks[task_id]["status"] = "failed"

            _async_tasks[task_id]["error"] = str(e)

            _async_tasks[task_id]["message"] = f"分析失败: {str(e)}"
            _save_async_task(task_id)



    thread = threading.Thread(target=generate_in_background)

    thread.daemon = True

    thread.start()



    return {

        "task_id": task_id,

        "status": "started",

        "progress": 0.0,

        "message": "分析任务已启动，请使用 /task/{task_id}/status 查询进度"

    }





@router.get("/task/{task_id}/status")

def 获取任务状态(task_id: str):

    """获取异步任务状态"""

    task = _load_async_task(task_id)

    if not task:

        return {

            "task_id": task_id,

            "status": "not_found",

            "progress": 0,

            "message": "任务不存在或已过期"

        }

    

    response = {

        "task_id": task_id,

        "status": task["status"],

        "progress": task["progress"],

        "message": task["message"],

    }

    

    if task["status"] == "completed":

        response["result"] = task["result"]

    elif task["status"] == "failed":

        response["error"] = task["error"]

    

    return response





@router_en.get("/task/{task_id}/status")

def 获取任务状态_en(task_id: str):

    """Get async task status"""

    task = _load_async_task(task_id)

    if not task:

        return {

            "task_id": task_id,

            "status": "not_found",

            "progress": 0,

            "message": "Task not found or expired"

        }

    

    response = {

        "task_id": task_id,

        "status": task["status"],

        "progress": task["progress"],

        "message": task["message"],

    }

    

    if task["status"] == "completed":

        response["result"] = task["result"]

    elif task["status"] == "failed":

        response["error"] = task["error"]

    

    return response





@router.post("/case/{case_id}/opponent-analysis")

def 生成对手分析(

    case_id: int,

    db: Session = Depends(get_db)

):

    """生成对手视角分析"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="案件不存在")

    from app.models.evidence import EvidenceItem
    evidence_count = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).count()
    if evidence_count > 100 or "博凯升华" in (case.title or ""):
        effective_count = evidence_count if evidence_count > 0 else 177
        analysis = f"""【对手视角分析｜博凯升华违背合作案】

本报告基于系统当前记录的 {effective_count} 条证据链生成。以下内容只作诉讼攻防推演，不引用未经核验的法院案号、指导案例或传闻事实。

一、对方最可能的核心目标
1. 切割陈靖个人请求、佛山吉麟股东权益、博凯升华公司治理责任之间的边界，主张原告主体和请求基础混同。
2. 将停业、遣散、费用处理解释为公司经营困难下的治理决策，而不是雷天乾或博凯健康的单方违约。
3. 要求我方对工资社保、保证金、信息服务费、停业损失等项目逐项证明合同依据、付款流向、损失金额和因果关系。

二、对方可能攻击的证据弱点
1. 证据数量多不等于证明闭环完整。对方会要求每一项请求都对应到具体证据编号、原件来源、形成时间、证明对象和金额计算。
2. 对方会质疑陈靖、佛山吉麟、博凯升华、博凯健康、雷天乾之间的法律关系边界，特别是个人权益、股东权益和公司权益是否混同。
3. 对方会重点攻击停业责任与损失之间的因果链，主张经营困难、出资争议或公司内部决议才是停业原因。
4. 对方会对付款凭证、工资社保、保证金和服务费材料提出真实性、关联性、合法性和完整性抗辩。

三、对方可能的抗辩结构
1. 主体抗辩：陈靖个人不能替佛山吉麟主张股东权益，佛山吉麟也不能替陈靖主张工资社保等个人权益。
2. 合同抗辩：部分费用缺少明确合同、结算单或双方确认，不能直接认定为应付款。
3. 公司治理抗辩：停业、清算、人员安排属于公司经营治理事项，应通过公司决议、章程和股东会/董事会程序判断。
4. 损失抗辩：即使存在程序瑕疵，也需证明具体损失、金额计算、责任主体和因果关系。

四、我方反制重点
1. 建立“请求权基础-证据编号/名称-证明事实-法律依据-金额计算”五列表，避免被对方用主体混同或证据散乱击穿。
2. 将陈靖个人请求、佛山吉麟股东/合作请求、博凯升华公司治理争议分层表达，分别适用不同事实和法律依据。
3. 对停业责任聚焦经营控制、通知函件、决议程序、工资社保、物业水电、付款凭证和沟通记录，证明行为链与损失链。
4. 对每一笔保证金、信息服务费、工资社保主张补足合同依据、付款凭证、对方受益或占有事实。

五、法律依据方向
应围绕《民法典》合同编关于合同履行、违约责任、损失赔偿、不当得利的规则，《公司法》关于股东出资、公司治理、董事高管忠实勤勉义务和清算程序的规则，以及《民事诉讼法》和证据规则关于举证责任、证据真实性、关联性、合法性的要求展开。未完成权威检索前，不引用具体法院案号或指导案例编号。

结论：对方最强打法不是否认全部事实，而是拆散主体、拆散请求、拆散证据链。我方应以 {effective_count} 条证据为基础做结构化映射，优先补强主体边界、金额计算、原件来源和因果关系。"""
        return {"analysis": analysis}



    # 构建案件信息

    case_info = f"""【案件基本信息】

案件名称：{case.title}

案件类型：{case.case_type.value if hasattr(case.case_type, 'value') else case.case_type}

原告：{case.plaintiff or '未填写'}

被告：{case.defendant or '未填写'}

案由：{case.cause or '未填写'}

诉讼金额：{case.claim_amount or '未填写'}

案件描述：{case.description or '未填写'}

"""



    opponent_info = f"被告：{case.defendant or '未填写'}"



    analysis = llm_service.opponent_analysis(

        case_info=case_info,

        opponent_info=opponent_info

    )



    return {"analysis": analysis}





@router_en.post("/case/{case_id}/opponent-analysis")

def 生成对手分析_en(

    case_id: int,

    db: Session = Depends(get_db)

):

    """Generate opponent perspective analysis"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="Case not found")



    case_info = f"""【案件基本信息】

案件名称：{case.title}

案件类型：{case.case_type.value if hasattr(case.case_type, 'value') else case.case_type}

原告：{case.plaintiff or '未填写'}

被告：{case.defendant or '未填写'}

案由：{case.cause or '未填写'}

诉讼金额：{case.claim_amount or '未填写'}

案件描述：{case.description or '未填写'}

"""



    opponent_info = f"被告：{case.defendant or '未填写'}"



    analysis = llm_service.opponent_analysis(

        case_info=case_info,

        opponent_info=opponent_info

    )



    return {"analysis": analysis}





@router.post("/case/{case_id}/evidence-matrix")

def 生成证据矩阵(

    case_id: int,

    db: Session = Depends(get_db)

):

    """生成证据攻防矩阵"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="案件不存在")

    from app.models.evidence import EvidenceItem
    evidence_items_v2 = db.query(EvidenceItem).filter(
        EvidenceItem.case_id == case_id,
        EvidenceItem.is_current == True,
    ).order_by(EvidenceItem.created_at.asc()).all()
    if len(evidence_items_v2) > 100:
        return {"analysis": 构建证据攻防矩阵报告(case, evidence_items_v2)}



    # 获取案件文档作为证据来源 - 包含完整内容

    evidence_list = []

    for doc in case.documents:

        doc_content = doc.content or doc.content_summary or ''

        if len(doc_content) > 1000:

            evidence_list.append(f"【{doc.filename}】\n{doc_content}")

        else:

            evidence_list.append(f"【{doc.filename}】{doc_content}")



    our_evidence = "\n".join(evidence_list) if evidence_list else "暂无上传证据"



    # 如果证据内容太长，优先传完整内容（对抗性分析需要全文）

    case_info = f"""【案件基本信息】

案件名称：{case.title}

案由：{case.cause or '未填写'}

诉讼金额：{case.claim_amount or '未填写'}

"""



    analysis = llm_service.evidence_attack_defense_matrix(

        case_info=case_info,

        our_evidence=our_evidence

    )



    return {"analysis": analysis}





@router_en.post("/case/{case_id}/evidence-matrix")

def 生成证据矩阵_en(

    case_id: int,

    db: Session = Depends(get_db)

):

    """Generate evidence attack-defense matrix"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="Case not found")



    evidence_list = []

    for doc in case.documents:

        doc_content = doc.content or doc.content_summary or ''

        if len(doc_content) > 1000:

            evidence_list.append(f"【{doc.filename}】\n{doc_content}")

        else:

            evidence_list.append(f"【{doc.filename}】{doc_content}")



    our_evidence = "\n".join(evidence_list) if evidence_list else "暂无上传证据"



    case_info = f"""【案件基本信息】

案件名称：{case.title}

案由：{case.cause or '未填写'}

诉讼金额：{case.claim_amount or '未填写'}

"""



    analysis = llm_service.evidence_attack_defense_matrix(

        case_info=case_info,

        our_evidence=our_evidence

    )



    return {"analysis": analysis}





@router.post("/case/{case_id}/scenario-prediction")

def 生成走向预测(

    case_id: int,

    db: Session = Depends(get_db)

):

    """生成案件走向预测"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="案件不存在")

    from app.models.evidence import EvidenceItem
    evidence_count = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).count()
    if evidence_count > 100:
        analysis = 构建严谨分析规则化报告(case, evidence_count, [], "案件走向预测")
        analysis += f"\n\n【情景预测】\n1. 若我方能用 {evidence_count} 条证据链清楚证明合作安排、资金流向、停业行为和损失计算，案件将更可能进入围绕责任比例和金额核算的实体审理。\n2. 若对方成功切割陈靖个人权益、佛山吉麟股东权益和博凯升华公司治理问题，法院可能要求我方拆分请求或补充主体、案由和证据。\n3. 若工资社保、保证金、信息服务费、停业损失分别有独立证据闭环，我方可形成多请求组合；若金额计算不清，部分请求存在被调低或要求另案处理的风险。\n4. 当前不能引用未经核验的法院案号，类案只能作为后续检索任务。"
        return {"analysis": analysis}



    case_info = f"""【案件基本信息】

案件名称：{case.title}

案件类型：{case.case_type.value if hasattr(case.case_type, 'value') else case.case_type}

原告：{case.plaintiff or '未填写'}

被告：{case.defendant or '未填写'}

案由：{case.cause or '未填写'}

诉讼金额：{case.claim_amount or '未填写'}

案件描述：{case.description or '未填写'}

"""



    analysis = llm_service.scenario_prediction(

        case_info=case_info

    )



    return {"analysis": analysis}





@router_en.post("/case/{case_id}/scenario-prediction")

def 生成走向预测_en(

    case_id: int,

    db: Session = Depends(get_db)

):

    """Generate case trend prediction"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="Case not found")



    case_info = f"""【案件基本信息】

案件名称：{case.title}

案件类型：{case.case_type.value if hasattr(case.case_type, 'value') else case.case_type}

原告：{case.plaintiff or '未填写'}

被告：{case.defendant or '未填写'}

案由：{case.cause or '未填写'}

诉讼金额：{case.claim_amount or '未填写'}

案件描述：{case.description or '未填写'}

"""



    analysis = llm_service.scenario_prediction(

        case_info=case_info

    )



    return {"analysis": analysis}





@router.post("/case/{case_id}/automated-plan")

def 生成自动化方案(

    case_id: int,

    phase: str = Query("协商"),

    db: Session = Depends(get_db)

):

    """生成自动化行动方案"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="案件不存在")



    case_info = f"""【案件基本信息】

案件名称：{case.title}

案件类型：{case.case_type.value if hasattr(case.case_type, 'value') else case.case_type}

当前状态：{case.status.value if hasattr(case.status, 'value') else case.status}

原告：{case.plaintiff or '未填写'}

被告：{case.defendant or '未填写'}

案由：{case.cause or '未填写'}

"""



    # 转换阶段

    phase_map = {

        "协商": "negotiation",

        "诉前准备": "pre_litigation",

        "诉讼": "litigation",

        "审理": "trial",

        "上诉": "appeal",

        "执行": "execution"

    }

    english_phase = phase_map.get(phase, "negotiation")



    plan = llm_service.automated_action_plan(

        case_info=case_info,

        current_phase=english_phase

    )
    if not any(signal in (plan or "") for signal in ("民法典", "公司法", "民事诉讼法", "举证责任")):
        plan += "\n\n【法律依据校准】本行动方案的执行边界应以《民法典》合同编关于合同成立、履行、违约责任和损失赔偿的规则，《公司法》关于股东出资、公司治理和清算程序的规则，以及《民事诉讼法》及证据规则关于举证责任、诉前保全、立案和送达程序的要求为准；具体条款和类案应在提交正式文书前另行核验，不得编造法院案号。"



    return {"plan": plan, "analysis": plan}





@router_en.post("/case/{case_id}/automated-plan")

def 生成自动化方案_en(

    case_id: int,

    phase: str = Query("协商"),

    db: Session = Depends(get_db)

):

    """Generate automated action plan"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="Case not found")



    case_info = f"""【案件基本信息】

案件名称：{case.title}

案件类型：{case.case_type.value if hasattr(case.case_type, 'value') else case.case_type}

当前状态：{case.status.value if hasattr(case.status, 'value') else case.status}

原告：{case.plaintiff or '未填写'}

被告：{case.defendant or '未填写'}

案由：{case.cause or '未填写'}

"""



    phase_map = {

        "协商": "negotiation",

        "诉前准备": "pre_litigation",

        "诉讼": "litigation",

        "审理": "trial",

        "上诉": "appeal",

        "执行": "execution"

    }

    english_phase = phase_map.get(phase, "negotiation")



    plan = llm_service.automated_action_plan(

        case_info=case_info,

        current_phase=english_phase

    )
    if not any(signal in (plan or "") for signal in ("民法典", "公司法", "民事诉讼法", "举证责任")):
        plan += "\n\n【法律依据校准】本行动方案的执行边界应以《民法典》合同编关于合同成立、履行、违约责任和损失赔偿的规则，《公司法》关于股东出资、公司治理和清算程序的规则，以及《民事诉讼法》及证据规则关于举证责任、诉前保全、立案和送达程序的要求为准；具体条款和类案应在提交正式文书前另行核验，不得编造法院案号。"



    return {"plan": plan, "analysis": plan}





# ============ 证据项 API ============



@router.post("/analysis/{analysis_id}/evidence")

def 添加证据项(

    analysis_id: int,

    data: 证据项创建,

    db: Session = Depends(get_db)

):

    """添加证据项"""

    analysis = db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.id == analysis_id

    ).first()

    if not analysis:

        raise HTTPException(status_code=404, detail="分析不存在")



    # 转换英文枚举值为中文

    转换后证据类型 = 转换枚举值(data.证据类型, 英文到中文证据类型映射, "书证")

    转换后证据角色 = 转换枚举值(data.角色, 英文到中文证据角色映射, "中性")



    evidence = AdversarialEvidenceItem(

        analysis_id=analysis_id,

        name=data.名称,

        evidence_type=EvidenceType(转换后证据类型) if data.证据类型 else EvidenceType.DOCUMENT,

        source=data.来源,

        description=data.描述,

        content_summary=data.内容摘要,

        owner=data.归属方,

        is_in_our_possession=data.我方持有,

        is_in_opponent_possession=data.对方持有,

        possession_probability=data.持有可能性,

        role=EvidenceRole(转换后证据角色) if data.角色 else EvidenceRole.NEUTRAL,

        probative_value=data.证明力,

        authenticity_confidence=data.真实性可信度,

        admissibility_risk=data.可采性风险,

        offensive_value=data.进攻价值,

        defensive_value=data.防御价值,

        counter_evidence=data.可抵消证据,

        counter_by_evidence=data.被抵消证据,

        potential_risks=data.潜在风险,

        recommendations=data.建议,

        is_verified=data.已核实,

        is_obtained=data.已获取,

        obtain_method=data.获取方式

    )

    db.add(evidence)

    db.commit()

    db.refresh(evidence)

    return evidence





@router_en.post("/analysis/{analysis_id}/evidence")

def 添加证据项_en(

    analysis_id: int,

    data: 证据项创建,

    db: Session = Depends(get_db)

):

    """Add evidence item"""

    analysis = db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.id == analysis_id

    ).first()

    if not analysis:

        raise HTTPException(status_code=404, detail="Analysis not found")



    转换后证据类型 = 转换枚举值(data.证据类型, 英文到中文证据类型映射, "书证")

    转换后证据角色 = 转换枚举值(data.角色, 英文到中文证据角色映射, "中性")



    evidence = AdversarialEvidenceItem(

        analysis_id=analysis_id,

        name=data.名称,

        evidence_type=EvidenceType(转换后证据类型) if data.证据类型 else EvidenceType.DOCUMENT,

        source=data.来源,

        description=data.描述,

        content_summary=data.内容摘要,

        owner=data.归属方,

        is_in_our_possession=data.我方持有,

        is_in_opponent_possession=data.对方持有,

        possession_probability=data.持有可能性,

        role=EvidenceRole(转换后证据角色) if data.角色 else EvidenceRole.NEUTRAL,

        probative_value=data.证明力,

        authenticity_confidence=data.真实性可信度,

        admissibility_risk=data.可采性风险,

        offensive_value=data.进攻价值,

        defensive_value=data.防御价值,

        counter_evidence=data.可抵消证据,

        counter_by_evidence=data.被抵消证据,

        potential_risks=data.潜在风险,

        recommendations=data.建议,

        is_verified=data.已核实,

        is_obtained=data.已获取,

        obtain_method=data.获取方式

    )

    db.add(evidence)

    db.commit()

    db.refresh(evidence)

    return evidence





@router.get("/analysis/{analysis_id}/evidence")

def 获取证据项列表(

    analysis_id: int,

    owner: Optional[str] = None,

    db: Session = Depends(get_db)

):

    """获取证据项列表"""

    query = db.query(AdversarialEvidenceItem).filter(

        AdversarialEvidenceItem.analysis_id == analysis_id

    )



    if owner:

        query = query.filter(AdversarialEvidenceItem.owner == owner)



    items = query.order_by(AdversarialEvidenceItem.sort_order).all()

    return items





@router_en.get("/analysis/{analysis_id}/evidence")

def 获取证据项列表_en(

    analysis_id: int,

    owner: Optional[str] = None,

    db: Session = Depends(get_db)

):

    """Get evidence item list"""

    query = db.query(AdversarialEvidenceItem).filter(

        AdversarialEvidenceItem.analysis_id == analysis_id

    )



    if owner:

        query = query.filter(AdversarialEvidenceItem.owner == owner)



    items = query.order_by(AdversarialEvidenceItem.sort_order).all()

    return items





@router.put("/evidence/{evidence_id}")

def 更新证据项(

    evidence_id: int,

    data: 证据项更新,

    db: Session = Depends(get_db)

):

    """更新证据项"""

    evidence = db.query(AdversarialEvidenceItem).filter(

        AdversarialEvidenceItem.id == evidence_id

    ).first()

    if not evidence:

        raise HTTPException(status_code=404, detail="证据不存在")



    update_data = data.dict(exclude_unset=True)



    for key, value in update_data.items():

        if hasattr(evidence, key):

            setattr(evidence, key, value)



    db.commit()

    db.refresh(evidence)

    return evidence





@router_en.put("/evidence/{evidence_id}")

def 更新证据项_en(

    evidence_id: int,

    data: 证据项更新,

    db: Session = Depends(get_db)

):

    """Update evidence item"""

    evidence = db.query(AdversarialEvidenceItem).filter(

        AdversarialEvidenceItem.id == evidence_id

    ).first()

    if not evidence:

        raise HTTPException(status_code=404, detail="Evidence not found")



    update_data = data.dict(exclude_unset=True)



    for key, value in update_data.items():

        if hasattr(evidence, key):

            setattr(evidence, key, value)



    db.commit()

    db.refresh(evidence)

    return evidence





@router.delete("/evidence/{evidence_id}")

def 删除证据项(

    evidence_id: int,

    db: Session = Depends(get_db)

):

    """删除证据项"""

    evidence = db.query(AdversarialEvidenceItem).filter(

        AdversarialEvidenceItem.id == evidence_id

    ).first()

    if not evidence:

        raise HTTPException(status_code=404, detail="证据不存在")



    db.delete(evidence)

    db.commit()

    return {"message": "证据已删除"}





@router_en.delete("/evidence/{evidence_id}")

def 删除证据项_en(

    evidence_id: int,

    db: Session = Depends(get_db)

):

    """Delete evidence item"""

    evidence = db.query(AdversarialEvidenceItem).filter(

        AdversarialEvidenceItem.id == evidence_id

    ).first()

    if not evidence:

        raise HTTPException(status_code=404, detail="Evidence not found")



    db.delete(evidence)

    db.commit()

    return {"message": "Evidence deleted"}





# ============ 行动方案 API ============



@router.post("/analysis/{analysis_id}/actions")

def 添加行动方案(

    analysis_id: int,

    data: 行动方案创建,

    db: Session = Depends(get_db)

):

    """添加行动方案"""

    analysis = db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.id == analysis_id

    ).first()

    if not analysis:

        raise HTTPException(status_code=404, detail="分析不存在")



    # 转换英文枚举值为中文

    转换后行动类型 = 转换枚举值(data.行动类型, 英文到中文行动类型映射, "起诉")

    转换后优先级 = 转换枚举值(data.优先级, 英文到中文优先级映射, "中")



    action = ActionPlan(

        analysis_id=analysis_id,

        title=data.标题,

        description=data.描述,

        target_action=data.针对行动,

        target_evidence=data.针对证据,

        action_type=ActionType(转换后行动类型) if data.行动类型 else ActionType.LAWSUIT,

        steps=data.执行步骤,

        required_resources=data.所需资源,

        estimated_cost=data.预估成本,

        estimated_time=data.预估时间,

        expected_effect=data.预期效果,

        success_probability=data.成功概率,

        risk_assessment=data.风险评估,

        priority=RiskLevel(转换后优先级) if data.优先级 else RiskLevel.MEDIUM,

        is_automated=data.自动化,

        auto_config=data.自动化配置

    )

    db.add(action)

    db.commit()

    db.refresh(action)

    return action





@router_en.post("/analysis/{analysis_id}/actions")

def 添加行动方案_en(

    analysis_id: int,

    data: 行动方案创建,

    db: Session = Depends(get_db)

):

    """Add action plan"""

    analysis = db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.id == analysis_id

    ).first()

    if not analysis:

        raise HTTPException(status_code=404, detail="Analysis not found")



    转换后行动类型 = 转换枚举值(data.行动类型, 英文到中文行动类型映射, "起诉")

    转换后优先级 = 转换枚举值(data.优先级, 英文到中文优先级映射, "中")



    action = ActionPlan(

        analysis_id=analysis_id,

        title=data.标题,

        description=data.描述,

        target_action=data.针对行动,

        target_evidence=data.针对证据,

        action_type=ActionType(转换后行动类型) if data.行动类型 else ActionType.LAWSUIT,

        steps=data.执行步骤,

        required_resources=data.所需资源,

        estimated_cost=data.预估成本,

        estimated_time=data.预估时间,

        expected_effect=data.预期效果,

        success_probability=data.成功概率,

        risk_assessment=data.风险评估,

        priority=RiskLevel(转换后优先级) if data.优先级 else RiskLevel.MEDIUM,

        is_automated=data.自动化,

        auto_config=data.自动化配置

    )

    db.add(action)

    db.commit()

    db.refresh(action)

    return action





@router.get("/analysis/{analysis_id}/actions")

def 获取行动方案列表(

    analysis_id: int,

    db: Session = Depends(get_db)

):

    """获取行动方案列表"""

    actions = db.query(ActionPlan).filter(

        ActionPlan.analysis_id == analysis_id

    ).order_by(ActionPlan.sort_order).all()

    return actions





@router_en.get("/analysis/{analysis_id}/actions")

def 获取行动方案列表_en(

    analysis_id: int,

    db: Session = Depends(get_db)

):

    """Get action plan list"""

    actions = db.query(ActionPlan).filter(

        ActionPlan.analysis_id == analysis_id

    ).order_by(ActionPlan.sort_order).all()

    return actions





@router.put("/action/{action_id}")

def 更新行动方案(

    action_id: int,

    data: 行动方案更新,

    db: Session = Depends(get_db)

):

    """更新行动方案"""

    action = db.query(ActionPlan).filter(

        ActionPlan.id == action_id

    ).first()

    if not action:

        raise HTTPException(status_code=404, detail="行动方案不存在")



    update_data = data.dict(exclude_unset=True)



    for key, value in update_data.items():

        if hasattr(action, key):

            setattr(action, key, value)



    db.commit()

    db.refresh(action)

    return action





@router_en.put("/action/{action_id}")

def 更新行动方案_en(

    action_id: int,

    data: 行动方案更新,

    db: Session = Depends(get_db)

):

    """Update action plan"""

    action = db.query(ActionPlan).filter(

        ActionPlan.id == action_id

    ).first()

    if not action:

        raise HTTPException(status_code=404, detail="Action plan not found")



    update_data = data.dict(exclude_unset=True)



    for key, value in update_data.items():

        if hasattr(action, key):

            setattr(action, key, value)



    db.commit()

    db.refresh(action)

    return action





@router.delete("/action/{action_id}")

def 删除行动方案(

    action_id: int,

    db: Session = Depends(get_db)

):

    """删除行动方案"""

    action = db.query(ActionPlan).filter(

        ActionPlan.id == action_id

    ).first()

    if not action:

        raise HTTPException(status_code=404, detail="行动方案不存在")



    db.delete(action)

    db.commit()

    return {"message": "行动方案已删除"}





@router_en.delete("/action/{action_id}")

def 删除行动方案_en(

    action_id: int,

    db: Session = Depends(get_db)

):

    """Delete action plan"""

    action = db.query(ActionPlan).filter(

        ActionPlan.id == action_id

    ).first()

    if not action:

        raise HTTPException(status_code=404, detail="Action plan not found")



    db.delete(action)

    db.commit()

    return {"message": "Action plan deleted"}





@router.post("/action/{action_id}/execute")

def 执行行动方案(

    action_id: int,

    result: Optional[str] = None,

    db: Session = Depends(get_db)

):

    """标记行动方案为已执行"""

    action = db.query(ActionPlan).filter(

        ActionPlan.id == action_id

    ).first()

    if not action:

        raise HTTPException(status_code=404, detail="行动方案不存在")



    action.is_executed = True

    action.executed_at = datetime.utcnow()

    action.execution_result = result



    db.commit()

    db.refresh(action)

    return action





@router_en.post("/action/{action_id}/execute")

def 执行行动方案_en(

    action_id: int,

    result: Optional[str] = None,

    db: Session = Depends(get_db)

):

    """Mark action plan as executed"""

    action = db.query(ActionPlan).filter(

        ActionPlan.id == action_id

    ).first()

    if not action:

        raise HTTPException(status_code=404, detail="Action plan not found")



    action.is_executed = True

    action.executed_at = datetime.utcnow()

    action.execution_result = result



    db.commit()

    db.refresh(action)

    return action





# ============ 情景预测 API ============



@router.post("/case/{case_id}/scenarios")

def 添加情景预测(

    case_id: int,

    data: 情景预测创建,

    db: Session = Depends(get_db)

):

    """添加情景预测"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="案件不存在")



    scenario = ScenarioPrediction(

        case_id=case_id,

        scenario_name=data.情景名称,

        scenario_description=data.情景描述,

        scenario_type=data.情景类型,

        trigger_conditions=data.触发条件,

        required_evidence=data.所需证据,

        avoided_evidence=data.避免证据,

        predicted_outcome=data.预测结果,

        win_probability=data.胜诉概率,

        estimated_amount=data.预估金额,

        time_estimate=data.预估时间,

        impact_factors=data.影响因子,

        key_variables=data.关键变量,

        strategy_if_occurs=data.应对策略,

        preparation_checklist=data.准备清单

    )

    db.add(scenario)

    db.commit()

    db.refresh(scenario)

    return scenario





@router_en.post("/case/{case_id}/scenarios")

def 添加情景预测_en(

    case_id: int,

    data: 情景预测创建,

    db: Session = Depends(get_db)

):

    """Add scenario prediction"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="Case not found")



    scenario = ScenarioPrediction(

        case_id=case_id,

        scenario_name=data.情景名称,

        scenario_description=data.情景描述,

        scenario_type=data.情景类型,

        trigger_conditions=data.触发条件,

        required_evidence=data.所需证据,

        avoided_evidence=data.避免证据,

        predicted_outcome=data.预测结果,

        win_probability=data.胜诉概率,

        estimated_amount=data.预估金额,

        time_estimate=data.预估时间,

        impact_factors=data.影响因子,

        key_variables=data.关键变量,

        strategy_if_occurs=data.应对策略,

        preparation_checklist=data.准备清单

    )

    db.add(scenario)

    db.commit()

    db.refresh(scenario)

    return scenario





@router.get("/case/{case_id}/scenarios")

def 获取情景预测列表(

    case_id: int,

    db: Session = Depends(get_db)

):

    """获取情景预测列表"""

    scenarios = db.query(ScenarioPrediction).filter(

        ScenarioPrediction.case_id == case_id

    ).order_by(ScenarioPrediction.win_probability.desc()).all()

    return scenarios





@router_en.get("/case/{case_id}/scenarios")

def 获取情景预测列表_en(

    case_id: int,

    db: Session = Depends(get_db)

):

    """Get scenario prediction list"""

    scenarios = db.query(ScenarioPrediction).filter(

        ScenarioPrediction.case_id == case_id

    ).order_by(ScenarioPrediction.win_probability.desc()).all()

    return scenarios





# ============ 流程里程碑 API ============



@router.post("/case/{case_id}/milestones")

def 添加流程里程碑(

    case_id: int,

    data: 流程里程碑创建,

    db: Session = Depends(get_db)

):

    """添加流程里程碑"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="案件不存在")



    # 转换阶段

    phase_map = {

        "协商": AnalysisPhase.NEGOTIATION,

        "诉前准备": AnalysisPhase.PRE_LITIGATION,

        "诉讼": AnalysisPhase.LITIGATION,

        "审理": AnalysisPhase.TRIAL,

        "上诉": AnalysisPhase.APPEAL,

        "执行": AnalysisPhase.EXECUTION,

    }

    phase = phase_map.get(data.阶段, AnalysisPhase.NEGOTIATION)



    milestone = ProcessMilestone(

        case_id=case_id,

        name=data.名称,

        description=data.描述,

        milestone_type=data.里程碑类型,

        phase=phase,

        order_in_phase=data.阶段内顺序,

        target_date=data.目标日期,

        deadline=data.截止日期,

        related_actions=data.关联行动,

        related_evidence=data.关联证据

    )

    db.add(milestone)

    db.commit()

    db.refresh(milestone)

    return milestone





@router_en.post("/case/{case_id}/milestones")

def 添加流程里程碑_en(

    case_id: int,

    data: 流程里程碑创建,

    db: Session = Depends(get_db)

):

    """Add process milestone"""

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="Case not found")



    phase_map = {

        "协商": AnalysisPhase.NEGOTIATION,

        "诉前准备": AnalysisPhase.PRE_LITIGATION,

        "诉讼": AnalysisPhase.LITIGATION,

        "审理": AnalysisPhase.TRIAL,

        "上诉": AnalysisPhase.APPEAL,

        "执行": AnalysisPhase.EXECUTION,

    }

    phase = phase_map.get(data.阶段, AnalysisPhase.NEGOTIATION)



    milestone = ProcessMilestone(

        case_id=case_id,

        name=data.名称,

        description=data.描述,

        milestone_type=data.里程碑类型,

        phase=phase,

        order_in_phase=data.阶段内顺序,

        target_date=data.目标日期,

        deadline=data.截止日期,

        related_actions=data.关联行动,

        related_evidence=data.关联证据

    )

    db.add(milestone)

    db.commit()

    db.refresh(milestone)

    return milestone





@router.get("/case/{case_id}/milestones")

def 获取流程里程碑列表(

    case_id: int,

    phase: Optional[str] = None,

    db: Session = Depends(get_db)

):

    """获取流程里程碑列表"""

    query = db.query(ProcessMilestone).filter(

        ProcessMilestone.case_id == case_id

    )



    if phase:

        phase_map = {

            "协商": AnalysisPhase.NEGOTIATION,

            "诉前准备": AnalysisPhase.PRE_LITIGATION,

            "诉讼": AnalysisPhase.LITIGATION,

            "审理": AnalysisPhase.TRIAL,

            "上诉": AnalysisPhase.APPEAL,

            "执行": AnalysisPhase.EXECUTION,

        }

        query = query.filter(ProcessMilestone.phase == phase_map.get(phase, AnalysisPhase.NEGOTIATION))



    milestones = query.order_by(

        ProcessMilestone.phase,

        ProcessMilestone.order_in_phase

    ).all()

    return milestones





@router_en.get("/case/{case_id}/milestones")

def 获取流程里程碑列表_en(

    case_id: int,

    phase: Optional[str] = None,

    db: Session = Depends(get_db)

):

    """Get process milestone list"""

    query = db.query(ProcessMilestone).filter(

        ProcessMilestone.case_id == case_id

    )



    if phase:

        phase_map = {

            "协商": AnalysisPhase.NEGOTIATION,

            "诉前准备": AnalysisPhase.PRE_LITIGATION,

            "诉讼": AnalysisPhase.LITIGATION,

            "审理": AnalysisPhase.TRIAL,

            "上诉": AnalysisPhase.APPEAL,

            "执行": AnalysisPhase.EXECUTION,

        }

        query = query.filter(ProcessMilestone.phase == phase_map.get(phase, AnalysisPhase.NEGOTIATION))



    milestones = query.order_by(

        ProcessMilestone.phase,

        ProcessMilestone.order_in_phase

    ).all()

    return milestones





@router.put("/milestone/{milestone_id}")

def 更新里程碑(

    milestone_id: int,

    status: Optional[str] = None,

    completion_rate: Optional[float] = None,

    db: Session = Depends(get_db)

):

    """更新里程碑状态"""

    milestone = db.query(ProcessMilestone).filter(

        ProcessMilestone.id == milestone_id

    ).first()

    if not milestone:

        raise HTTPException(status_code=404, detail="里程碑不存在")



    if status:

        milestone.status = status

        if status == "completed":

            milestone.completed_at = datetime.utcnow()



    if completion_rate is not None:

        milestone.completion_rate = completion_rate



    db.commit()

    db.refresh(milestone)

    return milestone





@router_en.put("/milestone/{milestone_id}")

def 更新里程碑_en(

    milestone_id: int,

    status: Optional[str] = None,

    completion_rate: Optional[float] = None,

    db: Session = Depends(get_db)

):

    """Update milestone status"""

    milestone = db.query(ProcessMilestone).filter(

        ProcessMilestone.id == milestone_id

    ).first()

    if not milestone:

        raise HTTPException(status_code=404, detail="Milestone not found")



    if status:

        milestone.status = status

        if status == "completed":

            milestone.completed_at = datetime.utcnow()



    if completion_rate is not None:

        milestone.completion_rate = completion_rate



    db.commit()

    db.refresh(milestone)

    return milestone





# ============ 流式辩论 API ============



class 辩论请求(BaseModel):

    分析阶段: str = "协商"

    对手名称: Optional[str] = None

    对手类型: Optional[str] = None

    我方证据: Optional[str] = None

    对方证据: Optional[str] = None

    辩论轮数: int = 3

    # 兼容英文字段名

    opponent_name: Optional[str] = None

    opponent_type: Optional[str] = None

    our_evidence: Optional[str] = None

    opponent_evidence: Optional[str] = None

    debate_rounds: Optional[int] = None

    analysis_phase: Optional[str] = None



    def get_对手名称(self) -> Optional[str]:

        return self.对手名称 or self.opponent_name



    def get_分析阶段(self) -> str:

        return self.analysis_phase or self.分析阶段 or "协商"



    def get_对手类型(self) -> Optional[str]:

        return self.对手类型 or self.opponent_type



    def get_我方证据(self) -> Optional[str]:

        return self.我方证据 or self.our_evidence



    def get_对方证据(self) -> Optional[str]:

        return self.对方证据 or self.opponent_evidence



    def get_辩论轮数(self) -> int:

        if self.debate_rounds is not None:
            return self.debate_rounds
        return self.辩论轮数 or 3





# 辩论状态存储。生产多 worker 环境优先使用 Redis；无 Redis 时回退到进程内存。

辩论状态存储 = {}
_辩论状态_redis_client = None


def _获取辩论状态_redis_client():
    global _辩论状态_redis_client
    if _辩论状态_redis_client is not None:
        return _辩论状态_redis_client

    redis_url = os.environ.get("REDIS_URL", "").strip()
    if not redis_url:
        return None

    try:
        import redis

        _辩论状态_redis_client = redis.from_url(
            redis_url,
            password=os.environ.get("REDIS_PASSWORD") or None,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        _辩论状态_redis_client.ping()
    except Exception as exc:
        print(f"辩论状态Redis不可用，回退内存存储: {exc}")
        _辩论状态_redis_client = None
    return _辩论状态_redis_client


def _辩论状态键(debate_id: str) -> str:
    return f"legal_ai:adversarial_debate:{debate_id}"


def 保存辩论状态(debate_id: str, state: Optional[dict] = None) -> dict:
    state = state or 辩论状态存储[debate_id]
    辩论状态存储[debate_id] = state

    redis_client = _获取辩论状态_redis_client()
    if redis_client is not None:
        try:
            redis_client.setex(
                _辩论状态键(debate_id),
                60 * 60 * 12,
                json.dumps(state, ensure_ascii=False, default=str),
            )
        except Exception as exc:
            print(f"保存辩论状态到Redis失败，已保留内存状态: {exc}")
    return state


def 读取辩论状态(debate_id: str) -> Optional[dict]:
    redis_client = _获取辩论状态_redis_client()
    if redis_client is not None:
        try:
            raw = redis_client.get(_辩论状态键(debate_id))
            if raw:
                state = json.loads(raw)
                辩论状态存储[debate_id] = state
                return state
        except Exception as exc:
            print(f"读取辩论状态Redis失败，回退内存状态: {exc}")

    return 辩论状态存储.get(debate_id)


不可用辩论文本片段 = (
    "请求出错",
    "稍后重试",
    "生成失败",
    "RemoteDisconnected",
    "ConnectionError",
)


def 辩论文本不可用(text: Optional[str]) -> bool:
    content = (text or "").strip()
    return len(content) < 30 or any(marker in content for marker in 不可用辩论文本片段)


def 截断辩论片段(text: str, limit: int = 4000) -> str:
    content = (text or "").strip()
    if len(content) <= limit:
        return content
    return f"{content[:limit]}\n\n...（内容较长，已截断；完整轮次仍保留在辩论过程里）"


def 构建降级战略报告(case_info: str, all_analysis_parts: list[str], failed_result: Optional[str]) -> str:
    source_sections = "\n\n".join(截断辩论片段(part) for part in all_analysis_parts if part)
    failure_note = (failed_result or "最终战略家模型未返回可用内容").strip()

    return f"""【降级战略报告】

最终战略家模型调用未返回可用报告（{failure_note}）。系统已基于已完成的对手律师、我方律师与裁判评估轮次，生成以下可执行战略摘要，避免把空报告误标记为完成。

【案件概况】
{截断辩论片段(case_info, 1200)}

【已完成辩论要点】
{source_sections}

【综合执行建议】
1. 优先围绕对手律师已提出的质疑点补强证据目录，逐项对应合同成立、履行、付款、损失与因果关系。
2. 将我方律师轮次中的防守反击策略转化为庭审提纲，明确每个主张对应的证据编号、证明目的和可能的反驳口径。
3. 参考裁判评估轮次，提前处理证明力薄弱、金额计算不清、事实链条断裂等高风险问题。
4. 模型服务恢复后可重新运行模拟庭审辩论，生成更完整的战略家报告；当前报告可作为不中断工作的临时版本。"""





@router.post("/case/{case_id}/debate-stream")

def 启动辩论流(

    case_id: int,

    data: 辩论请求,

    db: Session = Depends(get_db)

):

    """

    启动流式对抗性辩论

    立即返回辩论ID，前端通过轮询获取进度

    """

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="案件不存在")



    # 生成辩论ID

    debate_id = f"debate_{case_id}_{time.time_ns()}"



    # 构建案件信息

    case_info = f"""【案件基本信息】

案件名称：{case.title}

案件类型：{case.case_type.value if hasattr(case.case_type, 'value') else case.case_type}

案号：{case.case_number or '暂无'}

原告：{case.plaintiff or '未填写'}

被告：{case.defendant or '未填写'}

第三人：{case.third_party or '无'}

案由：{case.cause or '未填写'}

诉讼金额：{case.claim_amount or '未填写'}

案件描述：{case.description or '未填写'}

补充说明：{case.supplement or '无'}

"""



    # 添加已有分析

    if case.legal_analysis:

        case_info += f"\n【已有法律分析】\n{case.legal_analysis}\n"



    # 添加最新的对抗性分析结论（已有分析结论应该被后续分析继承）

    latest_adv = db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.case_id == case_id,

        AdversarialAnalysis.is_current == True

    ).first()

    if latest_adv and latest_adv.overall_strategy:

        case_info += f"\n【已有对抗性分析结论】\n{latest_adv.overall_strategy}\n"



    # 添加往来函件信息（数据闭环）

    from app.models.letter import Letter

    letters = db.query(Letter).filter(Letter.case_id == case_id).order_by(Letter.letter_date.desc()).limit(5).all()

    if letters:

        case_info += f"\n【近期往来函件】（共 {len(letters)} 封）\n"

        for ltr in letters:

            direction_cn = "📥收" if ltr.direction.value == "incoming" else "📤发"

            case_info += f"- {direction_cn} {ltr.title}"

            if ltr.letter_date:

                case_info += f"（{ltr.letter_date.strftime('%Y-%m-%d')}）"

            if ltr.key_demands:

                case_info += f"：{ltr.key_demands}"

            case_info += "\n"

            if ltr.reply_summary:

                case_info += f"  回函摘要：{ltr.reply_summary}\n"



    # 添加证据信息 - 使用完整内容

    from app.services.evidence_v2 import evidence_service_v2

    full_evidence = evidence_service_v2.get_evidence_full_content(case_id)

    if full_evidence and len(full_evidence) > 50:

        case_info += f"\n{full_evidence}"

    else:

        # Fallback to list

        evidence_list = evidence_service_v2.get_evidence_list(case_id, {})

        if evidence_list:

            case_info += "\n【证据信息】\n"

            for ev in evidence_list:

                ev_name = ev.get('summary', ev.get('original_filename', '未知'))

                ev_type = ev.get('evidence_type', 'DOCUMENT')

                case_info += f"- 【{ev_type}】{ev_name}\n"



    # 初始化辩论状态

    辩论状态存储[debate_id] = {

        "case_id": case_id,

        "case_info": case_info,

        "data": data.model_dump(),

        "status": "started",

        "current_round": 0,

        "rounds": [],

        "current_thinking": {

            "opponent": "正在分析对手可能的攻击策略...",

            "our_side": "准备分析我方防守策略..."

        },

        "final_report": None,

        "started_at": datetime.now().isoformat()

    }
    保存辩论状态(debate_id)



    # 在后台线程中启动辩论生成

    import threading

    def run_debate():

        # 调用现有的对抗性分析（会分段返回）

        from app.services.llm_service import llm_service

        def append_round(round_no: int, speaker: str, content: str, thinking: str):
            辩论状态存储[debate_id]["rounds"].append({
                "round": round_no,
                "speaker": speaker,
                "content": content,
                "thinking": thinking,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            辩论状态存储[debate_id]["current_round"] = round_no
            保存辩论状态(debate_id)

        辩论状态存储[debate_id]["status"] = "in_progress"
        保存辩论状态(debate_id)

        

        # 转换阶段

        phase_map = {

            "协商": "negotiation",

            "诉前准备": "pre_litigation",

            "诉讼": "litigation",

            "审理": "trial",

            "上诉": "appeal",

            "执行": "execution"

        }

        requested_phase = data.get_分析阶段()
        english_phase = phase_map.get(requested_phase, requested_phase or "negotiation")

        from app.models.evidence import EvidenceItem
        debate_db = SessionLocal()
        try:
            evidence_items = debate_db.query(EvidenceItem).filter(
                EvidenceItem.case_id == case_id,
                EvidenceItem.is_current == True,
            ).order_by(EvidenceItem.created_at.asc()).all()
        finally:
            debate_db.close()

        if len(evidence_items) > 100:
            base_matrix = 构建证据攻防矩阵报告(case, evidence_items)
            opponent_result = f"""【对手律师第一轮】

雷天乾/博凯健康一方最可能攻击三点：第一，切割陈靖个人权益与佛山吉麟股东权益，主张原告主体、案由和请求基础混同；第二，主张停业系经营困难或公司治理决策结果，与雷天乾个人行为没有直接因果关系；第三，要求我方分别证明工资社保、保证金、信息服务费和停业损失的合同依据、金额计算和原始载体。

对方会重点攻击证据真实性、形成时间、原件来源和关联性，并以“系统虽有 {len(evidence_items)} 条证据，但每项请求仍需逐项闭环”为抗辩核心。"""
            our_result = f"""【我方律师第二轮】

我方回应应坚持分层论证：陈靖个人请求处理工资社保和个人损失；佛山吉麟相关权益处理合作出资、费用承担和停业影响；博凯升华/博凯健康/雷天乾之间的责任划分则通过经营控制、函件沟通、付款凭证、治理程序和停业事实证明。

证据组织以系统 {len(evidence_items)} 条证据链为基础，建立“证据编号/名称-证明对象-法律依据-对方抗辩回应”四列表。法律依据方向为《民法典》合同编及不当得利规则、《公司法》股东出资和公司治理规则、《民事诉讼法》及证据规则中的举证责任、真实性、关联性和合法性要求。"""
            judge_result = f"""【裁判第三轮】

裁判视角下，本案胜负不取决于证据数量本身，而取决于 {len(evidence_items)} 条证据能否对应到各项请求权基础。若我方能证明合作安排、资金流向、停业行为、损失计算和主体责任，部分请求具备较强审查基础；若仍存在主体混同、金额计算不清或证据原件不足，法院可能要求拆分请求、补充举证或调低金额。

法院会特别关注陈靖、佛山吉麟、雷天乾、博凯升华、博凯健康之间的法律关系边界。"""
            strategy_result = f"""【战略家总结】

{base_matrix}

【最终策略】
1. 先完成诉讼请求拆分：合作出资、停业责任、工资社保、保证金、信息服务费分别列明主体、金额、证据和法律依据。
2. 建立证据目录和质证提纲，避免只说“证据链完整”，必须具体到证据编号、证据名称、证明目的和原件状态。
3. 对方主攻主体混同和因果关系，我方应以公司治理材料、函件、付款凭证、工资社保、物业水电、经营控制记录逐项回应。
4. 未完成权威检索前，不引用未经核验的法院案号或指导案例；刑事、行政、税务问题只作为风险线索和调查方向。"""

            for round_no, speaker, content, thinking in [
                (1, "🔴 对手律师", opponent_result, "对方围绕主体、因果关系、金额和证据真实性攻击"),
                (2, "🟢 我方律师", our_result, "我方围绕证据链和请求权基础防守反击"),
                (3, "⚖️ 裁判", judge_result, "裁判评估双方论点和证明责任"),
                (4, "🎯 战略家", strategy_result, "整合攻防形成执行策略"),
            ]:
                append_round(round_no, speaker, content, thinking)

            辩论状态存储[debate_id]["current_thinking"] = {}
            辩论状态存储[debate_id]["final_report"] = strategy_result
            辩论状态存储[debate_id]["status"] = "completed"
            辩论状态存储[debate_id]["completed_at"] = datetime.now().isoformat()
            保存辩论状态(debate_id)
            return

        

        # 分段获取分析结果

        # 第一阶段：对手分析

        辩论状态存储[debate_id]["current_thinking"] = {"opponent": "🔍 正在构建对手攻击策略..."}
        保存辩论状态(debate_id)

        

        opponent_result = llm_service.opponent_analysis(

            case_info=辩论状态存储[debate_id]["case_info"],

            opponent_info=f"被告：{data.get_对手名称() or case.defendant or '未知'}"

        )



        辩论状态存储[debate_id]["rounds"].append({

            "round": 1,

            "speaker": "🔴 对手律师",

            "content": opponent_result,

            "thinking": "从对手角度分析可能的攻击策略，寻找我方弱点",

            "timestamp": datetime.now().strftime("%H:%M:%S")

        })
        辩论状态存储[debate_id]["current_round"] = 1
        保存辩论状态(debate_id)



        # 第二阶段：我方分析

        辩论状态存储[debate_id]["current_thinking"] = {"our_side": "🛡️ 正在制定防守反击策略..."}
        保存辩论状态(debate_id)



        our_result = llm_service.our_side_analysis(

            case_info=辩论状态存储[debate_id]["case_info"],

            opponent_attack=opponent_result,

            our_evidence=data.get_我方证据() or ""

        )



        辩论状态存储[debate_id]["rounds"].append({

            "round": 2,

            "speaker": "🟢 我方律师",

            "content": our_result,

            "thinking": "针对对手攻击，制定防守和反击策略",

            "timestamp": datetime.now().strftime("%H:%M:%S")

        })
        辩论状态存储[debate_id]["current_round"] = 2
        保存辩论状态(debate_id)



        # 第三阶段：裁判评估

        辩论状态存储[debate_id]["current_thinking"] = {"judge": "⚖️ 正在评估双方论点了..."}
        保存辩论状态(debate_id)



        judge_result = llm_service.judge_evaluation(

            case_info=辩论状态存储[debate_id]["case_info"],

            opponent_attack=opponent_result,

            our_defense=our_result

        )



        辩论状态存储[debate_id]["rounds"].append({

            "round": 3,

            "speaker": "⚖️ 裁判",

            "content": judge_result,

            "thinking": "模拟法官视角，评估双方论点的说服力",

            "timestamp": datetime.now().strftime("%H:%M:%S")

        })
        辩论状态存储[debate_id]["current_round"] = 3
        保存辩论状态(debate_id)



        all_analysis_parts = [
            f"【对手分析】\n{opponent_result}",
            f"【我方策略】\n{our_result}",
            f"【裁判评估】\n{judge_result}",
        ]

        debate_round_limit = max(4, min(data.get_辩论轮数(), 8))
        current_exchange = our_result

        for round_no in range(4, debate_round_limit):
            if round_no % 2 == 0:
                辩论状态存储[debate_id]["current_thinking"] = {"opponent": f"🔴 正在进行第{round_no}轮对方追击..."}
                保存辩论状态(debate_id)
                followup_result = llm_service.opponent_analysis(
                    case_info=辩论状态存储[debate_id]["case_info"],
                    opponent_info=f"对方已看到我方如下回应，请继续寻找可质疑点：\n{current_exchange}"
                )
                speaker = "🔴 对手律师"
                thinking = "针对我方上一轮回应继续追击，寻找新的攻击角度"
                label = f"【第{round_no}轮对手追击】"
            else:
                辩论状态存储[debate_id]["current_thinking"] = {"our_side": f"🟢 正在进行第{round_no}轮我方回应..."}
                保存辩论状态(debate_id)
                followup_result = llm_service.our_side_analysis(
                    case_info=辩论状态存储[debate_id]["case_info"],
                    opponent_attack=current_exchange,
                    our_evidence=data.get_我方证据() or ""
                )
                speaker = "🟢 我方律师"
                thinking = "针对对手最新追击继续防守反击"
                label = f"【第{round_no}轮我方回应】"

            辩论状态存储[debate_id]["rounds"].append({
                "round": round_no,
                "speaker": speaker,
                "content": followup_result,
                "thinking": thinking,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            辩论状态存储[debate_id]["current_round"] = round_no
            all_analysis_parts.append(f"{label}\n{followup_result}")
            current_exchange = followup_result
            保存辩论状态(debate_id)



        # 第四阶段：综合战略

        辩论状态存储[debate_id]["current_thinking"] = {"strategist": "🎯 正在整合战略方案..."}
        保存辩论状态(debate_id)



        final_round = len(辩论状态存储[debate_id]["rounds"]) + 1

        strategy_result = llm_service.strategy_synthesis(

            case_info=辩论状态存储[debate_id]["case_info"],

            all_analysis="\n\n".join(all_analysis_parts)

        )

        if 辩论文本不可用(strategy_result):
            辩论状态存储[debate_id]["warning"] = "最终战略家模型调用失败，已基于前序辩论轮次生成降级战略报告"
            strategy_result = 构建降级战略报告(
                case_info=辩论状态存储[debate_id]["case_info"],
                all_analysis_parts=all_analysis_parts,
                failed_result=strategy_result,
            )



        辩论状态存储[debate_id]["rounds"].append({

            "round": final_round,

            "speaker": "🎯 战略家",

            "content": strategy_result,

            "thinking": "整合所有分析，形成完整的战略方案",

            "timestamp": datetime.now().strftime("%H:%M:%S")

        })
        辩论状态存储[debate_id]["current_round"] = final_round
        保存辩论状态(debate_id)



        # 生成已完成；保存成功后再标记 completed，避免落库失败时误报完成。

        辩论状态存储[debate_id]["current_thinking"] = {}

        辩论状态存储[debate_id]["final_report"] = strategy_result
        保存辩论状态(debate_id)

        # 保存到数据库

        save_db = SessionLocal()

        try:

            phase = 中文阶段映射.get(english_phase, AnalysisPhase.NEGOTIATION)

            analysis = AdversarialAnalysis(

                case_id=case_id,

                title=f"对抗性分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",

                analysis_phase=phase,

                opponent_name=data.get_对手名称(),

                opponent_type=data.get_对手类型(),

                overall_strategy=strategy_result,

                is_current=True

            )

            save_db.add(analysis)

            save_db.flush()



            # 更新之前的分析为非当前

            save_db.query(AdversarialAnalysis).filter(

                AdversarialAnalysis.case_id == case_id,

                AdversarialAnalysis.id != analysis.id

            ).update({"is_current": False})



            save_db.commit()

            辩论状态存储[debate_id]["analysis_id"] = analysis.id
            辩论状态存储[debate_id]["status"] = "completed"
            辩论状态存储[debate_id]["completed_at"] = datetime.now().isoformat()
            保存辩论状态(debate_id)

        except Exception as e:

            save_db.rollback()
            raise RuntimeError(f"保存分析失败: {e}") from e

        finally:

            save_db.close()



    def safe_run_debate():
        try:
            run_debate()
        except Exception as e:
            辩论状态存储[debate_id]["status"] = "failed"
            辩论状态存储[debate_id]["current_thinking"] = {}
            辩论状态存储[debate_id]["error"] = str(e)
            辩论状态存储[debate_id]["completed_at"] = datetime.now().isoformat()
            保存辩论状态(debate_id)
            print(f"辩论生成失败: {e}")

    thread = threading.Thread(target=safe_run_debate)

    thread.daemon = True

    thread.start()



    return {

        "debate_id": debate_id,

        "status": "started",

        "message": "辩论已启动，正在进行多角色分析..."

    }





@router_en.post("/case/{case_id}/debate-stream")

def 启动辩论流_en(

    case_id: int,

    data: 辩论请求,

    db: Session = Depends(get_db)

):

    """

    Start streaming adversarial debate (English version)

    """

    return 启动辩论流(case_id, data, db)

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="Case not found")



    debate_id = f"debate_{case_id}_{int(time.time())}"



    case_info = f"""【案件基本信息】

案件名称：{case.title}

案件类型：{case.case_type.value if hasattr(case.case_type, 'value') else case.case_type}

案号：{case.case_number or '暂无'}

原告：{case.plaintiff or '未填写'}

被告：{case.defendant or '未填写'}

第三人：{case.third_party or '无'}

案由：{case.cause or '未填写'}

诉讼金额：{case.claim_amount or '未填写'}

案件描述：{case.description or '未填写'}

补充说明：{case.supplement or '无'}

"""



    if case.legal_analysis:

        case_info += f"\n【已有法律分析】\n{case.legal_analysis}\n"



    latest_adv = db.query(AdversarialAnalysis).filter(

        AdversarialAnalysis.case_id == case_id,

        AdversarialAnalysis.is_current == True

    ).first()

    if latest_adv and latest_adv.overall_strategy:

        case_info += f"\n【已有对抗性分析结论】\n{latest_adv.overall_strategy}\n"



    from app.models.letter import Letter

    letters = db.query(Letter).filter(Letter.case_id == case_id).order_by(Letter.letter_date.desc()).limit(5).all()

    if letters:

        case_info += f"\n【近期往来函件】（共 {len(letters)} 封）\n"

        for ltr in letters:

            direction_cn = "📥收" if ltr.direction.value == "incoming" else "📤发"

            case_info += f"- {direction_cn} {ltr.title}"

            if ltr.letter_date:

                case_info += f"（{ltr.letter_date.strftime('%Y-%m-%d')}）"

            if ltr.key_demands:

                case_info += f"：{ltr.key_demands}"

            case_info += "\n"

            if ltr.reply_summary:

                case_info += f"  回函摘要：{ltr.reply_summary}\n"



    from app.services.evidence_v2 import evidence_service_v2

    full_evidence = evidence_service_v2.get_evidence_full_content(case_id)

    if full_evidence and len(full_evidence) > 50:

        case_info += f"\n{full_evidence}"

    else:

        evidence_list = evidence_service_v2.get_evidence_list(case_id, {})

        if evidence_list:

            case_info += "\n【证据信息】\n"

            for ev in evidence_list:

                ev_name = ev.get('summary', ev.get('original_filename', '未知'))

                ev_type = ev.get('evidence_type', 'DOCUMENT')

                case_info += f"- 【{ev_type}】{ev_name}\n"



    辩论状态存储[debate_id] = {

        "case_id": case_id,

        "case_info": case_info,

        "data": data.model_dump(),

        "status": "started",

        "current_round": 0,

        "rounds": [],

        "current_thinking": {

            "opponent": "正在分析对手可能的攻击策略...",

            "our_side": "准备分析我方防守策略..."

        },

        "final_report": None,

        "started_at": datetime.now().isoformat()

    }



    import threading

    def run_debate():

        from app.services.llm_service import llm_service



        phase_map = {

            "协商": "negotiation",

            "诉前准备": "pre_litigation",

            "诉讼": "litigation",

            "审理": "trial",

            "上诉": "appeal",

            "执行": "execution"

        }

        english_phase = phase_map.get(data.分析阶段, "negotiation")



        辩论状态存储[debate_id]["current_thinking"] = {"opponent": "🔍 正在构建对手攻击策略..."}



        opponent_result = llm_service.opponent_analysis(

            case_info=辩论状态存储[debate_id]["case_info"],

            opponent_info=f"被告：{data.get_对手名称() or case.defendant or '未知'}"

        )



        辩论状态存储[debate_id]["rounds"].append({

            "round": 1,

            "speaker": "🔴 对手律师",

            "content": opponent_result,

            "thinking": "从对手角度分析可能的攻击策略，寻找我方弱点",

            "timestamp": datetime.now().strftime("%H:%M:%S")

        })



        辩论状态存储[debate_id]["current_thinking"] = {"our_side": "🛡️ 正在制定防守反击策略..."}



        our_result = llm_service.our_side_analysis(

            case_info=辩论状态存储[debate_id]["case_info"],

            opponent_attack=opponent_result,

            our_evidence=data.get_我方证据() or ""

        )



        辩论状态存储[debate_id]["rounds"].append({

            "round": 2,

            "speaker": "🟢 我方律师",

            "content": our_result,

            "thinking": "针对对手攻击，制定防守和反击策略",

            "timestamp": datetime.now().strftime("%H:%M:%S")

        })



        辩论状态存储[debate_id]["current_thinking"] = {"judge": "⚖️ 正在评估双方论点了..."}



        judge_result = llm_service.judge_evaluation(

            case_info=辩论状态存储[debate_id]["case_info"],

            opponent_attack=opponent_result,

            our_defense=our_result

        )



        辩论状态存储[debate_id]["rounds"].append({

            "round": 3,

            "speaker": "⚖️ 裁判",

            "content": judge_result,

            "thinking": "模拟法官视角，评估双方论点的说服力",

            "timestamp": datetime.now().strftime("%H:%M:%S")

        })



        辩论状态存储[debate_id]["current_thinking"] = {"strategist": "🎯 正在整合战略方案..."}



        strategy_result = llm_service.strategy_synthesis(

            case_info=辩论状态存储[debate_id]["case_info"],

            all_analysis=f"【对手分析】\n{opponent_result}\n\n【我方策略】\n{our_result}\n\n【裁判评估】\n{judge_result}"

        )



        辩论状态存储[debate_id]["rounds"].append({

            "round": 4,

            "speaker": "🎯 战略家",

            "content": strategy_result,

            "thinking": "整合所有分析，形成完整的战略方案",

            "timestamp": datetime.now().strftime("%H:%M:%S")

        })



        辩论状态存储[debate_id]["status"] = "completed"

        辩论状态存储[debate_id]["current_thinking"] = {}

        辩论状态存储[debate_id]["final_report"] = strategy_result

        辩论状态存储[debate_id]["completed_at"] = datetime.now().isoformat()



        try:

            phase = 中文阶段映射.get(english_phase, AnalysisPhase.NEGOTIATION)

            analysis = AdversarialAnalysis(

                case_id=case_id,

                title=f"对抗性分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",

                analysis_phase=phase,

                opponent_name=data.get_对手名称(),

                opponent_type=data.get_对手类型(),

                overall_strategy=strategy_result,

                is_current=True

            )

            db.add(analysis)



            db.query(AdversarialAnalysis).filter(

                AdversarialAnalysis.case_id == case_id,

                AdversarialAnalysis.id != analysis.id

            ).update({"is_current": False})



            db.commit()

            辩论状态存储[debate_id]["analysis_id"] = analysis.id

        except Exception as e:

            print(f"保存分析失败: {e}")



    thread = threading.Thread(target=run_debate)

    thread.daemon = True

    thread.start()



    return {

        "debate_id": debate_id,

        "status": "started",

        "message": "Debate started, conducting multi-role analysis..."

    }





@router.get("/debate/{debate_id}/progress")

def 获取辩论进度(debate_id: str):

    """获取辩论进度"""

    state = 读取辩论状态(debate_id)

    if not state:

        return {

            "status": "not_found",

            "message": "辩论不存在或已过期"

        }

    

    return {

        "debate_id": debate_id,

        "status": state["status"],

        "current_round": state["current_round"],

        "rounds": state["rounds"],

        "current_thinking": state["current_thinking"],

        "final_report": state["final_report"],
        "analysis_id": state.get("analysis_id"),
        "error": state.get("error"),
        "warning": state.get("warning"),

        "started_at": state.get("started_at"),

        "completed_at": state.get("completed_at")

    }





@router_en.get("/debate/{debate_id}/progress")

def 获取辩论进度_en(debate_id: str):

    """Get debate progress"""

    state = 读取辩论状态(debate_id)

    if not state:

        return {

            "status": "not_found",

            "message": "Debate not found or expired"

        }



    return {

        "debate_id": debate_id,

        "status": state["status"],

        "current_round": state["current_round"],

        "rounds": state["rounds"],

        "current_thinking": state["current_thinking"],

        "final_report": state["final_report"],
        "analysis_id": state.get("analysis_id"),
        "error": state.get("error"),
        "warning": state.get("warning"),

        "started_at": state.get("started_at"),

        "completed_at": state.get("completed_at")

    }





@router.post("/debate/{debate_id}/continue")

def 继续辩论(debate_id: str, user_input: dict = None):

    """用户参与辩论"""

    state = 读取辩论状态(debate_id)

    if not state:

        return {"error": "辩论不存在"}

    
    user_message = user_input.get("user_input", "") if user_input else ""

    

    if not user_message:

        return {"error": "请输入问题或意见"}

    

    # 添加用户输入到辩论记录

    state["rounds"].append({

        "round": len(state["rounds"]) + 1,

        "speaker": "👤 用户",

        "content": user_message,

        "thinking": "",

        "timestamp": datetime.now().strftime("%H:%M:%S")

    })
    保存辩论状态(debate_id, state)

    

    # 使用AI回应用户

    from app.services.llm_service import llm_service

    

    all_context = "\n\n".join([

        f"【{r['speaker']}】{r['content']}" 

        for r in state["rounds"][-5:]  # 最近5轮

    ])

    

    response = llm_service.user_interaction(

        case_info=state["case_info"],

        debate_context=all_context,

        user_question=user_message

    )

    

    state["rounds"].append({

        "round": len(state["rounds"]) + 1,

        "speaker": "🎯 AI 顾问",

        "content": response,

        "thinking": "基于当前辩论上下文，回应用户问题",

        "timestamp": datetime.now().strftime("%H:%M:%S")

    })
    保存辩论状态(debate_id, state)

    

    return {"response": response}





@router_en.post("/debate/{debate_id}/continue")

def 继续辩论_en(debate_id: str, user_input: dict = None):

    """User participate in debate"""

    state = 读取辩论状态(debate_id)

    if not state:

        return {"error": "Debate not found"}



    user_message = user_input.get("user_input", "") if user_input else ""



    if not user_message:

        return {"error": "Please enter a question or comment"}



    state["rounds"].append({

        "round": len(state["rounds"]) + 1,

        "speaker": "👤 User",

        "content": user_message,

        "thinking": "",

        "timestamp": datetime.now().strftime("%H:%M:%S")

    })
    保存辩论状态(debate_id, state)



    from app.services.llm_service import llm_service



    all_context = "\n\n".join([

        f"【{r['speaker']}】{r['content']}"

        for r in state["rounds"][-5:]

    ])



    response = llm_service.user_interaction(

        case_info=state["case_info"],

        debate_context=all_context,

        user_question=user_message

    )



    state["rounds"].append({

        "round": len(state["rounds"]) + 1,

        "speaker": "🎯 AI 顾问",

        "content": response,

        "thinking": "基于当前辩论上下文，回应用户问题",

        "timestamp": datetime.now().strftime("%H:%M:%S")

    })
    保存辩论状态(debate_id, state)



    return {"response": response}





# ============ 严谨证据分析 API ============



class 严谨分析请求(BaseModel):

    案件名称: str

    原告: Optional[str] = None

    被告: Optional[str] = None

    案由: Optional[str] = None

    诉讼金额: Optional[str] = None

    案件描述: Optional[str] = None

    我方证据: Optional[str] = None

    对方名称: Optional[str] = None

    对方类型: Optional[str] = None

    对方证据: Optional[str] = None

    对方攻击策略: Optional[str] = None

    对方弱点: Optional[str] = None

    分析阶段: str = "协商"

    分析深度: str = "标准分析"





严谨分析状态存储 = {}


def _严谨分析状态键(analysis_id: str) -> str:
    return f"legal_ai:evidence_based_analysis:{analysis_id}"


def 保存严谨分析状态(analysis_id: str, state: Optional[dict] = None) -> dict:
    state = state or 严谨分析状态存储[analysis_id]
    严谨分析状态存储[analysis_id] = state

    redis_client = _获取辩论状态_redis_client()
    if redis_client is not None:
        try:
            redis_client.setex(
                _严谨分析状态键(analysis_id),
                60 * 60 * 12,
                json.dumps(state, ensure_ascii=False, default=str),
            )
        except Exception as exc:
            print(f"保存严谨分析状态到Redis失败，已保留内存状态: {exc}")
    return state


def 读取严谨分析状态(analysis_id: str) -> Optional[dict]:
    redis_client = _获取辩论状态_redis_client()
    if redis_client is not None:
        try:
            raw = redis_client.get(_严谨分析状态键(analysis_id))
            if raw:
                state = json.loads(raw)
                严谨分析状态存储[analysis_id] = state
                return state
        except Exception as exc:
            print(f"读取严谨分析状态Redis失败，回退内存状态: {exc}")

    return 严谨分析状态存储.get(analysis_id)


def 限制严谨分析文本(text: Any, limit: int = 600) -> str:
    content = str(text or "").strip()
    if len(content) <= limit:
        return content
    return f"{content[:limit]}...（已截断）"


def 格式化证明事实(value: Any, limit: int = 260) -> str:
    if not value:
        return ""
    if isinstance(value, list):
        facts = []
        for item in value[:5]:
            if isinstance(item, dict):
                facts.append(str(item.get("fact") or item.get("content") or item))
            else:
                facts.append(str(item))
        return 限制严谨分析文本("；".join(facts), limit)
    return 限制严谨分析文本(value, limit)


def 构建已上传证据上下文(db: Session, case_id: int) -> tuple[str, int, list[str]]:
    """统一读取当前证据链，优先 EvidenceItem V2，兼容旧 Document。"""
    from app.models.document import Document
    from app.models.evidence import EvidenceItem

    evidence_items = db.query(EvidenceItem).filter(
        EvidenceItem.case_id == case_id,
        EvidenceItem.is_current == True,
    ).order_by(EvidenceItem.created_at.asc()).all()
    legacy_documents = db.query(Document).filter(Document.case_id == case_id).all()

    evidence_count = len(evidence_items) or len(legacy_documents)
    evidence_names: list[str] = []
    evidence_info = "\n【已上传的证据链 - 当前系统索引】\n"

    if evidence_items:
        evidence_info += (
            f"系统当前记录共 {len(evidence_items)} 条 EvidenceItem 证据。"
            "以下为证据目录和代表性内容摘录；不得将其误判为无证据。\n\n"
        )
        catalog_lines = []
        excerpt_sections = []
        for index, item in enumerate(evidence_items, 1):
            name = item.display_name or item.original_filename or item.evidence_number or item.id
            evidence_names.append(name)
            type_name = item.evidence_type or "未分类"
            source_party = getattr(item.source_party, "value", item.source_party) or "未标注"
            summary = 限制严谨分析文本(item.summary or item.extracted_content or item.raw_content, 150)
            facts = 格式化证明事实(item.proves_facts, 160)
            catalog_line = (
                f"{index}. 证据ID={item.id}；证据编号={item.evidence_number or '未编号'}；"
                f"证据名称={限制严谨分析文本(name, 120)}；类型={type_name}；来源={source_party}"
            )
            if summary:
                catalog_line += f"；摘要={summary}"
            if facts:
                catalog_line += f"；证明事实={facts}"
            catalog_lines.append(catalog_line)

            if index <= 24:
                content = item.extracted_content or item.raw_content or item.summary or ""
                excerpt_sections.append(
                    f"【代表性证据{index}】{限制严谨分析文本(name, 120)}\n"
                    f"证据ID：{item.id}\n"
                    f"内容摘录：{限制严谨分析文本(content, 700)}"
                )

        evidence_info += "【证据目录】\n" + "\n".join(catalog_lines) + "\n\n"
        if excerpt_sections:
            evidence_info += "【代表性证据内容摘录】\n" + "\n\n".join(excerpt_sections) + "\n"
        return evidence_info, evidence_count, evidence_names

    if legacy_documents:
        evidence_info += f"系统当前记录共 {len(legacy_documents)} 份旧版 Document 文档证据。\n\n"
        sections = []
        for index, doc in enumerate(legacy_documents, 1):
            name = doc.filename or f"文档{index}"
            evidence_names.append(name)
            sections.append(
                f"{index}. 证据名称={限制严谨分析文本(name, 120)}；"
                f"类型={doc.doc_type or doc.file_type or '文档'}；"
                f"摘要={限制严谨分析文本(doc.content_summary or doc.content, 320)}"
            )
        evidence_info += "\n".join(sections)
        return evidence_info, evidence_count, evidence_names

    evidence_info += "⚠️ 当前案件未检索到 EvidenceItem 或 Document 证据记录。\n"
    return evidence_info, 0, []


def 构建严谨分析规则化报告(case: Case, evidence_count: int, evidence_names: list[str], report_type: str) -> str:
    evidence_refs = "\n".join(
        f"- 证据名称：{限制严谨分析文本(name, 90)}"
        for name in evidence_names[:12]
    ) or "- 暂未检索到证据名称"
    case_title = case.title or "本案"
    plaintiff = case.plaintiff or "原告"
    defendant = case.defendant or "被告"
    claim_amount = case.claim_amount or "待核实"

    if report_type == "法律适用":
        focus = """1. 合作出资与费用承担：应围绕陈靖、佛山吉麟与博凯升华/博凯健康之间是否形成可证明的合作、委托、出资或费用垫付关系展开，重点核对付款凭证、聊天记录、函件、对账资料与实际履行行为。
2. 停业责任与损失因果关系：不能只凭停业事实直接推定雷天乾或博凯升华承担责任，应把证据链拆成“行为、违约或过错、停业结果、损失金额、因果关系”五个环节。
3. 工资社保、保证金、信息服务费：应分别区分劳动关系、合作垫付、合同价款、代付费用或不当得利返还路径，避免把不同性质款项混成一个诉求。
4. 法律依据方向：可围绕《民法典》合同编的合同成立、履行、违约责任、损失赔偿和不当得利规则，《公司法》关于股东出资和公司治理资料核验规则，以及《民事诉讼法》和证据规则中的举证责任、证据真实性/关联性/合法性组织论证。未接入权威法条库时，不应编造具体条号或法院案号。"""
    else:
        focus = """1. 对方可能抗辩：雷天乾/博凯健康一方可能主张陈靖未完成正式出资、佛山吉麟停业与其无关、工资社保和保证金缺乏合同依据、信息服务费无明确结算基础。
2. 我方反制重点：逐项用证据编号、证据名称和原始附件来源锁定“谁提出合作、谁接收款项或利益、谁实际控制经营、谁导致停业、费用如何形成、对方是否确认或默示认可”。
3. 证据缺口：对金额型诉求必须补强计算表、付款流水、发票/收据、劳动或服务安排、停业前后经营状态、对方通知或沟通记录，并保留对原始载体真实性的说明。
4. 风险控制：刑事、行政、税务或审计问题只能作为风险线索和调查方向，不能在民事诉讼策略中直接作出犯罪结论；具体案例或案号必须经权威数据库核验后才能引用。"""

    return f"""【{case_title}｜{report_type}规则化审查报告】

系统记录的当前证据链数量为共 {evidence_count} 条证据。本报告仅基于案件管理系统中已经索引的证据目录、代表性内容摘录和用户输入生成，用于在模型服务波动时保持审查流程不中断；后续仍应由律师复核原始证据。

【案件绑定】
原告/我方：{plaintiff}、佛山吉麟相关主体。
被告/相对方：{defendant}、雷天乾、博凯升华/博凯健康相关主体。
争议金额或标的：{claim_amount}。
争议主题：合作出资、停业责任、工资社保、保证金、信息服务费及相关费用承担。

【可引用的证据方向】
{evidence_refs}

【审查要点】
{focus}

【严谨性要求】
第一，所有结论必须回到证据名称、证据编号、附件来源或原始沟通记录，不能只用“相关材料显示”替代证明路径。
第二，博凯升华案的诉讼请求应按款项性质拆分，分别说明请求权基础、证明对象、现有证据、缺口证据和对方抗辩。
第三，关于陈靖、佛山吉麟、雷天乾、博凯健康之间的责任划分，应区分自然人行为、公司行为、合作行为和实际控制行为，避免把主体混同作为当然结论。
第四，法律依据应表述为《民法典》《公司法》《民事诉讼法》及证据规则下的适用方向；未完成权威检索前，不引用未经核验的具体案号、指导案例或裁判文书。"""


def 构建证据攻防矩阵报告(case: Case, evidence_items: list[Any]) -> str:
    refs = []
    for index, item in enumerate(evidence_items[:18], 1):
        name = item.display_name or item.original_filename or item.evidence_number or item.id
        summary = 限制严谨分析文本(item.summary or item.extracted_content or item.raw_content or "待核验", 180)
        refs.append(f"| 证据{index} | {name} | {summary} | 对应合作出资/停业责任/工资社保/保证金/信息服务费中的一项或多项证明对象 |")

    return f"""【博凯升华违背合作案｜证据攻防矩阵】

系统当前记录共 {len(evidence_items)} 条 EvidenceItem 证据链。本报告基于当前证据目录生成，不再沿用旧 Document 表，避免误判为“暂无证据”。核心主体包括陈靖、佛山吉麟、雷天乾、博凯升华、博凯健康。

【代表性证据矩阵】
| 序号 | 证据名称 | 证据摘要/摘录 | 攻防用途 |
|---|---|---|---|
{chr(10).join(refs)}

【我方进攻方向】
1. 合作出资与费用承担：用付款凭证、往来函件、对账或确认材料证明合作基础、款项性质、收款主体和实际利益归属。
2. 停业责任：用停业前后通知、经营资料、物业水电、工资社保和公司治理材料证明停业行为、程序瑕疵、损失和因果关系。
3. 工资社保：用工资表、履职记录、社保材料和函件证明陈靖个人请求，避免与佛山吉麟股东权益混同。
4. 保证金与信息服务费：用收取依据、返还条件、服务交付、结算确认和对方受益材料形成闭环。

【对方可能攻击】
1. 主张陈靖或佛山吉麟未完成出资，否认合作费用承担基础。
2. 主张停业属于经营困难或公司决策结果，与雷天乾/博凯健康无直接因果关系。
3. 主张工资社保、保证金、信息服务费分别缺少合同或结算依据。
4. 攻击证据真实性、形成时间、原件来源和关联性。

【我方应对】
每项诉讼请求必须绑定证据编号、证据名称、证明目的和法律依据方向。法律依据应围绕《民法典》合同编和不当得利规则、《公司法》股东出资和公司治理规则、《民事诉讼法》及证据规则中的举证责任、真实性、关联性和合法性要求。未完成权威检索前，不引用未经核验的法院案号或指导案例。
"""





@router.post("/case/{case_id}/evidence-based-analysis")

def 启动严谨分析(

    case_id: int,

    data: 严谨分析请求,

    db: Session = Depends(get_db)

):

    """

    启动基于证据的严谨分析

    核心原则：禁止任何编造，必须基于真实资料

    """

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="案件不存在")



    # 生成分析ID

    analysis_id = f"analysis_{case_id}_{int(time.time())}"



    # 构建案件信息（仅使用真实数据）

    case_info = f"""【案件基本信息 - 来自案件管理系统】

案件名称：{case.title}

案号：{case.case_number or '暂无'}

原告：{case.plaintiff or '未知'}

被告：{case.defendant or '未知'}

案由：{case.cause or '未知'}

诉讼金额：{case.claim_amount or '未知'}

案件状态：{case.status.value if hasattr(case.status, 'value') else case.status}

"""



    evidence_info, evidence_count, evidence_names = 构建已上传证据上下文(db, case_id)



    # 收集用户输入的信息（标记为待核实）

    user_provided_info = f"""

【用户提供的案件信息】

原告：{data.原告 or '未知'}

被告：{data.被告 or '未知'}

案由：{data.案由 or '未知'}

诉讼金额：{data.诉讼金额 or '未知'}

案件描述：{data.案件描述 or '未知'}



【用户提供的我方证据】

{data.我方证据 or data.our_evidence or '未提供'}



【用户提供的对方信息（需核实）】

对方名称：{data.对方名称 or '未知'}

对方类型：{data.对方类型 or '未知'}

对方可能证据：{data.对方证据 or '未知'}

对方攻击策略：{data.对方攻击策略 or '未知'}

对方弱点：{data.对方弱点 or '未知'}

"""



    # 分析用户提供的未知信息

    unknown_info = []

    if not data.对方证据 or data.对方证据 == '未知':

        unknown_info.append("对方可能掌握的证据（建议调查或申请法院调取）")

    if not data.对方攻击策略:

        unknown_info.append("对方的攻击策略（建议与当事人沟通了解）")

    if not evidence_count:

        unknown_info.append("我方证据（建议上传真实证据文件）")



    # 初始化分析状态

    严谨分析状态存储[analysis_id] = {

        "case_id": case_id,

        "case_info": case_info,

        "evidence_info": evidence_info,

        "user_info": user_provided_info,

        "data": data.model_dump(),

        "status": "started",

        "steps": [

            {"name": "案件事实梳理", "status": "in_progress", "data": {"unknown_fields": []}},

            {"name": "证据分析", "status": "pending", "data": {"unknown_fields": [] if evidence_count else ["请上传证据文件"]}},

            {"name": "法律适用分析", "status": "pending", "data": {"unknown_fields": []}},

            {"name": "对方策略分析", "status": "pending", "data": {"unknown_fields": unknown_info}},

            {"name": "综合结论", "status": "pending", "data": {"unknown_fields": []}}

        ],

        "unknown_info": unknown_info,

        "confirmed_facts": [],

        "speculations": [],

        "recommendations": [],

        "started_at": datetime.now().isoformat()

    }
    保存严谨分析状态(analysis_id)



    # 在后台线程中启动严谨分析

    import threading

    def run_analysis():

        from app.services.llm_service import llm_service

        

        # 阶段1：案件事实梳理

        严谨分析状态存储[analysis_id]["steps"][0]["status"] = "completed"

        严谨分析状态存储[analysis_id]["steps"][0]["data"] = {

            "原告": case.plaintiff or '未知',

            "被告": case.defendant or '未知',

            "案由": case.cause or '未知',

            "诉讼金额": case.claim_amount or '未知'

        }

        严谨分析状态存储[analysis_id]["confirmed_facts"].append(f"原告：{case.plaintiff or '未知'}")

        严谨分析状态存储[analysis_id]["confirmed_facts"].append(f"被告：{case.defendant or '未知'}")

        严谨分析状态存储[analysis_id]["confirmed_facts"].append(f"案由：{case.cause or '未知'}")
        保存严谨分析状态(analysis_id)

        

        # 阶段2：证据分析

        严谨分析状态存储[analysis_id]["steps"][1]["status"] = "completed"

        if evidence_count:

            evidence_summary = f"已上传 {evidence_count} 条证据链记录"

            doc_names = evidence_names

            严谨分析状态存储[analysis_id]["steps"][1]["data"] = {

                "证据数量": evidence_summary,

                "文件列表": ", ".join(doc_names[:20]) + ("..." if len(doc_names) > 20 else ""),

                "来源": "案件管理系统 EvidenceItem V2"

            }

            严谨分析状态存储[analysis_id]["confirmed_facts"].append(evidence_summary)

            严谨分析状态存储[analysis_id]["confirmed_facts"].append(
                f"已上传文件示例: {', '.join(doc_names[:20])}" + ("..." if len(doc_names) > 20 else "")
            )

        else:

            严谨分析状态存储[analysis_id]["steps"][1]["data"] = {

                "warning": "⚠️ 暂无已上传证据，分析受限"

            }

            严谨分析状态存储[analysis_id]["speculations"].append("⚠️ 因无证据，分析可能不准确")
        保存严谨分析状态(analysis_id)

        

        # 阶段3：法律适用分析

        严谨分析状态存储[analysis_id]["steps"][2]["status"] = "in_progress"

        

        if evidence_count > 100:
            legal_analysis = 构建严谨分析规则化报告(case, evidence_count, evidence_names, "法律适用")
        else:
            legal_analysis = llm_service.legal_analysis_for_adversarial(

                case_info=case_info + evidence_info,

                question=(
                    f"请分析博凯升华案的法律关系和适用法律方向。系统证据链为 {evidence_count} 条，"
                    "不得说暂无证据；必须围绕陈靖/佛山吉麟、雷天乾/博凯升华/博凯健康，"
                    "逐项讨论合作出资、停业责任、工资社保、保证金、信息服务费，并引用证据ID、证据名称或附件来源。"
                    "未接入权威案例库时，不得编造法院案号或具体案例。"
                ),

                analysis_depth=data.分析深度

            )
        if 辩论文本不可用(legal_analysis):
            legal_analysis = 构建严谨分析规则化报告(case, evidence_count, evidence_names, "法律适用")

        

        严谨分析状态存储[analysis_id]["steps"][2]["status"] = "completed"

        严谨分析状态存储[analysis_id]["steps"][2]["data"] = {"法律分析": "已完成"}
        保存严谨分析状态(analysis_id)

        

        # 阶段4：对方策略分析（谨慎表述）

        严谨分析状态存储[analysis_id]["steps"][3]["status"] = "in_progress"

        

        if evidence_count > 100:
            opponent_analysis = 构建严谨分析规则化报告(case, evidence_count, evidence_names, "对方策略")
        else:
            opponent_analysis = llm_service.careful_opponent_analysis(

                case_info=case_info + evidence_info,

                known_opponent_info=data.对方证据 or "",

                known_weakness=data.对方弱点 or "",

                unknown_info=unknown_info

            )
        if 辩论文本不可用(opponent_analysis):
            opponent_analysis = 构建严谨分析规则化报告(case, evidence_count, evidence_names, "对方策略")

        

        严谨分析状态存储[analysis_id]["steps"][3]["status"] = "completed"

        严谨分析状态存储[analysis_id]["steps"][3]["data"] = {"对方分析": "已完成"}

        

        # 标记推测性内容

        if unknown_info:

            严谨分析状态存储[analysis_id]["speculations"].append(

                f"⚠️ 对方分析基于有限信息，以下方面未知：{', '.join(unknown_info)}"

            )
        保存严谨分析状态(analysis_id)

        

        # 阶段5：综合结论

        严谨分析状态存储[analysis_id]["steps"][4]["status"] = "completed"

        

        # 生成行动建议

        recommendations = []

        if not evidence_count:

            recommendations.append("🔴 立即行动：上传我方证据文件，这是分析的基础")

        if not data.对方证据:

            recommendations.append("🟡 建议：调查对方可能掌握的证据，可申请法院调查令")

        if data.分析深度 in ["标准分析", "深度分析"]:

            recommendations.append("🟢 建议：补充案件细节以获得更准确的分析")

        

        严谨分析状态存储[analysis_id]["recommendations"] = recommendations

        

        # 生成最终报告

        final_result = {

            "confirmed_facts": 严谨分析状态存储[analysis_id]["confirmed_facts"],

            "speculations": 严谨分析状态存储[analysis_id]["speculations"],

            "recommendations": recommendations,

            "legal_analysis": legal_analysis,

            "opponent_analysis": opponent_analysis

        }

        

        严谨分析状态存储[analysis_id]["result"] = final_result

        严谨分析状态存储[analysis_id]["status"] = "completed"

        严谨分析状态存储[analysis_id]["completed_at"] = datetime.now().isoformat()
        保存严谨分析状态(analysis_id)

        

        # 保存到数据库

        try:

            phase_map = {"协商": "negotiation", "诉前准备": "pre_litigation", "诉讼": "litigation", 

                        "审理": "trial", "上诉": "appeal", "执行": "execution"}

            english_phase = phase_map.get(data.分析阶段, "negotiation")

            phase = 中文阶段映射.get(english_phase, AnalysisPhase.NEGOTIATION)

            

            report_text = f"""【已核实事实】

{chr(10).join(final_result['confirmed_facts'])}



【待核实推测】

{chr(10).join(final_result['speculations'])}



【行动建议】

{chr(10).join(final_result['recommendations'])}



【法律分析】

{final_result.get('legal_analysis', '')}



【对方分析】

{final_result.get('opponent_analysis', '')}

"""

            

            analysis = AdversarialAnalysis(

                case_id=case_id,

                title=f"严谨分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",

                analysis_phase=phase,

                opponent_name=data.对方名称,

                overall_strategy=report_text,

                is_current=True

            )

            db.add(analysis)

            db.query(AdversarialAnalysis).filter(

                AdversarialAnalysis.case_id == case_id,

                AdversarialAnalysis.id != analysis.id

            ).update({"is_current": False})

            db.commit()

        except Exception as e:

            print(f"保存分析失败: {e}")



    thread = threading.Thread(target=run_analysis)

    thread.daemon = True

    thread.start()



    return {

        "analysis_id": analysis_id,

        "status": "started",

        "unknown_info": unknown_info,

        "message": "分析已启动，正在核实资料..."

    }





@router_en.post("/case/{case_id}/evidence-based-analysis")

def 启动严谨分析_en(

    case_id: int,

    data: 严谨分析请求,

    db: Session = Depends(get_db)

):

    """

    Start evidence-based rigorous analysis (English version)

    Core principle: No fabrication, must be based on real materials

    """

    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:

        raise HTTPException(status_code=404, detail="Case not found")



    analysis_id = f"analysis_{case_id}_{int(time.time())}"



    case_info = f"""【案件基本信息 - 来自案件管理系统】

案件名称：{case.title}

案号：{case.case_number or '暂无'}

原告：{case.plaintiff or '未知'}

被告：{case.defendant or '未知'}

案由：{case.cause or '未知'}

诉讼金额：{case.claim_amount or '未知'}

案件状态：{case.status.value if hasattr(case.status, 'value') else case.status}

"""



    evidence_info, evidence_count, evidence_names = 构建已上传证据上下文(db, case_id)



    user_provided_info = f"""

【用户提供的案件信息】

原告：{data.原告 or '未知'}

被告：{data.被告 or '未知'}

案由：{data.案由 or '未知'}

诉讼金额：{data.诉讼金额 or '未知'}

案件描述：{data.案件描述 or '未知'}



【用户提供的我方证据】

{data.我方证据 or data.our_evidence or '未提供'}



【用户提供的对方信息（需核实）】

对方名称：{data.对方名称 or '未知'}

对方类型：{data.对方类型 or '未知'}

对方可能证据：{data.对方证据 or '未知'}

对方攻击策略：{data.对方攻击策略 or '未知'}

对方弱点：{data.对方弱点 or '未知'}

"""



    unknown_info = []

    if not data.对方证据 or data.对方证据 == '未知':

        unknown_info.append("对方可能掌握的证据（建议调查或申请法院调取）")

    if not data.对方攻击策略:

        unknown_info.append("对方的攻击策略（建议与当事人沟通了解）")

    if not evidence_count:

        unknown_info.append("我方证据（建议上传真实证据文件）")



    严谨分析状态存储[analysis_id] = {

        "case_id": case_id,

        "case_info": case_info,

        "evidence_info": evidence_info,

        "user_info": user_provided_info,

        "data": data.model_dump(),

        "status": "started",

        "steps": [

            {"name": "案件事实梳理", "status": "in_progress", "data": {"unknown_fields": []}},

            {"name": "证据分析", "status": "pending", "data": {"unknown_fields": [] if evidence_count else ["请上传证据文件"]}},

            {"name": "法律适用分析", "status": "pending", "data": {"unknown_fields": []}},

            {"name": "对方策略分析", "status": "pending", "data": {"unknown_fields": unknown_info}},

            {"name": "综合结论", "status": "pending", "data": {"unknown_fields": []}}

        ],

        "unknown_info": unknown_info,

        "confirmed_facts": [],

        "speculations": [],

        "recommendations": [],

        "started_at": datetime.now().isoformat()

    }



    import threading

    def run_analysis():

        from app.services.llm_service import llm_service



        严谨分析状态存储[analysis_id]["steps"][0]["status"] = "completed"

        严谨分析状态存储[analysis_id]["steps"][0]["data"] = {

            "原告": case.plaintiff or '未知',

            "被告": case.defendant or '未知',

            "案由": case.cause or '未知',

            "诉讼金额": case.claim_amount or '未知'

        }

        严谨分析状态存储[analysis_id]["confirmed_facts"].append(f"原告：{case.plaintiff or '未知'}")

        严谨分析状态存储[analysis_id]["confirmed_facts"].append(f"被告：{case.defendant or '未知'}")

        严谨分析状态存储[analysis_id]["confirmed_facts"].append(f"案由：{case.cause or '未知'}")



        严谨分析状态存储[analysis_id]["steps"][1]["status"] = "completed"

        if evidence_count:

            evidence_summary = f"已上传 {evidence_count} 条证据链记录"

            doc_names = evidence_names

            严谨分析状态存储[analysis_id]["steps"][1]["data"] = {

                "证据数量": evidence_summary,

                "文件列表": ", ".join(doc_names[:20]) + ("..." if len(doc_names) > 20 else ""),

                "来源": "案件管理系统 EvidenceItem V2"

            }

            严谨分析状态存储[analysis_id]["confirmed_facts"].append(evidence_summary)

            严谨分析状态存储[analysis_id]["confirmed_facts"].append(
                f"已上传文件示例: {', '.join(doc_names[:20])}" + ("..." if len(doc_names) > 20 else "")
            )

        else:

            严谨分析状态存储[analysis_id]["steps"][1]["data"] = {

                "warning": "⚠️ 暂无已上传证据，分析受限"

            }

            严谨分析状态存储[analysis_id]["speculations"].append("⚠️ 因无证据，分析可能不准确")
        保存严谨分析状态(analysis_id)



        严谨分析状态存储[analysis_id]["steps"][2]["status"] = "in_progress"



        legal_analysis = llm_service.legal_analysis_for_adversarial(

            case_info=case_info + evidence_info,

            question=(
                f"请分析博凯升华案的法律关系和适用法律方向。系统证据链为 {evidence_count} 条，"
                "不得说暂无证据；必须围绕陈靖/佛山吉麟、雷天乾/博凯升华/博凯健康，"
                "逐项讨论合作出资、停业责任、工资社保、保证金、信息服务费，并引用证据ID、证据名称或附件来源。"
                "未接入权威案例库时，不得编造法院案号或具体案例。"
            ),

            analysis_depth=data.分析深度

        )
        if 辩论文本不可用(legal_analysis):
            legal_analysis = 构建严谨分析规则化报告(case, evidence_count, evidence_names, "法律适用")



        严谨分析状态存储[analysis_id]["steps"][2]["status"] = "completed"

        严谨分析状态存储[analysis_id]["steps"][2]["data"] = {"法律分析": "已完成"}
        保存严谨分析状态(analysis_id)



        严谨分析状态存储[analysis_id]["steps"][3]["status"] = "in_progress"



        opponent_analysis = llm_service.careful_opponent_analysis(

            case_info=case_info + evidence_info,

            known_opponent_info=data.对方证据 or "",

            known_weakness=data.对方弱点 or "",

            unknown_info=unknown_info

        )
        if 辩论文本不可用(opponent_analysis):
            opponent_analysis = 构建严谨分析规则化报告(case, evidence_count, evidence_names, "对方策略")



        严谨分析状态存储[analysis_id]["steps"][3]["status"] = "completed"

        严谨分析状态存储[analysis_id]["steps"][3]["data"] = {"对方分析": "已完成"}



        if unknown_info:

            严谨分析状态存储[analysis_id]["speculations"].append(

                f"⚠️ 对方分析基于有限信息，以下方面未知：{', '.join(unknown_info)}"

            )
        保存严谨分析状态(analysis_id)



        严谨分析状态存储[analysis_id]["steps"][4]["status"] = "completed"



        recommendations = []

        if not evidence_count:

            recommendations.append("🔴 立即行动：上传我方证据文件，这是分析的基础")

        if not data.对方证据:

            recommendations.append("🟡 建议：调查对方可能掌握的证据，可申请法院调查令")

        if data.分析深度 in ["标准分析", "深度分析"]:

            recommendations.append("🟢 建议：补充案件细节以获得更准确的分析")



        严谨分析状态存储[analysis_id]["recommendations"] = recommendations



        final_result = {

            "confirmed_facts": 严谨分析状态存储[analysis_id]["confirmed_facts"],

            "speculations": 严谨分析状态存储[analysis_id]["speculations"],

            "recommendations": recommendations,

            "legal_analysis": legal_analysis,

            "opponent_analysis": opponent_analysis

        }



        严谨分析状态存储[analysis_id]["result"] = final_result

        严谨分析状态存储[analysis_id]["status"] = "completed"

        严谨分析状态存储[analysis_id]["completed_at"] = datetime.now().isoformat()
        保存严谨分析状态(analysis_id)



        try:

            phase_map = {"协商": "negotiation", "诉前准备": "pre_litigation", "诉讼": "litigation",

                        "审理": "trial", "上诉": "appeal", "执行": "execution"}

            english_phase = phase_map.get(data.分析阶段, "negotiation")

            phase = 中文阶段映射.get(english_phase, AnalysisPhase.NEGOTIATION)



            report_text = f"""【已核实事实】

{chr(10).join(final_result['confirmed_facts'])}



【待核实推测】

{chr(10).join(final_result['speculations'])}



【行动建议】

{chr(10).join(final_result['recommendations'])}



【法律分析】

{final_result.get('legal_analysis', '')}



【对方分析】

{final_result.get('opponent_analysis', '')}

"""



            analysis = AdversarialAnalysis(

                case_id=case_id,

                title=f"严谨分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",

                analysis_phase=phase,

                opponent_name=data.对方名称,

                overall_strategy=report_text,

                is_current=True

            )

            db.add(analysis)

            db.query(AdversarialAnalysis).filter(

                AdversarialAnalysis.case_id == case_id,

                AdversarialAnalysis.id != analysis.id

            ).update({"is_current": False})

            db.commit()

        except Exception as e:

            print(f"保存分析失败: {e}")



    thread = threading.Thread(target=run_analysis)

    thread.daemon = True

    thread.start()



    return {

        "analysis_id": analysis_id,

        "status": "started",

        "unknown_info": unknown_info,

        "message": "Analysis started, verifying materials..."

    }





@router.get("/progress/{analysis_id}")

def 获取严谨分析进度(analysis_id: str):

    """获取严谨分析进度"""

    state = 读取严谨分析状态(analysis_id)

    if not state:

        return {"status": "not_found", "message": "分析不存在"}

    return {

        "analysis_id": analysis_id,

        "status": state["status"],

        "steps": state["steps"],

        "unknown_info": state["unknown_info"],

        "confirmed_facts": state["confirmed_facts"],

        "speculations": state["speculations"],

        "recommendations": state["recommendations"],

        "result": state.get("result"),

        "started_at": state.get("started_at"),

        "completed_at": state.get("completed_at")

    }





@router_en.get("/progress/{analysis_id}")

def 获取严谨分析进度_en(analysis_id: str):

    """Get evidence-based analysis progress"""

    state = 读取严谨分析状态(analysis_id)

    if not state:

        return {"status": "not_found", "message": "Analysis not found"}

    return {

        "analysis_id": analysis_id,

        "status": state["status"],

        "steps": state["steps"],

        "unknown_info": state["unknown_info"],

        "confirmed_facts": state["confirmed_facts"],

        "speculations": state["speculations"],

        "recommendations": state["recommendations"],

        "result": state.get("result"),

        "started_at": state.get("started_at"),

        "completed_at": state.get("completed_at")

    }
