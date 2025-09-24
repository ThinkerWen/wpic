"""
文件CRUD操作
"""
from datetime import datetime
from typing import Optional, List

from app.models import FileRecord, FileStatus


async def get_file_by_id(file_id: int) -> Optional[FileRecord]:
    """根据ID获取文件"""
    try:
        return await FileRecord.objects.select_related("user").get(id=file_id)
    except:
        return None


async def get_file_by_hash(file_hash: str, user_id: int) -> Optional[FileRecord]:
    """根据哈希值获取用户文件"""
    try:
        return await FileRecord.objects.filter(
            file_hash=file_hash,
            user=user_id,
            status=FileStatus.ACTIVE
        ).first()
    except:
        return None


async def create_file_record(user_id: int, **file_data) -> FileRecord:
    """创建文件记录"""
    return await FileRecord.objects.create(user=user_id, **file_data)


async def get_user_files(
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    status: Optional[FileStatus] = None
) -> List[FileRecord]:
    """获取用户文件列表"""
    query = FileRecord.objects.filter(user=user_id)
    
    if status:
        query = query.filter(status=status)
    else:
        query = query.filter(status=FileStatus.ACTIVE)
    
    return await query.offset(skip).limit(limit).order_by("-created_at").all()


async def get_user_files_count(user_id: int, status: Optional[FileStatus] = None) -> int:
    """获取用户文件数量"""
    query = FileRecord.objects.filter(user=user_id)
    
    if status:
        query = query.filter(status=status)
    else:
        query = query.filter(status=FileStatus.ACTIVE)
    
    return await query.count()


async def update_file_record(file_id: int, **kwargs) -> Optional[FileRecord]:
    """更新文件记录"""
    try:
        file_record = await FileRecord.objects.get(id=file_id)
        await file_record.update(**kwargs)
        return file_record
    except:
        return None


async def delete_file_record(file_id: int, user_id: int) -> bool:
    """删除文件记录（软删除）"""
    try:
        file_record = await FileRecord.objects.filter(
            id=file_id,
            user=user_id,
            status=FileStatus.ACTIVE
        ).first()
        
        if file_record:
            await file_record.update(
                status=FileStatus.DELETED,
                updated_at=datetime.utcnow()
            )
            return True
        return False
    except:
        return False


async def increment_download_count(file_id: int) -> bool:
    """增加下载计数"""
    try:
        file_record = await FileRecord.objects.get(id=file_id)
        await file_record.update(download_count=file_record.download_count + 1)
        return True
    except:
        return False


async def get_files_by_format(format_name: str, limit: int = 100) -> List[FileRecord]:
    """根据格式获取文件"""
    return await FileRecord.objects.filter(
        format=format_name,
        status=FileStatus.ACTIVE
    ).limit(limit).all()


async def get_expired_files() -> List[FileRecord]:
    """获取过期文件"""
    current_time = datetime.utcnow()
    return await FileRecord.objects.filter(
        expires_at__lt=current_time,
        status=FileStatus.ACTIVE
    ).all()
