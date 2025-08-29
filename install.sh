#!/bin/bash
# AI Manager System - Unix/Linux Installation Script

set -e

echo "AI Manager System - Installation"
echo "================================="
echo

echo "[1/4] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python is not installed or not in PATH"
        echo "Please install Python 3.8+ and try again"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "Using: $($PYTHON_CMD --version)"
echo

echo "[2/4] Upgrading pip..."
$PYTHON_CMD -m pip install --upgrade pip

echo
echo "[3/4] Installing dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt

echo
echo "[4/4] Installing AI Manager in development mode..."
$PYTHON_CMD -m pip install -e .

echo
echo "============================================"
echo "✅ Installation Complete!"
echo "============================================"
echo
echo "Next steps:"
echo "  1. Run '$PYTHON_CMD tests/test_basic_imports.py' to verify installation"
echo "  2. Run '$PYTHON_CMD tests/test_real_world_system.py' for full validation"
echo "  3. Use 'make health' for comprehensive health check"
echo "  4. Start the API server with 'make run-api'"
echo
echo "For help: run 'make help' or 'ai-manager --help'"
echo