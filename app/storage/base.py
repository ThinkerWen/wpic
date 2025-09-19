"""
存储后端基础类
定义存储接口规范
"""
from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator, Dict, Any
import aiofiles
from pathlib import Path


class StorageException(Exception):
    """存储操作异常"""
    pass


class BaseStorage(ABC):
    """存储后端基础类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化存储后端
        
        Args:
            config: 存储配置字典
        """
        self.config = config
    
    @abstractmethod
    async def save_file(self, file_path: str, file_data: bytes) -> bool:
        """保存文件
        
        Args:
            file_path: 文件路径
            file_data: 文件数据
            
        Returns:
            bool: 保存是否成功
            
        Raises:
            StorageException: 保存失败时抛出
        """
        pass
    
    @abstractmethod
    async def get_file(self, file_path: str) -> Optional[bytes]:
        """获取文件数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[bytes]: 文件数据，文件不存在时返回None
            
        Raises:
            StorageException: 获取失败时抛出
        """
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 删除是否成功
            
        Raises:
            StorageException: 删除失败时抛出
        """
        pass
    
    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 文件是否存在
        """
        pass
    
    @abstractmethod
    async def get_file_size(self, file_path: str) -> Optional[int]:
        """获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[int]: 文件大小（字节），文件不存在时返回None
        """
        pass
    
    async def get_file_stream(self, file_path: str) -> Optional[AsyncGenerator[bytes, None]]:
        """获取文件流（默认实现，子类可重写以优化）
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[AsyncGenerator[bytes, None]]: 文件流生成器
        """
        file_data = await self.get_file(file_path)
        if file_data is None:
            return None
        
        async def stream():
            chunk_size = 8192
            for i in range(0, len(file_data), chunk_size):
                yield file_data[i:i+chunk_size]
        
        return stream()
    
    def get_file_url(self, file_path: str) -> Optional[str]:
        """获取文件访问URL（可选实现）
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 文件URL，不支持时返回None
        """
        return None
    
    async def save_file_stream(self, file_path: str, file_stream: AsyncGenerator[bytes, None]) -> bool:
        """保存文件流（默认实现，子类可重写以优化）
        
        Args:
            file_path: 文件路径
            file_stream: 文件流
            
        Returns:
            bool: 保存是否成功
        """
        chunks = []
        async for chunk in file_stream:
            chunks.append(chunk)
        
        file_data = b''.join(chunks)
        return await self.save_file(file_path, file_data)
