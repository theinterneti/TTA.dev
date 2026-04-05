"""Unit tests for ModelRouterPrimitive.

Covers: _build_messages, RouterTierConfig, RouterModeConfig, ModelRouterRequest,
ModelRouterPrimitive (ctor, execute, cooldown helpers, _call_tier for every
provider, _try_model_candidates, _call_ollama, _call_openai_compat, from_yaml).

All HTTP calls are mocked via httpx.AsyncClient patches.
asyncio_mode = auto (pyproject.toml) — @pytest.mark.asyncio is not required.
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.llm.model_router import (
    ModelRouterPrimitive,
    ModelRouterRequest,
    RouterModeConfig,
    RouterTierConfig,
    _build_messages,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(name: str = "test") -> WorkflowContext:
    return WorkflowContext(workflow_id=name)


def _make_httpx_mock(json_response: dict):
    """Return (mock_cm, mock_resp, mock_client) for httpx.AsyncClient patching."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = json_response
    mock_resp.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    return mock_cm, mock_resp, mock_client


def _make_429_exc() -> httpx.HTTPStatusError:
    """Return an httpx.HTTPStatusError with status_code=429."""
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    return httpx.HTTPStatusError("429 Too Many Requests", request=MagicMock(), response=mock_resp)


def _simple_router(*, groq_api_key: str = "test-key") -> ModelRouterPrimitive:
    """Return a router with a single 'chat' mode (groq) for testing."""
    mock_tracker = MagicMock()
    mock_tracker.recommend = AsyncMock(return_value="some-free-model")
    modes = {
        "chat": RouterModeConfig(
            tiers=[RouterTierConfig(provider="groq", model="llama-3.1-8b-instant")]
        )
    }
    return ModelRouterPrimitive(
        modes=modes,
        groq_api_key=groq_api_key,
        free_tracker=mock_tracker,
    )


# ---------------------------------------------------------------------------
# _build_messages
# ---------------------------------------------------------------------------


class TestBuildMessages:
    def test_without_system(self):
        # Arrange / Act
        msgs = _build_messages("Hello", None)
        # Assert
        assert msgs == [{"role": "user", "content": "Hello"}]

    def test_with_system(self):
        # Arrange / Act
        msgs = _build_messages("Hello", "You are helpful.")
        # Assert
        assert msgs == [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ]

    def test_empty_system_string_not_prepended(self):
        # Arrange / Act — empty string is falsy
        msgs = _build_messages("Hi", "")
        # Assert
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"

    def test_prompt_content_preserved(self):
        msgs = _build_messages("Tell me about Python.", None)
        assert msgs[0]["content"] == "Tell me about Python."


# ---------------------------------------------------------------------------
# RouterTierConfig
# ---------------------------------------------------------------------------


class TestRouterTierConfig:
    def test_defaults(self):
        # Arrange / Act
        tier = RouterTierConfig(provider="ollama")
        # Assert
        assert tier.provider == "ollama"
        assert tier.model is None
        assert tier.models == []
        assert tier.params == {}
        assert tier.strip_thinking is True

    def test_custom_values_stored(self):
        # Arrange / Act
        tier = RouterTierConfig(
            provider="groq",
            model="llama3",
            models=["m1", "m2"],
            params={"temperature": 0.5},
            strip_thinking=False,
        )
        # Assert
        assert tier.model == "llama3"
        assert tier.models == ["m1", "m2"]
        assert tier.params["temperature"] == 0.5
        assert tier.strip_thinking is False


# ---------------------------------------------------------------------------
# RouterModeConfig
# ---------------------------------------------------------------------------


class TestRouterModeConfig:
    def test_defaults(self):
        mode = RouterModeConfig()
        assert mode.description == ""
        assert mode.tiers == []

    def test_with_tiers(self):
        t = RouterTierConfig(provider="ollama", model="m1")
        mode = RouterModeConfig(description="My mode", tiers=[t])
        assert mode.description == "My mode"
        assert len(mode.tiers) == 1


# ---------------------------------------------------------------------------
# ModelRouterRequest
# ---------------------------------------------------------------------------


class TestModelRouterRequest:
    def test_defaults(self):
        req = ModelRouterRequest(mode="chat", prompt="hi")
        assert req.mode == "chat"
        assert req.prompt == "hi"
        assert req.system is None
        assert req.tier_override is None
        assert req.task_profile is None

    def test_with_system(self):
        req = ModelRouterRequest(mode="chat", prompt="q", system="sys")
        assert req.system == "sys"


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


class TestModelRouterPrimitiveCtor:
    def test_explicit_keys_stored(self):
        # Arrange
        mock_tracker = MagicMock()
        modes = {"m": RouterModeConfig()}
        # Act
        router = ModelRouterPrimitive(
            modes=modes,
            groq_api_key="gk",
            openrouter_api_key="ok",
            together_api_key="tk",
            google_api_key="ggk",
            ollama_url="http://localhost:11434",
            free_tracker=mock_tracker,
            tier_cooldown_seconds=60,
        )
        # Assert
        assert router._groq_api_key == "gk"
        assert router._or_api_key == "ok"
        assert router._together_api_key == "tk"
        assert router._google_api_key == "ggk"
        assert router._tier_cooldown_seconds == 60
        assert router._tracker is mock_tracker

    def test_modes_property_returns_copy(self):
        # Arrange
        modes = {"a": RouterModeConfig(description="desc")}
        router = ModelRouterPrimitive(modes=modes, free_tracker=MagicMock())
        # Act / Assert
        assert "a" in router.modes
        assert router.modes["a"].description == "desc"

    def test_ollama_url_trailing_slash_stripped(self):
        # Arrange
        router = ModelRouterPrimitive(
            modes={},
            ollama_url="http://localhost:11434/",
            free_tracker=MagicMock(),
        )
        # Assert
        assert not router._ollama_url.endswith("/")


# ---------------------------------------------------------------------------
# execute — invalid mode / tier_override
# ---------------------------------------------------------------------------


class TestExecuteInvalidMode:
    async def test_unknown_mode_raises_value_error(self):
        # Arrange
        router = _simple_router()
        req = ModelRouterRequest(mode="nonexistent_mode", prompt="hi")
        # Act / Assert
        with pytest.raises(ValueError, match="Unknown routing mode"):
            await router.execute(req, _ctx())

    async def test_tier_override_zero_raises_value_error(self):
        # Arrange
        router = _simple_router()
        req = ModelRouterRequest(mode="chat", prompt="hi", tier_override=0)
        # Act / Assert
        with pytest.raises(ValueError, match="out of range"):
            await router.execute(req, _ctx())

    async def test_tier_override_too_large_raises_value_error(self):
        # Arrange
        router = _simple_router()
        req = ModelRouterRequest(mode="chat", prompt="hi", tier_override=99)
        # Act / Assert
        with pytest.raises(ValueError, match="out of range"):
            await router.execute(req, _ctx())


# ---------------------------------------------------------------------------
# execute — Groq success, strip_thinking
# ---------------------------------------------------------------------------


class TestExecuteGroqSuccess:
    async def test_returns_llm_response(self):
        # Arrange
        mock_cm, _, _ = _make_httpx_mock({"choices": [{"message": {"content": "hello from groq"}}]})
        router = _simple_router()
        req = ModelRouterRequest(mode="chat", prompt="say hi")
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(req, _ctx())
        # Assert
        assert result.content == "hello from groq"
        assert result.provider == "groq"
        assert result.model == "llama-3.1-8b-instant"

    async def test_strip_thinking_removes_think_tags(self):
        # Arrange
        mock_cm, _, _ = _make_httpx_mock(
            {"choices": [{"message": {"content": "<think>secret reasoning</think>final answer"}}]}
        )
        router = _simple_router()
        req = ModelRouterRequest(mode="chat", prompt="hi")
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(req, _ctx())
        # Assert
        assert "<think>" not in result.content
        assert result.content == "final answer"

    async def test_strip_thinking_disabled_preserves_tags(self):
        # Arrange
        raw = "<think>reason</think>answer"
        mock_cm, _, _ = _make_httpx_mock({"choices": [{"message": {"content": raw}}]})
        mock_tracker = MagicMock()
        mock_tracker.recommend = AsyncMock(return_value="x")
        modes = {
            "chat": RouterModeConfig(
                tiers=[RouterTierConfig(provider="groq", model="m", strip_thinking=False)]
            )
        }
        router = ModelRouterPrimitive(modes=modes, groq_api_key="k", free_tracker=mock_tracker)
        req = ModelRouterRequest(mode="chat", prompt="hi")
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(req, _ctx())
        # Assert
        assert "<think>" in result.content


# ---------------------------------------------------------------------------
# execute — tier_override
# ---------------------------------------------------------------------------


class TestExecuteTierOverride:
    async def test_override_selects_second_tier(self):
        # Arrange — mode has two tiers; override=2 picks the second
        mock_cm, _, _ = _make_httpx_mock({"choices": [{"message": {"content": "tier2 response"}}]})
        mock_tracker = MagicMock()
        mock_tracker.recommend = AsyncMock(return_value="x")
        modes = {
            "chat": RouterModeConfig(
                tiers=[
                    RouterTierConfig(provider="groq", model="m1"),
                    RouterTierConfig(provider="groq", model="m2"),
                ]
            )
        }
        router = ModelRouterPrimitive(modes=modes, groq_api_key="k", free_tracker=mock_tracker)
        req = ModelRouterRequest(mode="chat", prompt="hi", tier_override=2)
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(req, _ctx())
        # Assert
        assert result.model == "m2"


# ---------------------------------------------------------------------------
# execute — all tiers fail
# ---------------------------------------------------------------------------


class TestExecuteAllTiersFail:
    async def test_raises_runtime_error(self):
        # Arrange — connection always fails
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(side_effect=ConnectionError("refused"))
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        router = _simple_router()
        req = ModelRouterRequest(mode="chat", prompt="hi")
        # Act / Assert
        with patch("httpx.AsyncClient", return_value=mock_cm):
            with pytest.raises(RuntimeError, match="tiers failed"):
                await router.execute(req, _ctx())


# ---------------------------------------------------------------------------
# _call_ollama
# ---------------------------------------------------------------------------


class TestCallOllama:
    async def test_success_returns_content(self):
        # Arrange
        mock_cm, _, mock_client = _make_httpx_mock({"message": {"content": "hi from ollama"}})
        router = _simple_router()
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router._call_ollama("llama3", "hello", None, {})
        # Assert
        assert result == "hi from ollama"
        mock_client.post.assert_awaited_once()

    async def test_with_system_and_params(self):
        # Arrange
        mock_cm, _, mock_client = _make_httpx_mock({"message": {"content": "answer"}})
        router = _simple_router()
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            await router._call_ollama("llama3", "q", "be helpful", {"temperature": 0.5})
        # Assert
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["options"] == {"temperature": 0.5}
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][0]["content"] == "be helpful"

    async def test_raises_on_http_error(self):
        # Arrange
        mock_resp_obj = MagicMock()
        mock_resp_obj.status_code = 500
        http_exc = httpx.HTTPStatusError("500", request=MagicMock(), response=mock_resp_obj)
        inner_resp = MagicMock()
        inner_resp.raise_for_status = MagicMock(side_effect=http_exc)
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=inner_resp)
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        router = _simple_router()
        # Act / Assert
        with patch("httpx.AsyncClient", return_value=mock_cm):
            with pytest.raises(httpx.HTTPStatusError):
                await router._call_ollama("llama3", "q", None, {})

    async def test_no_params_omits_options_key(self):
        # Arrange
        mock_cm, _, mock_client = _make_httpx_mock({"message": {"content": "ok"}})
        router = _simple_router()
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            await router._call_ollama("llama3", "q", None, {})
        # Assert — empty params → no "options" in payload
        payload = mock_client.post.call_args.kwargs["json"]
        assert "options" not in payload


# ---------------------------------------------------------------------------
# _call_openai_compat
# ---------------------------------------------------------------------------


class TestCallOpenaiCompat:
    async def test_success_returns_content(self):
        # Arrange
        mock_cm, _, _ = _make_httpx_mock({"choices": [{"message": {"content": "good answer"}}]})
        router = _simple_router()
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router._call_openai_compat(
                "https://api.groq.com/v1/chat/completions",
                "mykey",
                "llama3",
                "prompt",
                None,
                {},
            )
        # Assert
        assert result == "good answer"

    async def test_extra_headers_forwarded(self):
        # Arrange
        mock_cm, _, mock_client = _make_httpx_mock({"choices": [{"message": {"content": "ok"}}]})
        router = _simple_router()
        extra = {"HTTP-Referer": "https://example.com"}
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            await router._call_openai_compat(
                "https://openrouter.ai/api/v1/chat/completions",
                "mykey",
                "model",
                "prompt",
                None,
                {},
                extra_headers=extra,
            )
        # Assert
        headers = mock_client.post.call_args.kwargs["headers"]
        assert headers.get("HTTP-Referer") == "https://example.com"

    async def test_bearer_auth_header_set(self):
        # Arrange
        mock_cm, _, mock_client = _make_httpx_mock({"choices": [{"message": {"content": "ok"}}]})
        router = _simple_router()
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            await router._call_openai_compat(
                "https://api.groq.com/v1/chat/completions",
                "secret-key",
                "model",
                "q",
                None,
                {},
            )
        # Assert
        headers = mock_client.post.call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer secret-key"


# ---------------------------------------------------------------------------
# _call_tier — Ollama
# ---------------------------------------------------------------------------


class TestCallTierOllama:
    async def test_no_model_raises_value_error(self):
        # Arrange
        router = _simple_router()
        tier = RouterTierConfig(provider="ollama", model=None)
        # Act / Assert
        with pytest.raises(ValueError, match="requires an explicit 'model'"):
            await router._call_tier(tier, "q", None)

    async def test_success_returns_content_and_model(self):
        # Arrange
        mock_cm, _, _ = _make_httpx_mock({"message": {"content": "local answer"}})
        router = _simple_router()
        tier = RouterTierConfig(provider="ollama", model="llama3.2")
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            content, model = await router._call_tier(tier, "q", None)
        # Assert
        assert content == "local answer"
        assert model == "llama3.2"


# ---------------------------------------------------------------------------
# _call_tier — Groq
# ---------------------------------------------------------------------------


class TestCallTierGroq:
    async def test_pinned_model_success(self):
        # Arrange
        mock_cm, _, _ = _make_httpx_mock({"choices": [{"message": {"content": "from groq"}}]})
        router = _simple_router()
        tier = RouterTierConfig(provider="groq", model="llama-3.1-8b-instant")
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            content, model = await router._call_tier(tier, "q", None)
        # Assert
        assert content == "from groq"
        assert model == "llama-3.1-8b-instant"

    async def test_models_list_falls_through_on_429(self):
        # Arrange — first model returns 429, second succeeds
        exc_429 = _make_429_exc()
        call_count = {"n": 0}

        async def post_side_effect(*args, **kwargs):
            call_count["n"] += 1
            mock_r = MagicMock()
            if call_count["n"] == 1:
                mock_r.raise_for_status = MagicMock(side_effect=exc_429)
            else:
                mock_r.raise_for_status = MagicMock()
                mock_r.json.return_value = {"choices": [{"message": {"content": "second works"}}]}
            return mock_r

        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=post_side_effect)
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        router = _simple_router()
        tier = RouterTierConfig(provider="groq", models=["m1", "m2"])
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            content, model = await router._call_tier(tier, "q", None)
        # Assert
        assert content == "second works"
        assert model == "m2"

    async def test_no_model_uses_discovery_fallback(self):
        # Arrange — no model specified; discovery returns list
        mock_cm, _, _ = _make_httpx_mock({"choices": [{"message": {"content": "discovered"}}]})
        mock_tracker = MagicMock()
        mock_tracker.recommend = AsyncMock(return_value="x")
        router = ModelRouterPrimitive(
            modes={},
            groq_api_key="gk",
            free_tracker=mock_tracker,
        )
        mock_discovery = MagicMock()
        mock_discovery.for_provider = AsyncMock(return_value=["llama-3.1-8b-instant"])
        mock_discovery.is_exhausted = MagicMock(return_value=False)
        router._discovery = mock_discovery
        tier = RouterTierConfig(provider="groq")
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            content, model = await router._call_tier(tier, "q", None)
        # Assert
        assert content == "discovered"


# ---------------------------------------------------------------------------
# _call_tier — Together AI
# ---------------------------------------------------------------------------


class TestCallTierTogether:
    async def test_no_model_raises_value_error(self):
        # Arrange
        router = _simple_router()
        tier = RouterTierConfig(provider="together")
        # Act / Assert
        with pytest.raises(ValueError, match="Together AI"):
            await router._call_tier(tier, "q", None)

    async def test_pinned_model_success(self):
        # Arrange
        mock_cm, _, _ = _make_httpx_mock({"choices": [{"message": {"content": "together answer"}}]})
        mock_tracker = MagicMock()
        router = ModelRouterPrimitive(modes={}, together_api_key="tk", free_tracker=mock_tracker)
        tier = RouterTierConfig(provider="together", model="togethercomputer/llama-2-7b")
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            content, model = await router._call_tier(tier, "q", None)
        # Assert
        assert content == "together answer"
        assert model == "togethercomputer/llama-2-7b"


# ---------------------------------------------------------------------------
# _call_tier — OpenRouter
# ---------------------------------------------------------------------------


class TestCallTierOpenrouter:
    async def test_pinned_model(self):
        # Arrange
        mock_cm, _, _ = _make_httpx_mock({"choices": [{"message": {"content": "or answer"}}]})
        mock_tracker = MagicMock()
        mock_tracker.recommend = AsyncMock(return_value="some-free-model")
        router = ModelRouterPrimitive(modes={}, openrouter_api_key="ok", free_tracker=mock_tracker)
        tier = RouterTierConfig(provider="openrouter", model="mistralai/mistral-7b:free")
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            content, model = await router._call_tier(tier, "q", None)
        # Assert
        assert content == "or answer"
        assert model == "mistralai/mistral-7b:free"

    async def test_alias_or_works(self):
        # Arrange — 'or' is an alias for 'openrouter'
        mock_cm, _, _ = _make_httpx_mock({"choices": [{"message": {"content": "or alias answer"}}]})
        mock_tracker = MagicMock()
        mock_tracker.recommend = AsyncMock(return_value="model-x")
        router = ModelRouterPrimitive(modes={}, openrouter_api_key="ok", free_tracker=mock_tracker)
        tier = RouterTierConfig(provider="or", model="some-model")
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            content, model = await router._call_tier(tier, "q", None)
        # Assert
        assert model == "some-model"

    async def test_no_model_uses_tracker(self):
        # Arrange
        mock_cm, _, _ = _make_httpx_mock({"choices": [{"message": {"content": "tracker answer"}}]})
        mock_tracker = MagicMock()
        mock_tracker.recommend = AsyncMock(return_value="free-model-xyz")
        router = ModelRouterPrimitive(modes={}, openrouter_api_key="ok", free_tracker=mock_tracker)
        tier = RouterTierConfig(provider="openrouter")
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            content, model = await router._call_tier(tier, "q", None)
        # Assert
        assert model == "free-model-xyz"

    async def test_tracker_returns_none_raises_runtime_error(self):
        # Arrange
        mock_tracker = MagicMock()
        mock_tracker.recommend = AsyncMock(return_value=None)
        router = ModelRouterPrimitive(modes={}, openrouter_api_key="ok", free_tracker=mock_tracker)
        tier = RouterTierConfig(provider="openrouter")
        # Act / Assert
        with pytest.raises(RuntimeError, match="no candidate models"):
            await router._call_tier(tier, "q", None)

    async def test_models_list_uses_try_model_candidates(self):
        # Arrange
        mock_cm, _, _ = _make_httpx_mock(
            {"choices": [{"message": {"content": "multi-model answer"}}]}
        )
        mock_tracker = MagicMock()
        router = ModelRouterPrimitive(modes={}, openrouter_api_key="ok", free_tracker=mock_tracker)
        tier = RouterTierConfig(provider="openrouter", models=["model-a", "model-b"])
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            content, model = await router._call_tier(tier, "q", None)
        # Assert
        assert model == "model-a"  # first one succeeds


# ---------------------------------------------------------------------------
# _call_tier — auto
# ---------------------------------------------------------------------------


class TestCallTierAuto:
    async def test_auto_uses_tracker(self):
        # Arrange
        mock_cm, _, _ = _make_httpx_mock({"choices": [{"message": {"content": "auto answer"}}]})
        mock_tracker = MagicMock()
        mock_tracker.recommend = AsyncMock(return_value="best-free-model")
        router = ModelRouterPrimitive(modes={}, openrouter_api_key="ok", free_tracker=mock_tracker)
        tier = RouterTierConfig(provider="auto")
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            content, model = await router._call_tier(tier, "q", None)
        # Assert
        assert content == "auto answer"
        assert model == "best-free-model"

    async def test_auto_tracker_none_raises_runtime_error(self):
        # Arrange
        mock_tracker = MagicMock()
        mock_tracker.recommend = AsyncMock(return_value=None)
        router = ModelRouterPrimitive(modes={}, free_tracker=mock_tracker)
        tier = RouterTierConfig(provider="auto")
        # Act / Assert
        with pytest.raises(RuntimeError, match="no candidate models"):
            await router._call_tier(tier, "q", None)


# ---------------------------------------------------------------------------
# _call_tier — Google
# ---------------------------------------------------------------------------


class TestCallTierGoogle:
    async def test_pinned_model_with_models_prefix(self):
        # Arrange
        mock_cm, _, _ = _make_httpx_mock({"choices": [{"message": {"content": "gemini answer"}}]})
        mock_tracker = MagicMock()
        router = ModelRouterPrimitive(modes={}, google_api_key="gk", free_tracker=mock_tracker)
        tier = RouterTierConfig(provider="google", model="models/gemini-2.0-flash-lite")
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            content, model = await router._call_tier(tier, "q", None)
        # Assert
        assert content == "gemini answer"
        assert model == "models/gemini-2.0-flash-lite"

    async def test_model_without_prefix_gets_prefix_added(self):
        # Arrange
        mock_cm, _, mock_client = _make_httpx_mock({"choices": [{"message": {"content": "ok"}}]})
        mock_tracker = MagicMock()
        router = ModelRouterPrimitive(modes={}, google_api_key="gk", free_tracker=mock_tracker)
        tier = RouterTierConfig(provider="google", models=["gemini-flash"])
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            content, model = await router._call_tier(tier, "q", None)
        # Assert — prefix was added
        assert model == "models/gemini-flash"

    async def test_no_model_falls_back_to_discovery(self):
        # Arrange
        mock_cm, _, _ = _make_httpx_mock(
            {"choices": [{"message": {"content": "discovered gemini"}}]}
        )
        mock_tracker = MagicMock()
        router = ModelRouterPrimitive(modes={}, google_api_key="gk", free_tracker=mock_tracker)
        mock_discovery = MagicMock()
        mock_discovery.for_provider = AsyncMock(return_value=["models/gemini-2.0-flash"])
        mock_discovery.is_exhausted = MagicMock(return_value=False)
        router._discovery = mock_discovery
        tier = RouterTierConfig(provider="google")
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            content, model = await router._call_tier(tier, "q", None)
        # Assert
        assert model == "models/gemini-2.0-flash"


# ---------------------------------------------------------------------------
# _call_tier — unknown provider
# ---------------------------------------------------------------------------


class TestCallTierUnknown:
    async def test_raises_value_error(self):
        # Arrange
        router = _simple_router()
        tier = RouterTierConfig(provider="unicorn_provider")
        # Act / Assert
        with pytest.raises(ValueError, match="Unknown provider"):
            await router._call_tier(tier, "q", None)


# ---------------------------------------------------------------------------
# _try_model_candidates
# ---------------------------------------------------------------------------


class TestTryModelCandidates:
    async def test_first_model_succeeds(self):
        # Arrange
        mock_cm, _, _ = _make_httpx_mock({"choices": [{"message": {"content": "ok"}}]})
        router = _simple_router()
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            content, model = await router._try_model_candidates(
                ["m1", "m2"],
                "https://api.groq.com/v1/chat/completions",
                "key",
                "prompt",
                None,
                {},
            )
        # Assert
        assert content == "ok"
        assert model == "m1"

    async def test_non_429_failure_raises_runtime_error(self):
        # Arrange — every model raises a non-HTTP connection error
        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=ConnectionError("refused"))
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        router = _simple_router()
        # Act / Assert
        with patch("httpx.AsyncClient", return_value=mock_cm):
            with pytest.raises(RuntimeError, match="model candidate"):
                await router._try_model_candidates(
                    ["m1"], "https://api/v1/chat/completions", "key", "q", None, {}
                )

    async def test_all_429_chains_cause_to_http_status_error(self):
        # Arrange — every model returns 429
        exc_429 = _make_429_exc()
        inner_resp = MagicMock()
        inner_resp.raise_for_status = MagicMock(side_effect=exc_429)
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=inner_resp)
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        router = _simple_router()
        # Act / Assert
        with patch("httpx.AsyncClient", return_value=mock_cm):
            with pytest.raises(RuntimeError) as exc_info:
                await router._try_model_candidates(
                    ["m1", "m2"],
                    "https://api/v1/chat/completions",
                    "key",
                    "q",
                    None,
                    {},
                )
        # __cause__ must be the original 429 HTTPStatusError
        assert exc_info.value.__cause__ is exc_429

    async def test_empty_candidates_raises_runtime_error(self):
        # Arrange
        router = _simple_router()
        # Act / Assert
        with pytest.raises(RuntimeError):
            await router._try_model_candidates([], "https://api/v1", "key", "q", None, {})


# ---------------------------------------------------------------------------
# Cooldown helpers
# ---------------------------------------------------------------------------


class TestCooldownHelpers:
    def test_is_cooling_false_with_no_entry(self):
        # Arrange
        router = _simple_router()
        # Act / Assert
        assert router._is_cooling("groq/llama3") is False

    def test_mark_cooling_makes_is_cooling_true(self):
        # Arrange
        router = _simple_router()
        key = "groq/model"
        # Act
        router._mark_cooling(key)
        # Assert
        assert router._is_cooling(key) is True

    def test_is_cooling_false_after_deadline_passes(self):
        # Arrange
        router = _simple_router()
        key = "groq/model"
        # Manually set an expired deadline
        router._tier_cooldowns[key] = time.monotonic() - 1.0
        # Act / Assert
        assert router._is_cooling(key) is False

    def test_cooldown_zero_disables_cooldown(self):
        # Arrange
        modes = {"m": RouterModeConfig()}
        router = ModelRouterPrimitive(
            modes=modes, free_tracker=MagicMock(), tier_cooldown_seconds=0
        )
        key = "groq/model"
        # Act
        router._mark_cooling(key)  # should be a no-op when cooldown=0
        # Assert
        assert router._is_cooling(key) is False
        assert key not in router._tier_cooldowns

    async def test_429_triggers_cooldown_and_fallthrough(self):
        # Arrange — tier1 returns 429, tier2 succeeds
        exc_429 = _make_429_exc()
        call_count = {"n": 0}

        async def post_side_effect(*args, **kwargs):
            call_count["n"] += 1
            mock_r = MagicMock()
            if call_count["n"] == 1:
                mock_r.raise_for_status = MagicMock(side_effect=exc_429)
            else:
                mock_r.raise_for_status = MagicMock()
                mock_r.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
            return mock_r

        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=post_side_effect)
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        mock_tracker = MagicMock()
        mock_tracker.recommend = AsyncMock(return_value="x")
        modes = {
            "chat": RouterModeConfig(
                tiers=[
                    RouterTierConfig(provider="groq", model="m1"),
                    RouterTierConfig(provider="groq", model="m2"),
                ]
            )
        }
        router = ModelRouterPrimitive(modes=modes, groq_api_key="key", free_tracker=mock_tracker)
        req = ModelRouterRequest(mode="chat", prompt="hi")
        # Act
        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(req, _ctx())
        # Assert — second tier succeeded; first tier is now cooling
        assert result.model == "m2"
        assert router._is_cooling("groq/m1") is True


# ---------------------------------------------------------------------------
# from_yaml
# ---------------------------------------------------------------------------


class TestFromYaml:
    def test_parses_yaml_modes(self, tmp_path: Path):
        # Arrange
        yaml_content = """
modes:
  chat:
    description: "Chat mode"
    tier1:
      provider: groq
      model: llama-3.1-8b-instant
      params:
        temperature: 0.7
    tier2:
      provider: openrouter
      model: "mistralai/mistral-7b-instruct:free"
  extract:
    description: "Extraction"
    tier1:
      provider: ollama
      model: qwen2.5:7b
"""
        config_file = tmp_path / "model_modes.yaml"
        config_file.write_text(yaml_content)
        # Act
        router = ModelRouterPrimitive.from_yaml(config_file, free_tracker=MagicMock())
        # Assert
        assert "chat" in router.modes
        assert "extract" in router.modes
        chat = router.modes["chat"]
        assert chat.description == "Chat mode"
        assert len(chat.tiers) == 2
        assert chat.tiers[0].provider == "groq"
        assert chat.tiers[0].model == "llama-3.1-8b-instant"
        assert chat.tiers[0].params["temperature"] == 0.7

    def test_null_model_becomes_none(self, tmp_path: Path):
        # Arrange
        yaml_content = "modes:\n  auto:\n    tier1:\n      provider: auto\n      model: null\n"
        config_file = tmp_path / "m.yaml"
        config_file.write_text(yaml_content)
        # Act
        router = ModelRouterPrimitive.from_yaml(config_file, free_tracker=MagicMock())
        # Assert
        assert router.modes["auto"].tiers[0].model is None

    def test_auto_model_value_becomes_none(self, tmp_path: Path):
        # Arrange
        yaml_content = "modes:\n  auto:\n    tier1:\n      provider: groq\n      model: auto\n"
        config_file = tmp_path / "m.yaml"
        config_file.write_text(yaml_content)
        # Act
        router = ModelRouterPrimitive.from_yaml(config_file, free_tracker=MagicMock())
        # Assert
        assert router.modes["auto"].tiers[0].model is None

    def test_empty_yaml_returns_empty_modes(self, tmp_path: Path):
        # Arrange
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("---\n")
        # Act
        router = ModelRouterPrimitive.from_yaml(config_file, free_tracker=MagicMock())
        # Assert
        assert router.modes == {}

    def test_kwargs_forwarded_to_constructor(self, tmp_path: Path):
        # Arrange
        yaml_content = "modes:\n  m:\n    tier1:\n      provider: groq\n      model: llama3\n"
        config_file = tmp_path / "m.yaml"
        config_file.write_text(yaml_content)
        # Act
        router = ModelRouterPrimitive.from_yaml(
            config_file, free_tracker=MagicMock(), groq_api_key="my-key"
        )
        # Assert
        assert router._groq_api_key == "my-key"
