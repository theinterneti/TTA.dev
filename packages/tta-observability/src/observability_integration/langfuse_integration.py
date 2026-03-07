"""LangFuse integration for LLM observability in TTA.dev workflows.

.. deprecated:: 2026-03-07
   This module is deprecated. Use ``tta_apm_langfuse`` instead.
   See docs/observability/LANGFUSE_CONSOLIDATION.md for migration guide.

This module provides LangFuse-based tracking for LLM calls, enabling:
- Cost and token tracking per workflow
- Latency and performance monitoring
- Prompt management and versioning
- Quality scoring and evaluation
"""

import os
import warnings
from typing import Any


class LangFuseIntegration:
    """Integrate TTA.dev primitives with LangFuse for LLM observability."""

    def __init__(
        self,
        public_key: str | None = None,
        secret_key: str | None = None,
        host: str | None = None,
    ):
        """Initialize LangFuse client.

        Args:
            public_key: LangFuse public key (or use LANGFUSE_PUBLIC_KEY env var)
            secret_key: LangFuse secret key (or use LANGFUSE_SECRET_KEY env var)
            host: LangFuse host URL (or use LANGFUSE_HOST env var)
        """
        warnings.warn(
            "LangFuseIntegration from observability_integration.langfuse_integration is deprecated. "
            "Use 'tta_apm_langfuse.LangFuseIntegration' instead. "
            "See docs/observability/LANGFUSE_CONSOLIDATION.md for migration guide.",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            from langfuse import Langfuse  # type: ignore[import-untyped]
        except ImportError as e:
            raise ImportError(
                "langfuse package is required but not installed. "
                "Install with: uv pip install langfuse"
            ) from e

        self.client = Langfuse(
            public_key=public_key or os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=secret_key or os.getenv("LANGFUSE_SECRET_KEY"),
            host=host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )

    async def trace_llm_call(
        self,
        workflow_id: str,
        primitive_name: str,
        model: str,
        prompt: str,
        response: str,
        tokens_used: int,
        cost_usd: float,
        latency_ms: float,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Trace an LLM call with full observability.

        Args:
            workflow_id: Unique workflow identifier
            primitive_name: Name of the primitive making the call
            model: LLM model used
            prompt: Input prompt
            response: LLM response
            tokens_used: Total tokens consumed
            cost_usd: Estimated cost in USD
            latency_ms: Call latency in milliseconds
            metadata: Additional metadata

        Returns:
            Trace metadata dictionary
        """
        trace_data = {
            "workflow_id": workflow_id,
            "primitive": primitive_name,
            "model": model,
            "prompt": prompt,
            "response": response,
            "tokens_used": tokens_used,
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
            **(metadata or {}),
        }
        return trace_data

    async def trace_workflow_stage(
        self,
        workflow_id: str,
        stage_name: str,
        primitive_name: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        quality_score: float | None = None,
    ) -> dict[str, Any]:
        """Trace a workflow stage execution.

        Args:
            workflow_id: Unique workflow identifier
            stage_name: Name of the workflow stage
            primitive_name: Name of the primitive
            input_data: Stage input
            output_data: Stage output
            quality_score: Optional quality score (0-1)

        Returns:
            Stage trace metadata
        """
        stage_data = {
            "workflow_id": workflow_id,
            "stage": stage_name,
            "primitive": primitive_name,
            "input": input_data,
            "output": output_data,
            "quality_score": quality_score,
        }
        return stage_data

    def create_dataset(
        self,
        name: str,
        description: str,
        items: list[dict[str, Any]],
    ) -> str:
        """Create a LangFuse dataset for evaluation.

        Args:
            name: Dataset name
            description: Dataset description
            items: List of dataset items with 'input' and 'expected_output'

        Returns:
            Dataset ID
        """
        dataset = self.client.create_dataset(name=name, description=description)

        for item in items:
            self.client.create_dataset_item(
                dataset_name=name,
                input=item["input"],
                expected_output=item["expected_output"],
                metadata=item.get("metadata", {}),
            )

        return dataset.id

    def flush(self) -> None:
        """Flush pending LangFuse events (call at shutdown)."""
        self.client.flush()


# Global singleton
_langfuse_integration: LangFuseIntegration | None = None


def get_langfuse() -> LangFuseIntegration:
    """Get global LangFuse integration instance."""
    warnings.warn(
        "get_langfuse() from observability_integration.langfuse_integration is deprecated. "
        "Use 'tta_apm_langfuse.LangFuseIntegration' instead. "
        "See docs/observability/LANGFUSE_CONSOLIDATION.md for migration guide.",
        DeprecationWarning,
        stacklevel=2,
    )
    global _langfuse_integration
    if _langfuse_integration is None:
        _langfuse_integration = LangFuseIntegration()
    return _langfuse_integration


def initialize_langfuse(
    public_key: str | None = None,
    secret_key: str | None = None,
    host: str | None = None,
) -> LangFuseIntegration:
    """Initialize global LangFuse integration.

    Args:
        public_key: LangFuse public key
        secret_key: LangFuse secret key
        host: LangFuse host URL

    Returns:
        Initialized LangFuse integration
    """
    warnings.warn(
        "initialize_langfuse() from observability_integration.langfuse_integration is deprecated. "
        "Use 'tta_apm_langfuse.LangFuseIntegration' instead. "
        "See docs/observability/LANGFUSE_CONSOLIDATION.md for migration guide.",
        DeprecationWarning,
        stacklevel=2,
    )
    global _langfuse_integration
    _langfuse_integration = LangFuseIntegration(
        public_key=public_key,
        secret_key=secret_key,
        host=host,
    )
    return _langfuse_integration
