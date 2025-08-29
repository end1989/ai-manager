"""Test the new AI-powered worker prompt system."""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from manager.core.schemas import TaskSpec
from manager.adapters.worker_prompt import WorkerPrompt


async def test_ai_integration():
    """Test the AI integration in WorkerPrompt."""
    
    print("Testing AI-Powered Worker Integration")
    print("=" * 50)
    
    # Create a test task
    test_task = TaskSpec(
        task_id="AI-TEST-001",
        title="AI Calculator Implementation",
        goal="Create a calculator module using AI-powered code generation",
        background="Testing the new LLM integration in the worker system",
        deliverables=["calculator.py", "test_calculator.py", "README.md"],
        timebox_hours=2.0,
        requirements="Use Python best practices and comprehensive error handling"
    )
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        workdir = Path(temp_dir)
        print(f"Working directory: {workdir}")
        
        # Initialize worker with AI capabilities
        worker = WorkerPrompt(workdir)
        print(f"Available LLM providers: {worker.llm_manager.get_available_providers()}")
        
        # Execute task
        print("\nExecuting AI-powered task...")
        worker_report, pr_proposal = await worker.execute_task(test_task)
        
        # Display results
        print(f"\n[OK] Task completed: {worker_report.task_id}")
        print(f"[OK] Files created: {len(worker_report.changes)}")
        print(f"[OK] Tests passed: {worker_report.test_results.passed}")
        print(f"[OK] PR proposal: {pr_proposal.pr_id}")
        
        # Show created files
        print("\nFiles created:")
        for change in worker_report.changes:
            file_path = workdir / change.file
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"  - {change.file} ({size} bytes) - {change.reason}")
            else:
                print(f"  - {change.file} (missing!) - {change.reason}")
        
        # Show AI vs Template implementation status
        print(f"\nImplementation status:")
        print(f"[OK] Worker summary: {worker_report.summary}")
        
        return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_ai_integration())
        print(f"\n{'='*50}")
        print(f"AI Integration Test: {'PASSED' if result else 'FAILED'}")
    except Exception as e:
        print(f"\n{'='*50}")
        print(f"AI Integration Test: FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()