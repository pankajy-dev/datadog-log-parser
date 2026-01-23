#!/bin/bash
# Quick start script for Log Parser Web UI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="${SCRIPT_DIR}/src/web"

echo "=========================================="
echo "🚀 Log Parser Utility - Web UI Launcher"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3 to continue"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Flask not found. Installing dependencies..."
    pip3 install -r "${WEB_DIR}/requirements.txt"
    echo ""
fi

echo "✓ Dependencies installed"
echo ""

# Navigate to web directory
cd "${WEB_DIR}"

echo "🌐 Starting web server..."
echo "   Server will run on: http://localhost:5000"
echo "   Press Ctrl+C to stop"
echo ""
echo "=========================================="
echo ""

# Start the server
python3 app.py
