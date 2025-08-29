"""Unit tests for core schemas and data models."""

import pytest
from datetime import datetime

from manager.core.schemas import (
    TaskSpec,
    WorkerTaskReport,
    PullRequestProposal,
    ReviewReport,
    TaskStatus,
    ReviewStatus,
    ChangeType,
    FileChange,
    TestResults,
    Artifact,
    ArtifactType,
)


def test_task_spec_creation():
    """Test TaskSpec creation and validation."""
    task = TaskSpec(
        task_id="T-001",
        title="Test task",
        goal="Test goal",
        background="Test background",
    )
    
    assert task.task_id == "T-001"
    assert task.title == "Test task"
    assert task.goal == "Test goal"
    assert task.background == "Test background"
    
    # Check defaults
    assert task.inputs == []
    assert task.deliverables == []
    assert task.timebox_hours == 2.0
    assert "ruff+black clean" in task.definition_of_done


def test_task_spec_serialization():
    """Test TaskSpec serialization to/from dict."""
    task = TaskSpec(
        task_id="T-001",
        title="Test task",
        goal="Test goal",
        background="Test background",
        deliverables=["API", "Tests"],
        timebox_hours=3.0,
    )
    
    # Serialize to dict
    task_dict = task.model_dump()
    
    assert task_dict["task_id"] == "T-001"
    assert task_dict["deliverables"] == ["API", "Tests"]
    assert task_dict["timebox_hours"] == 3.0
    
    # Deserialize from dict
    task_copy = TaskSpec(**task_dict)
    assert task_copy.task_id == task.task_id
    assert task_copy.deliverables == task.deliverables


def test_file_change_creation():
    """Test FileChange creation."""
    change = FileChange(
        file="src/main.py",
        change_type=ChangeType.ADDED,
        reason="New implementation",
    )
    
    assert change.file == "src/main.py"
    assert change.change_type == ChangeType.ADDED
    assert change.reason == "New implementation"


def test_test_results_creation():
    """Test TestResults creation."""
    results = TestResults(
        passed=True,
        summary="All tests passed",
        coverage={"lines": 90.5, "branches": 85.0},
    )
    
    assert results.passed is True
    assert results.summary == "All tests passed"
    assert results.coverage["lines"] == 90.5


def test_worker_task_report_creation():
    """Test WorkerTaskReport creation."""
    changes = [
        FileChange(
            file="src/api.py",
            change_type=ChangeType.ADDED,
            reason="API implementation",
        ),
    ]
    
    test_results = TestResults(
        passed=True,
        summary="3 tests passed",
        coverage={"lines": 95.0},
    )
    
    artifacts = [
        Artifact(type=ArtifactType.LOG, location="/logs/test.log"),
    ]
    
    report = WorkerTaskReport(
        task_id="T-001",
        summary="Task completed successfully",
        changes=changes,
        test_results=test_results,
        artifacts=artifacts,
        proposed_pr="PR-001",
    )
    
    assert report.task_id == "T-001"
    assert len(report.changes) == 1
    assert report.changes[0].file == "src/api.py"
    assert report.test_results.passed is True
    assert len(report.artifacts) == 1


def test_pull_request_proposal_creation():
    """Test PullRequestProposal creation."""
    from manager.core.schemas import DiffSummary, RiskAssessment
    
    diff_summary = [
        DiffSummary(file="src/main.py", insertions=50, deletions=5),
    ]
    
    risk_assessment = RiskAssessment(
        breaking_change=False,
        security_notes="No security concerns",
        perf_notes="Minimal performance impact",
    )
    
    proposal = PullRequestProposal(
        pr_id="PR-001",
        title="Add new feature",
        description="This PR adds a new feature",
        diff_summary=diff_summary,
        risk_assessment=risk_assessment,
    )
    
    assert proposal.pr_id == "PR-001"
    assert proposal.title == "Add new feature"
    assert len(proposal.diff_summary) == 1
    assert proposal.risk_assessment.breaking_change is False


def test_review_report_creation():
    """Test ReviewReport creation."""
    from manager.core.schemas import ReviewEvidence
    
    evidence = ReviewEvidence(
        pytest="All tests passed",
        coverage={"lines": 90.0},
        linters="No issues found",
    )
    
    report = ReviewReport(
        pr_id="PR-001",
        status=ReviewStatus.APPROVED,
        blocking=[], 
        non_blocking=["Consider refactoring"],
        evidence=evidence,
        notes="Looks good",
    )
    
    assert report.pr_id == "PR-001"
    assert report.status == ReviewStatus.APPROVED
    assert len(report.blocking) == 0
    assert len(report.non_blocking) == 1
    assert report.evidence.pytest == "All tests passed"


def test_task_status_enum():
    """Test TaskStatus enum values."""
    assert TaskStatus.QUEUED.value == "queued"
    assert TaskStatus.RUNNING.value == "running"
    assert TaskStatus.AWAITING_REVIEW.value == "awaiting_review"
    assert TaskStatus.APPROVED.value == "approved"
    assert TaskStatus.MERGED.value == "merged"


def test_review_status_enum():
    """Test ReviewStatus enum values."""
    assert ReviewStatus.APPROVED.value == "approved"
    assert ReviewStatus.CHANGES_REQUESTED.value == "changes_requested"
    assert ReviewStatus.REJECTED.value == "rejected"


def test_change_type_enum():
    """Test ChangeType enum values."""
    assert ChangeType.ADDED.value == "added"
    assert ChangeType.MODIFIED.value == "modified" 
    assert ChangeType.REMOVED.value == "removed"


def test_artifact_type_enum():
    """Test ArtifactType enum values."""
    assert ArtifactType.LOG.value == "log"
    assert ArtifactType.SCREENSHOT.value == "screenshot"
    assert ArtifactType.ARCHIVE.value == "archive"
    assert ArtifactType.DIAGRAM.value == "diagram"


def test_task_spec_validation():
    """Test TaskSpec validation rules."""
    # Valid task
    valid_task = TaskSpec(
        task_id="T-001",
        title="Valid task",
        goal="Valid goal",
        background="Valid background",
        timebox_hours=2.0,
    )
    
    # Should not raise exception
    assert valid_task.task_id == "T-001"
    
    # Invalid timebox (negative)
    with pytest.raises(ValueError):
        TaskSpec(
            task_id="T-002",
            title="Invalid task",
            goal="Invalid goal",
            background="Invalid background",
            timebox_hours=-1.0,  # Invalid
        )


def test_schema_json_serialization():
    """Test JSON serialization of schemas."""
    import json
    
    task = TaskSpec(
        task_id="T-001",
        title="JSON test",
        goal="Test JSON serialization",
        background="Testing",
        deliverables=["output.json"],
    )
    
    # Serialize to JSON
    json_str = task.model_dump_json()
    assert isinstance(json_str, str)
    
    # Parse JSON
    parsed = json.loads(json_str)
    assert parsed["task_id"] == "T-001"
    assert parsed["deliverables"] == ["output.json"]
    
    # Deserialize from JSON
    task_copy = TaskSpec.model_validate(parsed)
    assert task_copy.task_id == task.task_id
    assert task_copy.title == task.title


def test_optional_fields():
    """Test optional fields in schemas."""
    # Minimal TaskSpec
    minimal_task = TaskSpec(
        task_id="T-minimal",
        title="Minimal",
        goal="Minimal goal",
        background="Minimal background",
    )
    
    assert minimal_task.inputs == []
    assert minimal_task.deliverables == []
    assert len(minimal_task.acceptance_criteria) == 0
    assert len(minimal_task.definition_of_done) > 0  # Has defaults
    
    # WorkerTaskReport with minimal fields
    minimal_report = WorkerTaskReport(
        task_id="T-minimal",
        summary="Minimal report",
    )
    
    assert minimal_report.changes == []
    assert minimal_report.commands_run == []
    assert minimal_report.artifacts == []
    assert minimal_report.open_issues == []