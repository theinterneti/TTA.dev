"""ChatPrimitive protocol — the interface any model must satisfy to power an agent."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol, TypedDict, runtime_checkable

if TYPE_CHECKING:
    from ttadev.primitives.core.base import WorkflowContext


class ChatMessage(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: str


@runtime_checkable
class ChatPrimitive(Protocol):
    """Structural protocol for any model that can power an AgentPrimitive.

    Any object with a matching ``chat()`` signature satisfies this protocol —
    no base class required. All five built-in LLM primitives implement it.

    Example::

        class MyModel:
            async def chat(self, messages, system, ctx):
                return "response"

        assert isinstance(MyModel(), ChatPrimitive)  # True
    """

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str: ...
