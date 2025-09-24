"""
数据库模型定义
使用SQLAlchemy Core (不依赖Ormar)
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey, JSON

from app.core.database import metadata


class StorageType(str, Enum):
    """存储类型枚举"""
    LOCAL = "local"
    WEBDAV = "webdav"
    S3 = "s3"


class FileStatus(str, Enum):
    """文件状态枚举"""
    UPLOADING = "uploading"
    ACTIVE = "active"
    DELETED = "deleted"


# 用户表定义
users_table = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(50), unique=True, index=True, nullable=False),
    Column("email", String(100), unique=True, index=True, nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("storage_type", String(20), default=StorageType.LOCAL.value),
    Column("storage_config", JSON, default={}),
    Column("storage_quota", BigInteger, default=1024*1024*1024),  # 1GB
    Column("storage_used", BigInteger, default=0),
    Column("is_active", Boolean, default=True),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow)
)


# 简化的User类（用于类型提示和业务逻辑）
class User:
    """用户模型类"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.username = kwargs.get('username')
        self.email = kwargs.get('email')
        self.password_hash = kwargs.get('password_hash')
        self.storage_type = kwargs.get('storage_type', StorageType.LOCAL)
        self.storage_config = kwargs.get('storage_config', {})
        self.storage_quota = kwargs.get('storage_quota', 1024*1024*1024)
        self.storage_used = kwargs.get('storage_used', 0)
        self.is_active = kwargs.get('is_active', True)
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
    
    @property
    def remaining_storage(self) -> int:
        """剩余存储空间"""
        return max(0, self.storage_quota - self.storage_used)
    
    @property
    def storage_usage_percent(self) -> float:
        """存储使用百分比"""
        if self.storage_quota == 0:
            return 0.0
        return (self.storage_used / self.storage_quota) * 100


# 文件记录表定义
file_records_table = Table(
    "file_records",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("filename", String(255), index=True, nullable=False),
    Column("original_filename", String(255), nullable=False),
    Column("file_path", String(500), nullable=False),
    Column("file_size", BigInteger, nullable=False),
    Column("content_type", String(100), nullable=False),
    Column("file_hash", String(64), index=True, nullable=False),
    Column("width", Integer, nullable=True),
    Column("height", Integer, nullable=True),
    Column("format", String(10), nullable=True),
    Column("status", String(20), default=FileStatus.ACTIVE.value),
    Column("access_token", String(255), nullable=True, index=True),
    Column("download_count", Integer, default=0),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow),
    Column("expires_at", DateTime, nullable=True)
)


# 简化的FileRecord类
class FileRecord:
    """文件记录模型类"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.user_id = kwargs.get('user_id')
        self.user = kwargs.get('user')  # User对象
        self.filename = kwargs.get('filename')
        self.original_filename = kwargs.get('original_filename')
        self.file_path = kwargs.get('file_path')
        self.file_size = kwargs.get('file_size')
        self.content_type = kwargs.get('content_type')
        self.file_hash = kwargs.get('file_hash')
        self.width = kwargs.get('width')
        self.height = kwargs.get('height')
        self.format = kwargs.get('format')
        self.status = kwargs.get('status', FileStatus.ACTIVE)
        self.access_token = kwargs.get('access_token')
        self.download_count = kwargs.get('download_count', 0)
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.expires_at = kwargs.get('expires_at')
    
    @property
    def is_expired(self) -> bool:
        """检查文件是否过期"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_image(self) -> bool:
        """检查是否为图片文件"""
        return self.content_type.startswith('image/')


# 上传会话表定义
upload_sessions_table = Table(
    "upload_sessions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", String(255), unique=True, index=True, nullable=False),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("filename", String(255), nullable=False),
    Column("total_size", BigInteger, nullable=False),
    Column("chunk_size", Integer, default=1024*1024),  # 1MB
    Column("chunks_received", Integer, default=0),
    Column("total_chunks", Integer, nullable=False),
    Column("is_completed", Boolean, default=False),
    Column("temp_path", String(500), nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("expires_at", DateTime, nullable=False)
)

# 访问日志表定义
access_logs_table = Table(
    "access_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("file_record_id", Integer, ForeignKey("file_records.id"), nullable=False),
    Column("ip_address", String(45), nullable=False),  # 支持IPv6
    Column("user_agent", String(500), nullable=True),
    Column("referer", String(500), nullable=True),
    Column("access_type", String(20), nullable=False),  # view, download, thumbnail
    Column("accessed_at", DateTime, default=datetime.utcnow)
)


# 简化的UploadSession类
class UploadSession:
    """上传会话模型类"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.session_id = kwargs.get('session_id')
        self.user_id = kwargs.get('user_id')
        self.user = kwargs.get('user')
        self.filename = kwargs.get('filename')
        self.total_size = kwargs.get('total_size')
        self.chunk_size = kwargs.get('chunk_size', 1024*1024)
        self.chunks_received = kwargs.get('chunks_received', 0)
        self.total_chunks = kwargs.get('total_chunks')
        self.is_completed = kwargs.get('is_completed', False)
        self.temp_path = kwargs.get('temp_path')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.expires_at = kwargs.get('expires_at')
    
    @property
    def is_expired(self) -> bool:
        """检查上传会话是否过期"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def progress_percent(self) -> float:
        """上传进度百分比"""
        if self.total_chunks == 0:
            return 0.0
        return (self.chunks_received / self.total_chunks) * 100


# 简化的AccessLog类
class AccessLog:
    """访问日志模型类"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.file_record_id = kwargs.get('file_record_id')
        self.file_record = kwargs.get('file_record')
        self.ip_address = kwargs.get('ip_address')
        self.user_agent = kwargs.get('user_agent')
        self.referer = kwargs.get('referer')
        self.access_type = kwargs.get('access_type')
        self.accessed_at = kwargs.get('accessed_at', datetime.utcnow())
