"""Unit tests for quality_gate.py with 100% coverage."""

from __future__ import annotations

import importlib

import pytest

from ttadev.workflows.quality_gate import (
    quality_gate_passed,
    score_response,
)


class TestScoreResponse:
    """Test score_response function."""

    def test_empty_string_returns_zero(self) -> None:
        """Empty string should return 0.0."""
        assert score_response("") == 0.0

    def test_whitespace_only_returns_zero(self) -> None:
        """Whitespace-only string should return 0.0."""
        assert score_response("   \n\t  ") == 0.0

    def test_very_short_scores_low(self) -> None:
        """Very short response (< 20 chars) should score low."""
        assert score_response("Hi") < 0.3

    def test_short_under_80_penalised(self) -> None:
        """Response under 80 chars should be penalised."""
        # "Short answer." is 13 chars, < 20 AND < 80
        # Penalties: -0.8 (< 20) + -0.3 (< 80) = -1.1 from 1.0 = -0.1, clamped to 0.0
        assert score_response("Short answer.") == 0.0

    def test_refusal_pattern_scores_low(self) -> None:
        """Response with refusal pattern should score < 0.5."""
        assert score_response("I cannot help with that request.") < 0.5

    def test_refusal_variant_unable(self) -> None:
        """Response with 'unable' refusal variant should score < 0.5."""
        assert score_response("I'm unable to assist with this.") < 0.5

    def test_refusal_no_access(self) -> None:
        """Response with 'no access' pattern should score < 0.5."""
        assert score_response("I don't have access to that information.") < 0.5

    def test_ai_apology_scores_low(self) -> None:
        """Response with AI apology should score < 0.5."""
        # Contains "As an AI" without refusal keywords, so:
        # 1.0 - 0.4 (AI apology) - 0.3 (len < 80) = 0.3 < 0.5
        assert score_response("As an AI, I acknowledge this requires careful consideration.") < 0.5

    def test_ai_apology_variant(self) -> None:
        """Response with language model apology should score < 0.5."""
        assert score_response("As a language model I must inform you of my limitations.") < 0.5

    def test_no_alpha_content_penalised(self) -> None:
        """Response with no alphabetic content should be penalised."""
        assert score_response("123 456 789") < 0.5

    def test_clean_long_response_passes(self) -> None:
        """Clean response >= 200 chars should score >= 0.5."""
        clean_response = """def hello_world():
    print("Hello, World!")
    return 42

class MyClass:
    def __init__(self):
        self.value = 0

    def method(self):
        return self.value

def another_function(x, y):
    result = x + y
    return result * 2

if __name__ == '__main__':
    value = hello_world()"""
        assert len(clean_response) >= 200
        assert score_response(clean_response) >= 0.5

    def test_very_long_response_scores_higher(self) -> None:
        """Very long (> 500 chars) clean response should score >= 0.6."""
        clean_response = """def fibonacci(n):
    '''Generate Fibonacci sequence up to n terms.'''
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    fib_list = [0, 1]
    for i in range(2, n):
        fib_list.append(fib_list[i-1] + fib_list[i-2])
    return fib_list

class DataProcessor:
    '''Process and validate data from external sources.'''
    def __init__(self, name):
        self.name = name
        self.data = []

    def add_data(self, item):
        self.data.append(item)

    def process(self):
        return [x * 2 for x in self.data]

    def get_summary(self):
        return f'{self.name}: {len(self.data)} items'"""
        assert len(clean_response) > 500
        assert score_response(clean_response) >= 0.6

    def test_score_clamped_to_zero(self) -> None:
        """Score should never go below 0.0."""
        # Multiple penalties: short + refusal + apology + no alpha
        response = "123"  # < 20, < 80, no alpha
        assert score_response(response) >= 0.0

    def test_score_clamped_to_one(self) -> None:
        """Score should never go above 1.0."""
        # Response > 200 chars gets +0.1 bonus, > 500 chars gets another +0.1 bonus
        # = 1.0 + 0.1 + 0.1 = 1.2 before clamping, should be clamped to 1.0
        clean_response = (
            "This is a comprehensive response providing detailed information about the topic. It covers multiple aspects and provides thoughtful analysis. The content is well-structured and clear. "
            + "x" * 400
        )
        assert len(clean_response) > 500
        assert score_response(clean_response) == 1.0

    def test_case_insensitive_refusal(self) -> None:
        """Refusal patterns should match case-insensitively."""
        assert score_response("I CANNOT help you") < 0.5


class TestQualityGatePassed:
    """Test quality_gate_passed function."""

    def test_passes_above_threshold(self) -> None:
        """Long clean response should pass default threshold."""
        clean_response = """This is a good response that provides helpful information
        about the topic at hand. It is well-structured and clear."""
        assert quality_gate_passed(clean_response) is True

    def test_fails_below_threshold(self) -> None:
        """Refusal should fail default threshold."""
        assert quality_gate_passed("I cannot help with that.") is False

    def test_custom_threshold_zero(self) -> None:
        """Everything non-empty should pass with threshold=0.0."""
        assert quality_gate_passed("x", threshold=0.0) is True

    def test_custom_threshold_one(self) -> None:
        """Refusal should fail with threshold=1.0."""
        assert quality_gate_passed("I cannot help you.", threshold=1.0) is False


class TestThresholdFromEnv:
    """Test threshold reading from environment."""

    def test_reads_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Module should read QUALITY_GATE_THRESHOLD from environment."""
        monkeypatch.setenv("QUALITY_GATE_THRESHOLD", "0.3")
        # Reimport the module to trigger _read_threshold()
        import ttadev.workflows.quality_gate as qg_module

        importlib.reload(qg_module)
        assert qg_module._DEFAULT_THRESHOLD == 0.3

    def test_defaults_on_bad_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Module should default to 0.5 on bad QUALITY_GATE_THRESHOLD value."""
        monkeypatch.setenv("QUALITY_GATE_THRESHOLD", "bad")
        import ttadev.workflows.quality_gate as qg_module

        importlib.reload(qg_module)
        assert qg_module._DEFAULT_THRESHOLD == 0.5

    def test_clamps_above_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Module should clamp QUALITY_GATE_THRESHOLD to 1.0 if > 1.0."""
        monkeypatch.setenv("QUALITY_GATE_THRESHOLD", "2.0")
        import ttadev.workflows.quality_gate as qg_module

        importlib.reload(qg_module)
        assert qg_module._DEFAULT_THRESHOLD == 1.0

    def test_clamps_below_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Module should clamp QUALITY_GATE_THRESHOLD to 0.0 if < 0.0."""
        monkeypatch.setenv("QUALITY_GATE_THRESHOLD", "-0.5")
        import ttadev.workflows.quality_gate as qg_module

        importlib.reload(qg_module)
        assert qg_module._DEFAULT_THRESHOLD == 0.0
