"""Example: Using the Development Lifecycle Meta-Framework.

This example demonstrates how to use the lifecycle primitives to assess
project readiness and guide users through stage transitions.
"""

import asyncio
from pathlib import Path

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.lifecycle import (
    STAGE_CRITERIA_MAP,
    Stage,
    StageManager,
    StageRequest,
)


async def assess_project_readiness() -> None:
    """Assess a project's readiness to transition stages."""
    # Path to the project we want to assess (current package)
    project_path = Path(__file__).parent.parent.parent

    print("\n" + "=" * 70)
    print("Development Lifecycle Meta-Framework Demo")
    print("=" * 70)

    # Create stage manager with predefined criteria
    manager = StageManager(stage_criteria_map=STAGE_CRITERIA_MAP)

    # Create workflow context
    context = WorkflowContext(
        workflow_id="lifecycle-assessment-demo",
        metadata={"project": "tta-dev-primitives"},
    )

    # Assess readiness: STAGING → DEPLOYMENT
    print("\n📊 Assessing readiness: STAGING → DEPLOYMENT\n")

    request = StageRequest(
        project_path=project_path,
        current_stage=Stage.STAGING,
        target_stage=Stage.DEPLOYMENT,
    )

    readiness = await manager.execute(context, request)

    # Print detailed assessment
    print(readiness.get_summary())

    # Demonstrate the transition method (don't actually transition)
    if not readiness.ready:
        print("\n🔍 What if we tried to transition anyway?")
        print("(This would normally raise StageTransitionError)")

        try:
            transition_result = await manager.transition(
                from_stage=Stage.STAGING,
                to_stage=Stage.DEPLOYMENT,
                project_path=project_path,
                context=context,
                force=False,  # Don't force - will raise error if not ready
            )
            print(transition_result.get_summary())
        except Exception as e:
            print(f"\n❌ Transition blocked (as expected): {e}")

    # Show how to force transition (not recommended!)
    print("\n💪 Forcing transition (override blockers - use with caution!):")
    forced_result = await manager.transition(
        from_stage=Stage.STAGING,
        to_stage=Stage.DEPLOYMENT,
        project_path=project_path,
        context=context,
        force=True,  # Force the transition
    )
    print(forced_result.get_summary())


if __name__ == "__main__":
    asyncio.run(assess_project_readiness())
