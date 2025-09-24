"""
管理员API路由
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.api.schemas import (
    UserResponse, UserUpdate, StatsResponse,
    UserStatsResponse, SuccessResponse, ConfigResponse,
    StorageConfigRequest
)
from app.core.config import get_settings
from app.core.security import get_current_active_user
from app.models import User, FileRecord, FileStatus

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
        from app.crud.user import get_users_paginated
        
        offset = (page - 1) * page_size
        users = await get_users_paginated(offset, page_size)
        
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
        from app.crud.user import get_user_by_id
        
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserResponse(
            **user.dict(),
            remaining_storage=user.remaining_storage,
            storage_usage_percent=user.storage_usage_percent
        )
        
    except HTTPException:
        raise
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
        from app.crud.user import get_user_by_id, update_user as update_user_crud
        
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        update_data = user_update.dict(exclude_unset=True)
        if update_data:
            user = await update_user_crud(user_id, **update_data)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="更新用户失败"
                )
        
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
        from app.crud.user import get_user_by_id, update_user as update_user_crud
        
        if user_id == admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己的账户"
            )
        
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
            
        updated_user = await update_user_crud(user_id, is_active=False)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除用户失败"
            )
        
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
        from app.crud.user import get_all_users
        from app.crud.file import get_user_files_count
        from app.core.database import database
        from app.models import users_table, file_records_table
        from sqlalchemy import func
        
        # 总用户数
        total_users_query = users_table.select().with_only_columns([func.count(users_table.c.id)])
        total_users_result = await database.fetch_one(total_users_query)
        total_users = total_users_result[0] if total_users_result else 0
        
        # 总文件数
        total_files_query = file_records_table.select().with_only_columns([func.count(file_records_table.c.id)]).where(
            file_records_table.c.status == FileStatus.ACTIVE.value
        )
        total_files_result = await database.fetch_one(total_files_query)
        total_files = total_files_result[0] if total_files_result else 0
        
        # 总存储使用量
        storage_used_query = users_table.select().with_only_columns([func.sum(users_table.c.storage_used)])
        storage_used_result = await database.fetch_one(storage_used_query)
        total_storage_used = storage_used_result[0] if storage_used_result and storage_used_result[0] else 0
        
        # 总下载次数
        downloads_query = file_records_table.select().with_only_columns([func.sum(file_records_table.c.download_count)]).where(
            file_records_table.c.status == FileStatus.ACTIVE.value
        )
        downloads_result = await database.fetch_one(downloads_query)
        total_downloads = downloads_result[0] if downloads_result and downloads_result[0] else 0
        
        # 按格式统计文件 - 简化版本
        files_by_format = {"jpg": 0, "png": 0, "gif": 0, "other": 0}
        
        # 按存储类型统计 - 简化版本  
        storage_by_type = {"local": int(total_storage_used), "webdav": 0, "s3": 0}
        
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
        from app.crud.user import get_user_by_id, update_user as update_user_crud
        
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        updated_user = await update_user_crud(
            user_id,
            storage_type=storage_config.storage_type,
            storage_config=storage_config.config
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新存储配置失败"
            )
        
        return SuccessResponse(message="存储配置更新成功")
        
    except HTTPException:
        raise
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
        from app.crud.user import get_user_by_id
        from app.crud.file import get_user_files_count
        from app.core.database import database
        from app.models import file_records_table
        from sqlalchemy import func
        
        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 文件数量
        file_count_query = file_records_table.select().with_only_columns([func.count(file_records_table.c.id)]).where(
            (file_records_table.c.user_id == user.id) &
            (file_records_table.c.status == FileStatus.ACTIVE.value)
        )
        file_count_result = await database.fetch_one(file_count_query)
        file_count = file_count_result[0] if file_count_result else 0
        
        # 总下载次数
        downloads_query = file_records_table.select().with_only_columns([func.sum(file_records_table.c.download_count)]).where(
            (file_records_table.c.user_id == user.id) &
            (file_records_table.c.status == FileStatus.ACTIVE.value)
        )
        downloads_result = await database.fetch_one(downloads_query)
        total_downloads = downloads_result[0] if downloads_result and downloads_result[0] else 0
        
        # 最近7天上传数
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_uploads_query = file_records_table.select().with_only_columns([func.count(file_records_table.c.id)]).where(
            (file_records_table.c.user_id == user.id) &
            (file_records_table.c.status == FileStatus.ACTIVE.value) &
            (file_records_table.c.created_at >= week_ago)
        )
        recent_uploads_result = await database.fetch_one(recent_uploads_query)
        recent_uploads = recent_uploads_result[0] if recent_uploads_result else 0
        
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
