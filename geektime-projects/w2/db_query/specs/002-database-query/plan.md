# Implementation Plan: Database Query Tool

**Branch**: `002-database-query` | **Date**: 2025-12-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-database-query/spec.md`

## Summary

构建一个数据库查询工具，允许用户通过 Web 界面管理数据库连接、查看元数据、执行 SQL 查询以及使用自然语言生成 SQL。技术栈采用 Python/FastAPI 后端 + React/Refine 前端，使用 SQLite 存储元数据，OpenAI API 实现自然语言到 SQL 的转换。

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5+ strict mode (frontend)
**Primary Dependencies**: FastAPI, Pydantic V2, sqlglot, OpenAI SDK, React 18, Refine 5, Ant Design, Monaco Editor
**Storage**: SQLite (`~/.db_query/db_query.db`) for metadata and connections
**Testing**: pytest, pytest-asyncio (backend), Playwright (frontend)
**Target Platform**: Web browser (modern browsers: Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (backend + frontend)
**Performance Goals**:
- 元数据提取: 100 个表以内 < 10 秒
- 查询响应: 2 秒内开始展示结果
- SQL 验证: < 500ms
- 缓存加载: < 1 秒

**Constraints**:
- 仅允许 SELECT 查询（安全限制）
- 查询超时: 60 秒
- 默认 LIMIT 1000
- 无需认证（开放访问）
- 支持 CORS（所有 origin）

**Scale/Scope**:
- 支持数据库: PostgreSQL, MySQL
- 用户规模: < 100 人
- 并发查询: ≥ 10 用户同时操作

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### 原则合规性评估

| 原则 | 状态 | 说明 |
|------|------|------|
| **Ergonomic Python Style** | ✅ PASS | 使用 Python 3.11+, async/await, type hints, black/ruff/mypy |
| **Strict Type Annotation** | ✅ PASS | 后端 mypy --strict, 前端 TypeScript strict, 禁止 Any 类型 |
| **Pydantic Data Models** | ✅ PASS | 所有 API 请求/响应使用 Pydantic V2 模型 |
| **JSON Naming Convention** | ✅ PASS | API 响应使用 camelCase（通过 alias 实现） |
| **Open Access Policy** | ✅ PASS | 无需认证，支持 CORS 所有 origin |

### 技术标准合规性

**后端技术栈** (✅ 全部符合):
- Python 3.11+ ✅
- FastAPI ✅
- Pydantic V2 ✅
- 数据库驱动: asyncpg (PostgreSQL), aiomysql (MySQL), aiosqlite (SQLite) ✅
- SQL 解析: sqlglot ✅
- OpenAI SDK ✅
- 代码质量: black, ruff, mypy strict ✅
- 测试: pytest, pytest-asyncio ✅

**前端技术栈** (✅ 全部符合):
- TypeScript strict mode ✅
- React 18+ ✅
- Refine 5 ✅
- Ant Design ✅
- Tailwind CSS ✅
- Monaco Editor ✅
- 测试: Playwright ✅

**架构原则** (✅ 全部符合):
- SOLID 原则, 特别是开闭原则（Adapter 模式支持扩展数据库类型）
- RESTful API 风格 (`/api/v1/`)
- 统一错误处理
- SQLite 存储元数据
- SQL 安全（仅 SELECT，自动 LIMIT）

### Gate 决策

**状态**: ✅ **APPROVED** - 所有宪章原则和技术标准均符合，无需 Complexity Tracking

## Project Structure

### Documentation (this feature)

```text
specs/002-database-query/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── openapi.yaml     # OpenAPI 3.1 specification
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── models/                 # Pydantic 数据模型
│   │   ├── database.py         # 数据库连接模型
│   │   ├── metadata.py         # 元数据模型
│   │   └── query.py            # 查询请求/响应模型
│   ├── adapters/               # 数据库适配器 (SOLID - Adapter Pattern)
│   │   ├── base.py             # DatabaseAdapter 抽象基类
│   │   ├── postgresql.py       # PostgreSQL 适配器
│   │   ├── mysql.py            # MySQL 适配器
│   │   └── registry.py         # 适配器注册表
│   ├── services/               # 业务服务层
│   │   ├── database_service.py # 数据库服务门面
│   │   ├── metadata_service.py # 元数据服务
│   │   ├── query_service.py    # 查询服务
│   │   └── llm_service.py      # LLM 服务
│   ├── api/
│   │   └── v1/                 # API 路由
│   │       ├── databases.py    # 数据库管理端点
│   │       └── queries.py      # 查询端点
│   ├── core/                   # 核心功能
│   │   ├── db.py               # SQLite 数据库管理
│   │   ├── sql_parser.py       # SQL 解析 (sqlglot)
│   │   └── security.py         # 安全验证
│   └── utils/
│       └── logging.py
├── tests/
│   ├── unit/                   # 单元测试
│   ├── integration/            # 集成测试
│   └── fixtures/               # 测试夹具
│       └── test.rest           # HTTP 测试
├── pyproject.toml              # uv 项目配置
└── README.md

frontend/
├── src/
│   ├── components/             # React 组件
│   │   ├── DatabaseList.tsx
│   │   ├── AddDatabaseModal.tsx
│   │   ├── MetadataViewer.tsx
│   │   ├── SqlEditor.tsx       # Monaco Editor
│   │   └── QueryResult.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   └── QueryPage.tsx
│   ├── services/
│   │   └── api.ts              # API 服务
│   ├── types/
│   │   └── index.ts            # TypeScript 类型
│   ├── App.tsx
│   └── main.tsx
├── tests/
│   └── e2e/                    # E2E 测试
│       └── *.spec.ts           # Playwright specs
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

**Structure Decision**:
选择 **Web application 结构**（backend + frontend），原因：
- 前后端技术栈明确且独立（Python vs TypeScript）
- 部署可独立扩展（前端静态文件，后端 API 服务）
- 开发可并行进行（前后端通过 OpenAPI 契约协作）
- 符合宪章定义的技术栈标准

## Complexity Tracking

> **无需填写** - 宪章检查全部通过，无违规需要记录

