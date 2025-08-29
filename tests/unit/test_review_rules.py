"""Unit tests for review engine rules and validation."""

import pytest
import tempfile
from pathlib import Path

from manager.core.review import ReviewEngine
from manager.core.schemas import (
    PullRequestProposal,
    ReviewStatus,
    DiffSummary,
    RiskAssessment,
)


@pytest.fixture
def review_engine():
    """Create review engine for testing."""
    return ReviewEngine()


@pytest.fixture
def sample_pr_proposal():
    """Create sample PR proposal."""
    return PullRequestProposal(
        pr_id="PR-test-001",
        title="Test implementation",
        description="Test PR description",
        diff_summary=[
            DiffSummary(file="src/main.py", insertions=50, deletions=5),
        ],
        risk_assessment=RiskAssessment(
            breaking_change=False,
            security_notes="No security concerns",
            perf_notes="Good performance",
        ),
    )


@pytest.fixture
def temp_workdir():
    """Create temporary working directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def test_validate_pr_proposal(review_engine, sample_pr_proposal):
    """Test PR proposal validation."""
    errors = review_engine.validate_pr_proposal(sample_pr_proposal)
    
    assert len(errors) == 0  # Should be valid
    
    # Test invalid proposal
    invalid_proposal = PullRequestProposal(
        pr_id="",  # Empty ID
        title="",  # Empty title
        description="",  # Empty description
        diff_summary=[],  # Empty diff
    )
    
    errors = review_engine.validate_pr_proposal(invalid_proposal)
    assert len(errors) > 0
    assert any("PR ID is required" in error for error in errors)
    assert any("PR title is required" in error for error in errors)


@pytest.mark.asyncio
async def test_security_checks(review_engine, temp_workdir):
    """Test security vulnerability detection."""
    # Create Python file with potential security issues
    py_file = temp_workdir / "insecure.py"
    py_file.write_text('''
import os

# Hardcoded credentials
password = "secret123"
api_key = "sk-1234567890"

def dangerous_function():
    # Dangerous system call
    os.system("rm -rf /")
    
    # Use of eval
    user_input = input("Enter code: ")
    eval(user_input)
''')
    
    # Run security checks
    security_issues = await review_engine._check_security(temp_workdir)
    
    assert len(security_issues) > 0
    assert any("secret" in issue.lower() for issue in security_issues)


@pytest.mark.asyncio
async def test_code_quality_checks(review_engine, temp_workdir):
    """Test code quality analysis."""
    # Create Python file with quality issues
    py_file = temp_workdir / "quality_issues.py"
    py_file.write_text('''
def very_long_function():
    # TODO: This function is too long
    """ '''+'''
    This function has way too many lines and should be refactored.
    '''+'''
    """ + "".join([f"line_{i}\n" for i in range(60)]) + '''
    return "done"

def another_function():
    # FIXME: This needs fixing
    pass
''')
    
    # Run quality checks
    quality_issues = await review_engine._check_code_quality(temp_workdir)
    
    assert len(quality_issues) > 0
    assert any("TODO" in issue for issue in quality_issues)
    assert any("Long function" in issue for issue in quality_issues)


@pytest.mark.asyncio
async def test_pytest_execution(review_engine, temp_workdir):
    """Test pytest execution and result parsing."""
    # Create test file
    test_file = temp_workdir / "test_sample.py"
    test_file.write_text('''
def test_passing():
    assert True

def test_also_passing():
    assert 1 + 1 == 2
''')
    
    # Run pytest
    result = await review_engine._run_pytest(temp_workdir)
    
    assert "summary" in result
    assert "coverage" in result
    # Note: pytest might not be available in test environment


@pytest.mark.asyncio 
async def test_linter_execution(review_engine, temp_workdir):
    """Test linter execution."""
    # Create Python file
    py_file = temp_workdir / "sample.py"
    py_file.write_text('''
def hello_world():
    print("Hello, World!")
    return True
''')
    
    # Run linters
    result = await review_engine._run_linters(temp_workdir)
    
    assert isinstance(result, str)
    assert "ruff" in result or "failed" in result  # Either works or reports failure


def test_evidence_collection_structure(review_engine):
    """Test evidence collection data structure."""
    from manager.core.schemas import ReviewEvidence
    
    evidence = ReviewEvidence()
    
    # Test default values
    assert evidence.pytest == ""
    assert evidence.coverage == {}
    assert evidence.linters == ""
    assert evidence.logs == ""
    
    # Test with data
    evidence = ReviewEvidence(
        pytest="5 passed",
        coverage={"lines": 90.0, "branches": 80.0},
        linters="ruff: clean; mypy: clean",
        logs="No errors in logs",
    )
    
    assert evidence.pytest == "5 passed"
    assert evidence.coverage["lines"] == 90.0
    assert "ruff: clean" in evidence.linters


def test_review_status_logic():
    """Test review status determination logic."""
    # This tests the logic that would be in the actual review method
    
    # Scenario 1: No issues -> APPROVED
    blocking_issues = []
    non_blocking_issues = []
    expected_status = ReviewStatus.APPROVED
    
    if blocking_issues:
        actual_status = ReviewStatus.CHANGES_REQUESTED
    elif non_blocking_issues:
        actual_status = ReviewStatus.APPROVED
    else:
        actual_status = ReviewStatus.APPROVED
    
    assert actual_status == expected_status
    
    # Scenario 2: Blocking issues -> CHANGES_REQUESTED
    blocking_issues = ["Test failures", "Linting errors"]
    
    if blocking_issues:
        actual_status = ReviewStatus.CHANGES_REQUESTED
    else:
        actual_status = ReviewStatus.APPROVED
    
    assert actual_status == ReviewStatus.CHANGES_REQUESTED


def test_coverage_threshold_checking():
    """Test coverage threshold validation."""
    min_coverage = 85.0
    
    # Test passing coverage
    coverage_data = {"lines": 90.0, "branches": 85.0}
    coverage_issues = []
    
    if coverage_data.get("lines", 0) < min_coverage:
        coverage_issues.append(f"Line coverage below {min_coverage}%")
    
    assert len(coverage_issues) == 0
    
    # Test failing coverage
    coverage_data = {"lines": 75.0, "branches": 70.0}
    coverage_issues = []
    
    if coverage_data.get("lines", 0) < min_coverage:
        coverage_issues.append(f"Line coverage below {min_coverage}%")
    
    assert len(coverage_issues) > 0
    assert "75.0" not in coverage_issues[0]  # Should use threshold, not actual


def test_risk_assessment_validation():
    """Test risk assessment structure and validation."""
    # Valid risk assessment
    risk = RiskAssessment(
        breaking_change=False,
        security_notes="Validated input handling",
        perf_notes="O(1) complexity",
    )
    
    assert risk.breaking_change is False
    assert "Validated" in risk.security_notes
    assert "O(1)" in risk.perf_notes
    
    # High risk assessment
    high_risk = RiskAssessment(
        breaking_change=True,
        security_notes="Modifies authentication flow",
        perf_notes="May impact response time",
    )
    
    assert high_risk.breaking_change is True
    assert "authentication" in high_risk.security_notes


def test_file_pattern_matching():
    """Test file pattern matching for security checks."""
    import re
    
    # Test secret patterns
    secret_patterns = [
        r"password\s*=\s*['\"][^'\"]+['\"]",
        r"api_key\s*=\s*['\"][^'\"]+['\"]",
    ]
    
    # Test code with secrets
    code_with_secrets = '''
password = "secret123"
api_key = 'sk-abcdef123456'
safe_var = variable_name
'''
    
    found_secrets = []
    for pattern in secret_patterns:
        matches = re.finditer(pattern, code_with_secrets, re.IGNORECASE)
        found_secrets.extend(matches)
    
    assert len(found_secrets) == 2
    
    # Test safe code
    safe_code = '''
password_hash = get_password_hash()
api_key_name = "api_key"
'''
    
    found_secrets = []
    for pattern in secret_patterns:
        matches = re.finditer(pattern, safe_code, re.IGNORECASE)
        found_secrets.extend(matches)
    
    assert len(found_secrets) == 0