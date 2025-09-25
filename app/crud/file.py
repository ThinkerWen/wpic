"""
文件CRUD操作 - SQLModel版本
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select, func

from app.core.database import engine
from app.models import FileRecord, FileStatus


def get_session():
    """获取数据库会话"""
    return Session(engine)


async def get_file_by_id(file_id: int) -> Optional[FileRecord]:
    """根据ID获取文件"""
    try:
        with get_session() as session:
            return session.get(FileRecord, file_id)
    except Exception:
        return None


async def get_file_by_hash(file_hash: str, user_id: int) -> Optional[FileRecord]:
    """根据哈希值获取用户文件"""
    try:
        with get_session() as session:
            statement = select(FileRecord).where(
                FileRecord.file_hash == file_hash,
                FileRecord.user_id == user_id,
                FileRecord.status == FileStatus.ACTIVE.value
            )
            return session.exec(statement).first()
    except Exception:
        return None


async def create_file_record(user_id: int, **file_data) -> Optional[FileRecord]:
    """创建文件记录"""
    try:
        file_record = FileRecord(
            user_id=user_id,
            **file_data
        )
        
        with get_session() as session:
            session.add(file_record)
            session.commit()
            session.refresh(file_record)
            return file_record
    except IntegrityError:
        return None
    except Exception:
        return None


async def get_user_files(
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    status: Optional[FileStatus] = None
) -> List[FileRecord]:
    """获取用户文件列表"""
    try:
        with get_session() as session:
            statement = select(FileRecord).where(FileRecord.user_id == user_id)
            
            if status:
                statement = statement.where(FileRecord.status == status.value)
            else:
                statement = statement.where(FileRecord.status == FileStatus.ACTIVE.value)
            
            statement = statement.order_by(FileRecord.created_at.desc()).offset(skip).limit(limit)
            return list(session.exec(statement).all())
    except Exception:
        return []


async def get_user_files_count(user_id: int, status: Optional[FileStatus] = None) -> int:
    """获取用户文件数量"""
    try:
        with get_session() as session:
            statement = select(func.count(FileRecord.id)).where(FileRecord.user_id == user_id)
            
            if status:
                statement = statement.where(FileRecord.status == status.value)
            else:
                statement = statement.where(FileRecord.status == FileStatus.ACTIVE.value)
            
            return session.exec(statement).one()
    except Exception:
        return 0


async def update_file_record(file_id: int, **kwargs) -> Optional[FileRecord]:
    """更新文件记录"""
    try:
        with get_session() as session:
            file_record = session.get(FileRecord, file_id)
            if not file_record:
                return None
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(file_record, key):
                    setattr(file_record, key, value)
            
            # 更新时间
            file_record.updated_at = datetime.now().replace(microsecond=0)
            
            session.add(file_record)
            session.commit()
            session.refresh(file_record)
            return file_record
    except Exception:
        return None


async def delete_file_record(file_id: int, user_id: int) -> bool:
    """删除文件记录（软删除）"""
    try:
        with get_session() as session:
            statement = select(FileRecord).where(
                FileRecord.id == file_id,
                FileRecord.user_id == user_id,
                FileRecord.status == FileStatus.ACTIVE.value
            )
            file_record = session.exec(statement).first()
            
            if file_record:
                file_record.status = FileStatus.DELETED.value
                file_record.updated_at = datetime.now().replace(microsecond=0)
                session.add(file_record)
                session.commit()
                return True
            return False
    except Exception:
        return False


async def increment_download_count(file_id: int) -> bool:
    """增加下载计数"""
    try:
        with get_session() as session:
            file_record = session.get(FileRecord, file_id)
            if not file_record:
                return False
            
            file_record.download_count += 1
            file_record.updated_at = datetime.now().replace(microsecond=0)
            session.add(file_record)
            session.commit()
            return True
    except Exception:
        return False


async def get_files_by_format(format_name: str, limit: int = 100) -> List[FileRecord]:
    """根据格式获取文件"""
    try:
        with get_session() as session:
            statement = select(FileRecord).where(
                FileRecord.format == format_name,
                FileRecord.status == FileStatus.ACTIVE.value
            ).limit(limit)
            return list(session.exec(statement).all())
    except Exception:
        return []


async def get_expired_files() -> List[FileRecord]:
    """获取过期文件"""
    try:
        current_time = datetime.now()
        with get_session() as session:
            statement = select(FileRecord).where(
                FileRecord.expires_at < current_time,
                FileRecord.status == FileStatus.ACTIVE.value
            )
            return list(session.exec(statement).all())
    except Exception:
        return []


async def get_file_by_access_token(access_token: str) -> Optional[FileRecord]:
    """根据访问令牌获取文件"""
    try:
        with get_session() as session:
            statement = select(FileRecord).where(
                FileRecord.access_token == access_token,
                FileRecord.status == FileStatus.ACTIVE.value
            )
            return session.exec(statement).first()
    except Exception:
        return None


async def get_files_by_user_with_pagination(
    user_id: int,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[FileRecord], int]:
    """分页获取用户文件和总数"""
    try:
        with get_session() as session:
            # 获取总数
            count_statement = select(func.count(FileRecord.id)).where(
                FileRecord.user_id == user_id,
                FileRecord.status == FileStatus.ACTIVE.value
            )
            total = session.exec(count_statement).one()
            
            # 获取分页数据
            skip = (page - 1) * page_size
            statement = select(FileRecord).where(
                FileRecord.user_id == user_id,
                FileRecord.status == FileStatus.ACTIVE.value
            ).order_by(FileRecord.created_at.desc()).offset(skip).limit(page_size)
            
            files = list(session.exec(statement).all())
            return files, total
    except Exception:
        return [], 0


async def hard_delete_file_record(file_id: int) -> bool:
    """物理删除文件记录"""
    try:
        with get_session() as session:
            file_record = session.get(FileRecord, file_id)
            if not file_record:
                return False
            
            session.delete(file_record)
            session.commit()
            return True
    except Exception:
        return False