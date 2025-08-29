"""Test health monitoring and reporting system for AI-friendly debugging.

This module provides comprehensive health monitoring for the test suite,
enabling AI systems to quickly identify systemic issues and patterns
in test failures across the entire codebase.

Key Features:
- Real-time test execution monitoring
- Pattern recognition in failures
- Resource usage tracking
- Test environment validation
- Automated health reporting
- Dependency analysis
- Performance regression detection
"""

import asyncio
import json
import os
import sys
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
import pytest
import psutil


@dataclass
class TestHealthMetrics:
    """Health metrics for individual test cases."""
    
    test_name: str
    execution_time: float
    memory_peak: int  # bytes
    memory_avg: int  # bytes
    cpu_percent: float
    passed: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    dependencies: Set[str] = field(default_factory=set)
    resource_warnings: List[str] = field(default_factory=list)


@dataclass
class TestSuiteHealth:
    """Overall health status of the test suite."""
    
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    execution_time: float
    memory_peak: int
    avg_test_time: float
    slow_tests: List[str]  # Tests taking > 5 seconds
    flaky_tests: List[str]  # Tests with inconsistent results
    resource_intensive_tests: List[str]  # Tests using >50MB memory
    error_patterns: Dict[str, int]  # Error type frequency
    dependency_issues: List[str]
    environment_issues: List[str]
    recommendations: List[str]


class TestHealthMonitor:
    """AI-friendly test health monitoring system."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.health_dir = project_root / ".test_health"
        self.health_dir.mkdir(exist_ok=True)
        
        self.metrics: List[TestHealthMetrics] = []
        self.suite_history: List[TestSuiteHealth] = []
        self.load_history()
        
        # Resource monitoring
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss
        
    def load_history(self) -> None:
        """Load historical test health data."""
        history_file = self.health_dir / "suite_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.suite_history = [
                        TestSuiteHealth(**item) for item in data[-50:]  # Keep last 50 runs
                    ]
            except Exception as e:
                print(f"Warning: Could not load test history: {e}")
    
    def save_history(self) -> None:
        """Save test health history to disk."""
        history_file = self.health_dir / "suite_history.json"
        try:
            data = [
                {
                    "total_tests": h.total_tests,
                    "passed_tests": h.passed_tests,
                    "failed_tests": h.failed_tests,
                    "skipped_tests": h.skipped_tests,
                    "execution_time": h.execution_time,
                    "memory_peak": h.memory_peak,
                    "avg_test_time": h.avg_test_time,
                    "slow_tests": h.slow_tests,
                    "flaky_tests": h.flaky_tests,
                    "resource_intensive_tests": h.resource_intensive_tests,
                    "error_patterns": h.error_patterns,
                    "dependency_issues": h.dependency_issues,
                    "environment_issues": h.environment_issues,
                    "recommendations": h.recommendations,
                } for h in self.suite_history
            ]
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save test history: {e}")
    
    def monitor_test_execution(self, test_name: str) -> "TestMonitorContext":
        """Context manager for monitoring individual test execution."""
        return TestMonitorContext(self, test_name)
    
    def analyze_suite_health(self) -> TestSuiteHealth:
        """Analyze overall test suite health."""
        if not self.metrics:
            return TestSuiteHealth(
                total_tests=0, passed_tests=0, failed_tests=0, skipped_tests=0,
                execution_time=0.0, memory_peak=0, avg_test_time=0.0,
                slow_tests=[], flaky_tests=[], resource_intensive_tests=[],
                error_patterns={}, dependency_issues=[], environment_issues=[],
                recommendations=["No test metrics available - run some tests first"]
            )
        
        total_tests = len(self.metrics)
        passed_tests = sum(1 for m in self.metrics if m.passed)
        failed_tests = sum(1 for m in self.metrics if not m.passed)
        
        total_time = sum(m.execution_time for m in self.metrics)
        avg_time = total_time / total_tests if total_tests > 0 else 0
        
        # Identify problematic tests
        slow_tests = [m.test_name for m in self.metrics if m.execution_time > 5.0]
        resource_intensive = [m.test_name for m in self.metrics if m.memory_peak > 50 * 1024 * 1024]
        
        # Error pattern analysis
        error_patterns = defaultdict(int)
        for m in self.metrics:
            if m.error_type:
                error_patterns[m.error_type] += 1
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            passed_tests, failed_tests, slow_tests, resource_intensive, dict(error_patterns)
        )
        
        suite_health = TestSuiteHealth(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=0,  # TODO: Track skipped tests
            execution_time=total_time,
            memory_peak=max((m.memory_peak for m in self.metrics), default=0),
            avg_test_time=avg_time,
            slow_tests=slow_tests,
            flaky_tests=self._detect_flaky_tests(),
            resource_intensive_tests=resource_intensive,
            error_patterns=dict(error_patterns),
            dependency_issues=self._analyze_dependency_issues(),
            environment_issues=self._analyze_environment_issues(),
            recommendations=recommendations
        )
        
        self.suite_history.append(suite_health)
        self.save_history()
        
        return suite_health
    
    def _generate_recommendations(
        self, 
        passed: int, 
        failed: int, 
        slow_tests: List[str], 
        resource_intensive: List[str],
        error_patterns: Dict[str, int]
    ) -> List[str]:
        """Generate AI-friendly recommendations for test improvements."""
        recommendations = []
        
        # Pass rate analysis
        total = passed + failed
        if total > 0:
            pass_rate = passed / total
            if pass_rate < 0.8:
                recommendations.append(
                    f"LOW PASS RATE: {pass_rate:.1%} - Focus on fixing failing tests before adding new ones"
                )
            elif pass_rate == 1.0:
                recommendations.append("EXCELLENT: All tests passing - consider adding edge case tests")
        
        # Performance issues
        if slow_tests:
            recommendations.append(
                f"SLOW TESTS: {len(slow_tests)} tests >5s - Consider mocking or parallelization for: {', '.join(slow_tests[:3])}"
            )
        
        if resource_intensive:
            recommendations.append(
                f"MEMORY USAGE: {len(resource_intensive)} tests >50MB - Review memory management in: {', '.join(resource_intensive[:3])}"
            )
        
        # Error pattern analysis
        if "ImportError" in error_patterns:
            recommendations.append(
                f"IMPORT ISSUES: {error_patterns['ImportError']} import failures - Check dependencies and PYTHONPATH"
            )
        
        if "AssertionError" in error_patterns:
            recommendations.append(
                f"ASSERTION FAILURES: {error_patterns['AssertionError']} assertion errors - Review test expectations vs. actual behavior"
            )
        
        if "TimeoutError" in error_patterns:
            recommendations.append(
                f"TIMEOUT ISSUES: {error_patterns['TimeoutError']} timeout errors - Increase timeouts or optimize async operations"
            )
        
        # Historical trends
        if len(self.suite_history) >= 2:
            current_pass_rate = passed / total if total > 0 else 0
            prev_pass_rate = self.suite_history[-1].passed_tests / max(self.suite_history[-1].total_tests, 1)
            
            if current_pass_rate < prev_pass_rate - 0.1:
                recommendations.append(
                    f"REGRESSION: Pass rate dropped from {prev_pass_rate:.1%} to {current_pass_rate:.1%} - Recent changes may have introduced bugs"
                )
        
        if not recommendations:
            recommendations.append("HEALTHY: Test suite is performing well - continue current practices")
        
        return recommendations
    
    def _detect_flaky_tests(self) -> List[str]:
        """Detect tests with inconsistent behavior across runs."""
        # This would require multiple run history - simplified for now
        flaky = []
        
        # Check for tests that have both passed and failed in recent history
        test_results = defaultdict(list)
        for suite in self.suite_history[-5:]:  # Last 5 runs
            # This is a simplified implementation
            # In practice, we'd track individual test results across runs
            pass
        
        return flaky
    
    def _analyze_dependency_issues(self) -> List[str]:
        """Analyze dependency-related issues in tests."""
        issues = []
        
        # Check for common dependency problems
        for metric in self.metrics:
            if metric.error_type == "ImportError":
                issues.append(f"Import failure in {metric.test_name}: {metric.error_message}")
            elif "module" in (metric.error_message or "").lower():
                issues.append(f"Possible module issue in {metric.test_name}")
        
        # Check for missing test dependencies
        test_files = list(self.project_root.glob("tests/**/*.py"))
        for test_file in test_files:
            try:
                content = test_file.read_text()
                if "import pytest" in content and "pytest" not in sys.modules:
                    issues.append(f"pytest import found but not available: {test_file}")
            except Exception:
                pass
        
        return issues
    
    def _analyze_environment_issues(self) -> List[str]:
        """Analyze environment-related issues."""
        issues = []
        
        # Check Python version compatibility
        if sys.version_info < (3, 8):
            issues.append(f"Python {sys.version_info.major}.{sys.version_info.minor} may be too old - recommend Python 3.8+")
        
        # Check available memory
        memory = psutil.virtual_memory()
        if memory.available < 500 * 1024 * 1024:  # Less than 500MB
            issues.append(f"Low available memory: {memory.available / 1024 / 1024:.0f}MB - tests may fail due to resource constraints")
        
        # Check disk space
        disk = psutil.disk_usage('.')
        if disk.free < 100 * 1024 * 1024:  # Less than 100MB
            issues.append(f"Low disk space: {disk.free / 1024 / 1024:.0f}MB - tests may fail to create temporary files")
        
        # Check for required directories
        required_dirs = ['src', 'tests']
        for dir_name in required_dirs:
            if not (self.project_root / dir_name).exists():
                issues.append(f"Missing required directory: {dir_name}")
        
        return issues
    
    def generate_health_report(self, suite_health: TestSuiteHealth) -> str:
        """Generate a comprehensive, AI-readable health report."""
        report_lines = []
        
        # Header
        report_lines.append("=" * 80)
        report_lines.append("TEST SUITE HEALTH REPORT")
        report_lines.append(f"Generated: {datetime.now().isoformat()}")
        report_lines.append("=" * 80)
        
        # Summary
        report_lines.append("\n📊 SUMMARY")
        report_lines.append(f"Total Tests: {suite_health.total_tests}")
        report_lines.append(f"Passed: {suite_health.passed_tests} ({suite_health.passed_tests/max(suite_health.total_tests, 1):.1%})")
        report_lines.append(f"Failed: {suite_health.failed_tests}")
        report_lines.append(f"Execution Time: {suite_health.execution_time:.2f}s")
        report_lines.append(f"Average Test Time: {suite_health.avg_test_time:.2f}s")
        report_lines.append(f"Memory Peak: {suite_health.memory_peak / 1024 / 1024:.1f}MB")
        
        # Issues
        if suite_health.slow_tests:
            report_lines.append(f"\n🐌 SLOW TESTS ({len(suite_health.slow_tests)})")
            for test in suite_health.slow_tests:
                report_lines.append(f"  - {test}")
        
        if suite_health.resource_intensive_tests:
            report_lines.append(f"\n💾 MEMORY INTENSIVE TESTS ({len(suite_health.resource_intensive_tests)})")
            for test in suite_health.resource_intensive_tests:
                report_lines.append(f"  - {test}")
        
        if suite_health.error_patterns:
            report_lines.append(f"\n❌ ERROR PATTERNS")
            for error_type, count in sorted(suite_health.error_patterns.items(), key=lambda x: x[1], reverse=True):
                report_lines.append(f"  {error_type}: {count} occurrences")
        
        if suite_health.dependency_issues:
            report_lines.append(f"\n📦 DEPENDENCY ISSUES")
            for issue in suite_health.dependency_issues:
                report_lines.append(f"  - {issue}")
        
        if suite_health.environment_issues:
            report_lines.append(f"\n🔧 ENVIRONMENT ISSUES")
            for issue in suite_health.environment_issues:
                report_lines.append(f"  - {issue}")
        
        # Recommendations
        if suite_health.recommendations:
            report_lines.append(f"\n💡 RECOMMENDATIONS")
            for i, rec in enumerate(suite_health.recommendations, 1):
                report_lines.append(f"  {i}. {rec}")
        
        # Historical trend
        if len(self.suite_history) >= 2:
            report_lines.append(f"\n📈 TRENDS (Last 5 Runs)")
            recent_runs = self.suite_history[-5:]
            
            pass_rates = [r.passed_tests / max(r.total_tests, 1) for r in recent_runs]
            avg_times = [r.avg_test_time for r in recent_runs]
            
            report_lines.append(f"Pass Rate Trend: {' → '.join(f'{pr:.1%}' for pr in pass_rates)}")
            report_lines.append(f"Performance Trend: {' → '.join(f'{at:.2f}s' for at in avg_times)}")
        
        report_lines.append("\n" + "=" * 80)
        
        return "\n".join(report_lines)


class TestMonitorContext:
    """Context manager for monitoring individual test execution."""
    
    def __init__(self, monitor: TestHealthMonitor, test_name: str):
        self.monitor = monitor
        self.test_name = test_name
        self.start_time = 0.0
        self.start_memory = 0
        self.memory_samples = []
        self.passed = True
        self.error_type = None
        self.error_message = None
    
    def __enter__(self) -> "TestMonitorContext":
        self.start_time = time.time()
        self.start_memory = self.monitor.process.memory_info().rss
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time
        end_memory = self.monitor.process.memory_info().rss
        memory_peak = max(self.start_memory, end_memory, *self.memory_samples)
        memory_avg = sum([self.start_memory, end_memory] + self.memory_samples) / max(len(self.memory_samples) + 2, 1)
        
        if exc_type:
            self.passed = False
            self.error_type = exc_type.__name__
            self.error_message = str(exc_val) if exc_val else ""
        
        # Create metrics
        metrics = TestHealthMetrics(
            test_name=self.test_name,
            execution_time=execution_time,
            memory_peak=memory_peak,
            memory_avg=int(memory_avg),
            cpu_percent=0.0,  # TODO: Implement CPU monitoring
            passed=self.passed,
            error_type=self.error_type,
            error_message=self.error_message,
        )
        
        # Add resource warnings
        if execution_time > 5.0:
            metrics.resource_warnings.append(f"Slow execution: {execution_time:.2f}s")
        
        if memory_peak > 50 * 1024 * 1024:
            metrics.resource_warnings.append(f"High memory usage: {memory_peak / 1024 / 1024:.1f}MB")
        
        self.monitor.metrics.append(metrics)


# Global health monitor instance
_health_monitor = None


def get_health_monitor() -> TestHealthMonitor:
    """Get the global test health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        project_root = Path(__file__).parent.parent
        _health_monitor = TestHealthMonitor(project_root)
    return _health_monitor


# Pytest plugin for automatic health monitoring
class HealthMonitorPlugin:
    """Pytest plugin for automatic test health monitoring."""
    
    def __init__(self):
        self.monitor = get_health_monitor()
        self.current_context = None
    
    def pytest_runtest_setup(self, item):
        """Called before each test runs."""
        self.current_context = self.monitor.monitor_test_execution(item.name)
        self.current_context.__enter__()
    
    def pytest_runtest_teardown(self, item, nextitem):
        """Called after each test completes."""
        if self.current_context:
            self.current_context.__exit__(None, None, None)
            self.current_context = None
    
    def pytest_sessionfinish(self, session, exitstatus):
        """Called when the test session finishes."""
        suite_health = self.monitor.analyze_suite_health()
        report = self.monitor.generate_health_report(suite_health)
        
        # Save report to file
        report_file = self.monitor.health_dir / f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_file.write_text(report)
        
        # Print summary
        print("\n" + "=" * 50)
        print("TEST HEALTH SUMMARY")
        print("=" * 50)
        print(f"Pass Rate: {suite_health.passed_tests}/{suite_health.total_tests} ({suite_health.passed_tests/max(suite_health.total_tests, 1):.1%})")
        print(f"Total Time: {suite_health.execution_time:.2f}s")
        print(f"Report saved: {report_file}")
        
        if suite_health.recommendations:
            print(f"\nTop Recommendation: {suite_health.recommendations[0]}")


# Example usage and integration tests
class TestHealthMonitorSystem:
    """Test the health monitoring system itself."""
    
    def test_health_monitor_initialization(self, temp_dir):
        """Test that health monitor initializes correctly."""
        monitor = TestHealthMonitor(temp_dir)
        
        assert monitor.project_root == temp_dir
        assert monitor.health_dir.exists()
        assert isinstance(monitor.metrics, list)
        assert isinstance(monitor.suite_history, list)
    
    def test_test_monitoring_context(self, temp_dir):
        """Test individual test monitoring."""
        monitor = TestHealthMonitor(temp_dir)
        
        # Monitor a successful test
        with monitor.monitor_test_execution("test_success"):
            time.sleep(0.1)  # Simulate test execution
        
        assert len(monitor.metrics) == 1
        metric = monitor.metrics[0]
        assert metric.test_name == "test_success"
        assert metric.passed is True
        assert metric.execution_time >= 0.1
    
    def test_test_monitoring_with_failure(self, temp_dir):
        """Test monitoring of failed tests."""
        monitor = TestHealthMonitor(temp_dir)
        
        # Monitor a failed test
        try:
            with monitor.monitor_test_execution("test_failure"):
                raise ValueError("Test error message")
        except ValueError:
            pass
        
        assert len(monitor.metrics) == 1
        metric = monitor.metrics[0]
        assert metric.test_name == "test_failure"
        assert metric.passed is False
        assert metric.error_type == "ValueError"
        assert metric.error_message == "Test error message"
    
    def test_suite_health_analysis(self, temp_dir):
        """Test suite health analysis."""
        monitor = TestHealthMonitor(temp_dir)
        
        # Add some mock metrics
        monitor.metrics = [
            TestHealthMetrics("test1", 1.0, 1024*1024, 1024*1024, 5.0, True),
            TestHealthMetrics("test2", 6.0, 60*1024*1024, 50*1024*1024, 10.0, True),  # Slow & memory intensive
            TestHealthMetrics("test3", 0.5, 512*1024, 512*1024, 2.0, False, "AssertionError", "Test failed"),
        ]
        
        health = monitor.analyze_suite_health()
        
        assert health.total_tests == 3
        assert health.passed_tests == 2
        assert health.failed_tests == 1
        assert "test2" in health.slow_tests
        assert "test2" in health.resource_intensive_tests
        assert health.error_patterns["AssertionError"] == 1
        assert len(health.recommendations) > 0
    
    def test_health_report_generation(self, temp_dir):
        """Test health report generation."""
        monitor = TestHealthMonitor(temp_dir)
        
        # Create sample health data
        suite_health = TestSuiteHealth(
            total_tests=10,
            passed_tests=8,
            failed_tests=2,
            skipped_tests=0,
            execution_time=45.5,
            memory_peak=128*1024*1024,
            avg_test_time=4.55,
            slow_tests=["slow_test1", "slow_test2"],
            flaky_tests=[],
            resource_intensive_tests=["memory_hog"],
            error_patterns={"AssertionError": 2},
            dependency_issues=["Missing module: requests"],
            environment_issues=["Low disk space"],
            recommendations=["Fix failing assertions", "Optimize slow tests"]
        )
        
        report = monitor.generate_health_report(suite_health)
        
        assert "TEST SUITE HEALTH REPORT" in report
        assert "Total Tests: 10" in report
        assert "Passed: 8 (80.0%)" in report
        assert "slow_test1" in report
        assert "AssertionError: 2 occurrences" in report
        assert "Fix failing assertions" in report
    
    def test_history_persistence(self, temp_dir):
        """Test that health history is saved and loaded correctly."""
        monitor = TestHealthMonitor(temp_dir)
        
        # Create and save some history
        suite_health = TestSuiteHealth(
            total_tests=5, passed_tests=5, failed_tests=0, skipped_tests=0,
            execution_time=10.0, memory_peak=64*1024*1024, avg_test_time=2.0,
            slow_tests=[], flaky_tests=[], resource_intensive_tests=[],
            error_patterns={}, dependency_issues=[], environment_issues=[],
            recommendations=["All tests passing"]
        )
        
        monitor.suite_history.append(suite_health)
        monitor.save_history()
        
        # Create new monitor and verify it loads the history
        new_monitor = TestHealthMonitor(temp_dir)
        assert len(new_monitor.suite_history) == 1
        assert new_monitor.suite_history[0].total_tests == 5
        assert new_monitor.suite_history[0].passed_tests == 5


if __name__ == "__main__":
    # Example standalone usage
    monitor = get_health_monitor()
    
    # Simulate some test executions
    with monitor.monitor_test_execution("example_test_1"):
        time.sleep(0.1)
    
    try:
        with monitor.monitor_test_execution("example_test_2"):
            raise AssertionError("Example failure")
    except AssertionError:
        pass
    
    # Generate health report
    health = monitor.analyze_suite_health()
    report = monitor.generate_health_report(health)
    print(report)