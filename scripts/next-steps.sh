#!/bin/bash

# TTA.dev Next Steps & Validation Script
#
# This script outlines the next steps for completing the observability implementation
# and provides commands to validate the progress.

set -e

# --- Phase 1: Foundation (In Progress) ---

echo "Verifying Phase 1: Foundation..."

# 1.1 Enhanced WorkflowContext
# Verify that player_id is removed and trace context fields are present.

if grep -q "player_id: str | None = None" packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py; then
    echo "[FAIL] player_id found in WorkflowContext. It should be removed."
    exit 1
fi

if ! grep -q "trace_id: str | None = Field" packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py; then
    echo "[FAIL] trace_id not found in WorkflowContext."
    exit 1
fi

echo "[PASS] WorkflowContext enhanced."

# --- Phase 2: Core Primitive Instrumentation (Next) ---

echo "\nNext Steps: Phase 2 - Core Primitive Instrumentation"

# 2.1 InstrumentedSequentialPrimitive
# TODO: Refactor SequentialPrimitive to use the new InstrumentedPrimitive base class.

cat <<EOF

File: packages/tta-dev-primitives/src/tta_dev_primitives/core/sequential.py

- Inherit from InstrumentedPrimitive.
- Implement the _execute_impl method.
- Ensure step-level spans are created.

Example:

from ..observability.instrumentation import InstrumentedPrimitive

class SequentialPrimitive(InstrumentedPrimitive[Any, Any]):
    # ...
    async def _execute_impl(self, input_data: Any, context: WorkflowContext) -> Any:
        result = input_data
        for i, primitive in enumerate(self.primitives):
            step_name = f"step_{i}_{primitive.__class__.__name__}"
            with self._tracer.start_as_current_span(step_name) as span:
                # ... set attributes
                result = await primitive.execute(result, context)
        return result

EOF

# --- Code Snippets for Reference ---

# It seems this file contains snippets of the old code for reference.
# I will update them to reflect the new design.

# Old WorkflowContext:
# class WorkflowContext(BaseModel):
#     workflow_id: str | None = None
#     session_id: str | None = None
#     player_id: str | None = None # <-- REMOVED
#     metadata: dict[str, Any] = Field(default_factory=dict)
#     state: dict[str, Any] = Field(default_factory=dict)

# New WorkflowContext:
# class WorkflowContext(BaseModel):
#     workflow_id: str | None = None
#     session_id: str | None = None
#     metadata: dict[str, Any] = Field(default_factory=dict)
#     state: dict[str, Any] = Field(default_factory=dict)
#     # ... plus new observability fields

# Old create_child_context:
# def create_child_context(self) -> WorkflowContext:
#     return WorkflowContext(
#         workflow_id=self.workflow_id,
#         session_id=self.session_id,
#         player_id=self.player_id, # <-- REMOVED
#         metadata=copy.deepcopy(self.metadata),
#         # ...
#     )

# New create_child_context:
# def create_child_context(self) -> WorkflowContext:
#     return WorkflowContext(
#         workflow_id=self.workflow_id,
#         session_id=self.session_id,
#         metadata=copy.deepcopy(self.metadata),
#         # ...
#     )

# Old to_otel_context:
# def to_otel_context(self) -> dict[str, Any]:
#     return {
#         "workflow.id": self.workflow_id or "unknown",
#         "workflow.session_id": self.session_id or "unknown",
#         "workflow.player_id": self.player_id or "unknown", # <-- REMOVED
#         "workflow.correlation_id": self.correlation_id,
#         "workflow.elapsed_ms": self.elapsed_ms(),
#     }

# New to_otel_context:
# def to_otel_context(self) -> dict[str, Any]:
#     return {
#         "workflow.id": self.workflow_id or "unknown",
#         "workflow.session_id": self.session_id or "unknown",
#         "workflow.correlation_id": self.correlation_id,
#         "workflow.elapsed_ms": self.elapsed_ms(),
#     }

echo "\nScript finished. Please proceed with Phase 2 implementation."