"""Task planning engine with rule-based decomposition and LLM plugin hooks."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from manager.core.schemas import TaskSpec
from manager.adapters.llm_stub import LLMStub


class TaskPlanner:
    """Plans and decomposes tasks with pluggable LLM backend."""

    def __init__(self):
        self.llm = LLMStub()  # Use stub by default, can be swapped for real LLM

    def plan_task(self, task_spec: TaskSpec) -> List[TaskSpec]:
        """Plan task execution, potentially breaking into subtasks."""
        
        # For now, use rule-based planning
        # Real LLM integration would analyze the task and create a plan
        
        # Check if task needs decomposition
        if self._should_decompose(task_spec):
            return self._decompose_task(task_spec)
        else:
            return [task_spec]  # Single task execution

    def _should_decompose(self, task_spec: TaskSpec) -> bool:
        """Determine if task should be broken into subtasks."""
        
        # Rule-based decomposition triggers
        decomposition_indicators = [
            len(task_spec.deliverables) > 3,  # Multiple deliverables
            task_spec.timebox_hours > 4,      # Long duration
            "microservice" in task_spec.goal.lower(),  # Complex architecture
            "api" in task_spec.goal.lower() and "frontend" in task_spec.goal.lower(),
        ]
        
        return any(decomposition_indicators)

    def _decompose_task(self, task_spec: TaskSpec) -> List[TaskSpec]:
        """Break down task into smaller subtasks."""
        
        subtasks = []
        
        # Use LLM to generate decomposition plan
        decomposition_prompt = self._build_decomposition_prompt(task_spec)
        llm_response = self.llm.generate_plan(decomposition_prompt)
        
        # Parse LLM response into subtasks
        try:
            plan_data = json.loads(llm_response)
            subtasks = self._create_subtasks_from_plan(task_spec, plan_data)
        except (json.JSONDecodeError, KeyError):
            # Fallback to rule-based decomposition
            subtasks = self._rule_based_decomposition(task_spec)
        
        return subtasks if subtasks else [task_spec]

    def _build_decomposition_prompt(self, task_spec: TaskSpec) -> str:
        """Build prompt for LLM task decomposition."""
        
        prompt = f"""
Task Decomposition Request:

Title: {task_spec.title}
Goal: {task_spec.goal}
Background: {task_spec.background}
Deliverables: {', '.join(task_spec.deliverables)}
Timebox: {task_spec.timebox_hours} hours

Please decompose this task into 2-4 smaller subtasks that can be executed independently.
Each subtask should have a clear goal and deliverable.

Return a JSON array of subtasks in this format:
[
  {{
    "title": "Subtask title",
    "goal": "Specific goal",
    "deliverables": ["deliverable1", "deliverable2"],
    "timebox_hours": 1.5,
    "dependencies": []
  }}
]
"""
        return prompt

    def _create_subtasks_from_plan(self, parent_task: TaskSpec, plan_data: List[Dict]) -> List[TaskSpec]:
        """Create TaskSpec objects from LLM plan."""
        
        subtasks = []
        
        for i, subtask_data in enumerate(plan_data):
            # Generate subtask ID
            subtask_id = f"{parent_task.task_id}-{i+1}"
            
            # Create subtask spec
            subtask = TaskSpec(
                task_id=subtask_id,
                title=subtask_data.get("title", f"Subtask {i+1}"),
                goal=subtask_data.get("goal", ""),
                background=f"Subtask of {parent_task.task_id}: {parent_task.background}",
                inputs=parent_task.inputs,  # Inherit inputs
                deliverables=subtask_data.get("deliverables", []),
                acceptance_criteria=parent_task.acceptance_criteria,  # Inherit criteria
                definition_of_done=parent_task.definition_of_done,    # Inherit DoD
                risk_checks=parent_task.risk_checks,                  # Inherit risks
                run_instructions=parent_task.run_instructions,        # Inherit instructions
                timebox_hours=subtask_data.get("timebox_hours", 1.0),
            )
            
            subtasks.append(subtask)
        
        return subtasks

    def _rule_based_decomposition(self, task_spec: TaskSpec) -> List[TaskSpec]:
        """Fallback rule-based task decomposition."""
        
        subtasks = []
        
        # Decompose by deliverable type
        if len(task_spec.deliverables) > 1:
            for i, deliverable in enumerate(task_spec.deliverables):
                subtask_id = f"{task_spec.task_id}-{i+1}"
                
                subtask = TaskSpec(
                    task_id=subtask_id,
                    title=f"{task_spec.title} - {deliverable}",
                    goal=f"Implement: {deliverable}",
                    background=task_spec.background,
                    inputs=task_spec.inputs,
                    deliverables=[deliverable],
                    acceptance_criteria=task_spec.acceptance_criteria,
                    definition_of_done=task_spec.definition_of_done,
                    risk_checks=task_spec.risk_checks,
                    run_instructions=task_spec.run_instructions,
                    timebox_hours=task_spec.timebox_hours / len(task_spec.deliverables),
                )
                
                subtasks.append(subtask)
        
        return subtasks

    def generate_acceptance_criteria(self, task_spec: TaskSpec) -> List[str]:
        """Generate acceptance criteria for a task using LLM."""
        
        prompt = f"""
Generate acceptance criteria for this task:

Title: {task_spec.title}
Goal: {task_spec.goal}
Deliverables: {', '.join(task_spec.deliverables)}

Return 3-5 specific, measurable acceptance criteria as a JSON array of strings.
Each criterion should be testable and clearly define when the task is complete.
"""
        
        response = self.llm.generate_text(prompt)
        
        try:
            criteria = json.loads(response)
            return criteria if isinstance(criteria, list) else []
        except json.JSONDecodeError:
            # Fallback to rule-based criteria
            return self._generate_default_criteria(task_spec)

    def _generate_default_criteria(self, task_spec: TaskSpec) -> List[str]:
        """Generate default acceptance criteria."""
        
        criteria = [
            "All deliverables are implemented and functional",
            "Code passes all quality checks (linting, type checking)",
            "Tests are written and passing with >= 85% coverage",
        ]
        
        # Add specific criteria based on deliverables
        for deliverable in task_spec.deliverables:
            if "api" in deliverable.lower():
                criteria.append("API endpoints return correct responses")
            if "test" in deliverable.lower(): 
                criteria.append("Test suite covers all major functionality")
            if "docs" in deliverable.lower():
                criteria.append("Documentation is complete and accurate")
        
        return criteria

    def estimate_complexity(self, task_spec: TaskSpec) -> Dict[str, Any]:
        """Estimate task complexity and resource requirements."""
        
        # Use LLM for complexity analysis
        prompt = f"""
Analyze the complexity of this task:

Title: {task_spec.title}
Goal: {task_spec.goal}
Deliverables: {', '.join(task_spec.deliverables)}

Return a JSON object with complexity analysis:
{{
  "complexity_score": 1-10,
  "estimated_hours": number,
  "risk_level": "low|medium|high",
  "required_skills": ["skill1", "skill2"],
  "potential_blockers": ["blocker1", "blocker2"]
}}
"""
        
        response = self.llm.generate_text(prompt)
        
        try:
            analysis = json.loads(response)
            return analysis
        except json.JSONDecodeError:
            # Fallback to rule-based estimation
            return self._estimate_complexity_rules(task_spec)

    def _estimate_complexity_rules(self, task_spec: TaskSpec) -> Dict[str, Any]:
        """Rule-based complexity estimation."""
        
        complexity_score = 1
        
        # Factor in deliverables
        complexity_score += len(task_spec.deliverables)
        
        # Factor in timebox
        if task_spec.timebox_hours > 4:
            complexity_score += 2
        
        # Factor in keywords
        high_complexity_keywords = [
            "microservice", "api", "database", "authentication", 
            "integration", "migration", "performance"
        ]
        
        goal_lower = task_spec.goal.lower()
        for keyword in high_complexity_keywords:
            if keyword in goal_lower:
                complexity_score += 1
        
        # Determine risk level
        if complexity_score <= 3:
            risk_level = "low"
        elif complexity_score <= 6:
            risk_level = "medium" 
        else:
            risk_level = "high"
        
        return {
            "complexity_score": min(complexity_score, 10),
            "estimated_hours": task_spec.timebox_hours,
            "risk_level": risk_level,
            "required_skills": ["python", "testing"],
            "potential_blockers": ["dependency issues", "unclear requirements"],
        }

    def validate_plan(self, tasks: List[TaskSpec]) -> List[str]:
        """Validate a task plan for consistency and feasibility."""
        
        errors = []
        
        # Check for duplicate IDs
        task_ids = [task.task_id for task in tasks]
        if len(task_ids) != len(set(task_ids)):
            errors.append("Duplicate task IDs found in plan")
        
        # Validate individual tasks
        for task in tasks:
            # Check timebox is reasonable
            if task.timebox_hours > 8:
                errors.append(f"Task {task.task_id} timebox exceeds 8 hours")
            
            # Check for required fields
            if not task.goal.strip():
                errors.append(f"Task {task.task_id} missing goal")
                
            if not task.deliverables:
                errors.append(f"Task {task.task_id} has no deliverables")
        
        # Check total time estimate
        total_hours = sum(task.timebox_hours for task in tasks)
        if total_hours > 24:
            errors.append(f"Total plan time ({total_hours:.1f}h) exceeds 24 hours")
        
        return errors