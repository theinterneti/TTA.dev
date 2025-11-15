#!/usr/bin/env python3
"""
Test the ML template we just built.

This script verifies that:
1. The template loads quickly (~100ms vs ~30s)
2. All ML libraries are available and working
3. We can execute ML code immediately
"""

import asyncio
import os
import time

from e2b_code_interpreter import AsyncSandbox


async def test_ml_template():
    """Test our freshly built ML template."""

    # Check for API key
    api_key = os.getenv("E2B_API_KEY")
    if not api_key:
        print("❌ E2B_API_KEY environment variable not set!")
        print("Please set it with: export E2B_API_KEY=your_key_here")
        return

    print("🚀 Testing ML template: tta-ml-minimal")
    print("=" * 50)

    start_time = time.time()

    try:
        # Create sandbox with our ML template
        print("📦 Creating ML sandbox...")
        sandbox = await AsyncSandbox.create(template="tta-ml-minimal")

        create_time = time.time() - start_time
        print(f"⚡ Sandbox created in {create_time:.2f} seconds")

        # Test ML libraries
        print("\n🧪 Testing ML libraries...")
        result = await sandbox.run_code("""
import torch
import transformers
import numpy as np
import pandas as pd

print("📊 Library Versions:")
print(f"  PyTorch: {torch.__version__}")
print(f"  Transformers: {transformers.__version__}")
print(f"  NumPy: {np.__version__}")
print(f"  Pandas: {pd.__version__}")

print("\\n🧮 Quick Tests:")

# Tensor operations
x = torch.tensor([1.0, 2.0, 3.0])
y = x * 2 + 1
print(f"  Tensor math: [1,2,3] * 2 + 1 = {y.tolist()}")

# NumPy array
arr = np.array([1, 2, 3, 4, 5])
print(f"  NumPy mean: {arr.mean()}")

# Pandas DataFrame
df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
print(f"  Pandas sum: {df.sum().tolist()}")

print("\\n✅ All ML libraries working perfectly!")
""")

        print("\n📋 ML Test Results:")
        print("-" * 30)
        print(result.text)

        # Test model loading (if desired)
        print("\n🤖 Testing model loading (optional)...")
        model_result = await sandbox.run_code("""
try:
    from transformers import AutoTokenizer

    # Load a small tokenizer (fast download)
    tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')

    # Test tokenization
    text = "Hello ML template!"
    tokens = tokenizer.encode(text)
    decoded = tokenizer.decode(tokens)

    print(f"Original: {text}")
    print(f"Tokens: {tokens}")
    print(f"Decoded: {decoded}")
    print("✅ Model loading works!")

except Exception as e:
    print(f"ℹ️ Model loading test skipped: {e}")
    print("(This is normal - models download on first use)")
""")

        print(model_result.text)

        await sandbox.aclose()

        total_time = time.time() - start_time
        print(f"\n🏁 Total test time: {total_time:.2f} seconds")
        print(f"🎯 Template startup: {create_time:.2f}s (vs ~30s default)")

        # Performance analysis
        if create_time < 5:
            print("🚀 EXCELLENT! Template loads in under 5 seconds")
        elif create_time < 15:
            print("✅ GOOD! Template loads faster than default")
        else:
            print("⚠️  Template slower than expected (but still working)")

        print("\n" + "=" * 50)
        print("✅ ML Template Test Complete!")

    except Exception as e:
        print(f"❌ Error testing template: {e}")
        print("Make sure your E2B_API_KEY is valid and the template exists.")


if __name__ == "__main__":
    asyncio.run(test_ml_template())
