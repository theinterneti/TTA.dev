"""Unit tests for ttadev/workflows/orchestrator.py.

116 stmts, target 70%+ coverage.
Tests: WorkflowGoal, WorkflowOrchestrator._effective_policy, _execute_impl.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ttadev.agents.registry import AgentRegistry, override_registry
from ttadev.agents.task import AgentResult, AgentTask, Artifact
from ttadev.primitives.core.base import WorkflowContext
from ttadev.workflows.definition import MemoryConfig, WorkflowDefinition, WorkflowStep
from ttadev.workflows.gate import ApprovalGate, GateDecision, GatePolicy
from ttadev.workflows.memory import PersistentMemory
from ttadev.workflows.orchestrator import WorkflowGoal, WorkflowOrchestrator

# ── Helpers ────────────────────────────────────────────────────────────────────


def _agent_result(
    response: str = "task complete",
    confidence: float = 0.9,
    quality_gates_passed: bool = True,
    artifacts: list[Artifact] | None = None,
) -> AgentResult:
    return AgentResult(
        agent_name="mock",
        response=response,
        artifacts=artifacts or [],
        suggestions=[],
        spawned_agents=[],
        quality_gates_passed=quality_gates_passed,
        confidence=confidence,
    )


def _agent_class(result: AgentResult | None = None) -> type:
    _r = result or _agent_result()

    class _A:
        def __init__(self, model: object = None, **kw: object) -> None:
            pass

        async def execute(self, task: AgentTask, ctx: WorkflowContext) -> AgentResult:
            return _r

    return _A


def _registry(*names: str, result: AgentResult | None = None) -> AgentRegistry:
    reg = AgentRegistry()
    cls = _agent_class(result)
    for n in names:
        reg.register(n, cls)
    return reg


def _defn(
    agent: str = "developer",
    auto_approve: bool = True,
    gate: bool = True,
    steps: list[WorkflowStep] | None = None,
) -> WorkflowDefinition:
    return WorkflowDefinition(
        name="test_wf",
        description="test",
        steps=steps or [WorkflowStep(agent=agent, gate=gate)],
        auto_approve=auto_approve,
    )


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="test")


# ── WorkflowGoal ───────────────────────────────────────────────────────────────


class TestWorkflowGoal:
    def test_goal_stored(self) -> None:
        assert WorkflowGoal(goal="build a thing").goal == "build a thing"

    def test_context_defaults_empty(self) -> None:
        assert WorkflowGoal(goal="task").context == {}

    def test_context_provided(self) -> None:
        wg = WorkflowGoal(goal="t", context={"env": "prod"})
        assert wg.context == {"env": "prod"}

    def test_goal_is_string(self) -> None:
        assert isinstance(WorkflowGoal(goal="x").goal, str)


# ── Construction ───────────────────────────────────────────────────────────────


class TestOrchestratorConstruction:
    def test_gate_not_none(self) -> None:
        assert WorkflowOrchestrator(_defn())._gate is not None

    def test_explicit_gate_stored(self) -> None:
        g = ApprovalGate(auto_approve=True)
        orch = WorkflowOrchestrator(_defn(), gate=g)
        assert orch._gate is g

    def test_persistent_memory_stored(self) -> None:
        mem = MagicMock(spec=PersistentMemory)
        assert WorkflowOrchestrator(_defn(), persistent_memory=mem)._persistent_memory is mem

    def test_track_false_by_default(self) -> None:
        assert WorkflowOrchestrator(_defn())._track_in_control_plane is False


# ── _effective_policy ─────────────────────────────────────────────────────────


class TestEffectivePolicy:
    def test_auto_approve_returns_sentinel(self) -> None:
        orch = WorkflowOrchestrator(_defn(auto_approve=True))
        policy = orch._effective_policy(WorkflowStep(agent="dev", gate=True))
        assert policy.min_confidence >= 2.0

    def test_auto_approve_overrides_step_policy(self) -> None:
        orch = WorkflowOrchestrator(_defn(auto_approve=True))
        step = WorkflowStep(agent="dev", gate=True, gate_policy=GatePolicy(min_confidence=0.3))
        assert orch._effective_policy(step).min_confidence >= 2.0

    def test_auto_approve_sentinel_has_qg_false(self) -> None:
        orch = WorkflowOrchestrator(_defn(auto_approve=True))
        step = WorkflowStep(agent="dev", gate=True)
        assert orch._effective_policy(step).require_quality_gates is False

    def test_step_policy_overrides_workflow_policy(self) -> None:
        orch = WorkflowOrchestrator(_defn(auto_approve=False))
        step = WorkflowStep(agent="dev", gate=True, gate_policy=GatePolicy(min_confidence=0.75))
        assert orch._effective_policy(step).min_confidence == pytest.approx(0.75)

    def test_falls_back_to_workflow_policy(self) -> None:
        defn = WorkflowDefinition(
            name="t",
            description="t",
            steps=[],
            auto_approve=False,
            gate_policy=GatePolicy(min_confidence=0.6),
        )
        orch = WorkflowOrchestrator(defn)
        step = WorkflowStep(agent="dev", gate=True, gate_policy=None)
        assert orch._effective_policy(step).min_confidence == pytest.approx(0.6)


# ── _execute_impl ─────────────────────────────────────────────────────────────


class TestOrchestratorExecuteImpl:
    async def test_single_step_success(self) -> None:
        result = _agent_result(response="done", confidence=0.95)
        reg = _registry("developer", result=result)
        orch = WorkflowOrchestrator(_defn("developer", auto_approve=True))
        goal = WorkflowGoal(goal="feature X")

        with override_registry(reg):
            wf = await orch._execute_impl(goal, _ctx())

        assert wf.workflow_name == "test_wf"
        assert wf.goal == "feature X"
        assert len(wf.steps) == 1
        assert wf.steps[0].agent_name == "developer"
        assert wf.completed is True

    async def test_confidence_aggregated(self) -> None:
        reg = _registry("developer", result=_agent_result(confidence=0.8))
        orch = WorkflowOrchestrator(_defn(auto_approve=True))
        with override_registry(reg):
            wf = await orch._execute_impl(WorkflowGoal(goal="t"), _ctx())
        assert wf.total_confidence == pytest.approx(0.8)

    async def test_empty_steps_zero_confidence(self) -> None:
        defn = WorkflowDefinition(name="e", description="e", steps=[], auto_approve=True)
        orch = WorkflowOrchestrator(defn)
        with override_registry(AgentRegistry()):
            wf = await orch._execute_impl(WorkflowGoal(goal="t"), _ctx())
        assert wf.total_confidence == 0.0
        assert wf.steps == []
        assert wf.completed is True

    async def test_multi_step_all_run(self) -> None:
        r = _agent_result()
        reg = AgentRegistry()
        reg.register("developer", _agent_class(r))
        reg.register("qa", _agent_class(r))
        defn = WorkflowDefinition(
            name="m",
            description="m",
            steps=[WorkflowStep(agent="developer", gate=True), WorkflowStep(agent="qa", gate=True)],
            auto_approve=True,
        )
        orch = WorkflowOrchestrator(defn)
        with override_registry(reg):
            wf = await orch._execute_impl(WorkflowGoal(goal="build and test"), _ctx())
        assert len(wf.steps) == 2
        assert wf.steps[0].agent_name == "developer"
        assert wf.steps[1].agent_name == "qa"

    async def test_multi_step_confidence_is_average(self) -> None:
        reg = AgentRegistry()
        reg.register("a", _agent_class(_agent_result(confidence=0.6)))
        reg.register("b", _agent_class(_agent_result(confidence=1.0)))
        defn = WorkflowDefinition(
            name="avg",
            description="avg",
            steps=[WorkflowStep(agent="a", gate=True), WorkflowStep(agent="b", gate=True)],
            auto_approve=True,
        )
        orch = WorkflowOrchestrator(defn)
        with override_registry(reg):
            wf = await orch._execute_impl(WorkflowGoal(goal="t"), _ctx())
        assert wf.total_confidence == pytest.approx(0.8)

    async def test_no_gate_step_does_not_call_gate(self) -> None:
        reg = _registry("developer")
        defn = _defn("developer", auto_approve=False, gate=False)
        orch = WorkflowOrchestrator(defn)
        with override_registry(reg):
            wf = await orch._execute_impl(WorkflowGoal(goal="t"), _ctx())
        assert wf.completed is True

    async def test_gate_quit_stops_workflow(self) -> None:
        r = _agent_result()
        reg = AgentRegistry()
        reg.register("a", _agent_class(r))
        reg.register("b", _agent_class(r))
        defn = WorkflowDefinition(
            name="q",
            description="q",
            steps=[WorkflowStep(agent="a", gate=True), WorkflowStep(agent="b", gate=True)],
            auto_approve=False,
        )
        mock_gate = MagicMock(spec=ApprovalGate)
        mock_gate.check = AsyncMock(return_value=(GateDecision.QUIT, None, None))
        orch = WorkflowOrchestrator(defn, gate=mock_gate)
        with override_registry(reg):
            wf = await orch._execute_impl(WorkflowGoal(goal="t"), _ctx())
        assert wf.steps[-1].gate_decision == "quit"
        assert wf.completed is False

    async def test_gate_skip_marks_next_step_skipped(self) -> None:
        r = _agent_result()
        reg = AgentRegistry()
        reg.register("a", _agent_class(r))
        reg.register("b", _agent_class(r))
        defn = WorkflowDefinition(
            name="sk",
            description="sk",
            steps=[WorkflowStep(agent="a", gate=True), WorkflowStep(agent="b", gate=False)],
            auto_approve=False,
        )
        mock_gate = MagicMock(spec=ApprovalGate)
        mock_gate.check = AsyncMock(return_value=(GateDecision.SKIP, None, "auto:always"))
        orch = WorkflowOrchestrator(defn, gate=mock_gate)
        with override_registry(reg):
            wf = await orch._execute_impl(WorkflowGoal(goal="t"), _ctx())
        assert any(sr.skipped for sr in wf.steps)

    async def test_artifacts_collected(self) -> None:
        art = Artifact(name="out.py", content="print(1)", artifact_type="code")
        r = _agent_result(artifacts=[art])
        reg = _registry("developer", result=r)
        orch = WorkflowOrchestrator(_defn(auto_approve=True))
        with override_registry(reg):
            wf = await orch._execute_impl(WorkflowGoal(goal="t"), _ctx())
        assert len(wf.artifacts) == 1
        assert wf.artifacts[0].name == "out.py"

    async def test_memory_snapshot_is_dict(self) -> None:
        reg = _registry("developer")
        orch = WorkflowOrchestrator(_defn(auto_approve=True))
        with override_registry(reg):
            wf = await orch._execute_impl(WorkflowGoal(goal="t"), _ctx())
        assert isinstance(wf.memory_snapshot, dict)

    async def test_input_transform_called(self) -> None:
        calls: list[dict] = []

        def transform(snap: dict) -> AgentTask:
            calls.append(snap)
            return AgentTask(instruction="from transform", context={}, constraints=[])

        reg = _registry("developer")
        defn = WorkflowDefinition(
            name="tr",
            description="tr",
            steps=[WorkflowStep(agent="developer", gate=True, input_transform=transform)],
            auto_approve=True,
        )
        orch = WorkflowOrchestrator(defn)
        with override_registry(reg):
            await orch._execute_impl(WorkflowGoal(goal="ignored"), _ctx())
        assert len(calls) == 1

    async def test_persistent_memory_flushed(self) -> None:
        reg = _registry("developer")
        defn = WorkflowDefinition(
            name="fl",
            description="fl",
            steps=[WorkflowStep(agent="developer", gate=True)],
            auto_approve=True,
            memory_config=MemoryConfig(flush_to_persistent=True, bank_id="test.bank"),
        )
        mock_pm = MagicMock(spec=PersistentMemory)
        orch = WorkflowOrchestrator(defn, persistent_memory=mock_pm)
        with override_registry(reg):
            await orch._execute_impl(WorkflowGoal(goal="t"), _ctx())
        mock_pm.retain.assert_called_once()
        assert "test.bank" in mock_pm.retain.call_args[0]

    async def test_persistent_memory_not_flushed_when_disabled(self) -> None:
        reg = _registry("developer")
        defn = WorkflowDefinition(
            name="nf",
            description="nf",
            steps=[WorkflowStep(agent="developer", gate=True)],
            auto_approve=True,
            memory_config=MemoryConfig(flush_to_persistent=False),
        )
        mock_pm = MagicMock(spec=PersistentMemory)
        orch = WorkflowOrchestrator(defn, persistent_memory=mock_pm)
        with override_registry(reg):
            await orch._execute_impl(WorkflowGoal(goal="t"), _ctx())
        mock_pm.retain.assert_not_called()

    async def test_control_plane_required_when_tracking(self) -> None:
        orch = WorkflowOrchestrator(
            _defn(auto_approve=True),
            track_in_control_plane=True,
            control_plane_service=None,
        )
        with override_registry(_registry("developer")):
            with pytest.raises(RuntimeError, match="ControlPlaneService is required"):
                await orch._execute_impl(WorkflowGoal(goal="t"), _ctx())

    async def test_agent_exception_propagates(self) -> None:
        class _Fail:
            def __init__(self, **kw: object) -> None:
                pass

            async def execute(self, task: AgentTask, ctx: WorkflowContext) -> AgentResult:
                raise RuntimeError("agent exploded")

        reg = AgentRegistry()
        reg.register("developer", _Fail)
        orch = WorkflowOrchestrator(_defn(auto_approve=True))
        with override_registry(reg):
            with pytest.raises(RuntimeError, match="agent exploded"):
                await orch._execute_impl(WorkflowGoal(goal="t"), _ctx())

    async def test_model_factory_called_per_step(self) -> None:
        calls: list[object] = []
        mock_model = MagicMock()

        class _FA:
            def __init__(self, model: object = None, **kw: object) -> None:
                pass

            async def execute(self, task: AgentTask, ctx: WorkflowContext) -> AgentResult:
                return _agent_result()

        def factory() -> object:
            calls.append(mock_model)
            return mock_model

        reg = AgentRegistry()
        reg.register("developer", _FA)
        orch = WorkflowOrchestrator(_defn(auto_approve=True), model_factory=factory)
        with override_registry(reg):
            await orch._execute_impl(WorkflowGoal(goal="t"), _ctx())
        assert len(calls) == 1

    async def test_tracked_ids_none_when_not_tracking(self) -> None:
        reg = _registry("developer")
        orch = WorkflowOrchestrator(_defn(auto_approve=True), track_in_control_plane=False)
        with override_registry(reg):
            wf = await orch._execute_impl(WorkflowGoal(goal="t"), _ctx())
        assert wf.tracked_task_id is None
        assert wf.tracked_run_id is None

    async def test_auto_approve_prints_audit_trail(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        reg = _registry("developer")
        orch = WorkflowOrchestrator(_defn("developer", auto_approve=True, gate=True))
        with override_registry(reg):
            await orch._execute_impl(WorkflowGoal(goal="t"), _ctx())
        assert "[auto-approved]" in capsys.readouterr().out
