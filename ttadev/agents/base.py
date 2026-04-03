"""AgentPrimitive — wraps a ChatPrimitive with an AgentSpec."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ttadev.agents.spec import AgentSpec, ToolRule
from ttadev.agents.task import AgentResult, AgentTask
from ttadev.agents.tool_call_loop import ToolCallLoop, ToolCallRequest
from ttadev.primitives.observability.instrumented_primitive import InstrumentedPrimitive

if TYPE_CHECKING:
    from ttadev.agents.protocol import ChatPrimitive
    from ttadev.primitives.core.base import WorkflowContext
    from ttadev.primitives.llm.model_router import ModelRouterPrimitive


class QualityGateError(RuntimeError):
    """Raised when an agent's quality gate check fails."""

    def __init__(self, gate_name: str, message: str) -> None:
        self.gate_name = gate_name
        super().__init__(f"Quality gate {gate_name!r} failed: {message}")


class AgentPrimitive(InstrumentedPrimitive[AgentTask, AgentResult]):
    """A composable primitive that applies an AgentSpec to a ChatPrimitive model.

    Subclasses should set a ``_spec_name`` class attribute and call
    ``super().__init__(spec=..., model=...)`` in their constructor.

    Example::

        class DeveloperAgent(AgentPrimitive):
            def __init__(self, model: ChatPrimitive):
                super().__init__(spec=DEVELOPER_SPEC, model=model)

        agent = DeveloperAgent(model=AnthropicPrimitive())
        result = await agent.execute(task, ctx)

        # Composable with other primitives:
        workflow = TimeoutPrimitive(30) >> agent >> RetryPrimitive(2)
    """

    def __init__(self, spec: AgentSpec, model: ChatPrimitive) -> None:
        super().__init__(name=f"agent.{spec.name}")
        self._spec = spec
        self._model = model

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------

    async def _execute_impl(self, task: AgentTask, ctx: WorkflowContext) -> AgentResult:
        spawned_agents: list[str] = []

        # Check handoff triggers — spawn sub-agents before running main task
        for trigger in self._spec.handoff_triggers:
            if trigger.condition(task):
                sub_result = await ctx.spawn_agent(trigger.target_agent, task)
                spawned_agents.append(trigger.target_agent)
                # Return sub-agent result directly if it was triggered
                return AgentResult(
                    agent_name=self._spec.name,
                    response=sub_result.response,
                    artifacts=sub_result.artifacts,
                    suggestions=sub_result.suggestions,
                    spawned_agents=spawned_agents,
                    quality_gates_passed=sub_result.quality_gates_passed,
                    confidence=sub_result.confidence,
                )

        # Build tool handlers from ALWAYS and WHEN_INSTRUCTED tools
        tool_handlers: dict[str, Any] = {}
        for tool in self._spec.tools:
            if tool.rule in (ToolRule.ALWAYS, ToolRule.WHEN_INSTRUCTED):
                # Placeholder handler — subclasses or integration layer wires real ones
                tool_handlers[tool.name] = lambda args, t=tool: f"[{t.name} executed]"

        # Run the tool call loop
        messages = [{"role": "user", "content": self._build_prompt(task)}]
        loop = ToolCallLoop(model=self._model, tool_handlers=tool_handlers)
        request = ToolCallRequest(
            messages=messages,  # type: ignore[arg-type]
            tools=[],
            system=self._spec.system_prompt,
        )
        response = await loop.execute(request, ctx)

        result = AgentResult(
            agent_name=self._spec.name,
            response=response,
            artifacts=[],
            suggestions=[],
            spawned_agents=spawned_agents,
            quality_gates_passed=True,
            confidence=0.8,
        )

        # Run quality gates
        for gate in self._spec.quality_gates:
            if not gate.check(result):
                raise QualityGateError(gate.name, gate.error_message)

        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_prompt(self, task: AgentTask) -> str:
        parts = [task.instruction]
        if task.context:
            parts.append("\nContext:")
            for key, value in task.context.items():
                parts.append(f"  {key}: {value}")
        if task.constraints:
            parts.append("\nConstraints:")
            for c in task.constraints:
                parts.append(f"  - {c}")
        return "\n".join(parts)

    @property
    def spec(self) -> AgentSpec:
        return self._spec

    # ------------------------------------------------------------------
    # Factory: power this agent with a ModelRouterPrimitive
    # ------------------------------------------------------------------

    @classmethod
    def with_router(
        cls,
        router: ModelRouterPrimitive,
        mode: str = "default",
        task_profile: Any | None = None,
    ) -> AgentPrimitive:
        """Create an instance of this agent backed by a ``ModelRouterPrimitive``.

        The adapter automatically picks the best available model for the agent's
        task type and complexity, falling through tiers (Ollama → Groq → Gemini)
        as configured in the router.

        ``task_profile`` defaults to ``cls._class_spec.default_task_profile`` when
        the subclass declares one, so callers rarely need to pass it explicitly.

        Example::

            from ttadev.agents import DeveloperAgent
            from ttadev.primitives.llm import ModelRouterPrimitive, RouterModeConfig, RouterTierConfig

            router = ModelRouterPrimitive(
                modes={
                    "default": RouterModeConfig(
                        tiers=[
                            RouterTierConfig(provider="ollama"),
                            RouterTierConfig(provider="groq"),
                            RouterTierConfig(provider="google"),
                        ]
                    )
                },
                groq_api_key="...",
                gemini_api_key="...",
            )

            agent = DeveloperAgent.with_router(router)  # uses TaskProfile.coding(COMPLEX)
            result = await agent.execute(task, ctx)

        Args:
            router: A configured ``ModelRouterPrimitive`` instance.
            mode: Routing mode key in the router (default: ``"default"``).
            task_profile: Override the task profile from the spec. Pass ``None``
                to use the spec's ``default_task_profile`` automatically.
        """
        from ttadev.agents.adapter import ModelRouterChatAdapter

        # Resolve task_profile: explicit arg → spec default → None
        resolved_profile = task_profile
        if resolved_profile is None:
            class_spec = getattr(cls, "_class_spec", None)
            if class_spec is not None:
                resolved_profile = class_spec.default_task_profile

        adapter = ModelRouterChatAdapter(router, mode=mode, task_profile=resolved_profile)
        return cls(model=adapter)  # type: ignore[call-arg]
