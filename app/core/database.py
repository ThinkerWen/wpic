"""
数据库连接和初始化模块
"""
from typing import Dict, Any, Optional, Generator

from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine, Session

from app.core.config import get_settings
from app.core.logger import logger

# 延迟初始化，避免在导入时就获取配置
_engine: Optional[Engine] = None
_async_engine = None


def get_engine() -> Engine:
    """获取SQLAlchemy引擎实例"""
    global _engine
    if _engine is None:
        settings = get_settings()
        # 为SQLite添加额外选项
        engine_options: Dict[str, Any] = {"echo": settings.app.debug}
        if settings.database.database_url.startswith('sqlite'):
            engine_options["connect_args"] = {"check_same_thread": False}
        _engine = create_engine(settings.database.database_url, **engine_options)
    return _engine


def get_session() -> Generator[Session, None, None]:
    """获取数据库会话"""
    engine = get_engine()
    with Session(engine) as session:
        yield session


# 获取实例
engine = get_engine()


# 初始化数据库连接
async def init_database():
    """初始化数据库连接"""
    try:
        # SQLModel 不需要异步连接初始化，只需要确保引擎存在
        engine = get_engine()
        logger.info("✅ 数据库连接成功")
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")


# 关闭数据库连接
async def close_database():
    """关闭数据库连接"""
    try:
        # SQLModel 会自动管理连接
        logger.info("✅ 数据库连接已关闭")
    except Exception as e:
        logger.error(f"❌ 关闭数据库连接失败: {e}")


# 创建所有表
async def create_all_tables():
    """创建所有数据库表"""
    try:
        # 导入所有模型以确保它们被注册
        from app.models import User, FileRecord, UploadSession, AccessLog
        
        # 使用SQLModel创建所有表
        SQLModel.metadata.create_all(engine)
        logger.info("✅ 数据库表创建完成")
    except Exception as e:
        logger.error(f"❌ 创建数据库表失败: {e}")


async def create_default_admin():
    """创建默认管理员用户"""
    try:
        from app.models import User
        from app.core.security import get_auth_manager
        
        # 使用SQLModel会话
        with Session(engine) as session:
            # 检查是否已存在admin用户
            from sqlmodel import select
            statement = select(User).where(User.username == "admin")
            existing_user = session.exec(statement).first()
            
            if existing_user is None:
                auth_manager = get_auth_manager()
                password_hash = auth_manager.get_password_hash("123456")
                
                # 创建用户，SQLModel会自动应用默认值
                admin_user = User(
                    username="admin",
                    email="admin@localhost",
                    password_hash=password_hash,
                    storage_quota=10 * 1024 * 1024 * 1024
                )
                
                session.add(admin_user)
                session.commit()
                logger.info("✅ 默认管理员用户 'admin' 创建成功，密码: 123456")
            else:
                logger.debug("⚠️ 管理员用户 'admin' 已存在，跳过创建")
                
    except Exception as e:
        logger.error(f"❌ 创建默认管理员用户失败: {e}")
