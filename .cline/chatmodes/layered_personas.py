#!/usr/bin/env python3
"""
Layered Persona System - MCP-Native 5-Layer Architecture

18 specialized personas across 5 layers (L0-L4), each with 2-9 tools.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LayeredPersona:
    """Persona with layer-aware configuration and MCP stack."""
    
    name: str
    display_name: str
    layer: str  # L0, L1, L2, L3, L4
    description: str
    mcp_stack: list[str]  # 2-9 MCP servers
    cognitive_load: int  # Tool count
    tags: list[str] = field(default_factory=list)
    parent_layer: str | None = None
    child_layers: list[str] = field(default_factory=list)
    delegation_targets: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    token_budget: int = 4000
    
    def __post_init__(self):
        """Validate cognitive load limits."""
        if not (2 <= self.cognitive_load <= 9):
            raise ValueError(
                f"Cognitive load {self.cognitive_load} outside optimal range (2-9)"
            )


class LayeredPersonaRegistry:
    """Registry of all layered personas."""
    
    def __init__(self):
        self.personas: dict[str, LayeredPersona] = {}
        self._initialize_personas()
    
    def _initialize_personas(self):
        """Initialize all 18 layered personas."""
        
        # L0: META-CONTROL (2 personas)
        self.personas["system-overseer"] = LayeredPersona(
            name="system-overseer",
            display_name="System Overseer",
            layer="L0",
            description="Governance, cost monitoring, and agent mesh health",
            mcp_stack=["mcp-agent-monitor", "mcp-openai-cost", "mcp-sentry"],
            cognitive_load=3,
            tags=["meta", "governance", "monitoring"],
            child_layers=["L1"],
            token_budget=5000
        )
        
        self.personas["agent-provisioner"] = LayeredPersona(
            name="agent-provisioner",
            display_name="Agent Provisioner",
            layer="L0",
            description="Spawns/terminates agents based on load",
            mcp_stack=["mcp-k8s-admin", "mcp-docker", "mcp-aws-iam", "mcp-vault"],
            cognitive_load=4,
            tags=["meta", "provisioning", "scaling"],
            child_layers=["L2"],
            token_budget=4000
        )
        
        # L1: STRATEGY (3 personas)
        self.personas["prodmgr-orchestrator"] = LayeredPersona(
            name="prodmgr-orchestrator",
            display_name="Product Manager Orchestrator",
            layer="L1",
            description="Translates business intent to technical tasks",
            mcp_stack=["github", "sequential-thinking", "context7", "mcp-jira"],
            cognitive_load=4,
            tags=["strategy", "product", "planning"],
            parent_layer="L0",
            child_layers=["L2"],
            token_budget=4500
        )
        
        self.personas["devex-orchestrator"] = LayeredPersona(
            name="devex-orchestrator",
            display_name="Developer Experience Orchestrator",
            layer="L1",
            description="Human-to-machine interface and developer portal",
            mcp_stack=["github", "context7", "serena"],
            cognitive_load=3,
            tags=["strategy", "devex", "portal"],
            parent_layer="L0",
            child_layers=["L2", "L3"],
            token_budget=4000
        )
        
        self.personas["ciso-orchestrator"] = LayeredPersona(
            name="ciso-orchestrator",
            display_name="CISO Orchestrator",
            layer="L1",
            description="High-level security policy and risk management",
            mcp_stack=["mcp-grc-tool", "mcp-policy-engine", "sequential-thinking"],
            cognitive_load=3,
            tags=["strategy", "security", "policy"],
            parent_layer="L0",
            child_layers=["L2"],
            token_budget=4000
        )
        
        # L2: WORKFLOW MANAGEMENT (4 personas)
        self.personas["pipeline-manager"] = LayeredPersona(
            name="pipeline-manager",
            display_name="Pipeline Manager",
            layer="L2",
            description="Manages CI/CD flow and build artifacts",
            mcp_stack=["mcp-github-actions", "github", "mcp-docker-registry", "mcp-circleci"],
            cognitive_load=4,
            tags=["workflow", "cicd", "pipeline"],
            parent_layer="L1",
            child_layers=["L3"],
            token_budget=3500
        )
        
        self.personas["infra-manager"] = LayeredPersona(
            name="infra-manager",
            display_name="Infrastructure Manager",
            layer="L2",
            description="State management for cloud resources",
            mcp_stack=["mcp-terraform-cloud", "mcp-ansible-tower", "mcp-aws-resource-groups", "github", "sequential-thinking"],
            cognitive_load=5,
            tags=["workflow", "infrastructure", "cloud"],
            parent_layer="L1",
            child_layers=["L3", "L4"],
            token_budget=4000
        )
        
        self.personas["appsec-manager"] = LayeredPersona(
            name="appsec-manager",
            display_name="Application Security Manager",
            layer="L2",
            description="Code and dependency security management",
            mcp_stack=["mcp-snyk", "mcp-sonarqube", "mcp-dependabot", "github"],
            cognitive_load=4,
            tags=["workflow", "security", "code"],
            parent_layer="L1",
            child_layers=["L3", "L4"],
            token_budget=3500
        )
        
        self.personas["netsec-manager"] = LayeredPersona(
            name="netsec-manager",
            display_name="Network Security Manager",
            layer="L2",
            description="Network and perimeter security management",
            mcp_stack=["mcp-cloudflare", "mcp-aws-waf", "mcp-palo-alto", "mcp-tailscale"],
            cognitive_load=4,
            tags=["workflow", "security", "network"],
            parent_layer="L1",
            child_layers=["L3"],
            token_budget=3500
        )
        
        # L3: TOOL EXPERTS (7 personas)
        self.personas["git-flow-expert"] = LayeredPersona(
            name="git-flow-expert",
            display_name="Git Flow Expert",
            layer="L3",
            description="Branching, merging, and code review expertise",
            mcp_stack=["github", "gitmcp", "context7"],
            cognitive_load=3,
            tags=["expert", "git", "vcs"],
            parent_layer="L2",
            token_budget=3000
        )
        
        self.personas["db-data-expert"] = LayeredPersona(
            name="db-data-expert",
            display_name="Database & Data Expert",
            layer="L3",
            description="Database schemas, migrations, and queries",
            mcp_stack=["mcp-postgres", "mcp-mongodb", "mcp-redis", "context7"],
            cognitive_load=4,
            tags=["expert", "database", "data"],
            parent_layer="L2",
            child_layers=["L4"],
            token_budget=3500
        )
        
        self.personas["k8s-cluster-expert"] = LayeredPersona(
            name="k8s-cluster-expert",
            display_name="Kubernetes Cluster Expert",
            layer="L3",
            description="Kubernetes manifest and pod lifecycle",
            mcp_stack=["mcp-kubernetes", "mcp-helm", "mcp-argocd", "mcp-istio", "context7"],
            cognitive_load=5,
            tags=["expert", "kubernetes", "k8s"],
            parent_layer="L2",
            child_layers=["L4"],
            token_budget=4000
        )
        
        self.personas["observability-expert"] = LayeredPersona(
            name="observability-expert",
            display_name="Observability Expert",
            layer="L3",
            description="Metrics and distributed tracing",
            mcp_stack=["mcp-prometheus", "grafana", "mcp-honeycomb", "langfuse"],
            cognitive_load=4,
            tags=["expert", "observability", "metrics"],
            parent_layer="L2",
            token_budget=3500
        )
        
        self.personas["log-analysis-expert"] = LayeredPersona(
            name="log-analysis-expert",
            display_name="Log Analysis Expert",
            layer="L3",
            description="Log parsing and pattern matching",
            mcp_stack=["mcp-elasticsearch", "mcp-splunk", "mcp-datadog-logs"],
            cognitive_load=3,
            tags=["expert", "logs", "analysis"],
            parent_layer="L2",
            token_budget=3000
        )
        
        self.personas["testing-specialist"] = LayeredPersona(
            name="testing-specialist",
            display_name="Testing Specialist",
            layer="L3",
            description="Test automation and quality assurance",
            mcp_stack=["playwright", "github", "tta-primitives"],
            cognitive_load=3,
            tags=["expert", "testing", "qa"],
            parent_layer="L2",
            token_budget=3000
        )
        
        self.personas["frontend-developer"] = LayeredPersona(
            name="frontend-developer",
            display_name="Frontend Developer",
            layer="L3",
            description="UI/UX development and frontend expertise",
            mcp_stack=["playwright", "github", "serena", "context7"],
            cognitive_load=4,
            tags=["expert", "frontend", "ui"],
            parent_layer="L2",
            token_budget=3500
        )
        
        # L4: EXECUTION WRAPPERS (3 personas)
        self.personas["aws-api-wrapper"] = LayeredPersona(
            name="aws-api-wrapper",
            display_name="AWS API Wrapper",
            layer="L4",
            description="Direct AWS SDK execution",
            mcp_stack=["mcp-aws-sdk-python", "mcp-boto3", "mcp-cloudwatch"],
            cognitive_load=3,
            tags=["wrapper", "aws", "cloud"],
            parent_layer="L3",
            token_budget=2500
        )
        
        self.personas["kube-cli-wrapper"] = LayeredPersona(
            name="kube-cli-wrapper",
            display_name="Kubernetes CLI Wrapper",
            layer="L4",
            description="kubectl command execution",
            mcp_stack=["mcp-kubectl-cli", "mcp-k9s"],
            cognitive_load=2,
            tags=["wrapper", "kubernetes", "cli"],
            parent_layer="L3",
            token_budget=2000
        )
        
        self.personas["scanner-cli-wrapper"] = LayeredPersona(
            name="scanner-cli-wrapper",
            display_name="Security Scanner CLI Wrapper",
            layer="L4",
            description="Security scanning binary execution",
            mcp_stack=["mcp-trivy-cli", "mcp-zap-cli", "mcp-burpsuite-api"],
            cognitive_load=3,
            tags=["wrapper", "security", "scanning"],
            parent_layer="L3",
            token_budget=2500
        )
    
    def get_persona(self, name: str) -> LayeredPersona | None:
        """Get persona by name."""
        return self.personas.get(name)
    
    def get_personas_by_layer(self, layer: str) -> list[LayeredPersona]:
        """Get all personas in a specific layer."""
        return [p for p in self.personas.values() if p.layer == layer]
    
    def get_cognitive_load_stats(self) -> dict[str, Any]:
        """Get cognitive load statistics."""
        loads = [p.cognitive_load for p in self.personas.values()]
        
        return {
            "total_personas": len(self.personas),
            "total_tools": sum(loads),
            "avg_tools_per_persona": sum(loads) / len(loads),
            "min_tools": min(loads),
            "max_tools": max(loads),
        }


# Global registry
layered_persona_registry = LayeredPersonaRegistry()


if __name__ == "__main__":
    stats = layered_persona_registry.get_cognitive_load_stats()
    print(f"Layered Persona Architecture: {stats['total_personas']} personas")
    print(f"Average tools per persona: {stats['avg_tools_per_persona']:.1f}")
