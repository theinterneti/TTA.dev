"""Tests for OpenHandsPrimitive.

The OpenHands SDK *is* installed in this environment.  However, we mock the
``Conversation`` factory and ``Agent`` to avoid any real LLM calls or file I/O
in the test suite.  All SDK interaction is exercised through the public
primitive interface (``execute``).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext, WorkflowPrimitive
from ttadev.primitives.integrations.openhands_primitive import (
    _GOOGLE_AUTO_SENTINELS,
    _OPENHANDS_DENYLIST,
    OPENHANDS_COMPATIBLE_FREE_MODELS,
    OpenHandsAgentError,
    OpenHandsPrimitive,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(**kwargs: Any) -> WorkflowContext:
    """Build a minimal WorkflowContext for testing."""
    return WorkflowContext(workflow_id=kwargs.pop("workflow_id", "test-wf"), **kwargs)


def _make_message_event(text: str, source: str = "agent") -> MagicMock:
    """Return a minimal mock MessageEvent.

    Args:
        text: The text content of the message.
        source: The source of the event (``"agent"`` or ``"user"``).
    """
    content = MagicMock()
    content.text = text
    llm_msg = MagicMock()
    llm_msg.content = [content]
    event = MagicMock()
    event.source = source
    event.llm_message = llm_msg
    return event


def _make_conversation(
    *,
    status: str = "finished",
    events: list[Any] | None = None,
    conversation_id: str = "conv-abc",
) -> MagicMock:
    """Return a mock LocalConversation.

    Args:
        status: String value of the execution status.
        events: List of events to return from ``conversation.state.events``.
        conversation_id: ID to expose via ``state.id``.
    """
    from openhands.sdk.conversation.state import ConversationExecutionStatus

    status_obj = ConversationExecutionStatus(status)

    state = MagicMock()
    state.id = conversation_id
    state.execution_status = status_obj
    state.events = events or []  # _extract_result and _run_sync read state.events

    conv = MagicMock()
    conv.state = state
    conv.events = events or []
    conv.send_message = MagicMock()
    conv.run = MagicMock()
    conv.close = MagicMock()
    return conv


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestOpenHandsPrimitiveConstruction:
    def test_is_workflow_primitive_subclass(self):
        """OpenHandsPrimitive is a WorkflowPrimitive."""
        prim = OpenHandsPrimitive(model="groq/test-model")
        assert isinstance(prim, WorkflowPrimitive)

    def test_default_model(self):
        """Default model is the openrouter qwen variant."""
        prim = OpenHandsPrimitive()
        assert "openrouter" in prim.model

    def test_custom_model_stored(self):
        """Custom model string is stored on the primitive."""
        prim = OpenHandsPrimitive(model="ollama/mistral")
        assert prim.model == "ollama/mistral"

    def test_default_tools_include_finish(self):
        """Default tools list is empty (SDK built-ins handle finish/think)."""
        prim = OpenHandsPrimitive()
        assert prim.tools == []

    def test_custom_tools_stored(self):
        """Custom tools list is stored correctly."""
        prim = OpenHandsPrimitive(tools=["finish", "think"])
        assert prim.tools == ["finish", "think"]

    def test_default_name(self):
        """Default primitive name is 'openhands'."""
        prim = OpenHandsPrimitive()
        assert prim.name == "openhands"

    def test_custom_name(self):
        """Custom name is stored correctly."""
        prim = OpenHandsPrimitive(name="my-coder")
        assert prim.name == "my-coder"

    def test_default_raise_on_stuck_is_true(self):
        """raise_on_stuck defaults to True."""
        prim = OpenHandsPrimitive()
        assert prim.raise_on_stuck is True

    def test_raise_on_stuck_can_be_disabled(self):
        """raise_on_stuck can be set to False."""
        prim = OpenHandsPrimitive(raise_on_stuck=False)
        assert prim.raise_on_stuck is False

    def test_workspace_dir_none_by_default(self):
        """workspace_dir is None when not specified."""
        prim = OpenHandsPrimitive()
        assert prim.workspace_dir is None


# ---------------------------------------------------------------------------
# execute — string input
# ---------------------------------------------------------------------------


class TestOpenHandsPrimitiveExecuteStringInput:
    @pytest.mark.asyncio
    async def test_returns_result_dict_on_success(self, tmp_path):
        """Returns dict with result, status, events_count, conversation_id."""
        agent_msg = _make_message_event("The task is done.", source="agent")
        conv = _make_conversation(
            status="finished",
            events=[agent_msg],
            conversation_id="conv-123",
        )

        prim = OpenHandsPrimitive(
            model="groq/test",
            workspace_dir=tmp_path,
        )

        with (
            patch.object(prim, "_build_agent", return_value=MagicMock()),
            patch(
                "openhands.sdk.Conversation",
                return_value=conv,
            ),
        ):
            result = await prim.execute("do the thing", _ctx())

        assert result["result"] == "The task is done."
        assert result["status"] == "finished"
        assert result["events_count"] == 1
        assert result["conversation_id"] == "conv-123"

    @pytest.mark.asyncio
    async def test_send_message_called_with_task(self, tmp_path):
        """send_message is called with the task string."""
        conv = _make_conversation()
        prim = OpenHandsPrimitive(model="groq/test", workspace_dir=tmp_path)

        with (
            patch.object(prim, "_build_agent", return_value=MagicMock()),
            patch(
                "openhands.sdk.Conversation",
                return_value=conv,
            ),
        ):
            await prim.execute("write tests", _ctx())

        conv.send_message.assert_called_once_with("write tests")

    @pytest.mark.asyncio
    async def test_run_called(self, tmp_path):
        """conversation.run() is called to execute the agent."""
        conv = _make_conversation()
        prim = OpenHandsPrimitive(model="groq/test", workspace_dir=tmp_path)

        with (
            patch.object(prim, "_build_agent", return_value=MagicMock()),
            patch(
                "openhands.sdk.Conversation",
                return_value=conv,
            ),
        ):
            await prim.execute("run me", _ctx())

        conv.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_conversation_always_closed(self, tmp_path):
        """conversation.close() is called even if run() raises."""
        conv = _make_conversation()
        conv.run.side_effect = RuntimeError("boom")

        prim = OpenHandsPrimitive(
            model="groq/test",
            workspace_dir=tmp_path,
            raise_on_stuck=False,
        )

        with (
            patch.object(prim, "_build_agent", return_value=MagicMock()),
            patch(
                "openhands.sdk.Conversation",
                return_value=conv,
            ),
            pytest.raises(RuntimeError, match="boom"),
        ):
            await prim.execute("crash me", _ctx())

        conv.close.assert_called_once()


# ---------------------------------------------------------------------------
# execute — dict input
# ---------------------------------------------------------------------------


class TestOpenHandsPrimitiveExecuteDictInput:
    @pytest.mark.asyncio
    async def test_dict_with_task_key(self, tmp_path):
        """Dict input with 'task' key works correctly."""
        conv = _make_conversation(events=[_make_message_event("done")])
        prim = OpenHandsPrimitive(model="groq/test", workspace_dir=tmp_path)

        with (
            patch.object(prim, "_build_agent", return_value=MagicMock()),
            patch(
                "openhands.sdk.Conversation",
                return_value=conv,
            ),
        ):
            result = await prim.execute({"task": "write a poem"}, _ctx())

        assert result["result"] == "done"

    @pytest.mark.asyncio
    async def test_dict_missing_task_key_raises(self, tmp_path):
        """Dict without 'task' key raises ValueError."""
        prim = OpenHandsPrimitive(model="groq/test", workspace_dir=tmp_path)
        with pytest.raises(ValueError, match="task"):
            await prim.execute({"other": "value"}, _ctx())

    @pytest.mark.asyncio
    async def test_dict_empty_task_raises(self, tmp_path):
        """Dict with empty 'task' string raises ValueError."""
        prim = OpenHandsPrimitive(model="groq/test", workspace_dir=tmp_path)
        with pytest.raises(ValueError, match="task"):
            await prim.execute({"task": ""}, _ctx())


# ---------------------------------------------------------------------------
# Stuck / error status handling
# ---------------------------------------------------------------------------


class TestOpenHandsPrimitiveStuckHandling:
    @pytest.mark.asyncio
    async def test_raises_on_stuck_when_enabled(self, tmp_path):
        """OpenHandsAgentError raised when agent gets stuck and raise_on_stuck=True."""
        conv = _make_conversation(status="stuck")
        prim = OpenHandsPrimitive(
            model="groq/test",
            workspace_dir=tmp_path,
            raise_on_stuck=True,
        )

        with (
            patch.object(prim, "_build_agent", return_value=MagicMock()),
            patch(
                "openhands.sdk.Conversation",
                return_value=conv,
            ),
            pytest.raises(OpenHandsAgentError) as exc_info,
        ):
            await prim.execute("impossible task", _ctx())

        assert exc_info.value.status == "stuck"

    @pytest.mark.asyncio
    async def test_returns_result_when_raise_on_stuck_false(self, tmp_path):
        """Returns result dict on stuck status when raise_on_stuck=False."""
        conv = _make_conversation(status="stuck")
        prim = OpenHandsPrimitive(
            model="groq/test",
            workspace_dir=tmp_path,
            raise_on_stuck=False,
        )

        with (
            patch.object(prim, "_build_agent", return_value=MagicMock()),
            patch(
                "openhands.sdk.Conversation",
                return_value=conv,
            ),
        ):
            result = await prim.execute("stuck task", _ctx())

        assert result["status"] == "stuck"

    def test_agent_error_has_status_attribute(self):
        """OpenHandsAgentError exposes status and events_count attributes."""
        err = OpenHandsAgentError(status="stuck", events_count=7)
        assert err.status == "stuck"
        assert err.events_count == 7
        assert "stuck" in str(err)


# ---------------------------------------------------------------------------
# Result extraction
# ---------------------------------------------------------------------------


class TestOpenHandsPrimitiveResultExtraction:
    def test_extracts_last_agent_message(self):
        """_extract_result returns text from the last agent MessageEvent."""
        prim = OpenHandsPrimitive()
        conv = MagicMock()
        conv.state.events = [
            _make_message_event("first", source="agent"),
            _make_message_event("second", source="user"),
            _make_message_event("third", source="agent"),
        ]
        result = prim._extract_result(conv)
        assert result == "third"

    def test_returns_empty_string_when_no_agent_events(self):
        """_extract_result returns '' when no agent messages exist."""
        prim = OpenHandsPrimitive()
        conv = MagicMock()
        conv.state.events = [_make_message_event("user msg", source="user")]
        result = prim._extract_result(conv)
        assert result == ""

    def test_returns_empty_string_for_empty_event_log(self):
        """_extract_result handles empty event log gracefully."""
        prim = OpenHandsPrimitive()
        conv = MagicMock()
        conv.state.events = []
        result = prim._extract_result(conv)
        assert result == ""


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------


class TestOpenHandsPrimitiveComposition:
    @pytest.mark.asyncio
    async def test_composes_with_pipe_operator(self, tmp_path):
        """OpenHandsPrimitive composes with >> operator."""
        from ttadev.primitives.core.base import LambdaPrimitive

        conv = _make_conversation(events=[_make_message_event("composed result")])
        prim = OpenHandsPrimitive(model="groq/test", workspace_dir=tmp_path)
        post = LambdaPrimitive(lambda data, ctx: {**data, "post": True})
        pipeline = prim >> post

        with (
            patch.object(prim, "_build_agent", return_value=MagicMock()),
            patch(
                "openhands.sdk.Conversation",
                return_value=conv,
            ),
        ):
            result = await pipeline.execute("task", _ctx())

        assert result["post"] is True
        assert result["result"] == "composed result"


# ---------------------------------------------------------------------------
# Google auto-resolution
# ---------------------------------------------------------------------------


class TestOpenHandsPrimitiveBuildLlmGoogleAuto:
    """_build_llm() resolves Google sentinel values via best_google_free_model()."""

    def _mock_llm_class(self, model_fields_extra: dict | None = None):
        """Return a MagicMock that behaves like the LLM Pydantic model."""
        llm_instance = MagicMock()
        llm_instance.reasoning_effort = "high"
        llm_cls = MagicMock(return_value=llm_instance)
        return llm_cls, llm_instance

    @pytest.mark.parametrize("sentinel", list(_GOOGLE_AUTO_SENTINELS))
    def test_google_sentinel_calls_best_google_free_model(self, sentinel):
        """When model is a Google sentinel, best_google_free_model() is called."""
        prim = OpenHandsPrimitive(model=sentinel, api_key="test-key")
        mock_llm_cls, mock_llm_inst = self._mock_llm_class()

        with (
            patch(
                "ttadev.primitives.integrations.openhands_primitive.best_google_free_model",
                return_value="gemini/gemini-2.0-flash",
            ) as mock_discovery,
            patch("openhands.sdk.LLM", mock_llm_cls),
        ):
            prim._build_llm()

        mock_discovery.assert_called_once()
        # LLM should be constructed with the resolved model, not the sentinel
        call_kwargs = mock_llm_cls.call_args[1]
        assert call_kwargs["model"] == "gemini/gemini-2.0-flash"

    def test_fallback_when_best_google_free_model_returns_none(self):
        """When best_google_free_model() returns None, fallback model is used."""
        prim = OpenHandsPrimitive(model="google/auto", api_key="test-key")
        mock_llm_cls, mock_llm_inst = self._mock_llm_class()

        with (
            patch(
                "ttadev.primitives.integrations.openhands_primitive.best_google_free_model",
                return_value=None,
            ),
            patch("openhands.sdk.LLM", mock_llm_cls),
        ):
            prim._build_llm()

        call_kwargs = mock_llm_cls.call_args[1]
        assert call_kwargs["model"] == "gemini/gemini-2.0-flash-lite"

    def test_explicit_gemini_model_used_as_is(self):
        """A model already starting with 'gemini/' bypasses discovery."""
        prim = OpenHandsPrimitive(model="gemini/gemini-2.5-pro")
        mock_llm_cls, mock_llm_inst = self._mock_llm_class()

        with (
            patch(
                "ttadev.primitives.integrations.openhands_primitive.best_google_free_model",
            ) as mock_discovery,
            patch("openhands.sdk.LLM", mock_llm_cls),
        ):
            prim._build_llm()

        mock_discovery.assert_not_called()
        call_kwargs = mock_llm_cls.call_args[1]
        assert call_kwargs["model"] == "gemini/gemini-2.5-pro"

    def test_fallback_emits_warning_log(self, caplog):
        """A warning is logged when falling back to the hardcoded model."""
        import logging

        prim = OpenHandsPrimitive(model="gemini/auto", api_key="k")
        mock_llm_cls, _ = self._mock_llm_class()

        with (
            caplog.at_level(
                logging.WARNING, logger="ttadev.primitives.integrations.openhands_primitive"
            ),
            patch(
                "ttadev.primitives.integrations.openhands_primitive.best_google_free_model",
                return_value=None,
            ),
            patch("openhands.sdk.LLM", mock_llm_cls),
        ):
            prim._build_llm()

        assert any("gemini-2.0-flash-lite" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# Ollama reasoning_effort fix
# ---------------------------------------------------------------------------


class TestOpenHandsPrimitiveBuildLlmOllamaReasoningEffort:
    """_build_llm() clears reasoning_effort for Ollama models."""

    def test_ollama_model_gets_reasoning_effort_cleared(self):
        """reasoning_effort is set to None for ollama/* models."""
        prim = OpenHandsPrimitive(model="ollama/mistral")
        llm_instance = MagicMock()
        llm_instance.reasoning_effort = "high"
        mock_llm_cls = MagicMock(return_value=llm_instance)

        with patch("openhands.sdk.LLM", mock_llm_cls):
            result = prim._build_llm()

        assert result.reasoning_effort is None

    def test_non_ollama_model_reasoning_effort_unchanged(self):
        """reasoning_effort is not modified for non-ollama models."""
        prim = OpenHandsPrimitive(model="groq/llama-3.3-70b-versatile")
        llm_instance = MagicMock()
        llm_instance.reasoning_effort = "high"
        mock_llm_cls = MagicMock(return_value=llm_instance)

        with patch("openhands.sdk.LLM", mock_llm_cls):
            result = prim._build_llm()

        # reasoning_effort should remain untouched (still "high" from MagicMock)
        assert result.reasoning_effort == "high"


# ---------------------------------------------------------------------------
# Denylist integrity
# ---------------------------------------------------------------------------


class TestOpenHandsDenylist:
    """_OPENHANDS_DENYLIST sanity checks."""

    def test_denylist_has_no_overlap_with_compatible_models(self):
        """No model in _OPENHANDS_DENYLIST appears in OPENHANDS_COMPATIBLE_FREE_MODELS.

        The compatible list uses the 'openrouter/' prefix; the denylist uses
        bare provider/model IDs.  We check both with and without the prefix.
        """
        compatible_bare = {m.removeprefix("openrouter/") for m in OPENHANDS_COMPATIBLE_FREE_MODELS}
        overlap = set(_OPENHANDS_DENYLIST.keys()) & compatible_bare
        assert overlap == set(), f"Overlap found between denylist and compatible list: {overlap}"

    def test_denylist_values_are_non_empty_strings(self):
        """Every denylist reason is a non-empty string."""
        for model_id, reason in _OPENHANDS_DENYLIST.items():
            assert isinstance(reason, str) and reason, (
                f"Denylist entry {model_id!r} has an empty or invalid reason"
            )

    def test_denylist_is_exported_from_integrations_package(self):
        """_OPENHANDS_DENYLIST is re-exported from the integrations __init__."""
        from ttadev.primitives.integrations import (
            _OPENHANDS_DENYLIST as _exported_denylist,  # noqa: N811
        )

        assert _exported_denylist is _OPENHANDS_DENYLIST
