#!/usr/bin/env python3
"""Test default template vs ML template to isolate the issue"""

import asyncio
import time

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.integrations.e2b_primitive import CodeExecutionPrimitive


async def test_default_vs_ml_template():
    """Compare default template vs ML template performance."""

    print("🧪 Testing Default vs ML Template")
    print("=" * 50)

    # Test 1: Default template
    print("\n📦 Test 1: Default Template")
    try:
        default_executor = CodeExecutionPrimitive(default_timeout=60)
        context = WorkflowContext(correlation_id="default-test")

        start_time = time.time()
        result = await default_executor.execute(
            {
                "code": "print('Hello from default template!')\nresult = 1 + 1\nprint(f'Result: {result}')",
                "timeout": 45,
            },
            context,
        )

        elapsed = time.time() - start_time
        print(f"✅ Default template result: {result}")
        print(f"⏱️ Time: {elapsed:.2f}s")

    except Exception as e:
        print(f"❌ Default template failed: {e}")

    # Test 2: ML template
    print("\n🤖 Test 2: ML Template")
    try:
        ml_executor = CodeExecutionPrimitive(
            template_id="tta-ml-minimal",  # Try using template name
            default_timeout=120,
        )
        context = WorkflowContext(correlation_id="ml-test")

        start_time = time.time()
        result = await ml_executor.execute(
            {
                "code": "print('Hello from ML template!')\nresult = 2 + 2\nprint(f'Result: {result}')",
                "timeout": 90,
            },
            context,
        )

        elapsed = time.time() - start_time
        print(f"✅ ML template result: {result}")
        print(f"⏱️ Time: {elapsed:.2f}s")

    except Exception as e:
        print(f"❌ ML template failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_default_vs_ml_template())
