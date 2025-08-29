"""AI-Friendly Iterative Debugging Test Suite

This suite is designed for AI systems to:
1. Run tests and get detailed diagnostic information
2. Understand exactly what's broken and why
3. Get specific suggestions for fixes
4. Verify fixes work before moving to next issue

Each test includes comprehensive diagnostics and self-healing suggestions.
"""

import json
import sys
import tempfile
from pathlib import Path
import pytest

from tests.ai_diagnostics import ai_assert, ai_skip_if_broken, ai_diagnostics


class TestEnvironmentValidation:
    """Tests that validate the environment is set up correctly for development."""

    def test_python_environment(self):
        """Validate Python environment is correct for this project."""
        context = {
            "python_version": sys.version,
            "python_executable": sys.executable,
            "working_directory": str(Path.cwd()),
        }
        
        # Check Python version
        version_info = sys.version_info
        ai_assert(
            version_info.major == 3 and version_info.minor >= 11,
            f"Python 3.11+ required, got {version_info.major}.{version_info.minor}",
            context
        )
        
        # Check if we're in a virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        context["in_virtual_env"] = in_venv
        context["python_prefix"] = sys.prefix
        
        if not in_venv:
            pytest.skip("Not in virtual environment - recommended but not required for testing")

    def test_project_structure(self):
        """Validate project structure is correct."""
        required_files = [
            "pyproject.toml",
            "src/manager/__init__.py", 
            "src/manager/core/schemas.py",
            "src/manager/store/models.py",
            "tests/conftest.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        context = {
            "required_files": required_files,
            "missing_files": missing_files,
            "current_directory": str(Path.cwd()),
            "directory_contents": [str(p) for p in Path.cwd().iterdir()]
        }
        
        ai_assert(
            len(missing_files) == 0,
            f"Missing required project files: {missing_files}",
            context
        )

    def test_core_imports_basic(self):
        """Test basic imports work - this will identify import issues immediately."""
        import_tests = [
            ("manager", "Manager package root"),
            ("manager.config", "Configuration module"),
            ("manager.core.schemas", "Core schemas"),
            ("manager.store.models", "Database models")
        ]
        
        successful_imports = []
        failed_imports = []
        
        for module_name, description in import_tests:
            try:
                __import__(module_name)
                successful_imports.append(module_name)
            except ImportError as e:
                failed_imports.append({
                    "module": module_name,
                    "description": description,
                    "error": str(e)
                })
        
        context = {
            "successful_imports": successful_imports,
            "failed_imports": failed_imports,
            "python_path": sys.path[:5]  # First 5 entries
        }
        
        if failed_imports:
            # Create specific diagnostic for import failures
            for failed in failed_imports:
                diagnosis = ai_diagnostics.diagnose_import_error(failed["module"], ImportError(failed["error"]))
                ai_diagnostics.save_diagnostic_report({
                    **diagnosis,
                    "test_context": "core_imports_basic",
                    "module_description": failed["description"]
                })
        
        ai_assert(
            len(failed_imports) == 0,
            f"Core imports failed: {[f['module'] for f in failed_imports]}",
            context
        )


class TestDatabaseSetup:
    """Tests that validate database setup and operations."""

    def test_database_imports(self):
        """Test database-related imports work."""
        try:
            from manager.store.models import DatabaseManager, create_db_and_tables
            from manager.store.models import TaskModel, RunModel
            context = {"database_imports": "successful"}
        except ImportError as e:
            context = {
                "import_error": str(e),
                "attempted_imports": [
                    "manager.store.models.DatabaseManager",
                    "manager.store.models.create_db_and_tables", 
                    "manager.store.models.TaskModel"
                ]
            }
            ai_assert(False, f"Database imports failed: {e}", context)

    def test_database_creation(self, temp_dir):
        """Test database can be created successfully."""
        ai_skip_if_broken(
            not temp_dir.exists(),
            "Temp directory not available for database testing"
        )
        
        # Set up test database path
        test_db = temp_dir / "test_creation.db"
        
        context = {
            "database_path": str(test_db),
            "temp_dir": str(temp_dir),
            "db_exists_before": test_db.exists()
        }
        
        try:
            import os
            original_db_url = os.environ.get("MANAGER_DB_URL")
            os.environ["MANAGER_DB_URL"] = f"sqlite:///{test_db}"
            
            from manager.store.models import create_db_and_tables
            create_db_and_tables()
            
            context.update({
                "db_exists_after": test_db.exists(),
                "db_size": test_db.stat().st_size if test_db.exists() else 0,
                "creation_successful": True
            })
            
            # Restore original environment
            if original_db_url:
                os.environ["MANAGER_DB_URL"] = original_db_url
            elif "MANAGER_DB_URL" in os.environ:
                del os.environ["MANAGER_DB_URL"]
            
        except Exception as e:
            context.update({
                "creation_error": str(e),
                "creation_successful": False
            })
            # Generate database-specific diagnostic
            diagnosis = ai_diagnostics.diagnose_database_error(e, context)
            ai_diagnostics.save_diagnostic_report(diagnosis)
            raise
        
        ai_assert(
            test_db.exists() and test_db.stat().st_size > 0,
            "Database file was not created or is empty",
            context
        )

    def test_database_basic_operations(self, test_db):
        """Test basic database operations work."""
        context = {
            "database_file": str(test_db),
            "operations_attempted": []
        }
        
        try:
            from manager.store.models import DatabaseManager
            from manager.core.schemas import TaskStatus
            
            db = DatabaseManager()
            context["operations_attempted"].append("DatabaseManager creation")
            
            # Test task creation
            task_data = {
                "task_id": "T-db-test-001",
                "title": "Database test task",
                "goal": "Test database operations",
                "background": "Testing",
                "inputs_json": "[]",
                "deliverables_json": "[]",
                "acceptance_criteria_json": "[]",
                "definition_of_done_json": "[]", 
                "risk_checks_json": "[]",
                "run_instructions_json": "[]",
                "timebox_hours": 1.0,
                "status": TaskStatus.QUEUED.value,
            }
            
            task = db.create_task(task_data)
            context["operations_attempted"].append("Task creation")
            context["created_task_id"] = task.task_id
            
            # Test task retrieval
            retrieved_task = db.get_task("T-db-test-001")
            context["operations_attempted"].append("Task retrieval")
            context["retrieved_task_exists"] = retrieved_task is not None
            
            ai_assert(
                retrieved_task is not None and retrieved_task.task_id == "T-db-test-001",
                "Task creation and retrieval failed",
                context
            )
            
        except Exception as e:
            context["database_error"] = str(e)
            diagnosis = ai_diagnostics.diagnose_database_error(e, context)
            ai_diagnostics.save_diagnostic_report(diagnosis)
            raise


class TestAPISetup:
    """Tests that validate API setup and basic functionality."""

    def test_api_imports(self):
        """Test API-related imports work."""
        import_attempts = [
            "manager.api.http",
            "fastapi", 
            "uvicorn"
        ]
        
        successful_imports = []
        failed_imports = []
        
        for module in import_attempts:
            try:
                __import__(module)
                successful_imports.append(module)
            except ImportError as e:
                failed_imports.append({"module": module, "error": str(e)})
        
        context = {
            "successful_imports": successful_imports,
            "failed_imports": failed_imports
        }
        
        if failed_imports:
            for failed in failed_imports:
                diagnosis = ai_diagnostics.diagnose_import_error(failed["module"], ImportError(failed["error"]))
                ai_diagnostics.save_diagnostic_report({
                    **diagnosis,
                    "test_context": "api_imports"
                })
        
        ai_assert(
            len(failed_imports) == 0,
            f"API imports failed: {[f['module'] for f in failed_imports]}",
            context
        )

    def test_api_app_creation(self):
        """Test FastAPI app can be created."""
        context = {"app_creation_steps": []}
        
        try:
            from manager.api.http import app
            context["app_creation_steps"].append("Import successful")
            
            # Check app is FastAPI instance
            from fastapi import FastAPI
            context["app_creation_steps"].append("FastAPI import successful")
            
            ai_assert(
                isinstance(app, FastAPI),
                f"App is not FastAPI instance, got {type(app)}",
                context
            )
            
            context["app_creation_steps"].append("App validation successful")
            context["app_title"] = getattr(app, 'title', 'No title')
            
        except Exception as e:
            context["creation_error"] = str(e)
            diagnosis = ai_diagnostics.diagnose_import_error("manager.api.http", e)
            ai_diagnostics.save_diagnostic_report({
                **diagnosis,
                "test_context": "api_app_creation",
                "creation_steps": context["app_creation_steps"]
            })
            raise

    def test_api_basic_endpoints(self, api_client):
        """Test basic API endpoints are accessible."""
        endpoint_tests = [
            ("/", "Root endpoint"),
            ("/health", "Health check endpoint"),
            ("/docs", "API documentation"),
        ]
        
        results = []
        
        for endpoint, description in endpoint_tests:
            try:
                response = api_client.get(endpoint)
                results.append({
                    "endpoint": endpoint,
                    "description": description,
                    "status_code": response.status_code,
                    "success": response.status_code < 400,
                    "response_size": len(response.content)
                })
            except Exception as e:
                results.append({
                    "endpoint": endpoint,
                    "description": description,
                    "error": str(e),
                    "success": False
                })
        
        failed_endpoints = [r for r in results if not r.get("success")]
        context = {
            "endpoint_results": results,
            "failed_endpoints": failed_endpoints
        }
        
        if failed_endpoints:
            for failed in failed_endpoints:
                if "status_code" in failed:
                    diagnosis = ai_diagnostics.diagnose_api_error(
                        failed["status_code"], 
                        failed.get("response_text", ""), 
                        failed["endpoint"]
                    )
                    ai_diagnostics.save_diagnostic_report(diagnosis)
        
        ai_assert(
            len(failed_endpoints) == 0,
            f"API endpoints failed: {[f['endpoint'] for f in failed_endpoints]}",
            context
        )


class TestCLISetup:
    """Tests that validate CLI setup and functionality."""

    def test_cli_imports(self):
        """Test CLI-related imports work."""
        cli_modules = [
            ("cli.manager_cli", "Manager CLI"),
            ("cli.worker_cli", "Worker CLI"),
            ("typer", "CLI framework"),
        ]
        
        successful_imports = []
        failed_imports = []
        
        for module_name, description in cli_modules:
            try:
                __import__(module_name)
                successful_imports.append({"module": module_name, "description": description})
            except ImportError as e:
                failed_imports.append({
                    "module": module_name,
                    "description": description, 
                    "error": str(e)
                })
        
        context = {
            "successful_imports": successful_imports,
            "failed_imports": failed_imports
        }
        
        if failed_imports:
            for failed in failed_imports:
                diagnosis = ai_diagnostics.diagnose_import_error(failed["module"], ImportError(failed["error"]))
                ai_diagnostics.save_diagnostic_report({
                    **diagnosis,
                    "test_context": "cli_imports",
                    "module_description": failed["description"]
                })
        
        ai_assert(
            len(failed_imports) == 0,
            f"CLI imports failed: {[f['module'] for f in failed_imports]}",
            context
        )

    def test_cli_app_creation(self):
        """Test CLI apps can be created."""
        context = {"cli_tests": []}
        
        try:
            from cli.manager_cli import app as manager_app
            context["cli_tests"].append("Manager CLI import successful")
            
            from cli.worker_cli import app as worker_app  
            context["cli_tests"].append("Worker CLI import successful")
            
            # Test apps are Typer apps
            from typer import Typer
            ai_assert(
                isinstance(manager_app, Typer) and isinstance(worker_app, Typer),
                f"CLI apps are not Typer instances: manager={type(manager_app)}, worker={type(worker_app)}",
                context
            )
            
            context["cli_tests"].append("CLI app validation successful")
            
        except Exception as e:
            context["cli_error"] = str(e)
            diagnosis = ai_diagnostics.diagnose_import_error("cli", e)
            ai_diagnostics.save_diagnostic_report({
                **diagnosis,
                "test_context": "cli_app_creation",
                "cli_tests": context["cli_tests"]
            })
            raise


class TestProgressiveIntegration:
    """Progressive integration tests that build on each other."""

    def test_01_basic_task_creation(self, test_db):
        """Step 1: Test basic task creation works."""
        context = {"step": "01_basic_task_creation"}
        
        try:
            from manager.core.schemas import TaskSpec
            
            task_spec = TaskSpec(
                task_id="T-progressive-001",
                title="Progressive test task",
                goal="Test progressive integration",
                background="Testing step by step",
                timebox_hours=1.0
            )
            
            context.update({
                "task_created": True,
                "task_id": task_spec.task_id,
                "task_validation": "passed"
            })
            
            # Validate task spec
            ai_assert(
                task_spec.task_id == "T-progressive-001",
                "Task creation failed",
                context
            )
            
        except Exception as e:
            context["task_creation_error"] = str(e)
            raise

    def test_02_database_task_storage(self, test_db):
        """Step 2: Test task can be stored in database."""
        context = {"step": "02_database_task_storage"}
        
        try:
            from manager.core.schemas import TaskSpec, TaskStatus
            from manager.store.models import DatabaseManager
            
            # Create task spec
            task_spec = TaskSpec(
                task_id="T-progressive-002",
                title="Database storage test",
                goal="Test database storage",
                background="Testing database",
                timebox_hours=1.0
            )
            
            # Store in database
            db = DatabaseManager()
            task_data = {
                "task_id": task_spec.task_id,
                "title": task_spec.title,
                "goal": task_spec.goal,
                "background": task_spec.background,
                "inputs_json": "[]",
                "deliverables_json": "[]",
                "acceptance_criteria_json": "[]",
                "definition_of_done_json": "[]",
                "risk_checks_json": "[]",
                "run_instructions_json": "[]",
                "timebox_hours": task_spec.timebox_hours,
                "status": TaskStatus.QUEUED.value,
            }
            
            stored_task = db.create_task(task_data)
            retrieved_task = db.get_task(task_spec.task_id)
            
            context.update({
                "database_storage": "successful",
                "stored_task_id": stored_task.task_id,
                "retrieved_successfully": retrieved_task is not None
            })
            
            ai_assert(
                retrieved_task is not None and retrieved_task.task_id == task_spec.task_id,
                "Database task storage failed",
                context
            )
            
        except Exception as e:
            context["database_storage_error"] = str(e)
            diagnosis = ai_diagnostics.diagnose_database_error(e, context)
            ai_diagnostics.save_diagnostic_report(diagnosis)
            raise

    def test_03_queue_operations(self, test_db):
        """Step 3: Test task queue operations."""
        context = {"step": "03_queue_operations"}
        
        try:
            from manager.core.queue import TaskQueue
            from manager.core.schemas import TaskSpec
            
            queue = TaskQueue()
            
            task_spec = TaskSpec(
                task_id="T-progressive-003",
                title="Queue test task", 
                goal="Test queue operations",
                background="Testing queue",
                timebox_hours=1.0
            )
            
            # Test enqueue
            enqueued_id = queue.enqueue(task_spec)
            context["enqueue_successful"] = enqueued_id == task_spec.task_id
            
            # Test dequeue
            dequeued_task = queue.dequeue()
            context["dequeue_successful"] = dequeued_task is not None
            context["dequeued_task_id"] = dequeued_task.task_id if dequeued_task else None
            
            ai_assert(
                dequeued_task is not None and dequeued_task.task_id == task_spec.task_id,
                "Queue operations failed",
                context
            )
            
        except Exception as e:
            context["queue_error"] = str(e)
            raise

    @pytest.mark.slow
    def test_04_end_to_end_basic(self, test_db):
        """Step 4: Basic end-to-end test."""
        context = {"step": "04_end_to_end_basic"}
        
        try:
            from manager.core.manager import ManagerCore
            from manager.core.schemas import TaskSpec
            
            # Create manager
            manager = ManagerCore()
            context["manager_created"] = True
            
            # Create simple task
            task_spec = TaskSpec(
                task_id="T-progressive-004",
                title="End-to-end test",
                goal="Test complete workflow",
                background="Testing end-to-end",
                deliverables=["simple test output"],
                timebox_hours=0.1  # Very short for testing
            )
            
            # Submit task
            task_id = await manager.submit_task(task_spec)
            context["task_submitted"] = task_id == task_spec.task_id
            
            # Get system status
            status = manager.get_system_status()
            context["system_status"] = status.get("queue_stats", {})
            
            ai_assert(
                task_id == task_spec.task_id and status.get("queue_stats", {}).get("total", 0) > 0,
                "End-to-end basic test failed",
                context
            )
            
        except Exception as e:
            context["end_to_end_error"] = str(e)
            raise


# Utility function to run tests progressively
def run_progressive_tests():
    """Run tests in order, stopping at first failure for analysis."""
    import subprocess
    import sys
    
    test_order = [
        "TestEnvironmentValidation",
        "TestDatabaseSetup", 
        "TestAPISetup",
        "TestCLISetup",
        "TestProgressiveIntegration::test_01_basic_task_creation",
        "TestProgressiveIntegration::test_02_database_task_storage",
        "TestProgressiveIntegration::test_03_queue_operations",
    ]
    
    for test_class in test_order:
        print(f"\n🔍 Running: {test_class}")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            f"tests/test_ai_iterative_debugging.py::{test_class}",
            "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Failed at: {test_class}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            print(f"\n💡 Check test_diagnostics/ for detailed analysis")
            return False
        else:
            print(f"✅ Passed: {test_class}")
    
    print("\n🎉 All progressive tests passed!")
    return True


if __name__ == "__main__":
    # Run progressive tests when script is executed directly
    run_progressive_tests()