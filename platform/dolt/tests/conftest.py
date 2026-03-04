"""Shared fixtures for Dolt primitive tests."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from tta_dev_primitives.core.base import WorkflowContext

from tta_dolt_primitives import DoltConfig


@pytest.fixture
def temp_dolt_repo(tmp_path: Path) -> DoltConfig:
    """Create a temporary Dolt repository for testing.

    Initialises a real Dolt repo in a temp directory.
    Tests that use this fixture require the `dolt` binary to be installed.
    """
    repo_path = str(tmp_path / "test-universe-db")
    os.makedirs(repo_path, exist_ok=True)

    result = os.system(f"dolt init -d {repo_path} 2>/dev/null")
    if result != 0:
        pytest.skip("dolt binary not available — skipping integration test")

    return DoltConfig(repo_path=repo_path, database="test-universe-db")


@pytest.fixture
def dolt_config() -> DoltConfig:
    """A DoltConfig pointing at a non-existent path for unit tests."""
    return DoltConfig(repo_path="/fake/repo", database="test_db")


@pytest.fixture
def workflow_context() -> WorkflowContext:
    """Standard workflow context for tests."""
    return WorkflowContext(workflow_id="test-workflow")


@pytest.fixture
def mock_dolt_run():
    """Patch DoltPrimitive._run_dolt for unit tests that don't need a real repo."""
    with patch(
        "tta_dolt_primitives.core.base.DoltPrimitive._run_dolt",
        new_callable=AsyncMock,
    ) as mock:
        yield mock
