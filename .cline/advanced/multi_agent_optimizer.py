"""
Phase 3: Enhanced Multi-Agent Optimization

Sophisticated coordination patterns for complex multi-agent workflows.
This module provides intelligent agent orchestration, advanced workflow patterns, and self-healing systems.

Key Features:
- Intelligent Agent Orchestration: Dynamic agent selection, load balancing, context-aware handoffs
- Advanced Workflow Patterns: Conditional execution, dynamic composition, self-healing
- Agent Coordination Intelligence: Communication protocols, state management, failure recovery
"""

import asyncio
import json
import logging
import queue
import threading
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

# Import from our context system
from .dynamic_context_loader import ProjectContext
from .tool_aware_engine import Suggestion


class AgentType(Enum):
    """Types of agents in the system."""

    CODE_ANALYZER = "code_analyzer"
    SUGGESTION_ENGINE = "suggestion_engine"
    CONTEXT_LOADER = "context_loader"
    OPTIMIZATION_ENGINE = "optimization_engine"
    COORDINATOR = "coordinator"
    WORKER = "worker"
    SPECIALIST = "specialist"
    MONITOR = "monitor"


class AgentState(Enum):
    """Agent execution states."""

    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    SHUTDOWN = "shutdown"


class WorkflowType(Enum):
    """Types of workflow patterns."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    PIPELINE = "pipeline"
    FANOUT_FANIN = "fanout_fanin"
    CIRCUIT_BREAKER = "circuit_breaker"
    BULKHEAD = "bulkhead"
    ADAPTIVE = "adaptive"


class CoordinationStrategy(Enum):
    """Agent coordination strategies."""

    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    SKILL_BASED = "skill_based"
    CONTEXT_AWARE = "context_aware"
    PRIORITY_BASED = "priority_based"
    ADAPTIVE = "adaptive"


@dataclass
class AgentCapability:
    """Represents an agent's capability."""

    name: str
    level: float  # 0.0 to 1.0
    cost: float  # Computational cost
    speed: float  # Execution speed factor
    reliability: float  # Historical reliability


@dataclass
class Agent:
    """Represents an agent in the system."""

    id: str
    name: str
    type: AgentType
    capabilities: list[AgentCapability]
    current_load: float
    state: AgentState
    performance_history: list[dict[str, Any]]
    specialization: str
    max_concurrent_tasks: int
    current_tasks: set[str]
    last_heartbeat: datetime

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.current_tasks:
            self.current_tasks = set()
        if not self.last_heartbeat:
            self.last_heartbeat = datetime.now()


@dataclass
class Task:
    """Represents a task to be executed by agents."""

    id: str
    name: str
    type: str
    requirements: list[str]
    complexity: float
    priority: int
    context: dict[str, Any]
    input_data: Any
    callback: Callable | None = None
    timeout: float | None = None
    dependencies: list[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.dependencies:
            self.dependencies = []


@dataclass
class Workflow:
    """Represents a workflow composed of multiple tasks."""

    id: str
    name: str
    type: WorkflowType
    tasks: list[Task]
    coordination_strategy: CoordinationStrategy
    conditions: list[Callable] = None
    error_handlers: dict[str, Callable] = None
    timeout: float | None = None
    metadata: dict[str, Any] = None
    created_at: datetime = None
    status: str = "pending"
    result: Any = None
    error: Exception | None = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.conditions:
            self.conditions = []
        if not self.error_handlers:
            self.error_handlers = {}


@dataclass
class ExecutionContext:
    """Context for task execution."""

    workflow_id: str
    task_id: str
    agent_id: str
    start_time: datetime
    end_time: datetime | None = None
    result: Any = None
    error: Exception | None = None
    performance_metrics: dict[str, Any] = None


class AgentOrchestrator:
    """Intelligent agent orchestration and load balancing system."""

    def __init__(self, max_agents: int = 10):
        self.agents: dict[str, Agent] = {}
        self.agent_pools: dict[AgentType, list[str]] = defaultdict(list)
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.execution_history: list[ExecutionContext] = []
        self.performance_metrics: dict[str, dict[str, Any]] = defaultdict(dict)
        self.coordination_strategies = {
            CoordinationStrategy.ROUND_ROBIN: self._round_robin_selection,
            CoordinationStrategy.LOAD_BALANCED: self._load_balanced_selection,
            CoordinationStrategy.SKILL_BASED: self._skill_based_selection,
            CoordinationStrategy.CONTEXT_AWARE: self._context_aware_selection,
            CoordinationStrategy.ADAPTIVE: self._adaptive_selection,
        }
        self._lock = threading.RLock()
        self._shutdown_event = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=max_agents)

    def register_agent(self, agent: Agent) -> str:
        """Register a new agent in the system."""
        with self._lock:
            self.agents[agent.id] = agent
            self.agent_pools[agent.type].append(agent.id)
            logging.info(f"Registered agent {agent.name} ({agent.type.value})")
            return agent.id

    def unregister_agent(self, agent_id: str):
        """Unregister an agent from the system."""
        with self._lock:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                self.agent_pools[agent.type].remove(agent_id)
                agent.state = AgentState.SHUTDOWN
                del self.agents[agent_id]
                logging.info(f"Unregistered agent {agent_id}")

    def get_available_agents(
        self, agent_type: AgentType, min_capability: float = 0.0
    ) -> list[Agent]:
        """Get available agents of a specific type with minimum capability."""
        with self._lock:
            available = []
            for agent_id in self.agent_pools[agent_type]:
                agent = self.agents[agent_id]
                if (
                    agent.state == AgentState.IDLE
                    and agent.current_load < 1.0
                    and max(cap.level for cap in agent.capabilities) >= min_capability
                ):
                    available.append(agent)
            return available

    def assign_task(
        self,
        task: Task,
        agent_type: AgentType,
        strategy: CoordinationStrategy = CoordinationStrategy.ADAPTIVE,
    ) -> Agent | None:
        """Assign a task to an appropriate agent."""
        with self._lock:
            available_agents = self.get_available_agents(agent_type)
            if not available_agents:
                return None

            selection_func = self.coordination_strategies[strategy]
            selected_agent = selection_func(task, available_agents)

            if selected_agent:
                selected_agent.state = AgentState.BUSY
                selected_agent.current_load += 0.1
                selected_agent.current_tasks.add(task.id)
                return selected_agent

        return None

    def _round_robin_selection(self, task: Task, agents: list[Agent]) -> Agent:
        """Round-robin agent selection."""
        # Simple round-robin based on last used time
        return agents[0] if agents else None

    def _load_balanced_selection(self, task: Task, agents: list[Agent]) -> Agent:
        """Load-balanced agent selection."""
        return min(agents, key=lambda a: a.current_load)

    def _skill_based_selection(self, task: Task, agents: list[Agent]) -> Agent:
        """Skill-based agent selection."""
        best_agent = None
        best_score = -1

        for agent in agents:
            # Score based on capability match and current load
            capability_score = max(
                cap.level for cap in agent.capabilities if cap.name in task.requirements
            )
            load_score = 1.0 - agent.current_load
            total_score = (capability_score * 0.7) + (load_score * 0.3)

            if total_score > best_score:
                best_score = total_score
                best_agent = agent

        return best_agent

    def _context_aware_selection(self, task: Task, agents: list[Agent]) -> Agent:
        """Context-aware agent selection."""
        # Consider task complexity and agent specialization
        best_agent = None
        best_score = -1

        for agent in agents:
            # Score based on specialization match and performance history
            spec_score = 1.0 if task.type in agent.specialization else 0.5

            # Look at recent performance for similar tasks
            recent_performance = 0.0
            if task.type in self.performance_metrics.get(agent.id, {}):
                recent_performance = self.performance_metrics[agent.id][task.type]

            load_score = 1.0 - agent.current_load
            total_score = (
                (spec_score * 0.4) + (recent_performance * 0.4) + (load_score * 0.2)
            )

            if total_score > best_score:
                best_score = total_score
                best_agent = agent

        return best_agent

    def _adaptive_selection(self, task: Task, agents: list[Agent]) -> Agent:
        """Adaptive agent selection using all factors."""
        # Use a combination of all strategies
        skill_score = self._skill_based_selection(task, agents)
        context_score = self._context_aware_selection(task, agents)
        load_score = self._load_balanced_selection(task, agents)

        # Weighted combination
        agents_with_scores = []
        for agent in agents:
            skill_agent = self._skill_based_selection(task, [agent])
            context_agent = self._context_aware_selection(task, [agent])

            skill_match = 1.0 if skill_agent.id == agent.id else 0.0
            context_match = 1.0 if context_agent.id == agent.id else 0.0
            load_score = 1.0 - agent.current_load

            total_score = (
                (skill_match * 0.35) + (context_match * 0.35) + (load_score * 0.3)
            )
            agents_with_scores.append((agent, total_score))

        return (
            max(agents_with_scores, key=lambda x: x[1])[0]
            if agents_with_scores
            else None
        )

    def complete_task(
        self,
        agent_id: str,
        task_id: str,
        result: Any,
        execution_time: float,
        success: bool = True,
    ):
        """Mark a task as completed and update agent state."""
        with self._lock:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.current_tasks.discard(task_id)
                agent.current_load = max(0.0, agent.current_load - 0.1)

                if not agent.current_tasks:
                    agent.state = AgentState.IDLE

                # Update performance metrics
                if task_id not in self.performance_metrics.get(agent_id, {}):
                    self.performance_metrics[agent_id][task_id] = 0.0

                if success:
                    # Exponential moving average of success rate
                    current = self.performance_metrics[agent_id].get(
                        "success_rate", 0.0
                    )
                    self.performance_metrics[agent_id]["success_rate"] = (
                        current * 0.9
                    ) + (1.0 * 0.1)
                else:
                    current = self.performance_metrics[agent_id].get(
                        "success_rate", 0.0
                    )
                    self.performance_metrics[agent_id]["success_rate"] = (
                        current * 0.9
                    ) + (0.0 * 0.1)

    def get_system_status(self) -> dict[str, Any]:
        """Get current system status and metrics."""
        with self._lock:
            total_agents = len(self.agents)
            idle_agents = sum(
                1 for a in self.agents.values() if a.state == AgentState.IDLE
            )
            busy_agents = sum(
                1 for a in self.agents.values() if a.state == AgentState.BUSY
            )

            avg_load = sum(a.current_load for a in self.agents.values()) / max(
                total_agents, 1
            )

            return {
                "total_agents": total_agents,
                "idle_agents": idle_agents,
                "busy_agents": busy_agents,
                "average_load": avg_load,
                "agent_types": {
                    at.value: len(agent_ids)
                    for at, agent_ids in self.agent_pools.items()
                },
                "queue_size": self.task_queue.qsize(),
                "uptime": time.time() - getattr(self, "_start_time", time.time()),
            }


class AdvancedWorkflowEngine:
    """Engine for executing advanced workflow patterns."""

    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator
        self.active_workflows: dict[str, Workflow] = {}
        self.workflow_templates: dict[WorkflowType, dict[str, Any]] = (
            self._load_workflow_templates()
        )
        self._lock = threading.RLock()

    def _load_workflow_templates(self) -> dict[WorkflowType, dict[str, Any]]:
        """Load workflow pattern templates."""
        return {
            WorkflowType.SEQUENTIAL: {
                "description": "Execute tasks in sequence",
                "condition": lambda tasks, context: len(tasks) > 1,
                "execution_strategy": self._execute_sequential,
            },
            WorkflowType.PARALLEL: {
                "description": "Execute tasks in parallel",
                "condition": lambda tasks, context: len(tasks) > 1,
                "execution_strategy": self._execute_parallel,
            },
            WorkflowType.CONDITIONAL: {
                "description": "Execute tasks based on conditions",
                "condition": lambda tasks, context: any(
                    task.context.get("condition") for task in tasks
                ),
                "execution_strategy": self._execute_conditional,
            },
            WorkflowType.PIPELINE: {
                "description": "Pipeline processing with data flow",
                "condition": lambda tasks, context: len(tasks) > 2,
                "execution_strategy": self._execute_pipeline,
            },
            WorkflowType.FANOUT_FANIN: {
                "description": "Fan out to multiple agents, then fan in results",
                "condition": lambda tasks, context: len(tasks) > 3,
                "execution_strategy": self._execute_fanout_fanin,
            },
            WorkflowType.CIRCUIT_BREAKER: {
                "description": "Circuit breaker pattern for fault tolerance",
                "condition": lambda tasks, context: any(
                    "external_service" in str(task.context) for task in tasks
                ),
                "execution_strategy": self._execute_circuit_breaker,
            },
            WorkflowType.BULKHEAD: {
                "description": "Bulkhead pattern for resource isolation",
                "condition": lambda tasks, context: any(
                    "resource_intensive" in str(task.context) for task in tasks
                ),
                "execution_strategy": self._execute_bulkhead,
            },
        }

    def create_workflow(
        self,
        workflow_type: WorkflowType,
        tasks: list[Task],
        strategy: CoordinationStrategy = CoordinationStrategy.ADAPTIVE,
        **kwargs,
    ) -> Workflow:
        """Create a new workflow."""
        workflow = Workflow(
            id=str(uuid.uuid4()),
            name=f"{workflow_type.value}_workflow",
            type=workflow_type,
            tasks=tasks,
            coordination_strategy=strategy,
            metadata=kwargs.get("metadata", {}),
            timeout=kwargs.get("timeout"),
        )

        return workflow

    async def execute_workflow(self, workflow: Workflow) -> Any:
        """Execute a workflow using the appropriate pattern."""
        with self._lock:
            self.active_workflows[workflow.id] = workflow

        try:
            template = self.workflow_templates.get(workflow.type)
            if not template:
                raise ValueError(f"Unknown workflow type: {workflow.type}")

            logging.info(f"Executing workflow {workflow.name} ({workflow.type.value})")
            result = await template["execution_strategy"](workflow)

            workflow.status = "completed"
            workflow.result = result
            return result

        except Exception as e:
            workflow.status = "failed"
            workflow.error = e
            logging.error(f"Workflow {workflow.id} failed: {str(e)}")

            # Try error handlers if available
            if workflow.error_handlers:
                error_type = type(e).__name__
                if error_type in workflow.error_handlers:
                    try:
                        result = await workflow.error_handlers[error_type](e, workflow)
                        workflow.status = "recovered"
                        workflow.result = result
                        return result
                    except Exception as handler_error:
                        logging.error(f"Error handler failed: {str(handler_error)}")

            raise

        finally:
            with self._lock:
                self.active_workflows.pop(workflow.id, None)

    async def _execute_sequential(self, workflow: Workflow) -> Any:
        """Execute tasks sequentially."""
        result = None
        for task in workflow.tasks:
            logging.info(f"Executing task {task.name} sequentially")

            # Assign task to appropriate agent
            agent_type = self._get_agent_type_for_task(task)
            agent = self.orchestrator.assign_task(
                task, agent_type, workflow.coordination_strategy
            )

            if not agent:
                raise RuntimeError(f"No available agent for task {task.name}")

            # Execute task
            task_result = await self._execute_task(agent, task)
            result = task_result

            # Check if we should continue (for conditional workflows)
            if hasattr(workflow, "conditions") and workflow.conditions:
                should_continue = True
                for condition in workflow.conditions:
                    if not await self._evaluate_condition(condition, result, workflow):
                        should_continue = False
                        break
                if not should_continue:
                    break

        return result

    async def _execute_parallel(self, workflow: Workflow) -> list[Any]:
        """Execute tasks in parallel."""
        results = []

        # Assign all tasks
        assignments = []
        for task in workflow.tasks:
            agent_type = self._get_agent_type_for_task(task)
            agent = self.orchestrator.assign_task(
                task, agent_type, workflow.coordination_strategy
            )
            if not agent:
                raise RuntimeError(f"No available agent for task {task.name}")
            assignments.append((agent, task))

        # Execute in parallel
        tasks = []
        for agent, task in assignments:
            task_coroutine = self._execute_task(agent, task)
            tasks.append(task_coroutine)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logging.error(f"Task {assignments[i][1].name} failed: {str(result)}")
                raise result

        return results

    async def _execute_conditional(self, workflow: Workflow) -> Any:
        """Execute tasks based on conditions."""
        result = None
        for task in workflow.tasks:
            # Check if task should be executed
            condition = task.context.get("condition")
            if condition and not await self._evaluate_condition(
                condition, result, workflow
            ):
                logging.info(f"Skipping task {task.name} due to condition")
                continue

            # Execute task
            agent_type = self._get_agent_type_for_task(task)
            agent = self.orchestrator.assign_task(
                task, agent_type, workflow.coordination_strategy
            )

            if not agent:
                raise RuntimeError(f"No available agent for task {task.name}")

            result = await self._execute_task(agent, task)

        return result

    async def _execute_pipeline(self, workflow: Workflow) -> Any:
        """Execute tasks in a pipeline with data flow."""
        data = None
        for task in workflow.tasks:
            # Execute task with previous result as input
            if data is not None:
                task.input_data = data

            agent_type = self._get_agent_type_for_task(task)
            agent = self.orchestrator.assign_task(
                task, agent_type, workflow.coordination_strategy
            )

            if not agent:
                raise RuntimeError(f"No available agent for task {task.name}")

            data = await self._execute_task(agent, task)

        return data

    async def _execute_fanout_fanin(self, workflow: Workflow) -> Any:
        """Execute fanout-fanin pattern."""
        # Fan out - execute subtasks
        fanout_tasks = workflow.tasks[:-1]  # All except last
        fanin_task = workflow.tasks[-1]  # Last task collects results

        # Execute fanout tasks in parallel
        fanout_results = await self._execute_parallel(
            self.create_workflow(
                WorkflowType.PARALLEL, fanout_tasks, workflow.coordination_strategy
            )
        )

        # Fan in - pass results to final task
        fanin_task.input_data = fanout_results

        agent_type = self._get_agent_type_for_task(fanin_task)
        agent = self.orchestrator.assign_task(
            fanin_task, agent_type, workflow.coordination_strategy
        )

        if not agent:
            raise RuntimeError(f"No available agent for fanin task {fanin_task.name}")

        result = await self._execute_task(agent, fanin_task)
        return result

    async def _execute_circuit_breaker(self, workflow: Workflow) -> Any:
        """Execute with circuit breaker pattern."""
        # Simple implementation - could be enhanced with actual circuit breaker logic
        max_retries = 3
        retry_count = 0

        for task in workflow.tasks:
            while retry_count < max_retries:
                try:
                    agent_type = self._get_agent_type_for_task(task)
                    agent = self.orchestrator.assign_task(
                        task, agent_type, workflow.coordination_strategy
                    )

                    if not agent:
                        raise RuntimeError(f"No available agent for task {task.name}")

                    result = await self._execute_task(agent, task)
                    retry_count = 0  # Reset on success
                    break

                except Exception:
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise
                    logging.warning(
                        f"Task {task.name} failed, retry {retry_count}/{max_retries}"
                    )
                    await asyncio.sleep(0.1 * retry_count)  # Exponential backoff

    async def _execute_bulkhead(self, workflow: Workflow) -> Any:
        """Execute with bulkhead (resource isolation) pattern."""
        # Create separate resource pools for different task types
        resource_pools = defaultdict(list)

        for task in workflow.tasks:
            resource_type = task.context.get("resource_type", "default")
            resource_pools[resource_type].append(task)

        # Execute each resource pool in parallel
        pool_results = []
        for resource_type, tasks in resource_pools.items():
            pool_workflow = self.create_workflow(
                WorkflowType.PARALLEL, tasks, workflow.coordination_strategy
            )
            pool_result = await self._execute_parallel(pool_workflow)
            pool_results.extend(pool_result)

        return pool_results

    async def _execute_task(self, agent: Agent, task: Task) -> Any:
        """Execute a single task on an agent."""
        start_time = time.time()

        try:
            logging.info(f"Executing task {task.name} on agent {agent.name}")

            # Simulate task execution
            await asyncio.sleep(0.1)  # Simulate processing time

            # This would be replaced with actual agent task execution
            result = {
                "task_id": task.id,
                "agent_id": agent.id,
                "result": f"Task {task.name} completed",
                "execution_time": time.time() - start_time,
            }

            # Mark task as completed
            self.orchestrator.complete_task(
                agent.id, task.id, result, time.time() - start_time, True
            )
            return result

        except Exception as e:
            # Mark task as failed
            self.orchestrator.complete_task(
                agent.id, task.id, None, time.time() - start_time, False
            )
            logging.error(f"Task {task.name} failed: {str(e)}")
            raise

    def _get_agent_type_for_task(self, task: Task) -> AgentType:
        """Determine the appropriate agent type for a task."""
        task_type_mapping = {
            "code_analysis": AgentType.CODE_ANALYZER,
            "suggestion": AgentType.SUGGESTION_ENGINE,
            "context_loading": AgentType.CONTEXT_LOADER,
            "optimization": AgentType.OPTIMIZATION_ENGINE,
            "coordination": AgentType.COORDINATOR,
            "specialist": AgentType.SPECIALIST,
            "monitoring": AgentType.MONITOR,
        }

        return task_type_mapping.get(task.type, AgentType.WORKER)

    async def _evaluate_condition(
        self, condition: Callable, data: Any, workflow: Workflow
    ) -> bool:
        """Evaluate a workflow condition."""
        try:
            if asyncio.iscoroutinefunction(condition):
                return await condition(data, workflow)
            else:
                return condition(data, workflow)
        except Exception as e:
            logging.error(f"Condition evaluation failed: {str(e)}")
            return False


class SelfHealingSystem:
    """System for automatic recovery and optimization."""

    def __init__(
        self, orchestrator: AgentOrchestrator, workflow_engine: AdvancedWorkflowEngine
    ):
        self.orchestrator = orchestrator
        self.workflow_engine = workflow_engine
        self.health_checks: dict[str, Callable] = {}
        self.recovery_strategies: dict[str, Callable] = {}
        self.performance_thresholds = {
            "max_agent_load": 0.9,
            "min_success_rate": 0.7,
            "max_response_time": 5.0,
            "max_queue_size": 100,
        }
        self._monitoring_active = False
        self._monitor_task: asyncio.Task | None = None

    def register_health_check(self, name: str, check_func: Callable):
        """Register a health check function."""
        self.health_checks[name] = check_func
        logging.info(f"Registered health check: {name}")

    def register_recovery_strategy(self, name: str, recovery_func: Callable):
        """Register a recovery strategy function."""
        self.recovery_strategies[name] = recovery_func
        logging.info(f"Registered recovery strategy: {name}")

    async def start_monitoring(self):
        """Start the self-healing monitoring system."""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logging.info("Self-healing monitoring started")

    async def stop_monitoring(self):
        """Stop the self-healing monitoring system."""
        self._monitoring_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logging.info("Self-healing monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._monitoring_active:
            try:
                await self._check_system_health()
                await asyncio.sleep(5)  # Check every 5 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Monitoring loop error: {str(e)}")
                await asyncio.sleep(1)

    async def _check_system_health(self):
        """Check system health and trigger recovery if needed."""
        issues = []

        # Check agent health
        for agent_id, agent in self.orchestrator.agents.items():
            # Check if agent is responsive
            if (datetime.now() - agent.last_heartbeat).seconds > 30:
                issues.append(f"Agent {agent_id} heartbeat timeout")

            # Check agent load
            if agent.current_load > self.performance_thresholds["max_agent_load"]:
                issues.append(f"Agent {agent_id} overload: {agent.current_load}")

            # Check success rate
            if agent_id in self.orchestrator.performance_metrics:
                success_rate = self.orchestrator.performance_metrics[agent_id].get(
                    "success_rate", 1.0
                )
                if success_rate < self.performance_thresholds["min_success_rate"]:
                    issues.append(f"Agent {agent_id} low success rate: {success_rate}")

        # Check system metrics
        status = self.orchestrator.get_system_status()
        if status["queue_size"] > self.performance_thresholds["max_queue_size"]:
            issues.append(f"Task queue overflow: {status['queue_size']}")

        # Trigger recovery for each issue
        for issue in issues:
            await self._trigger_recovery(issue)

    async def _trigger_recovery(self, issue: str):
        """Trigger appropriate recovery strategy for an issue."""
        logging.info(f"Triggering recovery for issue: {issue}")

        # Determine recovery strategy based on issue type
        if "overload" in issue.lower():
            await self._handle_agent_overload(issue)
        elif "timeout" in issue.lower():
            await self._handle_agent_timeout(issue)
        elif "low success rate" in issue.lower():
            await self._handle_reliability_issue(issue)
        elif "overflow" in issue.lower():
            await self._handle_queue_overflow(issue)
        else:
            # Generic recovery
            await self._generic_recovery(issue)

    async def _handle_agent_overload(self, issue: str):
        """Handle agent overload situation."""
        # Could implement task redistribution, agent scaling, etc.
        logging.info(f"Handling agent overload: {issue}")
        # Placeholder for actual implementation

    async def _handle_agent_timeout(self, issue: str):
        """Handle agent timeout situation."""
        logging.info(f"Handling agent timeout: {issue}")
        # Could implement agent replacement, task reassignment, etc.

    async def _handle_reliability_issue(self, issue: str):
        """Handle agent reliability issues."""
        logging.info(f"Handling reliability issue: {issue}")
        # Could implement agent retraining, capability adjustment, etc.

    async def _handle_queue_overflow(self, issue: str):
        """Handle task queue overflow."""
        logging.info(f"Handling queue overflow: {issue}")
        # Could implement task prioritization, agent scaling, etc.

    async def _generic_recovery(self, issue: str):
        """Generic recovery strategy."""
        logging.info(f"Applying generic recovery for: {issue}")
        # Placeholder for generic recovery logic

    async def optimize_workflow_execution(self, workflow: Workflow) -> Workflow:
        """Optimize a workflow based on historical performance."""
        # Analyze historical performance
        optimized_tasks = []

        for task in workflow.tasks:
            # Check if task type has optimization opportunities
            similar_tasks = [
                t
                for t in self.orchestrator.execution_history
                if t.task_id.split("_")[0] == task.type
            ]

            if similar_tasks:
                # Find best performing agents for this task type
                performance_by_agent = defaultdict(list)
                for execution in similar_tasks:
                    if execution.result and execution.end_time:
                        performance_by_agent[execution.agent_id].append(
                            (execution.end_time - execution.start_time).total_seconds()
                        )

                if performance_by_agent:
                    # Choose agent with best average performance
                    best_agent = min(
                        performance_by_agent.items(),
                        key=lambda x: sum(x[1]) / len(x[1]),
                    )
                    task.context["preferred_agent_type"] = best_agent[0]

            optimized_tasks.append(task)

        # Create optimized workflow
        optimized_workflow = self.workflow_engine.create_workflow(
            workflow.type, optimized_tasks, workflow.coordination_strategy
        )
        optimized_workflow.metadata = {
            **workflow.metadata,
            "optimized": True,
            "optimization_timestamp": datetime.now().isoformat(),
        }

        return optimized_workflow


class MultiAgentOptimizer:
    """Main class for multi-agent optimization and coordination."""

    def __init__(self, max_agents: int = 10):
        self.orchestrator = AgentOrchestrator(max_agents)
        self.workflow_engine = AdvancedWorkflowEngine(self.orchestrator)
        self.healing_system = SelfHealingSystem(self.orchestrator, self.workflow_engine)
        self.context_cache: dict[str, Any] = {}

        # Register default health checks and recovery strategies
        self._register_default_strategies()

        # Initialize with default agents
        self._initialize_default_agents()

    def _register_default_strategies(self):
        """Register default health checks and recovery strategies."""
        self.healing_system.register_health_check(
            "agent_heartbeat", self._check_agent_heartbeat
        )
        self.healing_system.register_health_check(
            "system_load", self._check_system_load
        )
        self.healing_system.register_health_check(
            "task_success_rate", self._check_success_rate
        )

        self.healing_system.register_recovery_strategy(
            "restart_agent", self._restart_agent
        )
        self.healing_system.register_recovery_strategy(
            "redistribute_tasks", self._redistribute_tasks
        )
        self.healing_system.register_recovery_strategy(
            "scale_agents", self._scale_agents
        )

    def _initialize_default_agents(self):
        """Initialize the system with default agents."""
        default_agents = [
            Agent(
                id=str(uuid.uuid4()),
                name="Code Analyzer Alpha",
                type=AgentType.CODE_ANALYZER,
                capabilities=[
                    AgentCapability("ast_analysis", 0.9, 0.3, 0.8, 0.95),
                    AgentCapability("pattern_detection", 0.8, 0.2, 0.9, 0.92),
                ],
                current_load=0.0,
                state=AgentState.IDLE,
                performance_history=[],
                specialization="code_analysis",
                max_concurrent_tasks=3,
                current_tasks=set(),
                last_heartbeat=datetime.now(),
            ),
            Agent(
                id=str(uuid.uuid4()),
                name="Suggestion Engine Beta",
                type=AgentType.SUGGESTION_ENGINE,
                capabilities=[
                    AgentCapability("context_awareness", 0.85, 0.4, 0.7, 0.88),
                    AgentCapability("recommendation_generation", 0.9, 0.3, 0.8, 0.91),
                ],
                current_load=0.0,
                state=AgentState.IDLE,
                performance_history=[],
                specialization="suggestion_engine",
                max_concurrent_tasks=5,
                current_tasks=set(),
                last_heartbeat=datetime.now(),
            ),
            Agent(
                id=str(uuid.uuid4()),
                name="Context Loader Gamma",
                type=AgentType.CONTEXT_LOADER,
                capabilities=[
                    AgentCapability("project_analysis", 0.8, 0.2, 0.9, 0.94),
                    AgentCapability("framework_detection", 0.75, 0.3, 0.8, 0.89),
                ],
                current_load=0.0,
                state=AgentState.IDLE,
                performance_history=[],
                specialization="context_loading",
                max_concurrent_tasks=2,
                current_tasks=set(),
                last_heartbeat=datetime.now(),
            ),
        ]

        for agent in default_agents:
            self.orchestrator.register_agent(agent)

    async def optimize_suggestions_workflow(
        self, context: ProjectContext, suggestions: list[Suggestion]
    ) -> Any:
        """Optimize the workflow for generating and processing suggestions."""
        # Create tasks for suggestion processing
        tasks = [
            Task(
                id=str(uuid.uuid4()),
                name="analyze_context",
                type="code_analysis",
                requirements=["ast_analysis", "pattern_detection"],
                complexity=0.3,
                priority=1,
                context={"context": asdict(context)},
                input_data=context,
            ),
            Task(
                id=str(uuid.uuid4()),
                name="generate_suggestions",
                type="suggestion",
                requirements=["context_awareness", "recommendation_generation"],
                complexity=0.5,
                priority=2,
                context={"suggestions_count": len(suggestions)},
                input_data=suggestions,
            ),
            Task(
                id=str(uuid.uuid4()),
                name="optimize_workflow",
                type="optimization",
                requirements=["workflow_optimization"],
                complexity=0.4,
                priority=3,
                context={},
                input_data=None,
            ),
        ]

        # Create and execute workflow
        workflow = self.workflow_engine.create_workflow(
            WorkflowType.PIPELINE, tasks, CoordinationStrategy.ADAPTIVE
        )

        result = await self.workflow_engine.execute_workflow(workflow)
        return result

    async def start_system(self):
        """Start the multi-agent optimization system."""
        await self.healing_system.start_monitoring()
        logging.info("Multi-Agent Optimizer system started")

    async def stop_system(self):
        """Stop the multi-agent optimization system."""
        await self.healing_system.stop_monitoring()
        logging.info("Multi-Agent Optimizer system stopped")

    def get_system_health(self) -> dict[str, Any]:
        """Get comprehensive system health information."""
        orchestrator_status = self.orchestrator.get_system_status()
        healing_status = {
            "monitoring_active": self.healing_system._monitoring_active,
            "health_checks_count": len(self.healing_system.health_checks),
            "recovery_strategies_count": len(self.healing_system.recovery_strategies),
        }

        return {
            "orchestrator": orchestrator_status,
            "healing_system": healing_status,
            "timestamp": datetime.now().isoformat(),
        }

    # Default health check implementations
    def _check_agent_heartbeat(self) -> bool:
        """Check if all agents are responsive."""
        current_time = datetime.now()
        for agent in self.orchestrator.agents.values():
            if (current_time - agent.last_heartbeat).seconds > 30:
                return False
        return True

    def _check_system_load(self) -> bool:
        """Check if system load is within acceptable limits."""
        status = self.orchestrator.get_system_status()
        return status["average_load"] < 0.8

    def _check_success_rate(self) -> bool:
        """Check if overall success rate is acceptable."""
        total_agents = len(self.orchestrator.agents)
        if total_agents == 0:
            return True

        high_performers = 0
        for agent_id, metrics in self.orchestrator.performance_metrics.items():
            success_rate = metrics.get("success_rate", 1.0)
            if success_rate >= 0.8:
                high_performers += 1

        return (high_performers / total_agents) >= 0.7

    # Default recovery strategy implementations
    async def _restart_agent(self, issue: str) -> bool:
        """Restart an unresponsive agent."""
        # Implementation would depend on agent implementation
        logging.info(f"Attempting to restart agent for issue: {issue}")
        return True

    async def _redistribute_tasks(self, issue: str) -> bool:
        """Redistribute tasks from overloaded agents."""
        logging.info(f"Redistributing tasks for issue: {issue}")
        return True

    async def _scale_agents(self, issue: str) -> bool:
        """Scale up or down the number of agents."""
        logging.info(f"Scaling agents for issue: {issue}")
        return True


# Utility functions for external integration
def create_multi_agent_optimizer(max_agents: int = 10) -> MultiAgentOptimizer:
    """Create a configured multi-agent optimizer instance."""
    return MultiAgentOptimizer(max_agents)


async def optimize_development_workflow(
    project_path: str, context: ProjectContext
) -> dict[str, Any]:
    """Optimize the development workflow for a project."""
    optimizer = create_multi_agent_optimizer()
    await optimizer.start_system()

    try:
        # Simulate suggestion generation
        suggestions = []  # Would be populated by actual suggestion engine

        result = await optimizer.optimize_suggestions_workflow(context, suggestions)
        return {
            "optimization_result": result,
            "system_health": optimizer.get_system_health(),
            "timestamp": datetime.now().isoformat(),
        }
    finally:
        await optimizer.stop_system()


# Example usage and testing
if __name__ == "__main__":

    async def test_multi_agent_system():
        """Test the multi-agent optimization system."""
        optimizer = create_multi_agent_optimizer()

        print("Multi-Agent Optimizer initialized")
        print("Starting system...")
        await optimizer.start_system()

        # Simulate some work
        await asyncio.sleep(2)

        # Get system health
        health = optimizer.get_system_health()
        print(f"System Health: {json.dumps(health, indent=2, default=str)}")

        print("Stopping system...")
        await optimizer.stop_system()
        print("Test completed")

    # Run the test
    asyncio.run(test_multi_agent_system())
