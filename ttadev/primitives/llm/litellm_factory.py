"""Factory function for building resilient LLM workflows with TTA.dev primitives.

Provides :func:`make_resilient_llm` which composes a
:class:`~ttadev.primitives.llm.litellm_primitive.LiteLLMPrimitive` with
:class:`~ttadev.primitives.recovery.retry.RetryPrimitive` and optionally
:class:`~ttadev.primitives.performance.cache.CachePrimitive`.
"""

from __future__ import annotations

import json
from typing import Any

from ttadev.primitives.core import WorkflowContext, WorkflowPrimitive
from ttadev.primitives.llm.universal_llm_primitive import LLMProvider, LLMRequest, LLMResponse


def make_resilient_llm(
    provider: str | LLMProvider | None = None,
    *,
    litellm_fallbacks: list[str] | None = None,
    api_key: str | None = None,
    api_base: str | None = None,
    timeout: float | None = None,
    metadata: dict[str, Any] | None = None,
    retry_attempts: int = 3,
    cache: bool = True,
    cache_ttl_seconds: float = 3600.0,
) -> WorkflowPrimitive[LLMRequest, LLMResponse]:
    """Build a resilient LLM workflow using TTA.dev primitives.

    Composes a :class:`~ttadev.primitives.llm.litellm_primitive.LiteLLMPrimitive`
    with TTA.dev's :class:`~ttadev.primitives.recovery.retry.RetryPrimitive` and
    optionally :class:`~ttadev.primitives.performance.cache.CachePrimitive`.

    Litellm-native fallbacks (``litellm_fallbacks``) are used for cross-model
    fallback chains rather than TTA.dev's :class:`FallbackPrimitive`, because
    they keep the request consistent across all attempts.

    The resulting stack::

        CachePrimitive          ← optional, keyed on messages + model + params
          └─ RetryPrimitive     ← 3 attempts, exponential back-off
               └─ LiteLLMPrimitive(provider, fallbacks=[...])

    Example::

        from ttadev.primitives.llm import make_resilient_llm, LLMRequest, LLMProvider
        from ttadev.primitives.core import WorkflowContext

        llm = make_resilient_llm(
            LLMProvider.GROQ,
            litellm_fallbacks=["anthropic/claude-3-haiku-20240307", "ollama/llama3.2"],
        )
        resp = await llm.execute(
            LLMRequest(model="llama-3.1-8b-instant", messages=[...]),
            WorkflowContext(workflow_id="demo"),
        )

    Args:
        provider: Provider prefix bound to the
            :class:`~ttadev.primitives.llm.litellm_primitive.LiteLLMPrimitive`.
            When ``None``, ``request.model`` must be a full litellm model string.
        litellm_fallbacks: Ordered list of litellm model strings to attempt when
            the primary call fails.
        api_key: API key override forwarded to
            :class:`~ttadev.primitives.llm.litellm_primitive.LiteLLMPrimitive`.
        api_base: Base URL override forwarded to
            :class:`~ttadev.primitives.llm.litellm_primitive.LiteLLMPrimitive`.
        timeout: Per-call timeout in seconds.
        metadata: Extra metadata forwarded to litellm (Langfuse traces, etc.).
        retry_attempts: Number of retry attempts on transient failures (default 3).
        cache: When ``True`` (default), wrap in a
            :class:`~ttadev.primitives.performance.cache.CachePrimitive`.
        cache_ttl_seconds: Cache TTL.  Defaults to ``3600`` (1 hour).

    Returns:
        A :class:`WorkflowPrimitive` ready to call with :class:`LLMRequest`.
    """
    import hashlib  # noqa: PLC0415

    from ttadev.primitives import RetryPrimitive  # noqa: PLC0415

    # Local import to avoid circular dependency: litellm_primitive → litellm_factory
    # → litellm_primitive.  The import is deferred to call time when the module is
    # fully loaded.
    from ttadev.primitives.llm.litellm_primitive import LiteLLMPrimitive  # noqa: PLC0415
    from ttadev.primitives.recovery.retry import RetryStrategy  # noqa: PLC0415

    primary: WorkflowPrimitive[LLMRequest, LLMResponse] = LiteLLMPrimitive(
        provider=provider,
        fallbacks=litellm_fallbacks,
        api_key=api_key,
        api_base=api_base,
        timeout=timeout,
        metadata=metadata,
    )

    retried: WorkflowPrimitive[LLMRequest, LLMResponse] = RetryPrimitive(
        primary,
        strategy=RetryStrategy(max_retries=retry_attempts, backoff_base=2.0),
    )

    if not cache:
        return retried

    from ttadev.primitives import CachePrimitive  # noqa: PLC0415

    def _cache_key(req: LLMRequest, _ctx: WorkflowContext) -> str:
        parts = [
            str(req.model),
            f"{req.temperature:.4f}",
            str(req.max_tokens),
            req.system or "",
            json.dumps(req.messages, sort_keys=True),
        ]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    return CachePrimitive(retried, cache_key_fn=_cache_key, ttl_seconds=cache_ttl_seconds)
