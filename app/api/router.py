"""
API路由汇总
将所有API路由集中管理
"""
from fastapi import APIRouter

from app.api.auth_routes import router as auth_router
from app.api.file_routes import router as file_router
from app.api.admin_routes import router as admin_router

# 创建主API路由器
api_router = APIRouter(prefix="/api")

# 包含所有子路由
api_router.include_router(auth_router)
api_router.include_router(file_router)
api_router.include_router(admin_router)
