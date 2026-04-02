"""Extensions namespace — non-core, specialised primitive modules.

This package re-exports TTA's extension modules so agents can discover
all available capabilities from a single entry point, while keeping the
original import paths intact for backward compatibility.

Core primitives (WorkflowPrimitive, Sequential, Parallel, Router, Conditional,
Recovery, Performance, Testing) are exported directly from ``ttadev.primitives``.

Extension modules live here for structured discovery:

.. code-block:: python

    # Discover all extensions
    from ttadev.primitives.extensions import EXTENSION_MODULES

    # Import a specific extension (original path still works)
    from ttadev.primitives.adaptive import AdaptiveRetryPrimitive

    # Or via the extensions namespace
    from ttadev.primitives.extensions import adaptive

Extension Categories:
    **Agent Code Execution (ace)**
        LLM-powered code generation with sandbox execution.

    **Adaptive Primitives (adaptive)**
        Self-improving retry, cache, timeout, and fallback that learn
        from execution patterns.

    **Code Analysis (analysis)**
        AST-based pattern detection and transformation.

    **APM (apm)**
        Application Performance Monitoring decorators.

    **Benchmarking (benchmarking)**
        Performance benchmarking utilities.

    **Knowledge (knowledge)**
        Logseq knowledge base querying.

    **Lifecycle (lifecycle)**
        Stage management and validation gates.

    **Orchestration (orchestration)**
        Multi-model LLM orchestration and task routing.

    **Research (research)**
        Provider research and free-tier model discovery.

    **SpecKit (speckit)**
        Specification-driven development workflow primitives.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "EXTENSION_MODULES",
    "list_extensions",
]

# Lazy imports — only resolve when accessed to avoid heavy startup costs.
# Each entry maps a short alias to the full module path.
EXTENSION_MODULES: dict[str, str] = {
    "ace": "ttadev.primitives.ace",
    "adaptive": "ttadev.primitives.adaptive",
    "analysis": "ttadev.primitives.analysis",
    "apm": "ttadev.primitives.apm",
    "benchmarking": "ttadev.primitives.benchmarking",
    "knowledge": "ttadev.primitives.knowledge",
    "lifecycle": "ttadev.primitives.lifecycle",
    "orchestration": "ttadev.primitives.orchestration",
    "research": "ttadev.primitives.research",
    "speckit": "ttadev.primitives.speckit",
}


def __getattr__(name: str) -> Any:
    """Lazy-load extension modules on attribute access.

    Enables ``from ttadev.primitives.extensions import adaptive``
    without importing all extensions at startup.
    """
    if name in EXTENSION_MODULES:
        import importlib

        return importlib.import_module(EXTENSION_MODULES[name])  # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import  # fmt: skip
    raise AttributeError(f"module 'ttadev.primitives.extensions' has no attribute {name!r}")


def list_extensions() -> list[str]:
    """Return sorted list of available extension module names.

    Returns:
        List of extension names (e.g. ['ace', 'adaptive', 'analysis', ...]).
    """
    return sorted(EXTENSION_MODULES.keys())
