# Project Documents API

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.project import ProjectDocument, Project

router = APIRouter(prefix="/api/projects", tags=["项目管理"])

@router.post("/{project_id}/documents", response_model=Dict)
def create_document(project_id: int, doc: dict, db: Session = Depends(get_db)):
    """Add a project document"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    db_doc = ProjectDocument(
        project_id=project_id,
        doc_type=doc.get("doc_type"),
        name=doc.get("name"),
        description=doc.get("description"),
        source=doc.get("source"),
        content=doc.get("content"),
        content_summary=doc.get("content_summary"),
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return {"id": db_doc.id, "message": "文档添加成功"}

@router.get("/{project_id}/documents", response_model=List[Dict])
def list_documents(project_id: int, db: Session = Depends(get_db)):
    """Get list of project documents"""
    docs = (
        db.query(ProjectDocument)
        .filter(ProjectDocument.project_id == project_id)
        .order_by(ProjectDocument.created_at.desc())
        .all()
    )
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
            "created_at": d.created_at,
        }
        for d in docs
    ]
