"""TTA.dev Observability - Production-grade observability for AI workflows."""

# Lazy imports — avoid pulling aiohttp and friends at module level.
# Access classes via ttadev.observability.TraceCollector etc.


def __getattr__(name: str):
    if name == "TraceCollector":
        from ttadev.observability.collector import TraceCollector

        return TraceCollector
    if name == "ObservabilityServer":
        from ttadev.observability.server import ObservabilityServer

        return ObservabilityServer
    if name == "Session":
        from ttadev.observability.session_manager import Session

        return Session
    if name == "SessionManager":
        from ttadev.observability.session_manager import SessionManager

        return SessionManager
    if name == "ProcessedSpan":
        from ttadev.observability.span_processor import ProcessedSpan

        return ProcessedSpan
    if name == "SpanProcessor":
        from ttadev.observability.span_processor import SpanProcessor

        return SpanProcessor
    raise AttributeError(f"module 'ttadev.observability' has no attribute {name!r}")


__all__ = [
    "TraceCollector",
    "ObservabilityServer",
    "Session",
    "SessionManager",
    "ProcessedSpan",
    "SpanProcessor",
]
