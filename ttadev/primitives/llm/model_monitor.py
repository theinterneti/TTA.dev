"""ModelMonitorPrimitive — real-time LLM performance tracking.

Maintains in-memory rolling statistics per (model_id, provider) pair.
Models with success_rate below a configurable threshold are marked
unhealthy and excluded from routing for a configurable window.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from ttadev.primitives.core.base import WorkflowContext, WorkflowPrimitive

# ── Data models ───────────────────────────────────────────────────────────────


@dataclass
class ModelStats:
    """Accumulated performance statistics for a single (model_id, provider) pair.

    Attributes:
        model_id: Identifier of the model (e.g. ``"gpt-4o"``).
        provider: Provider name (e.g. ``"openai"``, ``"ollama"``).
        request_count: Total requests recorded (successes + failures).
        success_count: Number of successful requests.
        error_count: Number of failed requests.
        total_latency_ms: Cumulative latency of successful requests in ms.
        total_tokens: Cumulative token count from successful requests.
        last_error: Error message from the most recent failure, if any.
        last_success_at: Unix timestamp of the most recent success.
        last_error_at: Unix timestamp of the most recent failure.
    """

    model_id: str
    provider: str
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    last_error: str | None = None
    last_success_at: float | None = None
    last_error_at: float | None = None

    @property
    def success_rate(self) -> float:
        """Fraction of requests that succeeded (1.0 if no requests yet)."""
        if self.request_count == 0:
            return 1.0
        return self.success_count / self.request_count

    @property
    def avg_latency_ms(self) -> float:
        """Mean latency of successful requests in milliseconds."""
        if self.success_count == 0:
            return 0.0
        return self.total_latency_ms / self.success_count

    @property
    def tokens_per_second(self) -> float:
        """Token throughput: total_tokens / (total_latency_ms / 1000)."""
        if self.total_latency_ms == 0:
            return 0.0
        return self.total_tokens / (self.total_latency_ms / 1000)


@dataclass
class MonitorRequest:
    """Input for :class:`ModelMonitorPrimitive`.

    Attributes:
        action: One of ``"record"``, ``"get_stats"``, ``"get_all"``,
            ``"reset"``, ``"is_healthy"``.
        model_id: Model identifier.  Required for all actions except
            ``"get_all"`` and ``"reset"`` (where empty string resets all).
        provider: Provider name.  Required alongside *model_id*.
        success: Whether the request succeeded (used by ``"record"``).
        latency_ms: Request latency in ms (used by ``"record"`` on success).
        token_count: Tokens generated (used by ``"record"`` on success).
        error_message: Error description (used by ``"record"`` on failure).
    """

    action: str
    model_id: str = ""
    provider: str = ""
    success: bool = True
    latency_ms: float = 0.0
    token_count: int = 0
    error_message: str | None = None


@dataclass
class MonitorResponse:
    """Output from :class:`ModelMonitorPrimitive`.

    Attributes:
        action: Echoes the action that produced this response.
        stats: :class:`ModelStats` for the requested model, or ``None``.
        all_stats: Mapping of ``"{provider}:{model_id}"`` → :class:`ModelStats`
            (populated by ``"get_all"``).
        healthy: Whether the model is healthy for routing (``"is_healthy"``).
        failure_window_expires_at: Unix timestamp when the unhealthy window
            expires, or ``None`` if the model is healthy.
    """

    action: str
    stats: ModelStats | None = None
    all_stats: dict[str, ModelStats] = field(default_factory=dict)
    healthy: bool = True
    failure_window_expires_at: float | None = None


# ── Primitive ─────────────────────────────────────────────────────────────────


class ModelMonitorPrimitive(WorkflowPrimitive[MonitorRequest, MonitorResponse]):
    """Track per-model performance metrics for LLM provider health monitoring.

    Maintains in-memory rolling statistics per ``(model_id, provider)`` pair.
    Models with ``success_rate`` below *unhealthy_threshold* are marked
    unhealthy and excluded from routing for *failure_window_seconds* seconds.

    Supported actions:

    * ``record`` — Record a request outcome (success/failure, latency, tokens).
    * ``get_stats`` — Get :class:`ModelStats` for one model.
    * ``get_all`` — Get stats for all tracked models.
    * ``reset`` — Reset stats for one model (or all if ``model_id=""``).
    * ``is_healthy`` — Check if a model is currently healthy for routing.

    Args:
        failure_window_seconds: Seconds to keep a model marked unhealthy after
            it falls below the threshold.  Default: 1800 (30 minutes).
        unhealthy_threshold: ``success_rate`` below this triggers unhealthy
            status.  Default: 0.5 (50 %).

    Example:
        .. code-block:: python

            monitor = ModelMonitorPrimitive()
            ctx = WorkflowContext.root("llm-pipeline")

            monitor.record_success("gpt-4o", "openai", latency_ms=320, token_count=150)
            monitor.record_failure("gpt-4o", "openai", error="rate_limit")

            req = MonitorRequest(action="is_healthy", model_id="gpt-4o", provider="openai")
            resp = await monitor.execute(req, ctx)
            print(resp.healthy)  # True / False
    """

    def __init__(
        self,
        failure_window_seconds: float = 1800.0,
        unhealthy_threshold: float = 0.5,
    ) -> None:
        self._stats: dict[str, ModelStats] = {}
        self._failure_window = failure_window_seconds
        self._unhealthy_threshold = unhealthy_threshold
        self._unhealthy_until: dict[str, float] = {}

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _key(self, model_id: str, provider: str) -> str:
        return f"{provider}:{model_id}"

    def _ensure_stats(self, model_id: str, provider: str) -> ModelStats:
        key = self._key(model_id, provider)
        if key not in self._stats:
            self._stats[key] = ModelStats(model_id=model_id, provider=provider)
        return self._stats[key]

    # ── WorkflowPrimitive interface ───────────────────────────────────────────

    async def execute(self, request: MonitorRequest, ctx: WorkflowContext) -> MonitorResponse:
        """Dispatch *request.action* to the appropriate handler.

        Args:
            request: The monitor request specifying the action and parameters.
            ctx: Workflow context (used for tracing; not mutated by this primitive).

        Returns:
            A :class:`MonitorResponse` carrying the result of the action.

        Raises:
            ValueError: If *request.action* is not one of the supported actions.
        """
        action = request.action.lower()
        if action == "record":
            return self._record(request)
        elif action == "get_stats":
            return self._get_stats(request)
        elif action == "get_all":
            return MonitorResponse(action="get_all", all_stats=dict(self._stats))
        elif action == "reset":
            return self._reset(request)
        elif action == "is_healthy":
            return self._is_healthy(request)
        else:
            raise ValueError(
                f"Unknown action '{action}'. Valid: record, get_stats, get_all, reset, is_healthy"
            )

    # ── Action handlers ───────────────────────────────────────────────────────

    def _record(self, request: MonitorRequest) -> MonitorResponse:
        stats = self._ensure_stats(request.model_id, request.provider)
        key = self._key(request.model_id, request.provider)
        stats.request_count += 1
        if request.success:
            stats.success_count += 1
            stats.total_latency_ms += request.latency_ms
            stats.total_tokens += request.token_count
            stats.last_success_at = time.time()
        else:
            stats.error_count += 1
            stats.last_error = request.error_message
            stats.last_error_at = time.time()
            if stats.success_rate < self._unhealthy_threshold:
                self._unhealthy_until[key] = time.time() + self._failure_window
        return MonitorResponse(action="record", stats=stats)

    def _get_stats(self, request: MonitorRequest) -> MonitorResponse:
        key = self._key(request.model_id, request.provider)
        stats = self._stats.get(key)
        return MonitorResponse(action="get_stats", stats=stats)

    def _reset(self, request: MonitorRequest) -> MonitorResponse:
        if request.model_id:
            key = self._key(request.model_id, request.provider)
            self._stats.pop(key, None)
            self._unhealthy_until.pop(key, None)
        else:
            self._stats.clear()
            self._unhealthy_until.clear()
        return MonitorResponse(action="reset")

    def _is_healthy(self, request: MonitorRequest) -> MonitorResponse:
        key = self._key(request.model_id, request.provider)
        expiry = self._unhealthy_until.get(key)
        now = time.time()
        if expiry and now < expiry:
            return MonitorResponse(
                action="is_healthy",
                healthy=False,
                failure_window_expires_at=expiry,
            )
        if expiry:
            del self._unhealthy_until[key]
        return MonitorResponse(action="is_healthy", healthy=True)

    # ── Convenience / synchronous API ─────────────────────────────────────────

    def record_success(
        self,
        model_id: str,
        provider: str,
        latency_ms: float,
        token_count: int = 0,
    ) -> None:
        """Record a successful LLM call without going through *execute*.

        Args:
            model_id: Model identifier.
            provider: Provider name.
            latency_ms: Request round-trip latency in milliseconds.
            token_count: Number of tokens generated.
        """
        stats = self._ensure_stats(model_id, provider)
        stats.request_count += 1
        stats.success_count += 1
        stats.total_latency_ms += latency_ms
        stats.total_tokens += token_count
        stats.last_success_at = time.time()

    def record_failure(self, model_id: str, provider: str, error: str = "") -> None:
        """Record a failed LLM call without going through *execute*.

        Automatically marks the model unhealthy when ``success_rate`` drops
        below *unhealthy_threshold*.

        Args:
            model_id: Model identifier.
            provider: Provider name.
            error: Human-readable error description.
        """
        stats = self._ensure_stats(model_id, provider)
        key = self._key(model_id, provider)
        stats.request_count += 1
        stats.error_count += 1
        stats.last_error = error
        stats.last_error_at = time.time()
        if stats.success_rate < self._unhealthy_threshold:
            self._unhealthy_until[key] = time.time() + self._failure_window

    def is_healthy_sync(self, model_id: str, provider: str) -> bool:
        """Synchronous health check for use in routing logic.

        Args:
            model_id: Model identifier.
            provider: Provider name.

        Returns:
            ``True`` if the model is healthy (or has no recorded failures),
            ``False`` if it is within an active unhealthy window.
        """
        key = self._key(model_id, provider)
        expiry = self._unhealthy_until.get(key)
        now = time.time()
        if expiry and now < expiry:
            return False
        if expiry:
            del self._unhealthy_until[key]
        return True
