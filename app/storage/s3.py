"""
S3存储后端实现
支持AWS S3和兼容S3的存储服务
"""
import boto3
import aiobotocore.session
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, AsyncGenerator, Dict, Any
from .base import BaseStorage, StorageException


class S3Storage(BaseStorage):
    """S3存储后端"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化S3存储
        
        Args:
            config: 配置字典，包含access_key、secret_key、bucket、region、endpoint等配置项
        """
        super().__init__(config)
        self.access_key = config.get('access_key')
        self.secret_key = config.get('secret_key')
        self.bucket = config.get('bucket')
        self.region = config.get('region', 'us-east-1')
        self.endpoint = config.get('endpoint')
        
        if not all([self.access_key, self.secret_key, self.bucket]):
            raise StorageException("S3配置不完整：需要access_key、secret_key和bucket")
        
        # 创建同步客户端（用于某些操作）
        self._create_sync_client()
    
    def _create_sync_client(self):
        """创建同步S3客户端"""
        try:
            session = boto3.Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            
            config = {}
            if self.endpoint:
                config['endpoint_url'] = self.endpoint
            
            self.sync_client = session.client('s3', **config)
            
        except Exception as e:
            raise StorageException(f"创建S3客户端失败: {str(e)}")
    
    async def _get_async_client(self):
        """获取异步S3客户端"""
        session = aiobotocore.session.get_session()
        
        config = {
            'region_name': self.region,
            'aws_access_key_id': self.access_key,
            'aws_secret_access_key': self.secret_key
        }
        
        if self.endpoint:
            config['endpoint_url'] = self.endpoint
        
        return session.create_client('s3', **config)
    
    def _normalize_path(self, file_path: str) -> str:
        """标准化文件路径（移除开头的斜杠）
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 标准化的路径
        """
        return file_path.lstrip('/')
    
    async def save_file(self, file_path: str, file_data: bytes) -> bool:
        """保存文件到S3
        
        Args:
            file_path: 文件路径
            file_data: 文件数据
            
        Returns:
            bool: 保存是否成功
            
        Raises:
            StorageException: 保存失败时抛出
        """
        try:
            key = self._normalize_path(file_path)
            
            async with await self._get_async_client() as client:
                await client.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=file_data
                )
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            raise StorageException(f"S3保存文件失败 ({error_code}): {str(e)}")
        except Exception as e:
            raise StorageException(f"保存文件失败: {str(e)}")
    
    async def get_file(self, file_path: str) -> Optional[bytes]:
        """从S3获取文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[bytes]: 文件数据，文件不存在时返回None
            
        Raises:
            StorageException: 读取失败时抛出
        """
        try:
            key = self._normalize_path(file_path)
            
            async with await self._get_async_client() as client:
                response = await client.get_object(
                    Bucket=self.bucket,
                    Key=key
                )
                
                # 读取响应体
                file_data = await response['Body'].read()
                return file_data
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                return None
            raise StorageException(f"S3获取文件失败 ({error_code}): {str(e)}")
        except Exception as e:
            raise StorageException(f"读取文件失败: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """从S3删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 删除是否成功
            
        Raises:
            StorageException: 删除失败时抛出
        """
        try:
            key = self._normalize_path(file_path)
            
            async with await self._get_async_client() as client:
                await client.delete_object(
                    Bucket=self.bucket,
                    Key=key
                )
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            # S3删除不存在的文件不会报错，所以这里也不应该报错
            if error_code != 'NoSuchKey':
                raise StorageException(f"S3删除文件失败 ({error_code}): {str(e)}")
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
            key = self._normalize_path(file_path)
            
            async with await self._get_async_client() as client:
                await client.head_object(
                    Bucket=self.bucket,
                    Key=key
                )
                return True
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ('NoSuchKey', '404'):
                return False
            # 其他错误不确定是否存在
            return False
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
            key = self._normalize_path(file_path)
            
            async with await self._get_async_client() as client:
                response = await client.head_object(
                    Bucket=self.bucket,
                    Key=key
                )
                return response['ContentLength']
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ('NoSuchKey', '404'):
                return None
            raise StorageException(f"S3获取文件大小失败 ({error_code}): {str(e)}")
        except Exception as e:
            raise StorageException(f"获取文件大小失败: {str(e)}")
    
    async def get_file_stream(self, file_path: str) -> Optional[AsyncGenerator[bytes, None]]:
        """获取文件流
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[AsyncGenerator[bytes, None]]: 文件流生成器
        """
        try:
            key = self._normalize_path(file_path)
            
            client = await self._get_async_client()
            
            try:
                response = await client.get_object(
                    Bucket=self.bucket,
                    Key=key
                )
                
                async def stream():
                    try:
                        async for chunk in response['Body']:
                            yield chunk
                    finally:
                        await client.close()
                
                return stream()
                
            except ClientError as e:
                await client.close()
                error_code = e.response['Error']['Code']
                if error_code == 'NoSuchKey':
                    return None
                raise StorageException(f"S3获取文件流失败 ({error_code}): {str(e)}")
                
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
        # 对于S3，我们需要收集所有数据然后上传
        # 在生产环境中，可以考虑使用multipart upload优化大文件上传
        chunks = []
        async for chunk in file_stream:
            chunks.append(chunk)
        
        file_data = b''.join(chunks)
        return await self.save_file(file_path, file_data)
    
    def get_file_url(self, file_path: str, expires_in: int = 3600) -> Optional[str]:
        """获取文件的预签名URL
        
        Args:
            file_path: 文件路径
            expires_in: URL过期时间（秒），默认1小时
            
        Returns:
            Optional[str]: 预签名URL
        """
        try:
            key = self._normalize_path(file_path)
            
            url = self.sync_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            
            return url
            
        except Exception as e:
            raise StorageException(f"生成预签名URL失败: {str(e)}")
    
    def get_public_url(self, file_path: str) -> str:
        """获取文件的公共URL（假设bucket是公共的）
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 公共URL
        """
        key = self._normalize_path(file_path)
        
        if self.endpoint:
            # 自定义端点
            endpoint = self.endpoint.rstrip('/')
            return f"{endpoint}/{self.bucket}/{key}"
        else:
            # AWS S3
            return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
