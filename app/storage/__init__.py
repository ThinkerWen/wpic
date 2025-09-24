"""
存储后端模块
支持本地、WebDAV和S3存储
"""
from .base import BaseStorage
from .local import LocalStorage
from .s3 import S3Storage
from .webdav import WebDAVStorage

__all__ = [
    "BaseStorage",
    "LocalStorage", 
    "WebDAVStorage",
    "S3Storage"
]
