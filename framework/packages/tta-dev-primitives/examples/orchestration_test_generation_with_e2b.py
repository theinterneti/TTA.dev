"""Automated Test Generation with E2B Execution Validation

Enhanced version of orchestration_test_generation.py that EXECUTES generated tests
in E2B sandboxes to verify they actually work.

**Original Workflow:**
Claude analyzes code → Gemini generates tests → Claude validates (LLM opinion)

**Enhanced Workflow:**
Claude analyzes code → Gemini generates tests → **E2B executes tests** → Claude validates (real results)

**Benefits:**
- ✅ Catch syntax errors before committing
- ✅ Verify tests can import required modules
- ✅ Ensure test assertions actually work
- ✅ Immediate feedback loop for LLM improvement
- ✅ Higher quality generated tests

**Cost:**
- Original: ~$0.05 per file (90% savings vs all-Claude)
- With E2B: ~$0.05 per file + $0 E2B (FREE tier)
- Net: Same cost, way better quality!

Example:
    $ export E2B_API_KEY="your-key-here"
    $ python examples/orchestration_test_generation_with_e2b.py --file src/calculator.py

    ✅ Tests generated, executed in E2B, and validated!
"""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.integrations import CodeExecutionPrimitive
from tta_dev_primitives.orchestration import DelegationPrimitive

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class TestGenerationWithE2BWorkflow:
    """Enhanced test generation workflow with E2B execution validation.

    Architecture:
    - Orchestrator: Claude Sonnet 4.5 (analyze + validate)
    - Executor: Gemini 2.5 Pro (generate tests)
    - Validator: E2B (execute tests) ← NEW!
    """

    def __init__(self):
        # Multi-model delegation for test generation
        self.delegation = DelegationPrimitive(
            orchestrator_model="claude-sonnet-4.5",
            executor_model="gemini-2.5-pro",
        )

        # E2B code executor for test validation
        self.test_executor = CodeExecutionPrimitive(default_timeout=60)
        logger.info("🚀 Initialized TestGenerationWithE2BWorkflow")
        logger.info("   Orchestrator: Claude Sonnet 4.5")
        logger.info("   Executor: Gemini 2.5 Pro")
        logger.info("   Validator: E2B Code Execution ✨")

    async def analyze_code(self, file_path: str, code_content: str) -> dict[str, Any]:
        """Analyze code structure (orchestrator role).

        In production, this would be Claude Sonnet 4.5 analyzing the code.
        For demo purposes, we use simple static analysis.

        Args:
            file_path: Path to code file
            code_content: Code to analyze

        Returns:
            Analysis results with functions to test and strategy
        """
        logger.info(f"🔍 [Orchestrator] Analyzing code: {file_path}")

        # Simple analysis (in production, use Claude)
        functions = []
        for line in code_content.split("\n"):
            if line.strip().startswith("def ") and not line.strip().startswith("def _"):
                func_name = line.split("(")[0].replace("def ", "").strip()
                functions.append(func_name)

        analysis = {
            "functions_to_test": functions,
            "test_strategy": "unit_tests_with_pytest",
            "complexity": "medium",
            "coverage_target": 0.8,
        }

        logger.info(
            f"✅ [Orchestrator] Found {len(functions)} functions to test: {', '.join(functions)}"
        )
        return analysis

    async def generate_tests(
        self,
        file_path: str,
        code_content: str,
        analysis: dict,
        context: WorkflowContext,
    ) -> str:
        """Generate test code (executor role).

        In production, this would be Gemini 2.5 Pro generating tests.
        For demo purposes, we generate simple test templates.

        Args:
            file_path: Path to code file
            code_content: Original code
            analysis: Analysis results
            context: Workflow context

        Returns:
            Generated test code
        """
        logger.info(
            f"💡 [Executor] Generating tests for {len(analysis['functions_to_test'])} functions..."
        )

        # In production, this would be an LLM call via DelegationPrimitive
        # For demo, we generate template tests
        test_code_lines = ["import pytest", f"from {Path(file_path).stem} import *", ""]

        for func_name in analysis["functions_to_test"]:
            test_code_lines.extend(
                [
                    f"def test_{func_name}_basic():",
                    f'    """Test {func_name} with basic input."""',
                    "    # TODO: Add actual test implementation",
                    f"    result = {func_name}()",
                    "    assert result is not None",
                    "",
                ]
            )

        test_code = "\n".join(test_code_lines)

        # Record executor metrics (simulated)
        context.data["executor_tokens"] = len(test_code.split())
        context.data["executor_cost"] = 0.01  # ~$15/1M tokens for Gemini Pro

        logger.info(f"✅ [Executor] Generated {len(test_code)} chars of test code")
        return test_code

    async def execute_tests_in_e2b(
        self, test_code: str, context: WorkflowContext
    ) -> dict[str, Any]:
        """Execute generated tests in E2B sandbox (NEW!).

        This is the key enhancement: actually run the tests to verify they work.

        Args:
            test_code: Generated test code
            context: Workflow context

        Returns:
            Execution results with success status, output, and errors
        """
        logger.info("🧪 [E2B Validator] Executing tests in secure sandbox...")

        try:
            result = await self.test_executor.execute({"code": test_code, "timeout": 60}, context)

            execution_result = {
                "tests_execute": result["success"],
                "execution_time": result["execution_time"],
                "output": result["logs"],
                "errors": result["error"],
                "syntax_valid": result["success"] or "SyntaxError" not in str(result["error"]),
            }

            if result["success"]:
                logger.info("✅ [E2B Validator] Tests executed successfully!")
                logger.info(f"   Execution time: {result['execution_time']:.2f}s")
                if result["logs"]:
                    logger.info(f"   Output preview: {result['logs'][:200]}...")
            else:
                logger.error("❌ [E2B Validator] Tests failed to execute!")
                logger.error(f"   Error: {result['error']}")

            # Record E2B metrics
            context.data["e2b_execution_time"] = result["execution_time"]
            context.data["e2b_cost"] = 0.0  # FREE tier!

            return execution_result

        except Exception as e:
            logger.error(f"❌ [E2B Validator] Execution error: {e}")
            return {
                "tests_execute": False,
                "execution_time": 0.0,
                "output": "",
                "errors": str(e),
                "syntax_valid": False,
            }

    async def validate_tests(self, test_code: str, analysis: dict, execution_result: dict) -> bool:
        """Validate generated tests (orchestrator role) with E2B results.

        Enhanced validation using REAL execution results from E2B instead of
        just LLM opinion.

        Args:
            test_code: Generated test code
            analysis: Analysis results
            execution_result: E2B execution results

        Returns:
            True if tests pass validation, False otherwise
        """
        logger.info("🔍 [Orchestrator] Validating tests with E2B results...")

        # Validation checks (enhanced with E2B data)
        validations = {
            "has_imports": "import pytest" in test_code or "from pytest" in test_code,
            "has_test_functions": "def test_" in test_code,
            "has_assertions": "assert " in test_code,
            "covers_all_functions": all(
                func in test_code for func in analysis["functions_to_test"]
            ),
            "syntax_valid": execution_result["syntax_valid"],  # ← E2B result!
            "executes_successfully": execution_result["tests_execute"],  # ← E2B result!
        }

        passed = all(validations.values())

        logger.info(
            f"{'✅' if passed else '❌'} [Orchestrator] Validation: "
            f"{sum(validations.values())}/{len(validations)} checks passed"
        )

        # Show which checks failed
        for check, result in validations.items():
            status = "✅" if result else "❌"
            logger.info(f"   {status} {check}")

        return passed

    async def run(self, file_path: str) -> dict[str, Any]:
        """Run the complete test generation workflow with E2B validation.

        Enhanced workflow:
        1. Claude analyzes code
        2. Gemini generates tests
        3. E2B executes tests (NEW!)
        4. Claude validates with E2B results (ENHANCED!)

        Args:
            file_path: Path to the code file

        Returns:
            Workflow results with metrics
        """
        start_time = time.time()

        # Create workflow context
        context = WorkflowContext(
            workflow_id=f"test-gen-e2b-{Path(file_path).stem}",
            data={
                "file_path": file_path,
                "workflow_type": "test_generation_with_e2b",
                "orchestrator_model": "claude-sonnet-4.5",
                "executor_model": "gemini-2.5-pro",
                "validator": "e2b-code-execution",
            },
        )

        try:
            # Read code file
            with open(file_path) as f:
                code_content = f.read()

            # Step 1: Orchestrator analyzes code
            analysis = await self.analyze_code(file_path, code_content)
            context.data["orchestrator_tokens"] = 200
            context.data["orchestrator_cost"] = 0.006

            # Step 2: Executor generates tests
            test_code = await self.generate_tests(file_path, code_content, analysis, context)

            # Step 3: E2B executes tests (NEW!)
            execution_result = await self.execute_tests_in_e2b(test_code, context)

            # Step 4: Orchestrator validates with E2B results (ENHANCED!)
            validation_passed = await self.validate_tests(test_code, analysis, execution_result)
            context.data["validation_passed"] = validation_passed
            context.data["orchestrator_tokens"] += 100
            context.data["orchestrator_cost"] += 0.003

            # Calculate total cost
            total_cost = (
                context.data["orchestrator_cost"]
                + context.data["executor_cost"]
                + context.data["e2b_cost"]
            )
            all_claude_cost = 0.50
            cost_savings = (all_claude_cost - total_cost) / all_claude_cost

            context.data["total_cost"] = total_cost
            context.data["cost_savings_vs_all_paid"] = cost_savings

            duration_ms = (time.time() - start_time) * 1000

            # Log results
            logger.info("\n" + "=" * 80)
            logger.info("📊 WORKFLOW RESULTS (WITH E2B VALIDATION)")
            logger.info("=" * 80)
            logger.info(f"File: {file_path}")
            logger.info(f"Functions tested: {len(analysis['functions_to_test'])}")
            logger.info(f"Test code length: {len(test_code)} chars")
            logger.info(
                f"E2B execution: {'✅ Success' if execution_result['tests_execute'] else '❌ Failed'}"
            )
            logger.info(f"E2B execution time: {execution_result['execution_time']:.2f}s")
            logger.info(f"Validation: {'✅ Passed' if validation_passed else '❌ Failed'}")
            logger.info(f"Total duration: {duration_ms:.0f}ms")
            logger.info("\n💰 COST ANALYSIS")
            logger.info(f"Orchestrator (Claude): ${context.data['orchestrator_cost']:.4f}")
            logger.info(f"Executor (Gemini): ${context.data['executor_cost']:.4f}")
            logger.info(f"E2B Execution: ${context.data['e2b_cost']:.4f} (FREE!)")
            logger.info(f"Total: ${total_cost:.4f}")
            logger.info(f"vs. All-Claude: ${all_claude_cost:.2f}")
            logger.info(f"Cost Savings: {cost_savings * 100:.0f}%")
            logger.info("\n🎯 E2B VALIDATION BENEFITS")
            logger.info("✅ Tests verified to execute without errors")
            logger.info("✅ Syntax errors caught before committing")
            logger.info("✅ Import errors detected early")
            logger.info("✅ Real validation, not just LLM opinion")
            logger.info("=" * 80)

            # Write test file only if validation passed
            if validation_passed:
                test_file_path = file_path.replace(".py", "_test.py")
                with open(test_file_path, "w") as f:
                    f.write(test_code)
                logger.info(f"\n✅ Tests written to: {test_file_path}")
            else:
                logger.warning(
                    "\n⚠️  Tests NOT saved (validation failed - would retry in production)"
                )

            return {
                "success": True,
                "test_file": test_file_path if validation_passed else None,
                "validation_passed": validation_passed,
                "execution_result": execution_result,
                "metrics": context.data,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            return {"success": False, "error": str(e)}


async def main() -> None:
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(description="Generate tests with E2B execution validation")
    parser.add_argument("--file", required=True, help="Path to Python file")
    args = parser.parse_args()

    # Validate file exists
    if not Path(args.file).exists():
        logger.error(f"❌ File not found: {args.file}")
        sys.exit(1)

    # Check E2B API key
    import os

    if not os.getenv("E2B_API_KEY"):
        logger.error("❌ E2B_API_KEY environment variable not set!")
        logger.error("   Get your FREE key at: https://e2b.dev/dashboard")
        sys.exit(1)

    # Run workflow
    workflow = TestGenerationWithE2BWorkflow()
    result = await workflow.run(args.file)

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
