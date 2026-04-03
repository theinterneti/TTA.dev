"""ModelRouterChatAdapter — bridges ModelRouterPrimitive to the ChatPrimitive protocol.

Lets any AgentPrimitive be powered by ModelRouterPrimitive (with task-aware model
selection) without changing the agent's interface.

Example::

    from ttadev.agents import DeveloperAgent
    from ttadev.agents.adapter import ModelRouterChatAdapter
    from ttadev.primitives.llm import ModelRouterPrimitive, RouterModeConfig, RouterTierConfig

    router = ModelRouterPrimitive(
        modes={
            "default": RouterModeConfig(
                tiers=[
                    RouterTierConfig(provider="ollama"),
                    RouterTierConfig(provider="groq"),
                    RouterTierConfig(provider="gemini"),
                ]
            )
        },
        groq_api_key="...",
        gemini_api_key="...",
    )

    # Automatically uses DeveloperAgent's TaskProfile.coding(COMPLEXITY_COMPLEX)
    agent = DeveloperAgent.with_router(router)
    result = await agent.execute(task, ctx)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ttadev.primitives.llm.model_router import ModelRouterPrimitive, ModelRouterRequest

if TYPE_CHECKING:
    from ttadev.agents.protocol import ChatMessage
    from ttadev.primitives.core.base import WorkflowContext


class ModelRouterChatAdapter:
    """Adapts ``ModelRouterPrimitive`` to satisfy the ``ChatPrimitive`` protocol.

    Converts the ``chat(messages, system, ctx)`` call into a ``ModelRouterRequest``
    and returns the response content as a plain string.

    Args:
        router: A configured ``ModelRouterPrimitive`` instance.
        mode: The routing mode key (must exist in ``router``'s modes config).
        task_profile: Optional ``TaskProfile`` to pass to the router for
            benchmark-based model ranking.  Usually set automatically from
            ``AgentSpec.default_task_profile`` by ``AgentPrimitive.with_router()``.
    """

    def __init__(
        self,
        router: ModelRouterPrimitive,
        mode: str = "default",
        task_profile: Any | None = None,
    ) -> None:
        self._router = router
        self._mode = mode
        self._task_profile = task_profile

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str:
        """Execute via the router, returning the model's text response."""
        # Fold system prompt into the conversation if present.
        parts: list[str] = []
        if system:
            parts.append(system)
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                parts.append(content)
            elif role == "assistant":
                parts.append(f"[assistant]: {content}")

        prompt = "\n\n".join(parts)
        req = ModelRouterRequest(
            mode=self._mode,
            prompt=prompt,
            task_profile=self._task_profile,
        )
        resp = await self._router.execute(req, ctx)
        return resp.content

    @property
    def task_profile(self) -> Any | None:
        """The task profile used for benchmark-based model selection."""
        return self._task_profile

    @property
    def mode(self) -> str:
        """The routing mode key."""
        return self._mode
