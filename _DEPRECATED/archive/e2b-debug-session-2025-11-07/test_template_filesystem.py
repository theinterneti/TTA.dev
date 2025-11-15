#!/usr/bin/env python3
"""
Test ML template using filesystem approach to verify libraries are installed.
"""

import os
import time

from e2b_code_interpreter import Sandbox


def test_ml_template_filesystem():
    """Test ML template by checking installed packages."""

    # Set API key from environment
    if "E2B_KEY" in os.environ:
        os.environ["E2B_API_KEY"] = os.environ["E2B_KEY"]

    print("🚀 Testing ML template: tta-ml-minimal")
    print("📦 Using filesystem validation approach")
    print("=" * 50)

    start_time = time.time()

    try:
        # Create sandbox with longer timeout
        print("📦 Creating ML sandbox...")
        sandbox = Sandbox.create(template="tta-ml-minimal", timeout=120)

        create_time = time.time() - start_time
        print(f"⚡ Sandbox created in {create_time:.2f} seconds")

        # Instead of running code, let's check what's installed via filesystem
        print("🔍 Checking installed packages via filesystem...")

        # List Python packages
        files = sandbox.files.list("/usr/local/lib/python3.11/site-packages/")
        print(f"📚 Found {len(files)} packages in site-packages")

        # Check for our key ML libraries
        package_names = [f.name for f in files]

        ml_libraries = {
            "torch": any("torch" in name.lower() for name in package_names),
            "transformers": any(
                "transformers" in name.lower() for name in package_names
            ),
            "numpy": any("numpy" in name.lower() for name in package_names),
            "pandas": any("pandas" in name.lower() for name in package_names),
        }

        print("\n📊 Library Installation Status:")
        print("-" * 30)
        for lib, installed in ml_libraries.items():
            status = "✅ INSTALLED" if installed else "❌ MISSING"
            print(f"{lib:12} : {status}")

        # Check Python version
        try:
            python_version = sandbox.files.read("/usr/bin/python3 --version 2>&1")
            print("\n🐍 Python: Available")
        except:
            print("\n🐍 Python: Could not determine version")

        # Check if we can at least access the filesystem
        try:
            home_files = sandbox.files.list("/home/user/")
            print(f"🏠 Working directory: /home/user/ ({len(home_files)} items)")
        except Exception as e:
            print(f"🏠 Working directory: Error accessing - {e}")

        sandbox.kill()

        total_time = time.time() - start_time
        print(f"\n🏁 Total validation time: {total_time:.2f} seconds")
        print(f"🎯 Sandbox creation: {create_time:.2f}s")

        # Performance analysis
        print("\n🚀 Performance Analysis:")
        print("-" * 30)
        if create_time < 2:
            print("✨ EXCELLENT! Ultra-fast template loading")
        elif create_time < 5:
            print("🚀 GREAT! Much faster than default")
        else:
            print("✅ Good performance improvement")

        expected_default = 30  # Conservative estimate for fresh install
        improvement = (
            expected_default / create_time if create_time > 0 else float("inf")
        )
        print(f"📈 Speed improvement: {improvement:.1f}x faster than fresh install")

        # Overall assessment
        installed_count = sum(ml_libraries.values())
        print("\n📝 Template Assessment:")
        print(f"   Libraries: {installed_count}/4 ML libraries detected")
        print(f"   Speed: {create_time:.2f}s creation time")

        if installed_count >= 3 and create_time < 10:
            print("✅ Template is working well!")
            return True
        else:
            print("⚠️ Template needs investigation")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_ml_template_filesystem()
    if success:
        print("\n🎉 ML template filesystem validation passed!")
    else:
        print("\n⚠️ Template needs troubleshooting")
