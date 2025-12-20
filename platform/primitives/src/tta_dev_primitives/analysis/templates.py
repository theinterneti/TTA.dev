"""Code templates for TTA.dev primitives.

Provides ready-to-use code templates and examples for each primitive.
"""

from typing import Any


class TemplateProvider:
    """Provides code templates and examples for TTA.dev primitives.

    Templates are ready-to-use code snippets that can be
    inserted directly into user code with minimal modification.

    Example:
        provider = TemplateProvider()
        template = provider.get_template("RetryPrimitive")
        print(template)  # Ready-to-use Python code
    """

    def __init__(self) -> None:
        """Initialize with template definitions."""
        self.templates: dict[str, dict[str, Any]] = {
            "RetryPrimitive": {
                "basic": """from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives import WorkflowContext

# Wrap your function with retry logic
retry = RetryPrimitive(
    primitive=your_api_call,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0,
    jitter=True
)

# Execute with automatic retry
context = WorkflowContext(workflow_id="retry-example")
result = await retry.execute(data, context)""",
                "with_composition": """from tta_dev_primitives.recovery import RetryPrimitive, TimeoutPrimitive
from tta_dev_primitives import WorkflowContext

# Compose timeout + retry
workflow = (
    TimeoutPrimitive(seconds=30) >>
    RetryPrimitive(max_retries=3) >>
    your_api_call
)

context = WorkflowContext(workflow_id="reliable-api")
result = await workflow.execute(data, context)""",
                "examples": [
                    "Retry failed API calls with exponential backoff",
                    "Handle rate limiting with automatic retry",
                    "Recover from transient network errors",
                ],
            },
            "TimeoutPrimitive": {
                "basic": """from tta_dev_primitives.recovery import TimeoutPrimitive
from tta_dev_primitives import WorkflowContext

# Add timeout protection
timeout = TimeoutPrimitive(
    primitive=slow_operation,
    timeout_seconds=30.0,
    raise_on_timeout=True
)

context = WorkflowContext(workflow_id="timeout-example")
result = await timeout.execute(data, context)""",
                "with_fallback": """from tta_dev_primitives.recovery import TimeoutPrimitive, FallbackPrimitive
from tta_dev_primitives import WorkflowContext

# Timeout with fallback
protected = FallbackPrimitive(
    primary=TimeoutPrimitive(slow_api, timeout_seconds=10),
    fallbacks=[fast_cache_lookup, default_response]
)

context = WorkflowContext(workflow_id="protected-call")
result = await protected.execute(data, context)""",
                "examples": [
                    "Prevent hanging API calls",
                    "Set time limits on database queries",
                    "Protect webhook processing",
                ],
            },
            "CachePrimitive": {
                "basic": """from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives import WorkflowContext

# Cache expensive operations
cached = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,  # 1 hour
    max_size=1000
)

context = WorkflowContext(workflow_id="cached-llm")
result = await cached.execute(prompt, context)  # Cached on second call""",
                "with_custom_key": """from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives import WorkflowContext

# Custom cache key function
def make_cache_key(data, ctx):
    return f"{data['model']}:{hash(data['prompt'])}"

cached = CachePrimitive(
    primitive=llm_call,
    ttl_seconds=3600,
    key_fn=make_cache_key
)

context = WorkflowContext(workflow_id="smart-cache")
result = await cached.execute({"model": "gpt-4", "prompt": "Hello"}, context)""",
                "examples": [
                    "Cache LLM responses (save 40-60% costs)",
                    "Cache API responses",
                    "Memoize expensive computations",
                ],
            },
            "FallbackPrimitive": {
                "basic": """from tta_dev_primitives.recovery import FallbackPrimitive
from tta_dev_primitives import WorkflowContext

# Graceful degradation with fallbacks
fallback = FallbackPrimitive(
    primary=openai_gpt4,
    fallbacks=[anthropic_claude, local_llama, cached_response]
)

context = WorkflowContext(workflow_id="resilient-llm")
result = await fallback.execute(prompt, context)""",
                "multi_provider": """from tta_dev_primitives.recovery import FallbackPrimitive, RetryPrimitive
from tta_dev_primitives import WorkflowContext

# Multi-provider with retry per provider
fallback = FallbackPrimitive(
    primary=RetryPrimitive(openai_call, max_retries=2),
    fallbacks=[
        RetryPrimitive(anthropic_call, max_retries=2),
        RetryPrimitive(local_model, max_retries=1),
    ]
)

context = WorkflowContext(workflow_id="multi-llm")
result = await fallback.execute(data, context)""",
                "examples": [
                    "Multi-LLM provider failover",
                    "Graceful service degradation",
                    "High availability patterns",
                ],
            },
            "ParallelPrimitive": {
                "basic": """from tta_dev_primitives import ParallelPrimitive, WorkflowContext

# Execute multiple operations concurrently
parallel = ParallelPrimitive([
    fetch_user_data,
    fetch_recommendations,
    fetch_analytics
])

context = WorkflowContext(workflow_id="parallel-fetch")
results = await parallel.execute(user_id, context)
# results = [user_data, recommendations, analytics]""",
                "with_operator": """from tta_dev_primitives import WorkflowContext

# Use | operator for parallel composition
workflow = fetch_user | fetch_recs | fetch_analytics

context = WorkflowContext(workflow_id="parallel-op")
results = await workflow.execute(user_id, context)""",
                "examples": [
                    "Fetch data from multiple APIs concurrently",
                    "Parallel LLM calls for comparison",
                    "Concurrent data processing",
                ],
            },
            "SequentialPrimitive": {
                "basic": """from tta_dev_primitives import SequentialPrimitive, WorkflowContext

# Execute operations in sequence
workflow = SequentialPrimitive([
    validate_input,
    process_data,
    save_result
])

context = WorkflowContext(workflow_id="pipeline")
result = await workflow.execute(data, context)""",
                "with_operator": """from tta_dev_primitives import WorkflowContext

# Use >> operator for sequential composition
workflow = validate >> process >> save >> notify

context = WorkflowContext(workflow_id="chain")
result = await workflow.execute(data, context)""",
                "examples": [
                    "Multi-stage data pipelines",
                    "Validation → Processing → Storage",
                    "Chained transformations",
                ],
            },
            "RouterPrimitive": {
                "basic": """from tta_dev_primitives.core import RouterPrimitive
from tta_dev_primitives import WorkflowContext

def select_provider(data, ctx):
    if data.get("priority") == "quality":
        return "gpt4"
    elif data.get("priority") == "speed":
        return "gpt4-mini"
    return "default"

router = RouterPrimitive(
    routes={
        "gpt4": openai_gpt4,
        "gpt4-mini": openai_mini,
        "default": local_model
    },
    router_fn=select_provider,
    default="default"
)

context = WorkflowContext(workflow_id="smart-router")
result = await router.execute({"prompt": "Hello", "priority": "quality"}, context)""",
                "cost_based": """from tta_dev_primitives.core import RouterPrimitive
from tta_dev_primitives import WorkflowContext

def cost_aware_routing(data, ctx):
    estimated_tokens = len(data["prompt"].split()) * 1.3
    if estimated_tokens > 1000:
        return "cheap"  # Use cheaper model for long prompts
    return "quality"

router = RouterPrimitive(
    routes={"quality": gpt4, "cheap": gpt4_mini},
    router_fn=cost_aware_routing
)""",
                "examples": [
                    "Cost-optimized model selection",
                    "Performance-based routing",
                    "Geographic routing",
                ],
            },
            "CircuitBreakerPrimitive": {
                "basic": """from tta_dev_primitives.recovery import CircuitBreakerPrimitive
from tta_dev_primitives import WorkflowContext

# Protect against cascade failures
protected = CircuitBreakerPrimitive(
    primitive=unreliable_service,
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60,      # Try again after 60 seconds
    expected_successes=2      # Close after 2 successes
)

context = WorkflowContext(workflow_id="circuit-breaker")
result = await protected.execute(data, context)""",
                "examples": [
                    "Protect against unreliable services",
                    "Prevent cascade failures",
                    "Service health monitoring",
                ],
            },
            "MemoryPrimitive": {
                "basic": """from tta_dev_primitives.performance import MemoryPrimitive

# Zero-setup conversational memory
memory = MemoryPrimitive(max_size=100)

# Store conversation turns
await memory.add("user_msg_1", {"role": "user", "content": "Hello"})
await memory.add("assistant_1", {"role": "assistant", "content": "Hi there!"})

# Retrieve by key
msg = await memory.get("user_msg_1")

# Search by keywords
results = await memory.search("hello")""",
                "examples": [
                    "Multi-turn conversation history",
                    "Agent memory and context",
                    "Personalization based on history",
                ],
            },
        }

    def get_template(self, primitive_name: str, template_type: str = "basic") -> str | None:
        """Get a code template for a primitive.

        Args:
            primitive_name: Name of the primitive
            template_type: Type of template ("basic", "with_composition", etc.)

        Returns:
            Template string or None if not found
        """
        if primitive_name not in self.templates:
            return None

        return self.templates[primitive_name].get(template_type)

    def get_all_templates(self, primitive_name: str) -> dict[str, str]:
        """Get all templates for a primitive.

        Args:
            primitive_name: Name of the primitive

        Returns:
            Dict of template_type -> template_string
        """
        if primitive_name not in self.templates:
            return {}

        info = self.templates[primitive_name]
        return {
            key: value
            for key, value in info.items()
            if key != "examples" and isinstance(value, str)
        }

    def get_examples(self, primitive_name: str) -> list[str]:
        """Get example use cases for a primitive.

        Args:
            primitive_name: Name of the primitive

        Returns:
            List of example descriptions
        """
        if primitive_name not in self.templates:
            return []

        return self.templates[primitive_name].get("examples", [])

    def list_available_templates(self) -> list[str]:
        """List all primitives that have templates."""
        return list(self.templates.keys())

    def search_templates(self, query: str) -> list[dict[str, Any]]:
        """Search templates by keyword.

        Args:
            query: Search query

        Returns:
            List of matching template info
        """
        query_lower = query.lower()
        results = []

        for name, info in self.templates.items():
            # Search in examples
            examples = info.get("examples", [])
            for example in examples:
                if query_lower in example.lower():
                    results.append(
                        {
                            "primitive_name": name,
                            "match_type": "example",
                            "match_text": example,
                        }
                    )

            # Search in templates
            for template_type, template in info.items():
                if template_type != "examples" and isinstance(template, str):
                    if query_lower in template.lower():
                        results.append(
                            {
                                "primitive_name": name,
                                "match_type": "template",
                                "template_type": template_type,
                            }
                        )

        return results
