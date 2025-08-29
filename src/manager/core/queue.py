"""Task queue implementation with SQLite backend."""

import json
import uuid
from datetime import datetime
from typing import List, Optional

from manager.core.schemas import TaskSpec, TaskStatus
from manager.store.models import DatabaseManager, TaskModel


class TaskQueue:
    """SQLite-backed task queue with FIFO processing."""

    def __init__(self):
        self.db = DatabaseManager()

    def enqueue(self, task_spec: TaskSpec) -> str:
        """Enqueue a new task and return task ID."""
        task_data = {
            "task_id": task_spec.task_id,
            "title": task_spec.title,
            "goal": task_spec.goal,
            "background": task_spec.background,
            "inputs_json": json.dumps(task_spec.inputs),
            "deliverables_json": json.dumps(task_spec.deliverables),
            "acceptance_criteria_json": json.dumps(task_spec.acceptance_criteria),
            "definition_of_done_json": json.dumps(task_spec.definition_of_done),
            "risk_checks_json": json.dumps(task_spec.risk_checks),
            "run_instructions_json": json.dumps(task_spec.run_instructions),
            "timebox_hours": task_spec.timebox_hours,
            "status": TaskStatus.QUEUED.value,
        }
        
        task = self.db.create_task(task_data)
        
        # Log enqueue event
        self.db.log_event(
            event_type="task_enqueued",
            entity_type="task",
            entity_id=task_spec.task_id,
            data={"title": task_spec.title, "timebox_hours": task_spec.timebox_hours},
        )
        
        return task.task_id

    def dequeue(self) -> Optional[TaskSpec]:
        """Get next queued task (FIFO)."""
        tasks = self.db.list_tasks(limit=1000)  # Get recent tasks
        
        # Find first queued task
        for task_model in tasks:
            if task_model.status == TaskStatus.QUEUED.value:
                # Convert back to TaskSpec
                task_spec = self._model_to_spec(task_model)
                
                # Mark as running
                self.db.update_task_status(task_model.task_id, TaskStatus.RUNNING.value)
                
                # Log dequeue event
                self.db.log_event(
                    event_type="task_dequeued",
                    entity_type="task", 
                    entity_id=task_model.task_id,
                    data={"status": TaskStatus.RUNNING.value},
                )
                
                return task_spec
        
        return None

    def get_task(self, task_id: str) -> Optional[TaskSpec]:
        """Get task by ID."""
        task_model = self.db.get_task(task_id)
        if task_model:
            return self._model_to_spec(task_model)
        return None

    def update_status(self, task_id: str, status: TaskStatus) -> None:
        """Update task status."""
        self.db.update_task_status(task_id, status.value)
        
        # Log status change event
        self.db.log_event(
            event_type="task_status_changed",
            entity_type="task",
            entity_id=task_id,
            data={"new_status": status.value},
        )

    def list_tasks(self, status: Optional[TaskStatus] = None, limit: int = 100) -> List[TaskSpec]:
        """List tasks, optionally filtered by status."""
        task_models = self.db.list_tasks(limit=limit)
        
        tasks = []
        for model in task_models:
            if status is None or model.status == status.value:
                tasks.append(self._model_to_spec(model))
        
        return tasks

    def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        tasks = self.db.list_tasks(limit=1000)
        
        stats = {
            "total": len(tasks),
            "queued": sum(1 for t in tasks if t.status == TaskStatus.QUEUED.value),
            "running": sum(1 for t in tasks if t.status == TaskStatus.RUNNING.value), 
            "awaiting_review": sum(1 for t in tasks if t.status == TaskStatus.AWAITING_REVIEW.value),
            "completed": sum(1 for t in tasks if t.status in [
                TaskStatus.APPROVED.value, TaskStatus.MERGED.value
            ]),
            "failed": sum(1 for t in tasks if t.status in [
                TaskStatus.CHANGES_REQUESTED.value, TaskStatus.REJECTED.value
            ]),
        }
        
        return stats

    def _model_to_spec(self, model: TaskModel) -> TaskSpec:
        """Convert TaskModel to TaskSpec."""
        return TaskSpec(
            task_id=model.task_id,
            title=model.title,
            goal=model.goal,
            background=model.background,
            inputs=json.loads(model.inputs_json),
            deliverables=json.loads(model.deliverables_json),
            acceptance_criteria=json.loads(model.acceptance_criteria_json),
            definition_of_done=json.loads(model.definition_of_done_json),
            risk_checks=json.loads(model.risk_checks_json),
            run_instructions=json.loads(model.run_instructions_json),
            timebox_hours=model.timebox_hours,
        )

    def generate_task_id(self) -> str:
        """Generate a unique task ID."""
        # Use timestamp + short UUID for readability
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        short_uuid = str(uuid.uuid4())[:8]
        return f"T-{timestamp}-{short_uuid}"

    def validate_task_spec(self, task_spec: TaskSpec) -> List[str]:
        """Validate task specification and return errors."""
        errors = []
        
        if not task_spec.task_id.strip():
            errors.append("task_id is required")
        
        if not task_spec.title.strip():
            errors.append("title is required")
            
        if not task_spec.goal.strip():
            errors.append("goal is required")
        
        if task_spec.timebox_hours <= 0:
            errors.append("timebox_hours must be positive")
            
        if task_spec.timebox_hours > 24:
            errors.append("timebox_hours cannot exceed 24 hours")
            
        # Check for duplicate task ID
        existing_task = self.db.get_task(task_spec.task_id)
        if existing_task:
            errors.append(f"task_id '{task_spec.task_id}' already exists")
        
        return errors