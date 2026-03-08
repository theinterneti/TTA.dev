"""tta-skill-primitives — SKILL.md-compatible agent skill framework.

Provides composable skill primitives for any AI agent that needs modular,
discoverable capabilities. Built on TTA workflow primitives, skills inherit
``>>`` and ``|`` composition and integrate with recovery/performance primitives.

Usage:
    ```python
    from tta_skill_primitives import Skill, SkillDescriptor, SkillRegistry
    from tta_dev_primitives import WorkflowContext

    class CodeReviewSkill(Skill[str, dict]):
        descriptor = SkillDescriptor(
            name="code-review",
            description="Analyse code for quality and security issues.",
        )

        async def execute(self, input_data: str, context: WorkflowContext) -> dict:
            return {"issues": [], "score": 100}

    # Register and discover
    registry = SkillRegistry()
    registry.register(CodeReviewSkill())

    skill = registry.get("code-review")
    result = await skill.execute("def foo(): pass", WorkflowContext())
    ```

Skills:
    - Skill: Base class extending WorkflowPrimitive with SKILL.md metadata
    - SkillDescriptor: Pydantic model for SKILL.md YAML frontmatter
    - SkillRegistry: In-memory registry for discovery and search
    - parse_skill_md / load_skill_md / dump_skill_md: SKILL.md file I/O
"""

from .core.base import Skill
from .core.models import (
    SkillDescriptor,
    SkillMetadata,
    SkillParameter,
    SkillStatus,
)
from .errors import (
    SkillError,
    SkillLoadError,
    SkillNotFoundError,
    SkillValidationError,
)
from .loader import dump_skill_md, load_skill_md, parse_skill_md
from .registry import SkillRegistry

__all__ = [
    # Core
    "Skill",
    "SkillDescriptor",
    "SkillMetadata",
    "SkillParameter",
    "SkillStatus",
    # Registry
    "SkillRegistry",
    # Loader
    "parse_skill_md",
    "load_skill_md",
    "dump_skill_md",
    # Errors
    "SkillError",
    "SkillNotFoundError",
    "SkillValidationError",
    "SkillLoadError",
]
