# Agent Coordination Primitives - Examples

This directory contains practical examples demonstrating the three agent coordination primitives:

1. **AgentHandoffPrimitive** - Task delegation between agents
2. **AgentMemoryPrimitive** - Persistent decision storage
3. **AgentCoordinationPrimitive** - Parallel multi-agent execution

---

## 📚 Examples Overview

### 1. Agent Handoff Example

**File:** [`agent_handoff_example.py`](agent_handoff_example.py)

Demonstrates how to transfer tasks between agents with context preservation.

**Workflow:**
```
DataCollector → Handoff → DataAnalyzer → Handoff → ReportGenerator
```

**Key Features:**
- Immediate handoff strategy
- Context preservation
- Agent history tracking
- Metadata propagation

**Run:**
```bash
uv run python packages/universal-agent-context/examples/agent_handoff_example.py
```

---

### 2. Agent Memory Example

**File:** [`agent_memory_example.py`](agent_memory_example.py)

Shows how to store and retrieve architectural decisions across agents.

**Workflow:**
```
Architect → Store Decision → Implementer → Retrieve Decision → Reviewer
```

**Key Features:**
- Store/retrieve/query/list operations
- Session-scoped memory
- Cross-agent decision sharing
- Memory querying with filters

**Run:**
```bash
uv run python packages/universal-agent-context/examples/agent_memory_example.py
```

---

### 3. Parallel Agents Example

**File:** [`parallel_agents_example.py`](parallel_agents_example.py)

Demonstrates three coordination strategies for parallel agent execution.

**Strategies:**
- **Aggregate:** Collect all results
- **First Success:** Return first successful result
- **Consensus:** Find majority agreement

**Scenarios:**
1. Code review with multiple analyzers (aggregate)
2. Multi-LLM routing (first success)
3. Approval voting (consensus)

**Run:**
```bash
uv run python packages/universal-agent-context/examples/parallel_agents_example.py
```

---

### 4. Complete Multi-Agent Workflow

**File:** [`multi_agent_workflow.py`](multi_agent_workflow.py)

Real-world software development lifecycle workflow combining all three primitives.

**Phases:**
1. **Architectural Design** - Architect makes decisions, stores in memory
2. **Specialist Analysis** - Security, Performance, Infrastructure work in parallel
3. **Store Requirements** - Specialist results stored in memory
4. **Implementation** - Retrieves all decisions and implements
5. **QA Validation** - Validates against original decisions

**Workflow Diagram:**
```
Architect → Store → Handoff
                    ↓
        [Security | Performance | Infrastructure]  (Parallel)
                    ↓
              Store Results
                    ↓
         Retrieve All Decisions
                    ↓
            Implementation → Handoff
                              ↓
                             QA
```

**Run:**
```bash
uv run python packages/universal-agent-context/examples/multi_agent_workflow.py
```

---

## 🎯 Quick Start

### Prerequisites

1. Install the package:
```bash
cd packages/universal-agent-context
uv pip install -e .
```

2. Make sure `tta-dev-primitives` is installed:
```bash
cd packages/tta-dev-primitives
uv pip install -e .
```

### Running All Examples

```bash
# From repository root
uv run python packages/universal-agent-context/examples/agent_handoff_example.py
uv run python packages/universal-agent-context/examples/agent_memory_example.py
uv run python packages/universal-agent-context/examples/parallel_agents_example.py
uv run python packages/universal-agent-context/examples/multi_agent_workflow.py
```

---

## 📖 Learning Path

**New to Agent Coordination?** Follow this order:

1. **Start with Handoff** - Learn basic agent-to-agent delegation
2. **Add Memory** - Understand persistent state across agents
3. **Try Parallel** - Explore concurrent agent execution
4. **Complete Workflow** - See everything working together

---

## 🔑 Key Concepts

### WorkflowContext

All primitives use `WorkflowContext` for state management:

```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    workflow_id="my-workflow",
    session_id="session-123"
)

# Primitives update context.metadata automatically
context.metadata["current_agent"] = "architect"
context.metadata["agent_history"] = [...]
context.metadata["agent_memory"] = {...}
```

### Composition

Primitives compose using operators:

```python
# Sequential composition (>>)
workflow = step1 >> step2 >> step3

# Parallel composition (|)
workflow = branch1 | branch2 | branch3

# Mixed composition
workflow = (
    step1 >>
    (parallel1 | parallel2 | parallel3) >>
    step2
)
```

---

## 🎨 Customization

### Creating Custom Agents

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class MyCustomAgent(WorkflowPrimitive[dict, dict]):
    def __init__(self):
        self.name = "my_agent"

    async def execute(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        # Your agent logic here
        return {"result": "processed"}
```

### Custom Handoff Strategies

```python
from universal_agent_context.primitives import AgentHandoffPrimitive

# Conditional handoff
handoff = AgentHandoffPrimitive(
    target_agent="specialist",
    handoff_strategy="conditional",
    handoff_condition=lambda data: data.get("complexity") > 0.8
)
```

### Custom Memory Scopes

```python
from universal_agent_context.primitives import AgentMemoryPrimitive

# Global scope (shared across all workflows)
global_memory = AgentMemoryPrimitive(
    operation="store",
    memory_key="system_config",
    memory_scope="global"
)

# Workflow scope (isolated to single workflow)
workflow_memory = AgentMemoryPrimitive(
    operation="store",
    memory_key="temp_data",
    memory_scope="workflow"
)
```

---

## 🧪 Testing

Each example includes assertions and debug output. To run with pytest:

```bash
# Run tests for the primitives
uv run pytest packages/universal-agent-context/tests/ -v

# Run examples as tests
uv run python -m pytest packages/universal-agent-context/examples/ --doctest-modules
```

---

## 📚 Additional Resources

- **Primitives Catalog:** [`/PRIMITIVES_CATALOG.md`](../../../PRIMITIVES_CATALOG.md)
- **Package README:** [`../README.md`](../README.md)
- **Main Agent Instructions:** [`/AGENTS.md`](../../../AGENTS.md)
- **API Documentation:** [`../src/universal_agent_context/primitives/`](../src/universal_agent_context/primitives/)

---

## 💡 Tips

1. **Start Simple:** Begin with single-agent workflows before adding coordination
2. **Use Memory Wisely:** Choose appropriate scope (workflow/session/global)
3. **Monitor Performance:** Parallel execution shines with I/O-bound operations
4. **Handle Failures:** Use `require_all_success=False` for fault tolerance
5. **Track History:** Agent history in context helps debug complex workflows

---

## 🤝 Contributing

Found a bug or want to add an example? See [`/CONTRIBUTING.md`](../../../CONTRIBUTING.md).

---

**Last Updated:** October 29, 2025
**Package Version:** 1.0.0
**Maintained by:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Platform/Agent-context/Examples/Readme]]
