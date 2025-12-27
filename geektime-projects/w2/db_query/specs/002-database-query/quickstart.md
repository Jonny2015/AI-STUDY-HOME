# Quickstart Guide: Database Query Tool

**Feature**: Database Query Tool
**Date**: 2025-12-25
**Phase**: Phase 1 - Design & Contracts

## Overview

本文档提供 Database Query Tool 的开发快速入门指南，帮助开发者快速搭建开发环境并开始编码。

---

## Prerequisites

### Required Software

- **Python**: 3.11+ ([下载](https://www.python.org/downloads/))
- **Node.js**: 18+ ([下载](https://nodejs.org/))
- **uv**: Python 包管理工具 ([安装指南](https://github.com/astral-sh/uv?tab=readme-ov-file#installing))
- **Git**: 版本控制 ([下载](https://git-scm.com/))

### Optional Software

- **PostgreSQL**: 14+ ([下载](https://www.postgresql.org/download/)) - 用于测试
- **MySQL**: 8+ ([下载](https://dev.mysql.com/downloads/mysql/)) - 用于测试
- **Docker**: 容器化数据库 ([下载](https://www.docker.com/))

---

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd db_query
```

### 2. Backend Setup

```bash
# 进入后端目录
cd backend

# 使用 uv 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows

uv pip install fastapi uvicorn[standard] pydantic sqlglot openai aiosqlite asyncpg aiomysql

# 安装开发依赖
uv pip install black ruff mypy pytest pytest-asyncio httpx
```

### 3. Frontend Setup

```bash
# 进入前端目录（新终端窗口）
cd frontend

# 安装依赖
npm install

# 或使用 pnpm/yarn
pnpm install
# yarn install
```

### 4. Environment Variables

创建 `.env` 文件（backend 目录下）：

```bash
# .env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**获取 OpenAI API Key**:
1. 访问 [OpenAI Platform](https://platform.openai.com/api-keys)
2. 注册/登录账号
3. 创建 API Key
4. 复制到 `.env` 文件

---

## Development Workflow

### Backend Development

#### 1. 启动开发服务器

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

服务器将运行在 `http://localhost:8000`

#### 2. 访问 API 文档

打开浏览器访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### 3. 代码质量检查

```bash
# 格式化代码
black app tests

# 代码风格检查
ruff check app tests

# 类型检查
mypy app --strict
```

#### 4. 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行单个测试文件
uv run pytest tests/unit/test_sql_parser.py

# 显示详细输出
uv run pytest -v

# 显示覆盖率
uv run pytest --cov=app
```

---

### Frontend Development

#### 1. 启动开发服务器

```bash
cd frontend
npm run dev
```

应用将运行在 `http://localhost:3000`（或 Vite 分配的端口）

#### 2. 类型检查

```bash
npm run type-check
```

#### 3. 运行 E2E 测试

```bash
# 首次运行需要安装 Playwright 浏览器
npx playwright install

# 运行 E2E 测试
npm run test:e2e

# 查看测试报告
npm run test:e2e -- --reporter=html
```

---

## Project Structure Overview

### Backend Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理（环境变量）
│   ├── models/                 # Pydantic 数据模型
│   ├── adapters/               # 数据库适配器（SOLID）
│   ├── services/               # 业务逻辑层
│   ├── api/
│   │   └── v1/                 # API 路由
│   ├── core/                   # 核心功能
│   └── utils/                  # 工具函数
├── tests/
│   ├── unit/                   # 单元测试
│   ├── integration/            # 集成测试
│   └── fixtures/
│       └── test.rest           # HTTP 测试
├── pyproject.toml              # uv 项目配置
└── .env                        # 环境变量（不提交）
```

### Frontend Structure

```
frontend/
├── src/
│   ├── components/             # React 组件
│   ├── pages/                  # 页面组件
│   ├── services/               # API 服务
│   ├── types/                  # TypeScript 类型
│   ├── App.tsx                 # 根组件
│   └── main.tsx                # 入口文件
├── tests/e2e/                  # E2E 测试
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

---

## Quick Start Examples

### Example 1: Add Database Connection

```bash
curl -X PUT http://localhost:8000/api/v1/dbs/my_postgres \
  -H "Content-Type: application/json" \
  -d '{"url": "postgresql://postgres:postgres@localhost:5432/postgres"}'
```

**Response**:
```json
{
  "databaseName": "my_postgres",
  "dbType": "postgresql",
  "createdAt": "2025-12-25T12:00:00Z",
  "connectionStatus": "connected",
  "lastConnectedAt": "2025-12-25T12:00:00Z"
}
```

---

### Example 2: List Databases

```bash
curl http://localhost:8000/api/v1/dbs
```

**Response**:
```json
{
  "databases": [
    {
      "databaseName": "my_postgres",
      "dbType": "postgresql",
      "createdAt": "2025-12-25T12:00:00Z",
      "connectionStatus": "connected",
      "lastConnectedAt": "2025-12-25T12:00:00Z"
    }
  ],
  "totalCount": 1
}
```

---

### Example 3: Get Database Metadata

```bash
curl http://localhost:8000/api/v1/dbs/my_postgres
```

**Response**:
```json
{
  "databaseName": "my_postgres",
  "dbType": "postgresql",
  "tables": [
    {
      "schemaName": "public",
      "tableName": "users",
      "tableType": "table",
      "columns": [
        {
          "columnName": "id",
          "dataType": "integer",
          "isNullable": false,
          "isPrimaryKey": true
        },
        {
          "columnName": "name",
          "dataType": "varchar(255)",
          "isNullable": false,
          "isPrimaryKey": false
        }
      ]
    }
  ],
  "metadataExtractedAt": "2025-12-25T12:05:00Z"
}
```

---

### Example 4: Execute SQL Query

```bash
curl -X POST http://localhost:8000/api/v1/dbs/my_postgres/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM users LIMIT 10"}'
```

**Response**:
```json
{
  "columns": ["id", "name", "email"],
  "rows": [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"}
  ],
  "rowCount": 2,
  "executionTimeMs": 15
}
```

---

### Example 5: Generate SQL from Natural Language

```bash
curl -X POST http://localhost:8000/api/v1/dbs/my_postgres/query/natural \
  -H "Content-Type: application/json" \
  -d '{"prompt": "查询所有活跃用户"}'
```

**Response**:
```json
{
  "sql": "SELECT * FROM users WHERE status = 'active' LIMIT 1000",
  "explanation": "查询 status 字段为 'active' 的用户记录",
  "warnings": []
}
```

---

## Common Development Tasks

### Task 1: Add New Database Adapter

**File**: `backend/app/adapters/postgresql.py`

```python
from .base import DatabaseAdapter

class PostgreSQLAdapter(DatabaseAdapter):
    async def connect(self, url: str) -> Connection:
        # 实现连接逻辑
        pass

    async def get_metadata(self) -> DatabaseMetadata:
        # 实现元数据提取
        pass

    async def execute_query(self, sql: str) -> QueryResult:
        # 实现查询执行
        pass
```

**注册适配器**: `backend/app/adapters/registry.py`

```python
from .postgresql import PostgreSQLAdapter

AdapterRegistry.register('postgresql', PostgreSQLAdapter)
```

---

### Task 2: Add API Endpoint

**File**: `backend/app/api/v1/databases.py`

```python
from fastapi import APIRouter, HTTPException
from app.models.database import DatabaseResponse

router = APIRouter(prefix="/dbs", tags=["databases"])

@router.get("/{name}", response_model=DatabaseResponse)
async def get_database(name: str) -> DatabaseResponse:
    # 实现逻辑
    pass
```

**注册路由**: `backend/app/main.py`

```python
from app.api.v1 import databases

app.include_router(databases.router, prefix="/api/v1")
```

---

### Task 3: Add React Component

**File**: `frontend/src/components/DatabaseList.tsx`

```typescript
import React from 'react';
import { useList } from '@refine/core';
import type { Database } from '../types';

export const DatabaseList: React.FC = () => {
  const { data, isLoading } = useList<Database>({
    resource: 'databases',
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {data?.data.map((db) => (
        <div key={db.databaseName}>{db.databaseName}</div>
      ))}
    </div>
  );
};
```

---

## Testing Guide

### Backend Testing

#### Unit Tests

```python
# tests/unit/test_sql_parser.py
import pytest
from app.core.sql_parser import validate_sql

def test_validate_select_query():
    result = validate_sql("SELECT * FROM users")
    assert result.is_valid
    assert result.sql == "SELECT * FROM users LIMIT 1000"

def test_reject_non_select_query():
    result = validate_sql("UPDATE users SET name = 'test'")
    assert not result.is_valid
    assert "仅允许 SELECT" in result.error
```

#### Integration Tests

```python
# tests/integration/test_database_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_add_database():
    response = client.put(
        "/api/v1/dbs/test_db",
        json={"url": "postgresql://user:pass@localhost:5432/test"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["databaseName"] == "test_db"
```

---

### Frontend Testing

#### E2E Tests

```typescript
// tests/e2e/database.spec.ts
import { test, expect } from '@playwright/test';

test('add database connection', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // 点击添加数据库按钮
  await page.click('button:has-text("Add Database")');

  // 填写表单
  await page.fill('input[name="name"]', 'test_db');
  await page.fill('input[name="url"]', 'postgresql://localhost:5432/test');

  // 提交
  await page.click('button:has-text("Submit")');

  // 验证结果
  await expect(page.locator('text=test_db')).toBeVisible();
});
```

---

## Troubleshooting

### Issue: Cannot connect to PostgreSQL

**Solution**:
1. 确认 PostgreSQL 服务运行：`pg_isready`
2. 检查连接 URL 格式：`postgresql://user:password@host:port/database`
3. 检查防火墙设置
4. 查看 PostgreSQL 日志：`tail -f /var/log/postgresql/postgresql-*.log`

---

### Issue: OpenAI API Error

**Solution**:
1. 确认 API key 有效：检查 `.env` 文件
2. 检查 API key 配额：访问 [OpenAI Dashboard](https://platform.openai.com/usage)
3. 验证网络连接：`curl https://api.openai.com/v1/models`

---

### Issue: Frontend CORS Error

**Solution**:
确认后端 CORS 中间件配置正确：

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Next Steps

1. **Review Architecture**: 阅读 `research.md` 了解技术选型
2. **Study Data Model**: 阅读 `data-model.md` 理解数据结构
3. **Explore API**: 查看 `contracts/openapi.yaml` 了解 API 契约
4. **Start Coding**: 从最简单的端点开始（如 `/api/v1/dbs` GET）

---

## Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Refine Docs**: https://refine.dev/
- **sqlglot Docs**: https://github.com/tobymao/sqlglot
- **OpenAI API Docs**: https://platform.openai.com/docs
- **Monaco Editor Docs**: https://microsoft.github.io/monaco-editor/

---

**Happy Coding!** 🚀
