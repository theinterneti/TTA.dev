"""Tests for KnowledgeBasePrimitive."""

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.knowledge.knowledge_base import (
    KBPage,
    KBQuery,
    KBResult,
    KnowledgeBasePrimitive,
)


class TestKnowledgeBasePrimitive:
    """Test suite for KnowledgeBasePrimitive."""

    def test_initialization_defaults(self) -> None:
        """Test KB primitive initialization with defaults."""
        kb = KnowledgeBasePrimitive()

        assert kb.logseq_available is False
        assert kb.name == "knowledge_base"

    def test_initialization_with_logseq_available(self) -> None:
        """Test KB primitive initialization with LogSeq available."""
        kb = KnowledgeBasePrimitive(logseq_available=True)

        assert kb.logseq_available is True

    @pytest.mark.asyncio
    async def test_graceful_degradation_when_logseq_unavailable(self) -> None:
        """Test KB returns empty results when LogSeq MCP unavailable."""
        kb = KnowledgeBasePrimitive(logseq_available=False)

        query = KBQuery(
            query_type="best_practices",
            topic="testing",
            max_results=5,
        )

        context = WorkflowContext()
        result = await kb.execute(query, context)

        assert isinstance(result, KBResult)
        assert result.source == "fallback"
        assert result.pages == []
        assert result.total_found == 0
        assert result.query_time_ms >= 0

    @pytest.mark.asyncio
    async def test_best_practices_query(self) -> None:
        """Test best practices query execution."""
        kb = KnowledgeBasePrimitive(logseq_available=True)

        query = KBQuery(
            query_type="best_practices",
            topic="testing",
            stage="testing",
            max_results=3,
        )

        context = WorkflowContext()
        result = await kb.execute(query, context)

        assert isinstance(result, KBResult)
        assert result.source == "logseq"
        # Currently returns empty (MCP integration pending)
        assert isinstance(result.pages, list)
        assert result.total_found >= 0

    @pytest.mark.asyncio
    async def test_common_mistakes_query(self) -> None:
        """Test common mistakes query execution."""
        kb = KnowledgeBasePrimitive(logseq_available=True)

        query = KBQuery(
            query_type="common_mistakes",
            topic="deployment",
            stage="production",
            max_results=5,
        )

        context = WorkflowContext()
        result = await kb.execute(query, context)

        assert isinstance(result, KBResult)
        assert result.source == "logseq"

    @pytest.mark.asyncio
    async def test_examples_query(self) -> None:
        """Test examples query execution."""
        kb = KnowledgeBasePrimitive(logseq_available=True)

        query = KBQuery(
            query_type="examples",
            topic="stage-transitions",
            max_results=5,
        )

        context = WorkflowContext()
        result = await kb.execute(query, context)

        assert isinstance(result, KBResult)
        assert result.source == "logseq"

    @pytest.mark.asyncio
    async def test_related_pages_query(self) -> None:
        """Test related pages query execution."""
        kb = KnowledgeBasePrimitive(logseq_available=True)

        query = KBQuery(
            query_type="related",
            topic="Testing Best Practices",
            max_results=5,
        )

        context = WorkflowContext()
        result = await kb.execute(query, context)

        assert isinstance(result, KBResult)
        assert result.source == "logseq"

    @pytest.mark.asyncio
    async def test_tags_query(self) -> None:
        """Test query by tags execution."""
        kb = KnowledgeBasePrimitive(logseq_available=True)

        query = KBQuery(
            query_type="tags",
            topic="",  # Not used for tag queries
            tags=["testing", "best-practices"],
            max_results=5,
        )

        context = WorkflowContext()
        result = await kb.execute(query, context)

        assert isinstance(result, KBResult)
        assert result.source == "logseq"

    @pytest.mark.asyncio
    async def test_max_results_limit(self) -> None:
        """Test max_results parameter limits returned pages."""
        kb = KnowledgeBasePrimitive(logseq_available=True)

        query = KBQuery(
            query_type="best_practices",
            topic="testing",
            max_results=2,
        )

        context = WorkflowContext()
        result = await kb.execute(query, context)

        # Even if more found, should respect max_results
        assert len(result.pages) <= 2

    @pytest.mark.asyncio
    async def test_convenience_method_search_by_tags(self) -> None:
        """Test convenience method for searching by tags."""
        kb = KnowledgeBasePrimitive(logseq_available=False)

        result = await kb.search_by_tags(
            tags=["testing", "best-practices"],
            max_results=3,
        )

        assert isinstance(result, KBResult)
        assert result.source == "fallback"
        assert result.pages == []

    @pytest.mark.asyncio
    async def test_convenience_method_query_best_practices(self) -> None:
        """Test convenience method for querying best practices."""
        kb = KnowledgeBasePrimitive(logseq_available=False)

        result = await kb.query_best_practices(
            topic="testing",
            stage="testing",
            max_results=3,
        )

        assert isinstance(result, KBResult)
        assert result.source == "fallback"

    @pytest.mark.asyncio
    async def test_convenience_method_query_common_mistakes(self) -> None:
        """Test convenience method for querying common mistakes."""
        kb = KnowledgeBasePrimitive(logseq_available=False)

        result = await kb.query_common_mistakes(
            topic="deployment",
            stage="production",
        )

        assert isinstance(result, KBResult)
        assert result.source == "fallback"

    @pytest.mark.asyncio
    async def test_convenience_method_query_examples(self) -> None:
        """Test convenience method for querying examples."""
        kb = KnowledgeBasePrimitive(logseq_available=False)

        result = await kb.query_examples(topic="stage-transitions")

        assert isinstance(result, KBResult)
        assert result.source == "fallback"

    @pytest.mark.asyncio
    async def test_convenience_method_get_related_pages(self) -> None:
        """Test convenience method for getting related pages."""
        kb = KnowledgeBasePrimitive(logseq_available=False)

        result = await kb.get_related_pages(page_title="Testing Best Practices")

        assert isinstance(result, KBResult)
        assert result.source == "fallback"

    @pytest.mark.asyncio
    async def test_convenience_methods_create_default_context(self) -> None:
        """Test convenience methods create WorkflowContext when not provided."""
        kb = KnowledgeBasePrimitive(logseq_available=False)

        # All convenience methods should work without context parameter
        result1 = await kb.search_by_tags(tags=["test"])
        result2 = await kb.query_best_practices(topic="test")
        result3 = await kb.query_common_mistakes(topic="test")
        result4 = await kb.query_examples(topic="test")
        result5 = await kb.get_related_pages(page_title="test")

        assert all(
            isinstance(r, KBResult)
            for r in [result1, result2, result3, result4, result5]
        )

    @pytest.mark.asyncio
    async def test_query_time_measured(self) -> None:
        """Test query execution time is measured."""
        kb = KnowledgeBasePrimitive(logseq_available=False)

        query = KBQuery(
            query_type="best_practices",
            topic="testing",
        )

        result = await kb.execute(query, WorkflowContext())

        assert result.query_time_ms >= 0
        assert isinstance(result.query_time_ms, float)


class TestKBModels:
    """Test data models for KB queries and results."""

    def test_kb_page_model(self) -> None:
        """Test KBPage model creation."""
        page = KBPage(
            title="Testing Best Practices",
            content="# Testing\n\nBest practices...",
            tags=["testing", "best-practices"],
            url="logseq://graph/page/Testing%20Best%20Practices",
            relevance_score=0.95,
        )

        assert page.title == "Testing Best Practices"
        assert page.content == "# Testing\n\nBest practices..."
        assert page.tags == ["testing", "best-practices"]
        assert page.url == "logseq://graph/page/Testing%20Best%20Practices"
        assert page.relevance_score == 0.95

    def test_kb_page_defaults(self) -> None:
        """Test KBPage default values."""
        page = KBPage(
            title="Test Page",
            url="logseq://graph/page/Test",
        )

        assert page.content is None
        assert page.tags == []
        assert page.relevance_score == 1.0

    def test_kb_query_model(self) -> None:
        """Test KBQuery model creation."""
        query = KBQuery(
            query_type="best_practices",
            topic="testing",
            tags=["testing", "unit-tests"],
            stage="testing",
            max_results=10,
            include_content=True,
        )

        assert query.query_type == "best_practices"
        assert query.topic == "testing"
        assert query.tags == ["testing", "unit-tests"]
        assert query.stage == "testing"
        assert query.max_results == 10
        assert query.include_content is True

    def test_kb_query_defaults(self) -> None:
        """Test KBQuery default values."""
        query = KBQuery(
            query_type="examples",
            topic="deployment",
        )

        assert query.tags == []
        assert query.stage is None
        assert query.max_results == 5
        assert query.include_content is True

    def test_kb_result_model(self) -> None:
        """Test KBResult model creation."""
        pages = [
            KBPage(
                title="Page 1",
                url="logseq://graph/page/1",
            ),
            KBPage(
                title="Page 2",
                url="logseq://graph/page/2",
            ),
        ]

        result = KBResult(
            pages=pages,
            total_found=5,
            query_time_ms=42.5,
            source="logseq",
        )

        assert len(result.pages) == 2
        assert result.total_found == 5
        assert result.query_time_ms == 42.5
        assert result.source == "logseq"

    def test_kb_result_defaults(self) -> None:
        """Test KBResult default values."""
        result = KBResult(
            total_found=0,
            query_time_ms=1.0,
            source="fallback",
        )

        assert result.pages == []


class TestKBObservability:
    """Test observability features of KnowledgeBasePrimitive."""

    @pytest.mark.asyncio
    async def test_instrumented_primitive_base(self) -> None:
        """Test KB primitive uses InstrumentedPrimitive base."""
        kb = KnowledgeBasePrimitive(logseq_available=False)

        # InstrumentedPrimitive provides automatic span creation
        query = KBQuery(
            query_type="best_practices",
            topic="testing",
        )

        context = WorkflowContext(
            correlation_id="test-correlation-123",
        )

        result = await kb.execute(query, context)

        assert isinstance(result, KBResult)
        # Span creation tested in observability tests

    @pytest.mark.asyncio
    async def test_context_propagation(self) -> None:
        """Test WorkflowContext is propagated through queries."""
        kb = KnowledgeBasePrimitive(logseq_available=False)

        context = WorkflowContext(
            correlation_id="test-correlation-456",
            metadata={"user_id": "user-123"},
        )

        # Context should be available in convenience methods
        result = await kb.query_best_practices(
            topic="testing",
            context=context,
        )

        assert isinstance(result, KBResult)
        # Context propagation verified by InstrumentedPrimitive
