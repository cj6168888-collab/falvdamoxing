"""
会议管理 API
会议记录、纪要生成、合同/决议生成
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import json

from app.db.database import get_db
from app.models.meeting import MeetingRecord

router = APIRouter(prefix="/api/meetings", tags=["会议管理"])


@router.get("")
def list_meetings(db: Session = Depends(get_db)):
    """获取会议列表"""
    records = db.query(MeetingRecord).order_by(MeetingRecord.created_at.desc()).all()
    return {
        "meetings": [
            {
                "id": r.id,
                "session_id": r.session_id,
                "meeting_type": r.meeting_type,
                "topic": r.topic,
                "date": r.date,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
        "total": len(records),
    }


# ============ 会议记录模型 ============

class MeetingRecordCreate(BaseModel):
    """创建会议记录"""
    session_id: Optional[str] = None
    project_id: Optional[int] = None
    case_id: Optional[int] = None
    meeting_type: str
    topic: str
    date: str
    participants: Optional[str] = None
    content: Optional[str] = None
    records: Optional[List[dict]] = None
    audio_files: Optional[List[dict]] = None
    status: str = "active"
    notes: Optional[str] = None


class MeetingMinutesRequest(BaseModel):
    """生成会议纪要请求"""
    meeting_info: dict
    records: Optional[List[dict]] = None


class ContractGenerateRequest(BaseModel):
    """生成合同请求"""
    meeting_info: dict
    records: Optional[List[dict]] = None
    contract_type: str = "合作合同"


class ResolutionGenerateRequest(BaseModel):
    """生成决议请求"""
    meeting_info: dict
    decisions: Optional[List[dict]] = None


# ============ 辅助函数 ============

def _generate_meeting_minutes_content(meeting_info: dict, records: List[dict] = None) -> str:
    """生成会议纪要内容"""
    minutes = f"""
# 会议纪要

## 基本信息
- **会议类型**：{meeting_info.get('type', '未知')}
- **会议主题**：{meeting_info.get('topic', '未知')}
- **会议日期**：{meeting_info.get('date', '未知')}
- **我方角色**：{meeting_info.get('our_role', '未知')}

## 参会人员
{meeting_info.get('participants', '未记录')}

## 会议背景
**我方立场/诉求：**
{meeting_info.get('our_position', '未记录')}

**对方立场/诉求（推测）：**
{meeting_info.get('their_position', '未记录')}

## 会议记录
"""

    if records:
        for i, record in enumerate(records, 1):
            record_type = record.get('type', 'info')
            record_time = record.get('time', '')

            if record_type == 'analysis':
                content = record.get('content', {})
                if isinstance(content, dict):
                    minutes += f"\n### 第{i}项：分析记录 [{record_time}]\n"
                    if content.get('analysis'):
                        minutes += f"\n**分析内容：**\n{content['analysis']}\n"
                    if content.get('suggestions'):
                        minutes += f"\n**建议：**\n{content['suggestions']}\n"
            elif record_type == 'trap':
                content = record.get('content', {})
                if isinstance(content, dict):
                    minutes += f"\n### 第{i}项：风险识别 [{record_time}]\n"
                    if content.get('trap_detected'):
                        minutes += f"\n⚠️ **检测到陷阱：**{content.get('trap_type', '')}\n"
                        minutes += f"**描述：**{content.get('description', '')}\n"
                        minutes += f"**建议回应：**{content.get('suggested_response', '')}\n"
            elif record_type == 'strategy':
                content = record.get('content', {})
                if isinstance(content, dict):
                    minutes += f"\n### 第{i}项：应对策略 [{record_time}]\n"
                    if content.get('strategy'):
                        minutes += f"\n{content['strategy']}\n"

    minutes += """

## 会议结论
（待补充）

## 下一步行动
1.
2.
3.

---
纪要生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    return minutes


def _generate_contract_content(meeting_info: dict, records: List[dict] = None, contract_type: str = "合作合同") -> str:
    """生成合同内容"""
    return f"""
# {contract_type}

合同编号：__________
签订日期：{meeting_info.get('date', '年  月  日')}
签订地点：__________

## 甲方：__________  乙方：__________

## 合作内容
{meeting_info.get('our_position', '（待补充）')}

（标准合同模板，请根据实际情况补充完整）
"""


def _generate_resolution_content(meeting_info: dict, decisions: List[dict] = None) -> str:
    """生成会议决议内容"""
    resolution = f"""
# {meeting_info.get('topic', '会议')}决议

会议日期：{meeting_info.get('date', '年  月  日')}

## 决议事项
"""
    if decisions:
        for i, decision in enumerate(decisions, 1):
            content = decision.get('content', {})
            if isinstance(content, dict):
                resolution += f"\n### 决议第{i}项\n"
                resolution += f"{content.get('analysis', content.get('strategy', '待补充'))}\n\n"
    else:
        resolution += "\n（待补充）\n"

    resolution += "\n---\n主持人：________________  记录人：________________\n"
    return resolution


# ============ API 端点 ============

@router.post("/records")
def save_meeting_record(data: MeetingRecordCreate, db: Session = Depends(get_db)):
    """保存会议记录到数据库"""
    session_id = data.session_id or f"meeting-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    record = MeetingRecord(
        session_id=session_id,
        project_id=data.project_id,
        case_id=data.case_id,
        meeting_type=data.meeting_type,
        topic=data.topic,
        date=data.date,
        participants=data.participants,
        content=data.content,
        records=data.records,
        audio_files=data.audio_files,
        status=data.status,
        notes=data.notes,
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return {
        "success": True,
        "message": "会议记录已保存",
        "id": record.id,
        "session_id": record.session_id,
    }


@router.get("/records")
def get_meeting_records(
    project_id: Optional[int] = None,
    case_id: Optional[int] = None,
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db)
):
    """获取会议记录列表"""
    query = db.query(MeetingRecord)
    if project_id:
        query = query.filter(MeetingRecord.project_id == project_id)
    if case_id:
        query = query.filter(MeetingRecord.case_id == case_id)
    
    records = query.order_by(MeetingRecord.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": r.id,
            "session_id": r.session_id,
            "meeting_type": r.meeting_type,
            "topic": r.topic,
            "date": r.date,
            "status": r.status,
            "participants": r.participants,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.get("/records/{session_id}")
def get_meeting_record(session_id: str, db: Session = Depends(get_db)):
    """获取单个会议记录"""
    record = db.query(MeetingRecord).filter(MeetingRecord.session_id == session_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="会议记录不存在")
    
    return {
        "id": record.id,
        "session_id": record.session_id,
        "meeting_type": record.meeting_type,
        "topic": record.topic,
        "date": record.date,
        "participants": record.participants,
        "content": record.content,
        "records": record.records,
        "audio_files": record.audio_files,
        "status": record.status,
        "notes": record.notes,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


@router.post("/generate-minutes")
def generate_meeting_minutes(data: MeetingMinutesRequest):
    """生成会议纪要"""
    minutes_content = _generate_meeting_minutes_content(
        meeting_info=data.meeting_info,
        records=data.records
    )
    return {
        "minutes": minutes_content,
        "summary": "会议纪要已生成，请查看详细内容并进行必要的修改和补充。"
    }


@router.post("/generate-contract")
def generate_contract_from_meeting(data: ContractGenerateRequest):
    """从会议内容生成合同"""
    contract_content = _generate_contract_content(
        meeting_info=data.meeting_info,
        records=data.records,
        contract_type=data.contract_type
    )
    return {
        "contract": contract_content,
        "contract_type": data.contract_type,
        "summary": "合同草案已生成，请在正式签署前仔细审核并根据实际情况进行调整。"
    }


@router.post("/generate-resolution")
def generate_resolution(data: ResolutionGenerateRequest):
    """生成会议决议"""
    resolution_content = _generate_resolution_content(
        meeting_info=data.meeting_info,
        decisions=data.decisions
    )
    return {
        "resolution": resolution_content,
        "summary": "会议决议已生成，请根据实际情况补充完整。"
    }


@router.post("/hearing/generate-meeting-minutes")
def api_generate_meeting_minutes(data: MeetingMinutesRequest):
    """生成会议纪要（集成端点）"""
    return generate_meeting_minutes(data)


@router.post("/hearing/generate-contract")
def api_generate_contract(data: ContractGenerateRequest):
    """从会议内容生成合同（集成端点）"""
    return generate_contract_from_meeting(data)


@router.post("/hearing/generate-resolution")
def api_generate_resolution(data: ResolutionGenerateRequest):
    """生成会议决议（集成端点）"""
    return generate_resolution(data)
