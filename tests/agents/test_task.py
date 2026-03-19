"""Tests for ttadev.agents.task — Task A3."""

import dataclasses

from ttadev.agents.task import AgentResult, AgentTask, Artifact


class TestArtifact:
    def test_construction(self):
        a = Artifact(name="main.py", content="x = 1", artifact_type="code")
        assert a.name == "main.py"
        assert a.content == "x = 1"
        assert a.artifact_type == "code"

    def test_is_dataclass(self):
        assert dataclasses.is_dataclass(Artifact)


class TestAgentTask:
    def test_required_fields(self):
        t = AgentTask(instruction="review this", context={}, constraints=[])
        assert t.instruction == "review this"
        assert t.context == {}
        assert t.constraints == []

    def test_agent_hint_defaults_none(self):
        t = AgentTask(instruction="x", context={}, constraints=[])
        assert t.agent_hint is None

    def test_agent_hint_settable(self):
        t = AgentTask(instruction="x", context={}, constraints=[], agent_hint="developer")
        assert t.agent_hint == "developer"

    def test_is_dataclass(self):
        assert dataclasses.is_dataclass(AgentTask)


class TestAgentResult:
    def test_construction(self):
        r = AgentResult(
            agent_name="developer",
            response="looks good",
            artifacts=[],
            suggestions=[],
            spawned_agents=[],
            quality_gates_passed=True,
            confidence=0.9,
        )
        assert r.agent_name == "developer"
        assert r.quality_gates_passed is True
        assert r.confidence == 0.9

    def test_serialisable_via_asdict(self):
        r = AgentResult(
            agent_name="developer",
            response="ok",
            artifacts=[Artifact("f.py", "x=1", "code")],
            suggestions=["add type hints"],
            spawned_agents=[],
            quality_gates_passed=True,
            confidence=1.0,
        )
        d = dataclasses.asdict(r)
        assert d["agent_name"] == "developer"
        assert d["artifacts"][0]["name"] == "f.py"

    def test_is_dataclass(self):
        assert dataclasses.is_dataclass(AgentResult)
