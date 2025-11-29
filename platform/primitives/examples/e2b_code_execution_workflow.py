#!/usr/bin/env python3
"""E2B Code Execution Integration Examples.

This module demonstrates how to integrate E2B secure code execution
with TTA.dev primitives for various real-world workflows:

1. Code Generation + Validation - AI generates code, E2B validates it
2. Multi-Agent Collaboration - One agent writes, another executes
3. Data Processing Pipeline - Complex transformations in isolation
4. Agent Tooling - Provide agents with computational capabilities

Requirements:
    - E2B_API_KEY environment variable set
    - e2b-code-interpreter package installed

Examples:
    python examples/e2b_code_execution_workflow.py
"""

import asyncio
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.integrations import CodeExecutionPrimitive
from tta_dev_primitives.observability import InstrumentedPrimitive
from tta_dev_primitives.recovery import RetryPrimitive, RetryStrategy

# ==============================================================================
# Example 1: Code Generation + Validation Workflow
# ==============================================================================


class CodeGeneratorPrimitive(InstrumentedPrimitive[dict, dict]):
    """Mock LLM that generates Python code based on requirements."""

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Generate code based on task description."""
        task = input_data.get("task", "")

        # In real implementation, this would call an LLM
        # For demo, we generate simple code based on task keywords
        if "fibonacci" in task.lower():
            code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
print(f"Fibonacci(10) = {result}")
"""
        elif "prime" in task.lower():
            code = """
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

primes = [n for n in range(2, 50) if is_prime(n)]
print(f"Primes under 50: {primes}")
"""
        elif "data" in task.lower():
            code = """
import json

data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
print(json.dumps(data, indent=2))
"""
        else:
            code = 'print("Hello from E2B!")'

        return {
            "code": code,
            "task": task,
            "language": "python",
        }


class CodeValidatorPrimitive(InstrumentedPrimitive[dict, dict]):
    """Validate code execution results."""

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Analyze execution results and provide validation."""
        success = input_data.get("success", False)
        output = input_data.get("output", "")
        logs = input_data.get("logs", [])
        error = input_data.get("error")

        # Validation logic
        validation = {
            "is_valid": success and not error,
            "has_output": bool(output or logs),
            "error_free": error is None,
            "execution_successful": success,
        }

        # Provide feedback
        if validation["is_valid"]:
            feedback = "✅ Code executed successfully!"
        elif error:
            feedback = f"❌ Execution error: {error}"
        else:
            feedback = "⚠️  Code executed but no output"

        return {
            **input_data,
            "validation": validation,
            "feedback": feedback,
        }


async def code_generation_validation_workflow():
    """Demonstrate code generation + validation workflow.

    Flow:
        1. Generate code based on task description (mock LLM)
        2. Execute code in E2B sandbox
        3. Validate execution results
        4. Provide feedback
    """
    print("\n" + "=" * 70)
    print("Example 1: Code Generation + Validation Workflow")
    print("=" * 70)

    # Build workflow: Generate → Execute → Validate
    workflow = (
        CodeGeneratorPrimitive()
        >> RetryPrimitive(  # Retry execution on transient failures
            primitive=CodeExecutionPrimitive(),
            strategy=RetryStrategy(max_retries=2, backoff_base=2.0),
        )
        >> CodeValidatorPrimitive()
    )

    # Test with different tasks
    tasks = [
        "Generate code to calculate fibonacci numbers",
        "Generate code to find prime numbers",
        "Generate code to process JSON data",
    ]

    for i, task in enumerate(tasks, 1):
        print(f"\n--- Task {i}: {task} ---")
        context = WorkflowContext(trace_id=f"code-gen-{i}")

        result = await workflow.execute({"task": task}, context)

        print(f"Generated Code:\n{result.get('code', 'N/A')[:200]}...")
        print("\nExecution Results:")
        print(f"  Success: {result['success']}")
        print(f"  Logs: {result['logs']}")
        print(f"  Validation: {result['validation']}")
        print(f"  Feedback: {result['feedback']}")


# ==============================================================================
# Example 2: Multi-Agent Collaboration
# ==============================================================================


class AgentCoderPrimitive(InstrumentedPrimitive[dict, dict]):
    """Agent specialized in writing code."""

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Write code based on requirements."""
        requirement = input_data.get("requirement", "")

        # Simulate agent generating code
        code = f"""
# Code generated by AgentCoder
# Requirement: {requirement}

def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result

test_data = [1, 2, 3, 4, 5]
output = process_data(test_data)
print(f"Input: {{test_data}}")
print(f"Output: {{output}}")
"""

        return {
            "code": code,
            "author": "AgentCoder",
            "requirement": requirement,
        }


class AgentExecutorPrimitive(InstrumentedPrimitive[dict, dict]):
    """Agent specialized in executing and testing code."""

    def __init__(self):
        super().__init__()
        self.executor = CodeExecutionPrimitive()

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Execute code and provide analysis."""
        # Execute the code
        execution_result = await self.executor.execute({"code": input_data["code"]}, context)

        # Analyze results
        analysis = {
            "passed": execution_result["success"],
            "output_lines": len(execution_result["logs"]),
            "has_errors": execution_result["error"] is not None,
            "recommendation": (
                "Code looks good!" if execution_result["success"] else "Code needs fixes"
            ),
        }

        return {
            **input_data,
            "execution": execution_result,
            "analysis": analysis,
        }


async def multi_agent_collaboration():
    """Demonstrate multi-agent collaboration with code execution.

    Flow:
        1. AgentCoder writes code
        2. AgentExecutor runs and analyzes it
        3. Results are combined
    """
    print("\n" + "=" * 70)
    print("Example 2: Multi-Agent Collaboration")
    print("=" * 70)

    # Build workflow: Code → Execute & Analyze
    workflow = AgentCoderPrimitive() >> AgentExecutorPrimitive()

    context = WorkflowContext(trace_id="multi-agent-001")
    result = await workflow.execute({"requirement": "Double all numbers in a list"}, context)

    print(f"\n📝 Code Author: {result['author']}")
    print(f"📋 Requirement: {result['requirement']}")
    print("\n🔬 Execution Analysis:")
    print(f"  Passed: {result['analysis']['passed']}")
    print(f"  Output Lines: {result['analysis']['output_lines']}")
    print(f"  Recommendation: {result['analysis']['recommendation']}")
    print("\n📊 Execution Logs:")
    for log in result["execution"]["logs"]:
        print(f"  {log}")


# ==============================================================================
# Example 3: Data Processing Pipeline
# ==============================================================================


class DataFetcherPrimitive(InstrumentedPrimitive[dict, dict]):
    """Fetch data that needs processing."""

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Simulate fetching data."""
        # In real scenario, this would fetch from API/database
        return {
            "raw_data": {
                "transactions": [
                    {"id": 1, "amount": 100.50, "category": "food"},
                    {"id": 2, "amount": 75.25, "category": "transport"},
                    {"id": 3, "amount": 200.00, "category": "food"},
                    {"id": 4, "amount": 50.00, "category": "entertainment"},
                ]
            }
        }


class DataProcessorPrimitive(InstrumentedPrimitive[dict, dict]):
    """Process data using E2B code execution."""

    def __init__(self):
        super().__init__()
        self.executor = CodeExecutionPrimitive()

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Generate and execute processing code."""
        # Generate processing code dynamically
        code = f"""
import json

# Data to process
data = {input_data["raw_data"]}

# Process: Calculate category totals
category_totals = {{}}
for txn in data['transactions']:
    category = txn['category']
    amount = txn['amount']
    category_totals[category] = category_totals.get(category, 0) + amount

# Output results
print(json.dumps(category_totals, indent=2))
"""

        # Execute in E2B
        result = await self.executor.execute({"code": code}, context)

        return {
            "raw_data": input_data["raw_data"],
            "processed": result,
        }


async def data_processing_pipeline():
    """Demonstrate data processing with E2B execution.

    Flow:
        1. Fetch raw data
        2. Generate processing code
        3. Execute in E2B sandbox
        4. Return processed results
    """
    print("\n" + "=" * 70)
    print("Example 3: Data Processing Pipeline")
    print("=" * 70)

    # Build pipeline: Fetch → Process (in E2B)
    pipeline = DataFetcherPrimitive() >> DataProcessorPrimitive()

    context = WorkflowContext(trace_id="data-pipeline-001")
    result = await pipeline.execute({}, context)

    print("\n📥 Raw Data:")
    print(f"  Transactions: {len(result['raw_data']['transactions'])}")

    print("\n⚙️  Processing Results:")
    print(f"  Success: {result['processed']['success']}")
    print(f"  Execution Time: {result['processed']['execution_time']:.3f}s")

    print("\n📤 Processed Output:")
    for log in result["processed"]["logs"]:
        print(f"  {log}")


# ==============================================================================
# Example 4: Agent with Computational Tools
# ==============================================================================


class ToolCallingAgentPrimitive(InstrumentedPrimitive[dict, dict]):
    """Agent that can use E2B as a computational tool."""

    def __init__(self):
        super().__init__()
        # E2B as the primary tool for code execution
        # Could add fallback to local execution if needed
        self.code_executor = CodeExecutionPrimitive()

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Process query and decide which tools to use."""
        query = input_data.get("query", "")

        # Determine if computational tool is needed
        needs_computation = any(
            keyword in query.lower()
            for keyword in ["calculate", "compute", "find", "sum", "average"]
        )

        if needs_computation:
            # Use E2B tool
            code = self._generate_code_for_query(query)
            tool_result = await self.code_executor.execute({"code": code}, context)

            return {
                "query": query,
                "tool_used": "code_executor",
                "result": tool_result,
                "answer": self._format_answer(query, tool_result),
            }
        else:
            # Use other tools (mock response)
            return {
                "query": query,
                "tool_used": "knowledge_base",
                "answer": "Retrieved from knowledge base",
            }

    def _generate_code_for_query(self, query: str) -> str:
        """Generate code based on query."""
        if "average" in query.lower():
            return """
numbers = [10, 20, 30, 40, 50]
average = sum(numbers) / len(numbers)
print(f"Average: {average}")
"""
        elif "fibonacci" in query.lower():
            return """
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
result = fib(15)
print(f"Fibonacci(15) = {result}")
"""
        else:
            return 'print("Computation completed")'

    def _format_answer(self, query: str, execution_result: dict) -> str:
        """Format execution results as natural language answer."""
        if execution_result["success"]:
            logs = " ".join(execution_result["logs"])
            return f"Based on computation: {logs}"
        else:
            return "Unable to compute result"


async def agent_with_tools():
    """Demonstrate agent using E2B as a computational tool.

    Flow:
        1. Agent receives query
        2. Decides which tool to use
        3. Uses E2B for computational queries
        4. Returns formatted answer
    """
    print("\n" + "=" * 70)
    print("Example 4: Agent with Computational Tools")
    print("=" * 70)

    agent = ToolCallingAgentPrimitive()
    context = WorkflowContext(trace_id="tool-agent-001")

    queries = [
        "Calculate the average of numbers",
        "What is fibonacci of 15?",
        "Tell me about Python",  # Won't use E2B
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i}: {query} ---")
        result = await agent.execute({"query": query}, context)

        print(f"Tool Used: {result['tool_used']}")
        print(f"Answer: {result['answer']}")


# ==============================================================================
# Main Demo Runner
# ==============================================================================


async def main():
    """Run all E2B integration examples."""
    print("\n" + "=" * 70)
    print("E2B Code Execution Integration Examples")
    print("Demonstrating secure code execution in TTA.dev workflows")
    print("=" * 70)

    try:
        # Run all examples
        await code_generation_validation_workflow()
        await multi_agent_collaboration()
        await data_processing_pipeline()
        await agent_with_tools()

        print("\n" + "=" * 70)
        print("✅ All examples completed successfully!")
        print("=" * 70)
        print("\nKey Takeaways:")
        print("  1. E2B integrates seamlessly with TTA.dev primitives")
        print("  2. Code execution happens in isolated sandboxes")
        print("  3. Automatic retry and fallback support")
        print("  4. Full observability through WorkflowContext")
        print("  5. Perfect for AI-generated code validation")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("\nMake sure E2B_API_KEY is set:")
        print("  export E2B_API_KEY=your_api_key_here")


if __name__ == "__main__":
    asyncio.run(main())
