"""Orchestration primitives for multi-model workflows.

This module provides primitives for orchestrating multiple LLM models in a single
workflow, enabling cost optimization through intelligent task delegation.

Key primitives:
- DelegationPrimitive: Delegate tasks from orchestrator to executor models
- TaskClassifierPrimitive: Classify tasks to determine best model
- MultiModelWorkflow: Orchestrate multiple models in a workflow
"""

from primitives.orchestration.delegation_primitive import DelegationPrimitive
from primitives.orchestration.multi_model_workflow import MultiModelWorkflow
from primitives.orchestration.task_classifier_primitive import (
    TaskClassifierPrimitive,
)

__all__ = [
    "DelegationPrimitive",
    "TaskClassifierPrimitive",
    "MultiModelWorkflow",
]
