#!/usr/bin/env python
"""Create a test trace in Langfuse to verify integration."""

import asyncio
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "tta-langfuse-integration" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "packages" / "tta-dev-primitives" / "src"))

from langfuse_integration import initialize_langfuse, LangfusePrimitive
from tta_dev_primitives.core.base import WorkflowContext


async def test_trace():
    """Create a test trace in Langfuse."""
    print("🔧 Initializing Langfuse...")
    initialize_langfuse()

    print("✅ Creating test workflow context...")
    context = WorkflowContext(
        workflow_id="test-workflow-123",
        correlation_id="test-correlation-456"
    )

    print("✅ Creating LangfusePrimitive...")
    llm = LangfusePrimitive(
        name="test_llm_call",
        metadata={"model": "gpt-4", "environment": "test"},
        user_id="test-user-789",
        tags=["test", "integration-check", "tta-dev"]
    )

    print("✅ Executing primitive with test data...")
    input_data = {
        "prompt": "This is a test prompt to verify Langfuse integration with TTA.dev"
    }

    # Simulate an LLM response
    result = {
        "response": "This is a test response demonstrating successful Langfuse integration!",
        "model": "gpt-4",
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 12,
            "total_tokens": 27
        },
        "cost": 0.00027  # Example cost
    }

    try:
        # Execute the primitive
        tracked_result = await llm.execute(input_data, context)
        
        print("✅ Primitive executed successfully!")
        print(f"\n📊 Trace Details:")
        print(f"   Workflow ID: {context.workflow_id}")
        print(f"   Correlation ID: {context.correlation_id}")
        print(f"   Operation: test_llm_call")
        print(f"   Model: gpt-4")
        print(f"   Tokens: 27 (15 input + 12 output)")
        print(f"   Cost: $0.00027")
        
        print(f"\n🎯 Expected in Langfuse:")
        print(f"   Session ID: {context.correlation_id}")
        print(f"   User ID: test-user-789")
        print(f"   Tags: test, integration-check, tta-dev")
        print(f"   Input: {input_data['prompt']}")
        print(f"   Output: {result['response']}")
        
        print(f"\n🌐 Check your Langfuse dashboard:")
        print(f"   URL: https://cloud.langfuse.com")
        print(f"   Look for trace: 'test_llm_call'")
        print(f"   Session ID: test-correlation-456")
        
        # Flush to ensure data is sent
        from langfuse_integration.initialization import get_langfuse_client
        client = get_langfuse_client()
        if client:
            print(f"\n🔄 Flushing data to Langfuse...")
            client.flush()
            print("✅ Data sent successfully!")
        
        print(f"\n🎉 Integration test complete!")
        return 0

    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(test_trace()))
