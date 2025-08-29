"""Test subprocess worker execution to verify it works end-to-end."""

import asyncio
import json
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from manager.core.schemas import TaskSpec
from manager.core.executor import WorkerExecutor


async def test_subprocess_execution():
    """Test complete subprocess execution workflow."""
    
    print("[SUBPROCESS] Testing Subprocess Worker Execution")
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
    task_data["task_id"] = f"SUBPROCESS-TEST-{timestamp}"
    
    task_spec = TaskSpec(**task_data)
    print(f"[INFO] Task: {task_spec.task_id} - {task_spec.title}")
    print(f"[INFO] Deliverables: {len(task_spec.deliverables)}")
    
    # Create executor and run task
    executor = WorkerExecutor()
    
    try:
        print("\n[EXEC] Starting subprocess execution...")
        
        run_id, execution_result = await executor.execute_task(task_spec)
        
        print(f"[INFO] Run ID: {run_id}")
        print(f"[INFO] Success: {execution_result.get('success')}")
        
        if not execution_result.get("success"):
            print(f"[ERROR] Execution failed: {execution_result.get('error')}")
            
            # Check logs for debugging
            stdout_path = execution_result.get("stdout_path")
            stderr_path = execution_result.get("stderr_path")
            
            if stdout_path and Path(stdout_path).exists():
                print(f"\n[DEBUG] STDOUT ({stdout_path}):")
                try:
                    with open(stdout_path, "r", encoding="utf-8", errors="replace") as f:
                        stdout_content = f.read()
                        print(stdout_content[:1000] + ("..." if len(stdout_content) > 1000 else ""))
                except Exception as e:
                    print(f"[ERROR] Could not read stdout: {e}")
            
            if stderr_path and Path(stderr_path).exists():
                print(f"\n[DEBUG] STDERR ({stderr_path}):")
                try:
                    with open(stderr_path, "r", encoding="utf-8", errors="replace") as f:
                        stderr_content = f.read()
                        print(stderr_content[:1000] + ("..." if len(stderr_content) > 1000 else ""))
                except Exception as e:
                    print(f"[ERROR] Could not read stderr: {e}")
            
            return False
        
        print(f"[OK] Subprocess execution completed successfully!")
        
        # Check if expected outputs were created
        run_model = executor.db.get_run(run_id)
        if run_model:
            artifacts_path = Path(run_model.artifacts_path)
            workdir = artifacts_path / "workdir"
            
            print(f"[INFO] Checking outputs in: {workdir}")
            
            # Check for expected output files from worker_cli
            expected_outputs = [
                "worker_report.json",
                "pr_proposal.json"
            ]
            
            outputs_found = []
            for output_file in expected_outputs:
                output_path = workdir / output_file
                if output_path.exists():
                    outputs_found.append(output_file)
                    size = output_path.stat().st_size
                    print(f"   [OK] {output_file} ({size} bytes)")
                    
                    # Show content preview
                    try:
                        with open(output_path, "r", encoding="utf-8") as f:
                            content = json.load(f)
                            if output_file == "worker_report.json":
                                print(f"      Task ID: {content.get('task_id')}")
                                print(f"      Changes: {len(content.get('changes', []))}")
                            elif output_file == "pr_proposal.json":
                                print(f"      PR ID: {content.get('pr_id')}")
                                print(f"      Title: {content.get('title', 'N/A')}")
                    except Exception as e:
                        print(f"      [WARN] Could not parse JSON: {e}")
                else:
                    print(f"   [MISS] {output_file}")
            
            # Also check for generated code files
            code_files = ["calculator.py", "README.md", "requirements.txt", "test_calculator.py"]
            code_found = []
            
            print(f"\n[INFO] Checking generated code files:")
            for code_file in code_files:
                code_path = workdir / code_file
                if code_path.exists():
                    code_found.append(code_file)
                    size = code_path.stat().st_size
                    print(f"   [OK] {code_file} ({size} bytes)")
                else:
                    print(f"   [MISS] {code_file}")
            
            success = len(outputs_found) >= 1 and len(code_found) >= 2
            print(f"\n[RESULT] Subprocess success: {success}")
            print(f"[RESULT] Output files: {len(outputs_found)}/{len(expected_outputs)}")
            print(f"[RESULT] Code files: {len(code_found)}/{len(code_files)}")
            
            return success
        else:
            print("[ERROR] Could not find run record in database")
            return False
    
    except Exception as e:
        print(f"[ERROR] Subprocess execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main async function."""
    
    print("AI Manager - Subprocess Execution Test")
    print("=" * 50)
    print()
    
    success = await test_subprocess_execution()
    
    print("\n" + "=" * 50)
    if success:
        print("[PASS] SUBPROCESS EXECUTION TEST PASSED!")
        print("[PASS] Worker subprocess execution working correctly")
    else:
        print("[FAIL] SUBPROCESS EXECUTION TEST FAILED!")
        print("[FAIL] Issues found in subprocess execution")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)