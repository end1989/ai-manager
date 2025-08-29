"""Main orchestrator for AI Manager - coordinates planning, execution, and review."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from manager.config import settings
from manager.core.artifacts import ArtifactManager
from manager.core.executor import WorkerExecutor
from manager.core.planner import TaskPlanner
from manager.core.queue import TaskQueue
from manager.core.review import ReviewEngine
from manager.core.schemas import (
    PullRequestProposal,
    ReviewStatus,
    TaskSpec,
    TaskStatus,
    WorkerTaskReport,
)
from manager.store.models import DatabaseManager, create_db_and_tables

logger = logging.getLogger(__name__)


class ManagerCore:
    """Main orchestrator that coordinates task lifecycle from submission to merge."""

    def __init__(self):
        # Initialize core components
        self.queue = TaskQueue()
        self.planner = TaskPlanner()
        self.executor = WorkerExecutor()
        self.reviewer = ReviewEngine()
        self.artifacts = ArtifactManager()
        self.db = DatabaseManager()
        
        # Initialize database
        create_db_and_tables()
        
        # Dispatcher state
        self._running = False
        self._dispatcher_task: Optional[asyncio.Task] = None

    async def submit_task(self, task_spec: TaskSpec) -> str:
        """Submit new task to the system."""
        
        logger.info(f"Submitting task: {task_spec.task_id} - {task_spec.title}")
        
        # Validate task spec
        validation_errors = self.queue.validate_task_spec(task_spec)
        if validation_errors:
            raise ValueError(f"Invalid task spec: {', '.join(validation_errors)}")
        
        # Plan task (potentially decompose into subtasks)
        planned_tasks = self.planner.plan_task(task_spec)
        
        # Validate plan
        plan_errors = self.planner.validate_plan(planned_tasks)
        if plan_errors:
            raise ValueError(f"Invalid task plan: {', '.join(plan_errors)}")
        
        # Enqueue all tasks
        task_ids = []
        for task in planned_tasks:
            task_id = self.queue.enqueue(task)
            task_ids.append(task_id)
            
            logger.info(f"Enqueued task: {task_id}")
        
        # Log submission
        self.db.log_event(
            event_type="task_submitted",
            entity_type="task",
            entity_id=task_spec.task_id,
            data={
                "title": task_spec.title,
                "subtasks": len(planned_tasks),
                "total_timebox": sum(t.timebox_hours for t in planned_tasks),
            },
        )
        
        return task_spec.task_id

    async def start_dispatcher(self):
        """Start the main dispatcher loop."""
        
        if self._running:
            logger.warning("Dispatcher already running")
            return
        
        logger.info("Starting task dispatcher")
        self._running = True
        self._dispatcher_task = asyncio.create_task(self._dispatcher_loop())

    async def stop_dispatcher(self):
        """Stop the dispatcher loop."""
        
        if not self._running:
            logger.warning("Dispatcher not running")
            return
        
        logger.info("Stopping task dispatcher")
        self._running = False
        
        if self._dispatcher_task:
            self._dispatcher_task.cancel()
            try:
                await self._dispatcher_task
            except asyncio.CancelledError:
                pass
            self._dispatcher_task = None

    async def _dispatcher_loop(self):
        """Main dispatcher loop - processes queued tasks."""
        
        logger.info("Dispatcher loop started")
        
        while self._running:
            try:
                # Get next task from queue
                task_spec = self.queue.dequeue()
                
                if task_spec:
                    logger.info(f"Processing task: {task_spec.task_id}")
                    
                    # Execute task asynchronously
                    asyncio.create_task(self._process_task(task_spec))
                else:
                    # No tasks, wait before checking again
                    await asyncio.sleep(5)
                    
            except Exception as e:
                logger.error(f"Dispatcher error: {str(e)}")
                await asyncio.sleep(10)  # Back off on error

    async def _process_task(self, task_spec: TaskSpec):
        """Process a single task through execution and review."""
        
        try:
            # Execute task
            run_id, execution_result = await self.executor.execute_task(task_spec)
            
            if not execution_result.get("success", False):
                logger.error(f"Task execution failed: {task_spec.task_id}")
                self.queue.update_status(task_spec.task_id, TaskStatus.REJECTED)
                return
            
            # Collect worker results
            worker_report = self.artifacts.read_worker_report(run_id)
            pr_proposal_data = self.artifacts.read_pr_proposal(run_id)
            
            if not worker_report or not pr_proposal_data:
                logger.error(f"Missing worker outputs: {task_spec.task_id}")
                self.queue.update_status(task_spec.task_id, TaskStatus.REJECTED)
                return
            
            # Parse outputs
            report = WorkerTaskReport(**worker_report)
            proposal = PullRequestProposal(**pr_proposal_data)
            
            # Store PR proposal
            pr_data = {
                "pr_id": proposal.pr_id,
                "run_id": run_id,
                "title": proposal.title,
                "description": proposal.description,
                "diff_summary_json": proposal.model_dump_json(),
                "ci_status": proposal.ci_status,
            }
            self.db.create_pr(pr_data)
            
            # Update task status
            self.queue.update_status(task_spec.task_id, TaskStatus.AWAITING_REVIEW)
            
            # Perform review
            review_result = await self.reviewer.review_pr(proposal, run_id)
            
            # Process review decision
            if review_result.status == ReviewStatus.APPROVED:
                await self._merge_changes(task_spec, proposal, run_id)
                self.queue.update_status(task_spec.task_id, TaskStatus.APPROVED)
                
                # Eventually mark as merged after successful merge
                self.queue.update_status(task_spec.task_id, TaskStatus.MERGED)
                
                logger.info(f"Task completed successfully: {task_spec.task_id}")
                
            elif review_result.status == ReviewStatus.CHANGES_REQUESTED:
                self.queue.update_status(task_spec.task_id, TaskStatus.CHANGES_REQUESTED)
                logger.warning(f"Task requires changes: {task_spec.task_id}")
                
            else:  # REJECTED
                self.queue.update_status(task_spec.task_id, TaskStatus.REJECTED)
                logger.error(f"Task rejected: {task_spec.task_id}")
            
        except Exception as e:
            logger.error(f"Task processing error for {task_spec.task_id}: {str(e)}")
            self.queue.update_status(task_spec.task_id, TaskStatus.REJECTED)

    async def _merge_changes(self, task_spec: TaskSpec, proposal: PullRequestProposal, run_id: str):
        """Simulate merging approved changes to main codebase."""
        
        logger.info(f"Merging changes for task: {task_spec.task_id}")
        
        # In a real system, this would:
        # 1. Apply diffs to main branch
        # 2. Update services/components
        # 3. Update documentation
        # 4. Create deployment artifacts
        
        # For now, we'll create a merge summary
        run_path = settings.runs_dir / run_id
        workdir = run_path / "workdir"
        
        # Create merge record
        merge_summary = {
            "task_id": task_spec.task_id,
            "pr_id": proposal.pr_id,
            "merged_at": datetime.utcnow().isoformat(),
            "files_changed": len(proposal.diff_summary),
            "title": proposal.title,
            "description": proposal.description,
        }
        
        merge_path = run_path / "merge_summary.json"
        import json
        with open(merge_path, "w") as f:
            json.dump(merge_summary, f, indent=2)
        
        # Log merge event
        self.db.log_event(
            event_type="changes_merged",
            entity_type="task",
            entity_id=task_spec.task_id,
            data=merge_summary,
        )

    def get_system_status(self) -> Dict:
        """Get overall system status."""
        
        # Get queue stats
        queue_stats = self.queue.get_queue_stats()
        
        # Get active runs
        active_runs = self.executor.get_active_runs()
        
        # System health
        status = {
            "dispatcher_running": self._running,
            "queue_stats": queue_stats,
            "active_runs": len(active_runs),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        return status

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task and any running executions."""
        
        try:
            # Check if task exists
            task_model = self.db.get_task(task_id)
            if not task_model:
                return False
            
            # Update task status to cancelled
            self.db.update_task_status(task_id, "cancelled")
            
            # Find and stop any running executions
            runs = self.db.list_runs_for_task(task_id)
            stopped_runs = 0
            
            for run in runs:
                if run.status == "running" and run.worker_pid:
                    success = await self.executor.stop_run(run.run_id)
                    if success:
                        stopped_runs += 1
            
            # Log cancellation
            self.db.log_event(
                event_type="task_cancelled",
                entity_type="task",
                entity_id=task_id,
                data={
                    "cancelled_by": "api",
                    "stopped_runs": stopped_runs
                }
            )
            
            logger.info(f"Cancelled task {task_id}, stopped {stopped_runs} runs")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {str(e)}")
            return False

    async def run_single_task(self, task_spec: TaskSpec) -> Dict:
        """Run a single task synchronously (for testing/debugging)."""
        
        logger.info(f"Running single task: {task_spec.task_id}")
        
        # Validate task
        validation_errors = self.queue.validate_task_spec(task_spec)
        if validation_errors:
            return {
                "success": False,
                "error": f"Invalid task: {', '.join(validation_errors)}",
            }
        
        try:
            # Plan task
            planned_tasks = self.planner.plan_task(task_spec)
            
            if len(planned_tasks) > 1:
                return {
                    "success": False,
                    "error": "Single task execution doesn't support decomposition",
                }
            
            # Execute task
            run_id, execution_result = await self.executor.execute_task(task_spec)
            
            if not execution_result.get("success", False):
                return {
                    "success": False,
                    "run_id": run_id,
                    "error": execution_result.get("error", "Execution failed"),
                }
            
            # Get outputs
            worker_report = self.artifacts.read_worker_report(run_id)
            pr_proposal_data = self.artifacts.read_pr_proposal(run_id)
            
            if not worker_report or not pr_proposal_data:
                return {
                    "success": False,
                    "run_id": run_id,
                    "error": "Missing worker outputs",
                }
            
            # Parse and review
            proposal = PullRequestProposal(**pr_proposal_data)
            review_result = await self.reviewer.review_pr(proposal, run_id)
            
            return {
                "success": True,
                "run_id": run_id,
                "task_id": task_spec.task_id,
                "review_status": review_result.status.value,
                "blocking_issues": review_result.blocking,
                "execution_time": execution_result.get("duration_seconds", 0),
            }
            
        except Exception as e:
            logger.error(f"Single task execution error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }

    async def cleanup_old_data(self) -> Dict:
        """Clean up old runs and artifacts."""
        
        logger.info("Starting cleanup process")
        
        # Clean up old run directories
        cleanup_result = self.artifacts.cleanup_old_runs()
        
        logger.info(f"Cleanup completed: {cleanup_result}")
        
        return cleanup_result