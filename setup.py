"""Setup script for AI Manager System."""

from pathlib import Path
from setuptools import setup, find_packages

# Read the long description from README
README_PATH = Path(__file__).parent / "README.md"
long_description = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""

# Read requirements
def read_requirements(filename):
    """Read requirements from file."""
    requirements_path = Path(__file__).parent / filename
    if requirements_path.exists():
        with open(requirements_path) as f:
            return [
                line.strip() 
                for line in f 
                if line.strip() and not line.startswith("#") and not line.startswith("-r")
            ]
    return []

setup(
    name="ai-manager",
    version="0.1.0",
    description="AI Manager System - Automated AI development task management and execution",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Claude AI Assistant",
    author_email="noreply@anthropic.com",
    url="https://github.com/your-org/ai-manager",
    
    # Package configuration
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    
    # Dependencies
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
    },
    
    # Entry points for CLI commands
    entry_points={
        "console_scripts": [
            "ai-manager=cli.manager_cli:app",
            "ai-worker=cli.worker_cli:app",
        ],
    },
    
    # Package data
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yaml", "*.yml", "*.json"],
    },
    
    # Classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    
    # Keywords
    keywords="ai, automation, task-management, development, testing",
    
    # Project URLs
    project_urls={
        "Documentation": "https://github.com/your-org/ai-manager/wiki",
        "Source": "https://github.com/your-org/ai-manager",
        "Tracker": "https://github.com/your-org/ai-manager/issues",
    },
)