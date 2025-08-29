"""FastAPI HTTP API for AI Manager."""

import logging
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

from manager.config import settings
from manager.core.manager import ManagerCore
from manager.core.schemas import (
    RunListResponse,
    TaskListResponse,
    TaskResponse,
    TaskSpec,
    TaskSubmission,
    TaskStatus,
)
from manager.web.dashboard import DashboardManager
from manager.web.websocket import WebSocketManager

logger = logging.getLogger(__name__)

# Global instances
manager: Optional[ManagerCore] = None
dashboard_manager: Optional[DashboardManager] = None
websocket_manager: Optional[WebSocketManager] = None

app = FastAPI(
    title="AI Manager",
    description="Local-first AI task management infrastructure with real-time dashboard",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Mount static files
static_path = Path(__file__).parent.parent / "web" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


def get_manager() -> ManagerCore:
    """Get manager instance (dependency injection)."""
    global manager
    if manager is None:
        manager = ManagerCore()
    return manager


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting AI Manager API with Dashboard")
    
    # Initialize manager
    global manager, dashboard_manager, websocket_manager
    manager = ManagerCore()
    dashboard_manager = DashboardManager()
    websocket_manager = WebSocketManager()
    
    # Clear any phantom tasks from database to prevent infinite loops
    try:
        tasks = manager.db.list_tasks(limit=1000)
        cleared_count = 0
        for task in tasks:
            if task.status in ["QUEUED", "RUNNING"]:
                manager.db.update_task_status(task.task_id, "CANCELLED")
                cleared_count += 1
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} phantom tasks from database")
    except Exception as e:
        logger.warning(f"Could not clear phantom tasks: {e}")
    
    # Dispatcher disabled for initial testing to avoid infinite loops
    # Start dispatcher if not in dev mode
    # if not settings.dev_mode:
    #     await manager.start_dispatcher()
    
    logger.info("AI Manager API started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down AI Manager API")
    
    if manager:
        await manager.stop_dispatcher()
    
    logger.info("AI Manager API stopped")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Manager API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


@app.post("/tasks", response_model=TaskResponse)
async def submit_task(
    submission: TaskSubmission,
    background_tasks: BackgroundTasks,
    manager: ManagerCore = Depends(get_manager),
):
    """Submit a new task."""
    
    try:
        task_id = await manager.submit_task(submission.spec)
        
        # Get task info for response
        task_model = manager.db.get_task(task_id)
        if not task_model:
            raise HTTPException(status_code=500, detail="Failed to create task")
        
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus(task_model.status),
            created_at=task_model.created_at,
            updated_at=task_model.updated_at,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Task submission error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = None,
    search: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    manager: ManagerCore = Depends(get_manager),
):
    """List tasks with advanced filtering and search capabilities."""
    
    try:
        # Parse status filter
        status_filter = None
        if status:
            try:
                status_filter = TaskStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        # Parse date filters
        from datetime import datetime
        created_after_dt = None
        created_before_dt = None
        
        if created_after:
            try:
                created_after_dt = datetime.fromisoformat(created_after.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid created_after date format: {created_after}")
        
        if created_before:
            try:
                created_before_dt = datetime.fromisoformat(created_before.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid created_before date format: {created_before}")
        
        # Validate sort parameters
        valid_sort_fields = ["created_at", "updated_at", "task_id", "status"]
        if sort_by not in valid_sort_fields:
            raise HTTPException(status_code=400, detail=f"Invalid sort_by field. Must be one of: {valid_sort_fields}")
        
        if sort_order not in ["asc", "desc"]:
            raise HTTPException(status_code=400, detail="Invalid sort_order. Must be 'asc' or 'desc'")
        
        # Get all tasks from database with filters
        all_task_models = manager.db.list_tasks_advanced(
            status=status_filter,
            search=search,
            created_after=created_after_dt,
            created_before=created_before_dt,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Convert to response format with pagination
        task_responses = []
        for task_model in all_task_models[offset:offset + limit]:
            task_responses.append(TaskResponse(
                task_id=task_model.task_id,
                status=TaskStatus(task_model.status),
                created_at=task_model.created_at,
                updated_at=task_model.updated_at,
            ))
        
        return TaskListResponse(
            tasks=task_responses,
            total=len(all_task_models),
        )
        
    except Exception as e:
        logger.error(f"Task listing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/tasks/templates")
async def list_task_templates():
    """List available task templates."""
    
    templates = [
        # Basic Templates
        {
            "id": "python-module",
            "name": "Python Module",
            "description": "Create a Python module with comprehensive tests and documentation",
            "deliverables": ["Python module", "Unit tests", "README.md", "requirements.txt"],
            "timebox_hours": 2.0,
            "category": "basic",
            "complexity": "low"
        },
        {
            "id": "fastapi-service",
            "name": "FastAPI Service",
            "description": "Create a FastAPI microservice with endpoints and tests",
            "deliverables": ["FastAPI service", "API tests", "OpenAPI documentation", "Docker configuration"],
            "timebox_hours": 4.0,
            "category": "web",
            "complexity": "medium"
        },
        {
            "id": "data-analysis",
            "name": "Data Analysis Script",
            "description": "Create a data analysis script with visualizations and reports",
            "deliverables": ["Analysis script", "Jupyter notebook", "Visualization charts", "Summary report"],
            "timebox_hours": 3.0,
            "category": "data-science",
            "complexity": "medium"
        },
        {
            "id": "cli-tool",
            "name": "CLI Tool",
            "description": "Create a command-line tool with argument parsing and help",
            "deliverables": ["CLI script", "Command tests", "Usage documentation", "Installation guide"],
            "timebox_hours": 2.5,
            "category": "basic",
            "complexity": "low"
        },
        
        # Advanced Real-World Templates
        {
            "id": "ml-pipeline",
            "name": "Machine Learning Pipeline",
            "description": "Build a complete ML pipeline with data processing, model training, and inference API",
            "deliverables": [
                "Data preprocessing modules",
                "Model training scripts",
                "Model evaluation metrics",
                "FastAPI inference service",
                "Docker containerization",
                "CI/CD pipeline config",
                "Model versioning system",
                "Comprehensive test suite",
                "Documentation and examples"
            ],
            "timebox_hours": 8.0,
            "category": "machine-learning",
            "complexity": "high"
        },
        {
            "id": "microservice-ecosystem",
            "name": "Microservice Ecosystem",
            "description": "Create a multi-service architecture with API gateway, database, and monitoring",
            "deliverables": [
                "API Gateway service",
                "User management service",
                "Data service with database",
                "Message queue integration",
                "Service discovery setup",
                "Docker Compose orchestration",
                "Health check endpoints",
                "Load testing scripts",
                "Monitoring and logging",
                "API documentation"
            ],
            "timebox_hours": 12.0,
            "category": "architecture",
            "complexity": "high"
        },
        {
            "id": "react-dashboard",
            "name": "React Dashboard Application",
            "description": "Build a modern React dashboard with charts, real-time data, and responsive design",
            "deliverables": [
                "React application structure",
                "Component library",
                "Chart.js integrations",
                "WebSocket client",
                "State management (Redux)",
                "Responsive CSS/Styled Components",
                "Unit tests with Jest",
                "Storybook documentation",
                "Build and deployment scripts"
            ],
            "timebox_hours": 10.0,
            "category": "frontend",
            "complexity": "high"
        },
        {
            "id": "blockchain-dapp",
            "name": "Blockchain DApp",
            "description": "Develop a decentralized application with smart contracts and web3 integration",
            "deliverables": [
                "Solidity smart contracts",
                "Contract deployment scripts",
                "Web3.js frontend integration",
                "MetaMask connectivity",
                "Event listening system",
                "Security audit checklist",
                "Gas optimization analysis",
                "Unit tests for contracts",
                "Frontend UI components"
            ],
            "timebox_hours": 15.0,
            "category": "blockchain",
            "complexity": "high"
        },
        {
            "id": "data-warehouse",
            "name": "Data Warehouse ETL",
            "description": "Build a scalable data warehouse with ETL pipelines and analytics dashboards",
            "deliverables": [
                "Data extraction modules",
                "Transformation pipelines",
                "Data quality checks",
                "Database schema design",
                "Apache Airflow DAGs",
                "Data validation tests",
                "Performance monitoring",
                "Analytics SQL queries",
                "Reporting dashboards"
            ],
            "timebox_hours": 12.0,
            "category": "data-engineering",
            "complexity": "high"
        },
        {
            "id": "mobile-app-backend",
            "name": "Mobile App Backend",
            "description": "Create a scalable backend API for mobile applications with authentication and push notifications",
            "deliverables": [
                "REST API endpoints",
                "JWT authentication system",
                "Push notification service",
                "File upload handling",
                "Database models and migrations",
                "API rate limiting",
                "Caching layer (Redis)",
                "API documentation",
                "Load testing suite"
            ],
            "timebox_hours": 8.0,
            "category": "mobile-backend",
            "complexity": "high"
        },
        {
            "id": "iot-platform",
            "name": "IoT Data Platform",
            "description": "Build an IoT platform for collecting, processing, and visualizing sensor data",
            "deliverables": [
                "MQTT broker setup",
                "Device data ingestion",
                "Time-series database",
                "Real-time stream processing",
                "Device management API",
                "Alert system",
                "Data visualization dashboard",
                "Device simulation tools",
                "Scaling documentation"
            ],
            "timebox_hours": 14.0,
            "category": "iot",
            "complexity": "high"
        },
        {
            "id": "e-commerce-platform",
            "name": "E-Commerce Platform",
            "description": "Develop a complete e-commerce solution with payment processing and inventory management",
            "deliverables": [
                "Product catalog API",
                "Shopping cart system",
                "Payment gateway integration",
                "Inventory management",
                "Order processing workflow",
                "User authentication",
                "Admin dashboard",
                "Email notification system",
                "Search and filtering"
            ],
            "timebox_hours": 16.0,
            "category": "e-commerce",
            "complexity": "high"
        },
        {
            "id": "devops-infrastructure",
            "name": "DevOps Infrastructure",
            "description": "Set up complete DevOps infrastructure with CI/CD, monitoring, and automation",
            "deliverables": [
                "Terraform infrastructure code",
                "GitHub Actions workflows",
                "Docker multi-stage builds",
                "Kubernetes deployments",
                "Prometheus monitoring",
                "Grafana dashboards",
                "Log aggregation (ELK)",
                "Security scanning",
                "Backup and recovery"
            ],
            "timebox_hours": 12.0,
            "category": "devops",
            "complexity": "high"
        },
        {
            "id": "ai-chatbot",
            "name": "AI-Powered Chatbot",
            "description": "Create an intelligent chatbot with NLP processing and learning capabilities",
            "deliverables": [
                "NLP processing pipeline",
                "Intent recognition system",
                "Conversation flow engine",
                "Knowledge base integration",
                "Learning and feedback system",
                "Multi-platform deployment",
                "Analytics dashboard",
                "Training data management",
                "Performance optimization"
            ],
            "timebox_hours": 10.0,
            "category": "artificial-intelligence",
            "complexity": "high"
        }
    ]
    
    return {"templates": templates, "total": len(templates)}


@app.get("/tasks/{task_id}", response_model=TaskSpec)
async def get_task(
    task_id: str,
    manager: ManagerCore = Depends(get_manager),
):
    """Get task details."""
    
    task = manager.queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@app.post("/tasks/{task_id}/run")
async def run_task(
    task_id: str,
    manager: ManagerCore = Depends(get_manager),
):
    """Run a single task synchronously (for testing)."""
    
    task = manager.queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        result = await manager.run_single_task(task)
        return result
    except Exception as e:
        logger.error(f"Single task run error: {str(e)}")
        raise HTTPException(status_code=500, detail="Task execution failed")


@app.get("/runs")
async def list_runs(
    task_id: Optional[str] = None,
    limit: int = 100,
    manager: ManagerCore = Depends(get_manager),
):
    """List runs, optionally filtered by task."""
    
    try:
        # This is a simplified implementation
        # In practice, you'd query the database for runs
        runs = []  # manager.get_runs(task_id=task_id, limit=limit)
        
        return RunListResponse(runs=runs, total=len(runs))
        
    except Exception as e:
        logger.error(f"Run listing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/runs/{run_id}")
async def get_run(
    run_id: str,
    manager: ManagerCore = Depends(get_manager),
):
    """Get run details."""
    
    try:
        run_model = manager.db.get_run(run_id)
        if not run_model:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Get run summary
        summary = manager.artifacts.get_run_summary(run_id)
        
        return {
            "run_id": run_id,
            "task_id": run_model.task_id,
            "status": run_model.status,
            "started_at": run_model.started_at,
            "completed_at": run_model.completed_at,
            "exit_code": run_model.exit_code,
            "artifacts_path": run_model.artifacts_path,
            "summary": summary,
        }
        
    except Exception as e:
        logger.error(f"Run retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/runs/{run_id}/logs/{log_name}")
async def get_run_logs(
    run_id: str,
    log_name: str,
    manager: ManagerCore = Depends(get_manager),
):
    """Get run logs."""
    
    # Validate run exists
    run_model = manager.db.get_run(run_id)
    if not run_model:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get log content
    log_content = manager.artifacts.read_log_file(run_id, log_name)
    if log_content is None:
        raise HTTPException(status_code=404, detail="Log file not found")
    
    return {"run_id": run_id, "log_name": log_name, "content": log_content}


@app.post("/runs/{run_id}/stop")
async def stop_run(
    run_id: str,
    manager: ManagerCore = Depends(get_manager),
):
    """Stop a running task."""
    
    try:
        success = await manager.executor.stop_run(run_id)
        if not success:
            raise HTTPException(status_code=400, detail="Could not stop run")
        
        return {"message": "Run stopped", "run_id": run_id}
        
    except Exception as e:
        logger.error(f"Stop run error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/status")
async def get_system_status(manager: ManagerCore = Depends(get_manager)):
    """Get system status."""
    
    try:
        status = manager.get_system_status()
        return status
    except Exception as e:
        logger.error(f"Status retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/dispatcher/start")
async def start_dispatcher(manager: ManagerCore = Depends(get_manager)):
    """Start the task dispatcher."""
    
    try:
        await manager.start_dispatcher()
        return {"message": "Dispatcher started"}
    except Exception as e:
        logger.error(f"Dispatcher start error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not start dispatcher")


@app.post("/dispatcher/stop")
async def stop_dispatcher(manager: ManagerCore = Depends(get_manager)):
    """Stop the task dispatcher."""
    
    try:
        await manager.stop_dispatcher()
        return {"message": "Dispatcher stopped"}
    except Exception as e:
        logger.error(f"Dispatcher stop error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not stop dispatcher")


@app.post("/cleanup")
async def cleanup_old_data(manager: ManagerCore = Depends(get_manager)):
    """Clean up old data."""
    
    try:
        result = await manager.cleanup_old_data()
        return {"message": "Cleanup completed", "details": result}
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Cleanup failed")


# Task Operations
@app.post("/tasks/{task_id}/clone")
async def clone_task(
    task_id: str,
    new_task_id: Optional[str] = None,
    manager: ManagerCore = Depends(get_manager)
):
    """Clone an existing task with a new ID."""
    
    try:
        # Get original task
        original_task = manager.queue.get_task(task_id)
        if not original_task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Generate new task ID if not provided
        if not new_task_id:
            import uuid
            new_task_id = f"{task_id}-clone-{str(uuid.uuid4())[:8]}"
        
        # Create cloned task spec
        cloned_spec = TaskSpec(
            task_id=new_task_id,
            title=f"[CLONE] {original_task.title}",
            goal=original_task.goal,
            background=f"Cloned from {task_id}. {original_task.background}",
            inputs=original_task.inputs,
            deliverables=original_task.deliverables,
            acceptance_criteria=original_task.acceptance_criteria,
            definition_of_done=original_task.definition_of_done,
            risk_checks=original_task.risk_checks,
            run_instructions=original_task.run_instructions,
            timebox_hours=original_task.timebox_hours
        )
        
        # Submit cloned task
        new_task_id = await manager.submit_task(cloned_spec)
        
        # Get task info for response
        task_model = manager.db.get_task(new_task_id)
        if not task_model:
            raise HTTPException(status_code=500, detail="Failed to create cloned task")
        
        return TaskResponse(
            task_id=new_task_id,
            status=TaskStatus(task_model.status),
            created_at=task_model.created_at,
            updated_at=task_model.updated_at,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Task cloning error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/tasks/bulk/cancel")
async def bulk_cancel_tasks(
    task_ids: list[str],
    manager: ManagerCore = Depends(get_manager)
):
    """Cancel multiple tasks at once."""
    
    try:
        results = []
        
        for task_id in task_ids:
            try:
                # Cancel task and any running executions
                success = await manager.cancel_task(task_id)
                results.append({
                    "task_id": task_id,
                    "success": success,
                    "message": "Cancelled" if success else "Could not cancel"
                })
            except Exception as e:
                results.append({
                    "task_id": task_id,
                    "success": False,
                    "message": str(e)
                })
        
        return {
            "message": f"Processed {len(task_ids)} tasks",
            "results": results,
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"])
        }
        
    except Exception as e:
        logger.error(f"Bulk cancel error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


class CreateTaskFromTemplateRequest(BaseModel):
    """Request model for creating task from template."""
    title: str
    goal: str
    background: str = ""
    custom_deliverables: Optional[list[str]] = None
    custom_timebox: Optional[float] = None


@app.post("/tasks/from-template/{template_id}", response_model=TaskResponse)
async def create_task_from_template(
    template_id: str,
    request: CreateTaskFromTemplateRequest,
    manager: ManagerCore = Depends(get_manager)
):
    """Create a new task from a template."""
    
    try:
        # Define comprehensive template configurations
        templates = {
            # Basic Templates
            "python-module": {
                "deliverables": ["Python module with class", "Unit tests with pytest", "README.md with examples", "requirements.txt"],
                "definition_of_done": ["All tests pass", "Code coverage >= 90%", "ruff check passes", "mypy passes"],
                "timebox_hours": 2.0
            },
            "fastapi-service": {
                "deliverables": ["FastAPI service with endpoints", "API tests", "OpenAPI documentation", "Docker configuration"],
                "definition_of_done": ["All tests pass", "API documented", "Docker builds", "Health checks work"],
                "timebox_hours": 4.0
            },
            "data-analysis": {
                "deliverables": ["Analysis script", "Jupyter notebook", "Data visualizations", "Summary report"],
                "definition_of_done": ["Analysis complete", "Charts generated", "Report written", "Code documented"],
                "timebox_hours": 3.0
            },
            "cli-tool": {
                "deliverables": ["CLI script with argparse", "Command tests", "Usage documentation", "Installation guide"],
                "definition_of_done": ["CLI functional", "Tests pass", "Help system works", "Installable"],
                "timebox_hours": 2.5
            },
            
            # Advanced Real-World Templates
            "ml-pipeline": {
                "deliverables": ["Data preprocessing modules", "Model training scripts", "Model evaluation metrics", "FastAPI inference service", "Docker containerization", "CI/CD pipeline config", "Model versioning system", "Comprehensive test suite", "Documentation and examples"],
                "definition_of_done": ["Pipeline runs end-to-end", "Model metrics acceptable", "API inference working", "Docker builds successfully", "Tests pass with >85% coverage", "Documentation complete"],
                "timebox_hours": 8.0
            },
            "microservice-ecosystem": {
                "deliverables": ["API Gateway service", "User management service", "Data service with database", "Message queue integration", "Service discovery setup", "Docker Compose orchestration", "Health check endpoints", "Load testing scripts", "Monitoring and logging", "API documentation"],
                "definition_of_done": ["All services start successfully", "Inter-service communication works", "Load tests pass", "Health checks responsive", "Monitoring dashboards functional", "API docs complete"],
                "timebox_hours": 12.0
            },
            "react-dashboard": {
                "deliverables": ["React application structure", "Component library", "Chart.js integrations", "WebSocket client", "State management (Redux)", "Responsive CSS/Styled Components", "Unit tests with Jest", "Storybook documentation", "Build and deployment scripts"],
                "definition_of_done": ["Application builds successfully", "All components render properly", "Charts display data correctly", "WebSocket connections work", "Tests pass >90% coverage", "Responsive on all devices"],
                "timebox_hours": 10.0
            },
            "blockchain-dapp": {
                "deliverables": ["Solidity smart contracts", "Contract deployment scripts", "Web3.js frontend integration", "MetaMask connectivity", "Event listening system", "Security audit checklist", "Gas optimization analysis", "Unit tests for contracts", "Frontend UI components"],
                "definition_of_done": ["Contracts deploy successfully", "Frontend connects to blockchain", "MetaMask integration works", "Events are captured properly", "Security audit passed", "Gas usage optimized"],
                "timebox_hours": 15.0
            },
            "data-warehouse": {
                "deliverables": ["Data extraction modules", "Transformation pipelines", "Data quality checks", "Database schema design", "Apache Airflow DAGs", "Data validation tests", "Performance monitoring", "Analytics SQL queries", "Reporting dashboards"],
                "definition_of_done": ["ETL pipeline runs successfully", "Data quality checks pass", "Airflow DAGs scheduled", "Performance acceptable", "Dashboards render data", "SQL queries optimized"],
                "timebox_hours": 12.0
            },
            "mobile-app-backend": {
                "deliverables": ["REST API endpoints", "JWT authentication system", "Push notification service", "File upload handling", "Database models and migrations", "API rate limiting", "Caching layer (Redis)", "API documentation", "Load testing suite"],
                "definition_of_done": ["All endpoints functional", "Authentication secure", "Push notifications work", "File uploads handle all types", "Database performance good", "Rate limiting effective", "Load tests pass"],
                "timebox_hours": 8.0
            },
            "iot-platform": {
                "deliverables": ["MQTT broker setup", "Device data ingestion", "Time-series database", "Real-time stream processing", "Device management API", "Alert system", "Data visualization dashboard", "Device simulation tools", "Scaling documentation"],
                "definition_of_done": ["MQTT broker operational", "Data ingestion reliable", "Stream processing responsive", "Device management functional", "Alerts trigger correctly", "Dashboard shows live data", "Simulation tools work"],
                "timebox_hours": 14.0
            },
            "e-commerce-platform": {
                "deliverables": ["Product catalog API", "Shopping cart system", "Payment gateway integration", "Inventory management", "Order processing workflow", "User authentication", "Admin dashboard", "Email notification system", "Search and filtering"],
                "definition_of_done": ["Product catalog browsable", "Cart operations work", "Payments process successfully", "Inventory tracks accurately", "Order workflow complete", "User auth secure", "Admin functions operational"],
                "timebox_hours": 16.0
            },
            "devops-infrastructure": {
                "deliverables": ["Terraform infrastructure code", "GitHub Actions workflows", "Docker multi-stage builds", "Kubernetes deployments", "Prometheus monitoring", "Grafana dashboards", "Log aggregation (ELK)", "Security scanning", "Backup and recovery"],
                "definition_of_done": ["Infrastructure provisions", "CI/CD pipeline functional", "Docker builds optimized", "K8s deployments stable", "Monitoring captures metrics", "Dashboards show data", "Security scans pass"],
                "timebox_hours": 12.0
            },
            "ai-chatbot": {
                "deliverables": ["NLP processing pipeline", "Intent recognition system", "Conversation flow engine", "Knowledge base integration", "Learning and feedback system", "Multi-platform deployment", "Analytics dashboard", "Training data management", "Performance optimization"],
                "definition_of_done": ["NLP pipeline processes text", "Intent recognition accurate", "Conversations flow naturally", "Knowledge base accessible", "Learning improves responses", "Deploys to all platforms", "Analytics track usage"],
                "timebox_hours": 10.0
            }
        }
        
        if template_id not in templates:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template = templates[template_id]
        
        # Generate unique task ID
        import datetime, uuid
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        task_id = f"{template_id.upper()}-{timestamp}-{str(uuid.uuid4())[:8]}"
        
        # Create task spec from template
        task_spec = TaskSpec(
            task_id=task_id,
            title=request.title,
            goal=request.goal,
            background=request.background or f"Generated from {template_id} template",
            deliverables=request.custom_deliverables or template["deliverables"],
            definition_of_done=template["definition_of_done"],
            timebox_hours=request.custom_timebox or template["timebox_hours"]
        )
        
        # Submit task
        new_task_id = await manager.submit_task(task_spec)
        
        # Get task info for response
        task_model = manager.db.get_task(new_task_id)
        if not task_model:
            raise HTTPException(status_code=500, detail="Failed to create task from template")
        
        return TaskResponse(
            task_id=new_task_id,
            status=TaskStatus(task_model.status),
            created_at=task_model.created_at,
            updated_at=task_model.updated_at,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Template task creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Dashboard Routes
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML page."""
    dashboard_path = Path(__file__).parent.parent / "web" / "static" / "dashboard.html"
    if not dashboard_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(dashboard_path)


@app.get("/api/dashboard/data")
async def get_dashboard_data():
    """Get current dashboard data."""
    global dashboard_manager
    if not dashboard_manager:
        dashboard_manager = DashboardManager()
    
    try:
        data = dashboard_manager.get_dashboard_data()
        return data.model_dump()
    except Exception as e:
        logger.error(f"Dashboard data error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    global websocket_manager
    if not websocket_manager:
        websocket_manager = WebSocketManager()
    
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        websocket_manager.disconnect(websocket)


@app.post("/api/dashboard/alert")
async def send_dashboard_alert(
    alert_type: str,
    message: str,
    severity: str = "info"
):
    """Send alert to all dashboard clients."""
    global websocket_manager
    if not websocket_manager:
        websocket_manager = WebSocketManager()
    
    await websocket_manager.send_system_alert(alert_type, message, severity)
    return {"status": "alert_sent"}


# Review System Routes
@app.get("/reviews/pending")
async def get_pending_reviews(
    priority: Optional[str] = None,
    manager: ManagerCore = Depends(get_manager)
):
    """Get pending reviews for human approval."""
    try:
        reviews = manager.reviewer.get_pending_reviews(priority)
        
        # Convert datetime objects to strings for JSON serialization
        for review in reviews:
            if "submitted_at" in review:
                review["submitted_at"] = review["submitted_at"].isoformat()
        
        return {
            "reviews": reviews,
            "count": len(reviews)
        }
    except Exception as e:
        logger.error(f"Get pending reviews error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get pending reviews")


@app.post("/reviews/{review_id}/approve")
async def approve_review(
    review_id: str,
    approver: str,
    comments: str = "",
    manager: ManagerCore = Depends(get_manager)
):
    """Approve a pending review."""
    try:
        success = manager.reviewer.approve_review(review_id, approver, comments)
        
        if not success:
            raise HTTPException(status_code=404, detail="Review not found")
        
        # Send notification to dashboard
        global websocket_manager
        if websocket_manager:
            await websocket_manager.send_system_alert(
                "review_approved", 
                f"Review {review_id} approved by {approver}",
                "success"
            )
        
        return {"status": "approved", "review_id": review_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approve review error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to approve review")


@app.post("/reviews/{review_id}/reject")
async def reject_review(
    review_id: str,
    reviewer: str,
    reason: str,
    manager: ManagerCore = Depends(get_manager)
):
    """Reject a pending review."""
    try:
        success = manager.reviewer.reject_review(review_id, reviewer, reason)
        
        if not success:
            raise HTTPException(status_code=404, detail="Review not found")
        
        # Send notification to dashboard
        global websocket_manager
        if websocket_manager:
            await websocket_manager.send_system_alert(
                "review_rejected",
                f"Review {review_id} rejected by {reviewer}: {reason}",
                "warning"
            )
        
        return {"status": "rejected", "review_id": review_id, "reason": reason}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reject review error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reject review")


@app.get("/reviews/stats")
async def get_review_stats(manager: ManagerCore = Depends(get_manager)):
    """Get review system statistics."""
    try:
        stats = manager.reviewer.get_review_stats()
        return stats
    except Exception as e:
        logger.error(f"Get review stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get review stats")


@app.post("/tasks/{task_id}/ai-review")
async def request_ai_review(
    task_id: str,
    manager: ManagerCore = Depends(get_manager)
):
    """Request AI-powered review for a completed task."""
    try:
        # Get task and its latest run
        task_model = manager.db.get_task(task_id)
        if not task_model:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Find latest run for this task
        runs = manager.db.list_runs(task_id=task_id, limit=1)
        if not runs:
            raise HTTPException(status_code=400, detail="No runs found for task")
        
        latest_run = runs[0]
        
        # Get run artifacts
        run_path = settings.runs_dir / latest_run.run_id
        workdir = run_path / "workdir"
        
        if not workdir.exists():
            raise HTTPException(status_code=400, detail="Run workdir not found")
        
        # Load worker report and PR proposal
        worker_report_path = workdir / "worker_report.json"
        pr_proposal_path = workdir / "pr_proposal.json"
        
        if not (worker_report_path.exists() and pr_proposal_path.exists()):
            raise HTTPException(status_code=400, detail="Run artifacts not found")
        
        # Load the reports
        import json
        from manager.core.schemas import WorkerTaskReport, PullRequestProposal
        
        with open(worker_report_path, 'r') as f:
            worker_report_data = json.load(f)
        with open(pr_proposal_path, 'r') as f:
            pr_proposal_data = json.load(f)
        
        worker_report = WorkerTaskReport(**worker_report_data)
        pr_proposal = PullRequestProposal(**pr_proposal_data)
        
        # Perform AI review
        ai_result, review_id = await manager.reviewer.ai_review_pr(
            pr_proposal, worker_report, workdir
        )
        
        # Send notification to dashboard
        global websocket_manager
        if websocket_manager:
            await websocket_manager.send_system_alert(
                "ai_review_completed",
                f"AI review completed for task {task_id}: {ai_result.decision.value}",
                "info"
            )
        
        return {
            "review_id": review_id,
            "decision": ai_result.decision,
            "quality_score": ai_result.quality_score,
            "quality_grade": ai_result.quality_grade,
            "maintainability_score": ai_result.maintainability_score,
            "test_coverage": ai_result.test_coverage_assessment,
            "issues_count": len(ai_result.issues),
            "security_concerns_count": len(ai_result.security_concerns),
            "suggestions_count": len(ai_result.suggestions),
            "reviewer_comments": ai_result.reviewer_comments,
            "approval_conditions": ai_result.approval_conditions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI review error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI review failed: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )