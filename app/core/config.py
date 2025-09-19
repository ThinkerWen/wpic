"""
配置管理模块
支持从环境变量和配置文件加载设置
"""
from typing import Optional, Union, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    model_config = SettingsConfigDict(env_prefix="DB_", extra="ignore")
    
    # 数据库URL，支持MySQL和PostgreSQL
    database_url: str = Field(
        default="sqlite:///./app.db",
        description="数据库连接URL"
    )


class RedisConfig(BaseSettings):
    """Redis配置"""
    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="ignore")
    
    host: str = Field(default="localhost", description="Redis主机")
    port: int = Field(default=6379, description="Redis端口")
    password: Optional[str] = Field(default=None, description="Redis密码")
    db: int = Field(default=0, description="Redis数据库号")


class StorageConfig(BaseSettings):
    """存储配置"""
    model_config = SettingsConfigDict(env_prefix="STORAGE_", extra="ignore")
    
    # 本地存储
    local_base_path: str = Field(default="./uploads", description="本地存储基础路径")
    
    # S3存储
    s3_access_key: Optional[str] = Field(default=None, description="S3访问密钥")
    s3_secret_key: Optional[str] = Field(default=None, description="S3密钥")
    s3_bucket: Optional[str] = Field(default=None, description="S3存储桶")
    s3_region: Optional[str] = Field(default="us-east-1", description="S3区域")
    s3_endpoint: Optional[str] = Field(default=None, description="S3端点URL")
    
    # WebDAV存储
    webdav_url: Optional[str] = Field(default=None, description="WebDAV服务器URL")
    webdav_username: Optional[str] = Field(default=None, description="WebDAV用户名")
    webdav_password: Optional[str] = Field(default=None, description="WebDAV密码")


class SecurityConfig(BaseSettings):
    """安全配置"""
    model_config = SettingsConfigDict(env_prefix="SECURITY_", extra="ignore")
    
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        description="JWT密钥"
    )
    algorithm: str = Field(default="HS256", description="JWT算法")
    access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间(分钟)")
    enable_auth: bool = Field(default=True, description="是否启用认证")


class AppConfig(BaseSettings):
    """应用配置"""
    model_config = SettingsConfigDict(env_prefix="APP_", extra="ignore")
    
    title: str = Field(default="WPIC 图床后端", description="应用标题")
    description: str = Field(default="一个功能完整的图床后端服务", description="应用描述")
    version: str = Field(default="1.0.0", description="应用版本")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    debug: bool = Field(default=False, description="调试模式")
    
    # 文件上传配置
    max_file_size: int = Field(default=10 * 1024 * 1024, description="最大文件大小(字节)")  # 10MB
    allowed_extensions: list = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".bmp", ".tiff"],
        description="允许的文件扩展名"
    )
    
    # 预览配置
    thumbnail_size: tuple = Field(default=(200, 200), description="缩略图尺寸")
    preview_size: tuple = Field(default=(800, 600), description="预览图尺寸")
    
    # 文件管理
    auto_rename: bool = Field(default=True, description="是否自动重命名文件")


class Settings(BaseSettings):
    """全局设置"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # 各模块配置
    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    storage: StorageConfig = StorageConfig()
    security: SecurityConfig = SecurityConfig()


# 全局设置实例
settings = Settings()


def get_settings() -> Settings:
    """获取设置实例"""
    return settings
