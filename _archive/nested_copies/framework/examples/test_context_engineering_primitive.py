"""
Test ContextEngineeringPrimitive

This validates that the context engineering primitive works correctly.
"""

import asyncio
import sys

# Add packages to path
sys.path.insert(0, "packages/tta-dev-primitives/src")

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.core.context_engineering import (
    ContextEngineeringPrimitive,
    ContextRequest,
)
from tta_dev_primitives.recovery.retry import RetryPrimitive


async def main():
    """Test context engineering primitive."""

    print("🎯 Testing ContextEngineeringPrimitive")
    print("=" * 70)
    print()

    # Create context engineer
    engineer = ContextEngineeringPrimitive(
        max_tokens=100_000,
        include_examples=True,
        validate_quality=True,
    )

    # Request context for RetryPrimitive test generation
    request: ContextRequest = {
        "task": "Generate pytest tests for RetryPrimitive",
        "target_class": RetryPrimitive,
        "task_type": "test_generation",
        "quality_threshold": 0.9,
    }

    print("Request:")
    print(f"  Task: {request['task']}")
    print(f"  Target: {request['target_class'].__name__}")
    print(f"  Type: {request['task_type']}")
    print()

    # Engineer context
    context = WorkflowContext(correlation_id="context-engineering-test")
    bundle = await engineer.execute(request, context)

    print("Results:")
    print(f"  Quality Score: {bundle.quality_score:.1%}")
    print(f"  Token Count: {bundle.token_count:,}")
    print(f"  Components: {len(bundle.components)}")
    print()

    print("Components Included:")
    for comp in bundle.components:
        print(f"  - {comp.name} ({comp.component_type}, priority={comp.priority})")
    print()

    if bundle.missing_components:
        print("Missing Components:")
        for missing in bundle.missing_components:
            print(f"  - {missing}")
        print()

    if bundle.recommendations:
        print("Recommendations:")
        for rec in bundle.recommendations:
            print(f"  - {rec}")
        print()

    # Show first 1000 chars of context
    print("Context Preview (first 1000 chars):")
    print("-" * 70)
    print(bundle.content[:1000])
    print("...")
    print("-" * 70)
    print()

    # Show section headers
    print("Context Sections:")
    for line in bundle.content.split("\n"):
        if line.startswith("#"):
            print(f"  {line}")
    print()

    # Validate quality
    if bundle.quality_score >= 0.9:
        print("✅ Quality threshold met!")
    else:
        print(f"⚠️  Quality below threshold: {bundle.quality_score:.1%} < 90%")

    print()
    print("=" * 70)
    print("✅ ContextEngineeringPrimitive test complete!")


if __name__ == "__main__":
    asyncio.run(main())
