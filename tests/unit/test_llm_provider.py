"""Tests for get_llm_client() provider helper — Task T3."""

import os
from unittest.mock import patch

from ttadev.workflows.llm_provider import LLMClientConfig, get_llm_client


class TestGetLlmClient:
    def test_returns_openrouter_when_key_present(self):
        env = {
            "OPENROUTER_API_KEY": "sk-or-test-key",  # pragma: allowlist secret,
            "HINDSIGHT_LLM_MODEL": "nvidia/nemotron-3-super-120b-a12b:free",
        }
        with patch.dict(os.environ, env, clear=False):
            cfg = get_llm_client()
        assert "openrouter.ai" in cfg.base_url
        assert cfg.api_key == "sk-or-test-key"  # pragma: allowlist secret
        assert cfg.model == "nvidia/nemotron-3-super-120b-a12b:free"
        assert cfg.provider == "openrouter"

    def test_falls_back_to_ollama_when_key_absent(self):
        env = {"OLLAMA_BASE_URL": "http://localhost:11434/v1", "OLLAMA_MODEL": "qwen2.5:7b"}
        with patch.dict(os.environ, env, clear=False):
            with patch.dict(os.environ, {}, clear=False):
                # Ensure OPENROUTER_API_KEY is absent
                os.environ.pop("OPENROUTER_API_KEY", None)
                cfg = get_llm_client()
        assert "11434" in cfg.base_url
        assert cfg.model == "qwen2.5:7b"
        assert cfg.provider == "ollama"

    def test_ollama_env_override_respected(self):
        env = {
            "OPENROUTER_API_KEY": "sk-or-test-key",  # pragma: allowlist secret
            "LLM_FORCE_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://localhost:11434/v1",
            "OLLAMA_MODEL": "phi3.5:mini",
        }
        with patch.dict(os.environ, env, clear=False):
            cfg = get_llm_client()
        assert cfg.provider == "ollama"
        assert cfg.model == "phi3.5:mini"

    def test_returns_llm_client_config(self):
        env = {"OPENROUTER_API_KEY": "sk-or-test-key"}  # pragma: allowlist secret
        with patch.dict(os.environ, env, clear=False):
            cfg = get_llm_client()
        assert isinstance(cfg, LLMClientConfig)
        assert cfg.base_url
        assert cfg.model
        assert cfg.api_key

    def test_default_openrouter_model_fallback(self):
        """When HINDSIGHT_LLM_MODEL not set, uses built-in default."""
        env = {"OPENROUTER_API_KEY": "sk-or-test-key"}  # pragma: allowlist secret
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("HINDSIGHT_LLM_MODEL", None)
            cfg = get_llm_client()
        assert cfg.model  # some non-empty default
        assert cfg.provider == "openrouter"
