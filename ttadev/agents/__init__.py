"""TTA.dev Role-Based Agent System.

Provides composable, role-based agents that wrap any ChatPrimitive model
with a domain-specific identity (system prompt, tools, quality gates).

Quick start::

    from ttadev.agents import DeveloperAgent
    from ttadev.primitives.integrations import AnthropicPrimitive

    agent = DeveloperAgent(model=AnthropicPrimitive())
    result = await agent.execute(
        AgentTask(instruction="Review this function", context={"code": "..."}),
        WorkflowContext(),
    )

Composable with other primitives::

    from ttadev.primitives.recovery import TimeoutPrimitive
    workflow = TimeoutPrimitive(30) >> agent
"""

from ttadev.agents.base import AgentPrimitive, QualityGateError
from ttadev.agents.developer import DEVELOPER_SPEC, DeveloperAgent
from ttadev.agents.devops import DEVOPS_SPEC, DevOpsAgent
from ttadev.agents.git import GIT_SPEC, GitAgent
from ttadev.agents.github import GITHUB_SPEC, GitHubAgent
from ttadev.agents.performance import PERFORMANCE_SPEC, PerformanceAgent
from ttadev.agents.protocol import ChatMessage, ChatPrimitive
from ttadev.agents.qa import QA_SPEC, QAAgent
from ttadev.agents.registry import AgentRegistry, get_registry, override_registry
from ttadev.agents.router import AgentRouterPrimitive
from ttadev.agents.security import SECURITY_SPEC, SecurityAgent
from ttadev.agents.spec import AgentSpec, AgentTool, HandoffTrigger, QualityGate, ToolRule
from ttadev.agents.task import AgentResult, AgentTask, Artifact
from ttadev.agents.tool_call_loop import ToolCallLoop, ToolCallLoopError, ToolDefinition

__all__ = [
    # Core
    "AgentPrimitive",
    "QualityGateError",
    # Spec types
    "AgentSpec",
    "AgentTool",
    "ToolRule",
    "QualityGate",
    "HandoffTrigger",
    # Task types
    "AgentTask",
    "AgentResult",
    "Artifact",
    # Protocol
    "ChatPrimitive",
    "ChatMessage",
    # Registry
    "AgentRegistry",
    "get_registry",
    "override_registry",
    # Router
    "AgentRouterPrimitive",
    # Tool call loop
    "ToolCallLoop",
    "ToolCallLoopError",
    "ToolDefinition",
    # Concrete agents
    "DeveloperAgent",
    "DEVELOPER_SPEC",
    "QAAgent",
    "QA_SPEC",
    "SecurityAgent",
    "SECURITY_SPEC",
    "DevOpsAgent",
    "DEVOPS_SPEC",
    "GitAgent",
    "GIT_SPEC",
    "GitHubAgent",
    "GITHUB_SPEC",
    "PerformanceAgent",
    "PERFORMANCE_SPEC",
]
