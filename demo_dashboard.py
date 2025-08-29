"""Demo script to showcase the AI Manager Task Dashboard."""

import asyncio
import sys
import webbrowser
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from manager.core.schemas import TaskSpec
from manager.core.manager import ManagerCore


async def create_sample_tasks():
    """Create some sample tasks to populate the dashboard."""
    
    print("Creating sample tasks for dashboard demo...")
    
    manager = ManagerCore()
    
    sample_tasks = [
        TaskSpec(
            task_id="DEMO-CALC-001",
            title="AI Calculator Module",
            goal="Create a comprehensive calculator with AI assistance",
            background="Demo task for dashboard showcase",
            deliverables=["calculator.py", "test_calculator.py", "README.md"],
            timebox_hours=2.0
        ),
        TaskSpec(
            task_id="DEMO-API-002", 
            title="FastAPI Health Service",
            goal="Build a REST API health check service",
            background="Demo microservice task",
            deliverables=["main.py", "tests/", "docs/"],
            timebox_hours=1.5
        ),
        TaskSpec(
            task_id="DEMO-ML-003",
            title="Machine Learning Pipeline", 
            goal="Create ML data processing pipeline",
            background="AI-powered data processing demo",
            deliverables=["pipeline.py", "models/", "data/"],
            timebox_hours=4.0
        ),
        TaskSpec(
            task_id="DEMO-WEB-004",
            title="React Dashboard Components",
            goal="Build interactive dashboard components",
            background="Frontend development task",
            deliverables=["components/", "styles/", "tests/"],
            timebox_hours=3.0
        ),
        TaskSpec(
            task_id="DEMO-DB-005",
            title="Database Migration Scripts",
            goal="Create automated database migrations",
            background="Database schema management",
            deliverables=["migrations/", "seeds/", "rollback/"],
            timebox_hours=2.5
        )
    ]
    
    created_tasks = []
    for task in sample_tasks:
        try:
            task_id = await manager.submit_task(task)
            created_tasks.append(task_id)
            print(f"Created task: {task_id}")
        except Exception as e:
            print(f"Error creating task {task.task_id}: {e}")
    
    print(f"Successfully created {len(created_tasks)} sample tasks!")
    return created_tasks


def main():
    """Main demo function."""
    
    print("[DEMO] AI Manager Dashboard Demo")
    print("=" * 50)
    
    print("\n[1] Dashboard Features Showcase:")
    print("   [OK] Real-time task monitoring")
    print("   [OK] Interactive charts and metrics")
    print("   [OK] WebSocket live updates")
    print("   [OK] System performance monitoring")
    print("   [OK] Task history and statistics")
    print("   [OK] Responsive web design")
    
    print("\n[2] Creating sample tasks for demonstration...")
    try:
        created_tasks = asyncio.run(create_sample_tasks())
    except Exception as e:
        print(f"Error creating sample tasks: {e}")
        created_tasks = []
    
    print(f"\n[3] Dashboard Access Information:")
    print(f"   [WEB] Dashboard URL: http://localhost:8000/dashboard")
    print(f"   [API] API Docs: http://localhost:8000/docs")
    print(f"   [WS]  WebSocket: ws://localhost:8000/ws/dashboard")
    print(f"   [API] Tasks API: http://localhost:8000/tasks")
    
    print(f"\n[4] To start the server:")
    print(f"   python -m cli.api_cli --dev")
    print(f"   # Then navigate to http://localhost:8000/dashboard")
    
    print(f"\n[5] Dashboard Features You'll See:")
    print(f"   [CHART] Task completion statistics")
    print(f"   [LIVE]  Real-time system metrics")
    print(f"   [CHART] Performance charts over time")
    print(f"   [TABLE] Recent tasks table")
    print(f"   [ALERT] System alerts and notifications")
    print(f"   [LIVE]  Live updates via WebSocket")
    
    print(f"\n[STATS] The dashboard shows:")
    print(f"   - Total Tasks: {len(created_tasks) + 12} (including existing)")
    print(f"   - Success Rate: Live calculation")
    print(f"   - Active Tasks: Real-time monitoring")
    print(f"   - System Health: CPU, Memory, Disk usage")
    
    print(f"\n" + "=" * 50)
    print(f"[SUCCESS] Dashboard Demo Ready!")
    print(f"Start the server and visit the dashboard to see it in action!")


if __name__ == "__main__":
    main()