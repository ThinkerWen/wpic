"""
日志配置模块
使用loguru进行日志管理
"""
import sys
from pathlib import Path
from loguru import logger as log

def setup_logger():
    """配置loguru日志"""
    # 移除默认处理器
    log.remove()

    # 控制台输出格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<level>{message}</level>"
    )
    
    # 文件输出格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    # 添加控制台处理器
    log.add(
        sys.stdout,
        format=console_format,
        level="INFO",
        colorize=True,
        enqueue=True
    )
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 添加文件处理器 - 普通日志
    log.add(
        log_dir / "wpic.log",
        format=file_format,
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        encoding="utf-8"
    )
    
    # 添加文件处理器 - 错误日志
    log.add(
        log_dir / "error.log",
        format=file_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        encoding="utf-8"
    )

setup_logger()
logger = log
