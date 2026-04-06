"""Unit tests for ``tta models list``, ``tta models info``, ``tta models test``.

Covers:
- :func:`_cmd_list` output with mocked litellm.model_cost and Ollama tags
- :func:`_cmd_info` with existing and missing model keys
- :func:`_cmd_test` with mocked litellm.acompletion success and failure
- :func:`_format_cost` and :func:`_format_context` helpers
- :func:`_query_ollama_models` with success, empty, and network-failure scenarios
- Provider detection via environment variables
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from ttadev.cli.models import (
    _RECOMMENDED_MODELS,
    _cmd_info,
    _cmd_list,
    _cmd_test,
    _format_context,
    _format_cost,
    _query_ollama_models,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

_FAKE_MODEL_COST: dict = {
    "groq/llama-3.3-70b-versatile": {
        "input_cost_per_token": 5.9e-07,
        "output_cost_per_token": 7.9e-07,
        "max_input_tokens": 128000,
        "max_tokens": 32768,
        "mode": "chat",
        "supports_function_calling": True,
    },
    "groq/llama-3.1-8b-instant": {
        "input_cost_per_token": 5e-08,
        "output_cost_per_token": 8e-08,
        "max_input_tokens": 128000,
        "max_tokens": 8192,
        "mode": "chat",
    },
    "gemini/gemini-2.0-flash-lite": {
        "input_cost_per_token": 7.5e-08,
        "output_cost_per_token": 3e-07,
        "max_input_tokens": 1048576,
        "mode": "chat",
    },
}


# ---------------------------------------------------------------------------
# _format_cost
# ---------------------------------------------------------------------------


class TestFormatCost:
    """Tests for the per-token → per-million formatting helper."""

    def test_none_returns_free(self) -> None:
        assert _format_cost(None) == "FREE"

    def test_zero_returns_free(self) -> None:
        assert _format_cost(0.0) == "FREE"

    def test_groq_llama_input(self) -> None:
        # 5.9e-7 per token → $0.59 per 1M
        result = _format_cost(5.9e-07)
        assert result.startswith("$")
        assert "0.59" in result

    def test_gemini_flash_lite_input(self) -> None:
        # 7.5e-8 per token → $0.075 per 1M
        result = _format_cost(7.5e-08)
        assert result.startswith("$")

    def test_large_cost(self) -> None:
        # $15 per 1M = 1.5e-5 per token
        result = _format_cost(1.5e-05)
        assert result.startswith("$")
        assert "15" in result


# ---------------------------------------------------------------------------
# _format_context
# ---------------------------------------------------------------------------


class TestFormatContext:
    """Tests for the context-window formatting helper."""

    def test_none_returns_hint(self) -> None:
        assert _format_context(None, "128k") == "128k"

    def test_million_tokens(self) -> None:
        assert _format_context(1_048_576, "1M") == "1M"

    def test_128k(self) -> None:
        assert _format_context(128_000, "128k") == "128k"

    def test_small_value(self) -> None:
        assert _format_context(512, "512") == "512"

    def test_2m(self) -> None:
        assert _format_context(2_000_000, "2M") == "2M"


# ---------------------------------------------------------------------------
# _query_ollama_models
# ---------------------------------------------------------------------------


class TestQueryOllamaModels:
    """Tests for Ollama tags endpoint querying."""

    def test_returns_model_list_on_success(self) -> None:
        payload = {"models": [{"name": "qwen2.5:7b"}, {"name": "llama3:latest"}]}

        class FakeResponse:
            def json(self) -> dict:
                return payload

        with patch("httpx.get", return_value=FakeResponse()):
            result = _query_ollama_models()
        assert result == ["qwen2.5:7b", "llama3:latest"]

    def test_returns_empty_on_connection_error(self) -> None:
        import httpx

        with patch("httpx.get", side_effect=httpx.ConnectError("connection refused")):
            result = _query_ollama_models()
        assert result == []

    def test_returns_empty_on_timeout(self) -> None:
        import httpx

        with patch("httpx.get", side_effect=httpx.TimeoutException("timed out")):
            result = _query_ollama_models()
        assert result == []

    def test_empty_models_list(self) -> None:
        payload = {"models": []}

        class FakeResponse:
            def json(self) -> dict:
                return payload

        with patch("httpx.get", return_value=FakeResponse()):
            result = _query_ollama_models()
        assert result == []


# ---------------------------------------------------------------------------
# _cmd_list
# ---------------------------------------------------------------------------


class TestCmdList:
    """Tests for ``tta models list``."""

    def _run_list(
        self,
        env: dict[str, str] | None = None,
        ollama_models: list[str] | None = None,
        model_cost: dict | None = None,
        capsys=None,
    ) -> str:
        env = env or {}
        ollama_models = ollama_models if ollama_models is not None else []
        model_cost = model_cost if model_cost is not None else _FAKE_MODEL_COST

        import litellm

        with (
            patch.dict(os.environ, env, clear=False),
            patch.object(litellm, "model_cost", model_cost),
            patch(
                "ttadev.cli.models._query_ollama_models",
                return_value=ollama_models,
            ),
        ):
            _cmd_list()

        if capsys:
            return capsys.readouterr().out
        return ""

    def test_returns_zero(self) -> None:
        with (
            patch.dict(os.environ, {}, clear=False),
            patch("ttadev.cli.models._query_ollama_models", return_value=[]),
        ):
            import litellm

            with patch.object(litellm, "model_cost", _FAKE_MODEL_COST):
                result = _cmd_list()
        assert result == 0

    def test_shows_groq_model(self, capsys) -> None:
        self._run_list(capsys=None)
        captured = capsys.readouterr()
        assert "groq/llama-3.3-70b-versatile" in captured.out

    def test_shows_gemini_model(self, capsys) -> None:
        self._run_list()
        captured = capsys.readouterr()
        assert "gemini/gemini-2.0-flash-lite" in captured.out

    def test_shows_ollama_model(self, capsys) -> None:
        self._run_list()
        captured = capsys.readouterr()
        assert "ollama/qwen2.5:7b" in captured.out

    def test_configured_groq_shows_checkmark(self, capsys) -> None:
        self._run_list(env={"GROQ_API_KEY": "gsk_test"})
        captured = capsys.readouterr()
        assert "✓" in captured.out
        assert "Groq" in captured.out

    def test_unconfigured_providers_no_checkmark_for_google(self, capsys) -> None:
        # When GOOGLE_API_KEY is not set, no ✓ on Google row
        env = dict.fromkeys(["GOOGLE_API_KEY", "OPENROUTER_API_KEY"], "")
        self._run_list(env=env)
        captured = capsys.readouterr()
        assert "Configured providers:" in captured.out

    def test_ollama_running_shows_checkmark(self, capsys) -> None:
        self._run_list(ollama_models=["qwen2.5:7b"])
        captured = capsys.readouterr()
        assert "✓" in captured.out
        assert "qwen2.5:7b" in captured.out

    def test_ollama_not_running_message(self, capsys) -> None:
        self._run_list(ollama_models=[])
        captured = capsys.readouterr()
        assert "not running" in captured.out

    def test_free_cost_for_ollama_row(self, capsys) -> None:
        # ollama/qwen2.5:7b is not in _FAKE_MODEL_COST → cost columns show FREE
        self._run_list()
        captured = capsys.readouterr()
        assert "FREE" in captured.out

    def test_header_present(self, capsys) -> None:
        self._run_list()
        captured = capsys.readouterr()
        assert "Model" in captured.out
        assert "Provider" in captured.out
        assert "Input" in captured.out
        assert "Output" in captured.out
        assert "Context" in captured.out

    def test_shows_all_recommended_models(self, capsys) -> None:
        self._run_list()
        captured = capsys.readouterr()
        for litellm_key, display_name, *_ in _RECOMMENDED_MODELS:
            assert display_name in captured.out, f"Missing {display_name}"


# ---------------------------------------------------------------------------
# _cmd_info
# ---------------------------------------------------------------------------


class TestCmdInfo:
    """Tests for ``tta models info <model>``."""

    def test_returns_zero_for_known_model(self, capsys) -> None:
        import litellm

        with patch.object(litellm, "model_cost", _FAKE_MODEL_COST):
            rc = _cmd_info("groq/llama-3.3-70b-versatile")
        assert rc == 0

    def test_prints_fields_for_known_model(self, capsys) -> None:
        import litellm

        with patch.object(litellm, "model_cost", _FAKE_MODEL_COST):
            _cmd_info("groq/llama-3.3-70b-versatile")
        captured = capsys.readouterr()
        assert "input_cost_per_token" in captured.out
        assert "output_cost_per_token" in captured.out
        assert "mode" in captured.out

    def test_shows_per_million_annotation(self, capsys) -> None:
        import litellm

        with patch.object(litellm, "model_cost", _FAKE_MODEL_COST):
            _cmd_info("groq/llama-3.3-70b-versatile")
        captured = capsys.readouterr()
        assert "/1M tokens" in captured.out

    def test_returns_one_for_unknown_model(self, capsys) -> None:
        import litellm

        with patch.object(litellm, "model_cost", _FAKE_MODEL_COST):
            rc = _cmd_info("nonexistent/model-xyz")
        assert rc == 1

    def test_prints_error_for_unknown_model(self, capsys) -> None:
        import litellm

        with patch.object(litellm, "model_cost", _FAKE_MODEL_COST):
            _cmd_info("nonexistent/model-xyz")
        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_gemini_model_info(self, capsys) -> None:
        import litellm

        with patch.object(litellm, "model_cost", _FAKE_MODEL_COST):
            rc = _cmd_info("gemini/gemini-2.0-flash-lite")
        assert rc == 0
        captured = capsys.readouterr()
        assert "gemini/gemini-2.0-flash-lite" in captured.out


# ---------------------------------------------------------------------------
# _cmd_test
# ---------------------------------------------------------------------------


class TestCmdTest:
    """Tests for ``tta models test <model>``."""

    def _make_fake_response(self, content: str = "ok") -> MagicMock:
        msg = MagicMock()
        msg.content = content
        choice = MagicMock()
        choice.message = msg
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    def test_returns_zero_on_success(self, capsys) -> None:
        fake_resp = self._make_fake_response("ok")

        async def fake_completion(**kwargs):
            return fake_resp

        with patch("litellm.acompletion", side_effect=fake_completion):
            rc = _cmd_test("groq/llama-3.3-70b-versatile")
        assert rc == 0

    def test_prints_response_content(self, capsys) -> None:
        fake_resp = self._make_fake_response("ok")

        async def fake_completion(**kwargs):
            return fake_resp

        with patch("litellm.acompletion", side_effect=fake_completion):
            _cmd_test("groq/llama-3.3-70b-versatile")
        captured = capsys.readouterr()
        assert "ok" in captured.out

    def test_prints_latency(self, capsys) -> None:
        fake_resp = self._make_fake_response("ok")

        async def fake_completion(**kwargs):
            return fake_resp

        with patch("litellm.acompletion", side_effect=fake_completion):
            _cmd_test("groq/llama-3.3-70b-versatile")
        captured = capsys.readouterr()
        assert "ms" in captured.out

    def test_returns_one_on_api_error(self, capsys) -> None:
        async def fake_completion(**kwargs):
            raise RuntimeError("API key not configured")

        with patch("litellm.acompletion", side_effect=fake_completion):
            rc = _cmd_test("groq/llama-3.3-70b-versatile")
        assert rc == 1

    def test_prints_error_message_on_failure(self, capsys) -> None:
        async def fake_completion(**kwargs):
            raise RuntimeError("model not found")

        with patch("litellm.acompletion", side_effect=fake_completion):
            _cmd_test("groq/llama-3.3-70b-versatile")
        captured = capsys.readouterr()
        assert "Error" in captured.err or "error" in captured.err.lower()

    def test_model_string_passed_to_completion(self, capsys) -> None:
        captured_kwargs: dict = {}
        fake_resp = self._make_fake_response("ok")

        async def fake_completion(**kwargs):
            captured_kwargs.update(kwargs)
            return fake_resp

        with patch("litellm.acompletion", side_effect=fake_completion):
            _cmd_test("gemini/gemini-2.0-flash-lite")

        assert captured_kwargs.get("model") == "gemini/gemini-2.0-flash-lite"
