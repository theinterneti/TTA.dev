"""Unit tests for ModelRegistryPrimitive.

Covers: ModelEntry, SelectionPolicy, RegistryResponse, _COST_TIER_ORDER,
ModelRegistryPrimitive (init/prepopulate, _is_stale, _live_entries, execute
dispatch, _register, _get, _list, _discover_ollama, _select, _unregister),
_DEFAULT_CLOUD_MODELS integrity.

asyncio_mode = auto — no @pytest.mark.asyncio needed.
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.llm.model_registry import (
    _COST_TIER_ORDER,
    _DEFAULT_CLOUD_MODELS,
    ModelEntry,
    ModelRegistryPrimitive,
    RegistryRequest,
    RegistryResponse,
    SelectionPolicy,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(name: str = "test") -> WorkflowContext:
    return WorkflowContext(workflow_id=name)


def _fresh_registry(
    *, prepopulate: bool = False, ttl_seconds: float = 3600.0
) -> ModelRegistryPrimitive:
    """Return a registry with no default entries for deterministic testing."""
    return ModelRegistryPrimitive(prepopulate=prepopulate, ttl_seconds=ttl_seconds)


def _make_entry(
    model_id: str = "test-model",
    provider: str = "groq",
    cost_tier: str = "free",
    is_local: bool = False,
    last_seen: float = 0.0,
    supports_tool_calling: bool = False,
    supports_vision: bool = False,
) -> ModelEntry:
    return ModelEntry(
        model_id=model_id,
        provider=provider,
        cost_tier=cost_tier,
        is_local=is_local,
        last_seen=last_seen,
        supports_tool_calling=supports_tool_calling,
        supports_vision=supports_vision,
    )


# ---------------------------------------------------------------------------
# ModelEntry
# ---------------------------------------------------------------------------


class TestModelEntry:
    def test_defaults(self):
        # Arrange / Act
        entry = ModelEntry(model_id="m", provider="groq")
        # Assert
        assert entry.display_name == ""
        assert entry.context_length == 4096
        assert entry.supports_tool_calling is False
        assert entry.supports_vision is False
        assert entry.supports_streaming is True
        assert entry.cost_tier == "unknown"
        assert entry.is_local is False
        assert entry.last_seen == 0.0
        assert entry.metadata == {}

    def test_custom_values_stored(self):
        # Arrange / Act
        entry = ModelEntry(
            model_id="llama3",
            provider="ollama",
            cost_tier="free",
            is_local=True,
            last_seen=1000.0,
            metadata={"param_size": "7B"},
        )
        # Assert
        assert entry.is_local is True
        assert entry.metadata["param_size"] == "7B"
        assert entry.last_seen == 1000.0


# ---------------------------------------------------------------------------
# SelectionPolicy
# ---------------------------------------------------------------------------


class TestSelectionPolicy:
    def test_defaults(self):
        # Arrange / Act
        policy = SelectionPolicy()
        # Assert
        assert policy.prefer_local is True
        assert policy.max_cost_tier == "low"
        assert policy.require_tool_calling is False
        assert policy.require_vision is False
        assert policy.preferred_providers == []
        assert policy.fallback_providers == []
        assert policy.min_humaneval_score is None
        assert policy.min_mmlu_score is None
        assert policy.preferred_benchmark is None


# ---------------------------------------------------------------------------
# RegistryResponse
# ---------------------------------------------------------------------------


class TestRegistryResponse:
    def test_defaults(self):
        # Arrange / Act
        resp = RegistryResponse(action="get")
        # Assert
        assert resp.entry is None
        assert resp.entries == []
        assert resp.registered is False
        assert resp.unregistered is False
        assert resp.discovered_count == 0
        assert resp.error is None

    def test_action_echoed(self):
        resp = RegistryResponse(action="select")
        assert resp.action == "select"


# ---------------------------------------------------------------------------
# _COST_TIER_ORDER
# ---------------------------------------------------------------------------


class TestCostTierOrder:
    def test_ordering_is_ascending_by_cost(self):
        # Assert
        assert _COST_TIER_ORDER["free"] < _COST_TIER_ORDER["low"]
        assert _COST_TIER_ORDER["low"] < _COST_TIER_ORDER["medium"]
        assert _COST_TIER_ORDER["medium"] < _COST_TIER_ORDER["high"]

    def test_unknown_maps_to_high_sentinel(self):
        assert _COST_TIER_ORDER["unknown"] == 99


# ---------------------------------------------------------------------------
# Init / prepopulate
# ---------------------------------------------------------------------------


class TestModelRegistryInit:
    def test_prepopulate_true_fills_registry(self):
        # Arrange / Act
        registry = ModelRegistryPrimitive(prepopulate=True)
        # Assert
        assert len(registry._registry) > 0

    def test_prepopulate_false_empty_registry(self):
        # Arrange / Act
        registry = _fresh_registry()
        # Assert
        assert len(registry._registry) == 0

    def test_all_prepopulated_entries_have_last_seen_zero(self):
        # Arrange / Act
        registry = ModelRegistryPrimitive(prepopulate=True)
        # Assert
        for entry in registry._registry.values():
            assert entry.last_seen == 0.0, (
                f"Cloud entry {entry.model_id} has last_seen={entry.last_seen}"
            )

    def test_ttl_stored(self):
        registry = ModelRegistryPrimitive(prepopulate=False, ttl_seconds=7200.0)
        assert registry._ttl == 7200.0


# ---------------------------------------------------------------------------
# _is_stale / _live_entries
# ---------------------------------------------------------------------------


class TestIsStale:
    def test_last_seen_zero_never_stale(self):
        # Arrange
        registry = _fresh_registry()
        entry = _make_entry(last_seen=0.0)
        # Assert
        assert registry._is_stale(entry) is False

    def test_recent_entry_not_stale(self):
        # Arrange
        registry = _fresh_registry(ttl_seconds=3600.0)
        entry = _make_entry(last_seen=time.time())
        # Assert
        assert registry._is_stale(entry) is False

    def test_old_entry_is_stale(self):
        # Arrange
        registry = _fresh_registry(ttl_seconds=10.0)
        entry = _make_entry(last_seen=time.time() - 100.0)  # 100s ago, ttl=10s
        # Assert
        assert registry._is_stale(entry) is True

    def test_entry_just_under_ttl_not_stale(self):
        # Arrange
        registry = _fresh_registry(ttl_seconds=3600.0)
        entry = _make_entry(last_seen=time.time() - 3599.0)
        # Assert
        assert registry._is_stale(entry) is False


class TestLiveEntries:
    def test_excludes_stale_entries(self):
        # Arrange
        registry = _fresh_registry(ttl_seconds=10.0)
        fresh = _make_entry(model_id="fresh", last_seen=time.time())
        stale = _make_entry(model_id="stale", last_seen=time.time() - 9999.0)
        registry._registry["groq:fresh"] = fresh
        registry._registry["groq:stale"] = stale
        # Act
        live = registry._live_entries()
        ids = [e.model_id for e in live]
        # Assert
        assert "fresh" in ids
        assert "stale" not in ids

    def test_zero_last_seen_always_live(self):
        # Arrange
        registry = _fresh_registry()
        entry = _make_entry(model_id="cloud-m", last_seen=0.0)
        registry._registry["groq:cloud-m"] = entry
        # Act
        live = registry._live_entries()
        # Assert
        assert any(e.model_id == "cloud-m" for e in live)


# ---------------------------------------------------------------------------
# execute — dispatch
# ---------------------------------------------------------------------------


class TestExecuteDispatch:
    async def test_unknown_action_raises_value_error(self):
        # Arrange
        registry = _fresh_registry()
        # Act / Assert
        with pytest.raises(ValueError, match="Unknown action"):
            await registry.execute(RegistryRequest(action="explode"), _ctx())

    async def test_action_is_case_insensitive(self):
        # Arrange
        registry = _fresh_registry()
        # Act — "LIST" should work same as "list"
        resp = await registry.execute(RegistryRequest(action="LIST"), _ctx())
        # Assert
        assert resp.action == "list"


# ---------------------------------------------------------------------------
# _register
# ---------------------------------------------------------------------------


class TestRegister:
    async def test_no_entry_returns_error_response(self):
        # Arrange
        registry = _fresh_registry()
        req = RegistryRequest(action="register", entry=None)
        # Act
        resp = await registry.execute(req, _ctx())
        # Assert
        assert resp.registered is False
        assert resp.error is not None

    async def test_register_adds_entry(self):
        # Arrange
        registry = _fresh_registry()
        entry = _make_entry(model_id="new-model")
        # Act
        with patch(
            "ttadev.primitives.llm.model_pricing.get_effective_cost_tier",
            return_value="free",
        ):
            resp = await registry.execute(RegistryRequest(action="register", entry=entry), _ctx())
        # Assert
        assert resp.registered is True
        assert resp.entry is not None
        assert resp.entry.model_id == "new-model"
        assert "groq:new-model" in registry._registry

    async def test_register_overwrites_existing_entry(self):
        # Arrange
        registry = _fresh_registry()
        entry1 = _make_entry(model_id="model", cost_tier="free")
        entry2 = _make_entry(model_id="model", cost_tier="medium")
        # Act
        with patch(
            "ttadev.primitives.llm.model_pricing.get_effective_cost_tier",
            return_value="medium",
        ):
            await registry.execute(RegistryRequest(action="register", entry=entry1), _ctx())
            await registry.execute(RegistryRequest(action="register", entry=entry2), _ctx())
        # Assert
        stored = registry._registry["groq:model"]
        assert stored.cost_tier == "medium"

    async def test_register_applies_pricing_catalog(self):
        # Arrange
        registry = _fresh_registry()
        entry = _make_entry(model_id="model", cost_tier="unknown")
        # Act — catalog overrides unknown with free
        with patch(
            "ttadev.primitives.llm.model_pricing.get_effective_cost_tier",
            return_value="free",
        ):
            resp = await registry.execute(RegistryRequest(action="register", entry=entry), _ctx())
        # Assert — cost_tier updated from catalog
        assert resp.entry.cost_tier == "free"


# ---------------------------------------------------------------------------
# _get
# ---------------------------------------------------------------------------


class TestGet:
    async def test_get_existing_entry(self):
        # Arrange
        registry = _fresh_registry()
        entry = _make_entry(model_id="m1", provider="groq")
        registry._registry["groq:m1"] = entry
        # Act
        resp = await registry.execute(
            RegistryRequest(action="get", provider="groq", model_id="m1"), _ctx()
        )
        # Assert
        assert resp.entry is not None
        assert resp.entry.model_id == "m1"

    async def test_get_missing_entry_returns_none(self):
        # Arrange
        registry = _fresh_registry()
        # Act
        resp = await registry.execute(
            RegistryRequest(action="get", provider="groq", model_id="ghost"), _ctx()
        )
        # Assert
        assert resp.entry is None

    async def test_get_stale_entry_returns_none(self):
        # Arrange
        registry = _fresh_registry(ttl_seconds=1.0)
        entry = _make_entry(model_id="stale-m", last_seen=time.time() - 100.0)
        registry._registry["groq:stale-m"] = entry
        # Act
        resp = await registry.execute(
            RegistryRequest(action="get", provider="groq", model_id="stale-m"), _ctx()
        )
        # Assert
        assert resp.entry is None


# ---------------------------------------------------------------------------
# _list
# ---------------------------------------------------------------------------


class TestList:
    def _populate(self, registry: ModelRegistryPrimitive) -> None:
        registry._registry["groq:a"] = _make_entry("a", "groq", "free", supports_tool_calling=True)
        registry._registry["google:b"] = _make_entry("b", "google", "low")
        registry._registry["ollama:c"] = _make_entry(
            "c", "ollama", "free", is_local=True, supports_vision=True
        )

    async def test_list_all_no_filter(self):
        # Arrange
        registry = _fresh_registry()
        self._populate(registry)
        # Act
        resp = await registry.execute(RegistryRequest(action="list"), _ctx())
        # Assert
        assert len(resp.entries) == 3

    async def test_filter_by_provider(self):
        # Arrange
        registry = _fresh_registry()
        self._populate(registry)
        # Act
        resp = await registry.execute(
            RegistryRequest(action="list", filter_provider="groq"), _ctx()
        )
        # Assert
        assert len(resp.entries) == 1
        assert all(e.provider == "groq" for e in resp.entries)

    async def test_filter_by_cost_tier(self):
        # Arrange
        registry = _fresh_registry()
        self._populate(registry)
        # Act
        resp = await registry.execute(
            RegistryRequest(action="list", filter_cost_tier="low"), _ctx()
        )
        # Assert
        assert len(resp.entries) == 1
        assert resp.entries[0].cost_tier == "low"

    async def test_filter_tool_calling(self):
        # Arrange
        registry = _fresh_registry()
        self._populate(registry)
        # Act
        resp = await registry.execute(
            RegistryRequest(action="list", filter_tool_calling=True), _ctx()
        )
        # Assert
        assert all(e.supports_tool_calling for e in resp.entries)
        assert len(resp.entries) == 1

    async def test_filter_vision(self):
        # Arrange
        registry = _fresh_registry()
        self._populate(registry)
        # Act
        resp = await registry.execute(RegistryRequest(action="list", filter_vision=True), _ctx())
        # Assert
        assert all(e.supports_vision for e in resp.entries)
        assert len(resp.entries) == 1

    async def test_benchmark_filter_includes_matching_models(self):
        # Arrange
        registry = _fresh_registry()
        registry._registry["groq:a"] = _make_entry("a")
        registry._registry["groq:b"] = _make_entry("b")

        def mock_get_best_score(model_id: str, benchmark: str) -> float | None:
            return 85.0 if model_id == "a" else None

        # Act
        with patch(
            "ttadev.primitives.llm.model_benchmarks.get_best_score",
            side_effect=mock_get_best_score,
        ):
            resp = await registry.execute(
                RegistryRequest(
                    action="list",
                    benchmark_filter="humaneval",
                    min_benchmark_score=80.0,
                ),
                _ctx(),
            )
        # Assert
        assert len(resp.entries) == 1
        assert resp.entries[0].model_id == "a"

    async def test_benchmark_filter_without_min_score(self):
        # Arrange — min_benchmark_score=None means just "has any score"
        registry = _fresh_registry()
        registry._registry["groq:a"] = _make_entry("a")
        registry._registry["groq:b"] = _make_entry("b")

        def mock_score(model_id: str, benchmark: str) -> float | None:
            return 50.0 if model_id == "a" else None

        # Act
        with patch(
            "ttadev.primitives.llm.model_benchmarks.get_best_score",
            side_effect=mock_score,
        ):
            resp = await registry.execute(
                RegistryRequest(action="list", benchmark_filter="humaneval"), _ctx()
            )
        # Assert
        assert len(resp.entries) == 1
        assert resp.entries[0].model_id == "a"


# ---------------------------------------------------------------------------
# _discover_ollama
# ---------------------------------------------------------------------------


class TestDiscoverOllama:
    async def test_discovers_and_registers_models(self):
        # Arrange
        registry = _fresh_registry()
        mock_model = MagicMock()
        mock_model.name = "llama3.2:latest"
        mock_model.parameter_size = "7B"
        mock_model.quantization = "Q4_0"
        mock_model.family = "llama"
        mock_model.size_bytes = 4_000_000_000
        mock_ollama_resp = MagicMock()
        mock_ollama_resp.models = [mock_model]
        mock_manager = MagicMock()
        mock_manager.execute = AsyncMock(return_value=mock_ollama_resp)
        registry._ollama_manager = mock_manager
        # Act
        resp = await registry.execute(RegistryRequest(action="discover_ollama"), _ctx())
        # Assert
        assert resp.discovered_count == 1
        stored = registry._registry.get("ollama:llama3.2:latest")
        assert stored is not None
        assert stored.is_local is True
        assert stored.cost_tier == "free"

    async def test_discovers_multiple_models(self):
        # Arrange
        registry = _fresh_registry()

        def _mock_model(name: str) -> MagicMock:
            m = MagicMock()
            m.name = name
            m.parameter_size = "3B"
            m.quantization = "Q4_0"
            m.family = "llama"
            m.size_bytes = 2_000_000_000
            return m

        mock_ollama_resp = MagicMock()
        mock_ollama_resp.models = [_mock_model("m1:latest"), _mock_model("m2:latest")]
        mock_manager = MagicMock()
        mock_manager.execute = AsyncMock(return_value=mock_ollama_resp)
        registry._ollama_manager = mock_manager
        # Act
        resp = await registry.execute(RegistryRequest(action="discover_ollama"), _ctx())
        # Assert
        assert resp.discovered_count == 2

    async def test_ollama_unreachable_returns_error(self):
        # Arrange
        registry = _fresh_registry()
        mock_manager = MagicMock()
        mock_manager.execute = AsyncMock(side_effect=ConnectionError("refused"))
        registry._ollama_manager = mock_manager
        # Act
        resp = await registry.execute(RegistryRequest(action="discover_ollama"), _ctx())
        # Assert
        assert resp.discovered_count == 0
        assert resp.error is not None
        assert "unreachable" in resp.error.lower()


# ---------------------------------------------------------------------------
# _select
# ---------------------------------------------------------------------------


class TestSelect:
    async def test_select_returns_entry_when_available(self):
        # Arrange — cloud-only entries (skip hardware filter)
        registry = _fresh_registry()
        registry._registry["groq:m1"] = _make_entry("m1", "groq", "free")
        registry._registry["groq:m2"] = _make_entry("m2", "groq", "free")
        # Act
        with patch("ttadev.primitives.llm.model_benchmarks.get_best_score", return_value=None):
            resp = await registry.execute(
                RegistryRequest(action="select", policy=SelectionPolicy(max_cost_tier="high")),
                _ctx(),
            )
        # Assert
        assert resp.entry is not None

    async def test_select_no_entries_returns_none(self):
        # Arrange
        registry = _fresh_registry()
        # Act
        with patch("ttadev.primitives.llm.model_benchmarks.get_best_score", return_value=None):
            resp = await registry.execute(
                RegistryRequest(action="select", policy=SelectionPolicy()),
                _ctx(),
            )
        # Assert
        assert resp.entry is None

    async def test_select_excludes_above_cost_ceiling(self):
        # Arrange
        registry = _fresh_registry()
        registry._registry["google:cheap"] = _make_entry("cheap", "google", "free")
        registry._registry["google:pricey"] = _make_entry("pricey", "google", "medium")
        # Act
        with patch("ttadev.primitives.llm.model_benchmarks.get_best_score", return_value=None):
            resp = await registry.execute(
                RegistryRequest(action="select", policy=SelectionPolicy(max_cost_tier="free")),
                _ctx(),
            )
        # Assert
        assert resp.entry is not None
        assert resp.entry.model_id == "cheap"

    async def test_select_requires_tool_calling(self):
        # Arrange
        registry = _fresh_registry()
        registry._registry["groq:plain"] = _make_entry(
            "plain", "groq", "free", supports_tool_calling=False
        )
        registry._registry["groq:tools"] = _make_entry(
            "tools", "groq", "free", supports_tool_calling=True
        )
        # Act
        with patch("ttadev.primitives.llm.model_benchmarks.get_best_score", return_value=None):
            resp = await registry.execute(
                RegistryRequest(
                    action="select",
                    policy=SelectionPolicy(require_tool_calling=True, max_cost_tier="high"),
                ),
                _ctx(),
            )
        # Assert
        assert resp.entry is not None
        assert resp.entry.model_id == "tools"

    async def test_select_requires_vision(self):
        # Arrange
        registry = _fresh_registry()
        registry._registry["groq:novision"] = _make_entry(
            "novision", "groq", "free", supports_vision=False
        )
        registry._registry["groq:vision"] = _make_entry(
            "vision", "groq", "free", supports_vision=True
        )
        # Act
        with patch("ttadev.primitives.llm.model_benchmarks.get_best_score", return_value=None):
            resp = await registry.execute(
                RegistryRequest(
                    action="select",
                    policy=SelectionPolicy(require_vision=True, max_cost_tier="high"),
                ),
                _ctx(),
            )
        # Assert
        assert resp.entry is not None
        assert resp.entry.model_id == "vision"

    async def test_select_preferred_providers_ordering(self):
        # Arrange — prefer google over groq
        registry = _fresh_registry()
        registry._registry["groq:a"] = _make_entry("a", "groq", "free")
        registry._registry["google:b"] = _make_entry("b", "google", "free")
        # Act
        with patch("ttadev.primitives.llm.model_benchmarks.get_best_score", return_value=None):
            resp = await registry.execute(
                RegistryRequest(
                    action="select",
                    policy=SelectionPolicy(
                        preferred_providers=["google"],
                        prefer_local=False,
                        max_cost_tier="high",
                    ),
                ),
                _ctx(),
            )
        # Assert
        assert resp.entry is not None
        assert resp.entry.provider == "google"

    async def test_select_humaneval_filter(self):
        # Arrange
        registry = _fresh_registry()
        registry._registry["groq:good"] = _make_entry("good", "groq", "free")
        registry._registry["groq:bad"] = _make_entry("bad", "groq", "free")

        def mock_score(model_id: str, benchmark: str) -> float | None:
            return 85.0 if model_id == "good" else None

        # Act
        with patch(
            "ttadev.primitives.llm.model_benchmarks.get_best_score",
            side_effect=mock_score,
        ):
            resp = await registry.execute(
                RegistryRequest(
                    action="select",
                    policy=SelectionPolicy(min_humaneval_score=80.0, max_cost_tier="high"),
                ),
                _ctx(),
            )
        # Assert
        assert resp.entry is not None
        assert resp.entry.model_id == "good"

    async def test_select_mmlu_filter(self):
        # Arrange
        registry = _fresh_registry()
        registry._registry["groq:smart"] = _make_entry("smart", "groq", "free")
        registry._registry["groq:dumb"] = _make_entry("dumb", "groq", "free")

        def mock_score(model_id: str, benchmark: str) -> float | None:
            if model_id == "smart" and benchmark == "mmlu":
                return 90.0
            return None

        # Act
        with patch(
            "ttadev.primitives.llm.model_benchmarks.get_best_score",
            side_effect=mock_score,
        ):
            resp = await registry.execute(
                RegistryRequest(
                    action="select",
                    policy=SelectionPolicy(min_mmlu_score=80.0, max_cost_tier="high"),
                ),
                _ctx(),
            )
        # Assert
        assert resp.entry is not None
        assert resp.entry.model_id == "smart"

    async def test_select_with_monitor_prefers_healthy(self):
        # Arrange — "aaa" is sick (sorts first alphabetically); "bbb" is healthy
        registry = _fresh_registry()
        registry._registry["groq:aaa"] = _make_entry("aaa", "groq", "free")
        registry._registry["groq:bbb"] = _make_entry("bbb", "groq", "free")
        mock_monitor = MagicMock()
        mock_monitor.is_healthy_sync = MagicMock(
            side_effect=lambda model_id, provider: model_id == "bbb"
        )
        registry._monitor = mock_monitor
        # Act
        with patch("ttadev.primitives.llm.model_benchmarks.get_best_score", return_value=None):
            resp = await registry.execute(
                RegistryRequest(
                    action="select",
                    policy=SelectionPolicy(prefer_local=False, max_cost_tier="high"),
                ),
                _ctx(),
            )
        # Assert — healthy "bbb" preferred over sick "aaa"
        assert resp.entry is not None
        assert resp.entry.model_id == "bbb"

    async def test_select_preferred_benchmark_sort(self):
        # Arrange — "slow" scores low, "fast" scores high on the preferred benchmark
        registry = _fresh_registry()
        registry._registry["groq:slow"] = _make_entry("slow", "groq", "free")
        registry._registry["groq:fast"] = _make_entry("fast", "groq", "free")

        def mock_score(model_id: str, benchmark: str) -> float | None:
            return {"slow": 30.0, "fast": 90.0}.get(model_id)

        # Act
        with patch(
            "ttadev.primitives.llm.model_benchmarks.get_best_score",
            side_effect=mock_score,
        ):
            resp = await registry.execute(
                RegistryRequest(
                    action="select",
                    policy=SelectionPolicy(
                        prefer_local=False,
                        max_cost_tier="high",
                        preferred_benchmark="humaneval",
                    ),
                ),
                _ctx(),
            )
        # Assert — high benchmark score wins
        assert resp.entry is not None
        assert resp.entry.model_id == "fast"


# ---------------------------------------------------------------------------
# _unregister
# ---------------------------------------------------------------------------


class TestUnregister:
    async def test_unregister_existing_returns_true(self):
        # Arrange
        registry = _fresh_registry()
        registry._registry["groq:m1"] = _make_entry("m1")
        # Act
        resp = await registry.execute(
            RegistryRequest(action="unregister", provider="groq", model_id="m1"), _ctx()
        )
        # Assert
        assert resp.unregistered is True
        assert "groq:m1" not in registry._registry

    async def test_unregister_nonexistent_returns_false(self):
        # Arrange
        registry = _fresh_registry()
        # Act
        resp = await registry.execute(
            RegistryRequest(action="unregister", provider="groq", model_id="ghost"), _ctx()
        )
        # Assert
        assert resp.unregistered is False


# ---------------------------------------------------------------------------
# _DEFAULT_CLOUD_MODELS integrity
# ---------------------------------------------------------------------------


class TestDefaultCloudModels:
    def test_all_entries_have_model_id_and_provider(self):
        for entry in _DEFAULT_CLOUD_MODELS:
            assert entry.model_id, f"Entry missing model_id: {entry}"
            assert entry.provider, f"Entry missing provider: {entry}"

    def test_all_entries_have_last_seen_zero(self):
        for entry in _DEFAULT_CLOUD_MODELS:
            assert entry.last_seen == 0.0, (
                f"{entry.model_id} has last_seen={entry.last_seen}, expected 0.0"
            )

    def test_no_local_entries_in_default(self):
        for entry in _DEFAULT_CLOUD_MODELS:
            assert entry.is_local is False, (
                f"{entry.model_id} is marked is_local=True in default cloud models"
            )

    def test_unique_provider_model_id_pairs(self):
        pairs = [(e.provider, e.model_id) for e in _DEFAULT_CLOUD_MODELS]
        assert len(pairs) == len(set(pairs)), "Duplicate (provider, model_id) pairs found"

    def test_at_least_one_groq_entry(self):
        groq_entries = [e for e in _DEFAULT_CLOUD_MODELS if e.provider == "groq"]
        assert len(groq_entries) > 0

    def test_at_least_one_google_entry(self):
        google_entries = [e for e in _DEFAULT_CLOUD_MODELS if e.provider == "google"]
        assert len(google_entries) > 0

    def test_all_cost_tiers_are_valid(self):
        valid_tiers = set(_COST_TIER_ORDER.keys())
        for entry in _DEFAULT_CLOUD_MODELS:
            assert entry.cost_tier in valid_tiers, (
                f"{entry.model_id} has invalid cost_tier={entry.cost_tier!r}"
            )
