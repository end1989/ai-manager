"""Test worker execution directly without database constraints."""

import json
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from manager.core.schemas import TaskSpec
from manager.adapters.worker_prompt import WorkerPrompt


def test_worker_calculator_execution():
    """Test direct worker execution of calculator task."""
    
    print("[WORKER] Testing Direct Worker Calculator Execution")
    print("=" * 50)
    
    # Load the calculator task
    task_file = Path(__file__).parent / "examples" / "example_task.json"
    
    if not task_file.exists():
        print(f"ERROR: Task file not found: {task_file}")
        return False
    
    # Load task specification
    with open(task_file, "r", encoding="utf-8") as f:
        task_data = json.load(f)
    
    task_spec = TaskSpec(**task_data)
    print(f"[INFO] Loaded task: {task_spec.task_id} - {task_spec.title}")
    print(f"[INFO] Timebox: {task_spec.timebox_hours} hours")
    print(f"[INFO] Deliverables: {len(task_spec.deliverables)}")
    
    for i, deliverable in enumerate(task_spec.deliverables, 1):
        print(f"   {i}. {deliverable}")
    print()
    
    # Create temporary work directory
    with tempfile.TemporaryDirectory() as temp_dir:
        workdir = Path(temp_dir)
        print(f"[INFO] Work directory: {workdir}")
        
        try:
            # Create worker and execute task
            print("[EXEC] Creating worker and executing task...")
            worker = WorkerPrompt(workdir)
            worker_report, pr_proposal = worker.execute_task(task_spec)
            
            print(f"[OK] Task execution completed!")
            print(f"[INFO] Worker report task_id: {worker_report.task_id}")
            print(f"[INFO] PR proposal: {pr_proposal.pr_id}")
            
            # Validate outputs
            print("\n[VALIDATE] Checking generated files...")
            
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
            
            # Test calculator implementation
            if "calculator.py" in created_files:
                print("\n[TEST] Validating calculator implementation...")
                try:
                    # Add workdir to path temporarily
                    sys.path.insert(0, str(workdir))
                    
                    # Import and test calculator
                    import calculator
                    calc = calculator.Calculator()
                    
                    # Test basic operations
                    assert calc.add(2, 3) == 5, "Addition failed"
                    assert calc.subtract(10, 4) == 6, "Subtraction failed"
                    assert calc.multiply(5, 6) == 30, "Multiplication failed"
                    assert calc.divide(15, 3) == 5.0, "Division failed"
                    assert calc.power(2, 3) == 8, "Power failed"
                    
                    # Test error handling
                    try:
                        calc.divide(5, 0)
                        assert False, "Should have raised ZeroDivisionError"
                    except ZeroDivisionError:
                        pass  # Expected
                    
                    # Test history
                    history = calc.get_history()
                    assert len(history) >= 5, f"Expected at least 5 history entries, got {len(history)}"
                    
                    print("   [OK] Calculator implementation validated!")
                    
                    # Clean up path
                    sys.path.remove(str(workdir))
                    
                except Exception as e:
                    print(f"   [ERROR] Calculator validation failed: {e}")
                    if str(workdir) in sys.path:
                        sys.path.remove(str(workdir))
                    return False
            
            # Test worker report content
            print("\n[TEST] Validating worker report...")
            assert worker_report.task_id == task_spec.task_id, "Task ID mismatch"
            assert len(worker_report.changes) > 0, "No changes recorded"
            assert worker_report.summary, "No summary provided"
            
            # Check that all expected deliverables were created
            created_deliverables = [change.file for change in worker_report.changes]
            for expected_file in expected_files:
                if expected_file in created_files:
                    found = any(expected_file in deliverable for deliverable in created_deliverables)
                    if not found:
                        print(f"   [WARN] {expected_file} not recorded in changes")
            
            print("   [OK] Worker report validated!")
            
            # Test PR proposal content  
            print("\n[TEST] Validating PR proposal...")
            assert pr_proposal.pr_id, "No PR ID generated"
            assert pr_proposal.title, "No PR title"
            assert pr_proposal.description, "No PR description"
            assert len(pr_proposal.diff_summary) > 0, "No diff summary"
            
            print("   [OK] PR proposal validated!")
            
            # Test quality checks
            print("\n[TEST] Validating test results...")
            if worker_report.test_results:
                print(f"   [INFO] Tests passed: {worker_report.test_results.passed}")
                print(f"   [INFO] Test summary: {worker_report.test_results.summary[:100]}...")
                if worker_report.test_results.coverage:
                    print(f"   [INFO] Coverage: {worker_report.test_results.coverage}")
            
            success = len(created_files) >= 3 and "calculator.py" in created_files
            
            print(f"\n[RESULT] Overall success: {success}")
            return success
            
        except Exception as e:
            print(f"[ERROR] Task execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main function to run the test."""
    
    print("AI Manager - Direct Worker Calculator Test")
    print("=" * 50)
    print()
    
    success = test_worker_calculator_execution()
    
    print("\n" + "=" * 50)
    if success:
        print("[PASS] DIRECT WORKER TEST PASSED!")
        print("[PASS] Calculator implementation working correctly")
    else:
        print("[FAIL] DIRECT WORKER TEST FAILED!")
        print("[FAIL] Issues found in worker execution")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()