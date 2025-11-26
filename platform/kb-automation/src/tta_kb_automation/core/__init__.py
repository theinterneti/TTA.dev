"""Core primitives for KB automation.

All primitives follow TTA.dev patterns:
- Extend InstrumentedPrimitive for observability
- Support composition with >> and | operators
- Include comprehensive type hints
- Have 100% test coverage
"""

from tta_kb_automation.core.code_primitives import (
    AnalyzeCodeStructure,
    ExtractTODOs,
    ParseDocstrings,
    ScanCodebase,
)
from tta_kb_automation.core.integration_primitives import (
    CreateJournalEntry,
    GenerateReport,
    UpdateKBPage,
)
from tta_kb_automation.core.intelligence_primitives import (
    ClassifyTODO,
    GenerateFlashcards,
    SuggestKBLinks,
)
from tta_kb_automation.core.kb_primitives import (
    ExtractLinks,
    FindOrphanedPages,
    ParseLogseqPages,
    ValidateLinks,
)

__all__ = [
    # KB operations
    "ParseLogseqPages",
    "ExtractLinks",
    "ValidateLinks",
    "FindOrphanedPages",
    # Code operations
    "ScanCodebase",
    "ParseDocstrings",
    "ExtractTODOs",
    "AnalyzeCodeStructure",
    # Intelligence
    "ClassifyTODO",
    "SuggestKBLinks",
    "GenerateFlashcards",
    # Integration
    "CreateJournalEntry",
    "UpdateKBPage",
    "GenerateReport",
]
