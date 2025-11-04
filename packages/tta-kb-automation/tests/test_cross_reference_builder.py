"""Unit tests for CrossReferenceBuilder tool.

Tests cover:
- Basic cross-reference building
- KB→Code reference extraction
- Code→KB reference extraction
- Missing reference detection
- Report generation
"""

from pathlib import Path

import pytest

from tta_kb_automation.tools.cross_reference_builder import CrossReferenceBuilder


@pytest.fixture
def mock_cross_ref_structure(tmp_path: Path) -> tuple[Path, Path]:
    """Create mock KB and codebase for cross-reference testing."""
    # Create KB structure
    kb_path = tmp_path / "logseq"
    pages_dir = kb_path / "pages"
    pages_dir.mkdir(parents=True)

    # KB page with code references
    (pages_dir / "Architecture.md").write_text(
        "# Architecture\n\n"
        "The main implementation is in `packages/tta-dev-primitives/src/core/base.py`.\n"
        "See also: [RetryPrimitive](packages/tta-dev-primitives/src/recovery/retry.py)\n"
    )

    # KB page with no code references
    (pages_dir / "Concepts.md").write_text("# Concepts\n\nGeneral concepts here.\n")

    # Create code structure
    code_path = tmp_path / "packages"
    pkg_dir = code_path / "tta-dev-primitives" / "src" / "core"
    pkg_dir.mkdir(parents=True)

    # Code file with KB references
    (pkg_dir / "base.py").write_text(
        '"""Base primitive class.\n\n'
        "See: Architecture.md for design decisions.\n"
        "KB: TTA.dev/Primitives\n"
        '"""\n\n'
        "class WorkflowPrimitive:\n"
        "    pass\n"
    )

    # Code file with wiki-style KB references
    (pkg_dir / "sequential.py").write_text(
        '"""Sequential primitive.\n\n'
        "Implements the pattern described in [[Sequential Pattern]].\n"
        '"""\n\n'
        "class SequentialPrimitive:\n"
        "    pass\n"
    )

    # Code file with no KB references
    (pkg_dir / "utils.py").write_text(
        '"""Utility functions."""\n\ndef helper():\n    pass\n'
    )

    return kb_path, code_path


@pytest.mark.asyncio
async def test_cross_reference_builder_basic_workflow(
    mock_cross_ref_structure: tuple[Path, Path],
) -> None:
    """Test basic cross-reference building workflow."""
    kb_path, code_path = mock_cross_ref_structure

    builder = CrossReferenceBuilder(
        kb_path=kb_path, code_path=code_path, use_cache=False, exclude_patterns=[]
    )

    result = await builder.build()

    # Check result structure
    assert "kb_to_code" in result
    assert "code_to_kb" in result
    assert "missing_references" in result
    assert "stats" in result
    assert "report" in result


@pytest.mark.asyncio
async def test_cross_reference_builder_finds_kb_to_code(
    mock_cross_ref_structure: tuple[Path, Path],
) -> None:
    """Test extraction of KB→Code references."""
    kb_path, code_path = mock_cross_ref_structure

    builder = CrossReferenceBuilder(
        kb_path=kb_path, code_path=code_path, use_cache=False, exclude_patterns=[]
    )

    result = await builder.build()
    kb_to_code = result["kb_to_code"]

    # Should find code references in Architecture.md
    assert "Architecture" in kb_to_code
    refs = kb_to_code["Architecture"]

    # Should have found the two code file references
    assert len(refs) >= 1
    assert any("base.py" in ref for ref in refs)


@pytest.mark.asyncio
async def test_cross_reference_builder_finds_code_to_kb(
    mock_cross_ref_structure: tuple[Path, Path],
) -> None:
    """Test extraction of Code→KB references."""
    kb_path, code_path = mock_cross_ref_structure

    builder = CrossReferenceBuilder(
        kb_path=kb_path, code_path=code_path, use_cache=False, exclude_patterns=[]
    )

    result = await builder.build()
    code_to_kb = result["code_to_kb"]

    # Should find KB references in code files
    assert len(code_to_kb) > 0

    # Check that base.py has KB references
    base_py_files = [f for f in code_to_kb.keys() if "base.py" in f]
    assert len(base_py_files) > 0

    # Check references
    base_refs = code_to_kb[base_py_files[0]]
    assert any("Architecture" in ref for ref in base_refs)


@pytest.mark.asyncio
async def test_cross_reference_builder_finds_wiki_links(
    mock_cross_ref_structure: tuple[Path, Path],
) -> None:
    """Test detection of [[Wiki Link]] style references."""
    kb_path, code_path = mock_cross_ref_structure

    builder = CrossReferenceBuilder(
        kb_path=kb_path, code_path=code_path, use_cache=False, exclude_patterns=[]
    )

    result = await builder.build()
    code_to_kb = result["code_to_kb"]

    # Should find [[Sequential Pattern]] reference in sequential.py
    sequential_files = [f for f in code_to_kb.keys() if "sequential.py" in f]
    assert len(sequential_files) > 0

    refs = code_to_kb[sequential_files[0]]
    assert any("Sequential Pattern" in ref for ref in refs)


@pytest.mark.asyncio
async def test_cross_reference_builder_detects_missing_refs(
    mock_cross_ref_structure: tuple[Path, Path],
) -> None:
    """Test detection of missing references."""
    kb_path, code_path = mock_cross_ref_structure

    builder = CrossReferenceBuilder(
        kb_path=kb_path, code_path=code_path, use_cache=False, exclude_patterns=[]
    )

    result = await builder.build()
    missing = result["missing_references"]

    # Should detect some missing references
    # (either code files mentioned in KB that don't exist,
    #  or KB pages mentioned in code that don't exist)
    assert len(missing) > 0

    # Check structure of missing references
    if missing:
        ref = missing[0]
        assert "type" in ref
        assert "reference" in ref
        assert "suggestion" in ref


@pytest.mark.asyncio
async def test_cross_reference_builder_generates_stats(
    mock_cross_ref_structure: tuple[Path, Path],
) -> None:
    """Test statistics generation."""
    kb_path, code_path = mock_cross_ref_structure

    builder = CrossReferenceBuilder(
        kb_path=kb_path, code_path=code_path, use_cache=False, exclude_patterns=[]
    )

    result = await builder.build()
    stats = result["stats"]

    # Check all expected stats are present
    assert "total_kb_pages" in stats
    assert "total_code_files" in stats
    assert "kb_pages_with_code_refs" in stats
    assert "code_files_with_kb_refs" in stats
    assert "total_missing_refs" in stats

    # Verify reasonable values
    assert stats["total_kb_pages"] == 2  # Architecture.md, Concepts.md
    assert stats["total_code_files"] == 3  # base.py, sequential.py, utils.py
    assert stats["kb_pages_with_code_refs"] >= 1  # Architecture.md has refs


@pytest.mark.asyncio
async def test_cross_reference_builder_generates_report(
    mock_cross_ref_structure: tuple[Path, Path],
) -> None:
    """Test markdown report generation."""
    kb_path, code_path = mock_cross_ref_structure

    builder = CrossReferenceBuilder(
        kb_path=kb_path, code_path=code_path, use_cache=False, exclude_patterns=[]
    )

    result = await builder.build()
    report = result["report"]

    assert report
    assert "# Cross-Reference Analysis Report" in report
    assert "## Summary" in report
    assert "## Recommendations" in report


@pytest.mark.asyncio
async def test_cross_reference_builder_with_cache(
    mock_cross_ref_structure: tuple[Path, Path],
) -> None:
    """Test that caching works correctly."""
    kb_path, code_path = mock_cross_ref_structure

    builder = CrossReferenceBuilder(
        kb_path=kb_path, code_path=code_path, use_cache=True, exclude_patterns=[]
    )

    # First run
    result1 = await builder.build()

    # Second run (should use cache)
    result2 = await builder.build()

    # Results should be identical
    assert result1["stats"] == result2["stats"]
    assert len(result1["kb_to_code"]) == len(result2["kb_to_code"])
    assert len(result1["code_to_kb"]) == len(result2["code_to_kb"])


@pytest.mark.asyncio
async def test_cross_reference_builder_handles_empty_kb(tmp_path: Path) -> None:
    """Test handling of empty KB."""
    kb_path = tmp_path / "logseq"
    kb_path.mkdir()
    (kb_path / "pages").mkdir()

    code_path = tmp_path / "packages"
    code_path.mkdir()

    builder = CrossReferenceBuilder(
        kb_path=kb_path, code_path=code_path, use_cache=False, exclude_patterns=[]
    )

    result = await builder.build()

    # Should complete without errors
    assert result["stats"]["total_kb_pages"] == 0
    assert result["stats"]["total_code_files"] == 0


@pytest.mark.asyncio
async def test_cross_reference_builder_handles_empty_codebase(tmp_path: Path) -> None:
    """Test handling of empty codebase."""
    kb_path = tmp_path / "logseq"
    pages_dir = kb_path / "pages"
    pages_dir.mkdir(parents=True)

    (pages_dir / "Test.md").write_text("# Test\n\nSome content.\n")

    code_path = tmp_path / "packages"
    code_path.mkdir()

    builder = CrossReferenceBuilder(
        kb_path=kb_path, code_path=code_path, use_cache=False, exclude_patterns=[]
    )

    result = await builder.build()

    # Should complete without errors
    assert result["stats"]["total_kb_pages"] == 1
    assert result["stats"]["total_code_files"] == 0
    assert len(result["code_to_kb"]) == 0
