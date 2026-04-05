"""Tests for ttadev.workflows.agents factory functions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ttadev.workflows.agents import code_reviewer, coding_assistant, qa_agent
from ttadev.workflows.development_cycle import DevelopmentCycle


def _mock_deps():
    """Return context manager that patches internal deps with no network calls."""
    mem_patch = patch("ttadev.workflows.development_cycle.AgentMemory", return_value=MagicMock())
    graph_patch = patch(
        "ttadev.workflows.development_cycle.CodeGraphPrimitive", return_value=MagicMock()
    )
    return mem_patch, graph_patch


class TestCodingAssistant:
    def test_returns_development_cycle(self):
        mem_p, graph_p = _mock_deps()
        with mem_p, graph_p:
            agent = coding_assistant()
        assert isinstance(agent, DevelopmentCycle)

    def test_custom_bank_id(self):
        mem_p, graph_p = _mock_deps()
        with mem_p, graph_p:
            agent = coding_assistant(bank_id="my-bank")
        assert agent._bank_id == "my-bank"

    def test_agent_hint_developer(self):
        mem_p, graph_p = _mock_deps()
        with mem_p, graph_p:
            agent = coding_assistant()
        assert agent._agent_hint == "developer"


class TestCodeReviewer:
    def test_returns_development_cycle(self):
        mem_p, graph_p = _mock_deps()
        with mem_p, graph_p:
            agent = code_reviewer()
        assert isinstance(agent, DevelopmentCycle)

    def test_agent_hint_qa(self):
        mem_p, graph_p = _mock_deps()
        with mem_p, graph_p:
            agent = code_reviewer()
        assert agent._agent_hint == "qa"


class TestQaAgent:
    def test_returns_development_cycle(self):
        mem_p, graph_p = _mock_deps()
        with mem_p, graph_p:
            agent = qa_agent()
        assert isinstance(agent, DevelopmentCycle)

    def test_agent_hint_qa(self):
        mem_p, graph_p = _mock_deps()
        with mem_p, graph_p:
            agent = qa_agent()
        assert agent._agent_hint == "qa"
