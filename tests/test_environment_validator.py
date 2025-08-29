"""Automated test environment validation for AI-friendly testing.

This module provides comprehensive environment validation to ensure that
the testing environment is properly configured and ready for reliable
test execution. It catches environment issues before they cause mysterious
test failures.

Key Features:
- Python environment validation
- Package dependency checking
- Directory structure validation
- System resource verification
- Database connectivity testing
- Network connectivity checking
- Configuration validation
- Pre-test environment setup
"""

import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import importlib
import importlib.util
import platform
import psutil
import pytest


class ValidationLevel(Enum):
    """Validation levels for different testing scenarios."""
    MINIMAL = "minimal"      # Basic Python and pytest
    STANDARD = "standard"    # Common dependencies + structure
    COMPREHENSIVE = "comprehensive"  # Full system validation
    CUSTOM = "custom"        # User-defined validation rules


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    BLOCKER = "blocker"      # Must fix before running any tests
    CRITICAL = "critical"    # Will cause many test failures
    WARNING = "warning"      # May cause some test failures
    INFO = "info"           # Good to know but not blocking


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    check_name: str
    passed: bool
    severity: ValidationSeverity
    message: str
    details: Dict[str, Any]
    fix_suggestions: List[str]
    execution_time: float


@dataclass
class EnvironmentReport:
    """Comprehensive environment validation report."""
    validation_level: ValidationLevel
    total_checks: int
    passed_checks: int
    failed_checks: int
    blockers: List[ValidationResult]
    critical_issues: List[ValidationResult]
    warnings: List[ValidationResult]
    info_items: List[ValidationResult]
    overall_status: str  # "READY", "NEEDS_FIXES", "BLOCKED"
    execution_time: float
    environment_info: Dict[str, Any]
    recommendations: List[str]


class EnvironmentValidator:
    """AI-friendly environment validation system."""
    
    def __init__(self, project_root: Path, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.project_root = project_root
        self.validation_level = validation_level
        self.results: List[ValidationResult] = []
        
        # Load validation configuration
        self.config = self._load_validation_config()
        
        # Determine which checks to run based on level
        self.checks_to_run = self._get_checks_for_level(validation_level)
    
    def validate_environment(self) -> EnvironmentReport:
        """Run comprehensive environment validation."""
        start_time = time.time()
        self.results = []
        
        print("Running environment validation...")
        
        # Run all validation checks
        for check_name in self.checks_to_run:
            try:
                check_method = getattr(self, f"_validate_{check_name}")
                result = check_method()
                self.results.append(result)
                
                # Print progress
                status = "PASS" if result.passed else "FAIL"
                print(f"[{status}] {result.check_name}: {result.message}")
                
            except Exception as e:
                # If validation check itself fails, record it
                result = ValidationResult(
                    check_name=check_name,
                    passed=False,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Validation check failed: {e}",
                    details={"exception": str(e)},
                    fix_suggestions=["Check the validation system itself"],
                    execution_time=0.0
                )
                self.results.append(result)
                print(f"[FAIL] {check_name}: Validation check failed")
        
        # Analyze results
        total_time = time.time() - start_time
        report = self._generate_report(total_time)
        
        return report
    
    def _load_validation_config(self) -> Dict[str, Any]:
        """Load validation configuration."""
        config_file = self.project_root / "test_config.json"
        
        # Default configuration
        default_config = {
            "required_packages": [
                "pytest", "pydantic", "sqlmodel", "fastapi", "typer"
            ],
            "optional_packages": [
                "black", "ruff", "mypy", "coverage", "psutil"
            ],
            "required_directories": [
                "src", "tests", "src/manager"
            ],
            "required_files": [
                "pyproject.toml", "src/manager/__init__.py"
            ],
            "python_version_min": "3.8",
            "memory_min_mb": 512,
            "disk_space_min_mb": 100,
            "database_url": "sqlite:///test.db",
        }
        
        try:
            if config_file.exists():
                import json
                with open(config_file) as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            print(f"Warning: Could not load test config: {e}")
        
        return default_config
    
    def _get_checks_for_level(self, level: ValidationLevel) -> List[str]:
        """Get list of checks to run for given validation level."""
        
        minimal_checks = [
            "python_version",
            "pytest_available",
            "basic_imports"
        ]
        
        standard_checks = minimal_checks + [
            "required_packages",
            "directory_structure", 
            "basic_files",
            "system_resources",
            "permissions"
        ]
        
        comprehensive_checks = standard_checks + [
            "optional_packages",
            "database_connectivity",
            "network_connectivity",
            "subprocess_execution",
            "file_operations",
            "environment_variables",
            "system_configuration"
        ]
        
        level_mapping = {
            ValidationLevel.MINIMAL: minimal_checks,
            ValidationLevel.STANDARD: standard_checks,
            ValidationLevel.COMPREHENSIVE: comprehensive_checks,
            ValidationLevel.CUSTOM: self.config.get("custom_checks", standard_checks)
        }
        
        return level_mapping[level]
    
    def _validate_python_version(self) -> ValidationResult:
        """Validate Python version meets requirements."""
        start_time = time.time()
        
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        required_version = self.config.get("python_version_min", "3.8")
        
        # Parse version numbers
        current_parts = [int(x) for x in current_version.split(".")]
        required_parts = [int(x) for x in required_version.split(".")]
        
        # Compare versions
        version_ok = current_parts >= required_parts
        
        if version_ok:
            message = f"Python {current_version} meets minimum requirement ({required_version})"
            severity = ValidationSeverity.INFO
            fix_suggestions = []
        else:
            message = f"Python {current_version} is below minimum requirement ({required_version})"
            severity = ValidationSeverity.BLOCKER
            fix_suggestions = [
                f"Upgrade Python to {required_version} or higher",
                "Use pyenv to manage Python versions",
                "Update your virtual environment"
            ]
        
        return ValidationResult(
            check_name="Python Version",
            passed=version_ok,
            severity=severity,
            message=message,
            details={
                "current_version": current_version,
                "required_version": required_version,
                "executable": sys.executable,
                "platform": platform.platform()
            },
            fix_suggestions=fix_suggestions,
            execution_time=time.time() - start_time
        )
    
    def _validate_pytest_available(self) -> ValidationResult:
        """Validate pytest is available and working."""
        start_time = time.time()
        
        try:
            import pytest
            pytest_version = pytest.__version__
            
            # Try running pytest --version
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                message = f"pytest {pytest_version} is working correctly"
                passed = True
                severity = ValidationSeverity.INFO
                fix_suggestions = []
            else:
                message = f"pytest {pytest_version} import works but command fails"
                passed = False
                severity = ValidationSeverity.CRITICAL
                fix_suggestions = [
                    "Reinstall pytest: pip install --upgrade pytest",
                    "Check PATH and PYTHONPATH settings"
                ]
        
        except ImportError:
            message = "pytest is not installed"
            passed = False
            severity = ValidationSeverity.BLOCKER
            fix_suggestions = [
                "Install pytest: pip install pytest",
                "Add pytest to requirements.txt"
            ]
        
        except Exception as e:
            message = f"pytest validation failed: {e}"
            passed = False
            severity = ValidationSeverity.CRITICAL
            fix_suggestions = [
                "Reinstall pytest",
                "Check Python environment"
            ]
        
        return ValidationResult(
            check_name="pytest Availability",
            passed=passed,
            severity=severity,
            message=message,
            details={"pytest_version": locals().get("pytest_version", "unknown")},
            fix_suggestions=fix_suggestions,
            execution_time=time.time() - start_time
        )
    
    def _validate_basic_imports(self) -> ValidationResult:
        """Validate basic Python imports work."""
        start_time = time.time()
        
        essential_modules = ["os", "sys", "pathlib", "json", "subprocess", "time"]
        failed_imports = []
        
        for module_name in essential_modules:
            try:
                importlib.import_module(module_name)
            except ImportError:
                failed_imports.append(module_name)
        
        if not failed_imports:
            message = f"All {len(essential_modules)} essential modules import successfully"
            passed = True
            severity = ValidationSeverity.INFO
            fix_suggestions = []
        else:
            message = f"Failed to import {len(failed_imports)} essential modules: {', '.join(failed_imports)}"
            passed = False
            severity = ValidationSeverity.BLOCKER
            fix_suggestions = [
                "Check Python installation integrity",
                "Reinstall Python",
                "Check PYTHONPATH configuration"
            ]
        
        return ValidationResult(
            check_name="Basic Imports",
            passed=passed,
            severity=severity,
            message=message,
            details={
                "essential_modules": essential_modules,
                "failed_imports": failed_imports
            },
            fix_suggestions=fix_suggestions,
            execution_time=time.time() - start_time
        )
    
    def _validate_required_packages(self) -> ValidationResult:
        """Validate required packages are installed."""
        start_time = time.time()
        
        required_packages = self.config.get("required_packages", [])
        missing_packages = []
        installed_versions = {}
        
        for package_name in required_packages:
            try:
                module = importlib.import_module(package_name)
                version = getattr(module, "__version__", "unknown")
                installed_versions[package_name] = version
            except ImportError:
                missing_packages.append(package_name)
            except Exception as e:
                # Handle other import issues (like compatibility problems)
                print(f"Warning: {package_name} import issue: {e}")
                installed_versions[package_name] = "installed_with_warnings"
        
        if not missing_packages:
            message = f"All {len(required_packages)} required packages are installed"
            passed = True
            severity = ValidationSeverity.INFO
            fix_suggestions = []
        else:
            message = f"Missing {len(missing_packages)} required packages: {', '.join(missing_packages)}"
            passed = False
            severity = ValidationSeverity.BLOCKER
            fix_suggestions = [
                f"Install missing packages: pip install {' '.join(missing_packages)}",
                "Check requirements.txt and install: pip install -r requirements.txt",
                "Verify virtual environment is activated"
            ]
        
        return ValidationResult(
            check_name="Required Packages",
            passed=passed,
            severity=severity,
            message=message,
            details={
                "required_packages": required_packages,
                "missing_packages": missing_packages,
                "installed_versions": installed_versions
            },
            fix_suggestions=fix_suggestions,
            execution_time=time.time() - start_time
        )
    
    def _validate_optional_packages(self) -> ValidationResult:
        """Validate optional packages for enhanced functionality."""
        start_time = time.time()
        
        optional_packages = self.config.get("optional_packages", [])
        missing_packages = []
        installed_versions = {}
        
        for package_name in optional_packages:
            try:
                module = importlib.import_module(package_name)
                version = getattr(module, "__version__", "unknown")
                installed_versions[package_name] = version
            except ImportError:
                missing_packages.append(package_name)
        
        if not missing_packages:
            message = f"All {len(optional_packages)} optional packages are installed"
            passed = True
            severity = ValidationSeverity.INFO
        else:
            message = f"Missing {len(missing_packages)} optional packages: {', '.join(missing_packages)}"
            passed = True  # Optional packages don't fail validation
            severity = ValidationSeverity.WARNING
        
        fix_suggestions = []
        if missing_packages:
            fix_suggestions = [
                f"Install optional packages for enhanced functionality: pip install {' '.join(missing_packages)}",
                "Some advanced features may not work without these packages"
            ]
        
        return ValidationResult(
            check_name="Optional Packages",
            passed=passed,
            severity=severity,
            message=message,
            details={
                "optional_packages": optional_packages,
                "missing_packages": missing_packages,
                "installed_versions": installed_versions
            },
            fix_suggestions=fix_suggestions,
            execution_time=time.time() - start_time
        )
    
    def _validate_directory_structure(self) -> ValidationResult:
        """Validate required directory structure exists."""
        start_time = time.time()
        
        required_dirs = self.config.get("required_directories", [])
        missing_dirs = []
        existing_dirs = []
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                existing_dirs.append(dir_name)
            else:
                missing_dirs.append(dir_name)
        
        if not missing_dirs:
            message = f"All {len(required_dirs)} required directories exist"
            passed = True
            severity = ValidationSeverity.INFO
            fix_suggestions = []
        else:
            message = f"Missing {len(missing_dirs)} required directories: {', '.join(missing_dirs)}"
            passed = False
            severity = ValidationSeverity.CRITICAL
            fix_suggestions = [
                f"Create missing directories: mkdir -p {' '.join(missing_dirs)}",
                "Check project structure documentation",
                "Verify you're in the correct project directory"
            ]
        
        return ValidationResult(
            check_name="Directory Structure",
            passed=passed,
            severity=severity,
            message=message,
            details={
                "required_directories": required_dirs,
                "missing_directories": missing_dirs,
                "existing_directories": existing_dirs,
                "project_root": str(self.project_root)
            },
            fix_suggestions=fix_suggestions,
            execution_time=time.time() - start_time
        )
    
    def _validate_basic_files(self) -> ValidationResult:
        """Validate required files exist."""
        start_time = time.time()
        
        required_files = self.config.get("required_files", [])
        missing_files = []
        existing_files = []
        
        for file_name in required_files:
            file_path = self.project_root / file_name
            if file_path.exists() and file_path.is_file():
                existing_files.append(file_name)
            else:
                missing_files.append(file_name)
        
        if not missing_files:
            message = f"All {len(required_files)} required files exist"
            passed = True
            severity = ValidationSeverity.INFO
            fix_suggestions = []
        else:
            message = f"Missing {len(missing_files)} required files: {', '.join(missing_files)}"
            passed = False
            severity = ValidationSeverity.WARNING
            fix_suggestions = [
                "Create missing files as needed",
                "Check project initialization steps",
                "Verify project template was set up correctly"
            ]
        
        return ValidationResult(
            check_name="Basic Files",
            passed=passed,
            severity=severity,
            message=message,
            details={
                "required_files": required_files,
                "missing_files": missing_files,
                "existing_files": existing_files
            },
            fix_suggestions=fix_suggestions,
            execution_time=time.time() - start_time
        )
    
    def _validate_system_resources(self) -> ValidationResult:
        """Validate system resources are adequate."""
        start_time = time.time()
        
        issues = []
        warnings = []
        
        # Memory check
        memory = psutil.virtual_memory()
        min_memory_mb = self.config.get("memory_min_mb", 512)
        available_mb = memory.available / (1024 * 1024)
        
        if available_mb < min_memory_mb:
            issues.append(f"Low memory: {available_mb:.0f}MB available, {min_memory_mb}MB required")
        elif available_mb < min_memory_mb * 2:
            warnings.append(f"Memory may be tight: {available_mb:.0f}MB available")
        
        # Disk space check
        disk = psutil.disk_usage(str(self.project_root))
        min_disk_mb = self.config.get("disk_space_min_mb", 100)
        available_disk_mb = disk.free / (1024 * 1024)
        
        if available_disk_mb < min_disk_mb:
            issues.append(f"Low disk space: {available_disk_mb:.0f}MB available, {min_disk_mb}MB required")
        
        # CPU check
        cpu_count = psutil.cpu_count()
        if cpu_count and cpu_count < 2:
            warnings.append(f"Single CPU core may slow down tests")
        
        if issues:
            message = f"System resource issues: {'; '.join(issues)}"
            passed = False
            severity = ValidationSeverity.CRITICAL
            fix_suggestions = [
                "Free up memory by closing other applications",
                "Free up disk space by cleaning temporary files",
                "Consider running tests on a machine with more resources"
            ]
        elif warnings:
            message = f"System resource warnings: {'; '.join(warnings)}"
            passed = True
            severity = ValidationSeverity.WARNING
            fix_suggestions = [
                "Monitor resource usage during test execution",
                "Consider optimizing test resource usage"
            ]
        else:
            message = f"System resources adequate: {available_mb:.0f}MB memory, {available_disk_mb:.0f}MB disk"
            passed = True
            severity = ValidationSeverity.INFO
            fix_suggestions = []
        
        return ValidationResult(
            check_name="System Resources",
            passed=passed,
            severity=severity,
            message=message,
            details={
                "memory_available_mb": available_mb,
                "disk_available_mb": available_disk_mb,
                "cpu_cores": cpu_count,
                "memory_total_mb": memory.total / (1024 * 1024),
                "disk_total_mb": disk.total / (1024 * 1024)
            },
            fix_suggestions=fix_suggestions,
            execution_time=time.time() - start_time
        )
    
    def _validate_permissions(self) -> ValidationResult:
        """Validate file system permissions."""
        start_time = time.time()
        
        issues = []
        test_dir = self.project_root / "test_permissions_check"
        
        try:
            # Test directory creation
            test_dir.mkdir(exist_ok=True)
            
            # Test file creation
            test_file = test_dir / "test_file.txt"
            test_file.write_text("test content")
            
            # Test file reading
            content = test_file.read_text()
            if content != "test content":
                issues.append("File read/write operations not working correctly")
            
            # Test file deletion
            test_file.unlink()
            test_dir.rmdir()
            
        except PermissionError as e:
            issues.append(f"Permission denied: {e}")
        except Exception as e:
            issues.append(f"File operation failed: {e}")
        
        if issues:
            message = f"Permission issues: {'; '.join(issues)}"
            passed = False
            severity = ValidationSeverity.CRITICAL
            fix_suggestions = [
                "Check file system permissions for project directory",
                "Run as administrator/sudo if necessary",
                "Verify disk is not full or read-only"
            ]
        else:
            message = "File system permissions OK"
            passed = True
            severity = ValidationSeverity.INFO
            fix_suggestions = []
        
        return ValidationResult(
            check_name="Permissions",
            passed=passed,
            severity=severity,
            message=message,
            details={"test_directory": str(test_dir)},
            fix_suggestions=fix_suggestions,
            execution_time=time.time() - start_time
        )
    
    def _validate_database_connectivity(self) -> ValidationResult:
        """Validate database connectivity if needed."""
        start_time = time.time()
        
        db_url = self.config.get("database_url", "sqlite:///test.db")
        
        try:
            if db_url.startswith("sqlite"):
                # SQLite test
                db_path = db_url.replace("sqlite:///", "")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                conn.close()
                
                if result == (1,):
                    message = f"SQLite database connectivity OK: {db_path}"
                    passed = True
                    severity = ValidationSeverity.INFO
                    fix_suggestions = []
                else:
                    message = "SQLite database test query failed"
                    passed = False
                    severity = ValidationSeverity.CRITICAL
                    fix_suggestions = ["Check SQLite installation"]
            else:
                # For other databases, this would need specific drivers
                message = f"Database connectivity test skipped for: {db_url}"
                passed = True
                severity = ValidationSeverity.WARNING
                fix_suggestions = ["Implement specific database connectivity test"]
        
        except Exception as e:
            message = f"Database connectivity failed: {e}"
            passed = False
            severity = ValidationSeverity.WARNING  # May not be critical for all tests
            fix_suggestions = [
                "Check database server is running",
                "Verify database URL and credentials",
                "Install required database drivers"
            ]
        
        return ValidationResult(
            check_name="Database Connectivity",
            passed=passed,
            severity=severity,
            message=message,
            details={"database_url": db_url},
            fix_suggestions=fix_suggestions,
            execution_time=time.time() - start_time
        )
    
    def _validate_network_connectivity(self) -> ValidationResult:
        """Validate network connectivity for tests that need it."""
        start_time = time.time()
        
        test_hosts = [
            ("8.8.8.8", 53),  # Google DNS
            ("1.1.1.1", 53),  # Cloudflare DNS
        ]
        
        connected_hosts = []
        failed_hosts = []
        
        for host, port in test_hosts:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    connected_hosts.append(f"{host}:{port}")
                else:
                    failed_hosts.append(f"{host}:{port}")
                    
            except Exception:
                failed_hosts.append(f"{host}:{port}")
        
        if connected_hosts:
            message = f"Network connectivity OK: {', '.join(connected_hosts)}"
            passed = True
            severity = ValidationSeverity.INFO if not failed_hosts else ValidationSeverity.WARNING
            fix_suggestions = []
            
            if failed_hosts:
                fix_suggestions.append("Some network connections failed - tests requiring network may be affected")
        else:
            message = f"No network connectivity: {', '.join(failed_hosts)}"
            passed = False
            severity = ValidationSeverity.WARNING  # Not always critical
            fix_suggestions = [
                "Check internet connection",
                "Check firewall settings",
                "Tests requiring network will fail"
            ]
        
        return ValidationResult(
            check_name="Network Connectivity",
            passed=passed,
            severity=severity,
            message=message,
            details={
                "test_hosts": test_hosts,
                "connected_hosts": connected_hosts,
                "failed_hosts": failed_hosts
            },
            fix_suggestions=fix_suggestions,
            execution_time=time.time() - start_time
        )
    
    def _validate_subprocess_execution(self) -> ValidationResult:
        """Validate subprocess execution works correctly."""
        start_time = time.time()
        
        try:
            # Test basic subprocess execution
            result = subprocess.run(
                [sys.executable, "-c", "print('subprocess test')"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "subprocess test" in result.stdout:
                message = "Subprocess execution working correctly"
                passed = True
                severity = ValidationSeverity.INFO
                fix_suggestions = []
            else:
                message = f"Subprocess execution failed: return code {result.returncode}"
                passed = False
                severity = ValidationSeverity.CRITICAL
                fix_suggestions = [
                    "Check Python executable path",
                    "Verify subprocess module is working"
                ]
        
        except subprocess.TimeoutExpired:
            message = "Subprocess execution timed out"
            passed = False
            severity = ValidationSeverity.CRITICAL
            fix_suggestions = [
                "Check for system performance issues",
                "Verify subprocess module is working"
            ]
        
        except Exception as e:
            message = f"Subprocess execution error: {e}"
            passed = False
            severity = ValidationSeverity.CRITICAL
            fix_suggestions = [
                "Check subprocess module installation",
                "Verify system permissions"
            ]
        
        return ValidationResult(
            check_name="Subprocess Execution",
            passed=passed,
            severity=severity,
            message=message,
            details={"python_executable": sys.executable},
            fix_suggestions=fix_suggestions,
            execution_time=time.time() - start_time
        )
    
    def _validate_file_operations(self) -> ValidationResult:
        """Validate file operations work correctly."""
        start_time = time.time()
        
        test_dir = self.project_root / "test_file_ops"
        issues = []
        
        try:
            # Create directory
            test_dir.mkdir(exist_ok=True)
            
            # Create file
            test_file = test_dir / "test.txt"
            test_content = "File operations test\nLine 2\nLine 3"
            test_file.write_text(test_content)
            
            # Read file
            read_content = test_file.read_text()
            if read_content != test_content:
                issues.append("File content mismatch after write/read")
            
            # List directory
            files = list(test_dir.iterdir())
            if test_file not in files:
                issues.append("File not found in directory listing")
            
            # File stats
            stat = test_file.stat()
            if stat.st_size == 0:
                issues.append("File size is zero after writing content")
            
            # Delete file and directory
            test_file.unlink()
            test_dir.rmdir()
            
            if test_file.exists():
                issues.append("File still exists after deletion")
            
        except Exception as e:
            issues.append(f"File operation exception: {e}")
        
        if issues:
            message = f"File operation issues: {'; '.join(issues)}"
            passed = False
            severity = ValidationSeverity.CRITICAL
            fix_suggestions = [
                "Check file system integrity",
                "Verify disk is not full",
                "Check file permissions"
            ]
        else:
            message = "File operations working correctly"
            passed = True
            severity = ValidationSeverity.INFO
            fix_suggestions = []
        
        return ValidationResult(
            check_name="File Operations",
            passed=passed,
            severity=severity,
            message=message,
            details={"test_directory": str(test_dir)},
            fix_suggestions=fix_suggestions,
            execution_time=time.time() - start_time
        )
    
    def _validate_environment_variables(self) -> ValidationResult:
        """Validate important environment variables."""
        start_time = time.time()
        
        important_vars = ["PATH", "PYTHONPATH", "HOME" if os.name != "nt" else "USERPROFILE"]
        missing_vars = []
        present_vars = {}
        
        for var_name in important_vars:
            value = os.environ.get(var_name)
            if value:
                present_vars[var_name] = len(value)  # Store length, not full value for security
            else:
                missing_vars.append(var_name)
        
        # Check for Python in PATH
        python_in_path = shutil.which("python") or shutil.which("python3")
        
        warnings = []
        if not python_in_path:
            warnings.append("Python not found in PATH")
        
        if missing_vars:
            message = f"Missing environment variables: {', '.join(missing_vars)}"
            passed = False
            severity = ValidationSeverity.WARNING
            fix_suggestions = [
                "Set missing environment variables",
                "Check shell configuration (.bashrc, .zshrc, etc.)"
            ]
        elif warnings:
            message = f"Environment warnings: {'; '.join(warnings)}"
            passed = True
            severity = ValidationSeverity.WARNING
            fix_suggestions = [
                "Add Python to PATH for better script execution"
            ]
        else:
            message = f"Environment variables OK: {len(present_vars)} important vars present"
            passed = True
            severity = ValidationSeverity.INFO
            fix_suggestions = []
        
        return ValidationResult(
            check_name="Environment Variables",
            passed=passed,
            severity=severity,
            message=message,
            details={
                "present_vars": list(present_vars.keys()),
                "missing_vars": missing_vars,
                "python_in_path": python_in_path is not None
            },
            fix_suggestions=fix_suggestions,
            execution_time=time.time() - start_time
        )
    
    def _validate_system_configuration(self) -> ValidationResult:
        """Validate system configuration for testing."""
        start_time = time.time()
        
        config_issues = []
        config_info = {}
        
        # Check encoding
        default_encoding = sys.getdefaultencoding()
        if default_encoding.lower() not in ["utf-8", "utf8"]:
            config_issues.append(f"Non-UTF-8 encoding: {default_encoding}")
        config_info["encoding"] = default_encoding
        
        # Check locale (if available)
        try:
            import locale
            current_locale = locale.getlocale()
            config_info["locale"] = current_locale
        except Exception:
            config_info["locale"] = "unknown"
        
        # Check file system
        file_system = "unknown"
        try:
            if hasattr(os, "statvfs"):
                # Unix-like systems
                stat = os.statvfs(str(self.project_root))
                config_info["filesystem_type"] = "unix-like"
            else:
                # Windows
                config_info["filesystem_type"] = "windows"
        except Exception:
            pass
        
        # Check for case-sensitive filesystem
        try:
            test_upper = self.project_root / "TEST_CASE_SENSITIVITY"
            test_lower = self.project_root / "test_case_sensitivity"
            
            if not test_upper.exists() and not test_lower.exists():
                test_upper.touch()
                case_sensitive = not test_lower.exists()
                test_upper.unlink()
                config_info["case_sensitive_fs"] = case_sensitive
        except Exception:
            config_info["case_sensitive_fs"] = "unknown"
        
        if config_issues:
            message = f"System configuration issues: {'; '.join(config_issues)}"
            passed = False
            severity = ValidationSeverity.WARNING
            fix_suggestions = [
                "Check system locale and encoding settings",
                "Some tests may behave differently with current configuration"
            ]
        else:
            message = "System configuration appears compatible"
            passed = True
            severity = ValidationSeverity.INFO
            fix_suggestions = []
        
        return ValidationResult(
            check_name="System Configuration",
            passed=passed,
            severity=severity,
            message=message,
            details=config_info,
            fix_suggestions=fix_suggestions,
            execution_time=time.time() - start_time
        )
    
    def _generate_report(self, total_time: float) -> EnvironmentReport:
        """Generate comprehensive environment report."""
        
        # Categorize results by severity
        blockers = [r for r in self.results if r.severity == ValidationSeverity.BLOCKER]
        critical = [r for r in self.results if r.severity == ValidationSeverity.CRITICAL]
        warnings = [r for r in self.results if r.severity == ValidationSeverity.WARNING]
        info = [r for r in self.results if r.severity == ValidationSeverity.INFO]
        
        passed_checks = sum(1 for r in self.results if r.passed)
        failed_checks = len(self.results) - passed_checks
        
        # Determine overall status
        if blockers:
            overall_status = "BLOCKED"
        elif critical:
            overall_status = "NEEDS_FIXES"
        elif warnings:
            overall_status = "READY_WITH_WARNINGS"
        else:
            overall_status = "READY"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(blockers, critical, warnings)
        
        # Collect environment info
        environment_info = {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": platform.platform(),
            "project_root": str(self.project_root),
            "validation_level": self.validation_level.value,
            "total_execution_time": total_time
        }
        
        return EnvironmentReport(
            validation_level=self.validation_level,
            total_checks=len(self.results),
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            blockers=blockers,
            critical_issues=critical,
            warnings=warnings,
            info_items=info,
            overall_status=overall_status,
            execution_time=total_time,
            environment_info=environment_info,
            recommendations=recommendations
        )
    
    def _generate_recommendations(
        self, 
        blockers: List[ValidationResult], 
        critical: List[ValidationResult],
        warnings: List[ValidationResult]
    ) -> List[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []
        
        if blockers:
            recommendations.append(f"CRITICAL: Fix {len(blockers)} blocking issues before running tests")
            for blocker in blockers[:3]:  # Show top 3
                if blocker.fix_suggestions:
                    recommendations.append(f"   • {blocker.fix_suggestions[0]}")
        
        if critical:
            recommendations.append(f"HIGH PRIORITY: Address {len(critical)} critical issues")
            for issue in critical[:3]:  # Show top 3
                if issue.fix_suggestions:
                    recommendations.append(f"   • {issue.fix_suggestions[0]}")
        
        if warnings:
            recommendations.append(f"MEDIUM PRIORITY: Review {len(warnings)} warnings")
        
        if not blockers and not critical and not warnings:
            recommendations.append("Environment is ready for testing!")
        
        return recommendations


def print_environment_report(report: EnvironmentReport) -> None:
    """Print a comprehensive environment report."""
    
    print("\n" + "=" * 80)
    print("TEST ENVIRONMENT VALIDATION REPORT")
    print("=" * 80)
    
    # Summary
    print(f"\nOVERALL STATUS: {report.overall_status}")
    print(f"CHECKS: {report.passed_checks}/{report.total_checks} passed")
    print(f"TIME: {report.execution_time:.2f}s")
    print(f"LEVEL: {report.validation_level.value}")
    
    # Issues by severity
    if report.blockers:
        print(f"\nBLOCKING ISSUES ({len(report.blockers)})")
        for blocker in report.blockers:
            print(f"   • {blocker.check_name}: {blocker.message}")
    
    if report.critical_issues:
        print(f"\nCRITICAL ISSUES ({len(report.critical_issues)})")
        for issue in report.critical_issues:
            print(f"   • {issue.check_name}: {issue.message}")
    
    if report.warnings:
        print(f"\nWARNINGS ({len(report.warnings)})")
        for warning in report.warnings:
            print(f"   • {warning.check_name}: {warning.message}")
    
    # Recommendations
    if report.recommendations:
        print(f"\nRECOMMENDATIONS")
        for rec in report.recommendations:
            print(f"   {rec}")
    
    print("\n" + "=" * 80)


# Example usage and integration tests
class TestEnvironmentValidator:
    """Test the environment validator system itself."""
    
    def test_validator_initialization(self, temp_dir):
        """Test validator initializes correctly."""
        validator = EnvironmentValidator(temp_dir, ValidationLevel.MINIMAL)
        
        assert validator.project_root == temp_dir
        assert validator.validation_level == ValidationLevel.MINIMAL
        assert isinstance(validator.config, dict)
        assert isinstance(validator.checks_to_run, list)
    
    def test_python_version_validation(self, temp_dir):
        """Test Python version validation."""
        validator = EnvironmentValidator(temp_dir)
        result = validator._validate_python_version()
        
        assert isinstance(result, ValidationResult)
        assert result.check_name == "Python Version"
        assert isinstance(result.passed, bool)
        assert result.execution_time >= 0
        assert "current_version" in result.details
    
    def test_minimal_validation(self, temp_dir):
        """Test minimal validation level."""
        validator = EnvironmentValidator(temp_dir, ValidationLevel.MINIMAL)
        report = validator.validate_environment()
        
        assert isinstance(report, EnvironmentReport)
        assert report.validation_level == ValidationLevel.MINIMAL
        assert report.total_checks >= 3  # At least python, pytest, imports
        assert report.overall_status in ["READY", "READY_WITH_WARNINGS", "NEEDS_FIXES", "BLOCKED"]
    
    def test_report_generation(self, temp_dir):
        """Test report generation and formatting."""
        validator = EnvironmentValidator(temp_dir, ValidationLevel.MINIMAL)
        report = validator.validate_environment()
        
        # Should not raise exceptions
        print_environment_report(report)
        
        # Check report structure
        assert len(report.recommendations) > 0
        assert report.execution_time > 0
        assert "python_version" in report.environment_info


# Pytest integration
def pytest_configure(config):
    """Pytest hook to run environment validation before tests."""
    if hasattr(config, 'option') and getattr(config.option, 'validate_environment', False):
        project_root = Path.cwd()
        validator = EnvironmentValidator(project_root, ValidationLevel.STANDARD)
        report = validator.validate_environment()
        
        print_environment_report(report)
        
        if report.overall_status == "BLOCKED":
            pytest.exit("Environment validation failed - fix blocking issues before running tests", returncode=1)


# CLI integration
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate test environment")
    parser.add_argument("--level", choices=["minimal", "standard", "comprehensive"], 
                       default="standard", help="Validation level")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory")
    
    args = parser.parse_args()
    
    level_mapping = {
        "minimal": ValidationLevel.MINIMAL,
        "standard": ValidationLevel.STANDARD,
        "comprehensive": ValidationLevel.COMPREHENSIVE
    }
    
    validator = EnvironmentValidator(args.project_root, level_mapping[args.level])
    report = validator.validate_environment()
    
    print_environment_report(report)
    
    # Exit with appropriate code
    exit_codes = {
        "READY": 0,
        "READY_WITH_WARNINGS": 0,
        "NEEDS_FIXES": 1,
        "BLOCKED": 2
    }
    
    sys.exit(exit_codes.get(report.overall_status, 1))