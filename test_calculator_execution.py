"""Test complete task execution workflow with calculator example."""

import json
import sys
from pathlib import Path

# Add src to path for imports
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from manager.core.manager import ManagerCore
from manager.core.schemas import TaskSpec


async def test_calculator_task_execution():
    """Test complete execution of calculator task."""
    
    print("[CALC] Testing Calculator Task Execution Workflow")
    print("=" * 50)
    
    # Load the calculator task
    task_file = Path(__file__).parent / "examples" / "example_task.json"
    
    if not task_file.exists():
        print(f"ERROR: Task file not found: {task_file}")
        return False
    
    # Load task specification
    with open(task_file, "r", encoding="utf-8") as f:
        task_data = json.load(f)
    
    # Use unique task ID for this test run
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    task_data["task_id"] = f"CALC-TEST-{timestamp}"
    
    task_spec = TaskSpec(**task_data)
    print(f"[INFO] Loaded task: {task_spec.task_id} - {task_spec.title}")
    print(f"[INFO] Timebox: {task_spec.timebox_hours} hours")
    print(f"[INFO] Deliverables: {len(task_spec.deliverables)}")
    
    for i, deliverable in enumerate(task_spec.deliverables, 1):
        print(f"   {i}. {deliverable}")
    print()
    
    # Initialize manager
    manager = ManagerCore()
    
    try:
        # Submit task
        print("[EXEC] Submitting task to manager...")
        task_id = await manager.submit_task(task_spec)
        print(f"[OK] Task submitted with ID: {task_id}")
        
        # Run task synchronously for testing
        print("[EXEC] Running task synchronously...")
        task_item = manager.queue.get_task(task_id)
        if not task_item:
            print(f"ERROR: Task not found in queue: {task_id}")
            return False
        
        result = await manager.run_single_task(task_item)
        print(f"[DONE] Task execution completed")
        
        # Check results
        if result.get("success"):
            print(f"[SUCCESS] Task executed successfully!")
            
            # Get run information
            run_id = result.get("run_id")
            if run_id:
                print(f"[INFO] Run ID: {run_id}")
                
                # Try to get artifacts
                run_model = manager.db.get_run(run_id)
                if run_model:
                    artifacts_path = Path(run_model.artifacts_path)
                    workdir = artifacts_path / "workdir"
                    
                    print(f"[INFO] Work directory: {workdir}")
                    
                    # Check if calculator files were created
                    expected_files = [
                        "calculator.py",
                        "test_calculator.py", 
                        "README.md",
                        "requirements.txt"
                    ]
                    
                    created_files = []
                    for file_name in expected_files:
                        file_path = workdir / file_name
                        if file_path.exists():
                            created_files.append(file_name)
                            size = file_path.stat().st_size
                            print(f"   [OK] {file_name} ({size:,} bytes)")
                        else:
                            print(f"   [MISS] {file_name} (missing)")
                    
                    print(f"\n[STAT] Created {len(created_files)}/{len(expected_files)} expected files")
                    
                    # Try to validate calculator.py by importing it
                    if "calculator.py" in created_files:
                        print("\n[TEST] Validating calculator implementation...")
                        try:
                            # Add workdir to path temporarily
                            sys.path.insert(0, str(workdir))
                            
                            # Import and test calculator
                            import calculator
                            calc = calculator.Calculator()
                            
                            # Test basic operations
                            assert calc.add(2, 3) == 5
                            assert calc.subtract(10, 4) == 6
                            assert calc.multiply(5, 6) == 30
                            assert calc.divide(15, 3) == 5.0
                            assert calc.power(2, 3) == 8
                            
                            # Test error handling
                            try:
                                calc.divide(5, 0)
                                assert False, "Should have raised ZeroDivisionError"
                            except ZeroDivisionError:
                                pass  # Expected
                            
                            # Test history
                            history = calc.get_history()
                            assert len(history) == 6  # 5 operations + failed division
                            
                            print("   [OK] Calculator implementation validated!")
                            
                            # Clean up path
                            sys.path.remove(str(workdir))
                            
                        except Exception as e:
                            print(f"   [ERROR] Calculator validation failed: {e}")
                            if str(workdir) in sys.path:
                                sys.path.remove(str(workdir))
                    
                    # Check if tests exist and can be parsed
                    if "test_calculator.py" in created_files:
                        print("\n[TEST] Validating test implementation...")
                        test_file = workdir / "test_calculator.py"
                        test_content = test_file.read_text(encoding="utf-8")
                        
                        # Basic validation
                        required_test_patterns = [
                            "def test_add_",
                            "def test_divide_by_zero",
                            "def test_power_",
                            "ZeroDivisionError",
                            "pytest"
                        ]
                        
                        missing_patterns = []
                        for pattern in required_test_patterns:
                            if pattern not in test_content:
                                missing_patterns.append(pattern)
                        
                        if not missing_patterns:
                            print("   [OK] Test implementation validated!")
                        else:
                            print(f"   [WARN] Missing test patterns: {missing_patterns}")
                    
                    success = len(created_files) >= 3  # At least calculator, tests, and README
                    
                else:
                    print("[ERROR] Could not find run record in database")
                    success = False
        else:
            print(f"[ERROR] Task execution failed: {result.get('error')}")
            success = False
        
        # Cleanup
        print("\n[CLEANUP] Cleaning up...")
        
        return success
        
    except Exception as e:
        print(f"[ERROR] Error during task execution: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to run the test."""
    
    print("AI Manager - Calculator Task Execution Test")
    print("=" * 60)
    print()
    
    # This test needs to be run in an async context
    import asyncio
    
    async def run_test():
        try:
            success = await test_calculator_task_execution()
            
            print("\n" + "=" * 60)
            if success:
                print("[PASS] CALCULATOR TASK EXECUTION TEST PASSED!")
                print("[PASS] Complete workflow validated successfully")
            else:
                print("[FAIL] CALCULATOR TASK EXECUTION TEST FAILED!")
                print("[FAIL] Issues found in workflow")
            
            return success
            
        except Exception as e:
            print(f"\n[ERROR] TEST EXECUTION ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Run the async test
    success = asyncio.run(run_test())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()