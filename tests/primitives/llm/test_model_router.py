"""Tests for ModelRouterPrimitive and helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import yaml

from ttadev.primitives.core import WorkflowContext
from ttadev.primitives.llm.free_model_tracker import FreeModelTracker, ORModel
from ttadev.primitives.llm.model_router import (
    ModelRouterPrimitive,
    ModelRouterRequest,
    RouterModeConfig,
    RouterTierConfig,
    _build_messages,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

_FREE_MODEL = ORModel(
    id="free/best:free",
    name="Best Free",
    context_length=8192,
    prompt_price=0.0,
    completion_price=0.0,
)


def _make_router(
    tiers: list[RouterTierConfig],
    tracker: FreeModelTracker | None = None,
    tier_cooldown_seconds: int = 0,
) -> ModelRouterPrimitive:
    modes = {"test": RouterModeConfig(description="Test mode", tiers=tiers)}
    return ModelRouterPrimitive(
        modes,
        free_tracker=tracker,
        openrouter_api_key="test-key",  # pragma: allowlist secret
        tier_cooldown_seconds=tier_cooldown_seconds,
    )


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="test-router")


# ── _build_messages ───────────────────────────────────────────────────────────


class TestBuildMessages:
    def test_prompt_only(self):
        msgs = _build_messages("hello", None)
        assert msgs == [{"role": "user", "content": "hello"}]

    def test_with_system(self):
        msgs = _build_messages("hello", "you are helpful")
        assert msgs == [
            {"role": "system", "content": "you are helpful"},
            {"role": "user", "content": "hello"},
        ]


# ── from_yaml ─────────────────────────────────────────────────────────────────


class TestFromYaml:
    def test_parses_three_tier_config(self, tmp_path: Path):
        cfg = {
            "modes": {
                "narration": {
                    "description": "Generate narrative",
                    "tier1": {
                        "provider": "ollama",
                        "model": "llama3.2",
                        "params": {"temperature": 0.8},
                    },
                    "tier2": {
                        "provider": "openrouter",
                        "model": "some/model:free",
                        "params": {"max_tokens": 512},
                    },
                    "tier3": {
                        "provider": "auto",
                        "params": {"temperature": 0.7},
                    },
                }
            }
        }
        yaml_file = tmp_path / "model_modes.yaml"
        yaml_file.write_text(yaml.dump(cfg))

        router = ModelRouterPrimitive.from_yaml(yaml_file, openrouter_api_key="key")

        assert "narration" in router.modes
        mode = router.modes["narration"]
        assert mode.description == "Generate narrative"
        assert len(mode.tiers) == 3

        t1, t2, t3 = mode.tiers
        assert t1.provider == "ollama"
        assert t1.model == "llama3.2"
        assert t1.params == {"temperature": 0.8}

        assert t2.provider == "openrouter"
        assert t2.model == "some/model:free"

        assert t3.provider == "auto"
        assert t3.model is None

    def test_null_model_becomes_none(self, tmp_path: Path):
        cfg = {
            "modes": {
                "chat": {
                    "tier1": {
                        "provider": "ollama",
                        "model": None,
                    }
                }
            }
        }
        yaml_file = tmp_path / "modes.yaml"
        yaml_file.write_text(yaml.dump(cfg))
        router = ModelRouterPrimitive.from_yaml(yaml_file)
        assert router.modes["chat"].tiers[0].model is None

    def test_auto_string_model_becomes_none(self, tmp_path: Path):
        cfg = {
            "modes": {
                "chat": {
                    "tier1": {
                        "provider": "openrouter",
                        "model": "auto",
                    }
                }
            }
        }
        yaml_file = tmp_path / "modes.yaml"
        yaml_file.write_text(yaml.dump(cfg))
        router = ModelRouterPrimitive.from_yaml(yaml_file)
        assert router.modes["chat"].tiers[0].model is None

    def test_multiple_modes(self, tmp_path: Path):
        cfg = {
            "modes": {
                "a": {"tier1": {"provider": "auto"}},
                "b": {"tier1": {"provider": "auto"}},
            }
        }
        yaml_file = tmp_path / "modes.yaml"
        yaml_file.write_text(yaml.dump(cfg))
        router = ModelRouterPrimitive.from_yaml(yaml_file)
        assert set(router.modes.keys()) == {"a", "b"}


# ── execute — mode validation ─────────────────────────────────────────────────


class TestExecuteModeValidation:
    @pytest.mark.asyncio
    async def test_raises_value_error_for_unknown_mode(self):
        router = _make_router([])
        with pytest.raises(ValueError, match="Unknown routing mode"):
            await router.execute(
                ModelRouterRequest(mode="nonexistent", prompt="hi"),
                _ctx(),
            )

    @pytest.mark.asyncio
    async def test_error_message_lists_available_modes(self):
        router = _make_router([])
        with pytest.raises(ValueError, match="test"):
            await router.execute(
                ModelRouterRequest(mode="bad", prompt="hi"),
                _ctx(),
            )


# ── execute — ollama tier ─────────────────────────────────────────────────────


class TestExecuteOllamaTier:
    @pytest.mark.asyncio
    async def test_calls_ollama_and_returns_response(self):
        router = _make_router([RouterTierConfig(provider="ollama", model="llama3.2")])
        fake_ollama_resp = {"message": {"content": "ollama reply"}}
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value=fake_ollama_resp)
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="hello"),
                _ctx(),
            )

        assert result.content == "ollama reply"
        assert result.model == "llama3.2"
        assert result.provider == "ollama"

    @pytest.mark.asyncio
    async def test_ollama_tier_without_model_raises(self):
        router = _make_router([RouterTierConfig(provider="ollama", model=None)])
        with pytest.raises(RuntimeError, match=r"All .* tiers failed"):
            await router.execute(
                ModelRouterRequest(mode="test", prompt="hi"),
                _ctx(),
            )


# ── execute — openrouter tier ─────────────────────────────────────────────────


class TestExecuteOpenRouterTier:
    @pytest.mark.asyncio
    async def test_calls_openrouter_with_pinned_model(self):
        router = _make_router([RouterTierConfig(provider="openrouter", model="some/model:free")])
        fake_or_resp = {"choices": [{"message": {"content": "OR reply"}}]}
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value=fake_or_resp)
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="hello"),
                _ctx(),
            )

        assert result.content == "OR reply"
        assert result.model == "some/model:free"
        assert result.provider == "openrouter"

    @pytest.mark.asyncio
    async def test_openrouter_without_model_uses_tracker(self):
        tracker = MagicMock(spec=FreeModelTracker)
        tracker.recommend = AsyncMock(return_value="free/tracker-pick:free")

        router = _make_router(
            [RouterTierConfig(provider="openrouter", model=None)],
            tracker=tracker,
        )
        fake_or_resp = {"choices": [{"message": {"content": "tracked reply"}}]}
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value=fake_or_resp)
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="hi"),
                _ctx(),
            )

        assert result.model == "free/tracker-pick:free"
        tracker.recommend.assert_awaited_once()


# ── execute — auto tier ───────────────────────────────────────────────────────


class TestExecuteAutoTier:
    @pytest.mark.asyncio
    async def test_auto_uses_tracker_to_pick_model(self):
        tracker = MagicMock(spec=FreeModelTracker)
        tracker.recommend = AsyncMock(return_value="free/auto-pick:free")

        router = _make_router(
            [RouterTierConfig(provider="auto")],
            tracker=tracker,
        )
        fake_or_resp = {"choices": [{"message": {"content": "auto reply"}}]}
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value=fake_or_resp)
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="hi"),
                _ctx(),
            )

        assert result.content == "auto reply"
        assert result.model == "free/auto-pick:free"


# ── execute — tier fallback ───────────────────────────────────────────────────


class TestTierFallback:
    @pytest.mark.asyncio
    async def test_falls_through_to_next_tier_on_failure(self):
        """Tier 1 (Ollama) fails → should fall through to tier 2 (OpenRouter)."""
        tracker = MagicMock(spec=FreeModelTracker)
        tracker.recommend = AsyncMock(return_value=None)

        router = _make_router(
            [
                RouterTierConfig(provider="ollama", model="local-model"),
                RouterTierConfig(provider="openrouter", model="fallback:free"),
            ],
            tracker=tracker,
        )

        call_count = 0

        async def mock_post(url: str, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if "11434" in url:  # Ollama URL
                raise Exception("Ollama unavailable")
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            resp.json = MagicMock(
                return_value={"choices": [{"message": {"content": "fallback reply"}}]}
            )
            return resp

        mock_client = AsyncMock()
        mock_client.post = mock_post
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="hello"),
                _ctx(),
            )

        assert result.content == "fallback reply"
        assert result.model == "fallback:free"

    @pytest.mark.asyncio
    async def test_raises_runtime_error_when_all_tiers_fail(self):
        router = _make_router(
            [
                RouterTierConfig(provider="ollama", model="local"),
                RouterTierConfig(provider="openrouter", model="cloud:free"),
            ]
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("all fail"))
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_cm):
            with pytest.raises(RuntimeError, match=r"All .* tiers failed"):
                await router.execute(
                    ModelRouterRequest(mode="test", prompt="hi"),
                    _ctx(),
                )

    @pytest.mark.asyncio
    async def test_raises_runtime_error_when_no_tiers(self):
        router = _make_router([])
        with pytest.raises(RuntimeError, match="All 0 tiers failed"):
            await router.execute(
                ModelRouterRequest(mode="test", prompt="hi"),
                _ctx(),
            )


# ── tier_override ─────────────────────────────────────────────────────────────


class TestTierOverride:
    @pytest.mark.asyncio
    async def test_override_skips_to_specified_tier(self):
        """tier_override=2 should skip tier 1 (Ollama) and go straight to tier 2."""
        router = _make_router(
            [
                RouterTierConfig(provider="ollama", model="local"),
                RouterTierConfig(provider="openrouter", model="pinned:free"),
            ]
        )
        _, _mock_client, mock_cm = _mock_openai_compat_response("tier2 reply")

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="hi", tier_override=2),
                _ctx(),
            )

        assert result.content == "tier2 reply"
        assert result.model == "pinned:free"
        assert result.provider == "openrouter"

    @pytest.mark.asyncio
    async def test_override_out_of_range_raises_value_error(self):
        router = _make_router([RouterTierConfig(provider="ollama", model="m")])
        with pytest.raises(ValueError, match="tier_override=5 out of range"):
            await router.execute(
                ModelRouterRequest(mode="test", prompt="hi", tier_override=5),
                _ctx(),
            )


# ── unknown provider ──────────────────────────────────────────────────────────


class TestUnknownProvider:
    @pytest.mark.asyncio
    async def test_unknown_provider_raises_runtime_error(self):
        router = _make_router([RouterTierConfig(provider="magic-cloud")])
        with pytest.raises(RuntimeError, match="All 1 tiers failed"):
            await router.execute(
                ModelRouterRequest(mode="test", prompt="hi"),
                _ctx(),
            )


# ── execute — groq tier ───────────────────────────────────────────────────────


def _mock_openai_compat_response(content: str) -> tuple[Any, Any, Any]:
    """Return (mock_resp, mock_client, mock_cm) for OpenAI-compat endpoints."""
    fake_resp = {"choices": [{"message": {"content": content}}]}
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value=fake_resp)
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_cm = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=None)
    return mock_resp, mock_client, mock_cm


class TestExecuteGroqTier:
    @pytest.mark.asyncio
    async def test_calls_groq_with_pinned_model(self):
        router = ModelRouterPrimitive(
            {
                "test": RouterModeConfig(
                    tiers=[RouterTierConfig(provider="groq", model="llama-3.1-8b-instant")]
                )
            },
            groq_api_key="groq-key",  # pragma: allowlist secret
        )
        _, mock_client, mock_cm = _mock_openai_compat_response("groq reply")

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="hi"),
                _ctx(),
            )

        assert result.content == "groq reply"
        assert result.model == "llama-3.1-8b-instant"
        assert result.provider == "groq"
        call_args = mock_client.post.call_args
        assert "groq.com" in call_args[0][0]
        assert (
            call_args[1]["headers"]["Authorization"] == "Bearer groq-key"
        )  # pragma: allowlist secret

    @pytest.mark.asyncio
    async def test_groq_defaults_to_first_free_model_when_no_model(self):
        """When model is None for groq tier, falls back to _GROQ_FREE_MODELS[0]."""
        from ttadev.primitives.llm.model_router import _GROQ_FREE_MODELS

        router = ModelRouterPrimitive(
            {"test": RouterModeConfig(tiers=[RouterTierConfig(provider="groq", model=None)])},
            groq_api_key="groq-key",  # pragma: allowlist secret
        )
        _, _mock_client, mock_cm = _mock_openai_compat_response("groq default")

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="hi"),
                _ctx(),
            )

        assert result.model == _GROQ_FREE_MODELS[0]


# ── execute — together tier ───────────────────────────────────────────────────


class TestExecuteTogetherTier:
    @pytest.mark.asyncio
    async def test_calls_together_with_pinned_model(self):
        router = ModelRouterPrimitive(
            {
                "test": RouterModeConfig(
                    tiers=[
                        RouterTierConfig(provider="together", model="meta-llama/Llama-3-8b-chat-hf")
                    ]
                )
            },
            together_api_key="ta-key",  # pragma: allowlist secret
        )
        _, mock_client, mock_cm = _mock_openai_compat_response("together reply")

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="hi"),
                _ctx(),
            )

        assert result.content == "together reply"
        assert result.model == "meta-llama/Llama-3-8b-chat-hf"
        assert result.provider == "together"
        call_args = mock_client.post.call_args
        assert "together.xyz" in call_args[0][0]
        assert (
            call_args[1]["headers"]["Authorization"] == "Bearer ta-key"
        )  # pragma: allowlist secret

    @pytest.mark.asyncio
    async def test_together_without_model_raises(self):
        router = ModelRouterPrimitive(
            {"test": RouterModeConfig(tiers=[RouterTierConfig(provider="together", model=None)])},
            together_api_key="ta-key",  # pragma: allowlist secret
        )
        with pytest.raises(RuntimeError, match=r"All 1 tiers failed"):
            await router.execute(
                ModelRouterRequest(mode="test", prompt="hi"),
                _ctx(),
            )


# ── from_yaml — groq and together ─────────────────────────────────────────────


class TestFromYamlNewProviders:
    def test_parses_groq_and_together_tiers(self, tmp_path: Path):
        cfg = {
            "modes": {
                "chat": {
                    "tier1": {"provider": "groq", "model": "llama-3.1-8b-instant"},
                    "tier2": {"provider": "together", "model": "meta-llama/Llama-3-8b-chat-hf"},
                    "tier3": {"provider": "auto"},
                }
            }
        }
        p = tmp_path / "modes.yaml"
        p.write_text(yaml.dump(cfg))

        router = ModelRouterPrimitive.from_yaml(p)
        tiers = router.modes["chat"].tiers
        assert tiers[0].provider == "groq"
        assert tiers[0].model == "llama-3.1-8b-instant"
        assert tiers[1].provider == "together"
        assert tiers[1].model == "meta-llama/Llama-3-8b-chat-hf"
        assert tiers[2].provider == "auto"
        assert tiers[2].model is None


# ── Issue #283: Gemini models/ prefix ─────────────────────────────────────────


class TestGeminiModelsPrefix:
    """Gemini provider must always use the `models/` prefix (Issue #283)."""

    @pytest.mark.asyncio
    async def test_bare_model_id_gets_models_prefix(self):
        """A Gemini tier with a bare model ID (no `models/`) auto-prepends it."""
        router = ModelRouterPrimitive(
            {
                "test": RouterModeConfig(
                    tiers=[RouterTierConfig(provider="gemini", model="gemini-2.5-flash")]
                )
            },
            gemini_api_key="fake-key",  # pragma: allowlist secret
        )
        _, mock_client, mock_cm = _mock_openai_compat_response("gemini reply")

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="hello"),
                _ctx(),
            )

        # Model returned should have the prefix
        assert result.model == "models/gemini-2.5-flash"
        # The POST should have been called with the prefixed model in the payload
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["json"]["model"] == "models/gemini-2.5-flash"

    @pytest.mark.asyncio
    async def test_model_with_prefix_is_not_double_prefixed(self):
        """A Gemini tier with `models/gemini-…` already set is NOT double-prefixed."""
        router = ModelRouterPrimitive(
            {
                "test": RouterModeConfig(
                    tiers=[RouterTierConfig(provider="gemini", model="models/gemini-2.5-flash")]
                )
            },
            gemini_api_key="fake-key",  # pragma: allowlist secret
        )
        _, mock_client, mock_cm = _mock_openai_compat_response("gemini reply")

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="hello"),
                _ctx(),
            )

        assert result.model == "models/gemini-2.5-flash"
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["json"]["model"] == "models/gemini-2.5-flash"

    @pytest.mark.asyncio
    async def test_default_gemini_model_has_prefix(self):
        """When no model is specified for a Gemini tier, the default includes `models/`."""
        from ttadev.primitives.llm.providers import PROVIDERS

        router = ModelRouterPrimitive(
            {"test": RouterModeConfig(tiers=[RouterTierConfig(provider="gemini")])},
            gemini_api_key="fake-key",  # pragma: allowlist secret
        )
        _, mock_client, mock_cm = _mock_openai_compat_response("gemini default reply")

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="hello"),
                _ctx(),
            )

        default = PROVIDERS["gemini"].default_model
        assert default.startswith("models/"), (
            f"providers.py default_model should have prefix: {default!r}"
        )
        assert result.model == default


# ── Issue #284: Strip <think> reasoning tokens ────────────────────────────────


class TestStripThinking:
    """Per-tier strip_thinking flag removes <think>…</think> blocks (Issue #284)."""

    @pytest.mark.asyncio
    async def test_think_blocks_stripped_when_strip_thinking_true(self):
        """<think>…</think> block is removed from content when strip_thinking=True."""
        raw = "<think>let me reason step by step</think>\nThe answer is 42."
        router = _make_router(
            [RouterTierConfig(provider="openrouter", model="some/model:free", strip_thinking=True)]
        )
        _, _, mock_cm = _mock_openai_compat_response(raw)

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="what is the answer?"),
                _ctx(),
            )

        assert "<think>" not in result.content
        assert result.content == "The answer is 42."

    @pytest.mark.asyncio
    async def test_think_blocks_not_stripped_when_strip_thinking_false(self):
        """<think>…</think> block is preserved when strip_thinking=False."""
        raw = "<think>internal reasoning</think>Final answer."
        router = _make_router(
            [RouterTierConfig(provider="openrouter", model="some/model:free", strip_thinking=False)]
        )
        _, _, mock_cm = _mock_openai_compat_response(raw)

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="hi"),
                _ctx(),
            )

        assert "<think>" in result.content
        assert result.content == raw

    @pytest.mark.asyncio
    async def test_strip_thinking_is_noop_on_normal_response(self):
        """strip_thinking=True is a no-op when content has no <think> blocks."""
        normal = "Hello! How can I help you today?"
        router = _make_router(
            [RouterTierConfig(provider="openrouter", model="m:free", strip_thinking=True)]
        )
        _, _, mock_cm = _mock_openai_compat_response(normal)

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="greet me"),
                _ctx(),
            )

        assert result.content == normal

    @pytest.mark.asyncio
    async def test_strip_thinking_default_is_true(self):
        """RouterTierConfig.strip_thinking defaults to True."""
        tier = RouterTierConfig(provider="groq")
        assert tier.strip_thinking is True

    @pytest.mark.asyncio
    async def test_multiline_think_block_stripped(self):
        """Multi-line <think>…</think> blocks spanning newlines are stripped."""
        raw = "<think>\nStep 1: consider the options.\nStep 2: choose best.\n</think>\nResult: B."
        router = _make_router(
            [RouterTierConfig(provider="openrouter", model="m:free", strip_thinking=True)]
        )
        _, _, mock_cm = _mock_openai_compat_response(raw)

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="choose"),
                _ctx(),
            )

        assert result.content == "Result: B."


# ── Issue #285: Per-tier rate-limit cooldown ──────────────────────────────────


class TestTierCooldown:
    """Per-tier 429 cooldown skips throttled tiers for N seconds (Issue #285)."""

    @pytest.mark.asyncio
    async def test_tier_in_cooldown_is_skipped(self):
        """A tier that received a 429 is skipped during the cooldown window."""
        # Arrange: two tiers; tier1 is pre-marked as cooling
        router = _make_router(
            [
                RouterTierConfig(provider="groq", model="llama-3.1-8b-instant"),
                RouterTierConfig(provider="openrouter", model="fallback:free"),
            ],
            tier_cooldown_seconds=30,
        )
        # Manually put tier1 into cooldown
        router._mark_cooling("groq/llama-3.1-8b-instant")

        _, _, mock_cm = _mock_openai_compat_response("fallback reply")

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="hi"),
                _ctx(),
            )

        # Should have gone straight to tier2 (openrouter/fallback:free)
        assert result.content == "fallback reply"
        assert result.provider == "openrouter"

    @pytest.mark.asyncio
    async def test_429_response_triggers_cooldown(self):
        """A 429 HTTPStatusError from a tier marks it as cooling."""
        router = _make_router(
            [
                RouterTierConfig(provider="groq", model="llama-3.1-8b-instant"),
                RouterTierConfig(provider="openrouter", model="fallback:free"),
            ],
            tier_cooldown_seconds=30,
        )

        # First call to groq raises 429; fallback succeeds
        or_resp_data = {"choices": [{"message": {"content": "or reply"}}]}

        call_count = 0

        async def mock_post(url: str, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if "groq.com" in url:
                # Build a fake httpx 429 response
                fake_request = MagicMock()
                fake_response = MagicMock()
                fake_response.status_code = 429
                raise httpx.HTTPStatusError(
                    "429 Too Many Requests", request=fake_request, response=fake_response
                )
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            resp.json = MagicMock(return_value=or_resp_data)
            return resp

        mock_client = AsyncMock()
        mock_client.post = mock_post
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await router.execute(
                ModelRouterRequest(mode="test", prompt="hi"),
                _ctx(),
            )

        assert result.content == "or reply"
        # Groq tier should now be in cooldown
        assert router._is_cooling("groq/llama-3.1-8b-instant")

    @pytest.mark.asyncio
    async def test_cooldown_expires_after_timeout(self):
        """After the cooldown window passes, the tier is available again."""
        import time as _time

        router = _make_router(
            [RouterTierConfig(provider="groq", model="llama-3.1-8b-instant")],
            tier_cooldown_seconds=30,
        )
        tier_key = "groq/llama-3.1-8b-instant"
        router._mark_cooling(tier_key)

        # Should be cooling now
        assert router._is_cooling(tier_key)

        # Mock monotonic to be 60 seconds in the future (past the 30s window)
        with patch("ttadev.primitives.llm.model_router.time") as mock_time:
            mock_time.monotonic.return_value = _time.monotonic() + 60
            assert not router._is_cooling(tier_key)

    @pytest.mark.asyncio
    async def test_cooldown_disabled_when_seconds_zero(self):
        """tier_cooldown_seconds=0 disables cooldown entirely."""
        router = _make_router(
            [RouterTierConfig(provider="groq", model="llama-3.1-8b-instant")],
            tier_cooldown_seconds=0,
        )
        tier_key = "groq/llama-3.1-8b-instant"
        router._mark_cooling(tier_key)
        # With cooldown disabled, should never report as cooling
        assert not router._is_cooling(tier_key)

    @pytest.mark.asyncio
    async def test_cooldown_state_is_instance_level_not_shared(self):
        """Two separate router instances have independent cooldown state."""
        router_a = _make_router(
            [RouterTierConfig(provider="groq", model="model-x")],
            tier_cooldown_seconds=30,
        )
        router_b = _make_router(
            [RouterTierConfig(provider="groq", model="model-x")],
            tier_cooldown_seconds=30,
        )

        router_a._mark_cooling("groq/model-x")

        assert router_a._is_cooling("groq/model-x")
        assert not router_b._is_cooling("groq/model-x")
