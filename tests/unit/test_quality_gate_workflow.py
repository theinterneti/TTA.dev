"""Unit tests for ttadev/workflows/quality_gate.py.

36 stmts, target 70%+ coverage.
Tests: score_response, quality_gate_passed, _read_threshold.
"""

from __future__ import annotations

import pytest

from ttadev.workflows.quality_gate import _DEFAULT_THRESHOLD, quality_gate_passed, score_response


class TestScoreResponseEmpty:
    def test_empty_string_returns_zero(self) -> None:
        assert score_response("") == 0.0

    def test_whitespace_only_returns_zero(self) -> None:
        assert score_response("   ") == 0.0

    def test_newline_tab_returns_zero(self) -> None:
        assert score_response("\n\t\r") == 0.0


class TestScoreResponseLength:
    def test_short_under_20_clamped_to_zero(self) -> None:
        # 9 chars: 1.0 - 0.8 (< 20) - 0.3 (< 80) = -0.1 → 0.0
        assert score_response("Hi there!") == 0.0

    def test_len_exactly_20_only_80_penalty(self) -> None:
        # 20 chars: NOT < 20, IS < 80 → -0.3 = 0.7
        assert score_response("a" * 20) == pytest.approx(0.7)

    def test_len_50_short_80_penalty(self) -> None:
        assert score_response("a" * 50) == pytest.approx(0.7)

    def test_len_19_both_penalties_zero(self) -> None:
        assert score_response("a" * 19) == 0.0

    def test_len_80_to_200_no_penalties(self) -> None:
        assert score_response("a" * 100) == pytest.approx(1.0)

    def test_len_201_bonus_clamped_to_1(self) -> None:
        # 1.0 + 0.1 → clamped to 1.0
        assert score_response("a" * 201) == pytest.approx(1.0)

    def test_len_501_double_bonus_clamped_to_1(self) -> None:
        assert score_response("a" * 501) == pytest.approx(1.0)


class TestScoreResponseRefusalPatterns:
    def _padded(self, suffix: str) -> str:
        return "a" * 82 + " " + suffix

    def test_i_cannot_penalty(self) -> None:
        assert score_response(self._padded("I cannot do that.")) < 1.0

    def test_i_am_unable_to_penalty(self) -> None:
        assert score_response(self._padded("I am unable to help.")) < 1.0

    def test_im_unable_to_penalty(self) -> None:
        assert score_response(self._padded("I'm unable to assist.")) < 1.0

    def test_i_dont_have_access_penalty(self) -> None:
        assert score_response(self._padded("I don't have access to that.")) < 1.0

    def test_i_do_not_have_access_penalty(self) -> None:
        assert score_response(self._padded("I do not have access to that.")) < 1.0

    def test_i_cant_help_penalty(self) -> None:
        assert score_response(self._padded("I can't help with this.")) < 1.0

    def test_i_cannot_help_penalty(self) -> None:
        assert score_response(self._padded("I cannot help with this.")) < 1.0

    def test_refusal_case_insensitive(self) -> None:
        assert score_response(self._padded("I CANNOT do that.")) < 1.0

    def test_refusal_penalty_magnitude(self) -> None:
        # exactly 82 chars of 'a' + space + refusal; total > 80, no length penalty
        # 1.0 - 0.6 = 0.4
        response = "a" * 82 + " I cannot do that here."
        assert score_response(response) == pytest.approx(0.4)


class TestScoreResponseAIApologyPatterns:
    def _padded(self, suffix: str) -> str:
        return "a" * 82 + " " + suffix

    def test_as_an_ai_penalty(self) -> None:
        assert score_response(self._padded("As an AI, I can help.")) < 1.0

    def test_as_a_language_model_penalty(self) -> None:
        assert score_response(self._padded("As a language model, I understand.")) < 1.0

    def test_as_an_llm_penalty(self) -> None:
        assert score_response(self._padded("As an LLM, I can say...")) < 1.0

    def test_im_just_an_ai_penalty(self) -> None:
        assert score_response(self._padded("I'm just an AI assistant.")) < 1.0

    def test_i_am_just_an_ai_penalty(self) -> None:
        assert score_response(self._padded("I am just an AI.")) < 1.0

    def test_combined_refusal_and_apology_over_200(self) -> None:
        # > 200 chars → +0.1; refusal → -0.6; apology → -0.4; net = 0.1
        response = "a" * 201 + " As an AI, I cannot help."
        assert score_response(response) == pytest.approx(0.1)


class TestScoreResponseNoAlphabetic:
    def test_numeric_only_applies_penalty(self) -> None:
        response = "1234567890" * 10  # 100 chars, no alpha → -0.5 = 0.5
        assert score_response(response) == pytest.approx(0.5)

    def test_mixed_numeric_alpha_no_penalty(self) -> None:
        response = "abc123" * 20  # 120 chars, has alpha
        assert score_response(response) == pytest.approx(1.0)

    def test_special_chars_only_penalty(self) -> None:
        response = "!@#$%^&*()" * 10  # 100 chars, no alpha
        assert score_response(response) < 1.0


class TestScoreResponseClamping:
    def test_result_never_above_1(self) -> None:
        assert score_response("a" * 1000) <= 1.0

    def test_result_never_below_0(self) -> None:
        assert score_response("12") >= 0.0

    def test_good_long_response_scores_high(self) -> None:
        response = (
            "Here is a complete Python implementation:\n\n"
            "```python\ndef solve(n):\n    return n * 2\n```\n\n"
            "This doubles the input value and handles all integers."
        ) * 3
        assert score_response(response) >= 0.8


class TestQualityGatePassed:
    def test_high_quality_passes(self) -> None:
        assert quality_gate_passed("a" * 100, threshold=0.5) is True

    def test_empty_fails(self) -> None:
        assert quality_gate_passed("", threshold=0.5) is False

    def test_threshold_zero_passes_nonempty(self) -> None:
        assert quality_gate_passed("a" * 100, threshold=0.0) is True

    def test_threshold_one_passes_perfect(self) -> None:
        # score("a" * 100) = 1.0 ≥ 1.0 → True
        assert quality_gate_passed("a" * 100, threshold=1.0) is True

    def test_refusal_fails_default_threshold(self) -> None:
        # score ≈ 0.1 for short refusal; default threshold = 0.5
        assert quality_gate_passed("I cannot help you with that.") is False

    def test_custom_threshold_above_passes(self) -> None:
        assert quality_gate_passed("a" * 50, threshold=0.6) is True  # score=0.7

    def test_custom_threshold_below_fails(self) -> None:
        assert quality_gate_passed("a" * 50, threshold=0.8) is False  # score=0.7

    def test_default_threshold_is_float_in_range(self) -> None:
        assert isinstance(_DEFAULT_THRESHOLD, float)
        assert 0.0 <= _DEFAULT_THRESHOLD <= 1.0


class TestReadThreshold:
    def test_default_05_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("QUALITY_GATE_THRESHOLD", raising=False)
        from ttadev.workflows.quality_gate import _read_threshold

        assert _read_threshold() == 0.5

    def test_env_var_respected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("QUALITY_GATE_THRESHOLD", "0.8")
        from ttadev.workflows.quality_gate import _read_threshold

        assert _read_threshold() == pytest.approx(0.8)

    def test_invalid_env_defaults_to_05(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("QUALITY_GATE_THRESHOLD", "not-a-float")
        from ttadev.workflows.quality_gate import _read_threshold

        assert _read_threshold() == 0.5

    def test_above_1_clamped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("QUALITY_GATE_THRESHOLD", "2.5")
        from ttadev.workflows.quality_gate import _read_threshold

        assert _read_threshold() == 1.0

    def test_below_0_clamped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("QUALITY_GATE_THRESHOLD", "-0.5")
        from ttadev.workflows.quality_gate import _read_threshold

        assert _read_threshold() == 0.0
