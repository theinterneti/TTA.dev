"""Tests for TTA Documentation Primitives.

Demonstrates TTA.dev testing patterns using MockPrimitive.
"""

from pathlib import Path

import pytest
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

from tta_documentation_primitives.primitives import (
    FileWatcherPrimitive,
    LogseqPage,
    MarkdownConverterPrimitive,
)


@pytest.mark.asyncio
async def test_file_watcher_primitive():
    """Test FileWatcherPrimitive returns file paths."""
    primitive = FileWatcherPrimitive(paths=["docs/"], debounce_ms=500)
    context = WorkflowContext(trace_id="test-watcher")

    config = {"watch_paths": ["docs/"], "debounce_seconds": 1.0}
    result = await primitive.execute(config, context)

    assert isinstance(result, list)
    # Placeholder implementation returns empty list
    assert result == []


@pytest.mark.asyncio
async def test_markdown_converter_primitive():
    """Test MarkdownConverterPrimitive converts markdown to Logseq."""
    primitive = MarkdownConverterPrimitive(
        logseq_path=Path("logseq/pages"),
        preserve_code_blocks=True,
        convert_links=True,
    )
    context = WorkflowContext(trace_id="test-converter")

    # Test with actual file path
    file_path = Path(__file__).parent.parent / "README.md"
    result = await primitive.execute(file_path, context)

    assert isinstance(result, LogseqPage)
    assert result.title is not None
    assert result.content is not None


@pytest.mark.asyncio
async def test_workflow_composition_with_mocks():
    """Test workflow composition using MockPrimitive."""
    # Create mocks
    mock_converter = MockPrimitive(
        name="mock_converter",
        return_value=LogseqPage(
            title="Test Page",
            content="Test content",
            page_path=Path("test.md"),
            properties={"type": "guide"},
            frontmatter={},
        ),
    )

    mock_syncer = MockPrimitive(
        name="mock_syncer",
        return_value=Path("logseq/pages/test.md"),
    )

    # Compose workflow with >> operator
    workflow = mock_converter >> mock_syncer

    # Execute
    context = WorkflowContext(trace_id="test-composition")
    result = await workflow.execute(Path("test.md"), context)

    # Verify
    assert result == Path("logseq/pages/test.md")
    assert mock_converter.call_count == 1
    assert mock_syncer.call_count == 1


@pytest.mark.asyncio
async def test_parallel_workflow_with_mocks():
    """Test parallel execution using | operator."""
    # Create mocks for parallel operations
    mock1 = MockPrimitive(name="mock1", return_value="result1")
    mock2 = MockPrimitive(name="mock2", return_value="result2")
    mock3 = MockPrimitive(name="mock3", return_value="result3")

    # Compose with | operator
    workflow = mock1 | mock2 | mock3

    # Execute
    context = WorkflowContext(trace_id="test-parallel")
    results = await workflow.execute("input", context)

    # Verify all executed concurrently
    assert results == ["result1", "result2", "result3"]
    assert mock1.call_count == 1
    assert mock2.call_count == 1
    assert mock3.call_count == 1


@pytest.mark.asyncio
async def test_context_propagation():
    """Test WorkflowContext propagates through workflow."""
    mock_primitive = MockPrimitive(name="test_primitive", return_value="success")

    # Create context with metadata
    context = WorkflowContext(trace_id="test-ctx-prop", correlation_id="batch-123")

    # Execute
    result = await mock_primitive.execute("input", context)

    # Verify context was passed
    assert result == "success"
    assert mock_primitive.call_count == 1
    # MockPrimitive received context in execute call
    assert len(mock_primitive.calls) == 1
    call_data = mock_primitive.calls[0]
    assert call_data[0] == "input"  # First arg is input_data
