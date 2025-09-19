"""
图片处理模块
支持多种图片格式的处理和缩略图生成
"""
import io
import hashlib
from typing import Optional, Tuple, Union, Dict, Any
from PIL import Image, ImageOps, ExifTags
from PIL.Image import Resampling
import pillow_heif
from app.core.config import get_settings
from app.core.cache import get_cache_manager

settings = get_settings()
cache_manager = get_cache_manager()

# 注册HEIF支持
pillow_heif.register_heif_opener()


class ImageProcessorException(Exception):
    """图片处理异常"""
    pass


class ImageProcessor:
    """图片处理器"""
    
    # 支持的图片格式
    SUPPORTED_FORMATS = {
        '.jpg': 'JPEG',
        '.jpeg': 'JPEG', 
        '.png': 'PNG',
        '.gif': 'GIF',
        '.webp': 'WEBP',
        '.bmp': 'BMP',
        '.tiff': 'TIFF',
        '.tif': 'TIFF',
        '.heic': 'HEIF',
        '.heif': 'HEIF'
    }
    
    def __init__(self):
        """初始化图片处理器"""
        self.thumbnail_size = settings.app.thumbnail_size
        self.preview_size = settings.app.preview_size
    
    def is_supported_format(self, file_extension: str) -> bool:
        """检查是否支持的图片格式
        
        Args:
            file_extension: 文件扩展名
            
        Returns:
            bool: 是否支持
        """
        return file_extension.lower() in self.SUPPORTED_FORMATS
    
    def get_image_format(self, file_extension: str) -> Optional[str]:
        """获取图片格式
        
        Args:
            file_extension: 文件扩展名
            
        Returns:
            Optional[str]: 图片格式，不支持时返回None
        """
        return self.SUPPORTED_FORMATS.get(file_extension.lower())
    
    async def get_image_info(self, image_data: bytes) -> Dict[str, Any]:
        """获取图片信息
        
        Args:
            image_data: 图片数据
            
        Returns:
            Dict[str, Any]: 图片信息字典
            
        Raises:
            ImageProcessorException: 处理失败时抛出
        """
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # 基本信息
                info = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size': len(image_data),
                    'has_transparency': False
                }
                
                # 检查透明度
                if img.mode in ('RGBA', 'LA') or 'transparency' in img.info:
                    info['has_transparency'] = True
                
                # EXIF信息
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif() is not None:
                    exif = img._getexif()
                    for tag_id, value in exif.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        exif_data[tag] = value
                
                info['exif'] = exif_data
                
                # 文件哈希
                info['hash'] = hashlib.md5(image_data).hexdigest()
                
                return info
                
        except Exception as e:
            raise ImageProcessorException(f"获取图片信息失败: {str(e)}")
    
    async def auto_orient_image(self, image_data: bytes) -> bytes:
        """根据EXIF信息自动旋转图片
        
        Args:
            image_data: 原图片数据
            
        Returns:
            bytes: 旋转后的图片数据
            
        Raises:
            ImageProcessorException: 处理失败时抛出
        """
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # 使用ImageOps.exif_transpose自动处理EXIF方向
                oriented_img = ImageOps.exif_transpose(img)
                
                # 保存到字节流
                output = io.BytesIO()
                
                # 保持原格式和质量
                save_format = img.format or 'JPEG'
                if save_format == 'JPEG':
                    oriented_img.save(output, format=save_format, quality=95, optimize=True)
                elif save_format == 'PNG':
                    oriented_img.save(output, format=save_format, optimize=True)
                elif save_format == 'WEBP':
                    oriented_img.save(output, format=save_format, quality=95, method=6)
                else:
                    oriented_img.save(output, format=save_format)
                
                return output.getvalue()
                
        except Exception as e:
            raise ImageProcessorException(f"自动旋转图片失败: {str(e)}")
    
    async def resize_image(self, image_data: bytes, size: Tuple[int, int], 
                          keep_aspect_ratio: bool = True, 
                          output_format: str = 'WEBP',
                          quality: int = 85) -> bytes:
        """调整图片大小
        
        Args:
            image_data: 原图片数据
            size: 目标尺寸 (width, height)
            keep_aspect_ratio: 是否保持宽高比
            output_format: 输出格式
            quality: 输出质量 (1-100)
            
        Returns:
            bytes: 调整后的图片数据
            
        Raises:
            ImageProcessorException: 处理失败时抛出
        """
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # 自动旋转
                img = ImageOps.exif_transpose(img)
                
                # 转换为RGB模式（如果输出格式不支持透明度）
                if output_format.upper() == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # 调整大小
                if keep_aspect_ratio:
                    img.thumbnail(size, Resampling.LANCZOS)
                else:
                    img = img.resize(size, Resampling.LANCZOS)
                
                # 保存到字节流
                output = io.BytesIO()
                
                if output_format.upper() == 'JPEG':
                    img.save(output, format='JPEG', quality=quality, optimize=True)
                elif output_format.upper() == 'PNG':
                    img.save(output, format='PNG', optimize=True)
                elif output_format.upper() == 'WEBP':
                    img.save(output, format='WEBP', quality=quality, method=6)
                else:
                    img.save(output, format=output_format, quality=quality)
                
                return output.getvalue()
                
        except Exception as e:
            raise ImageProcessorException(f"调整图片大小失败: {str(e)}")
    
    async def generate_thumbnail(self, image_data: bytes, 
                               size: Optional[Tuple[int, int]] = None,
                               output_format: str = 'WEBP') -> bytes:
        """生成缩略图
        
        Args:
            image_data: 原图片数据
            size: 缩略图尺寸，默认使用配置中的尺寸
            output_format: 输出格式
            
        Returns:
            bytes: 缩略图数据
            
        Raises:
            ImageProcessorException: 生成失败时抛出
        """
        if size is None:
            size = self.thumbnail_size
        
        return await self.resize_image(
            image_data, 
            size, 
            keep_aspect_ratio=True,
            output_format=output_format,
            quality=75
        )
    
    async def generate_preview(self, image_data: bytes,
                             size: Optional[Tuple[int, int]] = None,
                             output_format: str = 'WEBP') -> bytes:
        """生成预览图
        
        Args:
            image_data: 原图片数据
            size: 预览图尺寸，默认使用配置中的尺寸
            output_format: 输出格式
            
        Returns:
            bytes: 预览图数据
            
        Raises:
            ImageProcessorException: 生成失败时抛出
        """
        if size is None:
            size = self.preview_size
        
        return await self.resize_image(
            image_data,
            size,
            keep_aspect_ratio=True,
            output_format=output_format,
            quality=85
        )
    
    async def get_cached_thumbnail(self, file_path: str, 
                                 size: Optional[Tuple[int, int]] = None,
                                 output_format: str = 'WEBP') -> Optional[bytes]:
        """获取缓存的缩略图
        
        Args:
            file_path: 文件路径
            size: 缩略图尺寸
            output_format: 输出格式
            
        Returns:
            Optional[bytes]: 缓存的缩略图数据，不存在时返回None
        """
        if size is None:
            size = self.thumbnail_size
        
        cache_key = f"{file_path}:{size[0]}x{size[1]}:{output_format}"
        return await cache_manager.get_thumbnail_cache(file_path, size)
    
    async def cache_thumbnail(self, file_path: str, thumbnail_data: bytes,
                            size: Optional[Tuple[int, int]] = None,
                            ttl: int = 7200) -> bool:
        """缓存缩略图
        
        Args:
            file_path: 文件路径
            thumbnail_data: 缩略图数据
            size: 缩略图尺寸
            ttl: 缓存过期时间（秒）
            
        Returns:
            bool: 缓存是否成功
        """
        if size is None:
            size = self.thumbnail_size
        
        return await cache_manager.set_thumbnail_cache(file_path, size, thumbnail_data, ttl)
    
    async def convert_format(self, image_data: bytes, 
                           target_format: str,
                           quality: int = 90) -> bytes:
        """转换图片格式
        
        Args:
            image_data: 原图片数据
            target_format: 目标格式
            quality: 输出质量
            
        Returns:
            bytes: 转换后的图片数据
            
        Raises:
            ImageProcessorException: 转换失败时抛出
        """
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # 自动旋转
                img = ImageOps.exif_transpose(img)
                
                # 处理颜色模式
                if target_format.upper() == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                    # JPEG不支持透明度，添加白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif target_format.upper() == 'PNG' and img.mode not in ('RGBA', 'LA', 'P'):
                    # PNG支持透明度，但如果原图没有透明度则保持原样
                    pass
                
                # 保存到字节流
                output = io.BytesIO()
                
                if target_format.upper() == 'JPEG':
                    img.save(output, format='JPEG', quality=quality, optimize=True)
                elif target_format.upper() == 'PNG':
                    img.save(output, format='PNG', optimize=True)
                elif target_format.upper() == 'WEBP':
                    img.save(output, format='WEBP', quality=quality, method=6)
                else:
                    img.save(output, format=target_format, quality=quality)
                
                return output.getvalue()
                
        except Exception as e:
            raise ImageProcessorException(f"转换图片格式失败: {str(e)}")
    
    async def crop_image(self, image_data: bytes, 
                        box: Tuple[int, int, int, int],
                        output_format: str = 'WEBP') -> bytes:
        """裁剪图片
        
        Args:
            image_data: 原图片数据
            box: 裁剪区域 (left, top, right, bottom)
            output_format: 输出格式
            
        Returns:
            bytes: 裁剪后的图片数据
            
        Raises:
            ImageProcessorException: 裁剪失败时抛出
        """
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # 自动旋转
                img = ImageOps.exif_transpose(img)
                
                # 裁剪
                cropped_img = img.crop(box)
                
                # 保存到字节流
                output = io.BytesIO()
                
                if output_format.upper() == 'JPEG':
                    if cropped_img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', cropped_img.size, (255, 255, 255))
                        if cropped_img.mode == 'P':
                            cropped_img = cropped_img.convert('RGBA')
                        background.paste(cropped_img, mask=cropped_img.split()[-1] if cropped_img.mode == 'RGBA' else None)
                        cropped_img = background
                    cropped_img.save(output, format='JPEG', quality=90, optimize=True)
                elif output_format.upper() == 'PNG':
                    cropped_img.save(output, format='PNG', optimize=True)
                elif output_format.upper() == 'WEBP':
                    cropped_img.save(output, format='WEBP', quality=90, method=6)
                else:
                    cropped_img.save(output, format=output_format)
                
                return output.getvalue()
                
        except Exception as e:
            raise ImageProcessorException(f"裁剪图片失败: {str(e)}")


# 全局图片处理器实例
image_processor = ImageProcessor()


def get_image_processor() -> ImageProcessor:
    """获取图片处理器实例"""
    return image_processor
