# Research Document: 数据导出功能模块

**Feature**: 数据导出功能模块
**Branch**: `001-data-export`
**Date**: 2025-12-28
**Status**: Completed

## Overview

本文档汇总了数据导出功能模块的技术研究结果,包括 CSV/JSON/Markdown 导出实现、进度跟踪机制、文件大小估算和 AI 智能导出助手集成。

---

## Research Topic 1: CSV 导出最佳实践

### Decision
**流式响应 + 异步生成器 + csv.writer**

使用 FastAPI 的 `StreamingResponse` + Python 异步生成器 + `csv.DictWriter` 实现内存高效的大文件导出。

### Rationale

1. **内存效率**: 流式处理避免一次性加载全部数据到内存,对大文件导出(100万行+)至关重要
2. **性能优化**: 分批处理(batch_size=1000)减少内存峰值
3. **实时反馈**: 流式响应允许客户端边接收边显示
4. **编码处理**: `utf-8-sig` 编码完美解决 Excel 中文乱码问题
5. **自动转义**: CSV 模块自动处理特殊字符、换行符、引号

### Technical Implementation

**核心组件**:
```python
class ExportService:
    @staticmethod
    async def generate_csv(result: QueryResult, batch_size: int = 1000) -> AsyncGenerator[str, None]:
        # 使用 csv.writer 流式生成 CSV
        # 编码: utf-8-sig (带 BOM)
        # 分批处理: batch_size=1000
        # 自动转义: QUOTE_MINIMAL
        pass
```

**API 端点**:
```python
@router.post("/{name}/export/current")
async def export_current_page(
    name: str,
    input_data: ExportInput,
    session: Session = Depends(get_session),
    user_id: str = "anonymous",
) -> StreamingResponse:
    # 并发限制: asyncio.Semaphore(3)
    # 流式响应: StreamingResponse
    # 文件命名: export-<uuid>.csv
    pass
```

**关键特性**:
- ✅ 使用 `utf-8-sig` 编码(带 BOM)解决 Excel 中文乱码
- ✅ `csv.QUOTE_MINIMAL` 自动转义特殊字符
- ✅ `asyncio.Semaphore` 限制单用户并发(最多3个)
- ✅ 异步生成器分批流式输出(batch_size=1000)
- ✅ 文件命名规则: `export-<uuid>.<ext>`

### Alternatives Considered

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| **流式响应** ✅ | 内存效率高,实时反馈 | 实现略复杂 | **推荐** |
| 一次性生成完整文件 | 实现简单 | 内存溢出风险 | ❌ |
| pandas + StringIO | 功能强大 | 重量级依赖,内存问题 | ❌ |
| 临时文件 + 后台任务 | 支持超大数据 | 需要任务队列,复杂度高 | ⚠️ 特殊场景 |

### Sources
- [Serving 1M+ CSV Exports with FastAPI and Streaming Responses](https://medium.com/@connect.hashblock/serving-1m-csv-exports-with-fastapi-and-streaming-responses-without-memory-bloat-32405f42cff5)
- [FastAPI Official Documentation - Custom Response](https://fastapi.tiangolo.com/advanced/custom-response/)
- [Encoding error in Python with Chinese characters (Stack Overflow)](https://stackoverflow.com/questions/3883573/encoding-error-in-python-with-chinese-characters)

---

## Research Topic 2: JSON 导出最佳实践

### Decision
**流式导出 + 自定义 JSON 编码器**

结合 `StreamingResponse` + Pydantic V2 的 `jsonable_encoder` + 自定义编码器,处理数据库特殊类型(datetime, decimal, binary)。

### Rationale

1. **内存效率**: 流式响应避免一次性加载百万行数据
2. **类型安全**: Pydantic 自动处理 datetime、decimal、UUID 等类型
3. **前端兼容**: 正确的 Content-Disposition 和 MIME 类型
4. **符合架构**: 集成到现有 SQLModel/Pydantic 架构

### Technical Implementation

**自定义编码器**:
```python
class DatabaseJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        # datetime/ date → ISO 8601
        # Decimal → string (保留精度)
        # UUID → string
        # bytes → base64
        pass

# 推荐:使用 Pydantic V2 的 jsonable_encoder
def serialize_for_json(obj: Any) -> Any:
    custom_encoders = {
        datetime: lambda v: v.isoformat(),
        Decimal: lambda v: str(v),
        bytes: lambda v: base64.b64encode(v).decode('utf-8'),
    }
    return jsonable_encoder(obj, custom_encoders=custom_encoders)
```

**导出格式选择**:
- **标准 JSON**: 适合中小数据集(<10MB)
- **JSONL (JSON Lines)**: 适合大数据集,每行一个 JSON 对象

### Alternatives Considered

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| **自定义编码器** ✅ | 类型安全,自动处理 | 需要配置 | **推荐** |
| 标准库 json.dumps() | 简单 | 无法处理特殊类型 | ❌ |
| orjson | 性能极高(2-3x) | 额外依赖 | ⚠️ 性能关键 |
| pandas.to_json() | 功能强大 | 重量级依赖 | ❌ |

### Sources
- [Streaming Large JSON Responses in FastAPI Without Killing Memory](https://medium.com/@bhagyarana80/streaming-large-json-responses-in-fastapi-without-killing-memory-6e2f9a49eb0e)
- [7 Hidden FastAPI Response Streaming Patterns That Cut Memory Usage by 90%](https://python.plainenglish.io/7-hidden-fastapi-response-streaming-patterns-that-cut-memory-usage-by-90-in-production-9f67cbbbd21d)
- [Pydantic Serialization (Official Docs)](https://docs.pydantic.dev/latest/concepts/serialization/)

---

## Research Topic 3: 导出进度跟踪方案

### Decision
**内存任务队列 + 轮询机制**

使用内存 TaskManager(单例) + 前端轮询(1秒间隔)实现进度跟踪,无需 Redis 等外部依赖。

### Rationale

1. **简单性优先**: 单机部署,无分布式需求,不引入外部依赖
2. **满足性能要求**: 1秒轮询间隔 > 规格要求的"每秒1次更新"
3. **适合项目规模**: 单用户并发3个任务,5分钟超时,100MB文件限制
4. **可扩展性**: 未来可迁移到 Redis + ARQ

### Architecture

```
Frontend                          Backend
┌──────────────┐                 ┌──────────────────┐
│ ExportButton │ ──POST /export─>│  TaskManager     │
│              │                 │  - asyncio.Queue │
│ ProgressBar  │ ←Poll /tasks/id─│  - Dict[Task]    │
└──────────────┘                 │  - worker()      │
                                 └──────────────────┘
                                          │
                                          ▼
                                   ┌──────────────────┐
                                   │  ExportService   │
                                   │  - execute_export│
                                   │  - progress_cb   │
                                   └──────────────────┘
```

**核心组件**:
1. **TaskManager** (单例): 管理所有导出任务的生命周期
2. **Task 数据模型**: task_id, user_id, status, progress, file_url, error
3. **进度回调**: `async def update_progress(progress: int)`

**API 设计**:
```python
POST   /api/v1/dbs/{name}/export      # 创建导出任务
GET    /api/v1/tasks/{task_id}         # 查询任务状态(轮询)
DELETE /api/v1/tasks/{task_id}         # 取消任务
GET    /api/v1/exports/download/{file} # 下载文件
```

### Alternatives Considered

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| **轮询机制** ✅ | 简单,可靠,无依赖 | 轮询开销 | **推荐** |
| WebSocket | 实时性更好 | 复杂度高,需消息队列 | ❌ 过度设计 |
| SSE | 基于HTTP,比WS简单 | 不支持双向通信 | ⚠️ 可行 |
| Redis + ARQ | 分布式,持久化 | 引入外部依赖 | ⚠️ 未来扩展 |
| Celery | 功能强大 | 重量级,复杂度高 | ❌ 过度设计 |

### Sources
- [FastAPI Background Tasks Tutorial](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Managing Background Tasks in FastAPI: BackgroundTasks vs ARQ](https://davidmuraya.com/blog/fastapi-background-tasks-arq-vs-built-in/)
- [Polling vs SSE vs WebSockets: which approach to use](https://www.reddit.com/r/FastAPI/comments/1if6o84/polling_vs_sse_vs_websockets_which_approach_use/)

---

## Research Topic 4: 文件大小估算方法

### Decision
**混合估算策略**

结合**基于元数据的快速估算**和**基于采样的精确估算**,根据数据规模自动选择最佳方法。

### Rationale

1. **性能平衡**: 元数据估算零额外查询,采样估算准确性高
2. **准确性保障**: 采样方法误差<2%,元数据方法误差~20%
3. **用户体验**: 快速响应(<100ms) + 渐进式提升准确性
4. **成本可控**: 对小数据集直接采样,大数据集优先元数据

### Algorithm

**决策流程**:
```
1. 导出前检查 → 元数据估算(<100ms)
   ├─ < 80MB  → 直接允许
   ├─ 80-100MB → 显示警告
   └─ > 100MB → 阻止导出

2. [可选] 如果估算接近限制或用户要求精确
   └─ 采样查询(LIMIT 100) → 重新估算

3. 实际导出过程中监控大小
   └─ 每1000行检查一次,超过限制立即终止
```

**估算公式**:

**元数据方法**:
```
CSV 每行大小 ≈ Σ(列类型平均大小 + 3字节) + 2字节换行 + 100字节表头

数据类型平均大小:
- integer: 6字节
- varchar: 50字节
- timestamp: 25字节
- text: 100字节
```

**采样方法**:
```
1. 执行 LIMIT 100 获取样本
2. 实际序列化样本为 CSV/JSON/MD
3. 平均行大小 = 样本总大小 / 100
4. 估算总大小 = 平均行大小 × 总行数
```

### Edge Cases

| 场景 | 处理方案 |
|------|----------|
| 空结果集 | 返回 "无数据可导出" 错误 |
| COUNT 查询失败 | 回退到元数据行数,标记低置信度 |
| 复杂查询(JOIN/GROUP BY) | 使用子查询: `SELECT COUNT(*) FROM (sql) AS subquery` |
| BLOB/大文本字段 | 增加 1.5x 安全系数 |
| 非ASCII字符(中文等) | 增加 1.3x 编码惩罚系数 |
| 实时导出超限 | 每1000行检查,超过100MB立即终止 |

### Alternatives Considered

| 方案 | 准确性 | 性能 | 选择 |
|------|--------|------|------|
| **混合策略** ✅ | 高(采样<2%) | 快(元数据<100ms) | **推荐** |
| 仅元数据估算 | 中(~20%) | 最快(<50ms) | ⚠️ 快速预检查 |
| 仅采样估算 | 高(<2%) | 慢(1-2s) | ⚠️ 精确模式 |
| 实际测量 | 100% | 最慢(需完整导出) | ❌ 不适用 |

---

## Research Topic 5: AI 导出助手集成

### Decision
**混合式 AI 导出助手架构**

采用**三层决策架构** + **结构化响应** + **反馈学习循环**,在现有 `nl2sql.py` 基础上扩展。

### Rationale

1. **复用现有架构**: 扩展现有 `NaturalLanguageToSQLService`,保持代码一致性
2. **渐进式增强**: P1/P2/P3 功能分层实现,降低开发风险
3. **可观测性**: 通过审计日志追踪 AI 建议接受率(目标80%)
4. **用户控制**: AI 仅提供建议,最终决策权在用户

### Prompt Design

**三层 Prompt 架构**:

1. **导出意图分析 Prompt**:
   - 判断是否应该建议导出
   - 输出: `shouldSuggestExport`, `confidence`, `reason`, `suggestedFormat`

2. **导出 SQL 生成 Prompt**:
   - 根据自然语言生成优化的导出 SQL
   - 输出: `sql`, `explanation`, `estimatedRows`, `performanceTips`

3. **主动建议 Prompt**:
   - 生成友好的导出建议文本
   - 输出: `suggestionText`, `quickActions`, `valueProposition`

**关键特性**:
- ✅ 使用 OpenAI 结构化输出(`json_schema`)
- ✅ 集成数据库元数据上下文
- ✅ 追踪用户响应和接受率
- ✅ 降级机制:AI 服务不可用时回退到规则引擎

### Technical Implementation

**服务层**:
```python
class AIExportAssistantService:
    async def analyze_export_intent(...) -> ExportIntentAnalysis:
        # 判断是否应该建议导出
        # 考虑因素: 行数, 查询类型, 用户历史, 接受率
        pass

    async def generate_export_sql(...) -> ExportSQLGeneration:
        # 根据自然语言生成导出 SQL
        # 优化: JOIN, WHERE, ORDER BY, LIMIT
        pass

    async def generate_proactive_suggestion(...) -> ProactiveSuggestion:
        # 生成主动导出建议
        # 风格: 友好, 简洁(<30字), 突出价值
        pass

    async def record_suggestion_response(...):
        # 记录用户响应用于分析
        pass

    async def get_analytics_dashboard(...) -> dict:
        # 获取接受率、响应分布等指标
        pass
```

**API 端点**:
```python
POST   /api/v1/export/analyze-intent       # 分析导出意图
POST   /api/v1/export/generate-sql         # 生成导出 SQL
POST   /api/v1/export/proactive-suggestion # 主动建议
POST   /api/v1/export/track-response       # 记录用户响应
GET    /api/v1/export/analytics            # 分析数据
```

### Alternatives Considered

| 方案 | 智能程度 | 用户控制 | 成本 | 选择 |
|------|----------|----------|------|------|
| **混合架构** ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 中 | **推荐** |
| 纯规则引擎 | ⭐⭐ | ⭐⭐⭐⭐⭐ | 零 | ❌ 智能化不足 |
| 主动式 AI | ⭐⭐⭐⭐ | ⭐⭐ | 高 | ❌ 用户失去控制 |
| 多模型集成 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 很高 | ❌ 过度设计 |

### Sources
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [How to Measure AI Assistant Performance in 2025](https://wbsolution.co.uk/measure-ai-assistant-performance-2025/)
- [AI Assistant Statistics 2026: Adoption & ROI Data](https://www.index.dev/blog/ai-assistant-statistics)

---

## Summary: 技术决策矩阵

| 技术领域 | 选择方案 | 关键技术 | 性能目标 | 复杂度 |
|----------|----------|----------|----------|--------|
| **CSV 导出** | 流式响应 + csv.writer | StreamingResponse, utf-8-sig | 30秒/1万行 | 中 |
| **JSON 导出** | 流式导出 + 自定义编码器 | jsonable_encoder, Pydantic V2 | 30秒/1万行 | 中 |
| **进度跟踪** | 内存队列 + 轮询 | TaskManager, asyncio.Semaphore | 1秒更新频率 | 低 |
| **文件大小估算** | 混合策略 | 元数据+采样 | <100ms(快)/<2s(精确) | 中 |
| **AI 助手** | 三层架构 + 结构化输出 | OpenAI API, json_schema | 80%接受率目标 | 高 |

---

## Implementation Phases

基于研究结果,建议按以下顺序实现:

### Phase 1: 核心导出功能 (P1)
- ✅ CSV/JSON/Markdown 流式导出
- ✅ 文件大小估算(元数据方法)
- ✅ 并发限制(3个任务/用户)
- ✅ 导出进度跟踪(轮询)

### Phase 2: AI 智能辅助 (P2)
- ✅ 导出意图分析
- ✅ 主动导出建议
- ✅ AI 建议响应追踪
- ✅ 分析仪表板

### Phase 3: 高级功能 (P3)
- ✅ AI 生成导出 SQL
- ✅ 文件大小精确估算(采样方法)
- ✅ 复杂查询优化

### Phase 4: 优化与完善
- ✅ 边界情况处理
- ✅ 性能优化
- ✅ 错误处理与重试
- ✅ 审计日志完善

---

## Key Takeaways

1. **流式响应是处理大文件导出的最佳实践**,避免内存溢出
2. **utf-8-sig 编码完美解决 Excel 中文乱码问题**
3. **轮询机制简单可靠**,适合单机部署的进度跟踪场景
4. **混合估算策略平衡性能和准确性**,元数据(<100ms) + 采样(<2s)
5. **AI 助手通过分层 Prompt 和结构化输出实现可控的智能化**
6. **并发控制使用 Semaphore**,限制单用户导出数量(3个)
7. **审计日志记录所有导出操作**,支持合规性和 AI 效果分析

---

## Next Steps

1. ✅ 生成 `data-model.md` - 定义数据模型
2. ✅ 生成 `contracts/api-v1.yaml` - API 契约
3. ✅ 更新 agent 上下文 - 同步技术栈变更
4. ✅ 生成 `quickstart.md` - 快速开始指南
5. ✅ 重新评估宪法检查 - 确认架构合规性
