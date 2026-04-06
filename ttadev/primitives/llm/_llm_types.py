"""LLM request/response types shared across universal_llm_primitive modules.

This module exists solely to break circular import dependencies between
provider_dispatch, streaming, cost_tracker, and universal_llm_primitive.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class LLMProvider(StrEnum):
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"
    GOOGLE = "google"
    OPENROUTER = "openrouter"
    TOGETHER = "together"
    XAI = "xai"


@dataclass
class ToolSchema:
    """Provider-agnostic tool declaration for native LLM tool-calling.

    Describes a single callable tool that can be passed to an LLM so the
    model may elect to invoke it.  The ``parameters`` field must be a valid
    JSON Schema object (``{"type": "object", "properties": {...}, ...}``).

    Example::

        weather_tool = ToolSchema(
            name="get_weather",
            description="Return current weather for a city.",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        )
    """

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema object for the tool's parameters
    strict: bool = False  # OpenAI strict-mode tool calling

    def to_openai(self) -> dict[str, Any]:
        """Convert to OpenAI function-calling wire format.

        Returns:
            A dict with ``{"type": "function", "function": {...}}`` structure
            as expected by the OpenAI (and OpenAI-compatible) chat completions
            API.  When ``strict=True``, adds the ``"strict": true`` field
            inside the function object to enable structured outputs.
        """
        func: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
        if self.strict:
            func["strict"] = True
        return {"type": "function", "function": func}

    def to_anthropic(self) -> dict[str, Any]:
        """Convert to Anthropic tool_use wire format.

        Returns:
            A dict with ``{"name": ..., "description": ..., "input_schema": ...}``
            structure as expected by the Anthropic Messages API.  The
            ``parameters`` dict is passed verbatim as ``input_schema``; it
            must already be a valid JSON Schema object.
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


@dataclass
class ToolCall:
    """A single tool invocation returned by the model.

    Populated in ``LLMResponse.tool_calls`` when the model decides to call
    one or more tools instead of (or in addition to) producing text.

    Attributes:
        id: Provider-assigned call identifier.  Used when sending tool results
            back to the model in the next turn.
        name: The name of the tool that the model wants to invoke.
        arguments: Parsed JSON arguments for the tool call, keyed by parameter
            name.  Always a ``dict`` — never a raw JSON string.
    """

    id: str
    name: str
    arguments: dict[str, Any]  # Parsed from the provider's JSON string


@dataclass
class LLMRequest:
    """Parameters for a single LLM invocation.

    Attributes:
        model: Provider model identifier (e.g. ``"gpt-4o"``, ``"llama3"``).
        messages: Chat history in OpenAI-compatible ``[{"role": ..., "content": ...}]``
            format.
        temperature: Sampling temperature (0–2).  Defaults to ``0.7``.
        max_tokens: Maximum tokens to generate.  ``None`` lets the provider
            decide.
        system: System prompt text.  Injected as a system message for providers
            that support it.
        stream: When ``True``, use the streaming interface (``primitive.stream()``).
        tools: Optional list of tool declarations to expose to the model.
            When ``None`` (default) no tool-calling behaviour is activated.
        tool_choice: How the model should select tools.  Accepted values are
            ``"auto"`` (default), ``"none"``, ``"required"``, or the name of a
            specific tool.
    """

    model: str
    messages: list[dict[str, str]]
    temperature: float = 0.7
    max_tokens: int | None = None
    system: str | None = None
    stream: bool = False
    tools: list[ToolSchema] | None = None
    tool_choice: str = "auto"


@dataclass
class LLMResponse:
    """Result of a single LLM invocation.

    Attributes:
        content: Text content returned by the model.  May be an empty string
            when the model's response consists entirely of tool calls.
        model: Model identifier echoed from the provider response.
        provider: Name of the provider that handled the request (e.g.
            ``"openai"``, ``"anthropic"``).
        usage: Token usage metadata.  Keys vary by provider
            (``prompt_tokens``/``input_tokens``, ``completion_tokens``/
            ``output_tokens``).
        tool_calls: Populated when the model invokes one or more tools.
            ``None`` when the response is plain text (backward-compatible
            default).
        finish_reason: The reason the model stopped generating.  Common values
            are ``"stop"`` (natural end), ``"tool_calls"`` (tool invocation),
            and ``"length"`` (max_tokens reached).  ``None`` for providers
            that do not report a finish reason.
    """

    content: str
    model: str
    provider: str
    usage: dict[str, int] | None = None
    tool_calls: list[ToolCall] | None = None
    finish_reason: str | None = None
