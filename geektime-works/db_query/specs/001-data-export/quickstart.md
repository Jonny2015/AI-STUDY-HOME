# Quickstart Guide: 数据导出功能模块

**Feature**: 数据导出功能模块
**Branch**: `001-data-export`
**Last Updated**: 2025-12-28

## Overview

本指南提供数据导出功能的快速开始说明,包括开发环境设置、核心概念、常见使用场景和故障排查。

---

## Prerequisites

### Required Software

- **Python**: 3.12+
- **Node.js**: 18+
- **Database**: PostgreSQL 12+ 或 MySQL 8+
- **OpenAI API Key**: 用于 AI 导出助手功能

### Check Your Environment

```bash
# Python 版本
python --version  # 应显示 3.12+

# Node.js 版本
node --version  # 应显示 18+

# 验证数据库连接
psql --version  # PostgreSQL
# 或
mysql --version  # MySQL
```

---

## Setup

### 1. Install Dependencies

```bash
# 安装后端依赖
cd backend
uv sync

# 安装前端依赖
cd ../frontend
npm install
```

### 2. Configure Environment

编辑 `backend/.env`:

```bash
# 数据库连接(应用数据库)
DATABASE_URL=postgresql://user:password@localhost:5432/db_query

# OpenAI API Key(用于 AI 导出助手)
OPENAI_API_KEY=sk-...

# CORS 设置(开发环境)
CORS_ORIGINS=http://localhost:5173

# 文件导出配置
EXPORT_MAX_FILE_SIZE_MB=100
EXPORT_TIMEOUT_SECONDS=300
EXPORT_MAX_CONCURRENT_PER_USER=3
```

编辑 `frontend/.env.local`:

```bash
# API 端点
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Initialize Database

```bash
cd backend

# 应用数据库迁移
uv run alembic upgrade head

# 验证迁移
uv run alembic current
```

### 4. Start Development Servers

```bash
# 方式 1: 使用 Make(推荐)
make dev  # 同时启动前后端

# 方式 2: 手动启动
# 终端 1: 启动后端
cd backend && uv run uvicorn app.main:app --reload --port 8000

# 终端 2: 启动前端
cd frontend && npm run dev
```

### 5. Verify Setup

```bash
# 后端健康检查
curl http://localhost:8000/health
# 预期输出: {"status": "healthy"}

# 查看 API 文档
open http://localhost:8000/docs
```

---

## Core Concepts

### 1. Export Task Lifecycle

```
创建任务 → pending → running → completed → 下载文件
                ↓         ↓
             cancelled  failed
```

### 2. Export Formats

| 格式 | MIME 类型 | 适用场景 |
|------|-----------|----------|
| **CSV** | `text/csv; charset=utf-8-sig` | Excel 兼容,数据分析 |
| **JSON** | `application/json; charset=utf-8` | Web 应用,API 集成 |
| **Markdown** | `text/markdown; charset=utf-8` | 文档,报告 |

### 3. Export Scope

- **Current Page**: 仅导出当前查询结果(受 LIMIT 1000 限制)
- **All Data**: 导出所有数据(移除 LIMIT 限制,需谨慎)

### 4. Concurrency Limits

- 单用户最多同时进行 **3 个**导出任务
- 超过限制时返回 `429 Too Many Requests`

### 5. File Size Limits

- 最大文件大小: **100MB**
- 预估超过限制时阻止导出
- 接近限制(>80MB)时显示警告

---

## Common Use Cases

### Use Case 1: 手动导出查询结果

**场景**: 用户执行查询后,手动导出为 CSV 文件。

**步骤**:

1. **执行查询**:
   ```sql
   SELECT * FROM users LIMIT 1000
   ```

2. **点击导出按钮**:
   ```typescript
   // 前端代码
   const handleExport = async () => {
     await exportQueryResult(
       'postgres_db',           // 数据库名称
       'SELECT * FROM users',   // SQL
       'csv',                   // 格式
       false                    // exportAll=false (当前页)
     );
   };
   ```

3. **轮询进度**:
   ```typescript
   const pollProgress = async (taskId: string) => {
     const task = await getTaskStatus(taskId);

     if (task.status === 'completed') {
       // 下载文件
       window.location.href = task.fileUrl;
     } else if (task.status === 'running') {
       // 更新进度条
       updateProgressBar(task.progress);
       // 继续轮询
       setTimeout(() => pollProgress(taskId), 1000);
     }
   };
   ```

4. **文件下载**:
   - 文件名格式: `export-<uuid>.csv`
   - 示例: `export-a1b2c3d4-e5f6-7890-abcd-ef1234567890.csv`

**后端 API 调用**:
```bash
curl -X POST "http://localhost:8000/api/v1/dbs/postgres_db/export" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM users LIMIT 1000",
    "format": "csv",
    "exportAll": false
  }'

# 响应:
# {
#   "taskId": "a1b2c3d4-...",
#   "status": "pending",
#   "progress": 0
# }
```

---

### Use Case 2: 检查文件大小后再导出

**场景**: 导出前预估文件大小,避免超过限制。

**步骤**:

1. **调用文件大小检查 API**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/dbs/postgres_db/export/check" \
     -H "Content-Type: application/json" \
     -d '{
       "sql": "SELECT * FROM large_table",
       "format": "csv",
       "useSampling": true
     }'
   ```

2. **解析响应**:
   ```json
   {
     "allowed": true,
     "estimatedSize": {
       "estimatedBytes": 89478485,
       "estimatedMb": 85.3,
       "bytesPerRow": 875,
       "method": "sample",
       "confidence": "high"
     },
     "warning": "预估文件大小 85.3MB 接近限制",
     "recommendation": "建议使用采样获取更准确的估算,或减少导出数据量"
   }
   ```

3. **决定是否导出**:
   - `allowed: true` → 可以导出
   - `allowed: false` → 阻止导出,显示错误信息
   - `warning` 不为空 → 显示警告,用户确认后导出

---

### Use Case 3: AI 主动建议导出

**场景**: 查询完成后,AI 助手主动询问是否需要导出。

**步骤**:

1. **前端集成 AI 建议组件**:
   ```typescript
   import { useAIExportSuggestion } from '@/hooks/useAIExportSuggestion';

   export const QueryResultTable = () => {
     const { analyzeIntent, suggestion } = useAIExportSuggestion();

     useEffect(() => {
       // 查询完成后自动分析
       if (queryResult) {
         analyzeIntent({
           databaseName: 'postgres_db',
           sqlText: queryResult.sql,
           rowCount: queryResult.rowCount,
           executionTimeMs: queryResult.executionTimeMs,
         });
       }
     }, [queryResult]);

     return (
       <>
         <Table data={queryResult.rows} />

         {suggestion?.shouldSuggestExport && (
           <Alert
             message={suggestion.reason}
             action={
               <Button onClick={() => handleExport(suggestion.suggestedFormat)}>
                 导出为 {suggestion.suggestedFormat.toUpperCase()}
               </Button>
             }
           />
         )}
       </>
     );
   };
   ```

2. **后端 API 调用**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/export/analyze-intent" \
     -H "Content-Type: application/json" \
     -d '{
       "databaseName": "postgres_db",
       "sqlText": "SELECT * FROM orders WHERE order_date >= '\''2025-01-01'\''",
       "rowCount": 1500,
       "executionTimeMs": 250
     }'
   ```

3. **AI 响应**:
   ```json
   {
     "shouldSuggestExport": true,
     "confidence": "high",
     "reason": "发现1500条2025年订单数据,建议导出为CSV进行财务分析",
     "suggestedFormat": "csv",
     "suggestedScope": "all_data",
     "clarificationQuestion": null
   }
   ```

---

### Use Case 4: AI 生成导出 SQL

**场景**: 用户描述需求,AI 自动生成优化的导出 SQL。

**步骤**:

1. **前端输入用户需求**:
   ```typescript
   const handleGenerateSQL = async (userPrompt: string) => {
     const result = await generateExportSQL({
       databaseName: 'postgres_db',
       userPrompt: '导出上个月销售额最高的前10个产品',
       dbType: 'postgresql',
       formatHint: 'csv',
     });

     setGeneratedSQL(result.sql);
     setExplanation(result.explanation);
   };
   ```

2. **后端 API 调用**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/export/generate-sql" \
     -H "Content-Type: application/json" \
     -d '{
       "databaseName": "postgres_db",
       "userPrompt": "导出上个月销售额最高的前10个产品",
       "dbType": "postgresql",
       "formatHint": "csv"
     }'
   ```

3. **AI 生成的 SQL**:
   ```json
   {
     "sql": "SELECT p.name, SUM(o.quantity) as total_sold, SUM(o.quantity * p.price) as revenue FROM products p JOIN orders o ON p.id = o.product_id WHERE o.order_date >= NOW() - INTERVAL '\''1 month'\'' GROUP BY p.id, p.name ORDER BY revenue DESC LIMIT 10",
     "explanation": "从订单表中筛选最近一个月的数据,按产品分组统计销售额,按收入降序排列",
     "estimatedRows": 10,
     "performanceTips": [
       "已在 order_date 上创建索引可加速查询",
       "考虑添加 WHERE o.status = '\''completed'\'' 仅统计已完成订单"
     ],
     "warnings": [
       "如果订单表数据量巨大(>100万行),建议先预估查询时间"
     ]
   }
   ```

---

## Testing

### Backend Tests

```bash
cd backend

# 运行所有测试
uv run pytest

# 运行导出相关测试
uv run pytest tests/test_export.py -v

# 运行 API 测试
uv run pytest tests/test_api_export.py -v
```

### Frontend Tests

```bash
cd frontend

# 运行所有测试
npm run test

# 运行导出组件测试
npm run test -- src/components/export
```

### Manual Testing

使用 VSCode REST Client 扩展测试 `fixtures/test.rest`:

```http
### 创建导出任务
POST http://localhost:8000/api/v1/dbs/postgres_db/export
Content-Type: application/json

{
  "sql": "SELECT * FROM users LIMIT 100",
  "format": "csv",
  "exportAll": false
}

### 查询任务状态
GET http://localhost:8000/api/v1/tasks/{{taskId}}

### 下载导出文件
GET http://localhost:8000/api/v1/exports/download/export-{{uuid}}.csv
```

---

## Troubleshooting

### Problem: 导出文件中文乱码

**症状**: Excel 打开 CSV 文件时中文显示为乱码。

**原因**: Excel 需要带 BOM 的 UTF-8 编码。

**解决方案**:
- 后端已使用 `utf-8-sig` 编码(带 BOM)
- 确保前端下载时未更改编码
- Excel 中使用"数据 → 从文本/CSV导入"功能

---

### Problem: 导出任务一直处于 pending 状态

**症状**: 任务创建后进度始终为 0,status 一直是 `pending`。

**原因**: 后台 worker 未启动或崩溃。

**解决方案**:
```bash
# 检查后端日志
cd backend
tail -f logs/app.log

# 重启后端服务
uv run uvicorn app.main:app --reload

# 检查 TaskManager 是否初始化
# 在 app/main.py 中确认:
# task_manager = TaskManager.get_instance()
# await task_manager.start_worker()
```

---

### Problem: 并发限制不生效

**症状**: 单用户可以同时启动超过 3 个导出任务。

**原因**: 用户标识符未正确传递或识别。

**解决方案**:
```python
# 确保请求头包含用户标识
# 前端:
headers: {
  'X-User-ID': 'user-123'
}

# 后端 API:
def get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> str:
    return x_user_id
```

---

### Problem: AI 建议不显示

**症状**: 查询完成后没有看到 AI 导出建议。

**原因**:
1. AI 分析失败(检查 `OPENAI_API_KEY`)
2. 查询结果不符合建议条件(如行数太少)
3. AI 助手开关未开启

**解决方案**:
```bash
# 验证 OpenAI API Key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# 检查 AI 助手设置
# 前端 localStorage: aiAssistantEnabled = true

# 查看后端日志
tail -f backend/logs/app.log | grep "AI"
```

---

### Problem: 文件大小估算不准确

**症状**: 实际文件大小与预估差异很大(>50%)。

**原因**:
1. 使用元数据估算(准确性较低)
2. 数据分布不均匀
3. 包含变长字段(如 TEXT)

**解决方案**:
```typescript
// 使用采样精确估算
const checkResult = await checkExportSize({
  sql: querySQL,
  format: 'csv',
  useSampling: true,  // 启用采样
  sampleSize: 500,    // 增加采样量
});
```

---

## Performance Tips

### 1. 优化导出性能

```python
# 批量处理大小调整
BATCH_SIZE = 1000  # 默认值

# 对于快速网络: 增大批处理
BATCH_SIZE = 5000

# 对于慢速网络: 减小批处理
BATCH_SIZE = 500
```

### 2. 减少内存占用

```python
# 使用流式响应(已默认实现)
StreamingResponse(generate_csv(), media_type="text/csv")

# 避免一次性加载全部数据
# ❌ 错误:
rows = await fetch_all_rows()  # 全部加载到内存

# ✅ 正确:
async for batch in fetch_batches(batch_size=1000):
    yield serialize_batch(batch)
```

### 3. 数据库查询优化

```sql
-- 添加索引加速导出
CREATE INDEX idx_order_date ON orders(order_date);

-- 避免导出不必要的列
SELECT col1, col2, col3 FROM table  -- ✅
SELECT * FROM table  -- ❌ (包含不需要的列)

-- 使用 WHERE 减少数据量
SELECT * FROM large_table WHERE status = 'active'  -- ✅
```

---

## Next Steps

1. **阅读完整文档**:
   - [数据模型](./data-model.md)
   - [API 规范](./contracts/api-v1.yaml)
   - [研究报告](./research.md)

2. **运行集成测试**:
   ```bash
   make test-backend
   make test-frontend
   ```

3. **查看示例代码**:
   - 后端: `backend/app/services/export.py`
   - 前端: `frontend/src/components/export/`

4. **提交 PR**:
   - 确保所有测试通过
   - 代码已格式化 (`make format`)
   - 更新文档

---

## Getting Help

- **文档**: 查看 `CLAUDE.md` 和 `docs/` 目录
- **Issues**: 在 GitHub 上提交 issue
- **日志**: 检查 `backend/logs/app.log`
- **API 文档**: 访问 http://localhost:8000/docs

---

**Happy Exporting! 🚀**
