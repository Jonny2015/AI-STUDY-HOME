#!/bin/bash
# Script to create GitHub Issues from tasks.md
# Requires: GitHub CLI (gh)
# Install: https://cli.github.com/

set -e

REPO="Jonny2015/geektime-ai-stydy-project"

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub CLI"
    echo "Run: gh auth login"
    exit 1
fi

echo "Creating GitHub Issues for Database Query Tool..."
echo "Repository: $REPO"
echo ""

# Helper function to create issue
create_issue() {
    local title="$1"
    local body="$2"
    local labels="$3"

    gh issue create \
        --repo "$REPO" \
        --title "$title" \
        --body "$body" \
        --labels "$labels"
}

# Phase 1: Setup
echo "Creating Phase 1: Setup issues..."

create_issue \
    "T001: Create backend and frontend directory structure" \
    "Create the complete project directory structure per implementation plan.

**Backend Structure:**
- \`backend/app/models/\` - Pydantic models
- \`backend/app/adapters/\` - Database adapters (SOLID)
- \`backend/app/services/\` - Business services
- \`backend/app/api/v1/\` - API routes
- \`backend/app/core/\` - Core functionality
- \`backend/app/utils/\` - Utilities
- \`backend/tests/unit/\` - Unit tests
- \`backend/tests/integration/\` - Integration tests
- \`backend/tests/fixtures/\` - Test fixtures

**Frontend Structure:**
- \`frontend/src/components/\` - React components
- \`frontend/src/pages/\` - Pages
- \`frontend/src/services/\` - API services
- \`frontend/src/types/\` - TypeScript types
- \`frontend/tests/e2e/\` - E2E tests

**Task ID:** T001
**Phase:** Phase 1 - Setup
**Parallel:** Yes" \
    "phase:setup,priority:high"

create_issue \
    "T002: Initialize backend uv project with Python 3.11+" \
    "Create \`backend/pyproject.toml\` with uv project configuration.

**Requirements:**
- Python 3.11+
- Project metadata (name, version, description)
- uv dependency management

**Task ID:** T002
**Phase:** Phase 1 - Setup
**Depends on:** T001" \
    "phase:setup,component:backend"

create_issue \
    "T003: Initialize frontend npm project" \
    "Create \`frontend/package.json\` with npm project configuration.

**Requirements:**
- React 18+
- Vite build tool
- Project metadata

**Task ID:** T003
**Phase:** Phase 1 - Setup
**Depends on:** T001" \
    "phase:setup,component:frontend"

create_issue \
    "T004: Install backend dependencies" \
    "Install backend production dependencies in \`backend/pyproject.toml\`:

- FastAPI
- uvicorn[standard]
- Pydantic V2
- sqlglot
- openai
- aiosqlite
- asyncpg (PostgreSQL)
- aiomysql (MySQL)

**Task ID:** T004
**Phase:** Phase 1 - Setup
**Parallel:** Yes
**Depends on:** T002" \
    "phase:setup,component:backend,dependencies"

create_issue \
    "T005: Install frontend dependencies" \
    "Install frontend dependencies in \`frontend/package.json\`:

- React 18
- Refine 5
- Ant Design
- Tailwind CSS
- Monaco Editor
- Vite

**Task ID:** T005
**Phase:** Phase 1 - Setup
**Parallel:** Yes
**Depends on:** T003" \
    "phase:setup,component:frontend,dependencies"

create_issue \
    "T006: Install backend dev dependencies" \
    "Install backend development dependencies in \`backend/pyproject.toml\`:

- black (formatter)
- ruff (linter)
- mypy (type checker)
- pytest
- pytest-asyncio
- httpx (testing)

**Task ID:** T006
**Phase:** Phase 1 - Setup
**Parallel:** Yes
**Depends on:** T002" \
    "phase:setup,component:backend,dev-tools"

create_issue \
    "T007: Install frontend dev dependencies" \
    "Install frontend development dependencies in \`frontend/package.json\`:

- Playwright
- TypeScript types

**Task ID:** T007
**Phase:** Phase 1 - Setup
**Parallel:** Yes
**Depends on:** T003" \
    "phase:setup,component:frontend,dev-tools"

create_issue \
    "T008: Configure backend mypy strict mode" \
    "Configure mypy strict mode in \`backend/pyproject.toml\`:

Enable strict type checking for all backend code.

**Task ID:** T008
**Phase:** Phase 1 - Setup
**Parallel:** Yes
**Depends on:** T006" \
    "phase:setup,component:backend,type-check"

create_issue \
    "T009: Configure frontend TypeScript strict mode" \
    "Configure TypeScript strict mode in \`frontend/tsconfig.json\`:

Enable all strict type checking options.

**Task ID:** T009
**Phase:** Phase 1 - Setup
**Parallel:** Yes
**Depends on:** T007" \
    "phase:setup,component:frontend,type-check"

create_issue \
    "T010: Create .env.example template" \
    "Create \`backend/.env.example\` with:

\`\`
OPENAI_API_KEY=sk-your-openai-api-key-here
\`\`

**Task ID:** T010
**Phase:** Phase 1 - Setup
**Parallel:** Yes
**Depends on:** T001" \
    "phase:setup,component:backend,config"

create_issue \
    "T011: Create backend README.md" \
    "Create \`backend/README.md\` with setup instructions.

**Include:**
- Prerequisites
- Installation steps
- Development server startup
- Code quality commands

**Task ID:** T011
**Phase:** Phase 1 - Setup
**Parallel:** Yes
**Depends on:** T001" \
    "phase:setup,component:backend,documentation"

create_issue \
    "T012: Create frontend README.md" \
    "Create \`frontend/README.md\` with setup instructions.

**Include:**
- Prerequisites
- Installation steps
- Development server startup
- Type check commands

**Task ID:** T012
**Phase:** Phase 1 - Setup
**Parallel:** Yes
**Depends on:** T001" \
    "phase:setup,component:frontend,documentation"

echo ""
echo "Phase 1 issues created! ✓"
echo ""
echo "Note: This script only creates Phase 1 tasks (12 issues) as an example."
echo "To create all 97 issues, run the full script or execute tasks manually."
echo ""
echo "Total issues created: 12"
echo "View issues at: https://github.com/$REPO/issues"
