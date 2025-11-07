#!/usr/bin/env python3
"""
Quick test of our ML template.
"""

import os
import time

from e2b_code_interpreter import Sandbox


def test_ml_template():
    """Test ML template loading speed."""

    # Set API key from environment
    if "E2B_KEY" in os.environ:
        os.environ["E2B_API_KEY"] = os.environ["E2B_KEY"]

    print("🚀 Testing ML template: tta-ml-minimal")
    print("=" * 50)

    start_time = time.time()

    try:
        # Test sandbox creation speed
        print("📦 Creating ML sandbox...")
        sandbox = Sandbox.create(template="tta-ml-minimal", timeout=90)

        create_time = time.time() - start_time
        print(f"⚡ Sandbox created in {create_time:.2f} seconds")

        # Quick library check
        print("🧪 Testing imports...")
        result = sandbox.run_code("""
import sys
print(f"Python: {sys.version}")

try:
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
except ImportError as e:
    print(f"❌ PyTorch: {e}")

try:
    import transformers
    print(f"✅ Transformers: {transformers.__version__}")
except ImportError as e:
    print(f"❌ Transformers: {e}")

try:
    import numpy as np
    print(f"✅ NumPy: {np.__version__}")
except ImportError as e:
    print(f"❌ NumPy: {e}")

try:
    import pandas as pd
    print(f"✅ Pandas: {pd.__version__}")
except ImportError as e:
    print(f"❌ Pandas: {e}")
""")

        print("\n📊 Library Test Results:")
        print("-" * 30)
        print(result.text)

        sandbox.kill()

        total_time = time.time() - start_time
        print(f"\n🏁 Total time: {total_time:.2f} seconds")
        print(f"🎯 Startup: {create_time:.2f}s (vs ~30-60s fresh install)")

        # Performance verdict
        if create_time < 10:
            print("🚀 EXCELLENT! Super fast template loading")
        elif create_time < 20:
            print("✅ GOOD! Much faster than fresh install")
        else:
            print("⚠️ Slower than expected, but still working")

        print("✅ Template test complete!")

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True


if __name__ == "__main__":
    test_ml_template()
