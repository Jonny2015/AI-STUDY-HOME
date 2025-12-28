# 数据导出功能 - 设计审查文档

**日期**: 2025-12-28
**范围**: Phase 1-2 数据模型和 Schema 设计
**状态**: ✅ **已审查并通过**

---

## 📦 已创建文件清单

### 1. 模型文件
- ✅ `backend/app/models/export.py` - 导出相关枚举和SQLModel实体

### 2. Schema 文件 (修改)
- ✅ `backend/app/models/schemas.py` - 添加了所有导出相关的Pydantic模型

### 3. 配置文件 (修改)
- ✅ `backend/app/config.py` - 添加了导出配置项

---

## 🎯 核心设计审查

### A. 数据模型 (`app/models/export.py`)

#### ✅ 优点

1. **枚举定义清晰**
   ```python
   ExportFormat: CSV, JSON, MARKDOWN
   ExportScope: CURRENT_PAGE, ALL_DATA
   TaskStatus: PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
   ExportSuggestionResponse: ACCEPTED, REJECTED, IGNORED, MODIFIED
   ```

2. **ExportTask 模型完整**
   - ✅ 包含所有必需字段 (task_id, user_id, database_name, etc.)
   - ✅ UUID 自动生成: `default_factory=lambda: str(uuid4())`
   - ✅ 文件大小限制: `le=104_857_600` (100MB)
   - ✅ 进度范围验证: `ge=0, le=100`
   - ✅ 索引优化: task_id, user_id, database_name, status, created_at
   - ✅ 外键关系: `foreign_key="databaseconnections.name"`
   - ✅ 使用 Text 类型存储长文本 (sql_text, error_message)

3. **AISuggestionAnalytics 模型完整**
   - ✅ 追踪AI建议效果
   - ✅ 包含便利属性: `@property is_accepted`
   - ✅ 支持置信度分析 (confidence字段)

#### ⚠️ 需要注意的设计决策

1. **datetime 处理不一致**
   ```python
   # 当前实现 (ExportTask)
   created_at: datetime = Field(
       default_factory=datetime.utcnow,  # ⚠️ 使用 utcnow()
       sa_column=Column(DateTime(timezone=False), index=True),
   )

   # 现有模型风格 (DatabaseConnection)
   created_at: datetime = Field(
       default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # ✅ 时区感知
   )
   ```
   **建议**: 统一使用现有项目的风格
   ```python
   from datetime import datetime, timezone

   created_at: datetime = Field(
       default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
       sa_column=Column(DateTime(timezone=False), index=True),
   )
   ```

2. **export_format 字段类型**
   ```python
   export_format: ExportFormat  # ✅ 使用枚举,存储为字符串
   ```
   - ✅ 优点: 类型安全,值限制明确
   - ✅ 与现有 DatabaseType 风格一致

3. **可选字段使用 `Optional` 类型**
   ```python
   file_name: Optional[str] = None  # ✅ Python 3.9+ 风格
   ```
   - ✅ 与现有代码一致
   - ✅ 可读性好

---

### B. API Schema 设计 (`app/models/schemas.py`)

#### ✅ 优点

1. **CamelCase 转换正确**
   ```python
   export_all: bool = Field(..., alias="exportAll")
   estimated_bytes: int = Field(..., alias="estimatedBytes")
   ```
   - ✅ 前后端命名约定分离
   - ✅ 使用 `alias` 参数实现自动转换

2. **字段验证完整**
   ```python
   format: str = Field(..., pattern="^(csv|json|md)$")
   sample_size: int = Field(default=100, ge=10, le=1000)
   progress: int = Field(..., ge=0, le=100)
   ```
   - ✅ 正则表达式验证格式
   - ✅ 范围验证 (ge, le)
   - ✅ 必填字段标记 (...)

3. **Schema 覆盖完整**
   - ✅ 导出请求/响应
   - ✅ 文件大小检查
   - ✅ 任务状态查询
   - ✅ AI 功能 (意图分析、SQL生成、主动建议)
   - ✅ 分析数据

4. **文档字符串完整**
   - ✅ 每个字段都有 `description` 参数
   - ✅ 类级别有 docstring

#### ⚠️ 潜在问题

1. **格式值不一致**
   ```python
   # ExportRequest (API schema)
   format: str = Field(..., pattern="^(csv|json|md)$")  # "md"

   # ExportFormat (Model enum)
   MARKDOWN = "markdown"  # "markdown"
   ```
   **建议**: 统一为 "markdown" 或 "md"
   ```python
   # 选项1: 全部使用 "markdown"
   format: str = Field(..., pattern="^(csv|json|markdown)$")

   # 选项2: 枚举也使用 "md"
   class ExportFormat(str, Enum):
       MD = "md"  # 而不是 MARKDOWN = "markdown"
   ```

2. **导出范围值不一致**
   ```python
   # API Schema
   suggested_scope: str | None = Field(None, pattern="^(current_page|all_data)$")

   # Model Enum
   class ExportScope(str, Enum):
       CURRENT_PAGE = "current_page"  # ✅ 一致
       ALL_DATA = "all_data"         # ✅ 一致
   ```
   - ✅ 这个是一致的,没问题

---

### C. 配置管理 (`app/config.py`)

#### ✅ 优点

1. **配置项完整**
   ```python
   export_max_file_size_mb: int = 100
   export_timeout_seconds: int = 300
   export_max_concurrent_per_user: int = 3
   export_temp_dir: str = str(Path.home() / ".db_query" / "exports")
   export_retention_days: int = 7
   ```

2. **默认值合理**
   - ✅ 100MB 文件限制符合规格要求
   - ✅ 5分钟超时 (300秒)
   - ✅ 单用户3个并发任务
   - ✅ 7天文件保留期

3. **环境变量支持**
   - ✅ 通过 `model_config` 支持从 `.env` 文件读取
   - ✅ `case_sensitive=False` 允许灵活的环境变量命名

#### 💡 改进建议

添加导出目录的 property 方法 (与 `db_path` 保持一致):
```python
@property
def export_temp_path(self) -> Path:
    """Get export temporary directory path."""
    temp_dir = Path(self.export_temp_dir).expanduser()
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir
```

---

## 🔄 与现有架构的一致性

### ✅ 符合现有架构

1. **SQLModel 使用**
   - ✅ 与 DatabaseConnection 风格一致
   - ✅ 使用 `Field()` 定义字段
   - ✅ 使用 `table=True` 标记表实体

2. **枚举模式**
   - ✅ 使用 `str, Enum` 基类
   - ✅ 全大写命名 (PENDING, RUNNING, etc.)

3. **Pydantic 模式**
   - ✅ 继承 `BaseModel`
   - ✅ 使用 `alias` 参数
   - ✅ 使用 `Field()` 添加验证

4. **项目结构**
   - ✅ 模型在 `app/models/`
   - ✅ Schemas 在 `app/models/schemas.py`
   - ✅ 配置在 `app/config.py`

---

## 🐛 发现的问题

### 1. 严重问题

#### ✅ 已修复: 格式值不一致
**位置**: `app/models/schemas.py:128`
```python
# 修复前
format: str = Field(..., pattern="^(csv|json|md)$")  # 使用 "md"

# 修复后 ✅
format: str = Field(..., pattern="^(csv|json|markdown)$")
```
**状态**: ✅ 已在 `ExportRequest` 和 `ExportCheckRequest` 中修复

### 2. 需要改进

#### ✅ 已修复: datetime 工厂函数不一致
**位置**: `app/models/export.py:92, 130`
```python
# 修复前
created_at: datetime = Field(default_factory=datetime.utcnow)

# 修复后 ✅
from datetime import datetime, timezone
created_at: datetime = Field(
    default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
)
```
**状态**: ✅ 已在 `ExportTask` 和 `AISuggestionAnalytics` 中统一

#### ✅ 已修复: 缺少导出目录 property
**位置**: `app/config.py:62-66`
```python
# 已添加 ✅
@property
def export_temp_path(self) -> Path:
    """Get export temporary directory path."""
    temp_dir = Path(self.export_temp_dir).expanduser()
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir
```
**状态**: ✅ 已添加

---

## 📋 审查检查清单

### 数据模型
- [x] 枚举定义清晰完整
- [x] SQLModel 字段类型正确
- [x] 外键关系正确
- [x] 索引策略合理
- [x] 验证规则完整 (文件大小、进度范围)
- [x] ✅ datetime 处理已统一
- [x] UUID 生成策略正确

### API Schema
- [x] CamelCase 别名配置正确
- [x] 字段验证完整 (pattern, ge, le)
- [x] 必填/可选字段标记清晰
- [x] 类型注解正确 (使用 `|` 联合类型)
- [x] 文档字符串完整
- [x] ✅ 格式值已统一为 "markdown"

### 配置管理
- [x] 配置项完整
- [x] 默认值合理
- [x] 环境变量支持
- [x] ✅ 已添加 `export_temp_path` property

---

## 🎯 下一步行动

### ✅ 已完成的修复
1. ✅ 统一格式值: 所有 `pattern` 从 `"md"` 改为 `"markdown"`
2. ✅ 统一 datetime 工厂函数: 使用 `datetime.now(timezone.utc).replace(tzinfo=None)`
3. ✅ 添加 `export_temp_path` property 到 Settings 类

### 可以继续实施
- ✅ Phase 2 剩余任务 (T019-T044) - ExportService 和 API 端点
- ✅ 数据库迁移文件 (T001, T002) - 需要手动创建
- ✅ Phase 3: User Story 1 实现 (T045-T074)

---

## ✅ 审查结论

**整体评价**: ✅ **设计优秀,所有问题已修复,可以继续实施**

**优点**:
- ✅ 架构一致性好
- ✅ 类型安全性高
- ✅ 验证规则完整
- ✅ 文档齐全
- ✅ 所有发现的问题已修复

**修复总结**:
- ✅ 3 个问题全部修复
- ✅ 代码质量符合项目标准
- ✅ 可以安全地继续实施 Phase 2-3

**下一步**: 🟢 **继续实施 Phase 2 剩余任务 (T019-T044)**
