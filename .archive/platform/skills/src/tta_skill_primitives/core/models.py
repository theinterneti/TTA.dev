"""Pydantic models for SKILL.md-compatible skill metadata.

These models mirror the open SKILL.md specification used by mainstream AI agent
frameworks (OpenAI, Anthropic Claude, LangChain) for portable, modular skills.
"""

from __future__ import annotations

import enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SkillStatus(enum.StrEnum):
    """Lifecycle status of a skill."""

    DRAFT = "draft"
    STABLE = "stable"
    DEPRECATED = "deprecated"


class SkillParameter(BaseModel):
    """Describes a single input parameter that a skill accepts.

    Parameters are declared in the SKILL.md frontmatter so that agents can
    discover what data a skill requires before invoking it.

    Example:
        ```yaml
        parameters:
          - name: language
            type: string
            description: Programming language to analyze
            required: true
        ```
    """

    name: str = Field(..., description="Parameter name (lowercase-hyphenated)")
    type: str = Field(default="string", description="JSON Schema type (string, number, boolean…)")
    description: str = Field(default="", description="Human-readable explanation")
    required: bool = Field(default=False, description="Whether the parameter is mandatory")
    default: Any = Field(default=None, description="Default value when not supplied")

    model_config = ConfigDict(extra="allow")


class SkillMetadata(BaseModel):
    """Extended metadata block inside the SKILL.md frontmatter.

    Captures authorship, versioning, and arbitrary key/value pairs so that
    skill marketplaces and registries can index skills.

    Example:
        ```yaml
        metadata:
          author: TTA Development Team
          version: "1.0.0"
          tags: [code-review, security]
        ```
    """

    author: str = Field(default="", description="Skill author or organisation")
    version: str = Field(default="0.1.0", description="Semantic version of the skill")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")

    model_config = ConfigDict(extra="allow")


class SkillDescriptor(BaseModel):
    """Complete SKILL.md frontmatter model.

    Represents the YAML frontmatter of a SKILL.md file — the standard format
    used by AI agent frameworks for portable, modular skills.

    Fields align with the open SKILL.md specification:
      - ``name`` (required) — unique lowercase-hyphenated identifier.
      - ``description`` (required) — concise summary of what the skill does.
      - ``license``, ``compatibility``, ``allowed_tools`` — optional spec fields.
      - ``metadata`` — nested author/version/tags block.
      - ``parameters`` — inputs the skill accepts.
      - ``instructions`` — the markdown body that follows the frontmatter.

    Example:
        ```python
        descriptor = SkillDescriptor(
            name="code-review",
            description="Perform static code analysis for quality and security.",
            metadata=SkillMetadata(author="TTA Team", version="1.0.0"),
        )
        ```
    """

    # Required fields
    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Unique skill identifier (lowercase-hyphenated)",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="Concise summary of what the skill does and when to use it",
    )

    # Optional spec-defined fields
    license: str = Field(default="MIT", description="Short license identifier")
    compatibility: str = Field(
        default="",
        description="Runtime or environment requirements (e.g. 'Python 3.11+')",
    )
    allowed_tools: list[str] = Field(
        default_factory=list,
        description="Tools the skill is permitted to invoke",
    )
    status: SkillStatus = Field(
        default=SkillStatus.DRAFT,
        description="Lifecycle status of the skill",
    )

    # Nested models
    metadata: SkillMetadata = Field(
        default_factory=SkillMetadata,
        description="Authorship and versioning metadata",
    )
    parameters: list[SkillParameter] = Field(
        default_factory=list,
        description="Input parameters the skill accepts",
    )

    # Markdown body (populated by the loader, not part of YAML frontmatter)
    instructions: str = Field(
        default="",
        description="Markdown body from the SKILL.md file (after frontmatter)",
    )

    model_config = ConfigDict(extra="allow", populate_by_name=True)
