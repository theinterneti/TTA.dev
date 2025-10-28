"""Observability features for workflow primitives."""

from .context_propagation import (
    create_linked_span,
    extract_baggage,
    extract_trace_context,
    inject_trace_context,
    propagate_baggage,
)
from .logging import setup_logging
from .metrics import PrimitiveMetrics, get_metrics_collector
from .tracing import ObservablePrimitive, setup_tracing

__all__ = [
    # Tracing
    "ObservablePrimitive",
    "setup_tracing",
    # Context propagation
    "inject_trace_context",
    "extract_trace_context",
    "create_linked_span",
    "propagate_baggage",
    "extract_baggage",
    # Metrics
    "PrimitiveMetrics",
    "get_metrics_collector",
    # Logging
    "setup_logging",
]
