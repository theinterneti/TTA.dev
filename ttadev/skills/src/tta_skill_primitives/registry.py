"""Skill registry for dynamic discovery and lookup.

The ``SkillRegistry`` stores ``Skill`` instances (or classes) keyed by their
descriptor name, enabling agents to discover available skills at runtime.
"""

from __future__ import annotations

from typing import Any

import structlog

from .core.base import Skill
from .core.models import SkillDescriptor, SkillStatus
from .errors import SkillNotFoundError, SkillValidationError

logger = structlog.get_logger(__name__)


class SkillRegistry:
    """Registry for discovering, storing, and searching skills.

    Provides a simple in-memory store that maps skill names to instances. AI
    agents can query the registry to find skills matching specific tags or
    descriptions.

    Example:
        ```python
        registry = SkillRegistry()
        registry.register(CodeReviewSkill())
        registry.register(SecurityScanSkill())

        skill = registry.get("code-review")
        results = registry.search(tags=["security"])
        ```
    """

    def __init__(self) -> None:
        """Initialise an empty registry."""
        self._skills: dict[str, Skill[Any, Any]] = {}

    # ── Mutation ────────────────────────────────────────────────────────

    def register(self, skill: Skill[Any, Any]) -> None:
        """Register a skill instance.

        Args:
            skill: Skill instance to register. Must have a valid descriptor.

        Raises:
            SkillValidationError: If the skill's descriptor is invalid or
                if a skill with the same name is already registered.
        """
        name = skill.descriptor.name
        if not name:
            raise SkillValidationError("Skill descriptor must have a non-empty name")
        if name in self._skills:
            raise SkillValidationError(
                f"Skill '{name}' is already registered. "
                f"Unregister it first or use a different name."
            )

        self._skills[name] = skill
        logger.info("skill_registered", name=name, version=skill.version)

    def unregister(self, name: str) -> None:
        """Remove a skill from the registry.

        Args:
            name: Name of the skill to remove.

        Raises:
            SkillNotFoundError: If the skill is not registered.
        """
        if name not in self._skills:
            raise SkillNotFoundError(name)

        del self._skills[name]
        logger.info("skill_unregistered", name=name)

    # ── Lookup ──────────────────────────────────────────────────────────

    def get(self, name: str) -> Skill[Any, Any]:
        """Get a skill by name.

        Args:
            name: Unique skill identifier.

        Returns:
            The registered ``Skill`` instance.

        Raises:
            SkillNotFoundError: If no skill with this name is registered.
        """
        try:
            return self._skills[name]
        except KeyError:
            raise SkillNotFoundError(name) from None

    def has(self, name: str) -> bool:
        """Check whether a skill is registered.

        Args:
            name: Skill name to check.

        Returns:
            ``True`` if registered, ``False`` otherwise.
        """
        return name in self._skills

    def list_skills(self) -> list[SkillDescriptor]:
        """List descriptors for all registered skills.

        Returns:
            List of ``SkillDescriptor`` instances, sorted by name.
        """
        return [s.descriptor for s in sorted(self._skills.values(), key=lambda s: s.name)]

    # ── Search ──────────────────────────────────────────────────────────

    def search(
        self,
        *,
        tags: list[str] | None = None,
        status: SkillStatus | None = None,
        query: str | None = None,
    ) -> list[Skill[Any, Any]]:
        """Search for skills matching criteria.

        All provided filters are combined with AND logic.

        Args:
            tags: Skills must have at least one of these tags.
            status: Skills must have this lifecycle status.
            query: Case-insensitive substring match against name and description.

        Returns:
            List of matching ``Skill`` instances.
        """
        results: list[Skill[Any, Any]] = []

        for skill in self._skills.values():
            if tags and not set(tags) & set(skill.tags):
                continue
            if status is not None and skill.status != status:
                continue
            if query:
                q = query.lower()
                if q not in skill.name.lower() and q not in skill.description.lower():
                    continue
            results.append(skill)

        return sorted(results, key=lambda s: s.name)

    def to_prompt_catalog(self) -> str:
        """Generate a markdown catalog of all registered skills.

        Useful for injecting available skills into an LLM system prompt so
        the agent can decide which skill to invoke.

        Returns:
            Markdown-formatted catalog string.
        """
        if not self._skills:
            return "No skills registered."

        lines = ["# Available Skills", ""]
        for descriptor in self.list_skills():
            lines.append(f"## {descriptor.name}")
            lines.append(f"*{descriptor.description}*")
            if descriptor.metadata.tags:
                lines.append(f"Tags: {', '.join(descriptor.metadata.tags)}")
            if descriptor.parameters:
                lines.append("Parameters:")
                for p in descriptor.parameters:
                    req = " (required)" if p.required else ""
                    lines.append(f"  - `{p.name}` ({p.type}){req}: {p.description}")
            lines.append("")

        return "\n".join(lines)

    def __len__(self) -> int:
        """Return number of registered skills."""
        return len(self._skills)

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"<SkillRegistry skills={len(self._skills)}>"
