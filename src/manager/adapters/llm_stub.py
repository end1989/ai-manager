"""LLM stub implementation for local-first operation without external API calls."""

import json
import random
from typing import Any, Dict, List


class LLMStub:
    """Stub LLM implementation that returns deterministic responses for testing."""

    def __init__(self):
        self.response_templates = self._load_templates()

    def generate_text(self, prompt: str) -> str:
        """Generate text response based on prompt analysis."""
        
        prompt_lower = prompt.lower()
        
        # Task planning responses
        if "acceptance criteria" in prompt_lower:
            return self._generate_acceptance_criteria(prompt)
        
        # Complexity analysis
        if "complexity" in prompt_lower and "analysis" in prompt_lower:
            return self._generate_complexity_analysis(prompt)
        
        # Code generation
        if "implement" in prompt_lower or "create" in prompt_lower:
            return self._generate_code_response(prompt)
        
        # Default response
        return self._generate_default_response(prompt)

    def generate_plan(self, prompt: str) -> str:
        """Generate task decomposition plan."""
        
        # Extract task information from prompt
        task_info = self._extract_task_info(prompt)
        
        # Generate subtasks based on deliverables
        subtasks = self._generate_subtasks(task_info)
        
        return json.dumps(subtasks, indent=2)

    def _generate_acceptance_criteria(self, prompt: str) -> str:
        """Generate acceptance criteria for a task."""
        
        # Extract deliverables from prompt
        deliverables = self._extract_deliverables(prompt)
        
        criteria = [
            "All specified deliverables are implemented and functional",
            "Code follows project coding standards and conventions",
            "All tests pass with minimum 85% code coverage",
        ]
        
        # Add specific criteria based on deliverables
        for deliverable in deliverables:
            if "api" in deliverable.lower():
                criteria.append("API endpoints return correct status codes and response formats")
            if "test" in deliverable.lower():
                criteria.append("Test cases cover all major functionality and edge cases")
            if "docs" in deliverable.lower():
                criteria.append("Documentation is clear, complete, and up-to-date")
            if "frontend" in deliverable.lower():
                criteria.append("UI components are responsive and accessible")
            if "database" in deliverable.lower():
                criteria.append("Database migrations are reversible and tested")
        
        return json.dumps(criteria)

    def _generate_complexity_analysis(self, prompt: str) -> str:
        """Generate complexity analysis for a task."""
        
        # Parse task information
        deliverables = self._extract_deliverables(prompt)
        timebox = self._extract_timebox(prompt)
        
        # Calculate complexity score
        complexity_score = 3  # Base complexity
        
        # Factor in deliverables
        complexity_score += min(len(deliverables), 5)
        
        # Factor in time estimate
        if timebox > 4:
            complexity_score += 2
        
        # Factor in keywords
        high_complexity_keywords = [
            "microservice", "api", "database", "authentication", "integration",
            "performance", "security", "migration", "distributed", "async"
        ]
        
        prompt_lower = prompt.lower()
        for keyword in high_complexity_keywords:
            if keyword in prompt_lower:
                complexity_score += 1
        
        complexity_score = min(complexity_score, 10)
        
        # Determine risk level
        if complexity_score <= 4:
            risk_level = "low"
            required_skills = ["python", "testing"]
            blockers = ["dependency conflicts"]
        elif complexity_score <= 7:
            risk_level = "medium"
            required_skills = ["python", "fastapi", "testing", "databases"]
            blockers = ["integration complexity", "third-party dependencies"]
        else:
            risk_level = "high"
            required_skills = ["python", "fastapi", "databases", "docker", "security"]
            blockers = ["architectural complexity", "performance requirements", "security concerns"]
        
        analysis = {
            "complexity_score": complexity_score,
            "estimated_hours": max(timebox, complexity_score * 0.5),
            "risk_level": risk_level,
            "required_skills": required_skills,
            "potential_blockers": blockers,
        }
        
        return json.dumps(analysis)

    def _generate_code_response(self, prompt: str) -> str:
        """Generate code implementation response."""
        
        if "fastapi" in prompt.lower():
            return self._generate_fastapi_code()
        elif "test" in prompt.lower():
            return self._generate_test_code()
        elif "class" in prompt.lower():
            return self._generate_class_code()
        else:
            return self._generate_function_code()

    def _generate_fastapi_code(self) -> str:
        """Generate FastAPI endpoint code."""
        
        code = '''
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str = None

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/items/")
async def create_item(item: Item):
    # Implementation here
    return {"message": "Item created", "item": item}

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    # Implementation here
    return {"item_id": item_id, "name": "Sample Item"}
'''
        return code.strip()

    def _generate_test_code(self) -> str:
        """Generate test code."""
        
        code = '''
import pytest
from fastapi.testclient import TestClient
from your_app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_create_item():
    item_data = {"name": "Test Item", "description": "Test Description"}
    response = client.post("/items/", json=item_data)
    assert response.status_code == 200
    assert "message" in response.json()

def test_get_item():
    response = client.get("/items/1")
    assert response.status_code == 200
    assert "item_id" in response.json()
'''
        return code.strip()

    def _generate_class_code(self) -> str:
        """Generate class implementation."""
        
        code = '''
class ServiceManager:
    """Service management class."""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.services = {}
    
    def register_service(self, name: str, service):
        """Register a service."""
        self.services[name] = service
    
    def get_service(self, name: str):
        """Get a registered service."""
        return self.services.get(name)
    
    def list_services(self) -> list:
        """List all registered services."""
        return list(self.services.keys())
'''
        return code.strip()

    def _generate_function_code(self) -> str:
        """Generate function implementation."""
        
        code = '''
def process_data(data: list) -> dict:
    """Process input data and return results."""
    
    if not data:
        return {"error": "No data provided"}
    
    results = {
        "count": len(data),
        "processed": [],
        "errors": []
    }
    
    for item in data:
        try:
            # Process item here
            processed_item = {"item": item, "status": "success"}
            results["processed"].append(processed_item)
        except Exception as e:
            results["errors"].append({"item": item, "error": str(e)})
    
    return results
'''
        return code.strip()

    def _generate_subtasks(self, task_info: Dict) -> List[Dict]:
        """Generate subtasks for decomposition."""
        
        deliverables = task_info.get("deliverables", [])
        timebox = task_info.get("timebox", 2.0)
        
        if len(deliverables) <= 1:
            # No decomposition needed
            return []
        
        subtasks = []
        time_per_task = timebox / len(deliverables)
        
        for i, deliverable in enumerate(deliverables):
            subtask = {
                "title": f"Implement {deliverable}",
                "goal": f"Create and test {deliverable}",
                "deliverables": [deliverable],
                "timebox_hours": round(time_per_task, 1),
                "dependencies": subtasks[-1]["title"] if subtasks else None,
            }
            subtasks.append(subtask)
        
        return subtasks

    def _generate_default_response(self, prompt: str) -> str:
        """Generate default response for unknown prompts."""
        
        responses = [
            "Task requirements understood. Implementation will follow best practices.",
            "Approach confirmed. Will implement with proper error handling and testing.",
            "Requirements clear. Solution will be modular and maintainable.",
        ]
        
        return random.choice(responses)

    def _extract_task_info(self, prompt: str) -> Dict:
        """Extract structured task information from prompt."""
        
        info = {
            "deliverables": self._extract_deliverables(prompt),
            "timebox": self._extract_timebox(prompt),
        }
        
        return info

    def _extract_deliverables(self, prompt: str) -> List[str]:
        """Extract deliverables from prompt text."""
        
        deliverables = []
        
        # Look for "Deliverables:" section
        if "deliverables:" in prompt.lower():
            lines = prompt.split("\n")
            in_deliverables = False
            
            for line in lines:
                if "deliverables:" in line.lower():
                    in_deliverables = True
                    continue
                
                if in_deliverables:
                    if line.strip() and not line.startswith(" "):
                        break  # End of deliverables section
                    
                    if line.strip():
                        # Clean up the line
                        clean_line = line.strip()
                        if clean_line.startswith("-") or clean_line.startswith("*"):
                            clean_line = clean_line[1:].strip()
                        deliverables.append(clean_line)
        
        # Fallback: look for common deliverable keywords
        if not deliverables:
            keywords = ["api", "test", "documentation", "frontend", "backend", "database"]
            for keyword in keywords:
                if keyword in prompt.lower():
                    deliverables.append(f"{keyword} implementation")
        
        return deliverables

    def _extract_timebox(self, prompt: str) -> float:
        """Extract timebox hours from prompt."""
        
        import re
        
        # Look for "Timebox:" or similar
        timebox_match = re.search(r"timebox[:\s]+(\d+(?:\.\d+)?)", prompt.lower())
        if timebox_match:
            return float(timebox_match.group(1))
        
        # Default timebox
        return 2.0

    def _load_templates(self) -> Dict[str, Any]:
        """Load response templates."""
        
        return {
            "task_plan": {
                "subtasks": [],
                "estimated_time": 0,
                "complexity": "medium",
            },
            "acceptance_criteria": [
                "Implementation complete",
                "Tests passing",
                "Documentation updated",
            ],
            "code_review": {
                "issues": [],
                "suggestions": [],
                "approval": True,
            },
        }