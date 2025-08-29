# AI Manager

A local-first AI task management infrastructure for planning, delegating, executing, and reviewing code changes through a Manager-Worker architecture.

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-manager

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install

# Set up environment
make setup-env

# Initialize database
make db-init
```

### Running the System

```bash
# Start API server
make run

# In another terminal, submit example task
make submit-example

# Check system status
manager status
```

The API will be available at http://localhost:8000 with documentation at http://localhost:8000/docs.

## 📋 System Overview

AI Manager is a local-first infrastructure that orchestrates AI-powered task execution through:

- **Manager Service**: FastAPI-based control plane for task orchestration
- **Worker Runtime**: Isolated execution environment for task completion  
- **Task Queue**: SQLite-based queue with status transitions
- **Review Engine**: Automated quality validation using tests, linting, and coverage
- **Artifacts Management**: Run directories, logs, and output storage

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Task Submit   │───▶│   Task Queue    │───▶│   Dispatcher    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Merge/Store   │◀───│  Review Engine  │◀───│ Worker Executor │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📝 Usage

### Command Line Interface

**Manager Commands:**

```bash
# Submit a task
manager submit -f task.json

# Submit and run immediately
manager submit -f task.json --run

# List tasks
manager list
manager list --status queued

# Show task details
manager show T-001

# Control dispatcher
manager dispatcher start
manager dispatcher stop

# View system status
manager status

# Generate task template
manager generate-task -o my-task.json
```

**Worker Commands:**

```bash
# Execute a task
worker run --task task.json --workdir ./workspace

# Validate task specification
worker validate task.json

# Test worker functionality
worker test

# Show worker capabilities
worker info
```

### HTTP API

The REST API provides programmatic access:

- `POST /tasks` - Submit new task
- `GET /tasks` - List tasks
- `GET /tasks/{task_id}` - Get task details
- `POST /tasks/{task_id}/run` - Run task immediately
- `GET /runs` - List runs
- `GET /runs/{run_id}` - Get run details
- `GET /status` - System status

### Task Specification

Tasks are defined using JSON specifications:

```json
{
  "task_id": "T-example-001",
  "title": "Create FastAPI health endpoint",
  "goal": "Implement a health check service for monitoring",
  "background": "We need basic service monitoring capabilities",
  "deliverables": [
    "FastAPI service with /health endpoint",
    "Unit tests with >85% coverage",
    "README documentation"
  ],
  "acceptance_criteria": [
    "/health endpoint returns 200 status",
    "Response includes timestamp and version",
    "Tests pass with coverage >85%"
  ],
  "timebox_hours": 2.0
}
```

## 🧪 Development

### Quality Commands

```bash
# Run all quality checks
make check

# Individual checks
make lint          # Ruff linting
make format        # Black formatting
make type-check    # MyPy type checking
make test          # Run all tests
make test-cov      # Tests with coverage
```

### Testing

```bash
# Run all tests
make test

# Run specific test types
make test-unit         # Unit tests only
make test-integration  # Integration tests only

# Generate coverage report
make test-cov
```

### Docker Development

```bash
# Build and run with Docker Compose
make docker-dev

# Build Docker image
make build

# Clean up containers
make docker-clean
```

## 🔧 Configuration

Configure via environment variables or `.env` file:

```bash
# Database
MANAGER_DB_URL=sqlite:///./manager.db

# Worker limits
RUN_CPU_SECS=300
RUN_MEM_MB=512
RUN_TIMEOUT_SECS=1800

# Security
NO_NET=1
WORKER_SANDBOX=1

# API
API_HOST=0.0.0.0
API_PORT=8000
```

## 🛡️ Security Features

- **Process Isolation**: Workers run in separate processes with resource limits
- **Network Restrictions**: No network access by default (configurable)
- **Sandbox Execution**: Isolated working directories
- **Secret Detection**: Automated scanning for hardcoded credentials
- **Code Review**: Comprehensive static analysis and security checks

## 🔍 Quality Gates

All code must pass:

- **Linting**: Ruff checks for code quality
- **Formatting**: Black code formatting
- **Type Checking**: MyPy static type analysis
- **Testing**: pytest with ≥85% coverage requirement
- **Security**: Automated vulnerability scanning

## 📊 Monitoring

- **System Status**: Real-time queue and process monitoring
- **Execution Logs**: Detailed stdout/stderr capture
- **Artifacts**: Comprehensive run artifact storage
- **Health Checks**: API health endpoints for monitoring

## 🚢 Deployment

### Docker Deployment

```bash
# Production deployment
docker-compose -f ops/docker-compose.yml up -d

# With PostgreSQL backend
docker-compose -f ops/docker-compose.yml up -d
```

### Manual Deployment

```bash
# Production server
make run-prod

# Initialize production database
make db-init
```

## 📚 Documentation

- **API Documentation**: Available at `/docs` and `/redoc` when running
- **Architecture**: See `ARCHITECTURE.md` for detailed system design
- **Contributing**: See `CONTRIBUTING.md` for development guidelines
- **Decisions**: See `DECISIONS.md` for architectural decisions

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes following coding standards
4. Add tests for new functionality
5. Run quality checks (`make check`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open Pull Request

## 🔄 Task Lifecycle

1. **Submit**: Task specification submitted via CLI or API
2. **Plan**: Task analyzed and potentially decomposed into subtasks
3. **Queue**: Tasks queued for execution in FIFO order
4. **Execute**: Worker spawned in isolated environment
5. **Review**: Automated quality checks and validation
6. **Merge**: Approved changes integrated into codebase
7. **Archive**: Run artifacts stored for audit trail

## 📈 Examples

See the `examples/` directory for:

- `hello_task.json` - Basic FastAPI service creation
- Additional task specifications
- Integration test scenarios

## 🆘 Troubleshooting

### Common Issues

**Database locked errors:**
```bash
make db-reset
```

**Permission issues:**
```bash
# Ensure proper permissions on run directories
chmod -R 755 runs/ artifacts/ logs/
```

**Port already in use:**
```bash
# Change port in .env file
echo "API_PORT=8001" >> .env
```

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with development mode
export DEV_MODE=1

# Check system status
manager status

# View run logs
manager logs <run-id>
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SQLModel](https://sqlmodel.tiangolo.com/) - SQL databases in Python
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [pytest](https://pytest.org/) - Testing framework
- [Ruff](https://beta.ruff.rs/) - Python linter