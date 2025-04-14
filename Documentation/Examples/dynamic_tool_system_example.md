# Dynamic Tool System Example

This document provides practical examples of implementing and using the Dynamic Tool System in the TTA project.

## Basic Tool Creation

Here's a basic example of creating a tool:

```python
from langchain_core.tools import BaseTool, tool
from typing import Dict, List, Optional, Any

@tool
def examine_object(object_name: str) -> str:
    """Examine an object in the current location.
    
    Args:
        object_name: The name of the object to examine
        
    Returns:
        A description of the object
    """
    # In a real implementation, this would query the knowledge graph
    # For this example, we'll return a simple description
    return f"You examine the {object_name} closely. It appears to be an ordinary {object_name}."
```

## Dynamic Tool Generator

Here's an example of a dynamic tool generator that creates tools based on the current game state:

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool, tool

class DynamicToolGenerator:
    def __init__(self, neo4j_manager):
        """Initialize the dynamic tool generator.
        
        Args:
            neo4j_manager: An instance of the Neo4jManager for querying the knowledge graph
        """
        self.neo4j_manager = neo4j_manager
        
    def create_movement_tool(self, direction: str, destination: str, description: str) -> BaseTool:
        """Create a dynamic movement tool for a specific direction.
        
        Args:
            direction: The direction to move (e.g., "north", "south")
            destination: The name of the destination location
            description: A description of the movement
            
        Returns:
            A BaseTool instance for the movement
        """
        # Define a function for this specific movement
        def move_function() -> str:
            # In a real implementation, this would update the player's location
            return f"You move {direction} to {destination}."
        
        # Set the function's metadata
        move_function.__name__ = f"move_{direction}"
        move_function.__doc__ = f"Move {direction} to {destination}. {description}"
        
        # Create and return a tool from the function
        return tool(move_function)
    
    def generate_movement_tools(self, current_location_id: str) -> List[BaseTool]:
        """Generate movement tools based on the available exits from the current location.
        
        Args:
            current_location_id: The ID of the current location
            
        Returns:
            A list of movement tools
        """
        # Query the knowledge graph for available exits
        query = """
        MATCH (l:Location {location_id: $location_id})-[r:CONNECTS_TO]->(destination:Location)
        WHERE NOT destination.hidden AND NOT destination.locked
        RETURN r.direction AS direction, destination.name AS destination_name, 
               destination.location_id AS destination_id, r.description AS description
        """
        
        exits = self.neo4j_manager.execute_query(query, {"location_id": current_location_id})
        
        # Create a movement tool for each available exit
        movement_tools = []
        for exit_info in exits:
            tool = self.create_movement_tool(
                direction=exit_info["direction"],
                destination=exit_info["destination_name"],
                description=exit_info.get("description", "")
            )
            movement_tools.append(tool)
            
        return movement_tools
    
    def create_interaction_tool(self, object_id: str, object_name: str, action: str) -> BaseTool:
        """Create a dynamic interaction tool for a specific object.
        
        Args:
            object_id: The ID of the object
            object_name: The name of the object
            action: The action to perform (e.g., "use", "take")
            
        Returns:
            A BaseTool instance for the interaction
        """
        # Define a function for this specific interaction
        def interaction_function() -> str:
            # In a real implementation, this would update the game state
            return f"You {action} the {object_name}."
        
        # Set the function's metadata
        interaction_function.__name__ = f"{action}_{object_name.lower().replace(' ', '_')}"
        interaction_function.__doc__ = f"{action.capitalize()} the {object_name}."
        
        # Create and return a tool from the function
        return tool(interaction_function)
    
    def generate_interaction_tools(self, current_location_id: str) -> List[BaseTool]:
        """Generate interaction tools based on the objects in the current location.
        
        Args:
            current_location_id: The ID of the current location
            
        Returns:
            A list of interaction tools
        """
        # Query the knowledge graph for interactive objects
        query = """
        MATCH (l:Location {location_id: $location_id})-[:CONTAINS]->(i:Item)
        WHERE i.visible AND i.interactive
        RETURN i.item_id AS item_id, i.name AS item_name, i.actions AS actions
        """
        
        objects = self.neo4j_manager.execute_query(query, {"location_id": current_location_id})
        
        # Create interaction tools for each object and available action
        interaction_tools = []
        for obj in objects:
            for action in obj.get("actions", ["examine"]):
                tool = self.create_interaction_tool(
                    object_id=obj["item_id"],
                    object_name=obj["item_name"],
                    action=action
                )
                interaction_tools.append(tool)
                
        return interaction_tools
    
    def generate_tools_for_state(self, game_state: Dict[str, Any]) -> List[BaseTool]:
        """Generate all tools based on the current game state.
        
        Args:
            game_state: The current game state
            
        Returns:
            A list of all available tools
        """
        current_location_id = game_state.get("current_location_id")
        if not current_location_id:
            return []
            
        # Generate movement tools
        movement_tools = self.generate_movement_tools(current_location_id)
        
        # Generate interaction tools
        interaction_tools = self.generate_interaction_tools(current_location_id)
        
        # Combine all tools
        all_tools = movement_tools + interaction_tools
        
        return all_tools
```

## Tool Selector

Here's an example of a tool selector that chooses the most appropriate tools based on the player's intent:

```python
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool

class ToolSelector:
    def __init__(self):
        """Initialize the tool selector."""
        pass
        
    def select_tools_for_intent(self, intent: str, entities: Dict[str, Any], 
                               available_tools: List[BaseTool]) -> List[BaseTool]:
        """Select appropriate tools based on the player's intent and entities.
        
        Args:
            intent: The player's intent (e.g., "move", "examine", "take")
            entities: Entities extracted from the player's input
            available_tools: List of all available tools
            
        Returns:
            A list of selected tools
        """
        selected_tools = []
        
        # Filter tools based on intent
        if intent == "move":
            # Select movement tools
            direction = entities.get("direction")
            if direction:
                for tool in available_tools:
                    if tool.name.startswith(f"move_{direction}"):
                        selected_tools.append(tool)
                        break
            else:
                # If no direction specified, include all movement tools
                selected_tools.extend([t for t in available_tools if t.name.startswith("move_")])
                
        elif intent == "examine":
            # Select examination tools
            object_name = entities.get("object")
            if object_name:
                for tool in available_tools:
                    if "examine" in tool.name and object_name.lower() in tool.name:
                        selected_tools.append(tool)
                        break
            else:
                # If no object specified, include the generic examine tool
                for tool in available_tools:
                    if tool.name == "examine_object":
                        selected_tools.append(tool)
                        break
                        
        elif intent == "take" or intent == "use":
            # Select interaction tools
            object_name = entities.get("object")
            if object_name:
                for tool in available_tools:
                    if (intent in tool.name and 
                        object_name.lower().replace(" ", "_") in tool.name):
                        selected_tools.append(tool)
                        break
                        
        # If no specific tools were selected, return a subset of general tools
        if not selected_tools:
            # Include some general tools as fallback
            general_tools = [t for t in available_tools if t.name in 
                            ["examine_object", "look_around", "check_inventory"]]
            selected_tools.extend(general_tools)
            
        return selected_tools
```

## Tool Executor

Here's an example of a tool executor that runs the selected tools and processes their results:

```python
from typing import Dict, List, Any, Optional, Union
from langchain_core.tools import BaseTool

class ToolExecutor:
    def __init__(self):
        """Initialize the tool executor."""
        pass
        
    def execute_tool(self, tool: BaseTool, args: Dict[str, Any], 
                    agent_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return the result.
        
        Args:
            tool: The tool to execute
            args: Arguments for the tool
            agent_state: The current agent state
            
        Returns:
            The result of the tool execution
        """
        try:
            # Execute the tool with the provided arguments
            result = tool.invoke(args)
            
            # Process the result based on the tool type
            if tool.name.startswith("move_"):
                # Update the agent's location
                direction = tool.name.replace("move_", "")
                new_location = self._get_new_location(direction, agent_state)
                
                return {
                    "result": result,
                    "state_updates": {
                        "current_location_id": new_location["id"],
                        "current_location_name": new_location["name"]
                    }
                }
                
            elif "take_" in tool.name:
                # Update the agent's inventory
                item_name = tool.name.replace("take_", "").replace("_", " ")
                
                return {
                    "result": result,
                    "state_updates": {
                        "inventory": agent_state.get("inventory", []) + [item_name]
                    }
                }
                
            else:
                # For other tools, just return the result
                return {
                    "result": result,
                    "state_updates": {}
                }
                
        except Exception as e:
            # Handle any errors during tool execution
            return {
                "result": f"Error executing tool: {str(e)}",
                "state_updates": {},
                "error": str(e)
            }
            
    def update_state_with_result(self, state: Dict[str, Any], 
                               result: Dict[str, Any]) -> Dict[str, Any]:
        """Update the agent state with the tool execution result.
        
        Args:
            state: The current agent state
            result: The tool execution result
            
        Returns:
            The updated agent state
        """
        # Create a copy of the state to avoid modifying the original
        updated_state = state.copy()
        
        # Apply state updates from the tool result
        state_updates = result.get("state_updates", {})
        for key, value in state_updates.items():
            if isinstance(value, dict) and isinstance(updated_state.get(key, {}), dict):
                # Merge dictionaries
                updated_state[key] = {**updated_state.get(key, {}), **value}
            elif isinstance(value, list) and isinstance(updated_state.get(key, []), list):
                # Merge lists
                updated_state[key] = updated_state.get(key, []) + value
            else:
                # Replace value
                updated_state[key] = value
                
        return updated_state
        
    def _get_new_location(self, direction: str, agent_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get the new location after moving in a direction.
        
        Args:
            direction: The direction of movement
            agent_state: The current agent state
            
        Returns:
            The new location information
        """
        # In a real implementation, this would query the knowledge graph
        # For this example, we'll return a placeholder
        return {
            "id": f"loc_{direction}",
            "name": f"{direction.capitalize()} Location"
        }
```

## Tool Registry

Here's an example of a tool registry that maintains a catalog of available tools:

```python
from typing import Dict, List, Any, Optional, Callable
from langchain_core.tools import BaseTool

class ToolRegistry:
    def __init__(self):
        """Initialize the tool registry."""
        self.tools = {}
        self.categories = {}
        self.intent_mappings = {}
        
    def register_tool(self, tool: BaseTool, category: str = "general", 
                     priority: int = 0, intents: List[str] = None) -> None:
        """Register a tool with the registry.
        
        Args:
            tool: The tool to register
            category: The category of the tool
            priority: The priority of the tool (higher values = higher priority)
            intents: List of intents this tool is relevant for
        """
        # Store the tool
        self.tools[tool.name] = {
            "tool": tool,
            "category": category,
            "priority": priority
        }
        
        # Add to category mapping
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(tool.name)
        
        # Add to intent mappings
        if intents:
            for intent in intents:
                if intent not in self.intent_mappings:
                    self.intent_mappings[intent] = []
                self.intent_mappings[intent].append(tool.name)
                
    def register_tools(self, tools: List[BaseTool], category: str = "general", 
                      priority: int = 0, intents: List[str] = None) -> None:
        """Register multiple tools with the registry.
        
        Args:
            tools: The tools to register
            category: The category of the tools
            priority: The priority of the tools
            intents: List of intents these tools are relevant for
        """
        for tool in tools:
            self.register_tool(tool, category, priority, intents)
            
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name.
        
        Args:
            tool_name: The name of the tool
            
        Returns:
            The tool, or None if not found
        """
        tool_info = self.tools.get(tool_name)
        return tool_info["tool"] if tool_info else None
        
    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """Get all tools in a category.
        
        Args:
            category: The category to filter by
            
        Returns:
            A list of tools in the category
        """
        tool_names = self.categories.get(category, [])
        return [self.tools[name]["tool"] for name in tool_names if name in self.tools]
        
    def get_tools_for_intent(self, intent: str) -> List[BaseTool]:
        """Get all tools relevant for an intent.
        
        Args:
            intent: The intent to filter by
            
        Returns:
            A list of tools relevant for the intent
        """
        tool_names = self.intent_mappings.get(intent, [])
        return [self.tools[name]["tool"] for name in tool_names if name in self.tools]
        
    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools.
        
        Returns:
            A list of all tools
        """
        return [info["tool"] for info in self.tools.values()]
```

## Integration with LangGraph

Here's an example of integrating the Dynamic Tool System with LangGraph:

```python
from typing import Dict, List, Any, TypedDict, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# Define the state type
class State(TypedDict):
    messages: Annotated[list, add_messages]
    game_state: Dict[str, Any]

# Initialize components
neo4j_manager = Neo4jManager(neo4j_uri, neo4j_user, neo4j_password)
tool_generator = DynamicToolGenerator(neo4j_manager)
tool_selector = ToolSelector()
tool_executor = ToolExecutor()
registry = ToolRegistry()

# Initialize the LLM
llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")

# Define the chatbot node
def chatbot(state: State):
    # Generate dynamic tools based on the current game state
    dynamic_tools = tool_generator.generate_tools_for_state(state["game_state"])
    
    # Register the tools
    registry.register_tools(dynamic_tools, category="dynamic")
    
    # Get all tools
    all_tools = registry.get_all_tools()
    
    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(all_tools)
    
    # Generate a response
    message = llm_with_tools.invoke(state["messages"])
    
    return {"messages": [message]}

# Define the tool execution node
def execute_tools(state: State, tool_calls):
    # Get the tool call
    tool_call = tool_calls[0]
    
    # Get the tool
    tool = registry.get_tool(tool_call["name"])
    
    # Execute the tool
    result = tool_executor.execute_tool(
        tool=tool,
        args=tool_call["args"],
        agent_state=state["game_state"]
    )
    
    # Update the game state
    updated_game_state = tool_executor.update_state_with_result(
        state=state["game_state"],
        result=result
    )
    
    # Return the updated state
    return {
        "messages": [{"role": "tool", "content": result["result"]}],
        "game_state": updated_game_state
    }

# Create the graph
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", execute_tools)

# Add edges
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

# Compile the graph
graph = graph_builder.compile()

# Example usage
initial_state = {
    "messages": [
        {"role": "user", "content": "I want to explore the cave."}
    ],
    "game_state": {
        "current_location_id": "loc001",
        "current_location_name": "Forest Clearing",
        "inventory": ["torch", "map"]
    }
}

# Run the graph
result = graph.invoke(initial_state)
```

## Therapeutic Tools

Here's an example of creating therapeutic tools:

```python
from langchain_core.tools import BaseTool, tool
from typing import Dict, List, Any, Optional

class TherapeuticToolGenerator:
    def __init__(self):
        """Initialize the therapeutic tool generator."""
        pass
        
    def create_reflection_tool(self, topic: str, prompt: str) -> BaseTool:
        """Create a reflection tool for a specific topic.
        
        Args:
            topic: The topic to reflect on
            prompt: The reflection prompt
            
        Returns:
            A BaseTool instance for the reflection
        """
        # Define a function for this specific reflection
        def reflection_function() -> str:
            return f"Take a moment to reflect on {topic}. {prompt}"
        
        # Set the function's metadata
        reflection_function.__name__ = f"reflect_on_{topic.lower().replace(' ', '_')}"
        reflection_function.__doc__ = f"Reflect on {topic}. {prompt}"
        
        # Create and return a tool from the function
        return tool(reflection_function)
        
    def create_emotion_tool(self, emotion: str) -> BaseTool:
        """Create an emotion tool for a specific emotion.
        
        Args:
            emotion: The emotion to process
            
        Returns:
            A BaseTool instance for the emotion
        """
        # Define a function for this specific emotion
        def emotion_function() -> str:
            return f"You're feeling {emotion}. Let's explore this emotion together."
        
        # Set the function's metadata
        emotion_function.__name__ = f"process_{emotion.lower().replace(' ', '_')}"
        emotion_function.__doc__ = f"Process the feeling of {emotion}."
        
        # Create and return a tool from the function
        return tool(emotion_function)
        
    def create_coping_tool(self, strategy: str, description: str) -> BaseTool:
        """Create a coping tool for a specific strategy.
        
        Args:
            strategy: The coping strategy
            description: A description of the strategy
            
        Returns:
            A BaseTool instance for the coping strategy
        """
        # Define a function for this specific coping strategy
        def coping_function() -> str:
            return f"Let's try {strategy}: {description}"
        
        # Set the function's metadata
        coping_function.__name__ = f"cope_with_{strategy.lower().replace(' ', '_')}"
        coping_function.__doc__ = f"Use {strategy} as a coping mechanism. {description}"
        
        # Create and return a tool from the function
        return tool(coping_function)
        
    def generate_therapeutic_tools(self, player_state: Dict[str, Any]) -> List[BaseTool]:
        """Generate therapeutic tools based on the player's state.
        
        Args:
            player_state: The player's current state
            
        Returns:
            A list of therapeutic tools
        """
        tools = []
        
        # Generate reflection tools based on recent experiences
        recent_events = player_state.get("recent_events", [])
        for event in recent_events:
            if event.get("type") == "challenge":
                tools.append(self.create_reflection_tool(
                    topic="challenge",
                    prompt="How did you feel when facing this challenge? What did you learn?"
                ))
            elif event.get("type") == "achievement":
                tools.append(self.create_reflection_tool(
                    topic="achievement",
                    prompt="What does this achievement mean to you? How did you accomplish it?"
                ))
                
        # Generate emotion tools based on current mood
        mood = player_state.get("mood")
        if mood:
            tools.append(self.create_emotion_tool(mood))
            
        # Generate coping tools based on current challenges
        challenges = player_state.get("current_challenges", [])
        for challenge in challenges:
            if challenge.get("type") == "anxiety":
                tools.append(self.create_coping_tool(
                    strategy="deep breathing",
                    description="Take slow, deep breaths to calm your mind and body."
                ))
            elif challenge.get("type") == "frustration":
                tools.append(self.create_coping_tool(
                    strategy="perspective taking",
                    description="Consider the situation from different perspectives."
                ))
                
        return tools
```

## Composite Tools

Here's an example of creating composite tools:

```python
from langchain_core.tools import BaseTool, tool
from typing import Dict, List, Any, Optional, Callable

class ToolComposer:
    def __init__(self):
        """Initialize the tool composer."""
        pass
        
    def compose(self, name: str, description: str, component_tools: List[BaseTool], 
               execution_order: str = "sequential") -> BaseTool:
        """Compose multiple tools into a single tool.
        
        Args:
            name: The name of the composite tool
            description: The description of the composite tool
            component_tools: The tools to compose
            execution_order: The order of execution ("sequential" or "parallel")
            
        Returns:
            A BaseTool instance for the composite tool
        """
        # Define a function for the composite tool
        def composite_function(**kwargs) -> str:
            results = []
            
            if execution_order == "sequential":
                # Execute tools in sequence
                current_args = kwargs
                for tool in component_tools:
                    # Execute the tool
                    result = tool.invoke(current_args)
                    results.append(result)
                    
                    # Update args for the next tool if the result is a dict
                    if isinstance(result, dict):
                        current_args.update(result)
                        
            elif execution_order == "parallel":
                # Execute tools in parallel (in this case, just execute them all with the same args)
                for tool in component_tools:
                    result = tool.invoke(kwargs)
                    results.append(result)
                    
            # Combine the results
            combined_result = "\n".join([str(r) for r in results])
            return combined_result
            
        # Set the function's metadata
        composite_function.__name__ = name
        composite_function.__doc__ = description
        
        # Create and return a tool from the function
        return tool(composite_function)
        
    def create_pickup_item_tool(self, registry: ToolRegistry) -> BaseTool:
        """Create a composite tool for picking up an item.
        
        Args:
            registry: The tool registry
            
        Returns:
            A BaseTool instance for picking up an item
        """
        # Get the component tools
        examine_tool = registry.get_tool("examine_object")
        take_tool = registry.get_tool("take_item")
        inventory_tool = registry.get_tool("check_inventory")
        
        # Compose the tools
        pickup_tool = self.compose(
            name="pickup_item",
            description="Pick up an item and add it to your inventory",
            component_tools=[examine_tool, take_tool, inventory_tool],
            execution_order="sequential"
        )
        
        return pickup_tool
```

## Usage Example

Here's a complete example of using the Dynamic Tool System:

```python
import os
from dotenv import load_dotenv
from typing import Dict, List, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import BaseTool, tool

# Load environment variables
load_dotenv()

# Get Neo4j connection details from environment variables
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

# Initialize components
neo4j_manager = Neo4jManager(neo4j_uri, neo4j_user, neo4j_password)
tool_generator = DynamicToolGenerator(neo4j_manager)
tool_selector = ToolSelector()
tool_executor = ToolExecutor()
registry = ToolRegistry()

# Create some static tools
@tool
def look_around() -> str:
    """Look around the current location."""
    return "You look around and observe your surroundings."

@tool
def check_inventory() -> str:
    """Check your inventory."""
    return "You check your inventory."

# Register the static tools
registry.register_tool(look_around, category="general", intents=["look"])
registry.register_tool(check_inventory, category="general", intents=["inventory"])

# Generate dynamic tools based on the current game state
game_state = {
    "current_location_id": "loc001",
    "current_location_name": "Forest Clearing",
    "inventory": ["torch", "map"]
}

dynamic_tools = tool_generator.generate_tools_for_state(game_state)

# Register the dynamic tools
registry.register_tools(dynamic_tools, category="dynamic")

# Get all tools
all_tools = registry.get_all_tools()

# Initialize the LLM
llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")

# Bind tools to the LLM
llm_with_tools = llm.bind_tools(all_tools)

# Process player input
player_input = "I want to go north and then examine the cave entrance"

# Parse the input (in a real implementation, this would be done by the Input Processor Agent)
parsed_input = {
    "intent": "move",
    "entities": {
        "direction": "north"
    }
}

# Select appropriate tools
selected_tools = tool_selector.select_tools_for_intent(
    intent=parsed_input["intent"],
    entities=parsed_input["entities"],
    available_tools=all_tools
)

# Generate a response
messages = [
    {"role": "user", "content": player_input}
]

response = llm_with_tools.invoke(messages)

# Extract tool calls
tool_calls = response.tool_calls

# Execute the tool
if tool_calls:
    tool_call = tool_calls[0]
    tool = registry.get_tool(tool_call.name)
    
    result = tool_executor.execute_tool(
        tool=tool,
        args=tool_call.args,
        agent_state=game_state
    )
    
    # Update the game state
    updated_game_state = tool_executor.update_state_with_result(
        state=game_state,
        result=result
    )
    
    # Print the result
    print(f"Tool result: {result['result']}")
    print(f"Updated game state: {updated_game_state}")
```

## Related Documentation

- [Dynamic Tool System](../Architecture/Dynamic_Tool_System.md): Overview of the dynamic tool system
- [AI Agents](../Architecture/AI_Agents.md): Information about the AI agents that use tools
- [Knowledge Graph](../Architecture/Knowledge_Graph.md): Details about the knowledge graph that tools interact with
- [LangGraph Integration](../Integration/AI_Libraries_Integration_Plan.md#4-langgraph): Information about LangGraph integration
