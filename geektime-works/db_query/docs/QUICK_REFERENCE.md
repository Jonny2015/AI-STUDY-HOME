# 快速参考：数据库适配器架构

## 添加新数据库支持（5步）

### 第1步：创建适配器
```python
# app/adapters/yourdb.py
from app.adapters.base import DatabaseAdapter, ConnectionConfig, QueryResult, MetadataResult

class YourDBAdapter(DatabaseAdapter):
    async def test_connection(self):
        # 测试连接，返回 (True, None) 或 (False, error_msg)
        pass

    async def get_connection_pool(self):
        # 创建并缓存连接池
        if self._pool is None:
            self._pool = await your_driver.create_pool(self.config.url)
        return self._pool

    async def close_connection_pool(self):
        # 关闭连接池
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def extract_metadata(self):
        # 查询数据库目录，返回 MetadataResult
        return MetadataResult(tables=[], views=[])

    async def execute_query(self, sql: str):
        # 执行 SQL，返回 QueryResult
        return QueryResult(columns=[], rows=[], row_count=0)

    def get_dialect_name(self):
        return "yourdb"  # 用于 SQL 验证

    def get_identifier_quote_char(self):
        return '"'  # 或 '`' 或 '['
```

### 第2步：添加数据库类型
```python
# app/models/database.py
class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    YOURDB = "yourdb"  # 添加这一行
```

### 第3步：注册适配器
```python
# app/adapters/registry.py
from app.adapters.yourdb import YourDBAdapter

class DatabaseAdapterRegistry:
    def __init__(self):
        # ... 现有代码 ...
        self.register(DatabaseType.YOURDB, YourDBAdapter)  # 添加这一行
```

### 第4步：更新 URL 解析器（可选）
```python
# app/utils/db_parser.py
def detect_database_type(url: str) -> DatabaseType:
    if url.startswith("yourdb://"):
        return DatabaseType.YOURDB
    # ... 其他数据库 ...
```

### 第5步：测试
```python
# tests/adapters/test_yourdb.py
@pytest.mark.asyncio
async def test_yourdb_adapter():
    config = ConnectionConfig(url="yourdb://localhost/test", name="test")
    adapter = YourDBAdapter(config)

    success, error = await adapter.test_connection()
    assert success or error is not None
```

## 常用模式

### 连接池管理
```python
async def get_connection_pool(self):
    if self._pool is None:
        # 创建一次，后续复用
        self._pool = await driver.create_pool(
            self.config.url,
            min_size=self.config.min_pool_size,
            max_size=self.config.max_pool_size,
        )
    return self._pool
```

### URL 解析
```python
from urllib.parse import urlparse

def _parse_url(self, url: str):
    parsed = urlparse(url)  # yourdb://user:pass@host:port/database
    return {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/'),
    }
```

### 元数据提取
```python
async def extract_metadata(self):
    pool = await self.get_connection_pool()

    async with pool.acquire() as conn:
        # 获取表
        tables = await self._get_tables(conn)
        # 获取视图
        views = await self._get_views(conn)

    return MetadataResult(tables=tables, views=views)

async def _get_tables(self, conn):
    rows = await conn.fetch("SELECT table_name FROM information_schema.tables")
    tables = []
    for row in rows:
        columns = await self._get_columns(conn, row['table_name'])
        tables.append({
            "name": row['table_name'],
            "type": "table",
            "schemaName": "public",
            "columns": columns,
        })
    return tables
```

### 查询执行
```python
async def execute_query(self, sql: str):
    pool = await self.get_connection_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql)

        # 从第一行提取列信息
        columns = []
        if rows:
            for key, value in rows[0].items():
                columns.append({
                    "name": key,
                    "dataType": self._infer_type(value)
                })

        # 转换行为字典列表
        result_rows = [dict(row) for row in rows]

        return QueryResult(
            columns=columns,
            rows=result_rows,
            row_count=len(result_rows)
        )
```

### 类型推断
```python
@staticmethod
def _infer_type(value):
    if value is None:
        return "unknown"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "numeric"
    elif isinstance(value, str):
        return "text"
    elif isinstance(value, datetime):
        return "timestamp"
    else:
        return str(type(value).__name__)
```

## 数据结构

### ConnectionConfig
```python
@dataclass
class ConnectionConfig:
    url: str              # 数据库连接 URL
    name: str             # 连接标识符
    min_pool_size: int = 1
    max_pool_size: int = 5
    command_timeout: int = 60
```

### QueryResult
```python
@dataclass
class QueryResult:
    columns: List[Dict[str, str]]    # [{"name": "id", "dataType": "integer"}]
    rows: List[Dict[str, Any]]       # [{"id": 1, "name": "Alice"}]
    row_count: int                    # 1
```

### MetadataResult
```python
@dataclass
class MetadataResult:
    tables: List[Dict[str, Any]]  # 表元数据
    views: List[Dict[str, Any]]   # 视图元数据

# 表结构:
{
    "name": "users",
    "type": "table",
    "schemaName": "public",
    "rowCount": 100,
    "columns": [
        {
            "name": "id",
            "dataType": "integer",
            "nullable": False,
            "primaryKey": True,
            "unique": False,
            "defaultValue": None
        }
    ]
}
```

## 使用服务

### 执行查询
```python
from app.services.database_service import database_service
from app.models.database import DatabaseType

result, time_ms = await database_service.execute_query(
    db_type=DatabaseType.POSTGRESQL,
    name="mydb",
    url="postgresql://localhost/mydb",
    sql="SELECT * FROM users",
    limit=1000
)

print(f"返回 {result.row_count} 行，耗时 {time_ms}ms")
for row in result.rows:
    print(row)
```

### 提取元数据
```python
metadata = await database_service.extract_metadata(
    db_type=DatabaseType.MYSQL,
    name="mydb",
    url="mysql://localhost/mydb"
)

print(f"表数量: {len(metadata.tables)}")
for table in metadata.tables:
    print(f"  {table['name']}: {len(table['columns'])} 列")
```

### 测试连接
```python
success, error = await database_service.test_connection(
    db_type=DatabaseType.POSTGRESQL,
    url="postgresql://localhost/test"
)

if success:
    print("连接成功！")
else:
    print(f"连接失败: {error}")
```

## 数据库特定示例

### PostgreSQL
```python
import asyncpg

async def get_connection_pool(self):
    if self._pool is None:
        self._pool = await asyncpg.create_pool(self.config.url)
    return self._pool

async def execute_query(self, sql):
    pool = await self.get_connection_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql)  # 返回 List[Record]
        return QueryResult(...)
```

### MySQL
```python
import aiomysql

async def get_connection_pool(self):
    if self._pool is None:
        params = self._parse_url(self.config.url)
        self._pool = await aiomysql.create_pool(**params)
    return self._pool

async def execute_query(self, sql):
    pool = await self.get_connection_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(sql)
            rows = await cursor.fetchall()  # 返回 List[Dict]
            return QueryResult(...)
```

### SQLite
```python
import aiosqlite

async def get_connection_pool(self):
    # SQLite 没有连接池，创建单个连接
    if self._pool is None:
        self._pool = await aiosqlite.connect(self.config.url)
    return self._pool

async def execute_query(self, sql):
    conn = await self.get_connection_pool()
    cursor = await conn.execute(sql)
    rows = await cursor.fetchall()  # 返回 List[Tuple]
    # 转换为字典列表...
    return QueryResult(...)
```

## 调试

### 启用日志
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('app.adapters')
```

### 检查已注册的适配器
```python
from app.adapters.registry import adapter_registry

print(adapter_registry.get_supported_types())
# [DatabaseType.POSTGRESQL, DatabaseType.MYSQL, ...]
```

### 直接测试适配器
```python
from app.adapters.postgresql import PostgreSQLAdapter
from app.adapters.base import ConnectionConfig

config = ConnectionConfig(url="postgresql://localhost/test", name="test")
adapter = PostgreSQLAdapter(config)

# 测试连接
success, error = await adapter.test_connection()
print(f"连接: {success}, 错误: {error}")

# 测试查询
result = await adapter.execute_query("SELECT 1 as num")
print(f"结果: {result.rows}")
```

## 常见问题

### 问题："不支持的数据库类型"
**原因**: 适配器未注册
**解决方法**: 添加到 `DatabaseAdapterRegistry.__init__()`
```python
self.register(DatabaseType.YOURDB, YourDBAdapter)
```

### 问题："连接池已关闭"
**原因**: 连接池过早关闭
**解决方法**: 确保连接池生命周期由注册表管理
```python
# 不要手动关闭连接池，让注册表处理
await adapter_registry.close_adapter(db_type, name)
```

### 问题："类型推断返回 unknown"
**原因**: 值为 None 或未处理的类型
**解决方法**: 在 `_infer_type()` 中添加类型映射
```python
elif isinstance(value, Decimal):
    return "decimal"
```

### 问题："元数据提取失败"
**原因**: 数据库目录查询不正确
**解决方法**: 检查数据库的 information schema 结构
```python
# PostgreSQL: information_schema.tables
# MySQL: INFORMATION_SCHEMA.TABLES
# Oracle: user_tables
# SQLite: sqlite_master
```

## 新适配器检查清单

- [ ] 实现所有 7 个抽象方法
- [ ] 优雅处理连接错误
- [ ] 管理连接池生命周期
- [ ] 提取元数据（表、视图、列）
- [ ] 执行查询并返回结果
- [ ] 返回正确的 SQL 方言名称
- [ ] 返回正确的标识符引号字符
- [ ] 添加单元测试（90%+ 覆盖率）
- [ ] 添加集成测试
- [ ] 通过契约测试
- [ ] 添加文档字符串
- [ ] 在注册表中注册
- [ ] 更新 DatabaseType 枚举
- [ ] 更新 URL 解析器（如需要）

## 相关资源

- **完整架构**: `ARCHITECTURE_REDESIGN.md`
- **实现指南**: `IMPLEMENTATION_GUIDE.md`
- **适配器指南**: `app/adapters/README.md`
- **架构总结**: `ARCHITECTURE_SUMMARY.md`
- **示例**: `app/adapters/postgresql.py`, `app/adapters/mysql.py`
