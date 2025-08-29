"""Test API client to demonstrate proper task submission."""

import json
import requests
import time
from pathlib import Path


def test_api_endpoints():
    """Test various API endpoints."""
    
    base_url = "http://localhost:8000"
    
    print("AI Manager API Test Client")
    print("=" * 40)
    
    # Test health endpoint
    print("\n[TEST] Health check...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
        return
    
    # Test root endpoint
    print("\n[TEST] Root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test task submission with calculator task
    print("\n[TEST] Task submission...")
    
    # Load the calculator task
    task_file = Path(__file__).parent / "examples" / "example_task.json"
    
    if not task_file.exists():
        print(f"ERROR: Task file not found: {task_file}")
        return
    
    # Load and prepare task
    with open(task_file, "r", encoding="utf-8") as f:
        task_spec = json.load(f)
    
    # Use unique task ID to avoid conflicts
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    task_spec["task_id"] = f"API-TEST-{timestamp}"
    
    # Create proper submission format
    task_submission = {
        "spec": task_spec
    }
    
    print(f"Submitting task: {task_spec['task_id']}")
    print(f"Title: {task_spec['title']}")
    
    try:
        response = requests.post(
            f"{base_url}/tasks",
            json=task_submission,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            task_response = response.json()
            print(f"Task submitted successfully!")
            print(f"Task ID: {task_response['task_id']}")
            print(f"Status: {task_response['status']}")
            print(f"Created: {task_response['created_at']}")
            
            # Test getting the task back
            print(f"\n[TEST] Getting task details...")
            task_id = task_response['task_id']
            
            get_response = requests.get(f"{base_url}/tasks/{task_id}")
            print(f"Status: {get_response.status_code}")
            
            if get_response.status_code == 200:
                task_details = get_response.json()
                print(f"Retrieved task: {task_details['task_id']}")
                print(f"Title: {task_details['title']}")
                print(f"Deliverables: {len(task_details.get('deliverables', []))}")
            else:
                print(f"Error getting task: {get_response.text}")
            
            # Test running the task
            print(f"\n[TEST] Running task...")
            run_response = requests.post(f"{base_url}/tasks/{task_id}/run")
            print(f"Status: {run_response.status_code}")
            
            if run_response.status_code == 200:
                run_result = run_response.json()
                print(f"Task execution result:")
                print(f"Success: {run_result.get('success', 'unknown')}")
                if 'run_id' in run_result:
                    print(f"Run ID: {run_result['run_id']}")
                if 'error' in run_result:
                    print(f"Error: {run_result['error']}")
            else:
                print(f"Error running task: {run_response.text}")
                
        else:
            print(f"Error submitting task:")
            try:
                error_detail = response.json()
                print(f"Detail: {error_detail}")
            except:
                print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"Error: {e}")
    
    # Test listing tasks
    print(f"\n[TEST] Listing tasks...")
    try:
        response = requests.get(f"{base_url}/tasks")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            tasks_response = response.json()
            print(f"Total tasks: {tasks_response.get('total', 0)}")
            print(f"Returned tasks: {len(tasks_response.get('tasks', []))}")
            
            for task in tasks_response.get('tasks', []):
                print(f"  - {task['task_id']}: {task['status']}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Test system status
    print(f"\n[TEST] System status...")
    try:
        response = requests.get(f"{base_url}/status")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            status = response.json()
            print(f"System status: {json.dumps(status, indent=2)}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")


def create_simple_task_example():
    """Create a simple task example for testing."""
    
    simple_task = {
        "task_id": "SIMPLE-HELLO-001",
        "title": "Create Hello World Script",
        "goal": "Create a simple Python script that prints hello world",
        "background": "Basic test task for API validation",
        "inputs": ["Python 3.8+"],
        "deliverables": ["hello.py script"],
        "acceptance_criteria": ["Script runs without errors", "Prints 'Hello World'"],
        "definition_of_done": ["Script executes successfully"],
        "risk_checks": ["No risks for hello world script"],
        "run_instructions": ["python hello.py"],
        "timebox_hours": 0.1
    }
    
    task_submission = {"spec": simple_task}
    
    print("\nSimple Task Example:")
    print("=" * 30)
    print("POST /tasks")
    print("Content-Type: application/json")
    print()
    print(json.dumps(task_submission, indent=2))
    print()
    
    return task_submission


def main():
    """Main function."""
    
    print("Testing AI Manager API...")
    print("Make sure the server is running on http://localhost:8000")
    print()
    
    # Show example request format
    create_simple_task_example()
    
    # Run API tests
    test_api_endpoints()
    
    print("\n" + "=" * 40)
    print("API testing complete!")


if __name__ == "__main__":
    main()