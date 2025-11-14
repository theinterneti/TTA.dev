#!/usr/bin/env python3
"""
Setup Langfuse Playground with Datasets and Evaluators

This script:
1. Creates test datasets for code, documentation, and tests
2. Registers custom evaluators
3. Runs sample evaluations

Usage:
    uv run python scripts/langfuse/setup_playground.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root / "packages" / "tta-langfuse-integration" / "src"))

from langfuse_integration import get_evaluator, initialize_langfuse
from langfuse_integration.playground import setup_all_datasets


def main():
    """Main execution function."""
    print("\n" + "=" * 60)
    print("🎮 TTA.dev Langfuse Playground Setup")
    print("=" * 60)

    # Initialize
    try:
        initialize_langfuse()
        print("✅ Langfuse initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        sys.exit(1)

    # Create datasets
    print("📊 Creating datasets...")
    try:
        result = setup_all_datasets()
        print(f"✅ {result['summary']}")
    except Exception as e:
        print(f"❌ Failed to create datasets: {e}")

    # Test evaluators
    print("\n🧪 Testing evaluators...")

    test_cases = [
        {
            "evaluator": "code",
            "input": 'def fibonacci(n: int) -> int:\n    """Calculate fibonacci."""\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)',
            "name": "Code with type hints and docstring",
        },
        {
            "evaluator": "docs",
            "input": "# Function\n\nThis function adds numbers.\n\n```python\nadd(1, 2)\n```",
            "name": "Basic documentation",
        },
        {
            "evaluator": "tests",
            "input": 'import pytest\n\ndef test_addition():\n    assert 1 + 1 == 2\n\ndef test_negative():\n    assert -1 + 1 == 0',
            "name": "Simple test suite",
        },
    ]

    for test in test_cases:
        try:
            evaluator = get_evaluator(test["evaluator"])
            result = evaluator.evaluate(test["input"])
            print(f"\n  {test['name']}:")
            print(f"    Score: {result['score']:.2f}")
            print(f"    {result['reasoning']}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")

    print("\n" + "=" * 60)
    print("🎉 Playground setup complete!")
    print("📊 Visit: https://cloud.langfuse.com")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
