# Database Query Tool - Backend

FastAPI 后端服务,提供数据库查询、元数据提取、自然语言转SQL等功能。

## 技术栈

- **Python**: 3.12+
- **Web 框架**: FastAPI 0.121+
- **数据验证**: Pydantic v2
- **数据库 ORM**: SQLModel (SQLite + PostgreSQL/MySQL)
- **SQL 解析**: sqlglot
- **AI 集成**: OpenAI SDK
- **异步驱动**: asyncpg (PostgreSQL), aiomysql (MySQL)
- **测试**: pytest, pytest-asyncio, httpx

## 项目结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理 (Pydantic Settings)
│   ├── database.py          # SQLite 数据库连接
│   ├── models/              # 数据模型
│   │   ├── database.py      # DatabaseConnection 实体
│   │   ├── metadata.py      # DatabaseMetadata 实体
│   │   ├── query.py         # QueryHistory 实体
│   │   └── schemas.py       # API 请求/响应模型 (camelCase)
│   ├── services/            # 业务逻辑
│   │   ├── db_connection.py # 数据库连接管理
│   │   ├── mysql_connection.py # MySQL 连接服务
│   │   ├── metadata.py      # 元数据提取
│   │   ├── mysql_metadata.py # MySQL 元数据服务
│   │   ├── query.py         # 查询执行
│   │   ├── mysql_query.py   # MySQL 查询服务
│   │   ├── sql_validator.py # SQL 验证 (sqlglot)
│   │   ├── nl2sql.py        # 自然语言转 SQL
│   │   ├── connection_factory.py  # 连接工厂
│   │   └── export.py        # 结果导出
│   └── api/                 # API 路由
│       └── v1/
│           ├── databases.py # 数据库管理 API
│           └── queries.py   # 查询执行 API
├── tests/
│   ├── unit/               # 单元测试
│   ├── integration/        # 集成测试
│   └── contract/           # 契约测试
├── alembic/                # 数据库迁移
├── pyproject.toml          # 项目依赖和配置
└── .env.example            # 环境变量模板
```

## 快速开始

### 1. 安装依赖

推荐使用 `uv` 包管理器:

```bash
# 安装 uv
pip install uv

# 安装项目依赖 (包括开发依赖)
uv pip install -e ".[dev]"

# 或使用 pip
pip install -e ".[dev]"
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置:

```bash
cp .env.example .env
```

编辑 `.env` 文件:

```env
# OpenAI API 配置 (用于自然语言转 SQL)
OPENAI_API_KEY=your_openai_api_key_here

# 数据库存储路径 (可选,默认 ~/.db_query/db_query.db)
DB_PATH=~/.db_query/db_query.db

# API 服务配置 (可选)
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. 初始化数据库

运行数据库迁移创建 SQLite 数据库:

```bash
# 创建所有表
alembic upgrade head

# 或使用 Python 脚本
python -m app.database
```

### 4. 启动服务

```bash
# 开发模式 (自动重载)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

服务启动后,访问:
- API 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc

## 开发工具

### 代码检查

```bash
# 使用 ruff 进行代码格式化和检查
ruff check .
ruff format .

# 使用 mypy 进行类型检查
mypy app/
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_sql_validator.py

# 查看测试覆盖率
pytest --cov=app --cov-report=html
```

### 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "description"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## API 使用示例

### 1. 添加数据库连接

```bash
curl -X PUT "http://localhost:8000/api/v1/dbs/mydb" \
  -H "Content-Type: application/json" \
  -d '{
    "connectionString": "postgresql://user:password@localhost:5432/mydb",
    "dbType": "postgresql"
  }'
```

### 2. 测试数据库连接

```bash
curl -X POST "http://localhost:8000/api/v1/dbs/mydb/test"
```

### 3. 获取数据库元数据

```bash
curl -X GET "http://localhost:8000/api/v1/dbs/mydb"
```

响应示例:

```json
{
  "name": "mydb",
  "dbType": "postgresql",
  "metadata": {
    "tables": [
      {
        "name": "users",
        "columns": [
          {
            "name": "id",
            "type": "integer",
            "nullable": false,
            "isPrimaryKey": true
          },
          {
            "name": "email",
            "type": "varchar",
            "nullable": false,
            "isPrimaryKey": false
          }
        ],
        "rowCount": 100
      }
    ]
  }
}
```

### 4. 执行 SQL 查询

```bash
curl -X POST "http://localhost:8000/api/v1/dbs/mydb/query" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM users LIMIT 10"
  }'
```

响应示例:

```json
{
  "columns": ["id", "email", "created_at"],
  "rows": [
    [1, "user1@example.com", "2025-01-01T00:00:00"],
    [2, "user2@example.com", "2025-01-02T00:00:00"]
  ],
  "rowCount": 2
}
```

### 5. 自然语言转 SQL

```bash
curl -X POST "http://localhost:8000/api/v1/dbs/mydb/query/natural" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查询所有邮箱以 example.com 结尾的用户"
  }'
```

响应示例:

```json
{
  "sql": "SELECT * FROM users WHERE email LIKE '%@example.com' LIMIT 1000",
  "explanation": "从 users 表中筛选邮箱以 @example.com 结尾的用户"
}
```

### 6. 查询历史

```bash
curl -X GET "http://localhost:8000/api/v1/dbs/mydb/history?limit=10"
```

## 核心功能

### 1. 数据库连接管理

- 支持 PostgreSQL 和 MySQL 数据库
- 连接池管理 (asyncpg/aiomysql)
- 连接测试和验证
- 元数据缓存

### 2. 元数据提取

- 自动提取表结构信息
- 列信息 (名称、类型、是否可空、主键)
- 行数统计
- 支持元数据刷新

### 3. SQL 查询执行

- SQL 安全验证 (仅允许 SELECT)
- 自动添加 LIMIT 1000 (如果未指定)
- 查询历史记录
- 结果分页支持

### 4. 自然语言转 SQL

- 基于 OpenAI GPT
- 根据数据库元数据生成 SQL
- 支持中英文自然语言
- 自动添加查询限制

### 5. 结果导出

- CSV 格式导出
- JSON 格式导出
- 前端客户端导出实现

## 安全性

- SQL 注入防护: 使用 sqlglot 解析和验证 SQL
- 仅允许 SELECT 查询
- 自动添加 LIMIT 限制
- 环境变量管理敏感信息
- CORS 配置

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | 必填 |
| `DB_PATH` | SQLite 数据库路径 | `~/.db_query/db_query.db` |
| `API_HOST` | API 服务主机 | `0.0.0.0` |
| `API_PORT` | API 服务端口 | `8000` |

### Pydantic 配置

所有 API 响应使用 camelCase 格式 (JavaScript 约定):

```python
# app/models/__init__.py
from pydantic import BaseModel

def to_camel(string: str) -> str:
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])

class Config(BaseModel):
    alias_generator = to_camel
    populate_by_name = True
```

## 故障排查

### 1. 数据库连接失败

检查连接字符串格式:
- PostgreSQL: `postgresql://user:password@host:port/database`
- MySQL: `mysql://user:password@host:port/database`

### 2. OpenAI API 错误

确保 `OPENAI_API_KEY` 已正确设置并有效:

```bash
# 测试 API 密钥
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### 3. 迁移错误

如果迁移失败,可以重置数据库:

```bash
# 删除数据库文件
rm ~/.db_query/db_query.db

# 重新运行迁移
alembic upgrade head
```

## 性能优化

- 连接池复用: 避免频繁创建连接
- 元数据缓存: 减少重复查询信息库
- 查询限制: 默认 LIMIT 1000 防止大查询
- 异步处理: 所有数据库操作使用 async/await

## 相关文档

- [API 规范](../specs/001-db-query-tool/contracts/api-v1.yaml)
- [数据模型](../specs/001-db-query-tool/data-model.md)
- [快速开始](../specs/001-db-query-tool/quickstart.md)
- [前端 README](../frontend/README.md)

## License

MIT
