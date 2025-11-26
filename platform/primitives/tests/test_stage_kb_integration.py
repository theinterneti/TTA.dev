"""Tests for KB integration with StageManager.

This module tests the integration between KnowledgeBasePrimitive and
StageManager for contextual stage transition guidance.

NOTE: Tests that execute stage validations spawn subprocesses and should be
marked as integration. To avoid nested ``pytest`` invocations (which can cause
recursion and timeouts), we set an environment flag that tells the
``check_tests_pass`` validation to short-circuit instead of spawning a
subprocess.
"""

import os
from pathlib import Path

import pytest

from tta_dev_primitives import WorkflowContext

# Mark ALL tests in this module as integration since they execute stage
# validations that may spawn subprocesses.
pytestmark = pytest.mark.integration
from typing import Never

from tta_dev_primitives.knowledge import (
    KBPage,
    KBQuery,
    KBResult,
    KnowledgeBasePrimitive,
)
from tta_dev_primitives.lifecycle import (
    STAGE_CRITERIA_MAP,
    Stage,
    StageManager,
    StageRequest,
)


# Ensure we don't spawn a nested pytest subprocess when these tests exercise
# StageManager validations.
os.environ.setdefault("TTA_LIFECYCLE_SKIP_TEST_SUBPROCESS", "1")


class MockKBPrimitive(KnowledgeBasePrimitive):
    """Mock KB primitive that returns predefined results."""

    def __init__(self, mock_pages: list[KBPage] | None = None) -> None:
        """Initialize mock KB with predefined pages."""
        super().__init__(logseq_available=False)
        self.mock_pages = mock_pages or []
        self.query_count = 0

    async def _execute_impl(self, input_data: KBQuery, context: WorkflowContext) -> KBResult:
        """Return mock KB results.

        The parameter order matches ``KnowledgeBasePrimitive._execute_impl``
        (input_data first, then context), so calls via ``execute(query,
        context)`` behave consistently.
        """
        self.query_count += 1

        # Filter mock pages by query type
        filtered_pages = []
        for page in self.mock_pages:
            if input_data.query_type == "best_practices" and "best-practices" in page.tags:
                filtered_pages.append(page)
            elif input_data.query_type == "common_mistakes" and "common-mistakes" in page.tags:
                filtered_pages.append(page)

        return KBResult(
            pages=filtered_pages[: input_data.max_results],
            total_found=len(filtered_pages),
            query_time_ms=0.0,
            source="logseq",
        )


@pytest.mark.asyncio
async def test_stage_manager_without_kb() -> None:
    """Test StageManager works without KB (backward compatibility)."""
    manager = StageManager(stage_criteria_map=STAGE_CRITERIA_MAP)
    context = WorkflowContext(correlation_id="test-001")

    readiness = await manager.check_readiness(
        current_stage=Stage.EXPERIMENTATION,
        target_stage=Stage.TESTING,
        project_path=Path("."),
        context=context,
        kb=None,  # No KB provided
    )

    # Should work without KB
    assert readiness.current_stage == Stage.EXPERIMENTATION
    assert readiness.target_stage == Stage.TESTING
    assert readiness.kb_recommendations == []  # No recommendations without KB


@pytest.mark.asyncio
async def test_stage_manager_with_kb_no_results() -> None:
    """Test StageManager with KB that returns no results."""
    mock_kb = MockKBPrimitive(mock_pages=[])
    manager = StageManager(stage_criteria_map=STAGE_CRITERIA_MAP)
    context = WorkflowContext(correlation_id="test-002")

    readiness = await manager.check_readiness(
        current_stage=Stage.TESTING,
        target_stage=Stage.STAGING,
        project_path=Path("."),
        context=context,
        kb=mock_kb,
    )

    # Should query KB but get no results
    assert mock_kb.query_count >= 2  # Best practices + common mistakes
    assert readiness.kb_recommendations == []


@pytest.mark.asyncio
async def test_stage_manager_with_kb_best_practices() -> None:
    """Test StageManager with KB returning best practices."""
    mock_pages = [
        KBPage(
            title="STAGING Best Practices",
            content="Deploy to staging environment...",
            tags=["best-practices", "staging", "stage-staging"],
            url=None,
            relevance_score=1.0,
        ),
        KBPage(
            title="Integration Testing Guide",
            content="Run integration tests...",
            tags=["best-practices", "testing", "stage-staging"],
            url=None,
            relevance_score=0.9,
        ),
    ]

    mock_kb = MockKBPrimitive(mock_pages=mock_pages)
    manager = StageManager(stage_criteria_map=STAGE_CRITERIA_MAP)
    context = WorkflowContext(correlation_id="test-003")

    readiness = await manager.check_readiness(
        current_stage=Stage.TESTING,
        target_stage=Stage.STAGING,
        project_path=Path("."),
        context=context,
        kb=mock_kb,
    )

    # Should have KB recommendations
    assert len(readiness.kb_recommendations) > 0
    assert any(rec["type"] == "best_practice" for rec in readiness.kb_recommendations)

    # Check recommendation structure
    for rec in readiness.kb_recommendations:
        assert "title" in rec
        assert "type" in rec
        assert "tags" in rec


@pytest.mark.asyncio
async def test_stage_manager_with_kb_common_mistakes() -> None:
    """Test StageManager with KB returning common mistakes."""
    mock_pages = [
        KBPage(
            title="Common TESTING Mistakes",
            content="Avoid these mistakes...",
            tags=["common-mistakes", "testing", "stage-testing"],
            url=None,
            relevance_score=1.0,
        ),
        KBPage(
            title="Testing Antipatterns",
            content="Don't do this...",
            tags=["common-mistakes", "testing"],
            url=None,
            relevance_score=0.8,
        ),
    ]

    mock_kb = MockKBPrimitive(mock_pages=mock_pages)
    manager = StageManager(stage_criteria_map=STAGE_CRITERIA_MAP)
    context = WorkflowContext(correlation_id="test-004")

    readiness = await manager.check_readiness(
        current_stage=Stage.TESTING,
        target_stage=Stage.STAGING,
        project_path=Path("."),
        context=context,
        kb=mock_kb,
    )

    # Should have KB recommendations
    assert len(readiness.kb_recommendations) > 0
    assert any(rec["type"] == "common_mistake" for rec in readiness.kb_recommendations)


@pytest.mark.asyncio
async def test_stage_manager_with_kb_mixed_recommendations() -> None:
    """Test StageManager with KB returning both best practices and mistakes."""
    mock_pages = [
        KBPage(
            title="STAGING Best Practices",
            content="Deploy to staging...",
            tags=["best-practices", "staging", "stage-staging"],
            url=None,
            relevance_score=1.0,
        ),
        KBPage(
            title="TESTING Common Mistakes",
            content="Avoid these...",
            tags=["common-mistakes", "testing", "stage-testing"],
            url=None,
            relevance_score=1.0,
        ),
    ]

    mock_kb = MockKBPrimitive(mock_pages=mock_pages)
    manager = StageManager(stage_criteria_map=STAGE_CRITERIA_MAP)
    context = WorkflowContext(correlation_id="test-005")

    readiness = await manager.check_readiness(
        current_stage=Stage.TESTING,
        target_stage=Stage.STAGING,
        project_path=Path("."),
        context=context,
        kb=mock_kb,
    )

    # Should have both types of recommendations
    assert len(readiness.kb_recommendations) == 2
    types = [rec["type"] for rec in readiness.kb_recommendations]
    assert "best_practice" in types
    assert "common_mistake" in types


@pytest.mark.asyncio
async def test_stage_manager_kb_error_handling() -> None:
    """Test StageManager handles KB errors gracefully."""

    class ErrorKB(KnowledgeBasePrimitive):
        """KB that raises errors."""

        async def _execute_impl(self, input_data, context) -> Never:
            raise RuntimeError("KB query failed")

    error_kb = ErrorKB(logseq_available=False)
    manager = StageManager(stage_criteria_map=STAGE_CRITERIA_MAP)
    context = WorkflowContext(correlation_id="test-006")

    # Should not raise error, just return empty recommendations
    readiness = await manager.check_readiness(
        current_stage=Stage.TESTING,
        target_stage=Stage.STAGING,
        project_path=Path("."),
        context=context,
        kb=error_kb,
    )

    # Should still work without KB recommendations
    assert readiness.current_stage == Stage.TESTING
    assert readiness.target_stage == Stage.STAGING
    assert readiness.kb_recommendations == []


@pytest.mark.asyncio
async def test_stage_readiness_summary_with_kb() -> None:
    """Test StageReadiness.get_summary() includes KB recommendations."""
    mock_pages = [
        KBPage(
            title="STAGING Best Practices",
            content="Deploy to staging...",
            tags=["best-practices", "staging"],
            url=None,
            relevance_score=1.0,
        ),
    ]

    mock_kb = MockKBPrimitive(mock_pages=mock_pages)
    manager = StageManager(stage_criteria_map=STAGE_CRITERIA_MAP)
    context = WorkflowContext(correlation_id="test-007")

    readiness = await manager.check_readiness(
        current_stage=Stage.TESTING,
        target_stage=Stage.STAGING,
        project_path=Path("."),
        context=context,
        kb=mock_kb,
    )

    summary = readiness.get_summary()

    # Summary should include KB recommendations section
    assert "📚 KNOWLEDGE BASE RECOMMENDATIONS:" in summary
    assert "STAGING Best Practices" in summary
    assert "[BEST_PRACTICE]" in summary or "[best_practice]" in summary.lower()


@pytest.mark.integration  # Spawns subprocess to run pytest
@pytest.mark.asyncio
async def test_stage_manager_execute_without_kb() -> None:
    """Test StageManager.execute() still works (backward compatibility)."""
    manager = StageManager(stage_criteria_map=STAGE_CRITERIA_MAP)
    context = WorkflowContext(correlation_id="test-008")

    request = StageRequest(
        project_path=Path("."),
        current_stage=Stage.EXPERIMENTATION,
        target_stage=Stage.TESTING,
    )

    # execute() doesn't pass KB, so it should work without it
    readiness = await manager.execute(context, request)

    assert readiness.current_stage == Stage.EXPERIMENTATION
    assert readiness.target_stage == Stage.TESTING
    assert readiness.kb_recommendations == []  # No KB used
