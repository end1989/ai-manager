"""Core data schemas for AI Manager tasks, reports, and reviews."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status enumeration."""
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"
    MERGED = "merged"


class ChangeType(str, Enum):
    """File change type enumeration."""
    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"


class ReviewStatus(str, Enum):
    """Review status enumeration."""
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"


class ArtifactType(str, Enum):
    """Artifact type enumeration."""
    LOG = "log"
    SCREENSHOT = "screenshot"
    ARCHIVE = "archive"
    DIAGRAM = "diagram"


class TaskSpec(BaseModel):
    """Task specification schema."""
    task_id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Short imperative title")
    goal: str = Field(..., description="Plain-English goal for the Manager to fulfill")
    background: str = Field(..., description="Why this matters / constraints / non-goals")
    inputs: List[str] = Field(default_factory=list, description="Facts, files, prior PRs, APIs")
    deliverables: List[str] = Field(
        default_factory=list, description="Code files or diffs, tests, docs"
    )
    acceptance_criteria: List[str] = Field(
        default_factory=list, description="Measurable behaviors and test expectations"
    )
    definition_of_done: List[str] = Field(
        default_factory=lambda: [
            "ruff+black clean",
            "mypy passes",
            "pytest passes",
            "coverage >= 85% on changed lines",
            "docs updated if behavior changed",
        ],
        description="Quality gates",
    )
    risk_checks: List[str] = Field(
        default_factory=lambda: [
            "performance risks?",
            "security validation?",
            "edge cases & failure paths?",
        ],
        description="Risk assessment items",
    )
    run_instructions: List[str] = Field(
        default_factory=list, description="Commands to run app/tests locally"
    )
    timebox_hours: float = Field(default=2.0, description="Time limit for task execution")


class FileChange(BaseModel):
    """File change description."""
    file: str = Field(..., description="File path")
    change_type: ChangeType = Field(..., description="Type of change")
    reason: str = Field(..., description="Brief explanation of change")


class TestResults(BaseModel):
    """Test execution results."""
    passed: bool = Field(..., description="Overall test status")
    summary: str = Field(..., description="Test output summary")
    coverage: Dict[str, float] = Field(
        default_factory=dict, description="Coverage metrics (lines, branches)"
    )


class Artifact(BaseModel):
    """Task artifact description."""
    type: ArtifactType = Field(..., description="Artifact type")
    location: str = Field(..., description="Artifact path or inline content")


class OpenIssue(BaseModel):
    """Open issue description."""
    desc: str = Field(..., description="Known gap description")
    mitigation: str = Field(..., description="Next step or mitigation")


class WorkerTaskReport(BaseModel):
    """Worker task execution report."""
    task_id: str = Field(..., description="Task identifier")
    summary: str = Field(..., description="What was done and why")
    changes: List[FileChange] = Field(default_factory=list, description="File changes made")
    commands_run: List[str] = Field(default_factory=list, description="Commands executed")
    test_results: Optional[TestResults] = Field(None, description="Test execution results")
    artifacts: List[Artifact] = Field(default_factory=list, description="Generated artifacts")
    open_issues: List[OpenIssue] = Field(default_factory=list, description="Known gaps")
    proposed_pr: Optional[str] = Field(None, description="PR proposal ID")


class DiffSummary(BaseModel):
    """Diff summary for a file."""
    file: str = Field(..., description="File path")
    insertions: int = Field(..., description="Lines added")
    deletions: int = Field(..., description="Lines removed")


class RiskAssessment(BaseModel):
    """Risk assessment for changes."""
    breaking_change: bool = Field(default=False, description="Is this a breaking change")
    security_notes: str = Field(default="", description="Security considerations")
    perf_notes: str = Field(default="", description="Performance considerations")


class PullRequestProposal(BaseModel):
    """Pull request proposal schema."""
    pr_id: str = Field(..., description="PR identifier")
    title: str = Field(..., description="Concise change title")
    description: str = Field(..., description="What/why, alternatives, tradeoffs")
    diff_summary: List[DiffSummary] = Field(default_factory=list, description="File changes")
    ci_status: str = Field(default="pending", description="CI status")
    tests_added: List[str] = Field(default_factory=list, description="Tests added")
    risk_assessment: RiskAssessment = Field(
        default_factory=RiskAssessment, description="Risk assessment"
    )
    rollback_plan: str = Field(default="", description="How to revert safely")
    migration_notes: str = Field(default="", description="Schema/config changes")
    docs_updated: List[str] = Field(default_factory=list, description="Documentation updated")


class ReviewEvidence(BaseModel):
    """Review evidence collection."""
    pytest: str = Field(default="", description="Test execution summary")
    coverage: Dict[str, float] = Field(default_factory=dict, description="Coverage metrics")
    linters: str = Field(default="", description="Linter output summaries")
    logs: str = Field(default="", description="Key run logs")


class ReviewReport(BaseModel):
    """Review report schema."""
    pr_id: str = Field(..., description="PR identifier")
    status: ReviewStatus = Field(..., description="Review status")
    blocking: List[str] = Field(
        default_factory=list, description="Failing checks with file:line references"
    )
    non_blocking: List[str] = Field(default_factory=list, description="Refactors or docs nits")
    evidence: ReviewEvidence = Field(
        default_factory=ReviewEvidence, description="Evidence collection"
    )
    notes: str = Field(default="", description="Rationale for decision")


class TaskSubmission(BaseModel):
    """Task submission request."""
    spec: TaskSpec = Field(..., description="Task specification")


class TaskResponse(BaseModel):
    """Task response."""
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class RunInfo(BaseModel):
    """Run information."""
    run_id: str = Field(..., description="Run identifier")
    task_id: str = Field(..., description="Associated task ID")
    status: str = Field(..., description="Run status")
    started_at: Optional[datetime] = Field(None, description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    artifacts_path: str = Field(..., description="Path to run artifacts")


class TaskListResponse(BaseModel):
    """Task list response."""
    tasks: List[TaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total task count")


class RunListResponse(BaseModel):
    """Run list response."""
    runs: List[RunInfo] = Field(..., description="List of runs")
    total: int = Field(..., description="Total run count")