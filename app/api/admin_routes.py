"""
管理员API路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.schemas import (
    UserResponse, UserUpdate, StatsResponse, 
    UserStatsResponse, SuccessResponse, ConfigResponse,
    StorageConfigRequest
)
from app.models import User, FileRecord, FileStatus
from app.core.security import get_current_active_user
from app.core.config import get_settings
from app.crud import user as user_crud, file as file_crud

router = APIRouter(prefix="/admin", tags=["管理"])
settings = get_settings()


async def get_admin_user(current_user: User = Depends(get_current_active_user)):
    """验证管理员权限"""
    # 这里简化实现，实际应该在User模型中添加is_admin字段
    # 暂时以user_id=1作为管理员
    if current_user.id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


@router.get("/users", response_model=List[UserResponse], summary="获取用户列表")
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    admin_user: User = Depends(get_admin_user)
):
    """获取用户列表"""
    try:
        offset = (page - 1) * page_size
        users = await User.objects.offset(offset).limit(page_size).order_by("-created_at").all()
        
        user_responses = []
        for user in users:
            user_responses.append(UserResponse(
                **user.dict(),
                remaining_storage=user.remaining_storage,
                storage_usage_percent=user.storage_usage_percent
            ))
        
        return user_responses
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserResponse, summary="获取用户详情")
async def get_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user)
):
    """获取用户详情"""
    try:
        user = await User.objects.get(id=user_id)
        
        return UserResponse(
            **user.dict(),
            remaining_storage=user.remaining_storage,
            storage_usage_percent=user.storage_usage_percent
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )


@router.put("/users/{user_id}", response_model=UserResponse, summary="更新用户信息")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    admin_user: User = Depends(get_admin_user)
):
    """更新用户信息"""
    try:
        user = await User.objects.get(id=user_id)
        
        update_data = user_update.dict(exclude_unset=True)
        if update_data:
            await user.update(**update_data)
        
        return UserResponse(
            **user.dict(),
            remaining_storage=user.remaining_storage,
            storage_usage_percent=user.storage_usage_percent
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )


@router.delete("/users/{user_id}", response_model=SuccessResponse, summary="删除用户")
async def delete_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user)
):
    """删除用户（软删除）"""
    try:
        if user_id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己的账户"
            )
        
        user = await User.objects.get(id=user_id)
        await user.update(is_active=False)
        
        return SuccessResponse(message="用户删除成功")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )


@router.get("/stats", response_model=StatsResponse, summary="获取系统统计")
async def get_system_stats(admin_user: User = Depends(get_admin_user)):
    """获取系统统计信息"""
    try:
        # 总文件数
        total_files = await FileRecord.objects.filter(status=FileStatus.ACTIVE).count()
        
        # 总存储使用量
        users = await User.objects.all()
        total_storage_used = sum(user.storage_used for user in users)
        
        # 总下载次数
        files = await FileRecord.objects.filter(status=FileStatus.ACTIVE).all()
        total_downloads = sum(file.download_count for file in files)
        
        # 按格式统计文件
        files_by_format = {}
        for file in files:
            format_name = file.format or "unknown"
            files_by_format[format_name] = files_by_format.get(format_name, 0) + 1
        
        # 按存储类型统计
        storage_by_type = {}
        for user in users:
            storage_type = user.storage_type.value
            storage_by_type[storage_type] = storage_by_type.get(storage_type, 0) + user.storage_used
        
        return StatsResponse(
            total_files=total_files,
            total_storage_used=total_storage_used,
            total_downloads=total_downloads,
            files_by_format=files_by_format,
            storage_by_type=storage_by_type
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.get("/config", response_model=ConfigResponse, summary="获取系统配置")
async def get_system_config(admin_user: User = Depends(get_admin_user)):
    """获取系统配置"""
    try:
        return ConfigResponse(
            max_file_size=settings.app.max_file_size,
            allowed_extensions=settings.app.allowed_extensions,
            storage_types=["local", "webdav", "s3"],
            auth_enabled=settings.security.enable_auth,
            thumbnail_size=settings.app.thumbnail_size,
            preview_size=settings.app.preview_size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置失败: {str(e)}"
        )


@router.post("/users/{user_id}/storage", response_model=SuccessResponse, summary="更新用户存储配置")
async def update_user_storage(
    user_id: int,
    storage_config: StorageConfigRequest,
    admin_user: User = Depends(get_admin_user)
):
    """更新用户存储配置"""
    try:
        user = await User.objects.get(id=user_id)
        
        await user.update(
            storage_type=storage_config.storage_type,
            storage_config=storage_config.config
        )
        
        return SuccessResponse(message="存储配置更新成功")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )


@router.get("/users/{user_id}/stats", response_model=UserStatsResponse, summary="获取用户统计")
async def get_user_stats(
    user_id: int,
    admin_user: User = Depends(get_admin_user)
):
    """获取用户统计信息"""
    try:
        user = await User.objects.get(id=user_id)
        
        # 文件数量
        file_count = await FileRecord.objects.filter(
            user=user.id,
            status=FileStatus.ACTIVE
        ).count()
        
        # 总下载次数
        files = await FileRecord.objects.filter(
            user=user.id,
            status=FileStatus.ACTIVE
        ).all()
        total_downloads = sum(file.download_count for file in files)
        
        # 最近7天上传数
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_uploads = await FileRecord.objects.filter(
            user=user.id,
            status=FileStatus.ACTIVE,
            created_at__gte=week_ago
        ).count()
        
        return UserStatsResponse(
            file_count=file_count,
            storage_used=user.storage_used,
            storage_quota=user.storage_quota,
            storage_usage_percent=user.storage_usage_percent,
            total_downloads=total_downloads,
            recent_uploads=recent_uploads
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
