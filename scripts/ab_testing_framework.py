"""
A/B Testing Framework for TTA.dev Primitives using e2b

This script provides a framework for A/B testing TTA.dev primitives to ensure
they work effectively across multiple AI agents and models.
"""

import asyncio
import logging
from typing import Any, Dict, List

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.integrations import CodeExecutionPrimitive
from tta_dev_primitives.observability import InstrumentedPrimitive

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class A_B_TestRunner(InstrumentedPrimitive[Dict, Dict]):
    """
    A primitive that runs a single A/B test case in an e2b sandbox.
    """

    def __init__(self):
        super().__init__(name="a_b_test_runner")
        self.executor = CodeExecutionPrimitive(default_timeout=60)

    async def _execute_impl(self, input_data: Dict, context: WorkflowContext) -> Dict[str, Any]:
        """
        Executes a single A/B test case.
        """
        test_code = input_data.get("test_code")
        test_name = input_data.get("test_name")

        logger.info(f"Running A/B test: {test_name}")

        execution_result = await self.executor.execute(
            {"code": test_code, "timeout": 60}, context=context
        )

        return {
            "test_name": test_name,
            "success": execution_result.get("success", False),
            "error": execution_result.get("error"),
            "logs": execution_result.get("logs", []),
            "execution_time": execution_result.get("execution_time", 0),
        }


async def main():
    """
    Main function to run the A/B testing framework.
    """
    logger.info("Starting A/B testing framework...")

    # TODO: Define test cases for each primitive
    test_cases = [
        {
            "test_name": "RouterPrimitive - Basic Routing",
            "test_code": """
from tta_dev_primitives import RouterPrimitive, WorkflowContext

async def test():
    routes = {
        "fast": lambda data, ctx: {"result": "fast"},
        "slow": lambda data, ctx: {"result": "slow"},
    }
    router = RouterPrimitive(routes=routes, router_fn=lambda data, ctx: "fast")
    result = await router.execute({}, WorkflowContext())
    assert result["result"] == "fast"
    print("Test passed!")

import asyncio
asyncio.run(test())
""",
        },
        {
            "test_name": "RetryPrimitive - Successful Retry",
            "test_code": """
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives import WorkflowContext
import asyncio

class UnreliablePrimitive:
    def __init__(self):
        self.attempts = 0

    async def execute(self, data, ctx):
        self.attempts += 1
        if self.attempts < 3:
            raise ValueError("Service unavailable")
        return {"result": "success"}

async def test():
    unreliable = UnreliablePrimitive()
    retry = RetryPrimitive(primitive=unreliable, max_retries=3, initial_delay=0.1)
    result = await retry.execute({}, WorkflowContext())
    assert result["result"] == "success"
    assert unreliable.attempts == 3
    print("Test passed!")

asyncio.run(test())
""",
        },
        {
            "test_name": "CachePrimitive - Cache Hit",
            "test_code": """
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives import WorkflowContext
import asyncio

class ExpensivePrimitive:
    def __init__(self):
        self.calls = 0

    async def execute(self, data, ctx):
        self.calls += 1
        return {"result": "expensive result"}

async def test():
    expensive = ExpensivePrimitive()
    cached = CachePrimitive(primitive=expensive, ttl_seconds=60)
    
    # First call, should execute the primitive
    result1 = await cached.execute({}, WorkflowContext())
    assert expensive.calls == 1
    
    # Second call, should hit the cache
    result2 = await cached.execute({}, WorkflowContext())
    assert expensive.calls == 1
    
    assert result1 == result2
    print("Test passed!")

asyncio.run(test())
""",
        },
    ]

    test_runner = A_B_TestRunner()
    context = WorkflowContext(workflow_id="ab-testing")

    results = []
    for test_case in test_cases:
        result = await test_runner.execute(test_case, context)
        results.append(result)

    logger.info("A/B testing complete.")
    logger.info("Results:")
    for result in results:
        logger.info(f"  - {result['test_name']}: {'Success' if result['success'] else 'Failure'}")
        if not result["success"]:
            logger.error(f"    Error: {result['error']}")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    if not os.getenv("E2B_API_KEY"):
        logger.error("E2B_API_KEY environment variable not set.")
    else:
        asyncio.run(main())
