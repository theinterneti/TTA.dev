"""Tests for SkillRegistry."""

from __future__ import annotations

import pytest

from tta_skill_primitives import SkillDescriptor, SkillRegistry, SkillStatus
from tta_skill_primitives.errors import SkillNotFoundError, SkillValidationError

from .conftest import EchoSkill


def test_register_and_get(echo_skill):
    """Register then get returns the same skill."""
    reg = SkillRegistry()
    reg.register(echo_skill)
    assert reg.get("echo") is echo_skill


def test_register_duplicate(echo_skill):
    """Registering the same name twice raises SkillValidationError."""
    reg = SkillRegistry()
    reg.register(echo_skill)
    with pytest.raises(SkillValidationError, match="already registered"):
        reg.register(echo_skill)


def test_get_missing():
    """Getting unregistered skill raises SkillNotFoundError."""
    reg = SkillRegistry()
    with pytest.raises(SkillNotFoundError, match="not-here"):
        reg.get("not-here")


def test_has(registry):
    """has() returns True for registered, False for missing."""
    assert registry.has("echo") is True
    assert registry.has("nonexistent") is False


def test_unregister(registry):
    """Unregister removes the skill."""
    registry.unregister("echo")
    assert not registry.has("echo")
    assert len(registry) == 1


def test_unregister_missing():
    """Unregistering missing skill raises SkillNotFoundError."""
    reg = SkillRegistry()
    with pytest.raises(SkillNotFoundError):
        reg.unregister("nope")


def test_list_skills(registry):
    """list_skills returns sorted descriptors."""
    descriptors = registry.list_skills()
    assert len(descriptors) == 2
    assert descriptors[0].name == "echo"
    assert descriptors[1].name == "upper"


def test_search_by_tags(registry):
    """Search by tags returns matching skills."""
    results = registry.search(tags=["testing"])
    assert len(results) == 1
    assert results[0].name == "echo"


def test_search_by_query(registry):
    """Search by query matches name or description."""
    results = registry.search(query="uppercase")
    assert len(results) == 1
    assert results[0].name == "upper"


def test_search_by_query_name(registry):
    """Search by query matches name."""
    results = registry.search(query="echo")
    assert len(results) == 1
    assert results[0].name == "echo"


def test_search_no_match(registry):
    """Search with no match returns empty."""
    results = registry.search(query="nonexistent-skill-xyz")
    assert results == []


def test_search_combined_filters(registry):
    """Combined filters use AND logic."""
    results = registry.search(tags=["text"], query="upper")
    assert len(results) == 1
    assert results[0].name == "upper"

    results = registry.search(tags=["testing"], query="upper")
    assert len(results) == 0


def test_search_by_status():
    """Search by status filters correctly."""

    class StableSkill(EchoSkill):
        descriptor = SkillDescriptor(
            name="stable-echo",
            description="A stable echo.",
            status=SkillStatus.STABLE,
        )

    reg = SkillRegistry()
    reg.register(EchoSkill())
    reg.register(StableSkill())

    draft = reg.search(status=SkillStatus.DRAFT)
    stable = reg.search(status=SkillStatus.STABLE)
    assert len(draft) == 1
    assert len(stable) == 1
    assert draft[0].name == "echo"
    assert stable[0].name == "stable-echo"


def test_to_prompt_catalog(registry):
    """to_prompt_catalog generates markdown."""
    catalog = registry.to_prompt_catalog()
    assert "# Available Skills" in catalog
    assert "## echo" in catalog
    assert "## upper" in catalog


def test_to_prompt_catalog_empty():
    """Empty registry returns informative message."""
    reg = SkillRegistry()
    assert reg.to_prompt_catalog() == "No skills registered."


def test_len(registry):
    """len() returns registered count."""
    assert len(registry) == 2


def test_repr():
    """repr shows count."""
    reg = SkillRegistry()
    assert "skills=0" in repr(reg)
