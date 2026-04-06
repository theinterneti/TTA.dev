"""Streaming chunk iteration for litellm ``acompletion`` streaming responses.

Provides :func:`iter_stream_chunks`, an async generator that extracts
non-empty text delta strings from the raw litellm async stream object
returned when ``stream=True`` is passed to ``litellm.acompletion()``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any


async def iter_stream_chunks(stream: Any) -> AsyncIterator[str]:
    """Yield non-empty text delta chunks from a litellm streaming response.

    Args:
        stream: The async iterable returned by ``await litellm.acompletion(...,
            stream=True)``.

    Yields:
        Non-empty text delta strings as they arrive from the provider.
    """
    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content
