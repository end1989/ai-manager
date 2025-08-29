"""Advanced AI-powered code review engine with automated quality checks and approval workflows."""

import asyncio
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from manager.config import settings
from manager.core.artifacts import ArtifactManager  
from manager.core.schemas import (
    PullRequestProposal,
    ReviewEvidence,
    ReviewReport,
    ReviewStatus,
    WorkerTaskReport,
)
from manager.store.models import DatabaseManager
from manager.adapters.llm_provider import LLMManager, LLMError


class ReviewDecision(str, Enum):
    """Enhanced review decision options."""
    APPROVED = "approved"
    REQUIRES_CHANGES = "requires_changes"
    REJECTED = "rejected"
    NEEDS_HUMAN_REVIEW = "needs_human_review"


class CodeQualityScore(str, Enum):
    """Code quality scoring."""
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"           # 70-89
    FAIR = "fair"           # 50-69
    POOR = "poor"           # 0-49


class AIReviewResult:
    """Enhanced AI review result."""
    
    def __init__(self):
        self.decision: ReviewDecision = ReviewDecision.NEEDS_HUMAN_REVIEW
        self.quality_score: int = 0
        self.quality_grade: CodeQualityScore = CodeQualityScore.POOR
        self.issues: List[Dict[str, Any]] = []
        self.suggestions: List[Dict[str, Any]] = []
        self.security_concerns: List[str] = []
        self.performance_notes: List[str] = []
        self.maintainability_score: int = 0
        self.test_coverage_assessment: str = ""
        self.compliance_checks: Dict[str, bool] = {}
        self.reviewer_comments: str = ""
        self.approval_conditions: List[str] = []


class ApprovalWorkflow:
    """Manages approval workflows and human review queues."""
    
    def __init__(self):
        self.pending_reviews: Dict[str, Dict[str, Any]] = {}
        self.approval_history: List[Dict[str, Any]] = []
        self.review_rules: Dict[str, Any] = self._load_default_rules()
    
    def _load_default_rules(self) -> Dict[str, Any]:
        """Load default approval rules."""
        return {
            "auto_approve_threshold": 85,
            "require_human_review_threshold": 50,
            "security_keywords": [
                "eval", "exec", "subprocess.call", "os.system", "shell=True",
                "pickle.loads", "yaml.load", "input(", "raw_input"
            ],
            "required_tests": True,
            "max_file_size": 10000,
            "max_complexity": 10,
        }
    
    def submit_for_review(self, pr_id: str, pr_proposal: PullRequestProposal, 
                         worker_report: WorkerTaskReport) -> str:
        """Submit PR for review workflow."""
        
        review_id = f"REV-{pr_id}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        self.pending_reviews[review_id] = {
            "pr_id": pr_id,
            "pr_proposal": pr_proposal,
            "worker_report": worker_report,
            "submitted_at": datetime.utcnow(),
            "status": "pending_analysis",
            "priority": self._calculate_priority(pr_proposal, worker_report)
        }
        
        return review_id
    
    def _calculate_priority(self, pr_proposal: PullRequestProposal, 
                          worker_report: WorkerTaskReport) -> str:
        """Calculate review priority."""
        
        if pr_proposal.risk_assessment.breaking_change:
            return "high"
        
        if len(pr_proposal.diff_summary) > 10:
            return "high"
            
        if "security" in pr_proposal.risk_assessment.security_notes.lower():
            return "high"
        
        if len(worker_report.changes) > 5:
            return "medium"
            
        return "low"


class ReviewEngine:
    """Advanced AI-powered review engine with automated quality checks and approval workflows."""

    def __init__(self):
        self.artifacts = ArtifactManager()
        self.db = DatabaseManager()
        self.llm_manager = LLMManager()
        self.approval_workflow = ApprovalWorkflow()
        self._setup_llm_providers()
        
    def _setup_llm_providers(self):
        """Setup LLM providers for AI-powered review."""
        providers_configured = []
        
        # Prefer Anthropic for code review
        if self.llm_manager.setup_anthropic(set_default=True):
            providers_configured.append("anthropic")
        
        if self.llm_manager.setup_openai(set_default=not providers_configured):
            providers_configured.append("openai")
        
        self.llm_manager.setup_mock({
            "review": "AI code review completed. Quality score: 82/100. Minor improvements suggested.",
            "security": "Security analysis complete. No critical vulnerabilities found.",
            "performance": "Performance analysis shows good practices with room for optimization."
        })
        providers_configured.append("mock")
        
        print(f"Review engine AI providers: {providers_configured}")

    async def review_pr(self, pr_proposal: PullRequestProposal, run_id: str) -> ReviewReport:
        """Perform comprehensive review of PR proposal."""
        
        # Initialize review report
        report = ReviewReport(
            pr_id=pr_proposal.pr_id,
            status=ReviewStatus.APPROVED,  # Start optimistic
            blocking=[],
            non_blocking=[],
            evidence=ReviewEvidence(),
            notes="",
        )
        
        try:
            # Get run directory for analysis
            run_path = settings.runs_dir / run_id
            workdir = run_path / "workdir"
            
            if not workdir.exists():
                report.status = ReviewStatus.REJECTED
                report.blocking.append("workdir not found - no code to review")
                return report
            
            # Run all quality checks
            evidence = await self._collect_evidence(workdir, run_id)
            report.evidence = evidence
            
            # Analyze results and determine blocking issues
            blocking_issues = []
            non_blocking_issues = []
            
            # Check pytest results
            if not evidence.pytest:
                blocking_issues.append("No pytest results found")
            elif "FAILED" in evidence.pytest or "ERROR" in evidence.pytest:
                blocking_issues.append(f"Test failures detected: {evidence.pytest}")
            
            # Check coverage requirements
            if evidence.coverage.get("lines", 0) < 85:
                blocking_issues.append(
                    f"Coverage below 85%: {evidence.coverage.get('lines', 0):.1f}%"
                )
            
            # Check linter results
            if "error" in evidence.linters.lower() or "E" in evidence.linters:
                blocking_issues.append(f"Linter errors: {evidence.linters}")
            
            # Security checks
            security_issues = await self._check_security(workdir)
            blocking_issues.extend(security_issues)
            
            # Code quality checks
            quality_issues = await self._check_code_quality(workdir)
            non_blocking_issues.extend(quality_issues)
            
            # Set final status
            report.blocking = blocking_issues
            report.non_blocking = non_blocking_issues
            
            if blocking_issues:
                report.status = ReviewStatus.CHANGES_REQUESTED
                report.notes = f"Found {len(blocking_issues)} blocking issues"
            elif non_blocking_issues:
                report.status = ReviewStatus.APPROVED
                report.notes = f"Approved with {len(non_blocking_issues)} non-blocking suggestions"
            else:
                report.status = ReviewStatus.APPROVED
                report.notes = "All checks passed"
            
            # Store review in database
            await self._store_review(report, run_id)
            
            return report
            
        except Exception as e:
            # On error, reject with details
            report.status = ReviewStatus.REJECTED
            report.blocking = [f"Review process failed: {str(e)}"]
            report.notes = "Internal review error"
            return report

    async def ai_review_pr(self, pr_proposal: PullRequestProposal, 
                          worker_report: WorkerTaskReport, 
                          workdir: Path) -> Tuple[AIReviewResult, str]:
        """AI-powered comprehensive PR review with workflow integration."""
        
        print(f"Starting AI-powered review for PR: {pr_proposal.pr_id}")
        
        # Submit to approval workflow
        review_id = self.approval_workflow.submit_for_review(
            pr_proposal.pr_id, pr_proposal, worker_report
        )
        
        # Perform AI-powered analysis
        ai_result = await self._perform_ai_analysis(pr_proposal, worker_report, workdir)
        
        # Apply business rules
        ai_result = self._apply_review_rules(ai_result, pr_proposal, worker_report)
        
        # Generate comprehensive review summary
        ai_result.reviewer_comments = self._generate_ai_review_summary(ai_result)
        
        print(f"AI review completed: {ai_result.decision} (score: {ai_result.quality_score})")
        
        return ai_result, review_id

    async def _perform_ai_analysis(self, pr_proposal: PullRequestProposal, 
                                  worker_report: WorkerTaskReport, 
                                  workdir: Path) -> AIReviewResult:
        """Perform comprehensive AI-powered code analysis."""
        
        result = AIReviewResult()
        
        try:
            # AI-powered code quality analysis
            quality_analysis = await self._ai_analyze_code_quality(pr_proposal, worker_report, workdir)
            result.quality_score = quality_analysis.get("score", 70)
            result.quality_grade = self._score_to_grade(result.quality_score)
            result.issues.extend(quality_analysis.get("issues", []))
            result.suggestions.extend(quality_analysis.get("suggestions", []))
            
            # AI security analysis
            security_analysis = await self._ai_analyze_security(pr_proposal, workdir)
            result.security_concerns.extend(security_analysis.get("concerns", []))
            
            # Performance analysis (heuristic + AI)
            performance_analysis = await self._ai_analyze_performance(workdir)
            result.performance_notes.extend(performance_analysis.get("notes", []))
            
            # Maintainability assessment
            result.maintainability_score = await self._assess_maintainability(workdir)
            
            # Test coverage analysis
            result.test_coverage_assessment = await self._analyze_test_coverage(
                worker_report, workdir
            )
            
        except Exception as e:
            print(f"AI analysis error: {e}")
            result.issues.append({
                "type": "ai_analysis_error",
                "message": f"AI analysis failed: {str(e)}",
                "severity": "warning"
            })
        
        return result

    async def _ai_analyze_code_quality(self, pr_proposal: PullRequestProposal,
                                      worker_report: WorkerTaskReport, 
                                      workdir: Path) -> Dict[str, Any]:
        """AI-powered code quality analysis."""
        
        system_prompt = """You are an expert Python code reviewer. Analyze code for:
        - Structure and organization
        - Naming conventions and readability  
        - Error handling and edge cases
        - Documentation quality
        - Best practices adherence
        - Potential bugs
        
        Provide actionable feedback and a quality score (0-100)."""
        
        # Collect code samples
        code_samples = []
        for change in worker_report.changes[:3]:  # Limit to first 3 files
            file_path = workdir / change.file
            if file_path.exists() and file_path.suffix == ".py":
                try:
                    content = file_path.read_text(encoding="utf-8")
                    code_samples.append(f"File: {change.file}\n```python\n{content[:1500]}\n```")
                except Exception:
                    continue
        
        if not code_samples:
            return {"score": 75, "issues": [], "suggestions": []}
        
        user_prompt = f"""
        Code Quality Review:
        
        PR: {pr_proposal.title}
        Changes: {len(worker_report.changes)} files
        
        Code to review:
        {chr(10).join(code_samples)}
        
        Provide JSON with: score (0-100), issues (list), suggestions (list)
        """
        
        try:
            response = await self.llm_manager.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.1,
                max_tokens=1200
            )
            
            return self._parse_ai_quality_response(response.content)
            
        except Exception as e:
            print(f"AI quality analysis failed: {e}")
            return {"score": 75, "issues": [], "suggestions": []}

    async def _ai_analyze_security(self, pr_proposal: PullRequestProposal, 
                                  workdir: Path) -> Dict[str, Any]:
        """AI-powered security analysis."""
        
        system_prompt = """You are a security expert. Analyze Python code for:
        - SQL injection vulnerabilities
        - Command injection risks
        - Insecure deserialization
        - Path traversal issues
        - Authentication/authorization flaws
        - Input validation problems
        - Hardcoded secrets
        
        Focus on real security risks."""
        
        # Find security-sensitive files
        security_files = []
        for file_path in workdir.rglob("*.py"):
            try:
                content = file_path.read_text(encoding="utf-8")
                security_keywords = ["subprocess", "eval", "exec", "sql", "auth", "password", "token"]
                if any(keyword in content.lower() for keyword in security_keywords):
                    security_files.append((file_path.name, content[:1000]))
            except Exception:
                continue
        
        if not security_files:
            return {"concerns": []}
        
        user_prompt = f"""
        Security Review for PR: {pr_proposal.title}
        
        Security-sensitive files:
        {chr(10).join(f"File: {name}\\n{content}" for name, content in security_files[:2])}
        
        Identify vulnerabilities and provide JSON with: concerns (list of strings)
        """
        
        try:
            response = await self.llm_manager.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.1,
                max_tokens=800
            )
            
            return self._parse_ai_security_response(response.content)
            
        except Exception as e:
            print(f"AI security analysis failed: {e}")
            return {"concerns": []}

    async def _ai_analyze_performance(self, workdir: Path) -> Dict[str, Any]:
        """AI-enhanced performance analysis."""
        
        notes = []
        
        # Heuristic checks
        for file_path in workdir.rglob("*.py"):
            try:
                content = file_path.read_text(encoding="utf-8")
                
                if "for" in content and content.count("for") > 2:
                    notes.append(f"Multiple loops in {file_path.name} - check for optimization")
                
                if content.count("import") > 15:
                    notes.append(f"Many imports in {file_path.name}")
                
                if len(content.split("\n")) > 400:
                    notes.append(f"Large file {file_path.name} - consider refactoring")
                    
            except Exception:
                continue
        
        return {"notes": notes}

    def _parse_ai_quality_response(self, content: str) -> Dict[str, Any]:
        """Parse AI quality analysis response."""
        try:
            if "{" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end]
                parsed = json.loads(json_str)
                # Validate structure
                return {
                    "score": max(0, min(100, parsed.get("score", 75))),
                    "issues": parsed.get("issues", [])[:5],  # Limit issues
                    "suggestions": parsed.get("suggestions", [])[:3]  # Limit suggestions
                }
        except Exception:
            pass
        
        # Extract score from text if JSON parsing fails
        import re
        score_match = re.search(r'score["\s:]+(\d+)', content.lower())
        score = int(score_match.group(1)) if score_match else 75
        
        return {"score": score, "issues": [], "suggestions": []}

    def _parse_ai_security_response(self, content: str) -> Dict[str, Any]:
        """Parse AI security analysis response."""
        try:
            if "{" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end]
                parsed = json.loads(json_str)
                return {"concerns": parsed.get("concerns", [])[:5]}  # Limit concerns
        except Exception:
            pass
        
        concerns = []
        if any(word in content.lower() for word in ["vulnerability", "risk", "insecure", "dangerous"]):
            concerns.append("Potential security concerns found - manual review recommended")
        
        return {"concerns": concerns}

    def _score_to_grade(self, score: int) -> CodeQualityScore:
        """Convert score to grade."""
        if score >= 90:
            return CodeQualityScore.EXCELLENT
        elif score >= 70:
            return CodeQualityScore.GOOD
        elif score >= 50:
            return CodeQualityScore.FAIR
        else:
            return CodeQualityScore.POOR

    async def _assess_maintainability(self, workdir: Path) -> int:
        """Assess code maintainability."""
        score = 80
        python_files = list(workdir.rglob("*.py"))
        
        if len(python_files) > 10:
            score -= 5
        
        for file_path in python_files:
            try:
                lines = len(file_path.read_text(encoding="utf-8").split("\n"))
                if lines > 300:
                    score -= 3
            except Exception:
                continue
        
        return max(score, 0)

    async def _analyze_test_coverage(self, worker_report: WorkerTaskReport, 
                                   workdir: Path) -> str:
        """Analyze test coverage."""
        test_files = [c for c in worker_report.changes if "test" in c.file.lower()]
        code_files = [c for c in worker_report.changes if c.file.endswith(".py") and "test" not in c.file.lower()]
        
        if not test_files:
            return "No tests found - testing required"
        
        if len(test_files) >= len(code_files):
            return "Good test coverage - tests match implementation files"
        
        return f"Partial test coverage - {len(test_files)} test files for {len(code_files)} code files"

    def _apply_review_rules(self, result: AIReviewResult, pr_proposal: PullRequestProposal,
                           worker_report: WorkerTaskReport) -> AIReviewResult:
        """Apply business rules to determine final decision."""
        
        rules = self.approval_workflow.review_rules
        
        # Auto-approve high quality code
        if result.quality_score >= rules["auto_approve_threshold"] and not result.security_concerns:
            result.decision = ReviewDecision.APPROVED
            result.approval_conditions = ["Automated approval based on high quality score"]
        
        # Require human review for low quality
        elif result.quality_score < rules["require_human_review_threshold"]:
            result.decision = ReviewDecision.NEEDS_HUMAN_REVIEW
            result.approval_conditions = ["Low quality score requires human review"]
        
        # Security concerns need human review
        elif result.security_concerns:
            result.decision = ReviewDecision.NEEDS_HUMAN_REVIEW
            result.approval_conditions = ["Security concerns require human review"]
        
        # Breaking changes need human review
        elif pr_proposal.risk_assessment.breaking_change:
            result.decision = ReviewDecision.NEEDS_HUMAN_REVIEW
            result.approval_conditions = ["Breaking changes require human review"]
        
        # Many issues require changes
        elif len(result.issues) > 5:
            result.decision = ReviewDecision.REQUIRES_CHANGES
            result.approval_conditions = ["Multiple issues need to be addressed"]
        
        else:
            result.decision = ReviewDecision.NEEDS_HUMAN_REVIEW
            result.approval_conditions = ["Standard human review required"]
        
        return result

    def _generate_ai_review_summary(self, result: AIReviewResult) -> str:
        """Generate comprehensive AI review summary."""
        
        parts = [
            "## AI Code Review Summary",
            f"**Decision:** {result.decision.value.upper()}",
            f"**Quality Score:** {result.quality_score}/100 ({result.quality_grade.value})",
            f"**Maintainability:** {result.maintainability_score}/100",
            ""
        ]
        
        if result.test_coverage_assessment:
            parts.extend([f"**Test Coverage:** {result.test_coverage_assessment}", ""])
        
        if result.issues:
            parts.append("### Issues Found")
            for issue in result.issues[:5]:
                parts.append(f"- {issue.get('message', str(issue))}")
            parts.append("")
        
        if result.security_concerns:
            parts.append("### Security Concerns")
            for concern in result.security_concerns:
                parts.append(f"- {concern}")
            parts.append("")
        
        if result.suggestions:
            parts.append("### Improvement Suggestions")
            for suggestion in result.suggestions[:3]:
                parts.append(f"- {suggestion.get('message', str(suggestion))}")
            parts.append("")
        
        if result.performance_notes:
            parts.append("### Performance Notes")
            for note in result.performance_notes:
                parts.append(f"- {note}")
            parts.append("")
        
        if result.approval_conditions:
            parts.append("### Next Steps")
            for condition in result.approval_conditions:
                parts.append(f"- {condition}")
        
        return "\n".join(parts)

    # Human workflow management
    def get_pending_reviews(self, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pending reviews for human reviewers."""
        reviews = list(self.approval_workflow.pending_reviews.values())
        
        if priority:
            reviews = [r for r in reviews if r["priority"] == priority]
        
        # Sort by priority and time
        priority_order = {"high": 0, "medium": 1, "low": 2}
        reviews.sort(key=lambda r: (
            priority_order.get(r["priority"], 3),
            r["submitted_at"]
        ))
        
        return reviews

    def approve_review(self, review_id: str, approver: str, comments: str = "") -> bool:
        """Human approver approves a review."""
        if review_id not in self.approval_workflow.pending_reviews:
            return False
        
        review = self.approval_workflow.pending_reviews.pop(review_id)
        
        self.approval_workflow.approval_history.append({
            "review_id": review_id,
            "pr_id": review["pr_id"],
            "decision": "approved",
            "approver": approver,
            "comments": comments,
            "approved_at": datetime.utcnow(),
            "priority": review["priority"]
        })
        
        return True

    def reject_review(self, review_id: str, reviewer: str, reason: str) -> bool:
        """Human reviewer rejects a review."""
        if review_id not in self.approval_workflow.pending_reviews:
            return False
        
        review = self.approval_workflow.pending_reviews.pop(review_id)
        
        self.approval_workflow.approval_history.append({
            "review_id": review_id,
            "pr_id": review["pr_id"],
            "decision": "rejected",
            "reviewer": reviewer,
            "reason": reason,
            "reviewed_at": datetime.utcnow(),
            "priority": review["priority"]
        })
        
        return True

    def get_review_stats(self) -> Dict[str, Any]:
        """Get review statistics."""
        history = self.approval_workflow.approval_history
        total = len(history)
        
        if total == 0:
            return {"total": 0, "approved": 0, "rejected": 0, "approval_rate": 0, "pending": 0}
        
        approved = len([h for h in history if h["decision"] == "approved"])
        rejected = len([h for h in history if h["decision"] == "rejected"])
        
        return {
            "total": total,
            "approved": approved,
            "rejected": rejected,
            "approval_rate": round(approved / total * 100, 1) if total > 0 else 0,
            "pending": len(self.approval_workflow.pending_reviews)
        }

    async def _collect_evidence(self, workdir: Path, run_id: str) -> ReviewEvidence:
        """Collect evidence from linting, testing, and analysis."""
        
        evidence = ReviewEvidence()
        
        # Run pytest with coverage
        pytest_result = await self._run_pytest(workdir)
        evidence.pytest = pytest_result.get("summary", "")
        evidence.coverage = pytest_result.get("coverage", {})
        
        # Run linters
        linter_results = await self._run_linters(workdir)
        evidence.linters = linter_results
        
        # Collect key logs
        evidence.logs = await self._collect_key_logs(run_id)
        
        return evidence

    async def _run_pytest(self, workdir: Path) -> Dict[str, Any]:
        """Run pytest with coverage reporting."""
        
        try:
            # Look for test files
            test_files = list(workdir.rglob("test_*.py")) + list(workdir.rglob("*_test.py"))
            
            if not test_files:
                return {
                    "summary": "No test files found",
                    "coverage": {"lines": 0, "branches": 0},
                }
            
            # Run pytest with coverage
            cmd = [
                "python", "-m", "pytest",
                "--cov=.", "--cov-report=json",
                "-v", str(workdir)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=workdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            # Parse coverage report if available
            coverage_data = {}
            coverage_file = workdir / "coverage.json"
            if coverage_file.exists():
                try:
                    with open(coverage_file, "r") as f:
                        cov_json = json.load(f)
                        coverage_data = {
                            "lines": cov_json.get("totals", {}).get("percent_covered", 0),
                            "branches": cov_json.get("totals", {}).get("percent_covered_display", 0),
                        }
                except:
                    pass
            
            return {
                "summary": stdout.decode("utf-8", errors="ignore")[:1000],  # Limit output
                "coverage": coverage_data,
                "exit_code": process.returncode,
            }
            
        except Exception as e:
            return {
                "summary": f"pytest failed: {str(e)}",
                "coverage": {"lines": 0, "branches": 0},
            }

    async def _run_linters(self, workdir: Path) -> str:
        """Run ruff, black, and mypy on the code."""
        
        results = []
        
        # Run ruff
        try:
            cmd = ["python", "-m", "ruff", "check", "."]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=workdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            ruff_output = stdout.decode("utf-8", errors="ignore")
            if process.returncode == 0:
                results.append("ruff: clean")
            else:
                results.append(f"ruff: {ruff_output[:200]}")
                
        except Exception as e:
            results.append(f"ruff: failed - {str(e)}")
        
        # Run black --check
        try:
            cmd = ["python", "-m", "black", "--check", "."]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=workdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            
            if process.returncode == 0:
                results.append("black: formatted")
            else:
                results.append("black: formatting issues found")
                
        except Exception as e:
            results.append(f"black: failed - {str(e)}")
        
        # Run mypy
        try:
            cmd = ["python", "-m", "mypy", "."]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=workdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            mypy_output = stdout.decode("utf-8", errors="ignore")
            if process.returncode == 0:
                results.append("mypy: clean")
            else:
                results.append(f"mypy: {mypy_output[:200]}")
                
        except Exception as e:
            results.append(f"mypy: failed - {str(e)}")
        
        return "; ".join(results)

    async def _check_security(self, workdir: Path) -> List[str]:
        """Perform security checks on the code."""
        
        issues = []
        
        # Check for hardcoded secrets
        secret_patterns = [
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"api_key\s*=\s*['\"][^'\"]+['\"]", 
            r"secret\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][^'\"]+['\"]",
        ]
        
        for py_file in workdir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                
                for pattern in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append(f"Potential secret in {py_file.name}:{line_num}")
                        
            except Exception:
                continue
        
        # Check for dangerous imports
        dangerous_imports = [
            "os.system", "subprocess.call", "eval(", "exec(",
        ]
        
        for py_file in workdir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                
                for danger in dangerous_imports:
                    if danger in content:
                        issues.append(f"Dangerous code pattern '{danger}' in {py_file.name}")
                        
            except Exception:
                continue
        
        return issues

    async def _check_code_quality(self, workdir: Path) -> List[str]:
        """Check for code quality issues (non-blocking)."""
        
        suggestions = []
        
        # Check for TODO/FIXME comments
        for py_file in workdir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    if "TODO" in line.upper() or "FIXME" in line.upper():
                        suggestions.append(f"TODO/FIXME comment in {py_file.name}:{i}")
                        
            except Exception:
                continue
        
        # Check for overly long functions (>50 lines)
        for py_file in workdir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                lines = content.split('\n')
                
                in_function = False
                function_start = 0
                function_name = ""
                
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith("def "):
                        if in_function and (i - function_start) > 50:
                            suggestions.append(
                                f"Long function '{function_name}' in {py_file.name} "
                                f"({i - function_start} lines)"
                            )
                        
                        in_function = True
                        function_start = i
                        function_name = stripped.split("(")[0].replace("def ", "")
                    
                    elif stripped and not stripped.startswith(" ") and not stripped.startswith("\t"):
                        if stripped.startswith("class "):
                            continue
                        if in_function and (i - function_start) > 50:
                            suggestions.append(
                                f"Long function '{function_name}' in {py_file.name} "
                                f"({i - function_start} lines)"
                            )
                        in_function = False
                        
            except Exception:
                continue
        
        return suggestions

    async def _collect_key_logs(self, run_id: str) -> str:
        """Collect key logs from the run."""
        
        logs = []
        
        # Read stdout
        stdout_content = self.artifacts.read_log_file(run_id, "stdout")
        if stdout_content:
            logs.append(f"STDOUT (last 500 chars): {stdout_content[-500:]}")
        
        # Read stderr  
        stderr_content = self.artifacts.read_log_file(run_id, "stderr")
        if stderr_content:
            logs.append(f"STDERR (last 500 chars): {stderr_content[-500:]}")
        
        return "\n".join(logs)

    async def _store_review(self, review: ReviewReport, run_id: str) -> None:
        """Store review report in database."""
        
        review_data = {
            "pr_id": review.pr_id,
            "status": review.status.value,
            "blocking_json": json.dumps(review.blocking),
            "non_blocking_json": json.dumps(review.non_blocking), 
            "evidence_json": json.dumps(review.evidence.model_dump()),
            "notes": review.notes,
        }
        
        self.db.create_review(review_data)
        
        # Log review completion
        self.db.log_event(
            event_type="review_completed",
            entity_type="review",
            entity_id=review.pr_id,
            data={
                "status": review.status.value,
                "blocking_count": len(review.blocking),
                "run_id": run_id,
            },
        )

    def validate_pr_proposal(self, proposal: PullRequestProposal) -> List[str]:
        """Validate PR proposal structure."""
        
        errors = []
        
        if not proposal.pr_id.strip():
            errors.append("PR ID is required")
        
        if not proposal.title.strip():
            errors.append("PR title is required")
            
        if not proposal.description.strip():
            errors.append("PR description is required")
        
        if not proposal.diff_summary:
            errors.append("Diff summary is required")
            
        return errors