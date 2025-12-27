<!--
Sync Impact Report:
- Version change: Initial creation → 1.0.0
- New principles added:
  1. Ergonomic Python Style (后端代码风格)
  2. Strict Type Annotation (严格类型标注)
  3. Pydantic Data Models (Pydantic数据模型)
  4. JSON Naming Convention (JSON命名规范)
  5. Open Access Policy (开放访问策略)
- New sections: Core Principles, Technical Standards, Governance
- Templates status:
  ✅ plan-template.md - Aligned with constitution principles
  ✅ spec-template.md - Compatible with technical standards
  ✅ tasks-template.md - Reflects principle-driven task structure
  ✅ checklist-template.md - No updates required
- Follow-up TODOs: None
-->

# Database Query Tool Constitution

## Core Principles

### I. Ergonomic Python Style

后端代码MUST遵循Ergonomic Python风格编写,强调代码的可读性、简洁性和Pythonic特性。

**规则**:
- 使用现代Python特性(3.11+): type hints、match/case、context managers
- 遵循PEP 8规范,使用black格式化和ruff linting
- 优先使用dataclass和pydantic模型而非普通类
- 使用async/await处理I/O密集型操作
- 避免过度设计,优先选择简单直接的方式
- 使用类型提示(type hints)增强代码可维护性

**理由**: Ergonomic Python风格确保代码简洁、易读、易维护,充分利用Python语言特性,减少样板代码,提高开发效率。

### II. Strict Type Annotation

前后端代码MUST有严格的类型标注,所有函数参数、返回值、类属性都必须有明确的类型声明。

**规则**:
- 后端使用Python type hints,启用mypy严格模式(`--strict`)
- 前端使用TypeScript strict模式,启用所有严格检查选项
- 禁止使用`Any`类型(除特定互操作场景)
- 所有Pydantic模型字段必须有明确类型
- API接口必须有完整的请求/响应类型定义

**理由**: 严格的类型标注可以在编译期/开发期捕获大量错误,提高代码可靠性,改善IDE支持,降低维护成本。

### III. Pydantic Data Models

所有数据模型MUST使用Pydantic定义,确保数据验证、序列化和文档生成的一致性。

**规则**:
- 所有API请求/响应模型继承自`BaseModel`
- 使用Pydantic V2特性(如果适用)
- 模型字段必须有明确的类型、约束和描述
- 复杂嵌套结构使用`Field`、`validator`、`model_serializer`等装饰器
- 利用Pydantic自动生成OpenAPI文档

**理由**: Pydantic提供统一的数据验证层,自动处理类型转换和错误提示,减少样板代码,提高数据安全性。

### IV. JSON Naming Convention

所有后端生成的JSON数据,MUST使用camelCase格式,确保与前端JavaScript/TypeScript生态系统的一致性。

**规则**:
- API响应JSON字段使用camelCase(如`userName`, `createdAt`)
- 数据库存储字段使用snake_case(如`user_name`, `created_at`)
- 在Pydantic模型中使用别名(alias)实现转换
- 示例:
  ```python
  class UserResponse(BaseModel):
      user_id: int = Field(alias="userId")
      created_at: datetime = Field(alias="createdAt")
  ```

**理由**: camelCase是JavaScript/TypeScript的标准命名约定,统一JSON格式减少前端转换逻辑,提高开发体验。

### V. Open Access Policy

系统不需要认证,任何用户都可以使用。所有API端点MUST公开访问,无需身份验证。

**规则**:
- 不实现用户认证、授权机制
- 不实现session、JWT、OAuth等
- API端点完全开放,支持CORS跨域访问
- 所有origin允许访问(`Access-Control-Allow-Origin: *`)

**理由**: 这是一个内部数据库查询工具,面向受信任环境使用,简化部署和使用流程,避免认证开销。

## Technical Standards

### 后端技术栈

- **语言**: Python 3.11+
- **框架**: FastAPI
- **数据验证**: Pydantic V2
- **数据库**: PostgreSQL (asyncpg)、MySQL (aiomysql)、SQLite (aiosqlite)
- **SQL解析**: sqlglot
- **LLM集成**: OpenAI SDK
- **异步**: asyncio优先,使用async/await
- **代码质量**: black、ruff、mypy strict
- **测试**: pytest、pytest-asyncio

### 前端技术栈

- **语言**: TypeScript strict mode
- **框架**: React 18+
- **UI框架**: Refine 5、Ant Design
- **样式**: Tailwind CSS
- **代码编辑器**: Monaco Editor
- **测试**: Playwright
- **构建工具**: Vite

### 架构原则

- **后端架构**: 遵循SOLID原则,采用Adapter+Factory+Registry+Facade模式
- **API设计**: RESTful风格,清晰的版本管理(`/api/v1/`)
- **错误处理**: 统一的错误响应格式,包含错误码和错误信息
- **数据库设计**: 使用SQLite存储元数据和连接配置
- **SQL安全**: 仅允许SELECT查询,自动添加LIMIT子句

### API约定

```bash
# 数据库管理
GET    /api/v1/dbs                    # 获取所有数据库
PUT    /api/v1/dbs/{name}             # 添加数据库
GET    /api/v1/dbs/{name}             # 获取数据库元数据
DELETE /api/v1/dbs/{name}             # 删除数据库连接

# 查询操作
POST   /api/v1/dbs/{name}/query       # 执行SQL查询
POST   /api/v1/dbs/{name}/query/natural  # 自然语言生成SQL
```

### 数据存储

- **数据库元数据**: `~/.db_query/db_query.db`
- **环境变量**: `OPENAI_API_KEY`
- **配置管理**: 使用环境变量,避免硬编码

## Development Workflow

### 代码规范

1. **后端代码**:
   - 使用Ergonomic Python风格
   - 所有函数必须有类型提示
   - 使用async/await处理I/O操作
   - 遵循SOLID原则,特别是开闭原则

2. **前端代码**:
   - TypeScript strict模式
   - React函数组件 + Hooks
   - 明确的props类型定义

3. **提交规范**:
   - 使用清晰的commit message
   - 格式: `type: description`
   - 类型: feat、fix、refactor、docs、test

### 测试要求

1. **后端测试**:
   - 使用pytest进行单元测试
   - 使用HTTP测试工具验证API端点
   - 测试文件: `fixtures/test.rest`

2. **前端测试**:
   - 使用Playwright进行E2E测试
   - 验证核心用户流程
   - 确保MySQL和PostgreSQL功能正常

### 质量门禁

1. **代码检查**:
   - `ruff check` - 代码风格检查
   - `mypy --strict` - 类型检查
   - `black --check` - 格式检查

2. **测试通过**:
   - 所有单元测试通过
   - API端点测试通过
   - E2E测试通过

3. **文档完整**:
   - API文档自动生成(FastAPI)
   - 关键模块有README说明

## Governance

### 宪章修订流程

1. **修订提案**: 提出修订理由和具体变更
2. **影响评估**: 评估对现有代码、模板、流程的影响
3. **版本管理**: 遵循语义化版本规范(MAJOR.MINOR.PATCH)
4. **一致性同步**: 更新所有相关模板和文档
5. **审查批准**: 团队审查通过后正式生效

### 版本规则

- **MAJOR**: 架构原则变更、技术栈替换、向后不兼容修改
- **MINOR**: 新增原则、扩展技术标准、新增工具
- **PATCH**: 措辞优化、文档更新、澄清说明

### 合规审查

- 所有代码合并前必须通过mypy strict模式检查
- 所有API变更必须更新OpenAPI文档
- 所有新功能必须包含相应的测试用例
- 代码审查必须检查是否遵循核心原则

### 例外处理

如需违反本宪章的任何原则:

1. 在Complexity Tracking表格中记录违规原因
2. 说明为什么需要更复杂的方案
3. 说明为什么不能采用更简单的替代方案
4. 团队审查批准后方可实施

**Version**: 1.0.0 | **Ratified**: 2025-12-24 | **Last Amended**: 2025-12-24
