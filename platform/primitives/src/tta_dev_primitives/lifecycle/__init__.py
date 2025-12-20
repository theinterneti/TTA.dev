"""Development Lifecycle Primitives for TTA.dev.

This module provides primitives for orchestrating the software development lifecycle,
making it accessible to non-technical users through AI-guided workflows.

Stages:
- Experimentation: Rapid prototyping and idea validation
- Testing: Automated testing and validation
- Staging: Pre-production validation
- Deployment: Production deployment
- Production: Live monitoring and maintenance

Each stage has:
- Entry criteria (what must be true to enter)
- Exit criteria (what must be true to proceed)
- Role-based agents (experts for that stage)
- Stage-specific primitives (tools for that stage)
- Validation rules (prevent mistakes)
"""

from tta_dev_primitives.lifecycle.stage import (
    DevelopmentStage,
    Stage,
    StageTransitionError,
)
from tta_dev_primitives.lifecycle.stage_criteria import (
    StageCriteria,
    StageReadiness,
    TransitionResult,
)
from tta_dev_primitives.lifecycle.stage_manager import StageManager, StageRequest
from tta_dev_primitives.lifecycle.stages import (
    DEPLOYMENT_TO_PRODUCTION,
    EXPERIMENTATION_TO_TESTING,
    STAGE_CRITERIA_MAP,
    STAGING_TO_DEPLOYMENT,
    TESTING_TO_STAGING,
)
from tta_dev_primitives.lifecycle.validation import (
    ReadinessCheckPrimitive,
    ReadinessCheckResult,
    Severity,
    ValidationCheck,
    ValidationPrimitive,
    ValidationResult,
)

__all__ = [
    # Stage enum and errors
    "Stage",
    "DevelopmentStage",  # Legacy alias
    "StageTransitionError",
    # Validation
    "Severity",
    "ValidationCheck",
    "ValidationResult",
    "ValidationPrimitive",
    "ReadinessCheckResult",
    "ReadinessCheckPrimitive",
    # Stage criteria and readiness
    "StageCriteria",
    "StageReadiness",
    "TransitionResult",
    # Stage manager
    "StageManager",
    "StageRequest",
    # Predefined stage criteria
    "EXPERIMENTATION_TO_TESTING",
    "TESTING_TO_STAGING",
    "STAGING_TO_DEPLOYMENT",
    "DEPLOYMENT_TO_PRODUCTION",
    "STAGE_CRITERIA_MAP",
]
