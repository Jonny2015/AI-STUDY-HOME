#!/bin/bash
# Setup script to localize Monaco Editor files
# Run this script if public/monaco-editor directory is missing

set -e

FRONTEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MONACO_DIR="$FRONTEND_DIR/public/monaco-editor"
NODE_MODULES_MONACO="$FRONTEND_DIR/node_modules/monaco-editor"

echo "📦 Setting up Monaco Editor local files..."

# Check if node_modules has monaco-editor
if [ ! -d "$NODE_MODULES_MONACO" ]; then
    echo "❌ Error: monaco-editor not found in node_modules"
    echo "Please run: npm install"
    exit 1
fi

# Create directory
mkdir -p "$MONACO_DIR"

# Copy files
echo "📋 Copying Monaco Editor files..."
cp -r "$NODE_MODULES_MONACO/min" "$MONACO_DIR/"

echo "✅ Monaco Editor files copied to $MONACO_DIR"
echo "📝 Size: $(du -sh "$MONACO_DIR" | cut -f1)"
