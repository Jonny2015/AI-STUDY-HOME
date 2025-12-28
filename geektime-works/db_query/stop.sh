#!/bin/bash

# Database Query Tool - Stop Script
# This script stops both backend and frontend development servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  Database Query Tool - Stop Servers"
echo "=========================================="
echo ""

# Stop backend
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    print_info "Stopping backend server (PID: $BACKEND_PID)..."

    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        sleep 1

        # Force kill if still running
        if kill -0 $BACKEND_PID 2>/dev/null; then
            print_warning "Backend still running, force killing..."
            kill -9 $BACKEND_PID
        fi

        print_info "Backend stopped"
    else
        print_warning "Backend process not found (PID: $BACKEND_PID)"
    fi

    rm -f logs/backend.pid
else
    print_warning "Backend PID file not found"
fi

# Stop frontend
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    print_info "Stopping frontend server (PID: $FRONTEND_PID)..."

    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        sleep 1

        # Force kill if still running
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            print_warning "Frontend still running, force killing..."
            kill -9 $FRONTEND_PID
        fi

        print_info "Frontend stopped"
    else
        print_warning "Frontend process not found (PID: $FRONTEND_PID)"
    fi

    rm -f logs/frontend.pid
else
    print_warning "Frontend PID file not found"
fi

# Also try to kill processes on ports 8000 and 5173
print_info "Checking for processes on ports 8000 and 5173..."

# Kill on port 8000 (backend)
BACKEND_PORT_PID=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$BACKEND_PORT_PID" ]; then
    print_info "Killing process on port 8000 (PID: $BACKEND_PORT_PID)..."
    kill -9 $BACKEND_PORT_PID 2>/dev/null || true
fi

# Kill on port 5173 (frontend)
FRONTEND_PORT_PID=$(lsof -ti:5173 2>/dev/null || true)
if [ -n "$FRONTEND_PORT_PID" ]; then
    print_info "Killing process on port 5173 (PID: $FRONTEND_PORT_PID)..."
    kill -9 $FRONTEND_PORT_PID 2>/dev/null || true
fi

echo ""
print_info "All servers stopped"
echo "=========================================="
