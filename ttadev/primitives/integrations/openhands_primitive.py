"""OpenHands SDK integration primitive.

Wraps the OpenHands SDK ``Agent`` + ``Conversation`` pair as a
:class:`WorkflowPrimitive` so that agent task execution composes naturally with
the rest of the TTA.dev primitive ecosystem (retry, timeout, cache, circuit
breaker, etc.).

OpenHands (https://github.com/All-Hands-AI/OpenHands) is an AI agent platform
with state-of-the-art coding-agent benchmarks.  This primitive uses its lean
``openhands-sdk`` package, which ships a Python-only runtime (no Docker/Redis
required) that talks to the same LiteLLM-backed LLM surface as
``ModelRouterPrimitive``.

Prerequisites:
    ``openhands-sdk`` is a core TTA.dev dependency — no extra install needed::

        uv sync  # already included

Example:
    ```python
    import asyncio
    from ttadev.primitives.integrations.openhands_primitive import (
        OpenHandsPrimitive,
    )
    from ttadev.primitives.core.base import WorkflowContext

    # Use a confirmed-compatible free model via OpenRouter
    prim = OpenHandsPrimitive(model="openrouter/qwen/qwen3.6-plus:free")
    ctx = WorkflowContext(workflow_id="demo")
    result = await prim.execute("Write a haiku about recursion.", ctx)
    print(result["result"])   # final agent message
    print(result["status"])   # "finished" | "stuck" | "error"

    # Compose with retry + timeout
    from ttadev.primitives import RetryPrimitive, TimeoutPrimitive
    workflow = TimeoutPrimitive(
        RetryPrimitive(prim),
        timeout_seconds=120.0,
    )
    result = await workflow.execute("Fix the failing tests in src/", ctx)
    ```

Provider compatibility notes (empirically verified 2026-04-04):

    **Works with OpenHands (free, require tool-use + array-content support):**
    - ``openrouter/qwen/qwen3.6-plus:free`` ✅ confirmed (status=finished)
    - ``openrouter/openai/gpt-oss-20b:free`` ✅ confirmed (status=finished)

    **Does NOT work:**
    - Gemma (any version, any provider) — function calling not enabled on Gemma models
    - Google AI Studio Gemma (``gemini/gemma-3-*-it``) — "Function calling is not enabled"
    - Ollama Gemma3 — "does not support thinking" (SDK sends reasoning_effort=high)
    - Groq free tier — 12K TPM hard limit; OpenHands sends ~36K tokens per request
    - ``openrouter/openai/gpt-oss-120b:free`` — provider rejects array-content messages (422)
    - ``openrouter/meta-llama/llama-3.3-70b-instruct:free`` — rate limited (provider 429)
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..llm.model_discovery import best_google_free_model
from ..observability.logging import get_logger

try:
    from opentelemetry import trace as _otel_trace

    _TRACING_AVAILABLE = True
except ImportError:  # pragma: no cover
    _otel_trace = None  # type: ignore[assignment]
    _TRACING_AVAILABLE = False

# openhands-sdk loads .env on import (side effect). To avoid polluting the
# process environment when this module is merely imported, we defer the actual
# SDK import until first use.  _require_sdk() checks availability via
# importlib.util.find_spec so we can fail fast without triggering the side effect.
import importlib.util as _importlib_util

_SDK_AVAILABLE: bool = _importlib_util.find_spec("openhands") is not None

logger = get_logger(__name__)
_std_logger = logging.getLogger(__name__)

# Sentinel used when callers do not supply an API key.
_ENV_KEY = "__from_env__"

# Sentinel values that mean "auto-pick the best available Google model".
_GOOGLE_AUTO_SENTINELS: frozenset[str] = frozenset({"google", "google/auto", "gemini/auto"})

# Free models confirmed compatible with OpenHands (tool-use + array-content support).
# Empirically verified 2026-04-04. Prefix with "openrouter/" for LiteLLM.
# Models that require function calling support AND accept array-content messages.
# Gemma (all versions/providers) and Groq free tier are NOT compatible.
#
# NOTE: This is an empirically-verified list. For Google models, prefer best_google_free_model()
# which queries the live native API instead of maintaining a static list.
# Use _OPENHANDS_DENYLIST to mark known-broken models without removing them from discovery.
OPENHANDS_COMPATIBLE_FREE_MODELS: list[str] = [
    "openrouter/qwen/qwen3.6-plus:free",
    "openrouter/openai/gpt-oss-20b:free",
]

# Models that are known to be broken with OpenHands — excluded from auto-selection.
# Do NOT remove entries from OPENHANDS_COMPATIBLE_FREE_MODELS; add them here instead.
_OPENHANDS_DENYLIST: dict[str, str] = {
    "openai/gpt-oss-120b:free": "array-content message format rejected by OpenHands",
    "google/gemma-3n-e4b-it:free": "Gemma family: no function calling support",
    "google/gemma-3-27b-it:free": "Gemma family: no function calling support",
    "google/gemma-3-12b-it:free": "Gemma family: no function calling support",
    "google/gemma-2-27b-it:free": "Gemma family: no function calling support",
}


async def get_ranked_openhands_free_models(
    task_type: str | None = None,
    or_api_key: str | None = None,
) -> list[str]:
    """Return OPENHANDS_COMPATIBLE_FREE_MODELS ranked by Artificial Analysis quality.

    Fetches the live OpenRouter free model list, filters to OpenHands-compatible
    models (must support tool use and have sufficient context), then ranks them
    using AA benchmark data for the given task type.

    The ``openrouter/`` prefix used by LiteLLM is stripped for the OR API
    comparison and re-applied to the returned IDs so callers can pass results
    directly to :class:`OpenHandsPrimitive`.

    Args:
        task_type: Optional hint — ``"coding"``, ``"math"``, ``"reasoning"``,
            or ``None`` for general-purpose ranking.
        or_api_key: OpenRouter API key (improves rate limits on the model list
            endpoint).

    Returns:
        Ranked list of model IDs with ``openrouter/`` prefix, best quality
        first.  Falls back to :data:`OPENHANDS_COMPATIBLE_FREE_MODELS` (in
        its original order) if the live fetch or ranking fails.
    """
    from ttadev.primitives.llm.free_model_tracker import get_free_models, rank_models_for_role

    try:
        all_free = await get_free_models(api_key=or_api_key)
        # OPENHANDS_COMPATIBLE_FREE_MODELS uses "openrouter/" prefix for LiteLLM;
        # OR API model IDs omit that prefix — strip it for the membership check.
        compatible_base_ids = {
            mid.removeprefix("openrouter/") for mid in OPENHANDS_COMPATIBLE_FREE_MODELS
        }
        compatible = [m for m in all_free if m.id in compatible_base_ids]
        if not compatible:
            return OPENHANDS_COMPATIBLE_FREE_MODELS
        ranked = rank_models_for_role(compatible, task_type=task_type)
        # Re-apply the "openrouter/" prefix expected by LiteLLM / OpenHandsPrimitive.
        return [f"openrouter/{m.id}" for m in ranked]
    except Exception:
        return OPENHANDS_COMPATIBLE_FREE_MODELS


def _require_sdk() -> None:
    """Raise ``ImportError`` with a helpful message when the SDK is absent."""
    if not _SDK_AVAILABLE:  # pragma: no cover
        raise ImportError("openhands-sdk is required but not installed. Run: uv add openhands-sdk")


class OpenHandsAgentError(RuntimeError):
    """Raised when the OpenHands agent finishes in a non-success state."""

    def __init__(self, status: str, events_count: int) -> None:
        """Initialize error.

        Args:
            status: Conversation execution status ("stuck", "error", etc.)
            events_count: Number of events recorded before the failure.
        """
        super().__init__(
            f"OpenHands agent finished with status={status!r} after {events_count} events"
        )
        self.status = status
        self.events_count = events_count


class OpenHandsPrimitive(WorkflowPrimitive[str | dict[str, Any], dict[str, Any]]):
    """Run an OpenHands AI agent as a TTA.dev ``WorkflowPrimitive``.

    The primitive accepts a *task* string (or a dict with a ``"task"`` key),
    executes it via the OpenHands SDK ``Agent`` + ``Conversation`` pair, and
    returns a result dict containing the final agent message and metadata.

    Because ``Conversation.run()`` is synchronous, execution is offloaded to a
    thread-pool executor so that the event loop is never blocked.

    Args:
        model: LiteLLM model string (e.g. ``"groq/llama-3.3-70b-versatile"``,
            ``"ollama/mistral"``, ``"anthropic/claude-3-5-haiku-20241022"``).
        api_key: API key for the model provider.  Defaults to ``None`` which
            lets LiteLLM discover credentials from environment variables.
        base_url: Optional base URL override (useful for Ollama or proxies).
        tools: List of OpenHands built-in tool names to enable.  Defaults to
            ``["finish"]`` which allows the agent to signal task completion.
        workspace_dir: Directory the agent uses for file operations.  Defaults
            to a temporary directory created per-execution.
        max_iterations: Maximum agent steps before the conversation is
            considered stuck.  Defaults to 50.
        name: Human-readable name for this primitive (appears in traces/logs).
        raise_on_stuck: When ``True`` (default), raise ``OpenHandsAgentError``
            if the agent gets stuck instead of returning a result dict.

    Example:
        ```python
        prim = OpenHandsPrimitive(
            model="groq/llama-3.3-70b-versatile",
            tools=["finish", "think"],
        )
        result = await prim.execute("Summarise the README.", ctx)
        # result == {"result": "...", "status": "finished", "events_count": N}
        ```
    """

    def __init__(
        self,
        model: str = "openrouter/qwen/qwen3.6-plus:free",
        api_key: str | None = None,
        base_url: str | None = None,
        tools: list[str] | None = None,
        workspace_dir: str | Path | None = None,
        max_iterations: int = 50,
        name: str = "openhands",
        raise_on_stuck: bool = True,
        extra_body: dict | None = None,
    ) -> None:
        """Initialize the OpenHands primitive.

        Args:
            model: LiteLLM model string (e.g. ``"groq/llama-3.3-70b-versatile"``
                or ``"openrouter/qwen/qwen3-235b-a22b:free"``).  The default
                Groq model is free with a ``GROQ_API_KEY`` and reliably supports
                OpenHands' array-content message format.  Many OpenRouter
                ``:free`` providers reject array-content messages with a 422
                error; prefer Groq or test compatibility before switching.
            api_key: Provider API key (None = discover from environment).
            base_url: Optional base URL for the LLM endpoint.
            tools: Additional custom tool names to register beyond the SDK
                built-ins (``FinishTool``, ``ThinkTool``).  Pass ``[]`` or
                omit to use only the built-in tools — do *not* pass
                ``["finish"]`` as that name is not registered and will raise
                ``KeyError``.
            workspace_dir: Working directory scoping the agent's file
                operations.  Restrict this to a safe subdirectory (e.g.
                ``docs/``) when running untrusted tasks.
            max_iterations: Hard cap on agent reasoning steps.
            name: Identifier used in logs and traces.
            raise_on_stuck: Raise on stuck/error status if True.
            extra_body: Extra fields forwarded to the LLM provider via
                LiteLLM's ``extra_body`` mechanism.  Use
                ``{"reasoning_effort": "none"}`` for Ollama thinking models
                (qwen3, qwen3.5, deepseek-r1) to disable the reasoning trace
                and ensure ``message.content`` is populated.
        """
        _require_sdk()
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.tools = tools if tools is not None else []
        self.workspace_dir = Path(workspace_dir) if workspace_dir else None
        self.max_iterations = max_iterations
        self.name = name
        self.raise_on_stuck = raise_on_stuck
        self.extra_body = extra_body or {}

    def _build_llm(self) -> Any:
        """Construct the LiteLLM-backed LLM config.

        Resolves Google "auto" sentinel values (``"google"``, ``"google/auto"``,
        ``"gemini/auto"``) via :func:`best_google_free_model` before building
        the LLM.  Clears ``reasoning_effort`` for Ollama models, which reject
        that parameter.

        Returns:
            Configured ``LLM`` instance.
        """
        from openhands.sdk import LLM
        from pydantic import SecretStr

        # --- Resolve model name -----------------------------------------------
        model = self.model

        if model in _GOOGLE_AUTO_SENTINELS:
            # Auto-pick the best available Google model via live API discovery.
            google_api_key = self.api_key or os.environ.get("GOOGLE_API_KEY", "")
            resolved = asyncio.run(best_google_free_model(google_api_key))
            if resolved is None:
                fallback = "gemini/gemini-2.0-flash-lite"
                _std_logger.warning(
                    "best_google_free_model() returned None; falling back to %s",
                    fallback,
                )
                resolved = fallback
            model = resolved
        elif model.startswith("gemini/"):
            # User explicitly specified a gemini/ model — use as-is.
            pass

        # --- Build LLM config -------------------------------------------------
        kwargs: dict[str, Any] = {"model": model}
        if self.api_key is not None:
            kwargs["api_key"] = SecretStr(self.api_key)
        if self.base_url is not None:
            kwargs["base_url"] = self.base_url
        llm_config = LLM(**kwargs)

        # Ollama thinking models (qwen3, qwen3.5, deepseek-r1) auto-enable thinking
        # via the OpenAI-compat endpoint unless explicitly disabled.  Python None
        # means "omit the field" → auto-thinking fires → message.content is empty.
        # The string "none" explicitly disables the reasoning trace.
        if self.model.startswith("ollama"):
            if self.extra_body.get("reasoning_effort") == "none":
                llm_config.reasoning_effort = "none"
            else:
                llm_config.reasoning_effort = None

        return llm_config

    def _build_agent(self) -> Any:
        """Construct the OpenHands Agent.

        Returns:
            Configured ``Agent`` instance.
        """
        from openhands.sdk import Agent, Tool

        tool_objects = [Tool(name=t) for t in self.tools]
        return Agent(llm=self._build_llm(), tools=tool_objects)

    def _extract_result(self, conversation: Any) -> str:
        """Extract the last agent message from the conversation event stream.

        Iterates the event log in reverse and returns the text of the first
        ``MessageEvent`` with ``source == "agent"``.  Falls back to an empty
        string when no such event exists.

        Args:
            conversation: A completed ``LocalConversation`` instance.

        Returns:
            Final agent message text, or empty string if none found.
        """
        last_text = ""
        # Events live at conversation.state.events (not conversation.events)
        for event in conversation.state.events:
            if getattr(event, "source", None) == "agent" and hasattr(event, "llm_message"):
                for content in event.llm_message.content:
                    if hasattr(content, "text"):
                        last_text = content.text
        return last_text

    def _run_sync(self, task: str, workspace_path: Path) -> dict[str, Any]:
        """Execute the agent synchronously (called from thread pool).

        Args:
            task: The task description to send to the agent.
            workspace_path: Directory for the agent's workspace.

        Returns:
            Result dict with ``result``, ``status``, ``events_count``,
            and ``conversation_id``.

        Raises:
            OpenHandsAgentError: If the agent gets stuck and ``raise_on_stuck``
                is True.
        """
        from openhands.sdk import Conversation
        from openhands.sdk.conversation.state import ConversationExecutionStatus

        agent = self._build_agent()
        conversation = Conversation(
            agent=agent,
            workspace=str(workspace_path),
            max_iteration_per_run=self.max_iterations,
            delete_on_close=True,
        )
        try:
            conversation.send_message(task)
            conversation.run()

            status_val = conversation.state.execution_status
            status_name = status_val.value if hasattr(status_val, "value") else str(status_val)
            events_count = len(list(conversation.state.events))
            result_text = self._extract_result(conversation)
            conversation_id = str(conversation.state.id)

        finally:
            conversation.close()

        if self.raise_on_stuck and status_val not in (
            ConversationExecutionStatus.FINISHED,
            ConversationExecutionStatus.IDLE,
        ):
            raise OpenHandsAgentError(
                status=status_name,
                events_count=events_count,
            )

        return {
            "result": result_text,
            "status": status_name,
            "events_count": events_count,
            "conversation_id": conversation_id,
        }

    async def execute(
        self, input_data: str | dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Run the OpenHands agent on the given task.

        Args:
            input_data: Either a plain task string, or a dict with a ``"task"``
                key and optional ``"workspace_dir"`` override.
            context: TTA.dev workflow context (used for tracing and logging).

        Returns:
            Dict with keys:

            - ``result`` (str): Final agent message text.
            - ``status`` (str): ``"finished"``, ``"stuck"``, or similar.
            - ``events_count`` (int): Total events recorded.
            - ``conversation_id`` (str): Conversation UUID for debugging.

        Raises:
            ValueError: If ``input_data`` is a dict without a ``"task"`` key.
            OpenHandsAgentError: If the agent gets stuck and
                ``raise_on_stuck`` is True.
        """
        if isinstance(input_data, str):
            task = input_data
            override_workspace: Path | None = None
        else:
            task = input_data.get("task", "")
            if not task:
                raise ValueError("input_data dict must contain a non-empty 'task' key")
            ws = input_data.get("workspace_dir")
            override_workspace = Path(ws) if ws else None

        workspace_path = override_workspace or self.workspace_dir
        span_name = f"openhands.{self.name}.execute"

        t_start = time.monotonic()

        async def _run() -> dict[str, Any]:
            if _TRACING_AVAILABLE and _otel_trace is not None:
                tracer = _otel_trace.get_tracer("ttadev.primitives.integrations.openhands")
                with tracer.start_as_current_span(span_name) as span:
                    span.set_attribute("openhands.model", self.model)
                    span.set_attribute("openhands.primitive_name", self.name)
                    span.set_attribute("openhands.max_iterations", self.max_iterations)
                    span.set_attribute("ttadev.workflow_id", context.workflow_id)
                    return await self._execute_with_workspace(task, workspace_path)
            return await self._execute_with_workspace(task, workspace_path)

        def _emit_langfuse(
            result: dict[str, Any] | None,
            duration: float,
            error: BaseException | None = None,
        ) -> None:
            """Emit a Langfuse generation record (fails silently)."""
            try:
                from tta_apm_langfuse import get_integration  # noqa: PLC0415

                _lf = get_integration()
                if _lf is not None:
                    status = (result or {}).get("status", "error")
                    events_count = (result or {}).get("events_count", 0)
                    output = (result or {}).get("result", "") if error is None else str(error)
                    _lf.create_generation(
                        name="openhands-agent",
                        model=self.model,
                        input=task[:2000],
                        output=output,
                        metadata={
                            "status": status,
                            "events_count": events_count,
                            "duration_seconds": round(duration, 3),
                            "workdir": str(workspace_path or self.workspace_dir or "<temp>"),
                        },
                    )
            except Exception:
                pass  # never let observability break the workflow

        try:
            result = await _run()
            duration = time.monotonic() - t_start
            _emit_langfuse(result, duration)
            return result
        except Exception as exc:
            duration = time.monotonic() - t_start
            _emit_langfuse(None, duration, error=exc)
            raise

    async def _execute_with_workspace(
        self, task: str, workspace_path: Path | None
    ) -> dict[str, Any]:
        """Handle workspace setup and dispatch to thread pool.

        Args:
            task: Task description string.
            workspace_path: Optional explicit workspace directory.

        Returns:
            Result dict from ``_run_sync``.
        """
        if workspace_path is not None:
            workspace_path.mkdir(parents=True, exist_ok=True)
            return await asyncio.get_event_loop().run_in_executor(
                None, self._run_sync, task, workspace_path
            )

        # Use a temp dir scoped to this execution.
        with tempfile.TemporaryDirectory(prefix="openhands_prim_") as tmpdir:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._run_sync, task, Path(tmpdir)
            )
