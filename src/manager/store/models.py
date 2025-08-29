"""SQLModel database models for AI Manager."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, create_engine, Session, select
from manager.config import settings


class TaskModel(SQLModel, table=True):
    """Task database model."""
    
    __tablename__ = "tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(unique=True, index=True)
    title: str
    goal: str
    background: str
    inputs_json: str = Field(default="[]")  # JSON-encoded list
    deliverables_json: str = Field(default="[]")  # JSON-encoded list
    acceptance_criteria_json: str = Field(default="[]")  # JSON-encoded list
    definition_of_done_json: str = Field(default="[]")  # JSON-encoded list
    risk_checks_json: str = Field(default="[]")  # JSON-encoded list
    run_instructions_json: str = Field(default="[]")  # JSON-encoded list
    timebox_hours: float = Field(default=2.0)
    status: str = Field(default="queued", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RunModel(SQLModel, table=True):
    """Run database model."""
    
    __tablename__ = "runs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(unique=True, index=True)
    task_id: str = Field(foreign_key="tasks.task_id", index=True)
    status: str = Field(default="pending", index=True)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    stdout_path: Optional[str] = None
    stderr_path: Optional[str] = None
    artifacts_path: str
    worker_pid: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ArtifactModel(SQLModel, table=True):
    """Artifact database model."""
    
    __tablename__ = "artifacts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: str = Field(foreign_key="runs.run_id", index=True)
    artifact_type: str
    name: str
    path: str
    size_bytes: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PRModel(SQLModel, table=True):
    """Pull Request database model."""
    
    __tablename__ = "prs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    pr_id: str = Field(unique=True, index=True)
    run_id: str = Field(foreign_key="runs.run_id", index=True)
    title: str
    description: str
    diff_summary_json: str = Field(default="[]")  # JSON-encoded list
    ci_status: str = Field(default="pending")
    tests_added_json: str = Field(default="[]")  # JSON-encoded list
    risk_assessment_json: str = Field(default="{}")  # JSON-encoded dict
    rollback_plan: str = Field(default="")
    migration_notes: str = Field(default="")
    docs_updated_json: str = Field(default="[]")  # JSON-encoded list
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewModel(SQLModel, table=True):
    """Review database model."""
    
    __tablename__ = "reviews"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    pr_id: str = Field(foreign_key="prs.pr_id", index=True)
    status: str = Field(index=True)
    blocking_json: str = Field(default="[]")  # JSON-encoded list
    non_blocking_json: str = Field(default="[]")  # JSON-encoded list
    evidence_json: str = Field(default="{}")  # JSON-encoded dict
    notes: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EventModel(SQLModel, table=True):
    """Event database model for audit log."""
    
    __tablename__ = "events"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    event_type: str = Field(index=True)
    entity_type: str  # "task", "run", "pr", "review"
    entity_id: str = Field(index=True)
    data_json: str = Field(default="{}")  # JSON-encoded event data
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


# Database setup
engine = create_engine(settings.manager_db_url, echo=settings.dev_mode)


def create_db_and_tables():
    """Create database and tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session


class DatabaseManager:
    """Database operations manager."""
    
    @staticmethod
    def create_task(task_data: dict) -> TaskModel:
        """Create a new task."""
        with Session(engine) as session:
            task = TaskModel(**task_data)
            session.add(task)
            session.commit()
            session.refresh(task)
            return task
    
    @staticmethod
    def get_task(task_id: str) -> Optional[TaskModel]:
        """Get task by ID."""
        with Session(engine) as session:
            statement = select(TaskModel).where(TaskModel.task_id == task_id)
            return session.exec(statement).first()
    
    @staticmethod
    def update_task_status(task_id: str, status: str) -> None:
        """Update task status."""
        with Session(engine) as session:
            statement = select(TaskModel).where(TaskModel.task_id == task_id)
            task = session.exec(statement).first()
            if task:
                task.status = status
                task.updated_at = datetime.utcnow()
                session.add(task)
                session.commit()
    
    @staticmethod
    def list_tasks(limit: int = 100, offset: int = 0) -> list[TaskModel]:
        """List tasks."""
        with Session(engine) as session:
            statement = select(TaskModel).offset(offset).limit(limit).order_by(
                TaskModel.created_at.desc()
            )
            return list(session.exec(statement).all())
    
    @staticmethod
    def create_run(run_data: dict) -> RunModel:
        """Create a new run."""
        with Session(engine) as session:
            run = RunModel(**run_data)
            session.add(run)
            session.commit()
            session.refresh(run)
            return run
    
    @staticmethod
    def get_run(run_id: str) -> Optional[RunModel]:
        """Get run by ID."""
        with Session(engine) as session:
            statement = select(RunModel).where(RunModel.run_id == run_id)
            return session.exec(statement).first()
    
    @staticmethod
    def update_run_status(run_id: str, status: str, **kwargs) -> None:
        """Update run status and other fields."""
        with Session(engine) as session:
            statement = select(RunModel).where(RunModel.run_id == run_id)
            run = session.exec(statement).first()
            if run:
                run.status = status
                for key, value in kwargs.items():
                    if hasattr(run, key):
                        setattr(run, key, value)
                session.add(run)
                session.commit()
    
    @staticmethod
    def create_pr(pr_data: dict) -> PRModel:
        """Create a new PR."""
        with Session(engine) as session:
            pr = PRModel(**pr_data)
            session.add(pr)
            session.commit()
            session.refresh(pr)
            return pr
    
    @staticmethod
    def create_review(review_data: dict) -> ReviewModel:
        """Create a new review."""
        with Session(engine) as session:
            review = ReviewModel(**review_data)
            session.add(review)
            session.commit()
            session.refresh(review)
            return review
    
    @staticmethod
    def log_event(event_type: str, entity_type: str, entity_id: str, data: dict) -> None:
        """Log an event."""
        import json
        with Session(engine) as session:
            event = EventModel(
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                data_json=json.dumps(data),
            )
            session.add(event)
            session.commit()
    
    @staticmethod
    def list_tasks_advanced(
        status=None,
        search=None,
        created_after=None,
        created_before=None,
        sort_by="created_at",
        sort_order="desc"
    ) -> list[TaskModel]:
        """List tasks with advanced filtering and sorting."""
        from sqlalchemy import or_, and_
        
        with Session(engine) as session:
            # Build base query
            query = select(TaskModel)
            conditions = []
            
            # Status filter
            if status:
                conditions.append(TaskModel.status == status.value)
            
            # Search filter (search in task_id, title, goal)
            if search:
                search_pattern = f"%{search}%"
                conditions.append(or_(
                    TaskModel.task_id.ilike(search_pattern),
                    TaskModel.title.ilike(search_pattern),
                    TaskModel.goal.ilike(search_pattern)
                ))
            
            # Date filters
            if created_after:
                conditions.append(TaskModel.created_at >= created_after)
            
            if created_before:
                conditions.append(TaskModel.created_at <= created_before)
            
            # Apply conditions
            if conditions:
                query = query.where(and_(*conditions))
            
            # Apply sorting
            sort_column = getattr(TaskModel, sort_by)
            if sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
            
            return list(session.exec(query).all())
    
    @staticmethod
    def update_task_status(task_id: str, status: str) -> bool:
        """Update task status."""
        with Session(engine) as session:
            task = session.get(TaskModel, task_id)
            if task:
                task.status = status
                task.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
    
    @staticmethod
    def list_runs_for_task(task_id: str) -> list[RunModel]:
        """List all runs for a specific task."""
        with Session(engine) as session:
            statement = select(RunModel).where(RunModel.task_id == task_id)
            return list(session.exec(statement).all())