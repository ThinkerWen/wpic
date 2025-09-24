"""
WebDAV存储后端实现
"""
import base64
from typing import Optional, AsyncGenerator, Dict, Any
from urllib.parse import urljoin

import aiohttp

from .base import BaseStorage, StorageException


class WebDAVStorage(BaseStorage):
    """WebDAV存储后端"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化WebDAV存储
        
        Args:
            config: 配置字典，包含url、username、password等配置项
        """
        super().__init__(config)
        self.base_url = config.get('url', '').rstrip('/')
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        
        if not self.base_url:
            raise StorageException("WebDAV URL配置不能为空")
        
        # 创建认证头
        self._auth_header = None
        if self.username and self.password:
            credentials = f"{self.username}:{self.password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            self._auth_header = f"Basic {encoded_credentials}"
    
    def _get_full_url(self, file_path: str) -> str:
        """获取文件的完整URL
        
        Args:
            file_path: 相对文件路径
            
        Returns:
            str: 完整文件URL
        """
        return urljoin(self.base_url + '/', file_path.lstrip('/'))
    
    def _get_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """获取请求头
        
        Args:
            additional_headers: 额外的请求头
            
        Returns:
            Dict[str, str]: 请求头字典
        """
        headers = {}
        if self._auth_header:
            headers['Authorization'] = self._auth_header
        
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    async def _ensure_directory(self, session: aiohttp.ClientSession, file_path: str):
        """确保目录存在
        
        Args:
            session: HTTP会话
            file_path: 文件路径
        """
        path_parts = file_path.strip('/').split('/')
        current_path = ''
        
        for part in path_parts[:-1]:  # 排除文件名
            current_path += f"/{part}"
            dir_url = urljoin(self.base_url + '/', current_path.lstrip('/') + '/')
            
            # 检查目录是否存在
            async with session.request(
                'PROPFIND',
                dir_url,
                headers=self._get_headers({'Depth': '0'})
            ) as response:
                if response.status == 404:
                    # 创建目录
                    async with session.request(
                        'MKCOL',
                        dir_url,
                        headers=self._get_headers()
                    ) as create_response:
                        if create_response.status not in (201, 405):  # 405表示目录已存在
                            raise StorageException(f"创建目录失败: {create_response.status}")
    
    async def save_file(self, file_path: str, file_data: bytes) -> bool:
        """保存文件到WebDAV服务器
        
        Args:
            file_path: 文件路径
            file_data: 文件数据
            
        Returns:
            bool: 保存是否成功
            
        Raises:
            StorageException: 保存失败时抛出
        """
        try:
            async with aiohttp.ClientSession() as session:
                # 确保目录存在
                await self._ensure_directory(session, file_path)
                
                # 上传文件
                url = self._get_full_url(file_path)
                async with session.put(
                    url,
                    data=file_data,
                    headers=self._get_headers()
                ) as response:
                    if response.status not in (200, 201, 204):
                        raise StorageException(f"上传文件失败: HTTP {response.status}")
                    
                    return True
                    
        except aiohttp.ClientError as e:
            raise StorageException(f"WebDAV连接错误: {str(e)}")
        except Exception as e:
            raise StorageException(f"保存文件失败: {str(e)}")
    
    async def get_file(self, file_path: str) -> Optional[bytes]:
        """从WebDAV服务器获取文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[bytes]: 文件数据，文件不存在时返回None
            
        Raises:
            StorageException: 读取失败时抛出
        """
        try:
            url = self._get_full_url(file_path)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 404:
                        return None
                    
                    if response.status != 200:
                        raise StorageException(f"获取文件失败: HTTP {response.status}")
                    
                    return await response.read()
                    
        except aiohttp.ClientError as e:
            raise StorageException(f"WebDAV连接错误: {str(e)}")
        except Exception as e:
            raise StorageException(f"读取文件失败: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """从WebDAV服务器删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 删除是否成功
            
        Raises:
            StorageException: 删除失败时抛出
        """
        try:
            url = self._get_full_url(file_path)
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=self._get_headers()) as response:
                    if response.status in (200, 204, 404):  # 404表示文件不存在，视为删除成功
                        return True
                    
                    raise StorageException(f"删除文件失败: HTTP {response.status}")
                    
        except aiohttp.ClientError as e:
            raise StorageException(f"WebDAV连接错误: {str(e)}")
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
            url = self._get_full_url(file_path)
            
            async with aiohttp.ClientSession() as session:
                async with session.head(url, headers=self._get_headers()) as response:
                    return response.status == 200
                    
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
            url = self._get_full_url(file_path)
            
            async with aiohttp.ClientSession() as session:
                async with session.head(url, headers=self._get_headers()) as response:
                    if response.status != 200:
                        return None
                    
                    content_length = response.headers.get('Content-Length')
                    if content_length:
                        return int(content_length)
                    
                    return None
                    
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
            url = self._get_full_url(file_path)
            
            session = aiohttp.ClientSession()
            response = await session.get(url, headers=self._get_headers())
            
            if response.status == 404:
                await session.close()
                return None
            
            if response.status != 200:
                await session.close()
                raise StorageException(f"获取文件流失败: HTTP {response.status}")
            
            async def stream():
                try:
                    async for chunk in response.content.iter_chunked(8192):
                        yield chunk
                finally:
                    await response.close()
                    await session.close()
            
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
        # WebDAV的PUT方法需要完整的数据，所以先收集所有chunks
        chunks = []
        async for chunk in file_stream:
            chunks.append(chunk)
        
        file_data = b''.join(chunks)
        return await self.save_file(file_path, file_data)
    
    def get_file_url(self, file_path: str) -> Optional[str]:
        """获取文件访问URL
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: 文件URL
        """
        return self._get_full_url(file_path)
