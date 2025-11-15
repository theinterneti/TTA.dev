"""Language-agnostic validation checks.

This module provides validation checks that work across all programming
languages and project types. These checks focus on universal project
requirements like README, LICENSE, documentation, and basic structure.

For language-specific checks (tests, linting, type checking), see:
- python.py - Python-specific checks (pytest, ruff, pyright)
- javascript.py - JavaScript/TypeScript checks (jest, eslint, tsc)
- rust.py - Rust checks (cargo test, clippy)
"""

from __future__ import annotations

from pathlib import Path

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.lifecycle.validation import Severity, ValidationCheck


async def check_package_manifest_exists(project_path: Path, context: WorkflowContext) -> bool:
    """Check if a package manifest file exists.

    Language-agnostic check for common package manifest files:
    - pyproject.toml (Python)
    - package.json (JavaScript/TypeScript)
    - Cargo.toml (Rust)
    - go.mod (Go)
    - pom.xml (Java/Maven)
    - build.gradle (Java/Gradle)
    - Gemfile (Ruby)
    - composer.json (PHP)

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if any standard package manifest file exists
    """
    manifest_files = [
        "pyproject.toml",  # Python
        "package.json",  # JavaScript/TypeScript
        "Cargo.toml",  # Rust
        "go.mod",  # Go
        "pom.xml",  # Java/Maven
        "build.gradle",  # Java/Gradle
        "Gemfile",  # Ruby
        "composer.json",  # PHP
    ]

    return any((project_path / manifest).exists() for manifest in manifest_files)


async def check_readme_exists(project_path: Path, context: WorkflowContext) -> bool:
    """Check if README file exists.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if README.md or README.rst exists
    """
    return (project_path / "README.md").exists() or (project_path / "README.rst").exists()


async def check_license_exists(project_path: Path, context: WorkflowContext) -> bool:
    """Check if LICENSE file exists.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if LICENSE file exists
    """
    return (project_path / "LICENSE").exists() or (project_path / "LICENSE.txt").exists()


async def check_tests_directory_exists(project_path: Path, context: WorkflowContext) -> bool:
    """Check if tests directory exists.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if tests/ directory exists
    """
    tests_dir = project_path / "tests"
    return tests_dir.exists() and tests_dir.is_dir()


async def check_src_directory_exists(project_path: Path, context: WorkflowContext) -> bool:
    """Check if source code directory exists.

    Language-agnostic check for common source code locations:
    - src/ directory (universal convention)
    - lib/ directory (common in Ruby, JavaScript)
    - Source code files in root (flat layout)

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if source code directory exists or source files are present
    """
    # Check for common source directories
    if (project_path / "src").exists():
        return True
    if (project_path / "lib").exists():
        return True

    # Check for source code files in root (common extensions)
    source_extensions = [
        "*.py",  # Python
        "*.js",  # JavaScript
        "*.ts",  # TypeScript
        "*.rs",  # Rust
        "*.go",  # Go
        "*.rb",  # Ruby
        "*.java",  # Java
        "*.php",  # PHP
    ]

    for pattern in source_extensions:
        if list(project_path.glob(pattern)):
            return True

    return False


# Pre-configured validation checks

HAS_PACKAGE_MANIFEST = ValidationCheck(
    name="Package manifest exists",
    description="Project must have a package manifest file",
    severity=Severity.BLOCKER,
    check_function=check_package_manifest_exists,
    failure_message="No package manifest found (pyproject.toml, package.json, Cargo.toml, etc.)",
    success_message="Package manifest found",
    fix_command="Create appropriate manifest for your language (e.g., 'uv init' for Python)",
    documentation_link="https://packaging.python.org/",
)

HAS_README = ValidationCheck(
    name="README exists",
    description="Project must have a README file",
    severity=Severity.BLOCKER,
    check_function=check_readme_exists,
    failure_message="No README.md or README.rst found. Documentation is required.",
    success_message="README found",
    fix_command="Create README.md with project description",
    documentation_link="https://www.makeareadme.com/",
)

HAS_LICENSE = ValidationCheck(
    name="LICENSE exists",
    description="Project must have a LICENSE file",
    severity=Severity.CRITICAL,
    check_function=check_license_exists,
    failure_message="No LICENSE file found. License is required for deployment.",
    success_message="LICENSE found",
    fix_command="Add LICENSE file (MIT or Apache 2.0 recommended)",
    documentation_link="https://choosealicense.com/",
)

HAS_TESTS_DIRECTORY = ValidationCheck(
    name="tests/ directory exists",
    description="Project must have a tests directory",
    severity=Severity.BLOCKER,
    check_function=check_tests_directory_exists,
    failure_message="No tests/ directory found. Tests are required for all stages beyond experimentation.",
    success_message="tests/ directory found",
    fix_command="Create tests/ directory: mkdir tests",
    documentation_link="https://en.wikipedia.org/wiki/Test-driven_development",
)

HAS_SRC_DIRECTORY = ValidationCheck(
    name="Source code exists",
    description="Project must have source code",
    severity=Severity.BLOCKER,
    check_function=check_src_directory_exists,
    failure_message="No source code found. Create src/ or lib/ directory, or add source files.",
    success_message="Source code found",
    fix_command="Create src/ directory: mkdir -p src",
    documentation_link="https://en.wikipedia.org/wiki/Software_project_management",
)

# Export all checks
__all__ = [
    "HAS_PACKAGE_MANIFEST",
    "HAS_README",
    "HAS_LICENSE",
    "HAS_TESTS_DIRECTORY",
    "HAS_SRC_DIRECTORY",
    "check_package_manifest_exists",
    "check_readme_exists",
    "check_license_exists",
    "check_tests_directory_exists",
    "check_src_directory_exists",
]
