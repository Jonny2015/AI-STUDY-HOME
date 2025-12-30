# 类图和关系

## UML 类图

```
┌─────────────────────────────────────────────────────────────────┐
│                        <<接口>>                                 │
│                      DatabaseAdapter                             │
├─────────────────────────────────────────────────────────────────┤
│ # config: ConnectionConfig                                       │
│ # _pool: Optional[Any]                                           │
├─────────────────────────────────────────────────────────────────┤
│ + __init__(config: ConnectionConfig)                             │
│ + test_connection(): Tuple[bool, Optional[str]]                  │
│ + get_connection_pool(): Any                                     │
│ + close_connection_pool(): None                                  │
│ + extract_metadata(): MetadataResult                             │
│ + execute_query(sql: str): QueryResult                           │
│ + get_dialect_name(): str                                        │
│ + get_identifier_quote_char(): str                               │
└─────────────────────────────────────────────────────────────────┘
                               △
                               │ 实现
                ┌──────────────┼──────────────┐
                │              │              │
┌───────────────┴────────┐ ┌──┴────────────┐ ┌┴──────────────────┐
│  PostgreSQLAdapter     │ │  MySQLAdapter │ │  OracleAdapter    │
├────────────────────────┤ ├───────────────┤ ├───────────────────┤
│ - _pool: asyncpg.Pool  │ │ - _pool: Pool │ │ - _pool: Pool     │
├────────────────────────┤ ├───────────────┤ ├───────────────────┤
│ + 所有抽象方法         │ │ + 所有方法    │ │ + 所有方法        │
│ - _parse_url()         │ │ - _parse_url()│ │ - _parse_url()    │
│ - _get_columns()       │ │ - _get_tables()│ │ - _extract_meta() │
│ - _get_row_count()     │ │ - _map_type() │ │ - _map_type()     │
│ - _infer_type()        │ │ - _infer_type()│ │ - _infer_type()   │
└────────────────────────┘ └───────────────┘ └───────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│               DatabaseAdapterRegistry                            │
├─────────────────────────────────────────────────────────────────┤
│ - _adapters: Dict[DatabaseType, Type[DatabaseAdapter]]          │
│ - _instances: Dict[str, DatabaseAdapter]                        │
├─────────────────────────────────────────────────────────────────┤
│ + __init__()                                                     │
│ + register(type, adapter_class): None                            │
│ + get_adapter(type, config): DatabaseAdapter                    │
│ + close_adapter(type, name): None                               │
│ + close_all_adapters(): None                                    │
│ + is_supported(type): bool                                       │
│ + get_supported_types(): List[DatabaseType]                     │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ 创建和管理
                               ▼
                       DatabaseAdapter


┌─────────────────────────────────────────────────────────────────┐
│                    DatabaseService                               │
├─────────────────────────────────────────────────────────────────┤
│ - registry: DatabaseAdapterRegistry                              │
├─────────────────────────────────────────────────────────────────┤
│ + __init__(registry: DatabaseAdapterRegistry)                    │
│ + test_connection(type, url): Tuple[bool, str]                  │
│ + execute_query(type, name, url, sql): Tuple[Result, int]       │
│ + extract_metadata(type, name, url): MetadataResult             │
│ + close_connection(type, name): None                            │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ 使用
                               ▼
                  DatabaseAdapterRegistry


┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI 路由                              │
│                    (queries.py, databases.py)                    │
├─────────────────────────────────────────────────────────────────┤
│ + POST   /api/v1/dbs/{name}/query                               │
│ + POST   /api/v1/dbs/{name}/query/natural                       │
│ + GET    /api/v1/dbs/{name}/history                             │
│ + GET    /api/v1/dbs/{name}                                     │
│ + POST   /api/v1/dbs/{name}/refresh                             │
│ + PUT    /api/v1/dbs/{name}                                     │
│ + DELETE /api/v1/dbs/{name}                                     │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ 依赖
                               ▼
                       DatabaseService
```

## 数据类

```
┌─────────────────────────────────────────────────────────────────┐
│                      ConnectionConfig                            │
├─────────────────────────────────────────────────────────────────┤
│ + url: str                                                       │
│ + name: str                                                      │
│ + min_pool_size: int = 1                                         │
│ + max_pool_size: int = 5                                         │
│ + command_timeout: int = 60                                      │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                        QueryResult                               │
├─────────────────────────────────────────────────────────────────┤
│ + columns: List[Dict[str, str]]                                  │
│ + rows: List[Dict[str, Any]]                                     │
│ + row_count: int                                                 │
├─────────────────────────────────────────────────────────────────┤
│ + to_dict(): Dict[str, Any]                                      │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                      MetadataResult                              │
├─────────────────────────────────────────────────────────────────┤
│ + tables: List[Dict[str, Any]]                                   │
│ + views: List[Dict[str, Any]]                                    │
├─────────────────────────────────────────────────────────────────┤
│ + to_dict(): Dict[str, Any]                                      │
└─────────────────────────────────────────────────────────────────┘
```

## 序列图

### 查询执行流程

```
客户端          API 路由      数据库服务      注册表         适配器
  │                 │                  │               │               │
  │  POST /query    │                  │               │               │
  ├────────────────>│                  │               │               │
  │                 │                  │               │               │
  │                 │ execute_query()  │               │               │
  │                 ├─────────────────>│               │               │
  │                 │                  │               │               │
  │                 │                  │ get_adapter() │               │
  │                 │                  ├──────────────>│               │
  │                 │                  │               │               │
  │                 │                  │               │ [如不存在则  │
  │                 │                  │               │   创建]       │
  │                 │                  │               │               │
  │                 │                  │<──────────────┤               │
  │                 │                  │  adapter      │               │
  │                 │                  │               │               │
  │                 │                  │ validate_sql()│               │
  │                 │                  ├───────────────┼──────────────>│
  │                 │                  │               │               │
  │                 │                  │ execute_query(sql)            │
  │                 │                  ├───────────────┼──────────────>│
  │                 │                  │               │               │
  │                 │                  │               │  get_pool()   │
  │                 │                  │               │  execute SQL  │
  │                 │                  │               │               │
  │                 │                  │<──────────────┼───────────────┤
  │                 │                  │   QueryResult │               │
  │                 │<─────────────────┤               │               │
  │                 │  result, time    │               │               │
  │                 │                  │               │               │
  │                 │ save_history()   │               │               │
  │                 │                  │               │               │
  │<────────────────┤                  │               │               │
  │  JSON response  │                  │               │               │
  │                 │                  │               │               │
```

### 元数据提取流程

```
客户端          API 路由      数据库服务      注册表         适配器
  │                 │                  │               │               │
  │  GET /{name}    │                  │               │               │
  ├────────────────>│                  │               │               │
  │                 │                  │               │               │
  │                 │ extract_metadata()│              │               │
  │                 ├─────────────────>│               │               │
  │                 │                  │               │               │
  │                 │                  │ get_adapter() │               │
  │                 │                  ├──────────────>│               │
  │                 │                  │<──────────────┤               │
  │                 │                  │  adapter      │               │
  │                 │                  │               │               │
  │                 │                  │ extract_metadata()            │
  │                 │                  ├───────────────┼──────────────>│
  │                 │                  │               │               │
  │                 │                  │               │  查询目录    │
  │                 │                  │               │  构建结果    │
  │                 │                  │               │               │
  │                 │                  │<──────────────┼───────────────┤
  │                 │                  │ MetadataResult│               │
  │                 │<─────────────────┤               │               │
  │                 │  metadata        │               │               │
  │                 │                  │               │               │
  │                 │ cache_metadata() │               │               │
  │                 │                  │               │               │
  │<────────────────┤                  │               │               │
  │  JSON response  │                  │               │               │
  │                 │                  │               │               │
```

### 适配器注册流程

```
应用启动        注册表         PostgreSQL适配器    MySQL适配器
     │            │                     │                  │
     │ __init__() │                     │                  │
     ├───────────>│                     │                  │
     │            │                     │                  │
     │            │ register(POSTGRESQL, PostgreSQLAdapter)│
     │            ├────────────────────>│                  │
     │            │    [存储映射]       │                  │
     │            │                     │                  │
     │            │ register(MYSQL, MySQLAdapter)          │
     │            ├────────────────────────────────────────>│
     │            │    [存储映射]       │                  │
     │            │                     │                  │
     │<───────────┤                     │                  │
     │  registry  │                     │                  │
     │            │                     │                  │
     │            │                     │                  │
   [就绪]         │                     │                  │
```

## 依赖图

```
                                    应用程序
                                         │
                                         ▼
                                    main.py
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
             API 层             数据库服务         适配器注册表
          (databases.py,             │                      │
           queries.py)               │                      │
                    │                │                      │
                    └────────────────┼──────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
            SQL 验证器       查询历史         适配器
                                              (PostgreSQL,
                                               MySQL, 等.)
                                                     │
                                                     ▼
                                            数据库驱动
                                            (asyncpg, aiomysql)
```

## 对象生命周期

### 适配器实例生命周期

```
┌──────────────────────────────────────────────────────────────┐
│  1. 创建                                                      │
│     config = ConnectionConfig(url=..., name="mydb")          │
│     adapter = PostgreSQLAdapter(config)                      │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  2. 注册（缓存在注册表中）                                    │
│     registry._instances["postgresql:mydb"] = adapter         │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  3. 连接池创建（延迟加载）                                    │
│     pool = await adapter.get_connection_pool()              │
│     # 首次调用时创建池，后续返回缓存的池                       │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  4. 使用（多个查询）                                          │
│     result1 = await adapter.execute_query("SELECT...")       │
│     result2 = await adapter.execute_query("SELECT...")       │
│     # 复用同一个池                                            │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  5. 清理                                                      │
│     await registry.close_adapter(db_type, name)              │
│     # 关闭池，从注册表中移除                                  │
└──────────────────────────────────────────────────────────────┘
```

## 使用的设计模式

### 1. 抽象工厂模式
```
DatabaseAdapterRegistry 根据 DatabaseType 创建 DatabaseAdapter 实例
```

### 2. 工厂方法模式
```
每个适配器实现工厂方法：
- get_connection_pool() 创建数据库特定的池
```

### 3. 外观模式
```
DatabaseService 提供简化的接口到：
- 适配器注册表
- SQL 验证
- 查询执行
- 元数据提取
```

### 4. 单例模式
```
全局实例：
- adapter_registry
- database_service
```

### 5. 策略模式
```
不同的适配器为以下操作实现不同的策略：
- 连接管理
- 元数据提取
- 查询执行
```

### 6. 模板方法模式
```
DatabaseAdapter 定义模板：
1. 获取池
2. 获取连接
3. 执行操作
4. 处理结果
5. 返回标准化格式
```

## 关系类型

### 继承
```
PostgreSQLAdapter ──▷ DatabaseAdapter (是一个)
MySQLAdapter ──▷ DatabaseAdapter (是一个)
```

### 组合
```
DatabaseService ◆── DatabaseAdapterRegistry (拥有一个)
DatabaseAdapter ◆── ConnectionConfig (拥有一个)
```

### 依赖
```
DatabaseService ···> DatabaseAdapter (使用)
API 路由 ···> DatabaseService (使用)
```

### 关联
```
DatabaseAdapterRegistry ──> DatabaseAdapter (创建)
```

## SOLID 原则映射

### 单一职责
- **DatabaseAdapter**：数据库操作
- **DatabaseAdapterRegistry**：适配器生命周期
- **DatabaseService**：业务逻辑协调
- **API 路由**：HTTP 请求/响应

### 开闭原则
- **开放**：通过创建新类添加新适配器
- **封闭**：现有适配器无需修改

### 里氏替换
- 所有适配器可以替换 DatabaseAdapter

### 接口隔离
- DatabaseAdapter 具有专注的接口
- 没有适配器被强制实现未使用的方法

### 依赖倒置
- 高层模块（服务）依赖抽象（DatabaseAdapter）
- 低层模块（适配器）实现抽象
- 不依赖具体实现
