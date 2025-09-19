#!/usr/bin/env python3
"""
项目设置检查脚本
验证WPIC图床后端项目的完整性和配置
"""
import sys
import os
from pathlib import Path
import importlib.util

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python版本需要3.8+，当前版本:", f"{version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def check_required_files():
    """检查必需文件"""
    required_files = [
        "main.py",
        "requirements.txt",
        "app/__init__.py",
        "app/core/config.py",
        "app/models.py", 
        "app/core/database.py",
        "app/core/security.py",
        "app/core/cache.py",
        "app/services/image_service.py",
        "app/services/storage_service.py",
        "app/api/auth_routes.py",
        "app/api/file_routes.py",
        "app/api/admin_routes.py",
        "app/api/schemas.py",
        "app/storage/base.py",
        "app/storage/local.py",
        "app/storage/webdav.py",
        "app/storage/s3.py",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 缺少必需文件:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ 所有必需文件都存在")
    return True

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "databases",
        "redis",
        "PIL",  # Pillow
        "jose",  # python-jose
        "passlib",
        "aiofiles",
        "aiohttp",
        "boto3",
        "pillow_heif"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == "PIL":
                import PIL
            elif package == "jose":
                from jose import jwt
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print("\n缺少依赖包，请运行:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def check_config():
    """检查配置文件"""
    if not Path("config.example.env").exists():
        print("❌ 缺少配置示例文件: config.example.env")
        return False
    
    if not Path(".env").exists():
        print("⚠️  未找到配置文件 .env，将从示例文件创建")
        try:
            import shutil
            shutil.copy("config.example.env", ".env")
            print("✅ 已创建配置文件 .env")
        except Exception as e:
            print(f"❌ 创建配置文件失败: {e}")
            return False
    else:
        print("✅ 配置文件 .env 存在")
    
    return True

def check_directories():
    """检查并创建必要目录"""
    directories = ["uploads", "logs"]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ 已创建目录: {directory}")
            except Exception as e:
                print(f"❌ 创建目录失败 {directory}: {e}")
                return False
        else:
            print(f"✅ 目录存在: {directory}")
    
    return True

def check_import_structure():
    """检查模块导入结构"""
    try:
        # 测试核心模块导入
        sys.path.insert(0, str(Path.cwd()))
        
        from app.core.config import get_settings
        from app.models import User, FileRecord
        from app.core.security import get_auth_manager
        from app.core.cache import get_cache_manager
        from app.services.storage_service import get_storage_manager
        from app.services.image_service import get_image_processor
        
        print("✅ 所有核心模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def main():
    """主检查函数"""
    print("🔍 WPIC 图床后端项目设置检查")
    print("=" * 50)
    
    checks = [
        ("Python版本", check_python_version),
        ("必需文件", check_required_files),
        ("依赖包", check_dependencies),
        ("配置文件", check_config),
        ("目录结构", check_directories),
        ("模块导入", check_import_structure),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n📋 检查{check_name}:")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有检查通过！项目设置完成")
        print("\n下一步:")
        print("1. 启动服务: python main.py")
        print("2. 访问API文档: http://localhost:8000/docs")
        print("🎉 main.py 已修复并可正常运行！")
    else:
        print("❌ 部分检查未通过，请根据提示修复问题")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
