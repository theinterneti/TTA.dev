"""
Observability Integration Package

Comprehensive observability and monitoring integration for TTA platform.
Connects existing monitoring infrastructure (Prometheus, Grafana, OpenTelemetry)
with agent orchestration, workflow primitives, and component lifecycle.

Key Features:
- OpenTelemetry APM integration
- Missing agentic primitives (Router, Cache, Timeout)
- Component maturity metrics
- Circuit breaker observability
- LLM usage and cost tracking
- Grafana dashboard suite

Quick Start:
    from observability_integration import initialize_observability

    # Initialize APM (call this early in main.py)
    initialize_observability(
        service_name="tta",
        enable_prometheus=True,
        prometheus_port=9464
    )

    # Use new primitives with observability
    from observability_integration.primitives import (
        RouterPrimitive,
        CachePrimitive,
        TimeoutPrimitive
    )

    workflow = (
        RouterPrimitive(routes={"fast": llama, "premium": gpt4})
        >> CachePrimitive(narrative_gen, ttl_seconds=3600)
        >> TimeoutPrimitive(timeout_seconds=30)
    )

See specs/observability-integration.md for full specification.
"""

from .apm_setup import initialize_observability, is_observability_enabled

__all__ = [
    "initialize_observability",
    "is_observability_enabled",
]

__version__ = "0.1.0"
