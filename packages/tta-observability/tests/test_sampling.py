"""Tests for sampling strategies."""

import pytest

from observability_integration.sampling import (
    AdaptiveSampler,
    CompositeSampler,
    ProbabilisticSampler,
    SamplingDecision,
    TailBasedSampler,
)


class TestProbabilisticSampler:
    """Tests for ProbabilisticSampler."""

    def test_sample_rate_validation(self):
        """Test sample rate must be 0.0-1.0."""
        with pytest.raises(ValueError, match="sample_rate must be 0.0-1.0"):
            ProbabilisticSampler(sample_rate=1.5)

        with pytest.raises(ValueError, match="sample_rate must be 0.0-1.0"):
            ProbabilisticSampler(sample_rate=-0.1)

    def test_consistent_sampling(self):
        """Test same trace_id always gets same decision."""
        sampler = ProbabilisticSampler(sample_rate=0.5)
        trace_id = "test-trace-123"

        # Same trace_id should always get same decision
        first = sampler.should_sample(trace_id)
        for _ in range(10):
            assert sampler.should_sample(trace_id) == first

    def test_sample_rate_accuracy(self):
        """Test sampling rate is approximately correct."""
        sampler = ProbabilisticSampler(sample_rate=0.3)

        sampled = 0
        total = 10000
        for i in range(total):
            if sampler.should_sample(f"trace-{i}") == SamplingDecision.SAMPLE:
                sampled += 1

        # Should be within 5% of target (30% ± 5%)
        actual_rate = sampled / total
        assert 0.25 <= actual_rate <= 0.35

    def test_zero_rate_never_samples(self):
        """Test 0.0 rate never samples."""
        sampler = ProbabilisticSampler(sample_rate=0.0)

        for i in range(100):
            assert sampler.should_sample(f"trace-{i}") == SamplingDecision.DROP

    def test_one_rate_always_samples(self):
        """Test 1.0 rate always samples."""
        sampler = ProbabilisticSampler(sample_rate=1.0)

        for i in range(100):
            assert sampler.should_sample(f"trace-{i}") == SamplingDecision.SAMPLE


class TestTailBasedSampler:
    """Tests for TailBasedSampler."""

    def test_always_sample_errors(self):
        """Test errors are always sampled."""
        sampler = TailBasedSampler(always_sample_errors=True)

        decision = sampler.should_sample("trace-1", {"has_error": True})
        assert decision == SamplingDecision.SAMPLE

    def test_skip_errors_when_disabled(self):
        """Test errors not sampled when disabled."""
        sampler = TailBasedSampler(always_sample_errors=False)

        decision = sampler.should_sample("trace-1", {"has_error": True})
        assert decision == SamplingDecision.DROP

    def test_always_sample_slow_traces(self):
        """Test slow traces are always sampled."""
        sampler = TailBasedSampler(always_sample_slow=True, slow_threshold_ms=1000.0)

        decision = sampler.should_sample("trace-1", {"duration_ms": 1500.0})
        assert decision == SamplingDecision.SAMPLE

    def test_skip_fast_traces(self):
        """Test fast traces are not sampled."""
        sampler = TailBasedSampler(always_sample_slow=True, slow_threshold_ms=1000.0)

        decision = sampler.should_sample("trace-1", {"duration_ms": 500.0})
        assert decision == SamplingDecision.DROP

    def test_configurable_threshold(self):
        """Test slow threshold is configurable."""
        sampler = TailBasedSampler(slow_threshold_ms=500.0)

        # Just below threshold
        decision = sampler.should_sample("trace-1", {"duration_ms": 499.0})
        assert decision == SamplingDecision.DROP

        # At threshold
        decision = sampler.should_sample("trace-2", {"duration_ms": 500.0})
        assert decision == SamplingDecision.SAMPLE


class TestAdaptiveSampler:
    """Tests for AdaptiveSampler."""

    def test_initial_rate_is_max(self):
        """Test sampler starts at max rate."""
        sampler = AdaptiveSampler(min_rate=0.1, max_rate=0.8)
        assert sampler.current_rate == 0.8

    def test_reduces_rate_on_high_overhead(self):
        """Test rate decreases when overhead is high."""
        sampler = AdaptiveSampler(
            min_rate=0.1, max_rate=1.0, target_overhead=0.02, adjustment_interval=0.0
        )
        initial_rate = sampler.current_rate

        # Report high overhead
        sampler.should_sample("trace-1", {"current_overhead": 0.05})

        assert sampler.current_rate < initial_rate
        assert sampler.current_rate >= 0.1  # Never below min

    def test_increases_rate_on_low_overhead(self):
        """Test rate increases when overhead is low."""
        sampler = AdaptiveSampler(
            min_rate=0.1, max_rate=1.0, target_overhead=0.02, adjustment_interval=0.0
        )
        sampler.current_rate = 0.5  # Start in middle

        # Report low overhead
        sampler.should_sample("trace-1", {"current_overhead": 0.01})

        assert sampler.current_rate > 0.5
        assert sampler.current_rate <= 1.0  # Never above max

    def test_rate_stays_within_bounds(self):
        """Test rate never goes below min or above max."""
        sampler = AdaptiveSampler(
            min_rate=0.1, max_rate=0.8, target_overhead=0.02, adjustment_interval=0.0
        )

        # Try to push below min
        for _ in range(100):
            sampler.should_sample("trace-1", {"current_overhead": 1.0})

        assert sampler.current_rate >= 0.1

        # Try to push above max
        for _ in range(100):
            sampler.should_sample("trace-1", {"current_overhead": 0.0})

        assert sampler.current_rate <= 0.8

    def test_consistent_sampling_with_adaptive_rate(self):
        """Test same trace_id gets same decision (within adjustment interval)."""
        sampler = AdaptiveSampler()
        trace_id = "test-trace-456"

        first = sampler.should_sample(trace_id)
        # Within adjustment interval, same trace should be consistent
        for _ in range(10):
            assert sampler.should_sample(trace_id) == first


class TestCompositeSampler:
    """Tests for CompositeSampler."""

    def test_samples_if_any_strategy_samples(self):
        """Test composite samples if ANY strategy says sample."""
        # Create strategies that will disagree
        always_drop = ProbabilisticSampler(sample_rate=0.0)
        always_sample = ProbabilisticSampler(sample_rate=1.0)

        composite = CompositeSampler(strategies=[always_drop, always_sample])

        # Should sample because second strategy says sample
        decision = composite.should_sample("trace-1")
        assert decision == SamplingDecision.SAMPLE

    def test_drops_if_all_strategies_drop(self):
        """Test composite drops if ALL strategies say drop."""
        drop1 = ProbabilisticSampler(sample_rate=0.0)
        drop2 = ProbabilisticSampler(sample_rate=0.0)

        composite = CompositeSampler(strategies=[drop1, drop2])

        decision = composite.should_sample("trace-1")
        assert decision == SamplingDecision.DROP

    def test_combines_probabilistic_and_tail_based(self):
        """Test composite can combine different strategy types."""
        # Low probabilistic rate
        probabilistic = ProbabilisticSampler(sample_rate=0.01)
        # Always sample errors
        tail_based = TailBasedSampler()

        composite = CompositeSampler(strategies=[probabilistic, tail_based])

        # Error should be sampled even if probabilistic says no
        decision = composite.should_sample("unlikely-trace", {"has_error": True})
        assert decision == SamplingDecision.SAMPLE

    def test_empty_strategies_always_drops(self):
        """Test composite with no strategies always drops."""
        composite = CompositeSampler(strategies=[])

        decision = composite.should_sample("trace-1")
        assert decision == SamplingDecision.DROP
