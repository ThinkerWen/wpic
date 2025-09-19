"""
Redis缓存模块
提供文件缓存和缩略图缓存功能
"""
import redis.asyncio as redis
import pickle
import json
from typing import Optional, Any, Union, Dict
import hashlib
from datetime import datetime, timedelta
from app.core.config import get_settings

settings = get_settings()


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        """初始化缓存管理器"""
        self.redis_client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self):
        """连接到Redis"""
        if self._connected:
            return
        
        try:
            self.redis_client = redis.Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                password=settings.redis.password,
                db=settings.redis.db,
                decode_responses=False,  # 保持二进制数据
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # 测试连接
            await self.redis_client.ping()
            self._connected = True
            
        except Exception as e:
            print(f"Redis连接失败: {str(e)}")
            self.redis_client = None
            self._connected = False
    
    async def disconnect(self):
        """断开Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            self._connected = False
    
    def _generate_cache_key(self, prefix: str, identifier: str) -> str:
        """生成缓存键
        
        Args:
            prefix: 缓存前缀
            identifier: 标识符
            
        Returns:
            str: 缓存键
        """
        # 使用MD5哈希确保键名不会太长
        hash_obj = hashlib.md5(identifier.encode())
        return f"wpic:{prefix}:{hash_obj.hexdigest()}"
    
    async def set_file_cache(self, file_path: str, file_data: bytes, ttl: int = 3600) -> bool:
        """设置文件缓存
        
        Args:
            file_path: 文件路径
            file_data: 文件数据
            ttl: 过期时间（秒），默认1小时
            
        Returns:
            bool: 设置是否成功
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key("file", file_path)
            await self.redis_client.setex(cache_key, ttl, file_data)
            return True
        except Exception as e:
            print(f"设置文件缓存失败: {str(e)}")
            return False
    
    async def get_file_cache(self, file_path: str) -> Optional[bytes]:
        """获取文件缓存
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[bytes]: 缓存的文件数据，不存在时返回None
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key("file", file_path)
            return await self.redis_client.get(cache_key)
        except Exception as e:
            print(f"获取文件缓存失败: {str(e)}")
            return None
    
    async def set_thumbnail_cache(self, file_path: str, size: tuple, thumbnail_data: bytes, ttl: int = 7200) -> bool:
        """设置缩略图缓存
        
        Args:
            file_path: 原文件路径
            size: 缩略图尺寸 (width, height)
            thumbnail_data: 缩略图数据
            ttl: 过期时间（秒），默认2小时
            
        Returns:
            bool: 设置是否成功
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key("thumb", f"{file_path}:{size[0]}x{size[1]}")
            await self.redis_client.setex(cache_key, ttl, thumbnail_data)
            return True
        except Exception as e:
            print(f"设置缩略图缓存失败: {str(e)}")
            return False
    
    async def get_thumbnail_cache(self, file_path: str, size: tuple) -> Optional[bytes]:
        """获取缩略图缓存
        
        Args:
            file_path: 原文件路径
            size: 缩略图尺寸 (width, height)
            
        Returns:
            Optional[bytes]: 缓存的缩略图数据，不存在时返回None
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key("thumb", f"{file_path}:{size[0]}x{size[1]}")
            return await self.redis_client.get(cache_key)
        except Exception as e:
            print(f"获取缩略图缓存失败: {str(e)}")
            return None
    
    async def set_metadata_cache(self, file_path: str, metadata: Dict[str, Any], ttl: int = 3600) -> bool:
        """设置文件元数据缓存
        
        Args:
            file_path: 文件路径
            metadata: 文件元数据
            ttl: 过期时间（秒），默认1小时
            
        Returns:
            bool: 设置是否成功
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key("meta", file_path)
            # 序列化元数据
            metadata_json = json.dumps(metadata, ensure_ascii=False, default=str)
            await self.redis_client.setex(cache_key, ttl, metadata_json)
            return True
        except Exception as e:
            print(f"设置元数据缓存失败: {str(e)}")
            return False
    
    async def get_metadata_cache(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取文件元数据缓存
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 缓存的元数据，不存在时返回None
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key("meta", file_path)
            metadata_json = await self.redis_client.get(cache_key)
            if metadata_json:
                return json.loads(metadata_json.decode())
            return None
        except Exception as e:
            print(f"获取元数据缓存失败: {str(e)}")
            return None
    
    async def delete_file_cache(self, file_path: str) -> bool:
        """删除文件相关的所有缓存
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 删除是否成功
        """
        if not self.redis_client:
            return False
        
        try:
            # 删除文件缓存
            file_key = self._generate_cache_key("file", file_path)
            await self.redis_client.delete(file_key)
            
            # 删除元数据缓存
            meta_key = self._generate_cache_key("meta", file_path)
            await self.redis_client.delete(meta_key)
            
            # 删除相关的缩略图缓存（通过模式匹配）
            thumb_pattern = self._generate_cache_key("thumb", f"{file_path}:*")
            thumb_keys = await self.redis_client.keys(thumb_pattern)
            if thumb_keys:
                await self.redis_client.delete(*thumb_keys)
            
            return True
        except Exception as e:
            print(f"删除文件缓存失败: {str(e)}")
            return False
    
    async def set_user_session(self, session_id: str, user_data: Dict[str, Any], ttl: int = 86400) -> bool:
        """设置用户会话缓存
        
        Args:
            session_id: 会话ID
            user_data: 用户数据
            ttl: 过期时间（秒），默认24小时
            
        Returns:
            bool: 设置是否成功
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key("session", session_id)
            user_json = json.dumps(user_data, ensure_ascii=False, default=str)
            await self.redis_client.setex(cache_key, ttl, user_json)
            return True
        except Exception as e:
            print(f"设置会话缓存失败: {str(e)}")
            return False
    
    async def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取用户会话缓存
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 用户数据，不存在时返回None
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key("session", session_id)
            user_json = await self.redis_client.get(cache_key)
            if user_json:
                return json.loads(user_json.decode())
            return None
        except Exception as e:
            print(f"获取会话缓存失败: {str(e)}")
            return None
    
    async def delete_user_session(self, session_id: str) -> bool:
        """删除用户会话缓存
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 删除是否成功
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key("session", session_id)
            await self.redis_client.delete(cache_key)
            return True
        except Exception as e:
            print(f"删除会话缓存失败: {str(e)}")
            return False
    
    async def increment_download_count(self, file_path: str, ttl: int = 86400) -> int:
        """增加文件下载计数
        
        Args:
            file_path: 文件路径
            ttl: 过期时间（秒），默认24小时
            
        Returns:
            int: 当前计数值
        """
        if not self.redis_client:
            return 0
        
        try:
            cache_key = self._generate_cache_key("count", file_path)
            count = await self.redis_client.incr(cache_key)
            # 设置过期时间（只在第一次时设置）
            if count == 1:
                await self.redis_client.expire(cache_key, ttl)
            return count
        except Exception as e:
            print(f"增加下载计数失败: {str(e)}")
            return 0
    
    async def get_download_count(self, file_path: str) -> int:
        """获取文件下载计数
        
        Args:
            file_path: 文件路径
            
        Returns:
            int: 下载计数
        """
        if not self.redis_client:
            return 0
        
        try:
            cache_key = self._generate_cache_key("count", file_path)
            count = await self.redis_client.get(cache_key)
            return int(count) if count else 0
        except Exception as e:
            print(f"获取下载计数失败: {str(e)}")
            return 0
    
    async def clear_all_cache(self) -> bool:
        """清除所有缓存（慎用）
        
        Returns:
            bool: 清除是否成功
        """
        if not self.redis_client:
            return False
        
        try:
            keys = await self.redis_client.keys("wpic:*")
            if keys:
                await self.redis_client.delete(*keys)
            return True
        except Exception as e:
            print(f"清除所有缓存失败: {str(e)}")
            return False


# 全局缓存管理器实例
cache_manager = CacheManager()


async def init_cache():
    """初始化缓存"""
    await cache_manager.connect()


async def close_cache():
    """关闭缓存"""
    await cache_manager.disconnect()


def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例"""
    return cache_manager
