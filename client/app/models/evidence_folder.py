"""
证据文件夹数据模型
支持文件夹扫描、文件索引、增量同步
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class ScanStatus:
    """扫描状态"""
    RUNNING = "running"      # 扫描中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


class ScanType:
    """扫描类型"""
    FULL = "full"            # 全量扫描
    INCREMENTAL = "incremental"  # 增量扫描


class FileProcessStatus:
    """文件处理状态"""
    PENDING = "pending"      # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    SKIPPED = "skipped"      # 跳过（重复/不支持）


class EvidenceFolderScan(Base):
    """
    证据文件夹扫描记录
    记录每次扫描的历史信息
    """
    __tablename__ = "evidence_folder_scans"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)

    # 扫描类型
    scan_type = Column(String(20), default=ScanType.FULL)  # full / incremental

    # 扫描时间
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 扫描状态
    status = Column(String(20), default=ScanStatus.RUNNING)  # running / completed / failed / cancelled

    # 统计信息
    files_found = Column(Integer, default=0)       # 发现的文件数
    files_processed = Column(Integer, default=0)    # 已处理的文件数
    files_failed = Column(Integer, default=0)        # 失败的文件数
    files_skipped = Column(Integer, default=0)       # 跳过的文件数（重复）

    # 扫描范围
    scan_path = Column(String(1000), nullable=True)  # 本次扫描的路径

    # 错误信息
    error_message = Column(Text, nullable=True)

    # 扫描结果摘要
    result_summary = Column(JSON, nullable=True)  # {categories: {}, total_size: int}

    # 关系
    case = relationship("Case", back_populates="folder_scans")

    def __repr__(self):
        return f"<EvidenceFolderScan(id={self.id}, case_id={self.case_id}, type={self.scan_type}, status={self.status})>"


class EvidenceFolderFile(Base):
    """
    证据文件夹文件索引
    记录文件夹中的每个文件的处理状态
    """
    __tablename__ = "evidence_folder_files"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)

    # 文件路径信息
    file_path = Column(String(1000), nullable=False)
    file_name = Column(String(500), nullable=True)
    file_extension = Column(String(20), nullable=True)  # .pdf, .docx, .jpg 等
    file_size = Column(Integer, nullable=True)  # 字节
    relative_path = Column(String(1000), nullable=True)  # 相对于文件夹根目录的路径

    # 文件内容指纹（用于去重）
    file_hash = Column(String(64), index=True, nullable=True)  # MD5/SHA256
    content_hash = Column(String(64), index=True, nullable=True)  # 内容哈希

    # 检测时间
    detected_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, nullable=True)

    # 处理状态
    processed = Column(Boolean, default=False)
    status = Column(String(20), default=FileProcessStatus.PENDING)  # pending / processing / completed / failed / skipped
    error_message = Column(Text, nullable=True)

    # 关联的证据记录
    evidence_id = Column(String(36), nullable=True)  # 关联到 evidence_items_v2 表 (UUID)

    # 处理详情
    extracted_content = Column(Text, nullable=True)  # 提取的文本内容
    extracted_content_length = Column(Integer, default=0)
    ocr_used = Column(Boolean, default=False)  # 是否使用了 OCR
    auto_category = Column(String(50), nullable=True)  # 自动分类结果
    auto_summary = Column(Text, nullable=True)  # 自动生成的摘要

    # 处理时间
    processed_at = Column(DateTime, nullable=True)

    # 关联的扫描记录
    scan_id = Column(Integer, ForeignKey("evidence_folder_scans.id"), nullable=True)

    # 关系
    case = relationship("Case", back_populates="folder_files")
    scan = relationship("EvidenceFolderScan", backref="files")

    def __repr__(self):
        return f"<EvidenceFolderFile(id={self.id}, case_id={self.case_id}, name={self.file_name}, status={self.status})>"

    def to_dict(self):
        """转换为字典（供 API 返回使用）"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'case_id': self.case_id,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_extension': self.file_extension,
            'file_size': self.file_size,
            'relative_path': self.relative_path,
            'file_hash': self.file_hash,
            'content_hash': self.content_hash,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'processed': self.processed,
            'status': self.status,
            'error_message': self.error_message,
            'evidence_id': self.evidence_id,
            'extracted_content_length': self.extracted_content_length,
            'ocr_used': self.ocr_used,
            'auto_category': self.auto_category,
            'auto_summary': self.auto_summary,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'scan_id': self.scan_id,
        }


class EvidenceFolderConfig(Base):
    """
    证据文件夹配置
    存储文件夹的扫描规则和偏好设置
    """
    __tablename__ = "evidence_folder_config"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(36), index=True, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, unique=True)

    # 扫描规则
    supported_formats = Column(JSON, nullable=True)  # ["pdf", "docx", "jpg", "png", "txt"]
    exclude_patterns = Column(JSON, nullable=True)  # ["*.tmp", "~$*", ".DS_Store"]
    include_subfolders = Column(Boolean, default=True)  # 是否扫描子文件夹

    # 处理偏好
    auto_ocr = Column(Boolean, default=True)  # 自动 OCR 图片/PDF
    auto_classify = Column(Boolean, default=True)  # 自动分类
    auto_deduplicate = Column(Boolean, default=True)  # 自动去重
    ocr_languages = Column(JSON, nullable=True)  # ["chinese", "english"]

    # 通知设置
    notify_on_new_file = Column(Boolean, default=True)  # 新文件时通知
    notify_on_error = Column(Boolean, default=True)  # 错误时通知

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<EvidenceFolderConfig(case_id={self.case_id})>"
