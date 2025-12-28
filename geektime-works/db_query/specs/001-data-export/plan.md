# Implementation Plan: 数据导出功能模块

**Branch**: `001-data-export` | **Date**: 2025-12-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-data-export/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

为数据库查询工具新增数据导出功能模块,支持将查询结果导出为 CSV、JSON、Markdown 三种格式。用户可选择导出当前页或全部数据,并集成 AI 助手提供智能导出建议和查询生成。功能包括实时进度反馈、文件大小限制(100MB)、超时控制(5分钟)、并发限制(每用户3个任务)以及条件审计日志记录。

**技术方法**:
- 后端使用 FastAPI 创建导出服务,通过流式响应处理大文件导出
- 前端使用 Refine + Ant Design 实现导出 UI 和进度跟踪
- AI 集成通过 OpenAI API 提供智能导出建议和 SQL 生成

## Technical Context

**Language/Version**:
- 后端: Python 3.12+
- 前端: TypeScript 5.9+

**Primary Dependencies**:
- 后端: FastAPI 0.121+, SQLModel 0.0.27, OpenAI 2.8+, asyncpg 0.30+, aiomysql 0.2+
- 前端: React 19, Refine 5, Ant Design 5, Monaco Editor, Vite 7

**Storage**:
- PostgreSQL (应用数据库,存储连接和查询历史)
- 文件系统 (临时导出文件存储)

**Testing**:
- 后端: pytest + pytest-asyncio + httpx
- 前端: vitest + @testing-library/react

**Target Platform**:
- Web 应用 (支持现代浏览器: Chrome, Firefox, Safari, Edge)
- 后端运行在 Linux/macOS

**Project Type**: web (前后端分离架构)

**Performance Goals**:
- 30秒内完成 10,000 行数据的 CSV 导出
- 进度更新频率不低于每秒 1 次
- 支持最大 100MB 文件导出
- 5 分钟超时限制

**Constraints**:
- 仅允许导出 SELECT 查询结果
- 单用户并发导出任务不超过 3 个
- 文件大小限制 100MB
- 必须正确处理特殊字符、空值和二进制数据

**Scale/Scope**:
- 支持 PostgreSQL 和 MySQL 数据库
- 预期并发用户数: <50
- 单次导出最大行数: ~1,000,000 行

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Initial Check (Pre-Design)**: ✅ PASSED
- 项目尚未定义项目宪法文件(constitution.md 为模板状态)
- 当前实现遵循现有项目架构和编码规范
- 符合适配器模式,不破坏现有架构
- 遵循 TDD 原则,将先编写测试再实现功能

**Re-check (Post-Design)**: ✅ PASSED

**设计阶段验证**:
1. **架构一致性**: ✅
   - 使用现有适配器模式(DatabaseAdapter)
   - 服务层(app/services/export.py)符合现有架构
   - 模型层(app/models/export.py)使用 SQLModel

2. **简单性原则**: ✅
   - 轮询机制替代 WebSocket(简单可靠)
   - 内存 TaskManager 替代 Redis(减少依赖)
   - 分阶段实现(P1→P2→P3),避免过度工程化

3. **可测试性**: ✅
   - 服务层与 API 层分离
   - 使用依赖注入(Session, adapter)
   - 每个功能都有对应的测试策略

4. **性能约束**: ✅
   - 流式响应处理大文件(避免内存溢出)
   - 分批处理(batch_size=1000)减少内存峰值
   - 文件大小限制(100MB)和超时控制(5分钟)

5. **安全性**: ✅
   - 并发限制(单用户3个任务)
   - SQL 验证(仅允许 SELECT)
   - 审计日志记录所有导出操作

**最终结论**: 无宪法违规,设计架构符合项目最佳实践

## Project Structure

### Documentation (this feature)

```text
specs/001-data-export/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── api-v1.yaml      # API OpenAPI 规范
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   ├── database.py          # 现有 DatabaseConnection 模型
│   │   ├── query.py             # 现有 QueryHistory 模型
│   │   └── export.py            # 新增: ExportTask 实体模型
│   ├── services/
│   │   ├── sql_validator.py     # 现有: SQL 验证
│   │   ├── nl2sql.py            # 现有: 自然语言转 SQL
│   │   └── export.py            # 新增: 导出服务 (格式转换、流式处理)
│   ├── api/v1/
│   │   ├── databases.py         # 现有: 数据库管理 API
│   │   ├── queries.py           # 现有: 查询执行 API
│   │   └── export.py            # 新增: 导出 API 端点
│   └── core/
│       ├── config.py            # 现有: 配置管理
│       └── security.py          # 现有: 安全配置
└── tests/
    ├── test_export.py           # 新增: 导出服务单元测试
    └── test_api_export.py       # 新增: 导出 API 集成测试

frontend/
├── src/
│   ├── components/
│   │   ├── query/
│   │   │   ├── SqlEditor.tsx    # 现有: SQL 编辑器
│   │   │   ├── ResultTable.tsx  # 现有: 结果表格
│   │   │   └── ExportButton.tsx # 新增: 导出按钮组件
│   │   └── export/
│   │       ├── ExportDialog.tsx # 新增: 导出配置对话框
│   │       ├── ExportProgress.tsx # 新增: 导出进度显示
│   │       └── AiExportAssistant.tsx # 新增: AI 导出助手
│   ├── pages/
│   │   └── query/
│   │       └── QueryPage.tsx    # 修改: 集成导出功能
│   ├── services/
│   │   └── export.ts            # 新增: 导出 API 客户端
│   └── types/
│       └── export.ts            # 新增: 导出相关类型定义
└── tests/
    └── components/
        └── export/              # 新增: 导出组件测试
```

**Structure Decision**:
- 选择前后端分离的 Web 应用架构 (Option 2)
- 后端采用服务层架构,在 `app/services/export.py` 实现导出逻辑
- 前端使用 Refine 框架,组件化设计,遵循现有目录结构
- 遵循现有适配器模式,导出功能通过 DatabaseAdapter 接口访问数据

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

无需填写 - 未发现宪法违规
