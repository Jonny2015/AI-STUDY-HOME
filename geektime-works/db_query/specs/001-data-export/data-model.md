# Data Model: 数据导出功能模块

**Feature**: 数据导出功能模块
**Branch**: `001-data-export`
**Date**: 2025-12-28

## Overview

本文档定义了数据导出功能模块的数据模型,包括实体定义、字段说明、验证规则和关系映射。

---

## Entity Definitions

### 1. ExportTask (导出任务)

跟踪导出操作的执行状态和进度信息。

**Table Name**: `exporttasks`

**Fields**:

| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | 主键 |
| task_id | String(36) | Unique, Not Null | UUID 格式的任务唯一标识 |
| user_id | String(255) | Not Null, Indexed | 用户标识符 (从认证中获取) |
| database_name | String(255) | Not Null, FK, Indexed | 数据库连接名称 (外键到 `databaseconnections.name`) |
| sql_text | Text | Not Null | 执行的 SQL 查询语句 |
| export_format | String(10) | Not Null | 导出格式: `csv`, `json`, `markdown` |
| export_scope | String(20) | Not Null | 导出范围: `current_page`, `all_data` |
| file_name | String(255) | Nullable | 生成的文件名 (格式: `export-<uuid>.<ext>`) |
| file_path | String(500) | Nullable | 服务器端文件存储路径 |
| file_size_bytes | Integer | Nullable | 实际生成的文件大小 (字节) |
| row_count | Integer | Nullable | 实际导出的行数 |
| status | String(20) | Not Null, Indexed | 任务状态: `pending`, `running`, `completed`, `failed`, `cancelled` |
| progress | Integer | Not Null, Default=0 | 进度百分比 (0-100) |
| error_message | Text | Nullable | 失败时的错误信息 |
| started_at | DateTime | Nullable, Indexed | 任务开始时间 |
| completed_at | DateTime | Nullable | 任务完成/失败/取消时间 |
| execution_time_ms | Integer | Nullable | 执行时长 (毫秒) |
| created_at | DateTime | Not Null, Default=NOW | 任务创建时间 |

**Validation Rules**:
- `task_id`: 必须是有效的 UUID 格式
- `export_format`: 必须是 `csv`, `json`, `markdown` 之一
- `export_scope`: 必须是 `current_page`, `all_data` 之一
- `status`: 必须是 `pending`, `running`, `completed`, `failed`, `cancelled` 之一
- `progress`: 必须在 0-100 之间
- `file_size_bytes`: 不能超过 100MB (104,857,600 字节)

**Indexes**:
- `idx_exporttasks_user_id`: 加速用户任务查询
- `idx_exporttasks_database_name`: 加速数据库导出历史查询
- `idx_exporttasks_status`: 加速任务状态过滤
- `idx_exporttasks_created_at`: 加速时间范围查询

**Relationships**:
- `many-to-one` with `DatabaseConnection`: 多个导出任务属于一个数据库连接

**State Transitions**:

```
pending → running → completed
                  → failed
                  → cancelled (用户取消)
```

---

### 2. ExportHistory (导出历史记录)

记录已完成的导出操作,用于审计和历史查询。**注意**: 这是一个可选实体,如果不需要持久化历史,可以仅使用 `ExportTask`。

**Table Name**: `exporthistory`

**Fields**:

| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | 主键 |
| database_name | String(255) | Not Null, FK, Indexed | 数据库连接名称 |
| sql_text | Text | Not Null | 执行的 SQL 查询语句 |
| export_format | String(10) | Not Null | 导出格式 |
| export_scope | String(20) | Not Null | 导出范围 |
| file_name | String(255) | Not Null | 导出的文件名 |
| file_size_bytes | Integer | Not Null | 文件大小 (字节) |
| row_count | Integer | Not Null | 导出的行数 |
| column_names | Text | Nullable | 导出的列名 (JSON 数组格式) |
| execution_time_ms | Integer | Nullable | 执行时长 (毫秒) |
| user_id | String(255) | Not Null, Indexed | 用户标识符 |
| ip_address | String(45) | Nullable | 客户端 IP 地址 (用于审计) |
| created_at | DateTime | Not Null, Default=NOW, Indexed | 导出时间戳 |

**Validation Rules**:
- `file_size_bytes`: 必须 > 0 且 ≤ 100MB
- `row_count`: 必须 ≥ 0

**Indexes**:
- `idx_exporthistory_user_id`: 用户导出历史
- `idx_exporthistory_database_name`: 数据库导出历史
- `idx_exporthistory_created_at`: 时间范围查询

---

### 3. AISuggestionAnalytics (AI 建议分析)

记录 AI 导出建议和用户响应,用于分析 AI 助手效果。

**Table Name**: `aisuggestionanalytics`

**Fields**:

| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | Integer | PK, Auto-increment | 主键 |
| suggestion_id | String(36) | Not Null, Unique | 建议唯一标识 (UUID) |
| database_name | String(255) | Not Null, Indexed | 数据库连接名称 |
| suggestion_type | String(50) | Not Null | 建议类型: `export_intent`, `export_sql`, `proactive` |
| sql_context | Text | Nullable | SQL 查询上下文 |
| row_count | Integer | Nullable | 查询返回的行数 |
| confidence | String(10) | Nullable | AI 置信度: `high`, `medium`, `low` |
| suggested_format | String(10) | Nullable | 建议的导出格式 |
| suggested_scope | String(20) | Nullable | 建议的导出范围 |
| user_response | String(20) | Not Null, Indexed | 用户响应: `accepted`, `rejected`, `ignored`, `modified` |
| response_time_ms | Integer | Nullable | 用户响应时间 (毫秒,从建议显示到用户操作) |
| suggested_at | DateTime | Not Null, Default=NOW, Indexed | 建议生成时间 |
| responded_at | DateTime | Nullable | 用户响应时间 |

**Validation Rules**:
- `user_response`: 必须是 `accepted`, `rejected`, `ignored`, `modified` 之一
- `confidence`: 必须是 `high`, `medium`, `low` 之一

**Indexes**:
- `idx_aisuggestionanalytics_user_response`: 加速接受率统计
- `idx_aisuggestionanalytics_suggested_at`: 时间范围分析

---

## Relationships

```
┌─────────────────────┐
│ DatabaseConnection  │
│  - name (PK)        │
│  - db_type          │
│  - url              │
└─────────────────────┘
           │
           │ 1:N
           ▼
┌─────────────────────┐         ┌──────────────────────┐
│    ExportTask       │         │  ExportHistory       │
│  - id (PK)          │────────>│  (归档历史,可选)      │
│  - task_id (UUID)   │         │  - id (PK)           │
│  - user_id          │         │  - file_name         │
│  - database_name    │         └──────────────────────┘
│  - status           │
│  - progress         │
└─────────────────────┘
           │
           │ (AI 建议)
           ▼
┌─────────────────────┐
│ AISuggestionAnalytics│
│  - id (PK)          │
│  - suggestion_id    │
│  - user_response    │
└─────────────────────┘
```

---

## Entity States

### ExportTask Status States

| Status | Description | Next States | Entry Conditions |
|--------|-------------|-------------|------------------|
| `pending` | 任务已创建,等待执行 | `running`, `cancelled` | 任务创建成功,通过并发检查 |
| `running` | 任务正在执行 | `completed`, `failed`, `cancelled` | Worker 开始处理任务 |
| `completed` | 任务成功完成 | - | 导出文件生成成功,无错误 |
| `failed` | 任务执行失败 | - | 导出过程中发生错误 |
| `cancelled` | 任务被用户取消 | - | 用户主动取消或系统取消 |

### Progress Calculation

```
progress = (已导出行数 / 总行数) * 100

特殊值:
- pending: 0
- running: 1-99
- completed: 100
- failed/ cancelled: 当前进度 (保持不变)
```

---

## Validation Examples

### Example 1: 创建导出任务

```python
from sqlmodel import SQLModel, Field, Session
from datetime import datetime, timezone
from enum import Enum
import uuid

class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"
    MARKDOWN = "markdown"

class ExportScope(str, Enum):
    CURRENT_PAGE = "current_page"
    ALL_DATA = "all_data"

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExportTask(SQLModel, table=True):
    __tablename__ = "exporttasks"

    id: int | None = Field(default=None, primary_key=True)
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    user_id: str = Field(index=True)
    database_name: str = Field(foreign_key="databaseconnections.name", index=True)
    sql_text: str = Field(sa_column=Column(Text))
    export_format: ExportFormat
    export_scope: ExportScope
    file_name: str | None = None
    file_path: str | None = None
    file_size_bytes: int | None = Field(default=None, le=104857600)  # 100MB limit
    row_count: int | None = None
    status: TaskStatus = Field(default=TaskStatus.PENDING, index=True)
    progress: int = Field(default=0, ge=0, le=100)
    error_message: str | None = None
    started_at: datetime | None = Field(default=None, index=True)
    completed_at: datetime | None = None
    execution_time_ms: int | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime(timezone=False), index=True)
    )

# 创建新任务
task = ExportTask(
    user_id="user-123",
    database_name="postgres_db",
    sql_text="SELECT * FROM users LIMIT 1000",
    export_format=ExportFormat.CSV,
    export_scope=ExportScope.CURRENT_PAGE
)
```

### Example 2: 验证文件大小限制

```python
from pydantic import BaseModel, Field, validator

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

class ExportCheckRequest(BaseModel):
    sql: str
    format: ExportFormat
    estimated_size_bytes: int = Field(..., ge=0)

    @validator('estimated_size_bytes')
    def check_file_size(cls, v):
        if v > MAX_FILE_SIZE:
            raise ValueError(f"Estimated file size ({v / 1024 / 1024:.1f}MB) exceeds limit (100MB)")
        return v
```

### Example 3: AI 建议响应追踪

```python
class ExportSuggestionResponse(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IGNORED = "ignored"
    MODIFIED = "modified"

class AISuggestionAnalytics(SQLModel, table=True):
    __tablename__ = "aisuggestionanalytics"

    id: int | None = Field(default=None, primary_key=True)
    suggestion_id: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    database_name: str = Field(index=True)
    suggestion_type: str
    sql_context: str | None = Field(sa_column=Column(Text))
    row_count: int | None = None
    confidence: str | None = None
    suggested_format: str | None = None
    suggested_scope: str | None = None
    user_response: ExportSuggestionResponse = Field(index=True)
    response_time_ms: int | None = None
    suggested_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    responded_at: datetime | None = None

    @property
    def is_accepted(self) -> bool:
        return self.user_response == ExportSuggestionResponse.ACCEPTED

# 记录用户响应
analytics = AISuggestionAnalytics(
    database_name="postgres_db",
    suggestion_type="export_intent",
    sql_context="SELECT * FROM users",
    row_count=1500,
    confidence="high",
    suggested_format="csv",
    user_response=ExportSuggestionResponse.ACCEPTED,
    response_time_ms=2500,  # 用户2.5秒后响应
    responded_at=datetime.utcnow()
)
```

---

## Database Migration Strategy

### Migration Steps

1. **Create `exporttasks` table**:
   ```sql
   CREATE TABLE exporttasks (
       id SERIAL PRIMARY KEY,
       task_id VARCHAR(36) UNIQUE NOT NULL,
       user_id VARCHAR(255) NOT NULL,
       database_name VARCHAR(255) NOT NULL REFERENCES databaseconnections(name),
       sql_text TEXT NOT NULL,
       export_format VARCHAR(10) NOT NULL,
       export_scope VARCHAR(20) NOT NULL,
       file_name VARCHAR(255),
       file_path VARCHAR(500),
       file_size_bytes INTEGER,
       row_count INTEGER,
       status VARCHAR(20) NOT NULL DEFAULT 'pending',
       progress INTEGER NOT NULL DEFAULT 0,
       error_message TEXT,
       started_at TIMESTAMP,
       completed_at TIMESTAMP,
       execution_time_ms INTEGER,
       created_at TIMESTAMP NOT NULL DEFAULT NOW()
   );

   CREATE INDEX idx_exporttasks_user_id ON exporttasks(user_id);
   CREATE INDEX idx_exporttasks_database_name ON exporttasks(database_name);
   CREATE INDEX idx_exporttasks_status ON exporttasks(status);
   CREATE INDEX idx_exporttasks_created_at ON exporttasks(created_at);
   ```

2. **Create `exporthistory` table** (可选):
   ```sql
   CREATE TABLE exporthistory (
       id SERIAL PRIMARY KEY,
       database_name VARCHAR(255) NOT NULL REFERENCES databaseconnections(name),
       sql_text TEXT NOT NULL,
       export_format VARCHAR(10) NOT NULL,
       export_scope VARCHAR(20) NOT NULL,
       file_name VARCHAR(255) NOT NULL,
       file_size_bytes INTEGER NOT NULL,
       row_count INTEGER NOT NULL,
       column_names TEXT,
       execution_time_ms INTEGER,
       user_id VARCHAR(255) NOT NULL,
       ip_address VARCHAR(45),
       created_at TIMESTAMP NOT NULL DEFAULT NOW()
   );

   CREATE INDEX idx_exporthistory_user_id ON exporthistory(user_id);
   CREATE INDEX idx_exporthistory_database_name ON exporthistory(database_name);
   CREATE INDEX idx_exporthistory_created_at ON exporthistory(created_at);
   ```

3. **Create `aisuggestionanalytics` table**:
   ```sql
   CREATE TABLE aisuggestionanalytics (
       id SERIAL PRIMARY KEY,
       suggestion_id VARCHAR(36) UNIQUE NOT NULL,
       database_name VARCHAR(255) NOT NULL,
       suggestion_type VARCHAR(50) NOT NULL,
       sql_context TEXT,
       row_count INTEGER,
       confidence VARCHAR(10),
       suggested_format VARCHAR(10),
       suggested_scope VARCHAR(20),
       user_response VARCHAR(20) NOT NULL,
       response_time_ms INTEGER,
       suggested_at TIMESTAMP NOT NULL DEFAULT NOW(),
       responded_at TIMESTAMP
   );

   CREATE INDEX idx_aisuggestionanalytics_user_response ON aisuggestionanalytics(user_response);
   CREATE INDEX idx_aisuggestionanalytics_suggested_at ON aisuggestionanalytics(suggested_at);
   ```

---

## Data Retention Policy

### ExportTask
- **保留期**: 任务完成后 7 天自动清理
- **归档**: 已完成的任务可选择归档到 `exporthistory` 表
- **原因**: 任务表主要用于状态跟踪,不需要长期保留

### ExportHistory
- **保留期**: 永久保留 (或根据合规要求设定,如 90 天)
- **目的**: 审计日志、使用分析

### AISuggestionAnalytics
- **保留期**: 90 天
- **目的**: AI 效果分析,优化 prompt 和建议策略

---

## Summary

本数据模型定义了三个核心实体:

1. **ExportTask**: 导出任务的实时状态跟踪
2. **ExportHistory**: (可选) 已完成导出的归档历史
3. **AISuggestionAnalytics**: AI 建议的效果分析

**关键设计决策**:
- ✅ 使用 UUID 作为任务标识符,避免冲突
- ✅ 文件大小限制在模型层面强制验证 (≤100MB)
- ✅ 状态转换严格限制,防止非法状态
- ✅ 索引优化,加速常见查询场景
- ✅ 审计日志分离,支持不同的保留策略
