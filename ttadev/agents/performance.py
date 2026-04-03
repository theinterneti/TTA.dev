"""PerformanceAgent — Performance Engineer specialist."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ttadev.agents._utils import _matches
from ttadev.agents.base import AgentPrimitive
from ttadev.agents.registry import _global_registry
from ttadev.agents.spec import AgentSpec, AgentTool, HandoffTrigger, QualityGate, ToolRule
from ttadev.primitives.llm import COMPLEXITY_MODERATE, TASK_REASONING, TaskProfile

if TYPE_CHECKING:
    from ttadev.agents.protocol import ChatPrimitive

_DEVELOPER_KEYWORDS = frozenset(
    ["implement", "rewrite", "refactor", "fix the code", "change the implementation", "add caching"]
)
_DEVOPS_KEYWORDS = frozenset(
    ["scale", "horizontal scaling", "load balancer", "kubernetes", "autoscale", "infrastructure"]
)


PERFORMANCE_SPEC = AgentSpec(
    name="performance",
    role="Performance Engineer",
    system_prompt=(
        "You are a performance engineer specialising in Python application profiling, "
        "benchmarking, and optimisation.\n\n"
        "## Core Responsibilities\n"
        "- Profile CPU and memory usage to identify hotspots\n"
        "- Design and run benchmarks with statistically meaningful results\n"
        "- Analyse latency distributions (p50, p95, p99 — not just averages)\n"
        "- Identify database query inefficiencies (N+1, missing indexes, full scans)\n"
        "- Recommend caching strategies (in-process, Redis, CDN)\n"
        "- Identify memory leaks and excessive allocations\n"
        "- Design load tests to validate performance under realistic traffic\n\n"
        "## Profiling Tools\n"
        "- py-spy: sampling profiler — low overhead, works on running processes\n"
        "- memory-profiler: line-by-line memory usage analysis\n"
        "- pytest-benchmark: microbenchmarks integrated with the test suite\n"
        "- cProfile / line_profiler: deterministic profiling for offline analysis\n\n"
        "## Analysis Principles\n"
        "1. Measure before optimising — never guess at bottlenecks\n"
        "2. Establish a baseline before any change\n"
        "3. Optimise the biggest bottleneck first (Amdahl's Law)\n"
        "4. Validate every optimisation with a before/after benchmark\n"
        "5. Document why an optimisation was applied and what it achieved\n\n"
        "## Output Format\n"
        "Structure findings as: Observation → Root Cause → Recommendation → Expected Impact. "
        "Always include benchmark commands the user can run to reproduce your findings. "
        "Quantify expected improvements where possible (e.g. '40% reduction in p99 latency')."
    ),
    capabilities=[
        "profiling",
        "benchmarking",
        "latency analysis",
        "memory usage",
        "database query optimization",
        "caching strategy",
        "load testing",
        "bottleneck identification",
        "memory leak detection",
        "performance regression",
    ],
    tools=[
        AgentTool(
            "py-spy",
            "Sampling profiler — low-overhead CPU profiling of running processes",
            ToolRule.WHEN_INSTRUCTED,
        ),
        AgentTool(
            "pytest-benchmark",
            "Microbenchmark runner integrated with pytest",
            ToolRule.WHEN_INSTRUCTED,
        ),
        AgentTool(
            "memory-profiler",
            "Line-by-line memory usage analysis",
            ToolRule.WHEN_INSTRUCTED,
        ),
    ],
    quality_gates=[
        QualityGate(
            name="response_not_empty",
            check=lambda r: len(r.response.strip()) > 0,
            error_message="Agent returned an empty response.",
        ),
    ],
    handoff_triggers=[
        HandoffTrigger(
            condition=lambda t: _matches(t, _DEVELOPER_KEYWORDS),
            target_agent="developer",
            reason="Task requires code changes — routing to DeveloperAgent.",
        ),
        HandoffTrigger(
            condition=lambda t: _matches(t, _DEVOPS_KEYWORDS),
            target_agent="devops",
            reason="Task involves infrastructure scaling — routing to DevOpsAgent.",
        ),
    ],
    default_task_profile=TaskProfile(task_type=TASK_REASONING, complexity=COMPLEXITY_MODERATE),
)


class PerformanceAgent(AgentPrimitive):
    """Performance Engineer agent.

    Profiles CPU and memory, runs benchmarks, analyses latency distributions,
    and recommends caching and query optimisation strategies. Hands off to
    DeveloperAgent for code changes or DevOpsAgent for infrastructure scaling.

    Example::

        from ttadev.agents import PerformanceAgent
        from ttadev.primitives.integrations import AnthropicPrimitive

        agent = PerformanceAgent(model=AnthropicPrimitive())
        result = await agent.execute(
            AgentTask(instruction="Our API p99 latency spiked to 2s", context={}),
            WorkflowContext(),
        )
    """

    _class_spec: AgentSpec = PERFORMANCE_SPEC

    def __init__(self, model: ChatPrimitive) -> None:
        super().__init__(spec=PERFORMANCE_SPEC, model=model)


# Auto-register in the global registry on import.
_global_registry.register("performance", PerformanceAgent)
