"""Iterative Code Refinement with E2B Sandbox

Demonstrates the critical pattern: Generate → Execute → Fix → Repeat until working.

**The Problem:**
AI-generated code often fails on first attempt due to:
- Syntax errors
- Import errors
- Logic bugs
- Edge cases not handled

**The Solution:**
Use E2B sandbox execution results to iteratively improve code until it works.

**Pattern:**
1. Generate initial code (LLM)
2. Execute in E2B sandbox
3. If fails: Feed error back to LLM with context
4. LLM fixes the code
5. Repeat steps 2-4 until success (max 3 attempts)

**Cost:**
- Per iteration: ~$0.01 (LLM) + $0 (E2B FREE tier)
- Typical: 1-2 iterations = $0.01-$0.02 total
- Value: Working code instead of broken code!

Example:
    $ export E2B_API_KEY="your-key-here"  # pragma: allowlist secret
    $ python examples/e2b_iterative_code_refinement.py

    🔄 Iteration 1: Generated code with syntax error
    ❌ E2B execution failed: SyntaxError
    🔄 Iteration 2: Fixed syntax, now has import error
    ❌ E2B execution failed: ImportError
    🔄 Iteration 3: Fixed imports, code works!
    ✅ SUCCESS: Code executes correctly
"""

import asyncio
import logging
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.integrations import CodeExecutionPrimitive
from tta_dev_primitives.observability import InstrumentedPrimitive

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class CodeGeneratorPrimitive(InstrumentedPrimitive[dict, dict]):
    """Simulates LLM code generation with learning from errors.

    In production, this would be an actual LLM (GPT-4, Claude, Gemini).
    For demo, we simulate realistic code generation progression.
    """

    def __init__(self):
        super().__init__(name="code_generator")
        self.attempt = 0

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict[str, Any]:
        """Generate code, learning from previous errors."""
        self.attempt += 1
        requirement = input_data.get("requirement", "Calculate fibonacci")
        previous_error = input_data.get("previous_error")
        input_data.get("previous_code")

        logger.info(f"\n{'=' * 80}")
        logger.info(f"🤖 CODE GENERATOR - Attempt {self.attempt}")
        logger.info(f"{'=' * 80}")

        if previous_error:
            logger.info("📝 Learning from previous error:")
            logger.info(f"   {previous_error}")

        # Simulate realistic code generation progression
        if self.attempt == 1:
            # First attempt: Common beginner mistake (syntax error)
            code = """
def fibonacci(n):
    if n <= 1
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
print(f"Result: {result}")
"""
            logger.info("💭 Generating initial code (might have issues)...")

        elif self.attempt == 2:
            # Second attempt: Fix syntax, but introduce import error
            code = """
import nonexistent_module

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
print(f"Result: {result}")
"""
            logger.info("💭 Fixed syntax, adding unnecessary import...")

        else:
            # Third attempt: Working code!
            code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
print(f"Result: {result}")
"""
            logger.info("💭 Generating clean, working code...")

        logger.info(f"✅ Generated {len(code)} chars of code")
        return {"code": code, "requirement": requirement}


class CodeValidatorPrimitive(InstrumentedPrimitive[dict, dict]):
    """Validates E2B execution results and provides feedback."""

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict[str, Any]:
        """Check if code executed successfully."""
        execution_result = input_data.get("execution_result", {})
        code = input_data.get("code", "")

        success = execution_result.get("success", False)
        error = execution_result.get("error")
        logs = execution_result.get("logs", [])

        logger.info(f"\n{'=' * 80}")
        logger.info("🔍 VALIDATION RESULTS")
        logger.info(f"{'=' * 80}")

        if success:
            logger.info("✅ Code executed successfully!")
            logger.info(f"📊 Output: {logs}")
            logger.info(f"⏱️  Execution time: {execution_result.get('execution_time', 0):.2f}s")
            return {
                "valid": True,
                "code": code,
                "output": logs,
                "execution_time": execution_result.get("execution_time"),
            }
        else:
            logger.error("❌ Code execution failed!")
            logger.error(f"🐛 Error: {error}")
            return {
                "valid": False,
                "code": code,
                "error": error,
                "needs_refinement": True,
            }


class IterativeCodeRefinementWorkflow(InstrumentedPrimitive[dict, dict]):
    """Complete iterative refinement workflow.

    Keeps trying to generate working code until success or max attempts.
    """

    def __init__(self, max_attempts: int = 3):
        super().__init__(name="iterative_refinement_workflow")
        self.max_attempts = max_attempts
        self.generator = CodeGeneratorPrimitive()
        self.executor = CodeExecutionPrimitive(default_timeout=30)
        self.validator = CodeValidatorPrimitive()

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict[str, Any]:
        """Run iterative refinement loop."""
        requirement = input_data.get("requirement", "Calculate fibonacci(10)")

        logger.info(f"\n{'=' * 80}")
        logger.info("🚀 ITERATIVE CODE REFINEMENT WORKFLOW")
        logger.info(f"{'=' * 80}")
        logger.info(f"📋 Requirement: {requirement}")
        logger.info(f"🔄 Max attempts: {self.max_attempts}")
        logger.info(f"{'=' * 80}\n")

        current_input = {"requirement": requirement}

        for attempt in range(1, self.max_attempts + 1):
            logger.info(f"\n{'🔄' * 40}")
            logger.info(f"ITERATION {attempt}/{self.max_attempts}")
            logger.info(f"{'🔄' * 40}\n")

            # Step 1: Generate code (learning from previous errors)
            generation_result = await self.generator.execute(current_input, context)

            # Step 2: Execute in E2B sandbox
            logger.info(f"\n{'=' * 80}")
            logger.info("⚡ EXECUTING IN E2B SANDBOX")
            logger.info(f"{'=' * 80}")

            execution_result = await self.executor.execute(
                {"code": generation_result["code"], "timeout": 30}, context
            )

            # Step 3: Validate results
            validation_result = await self.validator.execute(
                {
                    "code": generation_result["code"],
                    "execution_result": execution_result,
                },
                context,
            )

            # Step 4: Check if we're done
            if validation_result["valid"]:
                logger.info(f"\n{'=' * 80}")
                logger.info("🎉 SUCCESS!")
                logger.info(f"{'=' * 80}")
                logger.info(f"✅ Working code generated in {attempt} iteration(s)")
                logger.info(f"💰 Estimated cost: ${0.01 * attempt:.2f}")
                logger.info(f"⏱️  Total execution time: {validation_result['execution_time']:.2f}s")
                logger.info(f"{'=' * 80}\n")

                return {
                    "success": True,
                    "code": validation_result["code"],
                    "output": validation_result["output"],
                    "attempts": attempt,
                    "cost_estimate": 0.01 * attempt,
                }

            # Step 5: Prepare feedback for next iteration
            if attempt < self.max_attempts:
                logger.info(f"\n{'⚠️ ' * 40}")
                logger.info(f"Attempt {attempt} failed, preparing for retry...")
                logger.info(f"{'⚠️ ' * 40}\n")

                current_input = {
                    "requirement": requirement,
                    "previous_error": validation_result["error"],
                    "previous_code": validation_result["code"],
                }
            else:
                logger.error(f"\n{'=' * 80}")
                logger.error("❌ MAX ATTEMPTS REACHED")
                logger.error(f"{'=' * 80}")
                logger.error(f"Failed to generate working code after {self.max_attempts} attempts")
                logger.error(f"Last error: {validation_result['error']}")
                logger.error(f"{'=' * 80}\n")

        return {
            "success": False,
            "error": "Max attempts reached without success",
            "attempts": self.max_attempts,
        }


async def demo_basic_refinement():
    """Demo: Basic iterative refinement."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 1: Basic Iterative Code Refinement")
    logger.info("=" * 80)

    workflow = IterativeCodeRefinementWorkflow(max_attempts=3)
    context = WorkflowContext(workflow_id="basic-refinement")

    result = await workflow.execute({"requirement": "Calculate fibonacci(10)"}, context)

    if result["success"]:
        logger.info("\n✅ Demo completed successfully!")
        logger.info(f"Final code:\n{result['code']}")
        logger.info(f"Output: {result['output']}")
    else:
        logger.error("\n❌ Demo failed")


async def demo_with_sequential_primitive():
    """Demo: Using SequentialPrimitive for the refinement loop."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 2: Sequential Primitive Pattern")
    logger.info("=" * 80)
    logger.info("Shows how to use TTA primitives for single iteration")
    logger.info("=" * 80 + "\n")

    # Single iteration workflow
    single_iteration = (
        CodeGeneratorPrimitive()
        >> CodeExecutionPrimitive(default_timeout=30)
        >> CodeValidatorPrimitive()
    )

    context = WorkflowContext(workflow_id="sequential-pattern")

    # In production, wrap this in a loop with retry logic
    result = await single_iteration.execute({"requirement": "Calculate fibonacci(10)"}, context)

    logger.info(f"\nSingle iteration result: {result.get('valid', False)}")


async def demo_real_world_use_case():
    """Demo: Real-world code generation scenario."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 3: Real-World Use Case - Data Processing")
    logger.info("=" * 80)
    logger.info("Generate code to process JSON data with error handling")
    logger.info("=" * 80 + "\n")

    workflow = IterativeCodeRefinementWorkflow(max_attempts=3)
    context = WorkflowContext(workflow_id="real-world-demo")

    result = await workflow.execute(
        {"requirement": "Parse JSON and extract user emails, handle missing fields gracefully"},
        context,
    )

    if result["success"]:
        logger.info("\n✅ Real-world scenario completed!")
        logger.info(f"Iterations needed: {result['attempts']}")
        logger.info(f"Cost: ${result['cost_estimate']:.2f}")


async def main():
    """Run all demos."""
    import os

    # Check E2B API key
    if not os.getenv("E2B_API_KEY"):
        logger.error("❌ E2B_API_KEY environment variable not set!")
        logger.error("   Get your FREE key at: https://e2b.dev/dashboard")
        return

    logger.info("\n" + "🚀" * 40)
    logger.info("E2B ITERATIVE CODE REFINEMENT EXAMPLES")
    logger.info("🚀" * 40 + "\n")

    # Run demos
    await demo_basic_refinement()
    await demo_with_sequential_primitive()
    await demo_real_world_use_case()

    logger.info("\n" + "=" * 80)
    logger.info("📚 KEY TAKEAWAYS")
    logger.info("=" * 80)
    logger.info("1. ✅ Always execute generated code in E2B before using it")
    logger.info("2. ✅ Feed execution errors back to LLM for refinement")
    logger.info("3. ✅ Use max_attempts to prevent infinite loops")
    logger.info("4. ✅ E2B FREE tier = $0 cost for validation")
    logger.info("5. ✅ 1-3 iterations typically sufficient for working code")
    logger.info("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
