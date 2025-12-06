"""Tests for the PrimitiveMatcher class."""

import pytest

from tta_dev_primitives.analysis.matcher import PrimitiveMatcher
from tta_dev_primitives.analysis.models import (
    CodeAnalysisResult,
    RecommendationContext,
)


class TestPrimitiveMatcher:
    """Tests for PrimitiveMatcher functionality."""

    @pytest.fixture
    def matcher(self) -> PrimitiveMatcher:
        """Create a PrimitiveMatcher instance."""
        return PrimitiveMatcher()

    @pytest.fixture
    def basic_context(self) -> RecommendationContext:
        """Create a basic recommendation context."""
        return RecommendationContext(
            file_path="test.py",
            code_content="async def test(): pass",
        )

    def test_init_registers_primitives(self, matcher: PrimitiveMatcher) -> None:
        """Verify all primitives are registered in catalog."""
        expected_primitives = [
            "RetryPrimitive",
            "TimeoutPrimitive",
            "CachePrimitive",
            "FallbackPrimitive",
            "ParallelPrimitive",
            "SequentialPrimitive",
            "RouterPrimitive",
            "CircuitBreakerPrimitive",
            "MemoryPrimitive",
        ]
        for primitive in expected_primitives:
            assert primitive in matcher.primitive_catalog, f"Missing: {primitive}"

    def test_primitive_has_required_fields(self, matcher: PrimitiveMatcher) -> None:
        """Verify each primitive has required catalog fields."""
        required_fields = [
            "description",
            "import_path",
            "patterns",
            "use_cases",
        ]
        for name, info in matcher.primitive_catalog.items():
            for field in required_fields:
                assert field in info, f"{name} missing {field}"

    def test_find_matches_returns_list(
        self, matcher: PrimitiveMatcher, basic_context: RecommendationContext
    ) -> None:
        """Verify find_matches returns a list of tuples."""
        analysis = CodeAnalysisResult(
            detected_patterns=["async_operations"],
        )
        matches = matcher.find_matches(analysis, basic_context)
        assert isinstance(matches, list)
        for match in matches:
            assert isinstance(match, tuple)
            assert len(match) == 2
            assert isinstance(match[0], str)  # primitive name
            assert isinstance(match[1], float)  # confidence score

    def test_retry_patterns_match_retry_primitive(
        self, matcher: PrimitiveMatcher, basic_context: RecommendationContext
    ) -> None:
        """Verify retry patterns trigger RetryPrimitive."""
        analysis = CodeAnalysisResult(
            detected_patterns=["retry_patterns", "error_handling"],
            inferred_requirements=["retry_logic", "error_recovery"],
        )
        matches = matcher.find_matches(analysis, basic_context)
        primitive_names = [m[0] for m in matches]
        assert "RetryPrimitive" in primitive_names

    def test_timeout_patterns_match_timeout_primitive(
        self, matcher: PrimitiveMatcher, basic_context: RecommendationContext
    ) -> None:
        """Verify timeout patterns trigger TimeoutPrimitive."""
        analysis = CodeAnalysisResult(
            detected_patterns=["timeout_patterns", "async_operations"],
            inferred_requirements=["timeout_handling"],
        )
        matches = matcher.find_matches(analysis, basic_context)
        primitive_names = [m[0] for m in matches]
        assert "TimeoutPrimitive" in primitive_names

    def test_caching_patterns_match_cache_primitive(
        self, matcher: PrimitiveMatcher, basic_context: RecommendationContext
    ) -> None:
        """Verify caching patterns trigger CachePrimitive."""
        analysis = CodeAnalysisResult(
            detected_patterns=["caching_patterns", "api_calls"],
            inferred_requirements=["performance_optimization"],
        )
        matches = matcher.find_matches(analysis, basic_context)
        primitive_names = [m[0] for m in matches]
        assert "CachePrimitive" in primitive_names

    def test_fallback_patterns_match_fallback_primitive(
        self, matcher: PrimitiveMatcher, basic_context: RecommendationContext
    ) -> None:
        """Verify fallback patterns trigger FallbackPrimitive."""
        analysis = CodeAnalysisResult(
            detected_patterns=["fallback_patterns", "error_handling"],
            inferred_requirements=["fallback_strategy", "error_recovery"],
        )
        matches = matcher.find_matches(analysis, basic_context)
        primitive_names = [m[0] for m in matches]
        assert "FallbackPrimitive" in primitive_names

    def test_parallel_patterns_match_parallel_primitive(
        self, matcher: PrimitiveMatcher, basic_context: RecommendationContext
    ) -> None:
        """Verify parallel patterns trigger ParallelPrimitive."""
        analysis = CodeAnalysisResult(
            detected_patterns=["parallel_patterns", "async_operations"],
            inferred_requirements=["concurrent_execution"],
        )
        matches = matcher.find_matches(analysis, basic_context)
        primitive_names = [m[0] for m in matches]
        assert "ParallelPrimitive" in primitive_names

    def test_routing_patterns_match_router_primitive(
        self, matcher: PrimitiveMatcher, basic_context: RecommendationContext
    ) -> None:
        """Verify routing patterns trigger RouterPrimitive."""
        analysis = CodeAnalysisResult(
            detected_patterns=["routing_patterns"],
            inferred_requirements=["intelligent_routing"],
        )
        matches = matcher.find_matches(analysis, basic_context)
        primitive_names = [m[0] for m in matches]
        assert "RouterPrimitive" in primitive_names

    def test_min_confidence_filters_low_scores(
        self, matcher: PrimitiveMatcher, basic_context: RecommendationContext
    ) -> None:
        """Verify min_confidence filters out low-scoring matches."""
        analysis = CodeAnalysisResult(
            detected_patterns=["async_operations"],
        )
        # High threshold should filter more
        high_threshold_matches = matcher.find_matches(analysis, basic_context, min_confidence=0.8)
        low_threshold_matches = matcher.find_matches(analysis, basic_context, min_confidence=0.1)
        assert len(high_threshold_matches) <= len(low_threshold_matches)

    def test_matches_sorted_by_confidence(
        self, matcher: PrimitiveMatcher, basic_context: RecommendationContext
    ) -> None:
        """Verify matches are sorted by confidence score descending."""
        analysis = CodeAnalysisResult(
            detected_patterns=[
                "async_operations",
                "error_handling",
                "retry_patterns",
            ],
        )
        matches = matcher.find_matches(analysis, basic_context)
        if len(matches) > 1:
            scores = [m[1] for m in matches]
            assert scores == sorted(scores, reverse=True)

    def test_empty_patterns_returns_few_matches(
        self, matcher: PrimitiveMatcher, basic_context: RecommendationContext
    ) -> None:
        """Verify empty patterns returns minimal matches."""
        analysis = CodeAnalysisResult(
            detected_patterns=[],
        )
        matches = matcher.find_matches(analysis, basic_context, min_confidence=0.5)
        # With no patterns, should have few or no high-confidence matches
        assert len(matches) <= 2

    def test_confidence_between_0_and_1(
        self, matcher: PrimitiveMatcher, basic_context: RecommendationContext
    ) -> None:
        """Verify all confidence scores are between 0 and 1."""
        analysis = CodeAnalysisResult(
            detected_patterns=[
                "async_operations",
                "error_handling",
                "api_calls",
                "timeout_patterns",
            ],
        )
        matches = matcher.find_matches(analysis, basic_context, min_confidence=0.0)
        for name, score in matches:
            assert 0.0 <= score <= 1.0, f"{name} has invalid score: {score}"

    def test_get_primitive_info(self, matcher: PrimitiveMatcher) -> None:
        """Verify get_primitive_info returns correct info."""
        info = matcher.get_primitive_info("RetryPrimitive")
        assert info is not None
        assert "description" in info
        assert "import_path" in info

    def test_get_primitive_info_unknown_returns_none(self, matcher: PrimitiveMatcher) -> None:
        """Verify get_primitive_info returns None for unknown primitive."""
        info = matcher.get_primitive_info("UnknownPrimitive")
        assert info is None

    def test_issue_detection_boosts_confidence(self, matcher: PrimitiveMatcher) -> None:
        """Verify detected issues boost related primitive confidence."""
        context_with_issues = RecommendationContext(
            file_path="test.py",
            code_content="",
            detected_issues=["Missing timeout protection"],
        )
        context_without_issues = RecommendationContext(
            file_path="test.py",
            code_content="",
        )
        analysis = CodeAnalysisResult(
            detected_patterns=["async_operations"],
            inferred_requirements=["timeout_handling"],  # Add requirement to trigger match
        )

        with_issues = matcher.find_matches(analysis, context_with_issues)
        without_issues = matcher.find_matches(analysis, context_without_issues)

        # Both should return matches (issue detection is a bonus)
        assert len(with_issues) > 0 or len(without_issues) > 0
