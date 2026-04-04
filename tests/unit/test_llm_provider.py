"""Tests for get_llm_client() provider helper — Task T3."""

import subprocess
from unittest.mock import patch

import pytest

from ttadev.workflows.llm_provider import LLMClientConfig, get_default_ollama_model, get_llm_client


class TestGetLlmClient:
    def test_returns_openrouter_when_key_present(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")  # pragma: allowlist secret
        monkeypatch.setenv("HINDSIGHT_LLM_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)
        cfg = get_llm_client()
        assert "openrouter.ai" in cfg.base_url
        assert cfg.api_key == "sk-or-test-key"  # pragma: allowlist secret
        assert cfg.model == "nvidia/nemotron-3-super-120b-a12b:free"
        assert cfg.provider == "openrouter"

    def test_falls_back_to_ollama_when_key_absent(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:7b")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)
        cfg = get_llm_client()
        assert "11434" in cfg.base_url
        assert cfg.model == "qwen2.5:7b"
        assert cfg.provider == "ollama"

    def test_ollama_env_override_respected(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")  # pragma: allowlist secret
        monkeypatch.setenv("LLM_FORCE_PROVIDER", "ollama")
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        monkeypatch.setenv("OLLAMA_MODEL", "phi3.5:mini")
        cfg = get_llm_client()
        assert cfg.provider == "ollama"
        assert cfg.model == "phi3.5:mini"

    def test_returns_llm_client_config(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")  # pragma: allowlist secret
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)
        cfg = get_llm_client()
        assert isinstance(cfg, LLMClientConfig)
        assert cfg.base_url
        assert cfg.model
        assert cfg.api_key

    def test_default_openrouter_model_fallback(self, monkeypatch: pytest.MonkeyPatch):
        """When HINDSIGHT_LLM_MODEL not set, uses built-in default."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")  # pragma: allowlist secret
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)
        monkeypatch.delenv("HINDSIGHT_LLM_MODEL", raising=False)
        cfg = get_llm_client()
        assert cfg.model  # some non-empty default
        assert cfg.provider == "openrouter"


class TestGetDefaultOllamaModel:
    """Tests for get_default_ollama_model() auto-detection logic."""

    def test_env_var_wins_over_everything(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """OLLAMA_MODEL env var is always returned first, no subprocess called."""
        monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")
        with patch("subprocess.run") as mock_run:
            result = get_default_ollama_model()
        assert result == "llama3.2:3b"
        mock_run.assert_not_called()

    def test_auto_detects_first_model_from_ollama_list(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When OLLAMA_MODEL is unset, first model from `ollama list` is returned."""
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        fake_output = (
            "NAME                ID              SIZE    MODIFIED\n"
            "phi4-mini:latest    abc123def456    2.5 GB  2 hours ago\n"
            "gemma3:4b           def456abc123    3.1 GB  1 day ago\n"
        )
        mock_result = subprocess.CompletedProcess(
            args=["ollama", "list"], returncode=0, stdout=fake_output, stderr=""
        )
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = get_default_ollama_model()
        assert result == "phi4-mini:latest"
        mock_run.assert_called_once_with(
            ["ollama", "list"], capture_output=True, text=True, timeout=5
        )

    def test_falls_back_when_ollama_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FileNotFoundError (ollama not on PATH) → returns ultimate fallback."""
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = get_default_ollama_model()
        assert result == "gemma3:4b"

    def test_falls_back_when_ollama_times_out(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """TimeoutExpired → returns ultimate fallback without raising."""
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["ollama", "list"], timeout=5),
        ):
            result = get_default_ollama_model()
        assert result == "gemma3:4b"

    def test_falls_back_when_ollama_returns_nonzero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Non-zero return code (e.g. daemon not running) → ultimate fallback."""
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        mock_result = subprocess.CompletedProcess(
            args=["ollama", "list"], returncode=1, stdout="", stderr="connection refused"
        )
        with patch("subprocess.run", return_value=mock_result):
            result = get_default_ollama_model()
        assert result == "gemma3:4b"

    def test_falls_back_when_ollama_list_is_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty model list (header only) → ultimate fallback."""
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        fake_output = "NAME    ID    SIZE    MODIFIED\n"
        mock_result = subprocess.CompletedProcess(
            args=["ollama", "list"], returncode=0, stdout=fake_output, stderr=""
        )
        with patch("subprocess.run", return_value=mock_result):
            result = get_default_ollama_model()
        assert result == "gemma3:4b"

    def test_logs_debug_on_auto_detect(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A debug log message is emitted when a model is auto-detected."""
        import logging

        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        fake_output = (
            "NAME                ID              SIZE    MODIFIED\n"
            "gemma3:4b           abc123def456    3.1 GB  1 day ago\n"
        )
        mock_result = subprocess.CompletedProcess(
            args=["ollama", "list"], returncode=0, stdout=fake_output, stderr=""
        )
        with patch("subprocess.run", return_value=mock_result):
            with caplog.at_level(logging.DEBUG, logger="ttadev.workflows.llm_provider"):
                result = get_default_ollama_model()
        assert result == "gemma3:4b"
        assert any("Auto-detected ollama model" in r.message for r in caplog.records)

    def test_falls_back_on_oserror(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Generic OSError (e.g. permission denied) → ultimate fallback."""
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        with patch("subprocess.run", side_effect=OSError("permission denied")):
            result = get_default_ollama_model()
        assert result == "gemma3:4b"
