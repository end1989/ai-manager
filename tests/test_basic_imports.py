"""Test basic imports and functionality of core components.

This test validates that our core system components can be imported
and initialized properly. It serves as a smoke test for the codebase.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

def test_core_schemas_import():
    """Test that core schemas can be imported."""
    try:
        from manager.core.schemas import TaskSpec, WorkerTaskReport, PullRequestProposal
        print("[PASS] Core schemas imported successfully")
        
        # Test basic instantiation
        task = TaskSpec(
            task_id="test-001",
            title="Test Task",
            goal="Test goal",
            background="Test background",
            deliverables=["test deliverable"],
            timebox_hours=1.0
        )
        print(f"[PASS] TaskSpec created: {task.task_id}")
        return True
        
    except Exception as e:
        print(f"[FAIL] Core schemas import failed: {e}")
        return False


def test_database_models_import():
    """Test that database models can be imported."""
    try:
        from manager.store.models import TaskModel, RunModel, ReviewModel, PRModel, DatabaseManager
        print("[PASS] Database models imported successfully")
        return True
        
    except Exception as e:
        print(f"[FAIL] Database models import failed: {e}")
        return False


def test_basic_database_operations():
    """Test basic database operations."""
    try:
        from manager.store.models import DatabaseManager, TaskModel
        from manager.core.schemas import TaskSpec
        from sqlmodel import create_engine, SQLModel
        import tempfile
        import os
        
        print("[PASS] DatabaseManager imported successfully")
        
        # Create a temporary database file for testing
        temp_db_fd, temp_db_path = tempfile.mkstemp(suffix='.db')
        os.close(temp_db_fd)
        
        try:
            # Create engine and tables for testing
            test_engine = create_engine(f"sqlite:///{temp_db_path}")
            SQLModel.metadata.create_all(test_engine)
            
            print("[PASS] Test database tables created")
            
            # Test creating a task using static method
            task_data = {
                "task_id": "test-db-001",
                "title": "Database Test Task", 
                "goal": "Test database operations",
                "background": "Testing",
                "deliverables_json": '["test result"]',
                "timebox_hours": 0.5
            }
            
            # Temporarily set the engine for testing (this is a simplified approach)
            import manager.store.models
            original_engine = manager.store.models.engine
            manager.store.models.engine = test_engine
            
            task_model = DatabaseManager.create_task(task_data)
            print(f"[PASS] Task created in database: {task_model.task_id}")
            
            # Test retrieving the task
            retrieved_task = DatabaseManager.get_task("test-db-001")
            if retrieved_task:
                print(f"[PASS] Task retrieved from database: {retrieved_task.title}")
                success = True
            else:
                print("[FAIL] Could not retrieve task from database")
                success = False
                
            # Restore original engine
            manager.store.models.engine = original_engine
            
            return success
            
        finally:
            # Clean up temporary database file
            try:
                if os.path.exists(temp_db_path):
                    # Close engine connections first
                    test_engine.dispose()
                    os.unlink(temp_db_path)
            except PermissionError:
                # File might still be in use on Windows - ignore for testing
                pass
            
    except Exception as e:
        print(f"[FAIL] Database operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_task_queue_import():
    """Test that task queue can be imported."""
    try:
        from manager.core.queue import TaskQueue
        print("[PASS] TaskQueue imported successfully")
        return True
        
    except Exception as e:
        print(f"[FAIL] TaskQueue import failed: {e}")
        return False


def test_worker_executor_import():
    """Test that worker executor can be imported."""
    try:
        from manager.core.executor import WorkerExecutor
        print("[PASS] WorkerExecutor imported successfully")
        return True
        
    except Exception as e:
        print(f"[FAIL] WorkerExecutor import failed: {e}")
        return False


def test_api_import():
    """Test that API components can be imported."""
    try:
        from manager.api.http import app
        print("[PASS] FastAPI app imported successfully")
        return True
        
    except Exception as e:
        print(f"[FAIL] API import failed: {e}")
        return False


def test_cli_import():
    """Test that CLI components can be imported."""
    try:
        from cli.manager_cli import app as manager_app
        from cli.worker_cli import app as worker_app
        print("[PASS] CLI apps imported successfully") 
        return True
        
    except Exception as e:
        print(f"[FAIL] CLI import failed: {e}")
        return False


def run_all_tests():
    """Run all basic import tests."""
    print("Running basic import tests...")
    print("=" * 50)
    
    tests = [
        test_core_schemas_import,
        test_database_models_import, 
        test_basic_database_operations,
        test_task_queue_import,
        test_worker_executor_import,
        test_api_import,
        test_cli_import,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        print(f"\nRunning {test_func.__name__}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"  {test_func.__name__} FAILED")
        except Exception as e:
            print(f"  {test_func.__name__} ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS: All basic import tests passed!")
        return 0
    else:
        print("FAILURE: Some tests failed - need to fix import issues")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)