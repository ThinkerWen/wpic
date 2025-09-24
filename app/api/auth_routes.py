"""
认证相关API路由
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.schemas import (
    UserCreate, UserResponse, Token,
    SuccessResponse
)
from app.core.cache import get_cache_manager
from app.core.security import get_auth_manager, get_current_user, get_current_active_user
from app.models import User

router = APIRouter(prefix="/auth", tags=["认证"])
auth_manager = get_auth_manager()
cache_manager = get_cache_manager()


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(user_data: UserCreate):
    """用户注册"""
    try:
        from app.crud.user import get_user_by_username, get_user_by_email, create_user
        
        # 检查用户名是否已存在
        existing_user = await get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        existing_email = await get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
        
        # 创建用户
        user = await create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            storage_type=user_data.storage_type,
            storage_config=user_data.storage_config,
            storage_quota=user_data.storage_quota
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建用户失败"
            )
        
        # 转换为响应模型
        return UserResponse(
            **user.dict(),
            remaining_storage=user.remaining_storage,
            storage_usage_percent=user.storage_usage_percent
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login", response_model=Token, summary="用户登录")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录"""
    try:
        # 认证用户
        user = await auth_manager.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 创建访问令牌
        access_token_expires = timedelta(minutes=auth_manager.access_token_expire_minutes)
        access_token = auth_manager.create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=access_token_expires
        )
        
        # 缓存用户会话
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        }
        await cache_manager.set_user_session(access_token, user_data)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_manager.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.post("/logout", response_model=SuccessResponse, summary="用户登出")
async def logout(current_user: User = Depends(get_current_active_user)):
    """用户登出"""
    try:
        # 这里可以添加令牌黑名单逻辑
        # 暂时只返回成功响应
        return SuccessResponse(message="登出成功")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登出失败: {str(e)}"
        )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    try:
        return UserResponse(
            **current_user.dict(),
            remaining_storage=current_user.remaining_storage,
            storage_usage_percent=current_user.storage_usage_percent
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )


@router.post("/refresh", response_model=Token, summary="刷新访问令牌")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """刷新访问令牌"""
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=auth_manager.access_token_expire_minutes)
        access_token = auth_manager.create_access_token(
            data={"sub": str(current_user.id), "username": current_user.username},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_manager.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新令牌失败: {str(e)}"
        )


@router.post("/generate-api-key", response_model=dict, summary="生成API密钥")
async def generate_api_key(current_user: User = Depends(get_current_active_user)):
    """生成API密钥"""
    try:
        api_key = auth_manager.generate_api_key(current_user.id)
        
        # 缓存API密钥
        user_data = {
            "user_id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        }
        await cache_manager.set_user_session(
            api_key, 
            user_data, 
            ttl=86400 * 30  # 30天
        )
        
        return {
            "api_key": api_key,
            "message": "API密钥生成成功，请妥善保管",
            "expires_in_days": 30
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成API密钥失败: {str(e)}"
        )
