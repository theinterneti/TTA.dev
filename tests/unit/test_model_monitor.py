"""Unit tests for ttadev/primitives/llm/model_monitor.py.

Covers:
- ModelStats: success_rate, avg_latency_ms, tokens_per_second properties, defaults
- MonitorRequest / MonitorResponse: dataclass defaults
- ModelMonitorPrimitive.execute:
    record success, record failure, get_stats, get_all,
    reset single, reset all, is_healthy, unknown action, case-insensitive actions
- Unhealthy window: trigger, active, expiry, cleanup
- Convenience API: record_success, record_failure, is_healthy_sync
- Internal helpers: _key, _ensure_stats
"""

from __future__ import annotations

import time

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.llm.model_monitor import (
    ModelMonitorPrimitive,
    ModelStats,
    MonitorRequest,
    MonitorResponse,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(wid: str = "monitor-test") -> WorkflowContext:
    return WorkflowContext(workflow_id=wid)


# ---------------------------------------------------------------------------
# ModelStats properties
# ---------------------------------------------------------------------------


class TestModelStats:
    def test_success_rate_no_requests_is_1(self):
        stats = ModelStats(model_id="m", provider="p")
        assert stats.success_rate == 1.0

    def test_success_rate_all_success(self):
        stats = ModelStats(model_id="m", provider="p", request_count=10, success_count=10)
        assert stats.success_rate == 1.0

    def test_success_rate_partial(self):
        stats = ModelStats(model_id="m", provider="p", request_count=10, success_count=7)
        assert stats.success_rate == pytest.approx(0.7)

    def test_success_rate_all_failures(self):
        stats = ModelStats(model_id="m", provider="p", request_count=5, success_count=0)
        assert stats.success_rate == 0.0

    def test_avg_latency_no_successes_is_0(self):
        stats = ModelStats(model_id="m", provider="p", success_count=0)
        assert stats.avg_latency_ms == 0.0

    def test_avg_latency_computed_correctly(self):
        stats = ModelStats(model_id="m", provider="p", success_count=4, total_latency_ms=800.0)
        assert stats.avg_latency_ms == pytest.approx(200.0)

    def test_tokens_per_second_no_latency_is_0(self):
        stats = ModelStats(model_id="m", provider="p", total_latency_ms=0)
        assert stats.tokens_per_second == 0.0

    def test_tokens_per_second_computed(self):
        # 100 tokens in 500ms = 200 tok/s
        stats = ModelStats(model_id="m", provider="p", total_tokens=100, total_latency_ms=500.0)
        assert stats.tokens_per_second == pytest.approx(200.0)

    def test_dataclass_defaults(self):
        s = ModelStats(model_id="m", provider="p")
        assert s.request_count == 0
        assert s.success_count == 0
        assert s.error_count == 0
        assert s.total_latency_ms == 0.0
        assert s.total_tokens == 0
        assert s.last_error is None
        assert s.last_success_at is None
        assert s.last_error_at is None


# ---------------------------------------------------------------------------
# MonitorRequest / MonitorResponse dataclass defaults
# ---------------------------------------------------------------------------


class TestMonitorDataclasses:
    def test_monitor_request_defaults(self):
        req = MonitorRequest(action="record")
        assert req.model_id == ""
        assert req.provider == ""
        assert req.success is True
        assert req.latency_ms == 0.0
        assert req.token_count == 0
        assert req.error_message is None

    def test_monitor_response_defaults(self):
        resp = MonitorResponse(action="record")
        assert resp.stats is None
        assert resp.all_stats == {}
        assert resp.healthy is True
        assert resp.failure_window_expires_at is None


# ---------------------------------------------------------------------------
# execute: record
# ---------------------------------------------------------------------------


class TestExecuteRecord:
    @pytest.mark.asyncio
    async def test_record_success_increments_counts(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        req = MonitorRequest(
            action="record",
            model_id="gpt-4o",
            provider="openai",
            success=True,
            latency_ms=300.0,
            token_count=50,
        )
        # Act
        resp = await monitor.execute(req, _ctx())
        # Assert
        assert resp.action == "record"
        assert resp.stats is not None
        assert resp.stats.request_count == 1
        assert resp.stats.success_count == 1
        assert resp.stats.error_count == 0
        assert resp.stats.total_latency_ms == 300.0
        assert resp.stats.total_tokens == 50

    @pytest.mark.asyncio
    async def test_record_success_sets_last_success_at(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        before = time.time()
        req = MonitorRequest(
            action="record", model_id="m", provider="p", success=True, latency_ms=100.0
        )
        # Act
        resp = await monitor.execute(req, _ctx())
        # Assert
        assert resp.stats is not None
        assert resp.stats.last_success_at is not None
        assert resp.stats.last_success_at >= before

    @pytest.mark.asyncio
    async def test_record_failure_increments_error_count(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        req = MonitorRequest(
            action="record",
            model_id="llama3",
            provider="ollama",
            success=False,
            error_message="timeout",
        )
        # Act
        resp = await monitor.execute(req, _ctx())
        # Assert
        assert resp.stats is not None
        assert resp.stats.error_count == 1
        assert resp.stats.success_count == 0
        assert resp.stats.last_error == "timeout"

    @pytest.mark.asyncio
    async def test_record_failure_sets_last_error_at(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        before = time.time()
        req = MonitorRequest(
            action="record", model_id="m", provider="p", success=False, error_message="err"
        )
        # Act
        resp = await monitor.execute(req, _ctx())
        # Assert
        assert resp.stats is not None
        assert resp.stats.last_error_at is not None
        assert resp.stats.last_error_at >= before

    @pytest.mark.asyncio
    async def test_record_accumulates_across_calls(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        ctx = _ctx()
        for _ in range(3):
            await monitor.execute(
                MonitorRequest(
                    action="record",
                    model_id="m",
                    provider="p",
                    success=True,
                    latency_ms=100.0,
                    token_count=10,
                ),
                ctx,
            )
        # Act
        resp = await monitor.execute(
            MonitorRequest(action="get_stats", model_id="m", provider="p"), ctx
        )
        # Assert
        assert resp.stats is not None
        assert resp.stats.request_count == 3
        assert resp.stats.total_latency_ms == 300.0
        assert resp.stats.total_tokens == 30

    @pytest.mark.asyncio
    async def test_record_failure_triggers_unhealthy(self):
        # Arrange: 1 success + 2 failures → rate = 1/3 < threshold 0.5
        monitor = ModelMonitorPrimitive(unhealthy_threshold=0.5)
        ctx = _ctx()
        await monitor.execute(
            MonitorRequest(
                action="record", model_id="m", provider="p", success=True, latency_ms=10
            ),
            ctx,
        )
        for _ in range(2):
            await monitor.execute(
                MonitorRequest(action="record", model_id="m", provider="p", success=False),
                ctx,
            )
        # Act
        resp = await monitor.execute(
            MonitorRequest(action="is_healthy", model_id="m", provider="p"), ctx
        )
        # Assert
        assert resp.healthy is False
        assert resp.failure_window_expires_at is not None


# ---------------------------------------------------------------------------
# execute: get_stats
# ---------------------------------------------------------------------------


class TestExecuteGetStats:
    @pytest.mark.asyncio
    async def test_get_stats_unknown_model_returns_none(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        # Act
        resp = await monitor.execute(
            MonitorRequest(action="get_stats", model_id="unknown", provider="p"), _ctx()
        )
        # Assert
        assert resp.action == "get_stats"
        assert resp.stats is None

    @pytest.mark.asyncio
    async def test_get_stats_tracked_model(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        ctx = _ctx()
        await monitor.execute(
            MonitorRequest(
                action="record", model_id="gpt-4o", provider="openai", success=True, latency_ms=200
            ),
            ctx,
        )
        # Act
        resp = await monitor.execute(
            MonitorRequest(action="get_stats", model_id="gpt-4o", provider="openai"), ctx
        )
        # Assert
        assert resp.stats is not None
        assert resp.stats.model_id == "gpt-4o"
        assert resp.stats.provider == "openai"


# ---------------------------------------------------------------------------
# execute: get_all
# ---------------------------------------------------------------------------


class TestExecuteGetAll:
    @pytest.mark.asyncio
    async def test_get_all_empty_when_no_models(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        # Act
        resp = await monitor.execute(MonitorRequest(action="get_all"), _ctx())
        # Assert
        assert resp.action == "get_all"
        assert resp.all_stats == {}

    @pytest.mark.asyncio
    async def test_get_all_returns_all_tracked_models(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        ctx = _ctx()
        for model, provider in [("m1", "p1"), ("m2", "p2")]:
            await monitor.execute(
                MonitorRequest(
                    action="record", model_id=model, provider=provider, success=True, latency_ms=100
                ),
                ctx,
            )
        # Act
        resp = await monitor.execute(MonitorRequest(action="get_all"), ctx)
        # Assert
        assert "p1:m1" in resp.all_stats
        assert "p2:m2" in resp.all_stats
        assert len(resp.all_stats) == 2


# ---------------------------------------------------------------------------
# execute: reset
# ---------------------------------------------------------------------------


class TestExecuteReset:
    @pytest.mark.asyncio
    async def test_reset_single_model_removes_it(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        ctx = _ctx()
        for m in ("m1", "m2"):
            await monitor.execute(
                MonitorRequest(
                    action="record", model_id=m, provider="p", success=True, latency_ms=50
                ),
                ctx,
            )
        # Act
        resp = await monitor.execute(
            MonitorRequest(action="reset", model_id="m1", provider="p"), ctx
        )
        # Assert
        assert resp.action == "reset"
        all_resp = await monitor.execute(MonitorRequest(action="get_all"), ctx)
        assert "p:m1" not in all_resp.all_stats
        assert "p:m2" in all_resp.all_stats

    @pytest.mark.asyncio
    async def test_reset_all_clears_everything(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        ctx = _ctx()
        for m in ("m1", "m2", "m3"):
            await monitor.execute(
                MonitorRequest(
                    action="record", model_id=m, provider="p", success=True, latency_ms=50
                ),
                ctx,
            )
        # Act — empty model_id resets all
        await monitor.execute(MonitorRequest(action="reset", model_id="", provider=""), ctx)
        # Assert
        all_resp = await monitor.execute(MonitorRequest(action="get_all"), ctx)
        assert all_resp.all_stats == {}

    @pytest.mark.asyncio
    async def test_reset_nonexistent_model_is_safe(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        # Act & Assert — no error
        resp = await monitor.execute(
            MonitorRequest(action="reset", model_id="ghost", provider="p"), _ctx()
        )
        assert resp.action == "reset"

    @pytest.mark.asyncio
    async def test_reset_clears_unhealthy_window(self):
        # Arrange — force unhealthy
        monitor = ModelMonitorPrimitive(unhealthy_threshold=0.9)
        ctx = _ctx()
        await monitor.execute(
            MonitorRequest(action="record", model_id="m", provider="p", success=False),
            ctx,
        )
        # Act
        await monitor.execute(MonitorRequest(action="reset", model_id="m", provider="p"), ctx)
        # Assert — healthy again
        resp = await monitor.execute(
            MonitorRequest(action="is_healthy", model_id="m", provider="p"), ctx
        )
        assert resp.healthy is True


# ---------------------------------------------------------------------------
# execute: is_healthy
# ---------------------------------------------------------------------------


class TestExecuteIsHealthy:
    @pytest.mark.asyncio
    async def test_is_healthy_true_for_unknown_model(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        # Act
        resp = await monitor.execute(
            MonitorRequest(action="is_healthy", model_id="unknown", provider="p"), _ctx()
        )
        # Assert
        assert resp.healthy is True

    @pytest.mark.asyncio
    async def test_is_healthy_true_for_healthy_model(self):
        # Arrange — all successes
        monitor = ModelMonitorPrimitive()
        ctx = _ctx()
        for _ in range(5):
            await monitor.execute(
                MonitorRequest(
                    action="record", model_id="m", provider="p", success=True, latency_ms=100
                ),
                ctx,
            )
        # Act
        resp = await monitor.execute(
            MonitorRequest(action="is_healthy", model_id="m", provider="p"), ctx
        )
        # Assert
        assert resp.healthy is True
        assert resp.failure_window_expires_at is None

    @pytest.mark.asyncio
    async def test_is_healthy_false_within_window(self):
        # Arrange — window=3600s, threshold=0.5 → 2 failures, rate=0 < 0.5
        monitor = ModelMonitorPrimitive(failure_window_seconds=3600, unhealthy_threshold=0.5)
        ctx = _ctx()
        for _ in range(2):
            await monitor.execute(
                MonitorRequest(action="record", model_id="m", provider="p", success=False),
                ctx,
            )
        # Act
        resp = await monitor.execute(
            MonitorRequest(action="is_healthy", model_id="m", provider="p"), ctx
        )
        # Assert
        assert resp.healthy is False
        assert resp.failure_window_expires_at is not None
        assert resp.failure_window_expires_at > time.time()

    @pytest.mark.asyncio
    async def test_is_healthy_recovers_after_window_expires(self):
        # Arrange — 0s window expires immediately
        monitor = ModelMonitorPrimitive(failure_window_seconds=0, unhealthy_threshold=0.9)
        ctx = _ctx()
        await monitor.execute(
            MonitorRequest(action="record", model_id="m", provider="p", success=False),
            ctx,
        )
        import asyncio

        await asyncio.sleep(0.01)

        # Act
        resp = await monitor.execute(
            MonitorRequest(action="is_healthy", model_id="m", provider="p"), ctx
        )
        # Assert
        assert resp.healthy is True


# ---------------------------------------------------------------------------
# execute: unknown action / case-insensitive
# ---------------------------------------------------------------------------


class TestExecuteActions:
    @pytest.mark.asyncio
    async def test_unknown_action_raises_value_error(self):
        monitor = ModelMonitorPrimitive()
        with pytest.raises(ValueError, match="Unknown action"):
            await monitor.execute(MonitorRequest(action="fly"), _ctx())

    @pytest.mark.asyncio
    async def test_actions_are_case_insensitive(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        # Act
        resp = await monitor.execute(MonitorRequest(action="GET_ALL"), _ctx())
        # Assert
        assert resp.action == "get_all"

    @pytest.mark.asyncio
    async def test_record_mixed_case(self):
        monitor = ModelMonitorPrimitive()
        resp = await monitor.execute(
            MonitorRequest(
                action="RECORD", model_id="m", provider="p", success=True, latency_ms=100
            ),
            _ctx(),
        )
        assert resp.action == "record"


# ---------------------------------------------------------------------------
# Convenience methods
# ---------------------------------------------------------------------------


class TestConvenienceMethods:
    def test_record_success_updates_stats(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        # Act
        monitor.record_success("gpt-4o", "openai", latency_ms=250.0, token_count=100)
        # Assert
        stats = monitor._stats["openai:gpt-4o"]
        assert stats.request_count == 1
        assert stats.success_count == 1
        assert stats.total_latency_ms == 250.0
        assert stats.total_tokens == 100
        assert stats.last_success_at is not None

    def test_record_success_default_token_count_zero(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        # Act
        monitor.record_success("m", "p", latency_ms=100.0)
        # Assert
        assert monitor._stats["p:m"].total_tokens == 0

    def test_record_failure_updates_stats(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        # Act
        monitor.record_failure("llama3", "ollama", error="connection_refused")
        # Assert
        stats = monitor._stats["ollama:llama3"]
        assert stats.request_count == 1
        assert stats.error_count == 1
        assert stats.last_error == "connection_refused"
        assert stats.last_error_at is not None

    def test_record_failure_marks_model_unhealthy(self):
        # Arrange — threshold 0.5: 1 success + 2 failures → 1/3 < 0.5
        monitor = ModelMonitorPrimitive(unhealthy_threshold=0.5)
        monitor.record_success("m", "p", latency_ms=10.0)
        monitor.record_failure("m", "p", error="e")
        monitor.record_failure("m", "p", error="e")
        # Assert
        assert monitor.is_healthy_sync("m", "p") is False

    def test_is_healthy_sync_true_for_clean_model(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        monitor.record_success("m", "p", latency_ms=100.0, token_count=50)
        # Assert
        assert monitor.is_healthy_sync("m", "p") is True

    def test_is_healthy_sync_true_for_unknown_model(self):
        # Arrange
        monitor = ModelMonitorPrimitive()
        # Assert — no entries → healthy by default
        assert monitor.is_healthy_sync("unknown", "provider") is True

    def test_is_healthy_sync_false_within_window(self):
        # Arrange
        monitor = ModelMonitorPrimitive(failure_window_seconds=3600, unhealthy_threshold=0.9)
        monitor.record_failure("m", "p", error="err")
        # Assert
        assert monitor.is_healthy_sync("m", "p") is False

    def test_is_healthy_sync_recovers_after_expiry(self):
        # Arrange — 0s window
        monitor = ModelMonitorPrimitive(failure_window_seconds=0, unhealthy_threshold=0.9)
        monitor.record_failure("m", "p", error="err")
        time.sleep(0.01)
        # Act
        result = monitor.is_healthy_sync("m", "p")
        # Assert
        assert result is True
        assert "p:m" not in monitor._unhealthy_until

    def test_multiple_providers_tracked_independently(self):
        # Arrange — p1 unhealthy, p2 healthy
        monitor = ModelMonitorPrimitive(unhealthy_threshold=0.5)
        monitor.record_failure("m", "p1", error="e")
        monitor.record_failure("m", "p1", error="e")
        monitor.record_success("m", "p2", latency_ms=100.0)
        # Assert
        assert monitor.is_healthy_sync("m", "p1") is False
        assert monitor.is_healthy_sync("m", "p2") is True


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


class TestInternalHelpers:
    def test_key_format(self):
        monitor = ModelMonitorPrimitive()
        assert monitor._key("gpt-4o", "openai") == "openai:gpt-4o"

    def test_ensure_stats_creates_entry(self):
        monitor = ModelMonitorPrimitive()
        stats = monitor._ensure_stats("m", "p")
        assert "p:m" in monitor._stats
        assert stats.model_id == "m"
        assert stats.provider == "p"

    def test_ensure_stats_returns_same_object(self):
        monitor = ModelMonitorPrimitive()
        s1 = monitor._ensure_stats("m", "p")
        s2 = monitor._ensure_stats("m", "p")
        assert s1 is s2

    def test_failure_window_configurable(self):
        monitor = ModelMonitorPrimitive(failure_window_seconds=60.0)
        assert monitor._failure_window == 60.0

    def test_unhealthy_threshold_configurable(self):
        monitor = ModelMonitorPrimitive(unhealthy_threshold=0.8)
        assert monitor._unhealthy_threshold == 0.8
