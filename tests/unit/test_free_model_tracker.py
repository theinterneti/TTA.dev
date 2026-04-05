"""Unit tests for ttadev.primitives.llm.free_model_tracker.

Covers: ORModel, fetch_free_models, _load_cache, _save_cache,
get_free_models, rank_free_models_by_quality, rank_models_for_role,
FreeModelTracker.refresh / recommend

All HTTP is mocked — no live network calls.
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from ttadev.primitives.llm.free_model_tracker import (
    FreeModelTracker,
    ORModel,
    _load_cache,
    _save_cache,
    fetch_free_models,
    get_free_models,
    rank_free_models_by_quality,
    rank_models_for_role,
)

# ── Shared helpers ──────────────────────────────────────────────────────────────


def _free_model(
    model_id: str = "test/model:free",
    context_length: int = 32768,
    modality: str = "text->text",
) -> ORModel:
    return ORModel(
        id=model_id,
        name=model_id,
        context_length=context_length,
        prompt_price=0.0,
        completion_price=0.0,
        modality=modality,
    )


def _paid_model(model_id: str = "test/paid") -> ORModel:
    return ORModel(
        id=model_id,
        name=model_id,
        context_length=4096,
        prompt_price=0.001,
        completion_price=0.002,
    )


def _or_response(entries: list[dict]) -> dict:
    return {"data": entries}


def _raw_entry(
    model_id: str,
    prompt_price: str = "0",
    completion_price: str = "0",
    modality: str = "text->text",
) -> dict:
    return {
        "id": model_id,
        "name": model_id,
        "context_length": 32768,
        "pricing": {"prompt": prompt_price, "completion": completion_price},
        "architecture": {"modality": modality},
    }


def _make_http_mock(json_payload: dict) -> tuple[MagicMock, AsyncMock]:
    """Wire httpx.AsyncClient as an async context manager returning json_payload."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = json_payload

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    mock_cls = MagicMock()
    mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_cls, mock_client


# ── ORModel.is_free ─────────────────────────────────────────────────────────────


class TestORModelIsFree:
    def test_true_when_both_prices_zero(self):
        model = ORModel(
            id="m", name="m", context_length=4096, prompt_price=0.0, completion_price=0.0
        )
        assert model.is_free is True

    def test_false_when_prompt_price_nonzero(self):
        model = ORModel(
            id="m", name="m", context_length=4096, prompt_price=0.001, completion_price=0.0
        )
        assert model.is_free is False

    def test_false_when_completion_price_nonzero(self):
        model = ORModel(
            id="m", name="m", context_length=4096, prompt_price=0.0, completion_price=0.001
        )
        assert model.is_free is False

    def test_false_when_both_prices_nonzero(self):
        model = ORModel(
            id="m", name="m", context_length=4096, prompt_price=0.001, completion_price=0.002
        )
        assert model.is_free is False


# ── ORModel.is_text_model ───────────────────────────────────────────────────────


class TestORModelIsTextModel:
    def test_true_for_text_to_text_modality(self):
        assert _free_model(modality="text->text").is_text_model is True

    def test_true_for_text_to_text_plus_extra(self):
        # startswith("text->text") still matches
        assert _free_model(modality="text->text+image").is_text_model is True

    def test_false_for_image_modality(self):
        assert _free_model(modality="image->image").is_text_model is False

    def test_false_for_dall_e_model_id(self):
        assert _free_model(model_id="openai/dall-e-3").is_text_model is False

    def test_false_for_stable_diffusion_model_id(self):
        assert _free_model(model_id="stabilityai/stable-diffusion-3").is_text_model is False

    def test_false_for_whisper_model_id(self):
        assert _free_model(model_id="openai/whisper-large-v3").is_text_model is False

    def test_false_for_tts_model_id(self):
        assert _free_model(model_id="openai/tts-1").is_text_model is False

    def test_true_for_llama_instruct_model(self):
        assert _free_model(model_id="meta-llama/llama-3.3-70b-instruct:free").is_text_model is True

    def test_true_for_qwen_model(self):
        assert _free_model(model_id="qwen/qwen3-235b-a22b:free").is_text_model is True


# ── fetch_free_models() ─────────────────────────────────────────────────────────


class TestFetchFreeModels:
    async def test_returns_only_free_text_models(self):
        payload = _or_response(
            [
                _raw_entry("free/model-a", prompt_price="0", completion_price="0"),
                _raw_entry("paid/model-b", prompt_price="0.001", completion_price="0.002"),
            ]
        )
        mock_cls, _ = _make_http_mock(payload)

        with patch("ttadev.primitives.llm.free_model_tracker.httpx.AsyncClient", mock_cls):
            result = await fetch_free_models()

        assert len(result) == 1
        assert result[0].id == "free/model-a"

    async def test_filters_non_text_modality(self):
        payload = _or_response(
            [
                _raw_entry("image/model", modality="image->image"),
                _raw_entry("text/model", modality="text->text"),
            ]
        )
        mock_cls, _ = _make_http_mock(payload)

        with patch("ttadev.primitives.llm.free_model_tracker.httpx.AsyncClient", mock_cls):
            result = await fetch_free_models()

        assert len(result) == 1
        assert result[0].id == "text/model"

    async def test_handles_empty_data_list(self):
        mock_cls, _ = _make_http_mock({"data": []})
        with patch("ttadev.primitives.llm.free_model_tracker.httpx.AsyncClient", mock_cls):
            result = await fetch_free_models()
        assert result == []

    async def test_raises_on_http_status_error(self):
        mock_client = AsyncMock()
        err_resp = MagicMock()
        err_resp.status_code = 429
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Rate limited", request=MagicMock(), response=err_resp
            )
        )
        mock_cls = MagicMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("ttadev.primitives.llm.free_model_tracker.httpx.AsyncClient", mock_cls):
            with pytest.raises(httpx.HTTPStatusError):
                await fetch_free_models()

    async def test_excludes_model_with_malformed_price_string(self):
        # "free" is not parseable as float → defaults to 1.0 → not free → excluded
        payload = _or_response(
            [
                {
                    "id": "weird/model",
                    "name": "Weird",
                    "context_length": 4096,
                    "pricing": {"prompt": "free", "completion": None},
                    "architecture": {"modality": "text->text"},
                }
            ]
        )
        mock_cls, _ = _make_http_mock(payload)
        with patch("ttadev.primitives.llm.free_model_tracker.httpx.AsyncClient", mock_cls):
            result = await fetch_free_models()
        assert result == []

    async def test_excludes_model_with_no_pricing_key(self):
        # Missing "pricing" → defaults to price 1.0 → not free
        payload = _or_response(
            [
                {
                    "id": "no-pricing/model",
                    "name": "NP",
                    "context_length": 4096,
                    "architecture": {"modality": "text->text"},
                }
            ]
        )
        mock_cls, _ = _make_http_mock(payload)
        with patch("ttadev.primitives.llm.free_model_tracker.httpx.AsyncClient", mock_cls):
            result = await fetch_free_models()
        assert result == []

    async def test_sends_auth_header_when_api_key_provided(self):
        mock_cls, mock_client = _make_http_mock({"data": []})
        with patch("ttadev.primitives.llm.free_model_tracker.httpx.AsyncClient", mock_cls):
            await fetch_free_models(api_key="sk-test")  # pragma: allowlist secret
        call_kwargs = mock_client.get.call_args[1]
        assert "Authorization" in call_kwargs.get("headers", {})

    async def test_omits_auth_header_when_no_api_key(self):
        mock_cls, mock_client = _make_http_mock({"data": []})
        with patch("ttadev.primitives.llm.free_model_tracker.httpx.AsyncClient", mock_cls):
            await fetch_free_models(api_key=None)
        call_kwargs = mock_client.get.call_args[1]
        headers = call_kwargs.get("headers", {})
        assert "Authorization" not in headers


# ── _load_cache() and _save_cache() ─────────────────────────────────────────────


class TestCacheHelpers:
    def test_load_returns_empty_and_inf_when_file_missing(self, tmp_path: Path):
        models, age = _load_cache(tmp_path / "nonexistent.json")
        assert models == []
        assert age == float("inf")

    def test_load_returns_models_from_valid_file(self, tmp_path: Path):
        cache_path = tmp_path / "models.json"
        model = _free_model("test/saved-model")
        payload = {
            "fetched_at": time.time(),
            "models": [dataclasses.asdict(model)],
        }
        cache_path.write_text(json.dumps(payload))

        models, age = _load_cache(cache_path)

        assert len(models) == 1
        assert models[0].id == "test/saved-model"
        assert age < 10  # very fresh

    def test_load_returns_empty_on_corrupt_json(self, tmp_path: Path):
        cache_path = tmp_path / "bad.json"
        cache_path.write_text("not json {{")
        models, age = _load_cache(cache_path)
        assert models == []
        assert age == float("inf")

    def test_load_age_reflects_fetched_at_timestamp(self, tmp_path: Path):
        cache_path = tmp_path / "aged.json"
        payload = {"fetched_at": time.time() - 30, "models": []}
        cache_path.write_text(json.dumps(payload))
        _, age = _load_cache(cache_path)
        assert 25 <= age <= 40

    def test_save_creates_file_with_correct_structure(self, tmp_path: Path):
        cache_path = tmp_path / "saved.json"
        _save_cache([_free_model("test/x")], cache_path)

        assert cache_path.exists()
        data = json.loads(cache_path.read_text())
        assert "fetched_at" in data
        assert len(data["models"]) == 1
        assert data["models"][0]["id"] == "test/x"

    def test_save_creates_parent_directories(self, tmp_path: Path):
        cache_path = tmp_path / "a" / "b" / "models.json"
        _save_cache([], cache_path)
        assert cache_path.exists()

    def test_save_and_load_roundtrip(self, tmp_path: Path):
        cache_path = tmp_path / "roundtrip.json"
        original = [
            _free_model("a/model-1", context_length=8192),
            _free_model("b/model-2", context_length=32768),
        ]

        _save_cache(original, cache_path)
        loaded, _ = _load_cache(cache_path)

        assert len(loaded) == 2
        assert {m.id for m in loaded} == {"a/model-1", "b/model-2"}


# ── get_free_models() ───────────────────────────────────────────────────────────


class TestGetFreeModels:
    async def test_returns_fresh_cache_without_fetching(self, tmp_path: Path):
        # Arrange – write fresh cache
        cache_path = tmp_path / "fresh.json"
        model = _free_model("cached/model")
        payload = {"fetched_at": time.time(), "models": [dataclasses.asdict(model)]}
        cache_path.write_text(json.dumps(payload))

        with patch(
            "ttadev.primitives.llm.free_model_tracker.fetch_free_models",
            AsyncMock(),
        ) as mock_fetch:
            result = await get_free_models(cache_path=cache_path, cache_ttl=3600)

        mock_fetch.assert_not_called()
        assert len(result) == 1
        assert result[0].id == "cached/model"

    async def test_fetches_when_cache_is_stale(self, tmp_path: Path):
        cache_path = tmp_path / "stale.json"
        stale = _free_model("stale/model")
        payload = {"fetched_at": time.time() - 7200, "models": [dataclasses.asdict(stale)]}
        cache_path.write_text(json.dumps(payload))

        fresh = [_free_model("fresh/model")]
        with patch(
            "ttadev.primitives.llm.free_model_tracker.fetch_free_models",
            AsyncMock(return_value=fresh),
        ):
            result = await get_free_models(cache_path=cache_path, cache_ttl=3600)

        assert result[0].id == "fresh/model"

    async def test_force_refresh_bypasses_fresh_cache(self, tmp_path: Path):
        cache_path = tmp_path / "force.json"
        old = _free_model("old/model")
        payload = {"fetched_at": time.time(), "models": [dataclasses.asdict(old)]}
        cache_path.write_text(json.dumps(payload))

        new = [_free_model("new/model")]
        with patch(
            "ttadev.primitives.llm.free_model_tracker.fetch_free_models",
            AsyncMock(return_value=new),
        ):
            result = await get_free_models(
                force_refresh=True, cache_path=cache_path, cache_ttl=3600
            )

        assert result[0].id == "new/model"

    async def test_returns_stale_cache_on_network_failure(self, tmp_path: Path):
        cache_path = tmp_path / "fallback.json"
        stale = _free_model("stale/fallback")
        payload = {"fetched_at": time.time() - 9999, "models": [dataclasses.asdict(stale)]}
        cache_path.write_text(json.dumps(payload))

        with patch(
            "ttadev.primitives.llm.free_model_tracker.fetch_free_models",
            AsyncMock(side_effect=httpx.RequestError("timeout", request=MagicMock())),
        ):
            result = await get_free_models(cache_path=cache_path, cache_ttl=1.0)

        assert len(result) == 1
        assert result[0].id == "stale/fallback"

    async def test_returns_empty_when_no_cache_and_network_fails(self, tmp_path: Path):
        cache_path = tmp_path / "empty.json"
        with patch(
            "ttadev.primitives.llm.free_model_tracker.fetch_free_models",
            AsyncMock(side_effect=Exception("network down")),
        ):
            result = await get_free_models(cache_path=cache_path, cache_ttl=1.0)

        assert result == []


# ── rank_free_models_by_quality() ───────────────────────────────────────────────


class TestRankFreeModelsByQuality:
    def test_empty_input_returns_empty(self):
        assert rank_free_models_by_quality([]) == []

    def test_scored_models_appear_before_unscored(self):
        unscored = _free_model("unscored/model:free", context_length=131072)
        scored = _free_model("scored/model:free", context_length=4096)

        def mock_score(model_id: str, benchmark: str):
            return 80.0 if model_id == "scored/model" else None

        with patch(
            "ttadev.primitives.llm.free_model_tracker.get_best_score",
            side_effect=mock_score,
        ):
            result = rank_free_models_by_quality([unscored, scored])

        assert result[0].id == "scored/model:free"
        assert result[1].id == "unscored/model:free"

    def test_unscored_models_sorted_by_context_length_descending(self):
        small = _free_model("small:free", context_length=4096)
        large = _free_model("large:free", context_length=131072)
        medium = _free_model("medium:free", context_length=32768)

        with patch("ttadev.primitives.llm.free_model_tracker.get_best_score", return_value=None):
            result = rank_free_models_by_quality([small, large, medium])

        assert result[0].id == "large:free"
        assert result[1].id == "medium:free"
        assert result[2].id == "small:free"

    def test_scored_models_sorted_by_composite_score_descending(self):
        low = _free_model("low/model:free")
        high = _free_model("high/model:free")

        def mock_score(model_id: str, benchmark: str):
            return 90.0 if model_id == "high/model" else 50.0

        with patch(
            "ttadev.primitives.llm.free_model_tracker.get_best_score",
            side_effect=mock_score,
        ):
            result = rank_free_models_by_quality([low, high])

        assert result[0].id == "high/model:free"

    def test_coding_task_type_queries_aa_coding_benchmark(self):
        model = _free_model("coder/model:free")
        benchmarks_queried = []

        def mock_score(model_id: str, benchmark: str):
            benchmarks_queried.append(benchmark)
            return 75.0

        with patch(
            "ttadev.primitives.llm.free_model_tracker.get_best_score",
            side_effect=mock_score,
        ):
            rank_free_models_by_quality([model], task_type="coding")

        assert "aa_coding" in benchmarks_queried

    def test_math_task_type_queries_aa_math_benchmark(self):
        model = _free_model("math/model:free")
        benchmarks_queried = []

        def mock_score(model_id: str, benchmark: str):
            benchmarks_queried.append(benchmark)
            return 75.0

        with patch(
            "ttadev.primitives.llm.free_model_tracker.get_best_score",
            side_effect=mock_score,
        ):
            rank_free_models_by_quality([model], task_type="math")

        assert "aa_math" in benchmarks_queried

    def test_reasoning_task_type_queries_aa_intelligence_benchmark(self):
        model = _free_model("reasoning/model:free")
        benchmarks_queried = []

        def mock_score(model_id: str, benchmark: str):
            benchmarks_queried.append(benchmark)
            return 75.0

        with patch(
            "ttadev.primitives.llm.free_model_tracker.get_best_score",
            side_effect=mock_score,
        ):
            rank_free_models_by_quality([model], task_type="reasoning")

        assert "aa_intelligence" in benchmarks_queried

    def test_default_task_type_none_queries_intelligence_benchmark(self):
        model = _free_model("general/model:free")
        benchmarks_queried = []

        def mock_score(model_id: str, benchmark: str):
            benchmarks_queried.append(benchmark)
            return 75.0

        with patch(
            "ttadev.primitives.llm.free_model_tracker.get_best_score",
            side_effect=mock_score,
        ):
            rank_free_models_by_quality([model], task_type=None)

        assert "aa_intelligence" in benchmarks_queried

    def test_free_suffix_stripped_before_benchmark_lookup(self):
        model = _free_model("some/model:free")
        looked_up_ids = []

        def mock_score(model_id: str, benchmark: str):
            looked_up_ids.append(model_id)

        with patch(
            "ttadev.primitives.llm.free_model_tracker.get_best_score",
            side_effect=mock_score,
        ):
            rank_free_models_by_quality([model])

        # The ":free" suffix should be stripped before lookup
        assert all(mid == "some/model" for mid in looked_up_ids)
        assert not any(":free" in mid for mid in looked_up_ids)


# ── rank_models_for_role() ───────────────────────────────────────────────────────


class TestRankModelsForRole:
    def test_empty_input_returns_empty(self):
        assert rank_models_for_role([]) == []

    def test_uses_benchmark_ranking_when_data_available(self):
        scored = _free_model("scored/model:free")
        unscored = _free_model("unscored/model:free")

        def mock_score(model_id: str, benchmark: str):
            return 80.0 if model_id == "scored/model" else None

        with patch(
            "ttadev.primitives.llm.free_model_tracker.get_best_score",
            side_effect=mock_score,
        ):
            result = rank_models_for_role([unscored, scored])

        assert result[0].id == "scored/model:free"

    def test_fallback_respects_preferred_list_order(self):
        # No benchmark data → use preferred list
        alpha = _free_model("alpha/model:free", context_length=32768)
        beta = _free_model("beta/model:free", context_length=131072)
        gamma = _free_model("gamma/model:free", context_length=4096)

        with patch("ttadev.primitives.llm.free_model_tracker.get_best_score", return_value=None):
            result = rank_models_for_role(
                [gamma, beta, alpha],
                preferred=["alpha/model:free", "beta/model:free"],
            )

        assert result[0].id == "alpha/model:free"
        assert result[1].id == "beta/model:free"
        # gamma not in preferred → comes last
        assert result[2].id == "gamma/model:free"

    def test_fallback_non_preferred_sorted_by_context_length(self):
        small = _free_model("other/small:free", context_length=4096)
        large = _free_model("other/large:free", context_length=131072)

        with patch("ttadev.primitives.llm.free_model_tracker.get_best_score", return_value=None):
            result = rank_models_for_role([small, large], preferred=[])

        assert result[0].id == "other/large:free"
        assert result[1].id == "other/small:free"

    def test_uses_builtin_preferred_when_preferred_is_none(self):
        builtin = _free_model("qwen/qwen3.6-plus:free", context_length=32768)
        other = _free_model("other/model:free", context_length=4096)

        with patch("ttadev.primitives.llm.free_model_tracker.get_best_score", return_value=None):
            result = rank_models_for_role([other, builtin], preferred=None)

        assert result[0].id == "qwen/qwen3.6-plus:free"

    def test_preferred_model_not_in_candidate_list_is_skipped(self):
        available = _free_model("available/model:free")

        with patch("ttadev.primitives.llm.free_model_tracker.get_best_score", return_value=None):
            result = rank_models_for_role(
                [available],
                preferred=["not-available/model:free", "available/model:free"],
            )

        assert result[0].id == "available/model:free"
        assert len(result) == 1


# ── FreeModelTracker ─────────────────────────────────────────────────────────────


class TestFreeModelTracker:
    async def test_refresh_populates_internal_models(self, tmp_path: Path):
        # Arrange
        cache_path = tmp_path / "tracker.json"
        tracker = FreeModelTracker(cache_path=cache_path, cache_ttl=3600)
        expected = [_free_model("fetched/model:free")]

        with patch(
            "ttadev.primitives.llm.free_model_tracker.get_free_models",
            AsyncMock(return_value=expected),
        ):
            result = await tracker.refresh()

        assert len(result) == 1
        assert result[0].id == "fetched/model:free"
        assert tracker._models is not None

    async def test_refresh_force_passes_force_refresh_true(self, tmp_path: Path):
        tracker = FreeModelTracker(cache_path=tmp_path / "t.json")

        with patch(
            "ttadev.primitives.llm.free_model_tracker.get_free_models",
            AsyncMock(return_value=[]),
        ) as mock_get:
            await tracker.refresh(force=True)

        mock_get.assert_called_once()
        assert mock_get.call_args[1]["force_refresh"] is True

    async def test_recommend_returns_top_ranked_model(self, tmp_path: Path):
        tracker = FreeModelTracker(cache_path=tmp_path / "t.json")
        tracker._models = [
            _free_model("best/model:free", context_length=131072),
            _free_model("ok/model:free", context_length=4096),
        ]

        with patch("ttadev.primitives.llm.free_model_tracker.get_best_score", return_value=None):
            result = await tracker.recommend(preferred=["best/model:free"])

        assert result == "best/model:free"

    async def test_recommend_returns_none_when_no_models(self, tmp_path: Path):
        tracker = FreeModelTracker(cache_path=tmp_path / "t.json")
        tracker._models = []
        result = await tracker.recommend()
        assert result is None

    async def test_recommend_auto_fetches_when_models_not_cached(self, tmp_path: Path):
        tracker = FreeModelTracker(cache_path=tmp_path / "t.json")
        assert tracker._models is None

        fetched = [_free_model("on-demand/model:free")]
        with (
            patch(
                "ttadev.primitives.llm.free_model_tracker.get_free_models",
                AsyncMock(return_value=fetched),
            ),
            patch(
                "ttadev.primitives.llm.free_model_tracker.get_best_score",
                return_value=None,
            ),
        ):
            result = await tracker.recommend(preferred=["on-demand/model:free"])

        assert result == "on-demand/model:free"

    async def test_recommend_uses_in_memory_models_without_re_fetching(self, tmp_path: Path):
        tracker = FreeModelTracker(cache_path=tmp_path / "t.json")
        models = [_free_model("cached/model:free")]

        with patch(
            "ttadev.primitives.llm.free_model_tracker.get_free_models",
            AsyncMock(return_value=models),
        ) as mock_get:
            await tracker.refresh()
            mock_get.reset_mock()

            with patch(
                "ttadev.primitives.llm.free_model_tracker.get_best_score",
                return_value=None,
            ):
                await tracker.recommend(preferred=["cached/model:free"])

        mock_get.assert_not_called()

    async def test_recommend_with_task_type_coding(self, tmp_path: Path):
        tracker = FreeModelTracker(cache_path=tmp_path / "t.json")
        tracker._models = [_free_model("coder/model:free")]

        with patch("ttadev.primitives.llm.free_model_tracker.get_best_score", return_value=None):
            result = await tracker.recommend(task_type="coding")

        assert result == "coder/model:free"

    async def test_recommend_with_task_type_reasoning(self, tmp_path: Path):
        tracker = FreeModelTracker(cache_path=tmp_path / "t.json")
        tracker._models = [_free_model("reasoning/model:free")]

        with patch("ttadev.primitives.llm.free_model_tracker.get_best_score", return_value=None):
            result = await tracker.recommend(task_type="reasoning")

        assert result == "reasoning/model:free"

    def test_init_stores_api_key_and_cache_settings(self, tmp_path: Path):
        cache_path = tmp_path / "t.json"
        tracker = FreeModelTracker(
            api_key="sk-test",  # pragma: allowlist secret
            cache_path=cache_path,
            cache_ttl=999,
        )
        assert tracker._api_key == "sk-test"  # pragma: allowlist secret
        assert tracker._cache_path == cache_path
        assert tracker._cache_ttl == 999
        assert tracker._models is None
