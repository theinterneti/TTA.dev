"""Tests for the TTAAnalyzer class."""

import pytest

from tta_dev_primitives.analysis import TTAAnalyzer
from tta_dev_primitives.analysis.models import (
    AnalysisReport,
    PrimitiveRecommendation,
)


class TestTTAAnalyzer:
    """Tests for TTAAnalyzer functionality."""

    @pytest.fixture
    def analyzer(self) -> TTAAnalyzer:
        """Create a TTAAnalyzer instance."""
        return TTAAnalyzer()

    def test_version(self, analyzer: TTAAnalyzer) -> None:
        """Verify analyzer has version."""
        assert analyzer.VERSION == "1.0.0"

    def test_analyze_returns_analysis_report(self, analyzer: TTAAnalyzer) -> None:
        """Verify analyze returns AnalysisReport."""
        code = "def test(): pass"
        result = analyzer.analyze(code)
        assert isinstance(result, AnalysisReport)

    def test_analyze_detects_patterns(self, analyzer: TTAAnalyzer) -> None:
        """Verify analyze detects patterns in code."""
        code = """
async def fetch_data():
    try:
        return await client.get('/api')
    except Exception:
        return None
"""
        result = analyzer.analyze(code)
        assert len(result.analysis.detected_patterns) > 0
        assert "async_operations" in result.analysis.detected_patterns

    def test_analyze_generates_recommendations(self, analyzer: TTAAnalyzer) -> None:
        """Verify analyze generates recommendations."""
        code = """
async def fetch_with_retry():
    for attempt in range(3):
        try:
            return await api.call()
        except Exception:
            if attempt == 2:
                raise
            await asyncio.sleep(1)
"""
        result = analyzer.analyze(code)
        assert len(result.recommendations) > 0
        for rec in result.recommendations:
            assert isinstance(rec, PrimitiveRecommendation)

    def test_recommendations_have_templates(self, analyzer: TTAAnalyzer) -> None:
        """Verify recommendations include code templates."""
        code = """
async def fetch():
    return await client.get('/api', timeout=30)
"""
        result = analyzer.analyze(code)
        if result.recommendations:
            # At least some recommendations should have templates
            has_template = any(rec.code_template for rec in result.recommendations)
            assert has_template

    def test_min_confidence_filters_recommendations(self, analyzer: TTAAnalyzer) -> None:
        """Verify min_confidence filters recommendations."""
        code = """
async def complex():
    try:
        result = await asyncio.wait_for(api.call(), timeout=30)
        return result
    except Exception:
        return await fallback()
"""
        high_threshold = analyzer.analyze(code, min_confidence=0.8)
        low_threshold = analyzer.analyze(code, min_confidence=0.1)
        assert len(high_threshold.recommendations) <= len(low_threshold.recommendations)

    def test_report_to_dict(self, analyzer: TTAAnalyzer) -> None:
        """Verify report.to_dict() returns valid dict."""
        code = "async def test(): pass"
        result = analyzer.analyze(code)
        data = result.to_dict()

        assert isinstance(data, dict)
        assert "analysis" in data
        assert "recommendations" in data
        assert "detected_patterns" in data["analysis"]

    def test_report_to_table(self, analyzer: TTAAnalyzer) -> None:
        """Verify report.to_table() returns string output."""
        code = "async def test(): pass"
        result = analyzer.analyze(code)
        table = result.to_table()

        assert isinstance(table, str)
        assert len(table) > 0

    def test_file_path_context(self, analyzer: TTAAnalyzer) -> None:
        """Verify file_path is used in analysis."""
        code = "def test(): pass"
        result = analyzer.analyze(code, file_path="api_client.py")
        assert result.context.file_path == "api_client.py"

    def test_project_type_context(self, analyzer: TTAAnalyzer) -> None:
        """Verify project_type is used in analysis."""
        code = "def test(): pass"
        result = analyzer.analyze(code, project_type="web")
        assert result.context.project_type == "web"

    def test_get_primitive_info(self, analyzer: TTAAnalyzer) -> None:
        """Verify get_primitive_info returns info dict."""
        info = analyzer.get_primitive_info("RetryPrimitive")
        assert isinstance(info, dict)
        assert "name" in info
        assert "description" in info

    def test_get_primitive_info_unknown(self, analyzer: TTAAnalyzer) -> None:
        """Verify get_primitive_info handles unknown primitives."""
        info = analyzer.get_primitive_info("UnknownPrimitive")
        # Should return empty or error dict
        assert "error" in info or info == {}

    def test_list_primitives(self, analyzer: TTAAnalyzer) -> None:
        """Verify list_primitives returns all primitives."""
        primitives = analyzer.list_primitives()
        assert isinstance(primitives, list)
        assert len(primitives) >= 7

        # Check each has required fields
        for prim in primitives:
            assert "name" in prim
            assert "description" in prim

    def test_issue_detection(self, analyzer: TTAAnalyzer) -> None:
        """Verify issues are detected in code."""
        code = """
async def risky():
    result = await external_api.call()  # No timeout!
    return result
"""
        result = analyzer.analyze(code)
        # Should detect async without timeout as an issue
        assert len(result.context.detected_issues) > 0 or len(result.recommendations) > 0

    def test_optimization_opportunities(self, analyzer: TTAAnalyzer) -> None:
        """Verify optimization opportunities are detected."""
        code = """
def get_user(user_id):
    return db.query(User).filter(User.id == user_id).first()

def get_users():
    return [get_user(i) for i in range(100)]  # Could be parallelized
"""
        result = analyzer.analyze(code)
        # Analysis should complete and potentially suggest optimizations
        assert result is not None

    def test_empty_code(self, analyzer: TTAAnalyzer) -> None:
        """Verify empty code is handled gracefully."""
        result = analyzer.analyze("")
        assert result is not None
        assert result.analysis.detected_patterns == []

    def test_complex_code_analysis(self, analyzer: TTAAnalyzer) -> None:
        """Verify complex code with multiple patterns."""
        code = """
async def production_workflow(data):
    # Validate input
    validated = await validate(data)

    # Fetch from multiple sources in parallel
    results = await asyncio.gather(
        fetch_from_db(validated),
        fetch_from_cache(validated),
        fetch_from_api(validated),
    )

    # Process with retry logic
    for attempt in range(3):
        try:
            processed = await process_results(results)
            break
        except ProcessingError:
            if attempt == 2:
                raise
            await asyncio.sleep(2 ** attempt)

    # Save with fallback
    try:
        await save_to_primary(processed)
    except Exception:
        await save_to_backup(processed)

    return processed
"""
        result = analyzer.analyze(code, file_path="workflow.py")

        # Should detect multiple patterns
        assert len(result.analysis.detected_patterns) >= 3

        # Should have multiple recommendations
        assert len(result.recommendations) >= 2

        # Complexity should be medium or high
        assert result.analysis.complexity_level in ["medium", "high"]

    def test_filter_by_confidence(self, analyzer: TTAAnalyzer) -> None:
        """Verify filter_by_confidence method works."""
        code = """
async def fetch():
    try:
        return await api.call()
    except Exception:
        pass
"""
        result = analyzer.analyze(code, min_confidence=0.1)
        filtered = result.filter_by_confidence(0.5)

        # filter_by_confidence returns a list of recommendations
        assert isinstance(filtered, list)
        assert len(filtered) <= len(result.recommendations)

    def test_get_top_recommendation(self, analyzer: TTAAnalyzer) -> None:
        """Verify get_top_recommendation returns highest confidence."""
        code = """
async def fetch():
    for i in range(3):
        try:
            return await api.call()
        except:
            await asyncio.sleep(i)
"""
        result = analyzer.analyze(code)
        top = result.get_top_recommendation()

        if top and result.recommendations:
            # Top should be highest confidence
            assert top.confidence_score >= result.recommendations[-1].confidence_score
