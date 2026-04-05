"""Tests for the showcase Smart Code Reviewer.

Issue: #334

Covers:
- SecurityAgent: vulnerability pattern detection
- QAAgent: code style and quality checks
- MockLLMPrimitive: deterministic LLM stub response
- build_router: mock mode returns a usable primitive offline
- End-to-end: review() returns structured results;
  _render_markdown() produces Security, Quality, and LLM sections
"""

from __future__ import annotations

from pathlib import Path

import pytest

from examples.showcase.agents.qa_agent import QAAgent
from examples.showcase.agents.security_agent import SecurityAgent
from examples.showcase.main import _render_markdown, review
from examples.showcase.router import MockLLMPrimitive, build_router
from ttadev.primitives.core.base import WorkflowContext


def _ctx(name: str = "test-showcase") -> WorkflowContext:
    return WorkflowContext(workflow_id=name)


# ---------------------------------------------------------------------------
# SecurityAgent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_security_agent_hardcoded_password() -> None:
    """SecurityAgent finds a hardcoded password assignment."""
    # Arrange
    code = 'password = "super_secret_123"'
    agent = SecurityAgent()
    ctx = _ctx("test-security-password")

    # Act
    result = await agent.execute(code, ctx)

    # Assert
    assert "Security Review" in result
    assert "hardcoded secret" in result.lower()


@pytest.mark.asyncio
async def test_security_agent_unsafe_eval() -> None:
    """SecurityAgent flags eval(user_input) as an unsafe call."""
    # Arrange
    code = "result = eval(user_input)"
    agent = SecurityAgent()
    ctx = _ctx("test-security-eval")

    # Act
    result = await agent.execute(code, ctx)

    # Assert
    assert "Security Review" in result
    assert "Unsafe call" in result


@pytest.mark.asyncio
async def test_security_agent_sql_injection() -> None:
    """SecurityAgent detects SQL string concatenation (injection risk)."""
    # Arrange — intentionally insecure SQL code used as *input* to the scanner
    code = 'query = "SELECT * FROM users WHERE id = " + user_id'  # nosemgrep
    agent = SecurityAgent()
    ctx = _ctx("test-security-sql")

    # Act
    result = await agent.execute(code, ctx)

    # Assert
    assert "Security Review" in result
    assert "SQL injection" in result


@pytest.mark.asyncio
async def test_security_agent_clean_code() -> None:
    """SecurityAgent returns 'No issues detected' for safe Python code."""
    # Arrange
    code = "def add(a: int, b: int) -> int:\n    return a + b\n"
    agent = SecurityAgent()
    ctx = _ctx("test-security-clean")

    # Act
    result = await agent.execute(code, ctx)

    # Assert
    assert "Security Review" in result
    assert "No issues detected" in result


# ---------------------------------------------------------------------------
# QAAgent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_qa_agent_missing_docstring() -> None:
    """QAAgent flags a function that lacks a docstring."""
    # Arrange
    code = "def my_func(x: int) -> int:\n    return x * 2\n"
    agent = QAAgent()
    ctx = _ctx("test-qa-docstring")

    # Act
    result = await agent.execute(code, ctx)

    # Assert
    assert "Quality Review" in result
    assert "missing a docstring" in result


@pytest.mark.asyncio
async def test_qa_agent_missing_return_type() -> None:
    """QAAgent flags a function missing a return type annotation."""
    # Arrange
    code = 'def my_func(x: int):\n    """Has docstring but no return type."""\n    return x\n'
    agent = QAAgent()
    ctx = _ctx("test-qa-return-type")

    # Act
    result = await agent.execute(code, ctx)

    # Assert
    assert "Quality Review" in result
    assert "missing a return type annotation" in result


@pytest.mark.asyncio
async def test_qa_agent_long_line() -> None:
    """QAAgent flags lines exceeding 88 characters."""
    # Arrange — literal 92-char line (over the 88-char limit)
    # Using a literal avoids semgrep taint-analysis false positives.
    code = "x = aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
    agent = QAAgent()
    ctx = _ctx("test-qa-long-line")

    # Act
    result = await agent.execute(code, ctx)

    # Assert
    assert "Quality Review" in result
    assert "Line too long" in result
    assert "chars" in result


@pytest.mark.asyncio
async def test_qa_agent_syntax_error() -> None:
    """QAAgent returns a Syntax error message for invalid Python."""
    # Arrange
    code = "def broken(:\n    pass\n"
    agent = QAAgent()
    ctx = _ctx("test-qa-syntax")

    # Act
    result = await agent.execute(code, ctx)

    # Assert
    assert "Quality Review" in result
    assert "Syntax error" in result


@pytest.mark.asyncio
async def test_qa_agent_clean_function() -> None:
    """QAAgent returns 'No issues detected' for a well-formed function."""
    # Arrange
    code = (
        'def add(a: int, b: int) -> int:\n    """Return the sum of a and b."""\n    return a + b\n'
    )
    agent = QAAgent()
    ctx = _ctx("test-qa-clean")

    # Act
    result = await agent.execute(code, ctx)

    # Assert
    assert "Quality Review" in result
    assert "No issues detected" in result


# ---------------------------------------------------------------------------
# MockLLMPrimitive
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mock_llm_primitive_response_tag() -> None:
    """MockLLMPrimitive response always includes the [MockLLM/reviewer] tag."""
    # Arrange
    mock = MockLLMPrimitive()
    ctx = _ctx("test-mock-tag")

    # Act
    result = await mock.execute("print('hello')\n", ctx)

    # Assert
    assert "[MockLLM/reviewer]" in result


@pytest.mark.asyncio
async def test_mock_llm_primitive_line_count() -> None:
    """MockLLMPrimitive counts non-empty source lines correctly."""
    # Arrange
    code = "line_one = 1\nline_two = 2\nline_three = 3\n"
    mock = MockLLMPrimitive()
    ctx = _ctx("test-mock-lines")

    # Act
    result = await mock.execute(code, ctx)

    # Assert
    assert "3 lines" in result


@pytest.mark.asyncio
async def test_mock_llm_primitive_custom_role() -> None:
    """MockLLMPrimitive uses the custom role label in its bracketed tag."""
    # Arrange
    mock = MockLLMPrimitive(role="auditor")
    ctx = _ctx("test-mock-role")

    # Act
    result = await mock.execute("x = 1\n", ctx)

    # Assert
    assert "[MockLLM/auditor]" in result


# ---------------------------------------------------------------------------
# build_router
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_router_mock_mode_returns_string() -> None:
    """build_router(mock_mode=True) execute() returns a non-empty string."""
    # Arrange
    router = build_router(mock_mode=True)
    ctx = _ctx("test-router-mock")

    # Act
    result = await router.execute("def foo(): pass\n", ctx)

    # Assert
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_build_router_mock_mode_offline_response() -> None:
    """build_router mock router returns MockLLM-tagged response (no API key needed)."""
    # Arrange
    router = build_router(mock_mode=True)
    ctx = _ctx("test-router-offline")
    code = "x = 1\ny = 2\n"

    # Act
    result = await router.execute(code, ctx)

    # Assert
    assert "[MockLLM/" in result
    assert "lines" in result.lower()


# ---------------------------------------------------------------------------
# End-to-end: review() + _render_markdown()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_review_e2e_mock_mode_returns_dict(tmp_path: Path) -> None:
    """review() in mock mode returns a dict with 'security', 'quality', 'llm' keys."""
    # Arrange
    py_file = tmp_path / "sample.py"
    py_file.write_text(
        'def add(a: int, b: int) -> int:\n    """Return sum of a and b."""\n    return a + b\n',
        encoding="utf-8",
    )

    # Act
    results = await review(py_file, mock_mode=True)

    # Assert — dict shape
    assert "security" in results
    assert "quality" in results
    assert "llm" in results

    # Assert — static agents produced section headers
    assert "Security Review" in results["security"]
    assert "Quality Review" in results["quality"]

    # Assert — mock LLM returned a string
    assert isinstance(results["llm"], str)
    assert len(results["llm"]) > 0


@pytest.mark.asyncio
async def test_render_markdown_contains_all_sections(tmp_path: Path) -> None:
    """_render_markdown() produces a string containing all three review sections."""
    # Arrange
    py_file = tmp_path / "code.py"
    py_file.write_text("x = 1\n", encoding="utf-8")
    results = await review(py_file, mock_mode=True)

    # Act
    markdown = _render_markdown(results, py_file)

    # Assert
    assert "Security Review" in markdown
    assert "Quality Review" in markdown
    assert "LLM Review" in markdown


@pytest.mark.asyncio
async def test_review_e2e_mock_mode_insecure_code(tmp_path: Path) -> None:
    """review() in mock mode detects security issues in problematic code."""
    # Arrange
    py_file = tmp_path / "insecure.py"
    py_file.write_text(
        'password = "my_secret_password"\nresult = eval(user_input)\n',
        encoding="utf-8",
    )

    # Act
    results = await review(py_file, mock_mode=True)

    # Assert — security findings present
    assert "Security Review" in results["security"]
    assert "No issues detected" not in results["security"]
    assert "hardcoded secret" in results["security"].lower()
    assert "Unsafe call" in results["security"]
