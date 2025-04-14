# Dynamic Tool System

This document provides a detailed overview of the Dynamic Tool System used in the Therapeutic Text Adventure (TTA) project.

## Related Documentation

- [System Architecture](./System_Architecture.md): Overview of the TTA system architecture
- [AI Agents](./AI_Agents.md): Details about the AI agents that use the tools
- [Knowledge Graph](./Knowledge_Graph.md): Information about the knowledge graph that tools interact with
- [Models Guide](../Models/Models_Guide.md): Details about the LLM models used for tool execution

## Overview

The Dynamic Tool System is a core component of the TTA architecture that enables AI agents to interact with the game world in a flexible and extensible way. Unlike traditional static tools, dynamic tools are generated and selected based on the current game state, player intent, and available actions.

```
┌─────────────────────────────────────────────────────────────────┐
│                      Dynamic Tool System                         │
└─────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│   Tool Generator  │  │   Tool Selector   │  │   Tool Executor   │
└───────────────────┘  └───────────────────┘  └───────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│  Standard Tools   │  │ Therapeutic Tools │  │  Composite Tools  │
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

## Key Components

### Tool Generator

The Tool Generator dynamically creates tools based on the current game state and available actions. It uses templates and schemas to define the structure and behavior of tools.

**Key Files:**
- `src/tools/dynamic_tool_generator.py`: Main tool generation logic
- `src/tools/dynamic_tool_schema.py`: Schemas for dynamic tools
- `src/tools/enhanced_tool_generator.py`: Advanced tool generation with additional features
- `src/tools/simple_tool_generator.py`: Basic tool generation for simple actions

**Example: Creating a Dynamic Movement Tool**

```python
from tools.dynamic_tool_generator import DynamicToolGenerator
from knowledge.neo4j_manager import Neo4jManager

# Initialize the Neo4j manager and tool generator
neo4j_manager = Neo4jManager()
tool_generator = DynamicToolGenerator(neo4j_manager)

# Get the current location and available exits
current_location = neo4j_manager.get_player_location()
exits = neo4j_manager.get_location_exits(current_location)

# Generate movement tools for each available exit
movement_tools = []
for direction, destination in exits.items():
    tool = tool_generator.create_movement_tool(
        direction=direction,
        destination=destination,
        description=f"Move to {destination} by going {direction}"
    )
    movement_tools.append(tool)
```

### Tool Selector

The Tool Selector chooses the most appropriate tools based on the player's intent and the current game state. It uses natural language understanding and context to determine which tools are relevant.

**Key Files:**
- `src/tools/tool_selector.py`: Main tool selection logic
- `src/tools/selector.py`: Advanced selection algorithms

**Example: Selecting Tools Based on Player Intent**

```python
from tools.tool_selector import ToolSelector
from agents.input_processor import InputProcessor

# Initialize the input processor and tool selector
input_processor = InputProcessor()
tool_selector = ToolSelector()

# Process player input to determine intent
player_input = "look at the rusty key"
parsed_input = input_processor.parse(player_input)

# Select appropriate tools based on intent
selected_tools = tool_selector.select_tools_for_intent(
    intent=parsed_input.intent,
    entities=parsed_input.entities,
    available_tools=all_tools
)
```

### Tool Executor

The Tool Executor runs the selected tools and processes their results. It handles tool execution, error handling, and result formatting.

**Key Files:**
- `src/tools/dynamic_tools.py`: Main tool execution logic

**Example: Executing a Selected Tool**

```python
from tools.dynamic_tools import ToolExecutor

# Initialize the tool executor
tool_executor = ToolExecutor()

# Execute the selected tool
result = tool_executor.execute_tool(
    tool=selected_tools[0],
    args=parsed_input.entities,
    agent_state=current_state
)

# Process the result
updated_state = tool_executor.update_state_with_result(
    state=current_state,
    result=result
)
```

## Tool Types

### Standard Tools

Standard tools handle common game actions such as movement, examination, inventory management, and conversation.

**Examples:**
- **Movement Tools**: Move the player between locations
- **Examination Tools**: Examine objects, characters, or locations
- **Inventory Tools**: Manage the player's inventory
- **Conversation Tools**: Interact with non-player characters

### Therapeutic Tools

Therapeutic tools integrate therapeutic concepts and techniques into the game experience. They help create a personalized and potentially therapeutic experience for the player.

**Key Files:**
- `src/tools/therapeutic_tools.py`: Therapeutic tool implementations

**Examples:**
- **Reflection Tools**: Prompt the player to reflect on their experiences
- **Emotion Tools**: Help the player identify and process emotions
- **Coping Tools**: Introduce coping strategies for difficult situations
- **Mindfulness Tools**: Encourage mindfulness and present-moment awareness

### Composite Tools

Composite tools combine multiple simpler tools to handle complex actions. They use the Tool Composer to create and execute sequences of tools.

**Key Files:**
- `src/tools/tool_composer.py`: Tool composition logic
- `src/tools/composer.py`: Advanced composition strategies

**Example: Creating a Composite Tool**

```python
from tools.tool_composer import ToolComposer

# Initialize the tool composer
tool_composer = ToolComposer()

# Create a composite tool for picking up an item
pickup_tool = tool_composer.compose(
    name="pickup_item",
    description="Pick up an item and add it to the player's inventory",
    component_tools=[
        examine_tool,  # First examine the item
        take_tool,     # Then take the item
        inventory_tool # Finally, update the inventory
    ],
    execution_order="sequential"
)
```

## Tool Registration and Discovery

Tools are registered with the Tool Registry, which maintains a catalog of available tools and their metadata. The registry enables tool discovery and selection.

**Key Files:**
- `src/tools/registry.py`: Tool registration and discovery

**Example: Registering and Discovering Tools**

```python
from tools.registry import ToolRegistry

# Initialize the tool registry
registry = ToolRegistry()

# Register a tool
registry.register_tool(
    tool=movement_tool,
    category="movement",
    priority=1
)

# Discover tools by category
movement_tools = registry.get_tools_by_category("movement")

# Discover tools by intent
examination_tools = registry.get_tools_for_intent("examine")
```

## Integration with LangGraph

The Dynamic Tool System integrates with LangGraph to enable AI agents to use tools within the LangGraph workflow. This integration allows for seamless tool execution and state management.

**Key Files:**
- `src/core/dynamic_langgraph.py`: LangGraph integration
- `src/features/game_loop/langgraph.py`: Game loop integration

For more details about LangGraph, see the [AI Libraries Integration Plan](../Integration/AI_Libraries_Integration_Plan.md#4-langgraph).

**Example: Using Tools in LangGraph**

```python
from core.dynamic_langgraph import create_agent_workflow
from tools.registry import ToolRegistry

# Initialize the tool registry and register tools
registry = ToolRegistry()
registry.register_tools(all_tools)

# Create a LangGraph workflow with tool support
workflow = create_agent_workflow(
    agents=[input_processor, narrative_generator],
    tools=registry.get_all_tools()
)

# Run the workflow
result = workflow.invoke({
    "player_input": "look at the rusty key",
    "game_state": current_game_state
})
```

## Tool Schema

Tools are defined using a schema that specifies their name, description, parameters, and behavior. The schema ensures consistency and enables validation. The schema is implemented using Pydantic, which provides automatic validation and documentation.

**Example: Tool Schema**

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class ToolParameter(BaseModel):
    name: str
    description: str
    type: str
    required: bool = True
    default: Optional[any] = None

class ToolSchema(BaseModel):
    name: str
    description: str
    category: str
    parameters: List[ToolParameter]
    return_type: str
    function_name: str
```

## Performance Considerations

The Dynamic Tool System is designed to be efficient and scalable. Here are some performance considerations:

- **Caching**: Tool results are cached to avoid redundant execution
- **Lazy Loading**: Tools are loaded only when needed
- **Parallel Execution**: Some tools can be executed in parallel
- **Resource Management**: Tools are designed to minimize resource usage

## Security Considerations

The Dynamic Tool System includes security features to prevent misuse:

- **Input Validation**: All tool inputs are validated using Pydantic schemas
- **Sandboxing**: Tools run in a controlled environment
- **Permission System**: Tools have different permission levels
- **Logging**: All tool executions are logged for auditing

## Related Documentation

- [AI Agents](./AI_Agents.md): Overview of the AI agent roles and their use of tools
- [System Architecture](./System_Architecture.md): Overall system architecture
- [Knowledge Graph](./Knowledge_Graph.md): Knowledge graph schema and usage
- [LangGraph Integration](../Integration/AI_Libraries_Integration_Plan.md#4-langgraph): Details about LangGraph integration
- [Models Guide](../Models/Models_Guide.md): Information about the models used for tool execution
