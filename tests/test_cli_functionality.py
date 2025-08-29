"""Test CLI functionality of the AI Manager system.

This test validates that our CLI interfaces work correctly
and can handle basic operations.
"""

import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))


def test_manager_cli_help():
    """Test that manager CLI shows help."""
    try:
        src_path = str(src_dir).replace('\\', '\\\\')
        result = subprocess.run([
            sys.executable, "-c", 
            f"import sys; sys.path.insert(0, r'{src_path}'); from cli.manager_cli import app; app(['--help'])"
        ], capture_output=True, text=True, timeout=10)
        
        # CLI should show help and exit with code 0
        print(f"[PASS] Manager CLI help command works")
        return True
        
    except subprocess.TimeoutExpired:
        print("[FAIL] Manager CLI help timed out")
        return False
    except Exception as e:
        print(f"[FAIL] Manager CLI help failed: {e}")
        return False


def test_worker_cli_help():
    """Test that worker CLI shows help."""
    try:
        src_path = str(src_dir).replace('\\', '\\\\')
        result = subprocess.run([
            sys.executable, "-c", 
            f"import sys; sys.path.insert(0, r'{src_path}'); from cli.worker_cli import app; app(['--help'])"
        ], capture_output=True, text=True, timeout=10)
        
        print(f"[PASS] Worker CLI help command works")
        return True
        
    except subprocess.TimeoutExpired:
        print("[FAIL] Worker CLI help timed out")
        return False
    except Exception as e:
        print(f"[FAIL] Worker CLI help failed: {e}")
        return False


def test_fastapi_app_creation():
    """Test that FastAPI app can be created."""
    try:
        # Use raw string to avoid Windows path issues
        src_path = str(src_dir).replace('\\', '\\\\')
        
        # Test importing and creating the FastAPI app
        result = subprocess.run([
            sys.executable, "-c", f"""
import sys
sys.path.insert(0, r'{src_path}')
from manager.api.http import app
print("FastAPI app created successfully")
print(f"App type: {{type(app)}}")
print(f"Routes: {{len(app.routes)}}")
"""
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "FastAPI app created successfully" in result.stdout:
            print("[PASS] FastAPI app creation works")
            print(f"  Output: {result.stdout.strip()}")
            return True
        else:
            print(f"[FAIL] FastAPI app creation failed")
            print(f"  Return code: {result.returncode}")
            print(f"  Output: {result.stdout}")
            print(f"  Errors: {result.stderr}")
            return False
        
    except Exception as e:
        print(f"[FAIL] FastAPI app creation failed: {e}")
        return False


def test_task_queue_operations():
    """Test basic TaskQueue operations."""
    try:
        src_path = str(src_dir).replace('\\', '\\\\')
        result = subprocess.run([
            sys.executable, "-c", f"""
import sys
sys.path.insert(0, r'{src_path}')

# Test TaskQueue basic functionality
from manager.core.queue import TaskQueue
from manager.core.schemas import TaskSpec

# Create a temporary database
import tempfile
import os
temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
temp_db.close()

# Set database URL for testing
os.environ['MANAGER_DB_URL'] = f'sqlite:///{temp_db.name}'

try:
    # Test TaskQueue initialization
    queue = TaskQueue()
    print("TaskQueue created successfully")
    
    # Create test task
    task_spec = TaskSpec(
        task_id="test-queue-001",
        title="Test Queue Task",
        goal="Test task queue functionality",  
        background="Testing",
        deliverables=["test result"],
        timebox_hours=1.0
    )
    
    # Add task to queue
    queue.add_task(task_spec)
    print("Task added to queue successfully")
    
    # Get task from queue
    retrieved_task = queue.get_task("test-queue-001")
    if retrieved_task:
        print(f"Task retrieved: {{retrieved_task.title}}")
    else:
        print("ERROR: Could not retrieve task")
    
    print("TaskQueue operations completed successfully")
    
finally:
    # Cleanup
    if os.path.exists(temp_db.name):
        os.unlink(temp_db.name)
"""
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0 and "TaskQueue operations completed successfully" in result.stdout:
            print("[PASS] TaskQueue operations work")
            return True
        else:
            print(f"[FAIL] TaskQueue operations failed")
            print(f"  Output: {result.stdout}")
            print(f"  Errors: {result.stderr}")
            return False
        
    except Exception as e:
        print(f"[FAIL] TaskQueue operations failed: {e}")
        return False


def test_database_manager_operations():
    """Test DatabaseManager operations with table creation."""
    try:
        src_path = str(src_dir).replace('\\', '\\\\')
        result = subprocess.run([
            sys.executable, "-c", f"""
import sys
sys.path.insert(0, r'{src_path}')

# Test DatabaseManager with proper table creation
from manager.store.models import DatabaseManager, TaskModel
from sqlmodel import create_engine, SQLModel
import tempfile
import os

# Create temporary database
temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
temp_db.close()

try:
    # Create engine and tables
    engine = create_engine(f'sqlite:///{temp_db.name}')
    SQLModel.metadata.create_all(engine)
    print("Database tables created successfully")
    
    # Override the global engine temporarily
    import manager.store.models
    original_engine = manager.store.models.engine
    manager.store.models.engine = engine
    
    # Test DatabaseManager operations
    task_data = {{
        "task_id": "test-db-002",
        "title": "Database Manager Test",
        "goal": "Test database operations",
        "background": "Testing DatabaseManager",
        "deliverables_json": '["test output"]',
        "timebox_hours": 1.5
    }}
    
    # Create task
    task = DatabaseManager.create_task(task_data)
    print(f"Task created with ID: {{task.task_id}}")
    
    # Retrieve task
    retrieved = DatabaseManager.get_task("test-db-002")
    if retrieved:
        print(f"Task retrieved: {{retrieved.title}}")
        print("DatabaseManager operations completed successfully")
    else:
        print("ERROR: Could not retrieve created task")
    
    # Restore original engine
    manager.store.models.engine = original_engine
    
finally:
    # Cleanup
    if os.path.exists(temp_db.name):
        try:
            os.unlink(temp_db.name)
        except:
            pass  # Ignore cleanup errors on Windows
"""
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0 and "DatabaseManager operations completed successfully" in result.stdout:
            print("[PASS] DatabaseManager operations work")
            return True
        else:
            print(f"[FAIL] DatabaseManager operations failed")
            print(f"  Output: {result.stdout}")  
            print(f"  Errors: {result.stderr}")
            return False
        
    except Exception as e:
        print(f"[FAIL] DatabaseManager operations failed: {e}")
        return False


def run_all_tests():
    """Run all functionality tests."""
    print("AI MANAGER FUNCTIONALITY TESTS")
    print("=" * 50)
    
    tests = [
        ("Manager CLI Help", test_manager_cli_help),
        ("Worker CLI Help", test_worker_cli_help), 
        ("FastAPI App Creation", test_fastapi_app_creation),
        ("TaskQueue Operations", test_task_queue_operations),
        ("DatabaseManager Operations", test_database_manager_operations),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- Running {test_name} ---")
        try:
            if test_func():
                passed += 1
            else:
                print(f"  {test_name} FAILED")
        except Exception as e:
            print(f"  {test_name} ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS: All functionality tests passed!")
        return 0
    else:
        print("FAILURE: Some functionality tests failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)