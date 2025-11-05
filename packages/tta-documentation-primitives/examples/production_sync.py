"""Example: Production-Ready Documentation Sync with TTA.dev Patterns.

This example demonstrates TTA.dev's composable workflow primitives, observability
integration, and recovery patterns for building reliable documentation systems.

Key TTA.dev Patterns Demonstrated:
1. InstrumentedPrimitive - Automatic OpenTelemetry tracing
2. WorkflowContext - Distributed tracing with correlation IDs
3. Composition operators (>>, |) - Sequential and parallel workflows
4. Recovery patterns - Retry, Fallback, Timeout
5. Performance patterns - Cache for cost reduction
6. Observability - Structured logging and metrics
"""

import asyncio
from pathlib import Path

from observability_integration import initialize_observability
from tta_dev_primitives import WorkflowContext

from tta_documentation_primitives import create_production_sync_workflow


async def main() -> None:
    """Production documentation sync with full observability."""

    # Initialize observability (OpenTelemetry + Prometheus)
    success = initialize_observability(
        service_name="tta-docs-sync",
        enable_prometheus=True,
    )

    if success:
        pass
    else:
        pass

    # Create production workflow with all safeguards:
    # 1. TimeoutPrimitive - Circuit breaker (30s)
    # 2. CachePrimitive - 40-60% cost reduction for AI calls
    # 3. RetryPrimitive - Exponential backoff for transient failures
    # 4. FallbackPrimitive - Gemini → Ollama graceful degradation
    workflow = create_production_sync_workflow()

    # Example files to process
    example_files = [
        Path("docs/guides/how-to-create-primitive.md"),
        Path("docs/guides/how-to-add-observability.md"),
        Path("GETTING_STARTED.md"),
    ]


    # Process each file with observability
    for file_path in example_files:
        if not file_path.exists():
            continue

        # Create WorkflowContext with correlation ID
        # This propagates through entire workflow for tracing
        context = WorkflowContext(
            trace_id=f"sync-{file_path.stem}",
            correlation_id=f"batch-{asyncio.current_task().get_name()}",
            data={"file": str(file_path)},
        )


        try:
            # Execute workflow (composition of primitives)
            # Flow: Markdown → Logseq Converter (timeout)
            #       → AI Metadata Extractor (cached + retry + fallback)
            #       → Logseq Sync (retry)
            await workflow.execute(file_path, context)


        except Exception:
            # Errors are automatically logged with trace context
            pass


    if success:
        pass


if __name__ == "__main__":

    asyncio.run(main())
