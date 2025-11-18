"""ACE Phase 3: Generate comprehensive tests for RetryPrimitive.

This script uses ACE + E2B + LLM with source code injection to generate
production-ready tests for RetryPrimitive at zero cost.

Expected test coverage:
1. Success on first attempt (no retries)
2. Success after 1 retry
3. Success after 2 retries
4. Retry exhaustion (all attempts fail)
5. Backoff timing validation
6. RetryStrategy configuration
7. Error propagation
"""

import asyncio
import sys

# Add packages to path
sys.path.insert(0, "packages/tta-dev-primitives/src")

from tta_dev_primitives.ace.cognitive_manager import SelfLearningCodePrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Read RetryPrimitive source code to inject into prompts
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

# Read WorkflowContext and MockPrimitive for reference
TESTING_IMPORTS = """
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, RetryStrategy
from tta_dev_primitives.testing import MockPrimitive
import pytest
import asyncio
"""


async def main():
    """Generate RetryPrimitive tests with ACE Phase 3."""

    print("🎯 ACE + E2B: RetryPrimitive Test Generation (Phase 3)")
    print("=" * 70)
    print("Completing TODO: Add comprehensive tests for RetryPrimitive")
    print()
    print("Phase 3 Enhancements:")
    print("✅ Source code injection (prevents API hallucination)")
    print("✅ Iterative refinement (fixes errors automatically)")
    print("✅ Up to 3 iterations per scenario")
    print()
    print("=" * 70)
    print()

    # Initialize ACE self-learning primitive
    from pathlib import Path

    learner = SelfLearningCodePrimitive(
        playbook_file=Path("retry_primitive_tests_playbook_phase3.json")
    )
    context = WorkflowContext(correlation_id="retry-tests-phase3")

    # Test scenarios to generate
    scenarios = [
        {
            "name": "Core Retry Behavior",
            "task": "Create pytest tests for RetryPrimitive core retry behavior",
            "context": f"""Create comprehensive pytest tests that validate:
1. Success on first attempt (primitive succeeds immediately, no retries)
2. Success after 1 retry (primitive fails once, succeeds on second attempt)
3. Success after 2 retries (primitive fails twice, succeeds on third attempt)
4. Retry exhaustion (primitive always fails, all retries exhausted)

Use the actual RetryPrimitive API shown in the reference source code.

Reference Source Code:
{RETRY_PRIMITIVE_SOURCE}

Required Imports:
{TESTING_IMPORTS}

IMPORTANT: Use the exact API from the reference code:
- Constructor: RetryPrimitive(primitive=..., strategy=RetryStrategy(...))
- Method: await retry.execute(input_data, context)
- Use MockPrimitive for testing (NOT custom mock classes)
- MockPrimitive can be configured to fail N times then succeed
- Use pytest.raises() for testing exhaustion

Example MockPrimitive usage:
```python
# Success on first attempt
mock = MockPrimitive("test", return_value={{"result": "success"}})

# Fail once then succeed
mock = MockPrimitive("test", side_effect=[
    Exception("First attempt fails"),
    {{"result": "success"}}
])

# Always fail
mock = MockPrimitive("test", side_effect=Exception("Always fails"))
```
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

Use the actual RetryPrimitive API shown in the reference source code.

Reference Source Code:
{RETRY_PRIMITIVE_SOURCE}

Required Imports:
{TESTING_IMPORTS}

IMPORTANT: Use the exact API from the reference code:
- RetryStrategy(max_retries=..., backoff_base=..., max_backoff=..., jitter=...)
- Use asyncio.sleep() timing validation
- Use time.time() to measure actual backoff delays
- Test with jitter=False for predictable timing

Example timing validation:
```python
import time

start_time = time.time()
await retry.execute(input_data, context)
elapsed = time.time() - start_time

# Validate backoff timing (with tolerance for execution overhead)
expected_delay = 2.0  # backoff_base^attempt
assert abs(elapsed - expected_delay) < 0.5  # 500ms tolerance
```
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

    # Combine all tests into single file
    combined_tests = "\n\n".join(all_tests)

    # Write to test file
    test_file_path = "packages/tta-dev-primitives/tests/performance/test_retry_primitive_phase3.py"
    with open(test_file_path, "w") as f:
        f.write(f'''"""Comprehensive tests for RetryPrimitive (Phase 3).

Generated by ACE + E2B with iterative refinement.
Total scenarios: {len(scenarios)}
Strategies learned: {learner.playbook_size}
"""

{combined_tests}
''')

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
