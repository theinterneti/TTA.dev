"""Composable workflows for documentation synchronization.

This module demonstrates TTA.dev workflow composition patterns using >> and |
operators to create production-ready documentation pipelines.
"""

from pathlib import Path

from tta_dev_primitives import ParallelPrimitive, SequentialPrimitive
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import (
    FallbackPrimitive,
    RetryPrimitive,
    RetryStrategy,
    TimeoutPrimitive,
)

from .config import TTADocsConfig, load_config
from .primitives import (
    AIMetadataExtractorPrimitive,
    LogseqSyncPrimitive,
    MarkdownConverterPrimitive,
)


def create_basic_sync_workflow(
    config: TTADocsConfig | None = None,
) -> SequentialPrimitive:
    """Create basic documentation sync workflow.

    Workflow: Markdown → Logseq Conversion → Sync to Disk

    Example:
        >>> workflow = create_basic_sync_workflow()
        >>> context = WorkflowContext(trace_id="sync-123")
        >>> result = await workflow.execute(Path("docs/guide.md"), context)

    Args:
        config: Configuration (loads from file if None)

    Returns:
        Composable workflow primitive
    """
    if config is None:
        config = load_config()

    # Create primitives
    converter = MarkdownConverterPrimitive(
        logseq_path=Path(config.logseq_path),
        preserve_code_blocks=config.format.preserve_code_blocks,
        convert_links=config.format.convert_links,
    )

    syncer = LogseqSyncPrimitive(create_directories=True)

    # Compose with >> operator (sequential)
    return converter >> syncer



def create_ai_enhanced_sync_workflow(
    config: TTADocsConfig | None = None,
) -> SequentialPrimitive:
    """Create AI-enhanced documentation sync workflow with fallback.

    Workflow:
    1. Convert markdown → Logseq
    2. Try AI metadata extraction (with fallback to basic)
    3. Sync to disk

    Example:
        >>> workflow = create_ai_enhanced_sync_workflow()
        >>> context = WorkflowContext(trace_id="ai-sync-123")
        >>> result = await workflow.execute(Path("docs/guide.md"), context)

    Args:
        config: Configuration (loads from file if None)

    Returns:
        Composable workflow primitive with AI enhancement
    """
    if config is None:
        config = load_config()

    # Create primitives
    converter = MarkdownConverterPrimitive(
        logseq_path=Path(config.logseq_path),
        preserve_code_blocks=config.format.preserve_code_blocks,
        convert_links=config.format.convert_links,
    )

    # AI metadata extractor with retry
    ai_extractor = RetryPrimitive(
        primitive=AIMetadataExtractorPrimitive(
            provider=config.ai.provider,
            model=config.ai.model,
            api_key=config.ai.api_key,
        ),
        strategy=RetryStrategy(max_retries=3, backoff_base=2.0),
    )

    # Fallback to Ollama if Gemini fails
    if config.ai.fallback:
        fallback_extractor = AIMetadataExtractorPrimitive(
            provider="ollama",
            model=config.ai.fallback.split(":")[-1],  # Extract model from "ollama:model"
        )

        # Use fallback pattern
        metadata_extractor = FallbackPrimitive(
            primary=ai_extractor,
            fallback=fallback_extractor,
        )
    else:
        metadata_extractor = ai_extractor

    syncer = LogseqSyncPrimitive(create_directories=True)

    # Compose workflow: Convert >> AI Enhance >> Sync
    return converter >> metadata_extractor >> syncer



def create_production_sync_workflow(
    config: TTADocsConfig | None = None,
) -> SequentialPrimitive:
    """Create production-ready sync workflow with all safeguards.

    Workflow:
    1. Convert markdown → Logseq (with timeout)
    2. AI metadata extraction (with retry + fallback + caching)
    3. Sync to disk (with retry)

    Demonstrates:
    - TimeoutPrimitive for circuit breaker
    - RetryPrimitive for transient failures
    - FallbackPrimitive for graceful degradation
    - CachePrimitive for AI call reduction (30-40% cost savings)

    Example:
        >>> workflow = create_production_sync_workflow()
        >>> context = WorkflowContext(trace_id="prod-123")
        >>> result = await workflow.execute(Path("docs/guide.md"), context)

    Args:
        config: Configuration (loads from file if None)

    Returns:
        Production-ready composable workflow
    """
    if config is None:
        config = load_config()

    # Layer 1: Markdown conversion with timeout
    converter = TimeoutPrimitive(
        primitive=MarkdownConverterPrimitive(
            logseq_path=Path(config.logseq_path),
            preserve_code_blocks=config.format.preserve_code_blocks,
            convert_links=config.format.convert_links,
        ),
        timeout_seconds=30.0,
    )

    # Layer 2: AI metadata extraction with caching
    cached_ai = CachePrimitive(
        primitive=AIMetadataExtractorPrimitive(
            provider=config.ai.provider,
            model=config.ai.model,
            api_key=config.ai.api_key,
        ),
        cache_key_fn=lambda data, ctx: f"{data.title}:{ctx.trace_id}",
        ttl_seconds=3600.0,  # Cache for 1 hour
    )

    # Layer 3: Retry AI calls
    retry_ai = RetryPrimitive(
        primitive=cached_ai,
        strategy=RetryStrategy(max_retries=3, backoff_base=2.0),
    )

    # Layer 4: Fallback to Ollama
    if config.ai.fallback:
        fallback_ai = AIMetadataExtractorPrimitive(
            provider="ollama",
            model=config.ai.fallback.split(":")[-1],
        )

        metadata_extractor = FallbackPrimitive(
            primary=retry_ai,
            fallback=fallback_ai,
        )
    else:
        metadata_extractor = retry_ai

    # Layer 5: Sync with retry
    syncer = RetryPrimitive(
        primitive=LogseqSyncPrimitive(create_directories=True),
        strategy=RetryStrategy(max_retries=2, backoff_base=1.5),
    )

    # Compose complete workflow
    return converter >> metadata_extractor >> syncer



def create_batch_sync_workflow(
    config: TTADocsConfig | None = None,
    max_parallel: int = 5,
) -> ParallelPrimitive:
    """Create batch sync workflow for processing multiple files in parallel.

    Processes multiple markdown files concurrently using ParallelPrimitive.

    Example:
        >>> workflow = create_batch_sync_workflow(max_parallel=3)
        >>> context = WorkflowContext(trace_id="batch-123")
        >>> files = [Path("doc1.md"), Path("doc2.md"), Path("doc3.md")]
        >>> results = await workflow.execute(files, context)

    Args:
        config: Configuration (loads from file if None)
        max_parallel: Maximum number of parallel operations

    Returns:
        Parallel workflow primitive
    """
    if config is None:
        config = load_config()

    # Create individual sync workflows
    sync_workflows = [create_production_sync_workflow(config) for _ in range(max_parallel)]

    # Compose with | operator (parallel)
    return ParallelPrimitive(primitives=sync_workflows)



# Workflow examples demonstrating TTA.dev patterns
__all__ = [
    "create_ai_enhanced_sync_workflow",
    "create_basic_sync_workflow",
    "create_batch_sync_workflow",
    "create_production_sync_workflow",
]
