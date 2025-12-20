"""Tests for high-level KB automation workflows.

Tests cover:
- validate_kb_links workflow
- sync_code_todos workflow
- build_cross_references workflow
- build_session_context workflow
- document_feature workflow
- pre_commit_validation workflow
"""

from pathlib import Path

import pytest

from tta_kb_automation.workflows import (
    build_cross_references,
    build_session_context,
    document_feature,
    pre_commit_validation,
    validate_kb_links,
)


@pytest.fixture
def mock_kb(tmp_path):
    """Create a mock Logseq KB structure."""
    kb_dir = tmp_path / "logseq"
    pages_dir = kb_dir / "pages"
    journals_dir = kb_dir / "journals"

    pages_dir.mkdir(parents=True)
    journals_dir.mkdir(parents=True)

    # Create some pages
    (pages_dir / "Index.md").write_text("""# Index

Welcome to the knowledge base.

## Links
- [[TTA Primitives]]
- [[Architecture]]
""")

    (pages_dir / "TTA Primitives.md").write_text("""# TTA Primitives

Core workflow building blocks.

## Links
- [[CachePrimitive]]
- [[RetryPrimitive]]
- [[MissingPage]]  # This link is broken
""")

    (pages_dir / "CachePrimitive.md").write_text("""# CachePrimitive

LRU cache with TTL support.

## Implementation
See `platform/primitives/src/tta_dev_primitives/performance/cache.py`

## Related
- [[TTA Primitives]]
""")

    (pages_dir / "RetryPrimitive.md").write_text("""# RetryPrimitive

Retry with exponential backoff.

## Related
- [[TTA Primitives]]
""")

    # Orphaned page (no incoming links)
    (pages_dir / "OrphanedPage.md").write_text("""# Orphaned Page

This page has no incoming links.
""")

    return kb_dir


@pytest.fixture
def mock_codebase(tmp_path):
    """Create a mock codebase structure."""
    code_dir = tmp_path / "platform"
    src_dir = code_dir / "src"

    src_dir.mkdir(parents=True)

    # Create some Python files
    (src_dir / "cache.py").write_text('''"""CachePrimitive implementation.

See: [[CachePrimitive]]
"""

class CachePrimitive:
    """LRU cache with TTL.

    KB: CachePrimitive
    """

    def __init__(self, ttl: int = 3600):
        # TODO: Add metrics collection
        self.ttl = ttl

    def get(self, key: str):
        # TODO: Implement cache miss handling
        pass

    def set(self, key: str, value):
        # TODO: Add TTL validation
        pass
''')

    (src_dir / "retry.py").write_text('''"""RetryPrimitive implementation."""

class RetryPrimitive:
    """Retry with backoff.

    [[RetryPrimitive]]
    """

    def __init__(self, max_retries: int = 3):
        # TODO: Add jitter support
        self.max_retries = max_retries
''')

    return code_dir


class TestValidateKBLinks:
    """Test validate_kb_links workflow."""

    @pytest.mark.asyncio
    async def test_validates_kb_links(self, mock_kb):
        """Test basic KB link validation."""
        result = await validate_kb_links(str(mock_kb))

        assert "broken_links" in result
        assert "orphaned_pages" in result
        assert "valid_links" in result
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_detects_broken_links(self, mock_kb):
        """Test that broken links are detected."""
        result = await validate_kb_links(str(mock_kb))

        # Should detect [[MissingPage]] as broken
        broken_targets = [link["target"] for link in result.get("broken_links", [])]
        assert "MissingPage" in broken_targets

    @pytest.mark.asyncio
    async def test_detects_orphaned_pages(self, mock_kb):
        """Test that orphaned pages are detected."""
        result = await validate_kb_links(str(mock_kb))

        # Should detect OrphanedPage as orphaned
        orphaned = result.get("orphaned_pages", [])
        assert any("Orphaned" in str(page) for page in orphaned)

    @pytest.mark.asyncio
    async def test_generates_summary(self, mock_kb):
        """Test that summary is generated."""
        result = await validate_kb_links(str(mock_kb))

        summary = result.get("summary", "")
        assert "Validated" in summary
        assert "valid links" in summary.lower() or "✅" in summary


class TestBuildSessionContext:
    """Test build_session_context workflow."""

    @pytest.mark.asyncio
    async def test_builds_session_context(self, mock_kb, mock_codebase):
        """Test basic session context building."""
        result = await build_session_context(
            topic="CachePrimitive",
            kb_path=str(mock_kb),
            code_path=str(mock_codebase),
        )

        assert "topic" in result
        assert result["topic"] == "CachePrimitive"
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_includes_related_kb_pages(self, mock_kb, mock_codebase):
        """Test that related KB pages are included."""
        result = await build_session_context(
            topic="CachePrimitive",
            kb_path=str(mock_kb),
            code_path=str(mock_codebase),
        )

        # Should include kb_pages in result
        assert "kb_pages" in result

    @pytest.mark.asyncio
    async def test_includes_related_code_files(self, mock_kb, mock_codebase):
        """Test that related code files are included."""
        result = await build_session_context(
            topic="CachePrimitive",
            kb_path=str(mock_kb),
            code_path=str(mock_codebase),
        )

        # Should include code_files in result
        assert "code_files" in result

    @pytest.mark.asyncio
    async def test_includes_related_todos(self, mock_kb, mock_codebase):
        """Test that related TODOs are included."""
        result = await build_session_context(
            topic="CachePrimitive",
            kb_path=str(mock_kb),
            code_path=str(mock_codebase),
        )

        # Should include todos in result
        assert "todos" in result


class TestBuildCrossReferences:
    """Test build_cross_references workflow."""

    @pytest.mark.asyncio
    async def test_builds_cross_references(self, mock_kb, mock_codebase):
        """Test basic cross-reference building."""
        result = await build_cross_references(
            kb_path=str(mock_kb),
            code_path=str(mock_codebase),
        )

        assert "kb_to_code" in result
        assert "code_to_kb" in result
        assert "stats" in result

    @pytest.mark.asyncio
    async def test_includes_suggestions(self, mock_kb, mock_codebase):
        """Test that suggestions are included."""
        result = await build_cross_references(
            kb_path=str(mock_kb),
            code_path=str(mock_codebase),
        )

        # Should include suggestions list
        assert "suggestions" in result


class TestDocumentFeature:
    """Test document_feature workflow."""

    @pytest.mark.asyncio
    async def test_documents_feature(self, mock_kb, mock_codebase):
        """Test basic feature documentation."""
        result = await document_feature(
            feature_name="CachePrimitive",
            code_path=str(mock_codebase),
            kb_path=str(mock_kb),
        )

        assert "page_path" in result
        assert "code_files_analyzed" in result

    @pytest.mark.asyncio
    async def test_creates_kb_page(self, mock_kb, mock_codebase):
        """Test that KB page is created."""
        result = await document_feature(
            feature_name="TestFeature",
            code_path=str(mock_codebase),
            kb_path=str(mock_kb),
        )

        # Should either create or update a page
        assert result.get("created_pages") or result.get("updated_pages") is not None

        # Page should exist
        page_path = Path(result["page_path"])
        assert page_path.exists()


class TestPreCommitValidation:
    """Test pre_commit_validation workflow."""

    @pytest.mark.asyncio
    async def test_runs_pre_commit_validation(self, mock_kb, mock_codebase):
        """Test basic pre-commit validation."""
        result = await pre_commit_validation(
            kb_path=str(mock_kb),
            code_path=str(mock_codebase),
        )

        assert "passed" in result
        assert "link_validation" in result
        assert "todo_check" in result
        assert "cross_ref_check" in result
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_returns_issues_list(self, mock_kb, mock_codebase):
        """Test that issues list is returned."""
        result = await pre_commit_validation(
            kb_path=str(mock_kb),
            code_path=str(mock_codebase),
        )

        assert "issues" in result
        assert isinstance(result["issues"], list)

    @pytest.mark.asyncio
    async def test_detects_kb_issues(self, mock_kb, mock_codebase):
        """Test that KB issues are detected."""
        result = await pre_commit_validation(
            kb_path=str(mock_kb),
            code_path=str(mock_codebase),
        )

        # Should detect broken links
        link_validation = result.get("link_validation", {})
        # Our mock KB has a broken link to MissingPage
        assert link_validation.get("broken_links", 0) >= 1


class TestIntegration:
    """Integration tests for workflows."""

    @pytest.mark.asyncio
    async def test_workflows_compose_correctly(self, mock_kb, mock_codebase):
        """Test that workflows compose without errors."""
        # Run validate_kb_links
        validation_result = await validate_kb_links(str(mock_kb))
        assert validation_result is not None

        # Run build_session_context
        session_result = await build_session_context(
            topic="cache",
            kb_path=str(mock_kb),
            code_path=str(mock_codebase),
        )
        assert session_result is not None

        # Run build_cross_references
        xref_result = await build_cross_references(
            kb_path=str(mock_kb),
            code_path=str(mock_codebase),
        )
        assert xref_result is not None

    @pytest.mark.asyncio
    async def test_workflows_handle_empty_kb(self, tmp_path):
        """Test workflows handle empty KB gracefully."""
        empty_kb = tmp_path / "empty_kb"
        (empty_kb / "pages").mkdir(parents=True)
        (empty_kb / "journals").mkdir(parents=True)

        empty_code = tmp_path / "empty_code"
        empty_code.mkdir(parents=True)

        # Should not raise errors on empty KB
        result = await validate_kb_links(str(empty_kb))
        assert result is not None

    @pytest.mark.asyncio
    async def test_workflows_return_consistent_types(self, mock_kb, mock_codebase):
        """Test that workflows return consistent types."""
        validation = await validate_kb_links(str(mock_kb))
        assert isinstance(validation, dict)

        session = await build_session_context(
            topic="test",
            kb_path=str(mock_kb),
            code_path=str(mock_codebase),
        )
        assert isinstance(session, dict)

        pre_commit = await pre_commit_validation(
            kb_path=str(mock_kb),
            code_path=str(mock_codebase),
        )
        assert isinstance(pre_commit, dict)
