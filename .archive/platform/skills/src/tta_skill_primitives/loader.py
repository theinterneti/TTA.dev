"""SKILL.md file parser and writer.

Provides functions to parse SKILL.md files (YAML frontmatter + markdown body)
into ``SkillDescriptor`` instances and to serialise them back.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .core.models import SkillDescriptor, SkillMetadata
from .errors import SkillLoadError, SkillValidationError

_FRONTMATTER_DELIMITER = "---"


def parse_skill_md(content: str) -> SkillDescriptor:
    """Parse a SKILL.md string into a ``SkillDescriptor``.

    The expected format is YAML frontmatter delimited by ``---`` followed by
    a markdown body.

    Args:
        content: Full text content of a SKILL.md file.

    Returns:
        Populated ``SkillDescriptor``.

    Raises:
        SkillValidationError: If the content is missing frontmatter or
            required fields.

    Example:
        ```python
        text = Path("skills/code-review/SKILL.md").read_text()
        descriptor = parse_skill_md(text)
        print(descriptor.name)  # "code-review"
        ```
    """
    content = content.strip()
    if not content.startswith(_FRONTMATTER_DELIMITER):
        raise SkillValidationError("SKILL.md must start with '---' YAML frontmatter delimiter")

    # Split on the second '---'
    parts = content.split(_FRONTMATTER_DELIMITER, maxsplit=2)
    if len(parts) < 3:
        raise SkillValidationError("SKILL.md must contain opening and closing '---' delimiters")

    yaml_text = parts[1].strip()
    body = parts[2].strip()

    if not yaml_text:
        raise SkillValidationError("YAML frontmatter is empty")

    try:
        data: dict[str, Any] = yaml.safe_load(yaml_text) or {}
    except yaml.YAMLError as exc:
        raise SkillValidationError(f"Invalid YAML in frontmatter: {exc}") from exc

    if not isinstance(data, dict):
        raise SkillValidationError("YAML frontmatter must be a mapping")

    # Normalise nested metadata
    if "metadata" in data and isinstance(data["metadata"], dict):
        data["metadata"] = SkillMetadata(**data["metadata"])

    # Attach the markdown body
    data["instructions"] = body

    # Handle allowed-tools kebab-case key
    if "allowed-tools" in data:
        data["allowed_tools"] = data.pop("allowed-tools")

    try:
        return SkillDescriptor(**data)
    except Exception as exc:
        raise SkillValidationError(f"Invalid SKILL.md data: {exc}") from exc


def load_skill_md(path: str | Path) -> SkillDescriptor:
    """Load and parse a SKILL.md file from disk.

    Args:
        path: Filesystem path to the SKILL.md file.

    Returns:
        Populated ``SkillDescriptor``.

    Raises:
        SkillLoadError: If the file cannot be read or parsed.
    """
    path = Path(path)
    if not path.is_file():
        raise SkillLoadError(str(path), "File does not exist")

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SkillLoadError(str(path), str(exc)) from exc

    try:
        return parse_skill_md(content)
    except SkillValidationError as exc:
        raise SkillLoadError(str(path), str(exc)) from exc


def dump_skill_md(descriptor: SkillDescriptor) -> str:
    """Serialise a ``SkillDescriptor`` back to SKILL.md format.

    Args:
        descriptor: The descriptor to serialise.

    Returns:
        A string in SKILL.md format (YAML frontmatter + markdown body).

    Example:
        ```python
        text = dump_skill_md(descriptor)
        Path("SKILL.md").write_text(text, encoding="utf-8")
        ```
    """
    data: dict[str, Any] = {
        "name": descriptor.name,
        "description": descriptor.description,
    }

    if descriptor.license:
        data["license"] = descriptor.license
    if descriptor.compatibility:
        data["compatibility"] = descriptor.compatibility
    if descriptor.allowed_tools:
        data["allowed-tools"] = descriptor.allowed_tools
    if descriptor.status.value != "draft":
        data["status"] = descriptor.status.value

    # Metadata block
    meta: dict[str, Any] = {}
    if descriptor.metadata.author:
        meta["author"] = descriptor.metadata.author
    if descriptor.metadata.version != "0.1.0":
        meta["version"] = descriptor.metadata.version
    if descriptor.metadata.tags:
        meta["tags"] = descriptor.metadata.tags
    if meta:
        data["metadata"] = meta

    # Parameters
    if descriptor.parameters:
        data["parameters"] = [p.model_dump(exclude_defaults=True) for p in descriptor.parameters]

    yaml_text = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    body = descriptor.instructions or ""

    return f"---\n{yaml_text}---\n\n{body}\n" if body else f"---\n{yaml_text}---\n"
