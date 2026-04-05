"""Unit tests for ttadev.primitives.llm.benchmark_fetcher.

Targets 75%+ statement coverage on BenchmarkFetcher and load_live_benchmarks_into_global.
All HTTP is mocked — no live network calls.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from ttadev.primitives.llm.benchmark_fetcher import (
    BenchmarkFetcher,
    load_live_benchmarks_into_global,
)
from ttadev.primitives.llm.model_benchmarks import BENCHMARK_DATA, ModelBenchmarkMetadata

# ── Test helpers ────────────────────────────────────────────────────────────────


def _fetcher(tmp_path: Path, ttl_hours: float = 24.0) -> BenchmarkFetcher:
    return BenchmarkFetcher(cache_path=tmp_path / "bench.json", ttl_hours=ttl_hours)


def _write_cache(path: Path, entries: list[dict], age_seconds: float = 0.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"fetched_at": time.time() - age_seconds, "benchmarks": entries}
    path.write_text(json.dumps(payload), encoding="utf-8")


def _entry(**kw) -> dict:
    base = dict(
        model_id="test-model",
        benchmark="mmlu",
        score=75.0,
        source_url="https://example.com",
        measured_date="2024-01-01",
        notes="",
    )
    base.update(kw)
    return base


def _mock_http_client(json_payload: dict | list) -> tuple[MagicMock, AsyncMock]:
    """Return (mock_cls, mock_client) wiring httpx.AsyncClient as an async context manager."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = json_payload

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    mock_cls = MagicMock()
    mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_cls, mock_client


# ── get_cached() ────────────────────────────────────────────────────────────────


class TestGetCached:
    def test_empty_when_cache_file_absent(self, tmp_path: Path):
        assert _fetcher(tmp_path).get_cached() == []

    def test_returns_typed_entries_from_valid_cache(self, tmp_path: Path):
        # Arrange
        fetcher = _fetcher(tmp_path)
        _write_cache(
            fetcher.cache_path,
            [_entry(model_id="llama-3.3-70b-versatile", score=80.0)],
        )

        # Act
        result = fetcher.get_cached()

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], ModelBenchmarkMetadata)
        assert result[0].model_id == "llama-3.3-70b-versatile"
        assert result[0].score == 80.0

    def test_returns_all_valid_entries(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        _write_cache(
            fetcher.cache_path,
            [_entry(benchmark="mmlu"), _entry(benchmark="humaneval")],
        )
        assert len(fetcher.get_cached()) == 2

    def test_skips_malformed_entries_silently(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        _write_cache(
            fetcher.cache_path,
            [_entry(), {"model_id": "incomplete"}],  # second is missing required fields
        )
        assert len(fetcher.get_cached()) == 1

    def test_returns_empty_on_corrupt_json(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        fetcher.cache_path.parent.mkdir(parents=True, exist_ok=True)
        fetcher.cache_path.write_text("not json {{", encoding="utf-8")
        assert fetcher.get_cached() == []

    def test_returns_empty_when_benchmarks_list_is_empty(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        _write_cache(fetcher.cache_path, [])
        assert fetcher.get_cached() == []


# ── _cache_is_fresh() ───────────────────────────────────────────────────────────


class TestCacheIsFresh:
    def test_false_when_no_file(self, tmp_path: Path):
        assert _fetcher(tmp_path)._cache_is_fresh() is False

    def test_true_for_recent_cache(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        _write_cache(fetcher.cache_path, [], age_seconds=60)
        assert fetcher._cache_is_fresh() is True

    def test_false_when_cache_older_than_ttl(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path, ttl_hours=1.0)
        _write_cache(fetcher.cache_path, [], age_seconds=7200)  # 2 h > 1 h TTL
        assert fetcher._cache_is_fresh() is False

    def test_false_on_corrupt_json(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        fetcher.cache_path.parent.mkdir(parents=True, exist_ok=True)
        fetcher.cache_path.write_text("broken", encoding="utf-8")
        assert fetcher._cache_is_fresh() is False


# ── _write_cache() ──────────────────────────────────────────────────────────────


class TestWriteCache:
    def test_creates_file_with_correct_structure(self, tmp_path: Path):
        # Arrange
        fetcher = _fetcher(tmp_path)

        # Act
        fetcher._write_cache([_entry()])

        # Assert
        assert fetcher.cache_path.exists()
        data = json.loads(fetcher.cache_path.read_text())
        assert "fetched_at" in data
        assert "benchmarks" in data
        assert len(data["benchmarks"]) == 1

    def test_creates_parent_directories_automatically(self, tmp_path: Path):
        nested = tmp_path / "a" / "b" / "c" / "cache.json"
        fetcher = BenchmarkFetcher(cache_path=nested)
        fetcher._write_cache([])
        assert nested.exists()

    def test_overwrites_existing_cache(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        _write_cache(fetcher.cache_path, [_entry(model_id="old")])
        fetcher._write_cache([_entry(model_id="new")])
        data = json.loads(fetcher.cache_path.read_text())
        assert data["benchmarks"][0]["model_id"] == "new"


# ── _resolve_aa_slug() ──────────────────────────────────────────────────────────


class TestResolveAaSlug:
    def test_known_slug_returns_canonical_id(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        assert fetcher._resolve_aa_slug("llama-3-3-instruct-70b") == "llama-3.3-70b-versatile"

    def test_gemini_slug_maps_correctly(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        assert fetcher._resolve_aa_slug("gemini-2-5-flash") == "models/gemini-2.5-flash"

    def test_deepseek_slug_maps_correctly(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        assert fetcher._resolve_aa_slug("deepseek-r1") == "deepseek-r1"

    def test_qwen3_slug_maps_correctly(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        assert fetcher._resolve_aa_slug("qwen3-32b-instruct") == "qwen/qwen3-32b"

    def test_unknown_slug_returns_none(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        assert fetcher._resolve_aa_slug("totally-unknown-xyz") is None

    def test_empty_slug_returns_none(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        assert fetcher._resolve_aa_slug("") is None


# ── _resolve_hf_fullname() ──────────────────────────────────────────────────────


class TestResolveHfFullname:
    def test_known_fullname_lowercase_maps_correctly(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        result = fetcher._resolve_hf_fullname("meta-llama/Llama-3.3-70B-Instruct")
        assert result == "llama-3.3-70b-versatile"

    def test_case_insensitive_lookup(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        result = fetcher._resolve_hf_fullname("META-LLAMA/LLAMA-3.3-70B-INSTRUCT")
        assert result == "llama-3.3-70b-versatile"

    def test_phi4_fullname_maps_correctly(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        assert fetcher._resolve_hf_fullname("microsoft/Phi-4") == "phi4:latest"

    def test_deepseek_fullname_maps_correctly(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        assert fetcher._resolve_hf_fullname("deepseek-ai/DeepSeek-R1") == "deepseek-r1"

    def test_unknown_fullname_returns_none(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        assert fetcher._resolve_hf_fullname("unknown/model-xyz-9999") is None


# ── _fetch_artificial_analysis() ───────────────────────────────────────────────


class TestFetchArtificialAnalysis:
    async def test_happy_path_produces_expected_benchmark_entries(self, tmp_path: Path):
        # Arrange
        fetcher = _fetcher(tmp_path)
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {
                    "slug": "llama-3-3-instruct-70b",
                    "evaluations": {
                        "artificial_analysis_intelligence_index": 75.5,
                        "artificial_analysis_coding_index": 68.0,
                        "artificial_analysis_math_index": 62.0,
                        "mmlu_pro": 0.654,
                        "gpqa": 0.521,
                        "livecodebench": 0.48,
                        "math_500": 0.83,
                        "aime": 0.35,
                    },
                    "median_output_tokens_per_second": 120.5,
                    "median_time_to_first_token_seconds": 0.45,
                    "pricing": {"price_1m_input_tokens": 0.59},
                }
            ]
        }
        mock_client.get = AsyncMock(return_value=mock_resp)

        # Act
        result = await fetcher._fetch_artificial_analysis(mock_client, "test-key")

        # Assert
        found = {e["benchmark"] for e in result}
        assert "aa_intelligence" in found
        assert "aa_coding" in found
        assert "aa_math" in found
        assert "mmlu_pro" in found
        assert "gpqa" in found
        assert "aa_speed_tok_per_sec" in found
        assert "aa_ttft_seconds" in found
        assert "aa_price_per_1m_input" in found
        assert all(e["model_id"] == "llama-3.3-70b-versatile" for e in result)

    async def test_intelligence_index_not_multiplied_by_100(self, tmp_path: Path):
        # Arrange – aa_intelligence stays 0-100, not multiplied
        fetcher = _fetcher(tmp_path)
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {
                    "slug": "llama-3-3-instruct-70b",
                    "evaluations": {"artificial_analysis_intelligence_index": 75.5},
                }
            ]
        }
        mock_client.get = AsyncMock(return_value=mock_resp)

        # Act
        result = await fetcher._fetch_artificial_analysis(mock_client, "key")

        # Assert – 75.5 stays 75.5, not 7550
        intel = [e for e in result if e["benchmark"] == "aa_intelligence"]
        assert intel[0]["score"] == pytest.approx(75.5)

    async def test_other_scores_multiplied_by_100(self, tmp_path: Path):
        # Arrange – mmlu_pro raw 0.65 → score 65.0
        fetcher = _fetcher(tmp_path)
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {
                    "slug": "llama-3-3-instruct-70b",
                    "evaluations": {"mmlu_pro": 0.65},
                }
            ]
        }
        mock_client.get = AsyncMock(return_value=mock_resp)

        # Act
        result = await fetcher._fetch_artificial_analysis(mock_client, "key")

        # Assert
        mmlu = [e for e in result if e["benchmark"] == "mmlu_pro"]
        assert mmlu[0]["score"] == pytest.approx(65.0)

    async def test_skips_unknown_slugs(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {
                    "slug": "totally-unknown-xyz-9999",
                    "evaluations": {"artificial_analysis_intelligence_index": 80.0},
                }
            ]
        }
        mock_client.get = AsyncMock(return_value=mock_resp)
        result = await fetcher._fetch_artificial_analysis(mock_client, "key")
        assert result == []

    async def test_handles_http_status_error_returns_empty(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        mock_client = AsyncMock()
        err_resp = MagicMock()
        err_resp.status_code = 401
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Unauthorized", request=MagicMock(), response=err_resp
            )
        )
        result = await fetcher._fetch_artificial_analysis(mock_client, "bad-key")
        assert result == []

    async def test_handles_network_error_returns_empty(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.RequestError("refused", request=MagicMock()))
        result = await fetcher._fetch_artificial_analysis(mock_client, "key")
        assert result == []

    async def test_accepts_list_format_response(self, tmp_path: Path):
        # Arrange – AA can return a plain list instead of {"data": [...]}
        fetcher = _fetcher(tmp_path)
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [
            {
                "slug": "llama-3-3-instruct-70b",
                "evaluations": {"artificial_analysis_intelligence_index": 75.0},
            }
        ]
        mock_client.get = AsyncMock(return_value=mock_resp)
        result = await fetcher._fetch_artificial_analysis(mock_client, "key")
        assert any(e["benchmark"] == "aa_intelligence" for e in result)

    async def test_skips_none_eval_values(self, tmp_path: Path):
        # Arrange – all evals are None, no speed/pricing
        fetcher = _fetcher(tmp_path)
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {
                    "slug": "llama-3-3-instruct-70b",
                    "evaluations": {
                        "artificial_analysis_intelligence_index": None,
                        "artificial_analysis_coding_index": None,
                    },
                    "median_output_tokens_per_second": None,
                    "median_time_to_first_token_seconds": None,
                    "pricing": {},
                }
            ]
        }
        mock_client.get = AsyncMock(return_value=mock_resp)
        result = await fetcher._fetch_artificial_analysis(mock_client, "key")
        assert result == []


# ── _fetch_hf_leaderboard() ─────────────────────────────────────────────────────


class TestFetchHfLeaderboard:
    async def test_happy_path_produces_all_benchmark_types(self, tmp_path: Path):
        # Arrange
        fetcher = _fetcher(tmp_path)
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "rows": [
                {
                    "row": {
                        "fullname": "meta-llama/Llama-3.3-70B-Instruct",
                        "MMLU-PRO": 63.4,
                        "GPQA": 50.1,
                        "BBH": 78.3,
                        "MATH Lvl 5": 65.0,
                        "MUSR": 42.0,
                        "IFEval": 88.0,
                        "Average \u2b06\ufe0f": 65.0,
                    }
                }
            ],
            "num_rows_total": 1,
        }
        mock_client.get = AsyncMock(return_value=mock_resp)

        # Act
        result = await fetcher._fetch_hf_leaderboard(mock_client)

        # Assert
        found = {e["benchmark"] for e in result}
        for expected in ("mmlu_pro", "gpqa", "bbh", "math", "musr", "ifeval", "hf_average"):
            assert expected in found
        assert all(e["model_id"] == "llama-3.3-70b-versatile" for e in result)

    async def test_skips_unknown_fullnames(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "rows": [{"row": {"fullname": "unknown/xyz-9999", "MMLU-PRO": 65.0}}],
            "num_rows_total": 1,
        }
        mock_client.get = AsyncMock(return_value=mock_resp)
        result = await fetcher._fetch_hf_leaderboard(mock_client)
        assert result == []

    async def test_skips_rows_without_fullname_key(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "rows": [{"row": {"MMLU-PRO": 65.0}}],  # no fullname
            "num_rows_total": 1,
        }
        mock_client.get = AsyncMock(return_value=mock_resp)
        result = await fetcher._fetch_hf_leaderboard(mock_client)
        assert result == []

    async def test_handles_http_status_error_returns_empty(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        mock_client = AsyncMock()
        err_resp = MagicMock()
        err_resp.status_code = 503
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("Unavailable", request=MagicMock(), response=err_resp)
        )
        result = await fetcher._fetch_hf_leaderboard(mock_client)
        assert result == []

    async def test_handles_network_error_returns_empty(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.RequestError("timeout", request=MagicMock()))
        result = await fetcher._fetch_hf_leaderboard(mock_client)
        assert result == []

    async def test_pagination_stops_on_empty_rows(self, tmp_path: Path):
        # Arrange – page 1 has rows, page 2 is empty → stops
        fetcher = _fetcher(tmp_path)
        mock_client = AsyncMock()

        page1 = MagicMock()
        page1.raise_for_status = MagicMock()
        page1.json.return_value = {
            "rows": [{"row": {"fullname": "meta-llama/Llama-3.3-70B-Instruct", "MMLU-PRO": 63.0}}],
            "num_rows_total": 5000,
        }
        page2 = MagicMock()
        page2.raise_for_status = MagicMock()
        page2.json.return_value = {"rows": [], "num_rows_total": 5000}

        mock_client.get = AsyncMock(side_effect=[page1, page2])

        result = await fetcher._fetch_hf_leaderboard(mock_client)

        assert len(result) >= 1
        assert mock_client.get.call_count == 2

    async def test_pagination_stops_when_offset_reaches_total(self, tmp_path: Path):
        # Arrange – exactly 1 row, num_rows_total=1 → no page 2 requested
        fetcher = _fetcher(tmp_path)
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "rows": [{"row": {"fullname": "meta-llama/Llama-3.3-70B-Instruct", "MMLU-PRO": 63.0}}],
            "num_rows_total": 1,
        }
        mock_client.get = AsyncMock(return_value=mock_resp)

        await fetcher._fetch_hf_leaderboard(mock_client)

        assert mock_client.get.call_count == 1


# ── refresh() ───────────────────────────────────────────────────────────────────


class TestRefresh:
    async def test_returns_cached_when_fresh_without_network(self, tmp_path: Path):
        # Arrange
        fetcher = _fetcher(tmp_path)
        _write_cache(fetcher.cache_path, [_entry()], age_seconds=30)

        # Act
        with (
            patch.object(fetcher, "_fetch_artificial_analysis", AsyncMock()) as mock_aa,
            patch.object(fetcher, "_fetch_hf_leaderboard", AsyncMock()) as mock_hf,
        ):
            result = await fetcher.refresh()

        # Assert – helpers not called
        mock_aa.assert_not_called()
        mock_hf.assert_not_called()
        assert len(result) == 1

    async def test_fetches_when_stale_and_merges_sources(self, tmp_path: Path):
        # Arrange
        fetcher = _fetcher(tmp_path, ttl_hours=1.0)
        _write_cache(fetcher.cache_path, [], age_seconds=7200)

        aa_entry = _entry(benchmark="aa_intelligence", score=80.0)
        hf_entry = _entry(benchmark="mmlu_pro", score=65.0)

        with (
            patch("ttadev.primitives.llm.benchmark_fetcher.httpx.AsyncClient") as mock_cls,
            patch.object(fetcher, "_fetch_artificial_analysis", AsyncMock(return_value=[aa_entry])),
            patch.object(fetcher, "_fetch_hf_leaderboard", AsyncMock(return_value=[hf_entry])),
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            # Provide api_key directly so AA branch is taken
            result = await fetcher.refresh(api_key="test-key")

        found = {e.benchmark for e in result}
        assert "aa_intelligence" in found
        assert "mmlu_pro" in found

    async def test_force_true_bypasses_fresh_cache(self, tmp_path: Path):
        # Arrange – fresh cache, but force=True
        fetcher = _fetcher(tmp_path)
        _write_cache(fetcher.cache_path, [_entry(benchmark="old")], age_seconds=5)

        new_entry = _entry(benchmark="aa_intelligence", score=99.0)

        with (
            patch("ttadev.primitives.llm.benchmark_fetcher.httpx.AsyncClient") as mock_cls,
            patch.object(
                fetcher, "_fetch_artificial_analysis", AsyncMock(return_value=[new_entry])
            ),
            patch.object(fetcher, "_fetch_hf_leaderboard", AsyncMock(return_value=[])),
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await fetcher.refresh(api_key="test-key", force=True)

        assert any(e.benchmark == "aa_intelligence" for e in result)

    async def test_deduplicates_same_model_benchmark_pair(self, tmp_path: Path):
        # Arrange – same (model_id, benchmark) from both AA and HF
        fetcher = _fetcher(tmp_path)
        dup = _entry(model_id="test-model", benchmark="mmlu_pro", score=65.0)

        with (
            patch("ttadev.primitives.llm.benchmark_fetcher.httpx.AsyncClient") as mock_cls,
            patch.object(fetcher, "_fetch_artificial_analysis", AsyncMock(return_value=[dup])),
            patch.object(fetcher, "_fetch_hf_leaderboard", AsyncMock(return_value=[dup])),
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await fetcher.refresh(api_key="test-key", force=True)

        assert len(result) == 1

    async def test_skips_aa_when_no_api_key(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Arrange – no api_key arg and no env var
        monkeypatch.delenv("ARTIFICIAL_ANALYSIS_API_KEY", raising=False)
        fetcher = _fetcher(tmp_path)
        hf_entry = _entry(benchmark="mmlu_pro")

        with (
            patch("ttadev.primitives.llm.benchmark_fetcher.httpx.AsyncClient") as mock_cls,
            patch.object(
                fetcher, "_fetch_artificial_analysis", AsyncMock(return_value=[])
            ) as mock_aa,
            patch.object(fetcher, "_fetch_hf_leaderboard", AsyncMock(return_value=[hf_entry])),
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await fetcher.refresh(api_key=None, force=True)

        # AA not called (no key available)
        mock_aa.assert_not_called()
        assert len(result) == 1

    async def test_calls_aa_when_api_key_provided(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange – explicit api_key triggers AA call
        monkeypatch.delenv("ARTIFICIAL_ANALYSIS_API_KEY", raising=False)
        fetcher = _fetcher(tmp_path)
        aa_entry = _entry(benchmark="aa_intelligence", score=80.0)

        with (
            patch("ttadev.primitives.llm.benchmark_fetcher.httpx.AsyncClient") as mock_cls,
            patch.object(
                fetcher, "_fetch_artificial_analysis", AsyncMock(return_value=[aa_entry])
            ) as mock_aa,
            patch.object(fetcher, "_fetch_hf_leaderboard", AsyncMock(return_value=[])),
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            await fetcher.refresh(api_key="explicit-key", force=True)

        mock_aa.assert_called_once()

    async def test_writes_cache_file_after_fetch(self, tmp_path: Path):
        fetcher = _fetcher(tmp_path)
        entry = _entry(benchmark="aa_intelligence", score=77.0)

        with (
            patch("ttadev.primitives.llm.benchmark_fetcher.httpx.AsyncClient") as mock_cls,
            patch.object(fetcher, "_fetch_artificial_analysis", AsyncMock(return_value=[entry])),
            patch.object(fetcher, "_fetch_hf_leaderboard", AsyncMock(return_value=[])),
        ):
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            await fetcher.refresh(force=True)

        assert fetcher.cache_path.exists()


# ── load_live_benchmarks_into_global() ──────────────────────────────────────────


class TestLoadLiveBenchmarksIntoGlobal:
    def test_noop_when_cache_empty(self):
        original_len = len(BENCHMARK_DATA)
        with patch("ttadev.primitives.llm.benchmark_fetcher.BenchmarkFetcher") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.get_cached.return_value = []
            mock_cls.return_value = mock_instance
            load_live_benchmarks_into_global()
        assert len(BENCHMARK_DATA) == original_len

    def test_appends_new_entries_not_already_present(self):
        unique_id = "test-unique-model-zyxwvuts-99999"
        live_entry = ModelBenchmarkMetadata(
            model_id=unique_id,
            benchmark="mmlu_pro",
            score=85.0,
            source_url="https://example.com",
            measured_date="2024-01-01",
        )
        original_len = len(BENCHMARK_DATA)
        with patch("ttadev.primitives.llm.benchmark_fetcher.BenchmarkFetcher") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.get_cached.return_value = [live_entry]
            mock_cls.return_value = mock_instance
            load_live_benchmarks_into_global()
        try:
            assert len(BENCHMARK_DATA) == original_len + 1
            assert any(e.model_id == unique_id for e in BENCHMARK_DATA)
        finally:
            for i in range(len(BENCHMARK_DATA) - 1, -1, -1):
                if BENCHMARK_DATA[i].model_id == unique_id:
                    BENCHMARK_DATA.pop(i)

    def test_idempotent_does_not_duplicate_entries(self):
        unique_id = "test-idempotent-model-abcdef123"
        live_entry = ModelBenchmarkMetadata(
            model_id=unique_id,
            benchmark="mmlu",
            score=70.0,
            source_url="https://example.com",
            measured_date="2024-01-01",
        )
        with patch("ttadev.primitives.llm.benchmark_fetcher.BenchmarkFetcher") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.get_cached.return_value = [live_entry]
            mock_cls.return_value = mock_instance
            load_live_benchmarks_into_global()
            load_live_benchmarks_into_global()
        try:
            matching = [e for e in BENCHMARK_DATA if e.model_id == unique_id]
            assert len(matching) == 1
        finally:
            for i in range(len(BENCHMARK_DATA) - 1, -1, -1):
                if BENCHMARK_DATA[i].model_id == unique_id:
                    BENCHMARK_DATA.pop(i)
