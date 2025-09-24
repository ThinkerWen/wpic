"""
文件CRUD操作
"""
from datetime import datetime
from typing import Optional, List

from app.core.database import database
from app.models import FileRecord, FileStatus, file_records_table


async def get_file_by_id(file_id: int) -> Optional[FileRecord]:
    """根据ID获取文件"""
    try:
        query = file_records_table.select().where(file_records_table.c.id == file_id)
        result = await database.fetch_one(query)
        if result:
            return FileRecord(**dict(result))
        return None
    except:
        return None


async def get_file_by_hash(file_hash: str, user_id: int) -> Optional[FileRecord]:
    """根据哈希值获取用户文件"""
    try:
        query = file_records_table.select().where(
            (file_records_table.c.file_hash == file_hash) &
            (file_records_table.c.user_id == user_id) &
            (file_records_table.c.status == FileStatus.ACTIVE.value)
        )
        result = await database.fetch_one(query)
        if result:
            return FileRecord(**dict(result))
        return None
    except:
        return None


async def create_file_record(user_id: int, **file_data) -> FileRecord:
    """创建文件记录"""
    try:
        file_data['user_id'] = user_id
        file_data['created_at'] = datetime.utcnow()
        file_data['updated_at'] = datetime.utcnow()
        
        query = file_records_table.insert().values(**file_data)
        result = await database.execute(query)
        
        if result:
            return await get_file_by_id(result)
        return None
    except:
        return None


async def get_user_files(
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    status: Optional[FileStatus] = None
) -> List[FileRecord]:
    """获取用户文件列表"""
    try:
        query = file_records_table.select().where(file_records_table.c.user_id == user_id)
        
        if status:
            query = query.where(file_records_table.c.status == status.value)
        else:
            query = query.where(file_records_table.c.status == FileStatus.ACTIVE.value)
        
        query = query.order_by(file_records_table.c.created_at.desc()).offset(skip).limit(limit)
        results = await database.fetch_all(query)
        
        return [FileRecord(**dict(result)) for result in results]
    except:
        return []


async def get_user_files_count(user_id: int, status: Optional[FileStatus] = None) -> int:
    """获取用户文件数量"""
    try:
        from sqlalchemy import func
        query = file_records_table.select([func.count()]).where(file_records_table.c.user_id == user_id)
        
        if status:
            query = query.where(file_records_table.c.status == status.value)
        else:
            query = query.where(file_records_table.c.status == FileStatus.ACTIVE.value)
        
        result = await database.fetch_one(query)
        return result[0] if result else 0
    except:
        return 0


async def update_file_record(file_id: int, **kwargs) -> Optional[FileRecord]:
    """更新文件记录"""
    try:
        kwargs['updated_at'] = datetime.utcnow()
        
        query = file_records_table.update().where(
            file_records_table.c.id == file_id
        ).values(**kwargs)
        
        result = await database.execute(query)
        if result:
            return await get_file_by_id(file_id)
        return None
    except:
        return None


async def delete_file_record(file_id: int, user_id: int) -> bool:
    """删除文件记录（软删除）"""
    try:
        # 先检查文件是否存在且属于该用户
        query = file_records_table.select().where(
            (file_records_table.c.id == file_id) &
            (file_records_table.c.user_id == user_id) &
            (file_records_table.c.status == FileStatus.ACTIVE.value)
        )
        result = await database.fetch_one(query)
        
        if result:
            # 执行软删除
            update_query = file_records_table.update().where(
                file_records_table.c.id == file_id
            ).values(
                status=FileStatus.DELETED.value,
                updated_at=datetime.utcnow()
            )
            await database.execute(update_query)
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
