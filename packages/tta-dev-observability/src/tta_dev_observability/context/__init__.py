"""Context propagation module initialization."""

from tta_dev_observability.context.propagation import (
    create_linked_span,
    extract_trace_context,
    inject_trace_context,
)

__all__ = [
    "inject_trace_context",
    "extract_trace_context",
    "create_linked_span",
]
