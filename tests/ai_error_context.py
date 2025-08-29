"""AI-readable error context and suggestions system.

This module provides comprehensive error analysis and contextual suggestions
specifically designed for AI systems to understand and act upon test failures.
It transforms cryptic error messages into actionable intelligence.

Key Features:
- Semantic error classification
- Context-aware error analysis
- Step-by-step fix suggestions
- Code pattern recognition
- Dependency resolution guidance
- Environment troubleshooting
- Historical error pattern analysis
"""

import ast
import inspect
import json
import re
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union
import importlib.util


class ErrorSeverity(Enum):
    """Error severity levels for prioritization."""
    CRITICAL = "critical"  # Blocks all progress
    HIGH = "high"        # Blocks major functionality
    MEDIUM = "medium"    # Affects specific features
    LOW = "low"         # Minor issues or warnings


class ErrorCategory(Enum):
    """Semantic error categories for better understanding."""
    IMPORT_ERROR = "import_error"
    SYNTAX_ERROR = "syntax_error"
    TYPE_ERROR = "type_error"
    ASSERTION_ERROR = "assertion_error"
    ATTRIBUTE_ERROR = "attribute_error"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT_ERROR = "timeout_error"
    NETWORK_ERROR = "network_error"
    DATABASE_ERROR = "database_error"
    FILE_ERROR = "file_error"
    PERMISSION_ERROR = "permission_error"
    RESOURCE_ERROR = "resource_error"
    CONFIGURATION_ERROR = "configuration_error"
    DEPENDENCY_ERROR = "dependency_error"
    ENVIRONMENT_ERROR = "environment_error"
    LOGIC_ERROR = "logic_error"


@dataclass
class CodeContext:
    """Context information about code where error occurred."""
    file_path: str
    line_number: int
    function_name: Optional[str]
    class_name: Optional[str]
    code_snippet: str
    surrounding_code: List[str]  # Lines before and after
    imports: Set[str]
    variables_in_scope: Dict[str, str]  # var_name -> type
    docstring: Optional[str]


@dataclass
class ErrorContext:
    """Comprehensive error context for AI analysis."""
    
    # Basic error information
    error_type: str
    error_message: str
    error_category: ErrorCategory
    severity: ErrorSeverity
    
    # Location and context
    traceback_lines: List[str]
    code_context: Optional[CodeContext]
    
    # Analysis results
    root_cause: str
    contributing_factors: List[str]
    affected_components: List[str]
    
    # Fix suggestions
    immediate_fixes: List[str]  # Quick fixes to try first
    systematic_fixes: List[str]  # Deeper changes needed
    preventive_measures: List[str]  # How to avoid this error
    
    # Additional context
    related_errors: List[str]  # Similar errors seen before
    documentation_links: List[str]
    example_solutions: List[Dict[str, str]]  # code examples
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    test_name: Optional[str] = None
    environment_info: Dict[str, Any] = field(default_factory=dict)


class AIErrorAnalyzer:
    """AI-friendly error analysis and suggestion system."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.error_patterns = self._load_error_patterns()
        self.fix_templates = self._load_fix_templates()
        self.error_history: List[ErrorContext] = []
    
    def analyze_error(
        self, 
        exception: Exception, 
        traceback_obj: Optional[Any] = None,
        test_name: Optional[str] = None
    ) -> ErrorContext:
        """Analyze an error and provide comprehensive context."""
        
        # Extract basic error information
        error_type = type(exception).__name__
        error_message = str(exception)
        
        # Get traceback information
        if traceback_obj is None:
            traceback_obj = traceback.extract_tb(exception.__traceback__)
        
        traceback_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
        
        # Categorize error
        category = self._categorize_error(error_type, error_message, traceback_lines)
        severity = self._assess_severity(category, error_type, error_message)
        
        # Extract code context
        code_context = self._extract_code_context(traceback_obj, exception)
        
        # Analyze root cause
        root_cause = self._analyze_root_cause(error_type, error_message, code_context, traceback_lines)
        contributing_factors = self._identify_contributing_factors(error_type, error_message, code_context)
        affected_components = self._identify_affected_components(code_context, traceback_lines)
        
        # Generate fix suggestions
        immediate_fixes = self._generate_immediate_fixes(category, error_type, error_message, code_context)
        systematic_fixes = self._generate_systematic_fixes(category, error_type, error_message, code_context)
        preventive_measures = self._generate_preventive_measures(category, error_type, error_message)
        
        # Find related information
        related_errors = self._find_related_errors(error_type, error_message)
        documentation_links = self._get_documentation_links(category, error_type)
        example_solutions = self._get_example_solutions(category, error_type, error_message)
        
        # Create error context
        error_context = ErrorContext(
            error_type=error_type,
            error_message=error_message,
            error_category=category,
            severity=severity,
            traceback_lines=traceback_lines,
            code_context=code_context,
            root_cause=root_cause,
            contributing_factors=contributing_factors,
            affected_components=affected_components,
            immediate_fixes=immediate_fixes,
            systematic_fixes=systematic_fixes,
            preventive_measures=preventive_measures,
            related_errors=related_errors,
            documentation_links=documentation_links,
            example_solutions=example_solutions,
            test_name=test_name,
            environment_info=self._get_environment_info()
        )
        
        # Store in history for pattern analysis
        self.error_history.append(error_context)
        
        return error_context
    
    def _categorize_error(self, error_type: str, error_message: str, traceback_lines: List[str]) -> ErrorCategory:
        """Categorize error into semantic categories."""
        
        # Direct type mapping
        type_mapping = {
            "ImportError": ErrorCategory.IMPORT_ERROR,
            "ModuleNotFoundError": ErrorCategory.IMPORT_ERROR,
            "SyntaxError": ErrorCategory.SYNTAX_ERROR,
            "IndentationError": ErrorCategory.SYNTAX_ERROR,
            "TypeError": ErrorCategory.TYPE_ERROR,
            "AssertionError": ErrorCategory.ASSERTION_ERROR,
            "AttributeError": ErrorCategory.ATTRIBUTE_ERROR,
            "TimeoutError": ErrorCategory.TIMEOUT_ERROR,
            "ConnectionError": ErrorCategory.NETWORK_ERROR,
            "FileNotFoundError": ErrorCategory.FILE_ERROR,
            "PermissionError": ErrorCategory.PERMISSION_ERROR,
            "MemoryError": ErrorCategory.RESOURCE_ERROR,
        }
        
        if error_type in type_mapping:
            return type_mapping[error_type]
        
        # Message-based categorization
        message_lower = error_message.lower()
        
        if any(keyword in message_lower for keyword in ["database", "sql", "connection"]):
            return ErrorCategory.DATABASE_ERROR
        
        if any(keyword in message_lower for keyword in ["network", "http", "url", "connection"]):
            return ErrorCategory.NETWORK_ERROR
        
        if any(keyword in message_lower for keyword in ["config", "setting", "environment"]):
            return ErrorCategory.CONFIGURATION_ERROR
        
        if any(keyword in message_lower for keyword in ["dependency", "package", "version"]):
            return ErrorCategory.DEPENDENCY_ERROR
        
        # Traceback-based categorization
        traceback_text = " ".join(traceback_lines).lower()
        
        if "site-packages" in traceback_text or "pip" in traceback_text:
            return ErrorCategory.DEPENDENCY_ERROR
        
        return ErrorCategory.RUNTIME_ERROR
    
    def _assess_severity(self, category: ErrorCategory, error_type: str, error_message: str) -> ErrorSeverity:
        """Assess error severity for prioritization."""
        
        # Critical errors that block all progress
        critical_patterns = [
            "ImportError", "ModuleNotFoundError", "SyntaxError",
            "configuration", "environment", "python"
        ]
        
        if any(pattern.lower() in error_type.lower() or 
               pattern.lower() in error_message.lower() 
               for pattern in critical_patterns):
            return ErrorSeverity.CRITICAL
        
        # High severity - blocks major functionality
        high_patterns = ["database", "connection", "timeout", "permission"]
        
        if any(pattern in error_message.lower() for pattern in high_patterns):
            return ErrorSeverity.HIGH
        
        # Medium severity - affects specific features
        if category in [ErrorCategory.TYPE_ERROR, ErrorCategory.ATTRIBUTE_ERROR]:
            return ErrorSeverity.MEDIUM
        
        # Low severity - minor issues
        if category == ErrorCategory.ASSERTION_ERROR:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _extract_code_context(self, traceback_obj: Any, exception: Exception) -> Optional[CodeContext]:
        """Extract detailed code context from traceback."""
        
        if not traceback_obj:
            return None
        
        try:
            # Get the last frame (where error occurred)
            if hasattr(traceback_obj, '__iter__'):
                frames = list(traceback_obj)
                if not frames:
                    return None
                last_frame = frames[-1]
            else:
                last_frame = traceback_obj
            
            file_path = last_frame.filename
            line_number = last_frame.lineno
            
            # Read the source file
            try:
                source_lines = Path(file_path).read_text().splitlines()
            except:
                return CodeContext(
                    file_path=file_path,
                    line_number=line_number,
                    function_name=last_frame.name,
                    class_name=None,
                    code_snippet="[Source code not available]",
                    surrounding_code=[],
                    imports=set(),
                    variables_in_scope={},
                    docstring=None
                )
            
            # Extract code snippet and surrounding lines
            error_line_idx = line_number - 1
            code_snippet = source_lines[error_line_idx] if error_line_idx < len(source_lines) else ""
            
            # Get surrounding context (5 lines before and after)
            start_idx = max(0, error_line_idx - 5)
            end_idx = min(len(source_lines), error_line_idx + 6)
            surrounding_code = [
                f"{i+1:4d}: {source_lines[i]}" 
                for i in range(start_idx, end_idx)
            ]
            
            # Parse AST to get more context
            try:
                tree = ast.parse("\n".join(source_lines))
                
                # Find imports
                imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.update(alias.name for alias in node.names)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module)
                
                # Find function/class context
                function_name = last_frame.name
                class_name = None
                
                # Simple class detection (could be improved)
                for i in range(error_line_idx, max(0, error_line_idx - 50), -1):
                    line = source_lines[i].strip()
                    if line.startswith("class "):
                        class_name = line.split()[1].split("(")[0].rstrip(":")
                        break
                
            except:
                imports = set()
                function_name = last_frame.name
                class_name = None
            
            return CodeContext(
                file_path=file_path,
                line_number=line_number,
                function_name=function_name,
                class_name=class_name,
                code_snippet=code_snippet.strip(),
                surrounding_code=surrounding_code,
                imports=imports,
                variables_in_scope={},  # Would need frame inspection
                docstring=None  # Could extract from AST
            )
            
        except Exception as e:
            # If context extraction fails, return minimal context
            return CodeContext(
                file_path="[Unknown]",
                line_number=0,
                function_name=None,
                class_name=None,
                code_snippet=f"[Context extraction failed: {e}]",
                surrounding_code=[],
                imports=set(),
                variables_in_scope={},
                docstring=None
            )
    
    def _analyze_root_cause(
        self, 
        error_type: str, 
        error_message: str, 
        code_context: Optional[CodeContext],
        traceback_lines: List[str]
    ) -> str:
        """Analyze the root cause of the error."""
        
        # ImportError analysis
        if error_type in ["ImportError", "ModuleNotFoundError"]:
            if "No module named" in error_message:
                module_name = error_message.split("'")[1] if "'" in error_message else "unknown"
                return f"Missing Python package '{module_name}' - not installed or not in PYTHONPATH"
            return "Import system cannot locate the specified module or package"
        
        # SyntaxError analysis
        if error_type in ["SyntaxError", "IndentationError"]:
            if code_context:
                return f"Python syntax violation on line {code_context.line_number}: {code_context.code_snippet}"
            return "Code does not conform to Python syntax rules"
        
        # TypeError analysis
        if error_type == "TypeError":
            if "missing" in error_message and "argument" in error_message:
                return "Function called with incorrect number of arguments"
            if "unsupported operand" in error_message:
                return "Operation attempted between incompatible data types"
            if "'NoneType'" in error_message:
                return "Attempted to use None value where a specific type was expected"
            return "Type mismatch between expected and actual data types"
        
        # AssertionError analysis
        if error_type == "AssertionError":
            if code_context and code_context.code_snippet:
                if "assert" in code_context.code_snippet:
                    return f"Assertion failed: {code_context.code_snippet.strip()}"
            return "Test assertion did not meet expected conditions"
        
        # AttributeError analysis
        if error_type == "AttributeError":
            if "'NoneType'" in error_message:
                return "Attempted to access attribute on None value - possible uninitialized variable"
            return "Object does not have the requested attribute or method"
        
        # FileNotFoundError analysis
        if error_type == "FileNotFoundError":
            return "Required file or directory does not exist at the specified path"
        
        # Default analysis
        return f"Runtime error of type {error_type}: {error_message}"
    
    def _identify_contributing_factors(
        self, 
        error_type: str, 
        error_message: str, 
        code_context: Optional[CodeContext]
    ) -> List[str]:
        """Identify factors that contributed to the error."""
        factors = []
        
        # Environment factors
        if error_type in ["ImportError", "ModuleNotFoundError"]:
            factors.extend([
                "Package not installed via pip",
                "Virtual environment not activated",
                "PYTHONPATH not configured correctly",
                "Wrong Python version being used"
            ])
        
        # Code structure factors
        if code_context:
            if not code_context.imports and error_type == "NameError":
                factors.append("Missing import statements")
            
            if "test_" in code_context.function_name or "":
                factors.append("Test-specific environment or setup issue")
            
            if len(code_context.code_snippet) > 100:
                factors.append("Complex line of code - consider breaking into smaller parts")
        
        # Type-related factors
        if error_type == "TypeError":
            factors.extend([
                "Inconsistent data types in function parameters",
                "Missing type hints for better error prevention",
                "Possible None value not handled"
            ])
        
        # Logic factors
        if error_type == "AssertionError":
            factors.extend([
                "Test expectations don't match implementation behavior",
                "Test data may be outdated or incorrect",
                "Race condition in async code"
            ])
        
        return factors
    
    def _identify_affected_components(
        self, 
        code_context: Optional[CodeContext], 
        traceback_lines: List[str]
    ) -> List[str]:
        """Identify which components are affected by this error."""
        components = []
        
        if code_context:
            # File-based components
            file_path = Path(code_context.file_path)
            if "test" in file_path.name:
                components.append(f"Test suite: {file_path.name}")
            else:
                components.append(f"Source module: {file_path.stem}")
            
            # Class-based components
            if code_context.class_name:
                components.append(f"Class: {code_context.class_name}")
            
            # Function-based components
            if code_context.function_name:
                components.append(f"Function: {code_context.function_name}")
        
        # Extract components from traceback
        for line in traceback_lines:
            if "File" in line and ".py" in line:
                # Extract file path
                match = re.search(r'File "([^"]+)"', line)
                if match:
                    file_path = match.group(1)
                    if "site-packages" in file_path:
                        components.append(f"External package: {Path(file_path).parent.name}")
                    else:
                        components.append(f"Project file: {Path(file_path).name}")
        
        return list(set(components))  # Remove duplicates
    
    def _generate_immediate_fixes(
        self, 
        category: ErrorCategory, 
        error_type: str, 
        error_message: str, 
        code_context: Optional[CodeContext]
    ) -> List[str]:
        """Generate immediate fix suggestions that can be tried right away."""
        fixes = []
        
        # ImportError fixes
        if category == ErrorCategory.IMPORT_ERROR:
            if "No module named" in error_message:
                module_name = error_message.split("'")[1] if "'" in error_message else "unknown"
                fixes.extend([
                    f"Run: pip install {module_name}",
                    f"Check if {module_name} is in requirements.txt",
                    f"Verify virtual environment is activated",
                    f"Try: python -m pip install {module_name}"
                ])
        
        # SyntaxError fixes
        if category == ErrorCategory.SYNTAX_ERROR:
            if code_context:
                fixes.extend([
                    f"Check syntax on line {code_context.line_number}: {code_context.code_snippet}",
                    "Look for missing parentheses, brackets, or quotes",
                    "Check indentation consistency (spaces vs tabs)",
                    "Run: python -m py_compile <filename> to check syntax"
                ])
        
        # TypeError fixes
        if category == ErrorCategory.TYPE_ERROR:
            if "'NoneType'" in error_message:
                fixes.extend([
                    "Add None check: if variable is not None:",
                    "Initialize variable before use",
                    "Check function return values for None",
                    "Add default value in function parameter"
                ])
            elif "argument" in error_message:
                fixes.extend([
                    "Check function call has correct number of arguments",
                    "Verify parameter names match function signature",
                    "Add missing arguments or remove extra ones"
                ])
        
        # AssertionError fixes
        if category == ErrorCategory.ASSERTION_ERROR:
            fixes.extend([
                "Compare expected vs actual values with print statements",
                "Check test data setup and initialization",
                "Verify test assumptions are correct",
                "Run test in isolation to check for side effects"
            ])
        
        # AttributeError fixes
        if category == ErrorCategory.ATTRIBUTE_ERROR:
            fixes.extend([
                "Check object is properly initialized",
                "Verify attribute/method name spelling",
                "Check object type matches expected interface",
                "Add hasattr() check before accessing attribute"
            ])
        
        # File error fixes
        if category == ErrorCategory.FILE_ERROR:
            fixes.extend([
                "Verify file path exists and is correct",
                "Check file permissions",
                "Use absolute path instead of relative path",
                "Create missing directories with os.makedirs()"
            ])
        
        return fixes
    
    def _generate_systematic_fixes(
        self, 
        category: ErrorCategory, 
        error_type: str, 
        error_message: str, 
        code_context: Optional[CodeContext]
    ) -> List[str]:
        """Generate systematic fixes that address underlying issues."""
        fixes = []
        
        # Import system improvements
        if category == ErrorCategory.IMPORT_ERROR:
            fixes.extend([
                "Create requirements.txt with all dependencies",
                "Set up virtual environment with: python -m venv venv",
                "Configure PYTHONPATH in your IDE or shell",
                "Use absolute imports instead of relative imports",
                "Add __init__.py files to make directories into packages"
            ])
        
        # Type system improvements
        if category == ErrorCategory.TYPE_ERROR:
            fixes.extend([
                "Add type hints to function signatures",
                "Use mypy for static type checking",
                "Implement input validation in functions",
                "Add unit tests for edge cases with None values",
                "Use Optional[Type] for potentially None values"
            ])
        
        # Test system improvements
        if category == ErrorCategory.ASSERTION_ERROR:
            fixes.extend([
                "Implement better test data factories",
                "Add setup and teardown methods for test isolation",
                "Use parametrized tests for multiple scenarios",
                "Implement custom assertion methods with better error messages",
                "Add logging to understand test execution flow"
            ])
        
        # Error handling improvements
        fixes.extend([
            "Add comprehensive error handling with try/except",
            "Implement logging for debugging complex issues",
            "Add input validation at function boundaries",
            "Create custom exception classes for better error context",
            "Implement retry logic for transient failures"
        ])
        
        return fixes
    
    def _generate_preventive_measures(
        self, 
        category: ErrorCategory, 
        error_type: str, 
        error_message: str
    ) -> List[str]:
        """Generate measures to prevent similar errors in the future."""
        measures = []
        
        # General preventive measures
        measures.extend([
            "Run tests regularly during development",
            "Use linters like ruff or pylint for code quality",
            "Set up pre-commit hooks for automated checks",
            "Implement continuous integration (CI) pipeline"
        ])
        
        # Category-specific measures
        if category == ErrorCategory.IMPORT_ERROR:
            measures.extend([
                "Use dependency management tools like pip-tools",
                "Document all dependencies in requirements files",
                "Use Docker for consistent development environments",
                "Set up automated dependency updates"
            ])
        
        if category == ErrorCategory.TYPE_ERROR:
            measures.extend([
                "Enable strict mode in mypy configuration",
                "Use dataclasses or Pydantic for data validation",
                "Implement unit tests with edge case coverage",
                "Use IDE with good type checking support"
            ])
        
        if category == ErrorCategory.ASSERTION_ERROR:
            measures.extend([
                "Write tests before implementing features (TDD)",
                "Use test fixtures for consistent test data",
                "Implement property-based testing with Hypothesis",
                "Regular test review and maintenance"
            ])
        
        return measures
    
    def _find_related_errors(self, error_type: str, error_message: str) -> List[str]:
        """Find related errors from history."""
        related = []
        
        for past_error in self.error_history:
            # Same error type
            if past_error.error_type == error_type:
                related.append(f"Similar {error_type} in {past_error.test_name or 'unknown test'}")
            
            # Similar error message
            if error_message and past_error.error_message:
                # Simple similarity check (could be improved with fuzzy matching)
                common_words = set(error_message.lower().split()) & set(past_error.error_message.lower().split())
                if len(common_words) >= 2:
                    related.append(f"Similar error pattern: {past_error.error_message[:50]}...")
        
        return related[:5]  # Limit to 5 related errors
    
    def _get_documentation_links(self, category: ErrorCategory, error_type: str) -> List[str]:
        """Get relevant documentation links."""
        links = []
        
        base_docs = "https://docs.python.org/3/"
        
        # Python official documentation
        if category == ErrorCategory.IMPORT_ERROR:
            links.extend([
                f"{base_docs}tutorial/modules.html",
                f"{base_docs}library/importlib.html"
            ])
        
        if category == ErrorCategory.TYPE_ERROR:
            links.extend([
                f"{base_docs}library/typing.html",
                f"{base_docs}library/functions.html"
            ])
        
        if error_type == "AssertionError":
            links.extend([
                "https://docs.pytest.org/en/stable/assert.html",
                "https://docs.python.org/3/reference/simple_stmts.html#assert"
            ])
        
        # Testing documentation
        if "test" in error_type.lower():
            links.append("https://docs.pytest.org/en/stable/")
        
        return links
    
    def _get_example_solutions(
        self, 
        category: ErrorCategory, 
        error_type: str, 
        error_message: str
    ) -> List[Dict[str, str]]:
        """Get code example solutions."""
        examples = []
        
        # ImportError examples
        if category == ErrorCategory.IMPORT_ERROR:
            examples.extend([
                {
                    "title": "Install missing package",
                    "code": "# Terminal command\npip install package_name\n\n# Or in requirements.txt\npackage_name>=1.0.0"
                },
                {
                    "title": "Conditional import",
                    "code": "try:\n    import optional_package\nexcept ImportError:\n    optional_package = None\n\nif optional_package:\n    # Use the package\n    pass"
                }
            ])
        
        # TypeError examples
        if category == ErrorCategory.TYPE_ERROR:
            examples.extend([
                {
                    "title": "None value handling",
                    "code": "def safe_operation(value):\n    if value is None:\n        return default_value\n    return process(value)"
                },
                {
                    "title": "Type checking",
                    "code": "def typed_function(param: str) -> int:\n    if not isinstance(param, str):\n        raise TypeError(f\"Expected str, got {type(param)}\")\n    return len(param)"
                }
            ])
        
        # AssertionError examples
        if category == ErrorCategory.ASSERTION_ERROR:
            examples.extend([
                {
                    "title": "Better assertion messages",
                    "code": "# Instead of:\nassert result == expected\n\n# Use:\nassert result == expected, f\"Expected {expected}, got {result}\""
                },
                {
                    "title": "Pytest assertions",
                    "code": "import pytest\n\n# More informative failures\nwith pytest.raises(ValueError, match=\"Invalid input\"):\n    function_that_should_fail()"
                }
            ])
        
        return examples
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """Get current environment information."""
        return {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
            "executable": sys.executable,
            "path": sys.path[:5],  # First 5 path entries
        }
    
    def _load_error_patterns(self) -> Dict[str, Any]:
        """Load error patterns from configuration."""
        # This would load from a configuration file
        # For now, return empty dict
        return {}
    
    def _load_fix_templates(self) -> Dict[str, Any]:
        """Load fix templates from configuration."""
        # This would load from a configuration file
        # For now, return empty dict
        return {}
    
    def format_error_report(self, error_context: ErrorContext) -> str:
        """Format error context into a comprehensive, AI-readable report."""
        report_lines = []
        
        # Header
        report_lines.extend([
            "=" * 80,
            f"AI ERROR ANALYSIS REPORT",
            f"Generated: {error_context.timestamp.isoformat()}",
            "=" * 80,
            ""
        ])
        
        # Error Summary
        severity_emoji = {
            ErrorSeverity.CRITICAL: "🔴",
            ErrorSeverity.HIGH: "🟠", 
            ErrorSeverity.MEDIUM: "🟡",
            ErrorSeverity.LOW: "🟢"
        }
        
        report_lines.extend([
            "📋 ERROR SUMMARY",
            f"Type: {error_context.error_type}",
            f"Category: {error_context.error_category.value}",
            f"Severity: {severity_emoji[error_context.severity]} {error_context.severity.value.upper()}",
            f"Message: {error_context.error_message}",
            ""
        ])
        
        if error_context.test_name:
            report_lines.extend([
                f"Test: {error_context.test_name}",
                ""
            ])
        
        # Code Context
        if error_context.code_context:
            ctx = error_context.code_context
            report_lines.extend([
                "📍 CODE CONTEXT",
                f"File: {ctx.file_path}",
                f"Line: {ctx.line_number}",
                f"Function: {ctx.function_name or 'N/A'}",
                f"Class: {ctx.class_name or 'N/A'}",
                "",
                "Code snippet:",
                f">>> {ctx.code_snippet}",
                "",
            ])
            
            if ctx.surrounding_code:
                report_lines.extend([
                    "Surrounding code:",
                    *ctx.surrounding_code,
                    ""
                ])
        
        # Root Cause Analysis
        report_lines.extend([
            "🔍 ROOT CAUSE ANALYSIS",
            f"Primary cause: {error_context.root_cause}",
            ""
        ])
        
        if error_context.contributing_factors:
            report_lines.extend([
                "Contributing factors:",
                *[f"  • {factor}" for factor in error_context.contributing_factors],
                ""
            ])
        
        if error_context.affected_components:
            report_lines.extend([
                "Affected components:",
                *[f"  • {component}" for component in error_context.affected_components],
                ""
            ])
        
        # Fix Suggestions
        if error_context.immediate_fixes:
            report_lines.extend([
                "⚡ IMMEDIATE FIXES (try these first)",
                *[f"  {i+1}. {fix}" for i, fix in enumerate(error_context.immediate_fixes)],
                ""
            ])
        
        if error_context.systematic_fixes:
            report_lines.extend([
                "🔧 SYSTEMATIC FIXES (for long-term stability)",
                *[f"  • {fix}" for fix in error_context.systematic_fixes],
                ""
            ])
        
        if error_context.preventive_measures:
            report_lines.extend([
                "🛡️ PREVENTIVE MEASURES",
                *[f"  • {measure}" for measure in error_context.preventive_measures],
                ""
            ])
        
        # Additional Context
        if error_context.related_errors:
            report_lines.extend([
                "🔗 RELATED ERRORS",
                *[f"  • {error}" for error in error_context.related_errors],
                ""
            ])
        
        if error_context.documentation_links:
            report_lines.extend([
                "📖 DOCUMENTATION",
                *[f"  • {link}" for link in error_context.documentation_links],
                ""
            ])
        
        if error_context.example_solutions:
            report_lines.extend([
                "💡 EXAMPLE SOLUTIONS",
                ""
            ])
            
            for example in error_context.example_solutions:
                report_lines.extend([
                    f"  {example['title']}:",
                    "  ```python",
                    *[f"  {line}" for line in example['code'].split('\n')],
                    "  ```",
                    ""
                ])
        
        # Environment Info
        if error_context.environment_info:
            report_lines.extend([
                "🔧 ENVIRONMENT",
                f"Python: {error_context.environment_info.get('python_version', 'unknown')}",
                f"Platform: {error_context.environment_info.get('platform', 'unknown')}",
                ""
            ])
        
        # Traceback (for reference)
        report_lines.extend([
            "📚 FULL TRACEBACK (for reference)",
            *error_context.traceback_lines,
            ""
        ])
        
        report_lines.extend([
            "=" * 80,
            "END OF ERROR ANALYSIS",
            "=" * 80
        ])
        
        return "\n".join(report_lines)


# Global analyzer instance
_error_analyzer = None


def get_error_analyzer() -> AIErrorAnalyzer:
    """Get the global error analyzer instance."""
    global _error_analyzer
    if _error_analyzer is None:
        project_root = Path(__file__).parent.parent
        _error_analyzer = AIErrorAnalyzer(project_root)
    return _error_analyzer


def analyze_exception(exception: Exception, test_name: Optional[str] = None) -> ErrorContext:
    """Convenience function to analyze an exception."""
    analyzer = get_error_analyzer()
    return analyzer.analyze_error(exception, test_name=test_name)


def print_error_analysis(exception: Exception, test_name: Optional[str] = None) -> None:
    """Print comprehensive error analysis to console."""
    analyzer = get_error_analyzer()
    error_context = analyzer.analyze_error(exception, test_name=test_name)
    report = analyzer.format_error_report(error_context)
    print(report)


# Example usage and testing
if __name__ == "__main__":
    # Example error analysis
    try:
        import nonexistent_module
    except ImportError as e:
        print_error_analysis(e, "test_import_error")
    
    try:
        result = None
        print(result.some_attribute)
    except AttributeError as e:
        print_error_analysis(e, "test_none_attribute_error")
    
    try:
        assert 1 == 2, "Numbers should be equal"
    except AssertionError as e:
        print_error_analysis(e, "test_assertion_failure")