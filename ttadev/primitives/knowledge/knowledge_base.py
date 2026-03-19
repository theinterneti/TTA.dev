"""Knowledge base primitive for querying contextual guidance backends.

# See: [[TTA.dev/Primitives/KnowledgeBasePrimitive]]
"""

import time
from typing import Literal

from pydantic import BaseModel, Field

from ..core.base import WorkflowContext
from ..observability.instrumented_primitive import (
    InstrumentedPrimitive,
)


class KBPage(BaseModel):
    """Single page from knowledge base."""

    title: str = Field(description="Page title")
    content: str | None = Field(default=None, description="Page content markdown")
    tags: list[str] = Field(default_factory=list, description="Page tags")
    url: str | None = Field(default=None, description="Knowledge source URL (optional)")
    relevance_score: float = Field(default=1.0, description="Relevance score (0.0-1.0)")


class KBQuery(BaseModel):
    """Query to knowledge base."""

    query_type: Literal["best_practices", "common_mistakes", "examples", "related", "tags"] = Field(
        description="Type of query to perform"
    )
    topic: str = Field(description="Topic to search for")
    tags: list[str] = Field(default_factory=list, description="Tags to filter by")
    stage: str | None = Field(default=None, description="Lifecycle stage context (optional)")
    max_results: int = Field(default=5, description="Maximum pages to return")
    include_content: bool = Field(default=True, description="Include page content in results")


class KBResult(BaseModel):
    """Result from knowledge base query."""

    pages: list[KBPage] = Field(default_factory=list, description="Matching pages")
    total_found: int = Field(description="Total pages found")
    query_time_ms: float = Field(description="Query execution time in milliseconds")
    source: Literal["backend", "fallback"] = Field(
        description="Result source (backend=query backend, fallback=empty response)"
    )


class KnowledgeBasePrimitive(InstrumentedPrimitive[KBQuery, KBResult]):
    """Query a knowledge backend for contextual guidance.

    This primitive provides:
    - Best practices queries
    - Common mistakes warnings
    - Related examples
    - Stage-specific recommendations

    Gracefully degrades when the configured backend is unavailable.

    Example:
        ```python
        from ttadev.primitives.knowledge import (
            KnowledgeBasePrimitive,
            KBQuery,
        )
        from ttadev.primitives.core.base import WorkflowContext

        # Create KB primitive
        kb = KnowledgeBasePrimitive(backend_available=True)

        # Query best practices
        query = KBQuery(
            query_type="best_practices",
            topic="testing",
            stage="testing",
            max_results=3
        )

        context = WorkflowContext()
        result = await kb.execute(query, context)

        for page in result.pages:
            print(f"📄 {page.title}")
            print(f"   {page.content[:100]}...")
        ```
    """

    def __init__(self, backend_available: bool = False) -> None:
        """Initialize KB primitive.

        Args:
            backend_available: Whether a knowledge backend is available in the
                current environment.
        """
        super().__init__(name="knowledge_base")
        self.backend_available = backend_available

    async def _execute_impl(self, input_data: KBQuery, context: WorkflowContext) -> KBResult:
        """Execute knowledge base query.

        Args:
            input_data: Query parameters
            context: Workflow context for observability

        Returns:
            KBResult with matching pages or empty result if no backend is available
        """
        start_time = time.time()

        if not self.backend_available:
            # Graceful degradation - return empty result
            return KBResult(
                pages=[],
                total_found=0,
                query_time_ms=(time.time() - start_time) * 1000,
                source="fallback",
            )

        # Execute query based on type
        if input_data.query_type == "best_practices":
            pages = await self._query_best_practices_impl(input_data, context)
        elif input_data.query_type == "common_mistakes":
            pages = await self._query_common_mistakes_impl(input_data, context)
        elif input_data.query_type == "examples":
            pages = await self._query_examples_impl(input_data, context)
        elif input_data.query_type == "related":
            pages = await self._query_related_impl(input_data, context)
        elif input_data.query_type == "tags":
            pages = await self._query_by_tags_impl(input_data, context)
        else:
            pages = []

        query_time_ms = (time.time() - start_time) * 1000

        return KBResult(
            pages=pages[: input_data.max_results],
            total_found=len(pages),
            query_time_ms=query_time_ms,
            source="backend",
        )

    async def _query_best_practices_impl(
        self, query: KBQuery, context: WorkflowContext
    ) -> list[KBPage]:
        """Query best practices pages.

        Searches for pages tagged with #best-practices and matching topic.
        If stage provided, also filters by #stage-{stage}.

        Args:
            query: Query parameters
            context: Workflow context

        Returns:
            List of matching KB pages
        """
        # Build tag filter
        search_tags = ["best-practices", query.topic]
        if query.stage:
            search_tags.append(f"stage-{query.stage}")

        # TODO: Call the configured knowledge backend when available.
        return []

    async def _query_common_mistakes_impl(
        self, query: KBQuery, context: WorkflowContext
    ) -> list[KBPage]:
        """Query common mistakes pages.

        Searches for pages tagged with #common-mistakes and matching topic.

        Args:
            query: Query parameters
            context: Workflow context

        Returns:
            List of matching KB pages
        """
        search_tags = ["common-mistakes", query.topic]
        if query.stage:
            search_tags.append(f"stage-{query.stage}")

        # TODO: Call the configured knowledge backend.
        return []

    async def _query_examples_impl(self, query: KBQuery, context: WorkflowContext) -> list[KBPage]:
        """Query example pages.

        Searches for pages tagged with #examples and matching topic.

        Args:
            query: Query parameters
            context: Workflow context

        Returns:
            List of matching KB pages
        """
        # TODO: Call the configured knowledge backend with tags ["examples", query.topic].
        return []

    async def _query_related_impl(self, query: KBQuery, context: WorkflowContext) -> list[KBPage]:
        """Query related pages.

        Finds pages related to the specified topic.

        Args:
            query: Query parameters (topic = page title to find relations for)
            context: Workflow context

        Returns:
            List of related KB pages
        """
        # TODO: Call the configured knowledge backend for related pages.
        return []

    async def _query_by_tags_impl(self, query: KBQuery, context: WorkflowContext) -> list[KBPage]:
        """Query by tags directly.

        Args:
            query: Query parameters (uses query.tags)
            context: Workflow context

        Returns:
            List of matching KB pages
        """
        # TODO: Call the configured knowledge backend to search by tags.
        return []

    # Convenience methods for common queries

    async def search_by_tags(
        self,
        tags: list[str],
        max_results: int = 5,
        context: WorkflowContext | None = None,
    ) -> KBResult:
        """Search KB by tags.

        Args:
            tags: Tags to search for (e.g., ["best-practices", "testing"])
            max_results: Maximum pages to return
            context: Workflow context for observability

        Returns:
            KBResult with matching pages

        Example:
            ```python
            kb = KnowledgeBasePrimitive(backend_available=True)
            result = await kb.search_by_tags(
                tags=["testing", "best-practices"],
                max_results=3
            )

            for page in result.pages:
                print(f"📄 {page.title}")
                print(f"   Tags: {', '.join(page.tags)}")
            ```
        """
        query = KBQuery(
            query_type="tags",
            topic="",  # Not used for tag queries
            tags=tags,
            max_results=max_results,
        )
        return await self.execute(query, context or WorkflowContext())

    async def query_best_practices(
        self,
        topic: str,
        stage: str | None = None,
        max_results: int = 5,
        context: WorkflowContext | None = None,
    ) -> KBResult:
        """Query best practices for a topic.

        Args:
            topic: Topic to query (e.g., "deployment", "testing")
            stage: Lifecycle stage for context (optional)
            max_results: Maximum results to return
            context: Workflow context

        Returns:
            KBResult with best practice pages

        Example:
            ```python
            result = await kb.query_best_practices(
                topic="testing",
                stage="testing",
                max_results=3
            )

            for page in result.pages:
                print(f"✅ {page.title}")
            ```
        """
        query = KBQuery(
            query_type="best_practices",
            topic=topic,
            stage=stage,
            max_results=max_results,
        )
        return await self.execute(query, context or WorkflowContext())

    async def query_common_mistakes(
        self,
        topic: str,
        stage: str | None = None,
        max_results: int = 5,
        context: WorkflowContext | None = None,
    ) -> KBResult:
        """Query common mistakes for a topic.

        Args:
            topic: Topic to query
            stage: Lifecycle stage for context (optional)
            max_results: Maximum results to return
            context: Workflow context

        Returns:
            KBResult with common mistake warnings

        Example:
            ```python
            result = await kb.query_common_mistakes(
                topic="deployment",
                stage="production"
            )

            for page in result.pages:
                print(f"⚠️ {page.title}")
            ```
        """
        query = KBQuery(
            query_type="common_mistakes",
            topic=topic,
            stage=stage,
            max_results=max_results,
        )
        return await self.execute(query, context or WorkflowContext())

    async def query_examples(
        self,
        topic: str,
        max_results: int = 5,
        context: WorkflowContext | None = None,
    ) -> KBResult:
        """Query examples for a topic.

        Args:
            topic: Topic to query
            max_results: Maximum results to return
            context: Workflow context

        Returns:
            KBResult with example pages

        Example:
            ```python
            result = await kb.query_examples(topic="stage-transitions")

            for page in result.pages:
                print(f"💡 {page.title}")
            ```
        """
        query = KBQuery(
            query_type="examples",
            topic=topic,
            max_results=max_results,
        )
        return await self.execute(query, context or WorkflowContext())

    async def get_related_pages(
        self,
        page_title: str,
        max_results: int = 5,
        context: WorkflowContext | None = None,
    ) -> KBResult:
        """Get pages related to a given page.

        Args:
            page_title: Page to find relations for
            max_results: Maximum results
            context: Workflow context

        Returns:
            KBResult with related pages

        Example:
            ```python
            result = await kb.get_related_pages(
                page_title="Testing Best Practices"
            )

            for page in result.pages:
                print(f"🔗 {page.title}")
            ```
        """
        query = KBQuery(
            query_type="related",
            topic=page_title,  # Use topic field for page title
            max_results=max_results,
        )
        return await self.execute(query, context or WorkflowContext())
