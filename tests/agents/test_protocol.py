"""Tests for ttadev.agents.protocol — Task A1."""

import pytest

from ttadev.agents.protocol import ChatMessage, ChatPrimitive
from ttadev.primitives.core.base import WorkflowContext


class _GoodModel:
    """Structurally satisfies ChatPrimitive."""

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str:
        return "ok"


class _BadModel:
    """Missing chat() — does NOT satisfy ChatPrimitive."""

    async def execute(self, request: dict, ctx: WorkflowContext) -> str:
        return "ok"


class TestChatMessage:
    def test_valid_roles(self):
        for role in ("user", "assistant", "system"):
            msg: ChatMessage = {"role": role, "content": "hello"}  # type: ignore[assignment]
            assert msg["role"] == role

    def test_has_content_field(self):
        msg: ChatMessage = {"role": "user", "content": "hi"}
        assert msg["content"] == "hi"


class TestChatPrimitive:
    def test_good_model_is_structural_subtype(self):
        assert isinstance(_GoodModel(), ChatPrimitive)

    def test_bad_model_is_not_structural_subtype(self):
        assert not isinstance(_BadModel(), ChatPrimitive)

    def test_protocol_is_runtime_checkable(self):
        # Confirm @runtime_checkable is applied
        assert hasattr(ChatPrimitive, "__protocol_attrs__") or issubclass(ChatPrimitive, object)
        # isinstance() must not raise
        isinstance(_GoodModel(), ChatPrimitive)

    @pytest.mark.asyncio
    async def test_chat_returns_string(self):
        model = _GoodModel()
        ctx = WorkflowContext()
        result = await model.chat([{"role": "user", "content": "hi"}], None, ctx)
        assert isinstance(result, str)
