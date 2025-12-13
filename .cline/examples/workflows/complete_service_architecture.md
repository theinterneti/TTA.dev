# Workflow Examples for Cline

**Purpose:** Learn how to combine TTA.dev primitives into comprehensive, production-ready workflows for complex use cases

## Example 1: Complete Service Architecture - Layered Approach

**When to Use:** Building a production-grade service that needs caching, timeout handling, retry logic, and fallback capabilities in a layered architecture

**Cline Prompt Example:**

```
I need to build a production-ready LLM service that can handle high load,
costs, and reliability. Include caching, timeout protection, retry logic,
and fallback to cheaper models when needed.
```

**Expected Implementation:**

```python
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.sequential import SequentialPrimitive
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive, TimeoutPrimitive
from tta_dev_primitives.performance import CachePrimitive
import asyncio

class ProductionLLMService:
    def __init__(self):
        # Layer 1: Cache for cost optimization
        self.cached_llm = CachePrimitive(
            primitive=self._primary_llm_call,
            ttl_seconds=3600,  # 1 hour cache
            max_size=10000,    # Large cache for production
            key_fn=lambda data, ctx: f"{ctx.metadata.get('user_id', 'anonymous')}:{data.get('prompt', '')}"
        )

        # Layer 2: Timeout for reliability
        self.timed_llm = TimeoutPrimitive(
            primitive=self.cached_llm,
            timeout_seconds=30.0,  # 30 second timeout
            fallback=self._timeout_fallback,
            track_timeouts=True
        )

        # Layer 3: Retry for resilience
        self.retry_llm = RetryPrimitive(
            primitive=self.timed_llm,
            max_retries=3,
            backoff_strategy="exponential",
            retry_on=(ConnectionError, TimeoutError)
        )

        # Layer 4: Fallback for high availability
        self.fallback_llm = FallbackPrimitive(
            primary=self.retry_llm,
            fallbacks=[
                self._secondary_llm_call,
                self._local_fallback_model,
                self._emergency_fallback
            ]
        )

        # Complete service pipeline
        self.llm_service = self.fallback_llm

        # Performance monitoring
        self.request_counter = 0
        self.error_counter = 0
        self.cache_hit_rate = 0.0

    async def generate_response(self, prompt: str, request_context: dict) -> dict:
        """Generate response with complete service architecture"""
        self.request_counter += 1

        context = WorkflowContext(
            workflow_id="production-llm",
            metadata={
                "user_id": request_context.get("user_id", "anonymous"),
                "request_id": f"req_{self.request_counter}",
                "priority": request_context.get("priority", "normal"),
                "budget_constraint": request_context.get("max_cost", 0.05),
                "prompt_length": len(prompt)
            }
        )

        try:
            # Execute through complete pipeline
            result = await self.llm_service.execute(
                {"prompt": prompt, "request_context": request_context},
                context
            )

            # Add service metadata
            result["service_info"] = {
                "request_id": context.metadata["request_id"],
                "pipeline_layers": ["cache", "timeout", "retry", "fallback"],
                "cache_used": "cache" in str(type(self.llm_service.primitive)),
                "routing_decision": self._get_routing_decision(context),
                "cost_optimization": self._analyze_cost_optimization(prompt, request_context)
            }

            return result

        except Exception as e:
            self.error_counter += 1
            return {
                "error": "Service unavailable",
                "error_details": str(e),
                "request_id": context.metadata["request_id"],
                "fallback_used": True,
                "service_status": "degraded"
            }

    async def get_service_metrics(self) -> dict:
        """Get service performance metrics"""
        return {
            "total_requests": self.request_counter,
            "error_rate": self.error_counter / max(self.request_counter, 1),
            "cache_hit_rate": self.cache_hit_rate,
            "service_health": "healthy" if self.error_counter < self.request_counter * 0.1 else "degraded"
        }

    def _get_routing_decision(self, context: WorkflowContext) -> dict:
        """Analyze which service was used"""
        routing_history = context.state.get("routing_history", [])
        timeout_count = context.state.get("timeout_count", 0)

        return {
            "primary_service_used": "cache" in str(type(self.llm_service.primitive)),
            "fallbacks_triggered": len(routing_history),
            "timeouts_encountered": timeout_count,
            "final_service": "primary" if timeout_count == 0 else "fallback"
        }

    def _analyze_cost_optimization(self, prompt: str, request_context: dict) -> dict:
        """Analyze cost optimization strategies"""
        budget = request_context.get("max_cost", 0.05)
        prompt_tokens = len(prompt) // 4  # Rough token estimation

        # Cost analysis for different services
        service_costs = {
            "gpt-4": prompt_tokens * 0.00003,  # $0.03 per 1K tokens
            "claude": prompt_tokens * 0.000025,  # $0.025 per 1K tokens
            "local": prompt_tokens * 0.000001   # $0.001 per 1K tokens
        }

        cost_choices = []
        for service, cost in service_costs.items():
            if cost <= budget:
                cost_choices.append((service, cost))

        return {
            "budget_adequate": len(cost_choices) > 0,
            "optimal_service": min(cost_choices, key=lambda x: x[1])[0] if cost_choices else "emergency_fallback",
            "estimated_cost": min(service_costs.values()),
            "budget_utilization": min(service_costs.values()) / budget if budget > 0 else 0
        }

    async def _primary_llm_call(self, data: dict) -> dict:
        """Primary LLM service call"""
        prompt = data["prompt"]
        request_context = data.get("request_context", {})

        # Simulate API call
        await asyncio.sleep(2)  # Simulate API latency

        # Check if budget allows for primary service
        budget = request_context.get("max_cost", 0.05)
        prompt_tokens = len(prompt) // 4
        estimated_cost = prompt_tokens * 0.00003

        if estimated_cost > budget:
            raise ConnectionError("Budget exceeded for primary service")

        return {
            "response": f"Primary LLM response to: {prompt[:50]}...",
            "service_used": "gpt-4",
            "response_time": 2.0,
            "cost": estimated_cost
        }

    async def _secondary_llm_call(self, data: dict) -> dict:
        """Secondary LLM service (fallback)"""
        prompt = data["prompt"]
        request_context = data.get("request_context", {})

        await asyncio.sleep(1.5)

        return {
            "response": f"Secondary LLM response to: {prompt[:50]}...",
            "service_used": "claude",
            "response_time": 1.5,
            "cost": len(prompt) // 4 * 0.000025
        }

    async def _local_fallback_model(self, data: dict) -> dict:
        """Local fallback model"""
        prompt = data["prompt"]

        await asyncio.sleep(0.5)

        return {
            "response": f"Local model response to: {prompt[:50]}...",
            "service_used": "local_model",
            "response_time": 0.5,
            "cost": len(prompt) // 4 * 0.000001
        }

    async def _timeout_fallback(self, data: dict) -> dict:
        """Timeout fallback response"""
        return {
            "response": f"Quick response (timeout fallback): {data['prompt'][:30]}...",
            "service_used": "timeout_fallback",
            "response_time": 0.1,
            "note": "Generated with timeout fallback"
        }

    async def _emergency_fallback(self, data: dict) -> dict:
        """Emergency fallback - always succeeds"""
        return {
            "response": "I apologize, but I'm currently experiencing high load. Please try again in a moment.",
            "service_used": "emergency_fallback",
            "response_time": 0.01,
            "status": "service_unavailable"
        }

class ServiceOrchestrator:
    def __init__(self):
        self.production_service = ProductionLLMService()
        self.batch_processor = self._create_batch_processor()

    async def process_single_request(self, prompt: str, context: dict) -> dict:
        """Process single request through complete service"""
        return await self.production_service.generate_response(prompt, context)

    async def process_batch_requests(self, requests: list[dict]) -> list[dict]:
        """Process multiple requests in parallel for efficiency"""
        context = WorkflowContext(
            workflow_id="batch-processing",
            metadata={"batch_size": len(requests)}
        )

        # Create parallel processing for batch
        batch_tasks = []
        for i, request in enumerate(requests):
            task = self._process_single_batch_request(i, request, context)
            batch_tasks.append(task)

        # Execute all requests in parallel
        results = await asyncio.gather(*batch_tasks, return_exceptions=True)

        return [
            result if not isinstance(result, Exception) else {"error": str(result)}
            for result in results
        ]

    async def _process_single_batch_request(self, index: int, request: dict, context: WorkflowContext) -> dict:
        """Process single request in batch context"""
        child_context = context.create_child_context()
        child_context.metadata["batch_index"] = index

        try:
            return await self.production_service.generate_response(
                request["prompt"],
                request.get("context", {})
            )
        except Exception as e:
            return {
                "error": f"Batch request {index} failed",
                "error_details": str(e)
            }

    def _create_batch_processor(self):
        """Create batch processing pipeline"""
        return SequentialPrimitive([
            self.production_service.llm_service
        ])

# Usage examples
async def main():
    # Single request example
    service = ProductionLLMService()

    result1 = await service.generate_response(
        "Explain quantum computing in simple terms",
        {
            "user_id": "user123",
            "priority": "normal",
            "max_cost": 0.02
        }
    )
    print(f"Response from: {result1['service_info']['routing_decision']['final_service']}")

    # Batch processing example
    orchestrator = ServiceOrchestrator()
    batch_requests = [
        {"prompt": "What is AI?", "context": {"user_id": "user1"}},
        {"prompt": "How does ML work?", "context": {"user_id": "user2"}},
        {"prompt": "Explain blockchain", "context": {"user_id": "user3"}}
    ]

    batch_results = await orchestrator.process_batch_requests(batch_requests)
    print(f"Processed {len(batch_results)} requests in batch")

    # Service metrics
    metrics = await service.get_service_metrics()
    print(f"Service health: {metrics['service_health']}")
```

**Cline's Learning Pattern:**

- Identifies need for production-grade service architecture
- Uses layered approach: Cache → Timeout → Retry → Fallback
- Implements comprehensive error handling and monitoring
- Provides cost optimization and budget awareness
- Includes batch processing capabilities for efficiency
- Proper context tracking and metrics collection

## Example 2: Agent Coordination Patterns - Multi-Agent Workflows

**When to Use:** Building complex multi-agent systems that need coordination, state management, and intelligent task distribution

**Cline Prompt Example:**

```
I need to build a multi-agent system with a research agent, analysis agent,
and writing agent that can work together to create comprehensive reports.
Include state management and coordination between agents.
```

**Expected Implementation:**

```python
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.sequential import SequentialPrimitive
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
import asyncio
from typing import Any, Dict, List

class AgentState:
    """Shared state management for multi-agent coordination"""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.agents_status: Dict[str, str] = {}
        self.shared_data: Dict[str, Any] = {}
        self.task_queue: List[dict] = []
        self.completed_tasks: List[dict] = []
        self.coordination_log: List[dict] = []

    def update_agent_status(self, agent_name: str, status: str):
        """Update agent status"""
        self.agents_status[agent_name] = status
        self.coordination_log.append({
            "timestamp": asyncio.get_event_loop().time(),
            "agent": agent_name,
            "status": status
        })

    def add_task(self, task: dict):
        """Add task to queue"""
        self.task_queue.append({
            "id": len(self.task_queue),
            "assigned_to": None,
            "status": "pending",
            **task
        })

    def assign_task(self, task_id: int, agent_name: str):
        """Assign task to agent"""
        if 0 <= task_id < len(self.task_queue):
            self.task_queue[task_id]["assigned_to"] = agent_name
            self.update_agent_status(agent_name, f"assigned_task_{task_id}")

    def complete_task(self, task_id: int, result: Any):
        """Mark task as completed"""
        if 0 <= task_id < len(self.task_queue):
            task = self.task_queue[task_id]
            task["status"] = "completed"
            task["result"] = result
            self.completed_tasks.append(task)
            self.update_agent_status(task["assigned_to"], "task_completed")

class BaseAgent:
    """Base class for all agents in the system"""

    def __init__(self, name: str, state: AgentState):
        self.name = name
        self.state = state
        self.status = "idle"

    async def execute(self, task: dict, context: WorkflowContext) -> dict:
        """Execute a task - to be implemented by subclasses"""
        raise NotImplementedError

    def can_handle_task(self, task: dict) -> bool:
        """Check if agent can handle the task"""
        return True

    def update_status(self, status: str):
        """Update agent status"""
        self.status = status
        self.state.update_agent_status(self.name, status)

class ResearchAgent(BaseAgent):
    """Agent responsible for research and data gathering"""

    def __init__(self, state: AgentState):
        super().__init__("research_agent", state)

    async def execute(self, task: dict, context: WorkflowContext) -> dict:
        """Execute research task"""
        self.update_status("researching")

        research_topic = task.get("topic", "general research")
        depth = task.get("depth", "standard")

        # Simulate research process
        await asyncio.sleep(2)

        research_data = {
            "topic": research_topic,
            "sources_found": 5 if depth == "standard" else 10,
            "key_findings": [
                "Finding 1 about the topic",
                "Finding 2 about the topic",
                "Finding 3 about the topic"
            ],
            "data_quality": "high" if depth == "deep" else "medium"
        }

        self.update_status("research_completed")
        return {
            "agent": self.name,
            "task_type": "research",
            "result": research_data,
            "status": "success"
        }

class AnalysisAgent(BaseAgent):
    """Agent responsible for data analysis and insights"""

    def __init__(self, state: AgentState):
        super().__init__("analysis_agent", state)

    async def execute(self, task: dict, context: WorkflowContext) -> dict:
        """Execute analysis task"""
        self.update_status("analyzing")

        data_to_analyze = task.get("research_data", {})
        analysis_type = task.get("analysis_type", "comprehensive")

        # Simulate analysis process
        await asyncio.sleep(1.5)

        analysis_result = {
            "insights": [
                "Key insight 1 from the research",
                "Key insight 2 from the research",
                "Key insight 3 from the research"
            ],
            "trends": ["Trend analysis 1", "Trend analysis 2"],
            "recommendations": [
                "Recommendation based on analysis 1",
                "Recommendation based on analysis 2"
            ],
            "confidence_score": 0.85 if analysis_type == "comprehensive" else 0.70
        }

        self.update_status("analysis_completed")
        return {
            "agent": self.name,
            "task_type": "analysis",
            "result": analysis_result,
            "status": "success"
        }

class WritingAgent(BaseAgent):
    """Agent responsible for content generation and writing"""

    def __init__(self, state: AgentState):
        super().__init__("writing_agent", state)

    async def execute(self, task: dict, context: WorkflowContext) -> dict:
        """Execute writing task"""
        self.update_status("writing")

        content_data = task.get("analysis_result", {})
        writing_style = task.get("style", "professional")
        target_audience = task.get("audience", "general")

        # Simulate writing process
        await asyncio.sleep(1)

        written_content = {
            "title": "Comprehensive Report on Research Topic",
            "summary": "This report provides a thorough analysis of the research findings...",
            "sections": [
                "## Introduction",
                "## Research Findings",
                "## Analysis and Insights",
                "## Recommendations",
                "## Conclusion"
            ],
            "word_count": 1500 if writing_style == "detailed" else 800,
            "reading_level": "professional" if target_audience == "business" else "general"
        }

        self.update_status("writing_completed")
        return {
            "agent": self.name,
            "task_type": "writing",
            "result": written_content,
            "status": "success"
        }

class AgentCoordinator:
    """Coordinates multi-agent workflows and task distribution"""

    def __init__(self):
        self.agents = {
            "research": ResearchAgent,
            "analysis": AnalysisAgent,
            "writing": WritingAgent
        }
        self.workflow_strategies = {
            "sequential": self._sequential_workflow,
            "parallel": self._parallel_workflow,
            "hybrid": self._hybrid_workflow
        }

    async def execute_workflow(self, workflow_type: str, tasks: list[dict], workflow_id: str) -> dict:
        """Execute multi-agent workflow"""
        state = AgentState(workflow_id)

        # Initialize agents
        active_agents = {}
        for agent_type, agent_class in self.agents.items():
            active_agents[agent_type] = agent_class(state)

        # Execute workflow strategy
        strategy = self.workflow_strategies.get(workflow_type, self._sequential_workflow)
        result = await strategy(tasks, active_agents, state)

        return {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "result": result,
            "coordination_stats": {
                "total_tasks": len(tasks),
                "completed_tasks": len(state.completed_tasks),
                "agents_used": list(active_agents.keys()),
                "coordination_log": state.coordination_log
            }
        }

    async def _sequential_workflow(self, tasks: list[dict], agents: dict, state: AgentState) -> dict:
        """Sequential workflow - one agent at a time"""
        results = []

        for i, task in enumerate(tasks):
            # Determine which agent should handle this task
            agent_type = self._determine_agent_for_task(task)
            agent = agents.get(agent_type)

            if agent and agent.can_handle_task(task):
                context = WorkflowContext(
                    workflow_id=state.workflow_id,
                    metadata={"task_index": i, "agent_type": agent_type}
                )

                result = await agent.execute(task, context)
                results.append(result)

                state.complete_task(i, result)

        return {"sequential_results": results}

    async def _parallel_workflow(self, tasks: list[dict], agents: dict, state: AgentState) -> dict:
        """Parallel workflow - multiple agents working simultaneously"""
        # Group tasks by agent type
        agent_tasks = {}
        for i, task in enumerate(tasks):
            agent_type = self._determine_agent_for_task(task)
            if agent_type not in agent_tasks:
                agent_tasks[agent_type] = []
            agent_tasks[agent_type].append((i, task))

        # Execute tasks in parallel for each agent
        agent_results = {}
        for agent_type, task_list in agent_tasks.items():
            agent = agents.get(agent_type)
            if agent:
                # Create parallel execution for this agent's tasks
                parallel_tasks = []
                for task_id, task in task_list:
                    context = WorkflowContext(
                        workflow_id=state.workflow_id,
                        metadata={"task_id": task_id, "agent_type": agent_type}
                    )
                    task_coro = agent.execute(task, context)
                    parallel_tasks.append((task_id, task_coro))

                # Execute all tasks for this agent in parallel
                completed_tasks = await asyncio.gather(
                    *[task[1] for task in parallel_tasks],
                    return_exceptions=True
                )

                # Store results
                for (task_id, _), result in zip(parallel_tasks, completed_tasks):
                    if not isinstance(result, Exception):
                        agent_results[task_id] = result
                        state.complete_task(task_id, result)
                    else:
                        agent_results[task_id] = {"error": str(result)}

        return {"parallel_results": agent_results}

    async def _hybrid_workflow(self, tasks: list[dict], agents: dict, state: AgentState) -> dict:
        """Hybrid workflow - combination of sequential and parallel"""
        # Use sequential for dependent tasks, parallel for independent ones
        sequential_results = []
        parallel_tasks = []

        for i, task in enumerate(tasks):
            if task.get("depends_on_previous", False):
                # This task should be done sequentially
                agent_type = self._determine_agent_for_task(task)
                agent = agents.get(agent_type)

                if agent:
                    context = WorkflowContext(
                        workflow_id=state.workflow_id,
                        metadata={"task_index": i, "agent_type": agent_type, "sequential": True}
                    )

                    result = await agent.execute(task, context)
                    sequential_results.append(result)
                    state.complete_task(i, result)
            else:
                # This task can be done in parallel
                parallel_tasks.append((i, task, agent_type))

        # Execute parallel tasks
        if parallel_tasks:
            parallel_results = await self._execute_parallel_tasks(parallel_tasks, agents, state)
            return {
                "sequential_results": sequential_results,
                "parallel_results": parallel_results
            }

        return {"sequential_results": sequential_results}

    async def _execute_parallel_tasks(self, parallel_tasks: list, agents: dict, state: AgentState) -> dict:
        """Execute tasks in parallel"""
        task_coroutines = []

        for task_id, task, agent_type in parallel_tasks:
            agent = agents.get(agent_type)
            if agent:
                context = WorkflowContext(
                    workflow_id=state.workflow_id,
                    metadata={"task_id": task_id, "agent_type": agent_type, "parallel": True}
                )
                task_coro = agent.execute(task, context)
                task_coroutines.append((task_id, task_coro))

        # Execute all parallel tasks
        completed_tasks = await asyncio.gather(
            *[task[1] for task in task_coroutines],
            return_exceptions=True
        )

        # Store results
        results = {}
        for (task_id, _), result in zip(task_coroutines, completed_tasks):
            if not isinstance(result, Exception):
                results[task_id] = result
                state.complete_task(task_id, result)
            else:
                results[task_id] = {"error": str(result)}

        return results

    def _determine_agent_for_task(self, task: dict) -> str:
        """Determine which agent should handle the task"""
        task_type = task.get("type", "general")

        if task_type in ["research", "gather", "collect"]:
            return "research"
        elif task_type in ["analyze", "insight", "evaluate"]:
            return "analysis"
        elif task_type in ["write", "create", "generate"]:
            return "writing"
        else:
            # Default routing based on content
            content = str(task.get("content", ""))
            if any(keyword in content.lower() for keyword in ["research", "study", "investigate"]):
                return "research"
            elif any(keyword in content.lower() for keyword in ["analyze", "trend", "pattern"]):
                return "analysis"
            else:
                return "writing"

# Usage examples
async def main():
    coordinator = AgentCoordinator()

    # Sequential workflow example
    sequential_tasks = [
        {"type": "research", "topic": "AI trends in 2025", "depth": "standard"},
        {"type": "analysis", "analysis_type": "comprehensive"},
        {"type": "writing", "style": "professional", "audience": "business"}
    ]

    sequential_result = await coordinator.execute_workflow(
        "sequential",
        sequential_tasks,
        "report_generation_sequential"
    )
    print(f"Sequential workflow completed: {len(sequential_result['coordination_stats']['completed_tasks'])} tasks")

    # Parallel workflow example
    parallel_tasks = [
        {"type": "research", "topic": "Market analysis", "depth": "standard"},
        {"type": "research", "topic": "Technology trends", "depth": "standard"},
        {"type": "analysis", "analysis_type": "standard"}
    ]

    parallel_result = await coordinator.execute_workflow(
        "parallel",
        parallel_tasks,
        "research_aggregation_parallel"
    )
    print(f"Parallel workflow completed: {len(parallel_result['coordination_stats']['completed_tasks'])} tasks")

    # Hybrid workflow example
    hybrid_tasks = [
        {"type": "research", "topic": "Industry overview", "depth": "standard", "depends_on_previous": False},
        {"type": "analysis", "analysis_type": "comprehensive", "depends_on_previous": True},
        {"type": "writing", "style": "detailed", "audience": "technical", "depends_on_previous": True},
        {"type": "research", "topic": "Competitive landscape", "depth": "standard", "depends_on_previous": False}
    ]

    hybrid_result = await coordinator.execute_workflow(
        "hybrid",
        hybrid_tasks,
        "comprehensive_analysis_hybrid"
    )
    print(f"Hybrid workflow completed: {len(hybrid_result['coordination_stats']['completed_tasks'])} tasks")
```

**Cline's Learning Pattern:**

- Identifies complex multi-agent coordination needs
- Uses AgentState for shared state management across agents
- Implements different workflow strategies (sequential, parallel, hybrid)
- Provides intelligent task routing based on task type
- Includes comprehensive error handling and coordination logging
- Uses proper WorkflowContext for agent coordination tracking

## Cline Detection Patterns

**Multi-Agent Workflow Indicators:**

- "multiple agents working together"
- "coordinate between agents"
- "multi-agent system"
- "agent handoff"
- "workflow coordination"
- "shared state between agents"
- "agent orchestration"
- "delegation patterns"

**Cline's Response Strategy:**

1. Identify multi-agent coordination scenarios
2. Suggest BaseAgent pattern with proper state management
3. Recommend appropriate workflow strategies (sequential/parallel/hybrid)
4. Implement AgentState for shared data and coordination
5. Use WorkflowContext for agent coordination tracking

## Common Mistakes to Avoid

❌ **Wrong:** Agents sharing mutable state directly

```python
# Shared global state - dangerous!
global_shared_data = {}

class Agent:
    async def execute(self, task):
        global_shared_data["result"] = task["data"]  # Race conditions!
```

✅ **Right:** Use AgentState for coordination

```python
# Safe shared state management
class AgentState:
    def __init__(self, workflow_id):
        self.workflow_id = workflow_id
        self.shared_data = {}
        self.coordination_log = []

agent_state = AgentState("workflow_123")
agent = ResearchAgent(agent_state)
```

❌ **Wrong:** No coordination strategy

```python
# Agents work independently
result1 = await research_agent.execute(task1)
result2 = await analysis_agent.execute(task2)  # No coordination!
```

✅ **Right:** Structured coordination workflow

```python
# Coordinated multi-agent workflow
coordinator = AgentCoordinator()
result = await coordinator.execute_workflow("sequential", tasks, workflow_id)
```

❌ **Wrong:** No fallback for failed agents

```python
# Single point of failure
if not research_agent.available:
    return {"error": "Cannot proceed"}  # System fails!
```

✅ **Right:** Fallback strategies and error handling

```python
# Resilient multi-agent system
try:
    result = await primary_agent.execute(task)
except Exception:
    result = await fallback_agent.execute(task)  # Graceful degradation
```

---

**Next Steps:** When cline detects complex multi-agent coordination scenarios, it should automatically suggest appropriate workflow patterns, state management strategies, and coordination mechanisms based on the specific use case requirements.


---
**Logseq:** [[TTA.dev/.cline/Examples/Workflows/Complete_service_architecture]]
