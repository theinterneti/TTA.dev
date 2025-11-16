"""
Test Instrumented Workflow

Demonstrates PersonaMetricsCollector, WorkflowTracer, and LangfuseIntegration
usage with a multi-persona workflow example.

Features demonstrated:
- Prometheus metrics for persona tracking
- OpenTelemetry spans for workflow stages
- Langfuse LLM call tracing
- ObservableLLM wrapper for automatic instrumentation

Usage:
    python -m .hypertool.instrumentation.test_instrumented_workflow
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

load_dotenv()

# Import instrumentation
try:
    from observability_integration import initialize_observability

    OBSERVABILITY_AVAILABLE = True
except ImportError:
    print("⚠️  observability_integration not found - running without full APM")
    OBSERVABILITY_AVAILABLE = False

    def initialize_observability(**kwargs):
        pass


# Import our instrumentation
import os
import sys

# Add .hypertool to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from instrumentation import (
    ObservableLLM,
    PersonaMetricsCollector,
    WorkflowTracer,
    get_langfuse_integration,
)


# Mock LLM calls for testing
async def mock_llm_call(prompt: str) -> str:
    """
    Mock LLM call for testing ObservableLLM.

    In real usage, replace with actual LLM API call (OpenAI, Anthropic, etc.)
    """
    await asyncio.sleep(0.2)  # Simulate API latency
    return f"Mock LLM response for: {prompt}"


async def mock_backend_engineer_task(task: str, observable_llm: ObservableLLM) -> dict:
    """Simulate backend engineer work with ObservableLLM."""
    # Use ObservableLLM wrapper for automatic tracing
    response = await observable_llm(
        prompt=f"Implement backend for: {task}",
        persona="backend-engineer",
        chatmode="package-release",
    )

    await asyncio.sleep(0.3)  # Simulate additional work

    return {
        "status": "success",
        "result": response,
        "tokens_used": 850,
        "model": "gpt-4",
    }


async def mock_testing_specialist_task(
    task: str, observable_llm: ObservableLLM
) -> dict:
    """Simulate testing specialist work with ObservableLLM."""
    # Use ObservableLLM wrapper for automatic tracing
    response = await observable_llm(
        prompt=f"Create tests for: {task}",
        persona="testing-specialist",
        chatmode="package-release",
    )

    await asyncio.sleep(0.1)  # Simulate additional work

    return {
        "status": "success",
        "result": response,
        "tokens_used": 650,
        "model": "gpt-4",
    }


async def mock_devops_engineer_task(task: str, observable_llm: ObservableLLM) -> dict:
    """Simulate DevOps engineer work with ObservableLLM."""
    # Use ObservableLLM wrapper for automatic tracing
    response = await observable_llm(
        prompt=f"Deploy: {task}",
        persona="devops-engineer",
        chatmode="package-release",
    )

    await asyncio.sleep(0.2)  # Simulate additional work

    return {
        "status": "success",
        "result": response,
        "tokens_used": 550,
        "model": "gpt-4",
    }


async def package_release_workflow():
    """
    Example multi-persona workflow: Package Release

    Personas: backend-engineer → testing-specialist → devops-engineer
    Duration: ~30 minutes (simulated as 1.2 seconds)

    Demonstrates:
    - PersonaMetricsCollector for Prometheus metrics
    - WorkflowTracer for OpenTelemetry spans
    - LangfuseIntegration for LLM call tracing
    - ObservableLLM for automatic instrumentation
    """
    # Initialize APM
    if OBSERVABILITY_AVAILABLE:
        initialize_observability(
            service_name="hypertool-test", enable_prometheus=True, prometheus_port=9464
        )

    # Create separate Prometheus registry for tests to avoid metric conflicts
    try:
        from prometheus_client import CollectorRegistry

        test_registry = CollectorRegistry()
    except ImportError:
        test_registry = None

    # Get metrics collector with test registry
    collector = PersonaMetricsCollector(registry=test_registry)

    # Get Langfuse integration
    langfuse = get_langfuse_integration()

    # Create ObservableLLM wrapper
    observable_llm = ObservableLLM(
        llm_function=mock_llm_call,
        model="gpt-4-mini",
        langfuse=langfuse,
        metrics=collector,
    )

    print("🚀 Starting Package Release Workflow")
    print("=" * 60)

    # Start Langfuse trace for entire workflow
    workflow_trace = langfuse.start_trace(
        name="package-release-workflow",
        persona="multi-persona",
        chatmode="package-release",
        metadata={"version": "1.2.0"},
    )

    # Workflow execution with tracing
    async with WorkflowTracer(
        "package_release", metadata={"version": "1.2.0"}
    ) as tracer:
        # Stage 1: Version Bump (Backend Engineer)
        print("\n📝 Stage 1: Version Bump")
        print("   Persona: backend-engineer")

        # Record persona switch
        collector.switch_persona(None, "backend-engineer", "package-release")

        # Execute stage with tracing
        result1 = await tracer.trace_stage(
            "version_bump",
            "backend-engineer",
            mock_backend_engineer_task,
            "Update version to 1.2.0",
            observable_llm,  # Pass observable_llm to task
        )

        # Record token usage
        collector.record_token_usage(
            "backend-engineer",
            "package-release",
            result1["model"],
            result1["tokens_used"],
        )

        print(f"   ✅ {result1['result']}")
        print(f"   📊 Tokens: {result1['tokens_used']}")
        print(
            f"   💰 Budget remaining: {collector.get_remaining_budget('backend-engineer')}"
        )

        # Stage 2: Quality Validation (Testing Specialist)
        print("\n🧪 Stage 2: Quality Validation")
        print("   Persona: testing-specialist")

        # Record persona switch
        collector.switch_persona(
            "backend-engineer", "testing-specialist", "package-release"
        )

        # Execute stage with tracing
        result2 = await tracer.trace_stage(
            "quality_validation",
            "testing-specialist",
            mock_testing_specialist_task,
            "Run full test suite",
            observable_llm,  # Pass observable_llm to task
        )

        # Record token usage
        collector.record_token_usage(
            "testing-specialist",
            "package-release",
            result2["model"],
            result2["tokens_used"],
        )

        print(f"   ✅ {result2['result']}")
        print(f"   📊 Tokens: {result2['tokens_used']}")
        print(
            f"   💰 Budget remaining: {collector.get_remaining_budget('testing-specialist')}"
        )

        # Stage 3: Publish & Deploy (DevOps Engineer)
        print("\n🚀 Stage 3: Publish & Deploy")
        print("   Persona: devops-engineer")

        # Record persona switch
        collector.switch_persona(
            "testing-specialist", "devops-engineer", "package-release"
        )

        # Execute stage with tracing
        result3 = await tracer.trace_stage(
            "publish_deploy",
            "devops-engineer",
            mock_devops_engineer_task,
            "Publish to PyPI and deploy",
            observable_llm,  # Pass observable_llm to task
        )

        # Record token usage
        collector.record_token_usage(
            "devops-engineer",
            "package-release",
            result3["model"],
            result3["tokens_used"],
        )

        print(f"   ✅ {result3['result']}")
        print(f"   📊 Tokens: {result3['tokens_used']}")
        print(
            f"   💰 Budget remaining: {collector.get_remaining_budget('devops-engineer')}"
        )

    print("\n" + "=" * 60)
    print("✅ Package Release Workflow Complete!")
    print("\n📊 Workflow Summary:")
    print("   Total personas: 3")
    print(
        f"   Total tokens: {result1['tokens_used'] + result2['tokens_used'] + result3['tokens_used']}"
    )
    print(
        f"   Backend budget remaining: {collector.get_remaining_budget('backend-engineer')}"
    )
    print(
        f"   Testing budget remaining: {collector.get_remaining_budget('testing-specialist')}"
    )
    print(
        f"   DevOps budget remaining: {collector.get_remaining_budget('devops-engineer')}"
    )

    # End Langfuse trace
    langfuse.end_trace(workflow_trace, status="success")

    if OBSERVABILITY_AVAILABLE:
        print("\n📈 Metrics available at: http://localhost:9464/metrics")
        print("   Filter with: curl http://localhost:9464/metrics | grep hypertool")

    if langfuse.enabled:
        print("\n🔍 Langfuse tracing enabled!")
        print(f"   Host: {langfuse.host}")
        print("   Check Langfuse UI for LLM traces with persona context")
    else:
        print("\n⚠️  Langfuse not configured - LLM tracing disabled")
        print("   Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to enable")


async def main():
    """Run test workflow."""
    try:
        await package_release_workflow()

        print("\n✅ Test workflow completed successfully!")
        print("\nNext steps:")
        print("1. View Prometheus metrics: http://localhost:9464/metrics")
        print(
            "2. Query metrics: curl http://localhost:9464/metrics | grep hypertool_persona"
        )
        print("3. Check OpenTelemetry traces if OTLP exporter configured")
        print("4. View Langfuse traces if API keys configured (see Langfuse UI)")

    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
