# WPIC 图床系统前端

基于 Vue3 + Vite + Pinia + Tailwind CSS 的现代化图床前端应用。

## 功能特性

- ✨ **现代化界面**：使用 Tailwind CSS 构建的美观响应式界面
- 🚀 **快速开发**：Vite 提供极速的开发体验
- 📱 **响应式设计**：完美适配桌面端和移动端
- 🔐 **用户认证**：完整的登录/注销功能，支持权限控制
- 📤 **图片上传**：支持拖拽上传、批量上传、进度显示
- 🖼️ **图片管理**：图片列表、搜索、预览、删除等功能
- 👥 **用户管理**：管理员可管理用户账号和存储配置
- 🔄 **状态管理**：使用 Pinia 进行全局状态管理
- 📡 **API 集成**：完整的后端 API 调用封装

## 技术栈

- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP 客户端**: Axios
- **UI 框架**: Tailwind CSS
- **图标**: Heroicons

## 项目结构

```
web/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API 接口封装
│   │   └── index.js       # 认证、文件、管理员 API
│   ├── components/        # 公共组件
│   │   └── AppLayout.vue  # 应用布局组件
│   ├── router/            # 路由配置
│   │   └── index.js       # 路由定义和守卫
│   ├── store/             # Pinia 状态管理
│   │   ├── auth.js        # 认证状态
│   │   ├── file.js        # 文件状态
│   │   ├── admin.js       # 管理员状态
│   │   └── index.js       # 状态导出
│   ├── utils/             # 工具函数
│   │   ├── request.js     # Axios 封装
│   │   └── helpers.js     # 通用工具函数
│   ├── views/             # 页面组件
│   │   ├── Login.vue      # 登录页
│   │   ├── Dashboard.vue  # 仪表板
│   │   ├── Upload.vue     # 上传页
│   │   ├── Gallery.vue    # 图库页
│   │   ├── Settings.vue   # 设置页
│   │   └── NotFound.vue   # 404 页
│   ├── App.vue            # 根组件
│   ├── main.js            # 应用入口
│   └── style.css          # 全局样式
├── .env.development       # 开发环境配置
├── .env.production        # 生产环境配置
├── index.html             # HTML 模板
├── package.json           # 依赖配置
├── postcss.config.js      # PostCSS 配置
├── tailwind.config.js     # Tailwind 配置
└── vite.config.js         # Vite 配置
```

## 开发指南

### 环境要求

- Node.js >= 16.0.0
- npm >= 7.0.0

### 安装依赖

```bash
cd web
npm install
```

### 开发模式

```bash
npm run dev
```

开发服务器将在 http://localhost:3000 启动，并自动代理 API 请求到后端服务器。

### 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

### 代码格式化

```bash
npm run format
```

### 代码检查

```bash
npm run lint
```

## 环境配置

### 开发环境 (.env.development)

```bash
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_TITLE=WPIC 图床系统
VITE_APP_DESCRIPTION=一个现代化的图床管理系统
```

### 生产环境 (.env.production)

```bash
VITE_API_BASE_URL=/api
VITE_APP_TITLE=WPIC 图床系统
VITE_APP_DESCRIPTION=一个现代化的图床管理系统
```

## 与 FastAPI 集成

### 开发模式

在开发模式下，前端和后端分别运行：

1. 后端：`python main.py` (运行在 8000 端口)
2. 前端：`npm run dev` (运行在 3000 端口)

Vite 开发服务器会自动代理 `/api` 请求到后端。

### 生产模式

在生产模式下，FastAPI 托管前端静态文件：

1. 构建前端：`npm run build`
2. 启动后端：`python main.py`
3. 访问：http://localhost:8000

FastAPI 会自动服务前端静态文件，并处理前端路由。

### FastAPI 静态文件配置

已在 `main.py` 中添加了静态文件支持：

```python
# 静态文件配置
web_dist_path = os.path.join(os.path.dirname(__file__), "web", "dist")
if os.path.exists(web_dist_path):
    # 挂载静态文件
    app.mount("/assets", StaticFiles(directory=os.path.join(web_dist_path, "assets")), name="assets")
    
    # 处理前端路由
    @app.get("/{path:path}", include_in_schema=False)
    async def serve_frontend(request: Request, path: str):
        # 非 API 路径返回 index.html，让前端路由处理
        if not path.startswith("api/"):
            return FileResponse(os.path.join(web_dist_path, "index.html"))
```

## 主要功能

### 1. 用户认证

- 登录/注销
- Token 自动管理
- 权限路由守卫
- 自动刷新 Token

### 2. 图片上传

- 拖拽上传支持
- 批量文件上传
- 实时上传进度
- 文件格式验证
- 自动重命名选项

### 3. 图片管理

- 分页图片列表
- 搜索和排序
- 批量操作
- 图片预览
- 复制链接
- 删除功能

### 4. 用户管理 (管理员)

- 用户增删改查
- 角色权限管理
- 存储配置设置
- 系统统计信息

## 自定义开发

### 添加新页面

1. 在 `src/views/` 创建 Vue 组件
2. 在 `src/router/index.js` 添加路由
3. 在 `src/components/AppLayout.vue` 添加导航链接

### 添加新 API

1. 在 `src/api/index.js` 添加 API 方法
2. 在对应的 store 中调用 API
3. 在组件中使用 store 方法

### 自定义样式

- 修改 `tailwind.config.js` 自定义主题
- 在 `src/style.css` 添加全局样式
- 使用 Tailwind 的 `@apply` 指令创建组件样式

## 部署说明

### Docker 部署

如果后端项目有 Docker 配置，前端会自动包含在容器中：

```bash
# 构建前端
cd web && npm run build && cd ..

# 构建 Docker 镜像
docker build -t wpic .

# 运行容器
docker run -p 8000:8000 wpic
```

### 传统部署

1. 构建前端：`npm run build`
2. 将后端代码和 `web/dist/` 部署到服务器
3. 安装 Python 依赖并启动服务

## 故障排除

### 常见问题

1. **API 请求失败**
   - 检查后端服务是否启动
   - 确认 API 地址配置正确
   - 查看浏览器控制台错误信息

2. **页面空白**
   - 检查是否正确构建了前端
   - 确认静态文件路径配置正确
   - 查看浏览器控制台是否有 JavaScript 错误

3. **路由不工作**
   - 确认 FastAPI 正确配置了前端路由处理
   - 检查浏览器地址栏 URL 是否正确

### 开发调试

- 使用 Vue DevTools 浏览器插件调试 Vue 应用
- 检查 Network 选项卡查看 API 请求
- 使用 `console.log` 或 `debugger` 语句调试 JavaScript

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。