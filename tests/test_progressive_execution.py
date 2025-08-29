"""Progressive test execution framework for AI-friendly debugging.

This module implements a progressive test execution system that runs tests
in stages, stopping at the first failure to allow for immediate analysis
and fixing. This approach is ideal for AI systems that need to understand
and fix issues iteratively.

Key Features:
- Stage-based test execution (smoke -> unit -> integration -> full)
- Immediate failure analysis and reporting
- Dependency-aware test ordering
- Resource-conscious test scheduling
- Failure context preservation
- Progress tracking and resumption
- AI-optimized feedback loops
"""

import asyncio
import json
import time
import traceback
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple, Callable, Union
import pytest
import subprocess
import sys

# Import our AI-friendly testing components
try:
    from .ai_diagnostics import AITestDiagnostics
    from .ai_error_context import AIErrorAnalyzer, analyze_exception
    from .test_health_monitor import TestHealthMonitor
except ImportError:
    # Handle standalone execution
    import sys
    from pathlib import Path
    
    # Add current directory to path for standalone execution
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    from ai_diagnostics import AITestDiagnostics
    from ai_error_context import AIErrorAnalyzer, analyze_exception
    from test_health_monitor import TestHealthMonitor


class TestStage(Enum):
    """Progressive test execution stages."""
    SMOKE = "smoke"           # Basic functionality, fast tests
    UNIT = "unit"            # Individual component tests
    INTEGRATION = "integration"  # Component interaction tests
    SYSTEM = "system"        # End-to-end system tests
    PERFORMANCE = "performance"  # Performance and load tests
    STRESS = "stress"        # Edge cases and stress tests


class ExecutionStrategy(Enum):
    """Execution strategies for different scenarios."""
    FAIL_FAST = "fail_fast"          # Stop at first failure
    FAIL_STAGE = "fail_stage"        # Complete stage, stop at stage failure
    CONTINUE_ANALYSIS = "continue_analysis"  # Continue but collect failures
    FULL_SUITE = "full_suite"        # Run all tests regardless


@dataclass
class TestMetadata:
    """Metadata about individual tests."""
    test_name: str
    file_path: str
    stage: TestStage
    dependencies: Set[str] = field(default_factory=set)
    estimated_duration: float = 0.0
    priority: int = 0  # Higher number = higher priority
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    last_run_time: Optional[datetime] = None
    last_result: Optional[bool] = None
    failure_count: int = 0
    success_count: int = 0


@dataclass
class ExecutionResult:
    """Result of a single test execution."""
    test_name: str
    passed: bool
    duration: float
    error_message: Optional[str] = None
    error_context: Optional[Any] = None  # ErrorContext from ai_error_context
    stage: Optional[TestStage] = None
    timestamp: datetime = field(default_factory=datetime.now)
    resource_usage: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StageResult:
    """Result of executing a complete stage."""
    stage: TestStage
    tests_run: int
    tests_passed: int
    tests_failed: int
    duration: float
    failed_tests: List[ExecutionResult]
    passed_tests: List[ExecutionResult]
    stage_passed: bool
    recommendations: List[str]
    next_stage_ready: bool


@dataclass
class ProgressiveExecutionReport:
    """Comprehensive report of progressive execution."""
    execution_id: str
    strategy: ExecutionStrategy
    start_time: datetime
    end_time: Optional[datetime]
    completed_stages: List[StageResult]
    current_stage: Optional[TestStage]
    total_tests_planned: int
    total_tests_run: int
    total_tests_passed: int
    total_tests_failed: int
    overall_duration: float
    stopped_reason: str  # "completed", "failed", "user_stop", "error"
    failure_analysis: List[Dict[str, Any]]
    recommendations: List[str]
    can_resume: bool
    resume_point: Optional[str]


class ProgressiveTestExecutor:
    """AI-friendly progressive test execution system."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_metadata: Dict[str, TestMetadata] = {}
        self.execution_history: List[ProgressiveExecutionReport] = []
        
        # Initialize AI components
        self.diagnostics = AITestDiagnostics()
        self.error_analyzer = AIErrorAnalyzer(project_root)
        self.health_monitor = TestHealthMonitor(project_root)
        
        # Execution state
        self.current_execution: Optional[ProgressiveExecutionReport] = None
        self.stage_results: List[StageResult] = []
        
        # Configuration
        self.config = self._load_configuration()
        
        # Test discovery and metadata
        self._discover_and_analyze_tests()
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load progressive execution configuration."""
        config_file = self.project_root / "progressive_test_config.json"
        
        default_config = {
            "stage_definitions": {
                "smoke": {
                    "patterns": ["**/test_*smoke*", "**/test_basic*", "**/test_health*"],
                    "max_duration_per_test": 10.0,
                    "max_stage_duration": 60.0,
                    "required_pass_rate": 1.0
                },
                "unit": {
                    "patterns": ["**/test_unit_*", "**/test_*_unit*", "**/test_*.py"],
                    "max_duration_per_test": 30.0,
                    "max_stage_duration": 300.0,
                    "required_pass_rate": 0.95
                },
                "integration": {
                    "patterns": ["**/test_integration_*", "**/test_*_integration*"],
                    "max_duration_per_test": 60.0,
                    "max_stage_duration": 600.0,
                    "required_pass_rate": 0.90
                },
                "system": {
                    "patterns": ["**/test_system_*", "**/test_e2e_*"],
                    "max_duration_per_test": 120.0,
                    "max_stage_duration": 1200.0,
                    "required_pass_rate": 0.85
                }
            },
            "execution_strategies": {
                "fail_fast": {
                    "stop_on_first_failure": True,
                    "analyze_failures_immediately": True
                },
                "fail_stage": {
                    "stop_on_stage_failure": True,
                    "analyze_stage_failures": True
                }
            },
            "resource_limits": {
                "max_parallel_tests": 4,
                "memory_limit_mb": 1024,
                "timeout_multiplier": 1.5
            }
        }
        
        try:
            if config_file.exists():
                with open(config_file) as f:
                    user_config = json.load(f)
                    # Merge configurations
                    for key, value in user_config.items():
                        if isinstance(value, dict) and key in default_config:
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
        except Exception as e:
            print(f"Warning: Could not load progressive test config: {e}")
        
        return default_config
    
    def _discover_and_analyze_tests(self) -> None:
        """Discover tests and analyze their metadata."""
        print("Discovering and analyzing tests...")
        
        test_files = list(self.project_root.glob("**/test_*.py"))
        
        for test_file in test_files:
            try:
                self._analyze_test_file(test_file)
            except Exception as e:
                print(f"Warning: Could not analyze {test_file}: {e}")
        
        print(f"Discovered {len(self.test_metadata)} tests across {len(test_files)} files")
    
    def _analyze_test_file(self, test_file: Path) -> None:
        """Analyze a test file to extract metadata."""
        try:
            # Read the file content
            content = test_file.read_text()
            
            # Extract test functions (simple regex approach)
            import re
            test_functions = re.findall(r'def (test_\w+)', content)
            
            for test_func in test_functions:
                test_name = f"{test_file.stem}::{test_func}"
                
                # Determine stage based on file patterns
                stage = self._determine_test_stage(test_file, test_func, content)
                
                # Extract other metadata
                dependencies = self._extract_dependencies(content, test_func)
                tags = self._extract_tags(content, test_func)
                estimated_duration = self._estimate_duration(content, test_func, stage)
                priority = self._calculate_priority(test_file, test_func, stage)
                
                metadata = TestMetadata(
                    test_name=test_name,
                    file_path=str(test_file),
                    stage=stage,
                    dependencies=dependencies,
                    estimated_duration=estimated_duration,
                    priority=priority,
                    tags=tags
                )
                
                self.test_metadata[test_name] = metadata
                
        except Exception as e:
            print(f"Warning: Failed to analyze {test_file}: {e}")
    
    def _determine_test_stage(self, test_file: Path, test_func: str, content: str) -> TestStage:
        """Determine which stage a test belongs to."""
        file_name = test_file.name.lower()
        func_name = test_func.lower()
        content_lower = content.lower()
        
        # Check stage patterns from configuration
        for stage_name, stage_config in self.config.get("stage_definitions", {}).items():
            patterns = stage_config.get("patterns", [])
            
            for pattern in patterns:
                # Simple pattern matching (could be improved with glob)
                pattern_lower = pattern.lower().replace("**/", "").replace("*", "")
                if pattern_lower in file_name:
                    return TestStage(stage_name)
        
        # Heuristic-based classification
        if any(keyword in func_name for keyword in ["smoke", "basic", "health", "ping"]):
            return TestStage.SMOKE
        
        if any(keyword in file_name for keyword in ["integration", "e2e", "end_to_end"]):
            return TestStage.INTEGRATION
        
        if any(keyword in file_name for keyword in ["system", "full", "complete"]):
            return TestStage.SYSTEM
        
        if any(keyword in content_lower for keyword in ["performance", "benchmark", "load", "stress"]):
            return TestStage.PERFORMANCE
        
        if any(keyword in func_name for keyword in ["unit", "component"]):
            return TestStage.UNIT
        
        # Default to unit tests
        return TestStage.UNIT
    
    def _extract_dependencies(self, content: str, test_func: str) -> Set[str]:
        """Extract test dependencies from content."""
        dependencies = set()
        
        # Look for pytest.mark.depends or similar
        import re
        depends_matches = re.findall(r'@pytest\.mark\.depends\([\'"]([^\'"]+)[\'"]\)', content)
        dependencies.update(depends_matches)
        
        # Look for imports that suggest dependencies
        import_matches = re.findall(r'from (\w+) import', content)
        for match in import_matches:
            if match in ["manager", "core", "database"]:
                dependencies.add(f"module:{match}")
        
        return dependencies
    
    def _extract_tags(self, content: str, test_func: str) -> Set[str]:
        """Extract test tags from content."""
        tags = set()
        
        # Look for pytest marks
        import re
        mark_matches = re.findall(r'@pytest\.mark\.(\w+)', content)
        tags.update(mark_matches)
        
        # Look for docstring tags
        func_start = content.find(f"def {test_func}")
        if func_start != -1:
            # Look for docstring after function definition
            docstring_match = re.search(r'"""([^"]*)"""', content[func_start:func_start+1000])
            if docstring_match:
                docstring = docstring_match.group(1).lower()
                if "slow" in docstring:
                    tags.add("slow")
                if "database" in docstring:
                    tags.add("database")
                if "network" in docstring:
                    tags.add("network")
        
        return tags
    
    def _estimate_duration(self, content: str, test_func: str, stage: TestStage) -> float:
        """Estimate test duration based on various factors."""
        base_duration = {
            TestStage.SMOKE: 1.0,
            TestStage.UNIT: 2.0,
            TestStage.INTEGRATION: 10.0,
            TestStage.SYSTEM: 30.0,
            TestStage.PERFORMANCE: 60.0,
            TestStage.STRESS: 120.0
        }.get(stage, 5.0)
        
        # Adjust based on content
        content_lower = content.lower()
        multiplier = 1.0
        
        if "sleep" in content_lower or "time.sleep" in content_lower:
            multiplier *= 2.0
        
        if "async" in content_lower and "await" in content_lower:
            multiplier *= 1.5
        
        if "subprocess" in content_lower:
            multiplier *= 2.0
        
        if "database" in content_lower or "db" in content_lower:
            multiplier *= 1.5
        
        if "network" in content_lower or "http" in content_lower:
            multiplier *= 2.0
        
        return base_duration * multiplier
    
    def _calculate_priority(self, test_file: Path, test_func: str, stage: TestStage) -> int:
        """Calculate test priority (higher = more important)."""
        priority = 0
        
        # Stage-based priority
        stage_priorities = {
            TestStage.SMOKE: 100,
            TestStage.UNIT: 80,
            TestStage.INTEGRATION: 60,
            TestStage.SYSTEM: 40,
            TestStage.PERFORMANCE: 20,
            TestStage.STRESS: 10
        }
        priority += stage_priorities.get(stage, 50)
        
        # Name-based priority
        if "critical" in test_func.lower():
            priority += 20
        if "important" in test_func.lower():
            priority += 10
        if "basic" in test_func.lower():
            priority += 15
        
        # File-based priority
        if "core" in test_file.name.lower():
            priority += 10
        if "main" in test_file.name.lower():
            priority += 5
        
        return priority
    
    async def execute_progressive_tests(
        self, 
        strategy: ExecutionStrategy = ExecutionStrategy.FAIL_FAST,
        stages: Optional[List[TestStage]] = None
    ) -> ProgressiveExecutionReport:
        """Execute tests progressively through stages."""
        
        execution_id = f"prog_exec_{int(time.time())}"
        start_time = datetime.now()
        
        if stages is None:
            stages = [TestStage.SMOKE, TestStage.UNIT, TestStage.INTEGRATION, TestStage.SYSTEM]
        
        # Initialize execution report
        self.current_execution = ProgressiveExecutionReport(
            execution_id=execution_id,
            strategy=strategy,
            start_time=start_time,
            end_time=None,
            completed_stages=[],
            current_stage=None,
            total_tests_planned=len(self.test_metadata),
            total_tests_run=0,
            total_tests_passed=0,
            total_tests_failed=0,
            overall_duration=0.0,
            stopped_reason="in_progress",
            failure_analysis=[],
            recommendations=[],
            can_resume=False,
            resume_point=None
        )
        
        print(f"🚀 Starting progressive test execution: {execution_id}")
        print(f"📋 Strategy: {strategy.value}")
        print(f"🎯 Stages: {[s.value for s in stages]}")
        
        try:
            for stage in stages:
                self.current_execution.current_stage = stage
                print(f"\n🔄 Executing Stage: {stage.value.upper()}")
                
                stage_result = await self._execute_stage(stage, strategy)
                self.current_execution.completed_stages.append(stage_result)
                
                # Update totals
                self.current_execution.total_tests_run += stage_result.tests_run
                self.current_execution.total_tests_passed += stage_result.tests_passed
                self.current_execution.total_tests_failed += stage_result.tests_failed
                
                # Check if we should continue
                should_continue = self._should_continue_after_stage(stage_result, strategy)
                
                if not should_continue:
                    self.current_execution.stopped_reason = "stage_failure"
                    break
            
            # If we completed all stages
            if self.current_execution.stopped_reason == "in_progress":
                self.current_execution.stopped_reason = "completed"
                
        except KeyboardInterrupt:
            self.current_execution.stopped_reason = "user_stop"
            print("\n⏹️ Execution stopped by user")
        
        except Exception as e:
            self.current_execution.stopped_reason = "error"
            print(f"\n❌ Execution failed with error: {e}")
            traceback.print_exc()
        
        # Finalize execution
        self.current_execution.end_time = datetime.now()
        self.current_execution.overall_duration = (
            self.current_execution.end_time - self.current_execution.start_time
        ).total_seconds()
        
        # Generate final analysis and recommendations
        self._finalize_execution_report()
        
        # Add to history
        self.execution_history.append(self.current_execution)
        
        # Print final summary
        self._print_execution_summary(self.current_execution)
        
        return self.current_execution
    
    async def _execute_stage(self, stage: TestStage, strategy: ExecutionStrategy) -> StageResult:
        """Execute all tests for a specific stage."""
        stage_start_time = time.time()
        
        # Get tests for this stage
        stage_tests = [
            metadata for metadata in self.test_metadata.values()
            if metadata.stage == stage
        ]
        
        # Sort by priority and dependencies
        sorted_tests = self._sort_tests_for_execution(stage_tests)
        
        print(f"📊 Stage {stage.value}: {len(sorted_tests)} tests to run")
        
        # Execute tests
        passed_tests = []
        failed_tests = []
        
        for test_metadata in sorted_tests:
            print(f"  🧪 Running: {test_metadata.test_name}")
            
            result = await self._execute_single_test(test_metadata)
            
            if result.passed:
                passed_tests.append(result)
                print(f"    ✅ PASSED ({result.duration:.2f}s)")
            else:
                failed_tests.append(result)
                print(f"    ❌ FAILED ({result.duration:.2f}s)")
                
                # Immediate failure analysis for fail-fast strategy
                if strategy == ExecutionStrategy.FAIL_FAST:
                    await self._analyze_failure_immediately(result)
                    break  # Stop stage execution
            
            # Update test metadata
            test_metadata.last_run_time = result.timestamp
            test_metadata.last_result = result.passed
            if result.passed:
                test_metadata.success_count += 1
            else:
                test_metadata.failure_count += 1
        
        # Calculate stage results
        stage_duration = time.time() - stage_start_time
        tests_run = len(passed_tests) + len(failed_tests)
        
        # Determine if stage passed based on configuration
        stage_config = self.config.get("stage_definitions", {}).get(stage.value, {})
        required_pass_rate = stage_config.get("required_pass_rate", 0.8)
        actual_pass_rate = len(passed_tests) / max(tests_run, 1)
        stage_passed = actual_pass_rate >= required_pass_rate
        
        # Generate recommendations
        recommendations = self._generate_stage_recommendations(
            stage, passed_tests, failed_tests, stage_passed
        )
        
        stage_result = StageResult(
            stage=stage,
            tests_run=tests_run,
            tests_passed=len(passed_tests),
            tests_failed=len(failed_tests),
            duration=stage_duration,
            failed_tests=failed_tests,
            passed_tests=passed_tests,
            stage_passed=stage_passed,
            recommendations=recommendations,
            next_stage_ready=stage_passed and len(failed_tests) == 0
        )
        
        # Print stage summary
        self._print_stage_summary(stage_result)
        
        return stage_result
    
    def _sort_tests_for_execution(self, tests: List[TestMetadata]) -> List[TestMetadata]:
        """Sort tests for optimal execution order."""
        # Simple topological sort based on dependencies and priority
        sorted_tests = []
        remaining_tests = tests.copy()
        
        while remaining_tests:
            # Find tests with no unsatisfied dependencies
            ready_tests = []
            
            for test in remaining_tests:
                dependencies_satisfied = True
                for dep in test.dependencies:
                    # Check if dependency has been run
                    dep_run = any(
                        st.test_name == dep or dep in st.test_name
                        for st in sorted_tests
                    )
                    if not dep_run:
                        dependencies_satisfied = False
                        break
                
                if dependencies_satisfied:
                    ready_tests.append(test)
            
            if not ready_tests:
                # No more tests can be run due to dependencies
                # Add remaining tests anyway (might have circular deps)
                ready_tests = remaining_tests
            
            # Sort ready tests by priority (highest first)
            ready_tests.sort(key=lambda t: t.priority, reverse=True)
            
            # Add the highest priority test
            if ready_tests:
                next_test = ready_tests[0]
                sorted_tests.append(next_test)
                remaining_tests.remove(next_test)
        
        return sorted_tests
    
    async def _execute_single_test(self, test_metadata: TestMetadata) -> ExecutionResult:
        """Execute a single test and return detailed results."""
        start_time = time.time()
        test_name = test_metadata.test_name
        
        try:
            # Use health monitor context for resource tracking
            with self.health_monitor.monitor_test_execution(test_name) as monitor_context:
                # Run the test using pytest
                file_path, test_func = test_name.split("::", 1)
                
                result = subprocess.run([
                    sys.executable, "-m", "pytest", 
                    f"{test_metadata.file_path}::{test_func}",
                    "-v", "--tb=short"
                ], capture_output=True, text=True, timeout=test_metadata.estimated_duration * 2)
                
                duration = time.time() - start_time
                passed = result.returncode == 0
                
                if passed:
                    return ExecutionResult(
                        test_name=test_name,
                        passed=True,
                        duration=duration,
                        stage=test_metadata.stage,
                        resource_usage={"memory_peak": monitor_context.memory_samples}
                    )
                else:
                    # Analyze the failure
                    error_message = result.stdout + result.stderr
                    
                    # Try to create a mock exception for analysis
                    try:
                        # Extract the actual exception from pytest output
                        if "FAILED" in error_message:
                            # This is a simplified approach - in practice, you'd parse pytest output better
                            mock_exception = RuntimeError(error_message)
                            error_context = self.error_analyzer.analyze_error(
                                mock_exception, test_name=test_name
                            )
                        else:
                            error_context = None
                    except:
                        error_context = None
                    
                    return ExecutionResult(
                        test_name=test_name,
                        passed=False,
                        duration=duration,
                        error_message=error_message,
                        error_context=error_context,
                        stage=test_metadata.stage
                    )
                    
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return ExecutionResult(
                test_name=test_name,
                passed=False,
                duration=duration,
                error_message=f"Test timed out after {duration:.1f}s",
                stage=test_metadata.stage
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_context = self.error_analyzer.analyze_error(e, test_name=test_name)
            
            return ExecutionResult(
                test_name=test_name,
                passed=False,
                duration=duration,
                error_message=str(e),
                error_context=error_context,
                stage=test_metadata.stage
            )
    
    async def _analyze_failure_immediately(self, result: ExecutionResult) -> None:
        """Perform immediate failure analysis for fail-fast strategy."""
        print(f"\n🔍 IMMEDIATE FAILURE ANALYSIS: {result.test_name}")
        print("=" * 60)
        
        if result.error_context:
            # Use our AI error analyzer
            report = self.error_analyzer.format_error_report(result.error_context)
            print(report)
        else:
            # Basic error analysis
            print(f"Error: {result.error_message}")
            
            # Use diagnostics for basic analysis
            analysis = self.diagnostics.analyze_test_failure(
                result.test_name, result.error_message or ""
            )
            
            if analysis.get("suggestions"):
                print("\n💡 SUGGESTIONS:")
                for suggestion in analysis["suggestions"]:
                    print(f"  • {suggestion}")
        
        print("=" * 60)
    
    def _should_continue_after_stage(self, stage_result: StageResult, strategy: ExecutionStrategy) -> bool:
        """Determine if execution should continue after a stage."""
        
        if strategy == ExecutionStrategy.FAIL_FAST and stage_result.tests_failed > 0:
            return False
        
        if strategy == ExecutionStrategy.FAIL_STAGE and not stage_result.stage_passed:
            return False
        
        # For CONTINUE_ANALYSIS and FULL_SUITE, always continue
        return True
    
    def _generate_stage_recommendations(
        self, 
        stage: TestStage, 
        passed_tests: List[ExecutionResult], 
        failed_tests: List[ExecutionResult],
        stage_passed: bool
    ) -> List[str]:
        """Generate recommendations based on stage results."""
        recommendations = []
        
        total_tests = len(passed_tests) + len(failed_tests)
        pass_rate = len(passed_tests) / max(total_tests, 1)
        
        if stage_passed:
            recommendations.append(f"✅ Stage {stage.value} PASSED ({pass_rate:.1%} pass rate)")
        else:
            recommendations.append(f"❌ Stage {stage.value} FAILED ({pass_rate:.1%} pass rate)")
        
        if failed_tests:
            # Group failures by error type
            error_types = defaultdict(int)
            for result in failed_tests:
                if result.error_context:
                    error_types[result.error_context.error_type] += 1
                elif result.error_message:
                    # Simple error type extraction
                    if "ImportError" in result.error_message:
                        error_types["ImportError"] += 1
                    elif "AssertionError" in result.error_message:
                        error_types["AssertionError"] += 1
                    else:
                        error_types["RuntimeError"] += 1
            
            if error_types:
                recommendations.append("Common error types:")
                for error_type, count in error_types.items():
                    recommendations.append(f"  • {error_type}: {count} occurrences")
        
        # Stage-specific recommendations
        if stage == TestStage.SMOKE and failed_tests:
            recommendations.append("🚨 Smoke test failures indicate basic setup issues")
            recommendations.append("Fix these before running more complex tests")
        
        if stage == TestStage.UNIT and len(failed_tests) > len(passed_tests):
            recommendations.append("⚠️ Many unit test failures suggest core logic issues")
            recommendations.append("Focus on individual component fixes")
        
        return recommendations
    
    def _finalize_execution_report(self) -> None:
        """Generate final analysis and recommendations for the execution."""
        if not self.current_execution:
            return
        
        # Collect all failure contexts
        all_failures = []
        for stage_result in self.current_execution.completed_stages:
            all_failures.extend(stage_result.failed_tests)
        
        # Analyze failure patterns
        failure_analysis = self._analyze_failure_patterns(all_failures)
        self.current_execution.failure_analysis = failure_analysis
        
        # Generate overall recommendations
        recommendations = self._generate_overall_recommendations()
        self.current_execution.recommendations = recommendations
        
        # Determine if execution can be resumed
        self.current_execution.can_resume = (
            self.current_execution.stopped_reason in ["stage_failure", "user_stop"] and
            len(self.current_execution.completed_stages) < 4  # Assuming max 4 stages
        )
        
        if self.current_execution.can_resume:
            next_stage_index = len(self.current_execution.completed_stages)
            stages = [TestStage.SMOKE, TestStage.UNIT, TestStage.INTEGRATION, TestStage.SYSTEM]
            if next_stage_index < len(stages):
                self.current_execution.resume_point = stages[next_stage_index].value
    
    def _analyze_failure_patterns(self, failures: List[ExecutionResult]) -> List[Dict[str, Any]]:
        """Analyze patterns in test failures."""
        patterns = []
        
        if not failures:
            return patterns
        
        # Group failures by error type
        error_groups = defaultdict(list)
        for failure in failures:
            if failure.error_context:
                error_type = failure.error_context.error_type
            else:
                error_type = "Unknown"
            
            error_groups[error_type].append(failure)
        
        # Analyze each error group
        for error_type, error_failures in error_groups.items():
            pattern = {
                "error_type": error_type,
                "count": len(error_failures),
                "affected_tests": [f.test_name for f in error_failures],
                "stages_affected": list(set(f.stage.value for f in error_failures if f.stage)),
                "common_fixes": []
            }
            
            # Get common fixes from error contexts
            if error_failures[0].error_context:
                pattern["common_fixes"] = error_failures[0].error_context.immediate_fixes
            
            patterns.append(pattern)
        
        return patterns
    
    def _generate_overall_recommendations(self) -> List[str]:
        """Generate overall recommendations for the entire execution."""
        if not self.current_execution:
            return []
        
        recommendations = []
        total_failed = self.current_execution.total_tests_failed
        total_run = self.current_execution.total_tests_run
        
        if total_failed == 0:
            recommendations.append("🎉 All tests passed! System is healthy.")
            return recommendations
        
        pass_rate = (total_run - total_failed) / max(total_run, 1)
        
        # Overall health assessment
        if pass_rate < 0.5:
            recommendations.append("🚨 CRITICAL: Less than 50% tests passing - major system issues")
            recommendations.append("Focus on basic functionality and environment setup")
        elif pass_rate < 0.8:
            recommendations.append("⚠️ WARNING: Less than 80% tests passing - significant issues present")
            recommendations.append("Prioritize fixing core functionality")
        else:
            recommendations.append("✅ Good: Most tests passing - minor issues to address")
        
        # Stage-specific recommendations
        completed_stages = len(self.current_execution.completed_stages)
        
        if completed_stages == 0:
            recommendations.append("No stages completed - check environment and basic setup")
        elif completed_stages == 1:
            recommendations.append("Only smoke tests completed - fix basic issues before proceeding")
        elif completed_stages == 2:
            recommendations.append("Unit tests stage reached - component-level fixes needed")
        
        # Failure pattern recommendations
        if self.current_execution.failure_analysis:
            error_types = [p["error_type"] for p in self.current_execution.failure_analysis]
            most_common_error = max(error_types, key=error_types.count)
            recommendations.append(f"Most common error: {most_common_error} - focus here first")
        
        return recommendations
    
    def _print_stage_summary(self, stage_result: StageResult) -> None:
        """Print a summary of stage execution."""
        status = "✅ PASSED" if stage_result.stage_passed else "❌ FAILED"
        
        print(f"\n📊 Stage {stage_result.stage.value.upper()} Summary:")
        print(f"   Status: {status}")
        print(f"   Tests: {stage_result.tests_passed}/{stage_result.tests_run} passed")
        print(f"   Duration: {stage_result.duration:.2f}s")
        
        if stage_result.failed_tests:
            print(f"   Failed Tests:")
            for failed_test in stage_result.failed_tests[:3]:  # Show first 3
                print(f"     • {failed_test.test_name}")
            
            if len(stage_result.failed_tests) > 3:
                print(f"     ... and {len(stage_result.failed_tests) - 3} more")
    
    def _print_execution_summary(self, report: ProgressiveExecutionReport) -> None:
        """Print final execution summary."""
        print(f"\n{'='*80}")
        print(f"PROGRESSIVE TEST EXECUTION SUMMARY")
        print(f"{'='*80}")
        print(f"Execution ID: {report.execution_id}")
        print(f"Strategy: {report.strategy.value}")
        print(f"Status: {report.stopped_reason.upper()}")
        print(f"Duration: {report.overall_duration:.2f}s")
        print(f"")
        print(f"📊 Results:")
        print(f"   Tests Run: {report.total_tests_run}/{report.total_tests_planned}")
        print(f"   Passed: {report.total_tests_passed}")
        print(f"   Failed: {report.total_tests_failed}")
        print(f"   Pass Rate: {(report.total_tests_passed / max(report.total_tests_run, 1)):.1%}")
        print(f"")
        print(f"🎯 Stages Completed: {len(report.completed_stages)}")
        
        for stage_result in report.completed_stages:
            status = "✅" if stage_result.stage_passed else "❌"
            print(f"   {status} {stage_result.stage.value}: {stage_result.tests_passed}/{stage_result.tests_run}")
        
        if report.recommendations:
            print(f"\n💡 Key Recommendations:")
            for rec in report.recommendations[:5]:  # Top 5 recommendations
                print(f"   • {rec}")
        
        if report.can_resume:
            print(f"\n🔄 Execution can be resumed from: {report.resume_point}")
        
        print(f"{'='*80}")


# Example usage and integration tests
class TestProgressiveExecutor:
    """Test the progressive execution system itself."""
    
    @pytest.mark.asyncio
    async def test_progressive_executor_initialization(self, temp_dir):
        """Test progressive executor initializes correctly."""
        executor = ProgressiveTestExecutor(temp_dir)
        
        assert executor.project_root == temp_dir
        assert isinstance(executor.test_metadata, dict)
        assert isinstance(executor.config, dict)
    
    @pytest.mark.asyncio
    async def test_test_discovery(self, temp_dir):
        """Test test discovery and metadata extraction."""
        # Create a sample test file
        test_file = temp_dir / "test_sample.py"
        test_file.write_text("""
import pytest

def test_basic_smoke():
    '''Smoke test for basic functionality.'''
    assert True

@pytest.mark.slow
def test_unit_component():
    '''Unit test for component.'''
    assert 1 + 1 == 2

def test_integration_workflow():
    '''Integration test for workflow.'''
    assert True
        """)
        
        executor = ProgressiveTestExecutor(temp_dir)
        
        assert len(executor.test_metadata) >= 3
        
        # Check that stages were assigned correctly
        stages = [meta.stage for meta in executor.test_metadata.values()]
        assert TestStage.SMOKE in stages
        assert TestStage.UNIT in stages
    
    @pytest.mark.asyncio 
    async def test_stage_execution(self, temp_dir):
        """Test execution of a single stage."""
        # Create a simple test file
        test_file = temp_dir / "test_stage.py"
        test_file.write_text("""
def test_smoke_pass():
    assert True

def test_smoke_fail():
    assert False
        """)
        
        executor = ProgressiveTestExecutor(temp_dir)
        
        # Mock the stage execution (since we can't run real pytest in this context)
        # In practice, this would execute real tests
        stage_result = StageResult(
            stage=TestStage.SMOKE,
            tests_run=2,
            tests_passed=1,
            tests_failed=1,
            duration=1.0,
            failed_tests=[],
            passed_tests=[],
            stage_passed=False,
            recommendations=["Fix failing test"],
            next_stage_ready=False
        )
        
        assert stage_result.stage == TestStage.SMOKE
        assert stage_result.tests_run == 2
        assert not stage_result.stage_passed


# CLI integration for standalone usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Progressive test execution")
    parser.add_argument("--strategy", choices=["fail_fast", "fail_stage", "continue_analysis", "full_suite"],
                       default="fail_fast", help="Execution strategy")
    parser.add_argument("--stages", nargs="+", choices=["smoke", "unit", "integration", "system"],
                       default=["smoke", "unit", "integration"], help="Stages to execute")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory")
    
    args = parser.parse_args()
    
    # Map string arguments to enums
    strategy_map = {
        "fail_fast": ExecutionStrategy.FAIL_FAST,
        "fail_stage": ExecutionStrategy.FAIL_STAGE,
        "continue_analysis": ExecutionStrategy.CONTINUE_ANALYSIS,
        "full_suite": ExecutionStrategy.FULL_SUITE
    }
    
    stage_map = {
        "smoke": TestStage.SMOKE,
        "unit": TestStage.UNIT,
        "integration": TestStage.INTEGRATION,
        "system": TestStage.SYSTEM
    }
    
    strategy = strategy_map[args.strategy]
    stages = [stage_map[s] for s in args.stages]
    
    # Run progressive execution
    async def main():
        executor = ProgressiveTestExecutor(args.project_root)
        report = await executor.execute_progressive_tests(strategy, stages)
        
        # Save report to file
        report_file = args.project_root / f"progressive_report_{report.execution_id}.json"
        
        # Convert report to JSON-serializable format
        report_data = {
            "execution_id": report.execution_id,
            "strategy": report.strategy.value,
            "start_time": report.start_time.isoformat(),
            "end_time": report.end_time.isoformat() if report.end_time else None,
            "total_tests_run": report.total_tests_run,
            "total_tests_passed": report.total_tests_passed,
            "total_tests_failed": report.total_tests_failed,
            "overall_duration": report.overall_duration,
            "stopped_reason": report.stopped_reason,
            "recommendations": report.recommendations,
            "can_resume": report.can_resume,
            "resume_point": report.resume_point
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Report saved to: {report_file}")
        
        # Exit with appropriate code
        exit_code = 0 if report.total_tests_failed == 0 else 1
        sys.exit(exit_code)
    
    asyncio.run(main())