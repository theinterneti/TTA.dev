"""Tests for ModelMonitorPrimitive.

All tests are self-contained with no external dependencies.
Time-sensitive tests use unittest.mock.patch to control ``time.time``.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.llm.model_monitor import (
    ModelMonitorPrimitive,
    ModelStats,
    MonitorRequest,
    MonitorResponse,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="test-model-monitor")


def _monitor(**kwargs) -> ModelMonitorPrimitive:
    return ModelMonitorPrimitive(**kwargs)


# ── ModelStats unit tests ─────────────────────────────────────────────────────


class TestModelStatsProperties:
    def test_success_rate_no_requests(self) -> None:
        """Arrange: fresh stats → success_rate defaults to 1.0."""
        stats = ModelStats(model_id="gpt-4o", provider="openai")
        assert stats.success_rate == 1.0

    def test_avg_latency_no_successes(self) -> None:
        stats = ModelStats(model_id="gpt-4o", provider="openai")
        assert stats.avg_latency_ms == 0.0

    def test_tokens_per_second_zero_latency(self) -> None:
        stats = ModelStats(model_id="gpt-4o", provider="openai")
        assert stats.tokens_per_second == 0.0

    def test_tokens_per_second_computed(self) -> None:
        """Arrange: 100 tokens over 500 ms → 200 tok/s."""
        stats = ModelStats(
            model_id="m",
            provider="p",
            success_count=1,
            total_latency_ms=500.0,
            total_tokens=100,
        )
        assert stats.tokens_per_second == pytest.approx(200.0)

    def test_success_rate_computed(self) -> None:
        """Arrange: 2 successes + 1 failure → success_rate ≈ 0.666."""
        stats = ModelStats(
            model_id="m",
            provider="p",
            request_count=3,
            success_count=2,
            error_count=1,
        )
        assert stats.success_rate == pytest.approx(2 / 3)


# ── ModelMonitorPrimitive — record action ─────────────────────────────────────


class TestRecordAction:
    @pytest.mark.asyncio
    async def test_record_success_tracks_stats(self) -> None:
        """Arrange: fresh monitor → Act: record success → Assert: counters."""
        monitor = _monitor()
        ctx = _ctx()
        req = MonitorRequest(
            action="record",
            model_id="gpt-4o",
            provider="openai",
            success=True,
            latency_ms=250.0,
            token_count=80,
        )
        resp = await monitor.execute(req, ctx)

        assert isinstance(resp, MonitorResponse)
        assert resp.action == "record"
        assert resp.stats is not None
        assert resp.stats.request_count == 1
        assert resp.stats.success_count == 1
        assert resp.stats.error_count == 0
        assert resp.stats.avg_latency_ms == pytest.approx(250.0)
        assert resp.stats.total_tokens == 80

    @pytest.mark.asyncio
    async def test_record_failure_tracks_stats(self) -> None:
        """Arrange: fresh monitor → Act: record failure → Assert: error tracked."""
        monitor = _monitor()
        ctx = _ctx()
        req = MonitorRequest(
            action="record",
            model_id="gpt-4o",
            provider="openai",
            success=False,
            error_message="rate_limit_exceeded",
        )
        resp = await monitor.execute(req, ctx)

        assert resp.stats is not None
        assert resp.stats.request_count == 1
        assert resp.stats.success_count == 0
        assert resp.stats.error_count == 1
        assert resp.stats.last_error == "rate_limit_exceeded"

    @pytest.mark.asyncio
    async def test_success_rate_computed(self) -> None:
        """Arrange: 2 successes + 1 failure → success_rate ≈ 0.666."""
        monitor = _monitor()
        ctx = _ctx()

        for _ in range(2):
            await monitor.execute(
                MonitorRequest(
                    action="record",
                    model_id="m",
                    provider="p",
                    success=True,
                    latency_ms=100.0,
                ),
                ctx,
            )
        await monitor.execute(
            MonitorRequest(action="record", model_id="m", provider="p", success=False),
            ctx,
        )

        resp = await monitor.execute(
            MonitorRequest(action="get_stats", model_id="m", provider="p"), ctx
        )
        assert resp.stats is not None
        assert resp.stats.success_rate == pytest.approx(2 / 3)

    @pytest.mark.asyncio
    async def test_tokens_per_second_via_execute(self) -> None:
        """Arrange: 200 tokens over 1000 ms → 200 tok/s."""
        monitor = _monitor()
        ctx = _ctx()
        await monitor.execute(
            MonitorRequest(
                action="record",
                model_id="m",
                provider="p",
                success=True,
                latency_ms=1000.0,
                token_count=200,
            ),
            ctx,
        )
        resp = await monitor.execute(
            MonitorRequest(action="get_stats", model_id="m", provider="p"), ctx
        )
        assert resp.stats is not None
        assert resp.stats.tokens_per_second == pytest.approx(200.0)


# ── Health tracking ───────────────────────────────────────────────────────────


class TestHealthTracking:
    @pytest.mark.asyncio
    async def test_new_model_starts_healthy(self) -> None:
        """A model with no recorded failures is healthy by default."""
        monitor = _monitor()
        ctx = _ctx()
        resp = await monitor.execute(
            MonitorRequest(action="is_healthy", model_id="new-model", provider="openai"),
            ctx,
        )
        assert resp.healthy is True
        assert resp.failure_window_expires_at is None

    @pytest.mark.asyncio
    async def test_unhealthy_after_threshold(self) -> None:
        """Enough failures push success_rate below threshold → unhealthy."""
        monitor = _monitor(unhealthy_threshold=0.5, failure_window_seconds=300.0)
        ctx = _ctx()

        # 0 successes / 2 requests = 0.0 < 0.5
        for _ in range(2):
            await monitor.execute(
                MonitorRequest(action="record", model_id="m", provider="p", success=False),
                ctx,
            )

        resp = await monitor.execute(
            MonitorRequest(action="is_healthy", model_id="m", provider="p"), ctx
        )
        assert resp.healthy is False
        assert resp.failure_window_expires_at is not None

    @pytest.mark.asyncio
    async def test_healthy_after_window_expires(self) -> None:
        """Mock time past the failure window expiry → model becomes healthy again."""
        monitor = _monitor(unhealthy_threshold=0.5, failure_window_seconds=300.0)
        ctx = _ctx()

        base_time = 1_000_000.0

        with patch("time.time", return_value=base_time):
            for _ in range(2):
                await monitor.execute(
                    MonitorRequest(action="record", model_id="m", provider="p", success=False),
                    ctx,
                )

        # Advance time past the window
        future_time = base_time + 301.0
        with patch("time.time", return_value=future_time):
            resp = await monitor.execute(
                MonitorRequest(action="is_healthy", model_id="m", provider="p"), ctx
            )

        assert resp.healthy is True
        assert resp.failure_window_expires_at is None

    @pytest.mark.asyncio
    async def test_unhealthy_returns_expiry_timestamp(self) -> None:
        """failure_window_expires_at is set when model is unhealthy."""
        monitor = _monitor(unhealthy_threshold=0.5, failure_window_seconds=300.0)
        ctx = _ctx()

        base_time = 2_000_000.0
        with patch("time.time", return_value=base_time):
            for _ in range(2):
                await monitor.execute(
                    MonitorRequest(action="record", model_id="m", provider="p", success=False),
                    ctx,
                )
            resp = await monitor.execute(
                MonitorRequest(action="is_healthy", model_id="m", provider="p"), ctx
            )

        assert resp.healthy is False
        assert resp.failure_window_expires_at == pytest.approx(base_time + 300.0)


# ── Reset action ──────────────────────────────────────────────────────────────


class TestResetAction:
    @pytest.mark.asyncio
    async def test_reset_single_model(self) -> None:
        """Reset one model; the other model's stats remain intact."""
        monitor = _monitor()
        ctx = _ctx()

        await monitor.execute(
            MonitorRequest(
                action="record", model_id="m1", provider="p", success=True, latency_ms=100.0
            ),
            ctx,
        )
        await monitor.execute(
            MonitorRequest(
                action="record", model_id="m2", provider="p", success=True, latency_ms=200.0
            ),
            ctx,
        )

        # Reset only m1
        await monitor.execute(MonitorRequest(action="reset", model_id="m1", provider="p"), ctx)

        resp_m1 = await monitor.execute(
            MonitorRequest(action="get_stats", model_id="m1", provider="p"), ctx
        )
        resp_m2 = await monitor.execute(
            MonitorRequest(action="get_stats", model_id="m2", provider="p"), ctx
        )

        assert resp_m1.stats is None  # m1 cleared
        assert resp_m2.stats is not None  # m2 intact
        assert resp_m2.stats.request_count == 1

    @pytest.mark.asyncio
    async def test_reset_all(self) -> None:
        """Reset with model_id='' clears all tracked models."""
        monitor = _monitor()
        ctx = _ctx()

        for model in ("m1", "m2", "m3"):
            await monitor.execute(
                MonitorRequest(
                    action="record",
                    model_id=model,
                    provider="p",
                    success=True,
                    latency_ms=50.0,
                ),
                ctx,
            )

        await monitor.execute(MonitorRequest(action="reset", model_id="", provider=""), ctx)

        resp = await monitor.execute(MonitorRequest(action="get_all"), ctx)
        assert resp.all_stats == {}


# ── get_all action ────────────────────────────────────────────────────────────


class TestGetAllAction:
    @pytest.mark.asyncio
    async def test_get_all_returns_all_models(self) -> None:
        """Track 2 models → get_all returns both entries."""
        monitor = _monitor()
        ctx = _ctx()

        await monitor.execute(
            MonitorRequest(
                action="record",
                model_id="gpt-4o",
                provider="openai",
                success=True,
                latency_ms=300.0,
            ),
            ctx,
        )
        await monitor.execute(
            MonitorRequest(
                action="record",
                model_id="llama3",
                provider="ollama",
                success=True,
                latency_ms=150.0,
            ),
            ctx,
        )

        resp = await monitor.execute(MonitorRequest(action="get_all"), ctx)
        assert len(resp.all_stats) == 2
        assert "openai:gpt-4o" in resp.all_stats
        assert "ollama:llama3" in resp.all_stats

    @pytest.mark.asyncio
    async def test_get_all_empty_on_fresh_monitor(self) -> None:
        monitor = _monitor()
        ctx = _ctx()
        resp = await monitor.execute(MonitorRequest(action="get_all"), ctx)
        assert resp.all_stats == {}


# ── Convenience methods ───────────────────────────────────────────────────────


class TestConvenienceMethods:
    def test_record_success_updates_stats(self) -> None:
        """record_success() is synchronous and directly updates stats."""
        monitor = _monitor()
        monitor.record_success("gpt-4o", "openai", latency_ms=400.0, token_count=120)

        stats = monitor._stats["openai:gpt-4o"]
        assert stats.request_count == 1
        assert stats.success_count == 1
        assert stats.total_latency_ms == 400.0
        assert stats.total_tokens == 120

    def test_record_failure_updates_stats(self) -> None:
        """record_failure() updates error counters."""
        monitor = _monitor()
        monitor.record_failure("gpt-4o", "openai", error="timeout")

        stats = monitor._stats["openai:gpt-4o"]
        assert stats.request_count == 1
        assert stats.error_count == 1
        assert stats.last_error == "timeout"

    def test_is_healthy_sync_new_model(self) -> None:
        """A model with no stats is healthy."""
        monitor = _monitor()
        assert monitor.is_healthy_sync("gpt-4o", "openai") is True

    def test_is_healthy_sync_unhealthy(self) -> None:
        """After enough failures, is_healthy_sync returns False."""
        monitor = _monitor(unhealthy_threshold=0.5, failure_window_seconds=300.0)
        monitor.record_failure("m", "p", error="err")
        monitor.record_failure("m", "p", error="err")

        assert monitor.is_healthy_sync("m", "p") is False

    def test_is_healthy_sync_after_window(self) -> None:
        """After window expiry, is_healthy_sync returns True and clears entry."""
        monitor = _monitor(unhealthy_threshold=0.5, failure_window_seconds=300.0)
        base = 3_000_000.0

        with patch("time.time", return_value=base):
            monitor.record_failure("m", "p", error="e")
            monitor.record_failure("m", "p", error="e")

        with patch("time.time", return_value=base + 301.0):
            result = monitor.is_healthy_sync("m", "p")

        assert result is True
        # Expired entry should be cleaned up
        assert "p:m" not in monitor._unhealthy_until

    def test_convenience_methods_integrated(self) -> None:
        """record_success / record_failure / is_healthy_sync work together."""
        monitor = _monitor(unhealthy_threshold=0.5, failure_window_seconds=60.0)
        # 1 success + 2 failures → success_rate = 1/3 < 0.5 → unhealthy
        monitor.record_success("m", "p", latency_ms=100.0)
        monitor.record_failure("m", "p", error="err1")
        monitor.record_failure("m", "p", error="err2")

        assert monitor.is_healthy_sync("m", "p") is False
        stats = monitor._stats["p:m"]
        assert stats.request_count == 3
        assert stats.success_rate == pytest.approx(1 / 3)


# ── Error handling ────────────────────────────────────────────────────────────


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_invalid_action_raises_value_error(self) -> None:
        """An unknown action raises ValueError with a helpful message."""
        monitor = _monitor()
        ctx = _ctx()
        with pytest.raises(ValueError, match="Unknown action"):
            await monitor.execute(MonitorRequest(action="bogus"), ctx)

    @pytest.mark.asyncio
    async def test_invalid_action_message_includes_valid_actions(self) -> None:
        monitor = _monitor()
        ctx = _ctx()
        with pytest.raises(ValueError, match="record"):
            await monitor.execute(MonitorRequest(action="INVALID"), ctx)
