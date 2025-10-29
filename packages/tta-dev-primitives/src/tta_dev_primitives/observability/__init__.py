"""Observability features for workflow primitives."""

from .context_propagation import (
    create_linked_span,
    extract_baggage,
    extract_trace_context,
    inject_trace_context,
    propagate_baggage,
)
from .enhanced_collector import get_enhanced_metrics_collector
from .enhanced_metrics import (
    CostMetrics,
    PercentileMetrics,
    SLOConfig,
    SLOMetrics,
    ThroughputMetrics,
)

# Prometheus exporter (optional dependency)
try:
    from .prometheus_exporter import PrometheusExporter, get_prometheus_exporter

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
from .instrumented_primitive import InstrumentedPrimitive
from .logging import setup_logging
from .metrics import PrimitiveMetrics, get_metrics_collector
from .tracing import ObservablePrimitive, setup_tracing

__all__ = [
    # Instrumented primitives
    "InstrumentedPrimitive",
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
    # Enhanced metrics (Phase 3)
    "get_enhanced_metrics_collector",
    "PercentileMetrics",
    "SLOConfig",
    "SLOMetrics",
    "ThroughputMetrics",
    "CostMetrics",
    # Prometheus exporter (Phase 3 - optional)
    "PrometheusExporter",
    "get_prometheus_exporter",
    "PROMETHEUS_AVAILABLE",
    # Logging
    "setup_logging",
]
