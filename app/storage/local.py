"""
本地存储后端实现
"""
import os
import aiofiles
from pathlib import Path
from typing import Optional, AsyncGenerator, Dict, Any
from .base import BaseStorage, StorageException


class LocalStorage(BaseStorage):
    """本地文件系统存储后端"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化本地存储
        
        Args:
            config: 配置字典，包含base_path等配置项
        """
        super().__init__(config)
        self.base_path = Path(config.get('base_path', './uploads'))
        
        # 确保基础目录存在
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_full_path(self, file_path: str) -> Path:
        """获取文件的完整路径
        
        Args:
            file_path: 相对文件路径
            
        Returns:
            Path: 完整文件路径
        """
        return self.base_path / file_path.lstrip('/')
    
    async def save_file(self, file_path: str, file_data: bytes) -> bool:
        """保存文件到本地文件系统
        
        Args:
            file_path: 文件路径
            file_data: 文件数据
            
        Returns:
            bool: 保存是否成功
            
        Raises:
            StorageException: 保存失败时抛出
        """
        try:
            full_path = self._get_full_path(file_path)
            
            # 确保父目录存在
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 异步写入文件
            async with aiofiles.open(full_path, 'wb') as f:
                await f.write(file_data)
            
            return True
            
        except Exception as e:
            raise StorageException(f"保存文件失败: {str(e)}")
    
    async def get_file(self, file_path: str) -> Optional[bytes]:
        """从本地文件系统获取文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[bytes]: 文件数据，文件不存在时返回None
            
        Raises:
            StorageException: 读取失败时抛出
        """
        try:
            full_path = self._get_full_path(file_path)
            
            if not full_path.exists():
                return None
            
            async with aiofiles.open(full_path, 'rb') as f:
                return await f.read()
                
        except Exception as e:
            raise StorageException(f"读取文件失败: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """从本地文件系统删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 删除是否成功
            
        Raises:
            StorageException: 删除失败时抛出
        """
        try:
            full_path = self._get_full_path(file_path)
            
            if not full_path.exists():
                return True  # 文件不存在视为删除成功
            
            full_path.unlink()
            
            # 尝试删除空的父目录
            try:
                parent = full_path.parent
                if parent != self.base_path and not any(parent.iterdir()):
                    parent.rmdir()
            except:
                pass  # 忽略删除父目录的错误
            
            return True
            
        except Exception as e:
            raise StorageException(f"删除文件失败: {str(e)}")
    
    async def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 文件是否存在
        """
        try:
            full_path = self._get_full_path(file_path)
            return full_path.exists() and full_path.is_file()
        except:
            return False
    
    async def get_file_size(self, file_path: str) -> Optional[int]:
        """获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[int]: 文件大小（字节），文件不存在时返回None
        """
        try:
            full_path = self._get_full_path(file_path)
            
            if not full_path.exists():
                return None
            
            return full_path.stat().st_size
            
        except:
            return None
    
    async def get_file_stream(self, file_path: str) -> Optional[AsyncGenerator[bytes, None]]:
        """获取文件流
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[AsyncGenerator[bytes, None]]: 文件流生成器
        """
        try:
            full_path = self._get_full_path(file_path)
            
            if not full_path.exists():
                return None
            
            async def stream():
                async with aiofiles.open(full_path, 'rb') as f:
                    while True:
                        chunk = await f.read(8192)
                        if not chunk:
                            break
                        yield chunk
            
            return stream()
            
        except Exception as e:
            raise StorageException(f"读取文件流失败: {str(e)}")
    
    async def save_file_stream(self, file_path: str, file_stream: AsyncGenerator[bytes, None]) -> bool:
        """保存文件流
        
        Args:
            file_path: 文件路径
            file_stream: 文件流
            
        Returns:
            bool: 保存是否成功
        """
        try:
            full_path = self._get_full_path(file_path)
            
            # 确保父目录存在
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(full_path, 'wb') as f:
                async for chunk in file_stream:
                    await f.write(chunk)
            
            return True
            
        except Exception as e:
            raise StorageException(f"保存文件流失败: {str(e)}")
    
    def get_file_url(self, file_path: str) -> Optional[str]:
        """获取文件访问URL（本地存储不支持直接URL访问）
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 始终返回None
        """
        return None
