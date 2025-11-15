#!/usr/bin/env python3
"""
Test the updated E2B primitive after fixing the API usage.
"""

import asyncio
import os
from pathlib import Path

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.integrations import CodeExecutionPrimitive


def load_env():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


async def test_primitive():
    """Test the E2B primitive with corrected API usage."""
    print("🧪 Testing E2B CodeExecutionPrimitive")
    print("=" * 50)

    load_env()

    # Initialize primitive
    executor = CodeExecutionPrimitive()

    # Test simple code execution
    context = WorkflowContext(trace_id="test-001")

    test_code = """
print("Hello from E2B primitive!")
result = 2 + 2
print(f"2 + 2 = {result}")
"""

    try:
        print("🚀 Executing test code...")
        result = await executor.execute({"code": test_code, "timeout": 30}, context)

        print(f"✅ Success: {result['success']}")
        print(f"📝 Output: {result['output']}")
        print(f"⏱️ Execution time: {result['execution_time']:.3f}s")
        print(f"📋 Logs: {result['logs']}")

        if result["error"]:
            print(f"❌ Error: {result['error']}")

        return result["success"]

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

    finally:
        # Cleanup
        await executor.cleanup()


if __name__ == "__main__":
    success = asyncio.run(test_primitive())
    if success:
        print("\n🎉 E2B primitive test passed!")
    else:
        print("\n💥 E2B primitive test failed!")
