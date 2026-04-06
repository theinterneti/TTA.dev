"""Tests for SmartRouterPrimitive and AgentRouterPrimitive zero-config defaults."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.agents.router import AgentRouterPrimitive
from ttadev.agents.task import AgentResult, AgentTask
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.llm.model_router import RouterTierConfig
from ttadev.primitives.llm.smart_router import LiteLLMSmartAdapter, SmartRouterPrimitive

# ---------------------------------------------------------------------------
# SmartRouterPrimitive tests
# ---------------------------------------------------------------------------


class TestSmartRouterBuild:
    """SmartRouterPrimitive.build() returns a LiteLLMSmartAdapter."""

    def test_build_returns_litellm_smart_adapter(self):
        router = SmartRouterPrimitive().build()
        assert isinstance(router, LiteLLMSmartAdapter)

    def test_make_classmethod_returns_litellm_smart_adapter(self):
        router = SmartRouterPrimitive.make()
        assert isinstance(router, LiteLLMSmartAdapter)

    def test_default_mode_name(self):
        router = SmartRouterPrimitive().build()
        assert "default" in router.modes

    def test_custom_mode_name(self):
        router = SmartRouterPrimitive(mode="coding").build()
        assert "coding" in router.modes

    def test_ollama_always_present(self):
        """Ollama tier is always included regardless of env vars."""
        with patch.dict("os.environ", {}, clear=True):
            router = SmartRouterPrimitive().build()
        tiers = router.modes["default"].tiers
        providers = [t.provider for t in tiers]
        assert "ollama" in providers

    def test_ollama_is_last_tier(self):
        """Ollama is always the final fallback."""
        with patch.dict("os.environ", {}, clear=True):
            router = SmartRouterPrimitive().build()
        last_tier = router.modes["default"].tiers[-1]
        assert last_tier.provider == "ollama"

    def test_groq_added_when_key_present(self):
        env = {"GROQ_API_KEY": "sk-test"}
        with patch.dict("os.environ", env, clear=False):
            router = SmartRouterPrimitive().build()
        providers = [t.provider for t in router.modes["default"].tiers]
        assert "groq" in providers

    def test_groq_not_added_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            router = SmartRouterPrimitive().build()
        providers = [t.provider for t in router.modes["default"].tiers]
        assert "groq" not in providers

    def test_google_added_when_key_present(self):
        env = {"GOOGLE_API_KEY": "AIza-test"}
        with patch.dict("os.environ", env, clear=False):
            router = SmartRouterPrimitive().build()
        providers = [t.provider for t in router.modes["default"].tiers]
        assert "google" in providers

    def test_google_not_added_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            router = SmartRouterPrimitive().build()
        providers = [t.provider for t in router.modes["default"].tiers]
        assert "google" not in providers

    def test_openrouter_added_when_key_present(self):
        env = {"OPENROUTER_API_KEY": "sk-or-test"}
        with patch.dict("os.environ", env, clear=False):
            router = SmartRouterPrimitive().build()
        providers = [t.provider for t in router.modes["default"].tiers]
        assert "openrouter" in providers

    def test_openrouter_not_added_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            router = SmartRouterPrimitive().build()
        providers = [t.provider for t in router.modes["default"].tiers]
        assert "openrouter" not in providers

    def test_cascade_order_all_keys(self):
        """Groq → Google → OpenRouter → Ollama when all keys present."""
        env = {
            "GROQ_API_KEY": "sk-g",
            "GOOGLE_API_KEY": "AIza",
            "OPENROUTER_API_KEY": "sk-or",
        }
        with patch.dict("os.environ", env, clear=False):
            router = SmartRouterPrimitive().build()
        providers = [t.provider for t in router.modes["default"].tiers]
        assert providers == ["groq", "google", "openrouter", "ollama"]

    def test_cascade_order_no_keys(self):
        """Only Ollama when no keys present."""
        with patch.dict("os.environ", {}, clear=True):
            router = SmartRouterPrimitive().build()
        providers = [t.provider for t in router.modes["default"].tiers]
        assert providers == ["ollama"]

    def test_custom_or_free_model(self):
        env = {"OPENROUTER_API_KEY": "sk-or"}
        with patch.dict("os.environ", env, clear=False):
            router = SmartRouterPrimitive(
                or_free_model="meta-llama/llama-3.3-70b-instruct:free"
            ).build()
        tiers = router.modes["default"].tiers
        or_tier = next(t for t in tiers if t.provider == "openrouter")
        assert or_tier.model == "meta-llama/llama-3.3-70b-instruct:free"

    def test_tiers_are_router_tier_configs(self):
        router = SmartRouterPrimitive().build()
        for tier in router.modes["default"].tiers:
            assert isinstance(tier, RouterTierConfig)

    def test_adapter_has_execute_method(self):
        """LiteLLMSmartAdapter exposes the execute() interface."""
        router = SmartRouterPrimitive().build()
        assert hasattr(router, "execute")
        import asyncio

        assert asyncio.iscoroutinefunction(router.execute)


# ---------------------------------------------------------------------------
# LiteLLMSmartAdapter unit tests
# ---------------------------------------------------------------------------


class TestLiteLLMSmartAdapter:
    """Unit tests for LiteLLMSmartAdapter delegation to LiteLLMPrimitive."""

    @pytest.mark.asyncio
    async def test_execute_delegates_to_litellm(self):
        """execute() calls LiteLLMPrimitive.execute() with translated LLMRequest."""
        from unittest.mock import AsyncMock, patch

        from ttadev.primitives.llm.model_router import RouterModeConfig, RouterTierConfig
        from ttadev.primitives.llm.smart_router import LiteLLMSmartAdapter
        from ttadev.primitives.llm.universal_llm_primitive import LLMResponse

        modes = {
            "default": RouterModeConfig(
                tiers=[RouterTierConfig(provider="groq", model="llama-3.3-70b-versatile")]
            )
        }
        adapter = LiteLLMSmartAdapter(modes=modes)

        fake_response = LLMResponse(
            content="Hello from litellm",
            model="groq/llama-3.3-70b-versatile",
            provider="groq",
        )

        ctx = WorkflowContext(workflow_id="test-litellm-delegation")
        from ttadev.primitives.llm.model_router import ModelRouterRequest

        request = ModelRouterRequest(mode="default", prompt="Hi!")

        with patch.object(
            adapter._mode_primitives["default"][1],
            "execute",
            new=AsyncMock(return_value=fake_response),
        ) as mock_exec:
            result = await adapter.execute(request, ctx)

        mock_exec.assert_called_once()
        call_args = mock_exec.call_args[0]
        llm_req = call_args[0]
        assert llm_req.model == "groq/llama-3.3-70b-versatile"
        assert llm_req.messages == [{"role": "user", "content": "Hi!"}]
        assert result.content == "Hello from litellm"

    @pytest.mark.asyncio
    async def test_execute_passes_system_prompt(self):
        """System prompt from ModelRouterRequest is forwarded to LLMRequest."""
        from unittest.mock import AsyncMock, patch

        from ttadev.primitives.llm.model_router import (
            ModelRouterRequest,
            RouterModeConfig,
            RouterTierConfig,
        )
        from ttadev.primitives.llm.smart_router import LiteLLMSmartAdapter
        from ttadev.primitives.llm.universal_llm_primitive import LLMResponse

        modes = {
            "default": RouterModeConfig(
                tiers=[RouterTierConfig(provider="ollama", model="qwen2.5:7b")]
            )
        }
        adapter = LiteLLMSmartAdapter(modes=modes)
        fake_response = LLMResponse(content="ok", model="ollama/qwen2.5:7b", provider="ollama")
        ctx = WorkflowContext(workflow_id="test-system")
        request = ModelRouterRequest(mode="default", prompt="task", system="You are helpful.")

        with patch.object(
            adapter._mode_primitives["default"][1],
            "execute",
            new=AsyncMock(return_value=fake_response),
        ) as mock_exec:
            await adapter.execute(request, ctx)

        llm_req = mock_exec.call_args[0][0]
        assert llm_req.system == "You are helpful."

    @pytest.mark.asyncio
    async def test_execute_raises_on_unknown_mode(self):
        """KeyError raised when mode is not in modes dict."""
        from ttadev.primitives.llm.model_router import (
            ModelRouterRequest,
            RouterModeConfig,
            RouterTierConfig,
        )
        from ttadev.primitives.llm.smart_router import LiteLLMSmartAdapter

        modes = {
            "default": RouterModeConfig(
                tiers=[RouterTierConfig(provider="ollama", model="qwen2.5:7b")]
            )
        }
        adapter = LiteLLMSmartAdapter(modes=modes)
        ctx = WorkflowContext(workflow_id="test-unknown")
        request = ModelRouterRequest(mode="nonexistent", prompt="Hi")

        with pytest.raises(KeyError, match="nonexistent"):
            await adapter.execute(request, ctx)

    def test_mode_primitives_prebuilt_for_each_mode(self):
        """_mode_primitives is populated at init time for each mode."""
        from ttadev.primitives.llm.model_router import RouterModeConfig, RouterTierConfig
        from ttadev.primitives.llm.smart_router import LiteLLMSmartAdapter

        modes = {
            "default": RouterModeConfig(
                tiers=[RouterTierConfig(provider="groq", model="llama-3.3-70b-versatile")]
            ),
            "coding": RouterModeConfig(
                tiers=[RouterTierConfig(provider="ollama", model="qwen2.5:7b")]
            ),
        }
        adapter = LiteLLMSmartAdapter(modes=modes)
        assert "default" in adapter._mode_primitives
        assert "coding" in adapter._mode_primitives

    def test_litellm_model_string_groq(self):
        """Groq tier resolves to 'groq/<model>' litellm string."""
        from ttadev.primitives.llm.model_router import RouterTierConfig
        from ttadev.primitives.llm.smart_router import _tier_to_litellm_model

        tier = RouterTierConfig(provider="groq", model="llama-3.3-70b-versatile")
        assert _tier_to_litellm_model(tier) == "groq/llama-3.3-70b-versatile"

    def test_litellm_model_string_google_default(self):
        """Google tier without explicit model resolves to gemini default."""
        from ttadev.primitives.llm.model_router import RouterTierConfig
        from ttadev.primitives.llm.smart_router import _tier_to_litellm_model

        tier = RouterTierConfig(provider="google")
        result = _tier_to_litellm_model(tier)
        assert result is not None
        assert result.startswith("gemini/")

    def test_litellm_model_string_openrouter(self):
        """OpenRouter tier prepends 'openrouter/' prefix."""
        from ttadev.primitives.llm.model_router import RouterTierConfig
        from ttadev.primitives.llm.smart_router import _tier_to_litellm_model

        tier = RouterTierConfig(provider="openrouter", model="google/gemma-3-27b-it:free")
        assert _tier_to_litellm_model(tier) == "openrouter/google/gemma-3-27b-it:free"

    def test_litellm_model_string_ollama(self):
        """Ollama tier prepends 'ollama/' prefix."""
        from ttadev.primitives.llm.model_router import RouterTierConfig
        from ttadev.primitives.llm.smart_router import _tier_to_litellm_model

        tier = RouterTierConfig(provider="ollama", model="llama3.2")
        assert _tier_to_litellm_model(tier) == "ollama/llama3.2"

    def test_litellm_fallbacks_set_from_tier_order(self):
        """Fallbacks passed to LiteLLMPrimitive match tiers[1:]."""
        from ttadev.primitives.llm.model_router import RouterModeConfig, RouterTierConfig
        from ttadev.primitives.llm.smart_router import LiteLLMSmartAdapter, _tier_to_litellm_model

        tiers = [
            RouterTierConfig(provider="groq", model="llama-3.3-70b-versatile"),
            RouterTierConfig(provider="google"),
            RouterTierConfig(provider="ollama"),
        ]
        modes = {"default": RouterModeConfig(tiers=tiers)}
        adapter = LiteLLMSmartAdapter(modes=modes)

        primary, litellm_prim = adapter._mode_primitives["default"]
        assert primary == "groq/llama-3.3-70b-versatile"
        # fallbacks should be the remaining tiers
        expected_fallbacks = [
            _tier_to_litellm_model(tiers[1]),
            _tier_to_litellm_model(tiers[2]),
        ]
        assert litellm_prim._fallbacks == expected_fallbacks

    @pytest.mark.asyncio
    async def test_think_tokens_stripped(self):
        """<think>...</think> blocks are stripped from the response content."""
        from unittest.mock import AsyncMock, patch

        from ttadev.primitives.llm.model_router import (
            ModelRouterRequest,
            RouterModeConfig,
            RouterTierConfig,
        )
        from ttadev.primitives.llm.smart_router import LiteLLMSmartAdapter
        from ttadev.primitives.llm.universal_llm_primitive import LLMResponse

        modes = {
            "default": RouterModeConfig(
                tiers=[RouterTierConfig(provider="groq", model="qwen3-32b", strip_thinking=True)]
            )
        }
        adapter = LiteLLMSmartAdapter(modes=modes)
        raw_response = LLMResponse(
            content="<think>internal reasoning</think>Final answer",
            model="groq/qwen3-32b",
            provider="groq",
        )
        ctx = WorkflowContext(workflow_id="test-think")
        request = ModelRouterRequest(mode="default", prompt="Solve it")

        with patch.object(
            adapter._mode_primitives["default"][1],
            "execute",
            new=AsyncMock(return_value=raw_response),
        ):
            result = await adapter.execute(request, ctx)

        assert "<think>" not in result.content
        assert result.content == "Final answer"


# ---------------------------------------------------------------------------
# AgentRouterPrimitive zero-config tests
# ---------------------------------------------------------------------------


class TestAgentRouterDefaultModel:
    """AgentRouterPrimitive accepts model=None and builds SmartRouter."""

    def test_init_with_no_args(self):
        """Should construct without error."""
        router = AgentRouterPrimitive()
        assert router is not None

    def test_init_model_none_by_default(self):
        router = AgentRouterPrimitive()
        assert router._model is None

    def test_init_orchestrator_none_by_default(self):
        router = AgentRouterPrimitive()
        assert router._orchestrator is None

    def test_get_model_returns_adapter_when_model_none(self):
        from ttadev.agents.adapter import ModelRouterChatAdapter

        router = AgentRouterPrimitive()
        model = router._get_model()
        assert isinstance(model, ModelRouterChatAdapter)

    def test_get_orchestrator_reuses_model_when_none(self):
        """When orchestrator is None, falls back to the same model."""
        router = AgentRouterPrimitive()
        # Both calls should return a ChatPrimitive-compatible object
        model = router._get_model()
        orch = router._get_orchestrator()
        # Both come from SmartRouter — just verify they're chat-compatible
        assert hasattr(model, "chat")
        assert hasattr(orch, "chat")

    def test_explicit_model_preserved(self):
        mock_model = MagicMock()
        mock_model.chat = AsyncMock(return_value="ok")
        router = AgentRouterPrimitive(model=mock_model)
        assert router._get_model() is mock_model

    def test_explicit_orchestrator_preserved(self):
        mock_orch = MagicMock()
        mock_orch.chat = AsyncMock(return_value="ok")
        router = AgentRouterPrimitive(orchestrator=mock_orch)
        assert router._get_orchestrator() is mock_orch


# ---------------------------------------------------------------------------
# _resolve_default_model integration test
# ---------------------------------------------------------------------------


class TestResolveDefaultModel:
    """_resolve_default_model now uses SmartRouterPrimitive."""

    def test_returns_chat_primitive_compatible_object(self):
        from ttadev.primitives.core.base import _resolve_default_model

        model = _resolve_default_model()
        assert hasattr(model, "chat")

    def test_returns_model_router_chat_adapter(self):
        from ttadev.agents.adapter import ModelRouterChatAdapter
        from ttadev.primitives.core.base import _resolve_default_model

        model = _resolve_default_model()
        assert isinstance(model, ModelRouterChatAdapter)


# ---------------------------------------------------------------------------
# AgentRouterPrimitive routing logic (smoke test with mocked model)
# ---------------------------------------------------------------------------


class TestAgentRouterRoutingWithMockModel:
    """Routing logic works correctly when model is injected."""

    @pytest.mark.asyncio
    async def test_agent_hint_short_circuits(self):
        """agent_hint bypasses keyword scoring and LLM call."""
        mock_model = MagicMock()
        mock_model.chat = AsyncMock(return_value="some-agent")

        mock_agent_instance = MagicMock()
        mock_agent_instance.execute = AsyncMock(
            return_value=AgentResult(
                agent_name="test-agent",
                response="done",
                artifacts=[],
                suggestions=[],
                spawned_agents=[],
                quality_gates_passed=True,
                confidence=1.0,
            )
        )

        mock_agent_class = MagicMock(return_value=mock_agent_instance)

        mock_registry = MagicMock()
        mock_registry.all.return_value = []
        mock_registry.get.return_value = mock_agent_class

        router = AgentRouterPrimitive(model=mock_model, registry=mock_registry)
        task = AgentTask(instruction="test", context={}, constraints=[], agent_hint="test-agent")
        ctx = WorkflowContext(workflow_id="test")

        result = await router.execute(task, ctx)

        mock_registry.get.assert_called_with("test-agent")
        assert result.response == "done"

    @pytest.mark.asyncio
    async def test_no_agents_registered_raises(self):
        """RuntimeError when registry is empty and LLM fallback tries to dispatch."""
        mock_model = MagicMock()
        mock_model.chat = AsyncMock(return_value="unknown-agent")

        mock_registry = MagicMock()
        mock_registry.all.return_value = []
        mock_registry.get.side_effect = KeyError("unknown-agent")

        router = AgentRouterPrimitive(
            model=mock_model, orchestrator=mock_model, registry=mock_registry
        )
        task = AgentTask(instruction="do something", context={}, constraints=[])
        ctx = WorkflowContext(workflow_id="test")

        with pytest.raises(RuntimeError, match="No agents registered"):
            await router.execute(task, ctx)
