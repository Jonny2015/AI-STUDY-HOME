# Feature Specification: 修复项目设置和单元测试

**Feature Branch**: `001-fix-setup-tests`
**Created**: 2025-12-27
**Status**: Draft
**Input**: User description: "make setup 若出错则修复它；确保前后端 unit test 都通过。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 首次项目设置 (Priority: P1)

新开发者克隆项目仓库后，需要快速设置开发环境以便开始工作。开发者期望运行一条简单的命令就能安装所有必需的依赖，并看到清晰的成功提示。

**Why this priority**: 这是开发者接触项目的第一步，如果设置过程失败或遇到困难，会造成糟糕的第一印象并阻碍后续开发工作。

**Independent Test**: 新开发者可以在干净的环境中运行 `make setup`，完成后能够成功运行 `make dev-backend` 和 `make dev-frontend` 启动开发服务器。

**Acceptance Scenarios**:

1. **Given** 开发者克隆了项目到本地，**When** 在项目根目录运行 `make setup`，**Then** 命令成功完成，显示"项目初始化完成！"，没有错误信息
2. **Given** 开发者运行 `make setup`，**When** 后端依赖安装过程执行，**Then** uv sync 成功安装所有 Python 依赖，包括开发依赖
3. **Given** 开发者运行 `make setup`，**When** 前端依赖安装过程执行，**Then** npm install 成功安装所有 Node.js 依赖
4. **Given** 开发者首次运行 `make setup`，**When** 依赖安装完成，**Then** 可以成功启动后端服务器（`make dev-backend`）和前端服务器（`make dev-frontend`）

---

### User Story 2 - 验证代码质量 (Priority: P2)

开发者在提交代码前需要运行单元测试以确保代码质量。测试应该能够快速执行并提供清晰的反馈，帮助开发者发现和修复问题。

**Why this priority**: 持续的代码质量保证对团队协作和项目健康至关重要，但可以在设置完成后进行。

**Independent Test**: 开发者可以在设置完成后运行 `make test-backend` 和 `make test-frontend`，测试应该通过或提供明确的失败原因。

**Acceptance Scenarios**:

1. **Given** 开发者完成了代码修改，**When** 运行 `make test-backend`，**Then** 后端单元测试执行并显示通过/失败状态
2. **Given** 后端测试执行完成，**When** 查看测试输出，**Then** 所有单元测试通过，没有未通过的测试用例
3. **Given** 开发者完成了前端代码修改，**When** 运行 `make test-frontend`，**Then** 前端 E2E 测试执行并显示通过/失败状态
4. **Given** 前端测试执行完成，**When** 查看测试输出，**Then** 所有 E2E 测试通过，浏览器自动关闭
5. **Given** 开发者想要运行所有测试，**When** 执行 `make test`，**Then** 后端和前端测试依次执行并显示汇总结果

---

### User Story 3 - 故障排查和错误处理 (Priority: P3)

当设置或测试过程中出现错误时，开发者需要清晰的错误信息以便快速定位和解决问题。

**Why this priority**: 良好的错误处理能显著改善开发体验，但不是 MVP 的核心功能。

**Independent Test**: 开发者可以在出现错误时根据错误信息快速定位问题并采取正确的解决措施。

**Acceptance Scenarios**:

1. **Given** 开发者运行 `make setup`，**When** uv 命令不存在，**Then** 显示清晰的错误信息提示安装 uv
2. **Given** 开发者运行 `make setup`，**When** npm 命令不存在，**Then** 显示清晰的错误信息提示安装 Node.js 和 npm
3. **Given** 开发者运行 `make test-backend`，**When** 没有测试文件存在，**Then** 显示友好的提示信息而不是错误
4. **Given** 开发者运行 `make test-frontend`，**When** Playwright 浏览器未安装，**Then** 显示自动安装命令提示

---

### Edge Cases

- 如果网络中断导致依赖安装失败，重新运行 `make setup` 应该能够从断点继续或重新开始
- 如果 Python 版本不符合要求（< 3.11），应该显示明确的错误信息
- 如果 Node.js 版本过旧，应该显示版本要求提示
- 如果磁盘空间不足，应该显示清晰的错误信息
- 如果依赖包有安全漏洞，应该有提示机制（但不阻止安装）

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `make setup` 命令必须成功安装所有后端依赖，包括运行时依赖和开发依赖
- **FR-002**: `make setup` 命令必须成功安装所有前端依赖，包括运行时依赖和开发依赖
- **FR-003**: 后端单元测试必须存在并且能够成功运行，覆盖核心业务逻辑
- **FR-004**: 前端 E2E 测试必须能够成功运行，覆盖主要用户交互流程
- **FR-005**: 依赖安装失败时必须提供清晰的错误信息和解决建议
- **FR-006**: 测试失败时必须显示具体的失败原因和位置
- **FR-007**: Makefile 命令必须使用正确的路径和参数调用依赖管理工具
- **FR-008**: 后端测试必须能够独立运行，不依赖外部服务或使用 fixture/mock
- **FR-009**: 前端测试必须在测试环境中运行，不干扰开发环境
- **FR-010**: 所有测试命令必须返回正确的退出码（0 表示成功，非 0 表示失败）

### Key Entities

- **后端依赖**: Python 包及其版本，由 pyproject.toml 定义
- **前端依赖**: Node.js 包及其版本，由 package.json 定义
- **测试用例**: 验证代码功能的独立测试单元
- **测试 Fixture**: 测试用的模拟数据和对象
- **开发环境配置**: Makefile 中定义的构建和测试命令

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 新开发者可以在 5 分钟内完成项目设置（假设网络良好）
- **SC-002**: `make setup` 命令成功率达到 100%（在标准开发环境下）
- **SC-003**: 后端单元测试在 30 秒内完成执行
- **SC-004**: 前端 E2E 测试在 2 分钟内完成执行
- **SC-005**: 代码测试覆盖率达到至少 60%（后端核心功能模块）
- **SC-006**: 所有测试命令返回正确的退出码，便于 CI/CD 集成
- **SC-007**: 开发者能够根据错误信息在 10 分钟内解决常见的设置问题
- **SC-008**: `make test` 命令能够验证前后端代码质量，作为代码提交前的检查点

## Assumptions

- 开发者的操作系统为 macOS 或 Linux（Makefile 语法兼容）
- 开发者已安装 Git 用于克隆项目
- 开发者有权限安装全局工具（uv, npm, Node.js）
- 网络连接正常，可以访问 PyPI 和 npm registry
- 后端使用 SQLite 作为默认的测试数据库（已在 fixtures 目录配置）
- 前端 E2E 测试使用 Playwright，需要在测试前安装浏览器
- 不需要修改数据库相关的 Makefile 命令（db-init, db-reset 等）
- 不需要添加新的测试框架或工具

## Out of Scope

- 性能测试和压力测试
- 集成测试的外部服务设置（如真实的 PostgreSQL/MySQL 数据库）
- CI/CD 流水线配置
- Docker 容器化配置
- 跨平台支持（Windows 系统）
- 依赖包的安全审计和更新
- 测试报告生成和覆盖率可视化
