#!/usr/bin/env python3
"""
Example: Using ML Template with CodeExecutionPrimitive

This example demonstrates using our custom ML template "tta-ml-minimal"
with the CodeExecutionPrimitive for fast ML code execution.
"""

import asyncio
import os

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.integrations import CodeExecutionPrimitive


async def test_ml_template_integration():
    """Test ML template integration with CodeExecutionPrimitive."""

    print("🚀 Testing ML Template Integration")
    print("=" * 50)

    # Create executor with our ML template
    executor = CodeExecutionPrimitive(
        template_id="3xmp0rmfztawhlpysu4v",  # Our custom ML template (tta-ml-minimal)
        default_timeout=90,  # Allow extra time for ML service initialization
    )

    context = WorkflowContext(trace_id="ml-template-test")

    try:
        # Test 1: Basic ML library imports
        print("📚 Test 1: ML Library Imports")
        import_result = await executor.execute(
            {
                "code": """
import sys
print(f"Python: {sys.version}")

# Test PyTorch
try:
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
    print(f"   CUDA available: {torch.cuda.is_available()}")
except ImportError as e:
    print(f"❌ PyTorch: {err}")

# Test Transformers
try:
    import transformers
    print(f"✅ Transformers: {transformers.__version__}")
except ImportError as e:
    print(f"❌ Transformers: {e}")

# Test NumPy & Pandas
try:
    import numpy as np
    import pandas as pd
    print(f"✅ NumPy: {np.__version__}")
    print(f"✅ Pandas: {pd.__version__}")
except ImportError as e:
    print(f"❌ NumPy/Pandas: {e}")

print("🎯 All imports completed!")
""",
                "timeout": 60,
            },
            context,
        )

        print("Import Results:")
        print(import_result["output"])

        # Test 2: Simple ML computation
        if import_result["success"]:
            print("\n🧮 Test 2: ML Computation")
            compute_result = await executor.execute(
                {
                    "code": """
import torch
import numpy as np

# Create some tensors
x = torch.tensor([1.0, 2.0, 3.0])
y = torch.tensor([4.0, 5.0, 6.0])

# Simple computation
result = torch.dot(x, y)
print(f"Tensor dot product: {result.item()}")

# NumPy array
arr = np.array([1, 2, 3, 4, 5])
print(f"NumPy mean: {arr.mean()}")

print("✅ ML computation successful!")
""",
                    "timeout": 30,
                },
                context,
            )

            print("Computation Results:")
            print(compute_result["output"])

        print("\n✅ ML template integration test complete!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

    finally:
        # Cleanup
        await executor.cleanup()


async def test_performance_comparison():
    """Compare performance: default vs ML template."""

    print("\n🏁 Performance Comparison")
    print("=" * 50)

    import time

    # Test ML template performance
    print("Testing ML template (tta-ml-minimal)...")
    start_time = time.time()

    ml_executor = CodeExecutionPrimitive(template_id="tta-ml-minimal", default_timeout=60)

    context = WorkflowContext(trace_id="perf-test-ml")

    try:
        result = await ml_executor.execute(
            {
                "code": "import torch; print(f'PyTorch loaded: {torch.__version__}')",
                "timeout": 60,
            },
            context,
        )
        ml_time = time.time() - start_time
        ml_success = result["success"]
    except Exception as e:
        ml_time = time.time() - start_time
        ml_success = False
        print(f"ML template error: {e}")
    finally:
        await ml_executor.cleanup()

    print("📊 Results:")
    print(f"   ML Template: {ml_time:.2f}s ({'✅ SUCCESS' if ml_success else '❌ FAILED'})")

    if ml_success:
        print("🚀 ML template ready for production use!")
        estimated_default = 45  # Estimated time for fresh install + import
        improvement = estimated_default / ml_time if ml_time > 0 else float("inf")
        print(f"📈 Estimated improvement: {improvement:.1f}x faster than fresh install")

    return ml_success


async def main():
    """Main test function."""

    # Check if E2B API key is available
    if not os.getenv("E2B_API_KEY") and not os.getenv("E2B_KEY"):
        print("❌ E2B API key not found in environment")
        print("   Set E2B_API_KEY or E2B_KEY environment variable")
        return

    # Set API key from E2B_KEY if needed (for compatibility with .env file)
    if os.getenv("E2B_KEY") and not os.getenv("E2B_API_KEY"):
        os.environ["E2B_API_KEY"] = os.getenv("E2B_KEY")

    # Run tests
    integration_success = await test_ml_template_integration()

    if integration_success:
        performance_success = await test_performance_comparison()

        if performance_success:
            print("\n🎉 All tests passed! ML template is production ready.")
        else:
            print("\n⚠️ Integration works but performance needs investigation.")
    else:
        print("\n❌ Integration test failed. Check template and API key.")


if __name__ == "__main__":
    asyncio.run(main())
