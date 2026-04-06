"""AST-based code transformer for TTA.dev primitives.

Backward-compatible re-export of everything that was importable from
``ttadev.primitives.analysis.transformer`` when it was a single module.
"""

from ttadev.primitives.analysis.transformer.ast_detectors import (
    CachePatternDetector,
    CircuitBreakerDetector,
    CompensationDetector,
    FallbackDetector,
    GatherDetector,
    RetryLoopDetector,
    RouterPatternDetector,
    TimeoutDetector,
)
from ttadev.primitives.analysis.transformer.ast_detectors_advanced import (
    AdaptiveDetector,
    DelegationDetector,
    MemoryDetector,
    SequentialDetector,
)
from ttadev.primitives.analysis.transformer.ast_transformers import (
    FallbackTransformer,
    GatherTransformer,
    RetryLoopTransformer,
    TimeoutTransformer,
)
from ttadev.primitives.analysis.transformer.ast_transformers_advanced import (
    CacheTransformer,
    RouterTransformer,
)
from ttadev.primitives.analysis.transformer.ast_transformers_resilience import (
    CircuitBreakerTransformer,
    CompensationTransformer,
)
from ttadev.primitives.analysis.transformer.base import FunctionInfo, TransformResult
from ttadev.primitives.analysis.transformer.orchestrator import CodeTransformer, transform_code

__all__ = [
    # Data classes
    "TransformResult",
    "FunctionInfo",
    # AST Transformers
    "RetryLoopTransformer",
    "TimeoutTransformer",
    "FallbackTransformer",
    "GatherTransformer",
    "RouterTransformer",
    "CacheTransformer",
    "CircuitBreakerTransformer",
    "CompensationTransformer",
    # AST Detectors
    "RetryLoopDetector",
    "TimeoutDetector",
    "CachePatternDetector",
    "FallbackDetector",
    "GatherDetector",
    "RouterPatternDetector",
    "CircuitBreakerDetector",
    "CompensationDetector",
    "MemoryDetector",
    "DelegationDetector",
    "SequentialDetector",
    "AdaptiveDetector",
    # Orchestrator
    "CodeTransformer",
    "transform_code",
]
