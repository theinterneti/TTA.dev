"""
Langfuse Integration Package

Specialized LLM observability and analytics for TTA.dev applications.
Complements existing OpenTelemetry tracing with LLM-specific capabilities.

Key Features:
- LLM call tracing with prompts, completions, and costs
- Prompt version management and templates
- Custom evaluators for code, docs, tests, and responses
- Automated evaluation and scoring
- Playground datasets for testing
- Cost analytics per model/provider
- Integration with WorkflowContext

Quick Start:
    from langfuse_integration import initialize_langfuse
    from langfuse_integration.primitives import LangfusePrimitive
    from langfuse_integration.evaluators import get_evaluator

    # Initialize Langfuse
    initialize_langfuse(
        public_key="pk-lf-...",
        secret_key="sk-lf-...",
        host="https://cloud.langfuse.com"
    )

    # Wrap LLM primitive
    llm = LangfusePrimitive(
        name="narrative_gen",
        metadata={"model": "gpt-4", "type": "story"}
    )

    # Use evaluators
    code_eval = get_evaluator('code')
    result = code_eval.evaluate('def foo(): pass')

    # Use in workflow
    result = await llm.execute(context, input_data)
"""

from .evaluators import (
    BaseEvaluator,
    CodeQualityEvaluator,
    DocumentationEvaluator,
    ResponseQualityEvaluator,
    TestCoverageEvaluator,
    get_evaluator,
)
from .initialization import (
    get_langfuse_client,
    initialize_langfuse,
    is_langfuse_enabled,
    shutdown_langfuse,
)
from .primitives import LangfuseObservablePrimitive, LangfusePrimitive
from .prompt_management import PromptManager, create_prompt_from_instruction_file

__all__ = [
    # Initialization
    "initialize_langfuse",
    "shutdown_langfuse",
    "is_langfuse_enabled",
    "get_langfuse_client",
    # Primitives
    "LangfusePrimitive",
    "LangfuseObservablePrimitive",
    # Prompt Management
    "PromptManager",
    "create_prompt_from_instruction_file",
    # Evaluators
    "BaseEvaluator",
    "CodeQualityEvaluator",
    "DocumentationEvaluator",
    "TestCoverageEvaluator",
    "ResponseQualityEvaluator",
    "get_evaluator",
]

__version__ = "0.1.0"

