"""Unit tests for task queue functionality."""

import pytest
from datetime import datetime

from manager.core.queue import TaskQueue
from manager.core.schemas import TaskSpec, TaskStatus
from manager.store.models import create_db_and_tables


@pytest.fixture
def task_queue():
    """Create task queue for testing."""
    # Use in-memory SQLite for testing
    import os
    os.environ["MANAGER_DB_URL"] = "sqlite:///:memory:"
    
    create_db_and_tables()
    return TaskQueue()


@pytest.fixture
def sample_task():
    """Create sample task specification."""
    return TaskSpec(
        task_id="T-test-001",
        title="Test task",
        goal="Test goal",
        background="Test background",
        deliverables=["test deliverable"],
        timebox_hours=1.0,
    )


def test_enqueue_task(task_queue, sample_task):
    """Test task enqueuing."""
    task_id = task_queue.enqueue(sample_task)
    
    assert task_id == sample_task.task_id
    
    # Verify task was stored
    stored_task = task_queue.get_task(task_id)
    assert stored_task is not None
    assert stored_task.task_id == sample_task.task_id
    assert stored_task.title == sample_task.title


def test_dequeue_task(task_queue, sample_task):
    """Test task dequeuing."""
    # Enqueue task first
    task_queue.enqueue(sample_task)
    
    # Dequeue task
    dequeued_task = task_queue.dequeue()
    
    assert dequeued_task is not None
    assert dequeued_task.task_id == sample_task.task_id
    
    # Task should now be running
    stored_task = task_queue.get_task(sample_task.task_id)
    # Note: dequeue marks as running in the database, not the returned TaskSpec


def test_dequeue_empty_queue(task_queue):
    """Test dequeuing from empty queue."""
    task = task_queue.dequeue()
    assert task is None


def test_update_task_status(task_queue, sample_task):
    """Test updating task status."""
    task_queue.enqueue(sample_task)
    
    # Update status
    task_queue.update_status(sample_task.task_id, TaskStatus.APPROVED)
    
    # Verify status was updated in database
    task_model = task_queue.db.get_task(sample_task.task_id)
    assert task_model.status == TaskStatus.APPROVED.value


def test_list_tasks(task_queue):
    """Test listing tasks."""
    # Create multiple tasks
    tasks = []
    for i in range(3):
        task = TaskSpec(
            task_id=f"T-test-{i:03d}",
            title=f"Test task {i}",
            goal=f"Test goal {i}",
            background="Test background",
            deliverables=["test deliverable"],
            timebox_hours=1.0,
        )
        tasks.append(task)
        task_queue.enqueue(task)
    
    # List all tasks
    all_tasks = task_queue.list_tasks()
    assert len(all_tasks) == 3
    
    # List with status filter
    queued_tasks = task_queue.list_tasks(status=TaskStatus.QUEUED)
    assert len(queued_tasks) == 3
    
    # Update one task and test filter
    task_queue.update_status(tasks[0].task_id, TaskStatus.RUNNING)
    queued_tasks = task_queue.list_tasks(status=TaskStatus.QUEUED)
    assert len(queued_tasks) == 2


def test_queue_stats(task_queue):
    """Test queue statistics."""
    # Initially empty
    stats = task_queue.get_queue_stats()
    assert stats["total"] == 0
    assert stats["queued"] == 0
    
    # Add tasks with different statuses
    task1 = TaskSpec(task_id="T-001", title="Task 1", goal="Goal 1", background="BG")
    task2 = TaskSpec(task_id="T-002", title="Task 2", goal="Goal 2", background="BG")
    task3 = TaskSpec(task_id="T-003", title="Task 3", goal="Goal 3", background="BG")
    
    task_queue.enqueue(task1)
    task_queue.enqueue(task2)
    task_queue.enqueue(task3)
    
    # Update statuses
    task_queue.update_status(task1.task_id, TaskStatus.RUNNING)
    task_queue.update_status(task2.task_id, TaskStatus.APPROVED)
    
    # Check stats
    stats = task_queue.get_queue_stats()
    assert stats["total"] == 3
    assert stats["queued"] == 1
    assert stats["running"] == 1
    assert stats["completed"] == 1


def test_generate_task_id(task_queue):
    """Test task ID generation."""
    task_id = task_queue.generate_task_id()
    
    assert task_id.startswith("T-")
    assert len(task_id) > 10  # Should include timestamp and UUID


def test_validate_task_spec(task_queue, sample_task):
    """Test task specification validation."""
    # Valid task should have no errors
    errors = task_queue.validate_task_spec(sample_task)
    assert len(errors) == 0
    
    # Invalid task - missing required fields
    invalid_task = TaskSpec(
        task_id="",
        title="",
        goal="",
        background="Test",
        timebox_hours=-1.0,
    )
    
    errors = task_queue.validate_task_spec(invalid_task)
    assert len(errors) > 0
    assert any("task_id is required" in error for error in errors)
    assert any("title is required" in error for error in errors)
    assert any("goal is required" in error for error in errors)
    assert any("timebox_hours must be positive" in error for error in errors)


def test_duplicate_task_id(task_queue, sample_task):
    """Test duplicate task ID validation."""
    # Enqueue first task
    task_queue.enqueue(sample_task)
    
    # Try to enqueue duplicate
    duplicate_task = TaskSpec(
        task_id=sample_task.task_id,  # Same ID
        title="Different title",
        goal="Different goal", 
        background="Different background",
    )
    
    errors = task_queue.validate_task_spec(duplicate_task)
    assert len(errors) > 0
    assert any("already exists" in error for error in errors)


def test_task_timebox_validation(task_queue):
    """Test task timebox validation."""
    # Excessive timebox
    long_task = TaskSpec(
        task_id="T-long",
        title="Long task",
        goal="Long goal",
        background="Long background",
        timebox_hours=25.0,  # Over 24 hours
    )
    
    errors = task_queue.validate_task_spec(long_task)
    assert any("cannot exceed 24 hours" in error for error in errors)


def test_fifo_ordering(task_queue):
    """Test FIFO ordering of tasks."""
    # Enqueue multiple tasks
    tasks = []
    for i in range(3):
        task = TaskSpec(
            task_id=f"T-fifo-{i:03d}",
            title=f"FIFO task {i}",
            goal=f"Goal {i}",
            background="Background",
        )
        tasks.append(task)
        task_queue.enqueue(task)
    
    # Dequeue should return first task
    first_task = task_queue.dequeue()
    assert first_task.task_id == tasks[0].task_id
    
    # Second dequeue should return second task
    second_task = task_queue.dequeue()
    assert second_task.task_id == tasks[1].task_id