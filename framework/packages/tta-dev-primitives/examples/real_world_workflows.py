"""
Real-world workflow composition examples for tta-dev-primitives.

This example demonstrates building practical AI application workflows
using the composable primitives.
"""

import asyncio

from tta_dev_primitives.core.base import LambdaPrimitive, WorkflowContext
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.routing import RouterPrimitive
from tta_dev_primitives.core.sequential import SequentialPrimitive
from tta_dev_primitives.performance.cache import CachePrimitive
from tta_dev_primitives.recovery.fallback import FallbackPrimitive
from tta_dev_primitives.recovery.retry import RetryPrimitive
from tta_dev_primitives.recovery.timeout import TimeoutPrimitive


# Example 1: Customer Support Chatbot Workflow
async def customer_support_workflow():
    """
    A customer support workflow that:
    1. Validates input
    2. Checks cache for similar questions
    3. Routes to appropriate model based on complexity
    4. Retries on failure
    5. Falls back to simpler model if needed
    """

    # Define primitives
    validate_input = LambdaPrimitive(
        lambda x, ctx: {**x, "validated": True}
        if x.get("message")
        else {"error": "No message provided"}
    )

    # Cache with 1-hour TTL
    cache = CachePrimitive(ttl=3600, max_size=1000)

    # Route based on question complexity
    router = RouterPrimitive(
        routes={
            "simple": LambdaPrimitive(
                lambda x, ctx: {
                    **x,
                    "response": f"Simple answer to: {x['message']}",
                    "model": "fast-model",
                }
            ),
            "complex": LambdaPrimitive(
                lambda x, ctx: {
                    **x,
                    "response": f"Detailed answer to: {x['message']}",
                    "model": "quality-model",
                }
            ),
        },
        default_route="simple",
    )

    # Retry with exponential backoff
    with_retry = RetryPrimitive(primitive=router, max_attempts=3, backoff_factor=2.0)

    # Timeout after 30 seconds
    with_timeout = TimeoutPrimitive(primitive=with_retry, timeout_seconds=30.0)

    # Fallback to simple response if all else fails
    with_fallback = FallbackPrimitive(
        primary=with_timeout,
        fallback=LambdaPrimitive(
            lambda x, ctx: {
                **x,
                "response": "I'm having trouble processing your request. Please try again.",
                "fallback_used": True,
            }
        ),
    )

    # Compose the full workflow
    workflow = SequentialPrimitive([validate_input, cache, with_fallback])

    # Execute
    context = WorkflowContext(workflow_id="customer-support", session_id="user-123")

    data = {"message": "How do I reset my password?"}
    result = await workflow.execute(data, context)

    print("Customer Support Result:")
    print(result)
    return result


# Example 2: Content Generation Pipeline
async def content_generation_pipeline():
    """
    A content generation workflow that:
    1. Analyzes the topic in parallel (sentiment, keywords, similar content)
    2. Generates content with appropriate model
    3. Post-processes and validates
    """

    # Parallel analysis
    parallel_analysis = ParallelPrimitive(
        [
            LambdaPrimitive(
                lambda x, ctx: {**x, "sentiment": "neutral"}, name="sentiment_analyzer"
            ),
            LambdaPrimitive(
                lambda x, ctx: {**x, "keywords": ["AI", "development", "tools"]},
                name="keyword_extractor",
            ),
            LambdaPrimitive(lambda x, ctx: {**x, "similar_count": 5}, name="similarity_checker"),
        ]
    )

    # Content generation
    generate_content = LambdaPrimitive(
        lambda x, ctx: {
            **x,
            "content": f"Generated content about {x.get('topic', 'unknown')}",
            "word_count": 500,
        }
    )

    # Post-processing
    post_process = LambdaPrimitive(
        lambda x, ctx: {
            **x,
            "formatted": True,
            "html": f"<article>{x.get('content', '')}</article>",
        }
    )

    # Compose workflow
    workflow = SequentialPrimitive([parallel_analysis, generate_content, post_process])

    context = WorkflowContext(workflow_id="content-gen", session_id="blog-writer")

    data = {"topic": "AI Development Best Practices"}
    result = await workflow.execute(data, context)

    print("\nContent Generation Result:")
    print(result)
    return result


# Example 3: Data Processing Pipeline with Conditional Logic
async def data_processing_pipeline():
    """
    A data processing workflow with conditional branching:
    1. Load data
    2. Validate schema
    3. Branch based on data type
    4. Transform and enrich
    5. Save results
    """
    from tta_dev_primitives.core.conditional import ConditionalPrimitive

    # Load data
    load_data = LambdaPrimitive(
        lambda x, ctx: {**x, "data": [1, 2, 3, 4, 5], "data_type": "numbers"}
    )

    # Conditional processing based on data type
    process_numbers = LambdaPrimitive(
        lambda x, ctx: {
            **x,
            "processed": [n * 2 for n in x.get("data", [])],
            "operation": "multiply_by_2",
        }
    )

    process_strings = LambdaPrimitive(
        lambda x, ctx: {
            **x,
            "processed": [s.upper() for s in x.get("data", [])],
            "operation": "uppercase",
        }
    )

    conditional_processor = ConditionalPrimitive(
        condition=lambda x, ctx: x.get("data_type") == "numbers",
        if_true=process_numbers,
        if_false=process_strings,
    )

    # Enrich with metadata
    enrich = LambdaPrimitive(
        lambda x, ctx: {
            **x,
            "timestamp": "2024-10-28T12:00:00Z",
            "processed_count": len(x.get("processed", [])),
        }
    )

    # Compose workflow
    workflow = SequentialPrimitive([load_data, conditional_processor, enrich])

    context = WorkflowContext(workflow_id="data-processing", session_id="etl-job-001")

    data = {}
    result = await workflow.execute(data, context)

    print("\nData Processing Result:")
    print(result)
    return result


# Example 4: LLM Chain with Caching and Routing
async def llm_chain_workflow():
    """
    A typical LLM application workflow:
    1. Validate and preprocess input
    2. Check cache for similar queries
    3. Route to appropriate model tier
    4. Process response
    5. Cache results
    """

    # Input preprocessing
    preprocess = LambdaPrimitive(
        lambda x, ctx: {
            **x,
            "clean_prompt": x.get("prompt", "").strip(),
            "tier": x.get("tier", "balanced"),
        }
    )

    # Cache layer
    cache = CachePrimitive(ttl=1800, max_size=500)

    # Multi-tier routing
    router = RouterPrimitive(
        routes={
            "fast": LambdaPrimitive(
                lambda x, ctx: {
                    **x,
                    "response": f"Fast response: {x['clean_prompt'][:20]}...",
                    "cost": 0.001,
                    "latency_ms": 100,
                }
            ),
            "balanced": LambdaPrimitive(
                lambda x, ctx: {
                    **x,
                    "response": f"Balanced response: {x['clean_prompt'][:20]}...",
                    "cost": 0.01,
                    "latency_ms": 500,
                }
            ),
            "quality": LambdaPrimitive(
                lambda x, ctx: {
                    **x,
                    "response": f"Quality response: {x['clean_prompt'][:20]}...",
                    "cost": 0.05,
                    "latency_ms": 2000,
                }
            ),
        },
        default_route="balanced",
    )

    # Post-processing
    postprocess = LambdaPrimitive(
        lambda x, ctx: {
            **x,
            "formatted_response": x.get("response", ""),
            "metadata": {
                "tier": x.get("tier"),
                "cost": x.get("cost"),
                "latency_ms": x.get("latency_ms"),
            },
        }
    )

    # Compose with operator overloading
    workflow = preprocess >> cache >> router >> postprocess

    context = WorkflowContext(workflow_id="llm-chain", session_id="chat-abc123")

    # Test different tiers
    for tier in ["fast", "balanced", "quality"]:
        data = {"prompt": "Explain quantum computing in simple terms", "tier": tier}
        result = await workflow.execute(data, context)
        print(f"\n{tier.upper()} Tier Result:")
        print(f"  Response: {result['formatted_response']}")
        print(f"  Metadata: {result['metadata']}")

    return result


async def main() -> None:
    """Run all examples."""
    print("=" * 60)
    print("TTA-Dev-Primitives: Real-World Workflow Examples")
    print("=" * 60)

    await customer_support_workflow()
    await content_generation_pipeline()
    await data_processing_pipeline()
    await llm_chain_workflow()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
