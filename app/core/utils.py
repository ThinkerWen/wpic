"""
实用工具函数模块
"""
import os
import mimetypes
import hashlib
import secrets
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime, timedelta


def get_file_extension(filename: str) -> str:
    """获取文件扩展名
    
    Args:
        filename: 文件名
        
    Returns:
        str: 文件扩展名（包含点号）
    """
    return Path(filename).suffix.lower()


def get_content_type(filename: str) -> str:
    """根据文件名获取MIME类型
    
    Args:
        filename: 文件名
        
    Returns:
        str: MIME类型
    """
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or "application/octet-stream"


def generate_random_filename(original_filename: str, length: int = 16) -> str:
    """生成随机文件名
    
    Args:
        original_filename: 原始文件名
        length: 随机字符串长度
        
    Returns:
        str: 随机文件名
    """
    ext = get_file_extension(original_filename)
    random_name = secrets.token_hex(length // 2)
    return f"{random_name}{ext}"


def calculate_file_hash(file_data: bytes, algorithm: str = "md5") -> str:
    """计算文件哈希值
    
    Args:
        file_data: 文件数据
        algorithm: 哈希算法
        
    Returns:
        str: 哈希值
    """
    if algorithm == "md5":
        return hashlib.md5(file_data).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(file_data).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(file_data).hexdigest()
    else:
        raise ValueError(f"不支持的哈希算法: {algorithm}")


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化的大小字符串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def validate_filename(filename: str) -> bool:
    """验证文件名是否合法
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否合法
    """
    if not filename:
        return False
    
    # 检查非法字符
    illegal_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    for char in illegal_chars:
        if char in filename:
            return False
    
    # 检查文件名长度
    if len(filename) > 255:
        return False
    
    # 检查保留名称（Windows）
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    name_without_ext = Path(filename).stem.upper()
    if name_without_ext in reserved_names:
        return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    # 替换非法字符
    illegal_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    
    # 移除首尾空格和点号
    filename = filename.strip(' .')
    
    # 限制长度
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        max_name_length = 255 - len(ext)
        filename = name[:max_name_length] + ext
    
    return filename


def get_date_path(date: Optional[datetime] = None) -> str:
    """根据日期生成路径
    
    Args:
        date: 日期，默认为当前日期
        
    Returns:
        str: 日期路径，格式为 YYYY/MM/DD
    """
    if date is None:
        date = datetime.utcnow()
    
    return date.strftime("%Y/%m/%d")


def parse_range_header(range_header: str, file_size: int) -> Optional[Tuple[int, int]]:
    """解析HTTP Range头
    
    Args:
        range_header: Range头的值
        file_size: 文件大小
        
    Returns:
        Optional[Tuple[int, int]]: (start, end) 或 None
    """
    if not range_header.startswith('bytes='):
        return None
    
    range_spec = range_header[6:]  # 移除 'bytes='
    
    if '-' not in range_spec:
        return None
    
    parts = range_spec.split('-', 1)
    start_str, end_str = parts
    
    try:
        if start_str and end_str:
            # bytes=200-1000
            start = int(start_str)
            end = int(end_str)
        elif start_str:
            # bytes=200-
            start = int(start_str)
            end = file_size - 1
        elif end_str:
            # bytes=-500
            start = file_size - int(end_str)
            end = file_size - 1
        else:
            return None
        
        # 验证范围
        if start < 0 or end >= file_size or start > end:
            return None
        
        return start, end
    except ValueError:
        return None


def is_image_file(filename: str) -> bool:
    """判断是否为图片文件
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否为图片
    """
    image_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.webp', 
        '.bmp', '.tiff', '.tif', '.heic', '.heif'
    }
    return get_file_extension(filename) in image_extensions


def generate_thumbnail_path(original_path: str, size: Tuple[int, int], format: str = "webp") -> str:
    """生成缩略图路径
    
    Args:
        original_path: 原始文件路径
        size: 缩略图尺寸
        format: 输出格式
        
    Returns:
        str: 缩略图路径
    """
    path_obj = Path(original_path)
    parent = path_obj.parent
    stem = path_obj.stem
    
    thumbnail_name = f"{stem}_thumb_{size[0]}x{size[1]}.{format}"
    return str(parent / "thumbnails" / thumbnail_name)


def create_pagination_info(total: int, page: int, page_size: int) -> dict:
    """创建分页信息
    
    Args:
        total: 总记录数
        page: 当前页码
        page_size: 每页大小
        
    Returns:
        dict: 分页信息
    """
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_page": page - 1 if page > 1 else None,
        "next_page": page + 1 if page < total_pages else None
    }


def validate_image_dimensions(width: int, height: int, max_width: int = 10000, max_height: int = 10000) -> bool:
    """验证图片尺寸是否合理
    
    Args:
        width: 图片宽度
        height: 图片高度
        max_width: 最大宽度
        max_height: 最大高度
        
    Returns:
        bool: 尺寸是否合理
    """
    if width <= 0 or height <= 0:
        return False
    
    if width > max_width or height > max_height:
        return False
    
    # 检查像素总数（防止内存攻击）
    total_pixels = width * height
    max_pixels = 100 * 1024 * 1024  # 100M像素
    if total_pixels > max_pixels:
        return False
    
    return True


def get_client_ip(request) -> str:
    """获取客户端真实IP地址
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        str: IP地址
    """
    # 检查代理头
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 取第一个IP（原始客户端IP）
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # 返回直连IP
    return str(request.client.host) if request.client else "unknown"


def clean_expired_files(files: List, current_time: Optional[datetime] = None) -> List:
    """清理过期文件列表
    
    Args:
        files: 文件列表
        current_time: 当前时间
        
    Returns:
        List: 未过期的文件列表
    """
    if current_time is None:
        current_time = datetime.utcnow()
    
    return [
        f for f in files 
        if not hasattr(f, 'expires_at') or 
           f.expires_at is None or 
           f.expires_at > current_time
    ]
