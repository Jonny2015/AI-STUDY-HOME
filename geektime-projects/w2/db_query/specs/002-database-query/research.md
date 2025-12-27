# Research: Database Query Tool

**Feature**: Database Query Tool
**Date**: 2025-12-25
**Phase**: Phase 0 - Outline & Research

## Overview

本文档记录 Database Query Tool 的技术调研结果，解决所有技术选型和最佳实践问题。

## Research Topics

### 1. FastAPI 最佳实践

**Decision**: 使用 FastAPI 作为后端框架，结合 Pydantic V2 和 async/await

**Rationale**:
- 原生支持 async/await，适合 I/O 密集型数据库操作
- 自动生成 OpenAPI 文档，减少文档维护成本
- Pydantic V2 提供强大的数据验证和序列化
- 类型提示驱动，与 mypy --strict 完美配合
- 性能优异（基于 Starlette）

**Key Patterns**:
1. **依赖注入**: 使用 `Depends` 处理数据库连接和配置
2. **异常处理**: 统一使用 `HTTPException` 和自定义异常处理器
3. **CORS**: 使用 `CORSMiddleware` 允许所有 origin
4. **生命周期**: 使用 `lifespan` 上下文管理器管理资源

**Best Practices**:
- API 路由按功能模块拆分 (`api/v1/databases.py`, `api/v1/queries.py`)
- 使用 `APIRouter` 组织路由
- 所有端点添加清晰的 docstring
- 响应模型使用 Pydantic 的 `alias_generator` 实现 camelCase

**Alternatives Considered**:
- **Flask**: 缺少原生 async 支持，类型提示较弱
- **Django**: 过于重量级，ORM 不适合多数据库类型场景
- **Starlette**: 过于底层，缺少 Pydantic 集成

---

### 2. 数据库适配器架构 (SOLID - Adapter Pattern)

**Decision**: 使用 Adapter + Factory + Registry 模式实现多数据库支持

**Rationale**:
- **开闭原则**: 添加新数据库类型只需创建新 Adapter，无需修改现有代码
- **依赖倒置**: Service 层依赖 `DatabaseAdapter` 抽象，而非具体实现
- **单一职责**: 每个 Adapter 仅处理一个数据库类型的特定逻辑
- **里氏替换**: 所有 Adapter 可互换使用

**Architecture**:
```python
# 抽象基类
class DatabaseAdapter(ABC):
    @abstractmethod
    async def connect(self, url: str) -> Connection: ...

    @abstractmethod
    async def get_metadata(self) -> DatabaseMetadata: ...

    @abstractmethod
    async def execute_query(self, sql: str) -> QueryResult: ...

# 具体适配器
class PostgreSQLAdapter(DatabaseAdapter): ...
class MySQLAdapter(DatabaseAdapter): ...

# 注册表
class AdapterRegistry:
    _adapters: Dict[str, Type[DatabaseAdapter]] = {}

    @classmethod
    def register(cls, db_type: str, adapter: Type[DatabaseAdapter]): ...
    @classmethod
    def get_adapter(cls, db_type: str) -> DatabaseAdapter: ...

# 工厂
class AdapterFactory:
    @staticmethod
    def create(url: str) -> DatabaseAdapter: ...
```

**Best Practices**:
- 使用 `sqlglot` 解析连接 URL，自动检测数据库类型
- Adapter 实现所有数据库特定逻辑（连接、元数据提取、查询执行）
- 异常处理在 Adapter 层统一转换为标准异常
- 连接池管理封装在 Adapter 内部

**Alternatives Considered**:
- **单一类处理所有数据库**: 违反开闭原则，添加新数据库需修改现有代码
- **SQLAlchemy**: 过于重量级，ORM 抽象不适合元数据提取场景
- **原生 SQL 直接嵌入**: 数据库特定逻辑散落各处，难以维护

---

### 3. SQL 解析与安全验证

**Decision**: 使用 sqlglot 进行 SQL 解析和验证

**Rationale**:
- 支持多种 SQL 方言（PostgreSQL, MySQL）
- 纯 Python 实现，无外部依赖
- 可以解析和转换 SQL，易于添加 LIMIT 子句
- 性能优异，适合实时验证

**Implementation**:
```python
import sqlglot
from sqlglot import exp

def validate_sql(sql: str) -> ValidationResult:
    """验证 SQL 并确保是 SELECT 语句"""
    try:
        parsed = sqlglot.parse_one(sql, dialect='postgres')

        # 检查是否是 SELECT
        if not isinstance(parsed, exp.Select):
            return ValidationError("仅允许 SELECT 查询")

        # 添加 LIMIT（如果不存在）
        if not parsed.limit:
            parsed.set_limit(exp.Limit(expression=exp.Number(this=1000)))

        return SuccessResult(parsed.sql())
    except sqlglot.ParseError as e:
        return ParseError(str(e))
```

**Best Practices**:
- 在执行前解析 SQL，拒绝非 SELECT 语句
- 自动添加 LIMIT 1000（如果用户未指定）
- 保留原始 SQL 格式化（注释、换行）
- 错误信息指向具体错误位置

**Security Considerations**:
- ✅ 仅允许 SELECT（防止数据修改）
- ✅ 自动 LIMIT（防止资源耗尽）
- ✅ 查询超时（防止长时间运行）
- ⚠️ SQL 注入：使用参数化查询，不在 SQL 中拼接用户输入

**Alternatives Considered**:
- **pglast / mysql-parser**: 单一数据库，不支持多方言
- **正则表达式**: 无法准确解析复杂 SQL
- **数据库自带解析器**: 需要建立连接，无法在执行前验证

---

### 4. Pydantic 模型与 camelCase JSON

**Decision**: 使用 Pydantic V2 的 `alias_generator` 实现 camelCase

**Rationale**:
- 前端 JavaScript/TypeScript 生态系统使用 camelCase
- 后端 Python 使用 snake_case
- Pydantic 提供自动转换，减少手动映射代码

**Implementation**:
```python
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel_case

class DatabaseResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel_case,
        populate_by_name=True  # 允许使用字段名或别名
    )

    database_name: str = Field(alias="databaseName")
    created_at: datetime = Field(alias="createdAt")
    connection_status: str = Field(alias="connectionStatus")
```

**Best Practices**:
- 所有响应模型使用 `alias_generator=to_camel_case`
- 设置 `populate_by_name=True` 以支持测试和内部调用
- 请求模型也使用 camelCase（与前端一致）
- 嵌套模型递归应用相同配置

**Alternatives Considered**:
- **前端转换**: 前端需要处理每个响应，增加代码复杂度
- **snake_case JSON**: 不符合 JavaScript 规范，降低开发体验
- **手动映射**: 大量样板代码，容易出错

---

### 5. OpenAI SDK 集成 (自然语言生成 SQL)

**Decision**: 使用 OpenAI SDK (GPT-4o-mini) 生成 SQL

**Rationale**:
- GPT-4o-mini 性价比高，适合 SQL 生成场景
- SDK 提供 async 支持，与 FastAPI 集成顺畅
- 可配置 temperature 和 top_p 控制生成质量

**Implementation**:
```python
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

class LLMService:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_sql(
        self,
        prompt: str,
        metadata: DatabaseMetadata,
        db_type: str
    ) -> str:
        # 构造包含元数据的上下文
        context = self._build_context(metadata, db_type)

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a SQL expert. Database type: {db_type}\n\nSchema:\n{context}"
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # 低温度保证生成稳定
            top_p=0.9
        )

        return response.choices[0].message.content
```

**Best Practices**:
- 使用 system message 注入数据库元数据
- 低 temperature (0.1-0.2) 保证生成稳定性
- 捕获 OpenAI API 错误，返回友好提示
- 验证生成的 SQL 语法（使用 sqlglot）
- 记录使用的 token 数（成本监控）

**Cost Optimization**:
- 使用 GPT-4o-mini（非 GPT-4）
- 缓存元数据，减少重复传输
- 限制上下文长度（仅包含表结构，不含数据）

**Alternatives Considered**:
- **Claude API**: 成本较高，但性能更好
- **本地 LLM**: 部署复杂，生成质量不稳定
- **规则引擎**: 无法处理复杂查询

---

### 6. SQLite 元数据存储

**Decision**: 使用 SQLite 存储数据库连接和元数据

**Rationale**:
- 轻量级，无需独立数据库服务
- 文件存储，易于备份和迁移
- Python 内置支持（aiosqlite）
- 适合小规模数据（< 1000 个数据库连接）

**Schema Design**:
```sql
-- 数据库连接表
CREATE TABLE databases (
    name TEXT PRIMARY KEY,
    url TEXT NOT NULL,           -- 脱敏后的连接字符串
    db_type TEXT NOT NULL,       -- postgresql | mysql
    created_at TEXT NOT NULL,    -- ISO 8601
    last_connected_at TEXT       -- ISO 8601
);

-- 元数据表
CREATE TABLE metadata (
    db_name TEXT NOT NULL,
    schema_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    table_type TEXT NOT NULL,    -- table | view
    column_name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    is_nullable INTEGER NOT NULL,
    is_primary_key INTEGER NOT NULL,
    metadata_extracted_at TEXT NOT NULL,
    PRIMARY KEY (db_name, schema_name, table_name, column_name),
    FOREIGN KEY (db_name) REFERENCES databases(name) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_metadata_db_name ON metadata(db_name);
CREATE INDEX idx_metadata_table_name ON metadata(table_name);
```

**Best Practices**:
- 使用 WAL 模式提高并发性能
- 定期 VACUUM 回收空间
- 连接字符串脱敏存储（密码替换为 `****`）
- 外键约束保证数据一致性

**Security**:
- 文件权限: `0600`（仅所有者可读写）
- 密码脱敏: 连接 URL 中的密码部分替换为占位符
- 环境变量: API key 通过 `OPENAI_API_KEY` 传入

**Alternatives Considered**:
- **JSON 文件**: 并发不安全，查询效率低
- **PostgreSQL/MySQL**: 过于重量级，需额外服务
- **Redis**: 需要额外服务，持久化复杂

---

### 7. React + Refine + Ant Design 前端架构

**Decision**: 使用 Refine 5 框架 + Ant Design 组件库

**Rationale**:
- **Refine**: 内置 CRUD、资源管理、数据提供者，减少样板代码
- **Ant Design**: 企业级 UI 组件，适合内部工具
- **TypeScript strict**: 类型安全，减少运行时错误
- **Monaco Editor**: VS Code 同款编辑器，支持 SQL 语法高亮

**Architecture**:
```typescript
// types/index.ts
export interface Database {
  databaseName: string;
  dbType: 'postgresql' | 'mysql';
  createdAt: string;
  connectionStatus: 'connected' | 'failed';
}

// services/api.ts
import { dataProvider } from '@refine/core';

export const apiClient = axios.create({
  baseURL: '/api/v1',
});

export const databasesProvider = dataProvider({
  getList: () => apiClient.get('/dbs'),
  create: ({ name, url }) => apiClient.put(`/dbs/${name}`, { url }),
  delete: (name) => apiClient.delete(`/dbs/${name}`),
});

// components/SqlEditor.tsx
import Editor from '@monaco-editor/react';

export const SqlEditor: React.FC<Props> = ({ value, onChange }) => (
  <Editor
    height="400px"
    defaultLanguage="sql"
    value={value}
    onChange={(val) => onChange(val || '')}
    options={{
      minimap: { enabled: false },
      fontSize: 14,
      scrollBeyondLastLine: false,
    }}
  />
);
```

**Best Practices**:
- 使用 Refine 的 `useList`、`useCreate`、`useDelete` hooks
- API 调用封装在 `services/` 目录
- TypeScript 类型与后端 Pydantic 模型对应
- 使用 Tailwind CSS 补充 Ant Design 样式

**Alternatives Considered**:
- **纯 React + Ant Design**: 需要手动实现 CRUD 逻辑
- **Next.js**: SSR 不适合此场景（SPA 即可）
- **Material-UI**: 与 Ant Design 类似，但 Refine 默认集成 Ant Design

---

### 8. Monaco Editor 集成

**Decision**: 使用 `@monaco-editor/react` 封装组件

**Rationale**:
- VS Code 同款编辑器，体验优秀
- 支持 SQL 语法高亮（需配置）
- 自动补全（可基于元数据自定义）
- 跨浏览器兼容

**Implementation**:
```typescript
import Editor from '@monaco-editor/react';

export const SqlEditor: React.FC = () => {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);

  const handleEditorDidMount = (
    editor: monaco.editor.IStandaloneCodeEditor,
    monaco: typeof import('monaco-editor')
  ) => {
    editorRef.current = editor;

    // 配置 SQL 自动补全
    monaco.languages.registerCompletionItemProvider('sql', {
      provideCompletionItems: (model, position) => {
        // 基于元数据提供表名、列名补全
        return { suggestions: getSuggestions() };
      },
    });
  };

  return (
    <Editor
      height="500px"
      defaultLanguage="sql"
      defaultValue="SELECT * FROM users LIMIT 10;"
      onMount={handleEditorDidMount}
      options={{
        fontSize: 14,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        automaticLayout: true,
      }}
    />
  );
};
```

**Best Practices**:
- 使用 `ref` 访问编辑器实例（获取值、执行命令）
- 配置 SQL 自定义补全（基于数据库元数据）
- 暗色主题配置（`theme="vs-dark"`）
- 错误提示集成（显示后端返回的 SQL 验证错误）

---

### 9. CORS 与跨域配置

**Decision**: FastAPI 允许所有 origin（开发环境）

**Rationale**:
- 内部工具，无需认证
- 开发环境前后端端口不同（3000 vs 8000）
- 简化部署和使用流程

**Implementation**:
```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],              # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production Consideration**:
- 生产环境建议限制 `allow_origins` 为具体域名
- 或使用反向代理（Nginx）处理 CORS

---

### 10. 错误处理与响应格式

**Decision**: 统一的错误响应格式

**Rationale**:
- 前端可统一处理错误
- 提供清晰的错误信息
- 符合 RESTful 最佳实践

**Implementation**:
```python
from fastapi import HTTPException
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str = Field(alias="error")
    message: str = Field(alias="message")
    details: dict | None = Field(default=None, alias="details")

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "message": "请求处理失败",
            "details": None,
        },
    )

# 使用示例
if not is_select_query(sql):
    raise HTTPException(
        status_code=400,
        detail="仅允许 SELECT 查询",
    )
```

**Error Types**:
- `400`: 请求参数错误（如 SQL 语法错误）
- `404`: 资源不存在（如数据库不存在）
- `500`: 服务器错误（如数据库连接失败）

---

## Summary

所有技术选型已完成，符合项目宪章的技术标准：

| 技术领域 | 选择 | 符合标准 |
|---------|------|---------|
| 后端框架 | FastAPI | ✅ |
| 数据验证 | Pydantic V2 | ✅ |
| SQL 解析 | sqlglot | ✅ |
| LLM 集成 | OpenAI SDK | ✅ |
| 元数据存储 | SQLite | ✅ |
| 前端框架 | React 18 + Refine 5 | ✅ |
| UI 组件 | Ant Design | ✅ |
| 代码编辑器 | Monaco Editor | ✅ |
| 类型检查 | mypy --strict, TS strict | ✅ |
| 代码格式 | black, ruff | ✅ |
| 测试框架 | pytest, Playwright | ✅ |

**Next Steps**:
- Phase 1: 设计数据模型（data-model.md）
- Phase 1: 生成 API 契约（contracts/openapi.yaml）
- Phase 1: 编写快速入门（quickstart.md）
