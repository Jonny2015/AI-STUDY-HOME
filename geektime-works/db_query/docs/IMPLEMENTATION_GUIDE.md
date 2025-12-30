# 实现指南：架构重设计

## 概述

本指南提供了实现新架构的分步说明。实现设计为增量式且非破坏性的。

## 前提条件

- 了解当前代码库
- 熟悉 Python 异步编程
- 了解 ABC（抽象基类）
- 理解依赖注入模式

## 实现阶段

### 阶段 1：创建适配器基础设施（第 1 周）

#### 任务 1.1：创建基础适配器模块

**文件**：`app/adapters/base.py`

```python
"""数据库适配器的基础类和数据结构。"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ConnectionConfig:
    """数据库连接配置。

    Attributes:
        url: 数据库连接 URL
        name: 连接标识符
        min_pool_size: 池中最小连接数
        max_pool_size: 池中最大连接数
        command_timeout: 命令超时时间（秒）
    """
    url: str
    name: str
    min_pool_size: int = 1
    max_pool_size: int = 5
    command_timeout: int = 60


@dataclass
class QueryResult:
    """标准化查询结果。

    Attributes:
        columns: 列定义列表，包含名称和 dataType
        rows: 行字典列表
        row_count: 返回的行数
    """
    columns: List[Dict[str, str]]
    rows: List[Dict[str, Any]]
    row_count: int

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典以供 API 响应使用。"""
        return {
            "columns": self.columns,
            "rows": self.rows,
            "rowCount": self.row_count,
        }


@dataclass
class MetadataResult:
    """标准化元数据结果。

    Attributes:
        tables: 表元数据字典列表
        views: 视图元数据字典列表
    """
    tables: List[Dict[str, Any]]
    views: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典以供 API 响应使用。"""
        return {
            "tables": self.tables,
            "views": self.views,
        }


class DatabaseAdapter(ABC):
    """数据库适配器的抽象基类。

    所有数据库实现必须继承此类并实现所有抽象方法。
    这确保了不同数据库类型之间的一致行为。

    适配器负责：
    - 连接管理（池化）
    - 查询执行
    - 元数据提取
    - 数据库特定的类型转换

    示例：
        class PostgreSQLAdapter(DatabaseAdapter):
            async def test_connection(self):
                # 实现
                pass
    """

    def __init__(self, config: ConnectionConfig):
        """使用连接配置初始化适配器。

        Args:
            config: 连接配置
        """
        self.config = config
        self._pool: Optional[Any] = None

    @abstractmethod
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """测试数据库连接。

        此方法应尝试连接到数据库并验证连接是否有效。

        Returns:
            (success, error_message) 元组
            - success: 连接成功返回 True，否则返回 False
            - error_message: 失败时返回错误消息，成功时返回 None

        示例：
            success, error = await adapter.test_connection()
            if not success:
                print(f"连接失败: {error}")
        """
        pass

    @abstractmethod
    async def get_connection_pool(self) -> Any:
        """获取或创建连接池。

        此方法应在首次调用时创建连接池，并在后续调用中返回缓存的池。

        Returns:
            数据库特定的连接池对象

        示例：
            pool = await adapter.get_connection_pool()
            async with pool.acquire() as conn:
                # 使用连接
        """
        pass

    @abstractmethod
    async def close_connection_pool(self) -> None:
        """关闭连接池并清理资源。

        此方法应关闭池中的所有连接并释放任何资源。

        示例：
            await adapter.close_connection_pool()
        """
        pass

    @abstractmethod
    async def extract_metadata(self) -> MetadataResult:
        """提取数据库元数据（表、列等）。

        此方法应查询数据库的元数据目录
        （例如 information_schema、pg_catalog）以获取架构信息。

        Returns:
            包含表和视图的 MetadataResult

        示例：
            metadata = await adapter.extract_metadata()
            for table in metadata.tables:
                print(f"表: {table['name']}")
        """
        pass

    @abstractmethod
    async def execute_query(self, sql: str) -> QueryResult:
        """执行 SQL 查询。

        此方法应执行给定的 SQL 查询并以标准化格式返回结果。

        Args:
            sql: SQL 查询字符串（已验证）

        Returns:
            包含列和行的 QueryResult

        Raises:
            Exception: 如果查询执行失败

        示例：
            result = await adapter.execute_query("SELECT * FROM users")
            for row in result.rows:
                print(row)
        """
        pass

    @abstractmethod
    def get_dialect_name(self) -> str:
        """获取此数据库的 SQL 方言名称（用于 sqlglot）。

        Returns:
            方言名称（例如 'postgres'、'mysql'、'oracle'）

        示例：
            dialect = adapter.get_dialect_name()  # 'postgres'
        """
        pass

    @abstractmethod
    def get_identifier_quote_char(self) -> str:
        """获取用于引用标识符的字符。

        Returns:
            引用字符（例如 PostgreSQL 使用 '"'，MySQL 使用 '`'）

        示例：
            quote = adapter.get_identifier_quote_char()  # '"'
            table_name = f'{quote}my_table{quote}'  # "my_table"
        """
        pass

    async def __aenter__(self):
        """上下文管理器入口。"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口 - 清理资源。"""
        await self.close_connection_pool()
```

**验证**：
```bash
# 测试模块可以被导入
python -c "from app.adapters.base import DatabaseAdapter, ConnectionConfig"
```

#### 任务 1.2：创建 PostgreSQL 适配器

**文件**：`app/adapters/postgresql.py`

从以下文件提取 PostgreSQL 特定逻辑：
- `app/services/db_connection.py` → 连接池管理
- `app/services/metadata.py` → 元数据提取 (extract_postgres_metadata)
- `app/services/query.py` → 查询执行（PostgreSQL 分支）

（完整的 PostgreSQL 适配器代码示例 - 参考原文档）

**验证**：
```bash
# 运行 pytest 进行适配器测试
pytest tests/adapters/test_postgresql.py -v
```

#### 任务 1.3：创建 MySQL 适配器

**文件**：`app/adapters/mysql.py`

类似于 PostgreSQL 适配器，从以下文件提取：
- `app/services/mysql_connection.py`
- `app/services/mysql_metadata.py`
- `app/services/mysql_query.py`

（完整的 MySQL 适配器代码示例 - 参考原文档）

#### 任务 1.4：创建适配器注册表

**文件**：`app/adapters/registry.py`

（完整的注册表代码示例 - 参考原文档）

**验证**：
```bash
python -c "from app.adapters.registry import adapter_registry; print(adapter_registry.get_supported_types())"
```

### 阶段 2：创建服务层（第 2 周）

#### 任务 2.1：创建数据库服务

**文件**：`app/services/database_service.py`

（完整的数据库服务代码示例 - 参考原文档）

**验证**：
```bash
pytest tests/services/test_database_service.py -v
```

### 阶段 3：更新 API 层（第 3 周）

#### 任务 3.1：更新查询 API

**文件**：`app/api/v1/queries.py`（修改）

（完整的 API 代码示例 - 参考原文档）

#### 任务 3.2：更新数据库 API

**文件**：`app/api/v1/databases.py`（修改）

更新以使用 `database_service` 代替 `connection_factory`。

### 阶段 4：测试（第 4 周）

#### 任务 4.1：单元测试

为每个适配器创建测试。

#### 任务 4.2：集成测试

创建服务层集成测试。

#### 任务 4.3：契约测试

确保所有适配器实现契约。

### 阶段 5：清理和文档（第 5 周）

#### 任务 5.1：删除旧代码

所有测试通过后：

1. 删除旧的服务文件：
```bash
rm app/services/connection_factory.py
rm app/services/db_connection.py
rm app/services/mysql_connection.py
rm app/services/mysql_metadata.py
rm app/services/mysql_query.py
```

2. 更新整个代码库中的导入

#### 任务 5.2：更新文档

更新：
- README.md
- API 文档
- 创建 ADAPTER_DEVELOPMENT_GUIDE.md

## 回滚策略

如果实施过程中出现问题：

1. **阶段 1-2**：直接删除 `app/adapters/` 目录
2. **阶段 3**：恢复 API 更改（git revert）
3. **阶段 4**：无需回滚（测试不影响生产）
4. **阶段 5**：从 git 恢复删除的文件

## 部署期间的监控

监控以下指标：
- 响应时间（不应增加）
- 错误率（不应增加）
- 连接池利用率
- 内存使用（应略有减少，因为重复更少）

## 成功标准

- 所有现有测试通过
- 新适配器测试覆盖率达 90%+
- API 响应时间在基线的 5% 以内
- 错误率没有增加
- 文档已更新

## 时间表

- 第 1 周：适配器基础设施
- 第 2 周：服务层
- 第 3 周：API 更新
- 第 4 周：测试
- 第 5 周：清理和文档

**总计：5 周完成完整迁移**
