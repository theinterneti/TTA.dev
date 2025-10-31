"""Tests for TTA Documentation Workflows.

Tests demonstrate workflow composition patterns and recovery primitives.
"""

from pathlib import Path

import pytest
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.testing import MockPrimitive

from tta_documentation_primitives import (
    create_ai_enhanced_sync_workflow,
    create_basic_sync_workflow,
    create_batch_sync_workflow,
    create_production_sync_workflow,
)


@pytest.mark.asyncio
async def test_basic_workflow():
    """Test basic workflow composition."""
    workflow = create_basic_sync_workflow()
    context = WorkflowContext(trace_id="test-basic")

    # Test with README (exists in repo)
    readme_path = Path(__file__).parent.parent / "README.md"
    if readme_path.exists():
        result = await workflow.execute(readme_path, context)
        assert isinstance(result, Path)


@pytest.mark.asyncio
async def test_ai_enhanced_workflow():
    """Test workflow with retry and fallback patterns."""
    workflow = create_ai_enhanced_sync_workflow()
    context = WorkflowContext(trace_id="test-ai-enhanced")

    # Will use fallback if Gemini unavailable
    readme_path = Path(__file__).parent.parent / "README.md"
    if readme_path.exists():
        result = await workflow.execute(readme_path, context)
        assert isinstance(result, Path)


@pytest.mark.asyncio
async def test_production_workflow():
    """Test production workflow with full safeguards."""
    workflow = create_production_sync_workflow()
    context = WorkflowContext(trace_id="test-production")

    # Has timeout, cache, retry, fallback
    readme_path = Path(__file__).parent.parent / "README.md"
    if readme_path.exists():
        result = await workflow.execute(readme_path, context)
        assert isinstance(result, Path)


@pytest.mark.asyncio
async def test_batch_workflow():
    """Test batch processing with parallel execution."""
    # Note: ParallelPrimitive sends same input to all branches
    # For true batch processing, we'd need a different pattern
    # This test verifies the parallel workflow structure
    workflow = create_batch_sync_workflow(max_parallel=2)
    context = WorkflowContext(trace_id="test-batch")

    # Test with single file (ParallelPrimitive will send to both branches)
    test_file = Path(__file__).parent.parent / "README.md"

    if test_file.exists():
        results = await workflow.execute(test_file, context)
        assert isinstance(results, list)
        # Both branches process same file, so we get 2 results
        assert len(results) == 2


@pytest.mark.asyncio
async def test_workflow_composition_with_recovery():
    """Test recovery patterns in workflows."""
    # Mock that fails once then succeeds
    call_count = 0

    from tta_dev_primitives.recovery import RetryPrimitive, RetryStrategy

    class FlakeyMock(MockPrimitive):
        def __init__(self) -> None:
            super().__init__(name="flakey_mock")

        async def execute(self, input_data: str, context: WorkflowContext) -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Simulated failure")
            return "success"

    # Wrap with retry
    workflow = RetryPrimitive(
        primitive=FlakeyMock(),
        strategy=RetryStrategy(max_retries=3, backoff_base=1.5),
    )

    context = WorkflowContext(trace_id="test-retry")
    result = await workflow.execute("input", context)

    # Should succeed on second attempt
    assert result == "success"
    assert call_count == 2  # Failed once, succeeded on retry
