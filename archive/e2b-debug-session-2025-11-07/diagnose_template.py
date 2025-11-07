#!/usr/bin/env python3
"""
Test default E2B template vs our custom template to isolate the issue.
"""

import os
import time

from e2b_code_interpreter import Sandbox


async def test_default_template():
    """Test if default E2B template works."""

    # Set API key from environment
    if "E2B_KEY" in os.environ:
        os.environ["E2B_API_KEY"] = os.environ["E2B_KEY"]

    print("🔍 Testing DEFAULT E2B template")
    print("=" * 50)

    start_time = time.time()

    try:
        # Create default sandbox (no template specified)
        print("📦 Creating default sandbox...")
        sandbox = Sandbox.create(timeout=120)

        create_time = time.time() - start_time
        print(f"⚡ Default sandbox created in {create_time:.2f} seconds")

        # Test basic execution
        print("🧪 Testing basic code execution...")
        result = sandbox.run_code("print('Hello from default template!')")
        print(f"✅ Default template result: {result.text.strip()}")

        # Test ML library import
        print("📚 Testing ML library import on default...")
        ml_result = sandbox.run_code("""
try:
    import torch
    print(f"PyTorch available: {torch.__version__}")
except ImportError:
    print("PyTorch not available - needs installation")
""")
        print(f"ML test result: {ml_result.text.strip()}")

        sandbox.kill()

        total_time = time.time() - start_time
        print(f"🏁 Default template total time: {total_time:.2f} seconds")
        return True

    except Exception as e:
        print(f"❌ Default template failed: {e}")
        return False


async def test_custom_template():
    """Test our custom ML template."""

    print("\n🔍 Testing CUSTOM ML template (tta-ml-minimal)")
    print("=" * 50)

    start_time = time.time()

    try:
        # Create our custom template sandbox
        print("📦 Creating custom ML sandbox...")
        sandbox = Sandbox.create(template="tta-ml-minimal", timeout=120)

        create_time = time.time() - start_time
        print(f"⚡ Custom sandbox created in {create_time:.2f} seconds")

        # Test basic execution
        print("🧪 Testing basic code execution...")
        result = sandbox.run_code("print('Hello from ML template!')")
        print(f"✅ Custom template result: {result.text.strip()}")

        sandbox.kill()

        total_time = time.time() - start_time
        print(f"🏁 Custom template total time: {total_time:.2f} seconds")
        return True

    except Exception as e:
        print(f"❌ Custom template failed: {e}")
        return False


def main():
    """Compare default vs custom template."""

    print("🚨 TEMPLATE DIAGNOSIS")
    print("Investigating why our custom template isn't working...")
    print("=" * 60)

    # Test default first
    default_works = test_default_template()

    # Test custom
    custom_works = test_custom_template()

    print("\n📊 DIAGNOSIS RESULTS")
    print("=" * 30)
    print(f"Default template: {'✅ WORKS' if default_works else '❌ BROKEN'}")
    print(f"Custom template:  {'✅ WORKS' if custom_works else '❌ BROKEN'}")

    if default_works and not custom_works:
        print("\n🔍 CONCLUSION: Our custom template broke the code interpreter service")
        print("📝 Next steps:")
        print("   1. Check our Dockerfile for service-breaking changes")
        print("   2. Rebuild template without breaking code interpreter")
        print("   3. Test incrementally (base → packages → config)")
    elif not default_works and not custom_works:
        print("\n🔍 CONCLUSION: E2B service issue (not our template)")
        print("📝 Next steps:")
        print("   1. Check E2B service status")
        print("   2. Verify API key and account limits")
        print("   3. Try different timeout values")
    elif default_works and custom_works:
        print("\n✅ CONCLUSION: Both templates work! Issue might be intermittent")
    else:
        print("\n❓ CONCLUSION: Unexpected result - investigate further")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
