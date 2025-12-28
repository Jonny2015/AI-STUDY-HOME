# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个**数据库查询工具**,支持 PostgreSQL 和 MySQL 数据库,提供自然语言转 SQL、元数据浏览、查询执行和结果导出等功能。

**技术栈**:
- **后端**: FastAPI (Python 3.12+) + SQLModel + asyncpg/aiomysql + OpenAI SDK
- **前端**: React 19 + TypeScript 5 + Refine 5 + Ant Design 5 + Monaco Editor + Vite 7

## 常用开发命令

### 项目初始化
```bash
# 安装所有依赖并初始化数据库
make setup

# 初始化后需编辑 backend/.env 添加 OPENAI_API_KEY
```

### 开发服务器
```bash
# 同时启动前后端开发服务器
make dev

# 仅启动后端 (http://localhost:8000)
make dev-backend

# 仅启动前端 (http://localhost:5173)
make dev-frontend
```

### 测试
```bash
# 运行所有测试
make test

# 运行后端测试
make test-backend

# 运行后端测试并生成覆盖率报告
make test-backend-coverage

# 运行前端测试
make test-frontend
```

### 代码质量
```bash
# 代码检查
make lint
make lint-backend    # 使用 ruff
make lint-frontend   # 使用 ESLint

# 代码格式化
make format
make format-backend  # 使用 ruff format
make format-frontend # 使用 ESLint --fix
```

### 数据库迁移
```bash
# 应用迁移
make db-upgrade

# 创建新迁移
make db-migrate MESSAGE="your description"

# 查看迁移历史
make db-history
```

### 快捷命令
```bash
# 健康检查
make health

# 打开 API 文档
make docs
```

## 核心架构

### 后端架构模式

项目使用 **适配器模式 (Adapter Pattern) + 工厂模式 (Factory Pattern)** 来支持多种数据库:

```
app/
├── adapters/                    # 数据库适配器层
│   ├── base.py                  # DatabaseAdapter 抽象基类
│   ├── registry.py              # DatabaseAdapterRegistry (工厂)
│   ├── postgresql.py            # PostgreSQL 实现
│   └── mysql.py                 # MySQL 实现
│
├── services/                    # 业务逻辑层
│   ├── sql_validator.py         # SQL 验证 (仅允许 SELECT)
│   ├── nl2sql.py                # 自然语言转 SQL (OpenAI)
│   └── export.py                # 结果导出服务
│
├── models/                      # 数据模型 (SQLModel + Pydantic)
│   ├── database.py              # DatabaseConnection 实体
│   ├── metadata.py              # DatabaseMetadata 实体
│   ├── query.py                 # QueryHistory 实体
│   └── schemas.py               # API 请求/响应模型 (camelCase)
│
└── api/v1/                      # API 路由层
    ├── databases.py             # 数据库管理 API
    └── queries.py               # 查询执行 API
```

### 适配器模式 (关键架构理解)

**核心思想**: 所有数据库操作通过 `DatabaseAdapter` 抽象接口进行,新数据库支持无需修改现有代码。

#### 添加新数据库支持 (例如 Oracle)

1. **创建适配器** (`app/adapters/oracle.py`):
   ```python
   from app.adapters.base import DatabaseAdapter

   class OracleAdapter(DatabaseAdapter):
       async def test_connection(self): ...
       async def get_connection_pool(self): ...
       async def extract_metadata(self): ...
       async def execute_query(self, sql: str): ...
       def get_dialect_name(self) -> str: ...
       def get_identifier_quote_char(self) -> str: ...
   ```

2. **注册适配器** (在 `app/adapters/registry.py` 的 `__init__` 中):
   ```python
   self.register(DatabaseType.ORACLE, OracleAdapter)
   ```

3. **更新枚举** (在 `app/models/database.py` 的 `DatabaseType` 中):
   ```python
   class DatabaseType(str, Enum):
       ORACLE = "oracle"
   ```

**完成!** 所有 API 端点自动支持 Oracle,无需修改其他代码。

### API 命名约定

**后端使用 snake_case,前端使用 camelCase**:
- 后端 Pydantic 模型通过 `alias_generator=to_camel` 自动转换
- 前端 TypeScript 类型定义使用 camelCase

### 数据库连接字符串格式

- **PostgreSQL**: `postgresql://user:password@host:port/database`
- **MySQL**: `mysql://user:password@host:port/database`

## 安全规则

### SQL 验证
- **仅允许 SELECT 查询** (使用 `sqlglot` 解析验证)
- 自动添加 `LIMIT 1000` 限制
- SQL 注入防护

### 环境变量
- 所有敏感信息存储在 `backend/.env`
- 不要将 `.env` 文件提交到代码库

### CORS
- 后端已配置 CORS 允许所有 origin (开发环境)
- 生产环境需在 `backend/.env` 配置 `CORS_ORIGINS`

## 文件组织规范

### 后端服务层
- **adapters/**: 数据库适配器,每个数据库一个文件
- **services/**: 业务逻辑服务 (验证、转换、导出等)
- **models/**: 数据模型和 API schemas
- **api/v1/**: FastAPI 路由处理

### 前端组件
- **components/**: 可复用组件 (SqlEditor, ResultTable, MetadataTree 等)
- **pages/**: 页面级组件 (按功能分组)
- **services/**: API 服务层 (axios 实例、dataProvider)
- **types/**: TypeScript 类型定义

## 开发流程

### 实现新功能
1. 在 `specs/` 中查看或创建功能规格文档
2. 后端: 在 `app/services/` 添加业务逻辑,`app/api/v1/` 添加路由
3. 前端: 在 `src/types/` 添加类型定义,`src/pages/` 或 `src/components/` 添加组件
4. 在 `backend/tests/` 添加测试
5. 运行 `make lint` 和 `make test` 验证

### 数据库迁移
1. 修改 `app/models/` 中的模型
2. 运行 `make db-migrate MESSAGE="description"`
3. 检查生成的迁移文件
4. 运行 `make db-upgrade` 应用迁移

### API 契约测试
- API 规范定义在 `specs/001-db-query-tool/contracts/api-v1.yaml`
- 可使用 VSCode REST Client 扩展测试 `fixtures/test.rest`

## 项目状态

**当前分支**: `001-data-export` - 正在开发数据导出功能

**已完成阶段**:
- ✅ Phase 1: Setup & Foundation
- ✅ Phase 2: Core Features (数据库连接、元数据浏览)
- ✅ Phase 3: Enhanced Features (SQL 查询、自然语言转 SQL)
- ✅ Phase 4: Polish & Documentation

**当前开发**: 数据导出功能增强 (支持 CSV/JSON/MD 导出,AI 助手辅助)

## 相关文档

- [主 README](./README.md) - 项目快速开始
- [后端 README](./backend/README.md) - 后端详细文档
- [前端 README](./frontend/README.md) - 前端详细文档
- [架构总结](./docs/ARCHITECTURE_SUMMARY.md) - 架构设计详解
- [API 规范](./specs/001-db-query-tool/contracts/api-v1.yaml) - OpenAPI 规范

## 故障排查

### 后端无法启动
- 检查 Python 版本: `python --version` (需要 3.12+)
- 检查环境变量: `backend/.env` 是否包含 `OPENAI_API_KEY`
- 检查数据库迁移: `make db-upgrade`

### 前端无法连接后端
- 确认后端运行: `curl http://localhost:8000/health`
- 检查 `frontend/.env.local` 中的 `VITE_API_BASE_URL`

### 测试失败
- 后端: `cd backend && uv run pytest -v` (查看详细错误)
- 前端: `cd frontend && npm run test -- --verbose` (查看详细错误)

### OpenAI API 错误
- 验证 API 密钥: `curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models`
- 检查账户配额
