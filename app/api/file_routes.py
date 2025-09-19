"""
文件管理API路由
"""
import os
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import (
    APIRouter, Depends, HTTPException, status, 
    UploadFile, File, Form, Query, Response
)
from fastapi.responses import StreamingResponse
from app.api.schemas import (
    FileUploadResponse, FileResponse, FileListResponse,
    FileShareRequest, FileShareResponse, SuccessResponse,
    ImageProcessRequest, ThumbnailRequest
)
from app.models import User, FileRecord, FileStatus, AccessLog
from app.core.security import get_current_user, get_current_active_user, verify_file_access, get_auth_manager
from app.services.storage_service import get_storage_manager
from app.services.image_service import get_image_processor, ImageProcessorException
from app.core.cache import get_cache_manager
from app.core.config import get_settings
from app.crud import file as file_crud

router = APIRouter(prefix="/files", tags=["文件管理"])
auth_manager = get_auth_manager()
image_processor = get_image_processor()
cache_manager = get_cache_manager()
storage_manager = get_storage_manager()
settings = get_settings()


@router.post("/upload", response_model=FileUploadResponse, summary="上传文件")
async def upload_file(
    file: UploadFile = File(..., description="要上传的文件"),
    auto_rename: bool = Form(default=True, description="是否自动重命名"),
    current_user: User = Depends(get_current_active_user)
):
    """上传文件"""
    try:
        # 检查文件大小
        if file.size and file.size > settings.app.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制 ({settings.app.max_file_size} 字节)"
            )
        
        # 检查文件扩展名
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.app.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file_ext}"
            )
        
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 检查存储配额
        if not await auth_manager.check_storage_quota(current_user, file_size):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="存储空间不足"
            )
        
        # 计算文件哈希
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # 检查是否已存在相同文件
        existing_file = await FileRecord.objects.filter(
            user=current_user.id,
            file_hash=file_hash,
            status=FileStatus.ACTIVE
        ).first()
        
        if existing_file and not auto_rename:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="文件已存在"
            )
        
        # 生成文件名
        if auto_rename or existing_file:
            filename = auth_manager.generate_secure_filename(file.filename, current_user.id)
        else:
            filename = file.filename
        
        # 获取存储后端
        storage = storage_manager.get_storage_for_user(current_user)
        
        # 构建文件路径
        file_path = f"{datetime.utcnow().strftime('%Y/%m/%d')}/{filename}"
        
        # 保存文件
        success = await storage.save_file(file_path, file_content)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="文件保存失败"
            )
        
        # 获取图片信息（如果是图片）
        width, height, format_name = None, None, None
        if image_processor.is_supported_format(file_ext):
            try:
                image_info = await image_processor.get_image_info(file_content)
                width = image_info.get("width")
                height = image_info.get("height")
                format_name = image_info.get("format")
            except ImageProcessorException:
                pass  # 忽略图片处理错误
        
        # 创建文件记录
        file_record = await FileRecord.objects.create(
            user=current_user.id,
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            content_type=file.content_type or "application/octet-stream",
            file_hash=file_hash,
            width=width,
            height=height,
            format=format_name,
            status=FileStatus.ACTIVE
        )
        
        # 更新用户存储使用量
        await auth_manager.update_storage_usage(current_user, file_size)
        
        # 生成响应URLs
        base_url = f"/files/{file_record.id}"
        download_url = f"{base_url}/download"
        thumbnail_url = f"{base_url}/thumbnail" if file_record.is_image else None
        preview_url = f"{base_url}/preview" if file_record.is_image else None
        
        return FileUploadResponse(
            id=file_record.id,
            filename=file_record.filename,
            original_filename=file_record.original_filename,
            file_size=file_record.file_size,
            content_type=file_record.content_type,
            file_hash=file_record.file_hash,
            width=file_record.width,
            height=file_record.height,
            format=file_record.format,
            download_url=download_url,
            thumbnail_url=thumbnail_url,
            preview_url=preview_url,
            created_at=file_record.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败: {str(e)}"
        )


@router.get("/", response_model=FileListResponse, summary="获取文件列表")
async def get_file_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    status_filter: Optional[FileStatus] = Query(None, description="状态过滤"),
    format_filter: Optional[str] = Query(None, description="格式过滤"),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户文件列表"""
    try:
        # 构建查询
        query = FileRecord.objects.filter(user=current_user.id)
        
        if status_filter:
            query = query.filter(status=status_filter)
        else:
            query = query.filter(status=FileStatus.ACTIVE)
        
        if format_filter:
            query = query.filter(format=format_filter)
        
        # 计算总数
        total = await query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        files = await query.offset(offset).limit(page_size).order_by("-created_at").all()
        
        # 转换为响应格式
        file_responses = []
        for file_record in files:
            base_url = f"/files/{file_record.id}"
            download_url = f"{base_url}/download"
            thumbnail_url = f"{base_url}/thumbnail" if file_record.is_image else None
            preview_url = f"{base_url}/preview" if file_record.is_image else None
            
            file_responses.append(FileResponse(
                **file_record.dict(),
                download_url=download_url,
                thumbnail_url=thumbnail_url,
                preview_url=preview_url
            ))
        
        total_pages = (total + page_size - 1) // page_size
        
        return FileListResponse(
            files=file_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件列表失败: {str(e)}"
        )


@router.get("/{file_id}", response_model=FileResponse, summary="获取文件信息")
async def get_file_info(
    file_record: FileRecord = Depends(verify_file_access)
):
    """获取文件信息"""
    try:
        base_url = f"/files/{file_record.id}"
        download_url = f"{base_url}/download"
        thumbnail_url = f"{base_url}/thumbnail" if file_record.is_image else None
        preview_url = f"{base_url}/preview" if file_record.is_image else None
        
        return FileResponse(
            **file_record.dict(),
            download_url=download_url,
            thumbnail_url=thumbnail_url,
            preview_url=preview_url
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件信息失败: {str(e)}"
        )


@router.get("/{file_id}/download", summary="下载文件")
async def download_file(
    file_record: FileRecord = Depends(verify_file_access),
    download: bool = Query(False, description="是否作为下载")
):
    """下载或查看文件"""
    try:
        # 获取存储后端
        storage = storage_manager.get_storage_for_user(file_record.user)
        
        # 尝试从缓存获取
        cached_data = await cache_manager.get_file_cache(file_record.file_path)
        
        if cached_data:
            file_data = cached_data
        else:
            # 从存储获取文件
            file_data = await storage.get_file(file_record.file_path)
            if file_data is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文件不存在"
                )
            
            # 缓存文件（小于1MB的文件）
            if len(file_data) < 1024 * 1024:
                await cache_manager.set_file_cache(file_record.file_path, file_data)
        
        # 更新下载计数
        await file_record.update(download_count=file_record.download_count + 1)
        await cache_manager.increment_download_count(file_record.file_path)
        
        # 记录访问日志
        # 这里简化处理，实际应该记录IP等信息
        
        # 设置响应头
        headers = {
            "Content-Type": file_record.content_type,
            "Content-Length": str(len(file_data))
        }
        
        if download:
            headers["Content-Disposition"] = f"attachment; filename={file_record.original_filename}"
        else:
            headers["Content-Disposition"] = f"inline; filename={file_record.original_filename}"
        
        return Response(content=file_data, headers=headers)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载文件失败: {str(e)}"
        )


@router.get("/{file_id}/thumbnail", summary="获取缩略图")
async def get_thumbnail(
    file_id: int,
    width: int = Query(200, ge=50, le=800, description="缩略图宽度"),
    height: int = Query(200, ge=50, le=800, description="缩略图高度"),
    format: str = Query("webp", description="输出格式"),
    current_user: Optional[User] = Depends(get_current_user)
):
    """获取文件缩略图"""
    try:
        # 验证文件访问权限
        file_record = await verify_file_access(file_id, current_user)
        
        if not file_record.is_image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="此文件不是图片"
            )
        
        # 尝试从缓存获取缩略图
        cached_thumbnail = await cache_manager.get_thumbnail_cache(
            file_record.file_path, 
            (width, height)
        )
        
        if cached_thumbnail:
            return Response(
                content=cached_thumbnail,
                media_type=f"image/{format}",
                headers={"Cache-Control": "public, max-age=86400"}
            )
        
        # 获取原文件
        storage = storage_manager.get_storage_for_user(file_record.user)
        file_data = await storage.get_file(file_record.file_path)
        
        if file_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="原文件不存在"
            )
        
        # 生成缩略图
        thumbnail_data = await image_processor.resize_image(
            file_data,
            (width, height),
            keep_aspect_ratio=True,
            output_format=format,
            quality=75
        )
        
        # 缓存缩略图
        await cache_manager.set_thumbnail_cache(
            file_record.file_path,
            (width, height),
            thumbnail_data
        )
        
        return Response(
            content=thumbnail_data,
            media_type=f"image/{format}",
            headers={"Cache-Control": "public, max-age=86400"}
        )
        
    except HTTPException:
        raise
    except ImageProcessorException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成缩略图失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取缩略图失败: {str(e)}"
        )


@router.get("/{file_id}/preview", summary="获取预览图")
async def get_preview(
    file_id: int,
    width: int = Query(800, ge=200, le=1920, description="预览图宽度"),
    height: int = Query(600, ge=150, le=1080, description="预览图高度"),
    format: str = Query("webp", description="输出格式"),
    current_user: Optional[User] = Depends(get_current_user)
):
    """获取文件预览图"""
    try:
        # 验证文件访问权限
        file_record = await verify_file_access(file_id, current_user)
        
        if not file_record.is_image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="此文件不是图片"
            )
        
        # 尝试从缓存获取预览图
        cache_key = f"preview:{file_record.file_path}:{width}x{height}:{format}"
        cached_preview = await cache_manager.get_thumbnail_cache(
            f"preview_{file_record.file_path}",
            (width, height)
        )
        
        if cached_preview:
            return Response(
                content=cached_preview,
                media_type=f"image/{format}",
                headers={"Cache-Control": "public, max-age=3600"}
            )
        
        # 获取原文件
        storage = storage_manager.get_storage_for_user(file_record.user)
        file_data = await storage.get_file(file_record.file_path)
        
        if file_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="原文件不存在"
            )
        
        # 生成预览图
        preview_data = await image_processor.resize_image(
            file_data,
            (width, height),
            keep_aspect_ratio=True,
            output_format=format,
            quality=85
        )
        
        # 缓存预览图
        await cache_manager.set_thumbnail_cache(
            f"preview_{file_record.file_path}",
            (width, height),
            preview_data
        )
        
        return Response(
            content=preview_data,
            media_type=f"image/{format}",
            headers={"Cache-Control": "public, max-age=3600"}
        )
        
    except HTTPException:
        raise
    except ImageProcessorException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成预览图失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取预览图失败: {str(e)}"
        )


@router.post("/{file_id}/share", response_model=FileShareResponse, summary="分享文件")
async def share_file(
    file_id: int,
    share_request: FileShareRequest,
    current_user: User = Depends(get_current_active_user)
):
    """创建文件分享链接"""
    try:
        # 验证文件所有权
        file_record = await FileRecord.objects.filter(
            id=file_id,
            user=current_user.id,
            status=FileStatus.ACTIVE
        ).first()
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在或无权限"
            )
        
        # 生成分享令牌
        access_token = auth_manager.generate_file_share_link(
            file_id,
            current_user.id,
            share_request.expires_in_hours
        )
        
        # 更新文件记录
        expires_at = datetime.utcnow() + timedelta(hours=share_request.expires_in_hours)
        await file_record.update(
            access_token=access_token,
            expires_at=expires_at
        )
        
        # 生成分享URL
        share_url = f"/files/{file_id}/download?token={access_token}"
        
        return FileShareResponse(
            share_url=share_url,
            access_token=access_token,
            expires_at=expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建分享链接失败: {str(e)}"
        )


@router.delete("/{file_id}", response_model=SuccessResponse, summary="删除文件")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """删除文件"""
    try:
        # 验证文件所有权
        file_record = await FileRecord.objects.filter(
            id=file_id,
            user=current_user.id,
            status=FileStatus.ACTIVE
        ).first()
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在或无权限"
            )
        
        # 获取存储后端并删除文件
        storage = storage_manager.get_storage_for_user(current_user)
        await storage.delete_file(file_record.file_path)
        
        # 更新文件状态
        await file_record.update(
            status=FileStatus.DELETED,
            updated_at=datetime.utcnow()
        )
        
        # 更新用户存储使用量
        await auth_manager.update_storage_usage(current_user, -file_record.file_size)
        
        # 清除相关缓存
        await cache_manager.delete_file_cache(file_record.file_path)
        
        return SuccessResponse(message="文件删除成功")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文件失败: {str(e)}"
        )
