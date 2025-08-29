"""Test enhanced task management API endpoints."""

import json
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path


def test_enhanced_task_management():
    """Test all the enhanced task management features."""
    
    base_url = "http://localhost:8000"
    
    print("Enhanced Task Management API Test")
    print("=" * 50)
    
    # Test 1: List task templates
    print("\n[TEST 1] List task templates...")
    try:
        response = requests.get(f"{base_url}/tasks/templates")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            templates = response.json()
            print(f"Available templates: {templates['total']}")
            
            for template in templates['templates']:
                print(f"  - {template['id']}: {template['name']} ({template['timebox_hours']}h)")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Create task from template
    print("\n[TEST 2] Create task from template...")
    created_task_id = None
    
    try:
        template_data = {
            "title": "Build Calculator Library",
            "goal": "Create a comprehensive calculator library for mathematical operations",
            "background": "We need a reusable calculator module for our applications",
            "custom_deliverables": [
                "calculator.py module with Calculator class",
                "test_calculator.py with comprehensive tests", 
                "README.md with usage examples",
                "requirements.txt if needed"
            ],
            "custom_timebox": 1.5
        }
        
        response = requests.post(
            f"{base_url}/tasks/from-template/python-module",
            json=template_data
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            task = response.json()
            created_task_id = task['task_id']
            print(f"Created task: {created_task_id}")
            print(f"Status: {task['status']}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Advanced task filtering
    print("\n[TEST 3] Advanced task filtering...")
    try:
        # Test search
        search_params = {
            "search": "calculator",
            "limit": 10,
            "sort_by": "created_at",
            "sort_order": "desc"
        }
        
        response = requests.get(f"{base_url}/tasks", params=search_params)
        print(f"Search Status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"Found {results['total']} tasks matching 'calculator'")
            
            for task in results['tasks'][:3]:  # Show first 3
                print(f"  - {task['task_id']}: {task['status']}")
        
        # Test date filtering
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        date_params = {
            "created_after": yesterday,
            "status": "queued"
        }
        
        response = requests.get(f"{base_url}/tasks", params=date_params)
        print(f"Date filter Status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"Found {results['total']} queued tasks from last 24h")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Clone a task
    print("\n[TEST 4] Clone task...")
    cloned_task_id = None
    
    if created_task_id:
        try:
            clone_data = {
                "new_task_id": f"{created_task_id}-CLONE"
            }
            
            response = requests.post(
                f"{base_url}/tasks/{created_task_id}/clone",
                json=clone_data
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                cloned_task = response.json()
                cloned_task_id = cloned_task['task_id']
                print(f"Cloned task: {cloned_task_id}")
                print(f"Status: {cloned_task['status']}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Skipping clone test - no task was created")
    
    # Test 5: Run one of the tasks to generate some activity
    print("\n[TEST 5] Run task to generate activity...")
    
    if created_task_id:
        try:
            response = requests.post(f"{base_url}/tasks/{created_task_id}/run")
            print(f"Run Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Task execution initiated")
                print(f"Success: {result.get('success', 'unknown')}")
                if 'run_id' in result:
                    print(f"Run ID: {result['run_id']}")
                
                # Wait a moment for execution to start
                time.sleep(2)
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    # Test 6: Bulk cancel tasks
    print("\n[TEST 6] Bulk cancel tasks...")
    
    task_ids_to_cancel = []
    if created_task_id:
        task_ids_to_cancel.append(created_task_id)
    if cloned_task_id:
        task_ids_to_cancel.append(cloned_task_id)
    
    if task_ids_to_cancel:
        try:
            response = requests.post(
                f"{base_url}/tasks/bulk/cancel",
                json=task_ids_to_cancel
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                results = response.json()
                print(f"Processed: {results['message']}")
                print(f"Successful: {results['successful']}")
                print(f"Failed: {results['failed']}")
                
                for result in results['results']:
                    status = "✓" if result['success'] else "✗"
                    print(f"  {status} {result['task_id']}: {result['message']}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Skipping bulk cancel - no tasks to cancel")
    
    # Test 7: System status with enhanced info
    print("\n[TEST 7] System status...")
    try:
        response = requests.get(f"{base_url}/status")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            status = response.json()
            print("System Status:")
            print(f"  Dispatcher running: {status['dispatcher_running']}")
            print(f"  Active runs: {status['active_runs']}")
            
            queue_stats = status.get('queue_stats', {})
            print("  Queue statistics:")
            for stat_name, count in queue_stats.items():
                print(f"    {stat_name}: {count}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 8: Demonstrate advanced sorting and filtering
    print("\n[TEST 8] Advanced sorting and filtering...")
    
    try:
        # Test different sort options
        sort_tests = [
            {"sort_by": "created_at", "sort_order": "asc", "name": "Oldest first"},
            {"sort_by": "task_id", "sort_order": "desc", "name": "Task ID descending"},
            {"sort_by": "status", "sort_order": "asc", "name": "Status alphabetical"}
        ]
        
        for sort_test in sort_tests:
            response = requests.get(f"{base_url}/tasks", params={
                "limit": 5,
                **sort_test
            })
            
            if response.status_code == 200:
                results = response.json()
                print(f"{sort_test['name']}: {results['total']} total tasks")
                
                if results['tasks']:
                    first_task = results['tasks'][0]
                    print(f"  First: {first_task['task_id']} ({first_task['status']})")
            
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main function."""
    
    print("Testing Enhanced Task Management API...")
    print("Make sure the server is running on http://localhost:8000")
    print()
    
    test_enhanced_task_management()
    
    print("\n" + "=" * 50)
    print("Enhanced Task Management API testing complete!")


if __name__ == "__main__":
    main()