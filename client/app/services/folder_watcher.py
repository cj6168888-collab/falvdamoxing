"""
文件夹监控服务
使用 watchdog 库监控文件夹变化，自动触发新文件处理
"""
import os
import threading
import time
import logging
from pathlib import Path
from typing import Dict, Callable, List, Optional, Set
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class EvidenceFileHandler(FileSystemEventHandler):
    """
    证据文件夹事件处理器
    监听文件创建、修改、删除事件
    """

    def __init__(self, callback: Callable, case_id: int, supported_formats: Set[str]):
        super().__init__()
        self.callback = callback
        self.case_id = case_id
        self.supported_formats = supported_formats
        self._processed_recently: Dict[str, float] = {}  # path -> timestamp 防止短时间内重复处理

    def _should_process(self, path: str) -> bool:
        """判断是否应该处理该文件"""
        if not path:
            return False

        file_path = Path(path)

        # 检查文件是否存在
        if not file_path.exists() or not file_path.is_file():
            return False

        # 检查扩展名
        ext = file_path.suffix.lower().lstrip('.')
        if ext not in self.supported_formats:
            return False

        # 防止短时间内重复处理（3秒内同一文件只处理一次）
        current_time = time.time()
        if path in self._processed_recently:
            if current_time - self._processed_recently[path] < 3:
                return False

        self._processed_recently[path] = current_time
        return True

    def on_created(self, event: FileSystemEvent):
        """文件创建事件"""
        if event.is_directory:
            return

        if self._should_process(event.src_path):
            logger.info(f"[FolderWatcher] 新文件检测到: {event.src_path}")
            try:
                self.callback(self.case_id, [event.src_path])
            except Exception as e:
                logger.error(f"[FolderWatcher] 处理文件失败: {event.src_path}, 错误: {e}")

    def on_modified(self, event: FileSystemEvent):
        """文件修改事件"""
        if event.is_directory:
            return

        # 修改也触发处理（重新提取内容）
        if self._should_process(event.src_path):
            logger.info(f"[FolderWatcher] 文件修改检测到: {event.src_path}")
            try:
                self.callback(self.case_id, [event.src_path])
            except Exception as e:
                logger.error(f"[FolderWatcher] 处理文件失败: {event.src_path}, 错误: {e}")

    def on_deleted(self, event: FileSystemEvent):
        """文件删除事件"""
        if event.is_directory:
            return

        logger.info(f"[FolderWatcher] 文件删除: {event.src_path}")
        # 可以在这里添加删除关联证据记录的逻辑


class FolderWatcherService:
    """
    文件夹监控服务管理器
    统一管理所有案件的文件夹监控线程
    """

    _instances: Dict[int, 'FolderWatcherService'] = {}  # case_id -> service instance
    _observers: Dict[int, Observer] = {}  # case_id -> watchdog Observer
    _watch_threads: Dict[int, threading.Thread] = {}  # case_id -> monitoring thread
    _callbacks: Dict[int, Callable] = {}  # case_id -> callback function

    # 默认支持的文件格式
    DEFAULT_SUPPORTED_FORMATS = {
        'pdf', 'docx', 'doc', 'xlsx', 'xls',
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff',
        'txt', 'md', 'rtf',
        'mp4', 'avi', 'mov', 'mkv',  # 视频（预留）
        'mp3', 'wav', 'aac',  # 音频（预留）
    }

    @classmethod
    def get_instance(cls, case_id: int) -> 'FolderWatcherService':
        """获取或创建单例实例"""
        if case_id not in cls._instances:
            cls._instances[case_id] = cls(case_id)
        return cls._instances[case_id]

    def __init__(self, case_id: int):
        self.case_id = case_id
        self.folder_path: Optional[str] = None
        self.supported_formats: Set[str] = self.DEFAULT_SUPPORTED_FORMATS.copy()
        self.is_running: bool = False
        self.observer: Optional[Observer] = None
        self._stop_event: threading.Event = threading.Event()

    def start_watching(
        self,
        folder_path: str,
        callback: Callable,
        supported_formats: Optional[Set[str]] = None
    ) -> bool:
        """
        启动文件夹监控

        Args:
            folder_path: 要监控的文件夹路径
            callback: 文件变化时的回调函数，签名为 callback(case_id: int, file_paths: List[str])
            supported_formats: 支持的文件格式集合，不传则使用默认值

        Returns:
            bool: 启动是否成功
        """
        if self.is_running:
            logger.warning(f"[FolderWatcher] case_id={self.case_id} 已在监控中，先停止")
            self.stop_watching()

        # 验证路径
        if not os.path.exists(folder_path):
            logger.error(f"[FolderWatcher] 路径不存在: {folder_path}")
            return False

        if not os.path.isdir(folder_path):
            logger.error(f"[FolderWatcher] 路径不是文件夹: {folder_path}")
            return False

        # 更新配置
        self.folder_path = folder_path
        self.supported_formats = supported_formats or self.DEFAULT_SUPPORTED_FORMATS
        self._callbacks[self.case_id] = callback

        # 创建事件处理器
        event_handler = EvidenceFileHandler(
            callback=callback,
            case_id=self.case_id,
            supported_formats=self.supported_formats
        )

        # 创建 Observer
        self.observer = Observer()
        self.observer.schedule(event_handler, folder_path, recursive=True)
        self.observer.start()

        self.is_running = True
        self._stop_event.clear()

        # 记录到全局
        FolderWatcherService._observers[self.case_id] = self.observer

        logger.info(f"[FolderWatcher] 启动监控: case_id={self.case_id}, path={folder_path}")
        return True

    def stop_watching(self):
        """停止文件夹监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.observer = None

        self.is_running = False
        self._stop_event.set()

        # 从全局移除
        if self.case_id in FolderWatcherService._observers:
            del FolderWatcherService._observers[self.case_id]
        if self.case_id in FolderWatcherService._callbacks:
            del FolderWatcherService._callbacks[self.case_id]

        logger.info(f"[FolderWatcher] 停止监控: case_id={self.case_id}")

    def update_formats(self, supported_formats: Set[str]):
        """更新支持的文件格式"""
        self.supported_formats = supported_formats

    @classmethod
    def is_watching(cls, case_id: int) -> bool:
        """检查案件是否正在被监控"""
        if case_id in cls._instances:
            return cls._instances[case_id].is_running
        return False

    @classmethod
    def get_watching_info(cls, case_id: int) -> Optional[Dict]:
        """获取监控信息"""
        if case_id in cls._instances:
            instance = cls._instances[case_id]
            return {
                "case_id": case_id,
                "folder_path": instance.folder_path,
                "is_running": instance.is_running,
                "supported_formats": list(instance.supported_formats),
            }
        return None

    @classmethod
    def stop_all(cls):
        """停止所有监控"""
        for case_id in list(cls._instances.keys()):
            if cls._instances[case_id].is_running:
                cls._instances[case_id].stop_watching()
        logger.info("[FolderWatcher] 所有监控已停止")

    @classmethod
    def scan_directory(
        cls,
        folder_path: str,
        supported_formats: Optional[Set[str]] = None
    ) -> List[str]:
        """
        扫描目录，返回所有符合条件的文件路径

        Args:
            folder_path: 要扫描的文件夹路径
            supported_formats: 支持的文件格式集合

        Returns:
            List[str]: 文件路径列表
        """
        formats = supported_formats or cls.DEFAULT_SUPPORTED_FORMATS
        files = []

        try:
            folder = Path(folder_path)
            if not folder.exists():
                logger.warning(f"[FolderWatcher] 扫描目录不存在: {folder_path}")
                return []

            for file_path in folder.rglob('*'):
                if file_path.is_file():
                    ext = file_path.suffix.lower().lstrip('.')
                    if ext in formats:
                        files.append(str(file_path.absolute()))

            logger.info(f"[FolderWatcher] 扫描完成: path={folder_path}, 找到 {len(files)} 个文件")
        except Exception as e:
            logger.error(f"[FolderWatcher] 扫描目录失败: {folder_path}, 错误: {e}")

        return files
