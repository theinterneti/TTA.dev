"""ModelAdvisor package — data models and recommendation logic for model selection.

This package provides structured types used by the ModelAdvisor feature to
surface tier recommendations, ROI estimates, and fine-tuning suggestions to
callers of the TTA.dev primitive stack.
"""

from __future__ import annotations

from ttadev.primitives.llm.model_advisor.advisor import ModelAdvisor, advisor
from ttadev.primitives.llm.model_advisor.recommendation import (
    ROIEstimate,
    TaskSuggestion,
    TierRecommendation,
)

__all__ = [
    "ModelAdvisor",
    "ROIEstimate",
    "TaskSuggestion",
    "TierRecommendation",
    "advisor",
]
