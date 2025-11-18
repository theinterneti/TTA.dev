"""
Observability-enabled workflow primitives.

This package provides the missing agentic primitives identified in the
GitHub primitives analysis with full observability integration:

- RouterPrimitive: Route to optimal LLM provider (30% cost savings)
- CachePrimitive: Cache LLM responses (40% cost savings)
- TimeoutPrimitive: Enforce timeouts (prevent hanging workflows)

All primitives integrate with OpenTelemetry for comprehensive metrics tracking.
"""

from .cache import CachePrimitive
from .router import RouterPrimitive
from .timeout import TimeoutPrimitive

__all__ = [
    "RouterPrimitive",
    "CachePrimitive",
    "TimeoutPrimitive",
]
