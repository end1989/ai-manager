"""Manager CLI for task submission, monitoring, and control."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.json import JSON

from manager.config import settings
from manager.core.manager import ManagerCore
from manager.core.schemas import TaskSpec, TaskStatus

app = typer.Typer(
    name="manager",
    help="AI Manager CLI - Submit and manage tasks",
    no_args_is_help=True,
)

console = Console()


def get_manager() -> ManagerCore:
    """Get manager instance."""
    return ManagerCore()


@app.command("submit")
def submit_task(
    task_file: Path = typer.Option(..., "-f", "--file", help="Task specification JSON file"),
    run_immediately: bool = typer.Option(False, "--run", help="Run task immediately"),
):
    """Submit a new task from JSON file."""
    
    if not task_file.exists():
        console.print(f"❌ Task file not found: {task_file}", style="red")
        raise typer.Exit(1)
    
    try:
        # Load task specification
        with open(task_file, "r", encoding="utf-8") as f:
            task_data = json.load(f)
        
        task_spec = TaskSpec(**task_data)
        
        # Submit task
        manager = get_manager()
        task_id = asyncio.run(manager.submit_task(task_spec))
        
        console.print(f"✅ Task submitted successfully", style="green")
        console.print(f"Task ID: {task_id}")
        
        if run_immediately:
            console.print("🚀 Running task immediately...")
            result = asyncio.run(manager.run_single_task(task_spec))
            
            if result["success"]:
                console.print(f"✅ Task completed: {result['review_status']}", style="green")
                console.print(f"Run ID: {result['run_id']}")
                console.print(f"Execution time: {result.get('execution_time', 0):.1f}s")
                
                if result.get("blocking_issues"):
                    console.print("⚠️ Blocking issues found:", style="yellow")
                    for issue in result["blocking_issues"]:
                        console.print(f"  - {issue}")
            else:
                console.print(f"❌ Task failed: {result.get('error', 'Unknown error')}", style="red")
        
    except json.JSONDecodeError as e:
        console.print(f"❌ Invalid JSON in task file: {e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Error submitting task: {e}", style="red")
        raise typer.Exit(1)


@app.command("list")
def list_tasks(
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    limit: int = typer.Option(20, "--limit", help="Maximum number of tasks to show"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List tasks with optional status filter."""
    
    try:
        manager = get_manager()
        
        # Parse status filter
        status_filter = None
        if status:
            try:
                status_filter = TaskStatus(status)
            except ValueError:
                console.print(f"❌ Invalid status: {status}", style="red")
                console.print(f"Valid statuses: {', '.join([s.value for s in TaskStatus])}")
                raise typer.Exit(1)
        
        # Get tasks
        tasks = manager.queue.list_tasks(status=status_filter, limit=limit)
        
        if json_output:
            # Output as JSON
            task_data = []
            for task in tasks:
                task_model = manager.db.get_task(task.task_id)
                if task_model:
                    task_data.append({
                        "task_id": task.task_id,
                        "title": task.title,
                        "status": task_model.status,
                        "created_at": task_model.created_at.isoformat(),
                        "timebox_hours": task.timebox_hours,
                    })
            
            console.print(JSON.from_data(task_data))
        else:
            # Display as table
            if not tasks:
                console.print("No tasks found.")
                return
            
            table = Table(title=f"Tasks {f'(status: {status})' if status else ''}")
            table.add_column("Task ID", style="cyan")
            table.add_column("Title", style="white")
            table.add_column("Status", style="yellow")
            table.add_column("Created", style="dim")
            table.add_column("Timebox", justify="right", style="magenta")
            
            for task in tasks:
                task_model = manager.db.get_task(task.task_id)
                if task_model:
                    table.add_row(
                        task.task_id,
                        task.title[:50] + "..." if len(task.title) > 50 else task.title,
                        task_model.status,
                        task_model.created_at.strftime("%Y-%m-%d %H:%M"),
                        f"{task.timebox_hours:.1f}h",
                    )
            
            console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error listing tasks: {e}", style="red")
        raise typer.Exit(1)


@app.command("show")
def show_task(task_id: str):
    """Show detailed task information."""
    
    try:
        manager = get_manager()
        task = manager.queue.get_task(task_id)
        
        if not task:
            console.print(f"❌ Task not found: {task_id}", style="red")
            raise typer.Exit(1)
        
        # Get task model for status info
        task_model = manager.db.get_task(task_id)
        
        console.print(f"📋 Task Details: {task_id}", style="bold")
        console.print()
        
        table = Table(show_header=False, box=None)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Title", task.title)
        table.add_row("Status", task_model.status if task_model else "unknown")
        table.add_row("Goal", task.goal)
        table.add_row("Background", task.background)
        table.add_row("Timebox", f"{task.timebox_hours} hours")
        
        if task.deliverables:
            table.add_row("Deliverables", ", ".join(task.deliverables))
        
        if task.acceptance_criteria:
            table.add_row("Acceptance Criteria", "\n".join(f"• {c}" for c in task.acceptance_criteria))
        
        if task_model:
            table.add_row("Created", task_model.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            table.add_row("Updated", task_model.updated_at.strftime("%Y-%m-%d %H:%M:%S"))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error showing task: {e}", style="red")
        raise typer.Exit(1)


@app.command("status")
def system_status():
    """Show system status."""
    
    try:
        manager = get_manager()
        status = manager.get_system_status()
        
        console.print("🖥️ System Status", style="bold")
        console.print()
        
        # Dispatcher status
        dispatcher_emoji = "🟢" if status["dispatcher_running"] else "🔴"
        console.print(f"{dispatcher_emoji} Dispatcher: {'Running' if status['dispatcher_running'] else 'Stopped'}")
        
        # Queue stats
        queue_stats = status["queue_stats"]
        console.print(f"📊 Queue Stats:")
        console.print(f"  Total: {queue_stats['total']}")
        console.print(f"  Queued: {queue_stats['queued']}")
        console.print(f"  Running: {queue_stats['running']}")
        console.print(f"  Awaiting Review: {queue_stats['awaiting_review']}")
        console.print(f"  Completed: {queue_stats['completed']}")
        console.print(f"  Failed: {queue_stats['failed']}")
        
        # Active runs
        console.print(f"⚡ Active Runs: {status['active_runs']}")
        
        console.print(f"🕐 Last Updated: {status['timestamp']}")
        
    except Exception as e:
        console.print(f"❌ Error getting status: {e}", style="red")
        raise typer.Exit(1)


@app.command("dispatcher")
def dispatcher_control(
    action: str = typer.Argument(..., help="Action: start, stop, status"),
):
    """Control the task dispatcher."""
    
    try:
        manager = get_manager()
        
        if action == "start":
            asyncio.run(manager.start_dispatcher())
            console.print("✅ Dispatcher started", style="green")
        
        elif action == "stop":
            asyncio.run(manager.stop_dispatcher())
            console.print("✅ Dispatcher stopped", style="green")
        
        elif action == "status":
            status = manager.get_system_status()
            if status["dispatcher_running"]:
                console.print("🟢 Dispatcher is running", style="green")
            else:
                console.print("🔴 Dispatcher is stopped", style="red")
        
        else:
            console.print(f"❌ Invalid action: {action}. Use: start, stop, status", style="red")
            raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"❌ Error controlling dispatcher: {e}", style="red")
        raise typer.Exit(1)


@app.command("logs")
def show_logs(
    run_id: str,
    log_type: str = typer.Option("stdout", help="Log type: stdout, stderr"),
    tail: int = typer.Option(50, help="Number of lines to show"),
):
    """Show logs for a run."""
    
    try:
        manager = get_manager()
        
        # Check if run exists
        run_model = manager.db.get_run(run_id)
        if not run_model:
            console.print(f"❌ Run not found: {run_id}", style="red")
            raise typer.Exit(1)
        
        # Get log content
        log_content = manager.artifacts.read_log_file(run_id, log_type)
        
        if not log_content:
            console.print(f"📝 No {log_type} logs found for run {run_id}")
            return
        
        # Show logs
        console.print(f"📝 {log_type.upper()} logs for run {run_id}:", style="bold")
        console.print()
        
        lines = log_content.split('\n')
        if len(lines) > tail:
            console.print(f"... (showing last {tail} lines) ...")
            lines = lines[-tail:]
        
        for line in lines:
            console.print(line)
        
    except Exception as e:
        console.print(f"❌ Error showing logs: {e}", style="red")
        raise typer.Exit(1)


@app.command("cleanup")
def cleanup_old_data():
    """Clean up old run data."""
    
    try:
        manager = get_manager()
        result = asyncio.run(manager.cleanup_old_data())
        
        console.print("🧹 Cleanup completed", style="green")
        console.print(f"Runs cleaned: {result['runs_cleaned']}")
        console.print(f"Space freed: {result['bytes_freed'] / 1024 / 1024:.1f} MB")
        
    except Exception as e:
        console.print(f"❌ Error during cleanup: {e}", style="red")
        raise typer.Exit(1)


@app.command("generate-task")
def generate_task_template(
    output_file: Path = typer.Option("task.json", "-o", "--output", help="Output file path"),
):
    """Generate a task specification template."""
    
    template = {
        "task_id": "T-example-001",
        "title": "Create example service",
        "goal": "Implement a simple FastAPI service with health endpoint",
        "background": "We need a basic health check service for monitoring",
        "inputs": [
            "FastAPI framework",
            "Pydantic for data validation"
        ],
        "deliverables": [
            "FastAPI service with /health endpoint",
            "Unit tests with >85% coverage",
            "README.md documentation"
        ],
        "acceptance_criteria": [
            "/health endpoint returns 200 status",
            "Response includes timestamp and version",
            "Tests pass with coverage >85%",
            "Code passes linting checks"
        ],
        "definition_of_done": [
            "ruff+black clean",
            "mypy passes",
            "pytest passes",
            "coverage >= 85% on changed lines",
            "docs updated if behavior changed"
        ],
        "risk_checks": [
            "performance risks?",
            "security validation?",
            "edge cases & failure paths?"
        ],
        "run_instructions": [
            "uvicorn main:app --reload",
            "pytest tests/ --cov"
        ],
        "timebox_hours": 2.0
    }
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2)
        
        console.print(f"✅ Task template generated: {output_file}", style="green")
        console.print("Edit the file and use `manager submit -f task.json` to submit the task.")
        
    except Exception as e:
        console.print(f"❌ Error generating template: {e}", style="red")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()