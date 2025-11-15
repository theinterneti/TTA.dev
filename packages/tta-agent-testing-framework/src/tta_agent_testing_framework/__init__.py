"""
TTA Agent Testing Framework

Automated testing framework for AI agentic coders using VS Code + Playwright + TTA.dev primitives.
Tests agent handoffs, MCP server connectivity, workspace configurations, and performance benchmarking.
"""

from .core import (
    AgentExecutionMetrics,
    AgentHandoffState,
    AgentTestingFramework,
    ValidationResult,
    WorkspaceType,
)

__version__ = "0.1.0"

__all__ = [
    "AgentTestingFramework",
    "WorkspaceType",
    "AgentHandoffState",
    "AgentExecutionMetrics",
    "ValidationResult",
]
