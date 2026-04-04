"""Unit test for issue #312 — spawn_agent with no model arg succeeds.

Verifies that ``WorkflowContext.spawn_agent()`` does not raise ``TypeError``
when called without an explicit ``model`` argument, using ``MockPrimitive``
from ``ttadev.primitives.testing.mocks`` to stand in as a chat model via
duck-typing.
"""

from __future__ import annotations

import pytest

from ttadev.agents.base import AgentPrimitive
from ttadev.agents.protocol import ChatMessage
from ttadev.agents.registry import AgentRegistry, override_registry
from ttadev.agents.spec import AgentSpec
from ttadev.agents.task import AgentResult, AgentTask
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.testing.mocks import MockPrimitive

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


class _MockChatModel:
    """Minimal ChatPrimitive duck-type backed by a MockPrimitive call tracker."""

    def __init__(self) -> None:
        self.tracker = MockPrimitive(name="chat-model", return_value="mock chat response")

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str:
        # Delegate through the MockPrimitive so call_count is tracked.
        result = await self.tracker.execute(messages, ctx)
        return str(result)


def _make_model_aware_agent(name: str) -> type[AgentPrimitive]:
    """Return an AgentPrimitive subclass whose __init__ requires ``model``."""
    spec = _make_spec(name)

    class _Agent(AgentPrimitive):
        def __init__(self, model: _MockChatModel) -> None:
            super().__init__(spec=spec, model=model)  # type: ignore[arg-type]

    _Agent.__name__ = name
    _Agent.__qualname__ = name
    return _Agent


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSpawnAgentNoModelArg:
    """Issue #312 — spawn_agent must not raise TypeError when model= is omitted."""

    @pytest.mark.asyncio
    async def test_spawn_agent_no_model_arg_with_context_default_succeeds(self) -> None:
        """Calling spawn_agent() with no model= kwarg succeeds when context has default_model.

        This is the core regression from issue #312: previously the call raised
        ``TypeError: __init__() missing 1 required positional argument: 'model'``
        because spawn_agent called ``agent_class()`` without injecting a model.
        """
        # Arrange
        mock_chat = _MockChatModel()
        agent_cls = _make_model_aware_agent("helper")

        reg = AgentRegistry()
        reg.register("helper", agent_cls)

        # Provide default model on the context — no explicit model= to spawn_agent.
        ctx = WorkflowContext(default_model=mock_chat)
        task = AgentTask(instruction="help me", context={}, constraints=[])

        # Act — must NOT raise TypeError (regression guard for #312)
        with override_registry(reg):
            result = await ctx.spawn_agent("helper", task)  # no model= kwarg

        # Assert
        assert isinstance(result, AgentResult)
        assert result.agent_name == "helper"

    @pytest.mark.asyncio
    async def test_mock_primitive_tracker_was_invoked(self) -> None:
        """The MockPrimitive tracker inside the chat model is called during agent execution.

        Confirms the model is actually exercised, not just accepted silently.
        """
        # Arrange
        mock_chat = _MockChatModel()
        agent_cls = _make_model_aware_agent("helper")

        reg = AgentRegistry()
        reg.register("helper", agent_cls)

        ctx = WorkflowContext(default_model=mock_chat)
        task = AgentTask(instruction="do something", context={}, constraints=[])

        # Act
        with override_registry(reg):
            await ctx.spawn_agent("helper", task)

        # Assert — MockPrimitive.call_count proves chat() was reached
        mock_chat.tracker.assert_called()
