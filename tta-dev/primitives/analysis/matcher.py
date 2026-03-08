"""Primitive matching for TTA.dev code analysis.

Matches detected patterns to appropriate TTA.dev primitives
with confidence scoring.
"""

from typing import Any

from tta_dev_primitives.analysis.models import (
    CodeAnalysisResult,
    RecommendationContext,
)


class PrimitiveMatcher:
    """Matches code requirements to appropriate TTA.dev primitives.

    Uses a catalog of primitives with their:
    - Required patterns/requirements
    - Confidence factors
    - Use cases
    - Related primitives

    Example:
        matcher = PrimitiveMatcher()
        matches = matcher.find_matches(analysis_result)
        # Returns: [("RetryPrimitive", 0.87), ("CachePrimitive", 0.72), ...]
    """

    def __init__(self) -> None:
        """Initialize with the primitive catalog."""
        self.primitive_catalog: dict[str, dict[str, Any]] = {
            "RetryPrimitive": {
                "description": "Automatic retry with exponential backoff",
                "import_path": "from tta_dev_primitives.recovery import RetryPrimitive",
                "requirements": ["retry_logic", "error_recovery", "api_resilience"],
                "patterns": ["retry_patterns", "error_handling", "api_calls"],
                "use_cases": [
                    "Unstable API calls",
                    "Network issues",
                    "Rate limiting",
                    "Temporary failures",
                ],
                "confidence_factors": {
                    "retry_logic": 0.9,
                    "error_recovery": 0.8,
                    "api_resilience": 0.7,
                    "error_handling": 0.5,
                },
                "related_primitives": [
                    "TimeoutPrimitive",
                    "FallbackPrimitive",
                    "CircuitBreakerPrimitive",
                ],
            },
            "TimeoutPrimitive": {
                "description": "Timeout protection for operations",
                "import_path": "from tta_dev_primitives.recovery import TimeoutPrimitive",
                "requirements": ["timeout_handling", "api_resilience"],
                "patterns": ["timeout_patterns", "async_operations", "api_calls"],
                "use_cases": [
                    "API calls that may hang",
                    "Database queries with time limits",
                    "Webhook processing",
                    "Long-running operations",
                ],
                "confidence_factors": {
                    "timeout_handling": 0.9,
                    "api_resilience": 0.7,
                    "async_operations": 0.5,
                },
                "related_primitives": ["RetryPrimitive", "FallbackPrimitive"],
            },
            "CachePrimitive": {
                "description": "LRU cache with TTL for expensive operations",
                "import_path": "from tta_dev_primitives.performance import CachePrimitive",
                "requirements": ["performance_optimization"],
                "patterns": ["caching_patterns", "api_calls", "llm_patterns"],
                "use_cases": [
                    "Expensive API calls",
                    "LLM response caching",
                    "Data lookup optimization",
                    "Repeated computations",
                ],
                "confidence_factors": {
                    "performance_optimization": 0.85,
                    "caching_patterns": 0.7,
                    "llm_patterns": 0.8,
                    "api_calls": 0.5,
                },
                "related_primitives": ["MemoryPrimitive"],
            },
            "FallbackPrimitive": {
                "description": "Graceful degradation with fallback cascade",
                "import_path": "from tta_dev_primitives.recovery import FallbackPrimitive",
                "requirements": ["fallback_strategy", "error_recovery"],
                "patterns": ["fallback_patterns", "error_handling", "llm_patterns"],
                "use_cases": [
                    "Multi-provider failover",
                    "Service degradation",
                    "Graceful degradation",
                    "Backup strategies",
                ],
                "confidence_factors": {
                    "fallback_strategy": 0.9,
                    "error_recovery": 0.7,
                    "llm_patterns": 0.6,
                },
                "related_primitives": ["RetryPrimitive", "CircuitBreakerPrimitive"],
            },
            "ParallelPrimitive": {
                "description": "Execute primitives concurrently",
                "import_path": "from tta_dev_primitives import ParallelPrimitive",
                "requirements": ["concurrent_execution", "performance_optimization"],
                "patterns": ["parallel_patterns", "async_operations"],
                "use_cases": [
                    "Multiple API calls",
                    "Data processing pipelines",
                    "Concurrent LLM calls",
                    "Batch processing",
                ],
                "confidence_factors": {
                    "concurrent_execution": 0.9,
                    "performance_optimization": 0.7,
                    "async_operations": 0.5,
                },
                "related_primitives": ["SequentialPrimitive"],
            },
            "SequentialPrimitive": {
                "description": "Execute primitives in sequence",
                "import_path": "from tta_dev_primitives import SequentialPrimitive",
                "requirements": ["asynchronous_processing"],
                "patterns": ["async_operations"],
                "use_cases": [
                    "Step-by-step workflows",
                    "Data processing pipelines",
                    "Multi-stage operations",
                    "Chained operations",
                ],
                "confidence_factors": {
                    "asynchronous_processing": 0.7,
                },
                "related_primitives": ["ParallelPrimitive"],
            },
            "RouterPrimitive": {
                "description": "Dynamic routing to multiple destinations",
                "import_path": "from tta_dev_primitives.core import RouterPrimitive",
                "requirements": ["intelligent_routing"],
                "patterns": ["routing_patterns", "llm_patterns"],
                "use_cases": [
                    "Multi-provider selection",
                    "Cost optimization",
                    "Performance-based routing",
                    "Model selection",
                ],
                "confidence_factors": {
                    "intelligent_routing": 0.95,
                    "llm_patterns": 0.6,
                },
                "related_primitives": ["FallbackPrimitive"],
            },
            "CircuitBreakerPrimitive": {
                "description": "Circuit breaker pattern to prevent cascade failures",
                "import_path": "from tta_dev_primitives.recovery import CircuitBreakerPrimitive",
                "requirements": ["error_recovery", "api_resilience"],
                "patterns": ["error_handling", "api_calls"],
                "use_cases": [
                    "Unreliable external services",
                    "Preventing cascade failures",
                    "Service health monitoring",
                    "Graceful service degradation",
                ],
                "confidence_factors": {
                    "error_recovery": 0.8,
                    "api_resilience": 0.85,
                },
                "related_primitives": [
                    "RetryPrimitive",
                    "FallbackPrimitive",
                    "TimeoutPrimitive",
                ],
            },
            "MemoryPrimitive": {
                "description": "Conversational memory with zero-setup fallback",
                "import_path": "from tta_dev_primitives.performance import MemoryPrimitive",
                "requirements": ["llm_reliability", "performance_optimization"],
                "patterns": ["llm_patterns"],
                "use_cases": [
                    "Multi-turn conversations",
                    "Agent memory",
                    "Context management",
                    "Personalization",
                ],
                "confidence_factors": {
                    "llm_reliability": 0.9,
                    "llm_patterns": 0.8,
                },
                "related_primitives": ["CachePrimitive"],
            },
            "ConditionalPrimitive": {
                "description": "Branch execution based on runtime conditions",
                "import_path": "from tta_dev_primitives import ConditionalPrimitive",
                "requirements": ["intelligent_routing"],
                "patterns": ["routing_patterns", "validation_patterns"],
                "use_cases": [
                    "Conditional branching",
                    "A/B testing",
                    "Feature flags",
                    "Dynamic workflows",
                ],
                "confidence_factors": {
                    "intelligent_routing": 0.8,
                    "routing_patterns": 0.7,
                    "validation_patterns": 0.5,
                },
                "related_primitives": ["RouterPrimitive", "SequentialPrimitive"],
            },
            "CompensationPrimitive": {
                "description": "Saga pattern for distributed transactions with rollback",
                "import_path": "from tta_dev_primitives.recovery import CompensationPrimitive",
                "requirements": ["error_recovery", "transaction_management"],
                "patterns": ["error_handling", "workflow_patterns"],
                "use_cases": [
                    "Distributed transactions",
                    "Saga pattern",
                    "Rollback operations",
                    "Multi-step operations with undo",
                ],
                "confidence_factors": {
                    "error_recovery": 0.85,
                    "transaction_management": 0.95,
                    "workflow_patterns": 0.6,
                },
                "related_primitives": ["RetryPrimitive", "FallbackPrimitive"],
            },
            "DelegationPrimitive": {
                "description": "Orchestrator to Executor pattern for multi-agent workflows",
                "import_path": "from tta_dev_primitives.orchestration import DelegationPrimitive",
                "requirements": ["multi_agent", "intelligent_routing"],
                "patterns": ["llm_patterns", "workflow_patterns", "routing_patterns"],
                "use_cases": [
                    "Multi-agent coordination",
                    "Task delegation",
                    "Orchestrator pattern",
                    "Complex LLM workflows",
                ],
                "confidence_factors": {
                    "multi_agent": 0.95,
                    "intelligent_routing": 0.7,
                    "llm_patterns": 0.6,
                },
                "related_primitives": ["TaskClassifierPrimitive", "MultiModelWorkflow"],
            },
            "MultiModelWorkflow": {
                "description": "Intelligent multi-model coordination",
                "import_path": "from tta_dev_primitives.orchestration import MultiModelWorkflow",
                "requirements": ["multi_agent", "llm_reliability"],
                "patterns": ["llm_patterns", "routing_patterns"],
                "use_cases": [
                    "Multi-model orchestration",
                    "Model ensemble",
                    "Cross-model validation",
                    "Cost-optimized routing",
                ],
                "confidence_factors": {
                    "multi_agent": 0.9,
                    "llm_reliability": 0.85,
                    "llm_patterns": 0.7,
                },
                "related_primitives": ["DelegationPrimitive", "RouterPrimitive"],
            },
            "TaskClassifierPrimitive": {
                "description": "Classify tasks and route to appropriate handler",
                "import_path": "from tta_dev_primitives.orchestration import TaskClassifierPrimitive",
                "requirements": ["intelligent_routing"],
                "patterns": ["routing_patterns", "llm_patterns", "validation_patterns"],
                "use_cases": [
                    "Intent classification",
                    "Task routing",
                    "Request triage",
                    "Dynamic handler selection",
                ],
                "confidence_factors": {
                    "intelligent_routing": 0.9,
                    "routing_patterns": 0.75,
                    "validation_patterns": 0.5,
                },
                "related_primitives": ["RouterPrimitive", "DelegationPrimitive"],
            },
            "MockPrimitive": {
                "description": "Mock primitive for testing workflows",
                "import_path": "from tta_dev_primitives.testing import MockPrimitive",
                "requirements": ["testing_support"],
                "patterns": ["testing_patterns"],
                "use_cases": [
                    "Unit testing",
                    "Integration testing",
                    "Mock LLM responses",
                    "Test fixtures",
                ],
                "confidence_factors": {
                    "testing_support": 0.95,
                    "testing_patterns": 0.9,
                },
                "related_primitives": [],
            },
            "InstrumentedPrimitive": {
                "description": "Base class with automatic observability",
                "import_path": "from tta_dev_primitives.observability import InstrumentedPrimitive",
                "requirements": ["observability"],
                "patterns": ["logging_patterns"],
                "use_cases": [
                    "OpenTelemetry integration",
                    "Metrics collection",
                    "Distributed tracing",
                    "Performance monitoring",
                ],
                "confidence_factors": {
                    "observability": 0.95,
                    "logging_patterns": 0.6,
                },
                "related_primitives": [],
            },
            "AdaptivePrimitive": {
                "description": "Base class for self-improving primitives that learn from execution",
                "import_path": "from tta_dev_primitives.adaptive import AdaptivePrimitive",
                "requirements": ["self_improvement", "llm_reliability"],
                "patterns": ["llm_patterns", "workflow_patterns"],
                "use_cases": [
                    "Self-tuning workflows",
                    "Adaptive retry strategies",
                    "Learning from failures",
                    "Strategy optimization",
                ],
                "confidence_factors": {
                    "self_improvement": 0.95,
                    "llm_reliability": 0.7,
                },
                "related_primitives": ["AdaptiveRetryPrimitive"],
            },
            "AdaptiveRetryPrimitive": {
                "description": "Retry primitive that learns optimal parameters from execution",
                "import_path": "from tta_dev_primitives.adaptive import AdaptiveRetryPrimitive",
                "requirements": ["retry_logic", "self_improvement"],
                "patterns": ["retry_patterns", "error_handling", "api_calls"],
                "use_cases": [
                    "Self-tuning retries",
                    "Adaptive backoff",
                    "Learning optimal retry parameters",
                    "Context-aware retry strategies",
                ],
                "confidence_factors": {
                    "retry_logic": 0.85,
                    "self_improvement": 0.9,
                    "api_calls": 0.6,
                },
                "related_primitives": ["RetryPrimitive", "AdaptivePrimitive"],
            },
            "GitCollaborationPrimitive": {
                "description": "Enforce best practices for multi-agent Git collaboration",
                "import_path": "from tta_dev_primitives.collaboration import GitCollaborationPrimitive",
                "requirements": ["multi_agent"],
                "patterns": ["workflow_patterns"],
                "use_cases": [
                    "Multi-agent Git workflows",
                    "Conventional commits",
                    "Integration frequency enforcement",
                    "Branch health monitoring",
                ],
                "confidence_factors": {
                    "multi_agent": 0.9,
                    "workflow_patterns": 0.5,
                },
                "related_primitives": ["DelegationPrimitive"],
            },
        }

    def find_matches(
        self,
        analysis: CodeAnalysisResult,
        context: RecommendationContext | None = None,
        min_confidence: float = 0.3,
    ) -> list[tuple[str, float]]:
        """Find matching primitives with confidence scores.

        Args:
            analysis: Result from PatternDetector.analyze()
            context: Optional context for improved matching
            min_confidence: Minimum confidence threshold (0.0 to 1.0)

        Returns:
            List of (primitive_name, confidence_score) tuples, sorted by confidence
        """
        matches = []

        for primitive_name, info in self.primitive_catalog.items():
            score = self._calculate_score(primitive_name, info, analysis, context)

            if score >= min_confidence:
                matches.append((primitive_name, score))

        # Sort by confidence score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def _calculate_score(
        self,
        primitive_name: str,
        info: dict[str, Any],
        analysis: CodeAnalysisResult,
        context: RecommendationContext | None,
    ) -> float:
        """Calculate confidence score for a primitive."""
        score = 0.0
        confidence_factors = info.get("confidence_factors", {})

        # Score based on requirements match
        for requirement in analysis.inferred_requirements:
            if requirement in confidence_factors:
                score += confidence_factors[requirement]

        # Bonus for pattern matches
        for pattern in analysis.detected_patterns:
            if pattern in info.get("patterns", []):
                score += 0.1

        # Context bonuses
        if analysis.performance_critical:
            if "performance_optimization" in info.get("requirements", []):
                score += 0.15

        if analysis.error_handling_needed:
            if "error_recovery" in info.get("requirements", []):
                score += 0.15

        if analysis.concurrency_needed:
            if "concurrent_execution" in info.get("requirements", []):
                score += 0.2

        # Complexity-based adjustments
        if analysis.complexity_level == "high":
            # High complexity code benefits more from orchestration primitives
            if primitive_name in [
                "SequentialPrimitive",
                "ParallelPrimitive",
                "RouterPrimitive",
            ]:
                score += 0.1

        # Normalize score to 0.0-1.0 range
        max_possible = sum(confidence_factors.values()) + 0.5 if confidence_factors else 1.0
        normalized_score = min(score / max_possible, 1.0) if max_possible > 0 else 0.0

        return round(normalized_score, 3)

    def get_primitive_info(self, primitive_name: str) -> dict[str, Any] | None:
        """Get detailed information about a specific primitive.

        Args:
            primitive_name: Name of the primitive

        Returns:
            Primitive info dict or None if not found
        """
        return self.primitive_catalog.get(primitive_name)

    def list_primitives(self) -> list[dict[str, Any]]:
        """List all available primitives with basic info.

        Returns:
            List of primitive info dicts
        """
        return [
            {
                "name": name,
                "description": info["description"],
                "import_path": info["import_path"],
                "use_cases": info["use_cases"],
            }
            for name, info in self.primitive_catalog.items()
        ]

    def get_related_primitives(self, primitive_name: str) -> list[str]:
        """Get primitives that work well with the given primitive."""
        info = self.primitive_catalog.get(primitive_name)
        if info:
            return info.get("related_primitives", [])
        return []
