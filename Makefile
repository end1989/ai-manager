# AI Manager System - Makefile
# Provides convenient commands for development and deployment

.PHONY: help install dev test clean run-api run-worker lint format check-deps health

# Default target
help:
	@echo "AI Manager System - Available Commands"
	@echo "====================================="
	@echo "install     - Install dependencies and set up the system"
	@echo "dev         - Install development dependencies"
	@echo "test        - Run all tests"
	@echo "test-basic  - Run basic import tests"
	@echo "test-real   - Run real-world system tests"
	@echo "lint        - Run code linting (ruff)"
	@echo "format      - Format code (black)"
	@echo "type-check  - Run type checking (mypy)"
	@echo "check-deps  - Check system dependencies"
	@echo "health      - Run environment health check"
	@echo "run-api     - Start the FastAPI server"
	@echo "run-worker  - Start a worker process"
	@echo "clean       - Clean temporary files"
	@echo "setup-db    - Initialize database tables"

# Installation targets
install:
	@echo "Installing AI Manager System..."
	@echo "==============================="
	python -m pip install --upgrade pip
	pip install -e .
	pip install -r requirements.txt
	@echo ""
	@echo "✅ Installation complete!"
	@echo "Run 'make health' to validate the installation"

dev: install
	@echo "Installing development dependencies..."
	pip install -r requirements-dev.txt
	@echo "✅ Development environment ready!"

# Setup database
setup-db:
	@echo "Setting up database..."
	python -c "from src.manager.store.models import create_db_and_tables; create_db_and_tables()"
	@echo "✅ Database initialized!"

# Testing targets
test:
	@echo "Running comprehensive test suite..."
	python tests/test_basic_imports.py
	python tests/test_real_world_system.py

test-basic:
	@echo "Running basic import tests..."
	python tests/test_basic_imports.py

test-real:
	@echo "Running real-world system tests..."
	python tests/test_real_world_system.py

# Code quality targets
lint:
	@echo "Running code linting..."
	ruff check src/ tests/

format:
	@echo "Formatting code..."
	black src/ tests/

type-check:
	@echo "Running type checks..."
	mypy src/

# Health and validation
health:
	@echo "Running environment health check..."
	python tests/test_environment_validator.py --level comprehensive

check-deps:
	@echo "Checking system dependencies..."
	python -c "import sys; print(f'Python: {sys.version}')"
	python -c "import sqlmodel; print(f'SQLModel: {sqlmodel.__version__}')"
	python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
	python -c "import typer; print(f'Typer: {typer.__version__}')"
	@echo "✅ Core dependencies available"

# Runtime targets  
run-api:
	@echo "Starting FastAPI server..."
	cd src && python -m uvicorn manager.api.http:app --reload --host 0.0.0.0 --port 8000

run-worker:
	@echo "Starting worker process..."
	cd src && python -m cli.worker_cli

# Maintenance
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.db" -delete 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	rm -rf .pytest_cache/ 2>/dev/null || true
	rm -rf htmlcov/ 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# Show system status
status:
	@echo "AI Manager System Status"
	@echo "======================="
	@echo "Python version: $$(python --version)"
	@echo "Working directory: $$(pwd)"
	@echo "Virtual environment: $${VIRTUAL_ENV:-Not activated}"
	@echo "Database: $${MANAGER_DB_URL:-Not configured}"
	@echo ""
	@make check-deps