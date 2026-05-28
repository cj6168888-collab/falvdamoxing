"""
会议记录模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime
from app.db.database import Base


class MeetingRecord(Base):
    """会议记录"""
    __tablename__ = "meeting_records"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    session_id = Column(String(100), unique=True, index=True)
    project_id = Column(Integer, nullable=True)
    case_id = Column(Integer, nullable=True)
    meeting_type = Column(String(50), nullable=False)
    topic = Column(String(200), nullable=False)
    date = Column(String(50), nullable=False)
    participants = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    records = Column(JSON, nullable=True)
    audio_files = Column(JSON, nullable=True)
    status = Column(String(20), default="active")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
