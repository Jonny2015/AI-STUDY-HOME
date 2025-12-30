# MySQL 支持文档

## 概述

db_query 后端现在同时支持 PostgreSQL 和 MySQL 数据库。系统会自动从连接 URL 检测数据库类型，并将操作路由到相应的服务。

## 连接 URL 格式

### PostgreSQL
```
postgresql://user:password@host:port/database
postgres://user:password@host:port/database
```

### MySQL
```
mysql://user:password@host:port/database
mysql+aiomysql://user:password@host:port/database
```

## 示例

### 连接到 MySQL

**示例：本地 MySQL 数据库**
```bash
curl -X PUT "http://localhost:8000/api/v1/dbs/my_todo_db" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "mysql://root@localhost:3306/todo_db",
    "description": "本地 MySQL 待办事项数据库"
  }'
```

**示例：带密码的远程 MySQL**
```bash
curl -X PUT "http://localhost:8000/api/v1/dbs/prod_db" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "mysql://user:password@db.example.com:3306/mydb",
    "dbType": "mysql",
    "description": "生产 MySQL 数据库"
  }'
```

### 数据库类型检测

系统会自动从 URL scheme 检测数据库类型：
- `postgresql://` 或 `postgres://` → PostgreSQL
- `mysql://` 或 `mysql+aiomysql://` → MySQL

你也可以显式指定 `dbType` 参数（可选）：
```json
{
  "url": "mysql://root@localhost:3306/todo_db",
  "dbType": "mysql"
}
```

## 功能

### 1. 元数据提取

MySQL 元数据提取包括：
- 所有用户架构的表和视图
- 列信息（名称、数据类型、可空、主键、唯一）
- 表的行数
- 架构信息

**示例：获取 MySQL 元数据**
```bash
curl "http://localhost:8000/api/v1/dbs/my_todo_db"
```

### 2. SQL 查询执行

对 MySQL 数据库执行 SQL SELECT 查询：

**示例：查询 MySQL 数据库**
```bash
curl -X POST "http://localhost:8000/api/v1/dbs/my_todo_db/query" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM todos WHERE completed = 0"
  }'
```

**MySQL 特定语法支持：**
- 反引号标识符：`` `table_name` ``, `` `column_name` ``
- MySQL 数据类型：INT、VARCHAR、DATETIME 等
- MySQL LIMIT 语法：`LIMIT 10`

### 3. 自然语言转 SQL

从自然语言生成 MySQL 特定的 SQL：

**示例：中文提示**
```bash
curl -X POST "http://localhost:8000/api/v1/dbs/my_todo_db/query/natural" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "查询所有未完成的待办事项"
  }'
```

**示例：英文提示**
```bash
curl -X POST "http://localhost:8000/api/v1/dbs/my_todo_db/query/natural" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Find all incomplete todo items"
  }'
```

生成的 SQL 将使用 MySQL 特定语法：
```sql
SELECT * FROM `todos` WHERE `completed` = 0 LIMIT 1000
```

## 技术实现

### 架构

实现使用工厂模式来路由操作：

1. **连接工厂** (`app/services/connection_factory.py`)
   - 基于 `db_type` 路由连接操作
   - 为 PostgreSQL 和 MySQL 管理连接池

2. **元数据工厂** (`app/services/metadata.py`)
   - 将元数据提取路由到相应的服务
   - 在 SQLite 中缓存元数据

3. **查询工厂** (`app/services/query.py`)
   - 基于数据库类型路由查询执行
   - 使用适当的方言（postgres/mysql）验证 SQL

### 依赖

- **aiomysql**：异步 MySQL 驱动（类似于 PostgreSQL 的 asyncpg）
- **PyMySQL**：纯 Python MySQL 客户端库
- **sqlglot**：支持多种方言的 SQL 解析器

## PostgreSQL 和 MySQL 的区别

### 标识符
- **PostgreSQL**：双引号 `"table_name"`
- **MySQL**：反引号 `` `table_name` ``

### 数据类型
- **PostgreSQL**：`character varying`、`serial`、`timestamp with time zone`
- **MySQL**：`VARCHAR`、`AUTO_INCREMENT`、`DATETIME`

### 架构限定
- **PostgreSQL**：`schema.table`（多个架构很常见）
- **MySQL**：`database.table`（通常单个数据库）

## 查询历史

所有查询（手动和 NL2SQL）都保存到查询历史中，包含数据库类型：
```bash
curl "http://localhost:8000/api/v1/dbs/my_todo_db/history"
```

## 错误处理

MySQL 特定的错误得到了正确处理：
- 连接超时
- 身份验证失败
- 无效语法
- 权限错误

## 测试

### 使用你的 `todo_db` 进行手动测试

**1. 创建连接：**
```bash
curl -X PUT "http://localhost:8000/api/v1/dbs/todo_db" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "mysql://root@localhost:3306/todo_db",
    "description": "测试 MySQL 数据库"
  }'
```

**2. 获取元数据：**
```bash
curl "http://localhost:8000/api/v1/dbs/todo_db"
```

**3. 执行查询：**
```bash
curl -X POST "http://localhost:8000/api/v1/dbs/todo_db/query" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM todos LIMIT 10"
  }'
```

**4. 自然语言查询：**
```bash
curl -X POST "http://localhost:8000/api/v1/dbs/todo_db/query/natural" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "获取所有待办事项"
  }'
```

## 迁移说明

### 现有的 PostgreSQL 连接

现有的 PostgreSQL 连接将继续工作，无需任何更改。`db_type` 字段默认为 `postgresql` 以实现向后兼容。

### 数据库架构更改

`DatabaseConnection` 模型现在包含 `db_type` 字段：
```python
class DatabaseConnection(SQLModel, table=True):
    name: str
    url: str
    db_type: DatabaseType = Field(default=DatabaseType.POSTGRESQL)
    description: str | None
    ...
```

SQLModel 将在应用启动时自动处理架构迁移。

## 故障排查

### 连接问题

**问题**：无法连接到 MySQL
```
Connection test failed: Can't connect to MySQL server
```

**解决方案**：
1. 验证 MySQL 正在运行：`mysql -u root -p`
2. 检查主机/端口：使用 `localhost` 或 `127.0.0.1`
3. 验证连接 URL 中的凭据
4. 检查 MySQL 是否允许远程连接（如果需要）

### 元数据提取问题

**问题**：返回空元数据
```json
{"tables": [], "views": []}
```

**解决方案**：
1. 验证数据库存在：`SHOW DATABASES;`
2. 检查用户权限：`SHOW GRANTS;`
3. 确保表存在：`SHOW TABLES;`

### 查询执行问题

**问题**：SQL 语法错误
```
SQL parse error: ...
```

**解决方案**：
1. 使用 MySQL 特定语法（标识符使用反引号）
2. 先使用 `mysql` CLI 验证查询
3. 检查是否包含 LIMIT 子句（如果缺失则自动添加）

## API 更改

### 请求架构

`DatabaseConnectionInput` schema 现在支持可选的 `dbType`：

```typescript
{
  url: string;                    // 数据库连接 URL
  dbType?: "postgresql" | "mysql"; // 可选，从 URL 自动检测
  description?: string;            // 可选描述
}
```

### 响应架构

`DatabaseConnectionResponse` schema 现在包含 `dbType`：

```typescript
{
  name: string;
  url: string;
  dbType: "postgresql" | "mysql"; // 数据库类型
  description: string | null;
  createdAt: string;
  updatedAt: string;
  lastConnectedAt: string | null;
  status: string;
}
```

## 性能考虑

### 连接池

PostgreSQL 和 MySQL 连接都使用连接池：
- **最小池大小**：1
- **最大池大小**：5
- **命令超时**：60 秒（PostgreSQL）

### 元数据缓存

元数据在 SQLite 中缓存 24 小时（可通过 `metadata_cache_hours` 设置配置）。

### 查询限制

所有查询自动限制为 1000 行，以防止性能问题。
