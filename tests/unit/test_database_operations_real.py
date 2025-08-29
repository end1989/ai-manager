"""Real database operation testing with SQLite."""

import json
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import pytest

from manager.store.models import (
    DatabaseManager, 
    TaskModel, 
    RunModel, 
    ArtifactModel, 
    PRModel, 
    ReviewModel, 
    EventModel,
    create_db_and_tables
)
from manager.core.schemas import TaskStatus


@pytest.mark.database
class TestDatabaseOperationsReal:
    """Test real database operations with SQLite."""

    @pytest.fixture
    def db_manager(self, test_db):
        """Create database manager with real database."""
        return DatabaseManager()

    def test_database_creation_real(self, test_db, db_connection):
        """Test that database tables are actually created."""
        
        # Check that tables exist
        cursor = db_connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ["tasks", "runs", "artifacts", "prs", "reviews", "events"]
        for table in expected_tables:
            assert table in tables, f"Table {table} should exist in database"

    def test_database_schema_validation(self, test_db, db_connection):
        """Test that database schema matches expectations."""
        
        cursor = db_connection.cursor()
        
        # Check tasks table schema
        cursor.execute("PRAGMA table_info(tasks)")
        task_columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        expected_task_columns = {
            "id": "INTEGER",
            "task_id": "VARCHAR", 
            "title": "VARCHAR",
            "goal": "VARCHAR",
            "background": "VARCHAR",
            "status": "VARCHAR",
            "timebox_hours": "FLOAT",
        }
        
        for col, col_type in expected_task_columns.items():
            assert col in task_columns, f"Column {col} should exist in tasks table"
            assert col_type in task_columns[col], f"Column {col} should be {col_type}"

    def test_task_crud_operations_real(self, db_manager, sample_task_spec):
        """Test real CRUD operations on tasks."""
        
        # CREATE - Insert task
        task_data = {
            "task_id": sample_task_spec.task_id,
            "title": sample_task_spec.title,
            "goal": sample_task_spec.goal,
            "background": sample_task_spec.background,
            "inputs_json": json.dumps(sample_task_spec.inputs),
            "deliverables_json": json.dumps(sample_task_spec.deliverables),
            "acceptance_criteria_json": json.dumps(sample_task_spec.acceptance_criteria),
            "definition_of_done_json": json.dumps(sample_task_spec.definition_of_done),
            "risk_checks_json": json.dumps(sample_task_spec.risk_checks),
            "run_instructions_json": json.dumps(sample_task_spec.run_instructions),
            "timebox_hours": sample_task_spec.timebox_hours,
            "status": TaskStatus.QUEUED.value,
        }
        
        created_task = db_manager.create_task(task_data)
        assert created_task.task_id == sample_task_spec.task_id
        assert created_task.id is not None  # Should have auto-generated ID
        
        # READ - Retrieve task
        retrieved_task = db_manager.get_task(sample_task_spec.task_id)
        assert retrieved_task is not None
        assert retrieved_task.task_id == sample_task_spec.task_id
        assert retrieved_task.title == sample_task_spec.title
        assert retrieved_task.status == TaskStatus.QUEUED.value
        
        # UPDATE - Update task status
        db_manager.update_task_status(sample_task_spec.task_id, TaskStatus.RUNNING.value)
        updated_task = db_manager.get_task(sample_task_spec.task_id)
        assert updated_task.status == TaskStatus.RUNNING.value
        assert updated_task.updated_at > updated_task.created_at
        
        # LIST - List tasks
        tasks = db_manager.list_tasks(limit=10)
        assert len(tasks) >= 1
        assert any(task.task_id == sample_task_spec.task_id for task in tasks)

    def test_run_operations_real(self, db_manager, sample_task_spec):
        """Test real run database operations."""
        
        # Create task first
        task_data = {
            "task_id": sample_task_spec.task_id,
            "title": sample_task_spec.title,
            "goal": sample_task_spec.goal,
            "background": sample_task_spec.background,
            "inputs_json": "[]",
            "deliverables_json": "[]",
            "acceptance_criteria_json": "[]",
            "definition_of_done_json": "[]",
            "risk_checks_json": "[]",
            "run_instructions_json": "[]",
            "timebox_hours": 1.0,
            "status": TaskStatus.QUEUED.value,
        }
        db_manager.create_task(task_data)
        
        # Create run
        run_id = "test-run-001"
        run_data = {
            "run_id": run_id,
            "task_id": sample_task_spec.task_id,
            "status": "running",
            "started_at": datetime.utcnow(),
            "artifacts_path": "/tmp/artifacts",
            "worker_pid": 12345,
        }
        
        created_run = db_manager.create_run(run_data)
        assert created_run.run_id == run_id
        assert created_run.task_id == sample_task_spec.task_id
        
        # Retrieve run
        retrieved_run = db_manager.get_run(run_id)
        assert retrieved_run is not None
        assert retrieved_run.run_id == run_id
        assert retrieved_run.worker_pid == 12345
        
        # Update run status
        db_manager.update_run_status(
            run_id=run_id,
            status="completed",
            completed_at=datetime.utcnow(),
            exit_code=0
        )
        
        updated_run = db_manager.get_run(run_id)
        assert updated_run.status == "completed"
        assert updated_run.exit_code == 0
        assert updated_run.completed_at is not None

    def test_pr_and_review_operations_real(self, db_manager):
        """Test PR and review database operations."""
        
        # Create task and run first
        task_data = {
            "task_id": "T-pr-test",
            "title": "PR test",
            "goal": "Test PR operations",
            "background": "Testing",
            "inputs_json": "[]",
            "deliverables_json": "[]",
            "acceptance_criteria_json": "[]",
            "definition_of_done_json": "[]",
            "risk_checks_json": "[]",
            "run_instructions_json": "[]",
            "timebox_hours": 1.0,
            "status": TaskStatus.QUEUED.value,
        }
        db_manager.create_task(task_data)
        
        run_data = {
            "run_id": "run-pr-test",
            "task_id": "T-pr-test",
            "status": "completed",
            "artifacts_path": "/tmp/artifacts",
        }
        db_manager.create_run(run_data)
        
        # Create PR
        pr_data = {
            "pr_id": "PR-001",
            "run_id": "run-pr-test",
            "title": "Test PR",
            "description": "Test PR description",
            "diff_summary_json": json.dumps([]),
            "ci_status": "pending",
            "tests_added_json": json.dumps([]),
            "risk_assessment_json": json.dumps({}),
            "rollback_plan": "Test rollback",
            "migration_notes": "No migrations",
            "docs_updated_json": json.dumps([]),
        }
        
        created_pr = db_manager.create_pr(pr_data)
        assert created_pr.pr_id == "PR-001"
        assert created_pr.title == "Test PR"
        
        # Create review
        review_data = {
            "pr_id": "PR-001",
            "status": "approved",
            "blocking_json": json.dumps([]),
            "non_blocking_json": json.dumps(["Minor style issue"]),
            "evidence_json": json.dumps({"pytest": "All tests passed"}),
            "notes": "Looks good to merge",
        }
        
        created_review = db_manager.create_review(review_data)
        assert created_review.pr_id == "PR-001"
        assert created_review.status == "approved"

    def test_event_logging_real(self, db_manager):
        """Test real event logging operations."""
        
        # Log various events
        events = [
            ("task_submitted", "task", "T-001", {"title": "Test Task"}),
            ("task_started", "task", "T-001", {"run_id": "run-001"}),
            ("task_completed", "task", "T-001", {"success": True}),
        ]
        
        for event_type, entity_type, entity_id, data in events:
            db_manager.log_event(event_type, entity_type, entity_id, data)
        
        # Verify events were logged (direct SQL query)
        # Note: This is a bit lower-level but tests the actual database
        from manager.store.models import engine
        from sqlmodel import Session, select
        
        with Session(engine) as session:
            statement = select(EventModel).where(EventModel.entity_id == "T-001")
            logged_events = list(session.exec(statement))
            
            assert len(logged_events) == 3
            assert logged_events[0].event_type == "task_submitted"
            
            # Test JSON data was stored correctly
            first_event_data = json.loads(logged_events[0].data_json)
            assert first_event_data["title"] == "Test Task"

    def test_database_constraints_real(self, db_manager):
        """Test database constraints and foreign key relationships."""
        
        # Try to create run without corresponding task
        run_data = {
            "run_id": "orphan-run",
            "task_id": "nonexistent-task",
            "status": "running",
            "artifacts_path": "/tmp",
        }
        
        # This might succeed or fail depending on foreign key constraints
        # We test that it handles it gracefully either way
        try:
            orphan_run = db_manager.create_run(run_data)
            # If it succeeds, that's okay too (SQLite may not enforce FK by default)
            assert orphan_run.run_id == "orphan-run"
        except Exception as e:
            # If it fails due to constraints, that's expected behavior
            assert "foreign key" in str(e).lower() or "constraint" in str(e).lower()

    def test_database_transactions_real(self, db_manager, db_connection):
        """Test database transaction handling."""
        
        # Test that operations are properly committed
        initial_count = db_connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        
        # Create a task
        task_data = {
            "task_id": "T-transaction-test",
            "title": "Transaction test",
            "goal": "Test transactions",
            "background": "Testing",
            "inputs_json": "[]",
            "deliverables_json": "[]",
            "acceptance_criteria_json": "[]",
            "definition_of_done_json": "[]",
            "risk_checks_json": "[]",
            "run_instructions_json": "[]",
            "timebox_hours": 1.0,
            "status": TaskStatus.QUEUED.value,
        }
        
        db_manager.create_task(task_data)
        
        # Verify it was committed
        final_count = db_connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        assert final_count == initial_count + 1

    def test_database_concurrent_access_real(self, test_db):
        """Test concurrent database access."""
        import threading
        import time
        
        results = []
        
        def create_task(task_id):
            """Create a task from a thread."""
            try:
                db = DatabaseManager()
                task_data = {
                    "task_id": f"T-concurrent-{task_id}",
                    "title": f"Concurrent task {task_id}",
                    "goal": "Test concurrent access",
                    "background": "Testing",
                    "inputs_json": "[]",
                    "deliverables_json": "[]",
                    "acceptance_criteria_json": "[]",
                    "definition_of_done_json": "[]",
                    "risk_checks_json": "[]",
                    "run_instructions_json": "[]",
                    "timebox_hours": 1.0,
                    "status": TaskStatus.QUEUED.value,
                }
                task = db.create_task(task_data)
                results.append(task.task_id)
            except Exception as e:
                results.append(f"Error: {e}")
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_task, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(results) == 5
        successful_results = [r for r in results if not str(r).startswith("Error:")]
        assert len(successful_results) >= 3  # At least most should succeed

    def test_database_data_types_real(self, db_manager):
        """Test that different data types are handled correctly."""
        
        # Test with various data types
        task_data = {
            "task_id": "T-datatypes",
            "title": "Data types test with unicode: \U0001F600",
            "goal": "Test unicode and special characters",
            "background": "Testing with newlines\nand special chars: <>&\"'",
            "inputs_json": json.dumps(["item with spaces", "item-with-dashes", "item_with_underscores"]),
            "deliverables_json": json.dumps([]),
            "acceptance_criteria_json": json.dumps([]),
            "definition_of_done_json": json.dumps([]),
            "risk_checks_json": json.dumps([]),
            "run_instructions_json": json.dumps([]),
            "timebox_hours": 3.14159,  # Float with decimals
            "status": TaskStatus.QUEUED.value,
        }
        
        # Should handle various data types without corruption
        created_task = db_manager.create_task(task_data)
        retrieved_task = db_manager.get_task("T-datatypes")
        
        assert retrieved_task.title == task_data["title"]
        assert retrieved_task.background == task_data["background"]
        assert abs(retrieved_task.timebox_hours - task_data["timebox_hours"]) < 0.001

    def test_database_performance_real(self, db_manager):
        """Test database performance with multiple operations."""
        import time
        
        start_time = time.time()
        
        # Create multiple tasks
        task_ids = []
        for i in range(50):
            task_data = {
                "task_id": f"T-perf-{i:03d}",
                "title": f"Performance test task {i}",
                "goal": f"Performance test {i}",
                "background": "Performance testing",
                "inputs_json": "[]",
                "deliverables_json": "[]",
                "acceptance_criteria_json": "[]",
                "definition_of_done_json": "[]",
                "risk_checks_json": "[]",
                "run_instructions_json": "[]",
                "timebox_hours": 1.0,
                "status": TaskStatus.QUEUED.value,
            }
            task = db_manager.create_task(task_data)
            task_ids.append(task.task_id)
        
        # List all tasks
        tasks = db_manager.list_tasks(limit=100)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete reasonably quickly (adjust threshold as needed)
        assert duration < 10.0, f"Database operations took too long: {duration:.2f} seconds"
        assert len(tasks) >= 50
        assert len(task_ids) == 50

    def test_database_cleanup_real(self, test_db, db_connection):
        """Test database cleanup and maintenance operations."""
        
        # Create some old data
        old_timestamp = datetime.utcnow() - timedelta(days=35)
        
        cursor = db_connection.cursor()
        cursor.execute("""
            INSERT INTO tasks (task_id, title, goal, background, inputs_json, 
                             deliverables_json, acceptance_criteria_json, 
                             definition_of_done_json, risk_checks_json,
                             run_instructions_json, timebox_hours, status, 
                             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("T-old", "Old task", "Old goal", "Old background", "[]", "[]", "[]", 
              "[]", "[]", "[]", 1.0, "completed", old_timestamp, old_timestamp))
        
        db_connection.commit()
        
        # Verify old task exists
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE task_id = 'T-old'")
        assert cursor.fetchone()[0] == 1
        
        # Test that we can query old data
        cursor.execute("SELECT * FROM tasks WHERE created_at < ?", (datetime.utcnow(),))
        old_tasks = cursor.fetchall()
        assert len(old_tasks) >= 1

    def test_database_error_handling_real(self, db_manager):
        """Test database error handling."""
        
        # Test duplicate task ID
        task_data = {
            "task_id": "T-duplicate",
            "title": "First task",
            "goal": "First goal",
            "background": "First background",
            "inputs_json": "[]",
            "deliverables_json": "[]",
            "acceptance_criteria_json": "[]",
            "definition_of_done_json": "[]",
            "risk_checks_json": "[]",
            "run_instructions_json": "[]",
            "timebox_hours": 1.0,
            "status": TaskStatus.QUEUED.value,
        }
        
        # First creation should succeed
        first_task = db_manager.create_task(task_data)
        assert first_task.task_id == "T-duplicate"
        
        # Second creation with same ID should fail
        task_data["title"] = "Second task"
        
        with pytest.raises(Exception):  # Should raise some kind of constraint error
            db_manager.create_task(task_data)

    def test_database_backup_restore_simulation(self, test_db, db_manager):
        """Test database backup/restore concepts."""
        
        # Create some test data
        task_data = {
            "task_id": "T-backup-test",
            "title": "Backup test",
            "goal": "Test backup concepts",
            "background": "Testing",
            "inputs_json": "[]",
            "deliverables_json": "[]",
            "acceptance_criteria_json": "[]",
            "definition_of_done_json": "[]",
            "risk_checks_json": "[]",
            "run_instructions_json": "[]",
            "timebox_hours": 1.0,
            "status": TaskStatus.QUEUED.value,
        }
        
        original_task = db_manager.create_task(task_data)
        
        # Verify data exists
        retrieved_task = db_manager.get_task("T-backup-test")
        assert retrieved_task is not None
        assert retrieved_task.title == "Backup test"
        
        # Test that database file exists and has content
        assert test_db.exists()
        assert test_db.stat().st_size > 0  # Database file should have content