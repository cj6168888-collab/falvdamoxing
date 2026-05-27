"""
项目API服务
提供项目的创建、查询、更新、删除等功能
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import json

from app.models.project import (
    Project, ProjectType, ProjectStatus, ProjectPhase, UserRole,
    ProjectDocument, ProjectMilestone, ProjectCommunication, ProjectEvidence,
    ProjectLegalAdvice, ProjectEvent, ProjectContract, ProjectRisk, ProjectToCase
)
from app.db.database import SessionLocal, engine
from sqlalchemy.orm import Session
from sqlalchemy import or_, nullslast

router = APIRouter(prefix="/api/projects", tags=["项目管理"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============ 枚举定义 ============
class ProjectTypeEnum(str, Enum):
    """项目类型枚举"""
    BUSINESS_COOPERATION = "商业合作"
    INVESTMENT = "投资"
    PARTNERSHIP = "合伙/合作"
    JOINT_VENTURE = "合资企业"
    FRANCHISE = "特许经营"
    EMPLOYMENT = "劳动合同"
    PERSONAL_SERVICE = "劳务/服务"
    FREELANCE = "自由职业"
    PURCHASE = "采购合同"
    SALE = "销售合同"
    LEASE = "租赁"
    LOAN = "借贷"
    MORTGAGE = "抵押/担保"
    MARRIAGE = "婚姻家庭"
    DIVORCE = "离婚"
    INHERITANCE = "继承"
    PROPERTY_PURCHASE = "房产交易"
    VEHICLE = "车辆交易"
    COPYRIGHT = "著作权"
    TRADEMARK = "商标"
    CONSUMER_DISPUTE = "消费纠纷"
    NEIGHBOR_DISPUTE = "邻里纠纷"
    PERSONAL_INJURY = "人身损害"
    TRAFFIC_ACCIDENT = "交通事故"
    COMPLIANCE = "合规审查"
    OTHER = "其他"


class ProjectStatusEnum(str, Enum):
    """项目状态枚举"""
    PLANNING = "筹划中"
    NEGOTIATION = "洽谈中"
    DRAFTING = "起草/审核中"
    EXECUTING = "执行中"
    MONITORING = "监控中"
    COMPLETED = "已完成"
    DISPUTE = "发生纠纷"
    LITIGATION = "转入诉讼"
    SUSPENDED = "暂停"
    TERMINATED = "已终止"


class ProjectPhaseEnum(str, Enum):
    """项目阶段枚举"""
    INITIATION = "发起/启动"
    DUE_DILIGENCE = "尽职调查"
    NEGOTIATION = "谈判"
    DRAFTING = "起草合同"
    REVIEW = "审核"
    SIGNING = "签约"
    PERFORMANCE = "履行"
    MONITORING = "履约监控"
    COMPLETION = "完成/结算"
    EARLY_WARNING = "预警信号"
    NEGOTIATION_SETTLEMENT = "协商解决"
    MEDIATION = "调解"
    LITIGATION = "诉讼"


class UserRoleEnum(str, Enum):
    """用户角色枚举"""
    INDIVIDUAL = "个人"
    EMPLOYEE = "员工"
    EMPLOYER = "雇主"
    BUSINESS = "企业主"
    INVESTOR = "投资者"
    LANDLORD = "房东"
    TENANT = "租客"
    CONSUMER = "消费者"
    SELLER = "销售方"
    BUYER = "采购方"
    PARENT = "家长"
    CHILD = "子女"
    OTHER = "其他"


# ============ 枚举映射 ============
# 中文到英文枚举值的映射
PROJECT_TYPE_MAP = {
    "商业合作": "business_coopertion",  # 注意: 保持与数据库一致的拼写
    "投资": "investment",
    "合伙/合作": "partnership",
    "合资企业": "joint_venture",
    "特许经营": "franchise",
    "劳动合同": "employment",
    "劳务/服务": "personal_service",
    "自由职业": "freelance",
    "采购合同": "purchase",
    "销售合同": "sale",
    "租赁": "lease",
    "借贷": "loan",
    "抵押/担保": "mortgage",
    "婚姻家庭": "marriage",
    "离婚": "divorce",
    "继承": "inheritance",
    "房产交易": "property_purchase",
    "车辆交易": "vehicle",
    "著作权": "copyright",
    "商标": "trademark",
    "消费纠纷": "consumer_dispute",
    "邻里纠纷": "neighbor_dispute",
    "人身损害": "personal_injury",
    "交通事故": "traffic_accident",
    "合规审查": "compliance",
    "其他": "other",
}

PROJECT_STATUS_MAP = {
    "筹划中": "planning",
    "洽谈中": "negotiation",
    "起草/审核中": "drafting",
    "执行中": "executing",
    "监控中": "monitoring",
    "已完成": "completed",
    "发生纠纷": "dispute",
    "转入诉讼": "litigation",
    "暂停": "suspended",
    "已终止": "terminated",
}

PROJECT_PHASE_MAP = {
    "发起/启动": "initiation",
    "尽职调查": "due_diligence",
    "谈判": "negotiation",
    "起草合同": "drafting",
    "审核": "review",
    "签约": "signing",
    "履行": "performance",
    "履约监控": "monitoring",
    "完成/结算": "completion",
    "预警信号": "early_warning",
    "协商解决": "negotiation_settlement",
    "调解": "mediation",
    "诉讼": "litigation",
}

USER_ROLE_MAP = {
    "个人": "individual",
    "员工": "employee",
    "雇主": "employer",
    "企业主": "business",
    "投资者": "investor",
    "房东": "landlord",
    "租客": "tenant",
    "消费者": "consumer",
    "销售方": "seller",
    "采购方": "buyer",
    "家长": "parent",
    "子女": "child",
    "其他": "other",
}


def convert_to_enum(value: str, mapping: dict, enum_class):
    """将中文值转换为枚举"""
    if not value:
        return None
    # 如果已经是枚举值（英文），直接返回
    try:
        return enum_class(value)
    except (ValueError, TypeError):
        pass
    # 尝试从映射表转换
    english_value = mapping.get(value)
    if english_value:
        try:
            return enum_class(english_value)
        except (ValueError, TypeError):
            pass
    # 如果都失败，返回默认值
    return None


# ============ Pydantic 模型 ============
class ProjectCreate(BaseModel):
    """创建项目请求"""
    name: str = Field(..., description="项目名称")
    project_type: str = Field(..., description="项目类型")
    description: Optional[str] = Field(None, description="项目描述")
    user_role: str = Field("个人", description="用户角色")
    counterpart_name: Optional[str] = Field(None, description="对方名称")
    counterpart_type: Optional[str] = Field(None, description="对方类型")
    counterpart_contact: Optional[str] = Field(None, description="对方联系方式")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    expected_end_date: Optional[datetime] = Field(None, description="预期结束日期")
    amount: Optional[str] = Field(None, description="涉及金额")
    currency: str = Field("CNY", description="币种")


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = None
    project_type: Optional[str] = None
    description: Optional[str] = None
    user_role: Optional[str] = None
    counterpart_name: Optional[str] = None
    counterpart_type: Optional[str] = None
    counterpart_contact: Optional[str] = None
    start_date: Optional[datetime] = None
    expected_end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    status: Optional[str] = None
    current_phase: Optional[str] = None
    amount: Optional[str] = None
    risk_level: Optional[str] = None
    progress: Optional[float] = None
    legal_analysis: Optional[str] = None
    legal_advice: Optional[str] = None
    notes: Optional[str] = None
    is_favorite: Optional[bool] = None
    tags: Optional[List[str]] = None


class ProjectDocumentCreate(BaseModel):
    """创建项目文档请求"""
    doc_type: str = Field(..., description="文档类型")
    name: str = Field(..., description="文档名称")
    description: Optional[str] = None
    source: Optional[str] = "self_drafted"
    content: Optional[str] = None
    content_summary: Optional[str] = None


class ProjectCommunicationCreate(BaseModel):
    """创建往来记录请求"""
    communication_type: str = Field(..., description="沟通类型")
    direction: str = Field(..., description="方向: incoming/outgoing")
    subject: Optional[str] = None
    content: Optional[str] = None
    full_content: Optional[str] = None
    counterpart_name: Optional[str] = None
    counterpart_role: Optional[str] = None
    communication_date: Optional[datetime] = None


class ProjectMilestoneCreate(BaseModel):
    """创建里程碑请求"""
    name: str = Field(..., description="里程碑名称")
    description: Optional[str] = None
    milestone_type: Optional[str] = None
    phase: Optional[str] = None
    planned_date: Optional[datetime] = None


class ProjectEvidenceCreate(BaseModel):
    """创建证据材料请求"""
    evidence_type: str = Field(..., description="证据类型")
    name: str = Field(..., description="证据名称")
    description: Optional[str] = None
    source: Optional[str] = None
    content: Optional[str] = None
    content_summary: Optional[str] = None


class ProjectContractCreate(BaseModel):
    """创建合同请求"""
    contract_name: str = Field(..., description="合同名称")
    contract_type: Optional[str] = None
    party_a: Optional[str] = None
    party_b: Optional[str] = None
    amount: Optional[str] = None
    signing_date: Optional[datetime] = None
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None


class ProjectRiskCreate(BaseModel):
    """创建风险记录请求"""
    risk_type: str = Field(..., description="风险类型")
    title: str = Field(..., description="风险标题")
    description: Optional[str] = None
    severity: str = Field("medium", description="严重程度")
    probability: str = Field("medium", description="发生概率")
    impact: str = Field("medium", description="影响程度")
    mitigation_plan: Optional[str] = None


class ProjectMutationResponse(BaseModel):
    id: Optional[int] = None
    message: str


class ProjectFavoriteResponse(BaseModel):
    id: int
    is_favorite: bool
    message: str


class ProjectListItemResponse(BaseModel):
    id: int
    name: str
    project_type: Optional[str] = None
    description: Optional[str] = None
    user_role: Optional[str] = None
    counterpart_name: Optional[str] = None
    status: Optional[str] = None
    current_phase: Optional[str] = None
    risk_level: Optional[str] = None
    progress: Optional[float] = None
    start_date: Optional[datetime] = None
    expected_end_date: Optional[datetime] = None
    amount: Optional[str] = None
    is_favorite: Optional[bool] = None
    tags: Optional[Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProjectDetailResponse(ProjectListItemResponse):
    counterpart_type: Optional[str] = None
    counterpart_contact: Optional[str] = None
    actual_end_date: Optional[datetime] = None
    currency: Optional[str] = None
    risk_factors: Optional[Any] = None
    legal_analysis: Optional[str] = None
    legal_advice: Optional[str] = None
    contract_review: Optional[str] = None
    notes: Optional[str] = None


class ProjectStatsResponse(BaseModel):
    total: int
    active: int
    disputes: int
    completed: int
    favorites: int


# ============ 项目 CRUD ============
@router.post("/", response_model=ProjectMutationResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """创建新项目"""
    # 转换枚举值
    project_type_enum = convert_to_enum(project.project_type, PROJECT_TYPE_MAP, ProjectType)
    user_role_enum = convert_to_enum(project.user_role, USER_ROLE_MAP, UserRole)
    
    db_project = Project(
        name=project.name,
        project_type=project_type_enum or ProjectType.OTHER,
        description=project.description,
        user_role=user_role_enum or UserRole.INDIVIDUAL,
        counterpart_name=project.counterpart_name,
        counterpart_type=project.counterpart_type,
        counterpart_contact=project.counterpart_contact,
        start_date=project.start_date,
        expected_end_date=project.expected_end_date,
        amount=project.amount,
        currency=project.currency,
        status=ProjectStatus.PLANNING,
        current_phase=ProjectPhase.INITIATION
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return {"id": db_project.id, "message": "项目创建成功"}


@router.get("/", response_model=List[ProjectListItemResponse])
def list_projects(
    status: Optional[str] = None,
    project_type: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    is_archived: Optional[bool] = False,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    query = db.query(Project)
    
    if not is_archived:
        query = query.filter(Project.is_archived == False)
    else:
        query = query.filter(Project.is_archived == True)
    
    if status:
        query = query.filter(Project.status == status)
    if project_type:
        query = query.filter(Project.project_type == project_type)
    if is_favorite is not None:
        query = query.filter(Project.is_favorite == is_favorite)
    if search:
        query = query.filter(
            or_(
                Project.name.contains(search),
                Project.description.contains(search),
                Project.counterpart_name.contains(search)
            )
        )
    
    projects = query.order_by(Project.updated_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for p in projects:
        result.append({
            "id": p.id,
            "name": p.name,
            "project_type": p.project_type.value if hasattr(p.project_type, 'value') else str(p.project_type),
            "description": p.description,
            "user_role": p.user_role.value if hasattr(p.user_role, 'value') else str(p.user_role),
            "counterpart_name": p.counterpart_name,
            "status": p.status.value if hasattr(p.status, 'value') else str(p.status),
            "current_phase": p.current_phase.value if hasattr(p.current_phase, 'value') else str(p.current_phase),
            "risk_level": p.risk_level.value if hasattr(p.risk_level, 'value') else str(p.risk_level),
            "progress": p.progress,
            "start_date": p.start_date,
            "expected_end_date": p.expected_end_date,
            "amount": p.amount,
            "is_favorite": p.is_favorite,
            "tags": p.tags,
            "created_at": p.created_at,
            "updated_at": p.updated_at
        })
    
    return result


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """获取项目详情"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return {
        "id": project.id,
        "name": project.name,
        "project_type": project.project_type,
        "description": project.description,
        "user_role": project.user_role,
        "counterpart_name": project.counterpart_name,
        "counterpart_type": project.counterpart_type,
        "counterpart_contact": project.counterpart_contact,
        "start_date": project.start_date,
        "expected_end_date": project.expected_end_date,
        "actual_end_date": project.actual_end_date,
        "status": project.status,
        "current_phase": project.current_phase,
        "amount": project.amount,
        "currency": project.currency,
        "risk_level": project.risk_level,
        "risk_factors": project.risk_factors,
        "progress": project.progress,
        "legal_analysis": project.legal_analysis,
        "legal_advice": project.legal_advice,
        "contract_review": project.contract_review,
        "is_favorite": project.is_favorite,
        "tags": project.tags,
        "notes": project.notes,
        "created_at": project.created_at,
        "updated_at": project.updated_at
    }


@router.put("/{project_id}", response_model=ProjectMutationResponse)
def update_project(project_id: int, project_update: ProjectUpdate, db: Session = Depends(get_db)):
    """更新项目"""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    update_data = project_update.dict(exclude_unset=True)
    if 'tags' in update_data and update_data['tags']:
        update_data['tags'] = json.dumps(update_data['tags'])
    
    for key, value in update_data.items():
        setattr(db_project, key, value)
    
    db_project.updated_at = datetime.utcnow()
    db.commit()
    
    return {"id": project_id, "message": "项目更新成功"}


@router.delete("/{project_id}", response_model=ProjectMutationResponse)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """删除项目"""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db.delete(db_project)
    db.commit()
    
    return {"message": "项目删除成功"}


@router.post("/{project_id}/archive", response_model=ProjectMutationResponse)
def archive_project(project_id: int, db: Session = Depends(get_db)):
    """归档项目"""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db_project.is_archived = True
    db_project.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "项目归档成功"}


@router.post("/{project_id}/favorite", response_model=ProjectFavoriteResponse)
def toggle_favorite(project_id: int, db: Session = Depends(get_db)):
    """切换收藏状态"""
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db_project.is_favorite = not db_project.is_favorite
    db_project.updated_at = datetime.utcnow()
    db.commit()
    
    return {"id": project_id, "is_favorite": db_project.is_favorite, "message": "收藏状态已更新"}


# ============ 项目文档 ============
@router.post("/{project_id}/documents", response_model=Dict)
def create_document(project_id: int, doc: ProjectDocumentCreate, db: Session = Depends(get_db)):
    """添加项目文档"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db_doc = ProjectDocument(
        project_id=project_id,
        doc_type=doc.doc_type,
        name=doc.name,
        description=doc.description,
        source=doc.source,
        content=doc.content,
        content_summary=doc.content_summary
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    return {"id": db_doc.id, "message": "文档添加成功"}


@router.get("/{project_id}/documents", response_model=List[Dict])
def list_documents(project_id: int, db: Session = Depends(get_db)):
    """获取项目文档列表"""
    docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id
    ).order_by(ProjectDocument.created_at.desc()).all()
    
    return [
        {
            "id": d.id,
            "doc_type": d.doc_type,
            "name": d.name,
            "description": d.description,
            "source": d.source,
            "content": d.content,
            "content_summary": d.content_summary,
            "ai_review": d.ai_review,
            "status": d.status,
            "version": d.version,
            "created_at": d.created_at
        }
        for d in docs
    ]


# ============ 往来记录 ============
@router.post("/{project_id}/communications", response_model=Dict)
def create_communication(project_id: int, comm: ProjectCommunicationCreate, db: Session = Depends(get_db)):
    """添加往来记录"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db_comm = ProjectCommunication(
        project_id=project_id,
        communication_type=comm.communication_type,
        direction=comm.direction,
        subject=comm.subject,
        content=comm.content,
        full_content=comm.full_content,
        counterpart_name=comm.counterpart_name,
        counterpart_role=comm.counterpart_role,
        communication_date=comm.communication_date
    )
    db.add(db_comm)
    db.commit()
    db.refresh(db_comm)
    
    return {"id": db_comm.id, "message": "往来记录添加成功"}


@router.get("/{project_id}/communications", response_model=List[Dict])
def list_communications(project_id: int, db: Session = Depends(get_db)):
    """获取往来记录列表"""
    comms = db.query(ProjectCommunication).filter(
        ProjectCommunication.project_id == project_id
    ).order_by(ProjectCommunication.communication_date.desc()).all()
    
    return [
        {
            "id": c.id,
            "communication_type": c.communication_type,
            "direction": c.direction,
            "subject": c.subject,
            "content": c.content,
            "counterpart_name": c.counterpart_name,
            "communication_date": c.communication_date,
            "ai_summary": c.ai_summary,
            "evidence_value": c.evidence_value,
            "is_key_evidence": c.is_key_evidence,
            "created_at": c.created_at
        }
        for c in comms
    ]


# ============ 里程碑 ============
@router.post("/{project_id}/milestones", response_model=Dict)
def create_milestone(project_id: int, milestone: ProjectMilestoneCreate, db: Session = Depends(get_db)):
    """添加里程碑"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db_milestone = ProjectMilestone(
        project_id=project_id,
        name=milestone.name,
        description=milestone.description,
        milestone_type=milestone.milestone_type,
        phase=milestone.phase,
        planned_date=milestone.planned_date
    )
    db.add(db_milestone)
    db.commit()
    db.refresh(db_milestone)
    
    return {"id": db_milestone.id, "message": "里程碑添加成功"}


@router.get("/{project_id}/milestones", response_model=List[Dict])
def list_milestones(project_id: int, db: Session = Depends(get_db)):
    """获取里程碑列表"""
    milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id
    ).order_by(ProjectMilestone.planned_date.asc().nullslast(), ProjectMilestone.order.asc()).all()
    
    return [
        {
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "milestone_type": m.milestone_type,
            "phase": m.phase,
            "planned_date": m.planned_date,
            "actual_date": m.actual_date,
            "status": m.status,
            "ai_reminder": m.ai_reminder,
            "legal_tips": m.legal_tips,
            "order": m.order
        }
        for m in milestones
    ]


# ============ 证据材料 ============
@router.post("/{project_id}/evidence", response_model=Dict)
def create_evidence(project_id: int, evidence: ProjectEvidenceCreate, db: Session = Depends(get_db)):
    """添加证据材料"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db_evidence = ProjectEvidence(
        project_id=project_id,
        evidence_type=evidence.evidence_type,
        name=evidence.name,
        description=evidence.description,
        source=evidence.source,
        content=evidence.content,
        content_summary=evidence.content_summary
    )
    db.add(db_evidence)
    db.commit()
    db.refresh(db_evidence)
    
    return {"id": db_evidence.id, "message": "证据材料添加成功"}


@router.get("/{project_id}/evidence", response_model=List[Dict])
def list_evidence(project_id: int, db: Session = Depends(get_db)):
    """获取证据材料列表"""
    evidence_list = db.query(ProjectEvidence).filter(
        ProjectEvidence.project_id == project_id
    ).order_by(ProjectEvidence.created_at.desc()).all()
    
    return [
        {
            "id": e.id,
            "evidence_type": e.evidence_type,
            "name": e.name,
            "description": e.description,
            "source": e.source,
            "content": e.content,
            "content_summary": e.content_summary,
            "probative_value": e.probative_value,
            "authenticity": e.authenticity,
            "ai_analysis": e.ai_analysis,
            "status": e.status,
            "is_key_evidence": e.is_key_evidence,
            "completeness": e.completeness,
            "created_at": e.created_at
        }
        for e in evidence_list
    ]


# ============ 合同管理 ============
@router.post("/{project_id}/contracts", response_model=Dict)
def create_contract(project_id: int, contract: ProjectContractCreate, db: Session = Depends(get_db)):
    """添加合同"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db_contract = ProjectContract(
        project_id=project_id,
        contract_name=contract.contract_name,
        contract_type=contract.contract_type,
        party_a=contract.party_a,
        party_b=contract.party_b,
        amount=contract.amount,
        signing_date=contract.signing_date,
        effective_date=contract.effective_date,
        expiration_date=contract.expiration_date
    )
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    
    return {"id": db_contract.id, "message": "合同添加成功"}


@router.get("/{project_id}/contracts", response_model=List[Dict])
def list_contracts(project_id: int, db: Session = Depends(get_db)):
    """获取合同列表"""
    contracts = db.query(ProjectContract).filter(
        ProjectContract.project_id == project_id
    ).order_by(ProjectContract.created_at.desc()).all()
    
    return [
        {
            "id": c.id,
            "contract_name": c.contract_name,
            "contract_type": c.contract_type,
            "party_a": c.party_a,
            "party_b": c.party_b,
            "amount": c.amount,
            "signing_date": c.signing_date,
            "effective_date": c.effective_date,
            "expiration_date": c.expiration_date,
            "status": c.status,
            "ai_review": c.ai_review,
            "risk_level": c.risk_level,
            "performance_status": c.performance_status,
            "created_at": c.created_at
        }
        for c in contracts
    ]


# ============ 风险记录 ============
@router.post("/{project_id}/risks", response_model=Dict)
def create_risk(project_id: int, risk: ProjectRiskCreate, db: Session = Depends(get_db)):
    """添加风险记录"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db_risk = ProjectRisk(
        project_id=project_id,
        risk_type=risk.risk_type,
        title=risk.title,
        description=risk.description,
        severity=risk.severity,
        probability=risk.probability,
        impact=risk.impact,
        mitigation_plan=risk.mitigation_plan
    )
    db.add(db_risk)
    db.commit()
    db.refresh(db_risk)
    
    return {"id": db_risk.id, "message": "风险记录添加成功"}


@router.get("/{project_id}/risks", response_model=List[Dict])
def list_risks(project_id: int, db: Session = Depends(get_db)):
    """获取风险列表"""
    risks = db.query(ProjectRisk).filter(
        ProjectRisk.project_id == project_id
    ).order_by(ProjectRisk.created_at.desc()).all()
    
    return [
        {
            "id": r.id,
            "risk_type": r.risk_type,
            "title": r.title,
            "description": r.description,
            "severity": r.severity,
            "probability": r.probability,
            "impact": r.impact,
            "status": r.status,
            "mitigation_plan": r.mitigation_plan,
            "preventive_measures": r.preventive_measures,
            "is_monitored": r.is_monitored,
            "created_at": r.created_at
        }
        for r in risks
    ]


# ============ 法律建议 ============
@router.get("/{project_id}/advices", response_model=List[Dict])
def list_advices(project_id: int, db: Session = Depends(get_db)):
    """获取法律建议列表"""
    advices = db.query(ProjectLegalAdvice).filter(
        ProjectLegalAdvice.project_id == project_id
    ).order_by(ProjectLegalAdvice.created_at.desc()).all()
    
    return [
        {
            "id": a.id,
            "advice_type": a.advice_type,
            "title": a.title,
            "content": a.content,
            "applicable_phase": a.applicable_phase,
            "urgency": a.urgency,
            "is_read": a.is_read,
            "is_acted": a.is_acted,
            "action_taken": a.action_taken,
            "confidence": a.confidence,
            "created_at": a.created_at
        }
        for a in advices
    ]


# ============ 项目统计 ============
@router.get("/stats/summary", response_model=ProjectStatsResponse)
def get_project_stats(db: Session = Depends(get_db)):
    """获取项目统计信息"""
    total = db.query(Project).filter(Project.is_archived == False).count()
    active = db.query(Project).filter(
        Project.is_archived == False,
        Project.status.in_(["planning", "negotiation", "drafting", "executing", "monitoring"])
    ).count()
    disputes = db.query(Project).filter(
        Project.is_archived == False,
        Project.status == "dispute"
    ).count()
    completed = db.query(Project).filter(
        Project.is_archived == False,
        Project.status == "completed"
    ).count()
    favorites = db.query(Project).filter(
        Project.is_archived == False,
        Project.is_favorite == True
    ).count()
    
    return {
        "total": total,
        "active": active,
        "disputes": disputes,
        "completed": completed,
        "favorites": favorites
    }
