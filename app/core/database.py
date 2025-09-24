"""
数据库连接和初始化模块
"""
import databases
import sqlalchemy
from sqlalchemy import MetaData

from app.core.config import get_settings
from app.core.logger import logger

settings = get_settings()

# 创建数据库连接
database = databases.Database(settings.database.database_url)

# 创建元数据
metadata = MetaData()

# 创建SQLAlchemy引擎
engine = sqlalchemy.create_engine(settings.database.database_url)


# 初始化数据库连接
async def init_database():
    """初始化数据库连接"""
    try:
        await database.connect()
        logger.info("✅ 数据库连接成功")
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")


# 关闭数据库连接
async def close_database():
    """关闭数据库连接"""
    try:
        await database.disconnect()
        logger.info("✅ 数据库连接已关闭")
    except Exception as e:
        logger.error(f"❌ 关闭数据库连接失败: {e}")


# 创建所有表
async def create_all_tables():
    """创建所有数据库表"""
    try:
        # 导入所有模型
        from app.models import metadata
        
        # 创建所有表
        metadata.create_all(engine)
        logger.info("✅ 数据库表创建完成")
    except Exception as e:
        logger.error(f"❌ 创建数据库表失败: {e}")


async def create_default_admin():
    """创建默认管理员用户"""
    try:
        from app.models import users_table, User
        from app.core.security import get_auth_manager
        
        # 检查是否已存在admin用户
        query = users_table.select().where(users_table.c.username == "admin")
        result = await database.fetch_one(query)
        
        if result is None:
            # 创建默认admin用户
            auth_manager = get_auth_manager()
            password_hash = auth_manager.get_password_hash("123456")
            
            query = users_table.insert().values(
                username="admin",
                email="admin@localhost",
                password_hash=password_hash,
                storage_quota=10 * 1024 * 1024 * 1024,  # 10GB
                is_active=True
            )
            
            await database.execute(query)
            logger.info("✅ 默认管理员用户 'admin' 创建成功，密码: 123456")
        else:
            logger.debug("⚠️ 管理员用户 'admin' 已存在，跳过创建")
            
    except Exception as e:
        logger.error(f"❌ 创建默认管理员用户失败: {e}")
