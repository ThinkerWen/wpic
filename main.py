"""
WPIC 图床后端主应用
一个功能完整的图床后端服务，支持多种存储方式和图片处理功能
"""
import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import init_database, close_database, create_all_tables, create_default_admin
from app.core.cache import init_cache, close_cache
from app.core.logger import logger
from app.api.router import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app_main: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("🚀 启动 WPIC 图床后端服务...")
    
    # 初始化数据库连接
    await init_database()
    logger.info("✅ 数据库连接已建立")
    
    # 创建数据库表
    await create_all_tables()
    logger.info("✅ 数据库表已创建")
    
    # 初始化Redis缓存
    await init_cache()
    logger.info("✅ Redis缓存已连接")
    
    # 创建默认管理员用户
    await create_default_admin()
    
    logger.info(f"🎯 服务启动完成，访问地址: http://{settings.app.host}:{settings.app.port}")
    logger.info(f"📚 API文档地址: http://{settings.app.host}:{settings.app.port}/docs")
    
    yield
    
    # 关闭时清理
    logger.info("🛑 正在关闭服务...")
    await close_cache()
    await close_database()
    logger.info("✅ 服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app.title,
    description=settings.app.description,
    version=settings.app.version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router)

# 静态文件配置
web_dist_path = os.path.join(os.path.dirname(__file__), "web", "dist")
if os.path.exists(web_dist_path):
    # 挂载静态文件
    app.mount("/assets", StaticFiles(directory=os.path.join(web_dist_path, "assets")), name="assets")
    
    # 处理前端路由
    @app.get("/{path:path}", include_in_schema=False)
    async def serve_frontend(request: Request, path: str):
        """
        服务前端应用
        对于非 API 路径，返回 index.html 让前端路由处理
        """
        # API 路径跳过
        if path.startswith("api/") or path.startswith("docs") or path.startswith("redoc"):
            raise HTTPException(status_code=404, detail="Not Found")
        
        # 检查是否是静态资源文件
        static_file_path = os.path.join(web_dist_path, path)
        if os.path.isfile(static_file_path):
            return FileResponse(static_file_path)
        
        # 其他路径返回 index.html，让前端路由处理
        index_path = os.path.join(web_dist_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        else:
            raise HTTPException(status_code=404, detail="Frontend not built")


@app.get("/", include_in_schema=False)
async def root():
    """根路径"""
    # 如果前端已构建，直接返回前端页面
    if os.path.exists(web_dist_path):
        index_path = os.path.join(web_dist_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    
    # 否则重定向到API文档
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "WPIC Image Hosting Backend",
        "version": settings.app.version
    }


@app.get("/info", tags=["系统"])
async def get_service_info():
    """获取服务信息"""
    return {
        "name": settings.app.title,
        "version": settings.app.version,
        "description": settings.app.description,
        "auth_enabled": settings.security.enable_auth,
        "max_file_size": settings.app.max_file_size,
        "allowed_extensions": settings.app.allowed_extensions,
        "supported_storage": ["local", "webdav", "s3"]
    }


if __name__ == "__main__":
    # 运行服务器
    uvicorn.run(
        app="main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level="info" if not settings.app.debug else "debug"
    )
