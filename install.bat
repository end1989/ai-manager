@echo off
REM AI Manager System - Windows Installation Script

echo AI Manager System - Installation
echo ===================================

echo.
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    exit /b 1
)
python --version

echo.
echo [2/4] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [3/4] Installing dependencies...
pip install -r requirements.txt

echo.
echo [4/4] Installing AI Manager in development mode...
pip install -e .

echo.
echo ============================================
echo ✅ Installation Complete!
echo ============================================
echo.
echo Next steps:
echo   1. Run 'python tests/test_basic_imports.py' to verify installation
echo   2. Run 'python tests/test_real_world_system.py' for full validation  
echo   3. Use 'make health' for comprehensive health check (if make is available)
echo   4. Start the API server with 'make run-api' or 'python -m uvicorn manager.api.http:app --reload'
echo.
echo For help: run 'make help' or 'ai-manager --help'
echo.