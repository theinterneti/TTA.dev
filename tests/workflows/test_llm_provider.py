"""Unit tests for get_llm_provider_chain in llm_provider.py."""

from __future__ import annotations

import pytest

from ttadev.workflows.llm_provider import (
    _PROVIDER_REGISTRY,
    NoLLMProviderError,
    ProviderSpec,
    _config_from_spec,
    _is_provider_error,
    get_llm_client,
    get_llm_provider_chain,
)


class TestProviderRegistry:
    """Tests for the declarative _PROVIDER_REGISTRY."""

    def test_registry_is_nonempty(self) -> None:
        assert len(_PROVIDER_REGISTRY) >= 1

    def test_registry_entries_are_provider_specs(self) -> None:
        for spec in _PROVIDER_REGISTRY:
            assert isinstance(spec, ProviderSpec)

    def test_groq_is_first(self) -> None:
        """Groq must be the highest-priority cloud provider."""
        cloud = [s for s in _PROVIDER_REGISTRY if not s.is_local]
        assert cloud[0].name == "groq"

    def test_ollama_is_local(self) -> None:
        local = [s for s in _PROVIDER_REGISTRY if s.is_local]
        assert any(s.name == "ollama" for s in local)

    def test_all_names_unique(self) -> None:
        names = [s.name for s in _PROVIDER_REGISTRY]
        assert len(names) == len(set(names))


class TestConfigFromSpec:
    """Tests for _config_from_spec()."""

    def test_groq_spec_reads_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "gsk-test")  # pragma: allowlist secret
        groq_spec = next(s for s in _PROVIDER_REGISTRY if s.name == "groq")
        cfg = _config_from_spec(groq_spec)
        assert cfg.provider == "groq"
        assert cfg.api_key == "gsk-test"  # pragma: allowlist secret
        assert "groq.com" in cfg.base_url

    def test_openrouter_spec_reads_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")  # pragma: allowlist secret
        or_spec = next(s for s in _PROVIDER_REGISTRY if s.name == "openrouter")
        cfg = _config_from_spec(or_spec)
        assert cfg.provider == "openrouter"
        assert cfg.api_key == "or-test"  # pragma: allowlist secret

    def test_ollama_spec_uses_name_as_key(self) -> None:
        ollama_spec = next(s for s in _PROVIDER_REGISTRY if s.name == "ollama")
        cfg = _config_from_spec(ollama_spec)
        assert cfg.provider == "ollama"
        assert cfg.api_key == "ollama"  # pragma: allowlist secret


class TestGetLlmProviderChain:
    """Tests for get_llm_provider_chain()."""

    def test_chain_openrouter_then_ollama_when_key_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OPENROUTER_API_KEY set (no GROQ) → chain is [openrouter, ollama]."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-123")
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)

        chain = get_llm_provider_chain()

        assert len(chain) == 2
        assert chain[0].provider == "openrouter"
        assert chain[1].provider == "ollama"
        assert chain[0].api_key == "test-key-123"  # pragma: allowlist secret

    def test_chain_groq_then_openrouter_then_ollama_when_both_keys_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Both GROQ_API_KEY and OPENROUTER_API_KEY set → [groq, openrouter, ollama]."""
        monkeypatch.setenv("GROQ_API_KEY", "gsk-test")  # pragma: allowlist secret
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")  # pragma: allowlist secret
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)

        chain = get_llm_provider_chain()

        assert len(chain) == 3
        assert chain[0].provider == "groq"
        assert chain[1].provider == "openrouter"
        assert chain[2].provider == "ollama"

    def test_chain_groq_then_ollama_when_only_groq_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Only GROQ_API_KEY set → [groq, ollama]."""
        monkeypatch.setenv("GROQ_API_KEY", "gsk-only")  # pragma: allowlist secret
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)

        chain = get_llm_provider_chain()

        assert len(chain) == 2
        assert chain[0].provider == "groq"
        assert chain[1].provider == "ollama"

    def test_chain_ollama_only_when_no_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No cloud keys → chain is [ollama] only."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)

        chain = get_llm_provider_chain()

        assert len(chain) == 1
        assert chain[0].provider == "ollama"

    def test_chain_force_ollama_overrides_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """LLM_FORCE_PROVIDER=ollama → [ollama] even if keys are set."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-123")
        monkeypatch.setenv("GROQ_API_KEY", "gsk-test")  # pragma: allowlist secret
        monkeypatch.setenv("LLM_FORCE_PROVIDER", "ollama")

        chain = get_llm_provider_chain()

        assert len(chain) == 1
        assert chain[0].provider == "ollama"

    def test_chain_force_groq_overrides_other_keys(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """LLM_FORCE_PROVIDER=groq → [groq] only, ignores openrouter."""
        monkeypatch.setenv("GROQ_API_KEY", "gsk-test")  # pragma: allowlist secret
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")  # pragma: allowlist secret
        monkeypatch.setenv("LLM_FORCE_PROVIDER", "groq")

        chain = get_llm_provider_chain()

        assert len(chain) == 1
        assert chain[0].provider == "groq"

    def test_chain_force_unknown_provider_falls_through(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """LLM_FORCE_PROVIDER=nonexistent → warning logged, normal chain returned."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")  # pragma: allowlist secret
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.setenv("LLM_FORCE_PROVIDER", "nonexistent-provider")

        chain = get_llm_provider_chain()

        # Should fall through to normal resolution
        assert chain[0].provider == "openrouter"

    def test_chain_ollama_when_key_is_empty_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty string OPENROUTER_API_KEY falls back to [ollama] (same as unset)."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "")
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)

        chain = get_llm_provider_chain()
        assert len(chain) == 1
        assert chain[0].provider == "ollama"

    def test_get_llm_client_still_works(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """get_llm_client() returns the first item from get_llm_provider_chain()."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-456")
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)

        cfg = get_llm_client()

        assert cfg.provider == "openrouter"
        assert cfg.api_key == "test-key-456"  # pragma: allowlist secret

    def test_chain_uses_hindsight_model_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """HINDSIGHT_LLM_MODEL env var sets the openrouter model."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")  # pragma: allowlist secret
        monkeypatch.setenv("HINDSIGHT_LLM_MODEL", "anthropic/claude-3-haiku:free")
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)

        chain = get_llm_provider_chain()
        assert chain[0].model == "anthropic/claude-3-haiku:free"


class TestNoLLMProviderError:
    """Tests for NoLLMProviderError — issue #287."""

    def test_is_exception(self) -> None:
        """NoLLMProviderError must be a subclass of Exception."""
        assert issubclass(NoLLMProviderError, Exception)

    def test_default_message_contains_groq(self) -> None:
        """Default message mentions Groq as option 1."""
        err = NoLLMProviderError()
        assert "Groq" in str(err)
        assert "GROQ_API_KEY" in str(err)

    def test_default_message_contains_openrouter(self) -> None:
        """Default message mentions OpenRouter as option 2."""
        err = NoLLMProviderError()
        assert "OpenRouter" in str(err)
        assert "OPENROUTER_API_KEY" in str(err)

    def test_default_message_contains_ollama(self) -> None:
        """Default message mentions Ollama as option 3."""
        err = NoLLMProviderError()
        assert "Ollama" in str(err)
        assert "ollama pull" in str(err)

    def test_default_message_references_getting_started(self) -> None:
        """Default message references GETTING_STARTED.md."""
        err = NoLLMProviderError()
        assert "GETTING_STARTED.md" in str(err)

    def test_user_message_matches_str(self) -> None:
        """user_message() returns the same text as str(err)."""
        err = NoLLMProviderError()
        assert err.user_message() == str(err)

    def test_reason_stored(self) -> None:
        """Technical reason is preserved on the error object."""
        err = NoLLMProviderError(reason="groq: 401 Unauthorized")
        assert err.reason == "groq: 401 Unauthorized"

    def test_reason_default_empty_string(self) -> None:
        """reason defaults to empty string when not provided."""
        err = NoLLMProviderError()
        assert err.reason == ""

    def test_can_be_raised_and_caught(self) -> None:
        """NoLLMProviderError can be raised and caught normally."""
        with pytest.raises(NoLLMProviderError, match="No LLM provider"):
            raise NoLLMProviderError

    def test_can_be_caught_as_base_exception(self) -> None:
        """NoLLMProviderError is caught by bare except Exception."""
        caught: Exception | None = None
        try:
            raise NoLLMProviderError(reason="test")
        except Exception as exc:
            caught = exc
        assert isinstance(caught, NoLLMProviderError)


class TestIsProviderError:
    """Tests for _is_provider_error() — issue #287."""

    def test_httpx_connect_error_is_provider_error(self) -> None:
        """httpx.ConnectError (Ollama not running) → True."""
        import httpx

        exc = httpx.ConnectError("Connection refused")
        assert _is_provider_error(exc) is True

    def test_httpx_connect_timeout_is_provider_error(self) -> None:
        """httpx.ConnectTimeout → True."""
        import httpx

        exc = httpx.ConnectTimeout("Timed out")
        assert _is_provider_error(exc) is True

    def test_connection_refused_error_is_provider_error(self) -> None:
        """stdlib ConnectionRefusedError → True."""
        exc = ConnectionRefusedError("Connection refused")
        assert _is_provider_error(exc) is True

    def test_openai_authentication_error_is_provider_error(self) -> None:
        """openai.AuthenticationError (bad API key) → True."""
        from unittest.mock import MagicMock

        import openai

        mock_response = MagicMock()
        mock_response.request = MagicMock()
        exc = openai.AuthenticationError(
            message="Incorrect API key",
            response=mock_response,
            body=None,
        )
        assert _is_provider_error(exc) is True

    def test_openai_not_found_error_is_provider_error(self) -> None:
        """openai.NotFoundError (model not found / wrong endpoint) → True."""
        from unittest.mock import MagicMock

        import openai

        mock_response = MagicMock()
        mock_response.request = MagicMock()
        exc = openai.NotFoundError(
            message="Model not found",
            response=mock_response,
            body=None,
        )
        assert _is_provider_error(exc) is True

    def test_openai_api_connection_error_is_provider_error(self) -> None:
        """openai.APIConnectionError → True."""
        import openai

        exc = openai.APIConnectionError(request=None)  # type: ignore[arg-type]
        assert _is_provider_error(exc) is True

    def test_value_error_is_not_provider_error(self) -> None:
        """Generic ValueError is not a provider error."""
        exc = ValueError("something unrelated")
        assert _is_provider_error(exc) is False

    def test_runtime_error_is_not_provider_error(self) -> None:
        """Generic RuntimeError is not a provider error."""
        exc = RuntimeError("workflow failed")
        assert _is_provider_error(exc) is False

    def test_key_error_is_not_provider_error(self) -> None:
        """KeyError is not a provider error."""
        exc = KeyError("missing_key")
        assert _is_provider_error(exc) is False


class TestCliWorkflowRunErrorHandling:
    """Tests for the CLI _cmd_run error-handling path — issue #287."""

    def _make_fake_args(self, **overrides: object) -> object:
        """Build a minimal argparse.Namespace-like object for _cmd_run."""
        import argparse

        defaults = {
            "name": "feature_dev",
            "goal": "add login",
            "dry_run": False,
            "no_confirm": False,
            "track_l0": False,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_no_provider_error_returns_exit_1(self, capsys: pytest.CaptureFixture) -> None:
        """When the orchestrator raises NoLLMProviderError, _cmd_run returns 1."""
        from unittest.mock import AsyncMock, patch

        from ttadev.cli.workflow import _cmd_run
        from ttadev.workflows.llm_provider import NoLLMProviderError
        from ttadev.workflows.prebuilt import feature_dev_workflow

        workflows = {"feature_dev": feature_dev_workflow}
        args = self._make_fake_args()

        with patch(
            "ttadev.workflows.orchestrator.WorkflowOrchestrator.execute",
            new=AsyncMock(side_effect=NoLLMProviderError(reason="no key")),
        ):
            rc = _cmd_run(workflows, args, None)  # type: ignore[arg-type]

        assert rc == 1
        captured = capsys.readouterr()
        assert "No LLM provider" in captured.err

    def test_openai_auth_error_shows_friendly_message(self, capsys: pytest.CaptureFixture) -> None:
        """openai.AuthenticationError during run → friendly message, rc=1."""
        from unittest.mock import AsyncMock, MagicMock, patch

        import openai

        from ttadev.cli.workflow import _cmd_run
        from ttadev.workflows.prebuilt import feature_dev_workflow

        workflows = {"feature_dev": feature_dev_workflow}
        args = self._make_fake_args()

        mock_response = MagicMock()
        mock_response.request = MagicMock()
        auth_exc = openai.AuthenticationError(
            message="Incorrect API key",
            response=mock_response,
            body=None,
        )
        with patch(
            "ttadev.workflows.orchestrator.WorkflowOrchestrator.execute",
            new=AsyncMock(side_effect=auth_exc),
        ):
            rc = _cmd_run(workflows, args, None)  # type: ignore[arg-type]

        assert rc == 1
        captured = capsys.readouterr()
        assert "No LLM provider" in captured.err
        assert "GROQ_API_KEY" in captured.err

    def test_httpx_connect_error_shows_friendly_message(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """httpx.ConnectError (Ollama down) during run → friendly message, rc=1."""
        from unittest.mock import AsyncMock, patch

        import httpx

        from ttadev.cli.workflow import _cmd_run
        from ttadev.workflows.prebuilt import feature_dev_workflow

        workflows = {"feature_dev": feature_dev_workflow}
        args = self._make_fake_args()

        conn_exc = httpx.ConnectError("Connection refused")
        with patch(
            "ttadev.workflows.orchestrator.WorkflowOrchestrator.execute",
            new=AsyncMock(side_effect=conn_exc),
        ):
            rc = _cmd_run(workflows, args, None)  # type: ignore[arg-type]

        assert rc == 1
        captured = capsys.readouterr()
        assert "No LLM provider" in captured.err
        assert "ollama pull" in captured.err

    def test_unrelated_error_is_reraised(self) -> None:
        """Non-provider exceptions (e.g. RuntimeError) propagate unchanged."""
        from unittest.mock import AsyncMock, patch

        import pytest

        from ttadev.cli.workflow import _cmd_run
        from ttadev.workflows.prebuilt import feature_dev_workflow

        workflows = {"feature_dev": feature_dev_workflow}
        args = self._make_fake_args()

        boom = RuntimeError("something completely different")
        with patch(
            "ttadev.workflows.orchestrator.WorkflowOrchestrator.execute",
            new=AsyncMock(side_effect=boom),
        ):
            with pytest.raises(RuntimeError, match="something completely different"):
                _cmd_run(workflows, args, None)  # type: ignore[arg-type]
