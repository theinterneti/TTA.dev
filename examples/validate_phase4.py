#!/usr/bin/env python3
"""
Phase 4 Validation Script

Validates the Autonomous Feature Development workflow using the ACE Benchmark Suite.
This script wraps `scripts/coordinator.py` and runs it against standard benchmarks.

Usage:
    python scripts/validate_phase4.py
"""

import asyncio
import logging
import os
import sys

# Add repo root to path to import scripts
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "platform/primitives/src"))

from tta_dev_primitives.ace import BenchmarkSuite
from tta_dev_primitives.ace.cognitive_manager import (
    ACEInput,
    ACEOutput,
    SelfLearningCodePrimitive,
)
from tta_dev_primitives.core.base import WorkflowContext

# Import the coordinator logic
# Add scripts directory to path to allow importing coordinator
scripts_dir = os.path.join(os.getcwd(), "scripts")
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)
from coordinator import execute_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("validate_phase4")


class AutonomousDevWrapper(SelfLearningCodePrimitive):
    """Wrapper for the Autonomous Dev Coordinator to fit ACE Benchmark interface."""

    def __init__(self):
        super().__init__()
        # Override metrics if needed, but base class has them

    async def execute(
        self, input_data: ACEInput, context: WorkflowContext
    ) -> ACEOutput:
        """Executes the task using the coordinator."""
        task = input_data["task"]
        logger.info(f"🧪 Benchmarking Task: {task}")

        # Run the coordinator
        # Note: execute_task is synchronous, so we run it directly.
        # In a real async app we might offload to thread.
        try:
            code = execute_task(task)
            success = bool(code)

            return {
                "result": code,
                "code_generated": code,
                "execution_success": success,
                "strategies_learned": 0,
                "playbook_size": 0,
                "improvement_score": 0.0,
                "learning_summary": "Autonomous execution completed.",
            }
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                "result": None,
                "code_generated": None,
                "execution_success": False,
                "strategies_learned": 0,
                "playbook_size": 0,
                "improvement_score": 0.0,
                "learning_summary": f"Failed: {e}",
            }


async def run_validation():
    print("🚀 Validating Phase 4: Autonomous Feature Development")
    print("=" * 60)

    # Initialize wrapper
    learner = AutonomousDevWrapper()

    # Initialize benchmark suite
    suite = BenchmarkSuite()

    # Filter for a subset of tasks to save time/tokens
    # Let's pick one easy and one medium task
    suite.tasks = [
        t for t in suite.tasks if t.id in ["easy_fibonacci", "medium_binary_search"]
    ]

    print(f"📋 Running {len(suite.tasks)} benchmark tasks...")

    # Create context
    context = WorkflowContext(correlation_id="phase4-validation")

    # Run benchmarks
    results = await suite.run_all_benchmarks(learner, context)

    # Print summary
    print("\n📊 Validation Results")
    print("=" * 60)

    passed = 0
    for res in results:
        status = "✅ PASS" if res.success else "❌ FAIL"
        print(f"{status} - {res.task_name}")
        if not res.success:
            print(f"  Reason: {res.error_message or 'Validation criteria not met'}")
            if res.code_generated:
                print(f"  Code Preview: {res.code_generated[:100]}...")
        else:
            passed += 1

    print("-" * 60)
    print(f"Total Passed: {passed}/{len(results)}")

    if passed == len(results):
        print(
            "\n🎉 Phase 4 Validation Successful! The Autonomous Agent produces valid code."
        )
    else:
        print("\n⚠️ Phase 4 Validation Failed. Check logs.")


if __name__ == "__main__":
    asyncio.run(run_validation())
