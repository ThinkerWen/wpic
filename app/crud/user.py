"""
用户CRUD操作
"""
from typing import Optional, List
from datetime import datetime

from sqlmodel import Session, select, func
from sqlalchemy.exc import IntegrityError

from app.core.security import get_auth_manager
from app.core.database import engine
from app.models import User


def get_session():
    """获取数据库会话"""
    return Session(engine)


async def get_user_by_id(user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    try:
        with get_session() as session:
            return session.get(User, user_id)
    except Exception:
        return None


async def get_user_by_username(username: str) -> Optional[User]:
    """根据用户名获取用户"""
    try:
        with get_session() as session:
            statement = select(User).where(User.username == username)
            return session.exec(statement).first()
    except Exception:
        return None


async def get_user_by_email(email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    try:
        with get_session() as session:
            statement = select(User).where(User.email == email)
            return session.exec(statement).first()
    except Exception:
        return None


async def create_user(username: str, email: str, password: str, **kwargs) -> Optional[User]:
    """创建用户"""
    try:
        auth_manager = get_auth_manager()
        password_hash = auth_manager.get_password_hash(password)
        
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            **kwargs
        )
        
        with get_session() as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
    except IntegrityError:
        # 用户名或邮箱已存在
        return None
    except Exception:
        return None


async def authenticate_user(username: str, password: str) -> Optional[User]:
    """验证用户"""
    auth_manager = get_auth_manager()
    user = await get_user_by_username(username)
    if not user:
        return None
    if not auth_manager.verify_password(password, user.password_hash):
        return None
    return user


async def update_user(user_id: int, **kwargs) -> Optional[User]:
    """更新用户信息"""
    try:
        with get_session() as session:
            user = session.get(User, user_id)
            if not user:
                return None
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            # 更新时间
            user.updated_at = datetime.now().replace(microsecond=0)
            
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
    except Exception:
        return None


async def get_users(skip: int = 0, limit: int = 100) -> List[User]:
    """获取用户列表"""
    try:
        with get_session() as session:
            statement = select(User).offset(skip).limit(limit)
            return list(session.exec(statement).all())
    except Exception:
        return []


async def get_users_count() -> int:
    """获取用户总数"""
    try:
        with get_session() as session:
            statement = select(func.count(User.id))
            return session.exec(statement).one()
    except Exception:
        return 0


async def get_all_users() -> List[User]:
    """获取所有用户"""
    try:
        with get_session() as session:
            statement = select(User).order_by(User.created_at.desc())
            return list(session.exec(statement).all())
    except Exception:
        return []


async def get_users_paginated(skip: int = 0, limit: int = 20) -> List[User]:
    """分页获取用户列表"""
    try:
        with get_session() as session:
            statement = select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
            return list(session.exec(statement).all())
    except Exception:
        return []


async def delete_user(user_id: int) -> bool:
    """删除用户"""
    try:
        with get_session() as session:
            user = session.get(User, user_id)
            if not user:
                return False
            
            session.delete(user)
            session.commit()
            return True
    except Exception:
        return False


async def update_user_storage(user_id: int, storage_used: int) -> Optional[User]:
    """更新用户存储使用量"""
    return await update_user(user_id, storage_used=storage_used)


async def get_active_users() -> List[User]:
    """获取活跃用户"""
    try:
        with get_session() as session:
            statement = select(User).where(User.is_active == True)
            return list(session.exec(statement).all())
    except Exception:
        return []