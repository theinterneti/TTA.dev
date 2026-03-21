"""Git-related validation checks.

This module provides validation checks for git repository state:
- Working tree clean (no uncommitted changes)
- On correct branch for deployment
- Remote up to date (local matches remote)
- Version bumped in manifest file

These checks ensure the repository is in a clean, consistent state
before progressing through deployment stages.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.lifecycle.validation import Severity, ValidationCheck


async def check_working_tree_clean(project_path: Path, context: WorkflowContext) -> bool:
    """Check if the git working tree is clean (no uncommitted changes).

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if working tree has no uncommitted changes
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Empty output means clean working tree
        return result.returncode == 0 and result.stdout.strip() == ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


async def check_on_correct_branch(project_path: Path, context: WorkflowContext) -> bool:
    """Check if on a deployment-appropriate branch.

    Verifies the current branch is one of the standard deployment branches:
    main, master, release/*, or a tag-based deployment.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if on a deployment-appropriate branch
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return False

        branch = result.stdout.strip()
        deployment_branches = {"main", "master"}

        return branch in deployment_branches or branch.startswith("release/")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


async def check_remote_up_to_date(project_path: Path, context: WorkflowContext) -> bool:
    """Check if local branch is up to date with remote.

    Fetches the latest remote state and compares with local HEAD.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if local branch is up to date with remote
    """
    try:
        # Fetch latest from remote (quietly)
        subprocess.run(
            ["git", "fetch", "--quiet"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Check if local is behind remote
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD..@{upstream}"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            # No upstream configured - consider it OK
            return True

        behind_count = int(result.stdout.strip())
        return behind_count == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        return False


async def check_version_bumped(project_path: Path, context: WorkflowContext) -> bool:
    """Check if the version has been bumped in the package manifest.

    Compares the version in pyproject.toml (or package.json) against the
    latest git tag to ensure the version has been incremented.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if version appears to have been bumped from the last tag
    """
    # Try pyproject.toml first
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8")
            match = re.search(r'version\s*=\s*"([^"]+)"', content)
            if match:
                current_version = match.group(1)
                return _version_differs_from_latest_tag(project_path, current_version)
        except (OSError, UnicodeDecodeError):
            pass

    # Try package.json
    package_json = project_path / "package.json"
    if package_json.exists():
        try:
            import json

            data = json.loads(package_json.read_text(encoding="utf-8"))
            current_version = data.get("version", "")
            if current_version:
                return _version_differs_from_latest_tag(project_path, current_version)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            pass

    # No version found - can't verify
    return False


def _version_differs_from_latest_tag(project_path: Path, current_version: str) -> bool:
    """Check if current version differs from the latest git tag.

    Args:
        project_path: Path to project root
        current_version: Current version string from manifest

    Returns:
        True if version differs from latest tag, or no tags exist
    """
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            # No tags yet - version is considered "bumped"
            return True

        latest_tag = result.stdout.strip()
        # Strip version prefix: handle "v1.2.3", "packages/foo/v1.2.3", etc.
        # First remove any path prefix (e.g. "packages/foo/"), then strip leading v/V.
        tag_version = latest_tag.rsplit("/", 1)[-1]
        tag_version = re.sub(r"^[vV]", "", tag_version)

        return current_version != tag_version
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# Pre-configured validation checks

WORKING_TREE_CLEAN = ValidationCheck(
    name="Working tree clean",
    description="Git working tree must have no uncommitted changes",
    severity=Severity.BLOCKER,
    check_function=check_working_tree_clean,
    failure_message="Git working tree has uncommitted changes. Commit or stash changes first.",
    success_message="Working tree is clean",
    fix_command="Run: git add -A && git commit -m 'Prepare for deployment'",
)

ON_CORRECT_BRANCH = ValidationCheck(
    name="On correct branch",
    description="Must be on main, master, or release/* branch for deployment",
    severity=Severity.WARNING,
    check_function=check_on_correct_branch,
    failure_message="Not on a deployment branch (main, master, or release/*).",
    success_message="On deployment-appropriate branch",
    fix_command="Run: git checkout main",
)

REMOTE_UP_TO_DATE = ValidationCheck(
    name="Remote up to date",
    description="Local branch must be up to date with remote",
    severity=Severity.CRITICAL,
    check_function=check_remote_up_to_date,
    failure_message="Local branch is behind remote. Pull latest changes.",
    success_message="Local branch is up to date with remote",
    fix_command="Run: git pull",
)

VERSION_BUMPED = ValidationCheck(
    name="Version bumped",
    description="Version in manifest must differ from latest git tag",
    severity=Severity.BLOCKER,
    check_function=check_version_bumped,
    failure_message="Version has not been bumped. Update version in pyproject.toml or package.json.",
    success_message="Version has been bumped",
    fix_command="Update version in pyproject.toml: [project] version = 'X.Y.Z'",
)

__all__ = [
    "WORKING_TREE_CLEAN",
    "ON_CORRECT_BRANCH",
    "REMOTE_UP_TO_DATE",
    "VERSION_BUMPED",
    "check_working_tree_clean",
    "check_on_correct_branch",
    "check_remote_up_to_date",
    "check_version_bumped",
]
