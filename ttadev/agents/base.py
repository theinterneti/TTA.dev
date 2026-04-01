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


def _stub_handler(tool_name: str):  # type: ignore[return]
    """Return a placeholder tool handler that raises NotImplementedError when called."""

    def handler(args: dict) -> str:
        raise NotImplementedError(
            f"Tool '{tool_name}' has no handler — wire it in a subclass or integration layer"
        )

    return handler


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
                # Stub handler — subclasses or the integration layer must wire real ones.
                tool_handlers[tool.name] = _stub_handler(tool.name)

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
