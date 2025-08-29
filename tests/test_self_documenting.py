"""Self-Documenting Test Cases with Clear Failure Modes

These tests are designed to be completely self-explanatory and provide
comprehensive information about what they're testing, why they might fail,
and how to fix any issues. Perfect for AI systems to understand and act upon.
"""

import json
import os
import sys
from pathlib import Path
import pytest
import tempfile
from datetime import datetime
from typing import Dict, List, Any

from tests.ai_diagnostics import ai_assert, ai_skip_if_broken


class TestDocumentedImportValidation:
    """
    WHAT THIS TESTS: All critical imports work correctly
    WHY IT MIGHT FAIL: Missing dependencies, wrong Python path, broken code
    HOW TO FIX: Check error messages, run pip install -e .[dev], verify paths
    """

    def test_core_manager_imports(self):
        """
        PURPOSE: Verify all manager core modules can be imported
        
        FAILURE MODES:
        1. ImportError: Module not found -> pip install -e . 
        2. SyntaxError: Code has syntax errors -> fix syntax in source
        3. AttributeError: Missing dependencies -> check requirements
        
        DEPENDENCIES: None (this is the base test)
        PREREQUISITES: Project should be in PYTHONPATH
        """
        
        # Document what we're testing
        modules_to_test = {
            "manager": "Root manager package",
            "manager.config": "Configuration and settings",
            "manager.core.schemas": "Data models and validation",
            "manager.core.queue": "Task queue management", 
            "manager.store.models": "Database models",
            "manager.api.http": "FastAPI web interface",
        }
        
        test_results = {
            "test_purpose": "Validate core manager imports",
            "modules_tested": list(modules_to_test.keys()),
            "import_results": {},
            "environment": {
                "python_version": sys.version,
                "working_dir": str(Path.cwd()),
                "python_path": sys.path[:3]
            }
        }
        
        failed_imports = []
        
        for module_name, description in modules_to_test.items():
            try:
                imported_module = __import__(module_name, fromlist=[''])
                test_results["import_results"][module_name] = {
                    "status": "SUCCESS",
                    "description": description,
                    "module_file": getattr(imported_module, '__file__', 'unknown'),
                    "has_expected_attrs": True  # Could add specific checks
                }
            except ImportError as e:
                test_results["import_results"][module_name] = {
                    "status": "FAILED", 
                    "description": description,
                    "error": str(e),
                    "error_type": "ImportError",
                    "likely_cause": "Module not installed or not in path"
                }
                failed_imports.append(module_name)
            except SyntaxError as e:
                test_results["import_results"][module_name] = {
                    "status": "FAILED",
                    "description": description,
                    "error": str(e),
                    "error_type": "SyntaxError", 
                    "likely_cause": f"Syntax error in {module_name} source code",
                    "file_location": getattr(e, 'filename', 'unknown'),
                    "line_number": getattr(e, 'lineno', 'unknown')
                }
                failed_imports.append(module_name)
        
        # Create detailed failure context for AI
        if failed_imports:
            failure_context = {
                **test_results,
                "failed_modules": failed_imports,
                "next_steps": [
                    "1. Check if you're in the project root directory",
                    "2. Run: pip install -e .[dev]", 
                    "3. Verify virtual environment is activated",
                    "4. Check each failed module individually"
                ],
                "diagnostic_commands": [
                    "python -c \"import sys; print(sys.path)\"",
                    "ls -la src/manager/",
                    "pip list | grep -i manager"
                ]
            }
            
            ai_assert(
                False,
                f"Core manager imports failed for modules: {failed_imports}",
                failure_context
            )
        
        # Success case - document what worked
        print(f"✅ Successfully imported {len(modules_to_test)} core modules")

    def test_optional_dependencies(self):
        """
        PURPOSE: Check optional dependencies that enhance functionality
        
        FAILURE MODES:
        1. Missing optional deps -> pip install package_name
        2. Version conflicts -> pip install --upgrade package_name
        
        NOTE: These failures are non-critical but may limit functionality
        """
        
        optional_deps = {
            "psutil": "System monitoring and process management",
            "rich": "Enhanced CLI output formatting", 
            "aiofiles": "Async file operations",
        }
        
        test_results = {
            "test_purpose": "Validate optional dependencies",
            "optional_deps": optional_deps,
            "results": {},
            "warnings": []
        }
        
        missing_deps = []
        
        for dep_name, description in optional_deps.items():
            try:
                __import__(dep_name)
                test_results["results"][dep_name] = {
                    "status": "AVAILABLE",
                    "description": description
                }
            except ImportError:
                test_results["results"][dep_name] = {
                    "status": "MISSING",
                    "description": description,
                    "install_command": f"pip install {dep_name}"
                }
                missing_deps.append(dep_name)
                test_results["warnings"].append(f"{dep_name} not available - {description}")
        
        if missing_deps:
            pytest.skip(f"Optional dependencies missing: {missing_deps}. Tests will run but with limited functionality.")


class TestDocumentedDatabaseOperations:
    """
    WHAT THIS TESTS: Database setup, connection, and basic operations
    WHY IT MIGHT FAIL: SQLite issues, permission problems, schema errors
    HOW TO FIX: Check database file, run migrations, verify permissions
    """

    def test_database_file_creation(self, temp_dir):
        """
        PURPOSE: Verify database file can be created and initialized
        
        FAILURE MODES:
        1. Permission denied -> Check directory permissions
        2. SQLite not available -> Install SQLite 
        3. Schema creation fails -> Check model definitions
        
        PREREQUISITES: Write access to temp directory
        SIDE EFFECTS: Creates temporary database file
        """
        
        test_context = {
            "test_purpose": "Database file creation and initialization",
            "temp_dir": str(temp_dir),
            "operations": []
        }
        
        # Step 1: Set up database path
        db_path = temp_dir / "documented_test.db"
        test_context["operations"].append({
            "step": "setup_db_path",
            "db_path": str(db_path),
            "path_exists_before": db_path.exists()
        })
        
        # Step 2: Configure environment
        original_db_url = os.environ.get("MANAGER_DB_URL")
        test_db_url = f"sqlite:///{db_path}"
        os.environ["MANAGER_DB_URL"] = test_db_url
        
        test_context["operations"].append({
            "step": "configure_environment", 
            "db_url": test_db_url,
            "original_url": original_db_url
        })
        
        try:
            # Step 3: Import database functions
            try:
                from manager.store.models import create_db_and_tables, DatabaseManager
                test_context["operations"].append({
                    "step": "import_database_modules",
                    "status": "SUCCESS"
                })
            except ImportError as e:
                test_context["operations"].append({
                    "step": "import_database_modules",
                    "status": "FAILED",
                    "error": str(e),
                    "fix_suggestion": "Run: pip install -e ."
                })
                raise
            
            # Step 4: Create database tables
            try:
                create_db_and_tables()
                test_context["operations"].append({
                    "step": "create_tables",
                    "status": "SUCCESS",
                    "db_exists_after": db_path.exists(),
                    "db_size": db_path.stat().st_size if db_path.exists() else 0
                })
            except Exception as e:
                test_context["operations"].append({
                    "step": "create_tables",
                    "status": "FAILED",
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                raise
            
            # Step 5: Test basic database operations
            try:
                db_manager = DatabaseManager()
                
                # Test connection by getting tasks (should be empty)
                tasks = db_manager.list_tasks(limit=1)
                
                test_context["operations"].append({
                    "step": "test_basic_operations",
                    "status": "SUCCESS",
                    "initial_task_count": len(tasks)
                })
                
            except Exception as e:
                test_context["operations"].append({
                    "step": "test_basic_operations", 
                    "status": "FAILED",
                    "error": str(e),
                    "fix_suggestion": "Check database file permissions and SQLite installation"
                })
                raise
            
            # Verify final state
            final_state = {
                "db_file_exists": db_path.exists(),
                "db_file_size": db_path.stat().st_size if db_path.exists() else 0,
                "can_connect": True,
                "operations_completed": len([op for op in test_context["operations"] if op.get("status") == "SUCCESS"])
            }
            test_context["final_state"] = final_state
            
            ai_assert(
                db_path.exists() and db_path.stat().st_size > 0,
                "Database file was not created or is empty",
                test_context
            )
            
        finally:
            # Restore original environment
            if original_db_url:
                os.environ["MANAGER_DB_URL"] = original_db_url
            elif "MANAGER_DB_URL" in os.environ:
                del os.environ["MANAGER_DB_URL"]

    def test_database_schema_validation(self, test_db):
        """
        PURPOSE: Validate database schema matches expected structure
        
        FAILURE MODES:
        1. Missing tables -> Run create_db_and_tables()
        2. Wrong columns -> Check model definitions
        3. Database corruption -> Recreate database
        
        PREREQUISITES: Database file exists and is accessible
        """
        
        test_context = {
            "test_purpose": "Database schema validation",
            "database_file": str(test_db),
            "expected_tables": ["tasks", "runs", "artifacts", "prs", "reviews", "events"],
            "schema_checks": []
        }
        
        try:
            import sqlite3
            
            # Connect to database
            conn = sqlite3.connect(str(test_db))
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            actual_tables = [row[0] for row in cursor.fetchall()]
            
            test_context["schema_checks"].append({
                "check": "table_existence",
                "expected_tables": test_context["expected_tables"],
                "actual_tables": actual_tables,
                "missing_tables": [t for t in test_context["expected_tables"] if t not in actual_tables]
            })
            
            # Check each expected table
            for table_name in test_context["expected_tables"]:
                if table_name in actual_tables:
                    # Get column information
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    test_context["schema_checks"].append({
                        "check": f"{table_name}_columns",
                        "table": table_name,
                        "column_count": len(columns),
                        "columns": [{"name": col[1], "type": col[2]} for col in columns]
                    })
            
            conn.close()
            
            # Validate results
            missing_tables = [t for t in test_context["expected_tables"] if t not in actual_tables]
            
            if missing_tables:
                test_context["error_analysis"] = {
                    "missing_tables": missing_tables,
                    "likely_cause": "Database not properly initialized",
                    "fix_commands": [
                        "python -c \"from manager.store.models import create_db_and_tables; create_db_and_tables()\"",
                        f"sqlite3 {test_db} '.tables'"
                    ]
                }
            
            ai_assert(
                len(missing_tables) == 0,
                f"Database schema invalid: missing tables {missing_tables}",
                test_context
            )
            
        except sqlite3.Error as e:
            test_context["database_error"] = {
                "error": str(e),
                "error_type": "SQLite Error",
                "fix_suggestions": [
                    "Check if database file is corrupted",
                    "Verify SQLite installation",
                    "Recreate database file"
                ]
            }
            raise

    def test_database_crud_operations(self, test_db):
        """
        PURPOSE: Test Create, Read, Update, Delete operations work correctly
        
        FAILURE MODES:
        1. Create fails -> Check constraints and data validation
        2. Read fails -> Check table structure and queries
        3. Update fails -> Check foreign keys and constraints
        4. Delete fails -> Check cascade settings
        
        PREREQUISITES: Valid database with correct schema
        """
        
        test_context = {
            "test_purpose": "Database CRUD operations",
            "operations_log": [],
            "test_data": {
                "task_id": "T-documented-crud-001",
                "title": "CRUD test task",
                "goal": "Test database operations"
            }
        }
        
        try:
            from manager.store.models import DatabaseManager
            from manager.core.schemas import TaskStatus
            
            db = DatabaseManager()
            test_context["operations_log"].append({
                "operation": "initialize_db_manager",
                "status": "SUCCESS"
            })
            
            # CREATE operation
            task_data = {
                "task_id": test_context["test_data"]["task_id"],
                "title": test_context["test_data"]["title"],
                "goal": test_context["test_data"]["goal"], 
                "background": "Testing CRUD operations",
                "inputs_json": "[]",
                "deliverables_json": "[]",
                "acceptance_criteria_json": "[]",
                "definition_of_done_json": "[]",
                "risk_checks_json": "[]",
                "run_instructions_json": "[]",
                "timebox_hours": 1.0,
                "status": TaskStatus.QUEUED.value,
            }
            
            try:
                created_task = db.create_task(task_data)
                test_context["operations_log"].append({
                    "operation": "CREATE",
                    "status": "SUCCESS",
                    "created_id": created_task.id,
                    "created_task_id": created_task.task_id
                })
            except Exception as e:
                test_context["operations_log"].append({
                    "operation": "CREATE",
                    "status": "FAILED",
                    "error": str(e),
                    "data_attempted": task_data
                })
                raise
            
            # READ operation
            try:
                retrieved_task = db.get_task(test_context["test_data"]["task_id"])
                test_context["operations_log"].append({
                    "operation": "READ",
                    "status": "SUCCESS",
                    "found_task": retrieved_task is not None,
                    "task_matches": retrieved_task.task_id == test_context["test_data"]["task_id"] if retrieved_task else False
                })
            except Exception as e:
                test_context["operations_log"].append({
                    "operation": "READ",
                    "status": "FAILED", 
                    "error": str(e)
                })
                raise
            
            # UPDATE operation
            try:
                db.update_task_status(test_context["test_data"]["task_id"], TaskStatus.RUNNING.value)
                updated_task = db.get_task(test_context["test_data"]["task_id"])
                test_context["operations_log"].append({
                    "operation": "UPDATE",
                    "status": "SUCCESS",
                    "new_status": updated_task.status if updated_task else None,
                    "update_successful": updated_task.status == TaskStatus.RUNNING.value if updated_task else False
                })
            except Exception as e:
                test_context["operations_log"].append({
                    "operation": "UPDATE",
                    "status": "FAILED",
                    "error": str(e)
                })
                raise
            
            # Validate all operations succeeded
            failed_operations = [op for op in test_context["operations_log"] if op.get("status") == "FAILED"]
            
            test_context["summary"] = {
                "total_operations": len(test_context["operations_log"]),
                "successful_operations": len([op for op in test_context["operations_log"] if op.get("status") == "SUCCESS"]),
                "failed_operations": len(failed_operations),
                "all_operations_successful": len(failed_operations) == 0
            }
            
            ai_assert(
                len(failed_operations) == 0,
                f"CRUD operations failed: {[op['operation'] for op in failed_operations]}",
                test_context
            )
            
        except Exception as e:
            test_context["unexpected_error"] = {
                "error": str(e),
                "error_type": type(e).__name__,
                "operations_completed": len([op for op in test_context["operations_log"] if op.get("status") == "SUCCESS"])
            }
            raise


class TestDocumentedAPIOperations:
    """
    WHAT THIS TESTS: FastAPI application setup and basic endpoint functionality
    WHY IT MIGHT FAIL: FastAPI not installed, app configuration errors, database issues
    HOW TO FIX: Install dependencies, check app configuration, verify database
    """

    def test_api_application_setup(self):
        """
        PURPOSE: Verify FastAPI application can be imported and configured
        
        FAILURE MODES:
        1. ImportError -> pip install fastapi uvicorn
        2. App creation fails -> Check app configuration in manager.api.http
        3. Wrong app type -> Verify FastAPI import and usage
        
        PREREQUISITES: FastAPI and dependencies installed
        """
        
        test_context = {
            "test_purpose": "FastAPI application setup validation",
            "setup_steps": [],
            "app_properties": {}
        }
        
        # Step 1: Import FastAPI
        try:
            import fastapi
            test_context["setup_steps"].append({
                "step": "import_fastapi",
                "status": "SUCCESS",
                "fastapi_version": getattr(fastapi, '__version__', 'unknown')
            })
        except ImportError as e:
            test_context["setup_steps"].append({
                "step": "import_fastapi",
                "status": "FAILED",
                "error": str(e),
                "fix_command": "pip install fastapi"
            })
            ai_assert(False, "FastAPI not available", test_context)
        
        # Step 2: Import application
        try:
            from manager.api.http import app
            test_context["setup_steps"].append({
                "step": "import_app",
                "status": "SUCCESS"
            })
        except ImportError as e:
            test_context["setup_steps"].append({
                "step": "import_app", 
                "status": "FAILED",
                "error": str(e),
                "fix_suggestion": "Check manager.api.http module exists and is valid"
            })
            ai_assert(False, "Cannot import FastAPI app", test_context)
        
        # Step 3: Validate app properties
        try:
            from fastapi import FastAPI
            
            test_context["app_properties"] = {
                "is_fastapi_instance": isinstance(app, FastAPI),
                "app_title": getattr(app, 'title', 'No title'),
                "app_version": getattr(app, 'version', 'No version'),
                "app_description": getattr(app, 'description', 'No description')[:100],  # Truncate
                "routes_count": len(getattr(app, 'routes', []))
            }
            
            test_context["setup_steps"].append({
                "step": "validate_app_properties",
                "status": "SUCCESS",
                "properties": test_context["app_properties"]
            })
            
        except Exception as e:
            test_context["setup_steps"].append({
                "step": "validate_app_properties",
                "status": "FAILED", 
                "error": str(e)
            })
            raise
        
        # Final validation
        ai_assert(
            isinstance(app, fastapi.FastAPI) and len(getattr(app, 'routes', [])) > 0,
            "FastAPI app not properly configured",
            test_context
        )

    def test_api_endpoint_accessibility(self, api_client):
        """
        PURPOSE: Test that critical API endpoints are accessible and respond correctly
        
        FAILURE MODES:
        1. 404 errors -> Check route configuration
        2. 500 errors -> Check database connection and app dependencies  
        3. Timeout -> Check if app is properly running
        
        PREREQUISITES: FastAPI test client available, database accessible
        """
        
        test_context = {
            "test_purpose": "API endpoint accessibility validation",
            "endpoints_tested": [],
            "test_results": {}
        }
        
        # Define critical endpoints to test
        critical_endpoints = {
            "/": {
                "method": "GET",
                "description": "Root endpoint - basic app info",
                "expected_status": [200],
                "expected_content": ["message"]
            },
            "/health": {
                "method": "GET", 
                "description": "Health check endpoint",
                "expected_status": [200],
                "expected_content": ["status"]
            },
            "/docs": {
                "method": "GET",
                "description": "OpenAPI documentation",
                "expected_status": [200],
                "expected_content": []  # HTML content varies
            }
        }
        
        for endpoint, config in critical_endpoints.items():
            test_context["endpoints_tested"].append(endpoint)
            
            try:
                # Make request
                if config["method"] == "GET":
                    response = api_client.get(endpoint)
                else:
                    raise NotImplementedError(f"Method {config['method']} not implemented in test")
                
                # Analyze response
                response_analysis = {
                    "endpoint": endpoint,
                    "description": config["description"],
                    "status_code": response.status_code,
                    "status_acceptable": response.status_code in config["expected_status"],
                    "response_size": len(response.content),
                    "content_type": response.headers.get("content-type", "unknown")
                }
                
                # Check JSON content if applicable
                if "application/json" in response_analysis["content_type"]:
                    try:
                        json_data = response.json()
                        response_analysis["json_valid"] = True
                        response_analysis["json_keys"] = list(json_data.keys()) if isinstance(json_data, dict) else []
                        
                        # Check expected content
                        missing_content = []
                        for expected_key in config["expected_content"]:
                            if expected_key not in json_data:
                                missing_content.append(expected_key)
                        response_analysis["missing_expected_content"] = missing_content
                        response_analysis["has_expected_content"] = len(missing_content) == 0
                        
                    except json.JSONDecodeError:
                        response_analysis["json_valid"] = False
                        response_analysis["json_error"] = "Invalid JSON response"
                
                test_context["test_results"][endpoint] = response_analysis
                
            except Exception as e:
                test_context["test_results"][endpoint] = {
                    "endpoint": endpoint,
                    "description": config["description"], 
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "status_acceptable": False
                }
        
        # Analyze overall results
        failed_endpoints = []
        for endpoint, result in test_context["test_results"].items():
            if not result.get("status_acceptable", False):
                failed_endpoints.append({
                    "endpoint": endpoint,
                    "issue": result.get("error") or f"Status {result.get('status_code')} not in expected range"
                })
        
        test_context["summary"] = {
            "total_endpoints": len(critical_endpoints),
            "successful_endpoints": len(critical_endpoints) - len(failed_endpoints),
            "failed_endpoints": failed_endpoints,
            "success_rate": (len(critical_endpoints) - len(failed_endpoints)) / len(critical_endpoints)
        }
        
        if failed_endpoints:
            test_context["debugging_suggestions"] = [
                "1. Check if API server is running: uvicorn manager.api.http:app --reload",
                "2. Test endpoints manually: curl http://localhost:8000/health", 
                "3. Check database connection if 500 errors occur",
                "4. Review API logs for detailed error information"
            ]
        
        ai_assert(
            len(failed_endpoints) == 0,
            f"API endpoints failed: {[ep['endpoint'] for ep in failed_endpoints]}",
            test_context
        )


class TestDocumentedSystemIntegration:
    """
    WHAT THIS TESTS: Complete system integration from task submission to completion
    WHY IT MIGHT FAIL: Any component failure, integration issues, timing problems
    HOW TO FIX: Check individual components first, then integration points
    """

    def test_complete_workflow_simulation(self, test_db, temp_dir):
        """
        PURPOSE: Simulate complete task workflow to verify system integration
        
        FAILURE MODES:
        1. Task creation fails -> Check schemas and validation
        2. Database storage fails -> Check database setup
        3. Queue operations fail -> Check queue implementation
        4. Manager coordination fails -> Check manager logic
        
        PREREQUISITES: All components working individually
        INTEGRATION POINTS: Schemas -> Database -> Queue -> Manager
        """
        
        test_context = {
            "test_purpose": "Complete workflow simulation",
            "workflow_steps": [],
            "integration_points": [],
            "test_data": {
                "task_id": "T-integration-simulation-001",
                "task_title": "Integration test simulation",
                "workflow_start": datetime.utcnow().isoformat()
            }
        }
        
        # Step 1: Create task specification
        try:
            from manager.core.schemas import TaskSpec
            
            task_spec = TaskSpec(
                task_id=test_context["test_data"]["task_id"],
                title=test_context["test_data"]["task_title"],
                goal="Simulate complete workflow for integration testing",
                background="Testing system integration points",
                deliverables=["integration test output"],
                timebox_hours=0.1  # Short for testing
            )
            
            test_context["workflow_steps"].append({
                "step": "create_task_spec",
                "status": "SUCCESS",
                "task_id": task_spec.task_id,
                "task_valid": True
            })
            
        except Exception as e:
            test_context["workflow_steps"].append({
                "step": "create_task_spec",
                "status": "FAILED",
                "error": str(e),
                "fix_suggestion": "Check manager.core.schemas module"
            })
            ai_assert(False, "Task specification creation failed", test_context)
        
        # Step 2: Initialize manager components
        try:
            from manager.core.queue import TaskQueue
            from manager.store.models import DatabaseManager
            
            queue = TaskQueue()
            db = DatabaseManager()
            
            test_context["workflow_steps"].append({
                "step": "initialize_components",
                "status": "SUCCESS",
                "components": ["TaskQueue", "DatabaseManager"]
            })
            
            test_context["integration_points"].append({
                "point": "queue_database_integration",
                "queue_type": type(queue).__name__,
                "db_type": type(db).__name__,
                "status": "INITIALIZED"
            })
            
        except Exception as e:
            test_context["workflow_steps"].append({
                "step": "initialize_components",
                "status": "FAILED",
                "error": str(e)
            })
            ai_assert(False, "Component initialization failed", test_context)
        
        # Step 3: Test task enqueue
        try:
            enqueued_id = queue.enqueue(task_spec)
            
            test_context["workflow_steps"].append({
                "step": "enqueue_task",
                "status": "SUCCESS",
                "enqueued_id": enqueued_id,
                "matches_original": enqueued_id == task_spec.task_id
            })
            
            # Verify in database
            stored_task = db.get_task(enqueued_id)
            
            test_context["integration_points"].append({
                "point": "queue_database_persistence",
                "task_in_db": stored_task is not None,
                "task_data_matches": stored_task.task_id == task_spec.task_id if stored_task else False,
                "status": "SUCCESS" if stored_task else "FAILED"
            })
            
        except Exception as e:
            test_context["workflow_steps"].append({
                "step": "enqueue_task",
                "status": "FAILED",
                "error": str(e)
            })
            test_context["integration_points"].append({
                "point": "queue_database_persistence",
                "status": "FAILED",
                "error": str(e)
            })
            ai_assert(False, "Task enqueue failed", test_context)
        
        # Step 4: Test manager system status
        try:
            from manager.core.manager import ManagerCore
            
            manager = ManagerCore()
            system_status = manager.get_system_status()
            
            test_context["workflow_steps"].append({
                "step": "get_system_status",
                "status": "SUCCESS",
                "queue_stats": system_status.get("queue_stats", {}),
                "dispatcher_status": system_status.get("dispatcher_running", False)
            })
            
            test_context["integration_points"].append({
                "point": "manager_queue_integration",
                "can_read_queue": "queue_stats" in system_status,
                "queue_has_tasks": system_status.get("queue_stats", {}).get("total", 0) > 0,
                "status": "SUCCESS"
            })
            
        except Exception as e:
            test_context["workflow_steps"].append({
                "step": "get_system_status",
                "status": "FAILED",
                "error": str(e)
            })
            test_context["integration_points"].append({
                "point": "manager_queue_integration",
                "status": "FAILED",
                "error": str(e)
            })
            ai_assert(False, "Manager system status failed", test_context)
        
        # Final validation
        failed_steps = [step for step in test_context["workflow_steps"] if step.get("status") == "FAILED"]
        failed_integrations = [point for point in test_context["integration_points"] if point.get("status") == "FAILED"]
        
        test_context["final_summary"] = {
            "workflow_completion": datetime.utcnow().isoformat(),
            "total_steps": len(test_context["workflow_steps"]),
            "successful_steps": len([s for s in test_context["workflow_steps"] if s.get("status") == "SUCCESS"]),
            "failed_steps": len(failed_steps),
            "integration_points_tested": len(test_context["integration_points"]),
            "successful_integrations": len([p for p in test_context["integration_points"] if p.get("status") == "SUCCESS"]),
            "failed_integrations": len(failed_integrations)
        }
        
        # Overall success check
        workflow_success = len(failed_steps) == 0 and len(failed_integrations) == 0
        
        if not workflow_success:
            test_context["debugging_guide"] = {
                "failed_workflow_steps": [step["step"] for step in failed_steps],
                "failed_integration_points": [point["point"] for point in failed_integrations],
                "suggested_debugging_order": [
                    "1. Fix failed workflow steps first",
                    "2. Then address integration point failures",
                    "3. Re-run individual component tests",
                    "4. Re-run this integration test"
                ]
            }
        
        ai_assert(
            workflow_success,
            f"Workflow integration failed - Steps: {len(failed_steps)}, Integrations: {len(failed_integrations)}",
            test_context
        )


# Test runner with detailed reporting
def run_documented_tests():
    """
    Run all self-documenting tests with comprehensive reporting.
    This function provides detailed test execution information suitable for AI analysis.
    """
    import subprocess
    import sys
    
    print("🔍 Running Self-Documenting Tests")
    print("=" * 60)
    
    test_classes = [
        "TestDocumentedImportValidation",
        "TestDocumentedDatabaseOperations", 
        "TestDocumentedAPIOperations",
        "TestDocumentedSystemIntegration"
    ]
    
    results = {}
    
    for test_class in test_classes:
        print(f"\n📋 Running {test_class}...")
        
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            f"tests/test_self_documenting.py::{test_class}",
            "-v", "--tb=short", "--no-header"
        ], capture_output=True, text=True)
        
        results[test_class] = {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
        if result.returncode == 0:
            print(f"✅ {test_class} - All tests passed")
        else:
            print(f"❌ {test_class} - Tests failed")
            print("Error details:")
            print(result.stdout)
            if result.stderr:
                print("Stderr:", result.stderr)
    
    # Summary
    passed = sum(1 for r in results.values() if r["success"])
    total = len(results)
    
    print(f"\n📊 Summary: {passed}/{total} test classes passed")
    
    if passed < total:
        print("\n💡 Check test_diagnostics/ directory for detailed failure analysis")
        print("💡 Look for diagnostic_*.json and fix_*.sh files")
    
    return passed == total


if __name__ == "__main__":
    success = run_documented_tests()
    sys.exit(0 if success else 1)