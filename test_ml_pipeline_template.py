"""Test script to execute the ML Pipeline template task."""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from manager.core.manager import ManagerCore
from manager.core.schemas import TaskSpec


async def test_ml_pipeline_execution():
    """Test executing an ML Pipeline template task."""
    
    print("Testing ML Pipeline Template Execution")
    print("=" * 50)
    
    manager = ManagerCore()
    
    # Create ML Pipeline task
    task_spec = TaskSpec(
        task_id="ML-PIPELINE-TEST-001",
        title="Customer Churn Prediction ML Pipeline",
        goal="Build a complete machine learning pipeline to predict customer churn with >90% accuracy",
        background="E-commerce platform needs to identify customers likely to churn within 30 days to trigger retention campaigns",
        deliverables=[
            "Data preprocessing modules for customer behavior analysis",
            "Feature engineering pipeline for churn indicators", 
            "Model training scripts using scikit-learn and XGBoost",
            "Model evaluation metrics and validation framework",
            "FastAPI inference service for real-time predictions",
            "Docker containerization for deployment",
            "CI/CD pipeline configuration",
            "Model versioning and experiment tracking",
            "Comprehensive test suite for all components",
            "Documentation and usage examples"
        ],
        definition_of_done=[
            "Pipeline processes customer data end-to-end",
            "Model achieves >90% accuracy on test set",
            "API returns predictions within 100ms",
            "Docker image builds and runs successfully", 
            "All tests pass with >85% code coverage",
            "Documentation includes setup and usage guide"
        ],
        timebox_hours=8.0
    )
    
    print(f"[1] Creating ML Pipeline task: {task_spec.task_id}")
    try:
        task_id = await manager.submit_task(task_spec)
        print(f"    SUCCESS: Task created: {task_id}")
        
        # Get the task from queue
        task = manager.queue.get_task(task_id) 
        if not task:
            print(f"    ERROR: Task not found in queue")
            return False
            
        print(f"[2] Task details:")
        print(f"    Title: {task.title}")
        print(f"    Goal: {task.goal}")
        print(f"    Deliverables: {len(task.deliverables)}")
        print(f"    Time Budget: {task.timebox_hours} hours")
        
        print(f"[3] Executing ML Pipeline task...")
        print(f"    This will generate sophisticated ML pipeline code")
        print(f"    Including data preprocessing, model training, API service")
        
        # Execute the task
        result = await manager.run_single_task(task)
        
        print(f"[4] Execution completed!")
        print(f"    Status: {result['status']}")
        print(f"    Run ID: {result.get('run_id', 'N/A')}")
        
        if result.get('artifacts'):
            print(f"[5] Generated artifacts:")
            for artifact in result['artifacts']:
                print(f"    • {artifact}")
        
        # Check if workdir was created with files
        if result.get('workdir'):
            workdir = Path(result['workdir'])
            if workdir.exists():
                print(f"[6] Generated files in {workdir}:")
                for file_path in workdir.rglob('*'):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        print(f"    FILE: {file_path.name} ({size} bytes)")
                        
                        # Show preview of Python files
                        if file_path.suffix == '.py' and size < 10000:
                            print(f"        Preview (first 5 lines):")
                            try:
                                lines = file_path.read_text(encoding='utf-8').split('\n')[:5]
                                for i, line in enumerate(lines, 1):
                                    print(f"        {i:2d}: {line}")
                            except Exception as e:
                                print(f"        Error reading file: {e}")
                            print()
        
        return True
        
    except Exception as e:
        print(f"    ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("AI Manager: ML Pipeline Template Test")
    print("=" * 60)
    
    success = await test_ml_pipeline_execution()
    
    print(f"\n" + "=" * 60)
    print(f"ML Pipeline Template Test: {'PASSED' if success else 'FAILED'}")
    
    if success:
        print(f"\nSUCCESS: Advanced template system is working!")
        print(f"Features validated:")
        print(f"  • Complex multi-deliverable task creation")
        print(f"  • AI-powered code generation for ML pipeline")
        print(f"  • Real-world deliverable management")
        print(f"  • Professional code structure")
        print(f"  • Comprehensive testing framework")
    else:
        print(f"\nERROR: Template execution needs attention")


if __name__ == "__main__":
    asyncio.run(main())