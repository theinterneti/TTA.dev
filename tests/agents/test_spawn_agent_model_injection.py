"""Regression tests for issue #312 — spawn_agent raises TypeError — model not injected.

Verifies that ``WorkflowContext.spawn_agent()`` correctly injects a ``ChatPrimitive``
model into agents that require one, without breaking legacy agents that wire their
own model internally.
"""

from __future__ import annotations

import pytest

from ttadev.agents.base import AgentPrimitive
from ttadev.agents.protocol import ChatMessage, ChatPrimitive
from ttadev.agents.registry import AgentRegistry, override_registry
from ttadev.agents.spec import AgentSpec
from ttadev.agents.task import AgentResult, AgentTask
from ttadev.primitives.core.base import WorkflowContext

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_spec(name: str) -> AgentSpec:
    return AgentSpec(
        name=name,
        role=name.title(),
        system_prompt=f"You are {name}.",
        capabilities=[name],
        tools=[],
        quality_gates=[],
        handoff_triggers=[],
    )


class _MockModel:
    """Minimal ChatPrimitive implementation — satisfies the protocol."""

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str:
        return f"mock response from {system or 'no-system'}"


# ---------------------------------------------------------------------------
# Agent factories
# ---------------------------------------------------------------------------


def _make_model_aware_agent(name: str) -> type[AgentPrimitive]:
    """Create an AgentPrimitive subclass whose __init__ requires ``model``."""
    spec = _make_spec(name)

    class _Agent(AgentPrimitive):
        # Track the last model received so tests can inspect it.
        _last_received_model: ChatPrimitive | None = None

        def __init__(self, model: ChatPrimitive) -> None:
            super().__init__(spec=spec, model=model)
            _Agent._last_received_model = model

    _Agent.__name__ = name
    _Agent.__qualname__ = name
    return _Agent


def _make_legacy_agent(name: str) -> type[AgentPrimitive]:
    """Create a legacy AgentPrimitive that hard-wires its own model (no ``model`` param)."""
    spec = _make_spec(name)

    class _LegacyAgent(AgentPrimitive):
        def __init__(self) -> None:
            super().__init__(spec=spec, model=_MockModel())

    _LegacyAgent.__name__ = name
    _LegacyAgent.__qualname__ = name
    return _LegacyAgent


# ---------------------------------------------------------------------------
# Tests — issue #312 regression
# ---------------------------------------------------------------------------


class TestSpawnAgentModelInjection:
    """Regression suite for issue #312."""

    # ------------------------------------------------------------------
    # Core bug: no TypeError when spawning a model-aware agent
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_spawn_agent_context_default_model_no_type_error(self):
        """Spawning a model-aware agent via context.default_model raises no TypeError.

        This is the direct regression for issue #312: previously ``agent_class()``
        was called with no arguments, causing ``TypeError: __init__() missing 1
        required positional argument: 'model'``.
        """
        mock_model = _MockModel()
        agent_cls = _make_model_aware_agent("helper")

        reg = AgentRegistry()
        reg.register("helper", agent_cls)

        # Provide the model on the context — not as an explicit kwarg.
        ctx = WorkflowContext(default_model=mock_model)
        task = AgentTask(instruction="help me", context={}, constraints=[])

        # Must NOT raise TypeError.
        with override_registry(reg):
            result = await ctx.spawn_agent("helper", task)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "helper"

    @pytest.mark.asyncio
    async def test_spawned_agent_has_non_none_model(self):
        """The spawned agent's internal _model attribute is non-None after spawn.

        Verifies the model is actually stored in the agent, not just accepted.
        """
        mock_model = _MockModel()
        agent_cls = _make_model_aware_agent("helper")
        agent_cls._last_received_model = None  # reset class-level tracker

        reg = AgentRegistry()
        reg.register("helper", agent_cls)

        ctx = WorkflowContext(default_model=mock_model)
        task = AgentTask(instruction="help me", context={}, constraints=[])

        with override_registry(reg):
            await ctx.spawn_agent("helper", task)

        # The class-level tracker was set during __init__
        assert agent_cls._last_received_model is mock_model

    @pytest.mark.asyncio
    async def test_spawn_agent_explicit_model_kwarg(self):
        """Explicit model= kwarg is passed through even when context has no default_model."""
        mock_model = _MockModel()
        agent_cls = _make_model_aware_agent("helper")

        reg = AgentRegistry()
        reg.register("helper", agent_cls)

        # No default_model on context.
        ctx = WorkflowContext()
        task = AgentTask(instruction="help me", context={}, constraints=[])

        with override_registry(reg):
            result = await ctx.spawn_agent("helper", task, model=mock_model)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "helper"

    @pytest.mark.asyncio
    async def test_explicit_model_takes_precedence_over_context_default(self):
        """Explicit model= overrides WorkflowContext.default_model."""
        context_model = _MockModel()
        explicit_model = _MockModel()

        agent_cls = _make_model_aware_agent("helper")
        agent_cls._last_received_model = None

        reg = AgentRegistry()
        reg.register("helper", agent_cls)

        ctx = WorkflowContext(default_model=context_model)
        task = AgentTask(instruction="help me", context={}, constraints=[])

        with override_registry(reg):
            await ctx.spawn_agent("helper", task, model=explicit_model)

        # explicit_model wins
        assert agent_cls._last_received_model is explicit_model
        assert agent_cls._last_received_model is not context_model

    # ------------------------------------------------------------------
    # Backward compatibility — legacy agents without model param still work
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_legacy_agent_still_works_no_model_param(self):
        """Legacy agents that hard-wire their own model are NOT broken by the fix."""
        legacy_agent_cls = _make_legacy_agent("legacy")

        reg = AgentRegistry()
        reg.register("legacy", legacy_agent_cls)

        ctx = WorkflowContext()
        task = AgentTask(instruction="legacy task", context={}, constraints=[])

        with override_registry(reg):
            result = await ctx.spawn_agent("legacy", task)

        assert isinstance(result, AgentResult)
        assert result.agent_name == "legacy"

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_spawn_agent_unknown_name_still_raises_key_error(self):
        """KeyError for unknown agent names is unchanged by the fix."""
        reg = AgentRegistry()
        ctx = WorkflowContext()
        task = AgentTask(instruction="x", context={}, constraints=[])

        with override_registry(reg), pytest.raises(KeyError, match="unknown-agent"):
            await ctx.spawn_agent("unknown-agent", task)

    @pytest.mark.asyncio
    async def test_spawn_agent_no_model_no_default_raises_value_error_not_type_error(self):
        """When no model can be resolved a ValueError is raised, not a TypeError.

        The original bug surfaced as TypeError because ``agent_class()`` was
        called without required args.  After the fix the error is a clear
        ValueError with a helpful message.
        """
        agent_cls = _make_model_aware_agent("helper")

        reg = AgentRegistry()
        reg.register("helper", agent_cls)

        # No model, no default_model → auto-discovery must also fail.
        # We patch _resolve_default_model to raise so the test is deterministic.
        import ttadev.primitives.core.base as _base_mod

        original = _base_mod._resolve_default_model

        def _always_fail() -> None:
            raise ValueError("no providers available in test environment")

        _base_mod._resolve_default_model = _always_fail
        try:
            ctx = WorkflowContext()
            task = AgentTask(instruction="x", context={}, constraints=[])

            with override_registry(reg), pytest.raises(ValueError):
                await ctx.spawn_agent("helper", task)
        finally:
            _base_mod._resolve_default_model = original
