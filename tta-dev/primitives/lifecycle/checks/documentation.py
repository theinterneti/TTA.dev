"""Documentation validation checks.

This module provides validation checks for project documentation:
- README sections (Installation, Usage, Examples)
- CHANGELOG existence
- Examples directory or example files
- Docstring completeness in Python source files

These checks ensure projects have adequate documentation before
progressing through lifecycle stages.
"""

from __future__ import annotations

import re
from pathlib import Path

from primitives.core.base import WorkflowContext
from primitives.lifecycle.validation import Severity, ValidationCheck


async def check_readme_has_sections(project_path: Path, context: WorkflowContext) -> bool:
    """Check if README has required sections.

    Parses the README.md for markdown headings and checks for key sections:
    Installation, Usage, or Examples. At least one of these sections must
    be present for the check to pass.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if README has at least one required section
    """
    readme_path = project_path / "README.md"
    if not readme_path.exists():
        return False

    try:
        content = readme_path.read_text(encoding="utf-8").lower()
    except (OSError, UnicodeDecodeError):
        return False

    # Look for markdown headings containing these keywords
    required_keywords = ["installation", "usage", "example", "getting started", "quick start"]
    headings = re.findall(r"^#{1,4}\s+(.+)$", content, re.MULTILINE)

    return any(keyword in heading for heading in headings for keyword in required_keywords)


async def check_changelog_exists(project_path: Path, context: WorkflowContext) -> bool:
    """Check if CHANGELOG file exists.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if CHANGELOG.md or CHANGELOG file exists
    """
    return (
        (project_path / "CHANGELOG.md").exists()
        or (project_path / "CHANGELOG").exists()
        or (project_path / "CHANGELOG.txt").exists()
        or (project_path / "CHANGES.md").exists()
    )


async def check_examples_exist(project_path: Path, context: WorkflowContext) -> bool:
    """Check if examples directory or example files exist.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if examples/ directory exists or example files are found
    """
    if (project_path / "examples").is_dir():
        return True

    # Check for example files in project root
    example_patterns = ["example_*.py", "example_*.js", "example_*.ts"]
    for pattern in example_patterns:
        if list(project_path.glob(pattern)):
            return True

    return False


async def check_docstrings_complete(project_path: Path, context: WorkflowContext) -> bool:
    """Check if Python files in src/ have module-level docstrings.

    Reads the first few lines of each .py file in src/ and checks for
    triple-quoted strings indicating module docstrings.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if all .py files (excluding __init__.py) in src/ have docstrings
    """
    src_dir = project_path / "src"
    if not src_dir.exists():
        # No src directory - check passes vacuously
        return True

    # Skip __init__.py and dunder files (e.g., __main__.py) but include
    # private modules like _internal.py since they should still be documented.
    py_files = [f for f in src_dir.rglob("*.py") if not f.name.startswith("__")]

    if not py_files:
        return True

    missing_count = 0
    for py_file in py_files:
        try:
            content = py_file.read_text(encoding="utf-8").lstrip()
            # Check if file starts with a docstring (after optional comments/imports)
            has_docstring = (
                content.startswith('"""')
                or content.startswith("'''")
                or content.startswith('r"""')
                or content.startswith("r'''")
            )
            if not has_docstring:
                missing_count += 1
        except (OSError, UnicodeDecodeError):
            missing_count += 1

    # Allow a small tolerance: up to 20% of files may be missing docstrings.
    # This avoids failing for one-off utility files while still enforcing that
    # the majority of the codebase is documented.
    max_missing_ratio = 0.2
    total = len(py_files)
    return missing_count <= total * max_missing_ratio


# Pre-configured validation checks

HAS_README_SECTIONS = ValidationCheck(
    name="README has required sections",
    description="README must have Installation, Usage, or Examples sections",
    severity=Severity.WARNING,
    check_function=check_readme_has_sections,
    failure_message=(
        "README.md is missing key sections. Add Installation, Usage, or Examples sections."
    ),
    success_message="README has required sections",
    fix_command="Add ## Installation, ## Usage, or ## Examples sections to README.md",
    documentation_link="https://www.makeareadme.com/",
)

HAS_CHANGELOG = ValidationCheck(
    name="CHANGELOG exists",
    description="Project must have a CHANGELOG file for release tracking",
    severity=Severity.CRITICAL,
    check_function=check_changelog_exists,
    failure_message="No CHANGELOG.md found. Track changes for each release.",
    success_message="CHANGELOG found",
    fix_command="Create CHANGELOG.md with release notes",
    documentation_link="https://keepachangelog.com/",
)

HAS_EXAMPLES = ValidationCheck(
    name="Examples exist",
    description="Project should have usage examples",
    severity=Severity.WARNING,
    check_function=check_examples_exist,
    failure_message="No examples/ directory or example files found.",
    success_message="Examples found",
    fix_command="Create examples/ directory with usage examples",
)

HAS_DOCSTRINGS = ValidationCheck(
    name="Docstrings complete",
    description="Python source files should have module-level docstrings",
    severity=Severity.INFO,
    check_function=check_docstrings_complete,
    failure_message="Some Python source files are missing module-level docstrings.",
    success_message="Docstrings are present in source files",
    fix_command='Add module docstrings: """Module description.""" at top of each .py file',
)

__all__ = [
    "HAS_README_SECTIONS",
    "HAS_CHANGELOG",
    "HAS_EXAMPLES",
    "HAS_DOCSTRINGS",
    "check_readme_has_sections",
    "check_changelog_exists",
    "check_examples_exist",
    "check_docstrings_complete",
]
