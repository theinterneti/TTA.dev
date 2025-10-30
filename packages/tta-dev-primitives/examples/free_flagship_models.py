"""Free Flagship Model Access Examples.

This module demonstrates how to access flagship-quality LLM models for free using
TTA.dev primitives. All examples use 100% free models with no credit card required
(except Together.ai which requires credit card but provides $25 free credits).

**Providers Covered:**
1. Google AI Studio (Gemini 2.5 Pro) - FREE flagship model
2. OpenRouter (DeepSeek R1) - FREE, on par with OpenAI o1
3. Groq (Llama 3.3 70B) - FREE, ultra-fast inference
4. Hugging Face (thousands of models) - FREE, 300 req/hour
5. Together.ai (Llama 4 Scout) - $25 free credits

**Setup Instructions:**
1. Obtain API keys from each provider (see Quick Start Guide in docs)
2. Set environment variables or pass keys directly
3. Run examples to verify access

**Environment Variables:**
- GOOGLE_API_KEY: Google AI Studio API key
- OPENROUTER_API_KEY: OpenRouter API key
- GROQ_API_KEY: Groq API key
- HF_TOKEN: Hugging Face API token
- TOGETHER_API_KEY: Together.ai API key
"""

import asyncio
import os

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.integrations import (
    GoogleAIStudioPrimitive,
    GroqPrimitive,
    HuggingFacePrimitive,
    OpenRouterPrimitive,
    TogetherAIPrimitive,
)
from tta_dev_primitives.integrations.google_ai_studio_primitive import GoogleAIStudioRequest
from tta_dev_primitives.integrations.groq_primitive import GroqRequest
from tta_dev_primitives.integrations.huggingface_primitive import HuggingFaceRequest
from tta_dev_primitives.integrations.openrouter_primitive import OpenRouterRequest
from tta_dev_primitives.integrations.together_ai_primitive import TogetherAIRequest
from tta_dev_primitives.recovery import FallbackPrimitive


# ============================================================================
# Example 1: Google AI Studio (Gemini 2.5 Pro) - FREE Flagship Model
# ============================================================================


async def example_google_ai_studio():
    """Demonstrate free Gemini Pro access via Google AI Studio.

    **Free Tier:**
    - Gemini 2.5 Pro: 89/100 quality, 2M context window
    - 1500 RPD free tier
    - No credit card required

    **Setup:**
    1. Go to https://aistudio.google.com/
    2. Click "Get API key"
    3. Create new API key
    4. Set GOOGLE_API_KEY environment variable
    """
    print("\n" + "=" * 80)
    print("Example 1: Google AI Studio (Gemini 2.5 Pro) - FREE Flagship Model")
    print("=" * 80)

    # Create primitive
    llm = GoogleAIStudioPrimitive(
        model="gemini-2.5-pro", api_key=os.getenv("GOOGLE_API_KEY")
    )

    # Create request
    context = WorkflowContext(workflow_id="gemini-demo")
    request = GoogleAIStudioRequest(
        messages=[
            {"role": "user", "content": "Explain quantum computing in 2 sentences."}
        ]
    )

    # Execute
    response = await llm.execute(request, context)

    print(f"\n✅ Model: {response.model}")
    print(f"📝 Response: {response.content}")
    print(f"📊 Usage: {response.usage}")
    print(f"🎯 Quality: 89/100 (flagship)")
    print(f"💰 Cost: $0.00 (FREE)")


# ============================================================================
# Example 2: OpenRouter (DeepSeek R1) - FREE, On Par with OpenAI o1
# ============================================================================


async def example_openrouter():
    """Demonstrate free DeepSeek R1 access via OpenRouter.

    **Free Tier:**
    - DeepSeek R1: 90/100 quality, on par with OpenAI o1
    - Daily limits that reset at midnight UTC
    - No credit card required

    **Setup:**
    1. Go to https://openrouter.ai/
    2. Sign up for free account
    3. Get API key from dashboard
    4. Set OPENROUTER_API_KEY environment variable
    """
    print("\n" + "=" * 80)
    print("Example 2: OpenRouter (DeepSeek R1) - FREE, On Par with OpenAI o1")
    print("=" * 80)

    # Create primitive
    llm = OpenRouterPrimitive(
        model="deepseek/deepseek-r1:free", api_key=os.getenv("OPENROUTER_API_KEY")
    )

    # Create request
    context = WorkflowContext(workflow_id="deepseek-demo")
    request = OpenRouterRequest(
        messages=[{"role": "user", "content": "What is the meaning of life?"}]
    )

    # Execute
    response = await llm.execute(request, context)

    print(f"\n✅ Model: {response.model}")
    print(f"📝 Response: {response.content}")
    print(f"📊 Usage: {response.usage}")
    print(f"🎯 Quality: 90/100 (flagship)")
    print(f"💰 Cost: $0.00 (FREE)")


# ============================================================================
# Example 3: Groq (Llama 3.3 70B) - FREE, Ultra-Fast Inference
# ============================================================================


async def example_groq():
    """Demonstrate ultra-fast free inference via Groq.

    **Free Tier:**
    - Llama 3.3 70B: 87/100 quality, 300+ tokens/sec
    - 14,400 RPD free tier
    - No credit card required

    **Setup:**
    1. Go to https://console.groq.com/
    2. Sign up for free account
    3. Get API key from dashboard
    4. Set GROQ_API_KEY environment variable
    """
    print("\n" + "=" * 80)
    print("Example 3: Groq (Llama 3.3 70B) - FREE, Ultra-Fast Inference")
    print("=" * 80)

    # Create primitive
    llm = GroqPrimitive(model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))

    # Create request
    context = WorkflowContext(workflow_id="groq-demo")
    request = GroqRequest(
        messages=[{"role": "user", "content": "Write a haiku about coding."}]
    )

    # Execute
    import time

    start = time.time()
    response = await llm.execute(request, context)
    elapsed = time.time() - start

    print(f"\n✅ Model: {response.model}")
    print(f"📝 Response: {response.content}")
    print(f"📊 Usage: {response.usage}")
    print(f"⚡ Speed: {response.usage['completion_tokens'] / elapsed:.0f} tokens/sec")
    print(f"🎯 Quality: 87/100 (production-ready)")
    print(f"💰 Cost: $0.00 (FREE)")


# ============================================================================
# Example 4: Hugging Face (Llama 3.3 70B) - FREE, Model Variety
# ============================================================================


async def example_huggingface():
    """Demonstrate free access to thousands of models via Hugging Face.

    **Free Tier:**
    - Access to thousands of models
    - 300 requests/hour (registered users)
    - No credit card required

    **Setup:**
    1. Go to https://huggingface.co/
    2. Sign up for free account
    3. Get API token from settings
    4. Set HF_TOKEN environment variable
    """
    print("\n" + "=" * 80)
    print("Example 4: Hugging Face (Llama 3.3 70B) - FREE, Model Variety")
    print("=" * 80)

    # Create primitive
    llm = HuggingFacePrimitive(
        model="meta-llama/Llama-3.3-70B-Instruct", api_key=os.getenv("HF_TOKEN")
    )

    # Create request
    context = WorkflowContext(workflow_id="hf-demo")
    request = HuggingFaceRequest(
        messages=[{"role": "user", "content": "What is machine learning?"}]
    )

    # Execute
    response = await llm.execute(request, context)

    print(f"\n✅ Model: {response.model}")
    print(f"📝 Response: {response.content}")
    print(f"📊 Usage: {response.usage} (estimated)")
    print(f"🎯 Quality: 87/100 (production-ready)")
    print(f"💰 Cost: $0.00 (FREE)")


# ============================================================================
# Example 5: Together.ai (Llama 4 Scout) - $25 Free Credits
# ============================================================================


async def example_together_ai():
    """Demonstrate $25 free credits via Together.ai.

    **Free Credits:**
    - $25 in free credits for new users
    - Llama 4 Scout: 88/100 quality
    - 3 months of unlimited FLUX.1 image generation

    **Setup:**
    1. Go to https://www.together.ai/
    2. Sign up for account (credit card required)
    3. Get $25 in free credits
    4. Get API key from dashboard
    5. Set TOGETHER_API_KEY environment variable
    """
    print("\n" + "=" * 80)
    print("Example 5: Together.ai (Llama 4 Scout) - $25 Free Credits")
    print("=" * 80)

    # Create primitive
    llm = TogetherAIPrimitive(
        model="meta-llama/Llama-4-Scout", api_key=os.getenv("TOGETHER_API_KEY")
    )

    # Create request
    context = WorkflowContext(workflow_id="together-demo")
    request = TogetherAIRequest(
        messages=[{"role": "user", "content": "Explain neural networks briefly."}]
    )

    # Execute
    response = await llm.execute(request, context)

    print(f"\n✅ Model: {response.model}")
    print(f"📝 Response: {response.content}")
    print(f"📊 Usage: {response.usage}")
    print(f"🎯 Quality: 88/100 (flagship)")
    print(f"💰 Cost: Uses free credits ($25 total)")


# ============================================================================
# Example 6: Fallback Chain - 100% Uptime with Free Flagship Models
# ============================================================================


async def example_fallback_chain():
    """Demonstrate 100% uptime using free flagship model fallback chain.

    **Strategy:**
    1. Primary: Google AI Studio (Gemini Pro) - Best free flagship
    2. Fallback 1: OpenRouter (DeepSeek R1) - Daily limits reset
    3. Fallback 2: Groq (Llama 3.3 70B) - Ultra-fast, high limits

    **Benefits:**
    - 100% uptime (if one provider is down, fallback to next)
    - All free flagship models
    - No credit card required
    - Automatic failover
    """
    print("\n" + "=" * 80)
    print("Example 6: Fallback Chain - 100% Uptime with Free Flagship Models")
    print("=" * 80)

    # Create fallback chain
    workflow = FallbackPrimitive(
        primary=GoogleAIStudioPrimitive(
            model="gemini-2.5-pro", api_key=os.getenv("GOOGLE_API_KEY")
        ),
        fallbacks=[
            OpenRouterPrimitive(
                model="deepseek/deepseek-r1:free", api_key=os.getenv("OPENROUTER_API_KEY")
            ),
            GroqPrimitive(
                model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY")
            ),
        ],
    )

    # Create request (using dict format for FallbackPrimitive)
    context = WorkflowContext(workflow_id="fallback-demo")
    request_data = GoogleAIStudioRequest(
        messages=[{"role": "user", "content": "What is the future of AI?"}]
    )

    # Execute
    response = await workflow.execute(request_data, context)

    print(f"\n✅ Model: {response.model}")
    print(f"📝 Response: {response.content}")
    print(f"📊 Usage: {response.usage}")
    print(f"🎯 Strategy: Free flagship fallback chain")
    print(f"💰 Cost: $0.00 (100% FREE)")
    print(f"⏱️  Uptime: 100% (automatic failover)")


# ============================================================================
# Main Function - Run All Examples
# ============================================================================


async def main():
    """Run all free flagship model examples."""
    print("\n" + "=" * 80)
    print("FREE FLAGSHIP MODEL ACCESS EXAMPLES")
    print("=" * 80)
    print("\nDemonstrating 5 free flagship model providers + fallback chain")
    print("All examples use 100% free models (except Together.ai with $25 credits)")

    # Run examples
    await example_google_ai_studio()
    await example_openrouter()
    await example_groq()
    await example_huggingface()
    await example_together_ai()
    await example_fallback_chain()

    print("\n" + "=" * 80)
    print("✅ All examples completed successfully!")
    print("=" * 80)
    print("\n📚 Next Steps:")
    print("1. Set up your API keys (see Quick Start Guide)")
    print("2. Run individual examples to test each provider")
    print("3. Implement fallback chain in your production app")
    print("4. Monitor usage and rate limits")
    print("\n💡 Pro Tip: Use the fallback chain for 100% uptime!")


if __name__ == "__main__":
    asyncio.run(main())

