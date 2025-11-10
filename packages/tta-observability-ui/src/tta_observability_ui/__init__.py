"""
TTA Observability UI

Lightweight, LangSmith-inspired observability for TTA.dev workflows.
Provides trace collection, storage, and visualization for development.
"""

from __future__ import annotations

__version__ = "0.1.0"

from .collector import TraceCollector
from .models import MetricRecord, Span, Trace
from .storage import TraceStorage

__all__ = [
    "MetricRecord",
    "Span",
    "Trace",
    "TraceCollector",
    "TraceStorage",
]
