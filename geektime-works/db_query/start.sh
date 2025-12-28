#!/bin/bash

# Database Query Tool - Start Script
# This script starts both backend and frontend development servers

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -i :"$1" >/dev/null 2>&1
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Print banner
echo "=========================================="
echo "  Database Query Tool - Development"
echo "=========================================="
echo ""

# Check prerequisites
print_info "Checking prerequisites..."

# Check Python
if ! command_exists python3; then
    print_error "Python 3 is not installed"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
print_success "Python $PYTHON_VERSION found"

# Check Node.js
if ! command_exists node; then
    print_error "Node.js is not installed"
    exit 1
fi
NODE_VERSION=$(node --version)
print_success "Node $NODE_VERSION found"

# Check if uv is installed (optional, will use pip if not available)
if command_exists uv; then
    PYTHON_PKG_MANAGER="uv"
    print_success "uv package manager found"
else
    PYTHON_PKG_MANAGER="pip"
    print_warning "uv not found, will use pip"
fi

# Check if npm/yarn/pnpm is available
if command_exists pnpm; then
    NODE_PKG_MANAGER="pnpm"
elif command_exists yarn; then
    NODE_PKG_MANAGER="yarn"
else
    NODE_PKG_MANAGER="npm"
fi
print_success "Using $NODE_PKG_MANAGER for Node.js packages"

echo ""

# Check if ports are available
BACKEND_PORT=8000
FRONTEND_PORT=5173

if port_in_use $BACKEND_PORT; then
    print_warning "Port $BACKEND_PORT is already in use"
    read -p "Do you want to kill the process and continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Killing process on port $BACKEND_PORT..."
        lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
        sleep 1
    else
        print_error "Cannot start backend on port $BACKEND_PORT"
        exit 1
    fi
fi

if port_in_use $FRONTEND_PORT; then
    print_warning "Port $FRONTEND_PORT is already in use"
    read -p "Do you want to kill the process and continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Killing process on port $FRONTEND_PORT..."
        lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
        sleep 1
    else
        print_error "Cannot start frontend on port $FRONTEND_PORT"
        exit 1
    fi
fi

echo ""

# Backend setup
print_info "Setting up backend..."
cd backend

# Check if .env exists
if [ ! -f .env ]; then
    print_warning ".env file not found"
    if [ -f .env.example ]; then
        print_info "Creating .env from .env.example..."
        cp .env.example .env
        print_warning "Please edit backend/.env and add your OPENAI_API_KEY"
        read -p "Press Enter to continue after editing .env..."
    else
        print_error ".env.example not found"
        exit 1
    fi
fi

# Check if dependencies are installed
if [ "$PYTHON_PKG_MANAGER" = "uv" ]; then
    if ! uv pip show fastapi >/dev/null 2>&1; then
        print_info "Installing backend dependencies with uv..."
        uv pip install -e ".[dev]"
    fi
else
    if ! python3 -c "import fastapi" >/dev/null 2>&1; then
        print_info "Installing backend dependencies with pip..."
        pip install -e ".[dev]"
    fi
fi
print_success "Backend dependencies OK"

# Check if database is initialized
if [ ! -f ~/.db_query/db_query.db ]; then
    print_info "Initializing database..."
    alembic upgrade head
fi

cd "$SCRIPT_DIR"
echo ""

# Frontend setup
print_info "Setting up frontend..."
cd frontend

# Check if .env.local exists
if [ ! -f .env.local ]; then
    if [ -f .env.local.example ]; then
        print_info "Creating .env.local from .env.local.example..."
        cp .env.local.example .env.local
    fi
fi

# Check if node_modules exists
if [ ! -d node_modules ]; then
    print_info "Installing frontend dependencies..."
    $NODE_PKG_MANAGER install
fi
print_success "Frontend dependencies OK"

cd "$SCRIPT_DIR"
echo ""

# Create logs directory
mkdir -p logs

# Start backend
print_info "Starting backend server on port $BACKEND_PORT..."
cd backend

if [ "$PYTHON_PKG_MANAGER" = "uv" ]; then
    nohup uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT > ../logs/backend.log 2>&1 &
else
    nohup python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT > ../logs/backend.log 2>&1 &
fi

BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
print_success "Backend started (PID: $BACKEND_PID)"

# Wait for backend to start
sleep 3

# Check if backend is running
if ! curl -s http://localhost:$BACKEND_PORT/health >/dev/null 2>&1; then
    print_warning "Backend health check failed, checking logs..."
    tail -n 20 logs/backend.log
fi

cd "$SCRIPT_DIR"
echo ""

# Start frontend
print_info "Starting frontend server on port $FRONTEND_PORT..."
cd frontend

nohup $NODE_PKG_MANAGER run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
print_success "Frontend started (PID: $FRONTEND_PID)"

cd "$SCRIPT_DIR"
echo ""

# Print summary
echo "=========================================="
print_success "Development servers started!"
echo "=========================================="
echo ""
echo "Backend:"
echo "  - URL:    http://localhost:$BACKEND_PORT"
echo "  - Docs:   http://localhost:$BACKEND_PORT/docs"
echo "  - Logs:   logs/backend.log"
echo "  - PID:    $BACKEND_PID"
echo ""
echo "Frontend:"
echo "  - URL:    http://localhost:$FRONTEND_PORT"
echo "  - Logs:   logs/frontend.log"
echo "  - PID:    $FRONTEND_PID"
echo ""
echo "To stop the servers, run:"
echo "  ./stop.sh"
echo ""
echo "Or kill manually:"
echo "  kill $BACKEND_PID  # Stop backend"
echo "  kill $FRONTEND_PID # Stop frontend"
echo ""
echo "To view logs:"
echo "  tail -f logs/backend.log   # Backend logs"
echo "  tail -f logs/frontend.log  # Frontend logs"
echo "=========================================="
