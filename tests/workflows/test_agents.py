"""Tests for pre-built agent factories in ttadev.workflows.agents."""

from __future__ import annotations

from ttadev.workflows.agents import code_reviewer, coding_assistant, qa_agent
from ttadev.workflows.development_cycle import DevelopmentCycle


def test_coding_assistant_returns_development_cycle() -> None:
    result = coding_assistant()
    assert isinstance(result, DevelopmentCycle)


def test_coding_assistant_agent_hint_is_developer() -> None:
    result = coding_assistant()
    assert result._agent_hint == "developer"


def test_coding_assistant_zero_config() -> None:
    result = coding_assistant()
    assert isinstance(result, DevelopmentCycle)
    assert result._bank_id == "tta-dev"


def test_code_reviewer_returns_development_cycle() -> None:
    result = code_reviewer()
    assert isinstance(result, DevelopmentCycle)


def test_code_reviewer_agent_hint_is_qa() -> None:
    result = code_reviewer()
    assert result._agent_hint == "qa"


def test_qa_agent_returns_development_cycle() -> None:
    result = qa_agent()
    assert isinstance(result, DevelopmentCycle)


def test_qa_agent_agent_hint_is_qa() -> None:
    result = qa_agent()
    assert result._agent_hint == "qa"


def test_factories_accept_bank_id() -> None:
    result = coding_assistant(bank_id="myapp")
    assert result._bank_id == "myapp"
