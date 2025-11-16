"""
Multi-package workflow test: Simple Data Pipeline with Observability.

Demonstrates:
- Parallel data processing
- Sequential workflow composition
- Observable primitives for monitoring
- Basic error handling
- Context propagation
"""

import asyncio

import pytest
from tta_dev_primitives import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.sequential import SequentialPrimitive
from tta_dev_primitives.observability.tracing import ObservablePrimitive

# ============================================================================
# Data Processing Primitives
# ============================================================================


class DataValidator(WorkflowPrimitive[dict, dict]):
    """Validate input data."""

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Validate data structure."""
        if "data" not in input_data:
            raise ValueError("Missing 'data' field")

        return {**input_data, "validated": True}


class DataEnricher(WorkflowPrimitive[dict, dict]):
    """Enrich data with additional fields."""

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add metadata."""
        await asyncio.sleep(0.01)  # Simulate processing
        return {
            **input_data,
            "enriched": True,
            "timestamp": context.start_time,
            "workflow_id": context.workflow_id,
        }


class DataTransformer(WorkflowPrimitive[dict, dict]):
    """Transform data format."""

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Transform data."""
        await asyncio.sleep(0.01)
        data = input_data.get("data", [])
        return {
            **input_data,
            "data": [str(item).upper() for item in data],
            "transformed": True,
        }


class DataAggregator(WorkflowPrimitive[list, dict]):
    """Aggregate results from multiple sources."""

    async def execute(self, input_data: list, context: WorkflowContext) -> dict:
        """Aggregate data."""
        return {
            "results": input_data,
            "count": len(input_data),
            "aggregated": True,
        }


# ============================================================================
# Tests: Sequential Pipeline
# ============================================================================


@pytest.mark.asyncio
async def test_sequential_data_pipeline():
    """Test simple sequential data pipeline."""
    # Build pipeline
    validator = DataValidator()
    enricher = DataEnricher()
    transformer = DataTransformer()

    pipeline = validator >> enricher >> transformer

    # Execute
    context = WorkflowContext(workflow_id="sequential-pipeline")
    input_data = {"data": ["hello", "world"]}

    result = await pipeline.execute(input_data, context)

    # Verify
    assert result["validated"] is True
    assert result["enriched"] is True
    assert result["transformed"] is True
    assert result["data"] == ["HELLO", "WORLD"]


@pytest.mark.asyncio
async def test_sequential_pipeline_with_observability():
    """Test sequential pipeline with observability."""
    # Build observable pipeline
    validator = ObservablePrimitive(DataValidator(), name="validator")
    enricher = ObservablePrimitive(DataEnricher(), name="enricher")
    transformer = ObservablePrimitive(DataTransformer(), name="transformer")

    pipeline = validator >> enricher >> transformer

    # Execute
    context = WorkflowContext(workflow_id="observable-pipeline", correlation_id="test-123")
    input_data = {"data": ["foo", "bar"]}

    result = await pipeline.execute(input_data, context)

    # Verify
    assert result["validated"] is True
    assert result["enriched"] is True
    assert result["transformed"] is True
    assert context.correlation_id == "test-123"


# ============================================================================
# Tests: Parallel Processing
# ============================================================================


@pytest.mark.asyncio
async def test_parallel_data_processing():
    """Test parallel data processing."""

    class Processor1(WorkflowPrimitive[dict, dict]):
        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            await asyncio.sleep(0.01)
            return {"processor": "1", "data": input_data.get("data", [])}

    class Processor2(WorkflowPrimitive[dict, dict]):
        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            await asyncio.sleep(0.01)
            return {"processor": "2", "data": input_data.get("data", [])}

    class Processor3(WorkflowPrimitive[dict, dict]):
        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            await asyncio.sleep(0.01)
            return {"processor": "3", "data": input_data.get("data", [])}

    # Build parallel workflow
    parallel = ParallelPrimitive([Processor1(), Processor2(), Processor3()])

    # Execute
    context = WorkflowContext(workflow_id="parallel-processing")
    input_data = {"data": ["test"]}

    results = await parallel.execute(input_data, context)

    # Verify all processors ran
    assert len(results) == 3
    processors = {r["processor"] for r in results}
    assert processors == {"1", "2", "3"}


@pytest.mark.asyncio
async def test_mixed_sequential_parallel():
    """Test mixed sequential and parallel workflow."""
    # Parallel processing
    p1 = DataEnricher()
    p2 = DataTransformer()
    parallel = ParallelPrimitive([p1, p2])

    # Sequential wrapper
    validator = DataValidator()
    workflow = validator >> parallel

    # Execute
    context = WorkflowContext(workflow_id="mixed-workflow")
    input_data = {"data": ["alpha", "beta"]}

    results = await workflow.execute(input_data, context)

    # Verify
    assert len(results) == 2
    # First result has enrichment
    assert any(r.get("enriched") for r in results)
    # Second result has transformation
    assert any(r.get("transformed") for r in results)


# ============================================================================
# Tests: Context Propagation
# ============================================================================


@pytest.mark.asyncio
async def test_context_propagation_through_workflow():
    """Test that context is properly propagated through workflow."""

    class ContextChecker(WorkflowPrimitive[dict, dict]):
        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            # Verify context has expected fields
            assert context.workflow_id is not None
            assert context.correlation_id is not None
            return {**input_data, "context_checked": True}

    # Build workflow
    checker1 = ContextChecker()
    checker2 = ContextChecker()
    workflow = checker1 >> checker2

    # Execute with custom context
    context = WorkflowContext(workflow_id="context-test", correlation_id="ctx-123")
    context.metadata["custom_field"] = "test_value"

    result = await workflow.execute({"data": "test"}, context)

    # Verify context propagation
    assert result["context_checked"] is True
    assert context.metadata["custom_field"] == "test_value"


@pytest.mark.asyncio
async def test_checkpoints_tracking():
    """Test that checkpoints are tracked through workflow."""
    validator = DataValidator()
    enricher = DataEnricher()
    transformer = DataTransformer()

    workflow = validator >> enricher >> transformer

    context = WorkflowContext(workflow_id="checkpoint-test")
    await workflow.execute({"data": ["test"]}, context)

    # Verify checkpoints were recorded
    assert len(context.checkpoints) > 0


# ============================================================================
# Tests: Error Handling
# ============================================================================


@pytest.mark.asyncio
async def test_error_propagation():
    """Test that errors propagate correctly through workflow."""

    class FailingPrimitive(WorkflowPrimitive[dict, dict]):
        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            raise RuntimeError("Processing failed")

    workflow = DataValidator() >> FailingPrimitive()

    context = WorkflowContext(workflow_id="error-test")

    with pytest.raises(RuntimeError, match="Processing failed"):
        await workflow.execute({"data": ["test"]}, context)


@pytest.mark.asyncio
async def test_validation_error():
    """Test validation errors are caught."""
    validator = DataValidator()
    context = WorkflowContext(workflow_id="validation-test")

    with pytest.raises(ValueError, match="Missing 'data' field"):
        await validator.execute({}, context)


# ============================================================================
# Tests: Performance
# ============================================================================


@pytest.mark.asyncio
async def test_parallel_performance_benefit():
    """Test that parallel execution is faster than sequential."""
    import time

    class SlowProcessor(WorkflowPrimitive[dict, dict]):
        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            await asyncio.sleep(0.05)  # 50ms processing
            return {"processed": True}

    # Sequential execution
    seq_workflow = SlowProcessor() >> SlowProcessor() >> SlowProcessor()
    context = WorkflowContext(workflow_id="seq-perf")

    start = time.time()
    await seq_workflow.execute({"data": "test"}, context)
    seq_duration = time.time() - start

    # Parallel execution
    par_workflow = ParallelPrimitive([SlowProcessor(), SlowProcessor(), SlowProcessor()])
    context = WorkflowContext(workflow_id="par-perf")

    start = time.time()
    await par_workflow.execute({"data": "test"}, context)
    par_duration = time.time() - start

    # Parallel should be significantly faster (at least 2x)
    assert par_duration < seq_duration * 0.6


@pytest.mark.asyncio
async def test_workflow_with_many_steps():
    """Test workflow with many sequential steps."""
    # Build long pipeline
    steps = [DataEnricher() for _ in range(10)]
    workflow = SequentialPrimitive(steps)

    context = WorkflowContext(workflow_id="long-pipeline")
    result = await workflow.execute({"data": ["test"]}, context)

    # Should complete successfully
    assert result["enriched"] is True


# ============================================================================
# Tests: Real-World Scenario
# ============================================================================


@pytest.mark.asyncio
async def test_complete_data_pipeline():
    """Test complete data processing pipeline with all features."""
    # Stage 1: Validation
    validator = ObservablePrimitive(DataValidator(), name="validator")

    # Stage 2: Parallel enrichment and transformation
    enricher = ObservablePrimitive(DataEnricher(), name="enricher")
    transformer = ObservablePrimitive(DataTransformer(), name="transformer")
    parallel_stage = ParallelPrimitive([enricher, transformer])

    # Stage 3: Aggregation (custom aggregator for parallel results)
    class ResultMerger(WorkflowPrimitive[list, dict]):
        async def execute(self, input_data: list, context: WorkflowContext) -> dict:
            # Merge results from parallel stage
            merged = {}
            for result in input_data:
                merged.update(result)
            return merged

    merger = ObservablePrimitive(ResultMerger(), name="merger")

    # Build complete pipeline
    pipeline = validator >> parallel_stage >> merger

    # Execute
    context = WorkflowContext(workflow_id="complete-pipeline", correlation_id="pipeline-123")
    input_data = {"data": ["alpha", "beta", "gamma"]}

    result = await pipeline.execute(input_data, context)

    # Verify all stages completed
    assert result["validated"] is True
    assert result["enriched"] is True
    assert result["transformed"] is True
    assert result["data"] == ["ALPHA", "BETA", "GAMMA"]
