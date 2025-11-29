#!/usr/bin/env python3
"""
Test the debug template to isolate ML template issues.

Template: tta-debug-minimal (oefy20iwv272ehx2kqf4)
Includes: numpy only (minimal ML library)
Goal: Determine if issue is with specific ML libraries or general template approach
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path

import e2b_code_interpreter as eci


# Load environment variables from .env file
def load_env():
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


async def test_debug_template():
    """Test the debug template with minimal libraries."""
    print(f"🧪 Testing debug template at {datetime.now().strftime('%H:%M:%S')}")

    try:
        # Test 1: Basic sandbox creation
        print("📦 Creating sandbox with default code interpreter template")
        start_time = datetime.now()

        sandbox = await eci.AsyncSandbox.create()

        creation_time = (datetime.now() - start_time).total_seconds()
        print(f"✅ Sandbox created in {creation_time:.2f}s")

        # Wait a bit for the code interpreter to be ready
        print("⏳ Waiting for code interpreter to initialize...")
        await asyncio.sleep(5)

        # Test 2: Basic Python execution
        print("🐍 Testing basic Python execution...")
        execution = await sandbox.run_code("print('Hello from debug template!')")
        print(f"📝 Output: {execution.logs.stdout}")

        # Test 3: NumPy functionality
        print("🔢 Testing NumPy functionality...")
        numpy_code = """
import numpy as np

# Test NumPy installation and basic operations
print(f"NumPy version: {np.__version__}")

# Create a simple array
arr = np.array([1, 2, 3, 4, 5])
print(f"Array: {arr}")
print(f"Array sum: {np.sum(arr)}")
print("NumPy working correctly!")
"""

        execution = await sandbox.run_code(numpy_code)
        print(f"📊 NumPy test output:\n{execution.logs.stdout}")

        # Test 4: Environment check
        print("🔍 Checking environment...")
        env_code = """
import sys
import os

print(f"Python version: {sys.version}")
print(f"Platform: {sys.platform}")
print(f"Current directory: {os.getcwd()}")

# Check available packages
import pkg_resources
installed_packages = [d.project_name for d in pkg_resources.working_set]
print(f"Installed packages: {sorted(installed_packages)[:10]}...")  # First 10
"""

        execution = await sandbox.run_code(env_code)
        print(f"🌍 Environment info:\n{execution.logs.stdout}")

        # Test 5: Performance check
        print("⚡ Performance test...")
        perf_code = """
import time
import numpy as np

start = time.time()
# Simple NumPy operation
result = np.random.rand(1000).sum()
end = time.time()

print(f"Random array sum: {result:.4f}")
print(f"Computation time: {(end - start) * 1000:.2f}ms")
"""

        execution = await sandbox.run_code(perf_code)
        print(f"⚡ Performance result:\n{execution.logs.stdout}")

        await sandbox.kill()

        total_time = (datetime.now() - start_time).total_seconds()
        print(f"🎉 Debug template test completed successfully in {total_time:.2f}s")
        print("✅ Minimal template with NumPy works perfectly!")

        return True

    except Exception as e:
        print(f"❌ Debug template test failed: {e}")
        return False


async def main():
    """Main test runner."""
    print("🧪 E2B Debug Template Test")
    print("=" * 50)

    # Load environment variables
    load_env()

    # Check API key - try both E2B_KEY and E2B_API_KEY
    api_key = os.getenv("E2B_API_KEY") or os.getenv("E2B_KEY")
    if not api_key:
        print("❌ Neither E2B_API_KEY nor E2B_KEY found in environment")
        return

    # Set the expected environment variable
    os.environ["E2B_API_KEY"] = api_key

    success = await test_debug_template()

    print("\n" + "=" * 50)
    if success:
        print("🎯 CONCLUSION: Minimal template works - issue is with specific ML libraries")
        print("📋 NEXT STEP: Add libraries incrementally to find the culprit")
    else:
        print("🚨 CONCLUSION: Issue may be deeper than just ML libraries")


if __name__ == "__main__":
    asyncio.run(main())
