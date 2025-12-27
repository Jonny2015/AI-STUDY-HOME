# Database Query Tool

一个现代化的数据库查询工具，支持通过 SQL 或自然语言查询 PostgreSQL 和 MySQL 数据库。

## ✨ 功能特性

- 🔌 **多数据库支持**：支持 PostgreSQL 和 MySQL
- 📊 **数据库元数据管理**：自动提取和缓存数据库表、视图、列信息
- 🔍 **SQL 查询执行**：安全的只读 SQL 查询，自动添加 LIMIT 保护
- 🤖 **AI 自然语言查询**：使用 OpenAI 将自然语言转换为 SQL
- 📥 **结果导出**：支持将查询结果导出为 CSV
- 🎨 **现代化 UI**：基于 React + Ant Design 的响应式界面
- 📝 **Monaco Editor**：强大的 SQL 编辑器，支持语法高亮和自动补全
- 🔒 **安全保护**：仅允许 SELECT 查询，防止数据修改

## 🛠 技术栈

### 后端
- **Python 3.11+** - 编程语言
- **FastAPI** - 现代 Web 框架
- **uv** - 快速 Python 包管理器
- **sqlglot** - SQL 解析和验证
- **OpenAI SDK** - AI 自然语言处理
- **asyncpg** - PostgreSQL 异步驱动
- **aiomysql** - MySQL 异步驱动
- **aiosqlite** - SQLite 元数据存储

### 前端
- **React 19** - UI 框架
- **TypeScript** - 类型安全
- **Refine 5** - 数据管理框架
- **Ant Design 6** - UI 组件库
- **Tailwind CSS 4** - 样式框架
- **Monaco Editor** - SQL 编辑器
- **Vite 7** - 构建工具

## 📋 前置要求

- **Python 3.11+**
- **Node.js 18+**
- **uv** (Python 包管理器)
- **OpenAI API Key** (用于自然语言查询功能)
- **PostgreSQL** 或 **MySQL** 数据库（用于测试）

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd db_query
```

### 2. 安装依赖

使用 Makefile（推荐）：

```bash
make setup
```

或手动安装：

```bash
# 安装后端依赖
cd backend && uv sync

# 安装前端依赖
cd frontend && npm install
```

### 3. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. 启动开发服务器

使用 Makefile：

```bash
# 启动后端（端口 8000）
make dev-backend

# 启动前端（端口 5173）
make dev-frontend

# 或同时启动前后端
make dev
```

或手动启动：

```bash
# 后端
cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端（新终端）
cd frontend && npm run dev
```

### 5. 访问应用

- **前端应用**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc

## 📁 项目结构

```
db_query/
├── backend/              # 后端代码
│   ├── app/              # 应用主目录
│   │   ├── adapters/    # 数据库适配器（SOLID 原则）
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心功能（SQL 解析、安全等）
│   │   ├── models/      # Pydantic 数据模型
│   │   ├── services/    # 业务逻辑服务
│   │   └── utils/       # 工具函数
│   ├── tests/           # 测试文件
│   └── pyproject.toml   # Python 项目配置
├── frontend/            # 前端代码
│   ├── src/
│   │   ├── components/  # React 组件
│   │   ├── pages/       # 页面组件
│   │   ├── services/    # API 服务
│   │   └── types/       # TypeScript 类型定义
│   └── package.json     # Node.js 项目配置
├── fixtures/            # 测试文件
│   ├── test.rest        # REST Client 测试文件
│   └── README.md        # 测试说明
├── specs/               # 项目规范文档
├── Makefile            # 项目构建脚本
└── README.md           # 本文件
```

## 🔌 API 端点

### 数据库管理

- `GET /api/v1/dbs` - 获取所有数据库列表
- `POST /api/v1/dbs` - 添加数据库（POST 方式）
- `PUT /api/v1/dbs/{name}` - 添加数据库（PUT 方式）
- `GET /api/v1/dbs/{name}` - 获取数据库元数据
- `DELETE /api/v1/dbs/{name}` - 删除数据库

### SQL 查询

- `POST /api/v1/dbs/{name}/query` - 执行 SQL 查询
- `POST /api/v1/dbs/{name}/query/export` - 导出查询结果为 CSV

### 自然语言查询

- `POST /api/v1/dbs/{name}/query/natural` - 使用自然语言生成 SQL

### 健康检查

- `GET /health` - 健康检查端点

详细的 API 文档请访问：http://localhost:8000/docs

## 🧪 测试

### 使用 REST Client 测试 API

1. 在 VSCode 中安装 [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) 扩展
2. 打开 `fixtures/test.rest` 文件
3. 点击请求上方的 "Send Request" 按钮
4. 查看响应结果

详细说明请参考 [fixtures/README.md](fixtures/README.md)

### 运行单元测试

```bash
# 运行后端测试
make test-backend

# 运行前端测试
make test-frontend

# 运行所有测试
make test
```

## 🛠 开发指南

### Makefile 命令

查看所有可用命令：

```bash
make help
```

常用命令：

```bash
# 安装依赖
make setup

# 开发服务器
make dev-backend      # 启动后端
make dev-frontend     # 启动前端
make dev              # 同时启动前后端

# 代码质量
make lint-backend     # 检查后端代码
make lint-frontend    # 检查前端代码
make format-backend   # 格式化后端代码
make format-frontend  # 格式化前端代码

# 测试
make test-backend     # 后端测试
make test-frontend    # 前端测试
make test             # 所有测试

# 清理
make clean            # 清理临时文件
```

### 代码规范

#### 后端
- 使用 **Black** 进行代码格式化
- 使用 **Ruff** 进行代码检查
- 使用 **mypy** 进行类型检查
- 遵循 **Ergonomic Python** 风格

#### 前端
- 使用 **TypeScript** 严格模式
- 使用 **Prettier** 进行代码格式化
- 所有组件和函数都需要类型标注

### 数据库连接格式

#### PostgreSQL
```
postgresql://user:password@host:port/database
# 或
postgres://user:password@host:port/database
```

#### MySQL
```
mysql://user:password@host:port/database
```

## 📝 数据存储

- **元数据存储**: `~/.db_query/db_query.db` (SQLite)
- 数据库连接信息和元数据缓存都存储在此文件中

## 🔒 安全特性

- ✅ 仅允许 SELECT 查询
- ✅ SQL 语法验证（使用 sqlglot）
- ✅ 自动添加 LIMIT 1000 保护
- ✅ 输入验证和错误处理
- ✅ CORS 配置（开发环境允许所有来源）

## 🐛 故障排除

### 后端无法启动

1. 检查 Python 版本：`python --version` (需要 3.11+)
2. 检查依赖安装：`cd backend && uv sync`
3. 检查端口占用：确保 8000 端口未被占用
4. 检查环境变量：确保 `OPENAI_API_KEY` 已设置

### 前端无法启动

1. 检查 Node.js 版本：`node --version` (需要 18+)
2. 检查依赖安装：`cd frontend && npm install`
3. 检查端口占用：确保 5173 端口未被占用

### 数据库连接失败

1. 检查数据库服务是否运行
2. 验证连接字符串格式
3. 检查数据库用户权限
4. 查看后端日志获取详细错误信息

### 自然语言查询失败

1. 检查 `OPENAI_API_KEY` 环境变量
2. 确认 API Key 有效且有足够额度
3. 查看后端日志获取详细错误信息

## 📚 相关文档

- [后端 README](backend/README.md)
- [前端 README](frontend/README.md)
- [API 测试说明](fixtures/README.md)
- [项目规范](specs/instructions.md)
- [API 文档](http://localhost:8000/docs) (启动后端后访问)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[添加许可证信息]

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Refine](https://refine.dev/)
- [Ant Design](https://ant.design/)
- [Monaco Editor](https://microsoft.github.io/monaco-editor/)

