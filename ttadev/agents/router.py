"""AgentRouterPrimitive — inspects a task and dispatches to the right agent."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ttadev.agents.registry import AgentRegistry, get_registry
from ttadev.agents.task import AgentResult, AgentTask
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.observability.instrumented_primitive import InstrumentedPrimitive

if TYPE_CHECKING:
    from ttadev.agents.protocol import ChatPrimitive

# Minimum keyword-match score margin to route without an LLM call.
_ROUTING_CONFIDENCE_THRESHOLD = 0.25


def _score_agent(instruction: str, capabilities: list[str]) -> float:
    """Score an agent by keyword overlap with the instruction.

    A capability matches if the full phrase appears in the instruction, OR
    if the majority of its words appear individually (for multi-word capabilities).
    """
    text = instruction.lower()
    if not capabilities:
        return 0.0

    score = 0.0
    for cap in capabilities:
        cap_lower = cap.lower()
        if cap_lower in text:
            score += 1.0
        else:
            words = cap_lower.split()
            if len(words) > 1:
                word_hits = sum(1 for w in words if w in text)
                score += word_hits / len(words)

    return score / len(capabilities)


class AgentRouterPrimitive(InstrumentedPrimitive[AgentTask, AgentResult]):
    """Routes a task to the best-fit registered agent.

    Routing priority:
    1. ``task.agent_hint`` — if set and valid, use it directly (no LLM call)
    2. Keyword scoring — if top agent's score margin exceeds threshold, dispatch
    3. LLM fallback — ask orchestrator model to choose from agent descriptions

    Example::

        router = AgentRouterPrimitive(model=AnthropicPrimitive(), orchestrator=AnthropicPrimitive())
        result = await router.execute(
            AgentTask(instruction="our test suite is flaky", context={}),
            WorkflowContext(),
        )
        # Routes to QAAgent automatically
    """

    def __init__(
        self,
        model: ChatPrimitive,
        orchestrator: ChatPrimitive,
        registry: AgentRegistry | None = None,
    ) -> None:
        super().__init__(name="agent_router")
        self._model = model
        self._orchestrator = orchestrator
        # Registry resolved at call time if not provided at init
        self._registry = registry

    async def _execute_impl(self, task: AgentTask, ctx: WorkflowContext) -> AgentResult:
        registry = self._registry or get_registry()
        agent_classes = registry.all()

        # 1. agent_hint short-circuit
        if task.agent_hint:
            try:
                agent_class = registry.get(task.agent_hint)
                agent = agent_class(model=self._model)
                result = await agent.execute(task, ctx)
                return result
            except KeyError:
                pass  # unknown hint — fall through to scoring

        # 2. Keyword scoring — use class-level _class_spec to avoid instantiation
        scores: dict[str, float] = {}
        for agent_class in agent_classes:
            spec = getattr(agent_class, "_class_spec", None)
            if spec is None:
                # Fallback for agents without _class_spec: instantiate temporarily
                spec = agent_class(model=self._model).spec
            caps = spec.capabilities
            name = spec.name
            scores[name] = _score_agent(task.instruction, caps)

        if scores:
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            best_name, best_score = sorted_scores[0]
            second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0
            margin = best_score - second_score

            if best_score > 0 and margin >= _ROUTING_CONFIDENCE_THRESHOLD:
                agent = registry.get(best_name)(model=self._model)
                return await agent.execute(task, ctx)

        # 3. LLM fallback — read specs from class attribute without instantiation
        agent_descriptions = "\n".join(
            f"- {spec.name}: {', '.join(spec.capabilities)}"
            for ac in agent_classes
            for spec in [getattr(ac, "_class_spec", None) or ac(model=self._model).spec]
        )
        prompt = (
            f"Choose the best agent for this task: {task.instruction!r}\n\n"
            f"Available agents:\n{agent_descriptions}\n\n"
            "Reply with only the agent name."
        )
        chosen_name = await self._orchestrator.chat(
            [{"role": "user", "content": prompt}],
            system=None,
            ctx=ctx,
        )
        chosen_name = chosen_name.strip().lower()

        try:
            agent = registry.get(chosen_name)(model=self._model)
        except KeyError:
            # Fallback: use first registered agent
            if agent_classes:
                agent = agent_classes[0](model=self._model)
            else:
                raise RuntimeError("No agents registered in registry.")

        return await agent.execute(task, ctx)
