#!/usr/bin/env python3
"""Test the CodeExecutionPrimitive with our custom template."""

import asyncio
import os
import time

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.integrations.e2b_primitive import CodeExecutionPrimitive


async def test_primitive_with_template():
    """Test the primitive using our custom ML template."""

    print("🧪 Testing CodeExecutionPrimitive with tta-ml-minimal template")
    print("=" * 60)

    # Load API key - try both E2B_KEY and E2B_API_KEY
    api_key = os.getenv("E2B_KEY") or os.getenv("E2B_API_KEY")
    if not api_key:
        print("❌ Neither E2B_KEY nor E2B_API_KEY found in environment")
        return False

    print(f"✅ API key loaded: {api_key[:4]}...{api_key[-4:]}")

    # Create primitive with our template
    primitive = CodeExecutionPrimitive(
        template_id="3xmp0rmfztawhlpysu4v",  # tta-ml-minimal
        default_timeout=60,
    )

    context = WorkflowContext(correlation_id="test-primitive")

    start_time = time.time()

    try:
        # Test simple math
        print("\n🧮 Testing simple math...")
        result = await primitive.execute(
            {"code": "result = 1 + 1\nprint(f'Math result: {result}')", "timeout": 30},
            context,
        )

        print(f"✅ Simple math result: {result}")

        # Test ML imports
        print("\n🤖 Testing ML imports...")
        ml_code = """
import torch
import numpy as np
import pandas as pd
from transformers import pipeline

print(f"PyTorch version: {torch.__version__}")
print(f"NumPy version: {np.__version__}")
print(f"Pandas version: {pd.__version__}")

# Test basic functionality
tensor = torch.tensor([1, 2, 3])
array = np.array([4, 5, 6])
df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})

print(f"Tensor: {tensor}")
print(f"Array: {array}")
print(f"DataFrame shape: {df.shape}")
print("✅ All ML libraries working!")
"""

        result = await primitive.execute({"code": ml_code, "timeout": 45}, context)

        print(f"✅ ML test result: {result}")

        total_time = time.time() - start_time
        print(f"\n⏱️ Total test time: {total_time:.2f}s")
        print("🎉 All tests passed!")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Set up environment
    try:
        import python_dotenv

        python_dotenv.load_dotenv()
    except ImportError:
        pass  # dotenv not available, assume env vars are set

    success = asyncio.run(test_primitive_with_template())
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
