"""WorkflowDefinition — static workflow structure and result types."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ttadev.agents.task import AgentResult, AgentTask, Artifact


@dataclass(frozen=True)
class WorkflowStep:
    """A single step in a WorkflowDefinition."""

    agent: str
    gate: bool = True
    input_transform: Callable[[Any], AgentTask] | None = None


@dataclass(frozen=True)
class MemoryConfig:
    """Memory behaviour for a workflow run."""

    flush_to_persistent: bool = True
    bank_id: str | None = None


@dataclass(frozen=True)
class WorkflowDefinition:
    """Immutable description of a multi-step guided workflow."""

    name: str
    description: str
    steps: list[WorkflowStep]
    auto_approve: bool = False
    memory_config: MemoryConfig = field(default_factory=MemoryConfig)


@dataclass
class StepResult:
    """Result of a single workflow step."""

    step_index: int
    agent_name: str
    result: AgentResult
    skipped: bool = False
    gate_decision: str = "continue"


@dataclass
class WorkflowResult:
    """Aggregated result of a complete workflow run."""

    workflow_name: str
    goal: str
    steps: list[StepResult]
    artifacts: list[Artifact]
    memory_snapshot: dict[str, Any]
    completed: bool
    total_confidence: float
