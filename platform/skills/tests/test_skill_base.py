"""Tests for the Skill base class."""

from __future__ import annotations

import pytest
from tta_dev_primitives import MockPrimitive, WorkflowContext

from tta_skill_primitives import Skill, SkillDescriptor, SkillMetadata, SkillStatus


class ValidSkill(Skill[str, str]):
    descriptor = SkillDescriptor(name="valid", description="A valid skill.")

    async def execute(self, input_data: str, context: WorkflowContext) -> str:
        return f"valid:{input_data}"


@pytest.mark.asyncio
async def test_skill_execute(workflow_context):
    """Skill execute returns expected output."""
    skill = ValidSkill()
    result = await skill.execute("hello", workflow_context)
    assert result == "valid:hello"


def test_skill_name_property():
    """name property delegates to descriptor."""
    skill = ValidSkill()
    assert skill.name == "valid"


def test_skill_description_property():
    """description property delegates to descriptor."""
    skill = ValidSkill()
    assert skill.description == "A valid skill."


def test_skill_version_property():
    """version defaults to 0.1.0."""
    skill = ValidSkill()
    assert skill.version == "0.1.0"


def test_skill_status_property():
    """status defaults to DRAFT."""
    skill = ValidSkill()
    assert skill.status == SkillStatus.DRAFT


def test_skill_tags_property():
    """tags defaults to empty list."""
    skill = ValidSkill()
    assert skill.tags == []


def test_skill_repr():
    """repr includes name, version, status."""
    skill = ValidSkill()
    r = repr(skill)
    assert "ValidSkill" in r
    assert "valid" in r
    assert "0.1.0" in r
    assert "draft" in r


def test_skill_subclass_without_descriptor():
    """Subclass without descriptor raises TypeError."""
    with pytest.raises(TypeError, match="must define a class-level 'descriptor'"):

        class BadSkill(Skill[str, str]):
            async def execute(self, input_data, context):
                return input_data


@pytest.mark.asyncio
async def test_skill_sequential_composition(workflow_context):
    """Skills compose with >> operator."""
    skill = ValidSkill()
    mock = MockPrimitive("next", return_value="done")
    pipeline = skill >> mock
    result = await pipeline.execute("input", workflow_context)
    assert result == "done"
    assert mock.call_count == 1


@pytest.mark.asyncio
async def test_skill_parallel_composition(workflow_context):
    """Skills compose with | operator."""
    from tests.conftest import EchoSkill, UpperSkill

    echo = EchoSkill()
    upper = UpperSkill()
    pipeline = echo | upper
    results = await pipeline.execute("hello", workflow_context)
    assert results == ["hello", "HELLO"]


@pytest.mark.asyncio
async def test_skill_with_custom_metadata(workflow_context):
    """Skill with full metadata retains all fields."""

    class RichSkill(Skill[str, str]):
        descriptor = SkillDescriptor(
            name="rich-skill",
            description="A richly described skill.",
            license="Apache-2.0",
            status=SkillStatus.STABLE,
            metadata=SkillMetadata(
                author="Test Author",
                version="2.1.0",
                tags=["rich", "full"],
            ),
        )

        async def execute(self, input_data: str, context: WorkflowContext) -> str:
            return input_data

    skill = RichSkill()
    assert skill.name == "rich-skill"
    assert skill.version == "2.1.0"
    assert skill.status == SkillStatus.STABLE
    assert skill.tags == ["rich", "full"]
    assert skill.descriptor.license == "Apache-2.0"
