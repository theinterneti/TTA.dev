"""Tests for sampling strategies."""

from __future__ import annotations

import pytest

from tta_dev_primitives.observability.sampling import (
    AdaptiveSampler,
    CompositeSampler,
    ProbabilisticSampler,
    SamplingConfig,
    SamplingDecision,
    TailBasedSampler,
)


class TestProbabilisticSampler:
    """Tests for ProbabilisticSampler."""

    def test_zero_rate_always_drops(self) -> None:
        """Test that 0.0 rate always drops."""
        sampler = ProbabilisticSampler(sample_rate=0.0)

        for i in range(100):
            result = sampler.should_sample(f"trace-{i}")
            assert result.decision == SamplingDecision.DROP
            assert result.sample_rate == 0.0

    def test_one_rate_always_samples(self) -> None:
        """Test that 1.0 rate always samples."""
        sampler = ProbabilisticSampler(sample_rate=1.0)

        for i in range(100):
            result = sampler.should_sample(f"trace-{i}")
            assert result.decision == SamplingDecision.SAMPLE
            assert result.sample_rate == 1.0

    def test_consistent_sampling(self) -> None:
        """Test that same trace_id gets same decision."""
        sampler = ProbabilisticSampler(sample_rate=0.5)

        trace_id = "test-trace-123"

        # First decision
        result1 = sampler.should_sample(trace_id)

        # Second decision with same trace_id
        result2 = sampler.should_sample(trace_id)

        # Should be identical
        assert result1.decision == result2.decision
        assert result1.reason == result2.reason

    def test_sampling_rate_accuracy(self) -> None:
        """Test that sampling rate is approximately accurate."""
        sample_rate = 0.3
        sampler = ProbabilisticSampler(sample_rate=sample_rate)

        # Generate many decisions
        samples = 0
        total = 1000

        for i in range(total):
            result = sampler.should_sample(f"trace-{i}")
            if result.decision == SamplingDecision.SAMPLE:
                samples += 1

        # Should be within 5% of expected rate
        actual_rate = samples / total
        assert abs(actual_rate - sample_rate) < 0.05

    def test_none_trace_id_uses_random(self) -> None:
        """Test that None trace_id uses random sampling."""
        sampler = ProbabilisticSampler(sample_rate=0.5)

        # Multiple calls with None should potentially differ
        results = [sampler.should_sample(None) for _ in range(10)]

        # Should have mix of sample and drop (with high probability)
        decisions = [r.decision for r in results]
        assert SamplingDecision.SAMPLE in decisions
        assert SamplingDecision.DROP in decisions

    def test_invalid_rate_raises(self) -> None:
        """Test that invalid rates raise ValueError."""
        with pytest.raises(ValueError, match="Sample rate must be between"):
            ProbabilisticSampler(sample_rate=-0.1)

        with pytest.raises(ValueError, match="Sample rate must be between"):
            ProbabilisticSampler(sample_rate=1.5)


class TestTailBasedSampler:
    """Tests for TailBasedSampler."""

    def test_always_sample_errors(self) -> None:
        """Test that errors are always sampled."""
        sampler = TailBasedSampler(
            always_sample_errors=True,
            always_sample_slow=False,
        )

        result = sampler.should_sample_after_completion(
            has_error=True,
            duration_ms=100.0,
        )

        assert result.decision == SamplingDecision.SAMPLE
        assert result.reason == "tail_error"

    def test_always_sample_slow(self) -> None:
        """Test that slow traces are always sampled."""
        sampler = TailBasedSampler(
            always_sample_errors=False,
            always_sample_slow=True,
            slow_threshold_ms=1000.0,
        )

        result = sampler.should_sample_after_completion(
            has_error=False,
            duration_ms=1500.0,
        )

        assert result.decision == SamplingDecision.SAMPLE
        assert result.reason == "tail_slow"

    def test_drop_normal_traces(self) -> None:
        """Test that normal traces are dropped."""
        sampler = TailBasedSampler(
            always_sample_errors=True,
            always_sample_slow=True,
            slow_threshold_ms=1000.0,
        )

        result = sampler.should_sample_after_completion(
            has_error=False,
            duration_ms=500.0,
        )

        assert result.decision == SamplingDecision.DROP
        assert result.reason == "tail_normal"

    def test_slow_threshold_boundary(self) -> None:
        """Test slow threshold boundary conditions."""
        threshold = 1000.0
        sampler = TailBasedSampler(
            always_sample_slow=True,
            slow_threshold_ms=threshold,
        )

        # Just under threshold - should drop
        result = sampler.should_sample_after_completion(
            has_error=False,
            duration_ms=threshold - 1,
        )
        assert result.decision == SamplingDecision.DROP

        # At threshold - should sample
        result = sampler.should_sample_after_completion(
            has_error=False,
            duration_ms=threshold,
        )
        assert result.decision == SamplingDecision.SAMPLE

    def test_disabled_rules(self) -> None:
        """Test that disabled rules don't trigger sampling."""
        sampler = TailBasedSampler(
            always_sample_errors=False,
            always_sample_slow=False,
        )

        # Error but rule disabled
        result = sampler.should_sample_after_completion(
            has_error=True,
            duration_ms=100.0,
        )
        assert result.decision == SamplingDecision.DROP

        # Slow but rule disabled
        result = sampler.should_sample_after_completion(
            has_error=False,
            duration_ms=2000.0,
        )
        assert result.decision == SamplingDecision.DROP


class TestAdaptiveSampler:
    """Tests for AdaptiveSampler."""

    def test_starts_at_base_rate(self) -> None:
        """Test that sampler starts at base rate."""
        base_rate = 0.2
        sampler = AdaptiveSampler(base_rate=base_rate)

        assert sampler.current_rate == base_rate

    def test_reduces_rate_on_high_overhead(self) -> None:
        """Test that rate reduces when overhead is too high."""
        sampler = AdaptiveSampler(
            base_rate=0.5,
            min_rate=0.01,
            target_overhead=0.02,
            adjustment_interval=0.1,  # Fast adjustment for testing
        )

        # Simulate high overhead for adjustment interval
        import time

        for _ in range(10):
            sampler.should_sample("trace-1", current_overhead=0.05)  # 5% overhead
            time.sleep(0.01)

        # Wait for adjustment
        time.sleep(0.2)

        # Trigger another sample to potentially adjust
        sampler.should_sample("trace-2", current_overhead=0.05)

        # Rate should have decreased
        assert sampler.current_rate < 0.5

    def test_increases_rate_on_low_overhead(self) -> None:
        """Test that rate increases when overhead is low."""
        sampler = AdaptiveSampler(
            base_rate=0.1,
            max_rate=1.0,
            target_overhead=0.02,
            adjustment_interval=0.1,  # Fast adjustment for testing
        )

        # Simulate low overhead
        import time

        for _ in range(10):
            sampler.should_sample("trace-1", current_overhead=0.005)  # 0.5% overhead
            time.sleep(0.01)

        # Wait for adjustment
        time.sleep(0.2)

        # Trigger another sample
        sampler.should_sample("trace-2", current_overhead=0.005)

        # Rate should have increased
        assert sampler.current_rate > 0.1

    def test_respects_min_rate(self) -> None:
        """Test that rate doesn't go below min_rate."""
        min_rate = 0.05
        sampler = AdaptiveSampler(
            base_rate=0.1,
            min_rate=min_rate,
            adjustment_interval=0.1,
        )

        # Try to force rate down with high overhead
        import time

        for _ in range(20):
            sampler.should_sample("trace-1", current_overhead=0.9)
            time.sleep(0.01)

        time.sleep(0.2)
        sampler.should_sample("trace-2", current_overhead=0.9)

        # Should not go below min
        assert sampler.current_rate >= min_rate

    def test_respects_max_rate(self) -> None:
        """Test that rate doesn't exceed max_rate."""
        max_rate = 0.5
        sampler = AdaptiveSampler(
            base_rate=0.1,
            max_rate=max_rate,
            adjustment_interval=0.1,
        )

        # Try to force rate up with low overhead
        import time

        for _ in range(20):
            sampler.should_sample("trace-1", current_overhead=0.001)
            time.sleep(0.01)

        time.sleep(0.2)
        sampler.should_sample("trace-2", current_overhead=0.001)

        # Should not exceed max
        assert sampler.current_rate <= max_rate

    def test_get_stats(self) -> None:
        """Test getting sampler statistics."""
        sampler = AdaptiveSampler(base_rate=0.3)

        # Make some decisions
        for i in range(100):
            sampler.should_sample(f"trace-{i}")

        stats = sampler.get_stats()

        assert stats["current_rate"] == 0.3
        assert stats["total_decisions"] == 100
        assert "actual_sample_rate" in stats
        assert 0.0 <= stats["actual_sample_rate"] <= 1.0


class TestCompositeSampler:
    """Tests for CompositeSampler."""

    def test_head_sampling(self) -> None:
        """Test head-based sampling."""
        config = SamplingConfig(default_rate=0.5)
        sampler = CompositeSampler(config)

        # Head decision should use probabilistic
        result = sampler.should_sample_head("test-trace")

        assert result.decision in (SamplingDecision.SAMPLE, SamplingDecision.DROP)
        assert result.sample_rate == 0.5

    def test_tail_sampling_preserves_head_sample(self) -> None:
        """Test that tail preserves head SAMPLE decision."""
        config = SamplingConfig(
            default_rate=1.0,  # Always sample at head
            always_sample_errors=False,
        )
        sampler = CompositeSampler(config)

        # Head samples
        head_result = sampler.should_sample_head("test-trace")
        assert head_result.decision == SamplingDecision.SAMPLE

        # Tail with normal trace (would normally drop)
        tail_result = sampler.should_sample_tail(
            trace_id="test-trace",
            has_error=False,
            duration_ms=100.0,
            head_decision=head_result,
        )

        # Should preserve head decision
        assert tail_result.decision == SamplingDecision.SAMPLE

    def test_tail_sampling_upgrades_head_drop_on_error(self) -> None:
        """Test that tail upgrades DROP to SAMPLE on error."""
        config = SamplingConfig(
            default_rate=0.0,  # Never sample at head
            always_sample_errors=True,
        )
        sampler = CompositeSampler(config)

        # Head drops
        head_result = sampler.should_sample_head("test-trace")
        assert head_result.decision == SamplingDecision.DROP

        # Tail with error
        tail_result = sampler.should_sample_tail(
            trace_id="test-trace",
            has_error=True,
            duration_ms=100.0,
            head_decision=head_result,
        )

        # Should upgrade to SAMPLE
        assert tail_result.decision == SamplingDecision.SAMPLE
        assert tail_result.reason == "tail_error"

    def test_adaptive_sampling_enabled(self) -> None:
        """Test that adaptive sampling is used when enabled."""
        config = SamplingConfig(
            default_rate=0.1,
            adaptive_enabled=True,
            adaptive_min_rate=0.01,
            adaptive_max_rate=0.5,
        )
        sampler = CompositeSampler(config)

        # Check that adaptive sampler is used
        assert isinstance(sampler.probabilistic, AdaptiveSampler)
        assert sampler.probabilistic.current_rate == 0.1


class TestSamplingConfig:
    """Tests for SamplingConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = SamplingConfig()

        assert config.default_rate == 0.1
        assert config.always_sample_errors is True
        assert config.always_sample_slow is True
        assert config.slow_threshold_ms == 1000.0
        assert config.adaptive_enabled is False

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = SamplingConfig(
            default_rate=0.05,
            always_sample_errors=False,
            slow_threshold_ms=500.0,
            adaptive_enabled=True,
        )

        assert config.default_rate == 0.05
        assert config.always_sample_errors is False
        assert config.slow_threshold_ms == 500.0
        assert config.adaptive_enabled is True

    def test_validation(self) -> None:
        """Test configuration validation."""
        # Valid config
        config = SamplingConfig(default_rate=0.5)
        assert config.default_rate == 0.5

        # Invalid rate should raise
        with pytest.raises(Exception):  # Pydantic validation error
            SamplingConfig(default_rate=1.5)

        with pytest.raises(Exception):
            SamplingConfig(default_rate=-0.1)
