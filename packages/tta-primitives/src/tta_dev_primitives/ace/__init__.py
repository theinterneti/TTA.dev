"""ACE (Agentic Context Engine) Integration Module.

This module provides self-learning primitives that combine Agentic Context Engine
patterns with TTA.dev's primitive system and E2B execution environments.

Key Features:
- Self-improving code generation through execution feedback
- Strategy playbooks that learn from real results
- Integration with E2B for secure code execution
- Observable learning metrics and improvement tracking

Classes:
    SelfLearningCodePrimitive: Code generation that learns from execution results
    MockACEPlaybook: Strategy storage and learning system
    ACEInput: Input type for ACE-enabled primitives
    ACEOutput: Output type with learning metrics

Example:
    ```python
    from tta_dev_primitives.ace import SelfLearningCodePrimitive
    from tta_dev_primitives import WorkflowContext

    # Create a self-learning code primitive
    learner = SelfLearningCodePrimitive()

    # Execute and learn
    context = WorkflowContext(correlation_id="ace-demo")
    result = await learner.execute({
        "task": "Create a fibonacci function",
        "language": "python"
    }, context)

    print(f"Generated code: {result['code_generated']}")
    print(f"Strategies learned: {result['strategies_learned']}")
    print(f"Success rate: {learner.success_rate:.1%}")
    ```
"""

from .benchmarks import BenchmarkResult, BenchmarkSuite, BenchmarkTask, DifficultyLevel
from .cognitive_manager import (
    ACEInput,
    ACEOutput,
    MockACEPlaybook,
    SelfLearningCodePrimitive,
)
from .metrics import AggregatedMetrics, LearningMetrics, MetricsTracker

__all__ = [
    "SelfLearningCodePrimitive",
    "MockACEPlaybook",
    "ACEInput",
    "ACEOutput",
    "MetricsTracker",
    "LearningMetrics",
    "AggregatedMetrics",
    "BenchmarkSuite",
    "BenchmarkTask",
    "BenchmarkResult",
    "DifficultyLevel",
]

__version__ = "0.1.0"
