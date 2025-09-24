"""
依赖注入模块
FastAPI依赖项定义
"""
from typing import Optional, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.cache import get_cache_manager
from app.core.config import get_settings
from app.core.security import get_auth_manager
from app.models import User, FileRecord
from app.services.image_service import get_image_processor
from app.services.storage_service import get_storage_manager

settings = get_settings()
security = HTTPBearer(auto_error=False)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """获取当前用户（可选）"""
    if not settings.security.enable_auth:
        return None
    
    if not credentials:
        return None
    
    auth_manager = get_auth_manager()
    token = credentials.credentials
    
    # 检查是否为API密钥
    if token.startswith("wpic_"):
        import asyncio
        return asyncio.run(auth_manager.verify_api_key(token))
    
    # 验证JWT令牌
    payload = auth_manager.verify_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    try:
        import asyncio
        from app.crud.user import get_user_by_id
        return asyncio.run(get_user_by_id(int(user_id)))
    except:
        return None


def get_current_user_required(
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """获取当前用户（必需）"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录访问",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def get_admin_user(
    current_user: User = Depends(get_current_user_required)
) -> User:
    """获取管理员用户"""
    # 简化实现：用户ID为1的为管理员
    if current_user.id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def verify_file_access_dep(
    file_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    token: Optional[str] = None
) -> FileRecord:
    """验证文件访问权限依赖"""
    try:
        from app.crud.file import get_file_by_id
        file_record = await get_file_by_id(file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    auth_manager = get_auth_manager()
    has_permission = await auth_manager.check_file_permission(file_record, current_user, token)
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此文件"
        )
    
    return file_record


# 服务依赖
def get_cache() -> Generator:
    """获取缓存管理器"""
    return get_cache_manager()


def get_storage() -> Generator:
    """获取存储管理器"""
    return get_storage_manager()


def get_image_service() -> Generator:
    """获取图片处理服务"""
    return get_image_processor()
