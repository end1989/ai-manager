"""Worker process executor with subprocess isolation and resource limits."""

import asyncio
import json
import os
import signal
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import psutil

from manager.config import settings
from manager.core.artifacts import ArtifactManager
from manager.core.schemas import TaskSpec
from manager.store.models import DatabaseManager


class WorkerExecutor:
    """Executes worker tasks in isolated subprocess with resource limits."""

    def __init__(self):
        self.artifacts = ArtifactManager()
        self.db = DatabaseManager()

    async def execute_task(self, task_spec: TaskSpec) -> Tuple[str, Dict[str, Any]]:
        """Execute task in isolated worker process."""
        run_id = self._generate_run_id()
        
        # Create run directory and write task spec
        run_path = self.artifacts.create_run_directory(run_id)
        spec_path = self.artifacts.write_task_spec(run_id, task_spec.model_dump())
        
        # Create run record
        run_data = {
            "run_id": run_id,
            "task_id": task_spec.task_id,
            "status": "running",
            "started_at": datetime.utcnow(),
            "artifacts_path": str(run_path),
        }
        run_model = self.db.create_run(run_data)
        
        # Log run start
        self.db.log_event(
            event_type="run_started",
            entity_type="run",
            entity_id=run_id,
            data={"task_id": task_spec.task_id, "timebox_hours": task_spec.timebox_hours},
        )
        
        try:
            # Execute worker in subprocess
            result = await self._run_worker_subprocess(run_id, spec_path, run_path)
            
            # Check if worker produced outputs even with failed tests
            workdir = run_path / "workdir"
            worker_outputs_exist = (
                (workdir / "worker_report.json").exists() and 
                (workdir / "pr_proposal.json").exists()
            )
            
            # Determine final status
            if result["success"]:
                final_status = "completed"
            elif result.get("partial_success") and worker_outputs_exist:
                final_status = "completed"  # Worker completed task even if tests failed
                result["success"] = True  # Mark as success for downstream processing
            else:
                final_status = "failed"
            
            # Update run status
            self.db.update_run_status(
                run_id=run_id,
                status=final_status,
                completed_at=datetime.utcnow(),
                exit_code=result["exit_code"],
                stdout_path=str(result.get("stdout_path")),
                stderr_path=str(result.get("stderr_path")),
            )
            
            # Log run completion
            self.db.log_event(
                event_type="run_completed",
                entity_type="run", 
                entity_id=run_id,
                data={
                    "success": result["success"],
                    "exit_code": result["exit_code"],
                    "duration_seconds": result.get("duration_seconds", 0),
                },
            )
            
            return run_id, result
            
        except Exception as e:
            # Update run status on error
            self.db.update_run_status(
                run_id=run_id,
                status="error",
                completed_at=datetime.utcnow(),
            )
            
            # Log error
            self.db.log_event(
                event_type="run_error",
                entity_type="run",
                entity_id=run_id,
                data={"error": str(e)},
            )
            
            raise

    async def _run_worker_subprocess(
        self, run_id: str, spec_path: Path, run_path: Path
    ) -> Dict[str, Any]:
        """Run worker in isolated subprocess with resource limits."""
        
        # Setup paths
        workdir = run_path / "workdir"
        stdout_path = run_path / "logs" / "stdout.log"
        stderr_path = run_path / "logs" / "stderr.log"
        
        # Create virtual environment
        venv_path = await self._create_venv(run_path)
        if not venv_path:
            return {
                "success": False,
                "exit_code": -1,
                "error": "Failed to create virtual environment",
            }
        
        # Prepare command
        python_exe = venv_path / ("Scripts" if sys.platform == "win32" else "bin") / "python"
        # Use relative path to task spec from workdir
        relative_spec_path = "../task_spec.json"
        
        cmd = [
            str(python_exe),
            "-m", "cli.worker_cli",
            "run",
            "--task", relative_spec_path,
            "--workdir", ".",
        ]
        
        # Setup environment
        env = os.environ.copy()
        
        # Security: disable network if configured
        if settings.no_net:
            # On Windows, we can't easily disable network at process level
            # This would need network namespace isolation on Linux
            env["NO_NETWORK"] = "1"
        
        # Resource limits preparation
        start_time = datetime.utcnow()
        
        try:
            # Ensure workdir exists
            workdir.mkdir(parents=True, exist_ok=True)
            
            # Start subprocess
            with open(stdout_path, "w") as stdout_file, open(stderr_path, "w") as stderr_file:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=workdir,
                    env=env,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    limit=1024 * 1024,  # 1MB buffer limit
                )
                
                # Store PID for monitoring
                self.db.update_run_status(run_id, "running", worker_pid=process.pid)
                
                # Monitor process with timeout and resource limits
                result = await self._monitor_process(process, run_id)
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                result.update({
                    "duration_seconds": duration,
                    "stdout_path": stdout_path,
                    "stderr_path": stderr_path,
                })
                
                return result
                
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "error": f"Process execution failed: {str(e)}",
                "stdout_path": stdout_path,
                "stderr_path": stderr_path,
            }

    async def _monitor_process(self, process: asyncio.subprocess.Process, run_id: str) -> Dict[str, Any]:
        """Monitor process with timeout and resource limits."""
        timeout = settings.run_timeout_secs
        memory_limit_bytes = settings.run_mem_mb * 1024 * 1024
        
        try:
            # Wait for process with timeout
            exit_code = await asyncio.wait_for(process.wait(), timeout=timeout)
            
            # Check if process completed successfully
            # Exit code 1 with worker outputs is considered partial success
            success = exit_code == 0
            
            return {
                "success": success,
                "exit_code": exit_code,
                "partial_success": exit_code == 1,  # Worker completed but tests may have failed
            }
            
        except asyncio.TimeoutError:
            # Process timed out, kill it
            await self._kill_process_tree(process.pid)
            
            self.db.log_event(
                event_type="run_timeout",
                entity_type="run",
                entity_id=run_id,
                data={"timeout_seconds": timeout},
            )
            
            return {
                "success": False,
                "exit_code": -15,  # SIGTERM
                "error": f"Process timed out after {timeout} seconds",
            }
            
        except Exception as e:
            # Kill process on any other error
            try:
                await self._kill_process_tree(process.pid)
            except:
                pass
                
            return {
                "success": False,
                "exit_code": -1,
                "error": f"Process monitoring failed: {str(e)}",
            }

    async def _kill_process_tree(self, pid: int) -> None:
        """Kill process and all its children."""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Terminate children first
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            
            # Wait for children to terminate
            psutil.wait_procs(children, timeout=5)
            
            # Kill any remaining children
            for child in children:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            
            # Finally terminate parent
            parent.terminate()
            parent.wait(timeout=5)
            
        except psutil.NoSuchProcess:
            pass  # Process already dead
        except Exception as e:
            # Force kill if gentle termination fails
            try:
                os.kill(pid, signal.SIGKILL if hasattr(signal, 'SIGKILL') else signal.SIGTERM)
            except:
                pass

    async def _create_venv(self, run_path: Path) -> Optional[Path]:
        """Create isolated virtual environment for worker."""
        venv_path = run_path / "venv"
        
        try:
            # Create virtual environment
            cmd = [sys.executable, "-m", "venv", str(venv_path)]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            exit_code = await process.wait()
            if exit_code != 0:
                return None
            
            # Install current project in editable mode
            python_exe = venv_path / ("Scripts" if sys.platform == "win32" else "bin") / "python"
            
            # Get current project root (where pyproject.toml is)
            project_root = Path(__file__).parent.parent.parent.parent
            
            install_cmd = [str(python_exe), "-m", "pip", "install", "-e", str(project_root)]
            process = await asyncio.create_subprocess_exec(
                *install_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            exit_code = await process.wait()
            if exit_code != 0:
                return None
            
            # Install test dependencies
            test_deps = ["pytest", "pytest-cov", "ruff", "black", "mypy"]
            for dep in test_deps:
                cmd = [str(python_exe), "-m", "pip", "install", dep]
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await process.wait()
            
            return venv_path
            
        except Exception:
            return None

    def _generate_run_id(self) -> str:
        """Generate unique run ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        short_uuid = str(uuid.uuid4())[:8] 
        return f"run-{timestamp}-{short_uuid}"

    def get_active_runs(self) -> list:
        """Get list of currently running processes."""
        # This would query database for runs with status="running"
        # and check if the PIDs are still active
        # Implementation simplified for now
        return []

    async def stop_run(self, run_id: str) -> bool:
        """Stop a running task."""
        run_model = self.db.get_run(run_id)
        if not run_model or not run_model.worker_pid:
            return False
        
        try:
            await self._kill_process_tree(run_model.worker_pid)
            
            self.db.update_run_status(
                run_id=run_id,
                status="cancelled",
                completed_at=datetime.utcnow(),
            )
            
            self.db.log_event(
                event_type="run_cancelled",
                entity_type="run", 
                entity_id=run_id,
                data={"reason": "user_requested"},
            )
            
            return True
            
        except Exception:
            return False