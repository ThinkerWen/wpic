"""
用户认证和权限控制模块
支持JWT token认证和文件访问权限控制
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.cache import get_cache_manager
from app.core.config import get_settings
from app.models import User, FileRecord

settings = get_settings()
cache_manager = get_cache_manager()

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer token方案
security = HTTPBearer(auto_error=False)


class AuthException(Exception):
    """认证异常"""
    pass


class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        """初始化认证管理器"""
        self.secret_key = settings.security.secret_key
        self.algorithm = settings.security.algorithm
        self.access_token_expire_minutes = settings.security.access_token_expire_minutes
        self.enable_auth = settings.security.enable_auth
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            bool: 密码是否正确
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """生成密码哈希
        
        Args:
            password: 明文密码
            
        Returns:
            str: 哈希密码
        """
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], 
                          expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌
        
        Args:
            data: 令牌数据
            expires_delta: 过期时间增量
            
        Returns:
            str: JWT令牌
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict[str, Any]]: 令牌数据，无效时返回None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """认证用户
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            Optional[User]: 用户对象，认证失败时返回None
        """
        try:
            user = await User.objects.get(username=username, is_active=True)
            if not self.verify_password(password, user.password_hash):
                return None
            return user
        except:
            return None
    
    def create_file_access_token(self, file_id: int, user_id: int, 
                               expires_delta: Optional[timedelta] = None) -> str:
        """创建文件访问令牌
        
        Args:
            file_id: 文件ID
            user_id: 用户ID
            expires_delta: 过期时间增量
            
        Returns:
            str: 文件访问令牌
        """
        data = {
            "file_id": file_id,
            "user_id": user_id,
            "type": "file_access"
        }
        return self.create_access_token(data, expires_delta)
    
    def verify_file_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证文件访问令牌
        
        Args:
            token: 文件访问令牌
            
        Returns:
            Optional[Dict[str, Any]]: 令牌数据，无效时返回None
        """
        payload = self.verify_token(token)
        if payload and payload.get("type") == "file_access":
            return payload
        return None
    
    def generate_file_share_link(self, file_id: int, user_id: int,
                               expires_in_hours: int = 24) -> str:
        """生成文件分享链接令牌
        
        Args:
            file_id: 文件ID
            user_id: 用户ID
            expires_in_hours: 过期时间（小时）
            
        Returns:
            str: 分享链接令牌
        """
        expires_delta = timedelta(hours=expires_in_hours)
        data = {
            "file_id": file_id,
            "user_id": user_id,
            "type": "share_link",
            "share_time": datetime.utcnow().isoformat()
        }
        return self.create_access_token(data, expires_delta)
    
    def generate_secure_filename(self, original_filename: str, user_id: int) -> str:
        """生成安全的文件名
        
        Args:
            original_filename: 原始文件名
            user_id: 用户ID
            
        Returns:
            str: 安全的文件名
        """
        # 使用时间戳和随机数生成唯一文件名
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        random_suffix = secrets.token_hex(8)
        
        # 获取文件扩展名
        file_ext = ""
        if "." in original_filename:
            file_ext = original_filename.rsplit(".", 1)[1].lower()
        
        # 生成新文件名
        new_filename = f"{timestamp}_{user_id}_{random_suffix}"
        if file_ext:
            new_filename += f".{file_ext}"
        
        return new_filename
    
    async def check_file_permission(self, file_record: FileRecord, 
                                   user: Optional[User] = None,
                                   token: Optional[str] = None) -> bool:
        """检查文件访问权限
        
        Args:
            file_record: 文件记录
            user: 当前用户
            token: 访问令牌
            
        Returns:
            bool: 是否有权限访问
        """
        # 如果未启用认证，允许访问
        if not self.enable_auth:
            return True
        
        # 如果文件已删除，拒绝访问
        if file_record.status == "deleted":
            return False
        
        # 如果文件已过期，拒绝访问
        if file_record.is_expired:
            return False
        
        # 如果是文件所有者，允许访问
        if user and user.id == file_record.user.id:
            return True
        
        # 验证文件访问令牌
        if token:
            payload = self.verify_file_access_token(token)
            if payload:
                token_file_id = payload.get("file_id")
                if token_file_id == file_record.id:
                    return True
        
        # 验证分享链接令牌
        if file_record.access_token and token == file_record.access_token:
            share_payload = self.verify_token(token)
            if share_payload and share_payload.get("type") == "share_link":
                return True
        
        return False
    
    async def check_storage_quota(self, user: User, file_size: int) -> bool:
        """检查存储配额
        
        Args:
            user: 用户对象
            file_size: 文件大小（字节）
            
        Returns:
            bool: 是否有足够的存储空间
        """
        return user.storage_used + file_size <= user.storage_quota
    
    async def update_storage_usage(self, user: User, size_delta: int):
        """更新存储使用量
        
        Args:
            user: 用户对象
            size_delta: 大小变化（字节，可为负数）
        """
        new_usage = max(0, user.storage_used + size_delta)
        await user.update(storage_used=new_usage, updated_at=datetime.utcnow())
    
    def generate_api_key(self, user_id: int) -> str:
        """生成API密钥
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: API密钥
        """
        # 生成32字节的随机密钥
        random_key = secrets.token_hex(32)
        
        # 包含用户ID信息
        key_data = f"{user_id}:{random_key}:{datetime.utcnow().isoformat()}"
        
        # 使用SHA256哈希
        hash_obj = hashlib.sha256(key_data.encode())
        api_key = hash_obj.hexdigest()
        
        return f"wpic_{api_key}"
    
    async def verify_api_key(self, api_key: str) -> Optional[User]:
        """验证API密钥
        
        Args:
            api_key: API密钥
            
        Returns:
            Optional[User]: 用户对象，无效时返回None
        """
        # 这里简化实现，实际应该在数据库中存储API密钥
        # 暂时通过缓存来模拟
        try:
            # 从缓存中获取API密钥对应的用户ID
            cached_user_data = await cache_manager.get_user_session(api_key)
            if cached_user_data:
                user_id = cached_user_data.get("user_id")
                if user_id:
                    user = await User.objects.get(id=user_id, is_active=True)
                    return user
            return None
        except:
            return None


# 全局认证管理器实例
auth_manager = AuthManager()


def get_auth_manager() -> AuthManager:
    """获取认证管理器实例"""
    return auth_manager


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """获取当前用户
    
    Args:
        credentials: HTTP认证凭据
        
    Returns:
        Optional[User]: 当前用户，未认证时返回None
        
    Raises:
        HTTPException: 认证失败时抛出
    """
    if not settings.security.enable_auth:
        return None
    
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # 检查是否为API密钥
    if token.startswith("wpic_"):
        user = await auth_manager.verify_api_key(token)
        if user:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API密钥",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证JWT令牌
    payload = auth_manager.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌格式错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user = await User.objects.get(id=int(user_id), is_active=True)
        return user
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户（必须登录）
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 当前活跃用户
        
    Raises:
        HTTPException: 未登录时抛出
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录访问",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def verify_file_access(file_id: int, 
                           current_user: Optional[User] = Depends(get_current_user),
                           token: Optional[str] = None) -> FileRecord:
    """验证文件访问权限
    
    Args:
        file_id: 文件ID
        current_user: 当前用户
        token: 访问令牌
        
    Returns:
        FileRecord: 文件记录
        
    Raises:
        HTTPException: 无权限或文件不存在时抛出
    """
    try:
        file_record = await FileRecord.objects.select_related("user").get(id=file_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    has_permission = await auth_manager.check_file_permission(file_record, current_user, token)
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此文件"
        )
    
    return file_record
