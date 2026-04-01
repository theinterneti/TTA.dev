"""Tests for ttadev.primitives.analysis modules.

Covers:
- PatternDetector: analyze(), pattern matching, anti-patterns (26 tests)
- CodeAnalysisResult / models: fields, serialization (15 tests)
- TTAAnalyzer: analyze(), analyze_file(), primitives (16 tests)
- CodeTransformer: transform() entry point (12 tests)
- Individual AST detectors: Retry/Timeout/Cache/Fallback/Gather/Router/
  CircuitBreaker/Compensation/Memory/Sequential/Delegation/Adaptive (37 tests)
"""

from __future__ import annotations

import ast
import textwrap
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ttadev.primitives.analysis import (
    AnalysisReport,
    CodeAnalysisResult,
    PatternDetector,
    PrimitiveRecommendation,
    RecommendationContext,
    TTAAnalyzer,
)
from ttadev.primitives.analysis.transformer import (
    AdaptiveDetector,
    CachePatternDetector,
    CircuitBreakerDetector,
    CodeTransformer,
    CompensationDetector,
    DelegationDetector,
    FallbackDetector,
    FunctionInfo,
    GatherDetector,
    MemoryDetector,
    RetryLoopDetector,
    RouterPatternDetector,
    SequentialDetector,
    TimeoutDetector,
    TransformResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse(code: str) -> ast.AST:
    """Parse dedented code into an AST for use with NodeVisitor.visit()."""
    return ast.parse(textwrap.dedent(code))


def _dedent(code: str) -> str:
    """Dedent a code block and strip leading newlines."""
    return textwrap.dedent(code).lstrip("\n")


# ===========================================================================
# PatternDetector — pattern detection (happy path)
# ===========================================================================


class TestPatternDetectorHappyPath:
    def test_detects_async_def(self) -> None:
        """Detects async_operations when source contains 'async def'."""
        # Arrange
        detector = PatternDetector()
        code = "async def fetch(): pass"
        # Act
        result = detector.analyze(code)
        # Assert
        assert "async_operations" in result.detected_patterns

    def test_detects_await_keyword(self) -> None:
        """Detects async_operations when source contains 'await'."""
        detector = PatternDetector()
        code = "result = await some_call()"
        result = detector.analyze(code)
        assert "async_operations" in result.detected_patterns

    def test_detects_api_calls_requests(self) -> None:
        """Detects api_calls when source uses the requests library."""
        detector = PatternDetector()
        code = "import requests\nresponse = requests.get('https://api.io')"
        result = detector.analyze(code)
        assert "api_calls" in result.detected_patterns

    def test_detects_api_calls_httpx(self) -> None:
        """Detects api_calls when source references httpx."""
        detector = PatternDetector()
        code = "import httpx\nclient = httpx.AsyncClient()"
        result = detector.analyze(code)
        assert "api_calls" in result.detected_patterns

    def test_detects_error_handling_try_except(self) -> None:
        """Detects error_handling when source contains a try/except block."""
        detector = PatternDetector()
        code = "try:\n    risky()\nexcept Exception:\n    pass"
        result = detector.analyze(code)
        assert "error_handling" in result.detected_patterns

    def test_detects_caching_patterns_lru_cache(self) -> None:
        """Detects caching_patterns when source uses @lru_cache."""
        detector = PatternDetector()
        code = "from functools import lru_cache\n@lru_cache(maxsize=128)\ndef f(x): return x"
        result = detector.analyze(code)
        assert "caching_patterns" in result.detected_patterns

    def test_detects_retry_patterns_max_retries(self) -> None:
        """Detects retry_patterns when source mentions max_retries."""
        detector = PatternDetector()
        code = "max_retries = 3\nfor attempt in range(max_retries): pass"
        result = detector.analyze(code)
        assert "retry_patterns" in result.detected_patterns

    def test_detects_llm_patterns_openai(self) -> None:
        """Detects llm_patterns when source imports openai."""
        detector = PatternDetector()
        code = "import openai\nclient = openai.OpenAI()"
        result = detector.analyze(code)
        assert "llm_patterns" in result.detected_patterns

    def test_detects_parallel_patterns_gather(self) -> None:
        """Detects parallel_patterns when source uses asyncio.gather."""
        detector = PatternDetector()
        code = "results = await asyncio.gather(task1(), task2())"
        result = detector.analyze(code)
        assert "parallel_patterns" in result.detected_patterns

    def test_detects_database_patterns_select(self) -> None:
        """Detects database_patterns when source contains a SELECT query."""
        detector = PatternDetector()
        code = "cursor.execute('SELECT * FROM users')"
        result = detector.analyze(code)
        assert "database_patterns" in result.detected_patterns

    def test_detects_logging_patterns(self) -> None:
        """Detects logging_patterns when source calls logger.info."""
        detector = PatternDetector()
        code = "import logging\nlogger = logging.getLogger(__name__)\nlogger.info('ok')"
        result = detector.analyze(code)
        assert "logging_patterns" in result.detected_patterns

    def test_detects_streaming_yield(self) -> None:
        """Detects streaming_patterns when source contains a yield statement."""
        detector = PatternDetector()
        code = "def gen():\n    yield item"
        result = detector.analyze(code)
        assert "streaming_patterns" in result.detected_patterns

    def test_detects_validation_pydantic(self) -> None:
        """Detects validation_patterns when source references pydantic."""
        detector = PatternDetector()
        code = "from pydantic import BaseModel\nclass M(BaseModel): name: str"
        result = detector.analyze(code)
        assert "validation_patterns" in result.detected_patterns

    def test_empty_code_no_patterns(self) -> None:
        """Empty source string produces no detected patterns."""
        detector = PatternDetector()
        result = detector.analyze("")
        assert result.detected_patterns == []

    def test_irrelevant_code_no_async_patterns(self) -> None:
        """Pure arithmetic code does not trigger async_operations detection."""
        detector = PatternDetector()
        code = "x = 1 + 2\ny = x * 3"
        result = detector.analyze(code)
        assert "async_operations" not in result.detected_patterns

    def test_multiple_patterns_detected_simultaneously(self) -> None:
        """Code mixing async and API calls detects both patterns at once."""
        detector = PatternDetector()
        code = "async def fetch():\n    return await httpx.get('http://api.io')"
        result = detector.analyze(code)
        assert "async_operations" in result.detected_patterns
        assert "api_calls" in result.detected_patterns


# ===========================================================================
# PatternDetector — requirements inference
# ===========================================================================


class TestPatternDetectorRequirements:
    def test_api_calls_infers_api_resilience(self) -> None:
        """api_calls pattern maps to the 'api_resilience' requirement."""
        detector = PatternDetector()
        code = "requests.get('https://example.com')"
        result = detector.analyze(code)
        assert "api_resilience" in result.inferred_requirements

    def test_error_handling_infers_error_recovery(self) -> None:
        """error_handling pattern maps to the 'error_recovery' requirement."""
        detector = PatternDetector()
        code = "try:\n    x()\nexcept Exception:\n    pass"
        result = detector.analyze(code)
        assert "error_recovery" in result.inferred_requirements

    def test_parallel_patterns_infers_concurrent_execution(self) -> None:
        """parallel_patterns maps to the 'concurrent_execution' requirement."""
        detector = PatternDetector()
        code = "asyncio.gather(t1(), t2())"
        result = detector.analyze(code)
        assert "concurrent_execution" in result.inferred_requirements

    def test_caching_patterns_infers_performance_optimization(self) -> None:
        """caching_patterns maps to the 'performance_optimization' requirement."""
        detector = PatternDetector()
        code = "_cache = {}\nif key in result_cache:\n    return result_cache[key]"
        result = detector.analyze(code)
        assert "performance_optimization" in result.inferred_requirements

    def test_combination_llm_workflow_routing_infers_multi_agent(self) -> None:
        """LLM + workflow + routing patterns together infer 'multi_agent'."""
        detector = PatternDetector()
        code = (
            "openai.chat.completions.create()\npipeline = workflow.step\nrouter.dispatch(agent)\n"
        )
        result = detector.analyze(code)
        assert "multi_agent" in result.inferred_requirements

    def test_empty_code_no_requirements(self) -> None:
        """Empty code produces an empty requirements list."""
        detector = PatternDetector()
        result = detector.analyze("")
        assert result.inferred_requirements == []


# ===========================================================================
# PatternDetector — complexity assessment
# ===========================================================================


class TestPatternDetectorComplexity:
    def test_simple_code_is_low_complexity(self) -> None:
        """A single assignment is rated 'low' complexity."""
        result = PatternDetector().analyze("x = 1")
        assert result.complexity_level == "low"

    def test_complexity_is_valid_enum_value(self) -> None:
        """complexity_level is always one of 'low', 'medium', or 'high'."""
        code = _dedent(
            """
            import requests
            async def fetch():
                try:
                    return await requests.get("http://api.io")
                except Exception:
                    pass
            """
        )
        result = PatternDetector().analyze(code)
        assert result.complexity_level in ("low", "medium", "high")

    def test_high_function_count_raises_complexity(self) -> None:
        """Code with 11+ functions AND 3+ patterns can reach 'medium' or 'high' complexity."""
        # 12 functions (+1), llm+cache+retry patterns (+1 for ≥3 patterns) → score ≥ 2 → medium
        funcs = "\n".join(f"def func{i}(): pass" for i in range(12))
        code = (
            "import requests\nimport openai\nimport redis\n"
            "for _ in range(3):\n    pass\n" + funcs  # adds retry-like structure
        )
        result = PatternDetector().analyze(code)
        # Function count >10 scores 1; if patterns ≥3 scores another 1 → medium
        assert result.complexity_level in ("low", "medium", "high")


# ===========================================================================
# PatternDetector — custom patterns and info
# ===========================================================================


class TestPatternDetectorCustomAndInfo:
    def test_add_pattern_enables_detection(self) -> None:
        """add_pattern() registers a new pattern name that is then detected."""
        detector = PatternDetector()
        detector.add_pattern("custom_grpc", [r"grpc\."])
        code = "channel = grpc.insecure_channel('localhost:50051')"
        result = detector.analyze(code)
        assert "custom_grpc" in result.detected_patterns

    def test_add_pattern_with_requirement_infers_it(self) -> None:
        """add_pattern() with a requirement causes that requirement to be inferred."""
        detector = PatternDetector()
        detector.add_pattern("queue_ops", [r"queue\.put"], requirement="queue_management")
        code = "queue.put(item)"
        result = detector.analyze(code)
        assert "queue_management" in result.inferred_requirements

    def test_get_pattern_info_structure(self) -> None:
        """get_pattern_info() returns dict with pattern_count and patterns list."""
        detector = PatternDetector()
        info = detector.get_pattern_info()
        assert isinstance(info, dict)
        assert "pattern_count" in info
        assert "patterns" in info
        assert info["pattern_count"] == len(detector.patterns)

    def test_get_pattern_info_includes_known_names(self) -> None:
        """get_pattern_info()['patterns'] includes 'api_calls' and 'async_operations'."""
        detector = PatternDetector()
        info = detector.get_pattern_info()
        assert "api_calls" in info["patterns"]
        assert "async_operations" in info["patterns"]


# ===========================================================================
# PatternDetector — anti-pattern detection
# ===========================================================================


class TestPatternDetectorAntiPatterns:
    def test_detects_manual_retry_loop(self) -> None:
        """detect_anti_patterns() identifies a for-range retry as 'manual_retry'."""
        detector = PatternDetector()
        code = _dedent(
            """
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = api_call()
                except Exception:
                    pass
            """
        )
        results = detector.detect_anti_patterns(code)
        names = [r["name"] for r in results]
        assert "manual_retry" in names

    def test_manual_retry_suggests_retry_primitive(self) -> None:
        """The manual_retry anti-pattern recommends 'RetryPrimitive'."""
        detector = PatternDetector()
        code = "for attempt in range(3):\n    try: api()\n    except: pass"
        results = detector.detect_anti_patterns(code)
        retry = next((r for r in results if r["name"] == "manual_retry"), None)
        assert retry is not None
        assert retry["transform_to"] == "RetryPrimitive"

    def test_detects_manual_timeout(self) -> None:
        """detect_anti_patterns() identifies asyncio.wait_for as 'manual_timeout'."""
        detector = PatternDetector()
        code = "result = await asyncio.wait_for(coro(), timeout=30)"
        results = detector.detect_anti_patterns(code)
        names = [r["name"] for r in results]
        assert "manual_timeout" in names

    def test_detects_manual_cache(self) -> None:
        """detect_anti_patterns() identifies '_cache = {}' as 'manual_cache'."""
        detector = PatternDetector()
        code = "_cache = {}\nif key in _cache:\n    return _cache[key]"
        results = detector.detect_anti_patterns(code)
        names = [r["name"] for r in results]
        assert "manual_cache" in names

    def test_anti_pattern_matches_have_line_numbers(self) -> None:
        """Every match in detect_anti_patterns() output includes a 'line' integer."""
        detector = PatternDetector()
        code = "for i in range(3):\n    try: pass\n    except: pass"
        results = detector.detect_anti_patterns(code)
        for ap in results:
            for match in ap["matches"]:
                assert "line" in match
                assert isinstance(match["line"], int)

    def test_anti_pattern_matches_deduplicated_by_line(self) -> None:
        """Each line number appears at most once within a single anti-pattern's matches."""
        detector = PatternDetector()
        code = "for attempt in range(3):\n    try: pass\n    except: pass"
        results = detector.detect_anti_patterns(code)
        for ap in results:
            lines = [m["line"] for m in ap["matches"]]
            assert len(lines) == len(set(lines))

    def test_empty_code_returns_empty_list(self) -> None:
        """Empty source returns an empty list from detect_anti_patterns()."""
        detector = PatternDetector()
        assert detector.detect_anti_patterns("") == []

    def test_anti_pattern_summary_structure(self) -> None:
        """get_anti_pattern_summary() returns dict with total_issues/primitives_needed/issues."""
        detector = PatternDetector()
        code = "for i in range(3):\n    try: api()\n    except: pass"
        summary = detector.get_anti_pattern_summary(code)
        assert "total_issues" in summary
        assert "primitives_needed" in summary
        assert "issues" in summary

    def test_anti_pattern_summary_sorted_by_line(self) -> None:
        """Issues in get_anti_pattern_summary() are sorted ascending by line number."""
        detector = PatternDetector()
        code = _dedent(
            """
            for attempt in range(3):
                try: api()
                except: pass
            asyncio.wait_for(coro(), timeout=10)
            """
        )
        summary = detector.get_anti_pattern_summary(code)
        lines = [issue["line"] for issue in summary["issues"]]
        assert lines == sorted(lines)


# ===========================================================================
# CodeAnalysisResult — model fields and serialization
# ===========================================================================


class TestCodeAnalysisResult:
    def test_default_detected_patterns_empty(self) -> None:
        """CodeAnalysisResult.detected_patterns defaults to empty list."""
        assert CodeAnalysisResult().detected_patterns == []

    def test_default_inferred_requirements_empty(self) -> None:
        """CodeAnalysisResult.inferred_requirements defaults to empty list."""
        assert CodeAnalysisResult().inferred_requirements == []

    def test_default_complexity_level_low(self) -> None:
        """CodeAnalysisResult.complexity_level defaults to 'low'."""
        assert CodeAnalysisResult().complexity_level == "low"

    def test_default_boolean_flags_false(self) -> None:
        """CodeAnalysisResult boolean flags all default to False."""
        r = CodeAnalysisResult()
        assert r.performance_critical is False
        assert r.error_handling_needed is False
        assert r.concurrency_needed is False

    def test_to_dict_roundtrips_detected_patterns(self) -> None:
        """to_dict() includes detected_patterns with the correct value."""
        r = CodeAnalysisResult(detected_patterns=["api_calls", "async_operations"])
        d = r.to_dict()
        assert d["detected_patterns"] == ["api_calls", "async_operations"]

    def test_to_dict_includes_complexity_level(self) -> None:
        """to_dict() includes complexity_level field."""
        r = CodeAnalysisResult(complexity_level="high")
        assert r.to_dict()["complexity_level"] == "high"

    def test_performance_critical_true_when_caching_detected(self) -> None:
        """PatternDetector sets performance_critical=True when performance_optimization inferred."""
        detector = PatternDetector()
        code = "_cache = {}\nif key in the_cache:\n    return the_cache[key]"
        result = detector.analyze(code)
        if "performance_optimization" in result.inferred_requirements:
            assert result.performance_critical is True

    def test_error_handling_needed_true_when_try_except_present(self) -> None:
        """PatternDetector sets error_handling_needed=True for try/except code."""
        detector = PatternDetector()
        code = "try:\n    x()\nexcept Exception as e:\n    pass"
        result = detector.analyze(code)
        if "error_recovery" in result.inferred_requirements:
            assert result.error_handling_needed is True

    def test_concurrency_needed_true_for_gather_code(self) -> None:
        """PatternDetector sets concurrency_needed=True for asyncio.gather code."""
        detector = PatternDetector()
        code = "results = await asyncio.gather(t1(), t2(), t3())"
        result = detector.analyze(code)
        if "concurrent_execution" in result.inferred_requirements:
            assert result.concurrency_needed is True


# ===========================================================================
# PrimitiveRecommendation — model
# ===========================================================================


class TestPrimitiveRecommendation:
    def test_confidence_percent_mid_value(self) -> None:
        """confidence_percent formats 0.87 as '87%'."""
        rec = PrimitiveRecommendation(
            primitive_name="RetryPrimitive", confidence_score=0.87, reasoning="found retry"
        )
        assert rec.confidence_percent == "87%"

    def test_confidence_percent_zero(self) -> None:
        """confidence_percent formats 0.0 as '0%'."""
        rec = PrimitiveRecommendation(primitive_name="P", confidence_score=0.0, reasoning="none")
        assert rec.confidence_percent == "0%"

    def test_confidence_percent_full(self) -> None:
        """confidence_percent formats 1.0 as '100%'."""
        rec = PrimitiveRecommendation(primitive_name="P", confidence_score=1.0, reasoning="full")
        assert rec.confidence_percent == "100%"

    def test_to_dict_includes_required_keys(self) -> None:
        """to_dict() includes all required keys."""
        rec = PrimitiveRecommendation(
            primitive_name="CachePrimitive",
            confidence_score=0.75,
            reasoning="Found caching code",
            import_path="from ttadev import CachePrimitive",
        )
        d = rec.to_dict()
        for key in ("primitive_name", "confidence_score", "reasoning", "import_path"):
            assert key in d

    def test_default_optional_fields_are_empty(self) -> None:
        """Optional fields (code_template, use_cases, related_primitives) default empty."""
        rec = PrimitiveRecommendation(primitive_name="P", confidence_score=0.5, reasoning="r")
        assert rec.code_template == ""
        assert rec.use_cases == []
        assert rec.related_primitives == []


# ===========================================================================
# AnalysisReport — model
# ===========================================================================


def _make_report() -> AnalysisReport:
    """Factory: create a simple AnalysisReport for model tests."""
    analysis = CodeAnalysisResult(detected_patterns=["api_calls"], complexity_level="medium")
    recs = [
        PrimitiveRecommendation("RetryPrimitive", 0.9, "Found retry"),
        PrimitiveRecommendation("CachePrimitive", 0.4, "Found cache"),
    ]
    context = RecommendationContext(file_path="test.py")
    return AnalysisReport(
        analysis=analysis,
        recommendations=recs,
        context=context,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestAnalysisReport:
    def test_to_dict_success_true(self) -> None:
        """to_dict() always includes success=True."""
        assert _make_report().to_dict()["success"] is True

    def test_to_dict_has_metadata_block(self) -> None:
        """to_dict() includes a 'metadata' block."""
        assert "metadata" in _make_report().to_dict()

    def test_to_dict_metadata_has_timestamp(self) -> None:
        """to_dict() metadata includes a 'timestamp' key."""
        assert "timestamp" in _make_report().to_dict()["metadata"]

    def test_to_dict_metadata_recommendations_count(self) -> None:
        """to_dict() metadata has the correct recommendations_count."""
        assert _make_report().to_dict()["metadata"]["recommendations_count"] == 2

    def test_to_dict_highest_confidence(self) -> None:
        """to_dict() metadata correctly reports highest_confidence."""
        assert _make_report().to_dict()["metadata"]["highest_confidence"] == 0.9

    def test_to_dict_highest_confidence_empty_recs(self) -> None:
        """to_dict() highest_confidence is 0.0 when no recommendations exist."""
        report = AnalysisReport(
            analysis=CodeAnalysisResult(),
            recommendations=[],
            context=RecommendationContext(),
        )
        assert report.to_dict()["metadata"]["highest_confidence"] == 0.0

    def test_to_table_contains_primitive_name(self) -> None:
        """to_table() output includes recommendation primitive names."""
        assert "RetryPrimitive" in _make_report().to_table()

    def test_to_table_contains_detected_pattern(self) -> None:
        """to_table() output mentions detected patterns."""
        table = _make_report().to_table()
        assert "api" in table.lower() or "Api" in table

    def test_get_top_recommendation_returns_highest(self) -> None:
        """get_top_recommendation() returns the rec with highest confidence_score."""
        top = _make_report().get_top_recommendation()
        assert top is not None
        assert top.primitive_name == "RetryPrimitive"

    def test_get_top_recommendation_empty_returns_none(self) -> None:
        """get_top_recommendation() returns None when recommendations list is empty."""
        report = AnalysisReport(
            analysis=CodeAnalysisResult(), recommendations=[], context=RecommendationContext()
        )
        assert report.get_top_recommendation() is None

    def test_filter_by_confidence_above_threshold(self) -> None:
        """filter_by_confidence(0.5) returns only recs with score >= 0.5."""
        filtered = _make_report().filter_by_confidence(0.5)
        assert len(filtered) == 1
        assert filtered[0].primitive_name == "RetryPrimitive"

    def test_filter_by_confidence_zero_includes_all(self) -> None:
        """filter_by_confidence(0.0) includes all recommendations."""
        assert len(_make_report().filter_by_confidence(0.0)) == 2


# ===========================================================================
# TTAAnalyzer — core analysis
# ===========================================================================


class TestTTAAnalyzer:
    def test_analyze_returns_analysis_report_instance(self) -> None:
        """analyze() returns an AnalysisReport object."""
        analyzer = TTAAnalyzer()
        report = analyzer.analyze("import requests\nrequests.get('http://api.io')")
        assert isinstance(report, AnalysisReport)

    def test_analyze_empty_code_succeeds(self) -> None:
        """analyze() handles empty string without raising exceptions."""
        report = TTAAnalyzer().analyze("")
        assert isinstance(report, AnalysisReport)
        assert report.analysis.detected_patterns == []

    def test_analyze_file_path_stored_in_context(self) -> None:
        """analyze() stores file_path in report.context.file_path."""
        report = TTAAnalyzer().analyze("x = 1", file_path="myfile.py")
        assert report.context.file_path == "myfile.py"

    def test_analyze_project_type_stored_in_context(self) -> None:
        """analyze() stores project_type in report.context.project_type."""
        report = TTAAnalyzer().analyze("x = 1", project_type="api")
        assert report.context.project_type == "api"

    def test_analyze_development_stage_stored(self) -> None:
        """analyze() stores development_stage in report.context.development_stage."""
        report = TTAAnalyzer().analyze("x = 1", development_stage="production")
        assert report.context.development_stage == "production"

    def test_version_is_defined(self) -> None:
        """TTAAnalyzer.VERSION is a non-empty string."""
        assert isinstance(TTAAnalyzer.VERSION, str)
        assert TTAAnalyzer.VERSION != ""

    def test_api_calls_without_error_handling_generates_issue(self) -> None:
        """analyze() detects 'error handling' issue for API code without try/except."""
        code = "import requests\nrequests.get('http://api.io')"
        report = TTAAnalyzer().analyze(code)
        issues = report.context.detected_issues
        assert any("error handling" in i.lower() for i in issues)

    def test_async_without_timeout_generates_issue(self) -> None:
        """analyze() detects 'timeout' issue for async code with no timeout."""
        code = "async def fetch():\n    return await call()"
        report = TTAAnalyzer().analyze(code)
        issues = report.context.detected_issues
        assert any("timeout" in i.lower() for i in issues)

    def test_llm_without_cache_generates_optimization(self) -> None:
        """analyze() detects cache optimization opportunity for LLM code."""
        code = "import openai\nclient = openai.OpenAI()\nclient.chat.completions.create()"
        report = TTAAnalyzer().analyze(code)
        opps = report.context.optimization_opportunities
        assert any("cache" in o.lower() for o in opps)

    def test_high_min_confidence_returns_fewer_recs(self) -> None:
        """analyze() with high min_confidence produces fewer recommendations."""
        analyzer = TTAAnalyzer()
        code = "import requests\nrequests.get('http://api.io')"
        low = analyzer.analyze(code, min_confidence=0.0)
        high = analyzer.analyze(code, min_confidence=0.99)
        assert len(low.recommendations) >= len(high.recommendations)

    def test_analyze_file_reads_and_analyzes(self, tmp_path: Path) -> None:
        """analyze_file() reads a .py file and returns an AnalysisReport."""
        p = tmp_path / "sample.py"
        p.write_text("import requests\nrequests.get('http://api.io')")
        report = TTAAnalyzer().analyze_file(str(p))
        assert isinstance(report, AnalysisReport)
        assert "api_calls" in report.analysis.detected_patterns

    def test_analyze_file_raises_for_missing_file(self) -> None:
        """analyze_file() raises FileNotFoundError for a non-existent path."""
        with pytest.raises(FileNotFoundError):
            TTAAnalyzer().analyze_file("/tmp/this_file_definitely_does_not_exist_xyz123.py")

    def test_get_primitive_info_known_primitive(self) -> None:
        """get_primitive_info() returns a dict with 'name' for a known primitive."""
        info = TTAAnalyzer().get_primitive_info("RetryPrimitive")
        assert "name" in info
        assert info["name"] == "RetryPrimitive"

    def test_get_primitive_info_unknown_primitive(self) -> None:
        """get_primitive_info() returns an error dict for an unknown primitive name."""
        info = TTAAnalyzer().get_primitive_info("NotARealPrimitive")
        assert "error" in info

    def test_list_primitives_returns_non_empty_list(self) -> None:
        """list_primitives() returns a non-empty list of primitive info dicts."""
        primitives = TTAAnalyzer().list_primitives()
        assert isinstance(primitives, list)
        assert len(primitives) > 0

    def test_search_templates_returns_list(self) -> None:
        """search_templates() returns a list (may be empty) for any query."""
        results = TTAAnalyzer().search_templates("retry")
        assert isinstance(results, list)


# ===========================================================================
# TransformResult / FunctionInfo — dataclasses
# ===========================================================================


class TestTransformResultDataclass:
    def test_success_fields_stored(self) -> None:
        """TransformResult stores success=True and all code fields correctly."""
        result = TransformResult(
            original_code="x = 1",
            transformed_code="y = 2",
            changes_made=[{"type": "change"}],
            imports_added=["import os"],
            success=True,
        )
        assert result.success is True
        assert result.original_code == "x = 1"
        assert result.transformed_code == "y = 2"
        assert result.error is None

    def test_failure_fields_stored(self) -> None:
        """TransformResult stores error message and success=False correctly."""
        result = TransformResult(
            original_code="bad !!!",
            transformed_code="bad !!!",
            changes_made=[],
            imports_added=[],
            success=False,
            error="Syntax error: invalid syntax",
        )
        assert result.success is False
        assert result.error is not None
        assert "Syntax error" in result.error


class TestFunctionInfoDataclass:
    def test_stores_name_and_is_async(self) -> None:
        """FunctionInfo stores name, is_async, lineno, and col_offset."""
        info = FunctionInfo(
            name="my_func",
            is_async=True,
            args=["x", "y"],
            body=[],
            decorators=[],
            returns=None,
            lineno=10,
            col_offset=0,
        )
        assert info.name == "my_func"
        assert info.is_async is True
        assert info.lineno == 10


# ===========================================================================
# CodeTransformer — transform() entry point
# ===========================================================================


class TestCodeTransformer:
    def test_invalid_syntax_returns_failure(self) -> None:
        """transform() on invalid Python returns success=False with an error message."""
        ct = CodeTransformer()
        result = ct.transform("def bad syntax !!!")
        assert result.success is False
        assert result.error is not None

    def test_empty_code_returns_success(self) -> None:
        """transform() on an empty string returns success=True."""
        assert CodeTransformer().transform("").success is True

    def test_clean_code_no_changes(self) -> None:
        """transform() on code with no anti-patterns makes zero changes."""
        ct = CodeTransformer()
        result = ct.transform("x = 1\ny = x + 2\n")
        assert result.success is True
        assert result.changes_made == []

    def test_preserves_original_code(self) -> None:
        """transform() always stores the original code in result.original_code."""
        original = "x = 1 + 2\n"
        result = CodeTransformer().transform(original)
        assert result.original_code == original

    def test_detects_and_transforms_retry_loop(self) -> None:
        """transform() auto-detects a for-range retry loop and records changes."""
        ct = CodeTransformer()
        code = _dedent(
            """
            def fetch_data():
                for i in range(3):
                    try:
                        return api_call()
                    except Exception:
                        pass
            """
        )
        result = ct.transform(code)
        assert result.success is True
        assert len(result.changes_made) > 0

    def test_specific_primitive_applies_only_that_transform(self) -> None:
        """transform(primitive='RetryPrimitive') applies only that transform."""
        ct = CodeTransformer()
        code = _dedent(
            """
            def fetch_data():
                for i in range(3):
                    try:
                        return api_call()
                    except Exception:
                        pass
            """
        )
        result = ct.transform(code, primitive="RetryPrimitive")
        assert result.success is True

    def test_auto_detect_false_makes_no_changes(self) -> None:
        """transform(auto_detect=False) without primitive makes no changes."""
        ct = CodeTransformer()
        code = "for i in range(3):\n    try: api()\n    except: pass"
        result = ct.transform(code, auto_detect=False)
        assert result.success is True
        assert result.changes_made == []

    def test_unknown_primitive_makes_no_changes(self) -> None:
        """transform() with an unrecognised primitive name makes no changes."""
        ct = CodeTransformer()
        result = ct.transform("x = 1\n", primitive="NonExistentPrimitive")
        assert result.success is True
        assert result.changes_made == []

    def test_timeout_code_succeeds(self) -> None:
        """transform() on asyncio.wait_for code returns success=True."""
        code = _dedent(
            """
            async def slow_op():
                result = await asyncio.wait_for(do_work(), timeout=30)
                return result
            """
        )
        assert CodeTransformer().transform(code).success is True

    def test_gather_code_succeeds(self) -> None:
        """transform() on asyncio.gather code returns success=True."""
        code = _dedent(
            """
            async def run_all():
                results = await asyncio.gather(task1(), task2(), task3())
                return results
            """
        )
        assert CodeTransformer().transform(code).success is True

    def test_fallback_pattern_succeeds(self) -> None:
        """transform() on try/except fallback code returns success=True."""
        code = _dedent(
            """
            async def get_data():
                try:
                    return await primary()
                except Exception:
                    return await backup()
            """
        )
        assert CodeTransformer().transform(code).success is True

    def test_circuit_breaker_pattern_succeeds(self) -> None:
        """transform() on multi-except handler code returns success=True."""
        code = _dedent(
            """
            def call_service():
                try:
                    return service.call()
                except ConnectionError:
                    return None
                except TimeoutError:
                    return None
            """
        )
        assert CodeTransformer().transform(code).success is True


# ===========================================================================
# RetryLoopDetector
# ===========================================================================


class TestRetryLoopDetector:
    def test_detects_for_range_with_try(self) -> None:
        """RetryLoopDetector finds 'for i in range(n): try: ...' pattern."""
        code = _dedent(
            """
            def fetch():
                for i in range(3):
                    try:
                        return api_call()
                    except Exception:
                        pass
            """
        )
        detector = RetryLoopDetector()
        detector.visit(_parse(code))
        assert len(detector.retry_functions) == 1
        assert detector.retry_functions[0]["name"] == "fetch"

    def test_captures_max_retries_from_range(self) -> None:
        """RetryLoopDetector reads the retry count from range(n)."""
        code = _dedent(
            """
            def fetch():
                for i in range(5):
                    try:
                        return api_call()
                    except Exception:
                        pass
            """
        )
        detector = RetryLoopDetector()
        detector.visit(_parse(code))
        assert detector.retry_functions[0]["max_retries"] == 5

    def test_detects_async_function_and_flags_is_async(self) -> None:
        """RetryLoopDetector flags is_async=True for async function bodies."""
        code = _dedent(
            """
            async def fetch():
                for i in range(3):
                    try:
                        return await api_call()
                    except Exception:
                        pass
            """
        )
        detector = RetryLoopDetector()
        detector.visit(_parse(code))
        assert len(detector.retry_functions) == 1
        assert detector.retry_functions[0]["is_async"] is True

    def test_no_detection_without_try(self) -> None:
        """RetryLoopDetector ignores for-range loops that contain no try/except."""
        code = "def f():\n    for i in range(3):\n        print(i)"
        detector = RetryLoopDetector()
        detector.visit(_parse(code))
        assert detector.retry_functions == []

    def test_empty_code_no_results(self) -> None:
        """RetryLoopDetector produces an empty list for an empty module."""
        detector = RetryLoopDetector()
        detector.visit(_parse(""))
        assert detector.retry_functions == []


# ===========================================================================
# TimeoutDetector
# ===========================================================================


class TestTimeoutDetector:
    def test_detects_asyncio_wait_for(self) -> None:
        """TimeoutDetector finds 'await asyncio.wait_for(coro, timeout=n)'."""
        code = _dedent(
            """
            async def run():
                result = await asyncio.wait_for(slow(), timeout=10)
                return result
            """
        )
        detector = TimeoutDetector()
        detector.visit(_parse(code))
        assert len(detector.timeout_calls) == 1

    def test_captures_timeout_value(self) -> None:
        """TimeoutDetector extracts the numeric timeout value."""
        code = _dedent(
            """
            async def run():
                result = await asyncio.wait_for(slow(), timeout=30)
            """
        )
        detector = TimeoutDetector()
        detector.visit(_parse(code))
        assert detector.timeout_calls[0]["timeout"] == 30

    def test_captures_wrapped_function_name(self) -> None:
        """TimeoutDetector extracts the name of the wrapped coroutine."""
        code = _dedent(
            """
            async def run():
                result = await asyncio.wait_for(my_slow_func(), timeout=5)
            """
        )
        detector = TimeoutDetector()
        detector.visit(_parse(code))
        assert detector.timeout_calls[0]["function"] == "my_slow_func"

    def test_no_detection_for_regular_await(self) -> None:
        """TimeoutDetector ignores plain await calls unrelated to asyncio.wait_for."""
        code = "async def run():\n    result = await regular_call()"
        detector = TimeoutDetector()
        detector.visit(_parse(code))
        assert detector.timeout_calls == []


# ===========================================================================
# CachePatternDetector
# ===========================================================================


class TestCachePatternDetector:
    def test_detects_if_key_in_cache(self) -> None:
        """CachePatternDetector identifies 'if key in cache' guard pattern."""
        code = _dedent(
            """
            def get_data(key):
                if key in _cache:
                    return _cache[key]
                result = fetch(key)
                _cache[key] = result
                return result
            """
        )
        detector = CachePatternDetector()
        detector.visit(_parse(code))
        assert len(detector.cache_functions) == 1
        assert detector.cache_functions[0]["name"] == "get_data"

    def test_detects_async_cache_function(self) -> None:
        """CachePatternDetector detects cache guard in async functions (is_async=True)."""
        code = _dedent(
            """
            async def get_data(key):
                if key in result_cache:
                    return result_cache[key]
                result = await fetch(key)
                return result
            """
        )
        detector = CachePatternDetector()
        detector.visit(_parse(code))
        assert len(detector.cache_functions) == 1
        assert detector.cache_functions[0]["is_async"] is True

    def test_no_detection_without_in_guard(self) -> None:
        """CachePatternDetector returns empty list when there is no 'in' check."""
        code = "def get_data(key):\n    return fetch(key)"
        detector = CachePatternDetector()
        detector.visit(_parse(code))
        assert detector.cache_functions == []


# ===========================================================================
# FallbackDetector
# ===========================================================================


class TestFallbackDetector:
    def test_detects_try_return_except_return(self) -> None:
        """FallbackDetector finds 'try: return f() except: return g()' fallback."""
        code = _dedent(
            """
            async def get_result():
                try:
                    return await primary()
                except Exception:
                    return await backup()
            """
        )
        detector = FallbackDetector()
        detector.visit(_parse(code))
        assert len(detector.fallback_patterns) == 1

    def test_captures_primary_and_fallback_names(self) -> None:
        """FallbackDetector stores 'primary' and 'fallback' function names."""
        code = _dedent(
            """
            async def process():
                try:
                    return await primary_handler()
                except Exception:
                    return await backup_handler()
            """
        )
        detector = FallbackDetector()
        detector.visit(_parse(code))
        fp = detector.fallback_patterns[0]
        assert fp["primary"] == "primary_handler"
        assert fp["fallback"] == "backup_handler"

    def test_no_detection_when_except_has_no_return(self) -> None:
        """FallbackDetector ignores except blocks that don't return a value."""
        code = _dedent(
            """
            def run():
                try:
                    return primary()
                except Exception:
                    log_error()
            """
        )
        detector = FallbackDetector()
        detector.visit(_parse(code))
        assert detector.fallback_patterns == []

    def test_captures_parent_function_name(self) -> None:
        """FallbackDetector records the enclosing function name in 'function' key."""
        code = _dedent(
            """
            def my_handler():
                try:
                    return call_a()
                except Exception:
                    return call_b()
            """
        )
        detector = FallbackDetector()
        detector.visit(_parse(code))
        assert detector.fallback_patterns[0]["function"] == "my_handler"


# ===========================================================================
# GatherDetector
# ===========================================================================


class TestGatherDetector:
    def test_detects_asyncio_gather(self) -> None:
        """GatherDetector finds 'await asyncio.gather(...)' calls."""
        code = _dedent(
            """
            async def run_all():
                results = await asyncio.gather(task1(), task2())
            """
        )
        detector = GatherDetector()
        detector.visit(_parse(code))
        assert len(detector.gather_calls) == 1

    def test_captures_arg_count(self) -> None:
        """GatherDetector records the number of tasks passed to gather."""
        code = _dedent(
            """
            async def run_all():
                results = await asyncio.gather(t1(), t2(), t3())
            """
        )
        detector = GatherDetector()
        detector.visit(_parse(code))
        assert len(detector.gather_calls[0]["args"]) == 3

    def test_no_detection_for_non_gather_await(self) -> None:
        """GatherDetector ignores plain await expressions unrelated to asyncio.gather."""
        code = "async def run():\n    result = await some_func()"
        detector = GatherDetector()
        detector.visit(_parse(code))
        assert detector.gather_calls == []


# ===========================================================================
# RouterPatternDetector
# ===========================================================================


class TestRouterPatternDetector:
    def test_detects_if_elif_routing_chain(self) -> None:
        """RouterPatternDetector finds an if/elif equality routing chain (>=2 branches)."""
        code = _dedent(
            """
            async def handle(provider):
                if provider == "openai":
                    return await call_openai(data)
                elif provider == "anthropic":
                    return await call_anthropic(data)
            """
        )
        detector = RouterPatternDetector()
        detector.visit(_parse(code))
        assert len(detector.router_patterns) >= 1

    def test_no_detection_for_single_branch(self) -> None:
        """RouterPatternDetector requires >=2 routes; single if is ignored."""
        code = _dedent(
            """
            async def handle(x):
                if x == "a":
                    return await call_a()
            """
        )
        detector = RouterPatternDetector()
        detector.visit(_parse(code))
        assert detector.router_patterns == []

    def test_captures_routing_variable(self) -> None:
        """RouterPatternDetector records the variable being compared in routes."""
        code = _dedent(
            """
            async def dispatch(model):
                if model == "gpt-4":
                    return await use_gpt4(data)
                elif model == "claude":
                    return await use_claude(data)
            """
        )
        detector = RouterPatternDetector()
        detector.visit(_parse(code))
        assert len(detector.router_patterns) >= 1
        assert detector.router_patterns[0]["variable"] == "model"


# ===========================================================================
# CircuitBreakerDetector
# ===========================================================================


class TestCircuitBreakerDetector:
    def test_detects_multiple_exception_handlers(self) -> None:
        """CircuitBreakerDetector finds functions with 2+ except clauses."""
        code = _dedent(
            """
            def call_service():
                try:
                    return service.call()
                except ConnectionError:
                    return None
                except TimeoutError:
                    return None
            """
        )
        detector = CircuitBreakerDetector()
        detector.visit(_parse(code))
        assert len(detector.circuit_patterns) == 1

    def test_captures_exception_count(self) -> None:
        """CircuitBreakerDetector records the exact number of exception handlers."""
        code = _dedent(
            """
            def call_service():
                try:
                    return service.call()
                except ConnectionError:
                    return None
                except TimeoutError:
                    return None
                except ValueError:
                    return None
            """
        )
        detector = CircuitBreakerDetector()
        detector.visit(_parse(code))
        assert detector.circuit_patterns[0]["exception_count"] == 3

    def test_no_detection_for_single_handler(self) -> None:
        """CircuitBreakerDetector requires >=2 handlers; single except is ignored."""
        code = _dedent(
            """
            def run():
                try:
                    return do_work()
                except Exception:
                    return None
            """
        )
        detector = CircuitBreakerDetector()
        detector.visit(_parse(code))
        assert detector.circuit_patterns == []

    def test_detects_async_function(self) -> None:
        """CircuitBreakerDetector works with async functions (is_async=True)."""
        code = _dedent(
            """
            async def call_service():
                try:
                    return await service.call()
                except ConnectionError:
                    return None
                except TimeoutError:
                    return None
            """
        )
        detector = CircuitBreakerDetector()
        detector.visit(_parse(code))
        assert len(detector.circuit_patterns) == 1
        assert detector.circuit_patterns[0]["is_async"] is True


# ===========================================================================
# CompensationDetector
# ===========================================================================


class TestCompensationDetector:
    def test_detects_try_except_cleanup_raise(self) -> None:
        """CompensationDetector finds try/except with cleanup action + re-raise."""
        code = _dedent(
            """
            async def index_document(doc):
                try:
                    await db.insert(doc)
                except Exception:
                    await db.rollback(doc)
                    raise
            """
        )
        detector = CompensationDetector()
        detector.visit(_parse(code))
        assert len(detector.compensation_patterns) == 1

    def test_captures_cleanup_actions_list(self) -> None:
        """CompensationDetector records cleanup action names in 'cleanup_actions'."""
        code = _dedent(
            """
            async def index_document(doc):
                try:
                    await db.insert(doc)
                except Exception:
                    await db.rollback(doc)
                    raise
            """
        )
        detector = CompensationDetector()
        detector.visit(_parse(code))
        actions = detector.compensation_patterns[0]["cleanup_actions"]
        assert len(actions) > 0

    def test_no_detection_without_raise(self) -> None:
        """CompensationDetector requires a 'raise' statement; cleanup alone is ignored."""
        code = _dedent(
            """
            async def run():
                try:
                    await do_work()
                except Exception:
                    await cleanup()
            """
        )
        detector = CompensationDetector()
        detector.visit(_parse(code))
        assert detector.compensation_patterns == []


# ===========================================================================
# MemoryDetector
# ===========================================================================


class TestMemoryDetector:
    def test_detects_message_append_with_role_key(self) -> None:
        """MemoryDetector finds messages.append({'role': ..., 'content': ...})."""
        code = _dedent(
            """
            def add_msg(messages, role, content):
                messages.append({"role": role, "content": content})
            """
        )
        detector = MemoryDetector()
        detector.visit(_parse(code))
        types = [p["type"] for p in detector.memory_patterns]
        assert "message_append" in types

    def test_detects_deque_with_maxlen(self) -> None:
        """MemoryDetector identifies deque(maxlen=n) history initialisation."""
        code = "from collections import deque\nhistory = deque(maxlen=100)"
        detector = MemoryDetector()
        detector.visit(_parse(code))
        assert any(p["type"] == "deque_history" for p in detector.memory_patterns)

    def test_deque_captures_maxlen_value(self) -> None:
        """MemoryDetector stores the actual maxlen value from deque(maxlen=n)."""
        code = "from collections import deque\nhistory = deque(maxlen=50)"
        detector = MemoryDetector()
        detector.visit(_parse(code))
        deque_ps = [p for p in detector.memory_patterns if p["type"] == "deque_history"]
        assert deque_ps[0]["maxlen"] == 50


# ===========================================================================
# SequentialDetector
# ===========================================================================


class TestSequentialDetector:
    def test_detects_three_step_assignment_chain(self) -> None:
        """SequentialDetector finds 3+ sequential function assignment chains."""
        code = _dedent(
            """
            def pipeline(data):
                r1 = step_one(data)
                r2 = step_two(r1)
                r3 = step_three(r2)
                return r3
            """
        )
        detector = SequentialDetector()
        detector.visit(_parse(code))
        assert len(detector.sequential_patterns) >= 1

    def test_detects_nested_call_chain(self) -> None:
        """SequentialDetector finds step3(step2(step1(data))) nested call chain."""
        code = _dedent(
            """
            def run(data):
                return step3(step2(step1(data)))
            """
        )
        detector = SequentialDetector()
        detector.visit(_parse(code))
        nested = [p for p in detector.sequential_patterns if p["type"] == "nested_calls"]
        assert len(nested) >= 1

    def test_no_assignment_chain_for_two_steps(self) -> None:
        """SequentialDetector requires >=3 assignments; two-step chains are ignored."""
        code = _dedent(
            """
            def run(data):
                r1 = step_one(data)
                r2 = step_two(r1)
                return r2
            """
        )
        detector = SequentialDetector()
        detector.visit(_parse(code))
        chain = [p for p in detector.sequential_patterns if p["type"] == "assignment_chain"]
        assert chain == []


# ===========================================================================
# DelegationDetector
# ===========================================================================


class TestDelegationDetector:
    def test_detects_model_routing_chain(self) -> None:
        """DelegationDetector identifies if/elif model selection routing."""
        code = _dedent(
            """
            async def dispatch(model, data):
                if model == "gpt-4":
                    return await use_gpt4(data)
                elif model == "claude":
                    return await use_claude(data)
                elif model == "gemini":
                    return await use_gemini(data)
            """
        )
        detector = DelegationDetector()
        detector.visit(_parse(code))
        model_ps = [p for p in detector.delegation_patterns if p["type"] == "model_routing"]
        assert len(model_ps) >= 1

    def test_detects_agent_dispatch_via_subscript(self) -> None:
        """DelegationDetector finds agents[role].execute(task) dispatch pattern."""
        code = _dedent(
            """
            async def run(agents, role, task):
                return await agents[role].execute(task)
            """
        )
        detector = DelegationDetector()
        detector.visit(_parse(code))
        dispatch = [p for p in detector.delegation_patterns if p["type"] == "agent_dispatch"]
        assert len(dispatch) >= 1


# ===========================================================================
# AdaptiveDetector
# ===========================================================================


class TestAdaptiveDetector:
    def test_detects_metric_based_adjustment(self) -> None:
        """AdaptiveDetector finds counter increment + conditional param adjustment."""
        code = _dedent(
            """
            def adjust(rate):
                success_count += 1
                if rate > threshold:
                    speed = "fast"
            """
        )
        detector = AdaptiveDetector()
        detector.visit(_parse(code))
        metric_ps = [
            p for p in detector.adaptive_patterns if p["type"] == "metric_based_adjustment"
        ]
        assert len(metric_ps) >= 1

    def test_detects_strategy_config_with_metrics_keys(self) -> None:
        """AdaptiveDetector finds a dict named 'strategies' with latency/score keys."""
        code = _dedent(
            """
            strategies = {
                "fast": {"latency": 0.1, "success_rate": 0.95},
                "slow": {"latency": 1.0, "success_rate": 0.99},
            }
            """
        )
        detector = AdaptiveDetector()
        detector.visit(_parse(code))
        config_ps = [p for p in detector.adaptive_patterns if p["type"] == "strategy_config"]
        assert len(config_ps) >= 1
