#!/bin/bash

# WPIC 图床后端启动脚本

echo "🚀 WPIC 图床后端启动脚本"
echo "=========================="

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 检查是否存在虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  配置文件不存在，复制示例配置文件..."
    cp config.example.env .env
    echo "✅ 已创建 .env 配置文件，请编辑后重新运行"
    exit 1
fi

# 创建上传目录
if [ ! -d "uploads" ]; then
    echo "创建上传目录..."
    mkdir -p uploads
fi

echo "🎯 启动应用..."
python main.py
