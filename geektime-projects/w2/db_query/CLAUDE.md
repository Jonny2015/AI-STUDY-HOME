# Database Query Tool - Development Guidelines

Auto-generated from feature plans. Last updated: 2025-12-24

## Active Technologies

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Data Validation**: Pydantic V2
- **Database Drivers**: asyncpg (PostgreSQL), aiomysql (MySQL), aiosqlite (SQLite)
- **SQL Parser**: sqlglot
- **LLM**: OpenAI SDK (GPT-4o-mini)
- **Testing**: pytest, pytest-asyncio

### Frontend
- **Language**: TypeScript (strict mode)
- **Framework**: React 18+
- **UI Framework**: Refine 5, Ant Design
- **Editor**: Monaco Editor
- **Testing**: Playwright
- **Build Tool**: Vite

### Storage
- **Metadata Cache**: SQLite (~/.db_query/db_query.db)

## Project Structure

```text
backend/
├── app/
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置管理
│   ├── models/                 # Pydantic数据模型
│   │   ├── database.py         # 数据库连接模型
│   │   ├── metadata.py         # 元数据模型
│   │   └── query.py            # 查询请求/响应模型
│   ├── adapters/               # 数据库适配器(SOLID架构)
│   │   ├── base.py             # DatabaseAdapter抽象基类
│   │   ├── postgresql.py       # PostgreSQL适配器
│   │   ├── mysql.py            # MySQL适配器
│   │   └── registry.py         # 适配器注册表
│   ├── services/               # 业务服务层
│   │   ├── database_service.py # 数据库服务门面
│   │   ├── metadata_service.py # 元数据服务
│   │   ├── query_service.py    # 查询服务
│   │   └── llm_service.py      # LLM服务
│   ├── api/v1/                 # API路由
│   │   ├── databases.py        # 数据库管理端点
│   │   └── queries.py          # 查询端点
│   ├── core/                   # 核心功能
│   │   ├── db.py               # SQLite数据库管理
│   │   ├── sql_parser.py       # SQL解析(sqlglot)
│   │   └── security.py         # 安全验证
│   └── utils/
│       └── logging.py
└── tests/

frontend/
├── src/
│   ├── components/             # React组件
│   │   ├── DatabaseList.tsx
│   │   ├── AddDatabaseModal.tsx
│   │   ├── MetadataViewer.tsx
│   │   ├── SqlEditor.tsx       # Monaco Editor
│   │   └── QueryResult.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   └── QueryPage.tsx
│   ├── services/
│   │   └── api.ts              # API服务
│   ├── types/
│   │   └── index.ts            # TypeScript类型
│   ├── App.tsx
│   └── main.tsx
└── tests/e2e/
```

## Commands

### Backend
```bash
# 安装依赖
uv sync

# 运行开发服务器
uv run uvicorn app.main:app --reload --port 8000

# 代码检查
uv run black app tests --check
uv run ruff check app tests
uv run mypy app --strict

# 运行测试
uv run pytest
```

### Frontend
```bash
# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 类型检查
npm run type-check

# 运行E2E测试
npx playwright test
```

## Code Style

### Python (Backend)
- **Style Guide**: Ergonomic Python - 优先使用现代Python特性
- **Formatting**: black (line-length: 100)
- **Linting**: ruff
- **Type Checking**: mypy --strict (禁止Any类型)
- **Key Practices**:
  - 使用async/await处理所有I/O操作
  - 优先使用Pydantic模型而非普通类
  - 所有函数必须有类型提示
  - 遵循SOLID原则,特别是开闭原则

### TypeScript (Frontend)
- **Mode**: strict (所有严格检查开启)
- **Components**: 函数组件 + Hooks
- **Props**: 必须有明确的类型定义
- **State**: 使用useState, useReducer
- **API Calls**: 使用async/await

## API Endpoints

```bash
# 数据库管理
GET    /api/v1/dbs                    # 获取所有数据库
PUT    /api/v1/dbs/{name}             # 添加数据库
GET    /api/v1/dbs/{name}             # 获取数据库元数据
DELETE /api/v1/dbs/{name}             # 删除数据库连接

# 查询操作
POST   /api/v1/dbs/{name}/query       # 执行SQL查询
POST   /api/v1/dbs/{name}/query/natural  # 自然语言生成SQL
```

## Recent Changes

### Feature: 001-database-query-tool
- **Added**: Database query tool with PostgreSQL/MySQL support
- **Added**: Metadata extraction and caching with SQLite
- **Added**: SQL query execution with safety validation (SELECT only)
- **Added**: Natural language to SQL generation using OpenAI
- **Added**: SOLID architecture with Adapter pattern for extensibility
- **Added**: camelCase JSON responses with Pydantic aliases

<!-- MANUAL ADDITIONS START -->
<!-- Add custom development guidelines below -->

## Architecture Principles

### SOLID Principles Implementation

1. **Single Responsibility Principle**:
   - Adapter: 仅负责特定数据库的操作
   - Registry: 仅负责适配器的生命周期管理
   - Service: 仅负责业务逻辑协调
   - API: 仅负责HTTP请求/响应处理

2. **Open/Closed Principle**:
   - 添加新数据库: 创建新Adapter类,注册到Registry
   - 不需要修改现有代码

3. **Liskov Substitution Principle**:
   - 所有DatabaseAdapter子类可互换使用

4. **Interface Segregation Principle**:
   - DatabaseAdapter接口精简,只包含必要方法

5. **Dependency Inversion Principle**:
   - Service层依赖DatabaseAdapter抽象,而非具体实现

### JSON Naming Convention

所有API响应使用camelCase:
```python
class ExampleResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel_case,
        populate_by_name=True
    )

    database_id: int = Field(alias="databaseId")
    created_at: datetime = Field(alias="createdAt")
```

### Security Rules

- 只允许SELECT查询
- 自动添加LIMIT子句(默认1000)
- 使用sqlglot解析验证所有SQL
- 连接URL不记录明文密码

<!-- MANUAL ADDITIONS END -->
