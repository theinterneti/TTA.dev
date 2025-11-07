"""
ACE + E2B: RetryPrimitive Test Generation with Phase 4 Complete Context Engineering

This script demonstrates TTA.dev's context engineering excellence:
1. Target primitive (RetryPrimitive) - what we're testing
2. Critical dependencies (MockPrimitive, WorkflowContext) - what we need
3. Usage examples (how to use them together) - best practices

Expected: 90-100% test pass rate (up from 70% in Phase 3)
"""

import asyncio
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, "packages/tta-dev-primitives/src")

from tta_dev_primitives.ace.cognitive_manager import SelfLearningCodePrimitive
from tta_dev_primitives.core.base import WorkflowContext

# ============================================================================
# COMPLETE CONTEXT INJECTION (Phase 4: Context Engineering Excellence)
# ============================================================================

# 1. TARGET PRIMITIVE: RetryPrimitive
RETRY_PRIMITIVE_SOURCE = """
from dataclasses import dataclass

@dataclass
class RetryStrategy:
    max_retries: int = 3
    backoff_base: float = 2.0
    max_backoff: float = 60.0
    jitter: bool = True

    def calculate_delay(self, attempt: int) -> float:
        delay = min(self.backoff_base**attempt, self.max_backoff)
        if self.jitter:
            delay *= 0.5 + random.random()
        return delay

class RetryPrimitive(WorkflowPrimitive[Any, Any]):
    def __init__(
        self,
        primitive: WorkflowPrimitive,
        strategy: RetryStrategy | None = None,
    ) -> None:
        self.primitive = primitive
        self.strategy = strategy or RetryStrategy()

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        # Retries primitive up to max_retries times with exponential backoff
        # Returns result on success, raises last error on exhaustion
        ...
"""

# 2. CRITICAL DEPENDENCY: MockPrimitive
MOCK_PRIMITIVE_SOURCE = """
class MockPrimitive(WorkflowPrimitive[Any, Any]):
    def __init__(
        self,
        name: str,
        return_value: Any | None = None,
        side_effect: Callable | None = None,  # IMPORTANT: Callable, NOT list!
        raise_error: Exception | None = None,
    ) -> None:
        '''Initialize mock primitive.

        Args:
            name: Name of the mock
            return_value: Value to return (if no side_effect or error)
            side_effect: Function to call instead of returning value (NOT a list!)
            raise_error: Exception to raise when executed
        '''
        self.name = name
        self.return_value = return_value
        self.side_effect = side_effect
        self.raise_error = raise_error
        self.call_count = 0
        self.calls: list[tuple[Any, WorkflowContext]] = []

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        '''Execute mock primitive.'''
        self.call_count += 1
        self.calls.append((input_data, context))

        if self.raise_error:
            raise self.raise_error

        if self.side_effect:
            result = self.side_effect(input_data, context)
            if hasattr(result, "__await__"):
                return await result
            return result

        return self.return_value
"""

# 3. CRITICAL DEPENDENCY: WorkflowContext
WORKFLOW_CONTEXT_SOURCE = """
class WorkflowContext:
    def __init__(
        self,
        workflow_id: str | None = None,
        correlation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.workflow_id = workflow_id
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.metadata = metadata or {}
"""

# 4. USAGE EXAMPLES: How to use them together
USAGE_EXAMPLES = """
# Example 1: Mock that succeeds immediately
mock = MockPrimitive("test", return_value={"result": "success"})
retry = RetryPrimitive(primitive=mock, strategy=RetryStrategy(max_retries=3))
result = await retry.execute({"input": "data"}, WorkflowContext())

# Example 2: Mock that fails then succeeds (using side_effect as Callable)
call_count = 0
def side_effect_fn(input_data, context):
    nonlocal call_count
    call_count += 1
    if call_count == 1:
        raise Exception("First attempt fails")
    return {"result": "success"}

mock = MockPrimitive("test", side_effect=side_effect_fn)
retry = RetryPrimitive(primitive=mock, strategy=RetryStrategy(max_retries=3))
result = await retry.execute({"input": "data"}, WorkflowContext())

# Example 3: Mock that always fails
mock = MockPrimitive("test", raise_error=Exception("Always fails"))
retry = RetryPrimitive(primitive=mock, strategy=RetryStrategy(max_retries=2))
with pytest.raises(Exception, match="Always fails"):
    await retry.execute({"input": "data"}, WorkflowContext())
"""


async def main():
    """Generate RetryPrimitive tests with ACE Phase 4 (Complete Context)."""

    print("🎯 ACE + E2B: RetryPrimitive Test Generation (Phase 4)")
    print("=" * 70)
    print("PHASE 4: COMPLETE CONTEXT ENGINEERING")
    print()
    print("Context Injection:")
    print("✅ RetryPrimitive source code (target)")
    print("✅ MockPrimitive source code (critical dependency)")
    print("✅ WorkflowContext source code (critical dependency)")
    print("✅ Usage examples (best practices)")
    print()
    print("Expected: 90-100% pass rate (up from 70% in Phase 3)")
    print("=" * 70)
    print()

    # Initialize ACE self-learning primitive
    learner = SelfLearningCodePrimitive(
        playbook_file=Path("retry_primitive_tests_playbook_phase4.json")
    )
    context = WorkflowContext(correlation_id="retry-tests-phase4")

    # Test scenarios to generate
    scenarios = [
        {
            "name": "Core Retry Behavior",
            "task": "Create pytest tests for RetryPrimitive core retry behavior",
            "context": f"""Create comprehensive pytest tests that validate:
1. Success on first attempt (no retries needed)
2. Success after 1 retry (fails once, then succeeds)
3. Success after 2 retries (fails twice, then succeeds)
4. Retry exhaustion (all attempts fail, raises last error)

IMPORTANT CONTEXT:
{RETRY_PRIMITIVE_SOURCE}

{MOCK_PRIMITIVE_SOURCE}

{WORKFLOW_CONTEXT_SOURCE}

USAGE EXAMPLES:
{USAGE_EXAMPLES}

CRITICAL: Use side_effect as a Callable function, NOT a list!
""",
            "language": "python",
        },
        {
            "name": "Backoff Strategy Tests",
            "task": "Create pytest tests for RetryPrimitive backoff strategies",
            "context": f"""Create comprehensive pytest tests that validate:
1. Exponential backoff timing (backoff_base=2.0)
2. Linear backoff timing (backoff_base=1.0)
3. Constant backoff timing (backoff_base=1.0, max_backoff=1.0)
4. Jitter enabled vs disabled
5. Max backoff limit enforcement

IMPORTANT CONTEXT:
{RETRY_PRIMITIVE_SOURCE}

{MOCK_PRIMITIVE_SOURCE}

{WORKFLOW_CONTEXT_SOURCE}

USAGE EXAMPLES:
{USAGE_EXAMPLES}

CRITICAL: Use side_effect as a Callable function, NOT a list!
""",
            "language": "python",
        },
    ]

    all_tests = []

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'=' * 80}")
        print(f"SCENARIO {i}/{len(scenarios)}: {scenario['name']}")
        print(f"{'=' * 80}\n")

        # Execute with ACE
        result = await learner.execute(
            {
                "task": scenario["task"],
                "context": scenario["context"],
                "language": scenario["language"],
                "max_iterations": 3,
            },
            context,
        )

        print(f"\n✅ Scenario {i} complete!")
        print(f"   - Success: {result['execution_success']}")
        print(f"   - Code generated: {len(result.get('code_generated', ''))} chars")

        if result["execution_success"] and result.get("code_generated"):
            all_tests.append(f"# {scenario['name']}\n{result['code_generated']}")

    # Combine all tests
    combined_tests = "\n\n".join(all_tests)

    # Write to test file
    test_file_path = (
        "packages/tta-dev-primitives/tests/performance/test_retry_primitive_phase4.py"
    )
    with open(test_file_path, "w") as f:
        f.write(
            f'''"""Comprehensive tests for RetryPrimitive (Phase 4 - Complete Context).

Generated by ACE + E2B with complete context engineering.
Total scenarios: {len(scenarios)}
Strategies learned: {learner.playbook_size}
"""

{combined_tests}
'''
        )

    print(f"\n{'=' * 80}")
    print("✅ ALL SCENARIOS COMPLETE!")
    print(f"{'=' * 80}")
    print(f"\nTest file: {test_file_path}")
    print(f"Total scenarios: {len(scenarios)}")
    print(f"Strategies learned: {learner.playbook_size}")
    print(f"Success rate: {learner.success_rate:.1%}")
    print("\nRun tests with:")
    print(f"  uv run pytest {test_file_path} -v")


if __name__ == "__main__":
    asyncio.run(main())
