"""Tests for ttadev.agents.tool_call_loop — Task C1."""

import pytest

from ttadev.agents.protocol import ChatMessage
from ttadev.agents.tool_call_loop import (
    ToolCallLoop,
    ToolCallLoopError,
    ToolCallRequest,
    ToolDefinition,
)
from ttadev.primitives.core.base import WorkflowContext


class _StaticModel:
    """Returns a fixed string — no tool calls."""

    def __init__(self, response: str = "done"):
        self._response = response

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str:
        return self._response


class _ToolCallingModel:
    """First call requests a tool; second call returns final answer."""

    def __init__(self):
        self._call_count = 0

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str:
        self._call_count += 1
        if self._call_count == 1:
            return "__tool_call__:add_numbers:{}"
        return "the answer is 42"


class _InfiniteModel:
    """Always requests a tool — triggers iteration limit."""

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str:
        return "__tool_call__:add_numbers:{}"


class TestToolCallLoop:
    @pytest.mark.asyncio
    async def test_no_tool_calls_returns_response_directly(self):
        loop = ToolCallLoop(model=_StaticModel("hello"), tool_handlers={})
        request = ToolCallRequest(
            messages=[{"role": "user", "content": "hi"}],
            tools=[],
            system=None,
        )
        result = await loop.execute(request, WorkflowContext())
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_tool_call_resolved_and_loop_continues(self):
        handlers = {"add_numbers": lambda args: "42"}
        loop = ToolCallLoop(model=_ToolCallingModel(), tool_handlers=handlers)
        request = ToolCallRequest(
            messages=[{"role": "user", "content": "what is 6 * 7?"}],
            tools=[ToolDefinition(name="add_numbers", description="adds", parameters={})],
            system=None,
        )
        result = await loop.execute(request, WorkflowContext())
        assert "42" in result

    @pytest.mark.asyncio
    async def test_iteration_limit_raises(self):
        loop = ToolCallLoop(
            model=_InfiniteModel(),
            tool_handlers={"add_numbers": lambda args: "x"},
            max_iterations=3,
        )
        request = ToolCallRequest(
            messages=[{"role": "user", "content": "go"}],
            tools=[ToolDefinition(name="add_numbers", description="x", parameters={})],
            system=None,
        )
        with pytest.raises(ToolCallLoopError, match="iteration"):
            await loop.execute(request, WorkflowContext())

    def test_tool_definition_construction(self):
        t = ToolDefinition(name="ruff", description="linter", parameters={"path": "str"})
        assert t.name == "ruff"
        assert t.parameters == {"path": "str"}
