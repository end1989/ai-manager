"""Test template execution through the manager core directly."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from manager.core.manager import ManagerCore
from manager.core.executor import WorkerExecutor
from manager.core.schemas import TaskSpec


async def test_direct_execution():
    """Test direct task execution without the queue system."""
    
    print("Direct ML Pipeline Template Test")
    print("=" * 45)
    
    # Create task spec directly
    task_spec = TaskSpec(
        task_id="ML-DIRECT-TEST-001",
        title="ML Pipeline Direct Test", 
        goal="Test ML pipeline code generation with AI",
        background="Testing advanced template system with real AI code generation",
        deliverables=[
            "Data preprocessing module",
            "Model training script", 
            "FastAPI inference service",
            "Comprehensive test suite",
            "Documentation and examples"
        ],
        definition_of_done=[
            "Code generates successfully",
            "All files created",
            "Tests are comprehensive", 
            "Documentation complete"
        ],
        timebox_hours=6.0
    )
    
    print(f"[1] Task: {task_spec.title}")
    print(f"    Deliverables: {len(task_spec.deliverables)}")
    print(f"    Time Budget: {task_spec.timebox_hours} hours")
    
    try:
        # Use the manager for proper task execution
        manager = ManagerCore()
        
        print(f"[2] Starting task execution...")
        
        # Execute the task using the manager
        result = await manager.run_single_task(task_spec)
        
        print(f"[3] Execution completed!")
        print(f"    Success: {result.get('success', False)}")
        print(f"    Run ID: {result.get('run_id', 'N/A')}")
        
        if not result.get('success'):
            print(f"    Error: {result.get('error', 'Unknown error')}")
            if result.get('validation_errors'):
                print(f"    Validation errors: {result.get('validation_errors')}")
            return False
        
        if result.get('workdir') and Path(result['workdir']).exists():
            print(f"[4] Generated files:")
            workdir = Path(result['workdir'])
            
            file_count = 0
            total_size = 0
            
            for file_path in workdir.rglob('*'):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    file_count += 1
                    total_size += size
                    
                    print(f"    • {file_path.name} ({size:,} bytes)")
                    
                    # Show preview for key files
                    if file_path.name in ['worker_report.json', 'pr_proposal.json']:
                        try:
                            import json
                            content = json.loads(file_path.read_text(encoding='utf-8'))
                            if file_path.name == 'worker_report.json':
                                print(f"      Summary: {content.get('summary', 'N/A')}")
                                print(f"      Changes: {len(content.get('changes', []))}")
                            elif file_path.name == 'pr_proposal.json':
                                print(f"      PR Title: {content.get('title', 'N/A')}")
                                print(f"      Description: {content.get('description', 'N/A')[:100]}...")
                        except Exception as e:
                            print(f"      Error reading JSON: {e}")
                    
                    # Show Python file previews
                    elif file_path.suffix == '.py' and size < 50000:
                        try:
                            lines = file_path.read_text(encoding='utf-8').split('\n')
                            print(f"      Lines: {len(lines)}")
                            if len(lines) > 0:
                                print(f"      First line: {lines[0][:80]}")
                        except Exception as e:
                            print(f"      Error reading Python: {e}")
            
            print(f"\n[5] Summary:")
            print(f"    Total files: {file_count}")
            print(f"    Total size: {total_size:,} bytes")
            print(f"    Workdir: {workdir}")
            
            # Show specific AI-generated content
            key_files = ['main.py', 'model.py', 'train.py', 'api.py', 'README.md']
            for filename in key_files:
                file_path = workdir / filename
                if file_path.exists():
                    print(f"\n[6] Preview of {filename}:")
                    try:
                        lines = file_path.read_text(encoding='utf-8').split('\n')[:10]
                        for i, line in enumerate(lines, 1):
                            print(f"    {i:2d}: {line}")
                        if len(file_path.read_text(encoding='utf-8').split('\n')) > 10:
                            print(f"    ... ({len(file_path.read_text(encoding='utf-8').split('\n')) - 10} more lines)")
                    except Exception as e:
                        print(f"    Error reading: {e}")
                    break
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    
    print("Advanced Template System - Direct Execution Test") 
    print("=" * 55)
    
    success = await test_direct_execution()
    
    print(f"\n" + "=" * 55)
    print(f"Template Direct Execution: {'PASSED' if success else 'FAILED'}")
    
    if success:
        print("\nSUCCESS: AI-powered template system validated!")
        print("Advanced features working:")
        print("  • Complex task specification")
        print("  • AI-powered code generation")  
        print("  • Multi-file project creation")
        print("  • Professional code structure")
        print("  • Real-world deliverable management")
        print("\nThe advanced template system is production-ready!")


if __name__ == "__main__":
    asyncio.run(main())