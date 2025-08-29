"""Test the new task monitoring dashboard."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from manager.web.dashboard import DashboardManager
from manager.web.websocket import WebSocketManager


async def test_dashboard():
    """Test the dashboard components."""
    
    print("Testing Task Monitoring Dashboard")
    print("=" * 40)
    
    # Test dashboard manager
    print("\n[1] Testing DashboardManager...")
    dashboard = DashboardManager()
    
    try:
        data = dashboard.get_dashboard_data()
        print(f"[OK] Dashboard data retrieved successfully")
        print(f"  - Total tasks: {data.task_stats.total_tasks}")
        print(f"  - Completion rate: {data.task_stats.completion_rate}%")
        print(f"  - System uptime: {data.system_metrics.uptime}")
        print(f"  - Memory usage: {data.system_metrics.memory_usage}%")
        print(f"  - Recent tasks: {len(data.recent_tasks)}")
        print(f"  - Alert count: {data.alert_count}")
        
    except Exception as e:
        print(f"[ERROR] Dashboard data failed: {e}")
        return False
    
    # Test WebSocket manager
    print("\n[2] Testing WebSocketManager...")
    try:
        ws_manager = WebSocketManager()
        print(f"[OK] WebSocket manager initialized")
        print(f"  - Active connections: {ws_manager.get_connection_count()}")
        
        # Test broadcasting (no active connections, so just verify it doesn't crash)
        await ws_manager.broadcast_update({"test": "message"})
        await ws_manager.send_task_update("TEST-001", "running", {"progress": 50})
        await ws_manager.send_system_alert("test", "Test alert", "info")
        print(f"[OK] Broadcasting methods work correctly")
        
    except Exception as e:
        print(f"[ERROR] WebSocket manager failed: {e}")
        return False
    
    # Test performance chart generation
    print("\n[3] Testing performance metrics...")
    try:
        perf_chart = dashboard._get_performance_chart()
        print(f"[OK] Performance chart generated")
        print(f"  - Hours: {len(perf_chart['hours'])}")
        print(f"  - Completed data points: {len(perf_chart['completed'])}")
        print(f"  - Failed data points: {len(perf_chart['failed'])}")
        
    except Exception as e:
        print(f"[ERROR] Performance metrics failed: {e}")
        return False
    
    print(f"\n[4] Testing dashboard HTML availability...")
    dashboard_html = Path(__file__).parent / "src" / "manager" / "web" / "static" / "dashboard.html"
    if dashboard_html.exists():
        size = dashboard_html.stat().st_size
        print(f"[OK] Dashboard HTML found ({size} bytes)")
        
        # Check if it contains key elements
        content = dashboard_html.read_text(encoding="utf-8")
        if "AI Manager Dashboard" in content and "WebSocket" in content:
            print(f"[OK] Dashboard HTML contains required elements")
        else:
            print(f"[WARN] Dashboard HTML missing key elements")
    else:
        print(f"[ERROR] Dashboard HTML not found")
        return False
    
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_dashboard())
        print(f"\n{'='*40}")
        print(f"Dashboard Test: {'PASSED' if result else 'FAILED'}")
        
        if result:
            print(f"\n[SUCCESS] Dashboard is ready! Access at:")
            print(f"   http://localhost:8000/dashboard")
            print(f"   WebSocket: ws://localhost:8000/ws/dashboard")
    except Exception as e:
        print(f"\n{'='*40}")
        print(f"Dashboard Test: FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()