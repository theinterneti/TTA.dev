#!/usr/bin/env python3
"""
Agent Capability Registry - Central Registry of All Available Agent Capabilities

This module provides the central registry for all TTA.dev agent capabilities,
enabling dynamic discovery and coordination of personas, primitives, workflows,
and MCP tools. It serves as the backbone of the AGENTS.md orchestration hub.

Layer-Aware Enhancement:
- Integrated layered persona system with delegation chains
- MCP stack assignment per layer
- Multi-layer task routing
- Coordination session management
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Import layered persona system
try:
    from .chatmodes.layered_personas import LayeredPersona, layered_persona_registry
except ImportError:
    layered_persona_registry = None


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
    delegation_chain: list[dict] = field(default_factory=list)  # Layered delegation


@dataclass
class DelegationChain:
    """Represents a delegation chain from L0 to L4"""

    task_description: str
    layers_involved: list[str]
    mcp_stack: dict[str, list[str]]  # Layer -> MCP servers
    delegation_path: list[dict]  # Chain of delegation decisions
    success: bool = False
    confidence_score: float = 1.0


class AgentCapabilityRegistry:
    """
    Central registry of all available agent capabilities.

    Serves as the system of record for what each agent can do and coordinates
    capability discovery and routing for the orchestration layer.

    Layer-Aware Enhancements:
    - Integrated with layered persona system
    - Builds delegation chains for complex tasks
    - Assigns MCP stacks per layer
    - Supports multi-layer task routing
    """

    def __init__(self):
        self.personas: dict[str, Capability] = {}
        self.primitives: dict[str, Capability] = {}
        self.workflows: dict[str, Capability] = {}
        self.mcp_servers: dict[str, Capability] = {}
        self.memory_patterns: dict[str, Capability] = {}
        self.active_sessions: dict[str, CoordinationSession] = {}
        self.delegation_chains: dict[str, DelegationChain] = {}

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

        # Load from .hypertool/mcp_servers.json if available
        dynamic_servers = self._load_mcp_servers_from_config()

        # Fallback to built-in configs if file not found
        if not dynamic_servers:
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

    def _load_mcp_servers_from_config(self):
        """Load MCP servers from .hypertool/mcp_servers.json"""
        try:
            import json
            from pathlib import Path

            # Find the config file relative to TTA.dev root
            project_root = Path(__file__).parent.parent.parent
            config_file = project_root / ".hypertool" / "mcp_servers.json"

            if not config_file.exists():
                # Try different possible locations
                possible_paths = [
                    Path.cwd() / ".hypertool" / "mcp_servers.json",
                    Path.cwd().parent / ".hypertool" / "mcp_servers.json",
                    Path(__file__).parent.parent / ".hypertool" / "mcp_servers.json",
                ]

                for path in possible_paths:
                    if path.exists():
                        config_file = path
                        break

            if not config_file.exists():
                return False

            with open(config_file) as f:
                config_data = json.load(f)

            servers_loaded = 0
            for server_name, server_config in config_data.get("mcpServers", {}).items():
                # Extract layer information from tags
                layer_tag = None
                filtered_tags = []
                for tag in server_config.get("tags", []):
                    if tag.startswith("layer:"):
                        layer_tag = tag[6:]  # Remove "layer:" prefix
                    else:
                        filtered_tags.append(tag)

                # Create capability
                capability = Capability(
                    name=server_name,
                    category="mcp_server",
                    description=server_config.get(
                        "description", f"MCP server: {server_name}"
                    ),
                    tags=[f"layer:{layer_tag}" if layer_tag else None, *filtered_tags],
                    capabilities=self._extract_mcp_capabilities(server_config),
                    usage_stats={"query_count": 0, "response_time_avg": 0},
                )

                # Remove None values from tags
                capability.tags = [tag for tag in capability.tags if tag is not None]

                self.mcp_servers[server_name] = capability
                servers_loaded += 1

            return servers_loaded > 0

        except Exception:
            # Silently fail and use fallback
            return False

    def _extract_mcp_capabilities(self, server_config):
        """Extract capabilities from MCP server configuration"""
        capabilities = {}

        # Add command type
        if "command" in server_config:
            capabilities["command_type"] = server_config["command"]

        # Add environment requirements
        if "env" in server_config:
            capabilities["env_requirements"] = list(server_config["env"].keys())

        # Add layer information
        for tag in server_config.get("tags", []):
            if tag.startswith("layer:"):
                capabilities["layer"] = tag[6:]  # Remove "layer:" prefix

        # Add original capabilities if they exist
        if "capabilities" in server_config:
            capabilities.update(server_config.get("capabilities", {}))

        return capabilities

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
        Return optimal capability mix for a task (legacy method).

        For new layered routing, use get_capabilities_for_task_layered().
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

    def get_capabilities_for_task_layered(
        self, task_description: str
    ) -> dict[str, Any]:
        """
        Layer-Aware Task Analysis and Routing.

        Analyzes task and returns optimized layer-based capability mix:
        - Delegation chain from L0 to L4
        - MCP stack assignments per layer
        - Layer-appropriate personas with cognitive load distribution

        Returns enhanced recommendations with:
        - layered_personas: Layer-organized persona recommendations
        - delegation_chain: Step-by-step delegation path
        - mcp_stacks: Layer-specific MCP server assignments
        - coordination_sessions: Multi-layer coordination setup
        """
        if not layered_persona_registry:
            # Fallback to non-layered analysis
            return self.get_capabilities_for_task(task_description)

        # Analyze task requirements (enhanced with layering)
        task_analysis = self._analyze_task_requirements_layered(task_description)

        # Build delegation chain
        delegation_chain = self._build_delegation_chain(task_analysis)

        # Find layer-appropriate personas
        layered_personas = self._find_layered_personas(task_analysis, delegation_chain)

        # Assign MCP stacks per layer
        mcp_stacks = self._assign_mcp_stacks(delegation_chain)

        # Generate coordination recommendations
        coordination = self._generate_coordination_strategy(
            task_analysis, delegation_chain
        )

        recommendations = {
            "task_analysis": task_analysis,
            "layered_personas": layered_personas,
            "delegation_chain": delegation_chain.delegation_path,
            "mcp_stacks": mcp_stacks,
            "coordination": coordination,
            "confidence_score": delegation_chain.confidence_score,
            "estimated_complexity": task_analysis.get("layer_complexity", "medium"),
        }

        # Store delegation chain for coordination
        import uuid

        chain_id = str(uuid.uuid4())[:8]
        self.delegation_chains[chain_id] = delegation_chain

        return recommendations

    def _analyze_task_requirements_layered(self, task: str) -> dict[str, Any]:
        """Enhanced task analysis with layering considerations"""

        # Base analysis
        base_analysis = self._analyze_task_requirements(task)

        # Add layered insights
        layered_insights = {
            "required_layers": self._identify_required_layers(task),
            "coordination_complexity": self._assess_coordination_complexity(task),
            "layer_complexity": self._estimate_layer_complexity(task),
            "parallelization_opportunities": self._identify_parallel_ops(task),
            "delegation_points": self._identify_delegation_points(task),
        }

        # Combine analyses
        analysis = base_analysis.copy()
        analysis.update(layered_insights)

        return analysis

    def _identify_required_layers(self, task: str) -> list[str]:
        """Determine which layers are needed for this task"""

        task_lower = task.lower()
        required_layers = []

        # L0: Always needed for coordination
        required_layers.append("L0")

        # L1: Strategy tasks
        if any(
            word in task_lower
            for word in ["plan", "strategy", "coordinate", "organize"]
        ):
            required_layers.append("L1")

        # L2: Complex workflow tasks
        if any(
            word in task_lower
            for word in ["deploy", "infrastructure", "pipeline", "ci/cd"]
        ):
            required_layers.append("L2")

        # L3: Technical implementation
        if any(
            word in task_lower for word in ["implement", "code", "develop", "build"]
        ):
            required_layers.append("L3")

        # L4: Direct execution
        if any(word in task_lower for word in ["execute", "run", "call", "direct"]):
            required_layers.append("L4")

        # Ensure minimum layers
        if len(required_layers) < 2:
            required_layers.extend(["L1", "L3"])

        # Sort for proper delegation order
        return sorted(list(set(required_layers)))

    def _assess_coordination_complexity(self, task: str) -> str:
        """Assess how complex the coordination needed will be"""

        complexity_indicators = [
            len(task.split()),  # Word count
            task.count(","),  # Comma count (indicating multiple steps)
            len(self._extract_keywords(task)),  # Keyword diversity
        ]

        avg_complexity = sum(complexity_indicators) / len(complexity_indicators)

        if avg_complexity > 8:
            return "high"
        elif avg_complexity > 4:
            return "medium"
        else:
            return "low"

    def _estimate_layer_complexity(self, task: str) -> str:
        """Estimate overall complexity considering layers"""

        base_complexity = self._assess_complexity(task)
        layers_needed = len(self._identify_required_layers(task))

        # Layer count influences complexity
        if base_complexity == "high" or layers_needed >= 4:
            return "high"
        elif base_complexity == "medium" or layers_needed >= 3:
            return "medium"
        else:
            return "low"

    def _identify_parallel_ops(self, task: str) -> list[str]:
        """Identify opportunities for parallel execution"""

        task_lower = task.lower()
        parallel_ops = []

        if "and" in task_lower:
            parallel_ops.append("concurrent_steps")

        if "parallel" in task_lower or "concurrent" in task_lower:
            parallel_ops.append("explicit_parallel")

        if "multiple" in task_lower or "many" in task_lower:
            parallel_ops.append("data_parallel")

        return parallel_ops

    def _identify_delegation_points(self, task: str) -> list[str]:
        """Identify natural delegation boundaries"""

        task_lower = task.lower()
        delegation_points = []

        if "then" in task_lower or "after" in task_lower:
            delegation_points.append("sequential_delegation")

        if any(word in task_lower for word in ["strategy", "plan", "coordinate"]):
            delegation_points.append("strategy_delegation")

        if any(word in task_lower for word in ["execute", "run", "implement"]):
            delegation_points.append("execution_delegation")

        return delegation_points

    def _build_delegation_chain(self, task_analysis: dict[str, Any]) -> DelegationChain:
        """Build optimal delegation chain for the task"""

        task_desc = task_analysis.get("task_description", "")
        required_layers = task_analysis.get("required_layers", ["L0", "L3"])

        # Choose coordinator persona based on task type
        coordinator = self._select_coordinator_persona(task_analysis)

        # Build delegation path
        delegation_path = []

        # Start with coordinator
        delegation_path.append(
            {
                "layer": "L0",
                "persona": coordinator,
                "action": "coordinate",
                "reasoning": "Task coordination and delegation strategy",
            }
        )

        # Add strategy layer if needed
        if "L1" in required_layers:
            strategy_persona = self._select_strategy_persona(task_analysis)
            delegation_path.append(
                {
                    "layer": "L1",
                    "persona": strategy_persona,
                    "action": "strategize",
                    "reasoning": "Define high-level approach and requirements",
                }
            )

        # Add workflow layer if needed
        if "L2" in required_layers:
            workflow_persona = self._select_workflow_persona(task_analysis)
            delegation_path.append(
                {
                    "layer": "L2",
                    "persona": workflow_persona,
                    "action": "orchestrate",
                    "reasoning": "Manage execution workflow and dependencies",
                }
            )

        # Add expert layer if needed
        if "L3" in required_layers:
            expert_persona = self._select_expert_persona(task_analysis)
            delegation_path.append(
                {
                    "layer": "L3",
                    "persona": expert_persona,
                    "action": "implement",
                    "reasoning": "Execute technical implementation",
                }
            )

        # Add wrapper layer if needed
        if "L4" in required_layers:
            wrapper_persona = self._select_wrapper_persona(task_analysis)
            delegation_path.append(
                {
                    "layer": "L4",
                    "persona": wrapper_persona,
                    "action": "execute",
                    "reasoning": "Direct system and API execution",
                }
            )

        # Create delegation chain
        chain = DelegationChain(
            task_description=task_desc,
            layers_involved=required_layers,
            mcp_stack={},  # Will be filled by assign_mcp_stacks
            delegation_path=delegation_path,
        )

        chain.confidence_score = self._calculate_delegation_confidence(chain)

        return chain

    def _select_coordinator_persona(self, task_analysis: dict) -> str:
        """Select the best coordinator persona for this task"""

        if not layered_persona_registry:
            return "backend-developer"  # fallback

        domain = task_analysis.get("domain", "general")
        complexity = task_analysis.get("layer_complexity", "medium")

        # For complex system tasks, use system-overseer
        if complexity == "high" or domain in ["infrastructure", "observability"]:
            return "system-overseer"

        # For user-facing tasks, use agent-provisioner
        elif domain in ["frontend", "testing", "data"]:
            return "agent-provisioner"

        # Default to system-overseer
        return "system-overseer"

    def _select_strategy_persona(self, task_analysis: dict) -> str:
        """Select strategy-level persona based on domain"""

        domain = task_analysis.get("domain", "general")

        strategy_mapping = {
            "backend": "prodmgr-orchestrator",
            "frontend": "devex-orchestrator",
            "infrastructure": "ciso-orchestrator",  # Security focus
            "testing": "devex-orchestrator",
            "observability": "ciso-orchestrator",
            "data": "prodmgr-orchestrator",
        }

        return strategy_mapping.get(domain, "prodmgr-orchestrator")

    def _select_workflow_persona(self, task_analysis: dict) -> str:
        """Select workflow orchestration persona"""

        domain = task_analysis.get("domain", "general")

        workflow_mapping = {
            "backend": "pipeline-manager",
            "infrastructure": "infra-manager",
            "testing": "appsec-manager",
            "observability": "pipeline-manager",
            "security": "netsec-manager",
        }

        return workflow_mapping.get(domain, "pipeline-manager")

    def _select_expert_persona(self, task_analysis: dict) -> str:
        """Select technical expert persona"""

        domain = task_analysis.get("domain", "general")

        expert_mapping = {
            "backend": "backend-developer",
            "frontend": "frontend-developer",
            "infrastructure": "k8s-cluster-expert",
            "database": "db-data-expert",
            "testing": "testing-specialist",
            "observability": "observability-expert",
            "data": "data-scientist",
        }

        return expert_mapping.get(domain, "backend-developer")

    def _select_wrapper_persona(self, task_analysis: dict) -> str:
        """Select execution wrapper persona"""

        domain = task_analysis.get("domain", "general")

        wrapper_mapping = {
            "infrastructure": "kube-cli-wrapper",
            "cloud": "aws-api-wrapper",
            "security": "scanner-cli-wrapper",
            "testing": "scanner-cli-wrapper",
        }

        # Default to AWS wrapper as most common
        return wrapper_mapping.get(domain, "aws-api-wrapper")

    def _calculate_delegation_confidence(self, chain: DelegationChain) -> float:
        """Calculate confidence score for delegation chain"""

        base_confidence = 0.8

        # Penalize for too many layers
        if len(chain.delegation_path) > 4:
            base_confidence -= 0.1

        # Reward for covering task needs
        if len(chain.layers_involved) >= 3:
            base_confidence += 0.1

        # Penalize for gaps in layer coverage
        layer_numbers = [int(layer[1]) for layer in chain.layers_involved]
        if max(layer_numbers) - min(layer_numbers) > len(layer_numbers):
            base_confidence -= 0.1

        return min(max(base_confidence, 0.0), 1.0)

    def _find_layered_personas(
        self, task_analysis: dict, delegation_chain: DelegationChain
    ) -> dict[str, Any]:
        """Find personas organized by layer assignment"""

        layered_personas = {}

        for step in delegation_chain.delegation_path:
            layer = step["layer"]
            persona_name = step["persona"]

            if layer not in layered_personas:
                layered_personas[layer] = []

            # Get persona details from layered registry
            if layered_persona_registry:
                persona = layered_persona_registry.get_persona(persona_name)
                if persona:
                    layered_personas[layer].append(
                        {
                            "name": persona.name,
                            "display_name": persona.display_name,
                            "description": persona.description,
                            "mcp_stack": persona.mcp_stack,
                            "cognitive_load": persona.cognitive_load,
                            "delegation_targets": persona.delegation_targets,
                            "action": step["action"],
                            "reasoning": step["reasoning"],
                        }
                    )

        return layered_personas

    def _assign_mcp_stacks(
        self, delegation_chain: DelegationChain
    ) -> dict[str, list[str]]:
        """Assign appropriate MCP servers to each layer"""

        mcp_stacks = {}
        available_servers = set(self.mcp_servers.keys())

        for step in delegation_chain.delegation_path:
            layer = step["layer"]
            persona_name = step["persona"]

            # Get persona's preferred MCP stack
            mcp_stack = []
            if layered_persona_registry:
                persona = layered_persona_registry.get_persona(persona_name)
                if persona:
                    mcp_stack = [
                        server
                        for server in persona.mcp_stack
                        if server in available_servers
                    ]

            # Fallback: assign servers based on layer and domain
            if not mcp_stack:
                mcp_stack = self._get_default_mcp_stack(
                    layer, delegation_chain.task_description
                )

            mcp_stacks[layer] = mcp_stack

        return mcp_stacks

    def _get_default_mcp_stack(self, layer: str, task_desc: str) -> list[str]:
        """Get default MCP stack for a layer based on task context"""

        available_servers = list(self.mcp_servers.keys())
        task_lower = task_desc.lower()

        layer_defaults = {
            "L0": ["tta-dev-primitives"],  # Always include primitives
            "L1": ["tta-dev-primitives", "context7"],  # Strategy + research
            "L2": ["tta-dev-primitives"],  # Orchestration
            "L3": ["tta-dev-primitives"],  # Implementation
            "L4": ["tta-dev-primitives"],  # Direct execution
        }

        base_stack = layer_defaults.get(layer, ["tta-dev-primitives"])

        # Add domain-specific servers
        if "github" in task_lower and "github" in available_servers:
            base_stack.append("github")
        if "testing" in task_lower and "playwright" in available_servers:
            base_stack.append("playwright")

        # Remove duplicates
        return list(set(base_stack))

    def _generate_coordination_strategy(
        self, task_analysis: dict, delegation_chain: DelegationChain
    ) -> dict[str, Any]:
        """Generate coordination strategy for multi-layer execution"""

        strategy = {
            "coordination_type": "sequential",  # Default to sequential for now
            "handover_points": [],
            "parallel_opportunities": task_analysis.get(
                "parallelization_opportunities", []
            ),
            "error_handling_strategy": "fallback_to_previous_layer",
            "success_criteria": [],
            "estimated_duration": "medium",  # Could be calculated based on complexity
        }

        # Determine if parallel coordination is beneficial
        if len(delegation_chain.delegation_path) >= 3:
            strategy["coordination_type"] = "parallel_where_possible"

        # Define handover points
        for i, step in enumerate(delegation_chain.delegation_path):
            if i < len(delegation_chain.delegation_path) - 1:
                next_step = delegation_chain.delegation_path[i + 1]
                strategy["handover_points"].append(
                    {
                        "from": f"{step['layer']}:{step['persona']}",
                        "to": f"{next_step['layer']}:{next_step['persona']}",
                        "criteria": f"Deliver {next_step['action']} artifacts",
                    }
                )

        # Success criteria
        complexity = task_analysis.get("layer_complexity", "medium")
        if complexity == "high":
            strategy["success_criteria"].extend(
                [
                    "All layers executed successfully",
                    "Cross-layer validation passed",
                    "Metrics collected and analyzed",
                ]
            )
        else:
            strategy["success_criteria"].extend(
                [
                    "Task completed within layer boundaries",
                    "No critical errors reported",
                ]
            )

        return strategy

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
                        "capabilities": persona_capabilities,
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
        status = {
            "personas": {
                "count": len(self.personas),
                "active": len([p for p in self.personas.values() if p.is_available]),
            },
            "layered_personas": len(layered_persona_registry.personas)
            if layered_persona_registry
            else 0,
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
            "delegation_chains": len(self.delegation_chains),
            "last_updated": datetime.now().isoformat(),
        }

        return status


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

        elif command == "layered-analyze":
            if len(sys.argv) > 2:
                task = " ".join(sys.argv[2:])
                recommendations = capability_registry.get_capabilities_for_task_layered(
                    task
                )

                print(f"Layered Analysis for: '{task}'")
                print(
                    f"Complexity: {recommendations.get('estimated_complexity', 'unknown')}"
                )
                print(f"Confidence: {recommendations.get('confidence_score', 0):.2f}")

                layered = recommendations.get("layered_personas", {})
                if layered:
                    print("\nLayer Assignment:")
                    for layer, personas in layered.items():
                        if personas:
                            print(
                                f"  {layer}: {personas[0]['display_name']} ({personas[0]['action']})"
                            )

                delegation = recommendations.get("delegation_chain", [])
                if delegation:
                    print("\nDelegation Chain:")
                    for step in delegation:
                        print(
                            f"  {step['layer']} → {step['persona']} ({step['action']})"
                        )

                mcp_stacks = recommendations.get("mcp_stacks", {})
                if mcp_stacks:
                    print("\nMCP Stacks:")
                    for layer, servers in mcp_stacks.items():
                        if servers:
                            print(f"  {layer}: {', '.join(servers)}")

        else:
            print("Commands: status, analyze <task>, layered-analyze <task>")

    else:
        print("Agent Capability Registry")
        print("=" * 50)
        status = capability_registry.get_registry_status()
        print("Registry initialized with:")
        print(
            f"  Flat personas: {status['personas']['active']}/{status['personas']['count']}"
        )
        print(f"  Layered personas: {status.get('layered_personas', 0)}")
        print(
            f"  Primitives: {status['primitives']['active']}/{status['primitives']['count']}"
        )
        print(
            f"  Workflows: {status['workflows']['active']}/{status['workflows']['count']}"
        )
        print(
            f"  MCP servers: {status['mcp_servers']['active']}/{status['mcp_servers']['count']}"
        )
        if layered_persona_registry:
            print("  ✓ Layered persona system available")
        else:
            print("  ⚠ Layered persona system not available")
        print("Ready for layered agent coordination!")
