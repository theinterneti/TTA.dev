"""Generate hierarchical traces showing the full agent execution model."""

import asyncio
import time

from ttadev.observability.agent_tracker import AgentContext, get_tracker


async def demo_hierarchical_trace():
    """
    Generate a realistic trace showing:
    User Request → Provider → Model → Agent → Workflow → Primitives → Tools
    """
    tracker = get_tracker()

    # Simulate: User thein asks GitHub Copilot (Claude Sonnet 4.5) to build an API
    print("🎯 Simulating: User asks to build REST API...")

    # 1. User initiates request
    user_context = AgentContext(
        provider="github_copilot",
        model="claude-sonnet-4.5",
        agent_role=None,  # Not using a TTA agent yet
        user="thein",
    )

    tracker.log_activity(
        activity_type="user_request",
        context=user_context,
        details={
            "request": "Build a REST API endpoint for user management",
            "timestamp": time.time(),
        },
    )

    await asyncio.sleep(0.5)

    # 2. AI decides to use backend-engineer agent
    backend_context = AgentContext(
        provider="github_copilot",
        model="claude-sonnet-4.5",
        agent_role="backend-engineer",
        user="thein",
    )

    tracker.log_activity(
        activity_type="agent_activated",
        context=backend_context,
        details={
            "agent": "backend-engineer",
            "reason": "Building REST API requires backend engineering expertise",
        },
    )

    await asyncio.sleep(0.3)

    # 3. Agent starts a workflow
    tracker.log_activity(
        activity_type="workflow_start",
        context=backend_context,
        details={
            "workflow": "build_rest_api",
            "steps": ["create_models", "create_routes", "add_tests"],
        },
    )

    await asyncio.sleep(0.2)

    # 4. Workflow uses primitives
    tracker.log_activity(
        activity_type="primitive_execution",
        context=backend_context,
        details={
            "primitive": "SequentialPrimitive",
            "steps": ["validate_schema", "generate_code", "run_tests"],
        },
    )

    await asyncio.sleep(0.3)

    # 5. Primitives use tools
    tracker.log_activity(
        activity_type="tool_call",
        context=backend_context,
        details={"tool": "create", "file": "api/routes/users.py", "lines": 145},
    )

    await asyncio.sleep(0.2)

    tracker.log_activity(
        activity_type="tool_call",
        context=backend_context,
        details={
            "tool": "bash",
            "command": "uv run pytest tests/api/test_users.py",
            "exit_code": 0,
        },
    )

    await asyncio.sleep(0.4)

    # 6. Switch to architect agent for design review
    print("🏗️  Switching to architect agent...")

    architect_context = AgentContext(
        provider="github_copilot", model="claude-sonnet-4.5", agent_role="architect", user="thein"
    )

    tracker.log_activity(
        activity_type="agent_activated",
        context=architect_context,
        details={"agent": "architect", "reason": "Review API design for scalability"},
    )

    await asyncio.sleep(0.3)

    tracker.log_activity(
        activity_type="workflow_start",
        context=architect_context,
        details={
            "workflow": "review_api_design",
            "focus": ["scalability", "security", "performance"],
        },
    )

    await asyncio.sleep(0.2)

    # 7. Skills used during review
    tracker.log_activity(
        activity_type="skill_used",
        context=architect_context,
        details={"skill": "api-design-patterns", "recommendation": "Add rate limiting and caching"},
    )

    await asyncio.sleep(0.3)

    # 8. Complete the request
    tracker.log_activity(
        activity_type="workflow_complete",
        context=architect_context,
        details={
            "workflow": "review_api_design",
            "status": "success",
            "files_modified": 3,
            "tests_passed": 12,
        },
    )

    print("✅ Hierarchical trace complete!")
    print(f"📊 Total activities logged: {len(tracker.get_recent_actions(limit=100))}")
    print(f"🤖 Active agents: {tracker.get_active_agents(since_minutes=5)}")


if __name__ == "__main__":
    asyncio.run(demo_hierarchical_trace())
