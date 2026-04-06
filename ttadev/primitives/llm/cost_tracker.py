"""Token counting and cost calculation for LLM responses."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ttadev.primitives.llm._llm_types import LLMResponse


def build_langfuse_usage(provider: str, response: LLMResponse) -> dict[str, Any]:
    """Build a metadata dict with token usage and cost data for Langfuse.

    Extracts prompt/completion token counts from the response and looks up
    per-token pricing to compute USD cost breakdowns.  All failures are caught
    so callers never see an exception from this helper.

    Args:
        provider: Provider name string (e.g. ``"groq"``, ``"openai"``).
        response: The :class:`LLMResponse` returned by the provider.

    Returns:
        Dict with ``usage``, ``cost_details``, and ``cost_tier`` keys.
        Returns a minimal dict if pricing lookup fails.
    """
    usage = response.usage or {}
    prompt_tokens: int | None = usage.get("prompt_tokens") or usage.get("input_tokens")
    completion_tokens: int | None = usage.get("completion_tokens") or usage.get("output_tokens")

    result: dict[str, Any] = {
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
    }

    try:
        from ttadev.primitives.llm.model_pricing import get_pricing  # noqa: PLC0415

        pricing = get_pricing(provider, response.model)
        if pricing is not None:
            input_cost: float | None = None
            output_cost: float | None = None
            if prompt_tokens is not None and pricing.cost_per_1k_input_tokens is not None:
                input_cost = prompt_tokens * pricing.cost_per_1k_input_tokens / 1000.0
            if completion_tokens is not None and pricing.cost_per_1k_output_tokens is not None:
                output_cost = completion_tokens * pricing.cost_per_1k_output_tokens / 1000.0
            total_cost: float | None = None
            if input_cost is not None and output_cost is not None:
                total_cost = input_cost + output_cost
            result["cost_details"] = {
                "input_cost_usd": input_cost,
                "output_cost_usd": output_cost,
                "total_cost_usd": total_cost,
            }
            result["cost_tier"] = pricing.cost_tier
    except Exception:
        pass

    return result
