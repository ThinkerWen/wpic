"""
数据库模型定义
使用SQLModel，简洁版本
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


def get_current_timestamp() -> datetime:
    """获取当前时间戳，不包含毫秒"""
    now = datetime.now()
    return now.replace(microsecond=0)


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


# 用户模型
class User(SQLModel, table=True):
    """用户模型"""
    __tablename__ = "wpic_users"

    id: Optional[int] = Field(default=None, primary_key=True, description="用户ID，主键")
    username: str = Field(max_length=50, unique=True, index=True, description="用户名，唯一索引")
    email: str = Field(max_length=100, unique=True, index=True, description="邮箱地址，唯一索引")
    password_hash: str = Field(max_length=255, description="密码哈希值")
    storage_type: str = Field(default=StorageType.LOCAL.value, max_length=20, description="存储类型：local/webdav/s3")
    storage_config: str = Field(default="{}", description="存储配置信息JSON")
    storage_quota: int = Field(default=1024*1024*100, description="存储配额，单位字节，默认100MB")
    storage_used: int = Field(default=0, description="已使用存储空间，单位字节")
    is_active: bool = Field(default=True, description="用户是否激活")
    created_at: datetime = Field(default_factory=get_current_timestamp, description="创建时间")
    updated_at: datetime = Field(default_factory=get_current_timestamp, description="更新时间")

    # 关系
    file_records: list["FileRecord"] = Relationship(back_populates="user")
    upload_sessions: list["UploadSession"] = Relationship(back_populates="user")

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


# 文件记录模型
class FileRecord(SQLModel, table=True):
    """文件记录模型"""
    __tablename__ = "wpic_file_records"

    id: Optional[int] = Field(default=None, primary_key=True, description="文件记录ID，主键")
    user_id: int = Field(foreign_key="wpic_users.id", description="所属用户ID，外键关联wpic_users.id")
    filename: str = Field(max_length=255, index=True, description="文件名，带索引")
    original_filename: str = Field(max_length=255, description="原始文件名")
    file_path: str = Field(max_length=500, description="文件存储路径")
    file_size: int = Field(description="文件大小，单位字节")
    content_type: str = Field(max_length=100, description="文件MIME类型")
    file_hash: str = Field(max_length=64, index=True, description="文件哈希值，用于去重，带索引")
    width: int = Field(default=0, description="图片宽度，像素")
    height: int = Field(default=0, description="图片高度，像素")
    format: str = Field(default="", max_length=10, description="图片格式：jpg/png/gif等")
    status: str = Field(default=FileStatus.ACTIVE.value, max_length=20, description="文件状态：uploading/active/deleted")
    access_token: str = Field(default="", max_length=255, index=True, description="访问令牌，带索引")
    download_count: int = Field(default=0, description="下载次数")
    created_at: datetime = Field(default_factory=get_current_timestamp, description="创建时间")
    updated_at: datetime = Field(default_factory=get_current_timestamp, description="更新时间")
    expires_at: datetime = Field(default_factory=get_current_timestamp, description="过期时间，默认为当前时间")

    # 关系
    user: Optional[User] = Relationship(back_populates="file_records")
    access_logs: list["AccessLog"] = Relationship(back_populates="file_record")

    @property
    def is_expired(self) -> bool:
        """检查文件是否过期"""
        return datetime.now() > self.expires_at

    @property
    def is_image(self) -> bool:
        """检查是否为图片文件"""
        return self.content_type.startswith('image/')


# 上传会话模型
class UploadSession(SQLModel, table=True):
    """上传会话模型"""
    __tablename__ = "wpic_upload_sessions"

    id: Optional[int] = Field(default=None, primary_key=True, description="上传会话ID，主键")
    session_id: str = Field(max_length=255, unique=True, index=True, description="上传会话唯一标识符，唯一索引")
    user_id: int = Field(foreign_key="wpic_users.id", description="上传用户ID，外键关联wpic_users.id")
    filename: str = Field(max_length=255, description="上传文件名")
    total_size: int = Field(description="文件总大小，单位字节")
    chunk_size: int = Field(default=1024*1024, description="分块大小，单位字节，默认1MB")
    chunks_received: int = Field(default=0, description="已接收分块数量")
    total_chunks: int = Field(description="总分块数量")
    is_completed: bool = Field(default=False, description="是否上传完成")
    temp_path: str = Field(max_length=500, description="临时文件路径")
    created_at: datetime = Field(default_factory=get_current_timestamp, description="创建时间")
    expires_at: datetime = Field(default_factory=get_current_timestamp, description="过期时间")

    # 关系
    user: Optional[User] = Relationship(back_populates="upload_sessions")

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


# 访问日志模型
class AccessLog(SQLModel, table=True):
    """访问日志模型"""
    __tablename__ = "wpic_access_logs"

    id: Optional[int] = Field(default=None, primary_key=True, description="访问日志ID，主键")
    file_record_id: int = Field(foreign_key="wpic_file_records.id", description="文件记录ID，外键关联wpic_file_records.id")
    ip_address: str = Field(max_length=45, description="访问者IP地址，支持IPv6")
    user_agent: str = Field(default="", max_length=500, description="用户代理字符串")
    referer: str = Field(default="", max_length=500, description="引用页面URL")
    access_type: str = Field(max_length=20, description="访问类型：view/download/thumbnail")
    accessed_at: datetime = Field(default_factory=get_current_timestamp, description="访问时间")

    # 关系
    file_record: Optional[FileRecord] = Relationship(back_populates="access_logs")