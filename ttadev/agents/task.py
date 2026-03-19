"""AgentTask, AgentResult, and Artifact — the input/output types for agents."""

from __future__ import annotations

import dataclasses
from typing import Any


@dataclasses.dataclass
class Artifact:
    """A file or structured output produced by an agent."""

    name: str
    content: str
    artifact_type: str  # "code", "test", "diff", "report"


@dataclasses.dataclass
class AgentTask:
    """Input to an agent — what it should do and the context it needs."""

    instruction: str
    context: dict[str, Any]
    constraints: list[str]
    agent_hint: str | None = None  # caller's preferred agent; router may override


@dataclasses.dataclass
class AgentResult:
    """Output from an agent — its response plus structured metadata."""

    agent_name: str
    response: str
    artifacts: list[Artifact]
    suggestions: list[str]
    spawned_agents: list[str]
    quality_gates_passed: bool
    confidence: float  # 0.0–1.0 self-assessed confidence
