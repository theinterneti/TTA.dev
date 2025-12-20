"""Unit tests for LinkValidator tool.

Tests cover:
- Basic link validation workflow
- Broken link detection
- Orphaned page detection
- Cache behavior
- Error handling
"""

from pathlib import Path

import pytest

from tta_kb_automation.tools.link_validator import LinkValidator


@pytest.fixture
def mock_kb_structure(tmp_path: Path) -> Path:
    """Create a mock Logseq KB structure for testing."""
    kb_path = tmp_path / "logseq"
    pages_dir = kb_path / "pages"
    journals_dir = kb_path / "journals"

    pages_dir.mkdir(parents=True)
    journals_dir.mkdir(parents=True)

    # Create test pages
    (pages_dir / "Page A.md").write_text(
        "# Page A\n\n"
        "This links to [[Page B]] and [[Page C]].\n"
        "Also links to [[Nonexistent Page]].\n"
    )

    (pages_dir / "Page B.md").write_text("# Page B\n\nThis links back to [[Page A]].\n")

    (pages_dir / "Page C.md").write_text("# Page C\n\nThis is an orphan (no incoming links).\n")

    (pages_dir / "Orphan.md").write_text("# Orphan\n\nThis page has no incoming links.\n")

    # Create journal
    (journals_dir / "2025_11_03.md").write_text(
        "# November 3rd, 2025\n\nJournal entry linking to [[Page A]].\n"
    )

    return kb_path


@pytest.mark.asyncio
async def test_link_validator_basic_workflow(mock_kb_structure: Path) -> None:
    """Test basic link validation workflow."""
    validator = LinkValidator(kb_path=mock_kb_structure, use_cache=False)

    result = await validator.validate()

    # Check result structure
    assert "broken_links" in result
    assert "orphaned_pages" in result
    assert "valid_links" in result
    assert "total_pages" in result
    assert "summary" in result

    # Check totals
    assert result["total_pages"] == 5  # 4 pages + 1 journal


@pytest.mark.asyncio
async def test_link_validator_detects_broken_links(mock_kb_structure: Path) -> None:
    """Test broken link detection."""
    validator = LinkValidator(kb_path=mock_kb_structure, use_cache=False)

    result = await validator.validate()

    broken_links = result["broken_links"]

    # Should detect "Nonexistent Page"
    assert len(broken_links) >= 1

    broken_targets = [link["target"] for link in broken_links]
    assert "Nonexistent Page" in broken_targets


@pytest.mark.asyncio
async def test_link_validator_detects_orphaned_pages(mock_kb_structure: Path) -> None:
    """Test orphaned page detection."""
    validator = LinkValidator(kb_path=mock_kb_structure, use_cache=False)

    result = await validator.validate()

    orphaned_pages = result["orphaned_pages"]

    # Should detect "Orphan" page
    assert len(orphaned_pages) >= 1

    orphaned_titles = [page["title"] for page in orphaned_pages]
    assert "Orphan" in orphaned_titles


@pytest.mark.asyncio
async def test_link_validator_identifies_valid_links(mock_kb_structure: Path) -> None:
    """Test valid link identification."""
    validator = LinkValidator(kb_path=mock_kb_structure, use_cache=False)

    result = await validator.validate()

    valid_links = result["valid_links"]

    # Should have valid links (Page A -> Page B, Page A -> Page C, etc.)
    assert len(valid_links) >= 2

    # Check specific valid links
    valid_pairs = [(link["source"], link["target"]) for link in valid_links]
    assert ("Page A", "Page B") in valid_pairs
    assert ("Page A", "Page C") in valid_pairs


@pytest.mark.asyncio
async def test_link_validator_with_cache(mock_kb_structure: Path) -> None:
    """Test that caching works correctly."""
    validator = LinkValidator(kb_path=mock_kb_structure, use_cache=True)

    # First call
    result1 = await validator.validate()

    # Second call (should use cache)
    result2 = await validator.validate()

    # Results should be identical
    assert result1["total_pages"] == result2["total_pages"]
    assert len(result1["broken_links"]) == len(result2["broken_links"])


@pytest.mark.asyncio
async def test_link_validator_summary_generation(mock_kb_structure: Path) -> None:
    """Test summary generation."""
    validator = LinkValidator(kb_path=mock_kb_structure, use_cache=False)

    result = await validator.validate()

    summary = result["summary"]

    # Summary should contain key information
    assert "pages" in summary.lower()
    assert "links" in summary.lower()

    # Should indicate issues (broken links and orphans present)
    assert "⚠️" in summary or "❌" in summary


@pytest.mark.asyncio
async def test_link_validator_report_generation(mock_kb_structure: Path, tmp_path: Path) -> None:
    """Test report generation to file."""
    validator = LinkValidator(kb_path=mock_kb_structure, use_cache=False)

    report_path = tmp_path / "report.md"

    await validator.validate_and_report(output_path=report_path)

    # Check report was created
    assert report_path.exists()

    # Check report content
    report_content = report_path.read_text()
    assert "# KB Link Validation Report" in report_content
    assert "## Summary" in report_content
    assert "## ❌ Broken Links" in report_content or "orphaned" in report_content.lower()


@pytest.mark.asyncio
async def test_link_validator_empty_kb(tmp_path: Path) -> None:
    """Test validation with empty KB."""
    kb_path = tmp_path / "empty_logseq"
    kb_path.mkdir()
    (kb_path / "pages").mkdir()
    (kb_path / "journals").mkdir()

    validator = LinkValidator(kb_path=kb_path, use_cache=False)

    result = await validator.validate()

    # Should handle empty KB gracefully
    assert result["total_pages"] == 0
    assert len(result["broken_links"]) == 0
    assert len(result["orphaned_pages"]) == 0


@pytest.mark.asyncio
async def test_link_validator_handles_bidirectional_links(
    mock_kb_structure: Path,
) -> None:
    """Test handling of bidirectional links."""
    validator = LinkValidator(kb_path=mock_kb_structure, use_cache=False)

    result = await validator.validate()

    valid_links = result["valid_links"]

    # Should have bidirectional links between Page A and Page B
    links_dict = {(link["source"], link["target"]) for link in valid_links}

    # Check both directions exist
    has_a_to_b = ("Page A", "Page B") in links_dict
    has_b_to_a = ("Page B", "Page A") in links_dict

    assert has_a_to_b and has_b_to_a, "Bidirectional links not detected"
