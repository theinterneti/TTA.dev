# TTA.dev Knowledge Graph Schema Documentation

This document outlines the schema and conventions for organizing the TTA.dev framework's knowledge within Logseq. The goal is to create a living "developer's manual" that maps the framework's architecture, making it easier to understand, navigate, and contribute to.

## Phase 1: Framework Primitive Taxonomy

The TTA.dev framework is organized around five core "primitive" types. These types are abstract enough to describe the framework itself, not any specific application built with it.

- **[C] CoreConcept**: A core architectural idea or principle of the framework (e.g., StateManagement, GraphCompilation, ToolBinding).
- **[G] GraphComponent**: A specific LangGraph node, edge, or subgraph definition (e.g., EntrypointNode, PrimaryAgentState, SafetyCheckEdge).
- **[D] DataSchema**: A key data structure, likely a Pydantic model, that defines state or message passing (e.g., AgentState, ToolCallRequest, GraphConfig).
- **[T] ToolInterface**: An abstract definition or concrete implementation of a tool usable by agents (e.g., BaseTool, Neo4jSearchTool, RedisCacheTool).
- **[S] Service**: A discrete microservice or infrastructure component (e.g., APIServer-FastAPI, GraphExecutor-LangGraph, VectorDB-Neo4j).

## Phase 2: Logseq Metadata Schema Design

Each primitive's Logseq page will embed properties to capture hierarchy, relationships, and context.

### Universal Properties (for all primitives):

- `type::` (One of: `[C] CoreConcept`, `[G] GraphComponent`, `[D] DataSchema`, `[T] ToolInterface`, `[S] Service`)
- `status::` (One of: `stable`, `beta`, `idea`, `deprecated`)
- `tags::` (Comma-separated list, e.g., `#state`, `#routing`, `#tool-use`, `#langgraph`, `#fastapi`)
- `context-level::` (The "altitude" of the concept: `1-Strategic`, `2-Operational`, `3-Technical`)

### Context-Specific Properties (Examples):

#### For `type:: [G] GraphComponent`:

- `component-type::` (e.g., `node`, `edge`, `graph`)
- `in-graph::` (Link to the parent graph it belongs to, e.g., `[[TTA.dev/Graph/MainGraph]]`)
- `modifies-state::` (Links to `[D] DataSchema` fields it alters, e.g., `[[TTA.dev/Data/AgentState.messages]]`)
- `calls-tools::` (Links to `[T] ToolInterface`s, e.g., `[[TTA.dev/Tools/Neo4jSearchTool]]`)
- `source-file::` (Path to code, e.g., ``tta_dev/graphs/main_graph.py``)

#### For `type:: [C] CoreConcept`:

- `summary::` (A one-sentence definition of the concept)
- `implemented-by::` (Links to `[G] GraphComponent`s or `[S] Service`s that realize this idea)

#### For `type:: [D] DataSchema`:

- `used-by::` (Links to `[G] GraphComponent`s or `[T] ToolInterface`s)
- `source-file::` (Path to code, e.g., ``tta_dev/models/state.py``)

#### For `type:: [S] Service`:

- `exposes::` (Links to related concepts, e.g., `[[API-Endpoint]]`, `[[TTA.dev/Graph/PrimaryAgentState]]`)
- `depends-on::` (Links to other `[S] Service`s, e.g., `[[TTA.dev/Services/Infrastructure-Redis]]`)

## Phase 3: Hierarchy & Linking Strategy

### 1. Hierarchical Organization (via Logseq Namespaces):

Logseq's namespace feature (using `/` in page titles) is used to create a clear directory-like hierarchy.

**Example Structure:**
- `TTA.dev/Concepts/StateManagement`
- `TTA.dev/Graph/MainGraph`
- `TTA.dev/Graph/Nodes/ToolExecutorNode`
- `TTA.dev/Graph/Edges/ConditionalSafetyEdge`
- `TTA.dev/Data/AgentState`
- `TTA.dev/Tools/BaseTool`
- `TTA.dev/Services/FastAPI-Server`

### 2. Contextual Linking (via `[[Page Links]]`):

The properties from Phase 2 are the primary source of relational links (e.g., `modifies-state:: [[...]]`).

Within the content (the body) of each page, any mention of another framework primitive must be enclosed in `[[double-brackets]]` to create a backlink and visualize the connection.

**Example Page Content (TTA.dev/Graph/Nodes/ToolExecutorNode.md):**

```markdown
- ---
- type:: [G] GraphComponent
- component-type:: node
- status:: stable
- tags:: #tool-use, #langgraph, #execution
- context-level:: 3-Technical
- in-graph:: [[TTA.dev/Graph/MainGraph]]
- modifies-state:: [[TTA.dev/Data/AgentState.tool_calls]], [[TTA.dev/Data/AgentState.messages]]
- calls-tools:: [[TTA.dev/Tools/BaseTool]]
- source-file:: `tta_dev/graphs/nodes/tools.py`
- ---
- ### Summary
  - This node is responsible for invoking one or more tools based on the last message in the `[[TTA.dev/Data/AgentState]]`.
- ### Logic
  - 1. Reads the `tool_calls` attribute from the state.
  - 2. Iterates through each request and dynamically calls the corresponding `[[TTA.dev/Tools/BaseTool]]` implementation.
  - 3. Appends the tool's output as a new `ToolMessage` to the `messages` list.


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Readme]]
