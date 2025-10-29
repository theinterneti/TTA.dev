"""Predefined stage criteria for common lifecycle transitions.

This module defines the entry and exit criteria for transitioning
between lifecycle stages, along with recommended actions.
"""

from tta_dev_primitives.lifecycle.checks import (
    FORMAT_CHECK_PASSES,
    HAS_LICENSE,
    HAS_PYPROJECT_TOML,
    HAS_README,
    HAS_SRC_DIRECTORY,
    HAS_TESTS_DIRECTORY,
    LINT_PASSES,
    TESTS_PASS,
    TYPE_CHECK_PASSES,
)
from tta_dev_primitives.lifecycle.stage import Stage
from tta_dev_primitives.lifecycle.stage_criteria import StageCriteria

# Experimentation → Testing
EXPERIMENTATION_TO_TESTING = StageCriteria(
    stage=Stage.TESTING,
    entry_criteria=[
        HAS_PYPROJECT_TOML,
        HAS_SRC_DIRECTORY,
    ],
    exit_criteria=[
        HAS_TESTS_DIRECTORY,
        TESTS_PASS,
        TYPE_CHECK_PASSES,
    ],
    recommended_actions=[
        "Write unit tests for core functionality",
        "Add type hints to all functions",
        "Run pytest to verify tests pass",
        "Use uvx pyright to check types",
    ],
    description="Transition from prototyping to automated testing",
)

# Testing → Staging
TESTING_TO_STAGING = StageCriteria(
    stage=Stage.STAGING,
    entry_criteria=[
        TESTS_PASS,
        TYPE_CHECK_PASSES,
    ],
    exit_criteria=[
        HAS_README,
        LINT_PASSES,
        FORMAT_CHECK_PASSES,
    ],
    recommended_actions=[
        "Write comprehensive README with installation and usage",
        "Add working examples to demonstrate usage",
        "Fix linting issues with: uv run ruff check . --fix",
        "Format code with: uv run ruff format .",
        "Commit all changes to git",
    ],
    description="Transition from testing to pre-production validation",
)

# Staging → Deployment
STAGING_TO_DEPLOYMENT = StageCriteria(
    stage=Stage.DEPLOYMENT,
    entry_criteria=[
        TESTS_PASS,
        HAS_README,
        LINT_PASSES,
    ],
    exit_criteria=[
        HAS_LICENSE,
        TYPE_CHECK_PASSES,
        FORMAT_CHECK_PASSES,
    ],
    recommended_actions=[
        "Add LICENSE file (MIT or Apache 2.0 recommended)",
        "Update CHANGELOG with release notes",
        "Bump version in pyproject.toml",
        "Scan for secrets in code",
        "Create git tag for release",
        "Run final quality checks",
    ],
    description="Transition from staging to deployment ready",
)

# Deployment → Production
DEPLOYMENT_TO_PRODUCTION = StageCriteria(
    stage=Stage.PRODUCTION,
    entry_criteria=[
        HAS_LICENSE,
        TESTS_PASS,
        TYPE_CHECK_PASSES,
        LINT_PASSES,
    ],
    exit_criteria=[],  # No exit criteria - production is the final stage
    recommended_actions=[
        "Submit to package registry (PyPI, npm, etc.)",
        "Configure monitoring (Prometheus, Sentry)",
        "Publish documentation site",
        "Announce release to users",
        "Set up alerting for production issues",
    ],
    description="Transition from deployment to production monitoring",
)

# Map of stages to their criteria
STAGE_CRITERIA_MAP: dict[Stage, StageCriteria] = {
    Stage.TESTING: EXPERIMENTATION_TO_TESTING,
    Stage.STAGING: TESTING_TO_STAGING,
    Stage.DEPLOYMENT: STAGING_TO_DEPLOYMENT,
    Stage.PRODUCTION: DEPLOYMENT_TO_PRODUCTION,
}

__all__ = [
    "EXPERIMENTATION_TO_TESTING",
    "TESTING_TO_STAGING",
    "STAGING_TO_DEPLOYMENT",
    "DEPLOYMENT_TO_PRODUCTION",
    "STAGE_CRITERIA_MAP",
]
