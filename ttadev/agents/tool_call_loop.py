"""ToolCallLoop — runs the model → tool call → result → model conversation loop.

NATIVE STRUCTURED TOOL-CALLING SUPPORT
---------------------------------------
This module supports **provider-native** structured tool-calling formats as well
as a legacy text-based fallback.  The ``_parse_tool_calls`` helper detects the
response shape and extracts tool invocations regardless of provider:

- **OpenAI / Groq**: ``response.choices[0].message.tool_calls``
- **Anthropic**: ``response.content`` list — items where ``type == "tool_use"``
- **Google**: ``response.candidates[0].content.parts`` — items with ``.function_call``
- **Legacy / mock**: text prefixed with ``__tool_call__:<name>:<json>``

Tool registration
~~~~~~~~~~~~~~~~~
Use ``_format_tools_for_provider`` to convert ``ToolDefinition`` objects into
the correct wire format for each provider before passing them to the API.

Example::

    loop = ToolCallLoop(
        model=UniversalLLMPrimitive(...),
        tool_handlers={"ruff": run_ruff},
        max_iterations=5,
    )
    result = await loop.execute(request, ctx)
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

# Sentinel prefix used in legacy / mock responses to signal a tool call.
# Format: __tool_call__:<tool_name>:<json_args>
_TOOL_CALL_PREFIX = "__tool_call__:"


class ToolCallLoopError(RuntimeError):
    """Raised when the tool call loop exceeds its iteration limit."""


@dataclasses.dataclass
class ToolCall:
    """A single tool invocation parsed from a provider response.

    Attributes:
        name: The tool name the model wants to invoke.
        arguments: Parsed keyword arguments for the tool call.
    """

    name: str
    arguments: dict[str, Any]


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


def _parse_tool_calls(response: Any) -> list[ToolCall]:  # noqa: ANN401
    """Parse tool calls from a provider response in any supported format.

    Detects the response shape and extracts tool invocations for four
    provider families plus a legacy text fallback:

    - **OpenAI / Groq**: ``response.choices[0].message.tool_calls``
    - **Anthropic**: ``response.content`` — a list; items where ``type == "tool_use"``
    - **Google**: ``response.candidates[0].content.parts`` — items with ``.function_call``
    - **Legacy / mock text**: string starting with ``__tool_call__:<name>:<json>``

    Args:
        response: Raw provider response object *or* a plain string from a
            legacy / mock model.  Any other type returns an empty list.

    Returns:
        A (possibly empty) list of :class:`ToolCall` instances.  Returns an
        empty list when no tool calls are present, keeping callers simple.

    Example::

        calls = _parse_tool_calls(groq_response)
        for tc in calls:
            result = handlers[tc.name](tc.arguments)
    """
    # ── OpenAI / Groq ─────────────────────────────────────────────────────────
    if hasattr(response, "choices"):
        tool_calls: list[ToolCall] = []
        try:
            message = response.choices[0].message
            raw_calls = getattr(message, "tool_calls", None) or []
            for tc in raw_calls:
                raw_args = tc.function.arguments
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
                except (json.JSONDecodeError, TypeError):
                    args = {}
                tool_calls.append(ToolCall(name=tc.function.name, arguments=args))
        except (IndexError, AttributeError):
            pass
        return tool_calls

    # ── Anthropic ─────────────────────────────────────────────────────────────
    if hasattr(response, "content") and isinstance(response.content, list):
        tool_calls = []
        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                input_data = getattr(block, "input", {}) or {}
                tool_calls.append(ToolCall(name=block.name, arguments=dict(input_data)))
        return tool_calls

    # ── Google ────────────────────────────────────────────────────────────────
    if hasattr(response, "candidates"):
        tool_calls = []
        try:
            parts = response.candidates[0].content.parts
            for part in parts:
                fc = getattr(part, "function_call", None)
                if fc is not None:
                    args = dict(fc.args) if hasattr(fc, "args") else {}
                    tool_calls.append(ToolCall(name=fc.name, arguments=args))
        except (IndexError, AttributeError):
            pass
        return tool_calls

    # ── Legacy text prefix (mock / backward-compat) ───────────────────────────
    if isinstance(response, str) and response.startswith(_TOOL_CALL_PREFIX):
        rest = response[len(_TOOL_CALL_PREFIX) :]
        parts = rest.split(":", 1)
        tool_name = parts[0]
        raw_args = parts[1] if len(parts) > 1 else "{}"
        try:
            args = json.loads(raw_args)
        except json.JSONDecodeError:
            args = {}
        return [ToolCall(name=tool_name, arguments=args)]

    # Plain text response — no tool calls
    return []


def _format_tools_for_provider(
    tools: list[ToolDefinition],
    provider_type: str,
) -> list[dict[str, Any]]:
    """Convert ``ToolDefinition`` objects into the provider's native wire format.

    Args:
        tools: List of tool declarations to expose to the model.
        provider_type: One of ``"openai"``, ``"groq"``, ``"anthropic"``,
            ``"google"``.  Unknown values fall back to the OpenAI format.

    Returns:
        A list of dicts in the provider's expected tool schema format, ready
        to be passed directly to the provider SDK.

    Example::

        openai_tools = _format_tools_for_provider(tools, "openai")
        client.chat.completions.create(model=..., messages=..., tools=openai_tools)
    """
    if provider_type in ("openai", "groq"):
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    if provider_type == "anthropic":
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
            }
            for t in tools
        ]

    if provider_type == "google":
        return [
            {
                "function_declarations": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    }
                    for t in tools
                ]
            }
        ]

    # Unknown provider — default to OpenAI format
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        }
        for t in tools
    ]


class ToolCallLoop(InstrumentedPrimitive[ToolCallRequest, str]):
    """Runs the LLM function-calling conversation loop until completion.

    The loop continues until the model returns a response that does not
    contain any tool calls, or until ``max_iterations`` is reached.

    Tool calls are detected via :func:`_parse_tool_calls`, which handles
    OpenAI/Groq, Anthropic, Google, and legacy text formats automatically.
    Handlers are plain callables: ``(args: dict) -> str``.

    Example::

        loop = ToolCallLoop(
            model=UniversalLLMPrimitive(...),
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

        for _iteration in range(self._max_iterations):
            response = await self._model.chat(messages, request.system, ctx)

            tool_calls = _parse_tool_calls(response)
            if not tool_calls:
                # Plain text final answer — return it directly.
                return response if isinstance(response, str) else str(response)

            # Append the assistant turn (text representation of the response).
            response_text = response if isinstance(response, str) else str(response)
            messages.append({"role": "assistant", "content": response_text})

            # Execute each tool call and feed results back as user turns.
            for tool_call in tool_calls:
                handler = self._handlers.get(tool_call.name)
                if handler is None:
                    tool_result = f"Error: no handler registered for tool {tool_call.name!r}"
                else:
                    tool_result = handler(tool_call.arguments)
                messages.append(
                    {"role": "user", "content": f"Tool result ({tool_call.name}): {tool_result}"}
                )

        raise ToolCallLoopError(
            f"Tool call loop exceeded {self._max_iterations} iteration(s) without "
            "reaching a final response."
        )
