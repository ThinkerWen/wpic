"""
用户CRUD操作
"""
from typing import Optional, List
from datetime import datetime

from app.core.security import get_auth_manager
from app.core.database import database
from app.models import User, users_table


async def get_user_by_id(user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    try:
        query = users_table.select().where(users_table.c.id == user_id)
        result = await database.fetch_one(query)
        if result:
            return User(**dict(result))
        return None
    except Exception:
        return None


async def get_user_by_username(username: str) -> Optional[User]:
    """根据用户名获取用户"""
    try:
        query = users_table.select().where(users_table.c.username == username)
        result = await database.fetch_one(query)
        if result:
            return User(**dict(result))
        return None
    except Exception:
        return None


async def get_user_by_email(email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    try:
        query = users_table.select().where(users_table.c.email == email)
        result = await database.fetch_one(query)
        if result:
            return User(**dict(result))
        return None
    except Exception:
        return None


async def create_user(username: str, email: str, password: str, **kwargs) -> Optional[User]:
    """创建用户"""
    try:
        auth_manager = get_auth_manager()
        password_hash = auth_manager.get_password_hash(password)
        
        query = users_table.insert().values(
            username=username,
            email=email,
            password_hash=password_hash,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **kwargs
        )
        
        result = await database.execute(query)
        if result:
            # 获取创建的用户
            return await get_user_by_id(result)
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
        # 添加更新时间
        kwargs['updated_at'] = datetime.utcnow()
        
        query = users_table.update().where(
            users_table.c.id == user_id
        ).values(**kwargs)
        
        result = await database.execute(query)
        if result:
            return await get_user_by_id(user_id)
        return None
    except Exception:
        return None


async def get_users(skip: int = 0, limit: int = 100) -> List[User]:
    """获取用户列表"""
    try:
        query = users_table.select().offset(skip).limit(limit)
        results = await database.fetch_all(query)
        return [User(**dict(result)) for result in results]
    except Exception:
        return []


async def get_users_count() -> int:
    """获取用户总数"""
    try:
        from sqlalchemy import func
        query = users_table.select().with_only_columns([func.count(users_table.c.id)])
        result = await database.fetch_one(query)
        return result[0] if result else 0
    except Exception:
        return 0


async def get_all_users() -> List[User]:
    """获取所有用户"""
    try:
        query = users_table.select().order_by(users_table.c.created_at.desc())
        results = await database.fetch_all(query)
        return [User(**dict(result)) for result in results]
    except Exception:
        return []


async def get_users_paginated(skip: int = 0, limit: int = 20) -> List[User]:
    """分页获取用户列表"""
    try:
        query = users_table.select().offset(skip).limit(limit).order_by(users_table.c.created_at.desc())
        results = await database.fetch_all(query)
        return [User(**dict(result)) for result in results]
    except Exception:
        return []
