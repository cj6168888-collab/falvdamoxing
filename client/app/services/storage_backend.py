"""
证据存储后端 — 本地文件系统 / 云端 OSS 双模式
"""
from __future__ import annotations

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional


class StorageBackend(ABC):
    """证据存储后端抽象基类"""

    @abstractmethod
    def save(self, file_data: bytes, filename: str, case_id: int) -> str:
        """保存文件，返回存储路径/URL"""

    @abstractmethod
    def read(self, path: str) -> Optional[bytes]:
        """读取文件内容"""

    @abstractmethod
    def delete(self, path: str) -> bool:
        """删除文件"""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """检查文件是否存在"""


class LocalFileBackend(StorageBackend):
    """本地文件系统存储"""

    def __init__(self, base_dir: str = "data/files"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _case_dir(self, case_id: int) -> Path:
        d = self.base_dir / str(case_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self, file_data: bytes, filename: str, case_id: int) -> str:
        folder = self._case_dir(case_id)
        safe_name = f"{os.urandom(4).hex()}_{filename}"
        filepath = folder / safe_name
        filepath.write_bytes(file_data)
        return str(filepath)

    def read(self, path: str) -> Optional[bytes]:
        p = Path(path)
        return p.read_bytes() if p.exists() else None

    def delete(self, path: str) -> bool:
        p = Path(path)
        if p.exists():
            p.unlink()
            return True
        return False

    def exists(self, path: str) -> bool:
        return Path(path).exists()


class CloudStorageBackend(StorageBackend):
    """云端对象存储（兼容阿里云 OSS / AWS S3 / MinIO）"""

    def __init__(
        self,
        endpoint: str = "",
        access_key: str = "",
        secret_key: str = "",
        bucket: str = "legal-ai-evidence",
        region: str = "cn-hangzhou",
    ):
        self.endpoint = endpoint or os.environ.get("OSS_ENDPOINT", "")
        self.access_key = access_key or os.environ.get("OSS_ACCESS_KEY_ID", "")
        self.secret_key = secret_key or os.environ.get("OSS_ACCESS_KEY_SECRET", "")
        self.bucket = bucket or os.environ.get("OSS_BUCKET", "legal-ai-evidence")
        self.region = region
        self._client = None
        self._available = None

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        try:
            import boto3
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint or f"https://oss-{self.region}.aliyuncs.com",
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
            )
            self._client.head_bucket(Bucket=self.bucket)
            self._available = True
        except Exception:
            self._client = None
            self._available = False
        return self._client

    @property
    def is_available(self) -> bool:
        if self._available is None:
            self._ensure_client()
        return self._available is True

    def save(self, file_data: bytes, filename: str, case_id: int) -> str:
        client = self._ensure_client()
        if not client:
            raise RuntimeError("云端存储不可用，请检查 OSS 配置")

        key = f"cases/{case_id}/{os.urandom(4).hex()}_{filename}"
        client.put_object(Bucket=self.bucket, Key=key, Body=file_data)
        return f"oss://{self.bucket}/{key}"

    def read(self, path: str) -> Optional[bytes]:
        client = self._ensure_client()
        if not client:
            return None
        try:
            key = path.replace(f"oss://{self.bucket}/", "")
            resp = client.get_object(Bucket=self.bucket, Key=key)
            return resp["Body"].read()
        except Exception:
            return None

    def delete(self, path: str) -> bool:
        client = self._ensure_client()
        if not client:
            return False
        try:
            key = path.replace(f"oss://{self.bucket}/", "")
            client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def exists(self, path: str) -> bool:
        return self.read(path) is not None


# 全局实例
local_backend = LocalFileBackend()
cloud_backend = CloudStorageBackend()


def get_backend(mode: str) -> StorageBackend:
    """根据模式获取存储后端"""
    if mode == "cloud" and cloud_backend.is_available:
        return cloud_backend
    return local_backend
