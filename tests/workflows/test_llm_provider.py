"""Unit tests for get_llm_provider_chain in llm_provider.py."""

from __future__ import annotations

import pytest

from ttadev.workflows.llm_provider import (
    get_llm_client,
    get_llm_provider_chain,
)


class TestGetLlmProviderChain:
    """Tests for get_llm_provider_chain()."""

    def test_chain_openrouter_then_ollama_when_key_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OPENROUTER_API_KEY set → chain is [openrouter, ollama]."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-123")
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)

        chain = get_llm_provider_chain()

        assert len(chain) == 2
        assert chain[0].provider == "openrouter"
        assert chain[1].provider == "ollama"
        assert chain[0].api_key == "test-key-123"  # pragma: allowlist secret

    def test_chain_ollama_only_when_no_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No OPENROUTER_API_KEY → chain is [ollama] only."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)

        chain = get_llm_provider_chain()

        assert len(chain) == 1
        assert chain[0].provider == "ollama"

    def test_chain_force_ollama_overrides_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """LLM_FORCE_PROVIDER=ollama → [ollama] even if key is set."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-123")
        monkeypatch.setenv("LLM_FORCE_PROVIDER", "ollama")

        chain = get_llm_provider_chain()

        assert len(chain) == 1
        assert chain[0].provider == "ollama"

    def test_chain_ollama_when_key_is_empty_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty string OPENROUTER_API_KEY falls back to [ollama] (same as unset)."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "")
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)
        from ttadev.workflows.llm_provider import get_llm_provider_chain

        chain = get_llm_provider_chain()
        assert len(chain) == 1
        assert chain[0].provider == "ollama"

    def test_get_llm_client_still_works(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """get_llm_client() is unaffected by the new function."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-456")
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)

        cfg = get_llm_client()

        assert cfg.provider == "openrouter"
        assert cfg.api_key == "test-key-456"  # pragma: allowlist secret

    def test_chain_uses_hindsight_model_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """HINDSIGHT_LLM_MODEL env var sets the openrouter model."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")  # pragma: allowlist secret
        monkeypatch.setenv("HINDSIGHT_LLM_MODEL", "anthropic/claude-3-haiku:free")
        monkeypatch.delenv("LLM_FORCE_PROVIDER", raising=False)
        from ttadev.workflows.llm_provider import get_llm_provider_chain

        chain = get_llm_provider_chain()
        assert chain[0].model == "anthropic/claude-3-haiku:free"
