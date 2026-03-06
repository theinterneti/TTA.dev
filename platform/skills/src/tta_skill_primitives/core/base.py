"""Skill base class — a WorkflowPrimitive with SKILL.md metadata.

A Skill is a composable, self-describing unit of agent capability. It extends
``WorkflowPrimitive`` so that skills inherit the ``>>`` and ``|`` composition
operators and integrate seamlessly with existing recovery, performance, and
observability primitives.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Generic, TypeVar

import structlog
from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive

from .models import SkillDescriptor, SkillStatus

T = TypeVar("T")
U = TypeVar("U")

logger = structlog.get_logger(__name__)


class Skill(WorkflowPrimitive[T, U], Generic[T, U]):
    """Base class for agent skills.

    A Skill extends ``WorkflowPrimitive`` with self-describing metadata that
    follows the open SKILL.md specification.  This means every skill:

    * Carries a ``SkillDescriptor`` with name, description, parameters, etc.
    * Can be composed with ``>>`` (sequential) and ``|`` (parallel).
    * Can be wrapped in ``RetryPrimitive``, ``TimeoutPrimitive``, etc.
    * Can be registered in a ``SkillRegistry`` for dynamic discovery.

    Subclasses must implement ``execute()`` and provide a ``descriptor``.

    Example:
        ```python
        from tta_skill_primitives import Skill, SkillDescriptor

        class CodeReviewSkill(Skill[str, dict]):
            descriptor = SkillDescriptor(
                name="code-review",
                description="Analyse code for quality and security issues.",
            )

            async def execute(self, input_data: str, context: WorkflowContext) -> dict:
                # ... skill logic ...
                return {"issues": [], "score": 100}
        ```
    """

    descriptor: SkillDescriptor

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Validate that subclasses provide a descriptor."""
        super().__init_subclass__(**kwargs)
        # Skip validation for abstract subclasses
        if getattr(cls, "__abstractmethods__", None):
            return
        if not hasattr(cls, "descriptor") or cls.descriptor is None:
            raise TypeError(
                f"Skill subclass {cls.__name__} must define a class-level 'descriptor' "
                f"(SkillDescriptor instance)"
            )

    @abstractmethod
    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        """Execute the skill with input data and context.

        Args:
            input_data: Input data for the skill.
            context: Workflow context with session/state information.

        Returns:
            Output data from the skill.
        """
        ...

    # ── Convenience properties ──────────────────────────────────────────

    @property
    def name(self) -> str:
        """Return the skill's unique name."""
        return self.descriptor.name

    @property
    def description(self) -> str:
        """Return the skill's description."""
        return self.descriptor.description

    @property
    def version(self) -> str:
        """Return the skill's version string."""
        return self.descriptor.metadata.version

    @property
    def status(self) -> SkillStatus:
        """Return the skill's lifecycle status."""
        return self.descriptor.status

    @property
    def tags(self) -> list[str]:
        """Return the skill's searchable tags."""
        return self.descriptor.metadata.tags

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"<{self.__class__.__name__} name={self.name!r} "
            f"version={self.version!r} status={self.status.value!r}>"
        )
