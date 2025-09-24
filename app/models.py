"""
数据库模型定义
使用SQLAlchemy Core
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey, JSON, text

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
    "wpic_users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True, comment="用户ID，主键"),
    Column("username", String(50), unique=True, default='', server_default=text("''"), index=True, nullable=False, comment="用户名，唯一索引"),
    Column("email", String(100), unique=True, default='', server_default=text("''"), index=True, nullable=False, comment="邮箱地址，唯一索引"),
    Column("password_hash", String(255), default='', server_default=text("''"), nullable=False, comment="密码哈希值"),
    Column("storage_type", String(20), default=StorageType.LOCAL.value, server_default=text("'local'"), nullable=False, comment="存储类型：local/webdav/s3"),
    Column("storage_config", JSON, default={}, server_default=text("'{}'"), nullable=False, comment="存储配置信息JSON"),
    Column("storage_quota", BigInteger, default=1024*1024*100, server_default=text("104857600"), nullable=False, comment="存储配额，单位字节，默认100MB"),
    Column("storage_used", BigInteger, default=0, server_default=text("0"), nullable=False, comment="已使用存储空间，单位字节"),
    Column("is_active", Boolean, default=True, server_default=text("1"), nullable=False, comment="用户是否激活"),
    Column("created_at", DateTime, default=datetime.now, server_default=text("NOW()"), nullable=False, comment="创建时间"),
    Column("updated_at", DateTime, default=datetime.now, server_default=text("NOW()"), nullable=False, comment="更新时间")
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
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
    
    def dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'storage_type': self.storage_type,
            'storage_config': self.storage_config,
            'storage_quota': self.storage_quota,
            'storage_used': self.storage_used,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
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
    "wpic_file_records",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True, comment="文件记录ID，主键"),
    Column("user_id", Integer, ForeignKey("wpic_users.id"), nullable=False, comment="所属用户ID，外键关联wpic_users.id"),
    Column("filename", String(255), index=True, nullable=False, comment="文件名，带索引"),
    Column("original_filename", String(255), nullable=False, comment="原始文件名"),
    Column("file_path", String(500), nullable=False, comment="文件存储路径"),
    Column("file_size", BigInteger, nullable=False, comment="文件大小，单位字节"),
    Column("content_type", String(100), nullable=False, comment="文件MIME类型"),
    Column("file_hash", String(64), index=True, nullable=False, comment="文件哈希值，用于去重，带索引"),
    Column("width", Integer, default=0, server_default=text("0"), nullable=False, comment="图片宽度，像素"),
    Column("height", Integer, default=0, server_default=text("0"), nullable=False, comment="图片高度，像素"),
    Column("format", String(10), default='', server_default=text("''"), nullable=False, comment="图片格式：jpg/png/gif等"),
    Column("status", String(20), default=FileStatus.ACTIVE.value, server_default=text("'active'"), nullable=False, comment="文件状态：uploading/active/deleted"),
    Column("access_token", String(255), default='', server_default=text("''"), nullable=False, index=True, comment="访问令牌，带索引"),
    Column("download_count", Integer, default=0, server_default=text("0"), nullable=False, comment="下载次数"),
    Column("created_at", DateTime, default=datetime.now, server_default=text("NOW()"), nullable=False, comment="创建时间"),
    Column("updated_at", DateTime, default=datetime.now, server_default=text("NOW()"), nullable=False, comment="更新时间"),
    Column("expires_at", DateTime, nullable=True, comment="过期时间，NULL表示永不过期")
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
        self.width = kwargs.get('width', 0)
        self.height = kwargs.get('height', 0)
        self.format = kwargs.get('format', '')
        self.status = kwargs.get('status', FileStatus.ACTIVE)
        self.access_token = kwargs.get('access_token', '')
        self.download_count = kwargs.get('download_count', 0)
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
        self.expires_at = kwargs.get('expires_at')
    
    @property
    def is_expired(self) -> bool:
        """检查文件是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def is_image(self) -> bool:
        """检查是否为图片文件"""
        return self.content_type.startswith('image/')


# 上传会话表定义
upload_sessions_table = Table(
    "wpic_upload_sessions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True, comment="上传会话ID，主键"),
    Column("session_id", String(255), unique=True, index=True, nullable=False, comment="上传会话唯一标识符，唯一索引"),
    Column("user_id", Integer, ForeignKey("wpic_users.id"), nullable=False, comment="上传用户ID，外键关联wpic_users.id"),
    Column("filename", String(255), nullable=False, comment="上传文件名"),
    Column("total_size", BigInteger, nullable=False, comment="文件总大小，单位字节"),
    Column("chunk_size", Integer, default=1024*1024, server_default=text("1048576"), nullable=False, comment="分块大小，单位字节，默认1MB"),
    Column("chunks_received", Integer, default=0, server_default=text("0"), nullable=False, comment="已接收分块数量"),
    Column("total_chunks", Integer, nullable=False, comment="总分块数量"),
    Column("is_completed", Boolean, default=False, server_default=text("0"), nullable=False, comment="是否上传完成"),
    Column("temp_path", String(500), nullable=False, comment="临时文件路径"),
    Column("created_at", DateTime, default=datetime.now, server_default=text("NOW()"), nullable=False, comment="创建时间"),
    Column("expires_at", DateTime, nullable=False, comment="过期时间")
)

# 访问日志表定义
access_logs_table = Table(
    "wpic_access_logs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True, comment="访问日志ID，主键"),
    Column("file_record_id", Integer, ForeignKey("wpic_file_records.id"), nullable=False, comment="文件记录ID，外键关联wpic_file_records.id"),
    Column("ip_address", String(45), nullable=False, comment="访问者IP地址，支持IPv6"),
    Column("user_agent", String(500), default='', server_default=text("''"), nullable=False, comment="用户代理字符串"),
    Column("referer", String(500), default='', server_default=text("''"), nullable=False, comment="引用页面URL"),
    Column("access_type", String(20), nullable=False, comment="访问类型：view/download/thumbnail"),
    Column("accessed_at", DateTime, default=datetime.now, server_default=text("NOW()"), nullable=False, comment="访问时间")
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
        self.created_at = kwargs.get('created_at', datetime.now())
        self.expires_at = kwargs.get('expires_at')
    
    @property
    def is_expired(self) -> bool:
        """检查上传会话是否过期"""
        return datetime.now() > self.expires_at
    
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
        self.user_agent = kwargs.get('user_agent', '')
        self.referer = kwargs.get('referer', '')
        self.access_type = kwargs.get('access_type')
        self.accessed_at = kwargs.get('accessed_at', datetime.now())
