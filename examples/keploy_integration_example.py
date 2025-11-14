#!/usr/bin/env python3
"""Keploy Integration Example - Record and Replay TTA.dev Workflows

Demonstrates how to use Keploy primitives to:
1. Record workflow executions as test cases
2. Replay recorded tests for validation
3. Run test suites for regression testing

This enables automated test generation from real workflow usage!
"""

import asyncio

from tta_dev_primitives.core import SequentialPrimitive, WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive
from tta_dev_primitives.testing import (
    KeployRecordPrimitive,
    KeployReplayPrimitive,
    KeployTestSuitePrimitive,
    RecordingConfig,
)


# Example workflow to test
class TextProcessorPrimitive(InstrumentedPrimitive[dict, dict]):
    """Simple text processing primitive for demonstration."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Process text input.

        Args:
            input_data: {"text": str, "operation": str}
            context: Workflow context

        Returns:
            {"result": str, "length": int}
        """
        text = input_data.get("text", "")
        operation = input_data.get("operation", "uppercase")

        if operation == "uppercase":
            result = text.upper()
        elif operation == "lowercase":
            result = text.lower()
        elif operation == "reverse":
            result = text[::-1]
        elif operation == "wordcount":
            result = f"{len(text.split())} words"
        else:
            result = text

        return {"result": result, "length": len(result), "operation": operation}


async def example_record_workflow():
    """Example 1: Record workflow executions as test cases."""

    print("\n" + "=" * 70)
    print("Example 1: Recording Workflow Executions")
    print("=" * 70)

    # Create the workflow to test
    text_processor = TextProcessorPrimitive()

    # Wrap with recording primitive
    recorder = KeployRecordPrimitive(
        target_primitive=text_processor,
        config=RecordingConfig(
            test_name="text_processor_uppercase",
            output_dir="./keploy_tests",
            capture_context=True,
            capture_metrics=True,
        ),
    )

    # Execute and record
    print("\n📝 Recording test case: text_processor_uppercase")
    context = WorkflowContext(
        workflow_id="record-demo-1", agent_type="text-processor", workflow_name="Text Processing"
    )

    result = await recorder.execute(
        {"text": "hello world", "operation": "uppercase"}, context
    )

    print(f"   ✓ Test recorded: {result.test_name}")
    print(f"   ✓ Input: {result.input_data}")
    print(f"   ✓ Expected output: {result.expected_output}")
    print(f"   ✓ Saved to: ./keploy_tests/{result.test_name}.json")

    # Record another test case
    recorder2 = KeployRecordPrimitive(
        target_primitive=text_processor,
        config=RecordingConfig(test_name="text_processor_reverse", output_dir="./keploy_tests"),
    )

    print("\n📝 Recording test case: text_processor_reverse")
    result2 = await recorder2.execute({"text": "TTA.dev rocks!", "operation": "reverse"}, context)

    print(f"   ✓ Test recorded: {result2.test_name}")
    print(f"   ✓ Expected output: {result2.expected_output}")


async def example_replay_workflow():
    """Example 2: Replay recorded test cases."""

    print("\n" + "=" * 70)
    print("Example 2: Replaying Recorded Tests")
    print("=" * 70)

    # Create the workflow to test
    text_processor = TextProcessorPrimitive()

    # Create replay primitive
    replayer = KeployReplayPrimitive(target_primitive=text_processor, tests_dir="./keploy_tests")

    # Replay test 1
    print("\n🔄 Replaying test: text_processor_uppercase")
    context = WorkflowContext(workflow_id="replay-demo-1")

    result = await replayer.execute("text_processor_uppercase", context)

    print(f"   Test name: {result['test_name']}")
    print(f"   Passed: {'✅ YES' if result['passed'] else '❌ NO'}")
    print(f"   Actual output: {result['actual_output']}")
    print(f"   Expected output: {result['expected_output']}")

    # Replay test 2
    print("\n🔄 Replaying test: text_processor_reverse")
    result2 = await replayer.execute("text_processor_reverse", context)

    print(f"   Test name: {result2['test_name']}")
    print(f"   Passed: {'✅ YES' if result2['passed'] else '❌ NO'}")
    print(f"   Actual output: {result2['actual_output']}")


async def example_test_suite():
    """Example 3: Run a complete test suite."""

    print("\n" + "=" * 70)
    print("Example 3: Running Test Suite")
    print("=" * 70)

    # Create the workflow to test
    text_processor = TextProcessorPrimitive()

    # Create test suite primitive
    test_suite = KeployTestSuitePrimitive(
        target_primitive=text_processor, tests_dir="./keploy_tests"
    )

    # Run all tests
    print("\n🧪 Running all tests in ./keploy_tests/")
    context = WorkflowContext(workflow_id="suite-demo-1")

    results = await test_suite.execute({}, context)

    print(f"\n📊 Test Suite Results:")
    print(f"   Total tests: {results['total_tests']}")
    print(f"   Passed: {results['passed']}")
    print(f"   Failed: {results['failed']}")
    print(f"   Pass rate: {results['pass_rate']:.1%}")

    print(f"\n📋 Individual Test Results:")
    for i, test_result in enumerate(results["results"], 1):
        status = "✅" if test_result.get("passed") else "❌"
        print(f"   {status} Test {i}: {test_result.get('test_name')}")


async def example_workflow_integration():
    """Example 4: Integration with complex workflows."""

    print("\n" + "=" * 70)
    print("Example 4: Recording Complex Workflows")
    print("=" * 70)

    # Create a multi-step workflow
    step1 = TextProcessorPrimitive()
    step2 = TextProcessorPrimitive()
    workflow = step1 >> step2

    # Wrap entire workflow with recording
    recorder = KeployRecordPrimitive(
        target_primitive=workflow,
        config=RecordingConfig(
            test_name="multi_step_workflow", output_dir="./keploy_tests"
        ),
    )

    print("\n📝 Recording multi-step workflow")
    context = WorkflowContext(workflow_id="complex-demo-1", workflow_name="Multi-Step Text Processing")

    # Execute workflow (step1: uppercase, step2: reverse)
    # Note: This is simplified - in practice you'd need to handle sequential primitive chaining
    result = await recorder.execute({"text": "test", "operation": "uppercase"}, context)

    print(f"   ✓ Workflow recorded: {result.test_name}")
    print(f"   ✓ Test case saved")


async def example_ci_cd_integration():
    """Example 5: CI/CD Integration Pattern."""

    print("\n" + "=" * 70)
    print("Example 5: CI/CD Integration Pattern")
    print("=" * 70)

    print("\n💡 CI/CD Workflow:")
    print("   1. Developers use workflows normally")
    print("   2. KeployRecordPrimitive captures executions")
    print("   3. Tests committed to repo: ./keploy_tests/")
    print("   4. CI runs: KeployTestSuitePrimitive")
    print("   5. Automated regression testing ✅")

    print("\n📋 Example CI Script:")
    print("""
    # .github/workflows/test.yml
    - name: Run Keploy Test Suite
      run: |
        uv run python -c "
        from tta_dev_primitives.testing import KeployTestSuitePrimitive
        from my_app import my_workflow
        
        suite = KeployTestSuitePrimitive(
            target_primitive=my_workflow,
            tests_dir='./keploy_tests'
        )
        results = await suite.execute({}, context)
        
        if results['pass_rate'] < 1.0:
            exit(1)  # Fail build
        "
    """)


async def main():
    """Run all Keploy integration examples."""

    print("\n" + "=" * 70)
    print("TTA.dev Keploy Integration Examples")
    print("Automated Test Generation from Workflow Execution")
    print("=" * 70)

    # Example 1: Record workflow executions
    await example_record_workflow()

    # Example 2: Replay recorded tests
    await example_replay_workflow()

    # Example 3: Run test suite
    await example_test_suite()

    # Example 4: Complex workflow integration
    await example_workflow_integration()

    # Example 5: CI/CD integration pattern
    await example_ci_cd_integration()

    print("\n" + "=" * 70)
    print("Examples Complete!")
    print("=" * 70)

    print("\n💡 Key Benefits:")
    print("   1. Zero-effort test generation from real usage")
    print("   2. Automated regression testing")
    print("   3. CI/CD integration for quality gates")
    print("   4. Captures real execution context and metrics")
    print("   5. Works with any TTA.dev primitive")

    print("\n📚 Next Steps:")
    print("   - Record your production workflows")
    print("   - Commit tests to version control")
    print("   - Add to CI/CD pipeline")
    print("   - Monitor test pass rates over time")

    print("\n📁 Test Files Created:")
    print("   ./keploy_tests/text_processor_uppercase.json")
    print("   ./keploy_tests/text_processor_reverse.json")
    print("   ./keploy_tests/multi_step_workflow.json")


if __name__ == "__main__":
    asyncio.run(main())
