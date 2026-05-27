"""
证据文件夹管理 API
支持文件夹配置、扫描、监控、文件列表等操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
import os
import json
import time
import logging

from app.db.database import get_db, SessionLocal
from app.models.case import Case
from app.models.evidence_folder import (
    EvidenceFolderScan, EvidenceFolderFile,
    EvidenceFolderConfig, ScanStatus, ScanType, FileProcessStatus
)
from app.services.evidence_folder_service import EvidenceFolderService
from app.services.folder_watcher import FolderWatcherService
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/evidence-folder", tags=["证据文件夹"])


# ============ Pydantic 模型 ============

class FolderConfigRequest(BaseModel):
    """文件夹配置请求"""
    folder_path: str = Field(..., description="证据文件夹路径")
    enabled: bool = Field(default=True, description="是否启用监控")


class ScanRequest(BaseModel):
    """扫描请求"""
    scan_type: str = Field(default="full", description="扫描类型: full / incremental")


class FileReprocessResponse(BaseModel):
    """重新处理响应"""
    status: str
    message: str
    file_path: Optional[str] = None
    evidence_id: Optional[int] = None
    category: Optional[str] = None


# ============ 辅助函数 ============

def _get_case_or_404(case_id: int, db: Session) -> Case:
    """获取案件或返回 404"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    return case


def _validate_folder_path(path: str) -> str:
    """验证文件夹路径"""
    if not path or not path.strip():
        raise HTTPException(status_code=400, detail="文件夹路径不能为空")

    normalized = os.path.normpath(path.strip())

    if not os.path.exists(normalized):
        raise HTTPException(status_code=400, detail=f"路径不存在: {normalized}")

    if not os.path.isdir(normalized):
        raise HTTPException(status_code=400, detail=f"路径不是文件夹: {normalized}")

    if not os.access(normalized, os.R_OK):
        raise HTTPException(status_code=403, detail=f"没有读取权限: {normalized}")

    return normalized


# ============ 文件夹配置 ============

@router.get("/cases/{case_id}/config")
def get_folder_config(case_id: int, db: Session = Depends(get_db)):
    """获取案件的文件夹配置"""
    case = _get_case_or_404(case_id, db)

    config = db.query(EvidenceFolderConfig).filter(
        EvidenceFolderConfig.case_id == case_id
    ).first()

    is_monitoring = FolderWatcherService.is_watching(case_id)

    return {
        "case_id": case_id,
        "folder_path": case.evidence_folder_path,
        "enabled": case.evidence_folder_enabled,
        "last_scan_time": case.evidence_last_scan_time.isoformat() if case.evidence_last_scan_time else None,
        "last_sync_count": case.evidence_last_sync_count,
        "is_monitoring": is_monitoring,
        "config": {
            "supported_formats": config.supported_formats if config else None,
            "auto_ocr": config.auto_ocr if config else True,
            "auto_classify": config.auto_classify if config else True,
            "auto_deduplicate": config.auto_deduplicate if config else True,
            "include_subfolders": config.include_subfolders if config else True,
        }
    }


@router.put("/cases/{case_id}/config")
def update_folder_config(
    case_id: int,
    request: FolderConfigRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """更新案件的文件夹配置，保存后自动扫描"""
    case = _get_case_or_404(case_id, db)

    # 验证路径
    folder_path = _validate_folder_path(request.folder_path)

    # 更新案件
    case.evidence_folder_path = folder_path
    case.evidence_folder_enabled = request.enabled
    db.commit()

    # 确保配置记录存在
    config = db.query(EvidenceFolderConfig).filter(
        EvidenceFolderConfig.case_id == case_id
    ).first()

    if not config:
        config = EvidenceFolderConfig(case_id=case_id)
        db.add(config)

    db.commit()

    # 保存后自动触发全量扫描
    def _auto_scan():
        service = EvidenceFolderService(case_id)
        try:
            scan = service.full_scan()
            logger.info(f"[自动扫描] 全量扫描完成: case_id={case_id}, 找到{scan.files_found}个文件, 处理{scan.files_processed}个")
        except Exception as e:
            logger.error(f"[自动扫描] 扫描失败: case_id={case_id}, 错误: {e}")
        finally:
            service.close()

    background_tasks.add_task(_auto_scan)

    return {
        "message": "文件夹配置已更新，正在后台扫描...",
        "folder_path": folder_path,
        "enabled": request.enabled,
    }


# ============ 扫描操作 ============

@router.post("/cases/{case_id}/scan")
def trigger_scan(
    case_id: int,
    request: ScanRequest = ScanRequest(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """触发文件夹扫描（后台异步执行）"""
    case = _get_case_or_404(case_id, db)

    if not case.evidence_folder_path:
        raise HTTPException(status_code=400, detail="请先配置证据文件夹")

    if not os.path.exists(case.evidence_folder_path):
        raise HTTPException(status_code=400, detail="证据文件夹路径不存在")

    scan_type = request.scan_type

    def _run_scan():
        service = EvidenceFolderService(case_id)
        try:
            if scan_type == "full":
                scan = service.full_scan()
                logger.info(f"全量扫描完成: case_id={case_id}, 找到{scan.files_found}个文件, 处理{scan.files_processed}个")
            else:
                result = service.incremental_scan()
                logger.info(f"增量扫描完成: case_id={case_id}, 结果: {result}")
        except Exception as e:
            logger.error(f"扫描失败: case_id={case_id}, 错误: {e}")
        finally:
            service.close()

    background_tasks.add_task(_run_scan)

    return {
        "message": f"{'全量' if scan_type == 'full' else '增量'}扫描已在后台启动",
        "scan_type": scan_type,
    }


@router.post("/cases/{case_id}/scan-incremental")
def trigger_incremental_scan(
    case_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """触发增量扫描（后台执行）"""
    case = _get_case_or_404(case_id, db)

    if not case.evidence_folder_path:
        raise HTTPException(status_code=400, detail="请先配置证据文件夹")

    def _run_incremental():
        service = EvidenceFolderService(case_id)
        try:
            result = service.incremental_scan()
            logger.info(f"增量扫描完成: case_id={case_id}, 结果: {result}")
        except Exception as e:
            logger.error(f"增量扫描失败: case_id={case_id}, 错误: {e}")
        finally:
            service.close()

    background_tasks.add_task(_run_incremental)

    return {"message": "增量扫描已在后台启动"}


# ============ 状态与文件列表 ============

@router.get("/cases/{case_id}/status")
def get_folder_status(case_id: int, db: Session = Depends(get_db)):
    """获取文件夹状态"""
    case = _get_case_or_404(case_id, db)

    if not case.evidence_folder_path:
        return {
            "case_id": case_id,
            "folder_path": None,
            "enabled": False,
            "folder_exists": False,
            "is_monitoring": False,
            "stats": {"total": 0, "processed": 0, "pending": 0, "failed": 0, "skipped": 0},
            "recent_files": [],
        }

    service = EvidenceFolderService(case_id)
    try:
        status = service.get_folder_status()
        status["is_monitoring"] = FolderWatcherService.is_watching(case_id)
        return status
    finally:
        service.close()


@router.get("/cases/{case_id}/files")
def get_folder_files(
    case_id: int,
    status: Optional[str] = Query(None, description="过滤状态: pending / processing / completed / failed / skipped"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """获取文件夹文件列表"""
    _get_case_or_404(case_id, db)

    service = EvidenceFolderService(case_id)
    try:
        return service.get_file_records(status=status, page=page, page_size=page_size)
    finally:
        service.close()


@router.get("/cases/{case_id}/scans")
def get_scan_history(
    case_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取扫描历史记录"""
    _get_case_or_404(case_id, db)

    query = db.query(EvidenceFolderScan).filter(
        EvidenceFolderScan.case_id == case_id
    )

    total = query.count()
    scans = query.order_by(EvidenceFolderScan.started_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "scans": [
            {
                "id": s.id,
                "scan_type": s.scan_type,
                "status": s.status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "files_found": s.files_found,
                "files_processed": s.files_processed,
                "files_failed": s.files_failed,
                "files_skipped": s.files_skipped,
                "error_message": s.error_message,
            }
            for s in scans
        ]
    }


# ============ 文件操作 ============

@router.delete("/cases/{case_id}/files/{file_id}")
def delete_file_record(
    case_id: int,
    file_id: int,
    db: Session = Depends(get_db)
):
    """删除文件记录（不删除实际文件）"""
    _get_case_or_404(case_id, db)

    service = EvidenceFolderService(case_id)
    try:
        success = service.delete_file_record(file_id)
        if not success:
            raise HTTPException(status_code=404, detail="文件记录不存在")
        return {"message": "文件记录已删除"}
    finally:
        service.close()


@router.post("/cases/{case_id}/files/{file_id}/reprocess")
def reprocess_file(
    case_id: int,
    file_id: int,
    db: Session = Depends(get_db)
):
    """重新处理某个文件"""
    _get_case_or_404(case_id, db)

    service = EvidenceFolderService(case_id)
    try:
        result = service.reprocess_file(file_id)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message", "重新处理失败"))
        return result
    finally:
        service.close()


# ============ 监控开关 ============

@router.post("/cases/{case_id}/enable-monitor")
def enable_monitoring(case_id: int, db: Session = Depends(get_db)):
    """启用文件夹监控"""
    case = _get_case_or_404(case_id, db)

    if not case.evidence_folder_path:
        raise HTTPException(status_code=400, detail="请先配置证据文件夹")

    if not os.path.exists(case.evidence_folder_path):
        raise HTTPException(status_code=400, detail="证据文件夹路径不存在")

    # 更新案件状态
    case.evidence_folder_enabled = True
    db.commit()

    # 启动监控
    watcher = FolderWatcherService.get_instance(case_id)

    def _callback(cid: int, file_paths: list):
        """文件变化回调"""
        service = EvidenceFolderService(cid)
        try:
            result = service.incremental_scan(file_paths)
            logger.info(f"[监控回调] 增量处理完成: case_id={cid}, 结果: {result}")
        except Exception as e:
            logger.error(f"[监控回调] 增量处理失败: case_id={cid}, 错误: {e}")
        finally:
            service.close()

    success = watcher.start_watching(
        folder_path=case.evidence_folder_path,
        callback=_callback,
    )

    if not success:
        raise HTTPException(status_code=500, detail="启动监控失败")

    return {
        "message": "文件夹监控已启用",
        "is_monitoring": True,
        "folder_path": case.evidence_folder_path,
    }


@router.post("/cases/{case_id}/disable-monitor")
def disable_monitoring(case_id: int, db: Session = Depends(get_db)):
    """停用文件夹监控"""
    case = _get_case_or_404(case_id, db)

    # 更新案件状态
    case.evidence_folder_enabled = False
    db.commit()

    # 停止监控
    watcher = FolderWatcherService.get_instance(case_id)
    watcher.stop_watching()

    return {
        "message": "文件夹监控已停用",
        "is_monitoring": False,
    }


@router.get("/cases/{case_id}/scan-events")
def scan_events(case_id: int, db: Session = Depends(get_db)):
    """
    SSE 端点 - 实时推送扫描进度
    客户端通过 EventSource 连接，接收扫描状态变化事件
    """
    _get_case_or_404(case_id, db)

    def event_stream():
        """SSE 事件流"""
        last_status = None
        while True:
            try:
                inner_db = SessionLocal()
                case = inner_db.query(Case).filter(Case.id == case_id).first()
                if not case:
                    inner_db.close()
                    break

                current = {
                    "folder_path": case.evidence_folder_path,
                    "enabled": case.evidence_folder_enabled,
                    "last_scan_time": case.evidence_last_scan_time.isoformat() if case.evidence_last_scan_time else None,
                    "last_sync_count": case.evidence_last_sync_count,
                    "is_monitoring": FolderWatcherService.is_watching(case_id),
                }

                # 查询最新扫描记录
                latest_scan = inner_db.query(EvidenceFolderScan).filter(
                    EvidenceFolderScan.case_id == case_id
                ).order_by(EvidenceFolderScan.started_at.desc()).first()

                if latest_scan:
                    current["active_scan"] = {
                        "id": latest_scan.id,
                        "type": latest_scan.scan_type,
                        "status": latest_scan.status,
                        "files_found": latest_scan.files_found,
                        "files_processed": latest_scan.files_processed,
                        "files_failed": latest_scan.files_failed,
                        "files_skipped": latest_scan.files_skipped,
                    }

                inner_db.close()

                # 只在状态变化时发送
                status_str = json.dumps(current, ensure_ascii=False, default=str)
                if status_str != last_status:
                    yield f"data: {status_str}\n\n"
                    last_status = status_str

                time.sleep(2)
            except GeneratorExit:
                break
            except Exception as e:
                logger.error(f"SSE 事件流错误: {e}")
                time.sleep(5)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
