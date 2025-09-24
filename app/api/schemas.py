"""
API请求和响应模式定义
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, validator

from app.models import StorageType, FileStatus


class UserBase(BaseModel):
    """用户基础模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱地址")


class UserCreate(UserBase):
    """创建用户模式"""
    password: str = Field(..., min_length=6, description="密码")
    storage_type: StorageType = Field(default=StorageType.LOCAL, description="存储类型")
    storage_config: Optional[Dict[str, Any]] = Field(default={}, description="存储配置")
    storage_quota: int = Field(default=1024*1024*1024, description="存储配额（字节）")


class UserUpdate(BaseModel):
    """更新用户模式"""
    email: Optional[str] = None
    storage_type: Optional[StorageType] = None
    storage_config: Optional[Dict[str, Any]] = None
    storage_quota: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """用户响应模式"""
    id: int
    storage_type: StorageType
    storage_quota: int
    storage_used: int
    remaining_storage: int
    storage_usage_percent: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """用户登录模式"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class Token(BaseModel):
    """令牌响应模式"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class FileUploadResponse(BaseModel):
    """文件上传响应模式"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    file_hash: str
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    download_url: str
    thumbnail_url: Optional[str] = None
    preview_url: Optional[str] = None
    share_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FileResponse(BaseModel):
    """文件响应模式"""
    id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    content_type: str
    file_hash: str
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    status: FileStatus
    download_count: int
    download_url: str
    thumbnail_url: Optional[str] = None
    preview_url: Optional[str] = None
    share_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """文件列表响应模式"""
    files: List[FileResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FileShareRequest(BaseModel):
    """文件分享请求模式"""
    expires_in_hours: int = Field(default=24, ge=1, le=8760, description="过期时间（小时），最长1年")


class FileShareResponse(BaseModel):
    """文件分享响应模式"""
    share_url: str
    access_token: str
    expires_at: datetime


class StorageConfigRequest(BaseModel):
    """存储配置请求模式"""
    storage_type: StorageType
    config: Dict[str, Any] = Field(..., description="存储配置")

    @validator('config')
    def validate_config(cls, v, values):
        """验证存储配置"""
        storage_type = values.get('storage_type')
        
        if storage_type == StorageType.LOCAL:
            required_fields = ['base_path']
        elif storage_type == StorageType.WEBDAV:
            required_fields = ['url', 'username', 'password']
        elif storage_type == StorageType.S3:
            required_fields = ['access_key', 'secret_key', 'bucket']
        else:
            raise ValueError(f"不支持的存储类型: {storage_type}")
        
        for field in required_fields:
            if field not in v:
                raise ValueError(f"存储配置缺少必需字段: {field}")
        
        return v


class ErrorResponse(BaseModel):
    """错误响应模式"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """成功响应模式"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ImageProcessRequest(BaseModel):
    """图片处理请求模式"""
    width: Optional[int] = Field(None, ge=1, le=4096, description="目标宽度")
    height: Optional[int] = Field(None, ge=1, le=4096, description="目标高度")
    format: Optional[str] = Field(None, description="输出格式")
    quality: Optional[int] = Field(85, ge=1, le=100, description="输出质量")
    keep_aspect_ratio: bool = Field(True, description="保持宽高比")


class ThumbnailRequest(BaseModel):
    """缩略图请求模式"""
    width: int = Field(200, ge=50, le=800, description="缩略图宽度")
    height: int = Field(200, ge=50, le=800, description="缩略图高度")
    format: str = Field("webp", description="输出格式")


class StatsResponse(BaseModel):
    """统计信息响应模式"""
    total_files: int
    total_storage_used: int
    total_downloads: int
    files_by_format: Dict[str, int]
    storage_by_type: Dict[str, int]


class UserStatsResponse(BaseModel):
    """用户统计信息响应模式"""
    file_count: int
    storage_used: int
    storage_quota: int
    storage_usage_percent: float
    total_downloads: int
    recent_uploads: int  # 最近7天上传数


class UploadSessionCreate(BaseModel):
    """创建上传会话请求模式"""
    filename: str = Field(..., description="文件名")
    total_size: int = Field(..., ge=1, description="文件总大小")
    chunk_size: int = Field(1024*1024, ge=1024, le=10*1024*1024, description="分片大小")


class UploadSessionResponse(BaseModel):
    """上传会话响应模式"""
    session_id: str
    filename: str
    total_size: int
    chunk_size: int
    total_chunks: int
    chunks_received: int
    progress_percent: float
    is_completed: bool
    expires_at: datetime

    class Config:
        from_attributes = True


class ChunkUploadRequest(BaseModel):
    """分片上传请求模式"""
    chunk_index: int = Field(..., ge=0, description="分片索引")
    chunk_hash: str = Field(..., description="分片MD5哈希")


class ConfigResponse(BaseModel):
    """配置响应模式"""
    max_file_size: int
    allowed_extensions: List[str]
    storage_types: List[str]
    auth_enabled: bool
    thumbnail_size: tuple
    preview_size: tuple
