"""Test the AI-powered review and approval workflow system."""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from manager.core.review import ReviewEngine, AIReviewResult, ReviewDecision
from manager.core.schemas import (
    TaskSpec,
    WorkerTaskReport,
    PullRequestProposal,
    FileChange,
    ChangeType,
    RiskAssessment,
    DiffSummary
)


async def test_review_system():
    """Test the AI-powered review system."""
    
    print("Testing AI-Powered Review & Approval System")
    print("=" * 50)
    
    # Test 1: Initialize review engine
    print("\n[1] Testing ReviewEngine initialization...")
    try:
        review_engine = ReviewEngine()
        print(f"[OK] Review engine initialized with AI providers")
        
        # Check approval workflow
        workflow = review_engine.approval_workflow
        print(f"[OK] Approval workflow initialized")
        print(f"  - Auto-approve threshold: {workflow.review_rules['auto_approve_threshold']}")
        print(f"  - Human review threshold: {workflow.review_rules['require_human_review_threshold']}")
        
    except Exception as e:
        print(f"[ERROR] Review engine initialization failed: {e}")
        return False
    
    # Test 2: Create sample PR data for review
    print("\n[2] Creating sample PR data...")
    try:
        # Sample task spec
        task_spec = TaskSpec(
            task_id="REV-TEST-001",
            title="Calculator Module with AI Review",
            goal="Create calculator with comprehensive review",
            background="Testing the review system",
            deliverables=["calculator.py", "test_calculator.py"],
            timebox_hours=2.0
        )
        
        # Sample worker report
        worker_report = WorkerTaskReport(
            task_id="REV-TEST-001",
            summary="Calculator implementation completed",
            changes=[
                FileChange(
                    file="calculator.py",
                    change_type=ChangeType.ADDED,
                    reason="Core calculator implementation"
                ),
                FileChange(
                    file="test_calculator.py", 
                    change_type=ChangeType.ADDED,
                    reason="Comprehensive test suite"
                )
            ],
            test_results=None,
            artifacts=[],
            open_issues=[],
            proposed_pr="PR-REV-TEST-001"
        )
        
        # Sample PR proposal
        pr_proposal = PullRequestProposal(
            pr_id="PR-REV-TEST-001",
            title="Add Calculator Module",
            description="Implements basic calculator functionality with comprehensive tests",
            diff_summary=[
                DiffSummary(file="calculator.py", insertions=150, deletions=0),
                DiffSummary(file="test_calculator.py", insertions=200, deletions=0)
            ],
            ci_status="pending",
            tests_added=["test_calculator.py"],
            risk_assessment=RiskAssessment(
                breaking_change=False,
                security_notes="No security concerns",
                perf_notes="Good performance practices"
            ),
            rollback_plan="Remove added files",
            migration_notes="No migrations required",
            docs_updated=[]
        )
        
        print(f"[OK] Sample PR data created")
        print(f"  - Task: {task_spec.title}")
        print(f"  - Files: {len(worker_report.changes)}")
        print(f"  - PR: {pr_proposal.pr_id}")
        
    except Exception as e:
        print(f"[ERROR] Sample data creation failed: {e}")
        return False
    
    # Test 3: Test AI review process
    print("\n[3] Testing AI-powered review...")
    try:
        # Create temporary workdir with sample code
        with tempfile.TemporaryDirectory() as temp_dir:
            workdir = Path(temp_dir)
            
            # Create sample calculator.py
            calc_code = '''"""Simple calculator module."""

def add(a, b):
    """Add two numbers."""
    return a + b

def subtract(a, b): 
    """Subtract b from a."""
    return a - b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def divide(a, b):
    """Divide a by b."""
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b
'''
            
            calc_file = workdir / "calculator.py"
            calc_file.write_text(calc_code)
            
            # Create sample test file
            test_code = '''"""Tests for calculator module."""
import pytest
from calculator import add, subtract, multiply, divide

def test_add():
    assert add(2, 3) == 5

def test_subtract():
    assert subtract(5, 3) == 2

def test_multiply():
    assert multiply(3, 4) == 12

def test_divide():
    assert divide(10, 2) == 5

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)
'''
            
            test_file = workdir / "test_calculator.py"
            test_file.write_text(test_code)
            
            print(f"[OK] Sample code created in {workdir}")
            
            # Perform AI review
            ai_result, review_id = await review_engine.ai_review_pr(
                pr_proposal, worker_report, workdir
            )
            
            print(f"[OK] AI review completed")
            print(f"  - Review ID: {review_id}")
            print(f"  - Decision: {ai_result.decision}")
            print(f"  - Quality Score: {ai_result.quality_score}/100")
            print(f"  - Quality Grade: {ai_result.quality_grade}")
            print(f"  - Maintainability: {ai_result.maintainability_score}/100")
            print(f"  - Test Coverage: {ai_result.test_coverage_assessment}")
            print(f"  - Issues: {len(ai_result.issues)}")
            print(f"  - Security Concerns: {len(ai_result.security_concerns)}")
            print(f"  - Suggestions: {len(ai_result.suggestions)}")
            
            if ai_result.reviewer_comments:
                print(f"  - Review Summary: {len(ai_result.reviewer_comments)} chars")
        
    except Exception as e:
        print(f"[ERROR] AI review failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Test human workflow management
    print("\n[4] Testing human workflow management...")
    try:
        # Get pending reviews
        pending = review_engine.get_pending_reviews()
        print(f"[OK] Pending reviews: {len(pending)}")
        
        if pending:
            review = pending[0]
            review_id = review.get("pr_id", "test-review")  # Use PR ID as fallback
            
            # Test approval
            success = review_engine.approve_review(review_id, "test-reviewer", "Looks good!")
            print(f"[OK] Approval test: {success}")
            
        # Get review stats
        stats = review_engine.get_review_stats()
        print(f"[OK] Review stats retrieved")
        print(f"  - Total: {stats['total']}")
        print(f"  - Approved: {stats['approved']}")
        print(f"  - Rejected: {stats['rejected']}")
        print(f"  - Approval Rate: {stats['approval_rate']}%")
        print(f"  - Pending: {stats['pending']}")
        
    except Exception as e:
        print(f"[ERROR] Workflow management failed: {e}")
        return False
    
    # Test 5: Test review rules and decision logic
    print("\n[5] Testing review rules and decision logic...")
    try:
        # Create a simple AI result to test rules
        test_result = AIReviewResult()
        test_result.quality_score = 90  # High quality
        test_result.security_concerns = []  # No security issues
        
        # Apply rules
        final_result = review_engine._apply_review_rules(test_result, pr_proposal, worker_report)
        
        print(f"[OK] Review rules applied")
        print(f"  - Input score: 90")
        print(f"  - Final decision: {final_result.decision}")
        print(f"  - Conditions: {final_result.approval_conditions}")
        
        # Test low quality score
        test_result.quality_score = 40  # Low quality
        final_result = review_engine._apply_review_rules(test_result, pr_proposal, worker_report)
        print(f"  - Low quality decision: {final_result.decision}")
        
    except Exception as e:
        print(f"[ERROR] Rules testing failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_review_system())
        print(f"\n{'='*50}")
        print(f"Review System Test: {'PASSED' if result else 'FAILED'}")
        
        if result:
            print(f"\n[SUCCESS] AI-Powered Review System Ready!")
            print(f"Features available:")
            print(f"  - AI code quality analysis")
            print(f"  - Security vulnerability detection")
            print(f"  - Performance optimization suggestions")
            print(f"  - Automated approval workflows")
            print(f"  - Human review queue management")
            print(f"  - Review statistics and reporting")
            
    except Exception as e:
        print(f"\n{'='*50}")
        print(f"Review System Test: FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()