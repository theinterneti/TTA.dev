"""TTA KB Automation - Automated knowledge base maintenance for TTA.dev.

This package provides primitives and tools for:
- Link validation (detect broken [[Page]] links)
- TODO synchronization (code comments → journal entries)
- Cross-reference building (code ↔ KB relationships)
- Session context generation (synthetic context for agents)

All automation uses TTA.dev primitives for composability and observability.
"""

from tta_kb_automation.core import (
    AnalyzeCodeStructure,
    # Intelligence
    ClassifyTODO,
    # Integration
    CreateJournalEntry,
    ExtractLinks,
    ExtractTODOs,
    FindOrphanedPages,
    GenerateFlashcards,
    GenerateReport,
    ParseDocstrings,
    # Core primitives
    ParseLogseqPages,
    # Code operations
    ScanCodebase,
    SuggestKBLinks,
    UpdateKBPage,
    ValidateLinks,
)
from tta_kb_automation.tools import (
    CrossReferenceBuilder,
    # High-level tools
    LinkValidator,
    SessionContextBuilder,
    TODOSync,
)
from tta_kb_automation.workflows import (
    build_cross_references,
    build_session_context,
    document_feature,
    pre_commit_validation,
    sync_code_todos,
    # Complete workflows
    validate_kb_links,
)

__version__ = "0.1.0"

__all__ = [
    # Core primitives
    "ParseLogseqPages",
    "ExtractLinks",
    "ValidateLinks",
    "FindOrphanedPages",
    "ScanCodebase",
    "ParseDocstrings",
    "ExtractTODOs",
    "AnalyzeCodeStructure",
    "ClassifyTODO",
    "SuggestKBLinks",
    "GenerateFlashcards",
    "CreateJournalEntry",
    "UpdateKBPage",
    "GenerateReport",
    # Tools
    "LinkValidator",
    "TODOSync",
    "CrossReferenceBuilder",
    "SessionContextBuilder",
    # Workflows
    "validate_kb_links",
    "sync_code_todos",
    "build_cross_references",
    "build_session_context",
    "document_feature",
    "pre_commit_validation",
]
