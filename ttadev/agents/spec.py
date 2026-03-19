"""AgentSpec — the 'suit of clothes' that turns a generalist model into a specialist."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ttadev.agents.task import AgentResult, AgentTask


class ToolRule(StrEnum):
    """How an agent is permitted to use a given tool."""

    ALWAYS = "always"
    WHEN_INSTRUCTED = "when_instructed"
    NEVER = "never"


@dataclasses.dataclass(frozen=True)
class AgentTool:
    """A tool available to an agent, with its usage rule."""

    name: str
    description: str
    rule: ToolRule


@dataclasses.dataclass(frozen=True)
class QualityGate:
    """A check that must pass before an agent returns its result."""

    name: str
    check: Callable[[AgentResult], bool]
    error_message: str


@dataclasses.dataclass(frozen=True)
class HandoffTrigger:
    """A condition that causes an agent to spawn a sub-agent mid-task."""

    condition: Callable[[AgentTask], bool]
    target_agent: str  # name in AgentRegistry
    reason: str


@dataclasses.dataclass(frozen=True)
class AgentSpec:
    """Complete specification for a role-based agent.

    An ``AgentSpec`` is immutable and shareable. It defines everything that
    makes a generalist model into a specialist: identity, knowledge (via
    ``system_prompt``), tools, quality standards, and handoff logic.

    Example::

        DEVELOPER_SPEC = AgentSpec(
            name="developer",
            role="Senior Python Developer",
            system_prompt="You are a senior Python developer...",
            capabilities=["code review", "debugging"],
            tools=[AgentTool("ruff", "linter", ToolRule.ALWAYS)],
            quality_gates=[],
            handoff_triggers=[],
        )
    """

    name: str
    role: str
    system_prompt: str
    capabilities: list[str]
    tools: list[AgentTool]
    quality_gates: list[QualityGate]
    handoff_triggers: list[HandoffTrigger]
