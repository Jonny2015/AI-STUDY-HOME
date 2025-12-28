# Database Query Tool

一个功能强大的数据库查询工具,支持 PostgreSQL 和 MySQL 数据库,提供自然语言转 SQL、元数据浏览、查询执行和结果导出等功能。

A powerful database query tool supporting PostgreSQL and MySQL with natural language to SQL conversion, metadata browsing, query execution, and result export.

## 功能特性 Features

### 核心功能 Core Features

- ✅ **数据库连接管理**: Database Connection Management - 支持 PostgreSQL 和 MySQL
- ✅ **元数据浏览**: Metadata Browsing - 自动提取并展示数据库表结构和列信息
- ✅ **SQL 查询执行**: SQL Query Execution - 安全的 SQL 查询执行,自动添加查询限制
- ✅ **自然语言转 SQL**: Natural Language to SQL - 使用 AI 将中英文自然语言转换为 SQL 查询
- ✅ **查询结果导出**: Result Export - 支持 CSV 和 JSON 格式导出
- ✅ **查询历史**: Query History - 自动记录查询历史,方便追溯

### 安全特性 Security Features

- 🔒 SQL 注入防护 (sqlglot 解析验证)
- 🔒 仅允许 SELECT 查询
- 🔒 自动添加 LIMIT 1000 限制
- 🔒 环境变量管理敏感信息

## 技术栈 Tech Stack

### 后端 Backend

- **框架**: FastAPI (Python 3.12+)
- **数据验证**: Pydantic v2
- **数据库**: SQLModel (SQLite) + asyncpg/aiomysql (PostgreSQL/MySQL)
- **SQL 解析**: sqlglot
- **AI 集成**: OpenAI SDK

### 前端 Frontend

- **框架**: React 19 + TypeScript 5
- **UI 组件**: Refine 5 + Ant Design 5
- **代码编辑器**: Monaco Editor
- **样式**: Tailwind CSS 4
- **构建工具**: Vite 7

## 快速开始 Quick Start

### 前置要求 Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 或 MySQL 数据库 (可选,用于测试)

### 1. 初始化项目 Initial Setup

```bash
# 安装所有依赖
make install

# 设置数据库和环境
make setup
# 编辑 backend/.env 并添加 OPENAI_API_KEY

# 启动开发服务器
make dev
```

### 2. 手动设置 Manual Setup

#### 后端设置 Backend Setup

```bash
cd backend

# 安装依赖
uv pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件,添加 OPENAI_API_KEY

# 初始化数据库
alembic upgrade head

# 启动后端服务
uvicorn app.main:app --reload --port 8000
```

Backend will run on http://localhost:8000

API Docs: http://localhost:8000/docs

#### 前端设置 Frontend Setup

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.local.example .env.local
# .env.local 已包含默认配置,无需修改

# 启动开发服务器
npm run dev
```

Frontend will run on http://localhost:5173

### 3. 访问应用 Access Application

打开浏览器访问 http://localhost:5173

## 项目结构 Project Structure

```
db_query/
├── backend/                 # FastAPI 后端 Backend
│   ├── app/
│   │   ├── main.py          # 应用入口
│   │   ├── models/          # 数据模型
│   │   ├── services/        # 业务逻辑
│   │   └── api/             # API 路由
│   ├── tests/               # 测试
│   ├── alembic/             # 数据库迁移
│   └── pyproject.toml       # Python 依赖
│
├── frontend/                # React 前端 Frontend
│   ├── src/
│   │   ├── components/      # React 组件
│   │   ├── pages/           # 页面组件
│   │   ├── services/        # API 服务
│   │   └── types/           # TypeScript 类型
│   ├── package.json         # Node 依赖
│   └── vite.config.ts       # Vite 配置
│
├── specs/                   # 规格文档
│   └── 001-db-query-tool/
│       ├── spec.md          # 功能规格
│       ├── plan.md          # 实现计划
│       ├── tasks.md         # 任务列表
│       └── contracts/       # API 契约
│
├── fixtures/                # REST Client 测试
├── Makefile                 # 快捷命令
└── README.md                # 本文件
```

## 开发命令 Development Commands

```bash
# 查看所有可用命令
make help

# 启动开发环境 (后端 + 前端)
make dev

# 仅启动后端
make dev-backend

# 仅启动前端
make dev-frontend

# 运行测试
make test

# 代码格式化
make format

# 代码检查
make lint

# 健康检查
make health

# 打开 API 文档
make docs
```

## 使用指南 User Guide

### 1. 添加数据库连接 Add Database Connection

1. 点击"添加数据库"按钮
2. 填写连接信息:
   - **名称**: 数据库名称,如 `production_db`
   - **连接字符串**:
     - PostgreSQL: `postgresql://user:password@host:port/database`
     - MySQL: `mysql://user:password@host:port/database`
   - **数据库类型**: 选择 PostgreSQL 或 MySQL
3. 点击"测试连接"验证配置
4. 点击"保存"完成添加

### 2. 浏览数据库元数据 Browse Metadata

1. 在数据库列表中点击数据库名称
2. 查看树形结构的表和列信息
3. 点击表名查看列详情

### 3. 执行 SQL 查询 Execute SQL Query

1. 选择数据库
2. 在 SQL 编辑器中输入查询
3. 点击"执行查询"按钮
4. 在结果表格中查看数据
5. 可选: 导出结果为 CSV 或 JSON

### 4. 使用自然语言查询 Natural Language Query

1. 切换到"自然语言"标签
2. 输入查询描述 (支持中英文)
3. 点击"生成 SQL"按钮
4. 查看/编辑生成的 SQL
5. 点击"执行查询"运行

## API 测试 API Testing

### Using REST Client (VSCode)

1. 安装 [REST Client 扩展](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)
2. 打开 `fixtures/test.rest`
3. 点击请求上方的 "Send Request"
4. 在 VSCode 面板中查看响应

详见 `fixtures/README.md`

### Using Makefile

```bash
# 检查后端是否运行
make health

# 打开 API 文档
make docs
```

## 测试 Testing

### 后端测试 Backend Tests

```bash
cd backend

# 运行所有测试
pytest

# 查看覆盖率
pytest --cov=app --cov-report=html
```

### 前端测试 Frontend Tests

```bash
cd frontend

# 运行测试
npm run test

# 生成覆盖率报告
npm run test -- --coverage
```

## 部署 Deployment

### 使用 Docker

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 手动部署 Manual Deployment

详见:
- [后端部署指南](./backend/README.md#部署)
- [前端部署指南](./frontend/README.md#部署)

## 故障排查 Troubleshooting

### 后端无法启动 Backend Won't Start

1. 检查 Python 版本: `python --version` (需要 3.12+)
2. 检查依赖是否安装
3. 检查数据库迁移: `alembic upgrade head`
4. 查看日志输出

### 前端无法连接后端 Frontend Can't Connect

1. 确认后端正在运行: http://localhost:8000/docs
2. 检查 `.env.local` 中的 `VITE_API_BASE_URL`
3. 检查浏览器控制台的网络请求

### OpenAI API 错误 OpenAI API Error

1. 确认 API 密钥已设置
2. 检查 API 密钥是否有效
3. 确认账户有足够的配额

### 数据库连接失败 Database Connection Failed

1. 检查连接字符串格式
2. 确认数据库服务器正在运行
3. 检查网络连接和防火墙设置

## 项目状态 Project Status

✅ **Phase 4 Complete**: Polish & Documentation 完成

- ✅ Phase 1: Setup & Foundation
- ✅ Phase 2: Core Features (US1 + US2)
- ✅ Phase 3: Enhanced Features (US3 + US4)
- ✅ Phase 4: Polish & Documentation

## 相关文档 Related Documentation

- [后端 README](./backend/README.md)
- [前端 README](./frontend/README.md)
- [API 规范](./specs/001-db-query-tool/contracts/api-v1.yaml)
- [功能规格](./specs/001-db-query-tool/spec.md)
- [实现计划](./specs/001-db-query-tool/plan.md)

## 贡献 Contributing

欢迎贡献! 请遵循以下步骤:

1. Fork 项目
2. 创建功能分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add amazing feature'`
4. 推送到分支: `git push origin feature/amazing-feature`
5. 提交 Pull Request

## 许可证 License

MIT License

---

**享受使用 Database Query Tool!** 🚀

**Enjoy using Database Query Tool!** 🚀
