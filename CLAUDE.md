# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains a prompt specification for building an AI Manager infrastructure in Python. The project is designed to be a local-first AI task management system that can plan, delegate, execute, and review code changes through a Manager-Worker architecture.

## Key Architecture Components

The specification outlines a comprehensive system with:

- **Manager Service**: FastAPI-based control plane for task orchestration, planning, delegation, and review
- **Worker Runtime**: Isolated execution environment for task completion with safety constraints
- **Task Queue**: SQLite-based queue system with status transitions
- **Review Engine**: Skeptical validation using tests, linting, type checking, and policy rules
- **Data Contracts**: Standardized JSON schemas for Task Specs, Worker Reports, PR Proposals, and Review Reports

## Technology Stack (Per Specification)

- Python 3.11+
- FastAPI + Uvicorn for web services
- SQLite with SQLModel for data persistence  
- pytest with ≥85% coverage requirement
- Code quality: ruff, black, mypy
- Containerization: Docker + docker-compose
- CI: GitHub Actions

## Development Commands (From Specification)

Based on the prompt requirements, the following commands should be available once implemented:

```bash
# Setup
make dev          # Development setup
make test         # Run test suite
make run          # Start the services

# API Server
uvicorn manager.api.http:app --reload

# CLI Usage
manager task submit -f examples/hello_task.json
manager task list
manager run logs <run-id>

# Code Quality (Required)
ruff check .      # Linting
black --check .   # Code formatting check
mypy .           # Type checking
pytest --cov     # Tests with coverage
```

## Repository Structure (Target Layout)

```
ai-manager/
├── src/manager/
│   ├── api/http.py              # FastAPI routes
│   ├── core/                    # Core orchestration logic
│   │   ├── manager.py          # Main orchestrator
│   │   ├── planner.py          # Task planning
│   │   ├── queue.py            # Task queue management
│   │   ├── review.py           # Code review engine
│   │   ├── executor.py         # Worker subprocess launcher
│   │   ├── artifacts.py        # Artifact management
│   │   └── schemas.py          # Pydantic data models
│   ├── adapters/               # External integrations
│   │   ├── worker_prompt.py    # Worker behavior
│   │   └── llm_stub.py         # LLM placeholder
│   └── store/models.py         # SQLModel entities
├── cli/                        # Command-line interfaces
│   ├── manager_cli.py
│   └── worker_cli.py
├── tests/
│   ├── unit/
│   └── integration/
└── ops/                        # DevOps configuration
    ├── Dockerfile
    ├── docker-compose.yml
    └── Makefile
```

## Safety and Security Constraints

Workers operate with strict safety measures:
- No network access by default
- Low privileges execution
- Timeout enforcement
- Sandboxed working directories under `runs/<run-id>/`
- Artifact size limits
- Environment variable redaction

## Data Flow

1. Task submission via CLI/API → Task Spec JSON
2. Manager plans and enqueues task
3. Dispatcher spawns isolated Worker in subprocess
4. Worker produces Task Report + PR Proposal
5. Review engine validates using tests/linting/coverage
6. Approved changes get "merged" to working tree

## Quality Gates

All code must pass:
- ruff linting
- black formatting
- mypy type checking  
- pytest with ≥85% coverage on changed lines
- Integration tests for Manager-Worker flow

## Current State

This repository currently contains only the specification document (`first_prompt.txt`). The actual implementation needs to be built according to the detailed requirements provided in that specification.