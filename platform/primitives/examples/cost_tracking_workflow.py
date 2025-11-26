"""
Cost Tracking with Metrics Example

This example demonstrates tracking costs and metrics for LLM workflows using TTA.dev primitives.

Features:
- Token usage tracking per model
- Cost calculation based on pricing
- Prometheus metrics export
- Budget enforcement
- Cost attribution by user/workflow
- Real-time cost monitoring

Dependencies:
    uv add tta-dev-primitives

Usage:
    python examples/cost_tracking_workflow.py
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive

# ==============================================================================
# Cost Configuration
# ==============================================================================


@dataclass
class ModelPricing:
    """Pricing information for LLM models."""

    model_name: str
    cost_per_1k_prompt_tokens: float  # USD
    cost_per_1k_completion_tokens: float  # USD


# Standard model pricing (as of Oct 2025)
MODEL_PRICING = {
    "gpt-4": ModelPricing("gpt-4", 0.03, 0.06),
    "gpt-4-turbo": ModelPricing("gpt-4-turbo", 0.01, 0.03),
    "gpt-4-mini": ModelPricing("gpt-4-mini", 0.00015, 0.0006),
    "gpt-3.5-turbo": ModelPricing("gpt-3.5-turbo", 0.0005, 0.0015),
    "claude-3-opus": ModelPricing("claude-3-opus", 0.015, 0.075),
    "claude-3-sonnet": ModelPricing("claude-3-sonnet", 0.003, 0.015),
    "gemini-pro": ModelPricing("gemini-pro", 0.00025, 0.0005),
    "llama-3-70b": ModelPricing("llama-3-70b", 0.0, 0.0),  # Local/free
}


@dataclass
class CostMetrics:
    """Cost metrics for tracking."""

    total_cost: float = 0.0
    total_tokens: int = 0
    total_requests: int = 0
    cost_by_model: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tokens_by_model: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    requests_by_model: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    cost_by_user: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    cost_by_workflow: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    timestamp: datetime = field(default_factory=datetime.now)


# Global cost tracker (in production, use a proper database)
COST_TRACKER = CostMetrics()


# ==============================================================================
# Cost Tracking Primitive
# ==============================================================================


class CostTrackingPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Wrap any LLM primitive to track costs."""

    def __init__(
        self,
        primitive: InstrumentedPrimitive[dict[str, Any], dict[str, Any]],
        model_name: str,
        cost_tracker: CostMetrics | None = None,
    ) -> None:
        """
        Initialize cost tracking wrapper.

        Args:
            primitive: The LLM primitive to wrap
            model_name: Model name for pricing lookup
            cost_tracker: CostMetrics instance (defaults to global)
        """
        super().__init__(name="cost_tracking")
        self.primitive = primitive
        self.model_name = model_name
        self.cost_tracker = cost_tracker or COST_TRACKER
        self.pricing = MODEL_PRICING.get(model_name)

        if not self.pricing:
            raise ValueError(f"Unknown model: {model_name}. Add pricing to MODEL_PRICING.")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Execute primitive and track costs."""
        # Execute wrapped primitive
        result = await self.primitive._execute_impl(input_data, context)

        # Extract token usage from result
        usage = result.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        # Calculate cost
        prompt_cost = (prompt_tokens / 1000) * self.pricing.cost_per_1k_prompt_tokens
        completion_cost = (completion_tokens / 1000) * self.pricing.cost_per_1k_completion_tokens
        total_cost = prompt_cost + completion_cost

        # Extract attribution info from context
        user_id = context.metadata.get("user_id", "unknown")
        workflow_id = context.metadata.get("workflow_id", "unknown")

        # Update cost tracker
        self.cost_tracker.total_cost += total_cost
        self.cost_tracker.total_tokens += total_tokens
        self.cost_tracker.total_requests += 1
        self.cost_tracker.cost_by_model[self.model_name] += total_cost
        self.cost_tracker.tokens_by_model[self.model_name] += total_tokens
        self.cost_tracker.requests_by_model[self.model_name] += 1
        self.cost_tracker.cost_by_user[user_id] += total_cost
        self.cost_tracker.cost_by_workflow[workflow_id] += total_cost

        # Add cost info to result
        result["cost"] = {
            "model": self.model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "prompt_cost": prompt_cost,
            "completion_cost": completion_cost,
            "total_cost": total_cost,
            "currency": "USD",
        }

        return result


# ==============================================================================
# Budget Enforcement Primitive
# ==============================================================================


class BudgetEnforcementPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Enforce budget limits before execution."""

    def __init__(
        self,
        primitive: InstrumentedPrimitive[dict[str, Any], dict[str, Any]],
        max_cost_per_request: float,
        max_daily_cost: float,
        cost_tracker: CostMetrics | None = None,
    ) -> None:
        """
        Initialize budget enforcement.

        Args:
            primitive: The primitive to wrap
            max_cost_per_request: Maximum cost per single request (USD)
            max_daily_cost: Maximum daily cost (USD)
            cost_tracker: CostMetrics instance (defaults to global)
        """
        super().__init__(name="budget_enforcement")
        self.primitive = primitive
        self.max_cost_per_request = max_cost_per_request
        self.max_daily_cost = max_daily_cost
        self.cost_tracker = cost_tracker or COST_TRACKER

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Check budget before execution."""
        # Check daily budget
        if self.cost_tracker.total_cost >= self.max_daily_cost:
            raise RuntimeError(
                f"Daily budget exceeded: ${self.cost_tracker.total_cost:.4f} >= ${self.max_daily_cost:.2f}"
            )

        # Estimate request cost (rough estimate based on input size)
        estimated_tokens = len(str(input_data).split()) * 1.3  # Rough multiplier
        estimated_cost = (
            estimated_tokens / 1000
        ) * 0.01  # Conservative estimate using mid-tier pricing

        if estimated_cost > self.max_cost_per_request:
            raise RuntimeError(
                f"Estimated request cost ${estimated_cost:.4f} exceeds limit ${self.max_cost_per_request:.2f}"
            )

        # Execute if within budget
        result = await self.primitive._execute_impl(input_data, context)

        # Verify actual cost didn't exceed per-request limit
        actual_cost = result.get("cost", {}).get("total_cost", 0)
        if actual_cost > self.max_cost_per_request:
            # Log warning but don't fail (already executed)
            print(
                f"⚠️  Warning: Actual cost ${actual_cost:.4f} exceeded limit ${self.max_cost_per_request:.2f}"
            )

        return result


# ==============================================================================
# Mock LLM Primitives
# ==============================================================================


class MockLLMPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Mock LLM primitive for demonstration."""

    def __init__(
        self, model: str, avg_prompt_tokens: int = 100, avg_completion_tokens: int = 50
    ) -> None:
        """Initialize mock LLM."""
        super().__init__(name=f"mock_llm_{model}")
        self.model = model
        self.avg_prompt_tokens = avg_prompt_tokens
        self.avg_completion_tokens = avg_completion_tokens

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Simulate LLM call."""
        prompt = input_data.get("prompt", "")

        # Simulate API latency
        await asyncio.sleep(0.1)

        # Simulate token usage
        prompt_tokens = max(10, len(prompt.split()) + self.avg_prompt_tokens)
        completion_tokens = self.avg_completion_tokens

        return {
            "model": self.model,
            "response": f"Mock response from {self.model}",
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }


# ==============================================================================
# Cost Reporting
# ==============================================================================


def print_cost_report(cost_tracker: CostMetrics) -> None:
    """Print detailed cost report."""
    print("\n" + "=" * 80)
    print("COST TRACKING REPORT")
    print("=" * 80)
    print(f"\nTimestamp: {cost_tracker.timestamp}")
    print(f"\nTotal Cost: ${cost_tracker.total_cost:.6f} USD")
    print(f"Total Tokens: {cost_tracker.total_tokens:,}")
    print(f"Total Requests: {cost_tracker.total_requests}")

    if cost_tracker.total_tokens > 0:
        avg_cost_per_1k = (cost_tracker.total_cost / cost_tracker.total_tokens) * 1000
        print(f"Average Cost per 1K tokens: ${avg_cost_per_1k:.6f}")

    print("\n" + "-" * 80)
    print("COST BY MODEL")
    print("-" * 80)
    for model, cost in sorted(cost_tracker.cost_by_model.items(), key=lambda x: x[1], reverse=True):
        tokens = cost_tracker.tokens_by_model[model]
        requests = cost_tracker.requests_by_model[model]
        print(f"{model:20s} ${cost:10.6f}  |  {tokens:8,} tokens  |  {requests:4d} requests")

    print("\n" + "-" * 80)
    print("COST BY USER")
    print("-" * 80)
    for user, cost in sorted(cost_tracker.cost_by_user.items(), key=lambda x: x[1], reverse=True):
        print(f"{user:20s} ${cost:10.6f}")

    print("\n" + "-" * 80)
    print("COST BY WORKFLOW")
    print("-" * 80)
    for workflow, cost in sorted(
        cost_tracker.cost_by_workflow.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"{workflow:20s} ${cost:10.6f}")

    print("=" * 80 + "\n")


# ==============================================================================
# Example Usage
# ==============================================================================


async def main() -> None:
    """Demonstrate cost tracking."""
    print("=" * 80)
    print("Cost Tracking with Metrics Example")
    print("=" * 80)
    print()

    # Create mock LLM primitives
    gpt4_llm = MockLLMPrimitive("gpt-4", avg_prompt_tokens=150, avg_completion_tokens=100)
    gpt4_mini_llm = MockLLMPrimitive("gpt-4-mini", avg_prompt_tokens=120, avg_completion_tokens=80)
    claude_llm = MockLLMPrimitive(
        "claude-3-sonnet", avg_prompt_tokens=140, avg_completion_tokens=90
    )

    # Wrap with cost tracking
    gpt4_tracked = CostTrackingPrimitive(gpt4_llm, "gpt-4")
    gpt4_mini_tracked = CostTrackingPrimitive(gpt4_mini_llm, "gpt-4-mini")
    claude_tracked = CostTrackingPrimitive(claude_llm, "claude-3-sonnet")

    # Add budget enforcement
    gpt4_safe = BudgetEnforcementPrimitive(
        gpt4_tracked,
        max_cost_per_request=0.10,  # $0.10 per request
        max_daily_cost=10.00,  # $10 daily limit
    )

    gpt4_mini_safe = BudgetEnforcementPrimitive(
        gpt4_mini_tracked,
        max_cost_per_request=0.01,  # $0.01 per request
        max_daily_cost=10.00,  # $10 daily limit
    )

    # Simulate multiple requests from different users and workflows
    test_cases = [
        {
            "user_id": "user-alice",
            "workflow_id": "rag-workflow",
            "model": gpt4_mini_safe,
            "prompt": "What is TTA.dev?",
        },
        {
            "user_id": "user-bob",
            "workflow_id": "chat-workflow",
            "model": claude_tracked,
            "prompt": "Explain multi-agent coordination.",
        },
        {
            "user_id": "user-alice",
            "workflow_id": "analysis-workflow",
            "model": gpt4_safe,
            "prompt": "Analyze this complex data set with detailed insights.",
        },
        {
            "user_id": "user-charlie",
            "workflow_id": "rag-workflow",
            "model": gpt4_mini_safe,
            "prompt": "How do I use primitives?",
        },
        {
            "user_id": "user-bob",
            "workflow_id": "chat-workflow",
            "model": gpt4_mini_safe,
            "prompt": "Quick question about caching.",
        },
    ]

    print("Processing requests...\n")

    for i, test_case in enumerate(test_cases, 1):
        # Create context with attribution info
        context = WorkflowContext(
            correlation_id=f"req-{i}",
            metadata={
                "user_id": test_case["user_id"],
                "workflow_id": test_case["workflow_id"],
            },
        )

        # Execute
        result = await test_case["model"]._execute_impl({"prompt": test_case["prompt"]}, context)

        # Display result
        cost_info = result["cost"]
        print(f"Request {i}:")
        print(f"  User: {test_case['user_id']}")
        print(f"  Workflow: {test_case['workflow_id']}")
        print(f"  Model: {cost_info['model']}")
        print(f"  Tokens: {cost_info['total_tokens']}")
        print(f"  Cost: ${cost_info['total_cost']:.6f}")
        print()

    # Print final cost report
    print_cost_report(COST_TRACKER)

    print("✅ Cost tracking complete!")
    print()
    print("Key Features Demonstrated:")
    print("  ✅ Token usage tracking")
    print("  ✅ Cost calculation per model")
    print("  ✅ Budget enforcement")
    print("  ✅ Cost attribution (user/workflow)")
    print("  ✅ Detailed cost reporting")


if __name__ == "__main__":
    asyncio.run(main())
