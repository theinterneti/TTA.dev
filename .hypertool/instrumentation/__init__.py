"""
Hypertool Instrumentation Package

Observability components for Hypertool persona system:
- PersonaMetricsCollector: Prometheus metrics for persona operations
- WorkflowTracer: OpenTelemetry spans for multi-persona workflows
- LangfuseIntegration: LLM observability and prompt management
- ObservableLLM: Instrumented LLM wrapper
"""

from .langfuse_integration import (
    GenerationContext,
    LangfuseIntegration,
    SpanContext,
    TraceContext,
    get_langfuse_integration,
)
from .observable_llm import ObservableLLM, observe_llm
from .persona_metrics import PersonaMetricsCollector, reset_persona_metrics
from .workflow_tracing import WorkflowTracer

__all__ = [
    "PersonaMetricsCollector",
    "reset_persona_metrics",
    "WorkflowTracer",
    "LangfuseIntegration",
    "TraceContext",
    "SpanContext",
    "GenerationContext",
    "get_langfuse_integration",
    "ObservableLLM",
    "observe_llm",
]

__version__ = "1.0.0"
