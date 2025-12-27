.PHONY: help setup install-backend install-frontend dev-backend dev-frontend dev test-backend test-frontend test clean lint-backend lint-frontend format-backend format-frontend db-init db-reset db-clean db-info db-backup db-location

# 默认目标
help:
	@echo "可用命令:"
	@echo "  make setup              - 初始化项目（安装所有依赖）"
	@echo "  make install-backend    - 安装后端依赖"
	@echo "  make install-frontend   - 安装前端依赖"
	@echo "  make dev-backend        - 启动后端开发服务器"
	@echo "  make dev-frontend       - 启动前端开发服务器"
	@echo "  make dev                - 同时启动前后端开发服务器"
	@echo "  make test-backend       - 运行后端测试"
	@echo "  make test-frontend      - 运行前端测试"
	@echo "  make test               - 运行所有测试"
	@echo "  make lint-backend       - 检查后端代码风格"
	@echo "  make lint-frontend      - 检查前端代码风格"
	@echo "  make format-backend     - 格式化后端代码"
	@echo "  make format-frontend    - 格式化前端代码"
	@echo "  make clean              - 清理临时文件和缓存"
	@echo ""
	@echo "数据库操作:"
	@echo "  make db-init            - 初始化数据库（创建表结构）"
	@echo "  make db-reset           - 重置数据库（删除所有数据并重新创建表）"
	@echo "  make db-clean           - 清理数据库（删除所有数据但保留表结构）"
	@echo "  make db-info            - 显示数据库信息"
	@echo "  make db-backup          - 备份数据库"
	@echo "  make db-location        - 显示数据库文件位置"

# 初始化项目
setup: install-backend install-frontend db-init
	@echo "项目初始化完成！"
	@echo "运行 'make dev' 启动开发服务器"

# 安装后端依赖
install-backend:
	@echo "安装后端依赖..."
	cd backend && uv sync --extra dev

# 安装前端依赖
install-frontend:
	@echo "安装前端依赖..."
	cd frontend && npm install

# 启动后端开发服务器
dev-backend:
	@echo "启动后端开发服务器..."
	cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端开发服务器
dev-frontend:
	@echo "启动前端开发服务器..."
	cd frontend && npm run dev

# 同时启动前后端（需要后台运行）
dev:
	@echo "启动前后端开发服务器..."
	@echo "后端: http://localhost:8000"
	@echo "前端: http://localhost:5173"
	@echo "API 文档: http://localhost:8000/docs"
	@make dev-backend & make dev-frontend

# 运行后端测试
test-backend:
	@echo "运行后端测试..."
	cd backend && uv run pytest tests/ -v

# 运行前端测试
test-frontend:
	@echo "运行前端测试..."
	cd frontend && npm run test:e2e

# 运行所有测试
test: test-backend test-frontend

# 检查后端代码风格
lint-backend:
	@echo "检查后端代码风格..."
	cd backend && uv run ruff check app/ tests/
	cd backend && uv run mypy app/

# 检查前端代码风格
lint-frontend:
	@echo "检查前端代码风格..."
	cd frontend && npm run type-check

# 格式化后端代码
format-backend:
	@echo "格式化后端代码..."
	cd backend && uv run black app/ tests/
	cd backend && uv run ruff check --fix app/ tests/

# 格式化前端代码
format-frontend:
	@echo "格式化前端代码..."
	cd frontend && npx prettier --write "src/**/*.{ts,tsx,css}"

# 清理临时文件
clean:
	@echo "清理临时文件..."
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
	@echo "清理完成！"

##########################################
# 数据库操作命令
##########################################

# 初始化数据库
db-init:
	@echo "初始化数据库..."
	cd backend && uv run python scripts/init_db.py

# 重置数据库（删除所有数据并重新创建表）
db-reset:
	@echo "重置数据库..."
	cd backend && PYTHONPATH=. uv run python scripts/db_utils.py reset

# 清理数据库（删除所有数据但保留表结构）
db-clean:
	@echo "清理数据库..."
	cd backend && PYTHONPATH=. uv run python scripts/db_utils.py clean

# 显示数据库信息
db-info:
	@echo "数据库信息:"
	cd backend && PYTHONPATH=. uv run python scripts/db_utils.py info

# 备份数据库
db-backup:
	@echo "备份数据库..."
	cd backend && PYTHONPATH=. uv run python scripts/db_utils.py backup

# 显示数据库文件位置
db-location:
	@echo "数据库文件位置:"
	@cd backend && PYTHONPATH=. uv run python -c "from app.config import settings; print(settings.database_path)"

