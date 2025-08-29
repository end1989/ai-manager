"""Integration test for complete manager-worker flow."""

import asyncio
import json
import os
import pytest
import tempfile
from pathlib import Path

from manager.core.manager import ManagerCore
from manager.core.schemas import TaskSpec
from manager.store.models import create_db_and_tables


@pytest.fixture
def temp_env():
    """Set up temporary environment for integration testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Set environment variables for test database
        original_db_url = os.environ.get("MANAGER_DB_URL")
        os.environ["MANAGER_DB_URL"] = f"sqlite:///{temp_path / 'test.db'}"
        
        # Create test directories
        (temp_path / "runs").mkdir()
        (temp_path / "artifacts").mkdir()
        (temp_path / "logs").mkdir()
        
        try:
            # Initialize database
            create_db_and_tables()
            yield temp_path
        finally:
            # Restore original environment
            if original_db_url:
                os.environ["MANAGER_DB_URL"] = original_db_url
            elif "MANAGER_DB_URL" in os.environ:
                del os.environ["MANAGER_DB_URL"]


@pytest.fixture
def manager_core(temp_env):
    """Create manager core instance for testing."""
    return ManagerCore()


@pytest.fixture
def hello_task_spec():
    """Create hello task specification."""
    return TaskSpec(
        task_id="T-integration-001",
        title="Integration test task",
        goal="Create a minimal FastAPI service with health endpoint for integration testing",
        background="Testing the complete manager-worker flow",
        inputs=["FastAPI framework", "Pydantic models"],
        deliverables=[
            "FastAPI service with /health endpoint",
            "Unit tests with coverage",
            "README documentation"
        ],
        acceptance_criteria=[
            "/health endpoint returns 200 status",
            "Response includes status and timestamp",
            "Tests pass with >85% coverage"
        ],
        timebox_hours=1.0,
    )


@pytest.mark.asyncio
async def test_complete_task_flow(manager_core, hello_task_spec):
    """Test complete task submission to completion flow."""
    
    # Step 1: Submit task
    task_id = await manager_core.submit_task(hello_task_spec)
    assert task_id == hello_task_spec.task_id
    
    # Verify task was queued
    queued_task = manager_core.queue.get_task(task_id)
    assert queued_task is not None
    assert queued_task.task_id == task_id
    
    # Step 2: Run task synchronously (instead of using dispatcher)
    result = await manager_core.run_single_task(hello_task_spec)
    
    # Step 3: Verify execution succeeded
    assert result["success"] is True
    assert "run_id" in result
    assert result["task_id"] == task_id
    
    run_id = result["run_id"]
    
    # Step 4: Verify artifacts were created
    run_summary = manager_core.artifacts.get_run_summary(run_id)
    assert run_summary["has_task_spec"] is True
    assert run_summary["has_worker_report"] is True
    assert run_summary["has_pr_proposal"] is True
    
    # Step 5: Verify worker report content
    worker_report_data = manager_core.artifacts.read_worker_report(run_id)
    assert worker_report_data is not None
    assert worker_report_data["task_id"] == task_id
    assert len(worker_report_data["changes"]) > 0
    
    # Step 6: Verify PR proposal content
    pr_proposal_data = manager_core.artifacts.read_pr_proposal(run_id)
    assert pr_proposal_data is not None
    assert pr_proposal_data["pr_id"].startswith("PR-")
    assert pr_proposal_data["title"]
    assert len(pr_proposal_data["diff_summary"]) > 0
    
    # Step 7: Verify review was performed
    assert "review_status" in result
    assert result["review_status"] in ["approved", "changes_requested", "rejected"]


@pytest.mark.asyncio
async def test_task_validation_flow(manager_core):
    """Test task validation and error handling."""
    
    # Create invalid task
    invalid_task = TaskSpec(
        task_id="",  # Invalid empty ID
        title="",    # Invalid empty title
        goal="",     # Invalid empty goal
        background="Test background",
        timebox_hours=-1.0,  # Invalid negative timebox
    )
    
    # Should raise validation error
    with pytest.raises(ValueError) as exc_info:
        await manager_core.submit_task(invalid_task)
    
    assert "Invalid task spec" in str(exc_info.value)


@pytest.mark.asyncio
async def test_task_planning_flow(manager_core):
    """Test task planning and decomposition."""
    
    # Create complex task that might be decomposed
    complex_task = TaskSpec(
        task_id="T-complex-001",
        title="Complex multi-deliverable task",
        goal="Create a complete microservice with multiple components",
        background="Testing task decomposition",
        deliverables=[
            "API endpoints",
            "Database models", 
            "Frontend components",
            "Documentation",
            "Deployment scripts"
        ],
        timebox_hours=8.0,  # Long enough to potentially trigger decomposition
    )
    
    # Submit task
    task_id = await manager_core.submit_task(complex_task)
    
    # Verify task was submitted
    assert task_id == complex_task.task_id
    
    # Check if task was decomposed by counting related tasks
    all_tasks = manager_core.queue.list_tasks(limit=100)
    related_tasks = [t for t in all_tasks if t.task_id.startswith("T-complex-001")]
    
    # Should have at least the original task
    assert len(related_tasks) >= 1


@pytest.mark.asyncio
async def test_queue_operations_flow(manager_core):
    """Test queue operations and task status transitions."""
    
    # Create test tasks
    tasks = []
    for i in range(3):
        task = TaskSpec(
            task_id=f"T-queue-{i:03d}",
            title=f"Queue test task {i}",
            goal=f"Test queue operations {i}",
            background="Queue testing",
            timebox_hours=0.5,
        )
        tasks.append(task)
    
    # Submit all tasks
    for task in tasks:
        await manager_core.submit_task(task)
    
    # Verify all tasks are queued
    queue_stats = manager_core.queue.get_queue_stats()
    assert queue_stats["queued"] >= 3
    
    # Test dequeue operation
    dequeued_task = manager_core.queue.dequeue()
    assert dequeued_task is not None
    assert dequeued_task.task_id == tasks[0].task_id
    
    # Verify stats updated
    updated_stats = manager_core.queue.get_queue_stats()
    assert updated_stats["running"] >= 1


@pytest.mark.asyncio
async def test_error_handling_flow(manager_core):
    """Test error handling in the complete flow."""
    
    # Create a task that might fail
    problematic_task = TaskSpec(
        task_id="T-error-test",
        title="Problematic task",
        goal="Test error handling",
        background="This task is designed to test error scenarios",
        deliverables=["impossible deliverable"],
        timebox_hours=0.1,  # Very short timebox
    )
    
    # Submit and run task
    task_id = await manager_core.submit_task(problematic_task)
    result = await manager_core.run_single_task(problematic_task)
    
    # Should handle errors gracefully
    assert "success" in result
    assert "error" in result or result["success"] is True
    
    # Check if run artifacts exist even for failed tasks
    if "run_id" in result:
        run_summary = manager_core.artifacts.get_run_summary(result["run_id"])
        assert "error" not in run_summary or run_summary["run_id"] == result["run_id"]


@pytest.mark.asyncio
async def test_system_status_flow(manager_core):
    """Test system status monitoring."""
    
    # Get initial system status
    status = manager_core.get_system_status()
    
    assert "dispatcher_running" in status
    assert "queue_stats" in status
    assert "active_runs" in status
    assert "timestamp" in status
    
    # Verify queue stats structure
    queue_stats = status["queue_stats"]
    assert "total" in queue_stats
    assert "queued" in queue_stats
    assert "running" in queue_stats
    assert "completed" in queue_stats


@pytest.mark.asyncio
async def test_artifact_management_flow(manager_core, hello_task_spec):
    """Test artifact creation and management."""
    
    # Run a task to generate artifacts
    result = await manager_core.run_single_task(hello_task_spec)
    assert result["success"] is True
    
    run_id = result["run_id"]
    
    # Test artifact retrieval
    run_summary = manager_core.artifacts.get_run_summary(run_id)
    
    assert run_summary["run_id"] == run_id
    assert "created_at" in run_summary
    assert "size_bytes" in run_summary
    assert "artifacts" in run_summary
    
    # Test log file access
    stdout_content = manager_core.artifacts.read_log_file(run_id, "stdout")
    # Note: stdout might be empty for successful runs
    
    # Test task spec retrieval
    task_spec_data = manager_core.artifacts.read_task_spec(run_id)
    assert task_spec_data is not None
    assert task_spec_data["task_id"] == hello_task_spec.task_id


@pytest.mark.asyncio
async def test_cleanup_flow(manager_core):
    """Test cleanup operations."""
    
    # Create some test data first
    test_task = TaskSpec(
        task_id="T-cleanup-test",
        title="Cleanup test task",
        goal="Generate artifacts for cleanup testing",
        background="Testing cleanup",
        timebox_hours=0.5,
    )
    
    result = await manager_core.run_single_task(test_task)
    assert result["success"] is True
    
    # Test cleanup (won't actually clean recent data due to retention policy)
    cleanup_result = await manager_core.cleanup_old_data()
    
    assert "runs_cleaned" in cleanup_result
    assert "bytes_freed" in cleanup_result
    assert isinstance(cleanup_result["runs_cleaned"], int)
    assert isinstance(cleanup_result["bytes_freed"], int)