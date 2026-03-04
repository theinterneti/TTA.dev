"""Tests for SkillDescriptor and related models."""

from __future__ import annotations

import pytest

from tta_skill_primitives import (
    SkillDescriptor,
    SkillMetadata,
    SkillParameter,
    SkillStatus,
)


def test_descriptor_minimal():
    """Minimal descriptor with just name and description."""
    d = SkillDescriptor(name="test", description="A test skill.")
    assert d.name == "test"
    assert d.description == "A test skill."
    assert d.license == "MIT"
    assert d.status == SkillStatus.DRAFT
    assert d.metadata.version == "0.1.0"
    assert d.parameters == []
    assert d.instructions == ""


def test_descriptor_full(sample_descriptor):
    """Full descriptor with all fields populated."""
    d = sample_descriptor
    assert d.name == "code-review"
    assert d.metadata.author == "TTA Team"
    assert d.metadata.version == "1.0.0"
    assert d.metadata.tags == ["code-quality", "security"]
    assert len(d.parameters) == 2
    assert d.parameters[0].name == "language"
    assert d.parameters[0].required is True
    assert d.parameters[1].default is False


def test_descriptor_name_validation():
    """Name must be 1-64 characters."""
    with pytest.raises(ValueError):
        SkillDescriptor(name="", description="Empty name")

    with pytest.raises(ValueError):
        SkillDescriptor(name="x" * 65, description="Too long")


def test_descriptor_description_validation():
    """Description must be 1-1024 characters."""
    with pytest.raises(ValueError):
        SkillDescriptor(name="test", description="")


def test_descriptor_extra_fields():
    """Extra fields are allowed (forward compatibility)."""
    d = SkillDescriptor(
        name="test",
        description="A test.",
        custom_field="custom_value",
    )
    assert d.model_extra.get("custom_field") == "custom_value"


def test_metadata_defaults():
    """Metadata has sensible defaults."""
    m = SkillMetadata()
    assert m.author == ""
    assert m.version == "0.1.0"
    assert m.tags == []


def test_metadata_extra_fields():
    """Metadata allows extra fields."""
    m = SkillMetadata(author="Test", custom="value")
    assert m.model_extra.get("custom") == "value"


def test_parameter_defaults():
    """Parameter has sensible defaults."""
    p = SkillParameter(name="foo")
    assert p.type == "string"
    assert p.description == ""
    assert p.required is False
    assert p.default is None


def test_skill_status_values():
    """SkillStatus enum has expected members."""
    assert SkillStatus.DRAFT.value == "draft"
    assert SkillStatus.STABLE.value == "stable"
    assert SkillStatus.DEPRECATED.value == "deprecated"
