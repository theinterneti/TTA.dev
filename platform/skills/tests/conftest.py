"""Shared fixtures for skill primitive tests."""

from __future__ import annotations

import pytest
from tta_dev_primitives.core.base import WorkflowContext

from tta_skill_primitives import (
    Skill,
    SkillDescriptor,
    SkillMetadata,
    SkillParameter,
    SkillRegistry,
)


@pytest.fixture
def workflow_context() -> WorkflowContext:
    """Standard workflow context for tests."""
    return WorkflowContext(workflow_id="test-workflow")


@pytest.fixture
def sample_descriptor() -> SkillDescriptor:
    """A fully populated SkillDescriptor for testing."""
    return SkillDescriptor(
        name="code-review",
        description="Analyse code for quality and security issues.",
        license="MIT",
        compatibility="Python 3.11+",
        metadata=SkillMetadata(
            author="TTA Team",
            version="1.0.0",
            tags=["code-quality", "security"],
        ),
        parameters=[
            SkillParameter(
                name="language", type="string", description="Programming language", required=True
            ),
            SkillParameter(name="strict", type="boolean", description="Strict mode", default=False),
        ],
    )


class EchoSkill(Skill[str, str]):
    """Test skill that echoes input."""

    descriptor = SkillDescriptor(
        name="echo",
        description="Returns input unchanged.",
        metadata=SkillMetadata(version="1.0.0", tags=["testing"]),
    )

    async def execute(self, input_data: str, context: WorkflowContext) -> str:
        return input_data


class UpperSkill(Skill[str, str]):
    """Test skill that uppercases input."""

    descriptor = SkillDescriptor(
        name="upper",
        description="Converts text to uppercase.",
        metadata=SkillMetadata(version="0.2.0", tags=["text", "transform"]),
    )

    async def execute(self, input_data: str, context: WorkflowContext) -> str:
        return input_data.upper()


@pytest.fixture
def echo_skill() -> EchoSkill:
    return EchoSkill()


@pytest.fixture
def upper_skill() -> UpperSkill:
    return UpperSkill()


@pytest.fixture
def registry(echo_skill, upper_skill) -> SkillRegistry:
    """A registry pre-loaded with test skills."""
    reg = SkillRegistry()
    reg.register(echo_skill)
    reg.register(upper_skill)
    return reg
