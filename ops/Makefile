# AI Manager Makefile

.PHONY: help install dev test lint format type-check build run clean docs

# Default target
help: ## Show this help message
	@echo "AI Manager Development Commands"
	@echo "==============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development setup
install: ## Install dependencies
	pip install -e .

dev: ## Install development dependencies  
	pip install -e .[dev]

# Code quality
lint: ## Run linting with ruff
	ruff check src tests

format: ## Format code with black
	black src tests
	ruff format src tests

type-check: ## Run type checking with mypy
	mypy src

# Testing
test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

# Application
run: ## Start API server
	uvicorn manager.api.http:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Start API server in production mode
	uvicorn manager.api.http:app --host 0.0.0.0 --port 8000

# Task management
submit-example: ## Submit example task
	manager submit -f examples/hello_task.json

status: ## Show system status
	manager status

# Docker operations
build: ## Build Docker image
	docker build -f ops/Dockerfile -t ai-manager:latest .

docker-run: ## Run with Docker Compose
	docker-compose -f ops/docker-compose.yml up

docker-dev: ## Run development environment
	docker-compose -f ops/docker-compose.yml up --build

docker-stop: ## Stop Docker containers
	docker-compose -f ops/docker-compose.yml down

docker-clean: ## Clean Docker containers and volumes
	docker-compose -f ops/docker-compose.yml down -v
	docker system prune -f

# Database operations
db-init: ## Initialize database
	python -c "from manager.store.models import create_db_and_tables; create_db_and_tables()"

db-reset: ## Reset database (WARNING: destroys all data)
	rm -f manager.db
	$(MAKE) db-init

# Cleanup
clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf runs/
	rm -rf artifacts/
	rm -rf logs/

# Documentation
docs: ## Generate documentation
	@echo "Documentation generation not implemented yet"
	@echo "API docs available at: http://localhost:8000/docs"

# Quality gates (CI)
ci-quality: lint type-check ## Run all code quality checks

ci-test: test-cov ## Run tests with coverage for CI

ci-all: ci-quality ci-test ## Run all CI checks

# Development workflow
check: ci-quality test ## Run quality checks and tests

# Worker commands
worker-test: ## Test worker functionality
	worker test

worker-info: ## Show worker information
	worker info

# Task generation
generate-task: ## Generate task template
	manager generate-task -o task.json

# System maintenance
cleanup: ## Clean up old run data
	manager cleanup

# Monitoring
logs: ## Show system logs (requires run_id)
	@echo "Usage: manager logs <run_id>"

# Environment setup
setup-env: ## Set up environment file
	cp .env.example .env
	@echo "Edit .env file with your configuration"

# Git hooks (optional)
install-hooks: ## Install git hooks
	@echo "Git hooks not implemented yet"

# Performance testing
perf-test: ## Run performance tests
	@echo "Performance tests not implemented yet"

# Security scanning
security-scan: ## Run security checks
	@echo "Security scanning not implemented yet"
	@echo "Consider adding: bandit, safety, semgrep"