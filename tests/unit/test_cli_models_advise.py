"""Unit tests for `tta models advise` CLI command.

Covers:
- :func:`infer_task_type` keyword inference
- :func:`_cmd_advise` with positional ``task_description``
- :func:`_cmd_advise` with explicit ``--task-type`` (backward compat)
- :func:`_cmd_advise` with no arguments (defaults to ``general``)
- Error path when advisor raises ``ValueError``
"""

from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from ttadev.cli.models import _cmd_advise, infer_task_type

# The advisor singleton is imported inside _cmd_advise; patch at its definition site.
_ADVISOR_RECOMMEND = "ttadev.primitives.llm.model_advisor.advisor.advisor.recommend_tier"

# ---------------------------------------------------------------------------
# infer_task_type
# ---------------------------------------------------------------------------


class TestInferTaskType:
    """Tests for :func:`infer_task_type`."""

    @pytest.mark.parametrize(
        "description, expected",
        [
            ("I want to build a chatbot", "chat"),
            ("help me debug my Python code", "coding"),
            ("write a script to automate deployment", "coding"),
            ("solve this differential equation", "math"),
            ("analyse the logical argument", "reasoning"),
            ("use function calling to orchestrate tools", "function_calling"),
            ("process images and photos from the camera", "vision"),
            ("summarize this document", "general"),
            ("", "general"),
            ("random gibberish xyzzy foobar", "general"),
        ],
    )
    def test_keyword_inference(self, description: str, expected: str) -> None:
        """Infer task type from a variety of natural-language descriptions."""
        result = infer_task_type(description)
        assert result == expected, (
            f"infer_task_type({description!r}) -> {result!r}, expected {expected!r}"
        )

    def test_returns_string(self) -> None:
        """Return type is always a plain str."""
        assert isinstance(infer_task_type("build an api"), str)

    def test_case_insensitive(self) -> None:
        """Inference is case-insensitive."""
        assert infer_task_type("I LOVE CODING") == infer_task_type("i love coding")


# ---------------------------------------------------------------------------
# _cmd_advise helpers
# ---------------------------------------------------------------------------


def _make_namespace(**kwargs) -> argparse.Namespace:
    """Build a minimal :class:`argparse.Namespace` for ``advise``."""
    defaults = {
        "task_description": None,
        "task_type": None,
        "threshold": 7.0,
        "complexity": "moderate",
        "monthly_calls": 100,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _fake_rec() -> MagicMock:
    """Return a fake :class:`TierRecommendation`."""
    rec = MagicMock()
    rec.recommended_tier = "groq"
    rec.primary_model = "groq/llama-3.3-70b-versatile"
    rec.quality_score = 8.5
    rec.cost_usd_per_month = 0.0
    rec.rationale = "Fast and free."
    rec.fallback_models = ["ollama/llama3.2"]
    return rec


# ---------------------------------------------------------------------------
# _cmd_advise
# ---------------------------------------------------------------------------


class TestCmdAdvise:
    """Tests for :func:`_cmd_advise`."""

    def test_positional_description_infers_task_type(self, capsys: pytest.CaptureFixture) -> None:
        """Free-text description infers task type and shows it in output."""
        args = _make_namespace(task_description="I want to build a chatbot")

        with patch(_ADVISOR_RECOMMEND, return_value=_fake_rec()) as mock_rec:
            rc = _cmd_advise(args)

        assert rc == 0
        mock_rec.assert_called_once_with(
            task_type="chat",
            quality_threshold=7.0,
            complexity="moderate",
            monthly_calls=100,
        )
        out = capsys.readouterr().out
        assert "chat" in out
        assert "I want to build a chatbot" in out

    def test_explicit_task_type_takes_priority(self, capsys: pytest.CaptureFixture) -> None:
        """--task-type overrides any positional description."""
        args = _make_namespace(
            task_description="I want to build a chatbot",
            task_type="coding",
        )

        with patch(_ADVISOR_RECOMMEND, return_value=_fake_rec()) as mock_rec:
            rc = _cmd_advise(args)

        assert rc == 0
        mock_rec.assert_called_once_with(
            task_type="coding",
            quality_threshold=7.0,
            complexity="moderate",
            monthly_calls=100,
        )
        out = capsys.readouterr().out
        assert "coding" in out

    def test_no_args_defaults_to_general(self, capsys: pytest.CaptureFixture) -> None:
        """With no description and no --task-type, defaults to 'general'."""
        args = _make_namespace()

        with patch(_ADVISOR_RECOMMEND, return_value=_fake_rec()) as mock_rec:
            rc = _cmd_advise(args)

        assert rc == 0
        mock_rec.assert_called_once_with(
            task_type="general",
            quality_threshold=7.0,
            complexity="moderate",
            monthly_calls=100,
        )
        out = capsys.readouterr().out
        assert "general" in out

    def test_explicit_task_type_no_description(self, capsys: pytest.CaptureFixture) -> None:
        """--task-type alone (backward-compat) works without description."""
        args = _make_namespace(task_type="reasoning")

        with patch(_ADVISOR_RECOMMEND, return_value=_fake_rec()) as mock_rec:
            rc = _cmd_advise(args)

        assert rc == 0
        mock_rec.assert_called_once_with(
            task_type="reasoning",
            quality_threshold=7.0,
            complexity="moderate",
            monthly_calls=100,
        )

    def test_advisor_value_error_returns_1(self, capsys: pytest.CaptureFixture) -> None:
        """ValueError from advisor yields exit code 1 and error message."""
        args = _make_namespace(task_type="coding")

        with patch(_ADVISOR_RECOMMEND, side_effect=ValueError("unknown task type")):
            rc = _cmd_advise(args)

        assert rc == 1
        err = capsys.readouterr().err
        assert "unknown task type" in err

    def test_custom_threshold_and_complexity(self, capsys: pytest.CaptureFixture) -> None:
        """Custom threshold and complexity are forwarded correctly."""
        args = _make_namespace(
            task_type="math", threshold=9.0, complexity="complex", monthly_calls=500
        )

        with patch(_ADVISOR_RECOMMEND, return_value=_fake_rec()) as mock_rec:
            rc = _cmd_advise(args)

        assert rc == 0
        mock_rec.assert_called_once_with(
            task_type="math",
            quality_threshold=9.0,
            complexity="complex",
            monthly_calls=500,
        )

    def test_output_contains_key_fields(self, capsys: pytest.CaptureFixture) -> None:
        """Output includes tier, model, score, cost, rationale, fallbacks."""
        args = _make_namespace(task_type="coding")
        rec = _fake_rec()
        rec.fallback_models = ["ollama/llama3.2", "groq/mixtral"]

        with patch(_ADVISOR_RECOMMEND, return_value=rec):
            rc = _cmd_advise(args)

        assert rc == 0
        out = capsys.readouterr().out
        assert "groq" in out  # tier
        assert "groq/llama-3.3-70b-versatile" in out  # model
        assert "8.5" in out  # score
        assert "Fast and free." in out  # rationale
        assert "ollama/llama3.2" in out  # fallback
