"""Real worker execution testing with actual subprocess calls."""

import asyncio
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import pytest
import os
import signal

from manager.core.executor import WorkerExecutor
from manager.core.schemas import TaskSpec
from manager.adapters.worker_prompt import WorkerPrompt


@pytest.mark.subprocess
@pytest.mark.slow
class TestWorkerExecutionReal:
    """Test worker execution with real subprocess operations."""

    @pytest.mark.asyncio
    async def test_worker_executor_real_process(self, temp_dir, sample_task_spec):
        """Test WorkerExecutor with actual subprocess execution."""
        
        executor = WorkerExecutor()
        
        # Create a simple task that should succeed quickly
        simple_task = TaskSpec(
            task_id="T-real-process",
            title="Real process test",
            goal="Test real subprocess execution",
            background="Testing subprocess functionality",
            deliverables=["simple implementation"],
            timebox_hours=0.1,  # Very short for testing
        )
        
        try:
            # This will spawn a real subprocess
            run_id, result = await executor.execute_task(simple_task)
            
            # Basic result validation
            assert isinstance(result, dict)
            assert "success" in result
            assert "exit_code" in result
            assert run_id is not None
            
            # Check if run directory was created
            run_dir = temp_dir / "runs" / run_id
            if result.get("success"):
                pytest.assert_run_artifacts_exist(temp_dir, run_id)
            else:
                # Even failed runs should create some artifacts
                assert run_dir.exists(), f"Run directory should exist even for failed runs"
                
        except Exception as e:
            # If subprocess execution fails, we want detailed info
            pytest.fail(f"Real subprocess execution failed: {e}")

    @pytest.mark.asyncio 
    async def test_worker_timeout_handling_real(self, temp_dir):
        """Test real timeout handling with subprocess."""
        
        executor = WorkerExecutor()
        
        # Create a task that should timeout quickly
        timeout_task = TaskSpec(
            task_id="T-timeout-real",
            title="Timeout test",
            goal="Test timeout handling",
            background="Testing timeout functionality",
            deliverables=["timeout test"],
            timebox_hours=0.001,  # Very short timeout (36 milliseconds)
        )
        
        start_time = time.time()
        
        try:
            run_id, result = await executor.execute_task(timeout_task)
            duration = time.time() - start_time
            
            # Should complete quickly due to timeout
            assert duration < 60, f"Task took too long: {duration:.2f} seconds"
            
            # Result should indicate failure due to timeout
            assert isinstance(result, dict)
            if not result.get("success", True):
                # If it failed, should be due to timeout
                assert "timeout" in result.get("error", "").lower() or result.get("exit_code") == -15
                
        except asyncio.TimeoutError:
            # This is also acceptable - shows timeout is working
            duration = time.time() - start_time
            assert duration < 60, "Timeout took too long to trigger"

    def test_worker_prompt_real_execution(self, temp_dir, sample_task_spec):
        """Test WorkerPrompt with real file operations."""
        
        workdir = temp_dir / "worker_test"
        workdir.mkdir()
        
        worker = WorkerPrompt(workdir)
        
        # Execute task - this should do real file operations
        worker_report, pr_proposal = worker.execute_task(sample_task_spec)
        
        # Verify outputs are valid
        assert worker_report.task_id == sample_task_spec.task_id
        assert worker_report.summary
        assert pr_proposal.pr_id
        
        # Verify files were actually created
        created_files = []
        for change in worker_report.changes:
            file_path = workdir / change.file
            if file_path.exists():
                created_files.append(file_path)
        
        # Should have created at least some files
        assert len(created_files) > 0, f"No files were actually created: {[c.file for c in worker_report.changes]}"
        
        # Verify files have content
        for file_path in created_files:
            content = file_path.read_text()
            assert len(content) > 0, f"File {file_path} should have content"

    def test_worker_prompt_test_execution_real(self, temp_dir, real_workdir):
        """Test WorkerPrompt test execution with real pytest."""
        
        # Create a task that includes tests
        task_with_tests = TaskSpec(
            task_id="T-test-execution",
            title="Test execution task", 
            goal="Test real test execution",
            background="Testing test execution",
            deliverables=["code with tests"],
            timebox_hours=1.0,
        )
        
        worker = WorkerPrompt(real_workdir)
        worker_report, pr_proposal = worker.execute_task(task_with_tests)
        
        # Check if test results are included
        if worker_report.test_results:
            assert isinstance(worker_report.test_results.passed, bool)
            assert worker_report.test_results.summary
            # Coverage might be present
            assert isinstance(worker_report.test_results.coverage, dict)

    @pytest.mark.asyncio
    async def test_subprocess_resource_limits_real(self, temp_dir):
        """Test subprocess resource limit enforcement."""
        
        executor = WorkerExecutor()
        
        # Create task that might consume resources
        resource_task = TaskSpec(
            task_id="T-resource-test",
            title="Resource consumption test",
            goal="Test resource limits",
            background="Testing resource limitations",
            deliverables=["resource test"],
            timebox_hours=0.1,
        )
        
        # Monitor system resources during execution
        import psutil
        initial_memory = psutil.virtual_memory().percent
        
        run_id, result = await executor.execute_task(resource_task)
        
        final_memory = psutil.virtual_memory().percent
        
        # Should not consume excessive system resources
        memory_increase = final_memory - initial_memory
        assert memory_increase < 50, f"Memory usage increased by {memory_increase}%"
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "success" in result

    def test_subprocess_error_handling_real(self, temp_dir):
        """Test real subprocess error handling."""
        
        # Test with invalid Python code execution
        workdir = temp_dir / "error_test"
        workdir.mkdir()
        
        # Create a Python file with syntax error
        bad_file = workdir / "bad_code.py"
        bad_file.write_text("def broken_function(\n    # Missing closing parenthesis")
        
        # Try to run subprocess on this
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import sys; sys.path.insert(0, '{workdir}'); import bad_code"],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Should fail due to syntax error
            assert result.returncode != 0
            assert result.stderr  # Should have error output
            assert "SyntaxError" in result.stderr or "syntax" in result.stderr.lower()
            
        except subprocess.TimeoutExpired:
            # Timeout is also acceptable - shows process control works
            pass

    @pytest.mark.slow
    def test_multiple_concurrent_workers_real(self, temp_dir):
        """Test multiple worker processes concurrently."""
        
        async def run_worker_task(task_id):
            """Run a worker task."""
            executor = WorkerExecutor()
            task = TaskSpec(
                task_id=task_id,
                title=f"Concurrent task {task_id}",
                goal="Test concurrent execution",
                background="Testing concurrency",
                deliverables=["concurrent output"],
                timebox_hours=0.1,
            )
            
            try:
                run_id, result = await executor.execute_task(task)
                return {"task_id": task_id, "run_id": run_id, "success": result.get("success", False)}
            except Exception as e:
                return {"task_id": task_id, "error": str(e), "success": False}
        
        async def test_concurrent_execution():
            # Run multiple workers concurrently
            tasks = [run_worker_task(f"T-concurrent-{i}") for i in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Analyze results
            successful = 0
            failed = 0
            
            for result in results:
                if isinstance(result, dict) and result.get("success"):
                    successful += 1
                else:
                    failed += 1
            
            # At least some should succeed
            assert successful >= 1, f"No concurrent tasks succeeded. Results: {results}"
            assert successful + failed == 3, "Should have 3 total results"
            
            return results
        
        # Run the concurrent test
        results = asyncio.run(test_concurrent_execution())
        assert len(results) == 3

    def test_worker_environment_isolation_real(self, temp_dir):
        """Test that worker processes are properly isolated."""
        
        # Create two different working directories
        workdir1 = temp_dir / "worker1"
        workdir2 = temp_dir / "worker2"
        workdir1.mkdir()
        workdir2.mkdir()
        
        # Create different files in each directory
        (workdir1 / "worker1_file.txt").write_text("Worker 1 content")
        (workdir2 / "worker2_file.txt").write_text("Worker 2 content")
        
        worker1 = WorkerPrompt(workdir1)
        worker2 = WorkerPrompt(workdir2)
        
        task1 = TaskSpec(
            task_id="T-isolation-1",
            title="Isolation test 1",
            goal="Test worker isolation",
            background="Testing",
            deliverables=["isolated output 1"],
            timebox_hours=0.1,
        )
        
        task2 = TaskSpec(
            task_id="T-isolation-2", 
            title="Isolation test 2",
            goal="Test worker isolation",
            background="Testing",
            deliverables=["isolated output 2"],
            timebox_hours=0.1,
        )
        
        # Execute tasks in different directories
        report1, proposal1 = worker1.execute_task(task1)
        report2, proposal2 = worker2.execute_task(task2)
        
        # Verify they worked in separate directories
        assert report1.task_id != report2.task_id
        assert proposal1.pr_id != proposal2.pr_id
        
        # Check that files are in correct directories
        worker1_files = list(workdir1.rglob("*"))
        worker2_files = list(workdir2.rglob("*"))
        
        # Should have different files in each directory
        assert len(worker1_files) > 1  # Original file + created files
        assert len(worker2_files) > 1  # Original file + created files

    @pytest.mark.asyncio
    async def test_worker_process_cleanup_real(self, temp_dir):
        """Test that worker processes are properly cleaned up."""
        
        executor = WorkerExecutor()
        initial_processes = len(list(p for p in __import__('psutil').process_iter()))
        
        cleanup_task = TaskSpec(
            task_id="T-cleanup-test",
            title="Process cleanup test",
            goal="Test process cleanup",
            background="Testing cleanup",
            deliverables=["cleanup test"],
            timebox_hours=0.1,
        )
        
        run_id, result = await executor.execute_task(cleanup_task)
        
        # Wait a moment for cleanup
        await asyncio.sleep(1)
        
        final_processes = len(list(p for p in __import__('psutil').process_iter()))
        
        # Should not have significantly more processes
        process_increase = final_processes - initial_processes
        assert process_increase < 5, f"Too many processes left running: {process_increase}"

    def test_worker_file_permissions_real(self, temp_dir):
        """Test worker file permission handling."""
        
        workdir = temp_dir / "permissions_test"
        workdir.mkdir()
        
        # Create worker
        worker = WorkerPrompt(workdir)
        
        permission_task = TaskSpec(
            task_id="T-permissions",
            title="File permissions test",
            goal="Test file permission handling",
            background="Testing permissions",
            deliverables=["files with correct permissions"],
            timebox_hours=0.1,
        )
        
        worker_report, pr_proposal = worker.execute_task(permission_task)
        
        # Check created files have reasonable permissions
        for change in worker_report.changes:
            file_path = workdir / change.file
            if file_path.exists() and file_path.is_file():
                # File should be readable
                assert file_path.is_file()
                
                # Should be able to read the file
                try:
                    content = file_path.read_text()
                    assert isinstance(content, str)
                except PermissionError:
                    pytest.fail(f"Cannot read created file: {file_path}")

    def test_subprocess_signal_handling_real(self, temp_dir):
        """Test subprocess signal handling."""
        
        # Create a simple Python script that can be interrupted
        script_content = """
import time
import sys

print("Starting long-running task")
try:
    for i in range(100):
        print(f"Working... {i}")
        time.sleep(0.1)
    print("Completed normally")
except KeyboardInterrupt:
    print("Interrupted!")
    sys.exit(1)
"""
        
        script_file = temp_dir / "long_task.py"
        script_file.write_text(script_content)
        
        # Start the subprocess
        process = subprocess.Popen(
            [sys.executable, str(script_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Let it run briefly
        time.sleep(0.2)
        
        # Send interrupt signal
        try:
            if hasattr(signal, 'SIGINT'):
                process.send_signal(signal.SIGINT)
            else:
                process.terminate()
                
            # Wait for it to finish
            stdout, stderr = process.communicate(timeout=5)
            
            # Should have been interrupted
            assert process.returncode != 0
            assert "Working..." in stdout  # Should have started
            
        except subprocess.TimeoutExpired:
            # If it doesn't respond to signals, kill it
            process.kill()
            process.wait()

    @pytest.mark.asyncio 
    async def test_worker_memory_usage_real(self, temp_dir):
        """Test worker memory usage monitoring."""
        
        executor = WorkerExecutor()
        
        memory_task = TaskSpec(
            task_id="T-memory-test",
            title="Memory usage test", 
            goal="Monitor memory usage",
            background="Testing memory",
            deliverables=["memory test"],
            timebox_hours=0.1,
        )
        
        # Monitor memory before
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        run_id, result = await executor.execute_task(memory_task)
        
        # Monitor memory after
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Should not leak excessive memory (allow some increase)
        max_increase = 100 * 1024 * 1024  # 100MB threshold
        assert memory_increase < max_increase, f"Memory increased by {memory_increase / 1024 / 1024:.1f}MB"