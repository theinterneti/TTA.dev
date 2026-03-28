"""Tests for WorkflowOrchestrator — Task T7."""

import pytest

from ttadev.agents.registry import AgentRegistry, override_registry
from ttadev.agents.spec import AgentSpec
from ttadev.agents.task import AgentResult, AgentTask, Artifact
from ttadev.control_plane import ControlPlaneService
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.core.sequential import SequentialPrimitive
from ttadev.workflows.definition import MemoryConfig, WorkflowDefinition, WorkflowStep
from ttadev.workflows.gate import ApprovalGate
from ttadev.workflows.memory import WorkflowMemory
from ttadev.workflows.orchestrator import WorkflowGoal, WorkflowOrchestrator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(agent: str, confidence: float = 0.8) -> AgentResult:
    return AgentResult(
        agent_name=agent,
        response=f"{agent} output",
        artifacts=[Artifact(name=f"{agent}.txt", content="x", artifact_type="code")],
        suggestions=[],
        spawned_agents=[],
        quality_gates_passed=True,
        confidence=confidence,
    )


class _FakeAgent:
    """Minimal agent that returns a canned result."""

    _class_spec: AgentSpec

    def __init__(self) -> None:
        pass

    async def execute(self, task: AgentTask, ctx: WorkflowContext) -> AgentResult:
        return _make_result(self.__class__._class_spec.name)


def _make_fake_agent(name: str) -> type:
    spec = AgentSpec(
        name=name,
        role=name,
        system_prompt="test",
        capabilities=[],
        tools=[],
        quality_gates=[],
        handoff_triggers=[],
    )

    cls = type(
        f"_Fake{name.title()}Agent",
        (_FakeAgent,),
        {"_class_spec": spec},
    )
    return cls


def _three_step_registry() -> AgentRegistry:
    registry = AgentRegistry()
    for name in ["developer", "qa", "security"]:
        registry.register(name, _make_fake_agent(name))
    return registry


def _three_step_workflow(auto_approve: bool = True) -> WorkflowDefinition:
    return WorkflowDefinition(
        name="test_flow",
        description="3-step test",
        steps=[
            WorkflowStep(agent="developer"),
            WorkflowStep(agent="qa"),
            WorkflowStep(agent="security"),
        ],
        auto_approve=auto_approve,
        memory_config=MemoryConfig(flush_to_persistent=False),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestStaticRunAllContinue:
    @pytest.mark.asyncio
    async def test_completes_all_steps(self):
        registry = _three_step_registry()
        with override_registry(registry):
            orch = WorkflowOrchestrator(_three_step_workflow())
            ctx = WorkflowContext()
            result = await orch.execute(WorkflowGoal(goal="add feature"), ctx)

        assert result.completed is True
        assert len(result.steps) == 3
        assert [s.agent_name for s in result.steps] == ["developer", "qa", "security"]

    @pytest.mark.asyncio
    async def test_aggregates_artifacts(self):
        registry = _three_step_registry()
        with override_registry(registry):
            orch = WorkflowOrchestrator(_three_step_workflow())
            ctx = WorkflowContext()
            result = await orch.execute(WorkflowGoal(goal="x"), ctx)

        assert len(result.artifacts) == 3

    @pytest.mark.asyncio
    async def test_total_confidence_is_mean(self):
        registry = _three_step_registry()
        with override_registry(registry):
            orch = WorkflowOrchestrator(_three_step_workflow())
            ctx = WorkflowContext()
            result = await orch.execute(WorkflowGoal(goal="x"), ctx)

        assert abs(result.total_confidence - 0.8) < 0.01


class TestSkipStep:
    @pytest.mark.asyncio
    async def test_skip_marks_step_skipped(self):
        registry = _three_step_registry()

        class _SkipSecondGate(ApprovalGate):
            _call = 0

            async def _prompt_user(self, step_result, total_steps, next_agent):  # type: ignore[override]
                _SkipSecondGate._call += 1
                return "s" if _SkipSecondGate._call == 1 else ""

        with override_registry(registry):
            defn = _three_step_workflow(auto_approve=False)
            orch = WorkflowOrchestrator(defn, gate=_SkipSecondGate(auto_approve=False))
            ctx = WorkflowContext()
            result = await orch.execute(WorkflowGoal(goal="x"), ctx)

        assert result.completed is True
        assert result.steps[1].skipped is True
        assert len(result.steps) == 3


class TestQuitEarly:
    @pytest.mark.asyncio
    async def test_quit_stops_workflow(self):
        registry = _three_step_registry()

        class _QuitGate(ApprovalGate):
            async def _prompt_user(self, step_result, total_steps, next_agent):  # type: ignore[override]
                return "q"

        with override_registry(registry):
            defn = _three_step_workflow(auto_approve=False)
            orch = WorkflowOrchestrator(defn, gate=_QuitGate(auto_approve=False))
            ctx = WorkflowContext()
            result = await orch.execute(WorkflowGoal(goal="x"), ctx)

        assert result.completed is False
        assert len(result.steps) == 1


class TestEditStep:
    @pytest.mark.asyncio
    async def test_edit_reruns_step_with_new_instruction(self):
        instructions_seen: list[str] = []

        class _TrackingAgent(_FakeAgent):
            _class_spec = AgentSpec(
                name="developer",
                role="developer",
                system_prompt="test",
                capabilities=[],
                tools=[],
                quality_gates=[],
                handoff_triggers=[],
            )

            async def execute(self, task: AgentTask, ctx: WorkflowContext) -> AgentResult:
                instructions_seen.append(task.instruction)
                return _make_result("developer")

        registry = AgentRegistry()
        registry.register("developer", _TrackingAgent)

        edit_count = 0

        class _EditOnceGate(ApprovalGate):
            async def _prompt_user(self, step_result, total_steps, next_agent):  # type: ignore[override]
                nonlocal edit_count
                if edit_count == 0:
                    edit_count += 1
                    return "e"
                return "q"

            async def _prompt_edit(self, original: str) -> str:  # type: ignore[override]
                return "revised goal"

        defn = WorkflowDefinition(
            name="edit_test",
            description="d",
            steps=[WorkflowStep(agent="developer")],
            auto_approve=False,
            memory_config=MemoryConfig(flush_to_persistent=False),
        )
        with override_registry(registry):
            orch = WorkflowOrchestrator(defn, gate=_EditOnceGate(auto_approve=False))
            ctx = WorkflowContext()
            await orch.execute(WorkflowGoal(goal="original goal"), ctx)

        assert "revised goal" in instructions_seen
        assert len(instructions_seen) == 2


class TestMemoryPropagation:
    @pytest.mark.asyncio
    async def test_memory_attached_to_context(self):
        contexts_seen: list[WorkflowContext] = []

        class _MemoryAgent(_FakeAgent):
            _class_spec = AgentSpec(
                name="developer",
                role="developer",
                system_prompt="test",
                capabilities=[],
                tools=[],
                quality_gates=[],
                handoff_triggers=[],
            )

            async def execute(self, task: AgentTask, ctx: WorkflowContext) -> AgentResult:
                contexts_seen.append(ctx)
                return _make_result("developer")

        registry = AgentRegistry()
        registry.register("developer", _MemoryAgent)

        defn = WorkflowDefinition(
            name="mem_test",
            description="d",
            steps=[WorkflowStep(agent="developer")],
            auto_approve=True,
            memory_config=MemoryConfig(flush_to_persistent=False),
        )
        with override_registry(registry):
            orch = WorkflowOrchestrator(defn)
            ctx = WorkflowContext()
            await orch.execute(WorkflowGoal(goal="x"), ctx)

        assert len(contexts_seen) == 1
        assert isinstance(contexts_seen[0].memory, WorkflowMemory)


class TestComposability:
    def test_sequential_composition(self):
        defn = _three_step_workflow()
        orch = WorkflowOrchestrator(defn)
        from ttadev.primitives.core.base import LambdaPrimitive

        combined = orch >> LambdaPrimitive(lambda r, ctx: r)
        assert isinstance(combined, SequentialPrimitive)


class TestL0Tracking:
    @pytest.mark.asyncio
    async def test_tracked_run_creates_l0_task_and_run(self, tmp_path):
        registry = _three_step_registry()
        service = ControlPlaneService(tmp_path)

        with override_registry(registry):
            orch = WorkflowOrchestrator(
                _three_step_workflow(),
                control_plane_service=service,
                track_in_control_plane=True,
            )
            ctx = WorkflowContext()
            result = await orch.execute(WorkflowGoal(goal="add feature"), ctx)

        assert result.tracked_task_id is not None
        assert result.tracked_run_id is not None
        task = service.get_task(result.tracked_task_id)
        assert task.workflow is not None
        assert task.workflow.status.value == "completed"
        assert [step.status.value for step in task.workflow.steps] == [
            "completed",
            "completed",
            "completed",
        ]

    @pytest.mark.asyncio
    async def test_tracked_quit_records_quit_state(self, tmp_path):
        registry = _three_step_registry()
        service = ControlPlaneService(tmp_path)

        class _QuitGate(ApprovalGate):
            async def _prompt_user(self, step_result, total_steps, next_agent):  # type: ignore[override]
                return "q"

        with override_registry(registry):
            defn = _three_step_workflow(auto_approve=False)
            orch = WorkflowOrchestrator(
                defn,
                gate=_QuitGate(auto_approve=False),
                control_plane_service=service,
                track_in_control_plane=True,
            )
            ctx = WorkflowContext()
            result = await orch.execute(WorkflowGoal(goal="x"), ctx)

        assert result.completed is False
        assert result.tracked_task_id is not None
        task = service.get_task(result.tracked_task_id)
        assert task.workflow is not None
        assert task.workflow.status.value == "quit"
        assert task.workflow.steps[0].gate_decision.value == "quit"
        assert task.workflow.steps[0].status.value == "quit"
