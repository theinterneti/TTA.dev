"""Speckit primitives for specification-driven development.

This package provides primitives that enable systematic, reproducible
specification workflows:

- SpecifyPrimitive: Transform requirements into formal specifications
- ClarifyPrimitive: Iterative refinement through structured questioning
- PlanPrimitive: Generate implementation plans and data models
- TasksPrimitive: Break plans into ordered, dependent tasks
- ValidationGatePrimitive: Enforce human approval gates

Usage:
    from ttadev.primitives.speckit import (
        SpecifyPrimitive,
        ClarifyPrimitive,
        PlanPrimitive,
        TasksPrimitive,
        ValidationGatePrimitive,
    )

    # Complete spec-driven workflow
    workflow = (
        SpecifyPrimitive() >>
        ClarifyPrimitive(max_iterations=3) >>
        PlanPrimitive() >>
        TasksPrimitive() >>
        ValidationGatePrimitive(require_approval=True)
    )

    result = await workflow.execute(
        {"requirement": "Add caching to LLM pipeline"},
        context=WorkflowContext(workflow_id="feature-123")
    )
"""

from ttadev.primitives.speckit.clarify_primitive import ClarifyPrimitive
from ttadev.primitives.speckit.plan_primitive import PlanPrimitive
from ttadev.primitives.speckit.specify_primitive import SpecifyPrimitive
from ttadev.primitives.speckit.tasks_primitive import Task, TasksPrimitive
from ttadev.primitives.speckit.validation_gate_primitive import (
    ValidationGatePrimitive,
)

__all__ = [
    "SpecifyPrimitive",
    "ClarifyPrimitive",
    "ValidationGatePrimitive",
    "PlanPrimitive",
    "TasksPrimitive",
    "Task",
]

__version__ = "0.1.0"
