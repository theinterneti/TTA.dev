"""Unit tests for ttadev.primitives.llm.model_discovery.

Covers: DiscoveredModel, _ProviderCache, _sort_models,
ProviderModelDiscovery (mem/disk cache, live fetch, exhaustion tracking,
for_google), best_google_free_model.

All HTTP is mocked — no live network calls.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from ttadev.primitives.llm.model_discovery import (
    DiscoveredModel,
    ProviderModelDiscovery,
    _ProviderCache,
    _sort_models,
    best_google_free_model,
)

# ── Shared helpers ──────────────────────────────────────────────────────────────


def _discovery(tmp_path: Path, ttl: float = 3600.0) -> ProviderModelDiscovery:
    return ProviderModelDiscovery(cache_dir=tmp_path / "cache", cache_ttl=ttl)


def _model(model_id: str, owned_by: str = "test", created: int = 0) -> DiscoveredModel:
    return DiscoveredModel(id=model_id, owned_by=owned_by, created=created)


def _openai_compat_response(model_ids: list[str]) -> dict:
    return {"data": [{"id": mid, "owned_by": "test", "created": 1000} for mid in model_ids]}


def _make_httpx_mock(json_payload: dict) -> tuple[MagicMock, AsyncMock]:
    """Wire httpx.AsyncClient as an async context manager."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = json_payload

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    mock_cls = MagicMock()
    mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_cls, mock_client


def _error_httpx_mock(exc: Exception) -> MagicMock:
    """Wire httpx.AsyncClient to raise exc on client.get()."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=exc)
    mock_cls = MagicMock()
    mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_cls


# ── DiscoveredModel ─────────────────────────────────────────────────────────────


class TestDiscoveredModel:
    def test_id_required_field(self):
        model = DiscoveredModel(id="openai/gpt-4o")
        assert model.id == "openai/gpt-4o"

    def test_owned_by_defaults_to_empty_string(self):
        assert DiscoveredModel(id="m").owned_by == ""

    def test_created_defaults_to_zero(self):
        assert DiscoveredModel(id="m").created == 0

    def test_all_fields_stored(self):
        model = DiscoveredModel(id="x/y", owned_by="acme", created=1700000000)
        assert model.owned_by == "acme"
        assert model.created == 1700000000


# ── _ProviderCache.is_fresh() ───────────────────────────────────────────────────


class TestProviderCacheIsFresh:
    def test_true_when_just_populated(self):
        cache = _ProviderCache(models=["m"], fetched_at=time.time())
        assert cache.is_fresh(3600) is True

    def test_false_when_older_than_ttl(self):
        cache = _ProviderCache(models=["m"], fetched_at=time.time() - 7200)
        assert cache.is_fresh(3600) is False

    def test_false_when_fetched_at_is_zero(self):
        cache = _ProviderCache(models=[], fetched_at=0.0)
        assert cache.is_fresh(3600) is False


# ── _sort_models() ──────────────────────────────────────────────────────────────


class TestSortModels:
    def test_no_patterns_gives_lexicographic_order(self):
        models = [_model("z"), _model("a"), _model("m")]
        result = _sort_models(models, prefer_patterns=[])
        assert [m.id for m in result] == ["a", "m", "z"]

    def test_earlier_pattern_wins_over_later(self):
        models = [
            _model("gemini/gemini-2.5-flash"),
            _model("gemini/gemini-flash-lite-latest"),
        ]
        patterns = ["flash-lite-latest", "2.5-flash"]
        result = _sort_models(models, prefer_patterns=patterns)
        assert result[0].id == "gemini/gemini-flash-lite-latest"
        assert result[1].id == "gemini/gemini-2.5-flash"

    def test_unmatched_models_pushed_to_end(self):
        models = [_model("unmatched"), _model("gemini/flash-lite-latest")]
        result = _sort_models(models, prefer_patterns=["flash-lite-latest"])
        assert result[0].id == "gemini/flash-lite-latest"
        assert result[1].id == "unmatched"

    def test_empty_list_returns_empty(self):
        assert _sort_models([], prefer_patterns=["x"]) == []

    def test_pattern_matching_is_case_insensitive(self):
        models = [_model("Gemini/Flash-Lite-Latest")]
        result = _sort_models(models, prefer_patterns=["flash-lite-latest"])
        assert result[0].id == "Gemini/Flash-Lite-Latest"

    def test_three_tier_ordering(self):
        models = [
            _model("gemini/gemini-2.5-flash"),
            _model("gemini/gemini-flash-lite-latest"),
            _model("gemini/gemini-3.1-flash-lite"),
        ]
        patterns = ["flash-lite-latest", "3.1-flash-lite", "2.5-flash"]
        result = _sort_models(models, prefer_patterns=patterns)
        ids = [m.id for m in result]
        assert ids.index("gemini/gemini-flash-lite-latest") < ids.index(
            "gemini/gemini-3.1-flash-lite"
        )
        assert ids.index("gemini/gemini-3.1-flash-lite") < ids.index("gemini/gemini-2.5-flash")


# ── ProviderModelDiscovery — memory cache ──────────────────────────────────────


class TestForProviderMemoryCache:
    async def test_returns_mem_cache_when_fresh(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._mem_cache["groq"] = _ProviderCache(
            models=["llama-3.3-70b-versatile"], fetched_at=time.time()
        )
        result = await disc.for_provider("groq", "https://api.groq.com/openai/v1")
        assert result == ["llama-3.3-70b-versatile"]

    async def test_bypasses_stale_mem_cache_and_fetches_live(self, tmp_path: Path):
        disc = _discovery(tmp_path, ttl=60)
        disc._mem_cache["groq"] = _ProviderCache(
            models=["stale-model"], fetched_at=time.time() - 7200
        )
        mock_cls, _ = _make_httpx_mock(_openai_compat_response(["fresh-model"]))
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_provider("groq", "https://api.groq.com/openai/v1")
        assert "fresh-model" in result


# ── ProviderModelDiscovery — disk cache ────────────────────────────────────────


class TestForProviderDiskCache:
    async def test_uses_fresh_disk_cache_without_http(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        cache_path = disc._cache_path("groq")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({"models": ["disk-model"], "fetched_at": time.time()}))

        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient") as mock_cls:
            result = await disc.for_provider("groq", "https://api.groq.com/openai/v1")

        mock_cls.assert_not_called()
        assert result == ["disk-model"]

    async def test_fetches_live_when_disk_cache_stale(self, tmp_path: Path):
        disc = _discovery(tmp_path, ttl=60)
        cache_path = disc._cache_path("groq")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({"models": ["stale"], "fetched_at": time.time() - 7200}))
        mock_cls, _ = _make_httpx_mock(_openai_compat_response(["live-model"]))
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_provider("groq", "https://api.groq.com/openai/v1")
        assert "live-model" in result


# ── ProviderModelDiscovery — live fetch ────────────────────────────────────────


class TestForProviderLiveFetch:
    async def test_fetches_models_updates_mem_and_disk_cache(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        mock_cls, _ = _make_httpx_mock(_openai_compat_response(["model-1", "model-2"]))
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_provider("groq", "https://api.groq.com/openai/v1")

        assert "model-1" in result
        assert "model-2" in result
        assert "groq" in disc._mem_cache
        assert disc._cache_path("groq").exists()

    async def test_force_refresh_bypasses_all_caches(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._mem_cache["groq"] = _ProviderCache(models=["cached"], fetched_at=time.time())
        mock_cls, _ = _make_httpx_mock(_openai_compat_response(["forced"]))
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_provider(
                "groq", "https://api.groq.com/openai/v1", force_refresh=True
            )
        assert "forced" in result

    async def test_returns_empty_when_no_cache_and_network_fails(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        mock_cls = _error_httpx_mock(httpx.RequestError("refused", request=MagicMock()))
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_provider("groq", "https://api.groq.com/openai/v1")
        assert result == []

    async def test_returns_stale_disk_cache_when_network_fails(self, tmp_path: Path):
        disc = _discovery(tmp_path, ttl=1)
        cache_path = disc._cache_path("groq")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps({"models": ["fallback-model"], "fetched_at": time.time() - 9999})
        )
        mock_cls = _error_httpx_mock(httpx.TimeoutException("timeout"))
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_provider("groq", "https://api.groq.com/openai/v1")
        assert "fallback-model" in result

    async def test_applies_gemini_prefer_patterns_for_google_provider(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        mock_cls, _ = _make_httpx_mock(
            _openai_compat_response(["gemini-2.5-flash", "gemini-flash-lite-latest"])
        )
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_provider(
                "google", "https://generativelanguage.googleapis.com/v1beta/openai"
            )
        assert result[0] == "gemini-flash-lite-latest"

    async def test_applies_custom_prefer_patterns(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        mock_cls, _ = _make_httpx_mock(_openai_compat_response(["alpha", "beta", "gamma"]))
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_provider(
                "test", "https://api.example.com", prefer_patterns=["beta"]
            )
        assert result[0] == "beta"

    async def test_skips_models_with_empty_id(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        mock_cls, _ = _make_httpx_mock(
            {
                "data": [
                    {"id": "", "owned_by": "test"},
                    {"id": "valid-model", "owned_by": "test"},
                ]
            }
        )
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_provider("test", "https://api.example.com")
        assert result == ["valid-model"]

    async def test_sends_bearer_token_when_api_key_provided(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        mock_cls, mock_client = _make_httpx_mock(_openai_compat_response([]))
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            await disc.for_provider("groq", "https://api.groq.com/openai/v1", api_key="sk-groq-key")
        call_kwargs = mock_client.get.call_args[1]
        assert "Authorization" in call_kwargs.get("headers", {})


# ── Exhaustion tracking ─────────────────────────────────────────────────────────


class TestExhaustionTracking:
    def test_mark_then_is_exhausted_returns_true(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc.mark_exhausted("model-a", ttl_seconds=3600)
        assert disc.is_exhausted("model-a") is True

    def test_is_exhausted_false_for_unmarked_model(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        assert disc.is_exhausted("clean-model") is False

    def test_exhaustion_expires_after_ttl(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        # Set deadline already in the past
        disc._exhausted["model-a"] = time.monotonic() - 1
        assert disc.is_exhausted("model-a") is False
        assert "model-a" not in disc._exhausted  # cleaned up

    def test_clear_exhausted_single_model(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc.mark_exhausted("model-a")
        disc.mark_exhausted("model-b")
        disc.clear_exhausted("model-a")
        assert disc.is_exhausted("model-a") is False
        assert disc.is_exhausted("model-b") is True

    def test_clear_exhausted_all_models_when_none_passed(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc.mark_exhausted("model-a")
        disc.mark_exhausted("model-b")
        disc.clear_exhausted()
        assert disc.is_exhausted("model-a") is False
        assert disc.is_exhausted("model-b") is False

    def test_clear_exhausted_nonexistent_model_is_noop(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc.clear_exhausted("does-not-exist")  # should not raise

    def test_mark_exhausted_with_custom_ttl(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc.mark_exhausted("model-a", ttl_seconds=86400)
        assert disc.is_exhausted("model-a") is True


# ── next_working() ──────────────────────────────────────────────────────────────


class TestNextWorking:
    async def test_returns_first_available_model(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._mem_cache["test"] = _ProviderCache(
            models=["m-a", "m-b", "m-c"], fetched_at=time.time()
        )
        result = await disc.next_working("test", "https://api.example.com")
        assert result == "m-a"

    async def test_skips_exhausted_model(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._mem_cache["test"] = _ProviderCache(
            models=["exhausted", "fresh"], fetched_at=time.time()
        )
        disc.mark_exhausted("exhausted")
        result = await disc.next_working("test", "https://api.example.com")
        assert result == "fresh"

    async def test_skips_excluded_models(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._mem_cache["test"] = _ProviderCache(
            models=["excluded", "available"], fetched_at=time.time()
        )
        result = await disc.next_working("test", "https://api.example.com", exclude=["excluded"])
        assert result == "available"

    async def test_returns_none_when_all_exhausted(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._mem_cache["test"] = _ProviderCache(models=["m-a", "m-b"], fetched_at=time.time())
        disc.mark_exhausted("m-a")
        disc.mark_exhausted("m-b")
        result = await disc.next_working("test", "https://api.example.com")
        assert result is None

    async def test_returns_none_for_empty_model_list(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._mem_cache["test"] = _ProviderCache(models=[], fetched_at=time.time())
        result = await disc.next_working("test", "https://api.example.com")
        assert result is None

    async def test_skips_both_exhausted_and_excluded(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._mem_cache["test"] = _ProviderCache(
            models=["exhausted", "excluded", "winner"], fetched_at=time.time()
        )
        disc.mark_exhausted("exhausted")
        result = await disc.next_working("test", "https://api.example.com", exclude=["excluded"])
        assert result == "winner"


# ── for_google() ────────────────────────────────────────────────────────────────


class TestForGoogle:
    async def test_fetches_gemini_models_in_litellm_format(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        google_payload = {
            "models": [
                {
                    "name": "models/gemini-2.5-flash",
                    "supportedGenerationMethods": ["generateContent"],
                },
                {
                    "name": "models/gemini-flash-lite-latest",
                    "supportedGenerationMethods": ["generateContent"],
                },
            ]
        }
        mock_cls, _ = _make_httpx_mock(google_payload)
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_google(api_key="fake-key")

        assert "gemini/gemini-2.5-flash" in result
        assert "gemini/gemini-flash-lite-latest" in result

    async def test_filters_non_gemini_models(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        google_payload = {
            "models": [
                {
                    "name": "models/gemini-2.5-flash",
                    "supportedGenerationMethods": ["generateContent"],
                },
                {
                    "name": "models/text-bison@001",  # not a gemini model
                    "supportedGenerationMethods": ["generateContent"],
                },
            ]
        }
        mock_cls, _ = _make_httpx_mock(google_payload)
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_google(api_key="fake-key")

        assert not any("text-bison" in m for m in result)

    async def test_filters_models_without_generate_content_support(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        google_payload = {
            "models": [
                {
                    "name": "models/gemini-2.5-flash",
                    "supportedGenerationMethods": ["generateContent"],
                },
                {
                    "name": "models/gemini-embedding",
                    "supportedGenerationMethods": ["embedContent"],
                },
            ]
        }
        mock_cls, _ = _make_httpx_mock(google_payload)
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_google(api_key="fake-key")

        assert not any("embedding" in m for m in result)

    async def test_uses_memory_cache_when_fresh(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._mem_cache["google-native"] = _ProviderCache(
            models=["gemini/cached"], fetched_at=time.time()
        )
        result = await disc.for_google(api_key="fake-key")
        assert result == ["gemini/cached"]

    async def test_uses_disk_cache_when_fresh(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        cache_path = disc._cache_path("google-native")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps({"models": ["gemini/disk-cached"], "fetched_at": time.time()})
        )
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient") as mock_cls:
            result = await disc.for_google(api_key="fake-key")
        mock_cls.assert_not_called()
        assert result == ["gemini/disk-cached"]

    async def test_returns_empty_on_network_failure_with_no_cache(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        mock_cls = _error_httpx_mock(httpx.RequestError("refused", request=MagicMock()))
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_google(api_key="fake-key")
        assert result == []

    async def test_applies_gemini_priority_ordering(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        google_payload = {
            "models": [
                {
                    "name": "models/gemini-2.5-flash",
                    "supportedGenerationMethods": ["generateContent"],
                },
                {
                    "name": "models/gemini-flash-lite-latest",
                    "supportedGenerationMethods": ["generateContent"],
                },
            ]
        }
        mock_cls, _ = _make_httpx_mock(google_payload)
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_google(api_key="fake-key")
        assert result[0] == "gemini/gemini-flash-lite-latest"

    async def test_force_refresh_bypasses_caches(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._mem_cache["google-native"] = _ProviderCache(
            models=["gemini/old"], fetched_at=time.time()
        )
        google_payload = {
            "models": [
                {
                    "name": "models/gemini-new-model",
                    "supportedGenerationMethods": ["generateContent"],
                }
            ]
        }
        mock_cls, _ = _make_httpx_mock(google_payload)
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_google(api_key="fake-key", force_refresh=True)
        assert "gemini/gemini-new-model" in result

    async def test_returns_stale_cache_on_network_failure(self, tmp_path: Path):
        disc = _discovery(tmp_path, ttl=1)
        cache_path = disc._cache_path("google-native")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps({"models": ["gemini/stale-model"], "fetched_at": time.time() - 9999})
        )
        mock_cls = _error_httpx_mock(httpx.RequestError("down", request=MagicMock()))
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await disc.for_google(api_key="fake-key")
        assert "gemini/stale-model" in result


# ── Disk cache helpers ──────────────────────────────────────────────────────────


class TestDiskCacheHelpers:
    def test_load_returns_none_when_file_missing(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        assert disc._load_disk_cache("nonexistent") is None

    def test_save_and_load_roundtrip(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        entry = _ProviderCache(models=["m-a", "m-b"], fetched_at=time.time())
        disc._save_disk_cache("test-provider", entry)
        loaded = disc._load_disk_cache("test-provider")
        assert loaded is not None
        assert loaded.models == ["m-a", "m-b"]

    def test_load_returns_none_on_corrupt_json(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        path = disc._cache_path("bad")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not valid json {{")
        assert disc._load_disk_cache("bad") is None

    def test_save_creates_parent_directories(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._save_disk_cache("new-provider", _ProviderCache(models=[], fetched_at=time.time()))
        assert disc._cache_path("new-provider").exists()

    def test_loaded_cache_reflects_correct_freshness(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        recent_ts = time.time()
        disc._save_disk_cache("provider", _ProviderCache(models=["m"], fetched_at=recent_ts))
        loaded = disc._load_disk_cache("provider")
        assert loaded is not None
        assert loaded.is_fresh(3600) is True


# ── best_google_free_model() ─────────────────────────────────────────────────────


class TestBestGoogleFreeModel:
    async def test_returns_first_non_exhausted_model(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._mem_cache["google-native"] = _ProviderCache(
            models=["gemini/exhausted", "gemini/fresh"], fetched_at=time.time()
        )
        disc.mark_exhausted("gemini/exhausted")
        result = await best_google_free_model(api_key="fake-key", discovery=disc)
        assert result == "gemini/fresh"

    async def test_returns_none_when_all_models_exhausted(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._mem_cache["google-native"] = _ProviderCache(
            models=["gemini/only"], fetched_at=time.time()
        )
        disc.mark_exhausted("gemini/only")
        result = await best_google_free_model(api_key="fake-key", discovery=disc)
        assert result is None

    async def test_skips_excluded_models(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._mem_cache["google-native"] = _ProviderCache(
            models=["gemini/model-a", "gemini/model-b"], fetched_at=time.time()
        )
        result = await best_google_free_model(
            api_key="fake-key",
            exclude=["gemini/model-a"],
            discovery=disc,
        )
        assert result == "gemini/model-b"

    async def test_returns_first_model_when_nothing_excluded(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._mem_cache["google-native"] = _ProviderCache(
            models=["gemini/best", "gemini/second"], fetched_at=time.time()
        )
        result = await best_google_free_model(api_key="fake-key", discovery=disc)
        assert result == "gemini/best"

    async def test_returns_none_when_no_models_and_network_fails(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        mock_cls = _error_httpx_mock(httpx.RequestError("down", request=MagicMock()))
        with patch("ttadev.primitives.llm.model_discovery.httpx.AsyncClient", mock_cls):
            result = await best_google_free_model(api_key="fake-key", discovery=disc)
        assert result is None

    async def test_uses_module_level_default_discovery_when_none_given(self, tmp_path: Path):
        disc = _discovery(tmp_path)
        disc._mem_cache["google-native"] = _ProviderCache(
            models=["gemini/default-model"], fetched_at=time.time()
        )
        with patch("ttadev.primitives.llm.model_discovery.default_discovery", disc):
            result = await best_google_free_model(api_key="fake-key")
        assert result == "gemini/default-model"
