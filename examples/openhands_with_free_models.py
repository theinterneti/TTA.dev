"""OpenHands + Free Model Discovery demo.

End-to-end example showing the three-way integration:

1. **Artificial Analysis** (via FreeModelTracker) — live benchmark-ranked
   list of free OpenRouter models.
2. **OpenHandsPrimitive** — runs an AI coding agent on a task.
3. **Langfuse** — traces the LLM generation automatically (when
   ``LANGFUSE_*`` env vars are set; silently skipped when absent).

Usage::

    # Minimum — needs an OpenRouter key for the agent call:
    export OPENROUTER_API_KEY="sk-or-..."
    uv run python examples/openhands_with_free_models.py

    # With Langfuse tracing:
    export LANGFUSE_SECRET_KEY="sk-lf-..."
    export LANGFUSE_PUBLIC_KEY="pk-lf-..."
    export LANGFUSE_HOST="https://cloud.langfuse.com"
    uv run python examples/openhands_with_free_models.py

Confirmed free models that work with OpenHands (as of 2026-04-04):

- ``openrouter/qwen/qwen3.6-plus:free``  (default)
- ``openrouter/openai/gpt-oss-20b:free``  (fallback)

Models that do NOT work are excluded at runtime by filtering against
``OPENHANDS_COMPATIBLE_FREE_MODELS``.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("openhands_demo")


# ── 1. Imports ────────────────────────────────────────────────────────────────


def _check_env() -> str:
    """Validate required environment variables and return the API key.

    Returns:
        OpenRouter API key from the environment.

    Raises:
        SystemExit: When ``OPENROUTER_API_KEY`` is not set.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        logger.error(
            "OPENROUTER_API_KEY is not set.\n"
            "  export OPENROUTER_API_KEY='sk-or-...'\n"
            "  uv run python examples/openhands_with_free_models.py"
        )
        sys.exit(1)
    return api_key


# ── 2. Model selection via Artificial Analysis ────────────────────────────────


async def pick_best_model(api_key: str) -> str:
    """Fetch AA-ranked free models and return the best OpenHands-compatible one.

    Uses :func:`~ttadev.primitives.llm.free_model_tracker.get_free_models` to
    pull the live OpenRouter free model list (cached for 1 week), then ranks by
    Artificial Analysis benchmark scores for the ``"coding"`` task type with
    :func:`~ttadev.primitives.llm.free_model_tracker.rank_models_for_role`.

    Finally, intersects with
    :data:`~ttadev.primitives.integrations.openhands_primitive.OPENHANDS_COMPATIBLE_FREE_MODELS`
    (empirically verified to support function calling + array-content messages)
    to avoid models that fail at runtime.

    Args:
        api_key: OpenRouter API key for authenticated model list fetch.

    Returns:
        Full LiteLLM model string (``"openrouter/<id>"``), e.g.
        ``"openrouter/qwen/qwen3.6-plus:free"``.
    """
    from ttadev.primitives.integrations.openhands_primitive import (
        OPENHANDS_COMPATIBLE_FREE_MODELS,
    )
    from ttadev.primitives.llm.free_model_tracker import get_free_models, rank_models_for_role

    logger.info("Fetching free model list from OpenRouter…")
    all_free = await get_free_models(api_key=api_key)
    logger.info("Found %d free text models on OpenRouter", len(all_free))

    # Rank by Artificial Analysis coding benchmarks
    ranked = rank_models_for_role(all_free, task_type="coding")
    logger.info(
        "Top 5 AA-ranked free models for coding: %s",
        [m.id for m in ranked[:5]],
    )

    # Build a set of bare IDs that are confirmed OpenHands-compatible.
    # OPENHANDS_COMPATIBLE_FREE_MODELS uses the "openrouter/" prefix; strip it.
    compatible_bare: set[str] = {
        m.removeprefix("openrouter/") for m in OPENHANDS_COMPATIBLE_FREE_MODELS
    }

    # Pick the highest-ranked model that's in the compatible set
    for model in ranked:
        if model.id.removesuffix(":free") in compatible_bare or model.id in compatible_bare:
            selected = f"openrouter/{model.id}"
            logger.info("Selected model (AA-ranked + OH-compatible): %s", selected)
            return selected

    # Fall back to the statically verified first choice
    fallback = OPENHANDS_COMPATIBLE_FREE_MODELS[0]
    logger.warning("No AA-ranked model matched the compatible list — using fallback: %s", fallback)
    return fallback


# ── 3. Main demo ──────────────────────────────────────────────────────────────

# Simple coding task the agent should be able to handle quickly.
DEMO_TASK = """\
Write a Python function called `fibonacci(n: int) -> int` that returns the
n-th Fibonacci number using memoization (functools.lru_cache).
Include a docstring and a brief example in the docstring.
When finished, call the finish tool with the complete function code.
"""


async def run_demo(model: str, api_key: str) -> None:
    """Run the OpenHands agent on the demo coding task.

    Traces are automatically sent to Langfuse when ``LANGFUSE_SECRET_KEY`` and
    ``LANGFUSE_PUBLIC_KEY`` environment variables are present.

    Args:
        model: LiteLLM model string (e.g. ``"openrouter/qwen/qwen3.6-plus:free"``).
        api_key: OpenRouter API key forwarded to the primitive.
    """
    from ttadev.primitives.core.base import WorkflowContext
    from ttadev.primitives.integrations.openhands_primitive import OpenHandsPrimitive

    prim = OpenHandsPrimitive(
        model=model,
        api_key=api_key,
        # No extra tools needed — the SDK provides FinishTool / ThinkTool built-in.
        tools=[],
        max_iterations=20,
        name="demo-coding-agent",
    )

    ctx = WorkflowContext(workflow_id="openhands-free-model-demo")

    logger.info("Running OpenHands agent with model=%s…", model)
    logger.info("Task: %s", DEMO_TASK.strip().splitlines()[0])

    result = await prim.execute(DEMO_TASK, ctx)

    print("\n" + "=" * 60)
    print(f"Status      : {result['status']}")
    print(f"Events      : {result['events_count']}")
    print(f"Conversation: {result['conversation_id']}")
    print("-" * 60)
    print("Agent output:")
    print(result["result"] or "(no text output — check events above)")
    print("=" * 60 + "\n")

    if result["status"] != "finished":
        logger.warning("Agent did not finish cleanly (status=%s)", result["status"])
    else:
        logger.info("✅ Agent finished successfully")


# ── 4. Composed workflow with fallback ────────────────────────────────────────


async def run_with_fallback(api_key: str) -> None:
    """Demonstrate composing OpenHandsPrimitive with RetryPrimitive + FallbackPrimitive.

    This shows the TTA.dev philosophy: **use primitives, never write manual
    retry loops**.  The outer ``RetryPrimitive`` retries on transient errors.
    If the primary model is exhausted, a ``FallbackPrimitive`` switches to the
    secondary confirmed-compatible model.

    Args:
        api_key: OpenRouter API key.
    """
    from ttadev.primitives.core.base import WorkflowContext
    from ttadev.primitives.integrations.openhands_primitive import (
        OPENHANDS_COMPATIBLE_FREE_MODELS,
        OpenHandsPrimitive,
    )
    from ttadev.primitives.recovery.fallback import FallbackPrimitive
    from ttadev.primitives.recovery.retry import RetryPrimitive

    ctx = WorkflowContext(workflow_id="openhands-fallback-demo")

    primary_model, *rest = OPENHANDS_COMPATIBLE_FREE_MODELS
    fallback_model = rest[0] if rest else primary_model

    primary = RetryPrimitive(
        OpenHandsPrimitive(model=primary_model, api_key=api_key, name="primary"),
        max_retries=2,
    )
    fallback = OpenHandsPrimitive(model=fallback_model, api_key=api_key, name="fallback")

    pipeline: FallbackPrimitive[str, dict] = FallbackPrimitive(
        primary=primary,
        fallback=fallback,
    )

    task = "Write a one-liner Python function that reverses a string. Use the finish tool."
    result = await pipeline.execute(task, ctx)
    logger.info("Fallback pipeline result status: %s", result.get("status"))


# ── Entry point ───────────────────────────────────────────────────────────────


async def main() -> None:
    """Orchestrate the full demo flow."""
    api_key = _check_env()

    # --- Step 1: Discover the best model via Artificial Analysis ---
    model = await pick_best_model(api_key)

    # --- Step 2: Run the agent on a coding task ---
    await run_demo(model, api_key)

    # --- Step 3: Show how to compose with retry + fallback ---
    print("Demonstrating composed retry + fallback pipeline…")
    print(
        "(skipping live run to save quota — "
        "uncomment `await run_with_fallback(api_key)` to enable)\n"
    )
    # await run_with_fallback(api_key)


if __name__ == "__main__":
    asyncio.run(main())
