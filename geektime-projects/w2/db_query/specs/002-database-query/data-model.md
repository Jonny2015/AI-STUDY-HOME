# Data Model: Database Query Tool

**Feature**: Database Query Tool
**Date**: 2025-12-25
**Phase**: Phase 1 - Design & Contracts

## Overview

本文档定义 Database Query Tool 的所有数据模型，包括数据库存储模型（SQLite）和 API 请求/响应模型（Pydantic）。

---

## Storage Models (SQLite)

### Database: `db_query.db`

**Location**: `~/.db_query/db_query.db`

---

### Table: `databases`

存储数据库连接配置和状态信息。

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `name` | TEXT | PRIMARY KEY | 数据库连接的唯一名称（用户自定义） |
| `url` | TEXT | NOT NULL | 脱敏后的数据库连接字符串（密码部分替换为 `****`） |
| `db_type` | TEXT | NOT NULL | 数据库类型：`postgresql` \| `mysql` |
| `created_at` | TEXT | NOT NULL | 创建时间（ISO 8601 格式） |
| `last_connected_at` | TEXT | NULLABLE | 最后一次成功连接的时间（ISO 8601 格式） |

**Indexes**:
- None（主键查询，小规模数据无需额外索引）

**Validation Rules**:
- `name`: 非空，长度 1-100 字符，仅允许字母、数字、下划线、连字符
- `url`: 必须是有效的数据库连接 URL 格式（如 `postgresql://user:pass@host:port/db`）
- `db_type`: 必须是 `postgresql` 或 `mysql`
- `created_at`, `last_connected_at`: 必须是有效的 ISO 8601 日期时间字符串

**Example**:
```sql
INSERT INTO databases (name, url, db_type, created_at, last_connected_at)
VALUES (
  'prod_postgres',
  'postgresql://user:****@localhost:5432/mydb',
  'postgresql',
  '2025-12-25T10:30:00Z',
  '2025-12-25T12:00:00Z'
);
```

---

### Table: `metadata`

存储数据库表和视图的元数据信息。

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `db_name` | TEXT | NOT NULL, FOREIGN KEY | 关联的数据库名称（引用 `databases.name`） |
| `schema_name` | TEXT | NOT NULL | 模式名称（PostgreSQL 的 schema，MySQL 通常为数据库本身） |
| `table_name` | TEXT | NOT NULL | 表或视图的名称 |
| `table_type` | TEXT | NOT NULL | 类型：`table` \| `view` |
| `column_name` | TEXT | NOT NULL | 列名 |
| `data_type` | TEXT | NOT NULL | 数据类型（如 `integer`, `varchar(255)`, `timestamp`） |
| `is_nullable` | INTEGER | NOT NULL | 是否允许 NULL：1（允许） \| 0（不允许） |
| `is_primary_key` | INTEGER | NOT NULL | 是否是主键：1（是） \| 0（否） |
| `metadata_extracted_at` | TEXT | NOT NULL | 元数据提取时间（ISO 8601 格式） |

**Primary Key**:
```sql
PRIMARY KEY (db_name, schema_name, table_name, column_name)
```

**Foreign Key**:
```sql
FOREIGN KEY (db_name) REFERENCES databases(name) ON DELETE CASCADE
```

**Indexes**:
```sql
CREATE INDEX idx_metadata_db_name ON metadata(db_name);
CREATE INDEX idx_metadata_table_name ON metadata(table_name);
CREATE INDEX idx_metadata_schema_table ON metadata(schema_name, table_name);
```

**Validation Rules**:
- `db_name`: 必须存在于 `databases` 表中
- `schema_name`: 非空字符串
- `table_name`: 非空字符串
- `table_type`: 必须是 `table` 或 `view`
- `column_name`: 非空字符串
- `data_type`: 非空字符串，符合目标数据库的类型语法
- `is_nullable`, `is_primary_key`: 必须是 0 或 1
- `metadata_extracted_at`: 必须是有效的 ISO 8601 日期时间字符串

**Example**:
```sql
INSERT INTO metadata (
  db_name, schema_name, table_name, table_type,
  column_name, data_type, is_nullable, is_primary_key,
  metadata_extracted_at
) VALUES (
  'prod_postgres', 'public', 'users', 'table',
  'id', 'integer', 0, 1,
  '2025-12-25T12:00:00Z'
);
```

---

## API Models (Pydantic)

所有 API 模型使用 Pydantic V2 定义，响应模型自动转换为 camelCase JSON。

---

### Request Models

#### `AddDatabaseRequest`

添加数据库连接的请求。

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class AddDatabaseRequest(BaseModel):
    """添加数据库连接请求"""

    url: str = Field(
        ...,
        description="数据库连接字符串（如 postgresql://user:pass@host:port/db）",
        min_length=10,
        max_length=500,
    )

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """验证 URL 格式并检测数据库类型"""
        if not v.startswith(('postgresql://', 'mysql://', 'postgres://')):
            raise ValueError('仅支持 PostgreSQL 和 MySQL 连接字符串')
        return v
```

**Fields**:
- `url` (string, required): 数据库连接字符串

---

#### `ExecuteQueryRequest`

执行 SQL 查询的请求。

```python
class ExecuteQueryRequest(BaseModel):
    """执行 SQL 查询请求"""

    sql: str = Field(
        ...,
        description="要执行的 SELECT 查询语句",
        min_length=1,
        max_length=10000,
    )

    @field_validator('sql')
    @classmethod
    def strip_sql(cls, v: str) -> str:
        """去除前后空格"""
        return v.strip()
```

**Fields**:
- `sql` (string, required): SELECT 查询语句

---

#### `NaturalLanguageQueryRequest`

自然语言生成 SQL 的请求。

```python
class NaturalLanguageQueryRequest(BaseModel):
    """自然语言生成 SQL 请求"""

    prompt: str = Field(
        ...,
        description="自然语言查询描述",
        min_length=1,
        max_length=1000,
    )

    @field_validator('prompt')
    @classmethod
    def strip_prompt(cls, v: str) -> str:
        """去除前后空格"""
        return v.strip()
```

**Fields**:
- `prompt` (string, required): 自然语言查询描述

---

### Response Models

#### `DatabaseResponse`

数据库连接信息响应（camelCase）。

```python
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel_case
from datetime import datetime

class DatabaseResponse(BaseModel):
    """数据库连接响应"""

    model_config = ConfigDict(
        alias_generator=to_camel_case,
        populate_by_name=True,
    )

    database_name: str = Field(alias="databaseName", description="数据库名称")
    db_type: str = Field(alias="dbType", description="数据库类型")
    created_at: datetime = Field(alias="createdAt", description="创建时间")
    connection_status: str = Field(alias="connectionStatus", description="连接状态")
    last_connected_at: datetime | None = Field(
        default=None,
        alias="lastConnectedAt",
        description="最后连接时间",
    )
```

**Fields**:
- `databaseName` (string): 数据库连接名称
- `dbType` (string): 数据库类型（`postgresql` \| `mysql`）
- `createdAt` (string, ISO 8601): 创建时间
- `connectionStatus` (string): 连接状态（`connected` \| `failed` \| `pending`）
- `lastConnectedAt` (string \| null, ISO 8601): 最后连接时间

---

#### `DatabaseListResponse`

数据库列表响应。

```python
class DatabaseListResponse(BaseModel):
    """数据库列表响应"""

    model_config = ConfigDict(
        alias_generator=to_camel_case,
        populate_by_name=True,
    )

    databases: list[DatabaseResponse] = Field(
        alias="databases",
        description="数据库列表",
    )
    total_count: int = Field(
        alias="totalCount",
        description="总数",
    )
```

**Fields**:
- `databases` (array[DatabaseResponse]): 数据库列表
- `totalCount` (integer): 数据库总数

---

#### `ColumnMetadata`

列元数据。

```python
class ColumnMetadata(BaseModel):
    """列元数据"""

    model_config = ConfigDict(
        alias_generator=to_camel_case,
        populate_by_name=True,
    )

    column_name: str = Field(alias="columnName", description="列名")
    data_type: str = Field(alias="dataType", description="数据类型")
    is_nullable: bool = Field(alias="isNullable", description="是否允许 NULL")
    is_primary_key: bool = Field(alias="isPrimaryKey", description="是否是主键")
```

**Fields**:
- `columnName` (string): 列名
- `dataType` (string): 数据类型
- `isNullable` (boolean): 是否允许 NULL
- `isPrimaryKey` (boolean): 是否是主键

---

#### `TableMetadata`

表或视图元数据。

```python
class TableMetadata(BaseModel):
    """表或视图元数据"""

    model_config = ConfigDict(
        alias_generator=to_camel_case,
        populate_by_name=True,
    )

    schema_name: str = Field(alias="schemaName", description="模式名称")
    table_name: str = Field(alias="tableName", description="表名")
    table_type: str = Field(alias="tableType", description="类型（table/view）")
    columns: list[ColumnMetadata] = Field(alias="columns", description="列列表")
```

**Fields**:
- `schemaName` (string): 模式名称
- `tableName` (string): 表名
- `tableType` (string): 类型（`table` \| `view`）
- `columns` (array[ColumnMetadata]): 列列表

---

#### `DatabaseMetadataResponse`

数据库元数据响应。

```python
class DatabaseMetadataResponse(BaseModel):
    """数据库元数据响应"""

    model_config = ConfigDict(
        alias_generator=to_camel_case,
        populate_by_name=True,
    )

    database_name: str = Field(alias="databaseName", description="数据库名称")
    db_type: str = Field(alias="dbType", description="数据库类型")
    tables: list[TableMetadata] = Field(alias="tables", description="表和视图列表")
    metadata_extracted_at: datetime = Field(
        alias="metadataExtractedAt",
        description="元数据提取时间",
    )
```

**Fields**:
- `databaseName` (string): 数据库名称
- `dbType` (string): 数据库类型
- `tables` (array[TableMetadata]): 表和视图列表
- `metadataExtractedAt` (string, ISO 8601): 元数据提取时间

---

#### `QueryResult`

查询结果。

```python
class QueryResult(BaseModel):
    """查询结果"""

    model_config = ConfigDict(
        alias_generator=to_camel_case,
        populate_by_name=True,
    )

    columns: list[str] = Field(alias="columns", description="列名列表")
    rows: list[dict[str, Any]] = Field(alias="rows", description="数据行")
    row_count: int = Field(alias="rowCount", description="行数")
    execution_time_ms: int = Field(alias="executionTimeMs", description="执行时间（毫秒）")
```

**Fields**:
- `columns` (array[string]): 列名列表
- `rows` (array[object]): 数据行（对象数组，键为列名）
- `rowCount` (integer): 行数
- `executionTimeMs` (integer): 执行时间（毫秒）

**Example**:
```json
{
  "columns": ["id", "name", "email"],
  "rows": [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"}
  ],
  "rowCount": 2,
  "executionTimeMs": 45
}
```

---

#### `GeneratedSQLResponse`

生成的 SQL 响应。

```python
class GeneratedSQLResponse(BaseModel):
    """生成的 SQL 响应"""

    model_config = ConfigDict(
        alias_generator=to_camel_case,
        populate_by_name=True,
    )

    sql: str = Field(description="生成的 SQL 查询语句")
    explanation: str | None = Field(
        default=None,
        description="SQL 解释（可选）",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="警告信息",
    )
```

**Fields**:
- `sql` (string): 生成的 SQL 查询语句
- `explanation` (string \| null): SQL 解释
- `warnings` (array[string]): 警告信息

---

#### `ErrorResponse`

错误响应。

```python
class ErrorResponse(BaseModel):
    """错误响应"""

    model_config = ConfigDict(
        alias_generator=to_camel_case,
        populate_by_name=True,
    )

    error: str = Field(description="错误类型")
    message: str = Field(description="错误消息")
    details: dict[str, Any] | None = Field(
        default=None,
        description="错误详情（可选）",
    )
```

**Fields**:
- `error` (string): 错误类型
- `message` (string): 错误消息
- `details` (object \| null): 错误详情

---

## Entity Relationships

```mermaid
erDiagram
    DATABASES ||--o{ METADATA : contains
    DATABASES {
        string name PK
        string url
        string db_type
        datetime created_at
        datetime last_connected_at
    }
    METADATA {
        string db_name FK
        string schema_name
        string table_name
        string table_type
        string column_name
        string data_type
        boolean is_nullable
        boolean is_primary_key
        datetime metadata_extracted_at
    }
```

---

## State Transitions

### Database Connection Status

```mermaid
stateDiagram-v2
    [*] --> Pending: 创建数据库连接
    Pending --> Connected: 连接成功
    Pending --> Failed: 连接失败
    Connected --> Failed: 后续连接失败
    Failed --> Connected: 重新连接成功
    Connected --> [*]: 删除数据库
    Failed --> [*]: 删除数据库
```

**States**:
- `pending`: 刚创建，尚未验证连接
- `connected`: 连接验证成功
- `failed`: 连接验证失败

**Transitions**:
- 创建 → `pending`（初始状态）
- `pending` → `connected`（首次连接成功）
- `pending` → `failed`（首次连接失败）
- `connected` → `failed`（后续连接失败）
- `failed` → `connected`（重新连接成功）
- 任意状态 → `*`（删除数据库）

---

## Data Validation

### URL Validation

数据库连接 URL 必须符合以下格式：

**PostgreSQL**:
```
postgresql://[user[:password]@][host][:port][/database][?parameters]
postgres://[user[:password]@][host][:port][/database][?parameters]
```

**MySQL**:
```
mysql://[user[:password]@][host][:port][/database][?parameters]
```

**Validation Steps**:
1. 检查协议头（`postgresql://`, `postgres://`, `mysql://`）
2. 使用 `sqlglot` 或 `urllib.parse` 解析 URL
3. 尝试建立连接验证有效性
4. 提取数据库类型（`postgresql` 或 `mysql`）

---

### SQL Validation

SQL 查询必须满足以下条件：

1. **仅允许 SELECT 语句**:
   - 拒绝 `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER` 等
   - 使用 `sqlglot` 解析 SQL 类型

2. **自动添加 LIMIT**:
   - 如果 SQL 不包含 `LIMIT` 子句，自动添加 `LIMIT 1000`
   - 用户可以手动指定更大的 LIMIT

3. **语法验证**:
   - 使用 `sqlglot` 验证 SQL 语法
   - 返回详细的错误位置和原因

---

## Summary

数据模型定义完成，包括：

- **Storage Models**: SQLite 数据库表结构（`databases`, `metadata`）
- **API Models**: Pydantic 请求/响应模型（自动 camelCase 转换）
- **Entity Relationships**: 一对多关系（database → metadata）
- **State Transitions**: 数据库连接状态流转
- **Data Validation**: URL 和 SQL 验证规则

**Next Steps**:
- 生成 API 契约（contracts/openapi.yaml）
- 编写快速入门（quickstart.md）
- 更新 agent 上下文
