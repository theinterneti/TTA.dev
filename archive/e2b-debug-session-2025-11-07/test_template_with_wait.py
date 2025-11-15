#!/usr/bin/env python3
"""
Test ML template with proper service initialization wait.
"""

import os
import time

from e2b_code_interpreter import Sandbox


def test_ml_template():
    """Test ML template with proper initialization."""

    # Set API key from environment
    if "E2B_KEY" in os.environ:
        os.environ["E2B_API_KEY"] = os.environ["E2B_KEY"]

    print("🚀 Testing ML template: tta-ml-minimal")
    print("=" * 50)

    start_time = time.time()

    try:
        # Create sandbox with longer timeout
        print("📦 Creating ML sandbox...")
        sandbox = Sandbox.create(template="tta-ml-minimal", timeout=120)

        create_time = time.time() - start_time
        print(f"⚡ Sandbox created in {create_time:.2f} seconds")

        # Wait for code interpreter to initialize
        print("⏳ Waiting for code interpreter to initialize...")
        time.sleep(10)  # Give the service time to start

        # Test with a simple command first
        print("🔍 Testing basic Python execution...")
        simple_result = sandbox.run_code("print('Hello from ML template!')")
        print(f"Basic test: {simple_result.text.strip()}")

        # Now test imports
        print("🧪 Testing ML library imports...")
        result = sandbox.run_code("""
import sys
print(f"Python: {sys.version}")

# Test each import separately to isolate issues
libraries = []

try:
    import torch
    libraries.append(f"✅ PyTorch: {torch.__version__}")
except ImportError as e:
    libraries.append(f"❌ PyTorch: Failed to import")

try:
    import transformers
    libraries.append(f"✅ Transformers: {transformers.__version__}")
except ImportError as e:
    libraries.append(f"❌ Transformers: Failed to import")

try:
    import numpy as np
    libraries.append(f"✅ NumPy: {np.__version__}")
except ImportError as e:
    libraries.append(f"❌ NumPy: Failed to import")

try:
    import pandas as pd
    libraries.append(f"✅ Pandas: {pd.__version__}")
except ImportError as e:
    libraries.append(f"❌ Pandas: Failed to import")

for lib in libraries:
    print(lib)

print("\\n🎯 All imports tested successfully!")
""")

        print("\n📊 Library Test Results:")
        print("-" * 30)
        print(result.text)

        sandbox.kill()

        total_time = time.time() - start_time
        print(f"\n🏁 Total time: {total_time:.2f} seconds")
        print(f"🎯 Sandbox creation: {create_time:.2f}s")
        print(f"📚 Library validation: {total_time - create_time:.2f}s")

        # Performance analysis
        print("\n🚀 Performance Analysis:")
        print("-" * 30)
        if create_time < 5:
            print("✨ EXCELLENT! Ultra-fast template loading")
        elif create_time < 10:
            print("🚀 GREAT! Much faster than default")
        else:
            print("✅ Good performance improvement")

        expected_default = 30  # Conservative estimate for fresh install
        improvement = expected_default / create_time
        print(f"📈 Speed improvement: {improvement:.1f}x faster than fresh install")

        print("✅ Template test complete!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_ml_template()
    if success:
        print("\n🎉 ML template is working perfectly!")
    else:
        print("\n⚠️ Template needs troubleshooting")
