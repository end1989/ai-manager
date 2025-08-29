"""AI-Friendly Test Diagnostics Framework

This module provides comprehensive diagnostic capabilities for AI-driven iterative testing.
It creates detailed, actionable error reports that help AI systems understand and fix issues.
"""

import json
import sys
import traceback
import inspect
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
import pytest


class AITestDiagnostics:
    """AI-Friendly test diagnostics and error analysis."""

    def __init__(self):
        self.diagnostics = []
        self.environment_info = self._collect_environment_info()
        self.test_session_start = datetime.utcnow()

    def _collect_environment_info(self) -> Dict[str, Any]:
        """Collect comprehensive environment information."""
        try:
            import platform
            import psutil
            
            return {
                "python_version": sys.version,
                "platform": platform.platform(),
                "architecture": platform.architecture(),
                "cpu_count": os.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / 1024**3, 2),
                "disk_free_gb": round(psutil.disk_usage('.').free / 1024**3, 2),
                "working_directory": str(Path.cwd()),
                "python_path": sys.path[:3],  # First few entries
                "environment_vars": {k: v for k, v in os.environ.items() 
                                   if any(keyword in k.upper() for keyword in 
                                         ['MANAGER', 'TEST', 'PATH', 'HOME'])},
            }
        except ImportError:
            return {"error": "psutil not available for system info"}

    def diagnose_import_error(self, module_name: str, error: Exception) -> Dict[str, Any]:
        """Diagnose import errors with actionable solutions."""
        diagnosis = {
            "error_type": "ImportError",
            "module": module_name,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "possible_causes": [],
            "suggested_fixes": [],
            "verification_commands": []
        }

        # Analyze the specific import error
        if "No module named" in str(error):
            diagnosis["possible_causes"] = [
                f"Module '{module_name}' is not installed",
                "Virtual environment is not activated",
                "Module is in wrong location",
                "PYTHONPATH is incorrect"
            ]
            diagnosis["suggested_fixes"] = [
                f"pip install -e . # Install project in development mode",
                f"pip install {module_name.split('.')[0]} # Install specific package",
                "Check if you're in the correct virtual environment",
                "Verify the module exists in src/ directory"
            ]
            diagnosis["verification_commands"] = [
                "python -c \"import sys; print('\\n'.join(sys.path))\"",
                f"python -c \"import {module_name.split('.')[0]}\"",
                "pip list | grep -i manager",
                "ls -la src/"
            ]

        elif "circular import" in str(error).lower():
            diagnosis["possible_causes"] = [
                "Circular import dependency detected",
                "Module imports itself indirectly",
                "Import order issue"
            ]
            diagnosis["suggested_fixes"] = [
                "Move imports inside functions to break circular dependency",
                "Restructure module hierarchy",
                "Use lazy imports or TYPE_CHECKING blocks"
            ]

        return diagnosis

    def diagnose_database_error(self, error: Exception, context: Dict) -> Dict[str, Any]:
        """Diagnose database-related errors."""
        diagnosis = {
            "error_type": "DatabaseError",
            "error_message": str(error),
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
            "possible_causes": [],
            "suggested_fixes": [],
            "verification_commands": []
        }

        error_str = str(error).lower()
        
        if "no such table" in error_str:
            diagnosis["possible_causes"] = [
                "Database tables not created",
                "Wrong database file being used",
                "Database migration not run"
            ]
            diagnosis["suggested_fixes"] = [
                "Run: python -c \"from manager.store.models import create_db_and_tables; create_db_and_tables()\"",
                "Check MANAGER_DB_URL environment variable",
                "Verify database file exists and has correct permissions"
            ]

        elif "database is locked" in error_str:
            diagnosis["possible_causes"] = [
                "Another process is using the database",
                "Database connection not properly closed",
                "SQLite WAL mode issue"
            ]
            diagnosis["suggested_fixes"] = [
                "Close any other database connections",
                "Check for zombie processes: ps aux | grep python",
                "Remove database lock: rm manager.db-wal manager.db-shm"
            ]

        elif "permission denied" in error_str:
            diagnosis["possible_causes"] = [
                "Database file permissions incorrect",
                "Directory permissions incorrect",
                "Running as wrong user"
            ]
            diagnosis["suggested_fixes"] = [
                "chmod 664 manager.db",
                "chmod 775 .",
                "Check file ownership: ls -la manager.db"
            ]

        return diagnosis

    def diagnose_api_error(self, response_code: int, response_text: str, endpoint: str) -> Dict[str, Any]:
        """Diagnose API-related errors."""
        diagnosis = {
            "error_type": "APIError",
            "status_code": response_code,
            "endpoint": endpoint,
            "response_text": response_text[:500],  # Truncate long responses
            "timestamp": datetime.utcnow().isoformat(),
            "possible_causes": [],
            "suggested_fixes": [],
        }

        if response_code == 404:
            diagnosis["possible_causes"] = [
                "Endpoint URL is incorrect",
                "API server is not running",
                "Routing configuration issue"
            ]
            diagnosis["suggested_fixes"] = [
                "Check if API server is running: curl http://localhost:8000/health",
                "Verify endpoint exists: curl http://localhost:8000/docs",
                "Start API server: uvicorn manager.api.http:app --reload"
            ]

        elif response_code == 500:
            diagnosis["possible_causes"] = [
                "Internal server error",
                "Database connection issue",
                "Unhandled exception in API code"
            ]
            diagnosis["suggested_fixes"] = [
                "Check API server logs",
                "Verify database is accessible",
                "Test API endpoint manually with curl"
            ]

        elif response_code == 422:
            diagnosis["possible_causes"] = [
                "Invalid request data format",
                "Missing required fields",
                "Data validation failed"
            ]
            diagnosis["suggested_fixes"] = [
                "Check request JSON format",
                "Verify all required fields are present",
                "Check API documentation at /docs"
            ]

        return diagnosis

    def diagnose_subprocess_error(self, command: List[str], returncode: int, 
                                stdout: str, stderr: str) -> Dict[str, Any]:
        """Diagnose subprocess execution errors."""
        diagnosis = {
            "error_type": "SubprocessError",
            "command": command,
            "return_code": returncode,
            "stdout": stdout[:1000],  # Truncate long output
            "stderr": stderr[:1000],
            "timestamp": datetime.utcnow().isoformat(),
            "possible_causes": [],
            "suggested_fixes": [],
        }

        if returncode == 127:
            diagnosis["possible_causes"] = [
                "Command not found",
                "Executable not in PATH",
                "Wrong command name"
            ]
            diagnosis["suggested_fixes"] = [
                f"Install missing command: {command[0]}",
                f"Check if {command[0]} is in PATH: which {command[0]}",
                "Verify virtual environment is activated"
            ]

        elif "ModuleNotFoundError" in stderr:
            diagnosis["possible_causes"] = [
                "Python module not installed",
                "Wrong Python interpreter",
                "Virtual environment issue"
            ]
            diagnosis["suggested_fixes"] = [
                "pip install -e .",
                "Check Python interpreter: which python",
                "Activate virtual environment"
            ]

        elif "Permission denied" in stderr:
            diagnosis["possible_causes"] = [
                "File permissions incorrect",
                "Script not executable",
                "Directory permissions issue"
            ]
            diagnosis["suggested_fixes"] = [
                f"Make executable: chmod +x {' '.join(command)}",
                "Check directory permissions",
                "Run with appropriate user permissions"
            ]

        return diagnosis

    def create_fix_suggestions(self, test_name: str, error_type: str, 
                             context: Dict[str, Any]) -> List[str]:
        """Generate specific fix suggestions based on test failure context."""
        suggestions = []

        # Generic suggestions based on error type
        error_suggestions = {
            "ImportError": [
                "Ensure all dependencies are installed: pip install -e .[dev]",
                "Check that you're in the project root directory",
                "Verify virtual environment is activated",
                "Run: python -m pytest --collect-only to test imports"
            ],
            "DatabaseError": [
                "Initialize database: python -c \"from manager.store.models import create_db_and_tables; create_db_and_tables()\"",
                "Check database file permissions",
                "Verify MANAGER_DB_URL environment variable"
            ],
            "APIError": [
                "Start API server: uvicorn manager.api.http:app --reload",
                "Check API health: curl http://localhost:8000/health",
                "Verify API documentation: open http://localhost:8000/docs"
            ],
            "FileNotFoundError": [
                "Check if file paths are correct",
                "Verify working directory",
                "Ensure test fixtures create necessary files"
            ],
            "TimeoutError": [
                "Increase timeout values in test configuration",
                "Check for hanging processes",
                "Verify system resources are sufficient"
            ]
        }

        suggestions.extend(error_suggestions.get(error_type, []))

        # Test-specific suggestions
        if "test_database" in test_name.lower():
            suggestions.extend([
                "Check database schema with: sqlite3 manager.db '.schema'",
                "Verify database file exists: ls -la *.db"
            ])

        if "test_api" in test_name.lower():
            suggestions.extend([
                "Test API manually: pytest tests/integration/test_api_endpoints_real.py::TestAPIEndpointsReal::test_health_endpoint -v",
                "Check FastAPI logs for errors"
            ])

        if "test_cli" in test_name.lower():
            suggestions.extend([
                "Test CLI imports: python -c \"from cli.manager_cli import app\"",
                "Check CLI entry points in pyproject.toml"
            ])

        return list(set(suggestions))  # Remove duplicates

    def analyze_test_failure(self, test_item, call, report) -> Dict[str, Any]:
        """Comprehensive analysis of test failure with AI-friendly output."""
        analysis = {
            "test_name": test_item.name,
            "test_file": str(test_item.fspath),
            "test_function": test_item.function.__name__ if hasattr(test_item, 'function') else None,
            "failure_phase": report.when,
            "duration": getattr(report, 'duration', 0),
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.environment_info,
        }

        if report.failed and hasattr(report, 'longrepr'):
            # Extract error information
            if hasattr(report.longrepr, 'reprcrash'):
                crash_info = report.longrepr.reprcrash
                analysis.update({
                    "error_message": crash_info.message,
                    "error_file": crash_info.path,
                    "error_line": crash_info.lineno,
                })

            # Get full traceback
            if hasattr(report.longrepr, 'reprtraceback'):
                analysis["traceback"] = str(report.longrepr.reprtraceback)

            # Analyze specific error types
            exception_info = getattr(call, 'excinfo', None)
            if exception_info:
                exc_type = exception_info.type.__name__
                exc_value = str(exception_info.value)
                
                analysis["exception_type"] = exc_type
                analysis["exception_value"] = exc_value

                # Generate specific diagnostics
                if exc_type == "ImportError":
                    module_name = self._extract_module_name(exc_value)
                    analysis["diagnosis"] = self.diagnose_import_error(module_name, exception_info.value)
                
                elif "database" in exc_value.lower() or "sql" in exc_value.lower():
                    analysis["diagnosis"] = self.diagnose_database_error(
                        exception_info.value, {"test": test_item.name}
                    )

                # Generate fix suggestions
                analysis["fix_suggestions"] = self.create_fix_suggestions(
                    test_item.name, exc_type, analysis
                )

        return analysis

    def _extract_module_name(self, error_message: str) -> str:
        """Extract module name from import error message."""
        if "No module named" in error_message:
            start = error_message.find("'") + 1
            end = error_message.rfind("'")
            if start > 0 and end > start:
                return error_message[start:end]
        return "unknown"

    def save_diagnostic_report(self, analysis: Dict[str, Any], output_dir: Path = None):
        """Save diagnostic report to file for AI analysis."""
        if output_dir is None:
            output_dir = Path("test_diagnostics")
        
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        test_name = analysis.get("test_name", "unknown").replace("::", "_")
        filename = f"diagnostic_{test_name}_{timestamp}.json"
        
        report_path = output_dir / filename
        
        with open(report_path, "w") as f:
            json.dump(analysis, f, indent=2, default=str)
        
        return report_path

    def create_quick_fix_script(self, analysis: Dict[str, Any]) -> str:
        """Generate a shell script with potential fixes."""
        fixes = analysis.get("fix_suggestions", [])
        diagnosis = analysis.get("diagnosis", {})
        
        script_lines = [
            "#!/bin/bash",
            "# Auto-generated fix script for test failure",
            f"# Test: {analysis.get('test_name', 'unknown')}",
            f"# Error: {analysis.get('exception_type', 'unknown')}",
            "",
            "echo 'Attempting automated fixes...'",
            ""
        ]

        # Add verification commands from diagnosis
        if diagnosis and "verification_commands" in diagnosis:
            script_lines.extend([
                "echo 'Running verification commands...'",
                ""
            ])
            for cmd in diagnosis["verification_commands"]:
                script_lines.append(f"echo 'Running: {cmd}'")
                script_lines.append(f"{cmd} || echo 'Command failed: {cmd}'")
                script_lines.append("")

        # Add fix suggestions
        if fixes:
            script_lines.extend([
                "echo 'Applying suggested fixes...'",
                ""
            ])
            for fix in fixes[:5]:  # Limit to first 5 fixes
                if not fix.startswith("#") and ":" not in fix:  # Simple command check
                    script_lines.append(f"echo 'Trying: {fix}'")
                    script_lines.append(f"{fix} || echo 'Fix failed: {fix}'")
                    script_lines.append("")

        script_lines.append("echo 'Fix script completed.'")
        
        return "\n".join(script_lines)


# Global diagnostics instance
ai_diagnostics = AITestDiagnostics()


class AITestReporter:
    """Custom pytest reporter for AI-friendly output."""
    
    def __init__(self):
        self.failed_tests = []
        self.passed_tests = []
        self.diagnostic_reports = []

    def pytest_runtest_logreport(self, report):
        """Collect test results for analysis."""
        if report.when == "call":
            if report.failed:
                # Analyze failure immediately
                analysis = ai_diagnostics.analyze_test_failure(
                    report.nodeid, None, report
                )
                self.diagnostic_reports.append(analysis)
                self.failed_tests.append(report)
                
                # Save diagnostic report
                report_path = ai_diagnostics.save_diagnostic_report(analysis)
                print(f"\n🔍 Diagnostic report saved: {report_path}")
                
                # Create quick fix script
                fix_script = ai_diagnostics.create_quick_fix_script(analysis)
                fix_script_path = report_path.parent / f"fix_{report_path.stem}.sh"
                with open(fix_script_path, "w") as f:
                    f.write(fix_script)
                os.chmod(fix_script_path, 0o755)
                print(f"🛠️  Quick fix script: {fix_script_path}")
                
            elif report.passed:
                self.passed_tests.append(report)

    def pytest_sessionfinish(self, session):
        """Generate final AI-friendly report."""
        summary = {
            "session_summary": {
                "total_tests": len(self.passed_tests) + len(self.failed_tests),
                "passed": len(self.passed_tests),
                "failed": len(self.failed_tests),
                "success_rate": len(self.passed_tests) / max(1, len(self.passed_tests) + len(self.failed_tests)),
                "session_duration": (datetime.utcnow() - ai_diagnostics.test_session_start).total_seconds(),
            },
            "environment": ai_diagnostics.environment_info,
            "failed_tests_analysis": self.diagnostic_reports,
            "next_steps": self._generate_next_steps(),
        }

        # Save comprehensive report
        report_path = Path("test_diagnostics") / f"session_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n📊 Session report saved: {report_path}")
        
        # Print AI-friendly summary
        self._print_ai_summary(summary)

    def _generate_next_steps(self) -> List[str]:
        """Generate actionable next steps for fixing failures."""
        if not self.failed_tests:
            return ["All tests passed! 🎉"]

        steps = [
            "1. Review diagnostic reports in test_diagnostics/ directory",
            "2. Run suggested fix scripts (fix_*.sh files)",
            "3. Re-run failed tests individually with -v flag for detailed output",
        ]

        # Add specific steps based on failure patterns
        error_types = [report.get("exception_type") for report in self.diagnostic_reports]
        
        if "ImportError" in error_types:
            steps.append("4. Fix import issues: pip install -e .[dev]")
        
        if "DatabaseError" in error_types:
            steps.append("5. Initialize database: python -c \"from manager.store.models import create_db_and_tables; create_db_and_tables()\"")

        steps.extend([
            "6. Check environment setup with: python -c \"import manager; print('✅ Manager imports successfully')\"",
            "7. Run tests progressively: pytest tests/unit/ then tests/integration/",
        ])

        return steps

    def _print_ai_summary(self, summary):
        """Print concise AI-readable summary."""
        print("\n" + "="*60)
        print("🤖 AI-FRIENDLY TEST SUMMARY")
        print("="*60)
        
        stats = summary["session_summary"]
        print(f"✅ Passed: {stats['passed']}")
        print(f"❌ Failed: {stats['failed']}")
        print(f"📊 Success Rate: {stats['success_rate']:.1%}")
        print(f"⏱️  Duration: {stats['session_duration']:.2f}s")
        
        if self.diagnostic_reports:
            print(f"\n🔍 Failure Analysis:")
            for report in self.diagnostic_reports[:3]:  # Show first 3 failures
                print(f"   • {report['test_name']}: {report.get('exception_type', 'Unknown')}")
        
        print(f"\n📋 Next Steps:")
        for step in summary["next_steps"][:5]:  # Show first 5 steps
            print(f"   {step}")
        
        print("="*60)


def pytest_configure(config):
    """Configure AI-friendly pytest reporting."""
    config.pluginmanager.register(AITestReporter(), "ai_reporter")


# Utility functions for tests
def ai_assert(condition: bool, message: str, context: Dict[str, Any] = None):
    """AI-friendly assertion with diagnostic context."""
    if not condition:
        diagnosis = {
            "assertion_failed": message,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat(),
            "suggested_investigation": [
                f"Check the condition: {message}",
                "Review the context data provided",
                "Examine the test setup and fixtures"
            ]
        }
        
        # Save assertion failure diagnostic
        ai_diagnostics.save_diagnostic_report(diagnosis)
        
        # Enhanced assertion error
        enhanced_message = f"{message}\n\nDiagnostic context: {json.dumps(context, indent=2, default=str)}"
        raise AssertionError(enhanced_message)


def ai_skip_if_broken(condition: bool, reason: str):
    """Skip test if environment is broken, with diagnostic info."""
    if condition:
        diagnosis = {
            "test_skipped": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "environment_check": ai_diagnostics.environment_info,
        }
        ai_diagnostics.save_diagnostic_report(diagnosis)
        pytest.skip(reason)