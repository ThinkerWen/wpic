"""
存储管理器模块
统一管理不同存储后端的创建和使用
"""
from typing import Dict, Any, Optional

from app.core.config import get_settings
from app.models import User, StorageType
from app.storage import BaseStorage, LocalStorage, WebDAVStorage, S3Storage

settings = get_settings()


class StorageManager:
    """存储管理器"""
    
    def __init__(self):
        """初始化存储管理器"""
        self._storage_cache: Dict[str, BaseStorage] = {}
    
    def get_storage_for_user(self, user: User) -> BaseStorage:
        """为用户获取存储后端实例
        
        Args:
            user: 用户对象
            
        Returns:
            BaseStorage: 存储后端实例
            
        Raises:
            ValueError: 不支持的存储类型
        """
        # 生成缓存键
        cache_key = f"{user.id}_{user.storage_type.value}"
        
        # 检查缓存
        if cache_key in self._storage_cache:
            return self._storage_cache[cache_key]
        
        # 创建存储实例
        storage = self._create_storage(user.storage_type, user.storage_config, user.id)
        
        # 缓存存储实例
        self._storage_cache[cache_key] = storage
        
        return storage
    
    def _create_storage(self, storage_type: StorageType, 
                       user_config: Optional[Dict[str, Any]], 
                       user_id: int) -> BaseStorage:
        """创建存储后端实例
        
        Args:
            storage_type: 存储类型
            user_config: 用户存储配置
            user_id: 用户ID
            
        Returns:
            BaseStorage: 存储后端实例
            
        Raises:
            ValueError: 不支持的存储类型
        """
        config = user_config or {}
        
        if storage_type == StorageType.LOCAL:
            return self._create_local_storage(config, user_id)
        elif storage_type == StorageType.WEBDAV:
            return self._create_webdav_storage(config)
        elif storage_type == StorageType.S3:
            return self._create_s3_storage(config)
        else:
            raise ValueError(f"不支持的存储类型: {storage_type}")
    
    def _create_local_storage(self, config: Dict[str, Any], user_id: int) -> LocalStorage:
        """创建本地存储实例
        
        Args:
            config: 存储配置
            user_id: 用户ID
            
        Returns:
            LocalStorage: 本地存储实例
        """
        base_path = config.get("base_path", settings.storage.local_base_path)
        
        # 为每个用户创建独立目录
        user_base_path = f"{base_path}/user_{user_id}"
        
        return LocalStorage({
            "base_path": user_base_path
        })
    
    def _create_webdav_storage(self, config: Dict[str, Any]) -> WebDAVStorage:
        """创建WebDAV存储实例
        
        Args:
            config: 存储配置
            
        Returns:
            WebDAVStorage: WebDAV存储实例
        """
        # 合并默认配置和用户配置
        webdav_config = {
            "url": config.get("url", settings.storage.webdav_url),
            "username": config.get("username", settings.storage.webdav_username),
            "password": config.get("password", settings.storage.webdav_password)
        }
        
        # 验证必需配置
        if not all([webdav_config["url"], webdav_config["username"], webdav_config["password"]]):
            raise ValueError("WebDAV配置不完整：需要url、username和password")
        
        return WebDAVStorage(webdav_config)
    
    def _create_s3_storage(self, config: Dict[str, Any]) -> S3Storage:
        """创建S3存储实例
        
        Args:
            config: 存储配置
            
        Returns:
            S3Storage: S3存储实例
        """
        # 合并默认配置和用户配置
        s3_config = {
            "access_key": config.get("access_key", settings.storage.s3_access_key),
            "secret_key": config.get("secret_key", settings.storage.s3_secret_key),
            "bucket": config.get("bucket", settings.storage.s3_bucket),
            "region": config.get("region", settings.storage.s3_region),
            "endpoint": config.get("endpoint", settings.storage.s3_endpoint)
        }
        
        # 验证必需配置
        if not all([s3_config["access_key"], s3_config["secret_key"], s3_config["bucket"]]):
            raise ValueError("S3配置不完整：需要access_key、secret_key和bucket")
        
        return S3Storage(s3_config)
    
    def validate_storage_config(self, storage_type: StorageType, 
                               config: Dict[str, Any]) -> bool:
        """验证存储配置是否有效
        
        Args:
            storage_type: 存储类型
            config: 配置字典
            
        Returns:
            bool: 配置是否有效
        """
        try:
            # 尝试创建存储实例来验证配置
            self._create_storage(storage_type, config, 0)
            return True
        except Exception:
            return False
    
    async def test_storage_connection(self, storage: BaseStorage) -> bool:
        """测试存储连接是否正常
        
        Args:
            storage: 存储实例
            
        Returns:
            bool: 连接是否正常
        """
        try:
            # 创建一个测试文件
            test_data = b"test"
            test_path = "test_connection.txt"
            
            # 尝试保存文件
            await storage.save_file(test_path, test_data)
            
            # 尝试读取文件
            read_data = await storage.get_file(test_path)
            
            # 尝试删除文件
            await storage.delete_file(test_path)
            
            # 验证数据一致性
            return read_data == test_data
            
        except Exception:
            return False
    
    def clear_cache(self, user_id: Optional[int] = None):
        """清除存储缓存
        
        Args:
            user_id: 用户ID，如果为None则清除所有缓存
        """
        if user_id is None:
            self._storage_cache.clear()
        else:
            # 清除特定用户的缓存
            keys_to_remove = [key for key in self._storage_cache.keys() if key.startswith(f"{user_id}_")]
            for key in keys_to_remove:
                del self._storage_cache[key]
    
    def get_supported_storage_types(self) -> Dict[str, Dict[str, Any]]:
        """获取支持的存储类型信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 存储类型信息
        """
        return {
            "local": {
                "name": "本地存储",
                "description": "存储文件到本地文件系统",
                "required_config": ["base_path"],
                "optional_config": []
            },
            "webdav": {
                "name": "WebDAV存储",
                "description": "存储文件到WebDAV服务器",
                "required_config": ["url", "username", "password"],
                "optional_config": []
            },
            "s3": {
                "name": "S3对象存储",
                "description": "存储文件到AWS S3或兼容服务",
                "required_config": ["access_key", "secret_key", "bucket"],
                "optional_config": ["region", "endpoint"]
            }
        }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储管理器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "cached_storages": len(self._storage_cache),
            "supported_types": list(self.get_supported_storage_types().keys())
        }


# 全局存储管理器实例
storage_manager = StorageManager()


def get_storage_manager() -> StorageManager:
    """获取存储管理器实例
    
    Returns:
        StorageManager: 存储管理器实例
    """
    return storage_manager
