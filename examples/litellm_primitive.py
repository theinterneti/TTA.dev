"""LiteLLMPrimitive — canonical usage examples.

Demonstrates the recommended primary LLM execution path for TTA.dev:
LiteLLMPrimitive (via litellm) with TTA.dev's orchestration layer on top.

Run any example directly:
    uv run python examples/litellm_primitive.py

Set at least one provider key to get real responses:
    export GROQ_API_KEY=gsk_...
    export ANTHROPIC_API_KEY=sk-ant-...
    export OPENROUTER_API_KEY=sk-or-...
"""

import asyncio
import os

from ttadev.primitives import LiteLLMPrimitive, WorkflowContext, make_resilient_llm
from ttadev.primitives.llm import LLMProvider, LLMRequest, ToolSchema

# ---------------------------------------------------------------------------
# Example 1: Basic call
# ---------------------------------------------------------------------------


async def example_basic() -> None:
    """Simplest possible LiteLLMPrimitive call."""
    print("\n=== Example 1: Basic call ===")

    llm = LiteLLMPrimitive(
        provider=LLMProvider.GROQ,
        model="llama-3.1-8b-instant",
        temperature=0.0,
    )
    ctx = WorkflowContext(workflow_id="litellm-basic")
    request = LLMRequest(
        messages=[{"role": "user", "content": "What is 2 + 2? Reply with just the number."}]
    )

    response = await llm.execute(request, ctx)
    print(f"Content  : {response.content!r}")
    print(f"Provider : {response.provider}")
    print(f"Model    : {response.model}")
    print(f"Usage    : {response.usage}")


# ---------------------------------------------------------------------------
# Example 2: Pre-formed litellm model string
# ---------------------------------------------------------------------------


async def example_litellm_string() -> None:
    """Accept litellm-native 'provider/model' strings directly."""
    print("\n=== Example 2: litellm model string ===")

    # No need for LLMProvider enum — pass the string directly
    llm = LiteLLMPrimitive(model="groq/llama-3.1-8b-instant")
    ctx = WorkflowContext(workflow_id="litellm-string")
    request = LLMRequest(
        messages=[{"role": "user", "content": "Name the capital of France. One word."}],
        model="groq/llama-3.1-8b-instant",
    )
    response = await llm.execute(request, ctx)
    print(f"Answer: {response.content!r}")


# ---------------------------------------------------------------------------
# Example 3: make_resilient_llm factory — retry + cache + litellm fallbacks
# ---------------------------------------------------------------------------


async def example_resilient() -> None:
    """Production-ready resilient LLM with retry, cache, and provider fallback."""
    print("\n=== Example 3: make_resilient_llm ===")

    llm = make_resilient_llm(
        model="groq/llama-3.1-8b-instant",
        temperature=0.2,
        cache_ttl_seconds=120.0,  # cache identical prompts for 2 min
        max_retries=3,
        litellm_fallbacks=[  # try these if groq fails
            "anthropic/claude-3-haiku-20240307",
            "openrouter/meta-llama/llama-3.1-8b-instruct:free",
        ],
    )
    ctx = WorkflowContext(workflow_id="litellm-resilient")
    request = LLMRequest(
        messages=[{"role": "user", "content": "Explain async/await in one sentence."}]
    )

    response = await llm.execute(request, ctx)
    print(f"Response: {response.content!r}")
    print(f"Provider: {response.provider} | Model: {response.model}")


# ---------------------------------------------------------------------------
# Example 4: Streaming
# ---------------------------------------------------------------------------


async def example_streaming() -> None:
    """Stream tokens as they arrive."""
    print("\n=== Example 4: Streaming ===")

    llm = LiteLLMPrimitive(model="groq/llama-3.1-8b-instant")
    ctx = WorkflowContext(workflow_id="litellm-stream")
    request = LLMRequest(
        messages=[{"role": "user", "content": "Count from 1 to 5, one number per line."}]
    )

    print("Streaming: ", end="", flush=True)
    async for chunk in llm.stream(request, ctx):
        print(chunk, end="", flush=True)
    print()  # newline after stream


# ---------------------------------------------------------------------------
# Example 5: Tool calls
# ---------------------------------------------------------------------------


async def example_tool_calls() -> None:
    """Demonstrate structured tool-call output."""
    print("\n=== Example 5: Tool calls ===")

    llm = LiteLLMPrimitive(model="groq/llama-3.1-8b-instant")
    ctx = WorkflowContext(workflow_id="litellm-tools")

    tools = [
        ToolSchema(
            name="get_weather",
            description="Get the current weather for a city.",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit",
                    },
                },
                "required": ["city"],
            },
        )
    ]

    request = LLMRequest(
        messages=[{"role": "user", "content": "What's the weather in Paris right now?"}],
        tools=tools,
    )
    response = await llm.execute(request, ctx)

    if response.tool_calls:
        for tc in response.tool_calls:
            print(f"Tool: {tc.name}  Args: {tc.arguments}")
    else:
        print(f"No tool call — text response: {response.content!r}")


# ---------------------------------------------------------------------------
# Example 6: System prompt + metadata
# ---------------------------------------------------------------------------


async def example_system_and_metadata() -> None:
    """Pass a system prompt and metadata tags for Langfuse tracing."""
    print("\n=== Example 6: System prompt + metadata ===")

    llm = LiteLLMPrimitive(
        model="groq/llama-3.1-8b-instant",
        system_prompt="You are a pirate. Answer everything in pirate speak.",
        metadata={"trace_id": "my-trace-123", "user_id": "demo-user"},
    )
    ctx = WorkflowContext(workflow_id="litellm-system")
    request = LLMRequest(messages=[{"role": "user", "content": "Good morning!"}])
    response = await llm.execute(request, ctx)
    print(f"Pirate says: {response.content!r}")


# ---------------------------------------------------------------------------
# Example 7: Multi-provider strategy (no TTA.dev FallbackPrimitive needed)
# ---------------------------------------------------------------------------


async def example_litellm_native_fallbacks() -> None:
    """Use litellm's own fallback list — no FallbackPrimitive required."""
    print("\n=== Example 7: litellm-native fallbacks ===")

    llm = LiteLLMPrimitive(
        model="groq/llama-3.1-8b-instant",
        litellm_fallbacks=[
            "anthropic/claude-3-haiku-20240307",
            "openrouter/meta-llama/llama-3.1-8b-instruct:free",
        ],
    )
    ctx = WorkflowContext(workflow_id="litellm-fallback")
    request = LLMRequest(messages=[{"role": "user", "content": "Hello!"}])
    response = await llm.execute(request, ctx)
    print(f"Answered by: {response.provider}/{response.model}")
    print(f"Content: {response.content!r}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run all examples that have a required API key present."""
    has_key = any(
        [
            os.environ.get("GROQ_API_KEY"),
            os.environ.get("ANTHROPIC_API_KEY"),
            os.environ.get("OPENROUTER_API_KEY"),
        ]
    )
    if not has_key:
        print("⚠️  No API key found. Set GROQ_API_KEY, ANTHROPIC_API_KEY, or OPENROUTER_API_KEY.")
        print("   Examples will still run but will raise AuthenticationError from the provider.")

    await example_basic()
    await example_litellm_string()
    await example_resilient()
    await example_streaming()
    await example_tool_calls()
    await example_system_and_metadata()
    await example_litellm_native_fallbacks()

    print("\n✅ All examples complete.")


if __name__ == "__main__":
    asyncio.run(main())
