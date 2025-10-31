"""TTA Documentation Primitives - Automated docs-to-Logseq integration.

This package provides automated bidirectional synchronization between markdown
documentation and Logseq knowledge base, with AI-powered metadata generation,
built on TTA.dev's composable workflow primitives.

Key Features:
- InstrumentedPrimitive base classes with automatic observability
- Composable workflows using >> and | operators
- AI-powered metadata extraction with fallback patterns
- Recovery primitives (Retry, Fallback, Timeout)
- Performance primitives (Cache)
- WorkflowContext for distributed tracing
- Production-ready error handling

Quick Start:
    >>> from tta_documentation_primitives import create_production_sync_workflow
    >>> from tta_dev_primitives import WorkflowContext
    >>>
    >>> # Create production workflow with all safeguards
    >>> workflow = create_production_sync_workflow()
    >>>
    >>> # Execute with observability
    >>> context = WorkflowContext(trace_id="sync-123")
    >>> result = await workflow.execute(Path("docs/guide.md"), context)

Composable Example:
    >>> from tta_documentation_primitives import (
    ...     MarkdownConverterPrimitive,
    ...     AIMetadataExtractorPrimitive,
    ...     LogseqSyncPrimitive,
    ... )
    >>>
    >>> # Compose custom workflow
    >>> workflow = (
    ...     MarkdownConverterPrimitive(logseq_path=Path("logseq/pages")) >>
    ...     AIMetadataExtractorPrimitive(provider="gemini") >>
    ...     LogseqSyncPrimitive()
    ... )
"""

from .config import TTADocsConfig, load_config
from .primitives import (
    AIMetadataExtractorPrimitive,
    FileWatcherPrimitive,
    LogseqPage,
    LogseqSyncPrimitive,
    MarkdownConverterPrimitive,
    MarkdownDocument,
)
from .workflows import (
    create_ai_enhanced_sync_workflow,
    create_basic_sync_workflow,
    create_batch_sync_workflow,
    create_production_sync_workflow,
)

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Configuration
    "TTADocsConfig",
    "load_config",
    # Data models
    "LogseqPage",
    "MarkdownDocument",
    # Primitives
    "AIMetadataExtractorPrimitive",
    "FileWatcherPrimitive",
    "LogseqSyncPrimitive",
    "MarkdownConverterPrimitive",
    # Workflow factories
    "create_ai_enhanced_sync_workflow",
    "create_basic_sync_workflow",
    "create_batch_sync_workflow",
    "create_production_sync_workflow",
]
