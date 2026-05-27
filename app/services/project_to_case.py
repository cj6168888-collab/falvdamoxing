"""
项目转案件服务
处理项目发展为诉讼时的数据迁移
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.db.database import SessionLocal
from app.models.project import (
    Project, ProjectDocument, ProjectCommunication, ProjectEvidence,
    ProjectContract, ProjectRisk, ProjectEvent, ProjectToCase
)
from app.models.case import Case, CaseParty, Evidence, Document, CaseTimeline


class ProjectToCaseConverter:
    """项目转案件转换器"""
    
    def __init__(self, project_id: int):
        self.project_id = project_id
        self.db = SessionLocal()
        self.project = None
        self.case_id = None
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
        
    def load_project(self) -> bool:
        """加载项目"""
        self.project = self.db.query(Project).filter(
            Project.id == self.project_id
        ).first()
        return self.project is not None
    
    def convert(self, case_data: Dict[str, Any], conversion_reason: str = "") -> Optional[int]:
        """
        执行转换
        case_data: 案件基本信息
        """
        if not self.project:
            if not self.load_project():
                raise ValueError(f"项目 {self.project_id} 不存在")
        
        try:
            # 1. 创建案件记录
            case = Case(
                case_number=case_data.get("case_number", ""),
                case_title=f"[来自项目] {self.project.name}",
                case_type=case_data.get("case_type", "civil"),
                case_status="pending",
                description=f"由项目转换: {self.project.description or ''}",
                plaintiff_name=case_data.get("plaintiff_name", ""),
                plaintiff_contact=case_data.get("plaintiff_contact", ""),
                defendant_name=case_data.get("defendant_name", self.project.counterpart_name or ""),
                defendant_contact=case_data.get("defendant_contact", self.project.counterpart_contact or ""),
                court=case_data.get("court", ""),
                judge=case_data.get("judge", ""),
                legal_basis=case_data.get("legal_basis", ""),
                litigation_amount=self.project.amount,
                is_archived=False
            )
            self.db.add(case)
            self.db.flush()
            
            # 2. 创建案件关联的当事人
            if case_data.get("plaintiff_name"):
                plaintiff = CaseParty(
                    case_id=case.id,
                    party_type="plaintiff",
                    name=case_data["plaintiff_name"],
                    contact=case_data.get("plaintiff_contact", ""),
                    is_self=True
                )
                self.db.add(plaintiff)
                
            if case_data.get("defendant_name"):
                defendant = CaseParty(
                    case_id=case.id,
                    party_type="defendant",
                    name=case_data["defendant_name"],
                    contact=case_data.get("defendant_contact", ""),
                    is_self=False
                )
                self.db.add(defendant)
            
            # 3. 迁移证据材料
            evidence_list = self.db.query(ProjectEvidence).filter(
                ProjectEvidence.project_id == self.project_id
            ).all()
            
            migrated_evidence_ids = []
            for pe in evidence_list:
                evidence = Evidence(
                    case_id=case.id,
                    evidence_name=pe.name,
                    evidence_type=pe.evidence_type,
                    evidence_source=pe.source,
                    content=pe.content,
                    content_summary=pe.content_summary,
                    probative_value=pe.probative_value,
                    authenticity=pe.authenticity,
                    is_key_evidence=pe.is_key_evidence,
                    status="verified"
                )
                self.db.add(evidence)
                self.db.flush()
                migrated_evidence_ids.append(evidence.id)
            
            # 4. 迁移文档
            docs = self.db.query(ProjectDocument).filter(
                ProjectDocument.project_id == self.project_id
            ).all()
            
            migrated_doc_ids = []
            for pd in docs:
                doc = Document(
                    case_id=case.id,
                    doc_type=pd.doc_type,
                    doc_name=pd.name,
                    description=pd.description,
                    source=pd.source,
                    content=pd.content,
                    ai_review=pd.ai_review,
                    status="active"
                )
                self.db.add(doc)
                self.db.flush()
                migrated_doc_ids.append(doc.id)
            
            # 5. 迁移往来记录到时间线
            comms = self.db.query(ProjectCommunication).filter(
                ProjectCommunication.project_id == self.project_id
            ).all()
            
            migrated_comm_ids = []
            for pc in comms:
                timeline = CaseTimeline(
                    case_id=case.id,
                    event_type="communication",
                    event_date=pc.communication_date or datetime.utcnow(),
                    description=f"沟通: {pc.subject or pc.content[:50] if pc.content else ''}",
                    details=pc.content,
                    importance=pc.evidence_value
                )
                self.db.add(timeline)
                self.db.flush()
                migrated_comm_ids.append(timeline.id)
            
            # 6. 迁移合同信息到案件描述
            contracts = self.db.query(ProjectContract).filter(
                ProjectContract.project_id == self.project_id
            ).all()
            
            if contracts:
                contract_info = "\n".join([
                    f"- {c.contract_name}: {c.amount or ''} ({c.status})"
                    for c in contracts
                ])
                case.description = (case.description or "") + "\n\n相关合同:\n" + contract_info
            
            # 7. 记录转换映射
            mapping = ProjectToCase(
                project_id=self.project_id,
                case_id=case.id,
                conversion_reason=conversion_reason,
                conversion_date=datetime.utcnow(),
                migrated_documents=json.dumps(migrated_doc_ids),
                migrated_evidence=json.dumps(migrated_evidence_ids),
                migrated_communications=json.dumps(migrated_comm_ids),
                notes=f"从项目 {self.project.name} 转换"
            )
            self.db.add(mapping)
            
            # 8. 更新项目状态
            self.project.status = "litigation"
            self.project.related_cases = json.dumps([case.id])
            self.project.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.case_id = case.id
            
            return case.id
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_migration_preview(self) -> Dict[str, Any]:
        """获取迁移预览"""
        if not self.project:
            if not self.load_project():
                raise ValueError(f"项目 {self.project_id} 不存在")
        
        evidence_count = self.db.query(ProjectEvidence).filter(
            ProjectEvidence.project_id == self.project_id
        ).count()
        
        docs_count = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == self.project_id
        ).count()
        
        comms_count = self.db.query(ProjectCommunication).filter(
            ProjectCommunication.project_id == self.project_id
        ).count()
        
        contracts_count = self.db.query(ProjectContract).filter(
            ProjectContract.project_id == self.project_id
        ).count()
        
        risks_count = self.db.query(ProjectRisk).filter(
            ProjectRisk.project_id == self.project_id
        ).count()
        
        return {
            "project_id": self.project_id,
            "project_name": self.project.name,
            "project_type": self.project.project_type,
            "counterpart": self.project.counterpart_name,
            "risk_level": self.project.risk_level,
            "evidence_count": evidence_count,
            "docs_count": docs_count,
            "comms_count": comms_count,
            "contracts_count": contracts_count,
            "risks_count": risks_count,
            "total_items": evidence_count + docs_count + comms_count + contracts_count + risks_count
        }


def convert_project_to_case(project_id: int, case_data: Dict[str, Any], reason: str = "") -> Optional[int]:
    """便捷函数：转换项目到案件"""
    with ProjectToCaseConverter(project_id) as converter:
        return converter.convert(case_data, reason)


def get_migration_preview(project_id: int) -> Dict[str, Any]:
    """便捷函数：获取迁移预览"""
    with ProjectToCaseConverter(project_id) as converter:
        return converter.get_migration_preview()
