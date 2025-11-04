"""Tests for SessionContextBuilder tool.

Tests cover:
- RankByRelevance primitive
- SessionContextBuilder initialization
- Context building with different options
- KB page finding and ranking
- Code file finding and ranking
- TODO extraction and filtering
- Test file discovery
- Related topic extraction
- Summary generation
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from tta_dev_primitives import WorkflowContext

from tta_kb_automation.tools.session_context_builder import (
    RankByRelevance,
    SessionContextBuilder,
)


class TestRankByRelevance:
    """Test the RankByRelevance primitive."""

    @pytest.mark.asyncio
    async def test_ranks_exact_matches_highest(self):
        """Exact topic matches should score highest."""
        ranker = RankByRelevance(topic="CachePrimitive", max_results=3)
        context = WorkflowContext(workflow_id="test")

        items = [
            {"title": "Other Stuff", "content": "random content"},
            {"title": "CachePrimitive", "content": "docs for cache"},
            {"title": "Retry Pattern", "content": "retry logic"},
        ]

        result = await ranker.execute({"items": items}, context)

        assert len(result["ranked_items"]) == 3
        # CachePrimitive should be first
        assert result["ranked_items"][0]["title"] == "CachePrimitive"
        assert result["scores"][0] > result["scores"][1]

    @pytest.mark.asyncio
    async def test_respects_max_results(self):
        """Should limit results to max_results."""
        ranker = RankByRelevance(topic="test", max_results=2)
        context = WorkflowContext(workflow_id="test")

        items = [{"title": f"Item {i}"} for i in range(10)]

        result = await ranker.execute({"items": items}, context)

        assert len(result["ranked_items"]) == 2
        assert result["total_scored"] == 10

    @pytest.mark.asyncio
    async def test_word_boundary_matching(self):
        """Should match topic words across different fields."""
        ranker = RankByRelevance(topic="cache primitive", max_results=5)
        context = WorkflowContext(workflow_id="test")

        items = [
            {"title": "CachePrimitive", "content": ""},
            {"title": "Other", "content": "cache and primitive mentioned"},
            {"title": "Unrelated", "content": "nothing here"},
        ]

        result = await ranker.execute({"items": items}, context)

        # Both cache-related items should rank above unrelated
        assert result["ranked_items"][0]["title"] in ["CachePrimitive", "Other"]
        assert result["ranked_items"][1]["title"] in ["CachePrimitive", "Other"]
        assert result["ranked_items"][2]["title"] == "Unrelated"

    @pytest.mark.asyncio
    async def test_handles_empty_items(self):
        """Should handle empty item list gracefully."""
        ranker = RankByRelevance(topic="test", max_results=5)
        context = WorkflowContext(workflow_id="test")

        result = await ranker.execute({"items": []}, context)

        assert result["ranked_items"] == []
        assert result["scores"] == []
        assert result["total_scored"] == 0

    @pytest.mark.asyncio
    async def test_handles_non_dict_items(self):
        """Should handle string and Path items."""
        ranker = RankByRelevance(topic="cache", max_results=5)
        context = WorkflowContext(workflow_id="test")

        items = [
            "packages/tta-dev-primitives/src/cache.py",
            Path("packages/other/retry.py"),
            "unrelated/file.txt",
        ]

        result = await ranker.execute({"items": items}, context)

        # Cache item should rank first
        assert "cache" in str(result["ranked_items"][0]).lower()


class TestSessionContextBuilder:
    """Test SessionContextBuilder tool."""

    def test_initialization_defaults(self):
        """Should initialize with default values."""
        builder = SessionContextBuilder()

        assert builder.kb_path == Path("logseq")
        assert builder.code_path == Path("packages")
        assert builder.max_kb_pages == 5
        assert builder.max_code_files == 10
        assert builder.max_todos == 20
        assert builder.max_tests == 10

    def test_initialization_custom_paths(self):
        """Should accept custom paths."""
        builder = SessionContextBuilder(
            kb_path="custom/kb",
            code_path="custom/code",
            max_kb_pages=3,
            max_code_files=5,
        )

        assert builder.kb_path == Path("custom/kb")
        assert builder.code_path == Path("custom/code")
        assert builder.max_kb_pages == 3
        assert builder.max_code_files == 5

    @pytest.mark.asyncio
    async def test_build_context_basic(self):
        """Should build context with all components."""
        builder = SessionContextBuilder()

        # Mock all the internal methods
        with (
            patch.object(
                builder, "_find_relevant_kb_pages", new_callable=AsyncMock
            ) as mock_kb,
            patch.object(
                builder, "_find_relevant_code_files", new_callable=AsyncMock
            ) as mock_code,
            patch.object(
                builder, "_find_relevant_todos", new_callable=AsyncMock
            ) as mock_todos,
            patch.object(
                builder, "_find_relevant_tests", new_callable=AsyncMock
            ) as mock_tests,
        ):
            mock_kb.return_value = [
                {
                    "title": "Test Page",
                    "path": "logseq/pages/test.md",
                    "excerpt": "test content",
                    "tags": ["testing"],
                }
            ]
            mock_code.return_value = [
                {"path": "packages/test.py", "summary": "test module"}
            ]
            mock_todos.return_value = [{"text": "TODO: test this", "file": "test.py"}]
            mock_tests.return_value = [
                {"path": "tests/test_feature.py", "test_count": 5}
            ]

            result = await builder.build_context(topic="test feature")

            assert result["topic"] == "test feature"
            assert len(result["kb_pages"]) == 1
            assert len(result["code_files"]) == 1
            assert len(result["todos"]) == 1
            assert len(result["tests"]) == 1
            assert "summary" in result

    @pytest.mark.asyncio
    async def test_build_context_selective(self):
        """Should respect include_* flags."""
        builder = SessionContextBuilder()

        with (
            patch.object(
                builder, "_find_relevant_kb_pages", new_callable=AsyncMock
            ) as mock_kb,
            patch.object(
                builder, "_find_relevant_code_files", new_callable=AsyncMock
            ) as mock_code,
            patch.object(
                builder, "_find_relevant_todos", new_callable=AsyncMock
            ) as mock_todos,
            patch.object(
                builder, "_find_relevant_tests", new_callable=AsyncMock
            ) as mock_tests,
        ):
            mock_kb.return_value = []
            mock_code.return_value = []
            mock_todos.return_value = []
            mock_tests.return_value = []

            result = await builder.build_context(
                topic="test",
                include_kb=True,
                include_code=False,
                include_todos=False,
                include_tests=False,
            )

            # Only KB should be called
            mock_kb.assert_called_once()
            mock_code.assert_not_called()
            mock_todos.assert_not_called()
            mock_tests.assert_not_called()

            assert "kb_pages" in result
            assert "code_files" not in result
            assert "todos" not in result
            assert "tests" not in result

    @pytest.mark.asyncio
    async def test_find_relevant_kb_pages(self):
        """Should find and rank KB pages."""
        builder = SessionContextBuilder()

        mock_pages = [
            {
                "title": "CachePrimitive",
                "content": "Cache primitive documentation",
                "path": Path("logseq/pages/cache.md"),
                "tags": ["primitive"],
                "is_journal": False,
                "links": ["TTA Primitives"],
            },
            {
                "title": "Unrelated",
                "content": "Something else",
                "path": Path("logseq/pages/other.md"),
                "tags": [],
                "is_journal": False,
                "links": [],
            },
        ]

        with patch(
            "tta_kb_automation.tools.session_context_builder.ParseLogseqPages"
        ) as MockParser:
            mock_parser = AsyncMock()
            mock_parser.execute = AsyncMock(return_value={"pages": mock_pages})
            MockParser.return_value = mock_parser

            context = WorkflowContext(workflow_id="test")
            result = await builder._find_relevant_kb_pages("CachePrimitive", context)

            assert len(result) > 0
            # Most relevant page should be first
            assert "cache" in result[0]["title"].lower()

    @pytest.mark.asyncio
    async def test_find_relevant_code_files(self):
        """Should find and rank code files."""
        builder = SessionContextBuilder()

        mock_files = [
            Path("packages/tta-dev-primitives/src/cache.py"),
            Path("packages/tta-dev-primitives/src/retry.py"),
        ]

        with (
            patch(
                "tta_kb_automation.tools.session_context_builder.ScanCodebase"
            ) as MockScanner,
            patch(
                "tta_kb_automation.tools.session_context_builder.ParseDocstrings"
            ) as MockParser,
        ):
            mock_scanner = AsyncMock()
            mock_scanner.execute = AsyncMock(return_value={"files": mock_files})
            MockScanner.return_value = mock_scanner

            mock_parser = AsyncMock()
            mock_parser.execute = AsyncMock(
                return_value={
                    "module_docstring": "Cache implementation",
                    "classes": [],
                    "functions": [],
                }
            )
            MockParser.return_value = mock_parser

            context = WorkflowContext(workflow_id="test")
            result = await builder._find_relevant_code_files("cache", context)

            assert len(result) > 0
            assert any("cache" in r["path"].lower() for r in result)

    @pytest.mark.asyncio
    async def test_find_relevant_todos(self):
        """Should find and filter TODOs by relevance."""
        builder = SessionContextBuilder()

        mock_files = [Path("packages/test.py")]

        with (
            patch(
                "tta_kb_automation.tools.session_context_builder.ScanCodebase"
            ) as MockScanner,
            patch(
                "tta_kb_automation.tools.session_context_builder.ExtractTODOs"
            ) as MockExtractor,
        ):
            mock_scanner = AsyncMock()
            mock_scanner.execute = AsyncMock(return_value={"files": mock_files})
            MockScanner.return_value = mock_scanner

            mock_extractor = AsyncMock()
            mock_extractor.execute = AsyncMock(
                return_value={
                    "todos": [
                        {
                            "text": "TODO: Implement cache invalidation",
                            "file": "test.py",
                            "line": 10,
                        },
                        {
                            "text": "TODO: Add retry logic",
                            "file": "test.py",
                            "line": 20,
                        },
                    ]
                }
            )
            MockExtractor.return_value = mock_extractor

            context = WorkflowContext(workflow_id="test")
            result = await builder._find_relevant_todos("cache", context)

            # Should only return cache-related TODO
            assert len(result) == 1
            assert "cache" in result[0]["text"].lower()

    @pytest.mark.asyncio
    async def test_find_relevant_tests(self):
        """Should find and analyze test files."""
        builder = SessionContextBuilder()

        mock_test_files = [
            Path("packages/tests/test_cache.py"),
            Path("packages/tests/test_retry.py"),
        ]

        with (
            patch(
                "tta_kb_automation.tools.session_context_builder.ScanCodebase"
            ) as MockScanner,
            patch(
                "tta_kb_automation.tools.session_context_builder.AnalyzeCodeStructure"
            ) as MockAnalyzer,
        ):
            mock_scanner = AsyncMock()
            mock_scanner.execute = AsyncMock(return_value={"files": mock_test_files})
            MockScanner.return_value = mock_scanner

            mock_analyzer = AsyncMock()
            mock_analyzer.execute = AsyncMock(
                return_value={
                    "functions": ["test_cache_hit", "test_cache_miss", "test_ttl"]
                }
            )
            MockAnalyzer.return_value = mock_analyzer

            context = WorkflowContext(workflow_id="test")
            result = await builder._find_relevant_tests("cache", context)

            assert len(result) > 0
            # Cache test should be ranked first
            assert "cache" in result[0]["path"].lower()
            assert result[0]["test_count"] == 3

    def test_extract_related_topics(self):
        """Should extract related topics from KB page."""
        builder = SessionContextBuilder()

        kb_page = {
            "links": ["TTA Primitives", "Performance"],
            "tags": ["caching", "optimization"],
        }

        related = builder._extract_related_topics(kb_page)

        assert "TTA Primitives" in related
        assert "Performance" in related
        assert "caching" in related
        assert "optimization" in related

    def test_extract_excerpt_with_topic(self):
        """Should extract excerpt around topic mention."""
        builder = SessionContextBuilder()

        content = (
            "This is a long document. " * 10
            + "The CachePrimitive is very important. "
            + "More content here. " * 10
        )

        excerpt = builder._extract_excerpt(content, "CachePrimitive", max_chars=100)

        assert "CachePrimitive" in excerpt
        assert excerpt.startswith("...")
        assert excerpt.endswith("...")
        assert len(excerpt) <= 110  # Some margin for ellipsis

    def test_extract_excerpt_without_topic(self):
        """Should return start of content if topic not found."""
        builder = SessionContextBuilder()

        content = "This is the start of the document. " * 10

        excerpt = builder._extract_excerpt(content, "NonExistent", max_chars=100)

        assert excerpt.startswith("This is the start")
        assert len(excerpt) <= 103  # max_chars + "..."

    def test_generate_summary(self):
        """Should generate readable summary."""
        builder = SessionContextBuilder()

        context_parts = {
            "topic": "CachePrimitive",
            "kb_pages": [
                {
                    "title": "Cache Docs",
                    "excerpt": "Cache docs excerpt",
                    "path": "kb/cache.md",
                }
            ],
            "code_files": [{"path": "src/cache.py", "summary": "Cache implementation"}],
            "todos": [{"text": "TODO: Fix cache", "file": "cache.py"}],
            "tests": [{"path": "tests/test_cache.py", "test_count": 5}],
            "related_topics": ["Performance", "Optimization"],
        }

        summary = builder._generate_summary(context_parts)

        assert "CachePrimitive" in summary
        assert "1 relevant KB pages" in summary
        assert "1 relevant code files" in summary
        assert "1 relevant TODOs" in summary
        assert "1 relevant test files" in summary
        assert "Performance" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
