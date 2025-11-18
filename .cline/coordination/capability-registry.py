#!/usr/bin/env python3
"""
Agent Capability Registry - Central Registry of All Available Agent Capabilities

This module provides the central registry for all TTA.dev agent capabilities,
enabling dynamic discovery and coordination of personas, primitives, workflows,
and MCP tools. It serves as the backbone of the AGENTS.md orchestration hub.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Capability:
    """Represents a specific agent capability"""

    name: str
    category: str
    description: str
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    status: str = "active"  # active, inactive, maintenance
    health_score: float = 1.0  # 0.0 to 1.0
    last_health_check: datetime | None = None
    dependencies: list[str] = field(default_factory=list)
    capabilities: dict[str, Any] = field(default_factory=dict)
    usage_stats: dict[str, Any] = field(default_factory=dict)

    @property
    def is_available(self) -> bool:
        """Check if capability is currently available"""
        return self.status == "active" and self.health_score >= 0.8


@dataclass
class CoordinationSession:
    """Represents an active multi-agent coordination session"""

    session_id: str
    task_description: str
    participants: list[str]  # agent types/IDs involved
    coordinator: str  # primary coordinating agent
    started_at: datetime = field(default_factory=datetime.now)
    status: str = "active"  # active, completed, failed
    capabilities_used: list[str] = field(default_factory=list)
    success: bool = False


class AgentCapabilityRegistry:
    """
    Central registry of all available agent capabilities.

    Serves as the system of record for what each agent can do and coordinates
    capability discovery and routing for the orchestration layer.
    """

    def __init__(self):
        self.personas: dict[str, Capability] = {}
        self.primitives: dict[str, Capability] = {}
        self.workflows: dict[str, Capability] = {}
        self.mcp_servers: dict[str, Capability] = {}
        self.memory_patterns: dict[str, Capability] = {}
        self.active_sessions: dict[str, CoordinationSession] = {}

        # Initialize registry
        self._load_built_in_capabilities()
        self._load_dynamic_capabilities()

    def _load_built_in_capabilities(self):
        """Load capabilities that are built into the TTA.dev framework"""

        # Load personas
        self._load_personas()

        # Load primitives
        self._load_primitives()

        # Load workflows
        self._load_workflows()

        # Load MCP servers
        self._load_mcp_servers()

    def _load_personas(self):
        """Load available persona configurations"""

        personas_config = {
            "backend-developer": {
                "description": "Specialized in Python backend development and workflow primitives",
                "tags": ["backend", "python", "api", "database", "workflow"],
                "capabilities": {
                    "languages": ["python"],
                    "paradigms": ["async", "composable"],
                    "tools": ["pytest", "ruff", "pyright"],
                    "domains": [
                        "api-development",
                        "data-processing",
                        "workflow-orchestration",
                    ],
                },
            },
            "frontend-developer": {
                "description": "Specialized in UI/UX development and user interface patterns",
                "tags": ["frontend", "ui", "javascript", "react", "typescript"],
                "capabilities": {
                    "languages": ["javascript", "typescript"],
                    "frameworks": ["react", "vue", "angular"],
                    "tools": ["webpack", "babel", "eslint"],
                    "domains": ["user-experience", "responsive-design"],
                },
            },
            "testing-specialist": {
                "description": "Expert in testing methodologies and quality assurance",
                "tags": ["testing", "qa", "tdd", "coverage", "validation"],
                "capabilities": {
                    "paradigms": ["tdd", "bdd"],
                    "tools": ["pytest", "coverage", "playwright"],
                    "expertise": [
                        "unit-testing",
                        "integration-testing",
                        "performance-testing",
                    ],
                },
            },
            "devops-engineer": {
                "description": "Infrastructure and deployment automation expert",
                "tags": [
                    "infrastructure",
                    "deployment",
                    "ci/cd",
                    "containers",
                    "cloud",
                ],
                "capabilities": {
                    "platforms": ["aws", "gcp", "azure", "kubernetes", "docker"],
                    "tools": ["terraform", "ansible", "jenkins", "github-actions"],
                    "expertise": ["infrastructure-as-code", "monitoring", "scaling"],
                },
            },
            "observability-expert": {
                "description": "Metrics, tracing, and monitoring systems expert",
                "tags": ["monitoring", "metrics", "tracing", "logging", "alerting"],
                "capabilities": {
                    "tools": ["opentelemetry", "prometheus", "grafana"],
                    "platforms": ["jaeger", "datadog", "new-relic"],
                    "expertise": [
                        "distributed-tracing",
                        "metric-collection",
                        "alert-configuration",
                    ],
                },
            },
            "data-scientist": {
                "description": "Machine learning and data analysis specialist",
                "tags": ["data", "ml", "statistics", "visualization", "analysis"],
                "capabilities": {
                    "languages": ["python", "r", "sql"],
                    "libraries": ["pandas", "numpy", "scikit-learn", "tensorflow"],
                    "tools": ["jupyter", "mlflow", "dvc"],
                    "expertise": [
                        "data-processing",
                        "machine-learning",
                        "statistical-analysis",
                    ],
                },
            },
        }

        for name, config in personas_config.items():
            capability = Capability(
                name=name,
                category="persona",
                description=config["description"],
                tags=config["tags"],
                capabilities=config["capabilities"],
                usage_stats={"activation_count": 0, "last_activated": None},
            )
            self.personas[name] = capability

    def _load_primitives(self):
        """Load available workflow primitives"""

        primitives_config = {
            "SequentialPrimitive": {
                "description": "Execute steps in sequence with error propagation",
                "tags": ["workflow", "sequential", "composition"],
                "capabilities": {"max_steps": 20, "error_handling": True},
            },
            "ParallelPrimitive": {
                "description": "Execute steps concurrently with result aggregation",
                "tags": ["workflow", "parallel", "performance"],
                "capabilities": {"max_concurrent": 10, "aggregation": True},
            },
            "RouterPrimitive": {
                "description": "Route execution based on dynamic conditions",
                "tags": ["workflow", "routing", "conditional"],
                "capabilities": {"dynamic_routing": True, "performance_routing": True},
            },
            "RetryPrimitive": {
                "description": "Automatic retry with exponential backoff",
                "tags": ["recovery", "retry", "reliability"],
                "capabilities": {"strategies": ["fixed", "linear", "exponential"]},
            },
            "FallbackPrimitive": {
                "description": "Graceful degradation with fallback strategies",
                "tags": ["recovery", "fallback", "resilience"],
                "capabilities": {"max_fallbacks": 5, "circuit_breaker": True},
            },
            "TimeoutPrimitive": {
                "description": "Circuit breaker pattern with timeout protection",
                "tags": ["recovery", "timeout", "circuit-breaker"],
                "capabilities": {"timeout_precision": "ms", "fallback_support": True},
            },
            "CachePrimitive": {
                "description": "LRU cache with TTL and configurable key functions",
                "tags": ["performance", "cache", "optimization"],
                "capabilities": {
                    "cache_types": ["lru", "ttl"],
                    "key_customization": True,
                },
            },
        }

        for name, config in primitives_config.items():
            capability = Capability(
                name=name,
                category="primitive",
                description=config["description"],
                tags=config["tags"],
                capabilities=config["capabilities"],
                usage_stats={"invocation_count": 0, "success_rate": 1.0},
            )
            self.primitives[name] = capability

    def _load_workflows(self):
        """Load available workflow templates"""

        workflows_config = {
            "primitive-development": {
                "description": "Complete workflow for developing new TTA.dev primitives",
                "tags": ["development", "primitive", "tdd", "validation"],
                "capabilities": {"stages": 5, "validation_gates": 3},
            },
            "integration-testing": {
                "description": "Comprehensive testing workflow for primitive integration",
                "tags": ["testing", "integration", "quality", "validation"],
                "capabilities": {"test_types": ["unit", "integration", "performance"]},
            },
        }

        for name, config in workflows_config.items():
            capability = Capability(
                name=name,
                category="workflow",
                description=config["description"],
                tags=config["tags"],
                capabilities=config["capabilities"],
                usage_stats={"run_count": 0, "avg_duration": 0},
            )
            self.workflows[name] = capability

    def _load_mcp_servers(self):
        """Load available MCP servers and their capabilities"""

        mcp_servers_config = {
            "tta-dev-primitives": {
                "description": "Complete TTA.dev primitives MCP server",
                "tags": [
                    "tta-dev",
                    "primitives",
                    "workflow",
                    "orchestration",
                    "context",
                ],
                "capabilities": {
                    "tools_count": 14,
                    "categories": [
                        "workflow",
                        "recovery",
                        "performance",
                        "testing",
                        "context",
                    ],
                },
            },
            "context7": {
                "description": "Library documentation search and retrieval",
                "tags": ["documentation", "research", "learning"],
                "capabilities": {"specialization": "library_docs"},
            },
            "playwright": {
                "description": "Browser automation and testing",
                "tags": ["testing", "automation", "frontend"],
                "capabilities": {"browser_support": ["chromium"]},
            },
        }

        for name, config in mcp_servers_config.items():
            capability = Capability(
                name=name,
                category="mcp_server",
                description=config["description"],
                tags=config["tags"],
                capabilities=config["capabilities"],
                usage_stats={"query_count": 0, "response_time_avg": 0},
            )
            self.mcp_servers[name] = capability

    def _load_dynamic_capabilities(self):
        """Load capabilities that may change at runtime"""
        # Load memory patterns
        self._load_memory_patterns()

    def _load_memory_patterns(self):
        """Load learned patterns from memory system"""
        try:
            from memory.memory_manager import memory_manager

            # Get popular patterns from memory
            patterns = memory_manager.get_popular_patterns(10)

            for pattern in patterns:
                capability = Capability(
                    name=f"learned_{pattern['id']}",
                    category="memory_pattern",
                    description=f"Learned pattern: {pattern['description']}",
                    tags=["learned", "pattern", "memory"],
                    capabilities={"complexity": pattern["complexity_score"]},
                    usage_stats={"usage_count": pattern["usage_count"]},
                )
                self.memory_patterns[capability.name] = capability

        except ImportError:
            # Memory system not available yet
            pass

    def register_capability(self, category: str, name: str, capability: Capability):
        """Dynamically register a new capability"""
        registries = {
            "persona": self.personas,
            "primitive": self.primitives,
            "workflow": self.workflows,
            "mcp_server": self.mcp_servers,
            "memory_pattern": self.memory_patterns,
        }

        if category in registries:
            registries[category][name] = capability

    def get_capabilities_for_task(self, task_description: str) -> dict[str, Any]:
        """
        Return optimal capability mix for a task.

        Analyzes the task and provides:
        - Recommended personas
        - Required primitives
        - Suggested workflows
        - Relevant MCP tools
        """
        task_lower = task_description.lower()

        # Analyze task requirements
        task_analysis = self._analyze_task_requirements(task_description)

        # Find matching capabilities
        recommendations = {
            "personas": self._find_matching_personas(task_analysis),
            "primitives": self._find_required_primitives(task_analysis),
            "workflows": self._find_suitable_workflows(task_analysis),
            "mcp_servers": self._find_useful_mcp_servers(task_analysis),
            "confidence_score": self._calculate_confidence(task_analysis),
            "estimated_complexity": self._estimate_complexity(task_analysis),
        }

        return recommendations

    def _analyze_task_requirements(self, task: str) -> dict[str, Any]:
        """Analyze task to extract capability requirements"""

        analysis = {
            "domain": self._identify_domain(task),
            "complexity": self._assess_complexity(task),
            "paradigm": self._identify_paradigm(task),
            "quality_requirements": self._identify_quality_needs(task),
            "keywords": self._extract_keywords(task),
        }

        return analysis

    def _identify_domain(self, task: str) -> str:
        """Identify the primary domain of the task"""
        task_lower = task.lower()

        domains = {
            "backend": ["backend", "api", "server", "database", "async", "workflow"],
            "frontend": [
                "frontend",
                "ui",
                "component",
                "react",
                "javascript",
                "typescript",
            ],
            "testing": ["test", "testing", "qa", "validation", "coverage", "tdd"],
            "infrastructure": ["deployment", "kubernetes", "docker", "ci/cd", "infra"],
            "data": ["data", "ml", "machine learning", "statistics", "analysis"],
            "observability": ["monitoring", "tracing", "metrics", "logging"],
        }

        for domain, keywords in domains.items():
            if any(keyword in task_lower for keyword in keywords):
                return domain

        return "general"

    def _assess_complexity(self, task: str) -> str:
        """Assess task complexity level"""
        complexity_indicators = {
            "workflow": ["orchestrate", "coordinate", "pipeline", "complex"],
            "integration": ["integrate", "connect", "cross", "multiple"],
            "architecture": ["design", "architecture", "system", "enterprise"],
            "optimization": ["optimize", "performance", "scale", "efficient"],
        }

        task_lower = task.lower()
        complexity_score = 0

        for level, indicators in complexity_indicators.items():
            if any(indicator in task_lower for indicator in indicators):
                complexity_score += 1

        if complexity_score >= 3:
            return "high"
        elif complexity_score >= 2:
            return "medium"
        else:
            return "low"

    def _identify_paradigm(self, task: str) -> str:
        """Identify programming paradigm requirements"""
        task_lower = task.lower()

        if "async" in task_lower or "await" in task_lower:
            return "asynchronous"
        elif "primitive" in task_lower or "workflow" in task_lower:
            return "composable"
        elif "test" in task_lower:
            return "validation"
        else:
            return "imperative"

    def _identify_quality_needs(self, task: str) -> list[str]:
        """Identify quality requirements for the task"""
        requirements = []

        task_lower = task.lower()

        if "test" in task_lower or "testing" in task_lower:
            requirements.append("testing")
        if "performance" in task_lower or "fast" in task_lower:
            requirements.append("performance")
        if "reliable" in task_lower or "resilient" in task_lower:
            requirements.append("resilience")
        if "observable" in task_lower or "metrics" in task_lower:
            requirements.append("observability")

        return requirements

    def _extract_keywords(self, task: str) -> list[str]:
        """Extract relevant keywords from task description"""
        # Simple keyword extraction - could be enhanced with NLP
        keywords = []
        words = task.lower().split()

        for word in words:
            if len(word) > 3 and word not in [
                "that",
                "with",
                "this",
                "from",
                "have",
                "will",
            ]:
                keywords.append(word)

        return keywords[:5]  # Limit to top keywords

    def _find_matching_personas(self, analysis: dict) -> list[dict]:
        """Find personas that match task requirements"""
        matches = []

        for name, persona in self.personas.items():
            score = 0

            # Domain match
            if analysis["domain"] in [tag.replace("-", "") for tag in persona.tags]:
                score += 3

            # Capability match
            persona_domain = analysis["domain"]
            persona_capabilities = persona.capabilities

            if persona_domain == "backend" and "python" in str(persona_capabilities):
                score += 2
            elif persona_domain == "frontend" and "javascript" in str(
                persona_capabilities
            ):
                score += 2
            elif persona_domain == "testing" and "testing" in str(persona_capabilities):
                score += 2

            # Paradigm match
            if analysis["paradigm"] == "asynchronous" and "async" in str(
                persona_capabilities
            ):
                score += 1
            if analysis["paradigm"] == "composable" and "workflow" in str(
                persona_capabilities
            ):
                score += 1

            if score >= 2:  # Minimum threshold
                matches.append(
                    {
                        "persona": name,
                        "score": score,
                        "capabilities": persona.capabilities,
                        "description": persona.description,
                    }
                )

        return sorted(matches, key=lambda x: x["score"], reverse=True)[:3]

    def _find_required_primitives(self, analysis: dict) -> list[dict]:
        """Find primitives required for the task"""
        matches = []

        for name, primitive in self.primitives.items():
            relevance = 0

            # Domain-based matching
            if analysis["domain"] == "backend" and "workflow" in primitive.tags:
                relevance = 3
            elif analysis["domain"] == "testing" and "testing" in primitive.tags:
                relevance = 3

            # Paradigm matching
            if (
                analysis["paradigm"] == "asynchronous"
                and "async" in primitive.capabilities
            ):
                relevance += 2
            if analysis["paradigm"] == "composable" and "composition" in primitive.tags:
                relevance += 2

            # Quality requirements
            for req in analysis["quality_requirements"]:
                if req in [tag.replace("_", "") for tag in primitive.tags]:
                    relevance += 1

            if relevance > 0:
                matches.append(
                    {
                        "primitive": name,
                        "category": primitive.category,
                        "relevance": relevance,
                        "description": primitive.description,
                        "capabilities": primitive.capabilities,
                    }
                )

        return sorted(matches, key=lambda x: x["relevance"], reverse=True)[:5]

    def _find_suitable_workflows(self, analysis: dict) -> list[dict]:
        """Find workflows suitable for the task"""
        matches = []

        for name, workflow in self.workflows.items():
            suitability = 0

            # Match based on tags
            if analysis["domain"] in [tag.replace("-", "") for tag in workflow.tags]:
                suitability += 3

            if analysis["complexity"] == "high" and "tdd" in workflow.tags:
                suitability += 2
            elif analysis["complexity"] == "medium" and "integration" in workflow.tags:
                suitability += 2

            if suitability > 0:
                matches.append(
                    {
                        "workflow": name,
                        "suitability": suitability,
                        "stages": workflow.capabilities.get("stages", 0),
                        "description": workflow.description,
                    }
                )

        return sorted(matches, key=lambda x: x["suitability"], reverse=True)[:2]

    def _find_useful_mcp_servers(self, analysis: dict) -> list[dict]:
        """Find MCP servers useful for the task"""
        matches = []

        for name, server in self.mcp_servers.items():
            usefulness = 0

            # TTA.dev primitives server is always relevant for development tasks
            if name == "tta-dev-primitives" and analysis["domain"] in [
                "backend",
                "general",
            ]:
                usefulness += 5

            # Domain-specific servers
            if analysis["domain"] == "testing" and "testing" in str(
                server.capabilities
            ):
                usefulness += 3
            elif analysis["domain"] == "frontend" and "frontend" in server.tags:
                usefulness += 3

            if usefulness > 0:
                matches.append(
                    {
                        "server": name,
                        "usefulness": usefulness,
                        "tools_count": server.capabilities.get("tools_count", 0),
                        "description": server.description,
                    }
                )

        return sorted(matches, key=lambda x: x["usefulness"], reverse=True)[:3]

    def _calculate_confidence(self, analysis: dict) -> float:
        """Calculate overall confidence in recommendations"""
        base_confidence = 0.7

        # Adjust based on analysis quality
        if analysis["domain"] != "general":
            base_confidence += 0.1

        if len(analysis["keywords"]) >= 3:
            base_confidence += 0.1

        if analysis["complexity"] == "high":
            base_confidence -= 0.05  # Complex tasks harder to analyze

        return min(base_confidence, 1.0)

    def _estimate_complexity(self, analysis: dict) -> str:
        """Estimate overall task complexity"""
        return analysis["complexity"]

    def create_coordination_session(
        self, task: str, participants: list[str], coordinator: str = "cline"
    ) -> str:
        """Create a new coordination session"""
        import uuid

        session_id = str(uuid.uuid4())[:8]

        session = CoordinationSession(
            session_id=session_id,
            task_description=task,
            participants=participants,
            coordinator=coordinator,
        )

        self.active_sessions[session_id] = session
        return session_id

    def get_registry_status(self) -> dict[str, Any]:
        """Get current status of the capability registry"""
        return {
            "personas": {
                "count": len(self.personas),
                "active": len([p for p in self.personas.values() if p.is_available]),
            },
            "primitives": {
                "count": len(self.primitives),
                "active": len([p for p in self.primitives.values() if p.is_available]),
            },
            "workflows": {
                "count": len(self.workflows),
                "active": len([w for w in self.workflows.values() if w.is_available]),
            },
            "mcp_servers": {
                "count": len(self.mcp_servers),
                "active": len([s for s in self.mcp_servers.values() if s.is_available]),
            },
            "active_sessions": len(self.active_sessions),
            "last_updated": datetime.now().isoformat(),
        }


# Global registry instance
capability_registry = AgentCapabilityRegistry()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "status":
            status = capability_registry.get_registry_status()
            print("Capability Registry Status:")
            for category, info in status.items():
                if isinstance(info, dict):
                    print(
                        f"  {category}: {info.get('active', info)}/{info.get('count', '?')} active"
                    )
                else:
                    print(f"  {category}: {info}")

        elif command == "analyze":
            if len(sys.argv) > 2:
                task = " ".join(sys.argv[2:])
                recommendations = capability_registry.get_capabilities_for_task(task)

                print(f"Capability Recommendations for: '{task}'")
                print(
                    f"Domain: {recommendations.get('task_analysis', {}).get('domain', 'unknown')}"
                )

                if recommendations.get("personas"):
                    print("\nRecommended Personas:")
                    for persona in recommendations["personas"][:2]:
                        print(f"  • {persona['persona']} (score: {persona['score']})")

                if recommendations.get("primitives"):
                    print("\nRequired Primitives:")
                    for primitive in recommendations["primitives"][:3]:
                        print(
                            f"  • {primitive['primitive']} (relevance: {primitive['relevance']})"
                        )

        else:
            print("Commands: status, analyze <task>")

    else:
        print("Agent Capability Registry")
        status = capability_registry.get_registry_status()
        print("Registry initialized with:")
        print(f"  {status['personas']['count']} personas")
        print(f"  {status['primitives']['count']} primitives")
        print(f"  {status['workflows']['count']} workflows")
        print(f"  {status['mcp_servers']['count']} MCP servers")
        print("Ready for agent coordination!")
