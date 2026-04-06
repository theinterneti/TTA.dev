"""Unit tests for examples/auto_pr_reviewer/main.py.

Tests cover:
- URL parsing (_parse_pr_url)
- fetch_pr_diff with mocked subprocess
- build_reviewer() produces a proper WorkflowPrimitive
- Full workflow end-to-end with MockPrimitive for the LLM step
- format_review output structure
- Cache avoids redundant gh CLI invocations

No real LLM providers or network calls are used.
"""

from __future__ import annotations

import importlib.util
import subprocess
import types
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ttadev.primitives import (
    LLMResponse,
    MockPrimitive,
    WorkflowContext,
    WorkflowPrimitive,
)

# ---------------------------------------------------------------------------
# Load the example module via importlib so we don't require examples/ in
# sys.path and avoid polluting the package namespace.
# ---------------------------------------------------------------------------

_MODULE_PATH = Path(__file__).parents[2] / "examples" / "auto_pr_reviewer" / "main.py"


def _load_module() -> types.ModuleType:
    """Load examples/auto_pr_reviewer/main.py as a Python module."""
    spec = importlib.util.spec_from_file_location("auto_pr_reviewer_main", _MODULE_PATH)
    assert spec is not None, f"Could not find module at {_MODULE_PATH}"
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_mod = _load_module()

# Re-export symbols under convenient names for this test module.
fetch_pr_diff = _mod.fetch_pr_diff
format_review = _mod.format_review
build_reviewer = _mod.build_reviewer
_parse_pr_url = _mod._parse_pr_url
_make_prepare_request = _mod._make_prepare_request
_REVIEW_SYSTEM_PROMPT = _mod._REVIEW_SYSTEM_PROMPT

# ---------------------------------------------------------------------------
# Sample fixtures
# ---------------------------------------------------------------------------

_SAMPLE_DIFF = """\
diff --git a/ttadev/utils.py b/ttadev/utils.py
index 1234567..89abcde 100644
--- a/ttadev/utils.py
+++ b/ttadev/utils.py
@@ -10,6 +10,10 @@ import os
 def helper():
-    return None
+    return "fixed"
+
+
+def new_function() -> str:
+    \"\"\"A new helper.\"\"\"
+    return "hello"
"""

_SAMPLE_DIFF_DATA: dict[str, Any] = {
    "diff": _SAMPLE_DIFF,
    "pr_url": "https://github.com/acme/myapp/pull/42",
    "pr_number": 42,
    "repo": "acme/myapp",
}

_SAMPLE_LLM_RESPONSE = LLMResponse(
    content=(
        "## Summary\nThis PR fixes a bug in `helper()` and adds `new_function()`.\n\n"
        "## Assessment\nApprove ✅"
    ),
    model="llama-3.3-70b-versatile",
    provider="groq",
    usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    finish_reason="stop",
)


# ---------------------------------------------------------------------------
# _parse_pr_url tests
# ---------------------------------------------------------------------------


class TestParsePrUrl:
    """Tests for _parse_pr_url URL-parsing helper."""

    def test_full_github_url(self) -> None:
        """Full GitHub PR URL is parsed correctly."""
        owner, repo, number = _parse_pr_url("https://github.com/acme/myapp/pull/42")
        assert owner == "acme"
        assert repo == "myapp"
        assert number == 42

    def test_full_url_with_trailing_slash_stripped(self) -> None:
        """Leading/trailing whitespace is stripped."""
        owner, repo, number = _parse_pr_url("  https://github.com/acme/myapp/pull/7  ")
        assert owner == "acme"
        assert number == 7

    def test_short_form(self) -> None:
        """Short 'owner/repo#N' form is parsed correctly."""
        owner, repo, number = _parse_pr_url("acme/myapp#123")
        assert owner == "acme"
        assert repo == "myapp"
        assert number == 123

    def test_plain_integer_with_repo(self) -> None:
        """Plain integer PR number with explicit repo kwarg."""
        owner, repo, number = _parse_pr_url("42", repo="acme/myapp")
        assert owner == "acme"
        assert repo == "myapp"
        assert number == 42

    def test_plain_integer_without_repo_raises(self) -> None:
        """Plain integer without repo raises ValueError."""
        with pytest.raises(ValueError, match="plain number"):
            _parse_pr_url("42")

    def test_invalid_string_raises(self) -> None:
        """Completely unrecognisable input raises ValueError."""
        with pytest.raises(ValueError, match="Cannot parse PR reference"):
            _parse_pr_url("not-a-pr-url")

    def test_invalid_repo_format_raises(self) -> None:
        """A repo argument without '/' raises ValueError."""
        with pytest.raises(ValueError, match="owner/repo"):
            _parse_pr_url("42", repo="noslash")


# ---------------------------------------------------------------------------
# fetch_pr_diff tests
# ---------------------------------------------------------------------------


def _make_subprocess_result(stdout: str, returncode: int = 0) -> MagicMock:
    """Build a fake subprocess.CompletedProcess result."""
    result = MagicMock(spec=subprocess.CompletedProcess)
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = ""
    return result


class TestFetchPrDiff:
    """Tests for the fetch_pr_diff async function."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self) -> None:
        """fetch_pr_diff calls gh CLI and returns structured dict."""
        ctx = WorkflowContext.root("test-fetch")

        with patch("subprocess.run", return_value=_make_subprocess_result(_SAMPLE_DIFF)):
            result = await fetch_pr_diff("https://github.com/acme/myapp/pull/42", ctx)

        assert result["diff"] == _SAMPLE_DIFF
        assert result["pr_number"] == 42
        assert result["repo"] == "acme/myapp"
        assert result["pr_url"] == "https://github.com/acme/myapp/pull/42"

    @pytest.mark.asyncio
    async def test_gh_failure_raises_runtime_error(self) -> None:
        """A non-zero gh exit code raises RuntimeError."""
        ctx = WorkflowContext.root("test-fetch-fail")
        bad_result = MagicMock(spec=subprocess.CompletedProcess)
        bad_result.returncode = 1
        bad_result.stdout = ""
        bad_result.stderr = "Could not find PR"

        with patch("subprocess.run", return_value=bad_result):
            with pytest.raises(RuntimeError, match="Could not find PR"):
                await fetch_pr_diff("https://github.com/acme/myapp/pull/99", ctx)

    @pytest.mark.asyncio
    async def test_plain_int_with_repo_in_metadata(self) -> None:
        """Plain PR number with repo in ctx.metadata is resolved correctly."""
        ctx = WorkflowContext.root("test-fetch-int")
        ctx.metadata["repo"] = "acme/myapp"

        with patch("subprocess.run", return_value=_make_subprocess_result(_SAMPLE_DIFF)):
            result = await fetch_pr_diff("42", ctx)

        assert result["pr_number"] == 42
        assert result["repo"] == "acme/myapp"

    @pytest.mark.asyncio
    async def test_invokes_gh_with_correct_args(self) -> None:
        """Verify the exact subprocess command sent to gh CLI."""
        ctx = WorkflowContext.root("test-gh-cmd")
        captured: list[Any] = []

        def _spy(*args: Any, **kwargs: Any) -> MagicMock:
            captured.extend(args)
            return _make_subprocess_result(_SAMPLE_DIFF)

        with patch("subprocess.run", side_effect=_spy):
            await fetch_pr_diff("https://github.com/acme/myapp/pull/42", ctx)

        assert captured, "subprocess.run was not called"
        cmd = captured[0]
        assert "gh" in cmd
        assert "pr" in cmd
        assert "diff" in cmd
        assert "42" in cmd
        assert "acme/myapp" in cmd


# ---------------------------------------------------------------------------
# format_review tests
# ---------------------------------------------------------------------------


class TestFormatReview:
    """Tests for the format_review async function."""

    @pytest.mark.asyncio
    async def test_contains_llm_content(self) -> None:
        """Formatted output includes the LLM's review text."""
        ctx = WorkflowContext.root("test-format")
        output = await format_review(_SAMPLE_LLM_RESPONSE, ctx)

        assert "Summary" in output
        assert "Assessment" in output

    @pytest.mark.asyncio
    async def test_contains_model_info(self) -> None:
        """Formatted output includes model/provider information."""
        ctx = WorkflowContext.root("test-format-model")
        output = await format_review(_SAMPLE_LLM_RESPONSE, ctx)

        assert "groq" in output
        assert "llama-3.3-70b-versatile" in output

    @pytest.mark.asyncio
    async def test_contains_token_count(self) -> None:
        """Formatted output includes token usage when present."""
        ctx = WorkflowContext.root("test-format-tokens")
        output = await format_review(_SAMPLE_LLM_RESPONSE, ctx)
        assert "150" in output

    @pytest.mark.asyncio
    async def test_handles_missing_usage(self) -> None:
        """format_review does not crash when usage is None."""
        ctx = WorkflowContext.root("test-format-no-usage")
        resp = LLMResponse(content="Looks good.", model="m", provider="p")
        output = await format_review(resp, ctx)
        assert "Looks good." in output

    @pytest.mark.asyncio
    async def test_returns_string(self) -> None:
        """Return type is always str."""
        ctx = WorkflowContext.root("test-format-type")
        output = await format_review(_SAMPLE_LLM_RESPONSE, ctx)
        assert isinstance(output, str)


# ---------------------------------------------------------------------------
# _make_prepare_request tests
# ---------------------------------------------------------------------------


class TestMakePrepareRequest:
    """Tests for the _make_prepare_request factory."""

    @pytest.mark.asyncio
    async def test_returns_llm_request_with_correct_model(self) -> None:
        """LLMRequest carries the model string from the closure."""
        from ttadev.primitives import LLMRequest

        ctx = WorkflowContext.root("test-prepare")
        prepare_fn = _make_prepare_request("groq/llama-3.3-70b-versatile")
        req = await prepare_fn(_SAMPLE_DIFF_DATA, ctx)

        assert isinstance(req, LLMRequest)
        assert req.model == "groq/llama-3.3-70b-versatile"

    @pytest.mark.asyncio
    async def test_system_prompt_in_messages(self) -> None:
        """System prompt appears as the first message."""
        ctx = WorkflowContext.root("test-prepare-sys")
        prepare_fn = _make_prepare_request("test-model")
        req = await prepare_fn(_SAMPLE_DIFF_DATA, ctx)

        system_msgs = [m for m in req.messages if m["role"] == "system"]
        assert len(system_msgs) == 1
        assert "expert code reviewer" in system_msgs[0]["content"].lower()

    @pytest.mark.asyncio
    async def test_diff_included_in_user_message(self) -> None:
        """PR diff text appears in the user message."""
        ctx = WorkflowContext.root("test-prepare-diff")
        prepare_fn = _make_prepare_request("test-model")
        req = await prepare_fn(_SAMPLE_DIFF_DATA, ctx)

        user_msgs = [m for m in req.messages if m["role"] == "user"]
        assert len(user_msgs) >= 1
        combined = " ".join(m["content"] for m in user_msgs)
        assert "helper" in combined

    @pytest.mark.asyncio
    async def test_handles_empty_diff(self) -> None:
        """Empty diff is handled gracefully (no crash)."""
        ctx = WorkflowContext.root("test-prepare-empty")
        prepare_fn = _make_prepare_request("test-model")
        empty_data: dict[str, Any] = {
            "diff": "",
            "pr_url": "x",
            "pr_number": 0,
            "repo": "a/b",
        }
        req = await prepare_fn(empty_data, ctx)
        user_msgs = [m for m in req.messages if m["role"] == "user"]
        assert any("no diff available" in m["content"].lower() for m in user_msgs)


# ---------------------------------------------------------------------------
# build_reviewer tests
# ---------------------------------------------------------------------------


class TestBuildReviewer:
    """Tests for the build_reviewer factory function."""

    def test_returns_workflow_primitive(self) -> None:
        """build_reviewer returns a WorkflowPrimitive instance."""
        workflow = build_reviewer()
        assert isinstance(workflow, WorkflowPrimitive)

    def test_custom_model_accepted(self) -> None:
        """build_reviewer accepts any model string without error."""
        workflow = build_reviewer(model="ollama/qwen2.5:7b")
        assert isinstance(workflow, WorkflowPrimitive)

    def test_custom_llm_primitive_injected(self) -> None:
        """A MockPrimitive can be injected in place of LiteLLMPrimitive."""
        mock_llm = MockPrimitive("llm", return_value=_SAMPLE_LLM_RESPONSE)
        workflow = build_reviewer(llm_primitive=mock_llm)
        assert isinstance(workflow, WorkflowPrimitive)

    def test_custom_cache_ttl(self) -> None:
        """cache_ttl_seconds parameter is accepted without error."""
        workflow = build_reviewer(cache_ttl_seconds=60.0)
        assert isinstance(workflow, WorkflowPrimitive)

    def test_custom_max_retries(self) -> None:
        """max_retries parameter is accepted without error."""
        workflow = build_reviewer(max_retries=5)
        assert isinstance(workflow, WorkflowPrimitive)


# ---------------------------------------------------------------------------
# Full workflow integration tests (no real network / LLM)
# ---------------------------------------------------------------------------


class TestFullWorkflow:
    """End-to-end tests with mocked gh CLI and MockPrimitive for LLM."""

    @pytest.mark.asyncio
    async def test_workflow_produces_string_output(self) -> None:
        """Full pipeline with mocked deps produces a non-empty review string."""
        mock_llm = MockPrimitive("llm", return_value=_SAMPLE_LLM_RESPONSE)
        workflow = build_reviewer(llm_primitive=mock_llm)
        ctx = WorkflowContext.root("test-e2e")

        with patch("subprocess.run", return_value=_make_subprocess_result(_SAMPLE_DIFF)):
            result = await workflow.execute("https://github.com/acme/myapp/pull/42", ctx)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_workflow_output_contains_llm_content(self) -> None:
        """Review string contains content from the LLM response."""
        mock_llm = MockPrimitive("llm", return_value=_SAMPLE_LLM_RESPONSE)
        workflow = build_reviewer(llm_primitive=mock_llm)
        ctx = WorkflowContext.root("test-e2e-content")

        with patch("subprocess.run", return_value=_make_subprocess_result(_SAMPLE_DIFF)):
            result = await workflow.execute("https://github.com/acme/myapp/pull/42", ctx)

        assert "Summary" in result or "Assessment" in result

    @pytest.mark.asyncio
    async def test_mock_llm_receives_llm_request(self) -> None:
        """The LLM step receives an LLMRequest object (not raw diff text)."""
        from ttadev.primitives import LLMRequest

        mock_llm = MockPrimitive("llm", return_value=_SAMPLE_LLM_RESPONSE)
        workflow = build_reviewer(llm_primitive=mock_llm)
        ctx = WorkflowContext.root("test-e2e-request-type")

        with patch("subprocess.run", return_value=_make_subprocess_result(_SAMPLE_DIFF)):
            await workflow.execute("https://github.com/acme/myapp/pull/42", ctx)

        mock_llm.assert_called()
        received_input = mock_llm.last_input
        assert isinstance(received_input, LLMRequest), (
            f"Expected LLMRequest, got {type(received_input).__name__}"
        )

    @pytest.mark.asyncio
    async def test_mock_llm_receives_diff_in_messages(self) -> None:
        """The LLMRequest sent to the LLM includes the PR diff content."""
        from ttadev.primitives import LLMRequest

        mock_llm = MockPrimitive("llm", return_value=_SAMPLE_LLM_RESPONSE)
        workflow = build_reviewer(llm_primitive=mock_llm)
        ctx = WorkflowContext.root("test-e2e-messages")

        with patch("subprocess.run", return_value=_make_subprocess_result(_SAMPLE_DIFF)):
            await workflow.execute("https://github.com/acme/myapp/pull/42", ctx)

        req: LLMRequest = mock_llm.last_input
        all_content = " ".join(m["content"] for m in req.messages)
        assert "helper" in all_content, "Diff content should appear in LLM messages"

    @pytest.mark.asyncio
    async def test_cache_avoids_redundant_gh_invocations(self) -> None:
        """Second call with same PR URL uses cache — gh CLI called only once."""
        mock_llm = MockPrimitive("llm", return_value=_SAMPLE_LLM_RESPONSE)
        workflow = build_reviewer(llm_primitive=mock_llm)
        ctx = WorkflowContext.root("test-cache")

        call_count = 0

        def _counting_subprocess(*args: Any, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            return _make_subprocess_result(_SAMPLE_DIFF)

        pr_url = "https://github.com/acme/myapp/pull/42"
        with patch("subprocess.run", side_effect=_counting_subprocess):
            await workflow.execute(pr_url, ctx)
            await workflow.execute(pr_url, ctx)

        assert call_count == 1, (
            f"gh CLI should be called once (cache hit on second call), got {call_count}"
        )

    @pytest.mark.asyncio
    async def test_different_prs_fetch_independently(self) -> None:
        """Two different PR URLs each trigger a separate gh CLI call."""
        mock_llm = MockPrimitive("llm", return_value=_SAMPLE_LLM_RESPONSE)
        workflow = build_reviewer(llm_primitive=mock_llm)
        ctx = WorkflowContext.root("test-cache-independent")

        call_count = 0

        def _counting_subprocess(*args: Any, **kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            return _make_subprocess_result(_SAMPLE_DIFF)

        with patch("subprocess.run", side_effect=_counting_subprocess):
            await workflow.execute("https://github.com/acme/myapp/pull/42", ctx)
            await workflow.execute("https://github.com/acme/myapp/pull/99", ctx)

        assert call_count == 2, (
            f"Different PRs should each call gh CLI separately, got {call_count}"
        )

    @pytest.mark.asyncio
    async def test_gh_failure_propagates(self) -> None:
        """A gh CLI failure raises RuntimeError before the LLM is called."""
        mock_llm = MockPrimitive("llm", return_value=_SAMPLE_LLM_RESPONSE)
        workflow = build_reviewer(llm_primitive=mock_llm)
        ctx = WorkflowContext.root("test-gh-fail")

        bad_result = MagicMock(spec=subprocess.CompletedProcess)
        bad_result.returncode = 1
        bad_result.stdout = ""
        bad_result.stderr = "Not Found"

        with patch("subprocess.run", return_value=bad_result):
            with pytest.raises(RuntimeError, match="Not Found"):
                await workflow.execute("https://github.com/acme/myapp/pull/999", ctx)

        mock_llm.assert_not_called()
