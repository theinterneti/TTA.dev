"""Pre-built DevelopmentCycle agent factories for common roles."""

from __future__ import annotations

from ttadev.workflows.development_cycle import DevelopmentCycle


def coding_assistant(
    bank_id: str = "tta-dev",
    base_url: str | None = None,
    timeout: float = 10.0,
) -> DevelopmentCycle:
    """DevelopmentCycle configured for code generation (agent_hint='developer')."""
    return DevelopmentCycle(
        bank_id=bank_id, base_url=base_url, agent_hint="developer", timeout=timeout
    )


def code_reviewer(
    bank_id: str = "tta-dev",
    base_url: str | None = None,
    timeout: float = 10.0,
) -> DevelopmentCycle:
    """DevelopmentCycle configured for code review (agent_hint='qa')."""
    return DevelopmentCycle(bank_id=bank_id, base_url=base_url, agent_hint="qa", timeout=timeout)


def qa_agent(
    bank_id: str = "tta-dev",
    base_url: str | None = None,
    timeout: float = 10.0,
) -> DevelopmentCycle:
    """DevelopmentCycle configured for test generation (agent_hint='qa')."""
    return DevelopmentCycle(bank_id=bank_id, base_url=base_url, agent_hint="qa", timeout=timeout)
