"""Tests for StageManager KB integration.

Tests the integration between StageManager and KnowledgeBasePrimitive,
ensuring that KB recommendations are properly included in stage validation.

NOTE: These tests spawn subprocess tests and should be run as integration tests.
"""

from pathlib import Path

import pytest

from tta_dev_primitives import WorkflowContext

# Mark all tests in this module as integration since they spawn subprocesses
pytestmark = pytest.mark.integration
from tta_dev_primitives.knowledge import (
    KBPage,
    KBResult,
    KnowledgeBasePrimitive,
)
from tta_dev_primitives.lifecycle import (
    Stage,
    StageManager,
)


class TestStageManagerKBIntegration:
    """Test StageManager integration with KnowledgeBasePrimitive."""

    @pytest.mark.asyncio
    async def test_check_readiness_without_kb(self) -> None:
        """Test check_readiness works without KB parameter.

        Note: Uses empty stage_criteria_map to avoid running expensive
        validation checks (like pytest) that would cause test timeouts.
        This test focuses on KB integration, not validation logic.
        """
        # Use empty criteria map to avoid subprocess timeouts
        # Previously used STAGE_CRITERIA_MAP which includes TESTS_PASS check
        # that runs pytest recursively, causing 180+ second timeouts
        manager = StageManager(stage_criteria_map={})
        context = WorkflowContext(correlation_id="test-001")

        readiness = await manager.check_readiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            project_path=Path("."),
            context=context,
        )

        assert readiness.kb_recommendations == []

    @pytest.mark.asyncio
    async def test_check_readiness_with_kb_no_results(self) -> None:
        """Test check_readiness with KB that returns no results."""
        # Create KB that returns empty results
        kb = KnowledgeBasePrimitive(logseq_available=False)
        # Use empty criteria map to avoid pytest recursion timeouts
        manager = StageManager(stage_criteria_map={})
        context = WorkflowContext(correlation_id="test-002")

        readiness = await manager.check_readiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            project_path=Path("."),
            context=context,
            kb=kb,
        )

        # Should have empty list since KB returns no results
        assert readiness.kb_recommendations == []

    @pytest.mark.asyncio
    async def test_check_readiness_with_kb_results(self) -> None:
        """Test check_readiness with KB that returns results."""
        # Create mock KB with results
        kb = KnowledgeBasePrimitive(logseq_available=False)

        # Mock the execute method to return results based on query type
        mock_pages = [
            KBPage(
                title="Staging Best Practices",
                content="Deploy to staging first",
                tags=["best-practices", "staging"],
                url="https://example.com/staging-bp",
                relevance_score=0.95,
            ),
            KBPage(
                title="Common Staging Mistakes",
                content="Don't skip integration tests",
                tags=["common-mistakes", "staging"],
                url="https://example.com/staging-mistakes",
                relevance_score=0.90,
            ),
        ]

        async def mock_execute(query, context):
            if query.query_type == "best_practices":
                return KBResult(
                    pages=[mock_pages[0]],
                    total_found=1,
                    query_time_ms=5.0,
                    source="logseq",
                )
            else:  # common_mistakes
                return KBResult(
                    pages=[mock_pages[1]],
                    total_found=1,
                    query_time_ms=5.0,
                    source="logseq",
                )

        kb.execute = mock_execute

        # Use empty criteria map to avoid pytest recursion timeouts
        manager = StageManager(stage_criteria_map={})
        context = WorkflowContext(correlation_id="test-003")

        readiness = await manager.check_readiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            project_path=Path("."),
            context=context,
            kb=kb,
        )

        # Should have 2 recommendations (1 from best practices, 1 from common mistakes)
        assert len(readiness.kb_recommendations) == 2
        assert readiness.kb_recommendations[0]["title"] == "Staging Best Practices"
        assert readiness.kb_recommendations[0]["type"] == "best_practice"
        assert readiness.kb_recommendations[1]["title"] == "Common Staging Mistakes"
        assert readiness.kb_recommendations[1]["type"] == "common_mistake"

    @pytest.mark.asyncio
    async def test_check_readiness_kb_queries_correct_stages(self) -> None:
        """Test that KB queries use correct stage names."""
        kb = KnowledgeBasePrimitive(logseq_available=False)

        # Track what was queried
        queries = []

        async def mock_execute(query, context):
            queries.append((query.query_type, query.topic, query.stage))
            return KBResult(
                pages=[], total_found=0, query_time_ms=0.0, source="fallback"
            )

        kb.execute = mock_execute

        # Use empty criteria map to avoid pytest recursion timeouts
        manager = StageManager(stage_criteria_map={})
        context = WorkflowContext(correlation_id="test-004")

        await manager.check_readiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            project_path=Path("."),
            context=context,
            kb=kb,
        )

        # Should have 2 queries: best practices for target, common mistakes for current
        assert len(queries) == 2

        # First query: best practices for target stage (staging)
        assert queries[0] == ("best_practices", "staging", "staging")

        # Second query: common mistakes for current stage (testing)
        assert queries[1] == ("common_mistakes", "testing", "testing")

    @pytest.mark.asyncio
    async def test_kb_recommendations_in_summary(self) -> None:
        """Test that KB recommendations appear in readiness summary."""
        kb = KnowledgeBasePrimitive(logseq_available=False)

        mock_page = KBPage(
            title="Test Best Practice",
            content="Always test thoroughly",
            tags=["best-practices"],
            url="https://example.com/test-bp",
            relevance_score=1.0,
        )

        async def mock_execute(query, context):
            if query.query_type == "best_practices":
                return KBResult(
                    pages=[mock_page],
                    total_found=1,
                    query_time_ms=1.0,
                    source="logseq",
                )
            else:  # common_mistakes
                return KBResult(
                    pages=[], total_found=0, query_time_ms=0.0, source="fallback"
                )

        kb.execute = mock_execute

        # Use empty criteria map to avoid pytest recursion timeouts
        manager = StageManager(stage_criteria_map={})
        context = WorkflowContext(correlation_id="test-005")

        readiness = await manager.check_readiness(
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
            project_path=Path("."),
            context=context,
            kb=kb,
        )

        summary = readiness.get_summary()

        # Summary should include KB recommendations section
        assert "KNOWLEDGE BASE RECOMMENDATIONS:" in summary
        assert "[BEST_PRACTICE] Test Best Practice" in summary
        assert "Test Best Practice" in summary
