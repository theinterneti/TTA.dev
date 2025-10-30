"""Research primitives for automated data collection and documentation.

This module provides primitives for automating research workflows:
- Web scraping and data extraction
- Provider pricing research
- Documentation generation

All research primitives follow the WorkflowPrimitive interface for consistent
composition and observability.
"""

from tta_dev_primitives.research.free_tier_research import (
    FreeTierResearchPrimitive,
    FreeTierResearchRequest,
    FreeTierResearchResponse,
    ModelQualityMetrics,
    ProviderInfo,
)

__all__ = [
    "FreeTierResearchPrimitive",
    "FreeTierResearchRequest",
    "FreeTierResearchResponse",
    "ModelQualityMetrics",
    "ProviderInfo",
]
