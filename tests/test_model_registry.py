"""Tests for ModelRegistryPrimitive.

All tests are self-contained with no external dependencies.
Time-sensitive tests use unittest.mock.patch to control ``time.time``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.llm.model_registry import (
    ModelEntry,
    ModelRegistryPrimitive,
    RegistryRequest,
    RegistryResponse,
    SelectionPolicy,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="test-model-registry")


def _registry(**kwargs) -> ModelRegistryPrimitive:
    """Create a fresh registry; defaults to prepopulate=False for test isolation."""
    kwargs.setdefault("prepopulate", False)
    return ModelRegistryPrimitive(**kwargs)


def _entry(
    model_id: str = "test-model",
    provider: str = "ollama",
    is_local: bool = False,
    cost_tier: str = "free",
    supports_tool_calling: bool = False,
    supports_vision: bool = False,
    last_seen: float = 0.0,
) -> ModelEntry:
    return ModelEntry(
        model_id=model_id,
        provider=provider,
        is_local=is_local,
        cost_tier=cost_tier,
        supports_tool_calling=supports_tool_calling,
        supports_vision=supports_vision,
        last_seen=last_seen,
    )


# ── Register and Get ──────────────────────────────────────────────────────────


class TestRegisterAndGet:
    @pytest.mark.asyncio
    async def test_register_and_get(self) -> None:
        """Arrange: fresh registry → register model → get it back."""
        reg = _registry()
        ctx = _ctx()
        entry = _entry(model_id="llama3.2:latest", provider="ollama", is_local=True)

        reg_resp = await reg.execute(RegistryRequest(action="register", entry=entry), ctx)
        assert isinstance(reg_resp, RegistryResponse)
        assert reg_resp.registered is True

        get_resp = await reg.execute(
            RegistryRequest(action="get", provider="ollama", model_id="llama3.2:latest"), ctx
        )
        assert get_resp.entry is not None
        assert get_resp.entry.model_id == "llama3.2:latest"
        assert get_resp.entry.provider == "ollama"
        assert get_resp.entry.is_local is True

    @pytest.mark.asyncio
    async def test_register_updates_existing(self) -> None:
        """Re-registering an entry replaces it in-place."""
        reg = _registry()
        ctx = _ctx()
        await reg.execute(
            RegistryRequest(action="register", entry=_entry(model_id="m", provider="groq")), ctx
        )
        updated = _entry(model_id="m", provider="groq", cost_tier="low")
        await reg.execute(RegistryRequest(action="register", entry=updated), ctx)

        get_resp = await reg.execute(
            RegistryRequest(action="get", provider="groq", model_id="m"), ctx
        )
        assert get_resp.entry is not None
        assert get_resp.entry.cost_tier == "low"

    @pytest.mark.asyncio
    async def test_get_missing_returns_none(self) -> None:
        """Getting a model that was never registered returns entry=None."""
        reg = _registry()
        ctx = _ctx()
        resp = await reg.execute(
            RegistryRequest(action="get", provider="openai", model_id="nonexistent"), ctx
        )
        assert resp.entry is None

    @pytest.mark.asyncio
    async def test_register_without_entry_is_error(self) -> None:
        """Calling register with no entry returns registered=False and an error."""
        reg = _registry()
        ctx = _ctx()
        resp = await reg.execute(RegistryRequest(action="register"), ctx)
        assert resp.registered is False
        assert resp.error is not None


# ── List ──────────────────────────────────────────────────────────────────────


class TestListAll:
    @pytest.mark.asyncio
    async def test_list_all(self) -> None:
        """Three registered models → list returns all three."""
        reg = _registry()
        ctx = _ctx()
        for i in range(3):
            await reg.execute(
                RegistryRequest(action="register", entry=_entry(model_id=f"m{i}", provider="groq")),
                ctx,
            )
        resp = await reg.execute(RegistryRequest(action="list"), ctx)
        assert isinstance(resp.entries, list)
        assert len(resp.entries) == 3

    @pytest.mark.asyncio
    async def test_list_empty_on_fresh_no_prepopulate(self) -> None:
        """Without prepopulation, list returns empty."""
        reg = _registry()
        ctx = _ctx()
        resp = await reg.execute(RegistryRequest(action="list"), ctx)
        assert resp.entries == []

    @pytest.mark.asyncio
    async def test_list_returns_registry_response(self) -> None:
        """list action returns a RegistryResponse with action echoed."""
        reg = _registry()
        ctx = _ctx()
        resp = await reg.execute(RegistryRequest(action="list"), ctx)
        assert isinstance(resp, RegistryResponse)
        assert resp.action == "list"


class TestListFilterByProvider:
    @pytest.mark.asyncio
    async def test_list_filter_by_provider(self) -> None:
        """Filter by provider returns only matching entries."""
        reg = _registry()
        ctx = _ctx()
        await reg.execute(
            RegistryRequest(action="register", entry=_entry(model_id="m1", provider="groq")), ctx
        )
        await reg.execute(
            RegistryRequest(action="register", entry=_entry(model_id="m2", provider="openai")),
            ctx,
        )
        await reg.execute(
            RegistryRequest(action="register", entry=_entry(model_id="m3", provider="groq")), ctx
        )

        resp = await reg.execute(RegistryRequest(action="list", filter_provider="groq"), ctx)
        assert len(resp.entries) == 2
        assert all(e.provider == "groq" for e in resp.entries)

    @pytest.mark.asyncio
    async def test_list_filter_by_provider_no_match(self) -> None:
        """Filtering by a provider with no entries returns empty list."""
        reg = _registry()
        ctx = _ctx()
        await reg.execute(
            RegistryRequest(action="register", entry=_entry(model_id="m1", provider="groq")), ctx
        )
        resp = await reg.execute(RegistryRequest(action="list", filter_provider="anthropic"), ctx)
        assert resp.entries == []


class TestListFilterByCostTier:
    @pytest.mark.asyncio
    async def test_list_filter_by_cost_tier(self) -> None:
        """Filter by cost_tier returns only entries with that exact tier."""
        reg = _registry()
        ctx = _ctx()
        for tier, mid in [("free", "free-m"), ("low", "low-m"), ("high", "high-m")]:
            await reg.execute(
                RegistryRequest(action="register", entry=_entry(model_id=mid, cost_tier=tier)),
                ctx,
            )

        resp = await reg.execute(RegistryRequest(action="list", filter_cost_tier="free"), ctx)
        assert len(resp.entries) == 1
        assert resp.entries[0].model_id == "free-m"

    @pytest.mark.asyncio
    async def test_list_filter_by_cost_tier_low(self) -> None:
        """filter_cost_tier='low' is exact — does not include 'free'."""
        reg = _registry()
        ctx = _ctx()
        await reg.execute(
            RegistryRequest(action="register", entry=_entry(model_id="f", cost_tier="free")), ctx
        )
        await reg.execute(
            RegistryRequest(action="register", entry=_entry(model_id="l", cost_tier="low")), ctx
        )

        resp = await reg.execute(RegistryRequest(action="list", filter_cost_tier="low"), ctx)
        assert len(resp.entries) == 1
        assert resp.entries[0].model_id == "l"


class TestListFilterByCapability:
    @pytest.mark.asyncio
    async def test_list_filter_by_capability_tool_calling(self) -> None:
        """filter_tool_calling=True returns only tool-calling models."""
        reg = _registry()
        ctx = _ctx()
        await reg.execute(
            RegistryRequest(
                action="register",
                entry=_entry(model_id="tool-model", supports_tool_calling=True),
            ),
            ctx,
        )
        await reg.execute(
            RegistryRequest(
                action="register",
                entry=_entry(model_id="no-tool-model", supports_tool_calling=False),
            ),
            ctx,
        )

        resp = await reg.execute(RegistryRequest(action="list", filter_tool_calling=True), ctx)
        assert len(resp.entries) == 1
        assert resp.entries[0].model_id == "tool-model"
        assert resp.entries[0].supports_tool_calling is True

    @pytest.mark.asyncio
    async def test_list_filter_by_capability_vision(self) -> None:
        """filter_vision=True returns only vision-capable models."""
        reg = _registry()
        ctx = _ctx()
        await reg.execute(
            RegistryRequest(
                action="register",
                entry=_entry(model_id="vision-model", supports_vision=True),
            ),
            ctx,
        )
        await reg.execute(
            RegistryRequest(
                action="register",
                entry=_entry(model_id="text-only-model", supports_vision=False),
            ),
            ctx,
        )

        resp = await reg.execute(RegistryRequest(action="list", filter_vision=True), ctx)
        assert len(resp.entries) == 1
        assert resp.entries[0].model_id == "vision-model"

    @pytest.mark.asyncio
    async def test_list_combined_capability_filters(self) -> None:
        """Combining tool_calling + vision filters is AND semantics."""
        reg = _registry()
        ctx = _ctx()
        # Has both
        await reg.execute(
            RegistryRequest(
                action="register",
                entry=ModelEntry(
                    model_id="both",
                    provider="openai",
                    supports_tool_calling=True,
                    supports_vision=True,
                    cost_tier="low",
                ),
            ),
            ctx,
        )
        # Only tool calling
        await reg.execute(
            RegistryRequest(
                action="register",
                entry=ModelEntry(
                    model_id="tools-only",
                    provider="groq",
                    supports_tool_calling=True,
                    supports_vision=False,
                    cost_tier="free",
                ),
            ),
            ctx,
        )

        resp = await reg.execute(
            RegistryRequest(action="list", filter_tool_calling=True, filter_vision=True), ctx
        )
        assert len(resp.entries) == 1
        assert resp.entries[0].model_id == "both"


# ── Select ────────────────────────────────────────────────────────────────────


class TestSelectPrefersLocal:
    @pytest.mark.asyncio
    async def test_select_prefers_local(self) -> None:
        """Policy with prefer_local=True picks Ollama over cloud."""
        reg = _registry()
        ctx = _ctx()
        await reg.execute(
            RegistryRequest(
                action="register",
                entry=_entry(model_id="gpt-4o-mini", provider="openai", cost_tier="low"),
            ),
            ctx,
        )
        await reg.execute(
            RegistryRequest(
                action="register",
                entry=_entry(
                    model_id="llama3.2:latest",
                    provider="ollama",
                    is_local=True,
                    cost_tier="free",
                ),
            ),
            ctx,
        )

        resp = await reg.execute(
            RegistryRequest(
                action="select",
                policy=SelectionPolicy(prefer_local=True, max_cost_tier="high"),
            ),
            ctx,
        )
        assert resp.entry is not None
        assert resp.entry.is_local is True
        assert resp.entry.provider == "ollama"

    @pytest.mark.asyncio
    async def test_select_prefers_local_false_uses_cost_ordering(self) -> None:
        """prefer_local=False: locality not considered; cost tier wins."""
        reg = _registry()
        ctx = _ctx()
        await reg.execute(
            RegistryRequest(
                action="register",
                entry=_entry(model_id="cloud-free", provider="groq", cost_tier="free"),
            ),
            ctx,
        )
        await reg.execute(
            RegistryRequest(
                action="register",
                entry=_entry(
                    model_id="local-free", provider="ollama", is_local=True, cost_tier="free"
                ),
            ),
            ctx,
        )

        # With prefer_local=False both have same cost tier — either could win
        resp = await reg.execute(
            RegistryRequest(
                action="select",
                policy=SelectionPolicy(prefer_local=False, max_cost_tier="high"),
            ),
            ctx,
        )
        assert resp.entry is not None
        assert resp.entry.cost_tier == "free"


class TestSelectMaxCostTierFilters:
    @pytest.mark.asyncio
    async def test_select_max_cost_tier_filters(self) -> None:
        """High-cost model is excluded when max_cost_tier='low'."""
        reg = _registry()
        ctx = _ctx()
        await reg.execute(
            RegistryRequest(
                action="register",
                entry=_entry(model_id="expensive", provider="openai", cost_tier="high"),
            ),
            ctx,
        )
        await reg.execute(
            RegistryRequest(
                action="register",
                entry=_entry(model_id="cheap", provider="groq", cost_tier="free"),
            ),
            ctx,
        )

        resp = await reg.execute(
            RegistryRequest(
                action="select",
                policy=SelectionPolicy(prefer_local=False, max_cost_tier="low"),
            ),
            ctx,
        )
        assert resp.entry is not None
        assert resp.entry.model_id == "cheap"
        assert resp.entry.cost_tier == "free"

    @pytest.mark.asyncio
    async def test_select_max_cost_tier_medium_includes_lower_tiers(self) -> None:
        """max_cost_tier='medium' includes free, low, and medium; excludes high."""
        reg = _registry()
        ctx = _ctx()
        for tier, mid in [("free", "f"), ("low", "l"), ("medium", "m"), ("high", "h")]:
            await reg.execute(
                RegistryRequest(
                    action="register",
                    entry=_entry(model_id=mid, provider="groq", cost_tier=tier),
                ),
                ctx,
            )

        resp = await reg.execute(
            RegistryRequest(
                action="select",
                policy=SelectionPolicy(prefer_local=False, max_cost_tier="medium"),
            ),
            ctx,
        )
        assert resp.entry is not None
        assert resp.entry.cost_tier in {"free", "low", "medium"}
        assert resp.entry.model_id != "h"


class TestSelectRequireToolCalling:
    @pytest.mark.asyncio
    async def test_select_require_tool_calling(self) -> None:
        """Only tool-calling models selected when require_tool_calling=True."""
        reg = _registry()
        ctx = _ctx()
        await reg.execute(
            RegistryRequest(
                action="register",
                entry=_entry(model_id="no-tools", supports_tool_calling=False),
            ),
            ctx,
        )
        await reg.execute(
            RegistryRequest(
                action="register",
                entry=_entry(model_id="has-tools", supports_tool_calling=True),
            ),
            ctx,
        )

        resp = await reg.execute(
            RegistryRequest(
                action="select",
                policy=SelectionPolicy(require_tool_calling=True, max_cost_tier="high"),
            ),
            ctx,
        )
        assert resp.entry is not None
        assert resp.entry.supports_tool_calling is True
        assert resp.entry.model_id == "has-tools"


class TestSelectFallbackWhenEmpty:
    @pytest.mark.asyncio
    async def test_select_fallback_when_empty(self) -> None:
        """Returns entry=None when no model matches the policy."""
        reg = _registry()
        ctx = _ctx()
        # Only a high-cost model in registry
        await reg.execute(
            RegistryRequest(
                action="register",
                entry=_entry(model_id="pricey", provider="openai", cost_tier="high"),
            ),
            ctx,
        )

        resp = await reg.execute(
            RegistryRequest(action="select", policy=SelectionPolicy(max_cost_tier="free")),
            ctx,
        )
        assert resp.entry is None

    @pytest.mark.asyncio
    async def test_select_fallback_when_registry_empty(self) -> None:
        """Empty registry always returns entry=None."""
        reg = _registry()
        ctx = _ctx()
        resp = await reg.execute(
            RegistryRequest(action="select", policy=SelectionPolicy(max_cost_tier="high")), ctx
        )
        assert resp.entry is None

    @pytest.mark.asyncio
    async def test_select_no_policy_uses_defaults(self) -> None:
        """select without explicit policy uses SelectionPolicy defaults (max_cost_tier='low')."""
        reg = _registry()
        ctx = _ctx()
        await reg.execute(
            RegistryRequest(action="register", entry=_entry(model_id="free-m", cost_tier="free")),
            ctx,
        )
        await reg.execute(
            RegistryRequest(action="register", entry=_entry(model_id="high-m", cost_tier="high")),
            ctx,
        )

        resp = await reg.execute(RegistryRequest(action="select"), ctx)
        assert resp.entry is not None
        assert resp.entry.model_id == "free-m"


# ── Discover Ollama (mocked) ──────────────────────────────────────────────────


class TestDiscoverOllamaMocked:
    @pytest.mark.asyncio
    async def test_discover_ollama_mocked(self) -> None:
        """Mock OllamaModelManagerPrimitive; verify discovered models are registered."""
        from ttadev.primitives.llm.ollama_primitive import OllamaManagerResponse, OllamaModelInfo

        mock_manager = AsyncMock()
        mock_manager.execute = AsyncMock(
            return_value=OllamaManagerResponse(
                action="list",
                models=[
                    OllamaModelInfo(name="llama3.2:latest", parameter_size="3.2B"),
                    OllamaModelInfo(name="qwen3:1.7b", parameter_size="1.7B"),
                ],
            )
        )

        reg = _registry(ollama_manager=mock_manager)
        ctx = _ctx()

        resp = await reg.execute(RegistryRequest(action="discover_ollama"), ctx)
        assert resp.action == "discover_ollama"
        assert resp.discovered_count == 2
        assert resp.error is None

        list_resp = await reg.execute(RegistryRequest(action="list", filter_provider="ollama"), ctx)
        model_ids = {e.model_id for e in list_resp.entries}
        assert "llama3.2:latest" in model_ids
        assert "qwen3:1.7b" in model_ids

    @pytest.mark.asyncio
    async def test_discover_ollama_marks_local_and_free(self) -> None:
        """Discovered Ollama models are marked is_local=True and cost_tier='free'."""
        from ttadev.primitives.llm.ollama_primitive import OllamaManagerResponse, OllamaModelInfo

        mock_manager = AsyncMock()
        mock_manager.execute = AsyncMock(
            return_value=OllamaManagerResponse(
                action="list",
                models=[OllamaModelInfo(name="phi3:mini")],
            )
        )

        reg = _registry(ollama_manager=mock_manager)
        ctx = _ctx()
        await reg.execute(RegistryRequest(action="discover_ollama"), ctx)

        get_resp = await reg.execute(
            RegistryRequest(action="get", provider="ollama", model_id="phi3:mini"), ctx
        )
        assert get_resp.entry is not None
        assert get_resp.entry.is_local is True
        assert get_resp.entry.cost_tier == "free"
        assert get_resp.entry.provider == "ollama"

    @pytest.mark.asyncio
    async def test_discover_ollama_sets_last_seen(self) -> None:
        """Discovered Ollama entries have last_seen set to current timestamp."""
        from ttadev.primitives.llm.ollama_primitive import OllamaManagerResponse, OllamaModelInfo

        mock_manager = AsyncMock()
        mock_manager.execute = AsyncMock(
            return_value=OllamaManagerResponse(
                action="list",
                models=[OllamaModelInfo(name="gemma2:2b")],
            )
        )

        base_time = 1_000_000.0
        reg = _registry(ollama_manager=mock_manager)
        ctx = _ctx()

        with patch("ttadev.primitives.llm.model_registry.time.time", return_value=base_time):
            await reg.execute(RegistryRequest(action="discover_ollama"), ctx)

        # Access the raw registry entry to check last_seen value
        key = "ollama:gemma2:2b"
        assert key in reg._registry
        assert reg._registry[key].last_seen == base_time

    @pytest.mark.asyncio
    async def test_discover_ollama_handles_error(self) -> None:
        """Ollama unreachable → error returned, discovered_count=0."""
        mock_manager = AsyncMock()
        mock_manager.execute = AsyncMock(side_effect=ConnectionError("Connection refused"))

        reg = _registry(ollama_manager=mock_manager)
        ctx = _ctx()
        resp = await reg.execute(RegistryRequest(action="discover_ollama"), ctx)

        assert resp.discovered_count == 0
        assert resp.error is not None
        assert "Ollama unreachable" in resp.error

    @pytest.mark.asyncio
    async def test_discover_ollama_empty_list(self) -> None:
        """Ollama with no models → discovered_count=0, no error."""
        from ttadev.primitives.llm.ollama_primitive import OllamaManagerResponse

        mock_manager = AsyncMock()
        mock_manager.execute = AsyncMock(
            return_value=OllamaManagerResponse(action="list", models=[])
        )

        reg = _registry(ollama_manager=mock_manager)
        ctx = _ctx()
        resp = await reg.execute(RegistryRequest(action="discover_ollama"), ctx)

        assert resp.discovered_count == 0
        assert resp.error is None


# ── TTL Expiry ────────────────────────────────────────────────────────────────


class TestTTLExpiry:
    @pytest.mark.asyncio
    async def test_ttl_expiry(self) -> None:
        """Patch time.time: entry past TTL is excluded from list."""
        reg = _registry(ttl_seconds=60.0)
        ctx = _ctx()

        base_time = 1_000_000.0
        with patch("ttadev.primitives.llm.model_registry.time.time", return_value=base_time):
            await reg.execute(
                RegistryRequest(
                    action="register",
                    entry=ModelEntry(
                        model_id="stale-model",
                        provider="ollama",
                        is_local=True,
                        cost_tier="free",
                        last_seen=base_time,
                    ),
                ),
                ctx,
            )

        # Advance past TTL
        with patch("ttadev.primitives.llm.model_registry.time.time", return_value=base_time + 61.0):
            resp = await reg.execute(RegistryRequest(action="list"), ctx)

        assert all(e.model_id != "stale-model" for e in resp.entries)

    @pytest.mark.asyncio
    async def test_ttl_not_expired_still_visible(self) -> None:
        """Entry within TTL window remains visible."""
        reg = _registry(ttl_seconds=60.0)
        ctx = _ctx()

        base_time = 1_000_000.0
        with patch("ttadev.primitives.llm.model_registry.time.time", return_value=base_time):
            await reg.execute(
                RegistryRequest(
                    action="register",
                    entry=ModelEntry(
                        model_id="alive-model",
                        provider="ollama",
                        is_local=True,
                        cost_tier="free",
                        last_seen=base_time,
                    ),
                ),
                ctx,
            )

        # 30 seconds later — still within TTL
        with patch("ttadev.primitives.llm.model_registry.time.time", return_value=base_time + 30.0):
            resp = await reg.execute(RegistryRequest(action="list"), ctx)

        assert any(e.model_id == "alive-model" for e in resp.entries)

    @pytest.mark.asyncio
    async def test_zero_last_seen_never_expires(self) -> None:
        """Entry with last_seen=0.0 never expires regardless of elapsed time."""
        reg = _registry(ttl_seconds=60.0)
        ctx = _ctx()

        await reg.execute(
            RegistryRequest(
                action="register",
                entry=ModelEntry(
                    model_id="cloud-m",
                    provider="openai",
                    cost_tier="low",
                    last_seen=0.0,  # opt out of TTL
                ),
            ),
            ctx,
        )

        # 10 years later
        far_future = 1_000_000.0 + 10 * 365 * 24 * 3600
        with patch("ttadev.primitives.llm.model_registry.time.time", return_value=far_future):
            resp = await reg.execute(RegistryRequest(action="list"), ctx)

        assert any(e.model_id == "cloud-m" for e in resp.entries)

    @pytest.mark.asyncio
    async def test_ttl_expired_entry_not_returned_by_get(self) -> None:
        """get action also excludes TTL-expired entries."""
        reg = _registry(ttl_seconds=60.0)
        ctx = _ctx()

        base_time = 2_000_000.0
        with patch("ttadev.primitives.llm.model_registry.time.time", return_value=base_time):
            await reg.execute(
                RegistryRequest(
                    action="register",
                    entry=ModelEntry(
                        model_id="old-local",
                        provider="ollama",
                        is_local=True,
                        cost_tier="free",
                        last_seen=base_time,
                    ),
                ),
                ctx,
            )

        with patch(
            "ttadev.primitives.llm.model_registry.time.time", return_value=base_time + 120.0
        ):
            get_resp = await reg.execute(
                RegistryRequest(action="get", provider="ollama", model_id="old-local"), ctx
            )

        assert get_resp.entry is None


# ── Unregister ────────────────────────────────────────────────────────────────


class TestUnregister:
    @pytest.mark.asyncio
    async def test_unregister(self) -> None:
        """Model removed after unregister; subsequent get returns None."""
        reg = _registry()
        ctx = _ctx()
        entry = _entry(model_id="to-remove", provider="groq")
        await reg.execute(RegistryRequest(action="register", entry=entry), ctx)

        unreg_resp = await reg.execute(
            RegistryRequest(action="unregister", provider="groq", model_id="to-remove"), ctx
        )
        assert unreg_resp.unregistered is True

        get_resp = await reg.execute(
            RegistryRequest(action="get", provider="groq", model_id="to-remove"), ctx
        )
        assert get_resp.entry is None

    @pytest.mark.asyncio
    async def test_unregister_removes_from_list(self) -> None:
        """Unregistered model no longer appears in list results."""
        reg = _registry()
        ctx = _ctx()
        for i in range(3):
            await reg.execute(
                RegistryRequest(action="register", entry=_entry(model_id=f"m{i}", provider="groq")),
                ctx,
            )
        await reg.execute(RegistryRequest(action="unregister", provider="groq", model_id="m1"), ctx)

        resp = await reg.execute(RegistryRequest(action="list"), ctx)
        model_ids = {e.model_id for e in resp.entries}
        assert "m1" not in model_ids
        assert "m0" in model_ids
        assert "m2" in model_ids

    @pytest.mark.asyncio
    async def test_unregister_nonexistent(self) -> None:
        """Unregistering a model that does not exist returns unregistered=False."""
        reg = _registry()
        ctx = _ctx()
        resp = await reg.execute(
            RegistryRequest(action="unregister", provider="openai", model_id="ghost-model"), ctx
        )
        assert resp.unregistered is False


# ── Pre-populated cloud models ────────────────────────────────────────────────


class TestPrePopulatedCloudModels:
    @pytest.mark.asyncio
    async def test_pre_populated_cloud_models(self) -> None:
        """Fresh registry (prepopulate=True) has well-known cloud models."""
        reg = ModelRegistryPrimitive(prepopulate=True)
        ctx = _ctx()
        resp = await reg.execute(RegistryRequest(action="list"), ctx)
        providers = {e.provider for e in resp.entries}
        assert "openai" in providers
        assert "groq" in providers
        assert "google" in providers

    @pytest.mark.asyncio
    async def test_pre_populated_gpt4o_mini(self) -> None:
        """gpt-4o-mini from openai is pre-registered with correct attributes."""
        reg = ModelRegistryPrimitive(prepopulate=True)
        ctx = _ctx()
        resp = await reg.execute(
            RegistryRequest(action="get", provider="openai", model_id="gpt-4o-mini"), ctx
        )
        assert resp.entry is not None
        assert resp.entry.model_id == "gpt-4o-mini"
        assert resp.entry.cost_tier == "low"
        assert resp.entry.supports_tool_calling is True
        assert resp.entry.supports_vision is True

    @pytest.mark.asyncio
    async def test_pre_populated_groq_model_is_free(self) -> None:
        """Groq llama-3.1-8b-instant is pre-registered as cost_tier='free'."""
        reg = ModelRegistryPrimitive(prepopulate=True)
        ctx = _ctx()
        resp = await reg.execute(
            RegistryRequest(action="get", provider="groq", model_id="llama-3.1-8b-instant"), ctx
        )
        assert resp.entry is not None
        assert resp.entry.cost_tier == "free"

    @pytest.mark.asyncio
    async def test_pre_populated_gemini_flash_lite(self) -> None:
        """models/gemini-2.0-flash-lite is pre-registered as cost_tier='free'.

        The model ID uses the ``models/`` prefix required by Google's
        OpenAI-compatible endpoint (updated June 2026).
        """
        reg = ModelRegistryPrimitive(prepopulate=True)
        ctx = _ctx()
        resp = await reg.execute(
            RegistryRequest(
                action="get", provider="google", model_id="models/gemini-2.0-flash-lite"
            ),
            ctx,
        )
        assert resp.entry is not None
        assert resp.entry.cost_tier == "free"

    @pytest.mark.asyncio
    async def test_pre_populated_no_ollama_models(self) -> None:
        """Fresh registry has no ollama models (not discovered yet)."""
        reg = ModelRegistryPrimitive(prepopulate=True)
        ctx = _ctx()
        resp = await reg.execute(RegistryRequest(action="list", filter_provider="ollama"), ctx)
        assert resp.entries == []

    @pytest.mark.asyncio
    async def test_pre_populated_entries_have_zero_last_seen(self) -> None:
        """Pre-populated cloud entries have last_seen=0.0 so they never expire."""
        reg = ModelRegistryPrimitive(prepopulate=True)
        ctx = _ctx()
        resp = await reg.execute(RegistryRequest(action="list"), ctx)
        for entry in resp.entries:
            assert entry.last_seen == 0.0, f"{entry.provider}:{entry.model_id} has last_seen != 0"


# ── Error handling ────────────────────────────────────────────────────────────


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_invalid_action_raises_value_error(self) -> None:
        """Unknown action raises ValueError with a helpful message."""
        reg = _registry()
        ctx = _ctx()
        with pytest.raises(ValueError, match="Unknown action"):
            await reg.execute(RegistryRequest(action="bogus"), ctx)

    @pytest.mark.asyncio
    async def test_invalid_action_message_includes_valid_actions(self) -> None:
        """ValueError message lists valid actions."""
        reg = _registry()
        ctx = _ctx()
        with pytest.raises(ValueError, match="register"):
            await reg.execute(RegistryRequest(action="INVALID"), ctx)


# ── Export symbol ─────────────────────────────────────────────────────────────


class TestExportSymbol:
    def test_export_symbol(self) -> None:
        """ModelRegistryPrimitive and companions are importable from ttadev.primitives.llm."""
        from ttadev.primitives.llm import (
            ModelEntry,
            ModelRegistryPrimitive,
            RegistryRequest,
            RegistryResponse,
            SelectionPolicy,
        )

        assert ModelRegistryPrimitive is not None
        assert ModelEntry is not None
        assert RegistryRequest is not None
        assert RegistryResponse is not None
        assert SelectionPolicy is not None

    def test_all_exports_in_dunder_all(self) -> None:
        """All five new symbols appear in ttadev.primitives.llm.__all__."""
        import ttadev.primitives.llm as llm_pkg

        for name in (
            "ModelEntry",
            "ModelRegistryPrimitive",
            "RegistryRequest",
            "RegistryResponse",
            "SelectionPolicy",
        ):
            assert name in llm_pkg.__all__, f"{name!r} missing from __all__"


# ── Pricing catalog integration ───────────────────────────────────────────────


class TestPricingCatalogIntegration:
    @pytest.mark.asyncio
    async def test_pricing_override_applied_at_registration(self) -> None:
        """Register a ModelEntry with cost_tier='unknown' for a catalog-known model.

        After registration the entry stored in the registry must reflect the
        catalog's cost_tier ('free' for groq/llama-3.3-70b-versatile) rather
        than the caller-supplied 'unknown'.
        """
        reg = _registry()
        ctx = _ctx()

        # Arrange: entry with deliberately wrong cost_tier
        entry = ModelEntry(
            model_id="llama-3.3-70b-versatile",
            provider="groq",
            cost_tier="unknown",
        )

        # Act
        reg_resp = await reg.execute(RegistryRequest(action="register", entry=entry), ctx)
        assert reg_resp.registered is True

        get_resp = await reg.execute(
            RegistryRequest(action="get", provider="groq", model_id="llama-3.3-70b-versatile"),
            ctx,
        )

        # Assert: catalog overrides the stale static field
        assert get_resp.entry is not None
        assert get_resp.entry.cost_tier == "free", (
            f"Expected 'free' from pricing catalog, got {get_resp.entry.cost_tier!r}"
        )

    @pytest.mark.asyncio
    async def test_unknown_model_keeps_static_cost_tier(self) -> None:
        """Model not in the pricing catalog keeps the cost_tier from ModelEntry.

        This ensures backward-compat — new or unlisted models are not silently
        downgraded/upgraded by the catalog.
        """
        reg = _registry()
        ctx = _ctx()

        entry = ModelEntry(
            model_id="my-custom-finetune-v3",
            provider="groq",
            cost_tier="low",
        )
        await reg.execute(RegistryRequest(action="register", entry=entry), ctx)

        get_resp = await reg.execute(
            RegistryRequest(action="get", provider="groq", model_id="my-custom-finetune-v3"),
            ctx,
        )
        assert get_resp.entry is not None
        assert get_resp.entry.cost_tier == "low", (
            "Unlisted models must keep their static cost_tier as fallback"
        )
