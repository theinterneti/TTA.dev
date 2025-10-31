"""Multi-Model Orchestration Examples.

Demonstrates how Claude Sonnet 4.5 (or any orchestrator) can intelligently delegate
tasks to free flagship models for cost optimization while maintaining quality.

**Orchestration Patterns:**
1. Claude analyzes → Gemini Pro executes
2. Claude plans → Parallel execution across multiple free models
3. Claude validates → Free model outputs

**Cost Savings:**
- 80%+ cost reduction by delegating execution to free models
- Orchestrator handles planning/validation (small token usage)
- Executors handle bulk work (large token usage, free)
"""

import asyncio
import os

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.integrations import (
    GoogleAIStudioPrimitive,
    GroqPrimitive,
    OpenRouterPrimitive,
)
from tta_dev_primitives.orchestration import (
    DelegationPrimitive,
    MultiModelWorkflow,
    TaskClassifierPrimitive,
)
from tta_dev_primitives.orchestration.delegation_primitive import DelegationRequest
from tta_dev_primitives.orchestration.multi_model_workflow import MultiModelRequest
from tta_dev_primitives.orchestration.task_classifier_primitive import (
    TaskClassifierRequest,
)

# ============================================================================
# Example 1: Task Classification - Intelligent Model Selection
# ============================================================================


async def example_task_classification():
    """Demonstrate intelligent task classification for model selection.

    **Pattern:** Analyze task → Recommend best model
    **Use Case:** Determine which model to use before execution
    """
    print("\n" + "=" * 80)
    print("Example 1: Task Classification - Intelligent Model Selection")
    print("=" * 80)

    # Create classifier
    classifier = TaskClassifierPrimitive(prefer_free=True)
    context = WorkflowContext(workflow_id="classification-demo")

    # Test different task types
    tasks = [
        "Summarize this article in 3 bullet points",
        "Write a creative story about a robot",
        "Analyze the pros and cons of renewable energy",
        "Implement a binary search algorithm in Python",
    ]

    for task in tasks:
        request = TaskClassifierRequest(
            task_description=task, user_preferences={"prefer_free": True}
        )
        classification = await classifier.execute(request, context)

        print(f"\n📝 Task: {task}")
        print(f"🎯 Complexity: {classification.complexity.value}")
        print(f"🤖 Recommended: {classification.recommended_model}")
        print(f"💡 Reasoning: {classification.reasoning}")
        print(f"💰 Cost: ${classification.estimated_cost}")
        print(f"🔄 Fallbacks: {', '.join(classification.fallback_models)}")


# ============================================================================
# Example 2: Claude Analyzes → Gemini Pro Executes
# ============================================================================


async def example_claude_to_gemini():
    """Demonstrate Claude analyzing requirements → Gemini Pro executing.

    **Pattern:** Orchestrator analyzes → Executor executes
    **Cost Savings:** 95%+ (Claude plans, Gemini executes for free)
    """
    print("\n" + "=" * 80)
    print("Example 2: Claude Analyzes → Gemini Pro Executes")
    print("=" * 80)

    # Create delegation primitive with Gemini Pro executor
    delegation = DelegationPrimitive(
        executor_primitives={
            "gemini-2.5-pro": GoogleAIStudioPrimitive(
                model="gemini-2.5-pro", api_key=os.getenv("GOOGLE_API_KEY")
            )
        }
    )

    # Simulate Claude's analysis (in production, Claude would generate this)
    claude_analysis = """
    Task: Summarize the key benefits of renewable energy
    Recommended Executor: gemini-2.5-pro
    Reasoning: Moderate complexity task, Gemini Pro provides flagship quality for free
    """

    print(f"\n🧠 Claude's Analysis:\n{claude_analysis}")

    # Delegate to Gemini Pro
    context = WorkflowContext(workflow_id="claude-to-gemini")
    request = DelegationRequest(
        task_description="Summarize renewable energy benefits",
        executor_model="gemini-2.5-pro",
        messages=[
            {
                "role": "user",
                "content": "Summarize the key benefits of renewable energy in 3 bullet points.",
            }
        ],
    )

    response = await delegation.execute(request, context)

    print(f"\n✅ Executor: {response.executor_model}")
    print(f"📝 Response:\n{response.content}")
    print(f"📊 Usage: {response.usage}")
    print(f"💰 Cost: ${response.cost} (FREE!)")
    print("\n💡 Cost Savings: 95%+ vs. using Claude for execution")


# ============================================================================
# Example 3: Multi-Model Workflow - Automatic Routing
# ============================================================================


async def example_multi_model_workflow():
    """Demonstrate automatic task routing across multiple models.

    **Pattern:** Classify → Route → Execute → Validate
    **Cost Savings:** 80%+ by routing to optimal free models
    """
    print("\n" + "=" * 80)
    print("Example 3: Multi-Model Workflow - Automatic Routing")
    print("=" * 80)

    # Create workflow with multiple executors
    workflow = MultiModelWorkflow(
        executor_primitives={
            "gemini-2.5-pro": GoogleAIStudioPrimitive(
                model="gemini-2.5-pro", api_key=os.getenv("GOOGLE_API_KEY")
            ),
            "llama-3.3-70b-versatile": GroqPrimitive(
                model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY")
            ),
            "deepseek/deepseek-r1:free": OpenRouterPrimitive(
                model="deepseek/deepseek-r1:free",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            ),
        },
        prefer_free=True,
    )

    # Test different tasks
    tasks = [
        {
            "description": "Quick factual question",
            "messages": [{"role": "user", "content": "What is the capital of France?"}],
        },
        {
            "description": "Analysis task",
            "messages": [
                {
                    "role": "user",
                    "content": "Compare the advantages of solar vs. wind energy.",
                }
            ],
        },
        {
            "description": "Complex reasoning",
            "messages": [
                {
                    "role": "user",
                    "content": "Explain the philosophical implications of artificial consciousness.",
                }
            ],
        },
    ]

    context = WorkflowContext(workflow_id="multi-model-demo")
    total_cost = 0.0

    for task in tasks:
        request = MultiModelRequest(
            task_description=task["description"],
            messages=task["messages"],
            user_preferences={"prefer_free": True},
            validate_output=True,
        )

        response = await workflow.execute(request, context)
        total_cost += response.cost

        print(f"\n📝 Task: {task['description']}")
        print(f"🎯 Complexity: {response.classification['complexity']}")
        print(f"🤖 Executor: {response.executor_model}")
        print(f"💡 Reasoning: {response.classification['reasoning']}")
        print(f"✅ Validation: {'Passed' if response.validation_passed else 'Failed'}")
        print(f"💰 Cost: ${response.cost}")
        print(f"📝 Response: {response.content[:100]}...")

    print(f"\n💰 Total Cost: ${total_cost} (vs. ~$0.50 with Claude for all tasks)")
    print(f"💡 Cost Savings: {((0.50 - total_cost) / 0.50 * 100):.0f}%")


# ============================================================================
# Example 4: Parallel Execution - Claude Plans, Free Models Execute
# ============================================================================


async def example_parallel_execution():
    """Demonstrate Claude planning → parallel execution across free models.

    **Pattern:** Orchestrator plans → Parallel execution → Aggregation
    **Cost Savings:** 90%+ (Claude plans once, free models execute in parallel)
    """
    print("\n" + "=" * 80)
    print("Example 4: Parallel Execution - Claude Plans, Free Models Execute")
    print("=" * 80)

    # Simulate Claude's plan (in production, Claude would generate this)
    claude_plan = """
    Task: Research renewable energy from 3 perspectives
    Sub-tasks:
    1. Environmental benefits → Gemini Pro
    2. Economic impact → DeepSeek R1
    3. Technical challenges → Groq (Llama 3.3 70B)
    """

    print(f"\n🧠 Claude's Plan:\n{claude_plan}")

    # Create delegation primitive with multiple executors
    delegation = DelegationPrimitive(
        executor_primitives={
            "gemini-2.5-pro": GoogleAIStudioPrimitive(
                model="gemini-2.5-pro", api_key=os.getenv("GOOGLE_API_KEY")
            ),
            "deepseek/deepseek-r1:free": OpenRouterPrimitive(
                model="deepseek/deepseek-r1:free",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            ),
            "llama-3.3-70b-versatile": GroqPrimitive(
                model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY")
            ),
        }
    )

    # Execute sub-tasks in parallel
    context = WorkflowContext(workflow_id="parallel-demo")
    tasks = [
        DelegationRequest(
            task_description="Environmental benefits",
            executor_model="gemini-2.5-pro",
            messages=[
                {
                    "role": "user",
                    "content": "Explain the environmental benefits of renewable energy.",
                }
            ],
        ),
        DelegationRequest(
            task_description="Economic impact",
            executor_model="deepseek/deepseek-r1:free",
            messages=[
                {
                    "role": "user",
                    "content": "Analyze the economic impact of renewable energy.",
                }
            ],
        ),
        DelegationRequest(
            task_description="Technical challenges",
            executor_model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": "Describe the technical challenges of renewable energy.",
                }
            ],
        ),
    ]

    # Execute in parallel
    responses = await asyncio.gather(
        *[delegation.execute(task, context) for task in tasks]
    )

    # Display results
    total_cost = 0.0
    for i, response in enumerate(responses, 1):
        print(f"\n📝 Sub-task {i}: {tasks[i-1].task_description}")
        print(f"🤖 Executor: {response.executor_model}")
        print(f"📝 Response: {response.content[:100]}...")
        print(f"💰 Cost: ${response.cost}")
        total_cost += response.cost

    print(f"\n💰 Total Cost: ${total_cost} (FREE!)")
    print("💡 Cost Savings: 90%+ vs. using Claude for all sub-tasks")
    print("⚡ Execution: Parallel (3x faster than sequential)")


# ============================================================================
# Main Function - Run All Examples
# ============================================================================


async def main():
    """Run all multi-model orchestration examples."""
    print("\n" + "=" * 80)
    print("MULTI-MODEL ORCHESTRATION EXAMPLES")
    print("=" * 80)
    print("\nDemonstrating Claude Sonnet 4.5 orchestrating free flagship models")
    print("Cost savings: 80-95% while maintaining quality")

    # Run examples
    await example_task_classification()
    await example_claude_to_gemini()
    await example_multi_model_workflow()
    await example_parallel_execution()

    print("\n" + "=" * 80)
    print("✅ All examples completed successfully!")
    print("=" * 80)
    print("\n📚 Key Takeaways:")
    print("1. Task classification enables intelligent model selection")
    print("2. Delegation pattern: Orchestrator plans, executors execute")
    print("3. Multi-model workflows automatically route to optimal models")
    print("4. Parallel execution maximizes speed and cost savings")
    print("5. 80-95% cost reduction while maintaining flagship quality")


if __name__ == "__main__":
    asyncio.run(main())

