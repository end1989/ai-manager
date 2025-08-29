"""Quick test of task management API endpoints without long operations."""

import json
import requests
from datetime import datetime, timedelta


def test_api_endpoints_quick():
    """Quick test of all the new API endpoints."""
    
    base_url = "http://localhost:8000"
    
    print("Quick Task Management API Test")
    print("=" * 40)
    
    # Test 1: Templates
    print("\n[1] Templates endpoint...")
    try:
        response = requests.get(f"{base_url}/tasks/templates")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {data['total']} templates")
            for t in data['templates']:
                print(f"  - {t['id']}: {t['name']}")
        else:
            print(f"✗ Error: {response.text}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Create task from template
    print("\n[2] Create from template...")
    created_task_id = None
    
    try:
        payload = {
            "title": "API Test Calculator",
            "goal": "Test the template system", 
            "background": "Testing API functionality",
            "custom_timebox": 1.0
        }
        
        response = requests.post(
            f"{base_url}/tasks/from-template/python-module",
            json=payload
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            task = response.json()
            created_task_id = task['task_id']
            print(f"✓ Created task: {created_task_id}")
        else:
            print(f"✗ Error: {response.text}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Advanced filtering  
    print("\n[3] Advanced task filtering...")
    
    try:
        # Test search
        response = requests.get(f"{base_url}/tasks", params={
            "search": "calculator",
            "limit": 5
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Search found {data['total']} tasks")
        
        # Test sorting
        response = requests.get(f"{base_url}/tasks", params={
            "sort_by": "created_at",
            "sort_order": "desc",
            "limit": 3
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Sorting returned {len(data['tasks'])} tasks")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 4: Clone task
    print("\n[4] Clone task...")
    
    if created_task_id:
        try:
            # Don't provide new_task_id to test auto-generation
            response = requests.post(f"{base_url}/tasks/{created_task_id}/clone")
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                cloned = response.json()
                print(f"✓ Cloned to: {cloned['task_id']}")
            else:
                print(f"✗ Error: {response.text}")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    else:
        print("✗ Skipping - no task created")
    
    # Test 5: System status
    print("\n[5] System status...")
    
    try:
        response = requests.get(f"{base_url}/status")
        
        if response.status_code == 200:
            status = response.json()
            print(f"✓ Dispatcher running: {status['dispatcher_running']}")
            print(f"✓ Total tasks: {status['queue_stats']['total']}")
            print(f"✓ Active runs: {status['active_runs']}")
        else:
            print(f"✗ Error: {response.text}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 6: List all tasks with pagination
    print("\n[6] Task pagination...")
    
    try:
        response = requests.get(f"{base_url}/tasks", params={
            "limit": 10,
            "offset": 0
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Page 1: {len(data['tasks'])}/{data['total']} tasks")
            
            # Show some task info
            for task in data['tasks'][:3]:
                print(f"  - {task['task_id']}: {task['status']}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 7: Get specific task details
    print("\n[7] Task details...")
    
    if created_task_id:
        try:
            response = requests.get(f"{base_url}/tasks/{created_task_id}")
            
            if response.status_code == 200:
                task = response.json()
                print(f"✓ Task title: {task['title']}")
                print(f"✓ Deliverables: {len(task['deliverables'])}")
                print(f"✓ Timebox: {task['timebox_hours']}h")
            else:
                print(f"✗ Error: {response.text}")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print("\n" + "=" * 40)
    print("✓ Quick API endpoint tests completed!")


def main():
    """Main function."""
    print("Testing Task Management API Endpoints...")
    print("Server should be running on http://localhost:8000")
    
    test_api_endpoints_quick()


if __name__ == "__main__":
    main()