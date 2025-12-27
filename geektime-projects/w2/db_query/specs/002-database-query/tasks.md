# Tasks: Database Query Tool

**Input**: Design documents from `/specs/002-database-query/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Tests are NOT included in this task list (not explicitly requested in spec.md).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/app/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create backend and frontend directory structure per implementation plan
- [ ] T002 Initialize backend uv project with Python 3.11+ in backend/pyproject.toml
- [ ] T003 Initialize frontend npm project in frontend/package.json
- [ ] T004 [P] Install backend dependencies: FastAPI, uvicorn, Pydantic V2, sqlglot, openai, aiosqlite, asyncpg, aiomysql in backend/pyproject.toml
- [ ] T005 [P] Install frontend dependencies: React 18, Refine 5, Ant Design, Tailwind CSS, Monaco Editor, Vite in frontend/package.json
- [ ] T006 [P] Install backend dev dependencies: black, ruff, mypy, pytest, pytest-asyncio, httpx in backend/pyproject.toml
- [ ] T007 [P] Install frontend dev dependencies: Playwright, TypeScript types in frontend/package.json
- [ ] T008 [P] Configure backend mypy strict mode in backend/pyproject.toml
- [ ] T009 [P] Configure frontend TypeScript strict mode in frontend/tsconfig.json
- [ ] T010 [P] Create .env.example template in backend/.env.example with OPENAI_API_KEY placeholder
- [ ] T011 [P] Create README.md in backend/README.md with setup instructions
- [ ] T012 [P] Create README.md in frontend/README.md with setup instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Backend Foundation

- [ ] T013 Create FastAPI application entry point in backend/app/main.py with CORS middleware (allow all origins)
- [ ] T014 [P] Create configuration management module in backend/app/config.py to load OPENAI_API_KEY from environment
- [ ] T015 [P] Create SQLite database management module in backend/app/core/db.py to initialize ~/.db_query/db_query.db with databases and metadata tables
- [ ] T016 [P] Create SQL parser module in backend/app/core/sql_parser.py using sqlglot for validation and LIMIT injection
- [ ] T017 [P] Create security module in backend/app/core/security.py for URL validation and password masking
- [ ] T018 [P] Create logging utility in backend/app/utils/logging.py with structured logging setup
- [ ] T019 [P] Create base DatabaseAdapter abstract class in backend/app/adapters/base.py with connect, get_metadata, execute_query methods
- [ ] T020 [P] Create AdapterRegistry in backend/app/adapters/registry.py with register and get_adapter methods
- [ ] T021 [P] Create error response Pydantic model in backend/app/models/errors.py (ErrorResponse with camelCase)
- [ ] T022 Create global exception handler in backend/app/main.py to convert exceptions to ErrorResponse

### Frontend Foundation

- [ ] T023 [P] Create API service client in frontend/src/services/api.ts with axios instance configured for /api/v1
- [ ] T024 [P] Create TypeScript type definitions in frontend/src/types/index.ts mirroring backend Pydantic models (Database, TableMetadata, ColumnMetadata, QueryResult, etc.)
- [ ] T025 [P] Create Refine app setup in frontend/src/App.tsx with basic routing structure
- [ ] T026 [P] Create Tailwind CSS configuration in frontend/tailwind.config.js
- [ ] T027 [P] Create Vite configuration in frontend/vite.config.ts with proxy setup for backend API

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Manage Database Connections (Priority: P1) 🎯 MVP

**Goal**: Users can add, list, and delete database connections with automatic validation

**Independent Test**:
1. Add a PostgreSQL database connection → appears in list with "connected" status
2. Add an invalid connection → returns error with clear message
3. Delete a database → removed from list

### Backend Implementation for US1

- [ ] T028 [P] [US1] Create DatabaseResponse Pydantic model in backend/app/models/database.py with camelCase aliases
- [ ] T029 [P] [US1] Create DatabaseListResponse Pydantic model in backend/app/models/database.py with camelCase aliases
- [ ] T030 [P] [US1] Create AddDatabaseRequest Pydantic model in backend/app/models/database.py with URL validation
- [ ] T031 [P] [US1] Create PostgreSQLAdapter in backend/app/adapters/postgresql.py implementing DatabaseAdapter (connect, get_metadata, execute_query)
- [ ] T032 [P] [US1] Create MySQLAdapter in backend/app/adapters/mysql.py implementing DatabaseAdapter (connect, get_metadata, execute_query)
- [ ] T033 [P] [US1] Register adapters in backend/app/adapters/registry.py for postgresql and mysql types
- [ ] T034 [P] [US1] Create DatabaseService facade in backend/app/services/database_service.py with add_database, list_databases, delete_database, test_connection methods
- [ ] T035 [US1] Implement GET /api/v1/dbs endpoint in backend/app/api/v1/databases.py (router setup and list_databases handler)
- [ ] T036 [US1] Implement PUT /api/v1/dbs/{name} endpoint in backend/app/api/v1/databases.py (add_database handler with connection validation)
- [ ] T037 [US1] Implement DELETE /api/v1/dbs/{name} endpoint in backend/app/api/v1/databases.py (delete_database handler)
- [ ] T038 [US1] Register databases router in backend/app/main.py with /api/v1 prefix

### Frontend Implementation for US1

- [ ] T039 [P] [US1] Create DatabaseList component in frontend/src/components/DatabaseList.tsx using Refine's useList hook
- [ ] T040 [P] [US1] Create AddDatabaseModal component in frontend/src/components/AddDatabaseModal.tsx with form validation
- [ ] T041 [US1] Create Dashboard page in frontend/src/pages/Dashboard.tsx integrating DatabaseList and AddDatabaseModal
- [ ] T042 [US1] Add Dashboard route to frontend/src/App.tsx

**Checkpoint**: At this point, User Story 1 should be fully functional - users can manage database connections independently

---

## Phase 4: User Story 2 - View Database Metadata (Priority: P1)

**Goal**: Users can view database structure (tables, views, columns) with caching

**Independent Test**:
1. Select a database → metadata displays with tables/views and column details
2. Select same database again → loads from cache (faster)
3. Click refresh → metadata updates from database

### Backend Implementation for US2

- [ ] T043 [P] [US2] Create ColumnMetadata Pydantic model in backend/app/models/metadata.py with camelCase aliases
- [ ] T044 [P] [US2] Create TableMetadata Pydantic model in backend/app/models/metadata.py with camelCase aliases
- [ ] T045 [P] [US2] Create DatabaseMetadataResponse Pydantic model in backend/app/models/metadata.py with camelCase aliases
- [ ] T046 [P] [US2] Create MetadataService in backend/app/services/metadata_service.py with extract_metadata, get_cached_metadata, refresh_metadata methods
- [ ] T047 [US2] Implement GET /api/v1/dbs/{name} endpoint in backend/app/api/v1/databases.py (get_metadata handler with caching and refresh support)

### Frontend Implementation for US2

- [ ] T048 [P] [US2] Create MetadataViewer component in frontend/src/components/MetadataViewer.tsx with expandable table/column tree
- [ ] T049 [US2] Integrate MetadataViewer into Dashboard page in frontend/src/pages/Dashboard.tsx to show metadata when database selected
- [ ] T050 [US2] Add refresh button to MetadataViewer in frontend/src/components/MetadataViewer.tsx

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - users can manage connections and view metadata

---

## Phase 5: User Story 3 - Execute SQL Queries (Priority: P2)

**Goal**: Users can write and execute SELECT queries with validation and auto-LIMIT

**Independent Test**:
1. Execute SELECT * FROM users → displays results in table
2. Execute SELECT without LIMIT → auto-adds LIMIT 1000
3. Execute UPDATE/DELETE → rejected with "仅允许 SELECT" error
4. Execute invalid SQL → shows syntax error with location

### Backend Implementation for US3

- [ ] T051 [P] [US3] Create ExecuteQueryRequest Pydantic model in backend/app/models/query.py with SQL field
- [ ] T052 [P] [US3] Create QueryResult Pydantic model in backend/app/models/query.py with camelCase aliases (columns, rows, rowCount, executionTimeMs)
- [ ] T053 [P] [US3] Create QueryService in backend/app/services/query_service.py with validate_sql, execute_query methods
- [ ] T054 [US3] Implement SQL validation in backend/app/services/query_service.py using sqlglot (SELECT-only check, LIMIT injection)
- [ ] T055 [US3] Implement query execution in backend/app/services/query_service.py with 60-second timeout via AdapterRegistry
- [ ] T056 [US3] Implement POST /api/v1/dbs/{name}/query endpoint in backend/app/api/v1/queries.py (execute_query handler)
- [ ] T057 [US3] Register queries router in backend/app/main.py with /api/v1 prefix

### Frontend Implementation for US3

- [ ] T058 [P] [US3] Create SqlEditor component in frontend/src/components/SqlEditor.tsx using Monaco Editor with SQL language
- [ ] T059 [P] [US3] Create QueryResult component in frontend/src/components/QueryResult.tsx with table display and pagination
- [ ] T060 [US3] Create QueryPage in frontend/src/pages/QueryPage.tsx integrating SqlEditor and QueryResult
- [ ] T061 [US3] Add QueryPage route to frontend/src/App.tsx
- [ ] T062 [US3] Add execute button and error display to QueryPage in frontend/src/pages/QueryPage.tsx

**Checkpoint**: At this point, Users 1, 2, AND 3 should work - users can manage connections, view metadata, and execute queries

---

## Phase 6: User Story 5 - View and Export Query Results (Priority: P2)

**Goal**: Users can view query results in tables and export to CSV

**Independent Test**:
1. Execute query with large result set → displays with pagination
2. Click export CSV → downloads file
3. Execute query returning empty → shows "无数据" message

### Backend Implementation for US5

- [ ] T063 [P] [US5] Add CSV export method to QueryService in backend/app/services/query_service.py to convert QueryResult to CSV format
- [ ] T064 [US5] Implement GET /api/v1/dbs/{name}/query/export endpoint in backend/app/api/v1/queries.py (export_query handler with CSV download)

### Frontend Implementation for US5

- [ ] T065 [P] [US5] Add pagination to QueryResult component in frontend/src/components/QueryResult.tsx
- [ ] T066 [US5] Add export CSV button to QueryResult component in frontend/src/components/QueryResult.tsx
- [ ] T067 [US5] Add empty state display to QueryResult component in frontend/src/components/QueryResult.tsx

**Checkpoint**: At this point, Users 1, 2, 3, AND 5 should work - users can manage connections, view metadata, execute queries, and export results

---

## Phase 7: User Story 4 - Generate SQL from Natural Language (Priority: P3)

**Goal**: Users can generate SQL from natural language using AI

**Independent Test**:
1. Enter "查询所有活跃用户" → generates SELECT * FROM users WHERE status = 'active' LIMIT 1000
2. Generated SQL appears in editor → can be modified before execution
3. Invalid natural language → shows helpful error message

### Backend Implementation for US4

- [ ] T068 [P] [US4] Create NaturalLanguageQueryRequest Pydantic model in backend/app/models/query.py with prompt field
- [ ] T069 [P] [US4] Create GeneratedSQLResponse Pydantic model in backend/app/models/query.py with camelCase aliases (sql, explanation, warnings)
- [ ] T070 [P] [US4] Create LLMService in backend/app/services/llm_service.py with generate_sql method using OpenAI SDK
- [ ] T071 [US4] Implement context building in LLMService to include database metadata in system message
- [ ] T072 [US4] Implement SQL validation of generated SQL in LLMService using sqlglot
- [ ] T073 [US4] Implement POST /api/v1/dbs/{name}/query/natural endpoint in backend/app/api/v1/queries.py (generate_sql handler)

### Frontend Implementation for US4

- [ ] T074 [P] [US4] Create NaturalLanguageInput component in frontend/src/components/NaturalLanguageInput.tsx with textarea and submit button
- [ ] T075 [US4] Integrate NaturalLanguageInput into QueryPage in frontend/src/pages/QueryPage.tsx to populate SqlEditor on generation
- [ ] T076 [US4] Add loading state and error handling for AI generation in frontend/src/pages/QueryPage.tsx

**Checkpoint**: All user stories should now be independently functional - complete feature set ready

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Backend Polish

- [ ] T077 [P] Add comprehensive docstrings to all service modules in backend/app/services/
- [ ] T078 [P] Add request/response examples to FastAPI route docstrings in backend/app/api/v1/
- [ ] T079 [P] Create HTTP test fixtures in backend/tests/fixtures/test.rest for all endpoints
- [ ] T080 [P] Run black formatter on all backend code in backend/app/
- [ ] T081 [P] Run ruff linter and fix issues in backend/app/
- [ ] T082 [P] Run mypy --strict type check and fix issues in backend/app/

### Frontend Polish

- [ ] T083 [P] Add responsive design breakpoints to all components in frontend/src/components/
- [ ] T084 [P] Add loading states to all components that fetch data in frontend/src/components/
- [ ] T085 [P] Add error boundaries to frontend/src/App.tsx
- [ ] T086 [P] Run TypeScript type check and fix issues in frontend/src/
- [ ] T087 [P] Optimize Tailwind CSS bundle size in frontend/tailwind.config.js

### Integration & Validation

- [ ] T088 Test all user stories end-to-end following quickstart.md scenarios
- [ ] T089 Validate OpenAPI spec at http://localhost:8000/docs matches contracts/openapi.yaml
- [ ] T090 Verify CORS works from frontend to backend
- [ ] T091 Test with real PostgreSQL database connection
- [ ] T092 Test with real MySQL database connection
- [ ] T093 Verify password masking in stored URLs
- [ ] T094 Test metadata caching behavior
- [ ] T095 Test query timeout (60 seconds)
- [ ] T096 Verify auto-LIMIT 1000 injection
- [ ] T097 Test natural language SQL generation with OpenAI API

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (Phase 3): No dependencies on other user stories
  - US2 (Phase 4): Integrates with US1 (uses database list) but independently testable
  - US3 (Phase 5): Integrates with US1 (uses database selection) but independently testable
  - US5 (Phase 6): Depends on US3 (extends query results)
  - US4 (Phase 7): Integrates with US1, US2 (uses database and metadata) but independently testable
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

```
Foundational (Phase 2) MUST complete first
    ↓
┌─────────────┬─────────────┬─────────────┐
│   US1 (P1)  │   US2 (P1)  │   US3 (P2)  │
│  Phase 3    │   Phase 4   │   Phase 5   │
│  (MVP!)     │             │             │
└─────────────┴─────────────┴──────┬──────┘
                                     ↓
                                US5 (Phase 6)
                                (extends US3)
                                     ↓
                                US4 (Phase 7)
                                (uses US1, US2)
```

### Recommended Execution Order

**MVP Approach** (Single Developer):
1. Phase 1: Setup (T001-T012)
2. Phase 2: Foundational (T013-T027)
3. Phase 3: US1 - Manage Database Connections (T028-T042)
4. **STOP** - Validate MVP (database connection management)
5. Continue with US2 → US3 → US5 → US4

**Parallel Approach** (Multiple Developers):
1. All developers: Complete Phase 1 + 2 together
2. Once Phase 2 completes:
   - Developer A: US1 (T028-T042)
   - Developer B: US2 (T043-T050) - can start in parallel, integrates with US1
   - Developer C: US3 (T051-T062) - can start in parallel, integrates with US1
3. After US3 completes: Developer B/C → US5 (T063-T067)
4. After US1, US2 complete: Developer A/C → US4 (T068-T076)

### Within Each User Story

- Models marked [P] can be created in parallel
- Services wait for their dependent models
- Endpoints wait for their services
- Frontend components can often be built in parallel with backend

### Parallel Opportunities

**Setup Phase**:
```bash
# Can run in parallel:
T004, T005, T006, T007  # Install dependencies
T008, T009, T010, T011, T012  # Configuration files
```

**Foundational Phase**:
```bash
# Backend modules (can run in parallel):
T014, T015, T016, T017, T018
T019, T020, T021

# Frontend modules (can run in parallel):
T023, T024, T025, T026, T027
```

**User Story 1**:
```bash
# Models (can run in parallel):
T028, T029, T030
T031, T032

# Components (can run in parallel):
T039, T040
```

**User Story 2**:
```bash
# Models (can run in parallel):
T043, T044, T045
```

**User Story 3**:
```bash
# Models (can run in parallel):
T051, T052

# Components (can run in parallel):
T058, T059
```

---

## Parallel Example: User Story 1 (MVP)

```bash
# Launch all backend models together:
Task T028: "Create DatabaseResponse Pydantic model in backend/app/models/database.py"
Task T029: "Create DatabaseListResponse Pydantic model in backend/app/models/database.py"
Task T030: "Create AddDatabaseRequest Pydantic model in backend/app/models/database.py"

# Launch all adapters together:
Task T031: "Create PostgreSQLAdapter in backend/app/adapters/postgresql.py"
Task T032: "Create MySQLAdapter in backend/app/adapters/mysql.py"

# Launch all frontend components together:
Task T039: "Create DatabaseList component in frontend/src/components/DatabaseList.tsx"
Task T040: "Create AddDatabaseModal component in frontend/src/components/AddDatabaseModal.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only) - Recommended for Solo Developer

1. Complete Phase 1: Setup (T001-T012)
2. Complete Phase 2: Foundational (T013-T027)
3. Complete Phase 3: User Story 1 (T028-T042)
4. **STOP and VALIDATE**: Test database connection management independently
5. Demo MVP to stakeholders
6. Continue with US2 → US3 → US5 → US4 if approved

**MVP delivers**: Users can add, list, view status, and delete database connections

### Incremental Delivery

1. **Foundation**: Phase 1 + 2 (T001-T027)
2. **MVP v1**: Add US1 → Test → Deploy (Database connection management)
3. **MVP v2**: Add US2 → Test → Deploy (Metadata viewing)
4. **MVP v3**: Add US3 → Test → Deploy (SQL query execution)
5. **MVP v4**: Add US5 → Test → Deploy (Query results export)
6. **Full Product**: Add US4 → Test → Deploy (Natural language SQL)

Each increment adds value without breaking previous functionality.

### Parallel Team Strategy

With 3 developers:

1. **Week 1**: All - Complete Setup + Foundational together
2. **Week 2-3**:
   - Developer A: US1 (Database connections)
   - Developer B: US2 (Metadata) + US5 (Export)
   - Developer C: US3 (Query execution)
3. **Week 4**:
   - Integration testing across all stories
   - Developer A + C: US4 (Natural language)

**Benefits**:
- Faster time-to-market
- Specialization by component
- Shared ownership of foundational code

---

## Task Summary

- **Total Tasks**: 97
- **Setup Phase**: 12 tasks
- **Foundational Phase**: 15 tasks
- **User Story 1**: 15 tasks (MVP)
- **User Story 2**: 8 tasks
- **User Story 3**: 12 tasks
- **User Story 5**: 5 tasks
- **User Story 4**: 9 tasks
- **Polish Phase**: 21 tasks

**Parallelizable Tasks**: 67 tasks (69%) marked with [P]

**MVP Scope** (Phases 1-3): 42 tasks

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests NOT included (not requested in spec.md) - can add later if needed
- All file paths are absolute and follow the project structure from plan.md
- Backend follows Ergonomic Python style with mypy --strict
- Frontend follows TypeScript strict mode
- All API responses use camelCase via Pydantic aliases
