"""Simple test runner to validate our AI Manager system.

This is a simplified version of the progressive test execution that focuses
on running actual tests without Unicode encoding issues.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List


def run_pytest_on_file(test_file: Path, project_root: Path) -> Dict:
    """Run pytest on a specific test file."""
    start_time = time.time()
    
    # Set up environment with src path
    env = dict(os.environ)
    src_dir = project_root / "src"
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = str(src_dir)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_file),
            "-v", "--tb=short", "--no-header"
        ], capture_output=True, text=True, timeout=30, env=env)
        
        duration = time.time() - start_time
        
        return {
            "file": str(test_file),
            "passed": result.returncode == 0,
            "duration": duration,
            "output": result.stdout,
            "errors": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        return {
            "file": str(test_file),
            "passed": False,
            "duration": time.time() - start_time,
            "output": "",
            "errors": "Test timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "file": str(test_file),
            "passed": False,
            "duration": time.time() - start_time,
            "output": "",
            "errors": f"Execution error: {e}"
        }


def discover_tests(project_root: Path) -> List[Path]:
    """Discover test files in the project."""
    test_files = []
    
    # Look for test files
    for pattern in ["test_*.py", "*_test.py"]:
        test_files.extend(project_root.glob(f"**/{pattern}"))
    
    # Filter out our AI testing framework files for now
    excluded_files = {
        "test_progressive_execution.py",
        "test_health_monitor.py", 
        "test_result_analyzer.py",
        "test_environment_validator.py"
    }
    
    return [f for f in test_files if f.name not in excluded_files]


def run_smoke_tests(project_root: Path):
    """Run smoke tests - basic functionality tests."""
    print("=" * 60)
    print("RUNNING SMOKE TESTS")
    print("=" * 60)
    
    # Run our basic import test first
    basic_import_test = project_root / "tests" / "test_basic_imports.py"
    
    if basic_import_test.exists():
        print(f"Running basic import test: {basic_import_test.name}")
        result = run_pytest_on_file(basic_import_test, project_root)
        
        if result["passed"]:
            print(f"[PASS] Basic imports ({result['duration']:.2f}s)")
            return True
        else:
            print(f"[FAIL] Basic imports ({result['duration']:.2f}s)")
            print("Error output:")
            print(result["errors"])
            return False
    else:
        print(f"[SKIP] Basic import test not found")
        return True


def run_unit_tests(project_root: Path):
    """Run unit tests - individual component tests."""
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    
    test_files = discover_tests(project_root)
    
    if not test_files:
        print("[INFO] No test files found")
        return True
    
    passed_count = 0
    failed_count = 0
    
    for test_file in test_files:
        print(f"\nRunning: {test_file.name}")
        result = run_pytest_on_file(test_file, project_root)
        
        if result["passed"]:
            print(f"[PASS] {test_file.name} ({result['duration']:.2f}s)")
            passed_count += 1
        else:
            print(f"[FAIL] {test_file.name} ({result['duration']:.2f}s)")
            failed_count += 1
            
            # Show first few lines of error for context
            if result["errors"]:
                error_lines = result["errors"].split('\n')[:5]
                print("  Error summary:")
                for line in error_lines:
                    if line.strip():
                        print(f"    {line}")
    
    print(f"\nUnit Tests Summary: {passed_count} passed, {failed_count} failed")
    return failed_count == 0


def main():
    """Main test execution function."""
    project_root = Path(__file__).parent.parent
    
    print("AI MANAGER SYSTEM VALIDATION")
    print(f"Project root: {project_root}")
    print(f"Python version: {sys.version}")
    print()
    
    start_time = time.time()
    
    # Run smoke tests first
    smoke_passed = run_smoke_tests(project_root)
    
    if not smoke_passed:
        print("\n[CRITICAL] Smoke tests failed - stopping execution")
        return 1
    
    # Run unit tests
    unit_passed = run_unit_tests(project_root)
    
    total_time = time.time() - start_time
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Total execution time: {total_time:.2f}s")
    print(f"Smoke tests: {'PASSED' if smoke_passed else 'FAILED'}")
    print(f"Unit tests: {'PASSED' if unit_passed else 'FAILED'}")
    
    if smoke_passed and unit_passed:
        print("\nSUCCESS: All tests passed!")
        return 0
    else:
        print("\nFAILURE: Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)