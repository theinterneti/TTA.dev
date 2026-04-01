"""ToolCallLoop — runs the model → tool call → result → model conversation loop.

CUSTOM TEXT-BASED TOOL-CALLING PROTOCOL
----------------------------------------
This module implements a **custom, text-based** tool-calling convention rather
than the structured tool-calling APIs provided by LLM providers (OpenAI function
calling, Anthropic ``tool_use`` blocks, etc.).

Protocol format
~~~~~~~~~~~~~~~
The model is expected to signal a tool call by beginning its response with::

    __tool_call__:<tool_name>:<json_args>

For example::

    __tool_call__:ruff:{"path": "ttadev/"}

Requirements
~~~~~~~~~~~~
1. **The model MUST be instructed via a system prompt** to use this exact format
   when it wants to invoke a tool. Without that instruction the model will never
   produce the ``__tool_call__:`` prefix and tool calls will never fire.

2. This protocol is **NOT compatible** with native structured tool-calling
   out of the box:

   - OpenAI / Groq return tool calls as structured ``tool_calls`` objects in
     ``choice.message.tool_calls``, not as text prefixes.
   - Anthropic returns ``tool_use`` content blocks, not text.
   - Ollama can return either format depending on the model and ``tools``
     parameter.

   Using ``ToolCallLoop`` with a provider that emits structured tool-call
   payloads will silently skip all tool invocations because the text prefix
   check will never match.

3. The ``ChatPrimitive`` used as ``model`` must surface the raw text content
   of the assistant turn so that the prefix check in ``_execute_impl`` can work.

Future work
~~~~~~~~~~~
# TODO: Add native structured tool-calling support to ToolCallLoop #dev-todo
# type:: implementation
# priority:: medium
# package:: ttadev
# Replace (or augment) the custom __tool_call__ text protocol with proper
# provider-specific structured tool-call handling (OpenAI tool_calls objects,
# Anthropic tool_use blocks) so that ToolCallLoop works with standard provider
# APIs without requiring a custom system prompt.
"""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.observability.instrumented_primitive import InstrumentedPrimitive

if TYPE_CHECKING:
    from ttadev.agents.protocol import ChatMessage, ChatPrimitive

# Sentinel prefix used to signal tool calls in model responses.
# Format: __tool_call__:<tool_name>:<json_args>
_TOOL_CALL_PREFIX = "__tool_call__:"


class ToolCallLoopError(RuntimeError):
    """Raised when the tool call loop exceeds its iteration limit."""


@dataclasses.dataclass
class ToolDefinition:
    """Declaration of a tool the model may call."""

    name: str
    description: str
    parameters: dict[str, Any]


@dataclasses.dataclass
class ToolCallRequest:
    """Input to ToolCallLoop."""

    messages: list[ChatMessage]
    tools: list[ToolDefinition]
    system: str | None = None


class ToolCallLoop(InstrumentedPrimitive[ToolCallRequest, str]):
    """Runs the LLM function-calling conversation loop until completion.

    The loop continues until the model returns a response that does not
    contain a tool call, or until ``max_iterations`` is reached.

    Tool calls are detected by the ``__tool_call__:<name>:<json>`` prefix
    convention. Handlers are plain callables: ``(args: dict) -> str``.

    Example::

        loop = ToolCallLoop(
            model=AnthropicPrimitive(),
            tool_handlers={"ruff": run_ruff},
            max_iterations=5,
        )
        result = await loop.execute(request, ctx)
    """

    def __init__(
        self,
        model: ChatPrimitive,
        tool_handlers: dict[str, Callable[[dict[str, Any]], str]],
        max_iterations: int = 10,
    ) -> None:
        super().__init__(name="tool_call_loop")
        self._model = model
        self._handlers = tool_handlers
        self._max_iterations = max_iterations

    async def _execute_impl(self, request: ToolCallRequest, ctx: WorkflowContext) -> str:
        messages = list(request.messages)

        for iteration in range(self._max_iterations):
            response = await self._model.chat(messages, request.system, ctx)

            if not response.startswith(_TOOL_CALL_PREFIX):
                return response

            # Parse tool call
            rest = response[len(_TOOL_CALL_PREFIX) :]
            parts = rest.split(":", 1)
            tool_name = parts[0]
            raw_args = parts[1] if len(parts) > 1 else "{}"
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                args = {}

            # Execute handler
            handler = self._handlers.get(tool_name)
            if handler is None:
                tool_result = f"Error: no handler registered for tool {tool_name!r}"
            else:
                tool_result = handler(args)

            # Append tool result as assistant + user turn
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": f"Tool result: {tool_result}"})

        raise ToolCallLoopError(
            f"Tool call loop exceeded {self._max_iterations} iteration(s) without "
            "reaching a final response."
        )
