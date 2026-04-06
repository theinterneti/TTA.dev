"""Tool-call parsing utilities for litellm/OpenAI wire-format responses.

Provides :func:`parse_tool_calls` which converts the raw ``tool_calls`` list
returned by ``litellm.acompletion()`` into TTA.dev
:class:`~ttadev.primitives.llm.universal_llm_primitive.ToolCall` objects.
"""

from __future__ import annotations

import json
from typing import Any

from ttadev.primitives.llm.universal_llm_primitive import ToolCall


def parse_tool_calls(raw_calls: list[Any] | None) -> list[ToolCall] | None:
    """Convert litellm/OpenAI tool-call objects to TTA.dev :class:`ToolCall`.

    litellm returns tool calls in OpenAI wire format; this function extracts
    the id, function name, and JSON-decoded arguments.  Malformed entries
    are silently skipped.

    Args:
        raw_calls: The ``tool_calls`` list from a litellm response choice.

    Returns:
        A list of :class:`ToolCall` objects, or ``None`` when *raw_calls*
        is empty or ``None``.
    """
    if not raw_calls:
        return None
    result: list[ToolCall] = []
    for tc in raw_calls:
        try:
            fn = tc.function
            raw_args = fn.arguments
            args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
            result.append(ToolCall(id=tc.id, name=fn.name, arguments=args))
        except Exception:  # noqa: BLE001
            continue
    return result or None
