# AI Agents Example

This document provides practical examples of implementing and using AI agents in the TTA project using LangGraph.

## Basic Agent Structure

Here's a basic example of creating an agent using LangGraph:

```python
from typing import Dict, List, Any, TypedDict, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages

# Define the state type
class State(TypedDict):
    messages: Annotated[list, add_messages]

# Initialize the LLM
llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")

# Define the agent function
def agent(state: State):
    # Get the messages from the state
    messages = state["messages"]

    # Generate a response
    response = llm.invoke(messages)

    # Return the updated state
    return {"messages": [response]}

# Create the graph
graph_builder = StateGraph(State)
graph_builder.add_node("agent", agent)
graph_builder.add_edge(START, "agent")

# Compile the graph
graph = graph_builder.compile()

# Example usage
initial_state = {
    "messages": [
        {"role": "user", "content": "Hello, who are you?"}
    ]
}

# Run the graph
result = graph.invoke(initial_state)
```

## Input Processor Agent (IPA)

Here's an example of implementing the Input Processor Agent:

```python
from typing import Dict, List, Any, TypedDict, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages

# Define the state type
class State(TypedDict):
    messages: Annotated[list, add_messages]
    parsed_input: Dict[str, Any]

# Initialize the LLM
llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")

# Define the IPA prompt template
IPA_PROMPT = """
You are the Input Processor Agent (IPA) for a text adventure game.
Your task is to parse the player's input and identify their intent and any relevant entities.

Player input: {input}

Respond with a JSON object containing:
- intent: The player's intent (e.g., "move", "examine", "take", "talk_to", "quit", "unknown")
- entities: A dictionary of relevant entities (e.g., {"direction": "north", "object": "key", "character": "Elara"})

Example:
For input "go north", respond with:
{{"intent": "move", "entities": {{"direction": "north"}}}}

For input "examine the rusty key", respond with:
{{"intent": "examine", "entities": {{"object": "rusty key"}}}}
"""

# Define the IPA function
def input_processor_agent(state: State):
    # Get the latest user message
    user_message = state["messages"][-1]

    # Skip if not a user message
    if user_message.get("role") != "user":
        return {}

    # Format the prompt
    prompt = IPA_PROMPT.format(input=user_message.get("content", ""))

    # Generate a response
    response = llm.invoke([{"role": "user", "content": prompt}])

    # Extract the parsed input from the response
    # In a real implementation, you would use a more robust method to extract the JSON
    import json
    try:
        parsed_input = json.loads(response.content)
    except:
        # Fallback if JSON parsing fails
        parsed_input = {"intent": "unknown", "entities": {}}

    # Return the parsed input
    return {"parsed_input": parsed_input}

# Create the graph
graph_builder = StateGraph(State)
graph_builder.add_node("input_processor", input_processor_agent)
graph_builder.add_edge(START, "input_processor")

# Compile the graph
graph = graph_builder.compile()

# Example usage
initial_state = {
    "messages": [
        {"role": "user", "content": "go north and look for the treasure"}
    ],
    "parsed_input": {}
}

# Run the graph
result = graph.invoke(initial_state)
print(result["parsed_input"])
# Output: {"intent": "move", "entities": {"direction": "north", "object": "treasure"}}
```

## Narrative Generator Agent (NGA)

Here's an example of implementing the Narrative Generator Agent:

```python
from typing import Dict, List, Any, TypedDict, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages

# Define the state type
class State(TypedDict):
    messages: Annotated[list, add_messages]
    parsed_input: Dict[str, Any]
    game_state: Dict[str, Any]
    response: str

# Initialize the LLM
llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")

# Define the NGA prompt template
NGA_PROMPT = """
You are the Narrative Generator Agent (NGA) for a text adventure game.
Your task is to generate a response to the player's action, considering the current game state.

Player intent: {intent}
Player entities: {entities}
Current location: {location}
Nearby characters: {characters}
Visible objects: {objects}

Generate a descriptive and engaging response to the player's action.
Your response should be vivid, immersive, and reflect the game world.

Response:
"""

# Define the NGA function
def narrative_generator_agent(state: State):
    # Get the parsed input
    parsed_input = state.get("parsed_input", {})
    intent = parsed_input.get("intent", "unknown")
    entities = parsed_input.get("entities", {})

    # Get the game state
    game_state = state.get("game_state", {})
    location = game_state.get("current_location", "Unknown Location")
    characters = game_state.get("nearby_characters", [])
    objects = game_state.get("visible_objects", [])

    # Format the prompt
    prompt = NGA_PROMPT.format(
        intent=intent,
        entities=entities,
        location=location,
        characters=", ".join(characters) if characters else "None",
        objects=", ".join(objects) if objects else "None"
    )

    # Generate a response
    response = llm.invoke([{"role": "user", "content": prompt}])

    # Return the response
    return {"response": response.content}

# Create the graph
graph_builder = StateGraph(State)
graph_builder.add_node("narrative_generator", narrative_generator_agent)
graph_builder.add_edge(START, "narrative_generator")

# Compile the graph
graph = graph_builder.compile()

# Example usage
initial_state = {
    "messages": [
        {"role": "user", "content": "go north and look for the treasure"}
    ],
    "parsed_input": {"intent": "move", "entities": {"direction": "north", "object": "treasure"}},
    "game_state": {
        "current_location": "Forest Clearing",
        "nearby_characters": ["Old Hermit"],
        "visible_objects": ["Ancient Tree", "Moss-covered Rock"]
    },
    "response": ""
}

# Run the graph
result = graph.invoke(initial_state)
print(result["response"])
# Output: "You head north, leaving the Forest Clearing behind. As you walk, the trees grow denser, their ancient trunks towering above you. The Old Hermit watches you depart with curious eyes. You scan the area for any sign of treasure, but see only the natural wealth of the forest: vibrant mushrooms, colorful wildflowers, and the occasional glint of dew on spider webs. Perhaps the treasure lies further ahead, or perhaps it's hidden somewhere nearby, waiting to be discovered."
```

## World Builder Agent (WBA)

Here's an example of implementing the World Builder Agent:

```python
from typing import Dict, List, Any, TypedDict, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages

# Define the state type
class State(TypedDict):
    messages: Annotated[list, add_messages]
    game_state: Dict[str, Any]
    world_update: Dict[str, Any]

# Initialize the LLM
llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")

# Define the WBA prompt template
WBA_PROMPT = """
You are the World Builder Agent (WBA) for a text adventure game.
Your task is to create or update locations in the game world.

Current request: {request}
Location details (if updating): {location_details}
World context: {world_context}

Respond with a JSON object containing the location details:
{{
  "location_id": "unique_id",
  "name": "Location Name",
  "description": "Detailed description of the location",
  "type": "Location type (e.g., Forest, Cave, Village)",
  "atmosphere": "The mood or atmosphere of the location",
  "exits": {{
    "north": "connected_location_id_north",
    "south": "connected_location_id_south"
  }},
  "items": ["item_id_1", "item_id_2"],
  "characters": ["character_id_1", "character_id_2"],
  "hidden": false,
  "locked": false
}}
"""

# Define the WBA function
def world_builder_agent(state: State):
    # Get the request from the messages
    messages = state.get("messages", [])
    request = messages[-1].get("content", "") if messages else ""

    # Get the game state
    game_state = state.get("game_state", {})
    world_context = game_state.get("world_context", "A fantasy world with magic and adventure.")

    # Get location details if updating an existing location
    location_id = game_state.get("current_location_id")
    location_details = {}
    if location_id:
        # In a real implementation, this would query the knowledge graph
        location_details = {"location_id": location_id, "name": "Forest Clearing"}

    # Format the prompt
    prompt = WBA_PROMPT.format(
        request=request,
        location_details=location_details,
        world_context=world_context
    )

    # Generate a response
    response = llm.invoke([{"role": "user", "content": prompt}])

    # Extract the location details from the response
    # In a real implementation, you would use a more robust method to extract the JSON
    import json
    try:
        world_update = json.loads(response.content)
    except:
        # Fallback if JSON parsing fails
        world_update = {}

    # Return the world update
    return {"world_update": world_update}

# Create the graph
graph_builder = StateGraph(State)
graph_builder.add_node("world_builder", world_builder_agent)
graph_builder.add_edge(START, "world_builder")

# Compile the graph
graph = graph_builder.compile()

# Example usage
initial_state = {
    "messages": [
        {"role": "user", "content": "Create a new location: a mysterious cave entrance"}
    ],
    "game_state": {
        "world_context": "A fantasy world with ancient ruins and magical forests.",
        "current_location_id": "loc001"
    },
    "world_update": {}
}

# Run the graph
result = graph.invoke(initial_state)
print(result["world_update"])
# Output: {"location_id": "loc002", "name": "Mysterious Cave Entrance", "description": "A dark opening in the mountainside, partially hidden by hanging vines. Cool air flows from within, carrying a faint earthy scent. Ancient symbols are carved around the entrance, their meanings lost to time.", "type": "Cave", "atmosphere": "Mysterious and foreboding", "exits": {"south": "loc001", "north": "loc003"}, "items": ["item001"], "characters": [], "hidden": true, "locked": false}
```

## Complete Agent Workflow

Here's an example of a complete agent workflow that combines multiple agents:

```python
from typing import Dict, List, Any, TypedDict, Annotated, Literal
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages

# Define the state type
class State(TypedDict):
    messages: Annotated[list, add_messages]
    parsed_input: Dict[str, Any]
    game_state: Dict[str, Any]
    response: str
    current_agent: Literal["IPA", "NGA", "WBA", "CCA"]

# Initialize the LLM
llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")

# Define the agent functions (simplified versions)
def input_processor_agent(state: State):
    # Get the latest user message
    user_message = state["messages"][-1]

    # Skip if not a user message
    if user_message.get("role") != "user":
        return {}

    # Parse the input (simplified)
    content = user_message.get("content", "")

    if "go" in content or "move" in content:
        intent = "move"
        entities = {}
        for direction in ["north", "south", "east", "west"]:
            if direction in content:
                entities["direction"] = direction
                break
    elif "look" in content or "examine" in content:
        intent = "examine"
        entities = {}
    else:
        intent = "unknown"
        entities = {}

    # Return the parsed input
    return {
        "parsed_input": {"intent": intent, "entities": entities},
        "current_agent": "NGA"  # Next agent to run
    }

def narrative_generator_agent(state: State):
    # Get the parsed input
    parsed_input = state.get("parsed_input", {})
    intent = parsed_input.get("intent", "unknown")
    entities = parsed_input.get("entities", {})

    # Get the game state
    game_state = state.get("game_state", {})
    location = game_state.get("current_location", "Unknown Location")

    # Generate a response based on intent
    if intent == "move":
        direction = entities.get("direction", "somewhere")
        response = f"You move {direction} from {location}. You find yourself in a new area."

        # Update the game state
        new_location = f"{direction.capitalize()} of {location}"
        updated_game_state = {**game_state, "current_location": new_location}

        return {
            "response": response,
            "game_state": updated_game_state,
            "current_agent": "IPA"  # Back to IPA for next input
        }
    elif intent == "examine":
        response = f"You carefully examine your surroundings in {location}. You notice several interesting details."
        return {
            "response": response,
            "current_agent": "IPA"  # Back to IPA for next input
        }
    else:
        response = "I'm not sure what you want to do. Try moving in a direction or examining your surroundings."
        return {
            "response": response,
            "current_agent": "IPA"  # Back to IPA for next input
        }

def world_builder_agent(state: State):
    # This is a simplified version that doesn't do much
    return {"current_agent": "IPA"}

def character_creator_agent(state: State):
    # This is a simplified version that doesn't do much
    return {"current_agent": "IPA"}

# Define the router function
def router(state: State):
    current_agent = state.get("current_agent", "IPA")
    return current_agent

# Create the graph
graph_builder = StateGraph(State)

# Add nodes
graph_builder.add_node("IPA", input_processor_agent)
graph_builder.add_node("NGA", narrative_generator_agent)
graph_builder.add_node("WBA", world_builder_agent)
graph_builder.add_node("CCA", character_creator_agent)

# Add conditional edges based on the current_agent field
graph_builder.add_conditional_edges(
    "IPA",
    router,
    {
        "NGA": "NGA",
        "WBA": "WBA",
        "CCA": "CCA",
        "IPA": "IPA"  # Default case
    }
)

graph_builder.add_conditional_edges(
    "NGA",
    router,
    {
        "IPA": "IPA",
        "WBA": "WBA",
        "CCA": "CCA",
        "NGA": "NGA"  # Default case
    }
)

graph_builder.add_conditional_edges(
    "WBA",
    router,
    {
        "IPA": "IPA",
        "NGA": "NGA",
        "CCA": "CCA",
        "WBA": "WBA"  # Default case
    }
)

graph_builder.add_conditional_edges(
    "CCA",
    router,
    {
        "IPA": "IPA",
        "NGA": "NGA",
        "WBA": "WBA",
        "CCA": "CCA"  # Default case
    }
)

# Add the starting edge
graph_builder.add_edge(START, "IPA")

# Compile the graph
graph = graph_builder.compile()

# Example usage
initial_state = {
    "messages": [
        {"role": "user", "content": "go north"}
    ],
    "parsed_input": {},
    "game_state": {"current_location": "Forest Clearing"},
    "response": "",
    "current_agent": "IPA"
}

# Run the graph
result = graph.invoke(initial_state)
print(f"Final response: {result['response']}")
print(f"Final location: {result['game_state']['current_location']}")
# Output:
# Final response: You move north from Forest Clearing. You find yourself in a new area.
# Final location: North of Forest Clearing
```

## Related Documentation

- [AI Agents](../Architecture/AI_Agents.md): Detailed information about the AI agent roles
- [System Architecture](../Architecture/System_Architecture.md): Overview of the system architecture
- [Dynamic Tool System](../Architecture/Dynamic_Tool_System.md): Information about the tools used by agents
- [LangGraph Integration](../Integration/AI_Libraries_Integration_Plan.md#4-langgraph): Details about LangGraph integration
