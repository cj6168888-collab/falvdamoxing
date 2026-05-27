"""
项目管理 Facade 服务
===================
为项目提供统一的业务逻辑入口，整合：
- 项目基本 CRUD
- 项目文档管理
- 往来记录管理
- 里程碑管理
- 证据材料管理
- 合同管理
- 风险记录管理
- 法律建议管理
- 统计汇总

Facade 模式：统一入口，渐进拆分
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from app.models.project import (
    Project, ProjectDocument, ProjectCommunication,
    ProjectMilestone, ProjectEvidence, ProjectContract,
    ProjectRisk, ProjectLegalAdvice, ProjectEvent
)
from app.db.database import SessionLocal


class ProjectFacade:
    """
    项目管理统一 Facade

    提供项目全生命周期的业务逻辑整合，
    各子功能通过 facade.xxx 访问独立模块，
    新增代码应尽量添加到子模块而非扩展 facade。
    """

    def __init__(self):
        self._db: Optional[Session] = None

    def _get_db(self) -> Session:
        """获取数据库会话"""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def close(self):
        """关闭数据库会话"""
        if self._db:
            self._db.close()
            self._db = None

    # ==================== 项目 CRUD ====================

    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """获取项目详情"""
        db = self._get_db()
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None
        return self._project_to_dict(project)

    def list_projects(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        project_type: Optional[str] = None,
        search: Optional[str] = None,
        favorites_only: bool = False
    ) -> List[Dict[str, Any]]:
        """查询项目列表"""
        db = self._get_db()
        query = db.query(Project).filter(Project.is_archived == False)

        if status:
            query = query.filter(Project.status == status)
        if project_type:
            query = query.filter(Project.project_type == project_type)
        if search:
            query = query.filter(
                or_(
                    Project.name.ilike(f"%{search}%"),
                    Project.description.ilike(f"%{search}%")
                )
            )
        if favorites_only:
            query = query.filter(Project.is_favorite == True)

        projects = query.order_by(Project.updated_at.desc()).offset(skip).limit(limit).all()
        return [self._project_to_dict(p) for p in projects]

    def create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建项目"""
        db = self._get_db()
        project = Project(
            name=data["name"],
            project_type=data.get("project_type"),
            description=data.get("description"),
            user_role=data.get("user_role"),
            counterpart_name=data.get("counterpart_name"),
            counterpart_type=data.get("counterpart_type"),
            counterpart_contact=data.get("counterpart_contact"),
            start_date=data.get("start_date"),
            expected_end_date=data.get("expected_end_date"),
            amount=data.get("amount"),
            currency=data.get("currency", "CNY"),
            status="planning",
            progress=0.0
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return self._project_to_dict(project)

    def update_project(self, project_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新项目"""
        db = self._get_db()
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        for key, value in data.items():
            if hasattr(project, key) and value is not None:
                setattr(project, key, value)

        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)
        return self._project_to_dict(project)

    def delete_project(self, project_id: int) -> bool:
        """删除项目（软删除：归档）"""
        db = self._get_db()
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        project.is_archived = True
        project.updated_at = datetime.utcnow()
        db.commit()
        return True

    def archive_project(self, project_id: int) -> bool:
        """归档项目"""
        return self.delete_project(project_id)

    def toggle_favorite(self, project_id: int) -> bool:
        """切换收藏状态"""
        db = self._get_db()
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        project.is_favorite = not project.is_favorite
        project.updated_at = datetime.utcnow()
        db.commit()
        return True

    # ==================== 项目文档 ====================

    def create_document(self, project_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建项目文档"""
        db = self._get_db()
        doc = ProjectDocument(
            project_id=project_id,
            doc_type=data.get("doc_type"),
            name=data.get("name"),
            description=data.get("description"),
            source=data.get("source", "self_drafted"),
            content=data.get("content"),
            content_summary=data.get("content_summary")
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return self._doc_to_dict(doc)

    def list_documents(self, project_id: int) -> List[Dict[str, Any]]:
        """获取项目文档列表"""
        db = self._get_db()
        docs = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).order_by(ProjectDocument.created_at.desc()).all()
        return [self._doc_to_dict(d) for d in docs]

    # ==================== 往来记录 ====================

    def create_communication(self, project_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建往来记录"""
        db = self._get_db()
        comm = ProjectCommunication(
            project_id=project_id,
            communication_type=data.get("communication_type"),
            direction=data.get("direction"),
            subject=data.get("subject"),
            content=data.get("content"),
            full_content=data.get("full_content"),
            counterpart_name=data.get("counterpart_name"),
            counterpart_role=data.get("counterpart_role"),
            communication_date=data.get("communication_date")
        )
        db.add(comm)
        db.commit()
        db.refresh(comm)
        return self._comm_to_dict(comm)

    def list_communications(self, project_id: int) -> List[Dict[str, Any]]:
        """获取往来记录列表"""
        db = self._get_db()
        comms = db.query(ProjectCommunication).filter(
            ProjectCommunication.project_id == project_id
        ).order_by(ProjectCommunication.communication_date.desc()).all()
        return [self._comm_to_dict(c) for c in comms]

    # ==================== 里程碑 ====================

    def create_milestone(self, project_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建里程碑"""
        db = self._get_db()
        milestone = ProjectMilestone(
            project_id=project_id,
            name=data.get("name"),
            description=data.get("description"),
            milestone_type=data.get("milestone_type"),
            phase=data.get("phase"),
            planned_date=data.get("planned_date")
        )
        db.add(milestone)
        db.commit()
        db.refresh(milestone)
        return self._milestone_to_dict(milestone)

    def list_milestones(self, project_id: int) -> List[Dict[str, Any]]:
        """获取里程碑列表"""
        db = self._get_db()
        milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project_id
        ).order_by(ProjectMilestone.planned_date.asc()).all()
        return [self._milestone_to_dict(m) for m in milestones]

    # ==================== 证据材料 ====================

    def create_evidence(self, project_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建证据材料"""
        db = self._get_db()
        evidence = ProjectEvidence(
            project_id=project_id,
            evidence_type=data.get("evidence_type"),
            name=data.get("name"),
            description=data.get("description"),
            source=data.get("source"),
            content=data.get("content"),
            content_summary=data.get("content_summary")
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        return self._evidence_to_dict(evidence)

    def list_evidence(self, project_id: int) -> List[Dict[str, Any]]:
        """获取证据材料列表"""
        db = self._get_db()
        evidences = db.query(ProjectEvidence).filter(
            ProjectEvidence.project_id == project_id
        ).order_by(ProjectEvidence.created_at.desc()).all()
        return [self._evidence_to_dict(e) for e in evidences]

    # ==================== 合同管理 ====================

    def create_contract(self, project_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建合同"""
        db = self._get_db()
        contract = ProjectContract(
            project_id=project_id,
            contract_name=data.get("contract_name"),
            contract_type=data.get("contract_type"),
            party_a=data.get("party_a"),
            party_b=data.get("party_b"),
            amount=data.get("amount"),
            signing_date=data.get("signing_date"),
            effective_date=data.get("effective_date"),
            expiration_date=data.get("expiration_date")
        )
        db.add(contract)
        db.commit()
        db.refresh(contract)
        return self._contract_to_dict(contract)

    def list_contracts(self, project_id: int) -> List[Dict[str, Any]]:
        """获取合同列表"""
        db = self._get_db()
        contracts = db.query(ProjectContract).filter(
            ProjectContract.project_id == project_id
        ).order_by(ProjectContract.signing_date.desc()).all()
        return [self._contract_to_dict(c) for c in contracts]

    # ==================== 风险记录 ====================

    def create_risk(self, project_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建风险记录"""
        db = self._get_db()
        risk = ProjectRisk(
            project_id=project_id,
            risk_type=data.get("risk_type"),
            title=data.get("title"),
            description=data.get("description"),
            severity=data.get("severity", "medium"),
            probability=data.get("probability", "medium"),
            impact=data.get("impact", "medium"),
            mitigation_plan=data.get("mitigation_plan")
        )
        db.add(risk)
        db.commit()
        db.refresh(risk)
        return self._risk_to_dict(risk)

    def list_risks(self, project_id: int) -> List[Dict[str, Any]]:
        """获取风险列表"""
        db = self._get_db()
        risks = db.query(ProjectRisk).filter(
            ProjectRisk.project_id == project_id
        ).order_by(ProjectRisk.created_at.desc()).all()
        return [self._risk_to_dict(r) for r in risks]

    # ==================== 法律建议 ====================

    def list_advices(self, project_id: int) -> List[Dict[str, Any]]:
        """获取法律建议列表"""
        db = self._get_db()
        advices = db.query(ProjectLegalAdvice).filter(
            ProjectLegalAdvice.project_id == project_id
        ).order_by(ProjectLegalAdvice.created_at.desc()).all()
        return [self._advice_to_dict(a) for a in advices]

    # ==================== 项目统计 ====================

    def get_stats(self) -> Dict[str, Any]:
        """获取项目统计信息"""
        db = self._get_db()
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

    # ==================== 项目事件 ====================

    def add_event(
        self,
        project_id: int,
        event_type: str,
        title: str,
        description: str = "",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """添加项目事件记录"""
        db = self._get_db()
        event = ProjectEvent(
            project_id=project_id,
            event_type=event_type,
            title=title,
            description=description,
            metadata_json=metadata
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return self._event_to_dict(event)

    # ==================== 序列化辅助 ====================

    def _project_to_dict(self, p: Project) -> Dict[str, Any]:
        return {
            "id": p.id,
            "name": p.name,
            "project_type": p.project_type,
            "description": p.description,
            "user_role": p.user_role,
            "counterpart_name": p.counterpart_name,
            "counterpart_type": p.counterpart_type,
            "counterpart_contact": p.counterpart_contact,
            "start_date": p.start_date,
            "expected_end_date": p.expected_end_date,
            "actual_end_date": p.actual_end_date,
            "status": p.status,
            "current_phase": p.current_phase,
            "amount": p.amount,
            "currency": p.currency,
            "progress": p.progress,
            "risk_level": p.risk_level,
            "legal_analysis": p.legal_analysis,
            "legal_advice": p.legal_advice,
            "notes": p.notes,
            "is_favorite": p.is_favorite,
            "is_archived": p.is_archived,
            "tags": p.tags or [],
            "created_at": p.created_at,
            "updated_at": p.updated_at
        }

    def _doc_to_dict(self, d: ProjectDocument) -> Dict[str, Any]:
        return {
            "id": d.id,
            "doc_type": d.doc_type,
            "name": d.name,
            "description": d.description,
            "source": d.source,
            "content": d.content,
            "content_summary": d.content_summary,
            "created_at": d.created_at
        }

    def _comm_to_dict(self, c: ProjectCommunication) -> Dict[str, Any]:
        return {
            "id": c.id,
            "communication_type": c.communication_type,
            "direction": c.direction,
            "subject": c.subject,
            "content": c.content,
            "full_content": c.full_content,
            "counterpart_name": c.counterpart_name,
            "counterpart_role": c.counterpart_role,
            "communication_date": c.communication_date,
            "created_at": c.created_at
        }

    def _milestone_to_dict(self, m: ProjectMilestone) -> Dict[str, Any]:
        return {
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "milestone_type": m.milestone_type,
            "phase": m.phase,
            "planned_date": m.planned_date,
            "actual_date": m.actual_date,
            "status": m.status,
            "notes": m.notes,
            "created_at": m.created_at
        }

    def _evidence_to_dict(self, e: ProjectEvidence) -> Dict[str, Any]:
        return {
            "id": e.id,
            "evidence_type": e.evidence_type,
            "name": e.name,
            "description": e.description,
            "source": e.source,
            "content": e.content,
            "content_summary": e.content_summary,
            "created_at": e.created_at
        }

    def _contract_to_dict(self, c: ProjectContract) -> Dict[str, Any]:
        return {
            "id": c.id,
            "contract_name": c.contract_name,
            "contract_type": c.contract_type,
            "party_a": c.party_a,
            "party_b": c.party_b,
            "amount": c.amount,
            "signing_date": c.signing_date,
            "effective_date": c.effective_date,
            "expiration_date": c.expiration_date,
            "created_at": c.created_at
        }

    def _risk_to_dict(self, r: ProjectRisk) -> Dict[str, Any]:
        return {
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

    def _advice_to_dict(self, a: ProjectLegalAdvice) -> Dict[str, Any]:
        return {
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

    def _event_to_dict(self, e: ProjectEvent) -> Dict[str, Any]:
        return {
            "id": e.id,
            "event_type": e.event_type,
            "title": e.title,
            "description": e.description,
            "metadata": e.metadata_json,
            "created_at": e.created_at
        }


# 单例
project_facade = ProjectFacade()
