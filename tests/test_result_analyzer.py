"""Test result analysis and improvement suggestions system.

This module provides comprehensive analysis of test results and generates
actionable improvement suggestions specifically designed for AI systems
to understand and implement. It goes beyond simple pass/fail reporting
to provide deep insights into test patterns, quality trends, and optimization
opportunities.

Key Features:
- Multi-dimensional test result analysis
- Trend analysis across test runs
- Performance regression detection
- Quality metric tracking
- AI-optimized improvement suggestions
- Automated refactoring recommendations
- Test coverage gap analysis
- Resource usage optimization
- Flaky test detection and mitigation
"""

import json
import statistics
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple, Union
import re

# Import our AI-friendly testing components
from .ai_diagnostics import AITestDiagnostics  
from .ai_error_context import AIErrorAnalyzer, ErrorCategory, ErrorSeverity
from .test_health_monitor import TestHealthMonitor, TestSuiteHealth
from .test_progressive_execution import ProgressiveExecutionReport, TestStage


class AnalysisType(Enum):
    """Types of analysis that can be performed."""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    COVERAGE = "coverage"
    FLAKINESS = "flakiness"
    RESOURCE_USAGE = "resource_usage"
    ERROR_PATTERNS = "error_patterns"
    TRENDS = "trends"
    DEPENDENCIES = "dependencies"


class ImprovementPriority(Enum):
    """Priority levels for improvement suggestions."""
    CRITICAL = "critical"    # Must fix immediately
    HIGH = "high"           # Important for stability
    MEDIUM = "medium"       # Good to have
    LOW = "low"            # Nice to have
    FUTURE = "future"      # Long-term optimization


@dataclass
class TestMetrics:
    """Comprehensive metrics for a single test."""
    test_name: str
    file_path: str
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    skip_count: int = 0
    
    # Timing metrics
    total_duration: float = 0.0
    avg_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    duration_variance: float = 0.0
    
    # Resource metrics
    avg_memory_usage: float = 0.0
    max_memory_usage: float = 0.0
    avg_cpu_usage: float = 0.0
    
    # Quality metrics
    flakiness_score: float = 0.0  # 0-1, higher = more flaky
    stability_trend: str = "stable"  # improving, stable, degrading
    
    # Error analysis
    error_types: Dict[str, int] = field(default_factory=dict)
    common_failures: List[str] = field(default_factory=list)
    
    # Dependencies and relationships
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    
    # Metadata
    tags: Set[str] = field(default_factory=set)
    stage: Optional[TestStage] = None
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ImprovementSuggestion:
    """A specific improvement suggestion with actionable details."""
    title: str
    description: str
    category: str  # performance, reliability, coverage, etc.
    priority: ImprovementPriority
    effort_estimate: str  # "5 minutes", "1 hour", "1 day", etc.
    confidence: float  # 0-1, how confident we are this will help
    
    # Actionable details
    affected_tests: List[str]
    code_changes: List[Dict[str, str]]  # file -> suggested changes
    commands_to_run: List[str]
    verification_steps: List[str]
    
    # Context
    evidence: Dict[str, Any]  # Data supporting this suggestion
    related_issues: List[str]
    documentation_links: List[str]
    
    # Tracking
    implementation_status: str = "pending"  # pending, in_progress, completed, dismissed
    created_at: datetime = field(default_factory=datetime.now)


@dataclass  
class TestSuiteAnalysis:
    """Comprehensive analysis of the entire test suite."""
    analysis_id: str
    timestamp: datetime
    
    # Overall metrics
    total_tests: int
    total_execution_time: float
    overall_pass_rate: float
    overall_flakiness: float
    
    # Performance analysis
    slowest_tests: List[Tuple[str, float]]  # (test_name, duration)
    fastest_tests: List[Tuple[str, float]]
    performance_regressions: List[Dict[str, Any]]
    performance_improvements: List[Dict[str, Any]]
    
    # Quality analysis
    most_flaky_tests: List[Tuple[str, float]]  # (test_name, flakiness_score)
    most_reliable_tests: List[Tuple[str, float]]
    error_hotspots: List[Tuple[str, int]]  # (error_type, frequency)
    
    # Resource analysis
    memory_intensive_tests: List[Tuple[str, float]]  # (test_name, memory_mb)
    cpu_intensive_tests: List[Tuple[str, float]]
    resource_waste_opportunities: List[Dict[str, Any]]
    
    # Coverage analysis (if available)
    coverage_gaps: List[Dict[str, Any]]
    untested_code_paths: List[str]
    
    # Trend analysis
    quality_trend: str  # improving, stable, degrading
    performance_trend: str
    trends_over_time: Dict[str, List[float]]
    
    # Improvement suggestions
    improvement_suggestions: List[ImprovementSuggestion]
    
    # Summary
    health_score: float  # 0-100, overall test suite health
    readiness_assessment: str  # ready, needs_attention, critical_issues
    key_insights: List[str]


class TestResultAnalyzer:
    """Advanced test result analysis and improvement suggestion system."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.analysis_dir = project_root / ".test_analysis"
        self.analysis_dir.mkdir(exist_ok=True)
        
        # Initialize AI components
        self.diagnostics = AITestDiagnostics(project_root)
        self.error_analyzer = AIErrorAnalyzer(project_root)
        self.health_monitor = TestHealthMonitor(project_root)
        
        # Historical data
        self.test_metrics: Dict[str, TestMetrics] = {}
        self.analysis_history: List[TestSuiteAnalysis] = []
        
        # Configuration
        self.config = self._load_configuration()
        
        # Load historical data
        self._load_historical_data()
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load analyzer configuration."""
        config_file = self.project_root / "test_analyzer_config.json"
        
        default_config = {
            "performance_thresholds": {
                "slow_test_seconds": 5.0,
                "very_slow_test_seconds": 30.0,
                "performance_regression_threshold": 0.2  # 20% slower
            },
            "flakiness_thresholds": {
                "min_runs_for_analysis": 5,
                "flaky_threshold": 0.1,  # 10% failure rate in otherwise passing tests
                "very_flaky_threshold": 0.3
            },
            "resource_thresholds": {
                "memory_intensive_mb": 50,
                "cpu_intensive_percent": 80
            },
            "improvement_weights": {
                "performance": 0.3,
                "reliability": 0.4,
                "maintainability": 0.2,
                "coverage": 0.1
            },
            "analysis_settings": {
                "history_window_days": 30,
                "trend_analysis_min_points": 5,
                "confidence_threshold": 0.7
            }
        }
        
        try:
            if config_file.exists():
                with open(config_file) as f:
                    user_config = json.load(f)
                    # Deep merge configurations
                    for key, value in user_config.items():
                        if isinstance(value, dict) and key in default_config:
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
        except Exception as e:
            print(f"Warning: Could not load analyzer config: {e}")
        
        return default_config
    
    def _load_historical_data(self) -> None:
        """Load historical test metrics and analysis data."""
        # Load test metrics
        metrics_file = self.analysis_dir / "test_metrics.json"
        if metrics_file.exists():
            try:
                with open(metrics_file) as f:
                    data = json.load(f)
                    for test_name, metric_data in data.items():
                        # Convert dict back to TestMetrics object
                        metrics = TestMetrics(test_name=test_name, file_path=metric_data.get("file_path", ""))
                        
                        # Load numeric fields
                        for field in ["execution_count", "success_count", "failure_count", "skip_count",
                                    "total_duration", "avg_duration", "min_duration", "max_duration",
                                    "duration_variance", "avg_memory_usage", "max_memory_usage", 
                                    "avg_cpu_usage", "flakiness_score"]:
                            setattr(metrics, field, metric_data.get(field, getattr(metrics, field)))
                        
                        # Load complex fields
                        metrics.error_types = metric_data.get("error_types", {})
                        metrics.common_failures = metric_data.get("common_failures", [])
                        metrics.dependencies = set(metric_data.get("dependencies", []))
                        metrics.dependents = set(metric_data.get("dependents", []))
                        metrics.tags = set(metric_data.get("tags", []))
                        metrics.stability_trend = metric_data.get("stability_trend", "stable")
                        
                        if metric_data.get("stage"):
                            try:
                                metrics.stage = TestStage(metric_data["stage"])
                            except ValueError:
                                pass
                        
                        self.test_metrics[test_name] = metrics
                        
            except Exception as e:
                print(f"Warning: Could not load test metrics: {e}")
        
        # Load analysis history
        history_file = self.analysis_dir / "analysis_history.json"
        if history_file.exists():
            try:
                with open(history_file) as f:
                    history_data = json.load(f)
                    # Load recent analysis summaries (simplified)
                    # Full TestSuiteAnalysis objects are complex to serialize/deserialize
                    # For now, just track basic trends
                    pass
            except Exception as e:
                print(f"Warning: Could not load analysis history: {e}")
    
    def _save_historical_data(self) -> None:
        """Save test metrics and analysis data."""
        # Save test metrics
        metrics_file = self.analysis_dir / "test_metrics.json"
        try:
            metrics_data = {}
            for test_name, metrics in self.test_metrics.items():
                metrics_data[test_name] = {
                    "file_path": metrics.file_path,
                    "execution_count": metrics.execution_count,
                    "success_count": metrics.success_count,
                    "failure_count": metrics.failure_count,
                    "skip_count": metrics.skip_count,
                    "total_duration": metrics.total_duration,
                    "avg_duration": metrics.avg_duration,
                    "min_duration": metrics.min_duration if metrics.min_duration != float('inf') else 0.0,
                    "max_duration": metrics.max_duration,
                    "duration_variance": metrics.duration_variance,
                    "avg_memory_usage": metrics.avg_memory_usage,
                    "max_memory_usage": metrics.max_memory_usage,
                    "avg_cpu_usage": metrics.avg_cpu_usage,
                    "flakiness_score": metrics.flakiness_score,
                    "stability_trend": metrics.stability_trend,
                    "error_types": metrics.error_types,
                    "common_failures": metrics.common_failures,
                    "dependencies": list(metrics.dependencies),
                    "dependents": list(metrics.dependents),
                    "tags": list(metrics.tags),
                    "stage": metrics.stage.value if metrics.stage else None,
                    "last_updated": metrics.last_updated.isoformat()
                }
            
            with open(metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save test metrics: {e}")
    
    def update_test_metrics(
        self, 
        test_results: List[Dict[str, Any]], 
        execution_report: Optional[ProgressiveExecutionReport] = None
    ) -> None:
        """Update test metrics with new test results."""
        
        for result in test_results:
            test_name = result.get("test_name", "unknown")
            
            # Get or create metrics
            if test_name not in self.test_metrics:
                self.test_metrics[test_name] = TestMetrics(
                    test_name=test_name,
                    file_path=result.get("file_path", "")
                )
            
            metrics = self.test_metrics[test_name]
            
            # Update execution counts
            metrics.execution_count += 1
            if result.get("passed", False):
                metrics.success_count += 1
            else:
                metrics.failure_count += 1
            
            # Update timing metrics
            duration = result.get("duration", 0.0)
            if duration > 0:
                metrics.total_duration += duration
                metrics.avg_duration = metrics.total_duration / metrics.execution_count
                metrics.min_duration = min(metrics.min_duration, duration)
                metrics.max_duration = max(metrics.max_duration, duration)
                
                # Calculate variance (simplified)
                if metrics.execution_count > 1:
                    # This is a simplified variance calculation
                    metrics.duration_variance = abs(duration - metrics.avg_duration) / metrics.avg_duration
            
            # Update resource metrics
            if "memory_usage" in result:
                memory_mb = result["memory_usage"] / (1024 * 1024)
                metrics.avg_memory_usage = (
                    (metrics.avg_memory_usage * (metrics.execution_count - 1) + memory_mb) 
                    / metrics.execution_count
                )
                metrics.max_memory_usage = max(metrics.max_memory_usage, memory_mb)
            
            # Update error information
            if not result.get("passed", False) and result.get("error_message"):
                error_msg = result["error_message"]
                
                # Extract error type
                error_type = "RuntimeError"
                for known_error in ["ImportError", "AssertionError", "TypeError", "AttributeError", 
                                  "ValueError", "KeyError", "FileNotFoundError"]:
                    if known_error in error_msg:
                        error_type = known_error
                        break
                
                metrics.error_types[error_type] = metrics.error_types.get(error_type, 0) + 1
                
                # Store common failure message (simplified)
                if len(metrics.common_failures) < 5:
                    short_msg = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
                    if short_msg not in metrics.common_failures:
                        metrics.common_failures.append(short_msg)
            
            # Update flakiness score
            metrics.flakiness_score = self._calculate_flakiness_score(metrics)
            
            # Update tags and stage from execution report
            if execution_report:
                for stage_result in execution_report.completed_stages:
                    for test_result in stage_result.passed_tests + stage_result.failed_tests:
                        if test_result.test_name == test_name:
                            metrics.stage = test_result.stage
                            break
            
            metrics.last_updated = datetime.now()
        
        # Save updated metrics
        self._save_historical_data()
    
    def _calculate_flakiness_score(self, metrics: TestMetrics) -> float:
        """Calculate flakiness score for a test (0-1, higher = more flaky)."""
        if metrics.execution_count < self.config["flakiness_thresholds"]["min_runs_for_analysis"]:
            return 0.0
        
        # Simple flakiness calculation based on failure rate among runs
        failure_rate = metrics.failure_count / metrics.execution_count
        
        # If test always passes or always fails, it's not flaky
        if failure_rate == 0.0 or failure_rate == 1.0:
            return 0.0
        
        # Peak flakiness at 50% failure rate
        flakiness = 4 * failure_rate * (1 - failure_rate)
        
        # Adjust for duration variance (inconsistent timing suggests flakiness)
        if metrics.duration_variance > 0.5:  # 50% variance
            flakiness *= 1.2
        
        return min(flakiness, 1.0)
    
    def analyze_test_suite(
        self, 
        recent_execution: Optional[ProgressiveExecutionReport] = None,
        health_report: Optional[TestSuiteHealth] = None
    ) -> TestSuiteAnalysis:
        """Perform comprehensive analysis of the test suite."""
        
        analysis_id = f"analysis_{int(time.time())}"
        timestamp = datetime.now()
        
        print(f"🔍 Performing comprehensive test suite analysis: {analysis_id}")
        
        # Basic metrics calculation
        total_tests = len(self.test_metrics)
        total_execution_time = sum(m.total_duration for m in self.test_metrics.values())
        
        # Calculate overall pass rate
        total_runs = sum(m.execution_count for m in self.test_metrics.values())
        total_successes = sum(m.success_count for m in self.test_metrics.values())
        overall_pass_rate = total_successes / max(total_runs, 1)
        
        # Calculate overall flakiness
        flakiness_scores = [m.flakiness_score for m in self.test_metrics.values() if m.execution_count >= 5]
        overall_flakiness = statistics.mean(flakiness_scores) if flakiness_scores else 0.0
        
        # Performance analysis
        performance_data = self._analyze_performance()
        
        # Quality analysis  
        quality_data = self._analyze_quality()
        
        # Resource analysis
        resource_data = self._analyze_resource_usage()
        
        # Trend analysis
        trend_data = self._analyze_trends()
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            performance_data, quality_data, resource_data, trend_data
        )
        
        # Calculate health score
        health_score = self._calculate_health_score(
            overall_pass_rate, overall_flakiness, performance_data, quality_data
        )
        
        # Determine readiness assessment
        readiness_assessment = self._assess_readiness(health_score, improvement_suggestions)
        
        # Generate key insights
        key_insights = self._generate_key_insights(
            performance_data, quality_data, resource_data, improvement_suggestions
        )
        
        # Create analysis object
        analysis = TestSuiteAnalysis(
            analysis_id=analysis_id,
            timestamp=timestamp,
            total_tests=total_tests,
            total_execution_time=total_execution_time,
            overall_pass_rate=overall_pass_rate,
            overall_flakiness=overall_flakiness,
            
            slowest_tests=performance_data["slowest_tests"],
            fastest_tests=performance_data["fastest_tests"],
            performance_regressions=performance_data["regressions"],
            performance_improvements=performance_data["improvements"],
            
            most_flaky_tests=quality_data["most_flaky"],
            most_reliable_tests=quality_data["most_reliable"],
            error_hotspots=quality_data["error_hotspots"],
            
            memory_intensive_tests=resource_data["memory_intensive"],
            cpu_intensive_tests=resource_data["cpu_intensive"],
            resource_waste_opportunities=resource_data["waste_opportunities"],
            
            coverage_gaps=[],  # Would need coverage data
            untested_code_paths=[],
            
            quality_trend=trend_data["quality_trend"],
            performance_trend=trend_data["performance_trend"],
            trends_over_time=trend_data["trends"],
            
            improvement_suggestions=improvement_suggestions,
            health_score=health_score,
            readiness_assessment=readiness_assessment,
            key_insights=key_insights
        )
        
        # Add to history
        self.analysis_history.append(analysis)
        
        # Save analysis summary
        self._save_analysis_summary(analysis)
        
        return analysis
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance characteristics of tests."""
        
        # Get tests with timing data
        timed_tests = [(name, m.avg_duration) for name, m in self.test_metrics.items() 
                      if m.avg_duration > 0]
        timed_tests.sort(key=lambda x: x[1])
        
        slow_threshold = self.config["performance_thresholds"]["slow_test_seconds"]
        
        return {
            "slowest_tests": timed_tests[-10:],  # Top 10 slowest
            "fastest_tests": timed_tests[:10],   # Top 10 fastest
            "slow_test_count": len([t for t in timed_tests if t[1] > slow_threshold]),
            "regressions": self._detect_performance_regressions(),
            "improvements": self._detect_performance_improvements(),
            "total_slow_time": sum(t[1] for t in timed_tests if t[1] > slow_threshold)
        }
    
    def _analyze_quality(self) -> Dict[str, Any]:
        """Analyze quality and reliability characteristics."""
        
        # Flakiness analysis
        flaky_tests = [(name, m.flakiness_score) for name, m in self.test_metrics.items() 
                      if m.flakiness_score > 0]
        flaky_tests.sort(key=lambda x: x[1], reverse=True)
        
        # Reliability analysis (based on success rate)
        reliable_tests = []
        for name, metrics in self.test_metrics.items():
            if metrics.execution_count >= 5:
                success_rate = metrics.success_count / metrics.execution_count
                reliable_tests.append((name, success_rate))
        reliable_tests.sort(key=lambda x: x[1], reverse=True)
        
        # Error pattern analysis
        all_error_types = Counter()
        for metrics in self.test_metrics.values():
            for error_type, count in metrics.error_types.items():
                all_error_types[error_type] += count
        
        return {
            "most_flaky": flaky_tests[:10],
            "most_reliable": reliable_tests[:10],
            "error_hotspots": list(all_error_types.most_common(10)),
            "flaky_test_count": len([t for t in flaky_tests if t[1] > 0.1]),
            "total_error_count": sum(all_error_types.values())
        }
    
    def _analyze_resource_usage(self) -> Dict[str, Any]:
        """Analyze resource usage patterns."""
        
        memory_threshold = self.config["resource_thresholds"]["memory_intensive_mb"]
        
        # Memory usage analysis
        memory_tests = [(name, m.max_memory_usage) for name, m in self.test_metrics.items() 
                       if m.max_memory_usage > 0]
        memory_tests.sort(key=lambda x: x[1], reverse=True)
        
        # CPU usage analysis (simplified - would need more detailed metrics)
        cpu_tests = [(name, m.avg_cpu_usage) for name, m in self.test_metrics.items() 
                    if m.avg_cpu_usage > 0]
        cpu_tests.sort(key=lambda x: x[1], reverse=True)
        
        # Resource waste opportunities
        waste_opportunities = []
        for name, metrics in self.test_metrics.items():
            if metrics.max_memory_usage > memory_threshold and metrics.avg_duration > 10:
                waste_opportunities.append({
                    "test_name": name,
                    "type": "memory_and_time",
                    "memory_mb": metrics.max_memory_usage,
                    "duration": metrics.avg_duration,
                    "potential_savings": "High"
                })
        
        return {
            "memory_intensive": memory_tests[:10],
            "cpu_intensive": cpu_tests[:10],
            "waste_opportunities": waste_opportunities[:10],
            "total_memory_usage": sum(t[1] for t in memory_tests),
            "high_memory_test_count": len([t for t in memory_tests if t[1] > memory_threshold])
        }
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends over time."""
        
        # This is simplified - would need historical execution data
        # For now, analyze based on stability_trend field
        
        improving_tests = [name for name, m in self.test_metrics.items() 
                          if m.stability_trend == "improving"]
        degrading_tests = [name for name, m in self.test_metrics.items() 
                          if m.stability_trend == "degrading"]
        
        # Overall trend assessment
        if len(degrading_tests) > len(improving_tests):
            quality_trend = "degrading"
        elif len(improving_tests) > len(degrading_tests):
            quality_trend = "improving"
        else:
            quality_trend = "stable"
        
        # Performance trend (simplified)
        performance_trend = "stable"  # Would need historical timing data
        
        return {
            "quality_trend": quality_trend,
            "performance_trend": performance_trend,
            "improving_tests": improving_tests,
            "degrading_tests": degrading_tests,
            "trends": {
                "pass_rate": [overall_pass_rate for overall_pass_rate in [0.95, 0.93, 0.96, 0.94, 0.97]],  # Mock data
                "avg_duration": [2.1, 2.3, 2.0, 2.4, 2.2]  # Mock data
            }
        }
    
    def _detect_performance_regressions(self) -> List[Dict[str, Any]]:
        """Detect performance regressions."""
        regressions = []
        
        threshold = self.config["performance_thresholds"]["performance_regression_threshold"]
        
        for name, metrics in self.test_metrics.items():
            # This is simplified - would need historical timing data
            # For now, use duration variance as a proxy
            if metrics.duration_variance > threshold and metrics.avg_duration > 5.0:
                regressions.append({
                    "test_name": name,
                    "current_duration": metrics.avg_duration,
                    "variance": metrics.duration_variance,
                    "severity": "high" if metrics.avg_duration > 30 else "medium"
                })
        
        return sorted(regressions, key=lambda x: x["current_duration"], reverse=True)[:10]
    
    def _detect_performance_improvements(self) -> List[Dict[str, Any]]:
        """Detect performance improvements."""
        # This would compare against historical data
        # For now, return empty list
        return []
    
    def _generate_improvement_suggestions(
        self, 
        performance_data: Dict[str, Any],
        quality_data: Dict[str, Any],
        resource_data: Dict[str, Any],
        trend_data: Dict[str, Any]
    ) -> List[ImprovementSuggestion]:
        """Generate comprehensive improvement suggestions."""
        
        suggestions = []
        
        # Performance improvement suggestions
        suggestions.extend(self._generate_performance_suggestions(performance_data))
        
        # Quality improvement suggestions
        suggestions.extend(self._generate_quality_suggestions(quality_data))
        
        # Resource optimization suggestions
        suggestions.extend(self._generate_resource_suggestions(resource_data))
        
        # Trend-based suggestions
        suggestions.extend(self._generate_trend_suggestions(trend_data))
        
        # Sort by priority and confidence
        suggestions.sort(key=lambda s: (s.priority.value, -s.confidence))
        
        return suggestions[:20]  # Top 20 suggestions
    
    def _generate_performance_suggestions(self, performance_data: Dict[str, Any]) -> List[ImprovementSuggestion]:
        """Generate performance-focused improvement suggestions."""
        suggestions = []
        
        # Slow tests suggestions
        if performance_data["slow_test_count"] > 0:
            slow_tests = [t[0] for t in performance_data["slowest_tests"][-5:]]
            
            suggestions.append(ImprovementSuggestion(
                title="Optimize Slow Tests",
                description=f"Found {performance_data['slow_test_count']} slow tests consuming {performance_data['total_slow_time']:.1f}s total",
                category="performance",
                priority=ImprovementPriority.HIGH,
                effort_estimate="2-4 hours",
                confidence=0.8,
                affected_tests=slow_tests,
                code_changes=[{
                    "type": "optimization",
                    "description": "Add mocking, reduce test data, or parallelize operations"
                }],
                commands_to_run=[
                    "pytest --durations=10 -v",
                    "pytest-benchmark tests/ --benchmark-only"
                ],
                verification_steps=[
                    "Run tests with timing: pytest --durations=10",
                    "Verify reduced execution time",
                    "Ensure test functionality unchanged"
                ],
                evidence={
                    "slowest_tests": performance_data["slowest_tests"],
                    "total_time_saved_potential": performance_data['total_slow_time'] * 0.5
                },
                related_issues=["Test suite takes too long", "CI pipeline timeouts"],
                documentation_links=[
                    "https://docs.pytest.org/en/stable/example/simple.html#profiling-test-duration"
                ]
            ))
        
        # Performance regression suggestions
        if performance_data["regressions"]:
            regression_tests = [r["test_name"] for r in performance_data["regressions"][:3]]
            
            suggestions.append(ImprovementSuggestion(
                title="Fix Performance Regressions",
                description="Detected performance regressions in key tests",
                category="performance",
                priority=ImprovementPriority.CRITICAL,
                effort_estimate="1-2 days",
                confidence=0.9,
                affected_tests=regression_tests,
                code_changes=[{
                    "type": "regression_fix",
                    "description": "Profile and optimize regressed code paths"
                }],
                commands_to_run=[
                    "pytest --profile",
                    "python -m cProfile -o profile.stats -m pytest",
                ],
                verification_steps=[
                    "Profile regressed tests",
                    "Identify bottlenecks",
                    "Implement optimizations",
                    "Verify performance restoration"
                ],
                evidence={"regressions": performance_data["regressions"]},
                related_issues=["Performance degradation", "Slower CI builds"],
                documentation_links=["https://docs.python.org/3/library/profile.html"]
            ))
        
        return suggestions
    
    def _generate_quality_suggestions(self, quality_data: Dict[str, Any]) -> List[ImprovementSuggestion]:
        """Generate quality-focused improvement suggestions."""
        suggestions = []
        
        # Flaky test suggestions
        if quality_data["flaky_test_count"] > 0:
            flaky_tests = [t[0] for t in quality_data["most_flaky"][:5]]
            
            suggestions.append(ImprovementSuggestion(
                title="Fix Flaky Tests",
                description=f"Found {quality_data['flaky_test_count']} flaky tests causing intermittent failures",
                category="reliability",
                priority=ImprovementPriority.HIGH,
                effort_estimate="1-3 days",
                confidence=0.85,
                affected_tests=flaky_tests,
                code_changes=[{
                    "type": "flakiness_fix",
                    "description": "Add explicit waits, fix race conditions, improve test isolation"
                }],
                commands_to_run=[
                    "pytest --flake-finder --flake-runs=10",
                    "pytest -x -vvv <flaky_test>"
                ],
                verification_steps=[
                    "Run flaky test multiple times",
                    "Identify root cause of intermittency",
                    "Implement fixes (waits, mocking, isolation)",
                    "Verify consistent behavior"
                ],
                evidence={
                    "flaky_tests": quality_data["most_flaky"],
                    "total_flaky_count": quality_data["flaky_test_count"]
                },
                related_issues=["Intermittent test failures", "CI instability"],
                documentation_links=[
                    "https://docs.pytest.org/en/stable/example/markers.html#marking-test-functions-with-attributes"
                ]
            ))
        
        # Error pattern suggestions
        if quality_data["error_hotspots"]:
            top_error = quality_data["error_hotspots"][0]
            error_type, error_count = top_error
            
            suggestions.append(ImprovementSuggestion(
                title=f"Address {error_type} Error Pattern",
                description=f"{error_type} occurs {error_count} times - systematic issue likely",
                category="reliability",
                priority=ImprovementPriority.HIGH,
                effort_estimate="4-8 hours",
                confidence=0.75,
                affected_tests=[],  # Would need to track which tests have these errors
                code_changes=[{
                    "type": "error_pattern_fix",
                    "description": f"Address root cause of {error_type} pattern"
                }],
                commands_to_run=[
                    f"pytest -k 'not {error_type}' --tb=short",
                    "grep -r '{error_type}' tests/"
                ],
                verification_steps=[
                    f"Identify all tests with {error_type}",
                    "Find common root cause",
                    "Implement systematic fix",
                    "Verify error reduction"
                ],
                evidence={"error_hotspots": quality_data["error_hotspots"]},
                related_issues=[f"Frequent {error_type} errors", "Test reliability issues"],
                documentation_links=[]
            ))
        
        return suggestions
    
    def _generate_resource_suggestions(self, resource_data: Dict[str, Any]) -> List[ImprovementSuggestion]:
        """Generate resource optimization suggestions."""
        suggestions = []
        
        # Memory optimization suggestions
        if resource_data["high_memory_test_count"] > 3:
            memory_tests = [t[0] for t in resource_data["memory_intensive"][:3]]
            
            suggestions.append(ImprovementSuggestion(
                title="Optimize Memory Usage",
                description=f"Found {resource_data['high_memory_test_count']} memory-intensive tests",
                category="performance",
                priority=ImprovementPriority.MEDIUM,
                effort_estimate="1-2 days",
                confidence=0.7,
                affected_tests=memory_tests,
                code_changes=[{
                    "type": "memory_optimization",
                    "description": "Reduce test data size, add cleanup, use memory-efficient data structures"
                }],
                commands_to_run=[
                    "pytest --memray tests/",
                    "python -m memory_profiler tests/test_file.py"
                ],
                verification_steps=[
                    "Profile memory usage of intensive tests",
                    "Identify memory leaks or excessive usage",
                    "Optimize data structures and cleanup",
                    "Verify reduced memory footprint"
                ],
                evidence={
                    "memory_intensive_tests": resource_data["memory_intensive"],
                    "total_memory_usage": resource_data["total_memory_usage"]
                },
                related_issues=["High memory usage", "Resource constraints"],
                documentation_links=[
                    "https://pympler.readthedocs.io/en/latest/",
                    "https://github.com/bloomberg/memray"
                ]
            ))
        
        # Resource waste suggestions
        if resource_data["waste_opportunities"]:
            waste_tests = [w["test_name"] for w in resource_data["waste_opportunities"][:3]]
            
            suggestions.append(ImprovementSuggestion(
                title="Address Resource Waste",
                description="Tests using excessive resources for their scope",
                category="performance",
                priority=ImprovementPriority.MEDIUM,
                effort_estimate="2-4 hours",
                confidence=0.8,
                affected_tests=waste_tests,
                code_changes=[{
                    "type": "resource_optimization",
                    "description": "Optimize resource usage in wasteful tests"
                }],
                commands_to_run=["pytest --profile-resource <test>"],
                verification_steps=[
                    "Review resource-wasteful tests",
                    "Identify optimization opportunities",
                    "Implement resource-efficient alternatives",
                    "Verify maintained functionality"
                ],
                evidence={"waste_opportunities": resource_data["waste_opportunities"]},
                related_issues=["Resource inefficiency", "Slow CI builds"],
                documentation_links=[]
            ))
        
        return suggestions
    
    def _generate_trend_suggestions(self, trend_data: Dict[str, Any]) -> List[ImprovementSuggestion]:
        """Generate trend-based improvement suggestions."""
        suggestions = []
        
        if trend_data["quality_trend"] == "degrading":
            suggestions.append(ImprovementSuggestion(
                title="Address Quality Degradation Trend",
                description="Test suite quality is degrading over time",
                category="quality",
                priority=ImprovementPriority.HIGH,
                effort_estimate="1 week",
                confidence=0.6,
                affected_tests=trend_data["degrading_tests"],
                code_changes=[{
                    "type": "quality_improvement",
                    "description": "Address systematic quality issues"
                }],
                commands_to_run=["pytest --collect-only --quiet"],
                verification_steps=[
                    "Analyze degrading tests",
                    "Identify common patterns",
                    "Implement quality improvements",
                    "Monitor trend reversal"
                ],
                evidence={
                    "trend": trend_data["quality_trend"],
                    "degrading_tests": trend_data["degrading_tests"]
                },
                related_issues=["Quality degradation", "Increasing failures"],
                documentation_links=[]
            ))
        
        return suggestions
    
    def _calculate_health_score(
        self, 
        pass_rate: float, 
        flakiness: float, 
        performance_data: Dict[str, Any],
        quality_data: Dict[str, Any]
    ) -> float:
        """Calculate overall test suite health score (0-100)."""
        
        # Base score from pass rate
        pass_rate_score = pass_rate * 40  # 40 points max
        
        # Deduct for flakiness
        flakiness_penalty = flakiness * 20  # 20 points max penalty
        
        # Performance score
        total_tests = len(self.test_metrics)
        slow_test_ratio = performance_data["slow_test_count"] / max(total_tests, 1)
        performance_score = max(0, 20 - (slow_test_ratio * 20))  # 20 points max
        
        # Quality score
        error_count = quality_data["total_error_count"]
        error_penalty = min(error_count * 0.5, 10)  # 10 points max penalty
        quality_score = max(0, 20 - error_penalty)  # 20 points max
        
        total_score = pass_rate_score + performance_score + quality_score - flakiness_penalty
        
        return max(0, min(100, total_score))
    
    def _assess_readiness(self, health_score: float, suggestions: List[ImprovementSuggestion]) -> str:
        """Assess overall test suite readiness."""
        
        critical_suggestions = [s for s in suggestions if s.priority == ImprovementPriority.CRITICAL]
        
        if health_score < 50 or len(critical_suggestions) > 0:
            return "critical_issues"
        elif health_score < 70:
            return "needs_attention"
        else:
            return "ready"
    
    def _generate_key_insights(
        self, 
        performance_data: Dict[str, Any],
        quality_data: Dict[str, Any], 
        resource_data: Dict[str, Any],
        suggestions: List[ImprovementSuggestion]
    ) -> List[str]:
        """Generate key insights from the analysis."""
        insights = []
        
        # Performance insights
        if performance_data["slow_test_count"] > 5:
            insights.append(f"🐌 {performance_data['slow_test_count']} slow tests are consuming {performance_data['total_slow_time']:.1f}s - major optimization opportunity")
        
        # Quality insights  
        if quality_data["flaky_test_count"] > 0:
            insights.append(f"🎲 {quality_data['flaky_test_count']} flaky tests are reducing CI reliability")
        
        if quality_data["error_hotspots"]:
            top_error = quality_data["error_hotspots"][0]
            insights.append(f"❌ {top_error[1]} {top_error[0]} errors suggest systematic issue")
        
        # Resource insights
        if resource_data["high_memory_test_count"] > 3:
            insights.append(f"💾 {resource_data['high_memory_test_count']} tests use excessive memory - potential for optimization")
        
        # Suggestion insights
        critical_count = len([s for s in suggestions if s.priority == ImprovementPriority.CRITICAL])
        if critical_count > 0:
            insights.append(f"🚨 {critical_count} critical issues need immediate attention")
        
        high_count = len([s for s in suggestions if s.priority == ImprovementPriority.HIGH])
        if high_count > 0:
            insights.append(f"⚠️ {high_count} high-priority improvements would significantly help")
        
        return insights[:5]  # Top 5 insights
    
    def _save_analysis_summary(self, analysis: TestSuiteAnalysis) -> None:
        """Save analysis summary to disk."""
        summary_file = self.analysis_dir / f"analysis_{analysis.analysis_id}.json"
        
        try:
            # Create a simplified version for JSON serialization
            summary = {
                "analysis_id": analysis.analysis_id,
                "timestamp": analysis.timestamp.isoformat(),
                "total_tests": analysis.total_tests,
                "overall_pass_rate": analysis.overall_pass_rate,
                "overall_flakiness": analysis.overall_flakiness,
                "health_score": analysis.health_score,
                "readiness_assessment": analysis.readiness_assessment,
                "key_insights": analysis.key_insights,
                "improvement_count": len(analysis.improvement_suggestions),
                "critical_issues": len([s for s in analysis.improvement_suggestions 
                                      if s.priority == ImprovementPriority.CRITICAL]),
                "slowest_test": analysis.slowest_tests[-1] if analysis.slowest_tests else None,
                "most_flaky_test": analysis.most_flaky_tests[0] if analysis.most_flaky_tests else None
            }
            
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save analysis summary: {e}")
    
    def generate_analysis_report(self, analysis: TestSuiteAnalysis) -> str:
        """Generate a comprehensive, AI-readable analysis report."""
        
        report_lines = []
        
        # Header
        report_lines.extend([
            "=" * 100,
            "TEST SUITE ANALYSIS & IMPROVEMENT REPORT",
            f"Analysis ID: {analysis.analysis_id}",
            f"Generated: {analysis.timestamp.isoformat()}",
            "=" * 100,
            ""
        ])
        
        # Executive Summary
        status_emojis = {
            "ready": "✅",
            "needs_attention": "⚠️",
            "critical_issues": "🚨"
        }
        
        status_emoji = status_emojis.get(analysis.readiness_assessment, "❓")
        
        report_lines.extend([
            f"🎯 EXECUTIVE SUMMARY",
            f"Overall Status: {status_emoji} {analysis.readiness_assessment.upper()}",
            f"Health Score: {analysis.health_score:.1f}/100",
            f"Pass Rate: {analysis.overall_pass_rate:.1%}",
            f"Flakiness: {analysis.overall_flakiness:.1%}",
            f"Total Tests: {analysis.total_tests}",
            f"Total Execution Time: {analysis.total_execution_time:.1f}s",
            ""
        ])
        
        # Key Insights
        if analysis.key_insights:
            report_lines.extend([
                "🔍 KEY INSIGHTS",
                *[f"   {insight}" for insight in analysis.key_insights],
                ""
            ])
        
        # Performance Analysis
        report_lines.extend([
            "⚡ PERFORMANCE ANALYSIS",
            f"Slowest Tests (Top 5):"
        ])
        
        for test_name, duration in analysis.slowest_tests[-5:]:
            report_lines.append(f"   • {test_name}: {duration:.2f}s")
        
        if analysis.performance_regressions:
            report_lines.extend([
                "Performance Regressions:",
                *[f"   • {reg['test_name']}: {reg['current_duration']:.2f}s ({reg['severity']})" 
                  for reg in analysis.performance_regressions[:3]]
            ])
        
        report_lines.append("")
        
        # Quality Analysis
        report_lines.extend([
            "🎯 QUALITY ANALYSIS",
            f"Most Flaky Tests (Top 5):"
        ])
        
        for test_name, flakiness in analysis.most_flaky_tests[:5]:
            report_lines.append(f"   • {test_name}: {flakiness:.1%} flaky")
        
        if analysis.error_hotspots:
            report_lines.extend([
                "Error Hotspots:",
                *[f"   • {error_type}: {count} occurrences" 
                  for error_type, count in analysis.error_hotspots[:5]]
            ])
        
        report_lines.append("")
        
        # Resource Analysis
        if analysis.memory_intensive_tests:
            report_lines.extend([
                "💾 RESOURCE ANALYSIS",
                "Memory Intensive Tests (Top 5):",
                *[f"   • {test_name}: {memory_mb:.1f}MB" 
                  for test_name, memory_mb in analysis.memory_intensive_tests[:5]],
                ""
            ])
        
        # Improvement Suggestions
        if analysis.improvement_suggestions:
            report_lines.extend([
                "💡 IMPROVEMENT SUGGESTIONS",
                ""
            ])
            
            # Group by priority
            by_priority = defaultdict(list)
            for suggestion in analysis.improvement_suggestions:
                by_priority[suggestion.priority].append(suggestion)
            
            for priority in [ImprovementPriority.CRITICAL, ImprovementPriority.HIGH, 
                           ImprovementPriority.MEDIUM, ImprovementPriority.LOW]:
                
                suggestions = by_priority[priority]
                if suggestions:
                    priority_emoji = {
                        ImprovementPriority.CRITICAL: "🚨",
                        ImprovementPriority.HIGH: "⚠️", 
                        ImprovementPriority.MEDIUM: "📋",
                        ImprovementPriority.LOW: "💭"
                    }[priority]
                    
                    report_lines.append(f"{priority_emoji} {priority.value.upper()} PRIORITY ({len(suggestions)} items)")
                    
                    for i, suggestion in enumerate(suggestions[:3], 1):  # Top 3 per priority
                        report_lines.extend([
                            f"   {i}. {suggestion.title}",
                            f"      {suggestion.description}",
                            f"      Effort: {suggestion.effort_estimate} | Confidence: {suggestion.confidence:.0%}",
                            ""
                        ])
                        
                        if suggestion.commands_to_run:
                            report_lines.extend([
                                f"      Commands to run:",
                                *[f"        $ {cmd}" for cmd in suggestion.commands_to_run[:2]],
                                ""
                            ])
        
        # Trend Analysis
        if hasattr(analysis, 'trends_over_time') and analysis.trends_over_time:
            report_lines.extend([
                "📈 TREND ANALYSIS",
                f"Quality Trend: {analysis.quality_trend}",
                f"Performance Trend: {analysis.performance_trend}",
                ""
            ])
        
        # Action Plan
        critical_suggestions = [s for s in analysis.improvement_suggestions 
                              if s.priority == ImprovementPriority.CRITICAL]
        high_suggestions = [s for s in analysis.improvement_suggestions 
                           if s.priority == ImprovementPriority.HIGH]
        
        if critical_suggestions or high_suggestions:
            report_lines.extend([
                "🎯 RECOMMENDED ACTION PLAN",
                ""
            ])
            
            if critical_suggestions:
                report_lines.extend([
                    "IMMEDIATE (Critical Issues):",
                    *[f"   • {s.title}" for s in critical_suggestions[:3]],
                    ""
                ])
            
            if high_suggestions:
                report_lines.extend([
                    "SHORT TERM (High Priority):",
                    *[f"   • {s.title}" for s in high_suggestions[:3]],
                    ""
                ])
            
            medium_suggestions = [s for s in analysis.improvement_suggestions 
                                if s.priority == ImprovementPriority.MEDIUM]
            if medium_suggestions:
                report_lines.extend([
                    "MEDIUM TERM (Medium Priority):",
                    *[f"   • {s.title}" for s in medium_suggestions[:3]],
                    ""
                ])
        
        # Footer
        report_lines.extend([
            "=" * 100,
            f"Report generated by AI Test Result Analyzer",
            f"For detailed implementation guidance, refer to individual suggestions above.",
            "=" * 100
        ])
        
        return "\n".join(report_lines)


# Example usage and integration tests
class TestResultAnalyzerTests:
    """Test the test result analyzer system itself."""
    
    def test_analyzer_initialization(self, temp_dir):
        """Test analyzer initializes correctly."""
        analyzer = TestResultAnalyzer(temp_dir)
        
        assert analyzer.project_root == temp_dir
        assert isinstance(analyzer.config, dict)
        assert isinstance(analyzer.test_metrics, dict)
    
    def test_metrics_update(self, temp_dir):
        """Test updating test metrics with results."""
        analyzer = TestResultAnalyzer(temp_dir)
        
        # Mock test results
        test_results = [
            {
                "test_name": "test_example",
                "file_path": "test_example.py",
                "passed": True,
                "duration": 2.5,
                "memory_usage": 10 * 1024 * 1024  # 10MB
            },
            {
                "test_name": "test_example",
                "file_path": "test_example.py", 
                "passed": False,
                "duration": 3.0,
                "error_message": "AssertionError: expected True"
            }
        ]
        
        analyzer.update_test_metrics(test_results)
        
        assert "test_example" in analyzer.test_metrics
        metrics = analyzer.test_metrics["test_example"]
        assert metrics.execution_count == 2
        assert metrics.success_count == 1
        assert metrics.failure_count == 1
        assert metrics.avg_duration > 0
        assert "AssertionError" in metrics.error_types
    
    def test_analysis_generation(self, temp_dir):
        """Test full analysis generation."""
        analyzer = TestResultAnalyzer(temp_dir)
        
        # Add some test metrics
        analyzer.test_metrics["slow_test"] = TestMetrics(
            test_name="slow_test",
            file_path="test_slow.py",
            execution_count=10,
            success_count=10,
            avg_duration=15.0,  # Slow test
            max_memory_usage=100.0  # High memory
        )
        
        analyzer.test_metrics["flaky_test"] = TestMetrics(
            test_name="flaky_test", 
            file_path="test_flaky.py",
            execution_count=10,
            success_count=7,
            failure_count=3,
            avg_duration=2.0,
            flakiness_score=0.42  # Flaky
        )
        
        # Generate analysis
        analysis = analyzer.analyze_test_suite()
        
        assert isinstance(analysis, TestSuiteAnalysis)
        assert analysis.total_tests == 2
        assert analysis.health_score >= 0
        assert len(analysis.improvement_suggestions) > 0
        assert len(analysis.key_insights) > 0
    
    def test_report_generation(self, temp_dir):
        """Test comprehensive report generation."""
        analyzer = TestResultAnalyzer(temp_dir)
        
        # Create simple analysis
        analysis = TestSuiteAnalysis(
            analysis_id="test_analysis",
            timestamp=datetime.now(),
            total_tests=5,
            total_execution_time=25.0,
            overall_pass_rate=0.8,
            overall_flakiness=0.1,
            slowest_tests=[("slow_test", 10.0)],
            fastest_tests=[("fast_test", 0.5)],
            performance_regressions=[],
            performance_improvements=[],
            most_flaky_tests=[("flaky_test", 0.3)],
            most_reliable_tests=[("reliable_test", 1.0)],
            error_hotspots=[("AssertionError", 5)],
            memory_intensive_tests=[("memory_test", 100.0)],
            cpu_intensive_tests=[],
            resource_waste_opportunities=[],
            coverage_gaps=[],
            untested_code_paths=[],
            quality_trend="stable",
            performance_trend="stable", 
            trends_over_time={},
            improvement_suggestions=[],
            health_score=75.0,
            readiness_assessment="ready",
            key_insights=["Test suite is generally healthy"]
        )
        
        report = analyzer.generate_analysis_report(analysis)
        
        assert "TEST SUITE ANALYSIS & IMPROVEMENT REPORT" in report
        assert "EXECUTIVE SUMMARY" in report
        assert "75.0/100" in report
        assert "80.0%" in report


# CLI integration for standalone usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze test results and generate improvement suggestions")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory")
    parser.add_argument("--output", type=Path, help="Output file for analysis report")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                       help="Report format")
    
    args = parser.parse_args()
    
    # Run analysis
    analyzer = TestResultAnalyzer(args.project_root)
    analysis = analyzer.analyze_test_suite()
    
    if args.format == "text":
        report = analyzer.generate_analysis_report(analysis)
        
        if args.output:
            args.output.write_text(report)
            print(f"📄 Analysis report saved to: {args.output}")
        else:
            print(report)
            
    elif args.format == "json":
        # Generate JSON summary
        summary = {
            "analysis_id": analysis.analysis_id,
            "timestamp": analysis.timestamp.isoformat(),
            "health_score": analysis.health_score,
            "readiness": analysis.readiness_assessment,
            "key_insights": analysis.key_insights,
            "improvements": len(analysis.improvement_suggestions),
            "critical_issues": len([s for s in analysis.improvement_suggestions 
                                  if s.priority == ImprovementPriority.CRITICAL])
        }
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"📄 Analysis summary saved to: {args.output}")
        else:
            print(json.dumps(summary, indent=2))
    
    # Exit with code based on readiness
    exit_code = 0 if analysis.readiness_assessment == "ready" else 1
    print(f"\n🎯 Overall Status: {analysis.readiness_assessment} (exit code: {exit_code})")
    exit(exit_code)