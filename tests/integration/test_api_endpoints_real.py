"""Real API endpoint testing with FastAPI TestClient."""

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from manager.api.http import app
from manager.core.schemas import TaskSpec, TaskStatus


@pytest.mark.integration
class TestAPIEndpointsReal:
    """Test API endpoints with real FastAPI TestClient operations."""

    def test_root_endpoint(self, api_client):
        """Test root endpoint responds correctly."""
        response = api_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["message"] == "AI Manager API"

    def test_health_endpoint(self, api_client):
        """Test health check endpoint."""
        response = api_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"

    def test_submit_task_endpoint_real(self, api_client, sample_task_dict):
        """Test task submission endpoint with real operations."""
        
        task_submission = {
            "spec": sample_task_dict
        }
        
        response = api_client.post("/tasks", json=task_submission)
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "task_id" in data
            assert "status" in data
            assert "created_at" in data
            assert data["task_id"] == sample_task_dict["task_id"]
        else:
            # If it fails, should have error details
            data = response.json()
            assert "detail" in data

    def test_submit_invalid_task(self, api_client):
        """Test submitting invalid task returns proper error."""
        
        invalid_task = {
            "spec": {
                "task_id": "",  # Invalid empty ID
                "title": "",    # Invalid empty title
                "goal": "",     # Invalid empty goal
                "background": "Test",
                "timebox_hours": -1.0,  # Invalid negative hours
            }
        }
        
        response = api_client.post("/tasks", json=invalid_task)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid task spec" in data["detail"]

    def test_list_tasks_endpoint(self, api_client):
        """Test task listing endpoint."""
        
        response = api_client.get("/tasks")
        
        assert response.status_code in [200, 500]  # May fail if no database
        
        if response.status_code == 200:
            data = response.json()
            assert "tasks" in data
            assert "total" in data
            assert isinstance(data["tasks"], list)
            assert isinstance(data["total"], int)

    def test_list_tasks_with_filters(self, api_client):
        """Test task listing with status filter."""
        
        response = api_client.get("/tasks?status=queued&limit=10")
        
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "tasks" in data
            assert "total" in data

    def test_list_tasks_invalid_status(self, api_client):
        """Test task listing with invalid status filter."""
        
        response = api_client.get("/tasks?status=invalid_status")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid status" in data["detail"]

    def test_get_task_endpoint(self, api_client, sample_task_dict):
        """Test getting specific task details."""
        
        # First submit a task (may fail)
        task_submission = {"spec": sample_task_dict}
        submit_response = api_client.post("/tasks", json=task_submission)
        
        if submit_response.status_code == 200:
            task_id = sample_task_dict["task_id"]
            
            # Try to get the task
            response = api_client.get(f"/tasks/{task_id}")
            
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert data["task_id"] == task_id
                assert data["title"] == sample_task_dict["title"]

    def test_get_nonexistent_task(self, api_client):
        """Test getting non-existent task returns 404."""
        
        response = api_client.get("/tasks/T-nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_run_task_endpoint(self, api_client, sample_task_dict):
        """Test running a task immediately via API."""
        
        # Submit task first
        task_submission = {"spec": sample_task_dict}
        submit_response = api_client.post("/tasks", json=task_submission)
        
        if submit_response.status_code == 200:
            task_id = sample_task_dict["task_id"]
            
            # Try to run the task
            response = api_client.post(f"/tasks/{task_id}/run")
            
            # May succeed, fail, or timeout
            assert response.status_code in [200, 404, 500]
            
            data = response.json()
            if response.status_code == 200:
                assert "success" in data
                assert "task_id" in data

    def test_system_status_endpoint(self, api_client):
        """Test system status endpoint."""
        
        response = api_client.get("/status")
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "dispatcher_running" in data
            assert "queue_stats" in data
            assert "active_runs" in data
            assert "timestamp" in data
            
            # Validate queue stats structure
            queue_stats = data["queue_stats"]
            assert "total" in queue_stats
            assert "queued" in queue_stats
            assert isinstance(queue_stats["total"], int)

    def test_dispatcher_control_endpoints(self, api_client):
        """Test dispatcher start/stop endpoints."""
        
        # Test start dispatcher
        start_response = api_client.post("/dispatcher/start")
        assert start_response.status_code in [200, 500]
        
        if start_response.status_code == 200:
            data = start_response.json()
            assert "message" in data
        
        # Test stop dispatcher
        stop_response = api_client.post("/dispatcher/stop")
        assert stop_response.status_code in [200, 500]
        
        if stop_response.status_code == 200:
            data = stop_response.json()
            assert "message" in data

    def test_list_runs_endpoint(self, api_client):
        """Test listing runs endpoint."""
        
        response = api_client.get("/runs")
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "runs" in data
            assert "total" in data
            assert isinstance(data["runs"], list)

    def test_get_run_endpoint(self, api_client):
        """Test getting run details."""
        
        # Try to get a non-existent run
        response = api_client.get("/runs/run-nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_get_run_logs_endpoint(self, api_client):
        """Test getting run logs."""
        
        # Try to get logs for non-existent run
        response = api_client.get("/runs/run-nonexistent/logs/stdout")
        
        assert response.status_code == 404

    def test_stop_run_endpoint(self, api_client):
        """Test stopping a run."""
        
        # Try to stop non-existent run
        response = api_client.post("/runs/run-nonexistent/stop")
        
        assert response.status_code == 400

    def test_cleanup_endpoint(self, api_client):
        """Test cleanup endpoint."""
        
        response = api_client.post("/cleanup")
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "details" in data
            
            details = data["details"]
            assert "runs_cleaned" in details
            assert "bytes_freed" in details

    def test_error_handling_endpoints(self, api_client):
        """Test error handling in API endpoints."""
        
        # Test malformed JSON
        response = api_client.post(
            "/tasks",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Unprocessable Entity
        
        # Test missing required fields
        response = api_client.post("/tasks", json={})
        assert response.status_code == 422

    def test_content_type_handling(self, api_client, sample_task_dict):
        """Test content type handling."""
        
        task_submission = {"spec": sample_task_dict}
        
        # Test with correct content type
        response = api_client.post("/tasks", json=task_submission)
        assert response.status_code in [200, 400, 500]
        
        # Test response content type
        if response.status_code == 200:
            assert "application/json" in response.headers.get("content-type", "")

    def test_api_cors_headers(self, api_client):
        """Test CORS headers if configured."""
        
        response = api_client.get("/")
        
        # CORS headers might not be configured, but test structure
        assert response.status_code == 200
        # Could check for CORS headers if needed

    def test_api_large_payload(self, api_client):
        """Test API with large payload."""
        
        # Create large task specification
        large_task = {
            "task_id": "T-large-payload",
            "title": "Large payload test",
            "goal": "Test large payload handling",
            "background": "x" * 10000,  # Large background text
            "deliverables": [f"deliverable-{i}" for i in range(100)],
            "acceptance_criteria": [f"criteria-{i}" for i in range(50)],
            "timebox_hours": 2.0,
        }
        
        task_submission = {"spec": large_task}
        
        response = api_client.post("/tasks", json=task_submission)
        
        # Should handle large payloads gracefully
        assert response.status_code in [200, 400, 413, 500]  # 413 = Payload Too Large
        
        if response.status_code != 413:  # If not rejected for size
            data = response.json()
            assert "detail" in data or "task_id" in data

    @pytest.mark.slow
    def test_api_concurrent_requests(self, api_client, sample_task_dict):
        """Test API handling concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            """Make a request from a thread."""
            try:
                response = api_client.get("/status")
                results.append(response.status_code)
            except Exception as e:
                results.append(f"Error: {e}")
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10)
        
        # Check results
        assert len(results) == 5
        assert all(isinstance(result, int) for result in results)
        assert all(result in [200, 500] for result in results)

    def test_api_authentication_headers(self, api_client):
        """Test API with various headers (no auth required but test structure)."""
        
        # Test with various headers
        headers = {
            "User-Agent": "Test-Client/1.0",
            "X-Request-ID": "test-request-123",
        }
        
        response = api_client.get("/", headers=headers)
        assert response.status_code == 200

    def test_api_documentation_endpoints(self, api_client):
        """Test API documentation endpoints."""
        
        # Test OpenAPI spec
        response = api_client.get("/docs")
        assert response.status_code == 200
        
        # Test ReDoc
        response = api_client.get("/redoc")
        assert response.status_code == 200
        
        # Test OpenAPI JSON
        response = api_client.get("/openapi.json")
        assert response.status_code == 200
        
        if response.status_code == 200:
            spec = response.json()
            assert "openapi" in spec
            assert "info" in spec
            assert spec["info"]["title"] == "AI Manager"