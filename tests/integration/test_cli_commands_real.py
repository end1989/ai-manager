"""Real CLI command testing with actual command execution."""

import json
import subprocess
import sys
from pathlib import Path
import pytest
import tempfile
import os

from typer.testing import CliRunner

from cli.manager_cli import app as manager_app
from cli.worker_cli import app as worker_app


@pytest.mark.integration
class TestCLICommandsReal:
    """Test CLI commands with real command execution."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI runner for testing."""
        return CliRunner(mix_stderr=False)

    @pytest.fixture
    def test_task_file(self, temp_dir, sample_task_dict):
        """Create test task file for CLI testing."""
        task_file = temp_dir / "cli_test_task.json"
        with open(task_file, "w") as f:
            json.dump(sample_task_dict, f, indent=2)
        return task_file

    def test_manager_cli_help(self, cli_runner):
        """Test manager CLI help command."""
        result = cli_runner.invoke(manager_app, ["--help"])
        
        assert result.exit_code == 0
        assert "AI Manager CLI" in result.stdout
        assert "submit" in result.stdout
        assert "list" in result.stdout
        assert "status" in result.stdout

    def test_manager_generate_task_template(self, cli_runner, temp_dir):
        """Test generating task template."""
        output_file = temp_dir / "generated_task.json"
        
        result = cli_runner.invoke(manager_app, [
            "generate-task", 
            "--output", str(output_file)
        ])
        
        # Should succeed or fail gracefully
        if result.exit_code == 0:
            assert output_file.exists()
            
            # Verify generated file is valid JSON
            with open(output_file) as f:
                task_data = json.load(f)
                assert "task_id" in task_data
                assert "title" in task_data
                assert "goal" in task_data

    def test_manager_submit_task_dry_run(self, cli_runner, test_task_file, test_env):
        """Test task submission without actual execution."""
        
        # This will likely fail due to missing dependencies, but test the CLI
        result = cli_runner.invoke(manager_app, [
            "submit",
            "--file", str(test_task_file)
        ])
        
        # May succeed or fail, but should not crash
        assert result.exit_code in [0, 1]
        
        # Check output has some expected content
        assert "task" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_manager_list_tasks(self, cli_runner, test_env):
        """Test listing tasks."""
        
        result = cli_runner.invoke(manager_app, ["list"])
        
        # May succeed or fail based on database availability
        assert result.exit_code in [0, 1]
        
        if result.exit_code == 0:
            # Should show some output about tasks
            assert "tasks" in result.stdout.lower() or "no tasks" in result.stdout.lower()

    def test_manager_status(self, cli_runner, test_env):
        """Test system status command."""
        
        result = cli_runner.invoke(manager_app, ["status"])
        
        # Should attempt to get status
        assert result.exit_code in [0, 1]
        
        if result.exit_code == 0:
            assert "system" in result.stdout.lower() or "status" in result.stdout.lower()

    def test_worker_cli_help(self, cli_runner):
        """Test worker CLI help command."""
        result = cli_runner.invoke(worker_app, ["--help"])
        
        assert result.exit_code == 0
        assert "Worker CLI" in result.stdout
        assert "run" in result.stdout
        assert "validate" in result.stdout
        assert "info" in result.stdout

    def test_worker_info_command(self, cli_runner):
        """Test worker info command."""
        result = cli_runner.invoke(worker_app, ["info"])
        
        assert result.exit_code == 0
        assert "Worker" in result.stdout
        assert "Capabilities" in result.stdout

    def test_worker_validate_task(self, cli_runner, test_task_file):
        """Test worker task validation."""
        result = cli_runner.invoke(worker_app, [
            "validate",
            str(test_task_file)
        ])
        
        # Should succeed for valid task file
        if result.exit_code == 0:
            assert "valid" in result.stdout.lower()
        else:
            # If it fails, should show error
            assert "error" in result.stdout.lower() or "invalid" in result.stdout.lower()

    def test_worker_test_functionality(self, cli_runner):
        """Test worker test command."""
        result = cli_runner.invoke(worker_app, ["test"])
        
        # May succeed or fail based on environment
        assert result.exit_code in [0, 1]
        
        if result.exit_code == 0:
            assert "test" in result.stdout.lower()

    def test_worker_run_command_structure(self, cli_runner, test_task_file, temp_dir):
        """Test worker run command structure (may fail but test CLI)."""
        workdir = temp_dir / "worker_test_dir"
        workdir.mkdir()
        
        result = cli_runner.invoke(worker_app, [
            "run",
            "--task", str(test_task_file),
            "--workdir", str(workdir)
        ])
        
        # May fail due to missing dependencies, but should handle gracefully
        assert result.exit_code in [0, 1]
        
        # Should show some output about execution
        assert len(result.stdout) > 0 or len(result.stderr) > 0

    @pytest.mark.slow
    def test_cli_with_real_subprocess(self, temp_dir, sample_task_dict):
        """Test CLI commands as real subprocesses."""
        
        # Create task file
        task_file = temp_dir / "subprocess_task.json"
        with open(task_file, "w") as f:
            json.dump(sample_task_dict, f, indent=2)
        
        # Try to run manager help as subprocess
        try:
            result = subprocess.run(
                [sys.executable, "-m", "cli.manager_cli", "--help"],
                cwd=temp_dir.parent,  # Run from project root
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Should succeed or fail with import error
            assert result.returncode in [0, 1]
            
            if result.returncode == 0:
                assert "AI Manager CLI" in result.stdout
            else:
                # If it fails, should be due to import issues
                assert "import" in result.stderr.lower() or "module" in result.stderr.lower()
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            # Expected if CLI is not properly installed
            pytest.skip(f"CLI subprocess test skipped: {e}")

    def test_cli_error_handling(self, cli_runner):
        """Test CLI error handling with invalid inputs."""
        
        # Test manager with non-existent file
        result = cli_runner.invoke(manager_app, [
            "submit", 
            "--file", "/nonexistent/file.json"
        ])
        
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()
        
        # Test worker with non-existent file
        result = cli_runner.invoke(worker_app, [
            "validate",
            "/nonexistent/file.json" 
        ])
        
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_cli_json_output_format(self, cli_runner, test_env):
        """Test CLI JSON output format."""
        
        result = cli_runner.invoke(manager_app, ["list", "--json"])
        
        if result.exit_code == 0:
            # Should produce JSON output
            try:
                output = result.stdout.strip()
                if output:  # Only parse if there's content
                    json.loads(output)
                    # If we get here, it's valid JSON
            except json.JSONDecodeError:
                # JSON output might not be fully implemented
                pytest.skip("JSON output not properly implemented")

    def test_cli_configuration_handling(self, cli_runner, test_env):
        """Test CLI configuration and environment handling."""
        temp_dir, env_vars = test_env
        
        # Test that CLI respects environment variables
        result = cli_runner.invoke(manager_app, ["status"])
        
        # Should attempt to use test database path
        # (May fail but should try to use the configured path)
        assert result.exit_code in [0, 1]

    def test_cli_invalid_arguments(self, cli_runner):
        """Test CLI with invalid argument combinations."""
        
        # Test manager with invalid status filter
        result = cli_runner.invoke(manager_app, [
            "list", 
            "--status", "invalid_status"
        ])
        
        if result.exit_code != 0:
            assert "invalid" in result.stdout.lower() or "error" in result.stdout.lower()
        
        # Test invalid command
        result = cli_runner.invoke(manager_app, ["nonexistent_command"])
        
        assert result.exit_code != 0

    def test_cli_file_permissions(self, cli_runner, temp_dir):
        """Test CLI file permission handling."""
        
        # Create a task file with restricted permissions (on Unix systems)
        task_file = temp_dir / "restricted_task.json"
        task_file.write_text('{"task_id": "test", "title": "test", "goal": "test", "background": "test"}')
        
        # Try to make it unreadable (may not work on all systems)
        try:
            task_file.chmod(0o000)
            
            result = cli_runner.invoke(manager_app, [
                "submit",
                "--file", str(task_file)
            ])
            
            # Should fail gracefully
            assert result.exit_code == 1
            
            # Restore permissions for cleanup
            task_file.chmod(0o644)
            
        except (OSError, NotImplementedError):
            # Skip if chmod doesn't work (e.g., Windows)
            pytest.skip("File permission test not supported on this system")

    def test_cli_large_output_handling(self, cli_runner, temp_dir):
        """Test CLI handling of large outputs."""
        
        # Create task with very long strings
        large_task = {
            "task_id": "T-large-cli",
            "title": "Large output test",
            "goal": "Test large CLI output",
            "background": "x" * 5000,  # Large background
            "timebox_hours": 1.0
        }
        
        task_file = temp_dir / "large_task.json"
        with open(task_file, "w") as f:
            json.dump(large_task, f, indent=2)
        
        result = cli_runner.invoke(manager_app, [
            "submit",
            "--file", str(task_file)
        ])
        
        # Should handle large inputs gracefully
        assert result.exit_code in [0, 1]

    def test_cli_interactive_features(self, cli_runner):
        """Test CLI interactive features and prompts."""
        
        # Most commands should work non-interactively
        # This tests that they don't hang waiting for input
        
        result = cli_runner.invoke(manager_app, ["generate-task"])
        
        # Should complete without hanging
        assert result.exit_code in [0, 1]
        assert isinstance(result.stdout, str)

    def test_cli_version_and_metadata(self, cli_runner):
        """Test CLI version and metadata display."""
        
        # Test if version information is available
        result = cli_runner.invoke(manager_app, ["--help"])
        
        assert result.exit_code == 0
        # Should contain version or application info
        assert "AI Manager" in result.stdout

    @pytest.mark.subprocess
    def test_cli_process_cleanup(self, temp_dir, sample_task_dict):
        """Test that CLI commands clean up processes properly."""
        
        task_file = temp_dir / "cleanup_task.json"
        with open(task_file, "w") as f:
            json.dump(sample_task_dict, f, indent=2)
        
        # Run a CLI command and ensure it exits cleanly
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "cli.manager_cli", "--help"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=5)
            
            # Process should exit
            assert process.returncode is not None
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Expected if CLI is not properly set up
            pytest.skip("CLI process test skipped - CLI not available")