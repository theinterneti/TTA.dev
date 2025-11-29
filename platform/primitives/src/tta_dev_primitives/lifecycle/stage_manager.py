"""Stage manager primitive for orchestrating lifecycle transitions.

This module provides the StageManager primitive that validates project
readiness and manages transitions between lifecycle stages.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.lifecycle.stage import Stage, StageTransitionError
from tta_dev_primitives.lifecycle.stage_criteria import (
    StageCriteria,
    StageReadiness,
    TransitionResult,
)
from tta_dev_primitives.lifecycle.validation import (
    ReadinessCheckPrimitive,
    ReadinessCheckResult,
)


@dataclass
class StageRequest:
    """Request to check readiness or transition between stages.

    Attributes:
        project_path: Path to project root
        current_stage: Current lifecycle stage
        target_stage: Target lifecycle stage
        force: Whether to force transition even with blockers
    """

    project_path: Path
    current_stage: Stage
    target_stage: Stage
    force: bool = False


class StageManager(WorkflowPrimitive[StageRequest, StageReadiness]):
    """Manages lifecycle stages and validates project readiness.

    This primitive orchestrates stage transitions by:
    1. Validating exit criteria for current stage
    2. Validating entry criteria for target stage
    3. Running all validation checks in parallel
    4. Providing detailed feedback and recommendations

    Example:
        ```python
        from tta_dev_primitives.lifecycle import (
            StageManager,
            Stage,
            StageRequest,
        )
        from pathlib import Path

        manager = StageManager(stage_criteria_map={
            Stage.TESTING: testing_criteria,
            Stage.STAGING: staging_criteria,
        })

        request = StageRequest(
            project_path=Path("my-project"),
            current_stage=Stage.TESTING,
            target_stage=Stage.STAGING,
        )

        readiness = await manager.execute(WorkflowContext(), request)
        if not readiness.ready:
            print("Not ready! Fix these blockers:")
            for blocker in readiness.blockers:
                print(f"  - {blocker.message}")
        ```
    """

    def __init__(self, stage_criteria_map: dict[Stage, StageCriteria] | None = None) -> None:
        """Initialize stage manager.

        Args:
            stage_criteria_map: Map of stages to their criteria.
                If None, uses default criteria defined in stages module.
        """
        super().__init__()
        self.stage_criteria_map = stage_criteria_map or {}

    async def execute(self, context: WorkflowContext, input_data: StageRequest) -> StageReadiness:
        """Check project readiness for target stage.

        Args:
            context: Workflow context
            input_data: Stage request with project path and target stage

        Returns:
            StageReadiness assessment with detailed feedback
        """
        return await self.check_readiness(
            current_stage=input_data.current_stage,
            target_stage=input_data.target_stage,
            project_path=input_data.project_path,
            context=context,
        )

    async def check_readiness(
        self,
        current_stage: Stage,
        target_stage: Stage,
        project_path: Path,
        context: WorkflowContext,
        kb: WorkflowPrimitive | None = None,
    ) -> StageReadiness:
        """Check if project is ready to transition to target stage.

        Args:
            current_stage: Current lifecycle stage
            target_stage: Target lifecycle stage
            project_path: Path to project root
            context: Workflow context
            kb: Optional KnowledgeBasePrimitive for contextual guidance

        Returns:
            StageReadiness assessment with detailed feedback
        """
        # Get criteria for current and target stages
        current_criteria = self.stage_criteria_map.get(current_stage)
        target_criteria = self.stage_criteria_map.get(target_stage)

        # Collect all validation checks
        checks = []

        # Add exit criteria for current stage
        if current_criteria:
            checks.extend(current_criteria.exit_criteria)

        # Add entry criteria for target stage
        if target_criteria:
            checks.extend(target_criteria.entry_criteria)

        # Query KB for contextual guidance if available
        kb_recommendations = []
        if kb:
            try:
                # Query for target stage best practices
                from tta_dev_primitives.knowledge import KBQuery

                best_practices_query = KBQuery(
                    query_type="best_practices",
                    topic=target_stage.value,
                    stage=target_stage.value,
                    max_results=3,
                    include_content=False,
                )
                best_practices_result = await kb.execute(best_practices_query, context)

                # Query for common mistakes in current stage
                mistakes_query = KBQuery(
                    query_type="common_mistakes",
                    topic=current_stage.value,
                    stage=current_stage.value,
                    max_results=3,
                    include_content=False,
                )
                mistakes_result = await kb.execute(mistakes_query, context)

                # Add best practices pages to recommendations
                for page in best_practices_result.pages:
                    kb_recommendations.append({
                        "title": page.title,
                        "type": "best_practice",
                        "content": page.content or "",
                        "url": page.url or "",
                        "tags": page.tags
                    })

                # Add common mistakes pages to recommendations
                for page in mistakes_result.pages:
                    kb_recommendations.append({
                        "title": page.title,
                        "type": "common_mistake",
                        "content": page.content or "",
                        "url": page.url or "",
                        "tags": page.tags
                    })

            except Exception:
                # Gracefully ignore KB errors - don't fail validation
                pass

        if not checks:
            # No criteria defined - assume ready
            return StageReadiness(
                current_stage=current_stage,
                target_stage=target_stage,
                ready=True,
                info=[],
                recommended_actions=[],
                next_steps=["No validation criteria defined for this transition"],
                kb_recommendations=kb_recommendations,
            )

        # Run all validation checks in parallel
        readiness_primitive = ReadinessCheckPrimitive(checks)
        check_result: ReadinessCheckResult = await readiness_primitive.execute(
            context, project_path
        )

        # Build recommended actions
        recommended_actions = []
        if target_criteria:
            recommended_actions.extend(target_criteria.recommended_actions)

        # Build next steps from failed checks
        next_steps = []
        for blocker in check_result.blockers:
            if blocker.fix_command:
                next_steps.append(f"{blocker.check_name}: {blocker.fix_command}")
            else:
                next_steps.append(f"Fix: {blocker.message}")

        for critical in check_result.critical:
            if critical.fix_command:
                next_steps.append(f"{critical.check_name}: {critical.fix_command}")

        return StageReadiness(
            current_stage=current_stage,
            target_stage=target_stage,
            ready=check_result.ready,
            blockers=check_result.blockers,
            critical=check_result.critical,
            warnings=check_result.warnings,
            info=check_result.info,
            all_results=check_result.all_results,
            recommended_actions=recommended_actions,
            next_steps=next_steps,
            kb_recommendations=kb_recommendations,
        )

    async def transition(
        self,
        from_stage: Stage,
        to_stage: Stage,
        project_path: Path,
        context: WorkflowContext,
        force: bool = False,
    ) -> TransitionResult:
        """Attempt to transition between stages.

        Args:
            from_stage: Starting stage
            to_stage: Target stage
            project_path: Path to project root
            context: Workflow context
            force: Whether to force transition even with blockers

        Returns:
            TransitionResult with success status and details

        Raises:
            StageTransitionError: If transition fails and force=False
        """
        # Check readiness
        readiness = await self.check_readiness(
            current_stage=from_stage,
            target_stage=to_stage,
            project_path=project_path,
            context=context,
        )

        # Determine if we can proceed
        can_proceed = readiness.ready or force

        if not can_proceed:
            # Transition blocked
            blocker_messages = [f"  - {b.message}" for b in readiness.blockers]
            message = f"Cannot transition from {from_stage} to {to_stage}. Blockers:\n" + "\n".join(
                blocker_messages
            )

            result = TransitionResult(
                success=False,
                from_stage=from_stage,
                to_stage=to_stage,
                message=message,
                readiness=readiness,
            )

            if not force:
                raise StageTransitionError(
                    message, blockers=[b.message for b in readiness.blockers]
                )

            return result

        # Transition successful
        if force and readiness.blockers:
            message = (
                f"⚠️  Forced transition from {from_stage} to {to_stage}. "
                f"({len(readiness.blockers)} blockers overridden)"
            )
        else:
            message = f"✅ Successfully transitioned from {from_stage} to {to_stage}"

        return TransitionResult(
            success=True,
            from_stage=from_stage,
            to_stage=to_stage,
            message=message,
            readiness=readiness,
        )
