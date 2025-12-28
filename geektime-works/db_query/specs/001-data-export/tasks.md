# Tasks: 数据导出功能模块

**Input**: Design documents from `/specs/001-data-export/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/api-v1.yaml ✅

**Tests**: 后端使用 pytest + pytest-asyncio,前端使用 vitest + @testing-library/react

**Organization**: 任务按用户故事分组,以实现独立实现和测试

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行(不同文件,无依赖)
- **[Story]**: 任务所属用户故事(US1, US2, US3)
- 包含精确文件路径

## Path Conventions

- **后端**: `backend/app/` (源码), `backend/tests/` (测试)
- **前端**: `frontend/src/` (源码), `frontend/tests/` (测试)

---

## Phase 1: Setup (共享基础设施)

**Purpose**: 项目初始化和数据库结构

- [X] T001 创建数据库迁移文件,添加 ExportTask 和 AISuggestionAnalytics 表结构,使用 alembic revision 命令生成迁移脚本
- [X] T002 执行数据库迁移,应用 exporttasks 和 aisuggestionanalytics 表结构,运行 alembic upgrade head
- [X] T003 [P] 在 backend/app/core/config.py 添加导出相关配置项(最大文件大小 100MB、超时时间 5分钟、单用户并发限制 3)
- [X] T004 [P] 创建导出目录结构 backend/app/services/export.py、backend/app/models/export.py、backend/app/api/v1/export.py

**Checkpoint**: 数据库和项目结构就绪

---

## Phase 2: Foundational (阻塞前提条件)

**Purpose**: 核心基础设施,必须在任何用户故事实现前完成

**⚠️ CRITICAL**: 此阶段完成前不能开始任何用户故事工作

- [X] T005 在 backend/app/models/export.py 创建 ExportFormat 枚举类,定义 CSV/JSON/MARKDOWN 三个导出格式枚举值
- [X] T006 [P] 在 backend/app/models/export.py 创建 ExportScope 枚举类,定义 CURRENT_PAGE/ALL_DATA 两个导出范围枚举值
- [X] T007 [P] 在 backend/app/models/export.py 创建 TaskStatus 枚举类,定义 PENDING/RUNNING/COMPLETED/FAILED/CANCELLED 五个任务状态枚举值
- [X] T008 在 backend/app/models/export.py 创建 ExportTask SQLModel 类,定义所有字段(task_id, user_id, database_name, sql_text, export_format, export_scope, file_name, file_path, file_size_bytes, row_count, status, progress, error_message, started_at, completed_at, execution_time_ms, created_at)及验证规则
- [X] T009 [P] 在 backend/app/models/export.py 创建 ExportSuggestionResponse 枚举类,定义 ACCEPTED/REJECTED/IGNORED/MODIFIED 四个AI响应枚举值
- [X] T010 [P] 在 backend/app/models/export.py 创建 AISuggestionAnalytics SQLModel 类,定义所有字段(suggestion_id, database_name, suggestion_type, sql_context, row_count, confidence, suggested_format, suggested_scope, user_response, response_time_ms, suggested_at, responded_at)及验证规则
- [X] T011 在 backend/app/models/schemas.py 创建 ExportRequest Pydantic 模型,定义导出请求字段(sql, format, exportAll)并配置 to_camel 别名生成器
- [X] T012 [P] 在 backend/app/models/schemas.py 创建 ExportCheckRequest 和 ExportCheckResponse Pydantic 模型,定义文件大小检查请求和响应字段
- [X] T013 [P] 在 backend/app/models/schemas.py 创建 TaskResponse Pydantic 模型,定义任务状态响应字段(taskId, status, progress, fileUrl, error)
- [X] T014 在 backend/app/models/schemas.py 创建 SizeEstimate Pydantic 模型,定义文件大小估算字段(estimatedBytes, estimatedMb, bytesPerRow, method, confidence, sampleSize)
- [X] T015 [P] 在 backend/app/models/schemas.py 创建 ExportIntentRequest 和 ExportIntentResponse Pydantic 模型,定义AI意图分析请求和响应字段
- [X] T016 [P] 在 backend/app/models/schemas.py 创建 GenerateSQLRequest 和 GenerateSQLResponse Pydantic 模型,定义SQL生成请求和响应字段
- [X] T017 [P] 在 backend/app/models/schemas.py 创建 ProactiveSuggestionRequest 和 ProactiveSuggestionResponse Pydantic 模型,定义主动建议请求和响应字段
- [X] T018 [P] 在 backend/app/models/schemas.py 创建 TrackResponseRequest 和 AnalyticsResponse Pydantic 模型,定义响应跟踪和分析数据响应字段
- [X] T019 在 backend/app/services/export.py 创建 TaskManager 单例类,实现任务队列(Dict[task_id, Task])和并发控制(asyncio.Semaphore(3))
- [X] T020 在 backend/app/services/export.py 创建 ExportService 类,实现文件大小估算方法 estimate_file_size,支持 metadata/sample/actual 三种估算方法
- [X] T021 [P] 在 backend/app/services/export.py 实现 ExportService._validate_export_constraints 方法,检查文件大小限制(100MB)并发限制(单用户3个任务)
- [X] T022 [P] 在 backend/app/services/export.py 实现 ExportService._generate_csv_row 方法,将单行数据转换为 CSV 格式字符串,处理特殊字符转义
- [X] T023 [P] 在 backend/app/services/export.py 实现 ExportService._generate_json_row 方法,将单行数据转换为 JSON 格式,处理 datetime/Decimal/bytes 等特殊类型
- [X] T024 [P] 在 backend/app/services/export.py 实现 ExportService._generate_markdown_row 方法,将单行数据转换为 Markdown 表格行格式
- [X] T025 在 backend/app/services/export.py 实现 ExportService._serialize_for_json 方法,使用 Pydantic jsonable_encoder 处理数据库特殊类型序列化
- [X] T026 在 backend/app/services/export.py 实现 ExportService._generate_filename 方法,根据 task_id 和导出格式生成文件名(export-<uuid>.<ext>)
- [X] T027 在 backend/app/services/export.py 创建 ExportService.export_to_csv 方法,使用异步生成器实现流式 CSV 导出,编码使用 utf-8-sig
- [X] T028 在 backend/app/services/export.py 创建 ExportService.export_to_json 方法,使用异步生成器实现流式 JSON 导出,使用自定义编码器
- [X] T029 在 backend/app/services/export.py 创建 ExportService.export_to_markdown 方法,生成 Markdown 表格格式文件
- [X] T030 在 backend/app/services/export.py 实现 ExportService.execute_export 方法,协调整个导出流程(验证、执行、进度更新、文件保存)
- [X] T031 在 backend/app/services/export.py 实现 ExportService._update_progress 方法,更新任务进度到 TaskManager
- [X] T032 [P] 在 backend/app/services/export.py 实现 ExportService._cleanup_task 方法,清理已完成任务的临时资源
- [X] T033 在 backend/app/services/export.py 实现 ExportService.get_task 方法,从 TaskManager 获取任务状态
- [X] T034 在 backend/app/services/export.py 实现 ExportService.cancel_task 方法,取消正在运行的任务并清理资源
- [X] T035 在 backend/app/services/export.py 实现 ExportService.check_export_size 方法,调用 estimate_file_size 并返回检查结果和警告
- [X] T036 创建后端 API 路由文件 backend/app/api/v1/export.py,初始化 FastAPI APIRouter 并添加导出相关路由前缀 /export
- [X] T037 在 backend/app/api/v1/export.py 实现 POST /api/v1/dbs/{name}/export 端点,创建导出任务并返回 task_id
- [X] T038 [P] 在 backend/app/api/v1/export.py 实现 POST /api/v1/dbs/{name}/export/check 端点,检查预估文件大小并返回建议
- [X] T039 [P] 在 backend/app/api/v1/export.py 实现 GET /api/v1/tasks/{task_id} 端点,查询任务状态和进度
- [X] T040 [P] 在 backend/app/api/v1/export.py 实现 DELETE /api/v1/tasks/{task_id} 端点,取消正在执行的任务
- [X] T041 [P] 在 backend/app/api/v1/export.py 实现 GET /api/v1/exports/download/{filename} 端点,下载已完成的导出文件
- [X] T042 创建前端类型定义文件 frontend/src/types/export.ts,定义导出相关 TypeScript 类型(ExportFormat, ExportScope, TaskStatus, ExportRequest, TaskResponse, ExportCheckResponse 等)
- [X] T043 [P] 创建前端 API 服务文件 frontend/src/services/export.ts,实现导出 API 客户端方法(createExport, checkExportSize, getTaskStatus, cancelTask, downloadFile)
- [X] T044 创建前端导出按钮组件 frontend/src/components/query/ExportButton.tsx,实现导出按钮和格式选择下拉菜单

**Checkpoint**: 基础架构完成 - 用户故事实现现在可以并行开始

---

## Phase 3: User Story 1 - 手动导出查询结果 (Priority: P1) 🎯 MVP

**Goal**: 用户可以将查询结果手动导出为 CSV/JSON/MD 格式,支持导出当前页或全部数据

**Independent Test**: 执行查询 → 点击导出按钮 → 选择格式和范围 → 验证文件生成成功并下载

### Tests for User Story 1

- [X] T045 [P] [US1] 编写导出文件大小估算的单元测试,测试 metadata/sample/actual 三种估算方法,创建 backend/tests/test_export_size_estimation.py
- [X] T046 [P] [US1] 编写 CSV 格式转换的单元测试,验证特殊字符、中文、换行符的正确转义,创建 backend/tests/test_export_csv.py
- [X] T047 [P] [US1] 编写 JSON 格式转换的单元测试,验证 datetime/Decimal/bytes 类型的正确序列化,创建 backend/tests/test_export_json.py
- [X] T048 [P] [US1] 编写导出约束验证的单元测试,验证文件大小限制和并发限制检查,创建 backend/tests/test_export_constraints.py
- [X] T049 [P] [US1] 编写导出 API 端点的集成测试,测试创建任务、查询状态、下载文件的完整流程,创建 backend/tests/test_api_export.py
- [X] T050 [P] [US1] 编写导出按钮组件的单元测试,验证点击事件和格式选择逻辑,创建 frontend/tests/components/export/ExportButton.test.tsx

### Implementation for User Story 1

- [X] T051 [P] [US1] 创建前端导出配置对话框组件 frontend/src/components/export/ExportDialog.tsx,实现导出格式选择(CSV/JSON/MD)、导出范围选择(当前页/全部数据)、预估文件大小显示
- [X] T052 [P] [US1] 创建前端导出进度显示组件 frontend/src/components/export/ExportProgress.tsx,实现进度条、百分比显示、取消按钮、完成提示
- [X] T053 [US1] 集成导出功能到查询页面 frontend/src/pages/queries/execute.tsx,在 ResultTable 组件旁添加 ExportButton,点击后显示 ExportDialog
- [X] T054 [US1] 实现前端导出流程逻辑,在 ExportDialog 中调用 checkExportSize API 检查文件大小,显示警告或阻止导出
- [X] T055 [US1] 实现前端导出流程逻辑,在 ExportDialog 确认后调用 createExport API 创建任务并轮询任务状态
- [X] T056 [US1] 实现前端导出进度更新,通过轮询 getTaskStatus API(1秒间隔)更新 ExportProgress 组件,显示实时进度
- [X] T057 [US1] 实现前端导出完成处理,任务完成后调用 downloadFile API 下载文件,显示成功提示并关闭进度对话框
- [X] T058 [US1] 实现前端导出错误处理,捕获任务失败状态,显示错误信息并提供重试选项
- [X] T059 [US1] 实现前端导出取消逻辑,在 ExportProgress 组件中点击取消按钮调用 cancelTask API,清理前端状态
- [X] T060 [US1] 在后端 ExportService.export_to_csv 方法中实现分批处理逻辑,使用 batch_size=1000 减少内存峰值
- [X] T061 [US1] 在后端 ExportService.export_to_csv 方法中添加进度回调,每处理完一批数据调用 _update_progress 更新进度
- [X] T062 [US1] 在后端 ExportService.export_to_json 方法中实现分批处理逻辑,使用 batch_size=1000 减少内存峰值
- [X] T063 [US1] 在后端 ExportService.export_to_json 方法中添加进度回调,每处理完一批数据调用 _update_progress 更新进度
- [X] T064 [US1] 在后端 ExportService.export_to_markdown 方法中实现分批处理逻辑,使用 batch_size=1000 减少内存峰值
- [X] T065 [US1] 在后端 ExportService.export_to_markdown 方法中添加进度回调,每处理完一批数据调用 _update_progress 更新进度
- [X] T066 [US1] 在后端 ExportService.execute_export 方法中实现文件保存逻辑,将生成的文件保存到临时目录并更新 file_path 字段
- [X] T067 [US1] 在后端 ExportService.execute_export 方法中添加错误处理,捕获导出过程中的异常,更新任务状态为 failed 并记录 error_message
- [X] T068 [US1] 在后端 ExportService.execute_export 方法中添加超时控制,使用 asyncio.wait_for 实现 5 分钟超时限制
- [X] T069 [US1] 在后端 ExportService.execute_export 方法中添加审计日志记录,记录用户 ID、时间戳、数据源、格式、文件大小等基本信息
- [X] T070 [US1] 在后端 POST /api/v1/dbs/{name}/export 端点中实现并发限制检查,查询 TaskManager 中用户的活跃任务数量,超过 3 个则返回 429 错误
- [X] T071 [US1] 在后端 POST /api/v1/dbs/{name}/export 端点中实现 SQL 验证,调用 sql_validator 验证仅允许 SELECT 查询
- [X] T072 [US1] 在后端 GET /api/v1/exports/download/{filename} 端点中实现文件流式下载,设置正确的 Content-Disposition 头和 MIME 类型
- [X] T073 [US1] 在后端 GET /api/v1/exports/download/{filename} 端点中添加文件存在性检查,文件不存在或已过期返回 404 错误
- [X] T074 [US1] 在前端 ExportButton 组件中实现空结果检查,查询结果为空时显示"无数据可导出"提示并禁用导出按钮

**Checkpoint**: 用户可以手动导出查询结果为 CSV/JSON/MD 格式

---

## Phase 4: User Story 2 - AI 助手辅助导出 (Priority: P2)

**Goal**: AI 助手在查询完成后主动询问是否需要导出,并根据结果提供智能建议

**Independent Test**: 开启 AI 助手 → 执行查询 → AI 提示导出建议 → 用户确认 → 自动执行导出

### Tests for User Story 2

- [ ] T075 [P] [US2] 编写 AI 导出意图分析的单元测试,验证不同查询场景下的建议生成逻辑,创建 backend/tests/test_ai_export_intent.py
- [ ] T076 [P] [US2] 编写主动导出建议生成的单元测试,验证建议文本和快捷操作的生成,创建 backend/tests/test_ai_proactive_suggestion.py
- [ ] T077 [P] [US2] 编写 AI 响应跟踪的单元测试,验证用户响应记录和分析数据统计,创建 backend/tests/test_ai_response_tracking.py
- [ ] T078 [P] [US2] 编写 AI 导出端点的集成测试,测试意图分析、建议生成、响应跟踪的完整流程,创建 backend/tests/test_api_ai_export.py
- [ ] T079 [P] [US2] 编写 AI 导出助手组件的单元测试,验证 AI 建议显示和用户交互逻辑,创建 frontend/tests/components/export/AiExportAssistant.test.tsx

### Implementation for User Story 2

- [ ] T080 [P] [US2] 在 backend/app/services/export.py 创建 AIExportService 类,实现 AI 导出辅助功能
- [ ] T081 [P] [US2] 在 AIExportService 中实现 analyze_export_intent 方法,使用 OpenAI API 分析查询结果,判断是否应该建议导出
- [ ] T082 [P] [US2] 在 AIExportService 中实现 generate_proactive_suggestion 方法,生成友好的导出建议文本和快捷操作按钮
- [ ] T083 [P] [US2] 在 AIExportService 中实现 track_suggestion_response 方法,记录用户对 AI 建议的响应到 AISuggestionAnalytics 表
- [ ] T084 [P] [US2] 在 AIExportService 中实现 get_export_analytics 方法,统计 AI 建议的接受率、响应分布等分析数据
- [ ] T085 [US2] 在后端 POST /api/v1/export/analyze-intent 端点中调用 AIExportService.analyze_export_intent,返回导出意图分析结果
- [ ] T086 [US2] 在后端 POST /api/v1/export/proactive-suggestion 端点中调用 AIExportService.generate_proactive_suggestion,返回主动建议文本和快捷操作
- [ ] T087 [US2] 在后端 POST /api/v1/export/track-response 端点中调用 AIExportService.track_suggestion_response,记录用户响应
- [ ] T088 [US2] 在后端 GET /api/v1/export/analytics 端点中调用 AIExportService.get_export_analytics,返回 AI 效果分析数据
- [ ] T089 [US2] 创建前端 AI 导出助手组件 frontend/src/components/export/AiExportAssistant.tsx,显示 AI 导出建议、快捷操作按钮和用户交互界面
- [ ] T090 [US2] 在前端 AiExportAssistant 组件中实现建议显示逻辑,根据 AI 返回的 suggestionText 和 quickActions 渲染建议界面
- [ ] T091 [US2] 在前端 AiExportAssistant 组件中实现用户交互逻辑,点击快捷操作按钮调用导出 API 并记录用户响应
- [ ] T092 [US2] 集成 AI 导出助手到查询页面,在 QueryPage.tsx 中添加 AiExportAssistant 组件,在查询结果显示后调用 analyze-intent API
- [ ] T093 [US2] 在前端查询页面中实现 AI 助手开关控制,添加用户偏好设置控制 AI 导出助手的开启/关闭状态
- [ ] T094 [US2] 在前端查询页面中实现 AI 建议触发逻辑,查询完成后根据用户设置的 AI 助手开关状态决定是否显示建议
- [ ] T095 [US2] 在前端 AiExportAssistant 组件中实现澄清问题显示,当 AI 返回 clarificationQuestion 时显示用户交互界面收集更多信息
- [ ] T096 [US2] 在前端 AiExportAssistant 组件中实现响应时间跟踪,记录从建议显示到用户操作的时间间隔,调用 track-response API

**Checkpoint**: AI 助手可以主动建议导出并协助用户完成导出

---

## Phase 5: User Story 3 - AI 智能生成导出查询 (Priority: P3)

**Goal**: AI 根据自然语言需求生成优化的导出 SQL 查询

**Independent Test**: 开启 AI 助手 → 输入自然语言需求 → AI 生成 SQL → 执行查询并导出

### Tests for User Story 3

- [ ] T097 [P] [US3] 编写 AI SQL 生成的单元测试,验证自然语言到 SQL 的转换准确性,创建 backend/tests/test_ai_sql_generation.py
- [ ] T098 [P] [US3] 编写 AI SQL 生成的集成测试,测试完整流程从自然语言到可执行的 SQL,创建 backend/tests/test_ai_sql_generation_integration.py
- [ ] T099 [P] [US3] 编写 AI SQL 生成组件的单元测试,验证用户输入和 SQL 显示逻辑,创建 frontend/tests/components/export/AiSqlGenerator.test.tsx

### Implementation for User Story 3

- [ ] T100 [P] [US3] 在 backend/app/services/export.py 的 AIExportService 中实现 generate_export_sql 方法,使用 OpenAI API 根据自然语言生成 SQL 查询
- [ ] T101 [P] [US3] 在 AIExportService.generate_export_sql 方法中集成数据库元数据,从 DatabaseMetadata 获取表和视图结构信息传递给 AI
- [ ] T102 [P] [US3] 在 AIExportService.generate_export_sql 方法中添加 SQL 验证,使用 sql_validator 验证生成的 SQL 仅包含 SELECT 语句
- [ ] T103 [P] [US3] 在 AIExportService.generate_export_sql 方法中添加性能优化建议,分析生成的 SQL 并返回索引建议和查询优化提示
- [ ] T104 [US3] 在后端 POST /api/v1/export/generate-sql 端点中调用 AIExportService.generate_export_sql,返回生成的 SQL、说明、预估行数和性能提示
- [ ] T105 [US3] 创建前端 AI SQL 生成组件 frontend/src/components/export/AiSqlGenerator.tsx,实现自然语言输入界面、SQL 显示和编辑功能
- [ ] T106 [US3] 在前端 AiSqlGenerator 组件中实现自然语言输入,提供文本输入框收集用户的导出需求描述
- [ ] T107 [US3] 在前端 AiSqlGenerator 组件中实现 SQL 显示,使用 Monaco Editor 显示 AI 生成的 SQL 查询,支持语法高亮和编辑
- [ ] T108 [US3] 在前端 AiSqlGenerator 组件中实现查询执行,点击执行按钮后将生成的 SQL 传递给查询页面执行并显示结果
- [ ] T109 [US3] 在前端 AiSqlGenerator 组件中实现导出联动,SQL 查询执行成功后自动显示导出选项,快速启动导出流程
- [ ] T110 [US3] 集成 AI SQL 生成到查询页面,在 QueryPage.tsx 中添加 AiSqlGenerator 组件标签页,提供 AI 辅助查询入口

**Checkpoint**: AI 可以根据自然语言生成导出查询并协助执行和导出

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 跨用户故事的改进和完善

- [ ] T111 [P] 更新后端 README.md,添加导出功能的使用说明、API 端点文档和配置说明
- [ ] T112 [P] 更新前端 README.md,添加导出组件的使用说明和类型定义文档
- [ ] T113 [P] 在后端添加导出日志记录,使用 Python logging 模块记录导出操作的关键事件(开始、进度、完成、错误)
- [ ] T114 [P] 在前端添加导出用户反馈,使用 Ant Design message 组件显示操作成功/失败的提示信息
- [ ] T115 优化后端导出性能,分析导出服务的瓶颈,优化数据库查询和文件 I/O 性能
- [ ] T116 [P] 优化前端导出 UI,改进导出对话框、进度显示、AI 助手的用户界面和交互体验
- [ ] T117 [P] 添加后端错误处理增强,细化导出过程中的错误类型,提供更友好的错误信息和建议
- [ ] T118 [P] 添加前端错误处理增强,捕获并显示网络错误、超时错误、并发限制错误等用户可理解的错误信息
- [ ] T119 实现导出文件清理任务,创建后台定时任务清理超过 7 天的临时导出文件
- [ ] T120 [P] 添加后端集成测试,编写跨服务的集成测试验证导出功能的完整流程
- [ ] T121 [P] 添加前端 E2E 测试,使用 Playwright 或 Cypress 编写导出功能的端到端测试
- [ ] T122 运行 quickstart.md 验证,按照快速开始文档执行所有测试场景,验证功能完整性

**Checkpoint**: 所有改进完成,功能就绪交付

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖 - 可立即开始
- **Foundational (Phase 2)**: 依赖 Setup 完成 - 阻塞所有用户故事
- **User Story 1 (Phase 3)**: 依赖 Foundational 完成 - 可独立测试
- **User Story 2 (Phase 4)**: 依赖 Foundational 完成 - 可独立测试,可选择集成 US1
- **User Story 3 (Phase 5)**: 依赖 Foundational 完成 - 可独立测试,可选择集成 US1/US2
- **Polish (Phase 6)**: 依赖所有期望的用户故事完成

### User Story Dependencies

- **User Story 1 (P1)**: Foundational 完成后即可开始 - 无其他用户故事依赖
- **User Story 2 (P2)**: Foundational 完成后即可开始 - 可选择与 US1 集成,但应独立可测试
- **User Story 3 (P3)**: Foundational 完成后即可开始 - 可选择与 US1/US2 集成,但应独立可测试

### Within Each User Story

- 测试必须先编写并确保 FAIL 再实现功能
- 枚举和 Pydantic 模型优先于服务层实现
- 服务层方法优先于 API 端点实现
- 核心功能优先于集成和优化
- 用户故事完成后再进入下一个优先级

### Parallel Opportunities

- Setup 阶段所有标记 [P] 的任务可并行
- Foundational 阶段所有标记 [P] 的枚举和 Pydantic 模型可并行
- Foundational 阶段所有标记 [P] 的服务层方法可并行
- Foundational 阶段所有标记 [P] 的 API 端点可并行
- User Story 1 所有标记 [P] 的测试可并行
- User Story 1 所有标记 [P] 的前端组件可并行
- User Story 2 所有标记 [P] 的测试可并行
- User Story 2 所有标记 [P] 的 AIExportService 方法可并行
- User Story 2 所有标记 [P] 的 API 端点可并行
- User Story 3 所有标记 [P] 的测试可并行
- User Story 3 所有标记 [P] 的 AIExportService 方法可并行
- Polish 阶段所有标记 [P] 的任务可并行
- 不同用户故事可由不同团队成员并行开发

---

## Parallel Example: User Story 1

```bash
# 并行启动 User Story 1 的所有测试:
Task T045: "编写导出文件大小估算的单元测试"
Task T046: "编写 CSV 格式转换的单元测试"
Task T047: "编写 JSON 格式转换的单元测试"
Task T048: "编写导出约束验证的单元测试"
Task T049: "编写导出 API 端点的集成测试"
Task T050: "编写导出按钮组件的单元测试"

# 并行启动 User Story 1 的前端组件:
Task T051: "创建前端导出配置对话框组件"
Task T052: "创建前端导出进度显示组件"
```

---

## Parallel Example: User Story 2

```bash
# 并行启动 User Story 2 的所有测试:
Task T075: "编写 AI 导出意图分析的单元测试"
Task T076: "编写主动导出建议生成的单元测试"
Task T077: "编写 AI 响应跟踪的单元测试"
Task T078: "编写 AI 导出端点的集成测试"
Task T079: "编写 AI 导出助手组件的单元测试"

# 并行启动 User Story 2 的 AI 服务方法:
Task T081: "实现 analyze_export_intent 方法"
Task T082: "实现 generate_proactive_suggestion 方法"
Task T083: "实现 track_suggestion_response 方法"
Task T084: "实现 get_export_analytics 方法"
```

---

## Parallel Example: User Story 3

```bash
# 并行启动 User Story 3 的所有测试:
Task T097: "编写 AI SQL 生成的单元测试"
Task T098: "编写 AI SQL 生成的集成测试"
Task T099: "编写 AI SQL 生成组件的单元测试"

# 并行启动 User Story 3 的 AI 服务方法:
Task T101: "集成数据库元数据到 SQL 生成"
Task T102: "添加 SQL 验证"
Task T103: "添加性能优化建议"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup (T001-T004)
2. 完成 Phase 2: Foundational (T005-T044) - **关键,阻塞所有用户故事**
3. 完成 Phase 3: User Story 1 (T045-T074)
4. **停止并验证**: 独立测试 User Story 1
5. 准备就绪后部署/演示 MVP

**MVP 交付内容**:
- ✅ 手动导出 CSV/JSON/MD 格式
- ✅ 导出当前页或全部数据
- ✅ 实时进度跟踪
- ✅ 文件大小限制和并发控制
- ✅ 完整的错误处理和用户反馈

### Incremental Delivery

1. 完成 Setup + Foundational → 基础架构就绪
2. 添加 User Story 1 → 独立测试 → 部署/演示 **(MVP!)**
3. 添加 User Story 2 → 独立测试 → 部署/演示
4. 添加 User Story 3 → 独立测试 → 部署/演示
5. 添加 Polish → 最终交付

每个用户故事都增加价值而不破坏已有功能。

### Parallel Team Strategy

多个开发者协作时:

1. 团队共同完成 Setup + Foundational
2. Foundational 完成后:
   - 开发者 A: User Story 1 (T045-T074)
   - 开发者 B: User Story 2 (T075-T096)
   - 开发者 C: User Story 3 (T097-T110)
3. 用户故事独立完成并集成

---

## Task Granularity Notes

### 细粒度任务设计原则

按照用户要求"按过程中的事件或动作维度分解",任务设计遵循以下原则:

1. **动作导向**: 每个任务描述一个明确的动作或事件
   - ✅ "创建 ExportFormat 枚举类"
   - ✅ "实现 ExportService.export_to_csv 方法"
   - ✅ "添加进度回调,每处理完一批数据调用 _update_progress"

2. **原子性**: 每个任务代表一个不可再分的原子操作
   - ✅ "创建后端 API 路由文件" - 单一文件创建
   - ✅ "实现 POST /api/v1/dbs/{name}/export 端点" - 单一端点实现
   - ✅ "添加文件存在性检查" - 单一功能添加

3. **独立性**: 任务之间无循环依赖,可独立执行
   - ✅ 枚举定义之间无依赖,可并行
   - ✅ Pydantic 模型之间无依赖,可并行
   - ✅ 服务方法之间有明确依赖顺序,通过任务 ID 体现

4. **可验证性**: 每个任务完成后可明确验证是否成功
   - ✅ 文件创建任务: 检查文件是否存在
   - ✅ 方法实现任务: 运行单元测试验证
   - ✅ API 端点任务: 使用 curl 或 Postman 测试

5. **粒度适中**: 既不过于宽泛也不过于琐碎
   - ✅ "创建前端导出配置对话框组件" - 适中的粒度(一个组件)
   - ❌ "实现前端导出功能" - 过于宽泛
   - ❌ "在 frontend/src/components/export/ExportDialog.tsx 第 10 行添加 import" - 过于琐碎

### 任务分解示例

**宽泛任务** (避免):
- ❌ "实现导出功能"
- ❌ "添加 AI 助手"

**细粒度任务** (推荐):
- ✅ "创建 ExportFormat 枚举类"
- ✅ "实现 ExportService.export_to_csv 方法"
- ✅ "在 ExportDialog 确认后调用 createExport API"
- ✅ "每处理完一批数据调用 _update_progress 更新进度"

---

## Notes

- **[P] 任务**: 不同文件,无依赖,可并行执行
- **[Story] 标签**: 将任务映射到特定用户故事以支持可追溯性
- **独立可测试**: 每个用户故事应独立完成和测试
- **TDD 原则**: 测试先编写并确保 FAIL,再实现功能
- **提交策略**: 每个任务或逻辑组完成后提交代码
- **验证检查点**: 在任何检查点停止以独立验证用户故事
- **避免**: 模糊任务、同一文件冲突、破坏独立性的跨用户故事依赖

---

## Summary

**Total Tasks**: 122 tasks
- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 40 tasks
- **Phase 3 (User Story 1)**: 30 tasks (15 tests + 15 implementation)
- **Phase 4 (User Story 2)**: 22 tasks (10 tests + 12 implementation)
- **Phase 5 (User Story 3)**: 14 tasks (7 tests + 7 implementation)
- **Phase 6 (Polish)**: 12 tasks

**Parallel Opportunities**:
- Setup: 3 tasks can run in parallel
- Foundational: 31 tasks can run in parallel
- User Story 1: 14 tasks can run in parallel
- User Story 2: 14 tasks can run in parallel
- User Story 3: 10 tasks can run in parallel
- Polish: 8 tasks can run in parallel

**MVP Scope** (User Story 1): 74 tasks total (4 setup + 40 foundational + 30 US1)
- 可独立交付完整的手动导出功能
- 支持三种格式(CSV/JSON/MD)和两种范围(当前页/全部数据)
- 包含进度跟踪、错误处理、并发控制和文件大小限制

**Incremental Value**:
- MVP (US1): 基础导出能力 ✅
- US2: AI 智能助手增强用户体验
- US3: AI SQL 生成降低使用门槛
- Polish: 生产就绪的质量和性能
