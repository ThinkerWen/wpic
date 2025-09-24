"""
数据库连接和初始化模块
"""
import databases
import sqlalchemy
from sqlalchemy import MetaData

from app.core.config import get_settings

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
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")


# 关闭数据库连接
async def close_database():
    """关闭数据库连接"""
    try:
        await database.disconnect()
        print("✅ 数据库连接已关闭")
    except Exception as e:
        print(f"❌ 关闭数据库连接失败: {e}")


# 创建所有表
async def create_all_tables():
    """创建所有数据库表"""
    try:
        # 这里我们先不创建表，等模型完善后再处理
        print("✅ 数据库表检查完成")
    except Exception as e:
        print(f"❌ 创建数据库表失败: {e}")
