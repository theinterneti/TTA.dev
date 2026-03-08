"""Tests for SKILL.md loader (parse / load / dump)."""

from __future__ import annotations

import pytest

from tta_skill_primitives import (
    SkillDescriptor,
    SkillMetadata,
    SkillParameter,
    SkillStatus,
    dump_skill_md,
    load_skill_md,
    parse_skill_md,
)
from tta_skill_primitives.errors import SkillLoadError, SkillValidationError

MINIMAL_SKILL_MD = """\
---
name: my-skill
description: A minimal test skill.
---
"""

FULL_SKILL_MD = """\
---
name: code-review
description: Analyse code for quality and security issues.
license: Apache-2.0
compatibility: Python 3.11+
allowed-tools:
  - Bash(git:*)
  - Bash(ruff:*)
status: stable
metadata:
  author: TTA Team
  version: "1.0.0"
  tags:
    - code-quality
    - security
parameters:
  - name: language
    type: string
    description: Programming language
    required: true
---

# Code Review Skill

## When to use
Use when the user requests a code review.

## Instructions
1. Receive code and language.
2. Analyse for anti-patterns.
3. Return issues and score.
"""


def test_parse_minimal():
    """Parse minimal SKILL.md."""
    d = parse_skill_md(MINIMAL_SKILL_MD)
    assert d.name == "my-skill"
    assert d.description == "A minimal test skill."
    assert d.instructions == ""


def test_parse_full():
    """Parse fully populated SKILL.md."""
    d = parse_skill_md(FULL_SKILL_MD)
    assert d.name == "code-review"
    assert d.description == "Analyse code for quality and security issues."
    assert d.license == "Apache-2.0"
    assert d.compatibility == "Python 3.11+"
    assert d.allowed_tools == ["Bash(git:*)", "Bash(ruff:*)"]
    assert d.status == SkillStatus.STABLE
    assert d.metadata.author == "TTA Team"
    assert d.metadata.version == "1.0.0"
    assert d.metadata.tags == ["code-quality", "security"]
    assert len(d.parameters) == 1
    assert d.parameters[0].name == "language"
    assert d.parameters[0].required is True
    assert "# Code Review Skill" in d.instructions
    assert "anti-patterns" in d.instructions


def test_parse_no_frontmatter():
    """Content without frontmatter raises SkillValidationError."""
    with pytest.raises(SkillValidationError, match="must start with"):
        parse_skill_md("# Just markdown, no frontmatter")


def test_parse_unclosed_frontmatter():
    """Content with only opening --- raises SkillValidationError."""
    with pytest.raises(SkillValidationError, match="opening and closing"):
        parse_skill_md("---\nname: test\n")


def test_parse_empty_frontmatter():
    """Empty frontmatter raises SkillValidationError."""
    with pytest.raises(SkillValidationError, match="empty"):
        parse_skill_md("---\n---\n")


def test_parse_invalid_yaml():
    """Malformed YAML raises SkillValidationError."""
    with pytest.raises(SkillValidationError, match="Invalid YAML"):
        parse_skill_md("---\n: invalid: yaml: [\n---\n")


def test_parse_missing_required_field():
    """Missing required name field raises SkillValidationError."""
    with pytest.raises(SkillValidationError, match="Invalid SKILL.md data"):
        parse_skill_md("---\ndescription: No name\n---\n")


def test_load_nonexistent_file():
    """Loading a non-existent file raises SkillLoadError."""
    with pytest.raises(SkillLoadError, match="does not exist"):
        load_skill_md("/nonexistent/path/SKILL.md")


def test_load_from_file(tmp_path):
    """Load a SKILL.md file from disk."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(FULL_SKILL_MD, encoding="utf-8")

    d = load_skill_md(skill_file)
    assert d.name == "code-review"
    assert d.metadata.version == "1.0.0"


def test_dump_minimal():
    """Dump minimal descriptor."""
    d = SkillDescriptor(name="test", description="A test.")
    text = dump_skill_md(d)
    assert text.startswith("---\n")
    assert "name: test" in text
    assert "description: A test." in text


def test_dump_full():
    """Dump full descriptor preserves all fields."""
    d = SkillDescriptor(
        name="code-review",
        description="Analyse code.",
        license="Apache-2.0",
        compatibility="Python 3.11+",
        status=SkillStatus.STABLE,
        allowed_tools=["Bash(git:*)"],
        metadata=SkillMetadata(
            author="TTA Team",
            version="1.0.0",
            tags=["security"],
        ),
        parameters=[
            SkillParameter(name="lang", type="string", required=True),
        ],
        instructions="# Instructions\nDo the thing.",
    )
    text = dump_skill_md(d)
    assert "name: code-review" in text
    assert "Apache-2.0" in text
    assert "status: stable" in text
    assert "allowed-tools" in text
    assert "author: TTA Team" in text
    assert "# Instructions" in text


def test_roundtrip():
    """Dump then parse preserves core data."""
    original = SkillDescriptor(
        name="roundtrip",
        description="Test round-trip fidelity.",
        metadata=SkillMetadata(author="Tester", version="2.0.0", tags=["test"]),
        instructions="# Body\nHello world.",
    )
    text = dump_skill_md(original)
    restored = parse_skill_md(text)

    assert restored.name == original.name
    assert restored.description == original.description
    assert restored.metadata.author == original.metadata.author
    assert restored.metadata.version == original.metadata.version
    assert restored.metadata.tags == original.metadata.tags
    assert "Hello world" in restored.instructions
