# WPIC 图床后端

一个功能完整的图床后端服务，使用 Python FastAPI 框架开发，支持多种存储方式和图片处理功能。

## 主要特性

### 🗄️ 存储支持
- **本地存储**: 存储文件到本地文件系统
- **WebDAV**: 支持 WebDAV 协议的存储服务
- **S3 兼容**: 支持 AWS S3 和兼容 S3 的对象存储

### 🖼️ 图片处理
- 支持多种图片格式：JPG, PNG, GIF, WebP, HEIC 等
- 自动生成缩略图和预览图
- 图片自动旋转（基于 EXIF）
- 图片格式转换和压缩

### 🔐 安全认证
- JWT Token 认证
- API 密钥支持
- 文件访问权限控制
- 分享链接过期机制
- 可选的无认证模式

### 📊 缓存系统
- Redis 缓存文件数据
- 缩略图缓存
- 元数据缓存
- 下载计数缓存

### 👥 用户管理
- 多用户支持
- 存储配额管理
- 用户独立存储配置
- 管理员后台接口

### 📁 文件管理
- 文件上传、下载、删除
- 文件列表分页查询
- 文件信息统计
- 重复文件检测

## 快速开始

### 1. 环境要求

- Python 3.8+
- Redis (可选，用于缓存)
- PostgreSQL 或 MySQL (可选，默认使用 SQLite)

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境

复制配置文件并修改：

```bash
cp config.example.env .env
```

编辑 `.env` 文件，配置数据库、Redis 等连接信息。

### 4. 运行服务

```bash
# 直接运行
python main.py

# 或使用生产环境方式
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

服务启动后，访问 http://localhost:8000/docs 查看 API 文档。

## 配置说明

### 数据库配置

支持多种数据库：

```env
# SQLite (默认)
DB_DATABASE_URL="sqlite:///./wpic.db"

# PostgreSQL
DB_DATABASE_URL="postgresql://username:password@localhost:5432/wpic"

# MySQL
DB_DATABASE_URL="mysql://username:password@localhost:3306/wpic"
```

### 存储配置

用户可以选择不同的存储后端：

#### 本地存储
```env
STORAGE_LOCAL_BASE_PATH="./uploads"
```

#### S3 存储
```env
STORAGE_S3_ACCESS_KEY="your-access-key"
STORAGE_S3_SECRET_KEY="your-secret-key"
STORAGE_S3_BUCKET="your-bucket"
STORAGE_S3_REGION="us-east-1"
STORAGE_S3_ENDPOINT=""  # 可选，用于兼容S3的服务
```

#### WebDAV 存储
```env
STORAGE_WEBDAV_URL="https://your-webdav-server.com"
STORAGE_WEBDAV_USERNAME="username"
STORAGE_WEBDAV_PASSWORD="password"
```

### 安全配置

```env
SECURITY_SECRET_KEY="your-secret-key-32-chars-long"
SECURITY_ENABLE_AUTH=true  # 设为 false 可禁用认证
```

## API 接口

### 认证接口

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/generate-api-key` - 生成 API 密钥

### 文件管理接口

- `POST /api/files/upload` - 上传文件
- `GET /api/files/` - 获取文件列表
- `GET /api/files/{file_id}` - 获取文件信息
- `GET /api/files/{file_id}/download` - 下载文件
- `GET /api/files/{file_id}/thumbnail` - 获取缩略图
- `GET /api/files/{file_id}/preview` - 获取预览图
- `POST /api/files/{file_id}/share` - 创建分享链接
- `DELETE /api/files/{file_id}` - 删除文件

### 管理员接口

- `GET /api/admin/users` - 获取用户列表
- `GET /api/admin/stats` - 获取系统统计
- `GET /api/admin/config` - 获取系统配置

## 使用示例

### 用户注册

```bash
curl -X POST "http://localhost:8000/api/auth/register" \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "storage_type": "local"
  }'
```

### 用户登录

```bash
curl -X POST "http://localhost:8000/api/auth/login" \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "username=testuser&password=password123"
```

### 上传文件

```bash
curl -X POST "http://localhost:8000/api/files/upload" \\
  -H "Authorization: Bearer your-token" \\
  -F "file=@image.jpg"
```

### 获取文件列表

```bash
curl -X GET "http://localhost:8000/api/files/" \\
  -H "Authorization: Bearer your-token"
```

## 项目结构

```
wpic/
├── app/                    # 应用核心代码
│   ├── api/               # API 路由
│   │   ├── auth_routes.py # 认证相关路由
│   │   ├── file_routes.py # 文件管理路由
│   │   ├── admin_routes.py# 管理员路由
│   │   └── schemas.py     # API 模式定义
│   ├── storage/           # 存储后端
│   │   ├── base.py        # 存储基类
│   │   ├── local.py       # 本地存储
│   │   ├── webdav.py      # WebDAV 存储
│   │   └── s3.py          # S3 存储
│   ├── auth.py            # 认证模块
│   ├── cache.py           # 缓存模块
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   ├── image_processor.py # 图片处理
│   └── models.py          # 数据模型
├── main.py                # 应用入口
├── requirements.txt       # 依赖列表
├── config.example.env     # 配置示例
└── README.md             # 说明文档
```

## 部署建议

### Docker 部署

可以创建 Dockerfile 进行容器化部署：

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

### 生产环境配置

1. 使用 PostgreSQL 或 MySQL 作为数据库
2. 配置 Redis 用于缓存
3. 设置强密码和密钥
4. 启用 HTTPS
5. 配置反向代理（如 Nginx）
6. 设置文件上传大小限制
7. 定期备份数据库和文件

### 性能优化

1. 使用 Redis 缓存热点文件
2. 配置 CDN 加速静态资源
3. 启用 Gzip 压缩
4. 使用对象存储（S3）提高并发性能
5. 数据库索引优化
6. 异步处理大文件上传

## 开发

### 运行开发服务器

```bash
python main.py
```

### 代码风格

项目使用 Python 标准代码风格，建议使用 black 和 isort 格式化代码。

### 测试

可以使用项目中的 test_main.http 文件进行 API 测试。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.0
- 初始版本发布
- 支持多种存储后端
- 完整的用户认证系统
- 图片处理和缓存功能
- RESTful API 接口
