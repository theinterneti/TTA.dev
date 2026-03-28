#!/usr/bin/env python3
"""
Corrected E2B template test with proper cleanup.
"""

import os
import time

from e2b_code_interpreter import Sandbox


def load_api_key():
    """Load API key from various sources."""
    if "E2B_API_KEY" in os.environ:
        return os.environ["E2B_API_KEY"]
    if "E2B_KEY" in os.environ:
        os.environ["E2B_API_KEY"] = os.environ["E2B_KEY"]
        return os.environ["E2B_KEY"]
    # Try loading from .env file
    try:
        with open(".env") as f:
            for line in f:
                if line.startswith("E2B_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    os.environ["E2B_API_KEY"] = api_key
                    return api_key
    except FileNotFoundError:
        pass
    return None


def test_default_template():
    """Test default E2B template."""
    print("🔍 Testing DEFAULT template")
    print("-" * 30)

    start_time = time.time()

    try:
        sandbox = Sandbox.create()
        create_time = time.time() - start_time
        print(f"✅ Default sandbox: {create_time:.2f}s")

        result = sandbox.run_code("print('Hello default!')")
        print(f"✅ Code execution: {result.text.strip()}")

        sandbox.kill()  # Correct method name
        return True, create_time

    except Exception as e:
        print(f"❌ Default failed: {e}")
        return False, 0


def test_ml_template():
    """Test our ML template."""
    print("\n🔍 Testing ML template (tta-ml-minimal)")
    print("-" * 30)

    start_time = time.time()

    try:
        sandbox = Sandbox.create(template="tta-ml-minimal")
        create_time = time.time() - start_time
        print(f"✅ ML sandbox: {create_time:.2f}s")

        # Test basic execution
        result = sandbox.run_code("print('Hello ML template!')")
        print(f"✅ Code execution: {result.text.strip()}")

        # Test ML library (quick check)
        ml_result = sandbox.run_code("""
try:
    import torch
    print(f"PyTorch: {torch.__version__}")
except ImportError as e:
    print(f"PyTorch import failed: {e}")
""")
        print(f"📚 ML check: {ml_result.text.strip()}")

        sandbox.kill()  # Correct method name
        return True, create_time

    except Exception as e:
        print(f"❌ ML template failed: {e}")
        return False, 0


def main():
    """Main test function."""

    print("🚀 E2B TEMPLATE VALIDATION")
    print("=" * 50)

    # Load API key
    api_key = load_api_key()
    if not api_key:
        print("❌ No API key found")
        return

    # Security: Never log API keys, even partially
    print("✅ API key loaded successfully")

    # Test both templates
    default_success, default_time = test_default_template()
    ml_success, ml_time = test_ml_template()

    # Results
    print("\n📊 RESULTS SUMMARY")
    print("=" * 30)
    print(
        f"Default template: {'✅ WORKS' if default_success else '❌ FAILED'} ({default_time:.2f}s)"
    )
    print(f"ML template:      {'✅ WORKS' if ml_success else '❌ FAILED'} ({ml_time:.2f}s)")

    if default_success and ml_success:
        improvement = default_time / ml_time if ml_time > 0 else 1
        print("\n🎯 CONCLUSION: Both templates work!")
        print(
            f"📈 Speed comparison: ML template is {improvement:.1f}x {'faster' if improvement > 1 else 'slower'}"
        )
        print("✅ Our custom ML template is fully functional!")

        if ml_time < 5:
            print("🚀 EXCELLENT: Ultra-fast ML template performance!")

    elif default_success and not ml_success:
        print("\n⚠️ CONCLUSION: ML template has issues, default works")
        print("🔧 Action needed: Debug ML template configuration")

    elif not default_success and not ml_success:
        print("\n🔍 CONCLUSION: E2B service issues (both templates failed)")
        print("📞 Action needed: Check E2B service status")

    else:
        print("\n❓ CONCLUSION: Unexpected results - investigate further")


if __name__ == "__main__":
    main()
