"""Worker CLI for executing individual tasks."""

import asyncio
import json
import sys
from pathlib import Path

import typer
from rich.console import Console

from manager.adapters.worker_prompt import WorkerPrompt
from manager.core.schemas import TaskSpec

app = typer.Typer(
    name="worker",
    help="AI Manager Worker CLI - Execute tasks",
    no_args_is_help=True,
)

console = Console()


@app.command("run")
def run_task(
    task_file: Path = typer.Option(..., "--task", help="Task specification JSON file"),
    workdir: Path = typer.Option(Path.cwd(), "--workdir", help="Working directory"),
):
    """Execute a task from specification file."""
    
    if not task_file.exists():
        console.print(f"[ERROR] Task file not found: {task_file}", style="red")
        raise typer.Exit(1)
    
    try:
        # Load task specification
        with open(task_file, "r", encoding="utf-8") as f:
            task_data = json.load(f)
        
        task_spec = TaskSpec(**task_data)
        
        console.print(f"[EXEC] Starting task execution: {task_spec.task_id}", style="blue")
        console.print(f"Title: {task_spec.title}")
        console.print(f"Working directory: {workdir}")
        console.print()
        
        # Create worker and execute task asynchronously
        worker = WorkerPrompt(workdir)
        worker_report, pr_proposal = asyncio.run(worker.execute_task(task_spec))
        
        # Write outputs to files
        report_path = workdir / "worker_report.json"
        proposal_path = workdir / "pr_proposal.json"
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(worker_report.model_dump(), f, indent=2, default=str)
        
        with open(proposal_path, "w", encoding="utf-8") as f:
            json.dump(pr_proposal.model_dump(), f, indent=2, default=str)
        
        console.print(f"[OK] Task execution completed", style="green")
        console.print(f"Worker report: {report_path}")
        console.print(f"PR proposal: {proposal_path}")
        
        # Show summary
        console.print("\n[SUMMARY] Execution Summary:", style="bold")
        console.print(f"Files changed: {len(worker_report.changes)}")
        console.print(f"Commands run: {len(worker_report.commands_run)}")
        console.print(f"Tests passed: {'OK' if worker_report.test_results and worker_report.test_results.passed else 'FAIL'}")
        console.print(f"Open issues: {len(worker_report.open_issues)}")
        
        if worker_report.changes:
            console.print("\n[CHANGES] File Changes:")
            for change in worker_report.changes:
                icon = "[+]" if change.change_type.value == "added" else "[*]" if change.change_type.value == "modified" else "[-]"
                console.print(f"  {icon} {change.file} ({change.change_type.value})")
        
        if worker_report.open_issues:
            console.print("\n[WARN] Open Issues:", style="yellow")
            for issue in worker_report.open_issues:
                console.print(f"  - {issue.desc}")
                console.print(f"    Mitigation: {issue.mitigation}")
        
        # Exit with appropriate code
        if worker_report.test_results and not worker_report.test_results.passed:
            console.print("\n[ERROR] Some tests failed", style="red")
            raise typer.Exit(1)
        
    except json.JSONDecodeError as e:
        console.print(f"[ERROR] Invalid JSON in task file: {e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[ERROR] Error executing task: {e}", style="red")
        console.print(f"Error details: {str(e)}")
        raise typer.Exit(1)


@app.command("validate")
def validate_task(
    task_file: Path = typer.Argument(..., help="Task specification JSON file"),
):
    """Validate a task specification file."""
    
    if not task_file.exists():
        console.print(f"[ERROR] Task file not found: {task_file}", style="red")
        raise typer.Exit(1)
    
    try:
        # Load and validate task specification
        with open(task_file, "r", encoding="utf-8") as f:
            task_data = json.load(f)
        
        task_spec = TaskSpec(**task_data)
        
        console.print(f"[OK] Task specification is valid", style="green")
        console.print(f"Task ID: {task_spec.task_id}")
        console.print(f"Title: {task_spec.title}")
        console.print(f"Deliverables: {len(task_spec.deliverables)}")
        console.print(f"Timebox: {task_spec.timebox_hours} hours")
        
    except json.JSONDecodeError as e:
        console.print(f"[ERROR] Invalid JSON: {e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[ERROR] Invalid task specification: {e}", style="red")
        raise typer.Exit(1)


@app.command("test")
def test_worker():
    """Test worker functionality with a simple task."""
    
    # Create a simple test task
    test_task = TaskSpec(
        task_id="T-test-worker",
        title="Test worker functionality",
        goal="Verify that worker can execute basic tasks",
        background="Testing worker implementation",
        deliverables=["simple Python script"],
        timebox_hours=0.5,
    )
    
    console.print("[TEST] Testing worker functionality...", style="blue")
    
    try:
        # Create temporary work directory
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            workdir = Path(temp_dir)
            
            # Execute test task
            worker = WorkerPrompt(workdir)
            worker_report, pr_proposal = asyncio.run(worker.execute_task(test_task))
            
            console.print("[OK] Worker test completed successfully", style="green")
            console.print(f"Created {len(worker_report.changes)} files")
            console.print(f"Generated PR proposal: {pr_proposal.pr_id}")
            
            return True
            
    except Exception as e:
        console.print(f"[ERROR] Worker test failed: {e}", style="red")
        raise typer.Exit(1)


@app.command("info")
def show_info():
    """Show worker information and capabilities."""
    
    console.print("[INFO] AI Manager Worker", style="bold blue")
    console.print()
    
    console.print("[CAPS] Capabilities:", style="bold")
    console.print("• Execute task specifications")
    console.print("• Generate FastAPI services")
    console.print("• Create comprehensive tests")  
    console.print("• Write documentation")
    console.print("• Generate PR proposals")
    console.print("• Run quality checks")
    
    console.print("\n[DELIVER] Supported Deliverables:", style="bold")
    console.print("• API endpoints (FastAPI)")
    console.print("• Unit tests (pytest)")
    console.print("• Documentation (Markdown)")
    console.print("• Generic Python modules")
    
    console.print("\n[OUTPUT] Output Artifacts:", style="bold")
    console.print("• worker_report.json - Execution report")
    console.print("• pr_proposal.json - Pull request proposal")
    console.print("• Implementation files in working directory")
    console.print("• Test files and documentation")
    
    console.print("\n[QUALITY] Quality Checks:", style="bold")
    console.print("• Automated test execution")
    console.print("• Code coverage analysis")
    console.print("• Linting and formatting")
    console.print("• Type checking")
    
    console.print("\n[SAFETY] Safety Features:", style="bold")
    console.print("• Isolated execution environment")
    console.print("• Resource limits and timeouts")
    console.print("• No network access by default")
    console.print("• Comprehensive logging")


if __name__ == "__main__":
    app()