"""Tests for FreeModelTracker and module-level helpers."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.llm.free_model_tracker import (
    FreeModelTracker,
    ORModel,
    _load_cache,
    _save_cache,
    fetch_free_models,
    get_free_models,
    rank_models_for_role,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

_FAKE_API_RESPONSE = {
    "data": [
        {
            "id": "free/model-a:free",
            "name": "Free Model A",
            "context_length": 8192,
            "pricing": {"prompt": "0", "completion": "0"},
        },
        {
            "id": "paid/model-b",
            "name": "Paid Model B",
            "context_length": 16384,
            "pricing": {"prompt": "0.001", "completion": "0.002"},
        },
        {
            "id": "free/model-c:free",
            "name": "Free Model C",
            "context_length": 4096,
            "pricing": {"prompt": "0", "completion": "0"},
        },
    ]
}

_FREE_MODELS = [
    ORModel(
        id="free/model-a:free",
        name="Free Model A",
        context_length=8192,
        prompt_price=0.0,
        completion_price=0.0,
    ),
    ORModel(
        id="free/model-c:free",
        name="Free Model C",
        context_length=4096,
        prompt_price=0.0,
        completion_price=0.0,
    ),
]


def _make_httpx_response(data: dict) -> MagicMock:
    """Return a mock httpx Response with .raise_for_status() and .json()."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=data)
    return resp


# ── ORModel ───────────────────────────────────────────────────────────────────


class TestORModel:
    def test_is_free_true_when_both_prices_zero(self):
        model = ORModel(
            id="x", name="X", context_length=4096, prompt_price=0.0, completion_price=0.0
        )
        assert model.is_free is True

    def test_is_free_false_when_prompt_nonzero(self):
        model = ORModel(
            id="x", name="X", context_length=4096, prompt_price=0.001, completion_price=0.0
        )
        assert model.is_free is False

    def test_is_free_false_when_completion_nonzero(self):
        model = ORModel(
            id="x", name="X", context_length=4096, prompt_price=0.0, completion_price=0.001
        )
        assert model.is_free is False


# ── fetch_free_models ─────────────────────────────────────────────────────────


class TestFetchFreeModels:
    @pytest.mark.asyncio
    async def test_returns_only_free_models(self):
        mock_resp = _make_httpx_response(_FAKE_API_RESPONSE)
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await fetch_free_models()

        assert len(result) == 2
        assert all(m.is_free for m in result)
        ids = {m.id for m in result}
        assert "free/model-a:free" in ids
        assert "free/model-c:free" in ids
        assert "paid/model-b" not in ids

    @pytest.mark.asyncio
    async def test_passes_api_key_as_auth_header(self):
        mock_resp = _make_httpx_response({"data": []})
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_cm):
            await fetch_free_models(api_key="test-key")

        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["headers"]["Authorization"] == "Bearer test-key"

    @pytest.mark.asyncio
    async def test_no_api_key_sends_no_auth_header(self):
        mock_resp = _make_httpx_response({"data": []})
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_cm):
            await fetch_free_models()

        call_kwargs = mock_client.get.call_args[1]
        assert "Authorization" not in call_kwargs.get("headers", {})

    @pytest.mark.asyncio
    async def test_handles_null_pricing_gracefully(self):
        data = {
            "data": [
                {
                    "id": "weird/model:free",
                    "name": "Weird",
                    "context_length": 2048,
                    "pricing": {"prompt": None, "completion": None},
                }
            ]
        }
        mock_resp = _make_httpx_response(data)
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_cm):
            result = await fetch_free_models()

        # null pricing → treated as non-free (price defaults to 1.0)
        assert result == []


# ── _load_cache / _save_cache ─────────────────────────────────────────────────


class TestCacheIO:
    def test_load_cache_returns_empty_when_file_missing(self, tmp_path: Path):
        models, age = _load_cache(tmp_path / "nonexistent.json")
        assert models == []
        assert age == float("inf")

    def test_save_and_load_roundtrip(self, tmp_path: Path):
        cache_file = tmp_path / "cache.json"
        _save_cache(_FREE_MODELS, cache_file)
        loaded, age = _load_cache(cache_file)

        assert len(loaded) == 2
        assert loaded[0].id == "free/model-a:free"
        assert loaded[1].id == "free/model-c:free"
        assert 0 <= age < 5  # just created

    def test_load_cache_handles_corrupt_file(self, tmp_path: Path):
        bad = tmp_path / "bad.json"
        bad.write_text("NOT JSON{{{{")
        models, age = _load_cache(bad)
        assert models == []
        assert age == float("inf")


# ── get_free_models ───────────────────────────────────────────────────────────


class TestGetFreeModels:
    @pytest.mark.asyncio
    async def test_uses_fresh_cache(self, tmp_path: Path):
        cache_file = tmp_path / "cache.json"
        _save_cache(_FREE_MODELS, cache_file)

        with patch("ttadev.primitives.llm.free_model_tracker.fetch_free_models") as mock_fetch:
            result = await get_free_models(cache_path=cache_file, cache_ttl=3600)

        mock_fetch.assert_not_called()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_fetches_when_cache_stale(self, tmp_path: Path):
        cache_file = tmp_path / "cache.json"
        # Write cache with old timestamp
        cache_file.write_text(
            json.dumps(
                {
                    "fetched_at": time.time() - 999999,
                    "models": [m.__dict__ for m in _FREE_MODELS],
                }
            )
        )

        new_models = [
            ORModel(
                id="brand/new:free",
                name="Brand New",
                context_length=32768,
                prompt_price=0.0,
                completion_price=0.0,
            ),
        ]
        with patch(
            "ttadev.primitives.llm.free_model_tracker.fetch_free_models",
            AsyncMock(return_value=new_models),
        ):
            result = await get_free_models(cache_path=cache_file, cache_ttl=60)

        assert result[0].id == "brand/new:free"

    @pytest.mark.asyncio
    async def test_returns_stale_cache_on_network_failure(self, tmp_path: Path):
        cache_file = tmp_path / "cache.json"
        cache_file.write_text(
            json.dumps(
                {
                    "fetched_at": time.time() - 999999,
                    "models": [m.__dict__ for m in _FREE_MODELS],
                }
            )
        )

        with patch(
            "ttadev.primitives.llm.free_model_tracker.fetch_free_models",
            AsyncMock(side_effect=Exception("network down")),
        ):
            result = await get_free_models(cache_path=cache_file, cache_ttl=60)

        assert len(result) == 2  # stale cache returned

    @pytest.mark.asyncio
    async def test_force_refresh_bypasses_fresh_cache(self, tmp_path: Path):
        cache_file = tmp_path / "cache.json"
        _save_cache(_FREE_MODELS, cache_file)

        new_models: list[ORModel] = []
        with patch(
            "ttadev.primitives.llm.free_model_tracker.fetch_free_models",
            AsyncMock(return_value=new_models),
        ):
            result = await get_free_models(
                cache_path=cache_file, cache_ttl=3600, force_refresh=True
            )

        assert result == []


# ── rank_models_for_role ──────────────────────────────────────────────────────


class TestRankModelsForRole:
    def test_preferred_models_appear_first(self):
        models = [
            ORModel(
                id="a:free", name="A", context_length=4096, prompt_price=0.0, completion_price=0.0
            ),
            ORModel(
                id="b:free", name="B", context_length=8192, prompt_price=0.0, completion_price=0.0
            ),
            ORModel(
                id="c:free", name="C", context_length=2048, prompt_price=0.0, completion_price=0.0
            ),
        ]
        ranked = rank_models_for_role(models, preferred=["c:free", "a:free"])
        assert ranked[0].id == "c:free"
        assert ranked[1].id == "a:free"

    def test_remainder_sorted_by_context_length_desc(self):
        models = [
            ORModel(
                id="small:free",
                name="Small",
                context_length=2048,
                prompt_price=0.0,
                completion_price=0.0,
            ),
            ORModel(
                id="large:free",
                name="Large",
                context_length=16384,
                prompt_price=0.0,
                completion_price=0.0,
            ),
            ORModel(
                id="medium:free",
                name="Medium",
                context_length=8192,
                prompt_price=0.0,
                completion_price=0.0,
            ),
        ]
        ranked = rank_models_for_role(models, preferred=[])
        assert ranked[0].id == "large:free"
        assert ranked[1].id == "medium:free"
        assert ranked[2].id == "small:free"

    def test_uses_builtin_defaults_when_preferred_is_none(self):
        models = [
            ORModel(
                id="nousresearch/hermes-3-llama-3.1-405b:free",
                name="Hermes",
                context_length=128000,
                prompt_price=0.0,
                completion_price=0.0,
            ),
            ORModel(
                id="other:free",
                name="Other",
                context_length=4096,
                prompt_price=0.0,
                completion_price=0.0,
            ),
        ]
        ranked = rank_models_for_role(models, preferred=None)
        assert ranked[0].id == "nousresearch/hermes-3-llama-3.1-405b:free"

    def test_empty_models_returns_empty(self):
        assert rank_models_for_role([], preferred=["anything:free"]) == []


# ── FreeModelTracker ──────────────────────────────────────────────────────────


class TestFreeModelTracker:
    @pytest.mark.asyncio
    async def test_refresh_populates_in_memory_models(self, tmp_path: Path):
        tracker = FreeModelTracker(cache_path=tmp_path / "cache.json")
        with patch(
            "ttadev.primitives.llm.free_model_tracker.fetch_free_models",
            AsyncMock(return_value=_FREE_MODELS),
        ):
            models = await tracker.refresh()

        assert models == _FREE_MODELS
        assert tracker._models == _FREE_MODELS

    @pytest.mark.asyncio
    async def test_recommend_returns_best_model_id(self, tmp_path: Path):
        tracker = FreeModelTracker(cache_path=tmp_path / "cache.json")
        tracker._models = _FREE_MODELS  # pre-populate in-memory cache
        best = await tracker.recommend(preferred=["free/model-a:free"])
        assert best == "free/model-a:free"

    @pytest.mark.asyncio
    async def test_recommend_fetches_when_models_none(self, tmp_path: Path):
        tracker = FreeModelTracker(cache_path=tmp_path / "cache.json")
        with patch(
            "ttadev.primitives.llm.free_model_tracker.fetch_free_models",
            AsyncMock(return_value=_FREE_MODELS),
        ):
            best = await tracker.recommend(preferred=["free/model-c:free"])

        assert best == "free/model-c:free"

    @pytest.mark.asyncio
    async def test_recommend_returns_none_when_no_models(self, tmp_path: Path):
        tracker = FreeModelTracker(cache_path=tmp_path / "cache.json")
        tracker._models = []
        result = await tracker.recommend()
        assert result is None
