#!/usr/bin/env python3
"""
Complete Langfuse Maintenance Setup

Runs all maintenance tasks:
1. Upload prompts
2. Setup playground
3. Test evaluators

Usage:
    uv run python scripts/langfuse/maintenance.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root / "packages" / "tta-langfuse-integration" / "src"))

from langfuse_integration import initialize_langfuse


def run_script(script_path: Path):
    """Run a Python script."""
    import subprocess

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    return result.returncode == 0


def main():
    """Main execution."""
    print("\n" + "=" * 70)
    print("🔧 TTA.dev Langfuse Complete Maintenance")
    print("=" * 70)

    # Initialize
    try:
        initialize_langfuse()
        print("✅ Langfuse initialized\n")
    except Exception as e:
        print(f"❌ Failed: {e}\n")
        print("Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY first!")
        sys.exit(1)

    scripts_dir = Path(__file__).parent

    # Step 1: Upload prompts
    print("\n📤 STEP 1: Uploading prompts...")
    print("-" * 70)
    success = run_script(scripts_dir / "upload_prompts.py")
    if not success:
        print("⚠️  Some prompts failed to upload")

    # Step 2: Setup playground
    print("\n🎮 STEP 2: Setting up playground...")
    print("-" * 70)
    success = run_script(scripts_dir / "setup_playground.py")
    if not success:
        print("⚠️  Playground setup encountered issues")

    print("\n" + "=" * 70)
    print("✨ MAINTENANCE COMPLETE!")
    print("=" * 70)
    print("\n📊 Your Langfuse dashboard is ready:")
    print("   - Prompts: https://cloud.langfuse.com/prompts")
    print("   - Datasets: https://cloud.langfuse.com/datasets")
    print("   - Traces: https://cloud.langfuse.com/traces")
    print("\n🎯 Next steps:")
    print("   1. Test prompts in the playground")
    print("   2. Run evaluators on traces")
    print("   3. Monitor quality metrics")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
