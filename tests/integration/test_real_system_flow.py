"""Real system integration tests that verify actual functionality."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
import pytest
import time

from manager.core.manager import ManagerCore
from manager.core.schemas import TaskSpec, TaskStatus
from manager.core.queue import TaskQueue
from manager.store.models import DatabaseManager


@pytest.mark.integration
@pytest.mark.slow
class TestRealSystemFlow:
    """Test the complete system with real operations - no mocking."""

    async def test_complete_task_lifecycle_no_mocks(self, manager_core, sample_task_spec, temp_dir, test_utils):
        """Test complete task lifecycle with real operations."""
        
        # 1. Submit task - should create database entries
        task_id = await manager_core.submit_task(sample_task_spec)
        assert task_id == sample_task_spec.task_id
        
        # 2. Verify task is in database
        assert test_utils.verify_task_in_db(manager_core.queue, task_id)
        
        # 3. Verify task is queued
        queue_stats = manager_core.queue.get_queue_stats()
        assert queue_stats["queued"] >= 1
        
        # 4. Execute task synchronously (this will do real work)
        result = await manager_core.run_single_task(sample_task_spec)
        
        # 5. Verify execution results
        assert isinstance(result, dict)
        assert "success" in result
        assert "run_id" in result
        
        # 6. Verify run artifacts were actually created
        if result.get("success"):
            run_id = result["run_id"]
            pytest.assert_run_artifacts_exist(temp_dir, run_id)
            
            # 7. Verify artifact contents are valid JSON
            run_dir = temp_dir / "runs" / run_id
            
            # Check task spec was written correctly
            with open(run_dir / "task_spec.json") as f:
                stored_spec = json.load(f)
                assert stored_spec["task_id"] == task_id
            
            # Check worker report exists and has expected structure
            with open(run_dir / "worker_report.json") as f:
                worker_report = json.load(f)
                assert worker_report["task_id"] == task_id
                assert "summary" in worker_report
                assert "changes" in worker_report
            
            # Check PR proposal exists and has expected structure
            with open(run_dir / "pr_proposal.json") as f:
                pr_proposal = json.load(f)
                assert "pr_id" in pr_proposal
                assert "title" in pr_proposal

    @pytest.mark.database
    async def test_database_operations_real(self, test_db, sample_task_spec):
        """Test real database operations without mocks."""
        
        # Test direct database operations
        db = DatabaseManager()
        
        # 1. Create task in database
        task_data = {
            "task_id": sample_task_spec.task_id,
            "title": sample_task_spec.title,
            "goal": sample_task_spec.goal,
            "background": sample_task_spec.background,
            "inputs_json": json.dumps(sample_task_spec.inputs),
            "deliverables_json": json.dumps(sample_task_spec.deliverables),
            "acceptance_criteria_json": json.dumps(sample_task_spec.acceptance_criteria),
            "definition_of_done_json": json.dumps(sample_task_spec.definition_of_done),
            "risk_checks_json": json.dumps(sample_task_spec.risk_checks),
            "run_instructions_json": json.dumps(sample_task_spec.run_instructions),
            "timebox_hours": sample_task_spec.timebox_hours,
            "status": TaskStatus.QUEUED.value,
        }
        
        task_model = db.create_task(task_data)
        assert task_model.task_id == sample_task_spec.task_id
        
        # 2. Retrieve task from database
        retrieved_task = db.get_task(sample_task_spec.task_id)
        assert retrieved_task is not None
        assert retrieved_task.task_id == sample_task_spec.task_id
        assert retrieved_task.title == sample_task_spec.title
        
        # 3. Update task status
        db.update_task_status(sample_task_spec.task_id, TaskStatus.RUNNING.value)
        
        updated_task = db.get_task(sample_task_spec.task_id)
        assert updated_task.status == TaskStatus.RUNNING.value
        
        # 4. List tasks
        tasks = db.list_tasks(limit=10)
        assert len(tasks) >= 1
        assert any(task.task_id == sample_task_spec.task_id for task in tasks)

    @pytest.mark.filesystem
    async def test_artifact_management_real(self, temp_dir, sample_task_spec):
        """Test real file system operations for artifact management."""
        from manager.core.artifacts import ArtifactManager
        
        artifacts = ArtifactManager()
        run_id = "test-run-001"
        
        # 1. Create run directory
        run_dir = artifacts.create_run_directory(run_id)
        assert run_dir.exists()
        assert (run_dir / "workdir").exists()
        assert (run_dir / "logs").exists()
        assert (run_dir / "artifacts").exists()
        
        # 2. Write and read task spec
        task_dict = sample_task_spec.model_dump()
        spec_path = artifacts.write_task_spec(run_id, task_dict)
        assert spec_path.exists()
        
        read_spec = artifacts.read_task_spec(run_id)
        assert read_spec is not None
        assert read_spec["task_id"] == sample_task_spec.task_id
        
        # 3. Write and read log files
        test_log_content = "Test log content\nLine 2\nLine 3"
        log_path = artifacts.write_log_file(run_id, "test", test_log_content)
        assert log_path.exists()
        
        read_log = artifacts.read_log_file(run_id, "test")
        assert read_log == test_log_content
        
        # 4. Store and retrieve artifacts
        test_artifact_content = b"Binary test content"
        artifact_path = artifacts.store_artifact(run_id, "test.bin", test_artifact_content)
        assert artifact_path is not None
        assert artifact_path.exists()
        
        # 5. Get run summary
        summary = artifacts.get_run_summary(run_id)
        assert summary["run_id"] == run_id
        assert summary["has_task_spec"] is True
        assert len(summary["artifacts"]) >= 1

    @pytest.mark.subprocess 
    async def test_worker_execution_real_subprocess(self, temp_dir, real_workdir, sample_task_spec):
        """Test worker execution with real subprocess operations."""
        
        # This test will actually try to run the worker
        from manager.core.executor import WorkerExecutor
        
        executor = WorkerExecutor()
        
        # Create a simple task that should succeed
        simple_task = TaskSpec(
            task_id="T-subprocess-test",
            title="Simple subprocess test",
            goal="Test real subprocess execution",
            background="Testing subprocess functionality",
            deliverables=["simple output"],
            timebox_hours=0.5,  # Short timeout for test
        )
        
        try:
            # This will actually spawn a subprocess
            run_id, result = await executor.execute_task(simple_task)
            
            # Verify we got a result
            assert isinstance(result, dict)
            assert "success" in result
            assert run_id is not None
            
            # Check if run directory was created
            run_dir = temp_dir / "runs" / run_id
            assert run_dir.exists(), f"Run directory should exist: {run_dir}"
            
        except Exception as e:
            # If subprocess fails, we want to know why
            pytest.fail(f"Subprocess execution failed: {e}")

    @pytest.mark.integration
    async def test_queue_operations_real(self, task_queue, sample_task_spec, test_utils):
        """Test queue operations with real database."""
        
        # 1. Test enqueue
        task_id = task_queue.enqueue(sample_task_spec)
        assert task_id == sample_task_spec.task_id
        
        # 2. Verify in database
        assert test_utils.verify_task_in_db(task_queue, task_id)
        
        # 3. Test queue stats
        stats = task_queue.get_queue_stats()
        assert stats["total"] >= 1
        assert stats["queued"] >= 1
        
        # 4. Test dequeue
        dequeued_task = task_queue.dequeue()
        assert dequeued_task is not None
        assert dequeued_task.task_id == task_id
        
        # 5. Verify status change in database
        updated_stats = task_queue.get_queue_stats()
        assert updated_stats["running"] >= 1
        assert updated_stats["queued"] == stats["queued"] - 1

    @pytest.mark.integration
    async def test_manager_core_system_status_real(self, manager_core, sample_task_spec):
        """Test manager core system status with real data."""
        
        # 1. Get initial status
        status = manager_core.get_system_status()
        assert isinstance(status, dict)
        assert "dispatcher_running" in status
        assert "queue_stats" in status
        assert "active_runs" in status
        assert "timestamp" in status
        
        # 2. Submit a task and check status changes
        await manager_core.submit_task(sample_task_spec)
        
        updated_status = manager_core.get_system_status()
        assert updated_status["queue_stats"]["total"] >= 1

    @pytest.mark.integration
    async def test_error_handling_real(self, manager_core, temp_dir):
        """Test error handling with real problematic scenarios."""
        
        # 1. Test invalid task spec
        invalid_task = TaskSpec(
            task_id="",  # Invalid empty ID
            title="Invalid task",
            goal="This should fail",
            background="Testing error handling",
            timebox_hours=-1.0,  # Invalid timebox
        )
        
        with pytest.raises(ValueError, match="Invalid task spec"):
            await manager_core.submit_task(invalid_task)
        
        # 2. Test task with very short timeout
        timeout_task = TaskSpec(
            task_id="T-timeout-test",
            title="Timeout test",
            goal="This should timeout",
            background="Testing timeout handling",
            timebox_hours=0.001,  # Very short timeout
        )
        
        # Should handle timeout gracefully
        result = await manager_core.run_single_task(timeout_task)
        assert isinstance(result, dict)
        # May succeed or fail, but should not crash

    @pytest.mark.filesystem
    async def test_cleanup_operations_real(self, manager_core, temp_dir, sample_task_spec):
        """Test cleanup operations with real files."""
        
        # 1. Create some test data
        result = await manager_core.run_single_task(sample_task_spec)
        
        if result.get("success"):
            run_id = result["run_id"]
            run_dir = temp_dir / "runs" / run_id
            
            # Verify data exists before cleanup
            assert run_dir.exists()
            
            # 2. Test cleanup (won't actually clean new files due to retention policy)
            cleanup_result = await manager_core.cleanup_old_data()
            
            assert isinstance(cleanup_result, dict)
            assert "runs_cleaned" in cleanup_result
            assert "bytes_freed" in cleanup_result
            assert isinstance(cleanup_result["runs_cleaned"], int)
            assert isinstance(cleanup_result["bytes_freed"], int)

    @pytest.mark.slow
    async def test_concurrent_task_execution(self, manager_core):
        """Test handling multiple concurrent tasks."""
        
        tasks = []
        for i in range(3):
            task = TaskSpec(
                task_id=f"T-concurrent-{i:03d}",
                title=f"Concurrent test task {i}",
                goal=f"Test concurrent execution {i}",
                background="Testing concurrent operations",
                timebox_hours=0.5,
            )
            tasks.append(task)
        
        # Submit all tasks
        task_ids = []
        for task in tasks:
            task_id = await manager_core.submit_task(task)
            task_ids.append(task_id)
        
        # Verify all were submitted
        assert len(task_ids) == 3
        
        # Check queue stats
        status = manager_core.get_system_status()
        assert status["queue_stats"]["total"] >= 3

    @pytest.mark.integration
    async def test_task_validation_edge_cases(self, task_queue):
        """Test task validation with real edge cases."""
        
        # 1. Test very long task ID
        long_task = TaskSpec(
            task_id="T-" + "x" * 200,  # Very long ID
            title="Long ID test",
            goal="Test long identifier",
            background="Testing edge cases",
        )
        
        # Should not crash, may accept or reject
        errors = task_queue.validate_task_spec(long_task)
        assert isinstance(errors, list)
        
        # 2. Test task with special characters
        special_task = TaskSpec(
            task_id="T-special-\U0001F600",  # Unicode emoji
            title="Special chars: <>&\"'",
            goal="Test special character handling",
            background="Testing character encoding",
        )
        
        errors = task_queue.validate_task_spec(special_task)
        assert isinstance(errors, list)
        
        # 3. Test very large task
        huge_task = TaskSpec(
            task_id="T-huge",
            title="Huge task",
            goal="Test very large task specification",
            background="x" * 10000,  # Very long background
            deliverables=["item"] * 100,  # Many deliverables
            acceptance_criteria=["criteria"] * 50,  # Many criteria
        )
        
        errors = task_queue.validate_task_spec(huge_task)
        assert isinstance(errors, list)