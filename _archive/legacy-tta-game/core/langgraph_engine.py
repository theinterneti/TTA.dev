"""
LangGraph Engine for Therapeutic Text Adventure (TTA)
This module implements the core LangGraph architecture for the TTA project.
"""

import json
import logging
from typing import Any

try:
    from pydantic import BaseModel, Field
except ImportError:
    # Fallback for environments without pydantic
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    def Field(*args, **kwargs):
        return None


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- LangGraph State Models ---


class CharacterState(BaseModel):
    """Represents the dynamic state of a character in the game."""

    character_id: str = Field(..., description="Character ID consistent with KG")
    name: str = Field(..., description="Character name")
    location_id: str = Field(..., description="Current location node ID")
    health: int = Field(100, description="Character health")
    mood: str = Field("neutral", description="Character mood")
    relationship_scores: dict[str, float] = Field(
        default_factory=dict, description="Relationship scores with other characters"
    )


class GameState(BaseModel):
    """Represents the current state of the game world."""

    current_location_id: str = Field(..., description="Current location node ID")
    current_location_name: str = Field(..., description="Current location name")
    nearby_character_ids: list[str] = Field(
        default_factory=list, description="List of character IDs in current location"
    )
    nearby_item_ids: list[str] = Field(
        default_factory=list, description="List of item IDs in current location"
    )
    world_state: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters like time, weather, active world/universe rules",
    )
    player_id: str = Field("player", description="ID of the player character")
    turn_count: int = Field(0, description="Number of turns taken in the game")


class AgentState(BaseModel):
    """Represents the complete state managed by LangGraph."""

    # Core workflow state
    current_agent: str = Field("ipa", description="ID of the current agent role/task node")
    player_input: str | None = Field(None, description="Raw player input for the current turn")
    parsed_input: dict[str, Any] | None = Field(None, description="Structured output from IPA role")
    response: str = Field(
        "", description="Final narrative response generated for the player this turn"
    )

    # Game context
    game_state: GameState = Field(..., description="Snapshot of the overall game world state")
    character_states: dict[str, CharacterState] = Field(
        default_factory=dict, description="Dynamic states of relevant characters"
    )
    player_inventory_ids: list[str] = Field(
        default_factory=list,
        description="List of item IDs currently held by the player",
    )

    # Agent execution context
    conversation_history: list[dict[str, str]] = Field(
        default_factory=list, description="History of recent turns"
    )
    active_metaconcepts: list[str] = Field(
        default_factory=list,
        description="Names of metaconcepts currently influencing agent behavior",
    )
    agent_memory: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Working memory for the current agent execution chain",
    )

    # Tool interaction tracking
    last_tool_call: dict[str, Any] | None = Field(
        None, description="Details of the last tool called"
    )
    last_tool_result: Any | None = Field(None, description="Result from the last tool call")

    # Quest tracking
    active_quests: list[dict[str, Any]] = Field(
        default_factory=list, description="List of active quests"
    )
    completed_quests: list[dict[str, Any]] = Field(
        default_factory=list, description="List of completed quests"
    )


# --- LangChain Tools ---


class QueryKnowledgeGraphInput(BaseModel):
    """Input schema for the query_knowledge_graph tool."""

    query: str = Field(..., description="Cypher query to execute")


class QueryKnowledgeGraphOutput(BaseModel):
    """Output schema for the query_knowledge_graph tool."""

    results: list[dict[str, Any]] = Field(..., description="Query results")
    success: bool = Field(..., description="Whether the query was successful")
    message: str = Field("", description="Error message if query failed")


class GetNodePropertiesInput(BaseModel):
    """Input schema for the get_node_properties tool."""

    node_id: str | int = Field(..., description="ID of the node")
    node_type: str = Field(..., description="Type of the node (e.g., Character, Location)")
    properties: list[str] | None = Field(
        None, description="List of properties to retrieve (None for all)"
    )


class GetNodePropertiesOutput(BaseModel):
    """Output schema for the get_node_properties tool."""

    data: dict[str, Any] = Field(..., description="Node properties")
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field("", description="Error message if operation failed")


class CreateGameObjectInput(BaseModel):
    """Input schema for the create_game_object tool."""

    object_type: str = Field(
        ..., description="Type of object to create (Item, Character, Location)"
    )
    name: str = Field(..., description="Name of the object")
    description: str = Field(..., description="Description of the object")
    location_name: str | None = Field(
        None, description="Location to place the object (if applicable)"
    )
    properties: dict[str, Any] | None = Field(
        None, description="Additional properties for the object"
    )


class CreateGameObjectOutput(BaseModel):
    """Output schema for the create_game_object tool."""

    object_data: dict[str, Any] = Field(..., description="Created object data")
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field("", description="Error message if operation failed")


def query_knowledge_graph(
    neo4j_manager, input_data: QueryKnowledgeGraphInput
) -> QueryKnowledgeGraphOutput:
    """
    Execute a read-only Cypher query against the Neo4j knowledge graph.

    Args:
        neo4j_manager: Neo4j manager instance
        input_data: Query input data

    Returns:
        Query results
    """
    try:
        # Execute the query
        results = neo4j_manager.query(input_data.query)

        # Return the results
        return QueryKnowledgeGraphOutput(
            results=results if results else [],
            success=True,
            message="Query executed successfully",
        )
    except Exception as e:
        # Return error
        logger.error(f"Error executing query: {e}")
        return QueryKnowledgeGraphOutput(
            results=[], success=False, message=f"Error executing query: {str(e)}"
        )


def get_node_properties(
    neo4j_manager, input_data: GetNodePropertiesInput
) -> GetNodePropertiesOutput:
    """
    Retrieve properties for a specific node.

    Args:
        neo4j_manager: Neo4j manager instance
        input_data: Input data

    Returns:
        Node properties
    """
    try:
        # Build the query based on node type and ID
        id_field = (
            f"{input_data.node_type.lower()}_id" if input_data.node_type != "Location" else "name"
        )

        # Determine which properties to return
        prop_selection = (
            "*"
            if not input_data.properties
            else ", ".join([f"n.{prop} AS {prop}" for prop in input_data.properties])
        )

        # Execute the query
        query = f"MATCH (n:{input_data.node_type} {{{id_field}: $id}}) RETURN {prop_selection}"
        results = neo4j_manager.query(query, {"id": input_data.node_id})

        if not results:
            return GetNodePropertiesOutput(
                data={},
                success=False,
                message=f"No {input_data.node_type} found with ID {input_data.node_id}",
            )

        # Return the properties
        return GetNodePropertiesOutput(
            data=results[0],
            success=True,
            message=f"Retrieved properties for {input_data.node_type} with ID {input_data.node_id}",
        )
    except Exception as e:
        # Return error
        logger.error(f"Error retrieving properties: {e}")
        return GetNodePropertiesOutput(
            data={}, success=False, message=f"Error retrieving properties: {str(e)}"
        )


def create_game_object(neo4j_manager, input_data: CreateGameObjectInput) -> CreateGameObjectOutput:
    """
    Create a new game object (Item, Character, Location) and save it to Neo4j.

    Args:
        neo4j_manager: Neo4j manager instance
        input_data: Input data for object creation

    Returns:
        Created object data
    """
    try:
        object_type = input_data.object_type
        name = input_data.name
        description = input_data.description
        location_name = input_data.location_name
        properties = input_data.properties or {}

        # Create the object based on its type
        if object_type.lower() == "item":
            # Create an item
            if hasattr(neo4j_manager, "create_item"):
                neo4j_manager.create_item(name, description, location_name)

            # Add additional properties if provided
            if properties:
                props_query = "MATCH (i:Item {name: $name}) SET "
                props_query += ", ".join([f"i.{key} = ${key}" for key in properties.keys()])
                neo4j_manager.query(props_query, {"name": name, **properties})

            return CreateGameObjectOutput(
                object_data={
                    "type": "Item",
                    "name": name,
                    "description": description,
                    **properties,
                },
                success=True,
                message=f"Item '{name}' created successfully",
            )

        elif object_type.lower() == "character":
            # Create a character
            if hasattr(neo4j_manager, "create_character"):
                neo4j_manager.create_character(name, description, location_name)

            # Add additional properties if provided
            if properties:
                props_query = "MATCH (c:Character {name: $name}) SET "
                props_query += ", ".join([f"c.{key} = ${key}" for key in properties.keys()])
                neo4j_manager.query(props_query, {"name": name, **properties})

            return CreateGameObjectOutput(
                object_data={
                    "type": "Character",
                    "name": name,
                    "description": description,
                    **properties,
                },
                success=True,
                message=f"Character '{name}' created successfully",
            )

        elif object_type.lower() == "location":
            # Create a location
            query = """
            MERGE (l:Location {name: $name})
            ON CREATE SET l.description = $description
            """
            neo4j_manager.query(query, {"name": name, "description": description})

            # Add additional properties if provided
            if properties:
                props_query = "MATCH (l:Location {name: $name}) SET "
                props_query += ", ".join([f"l.{key} = ${key}" for key in properties.keys()])
                neo4j_manager.query(props_query, {"name": name, **properties})

            return CreateGameObjectOutput(
                object_data={
                    "type": "Location",
                    "name": name,
                    "description": description,
                    **properties,
                },
                success=True,
                message=f"Location '{name}' created successfully",
            )

        else:
            # Unsupported object type
            return CreateGameObjectOutput(
                object_data={},
                success=False,
                message=f"Unsupported object type: {object_type}",
            )

    except Exception as e:
        # Return error
        logger.error(f"Error creating {input_data.object_type}: {e}")
        return CreateGameObjectOutput(
            object_data={},
            success=False,
            message=f"Error creating {input_data.object_type}: {str(e)}",
        )


# --- LangGraph Agent Nodes ---

# Cache for IPA responses to avoid repeated LLM calls for common inputs
IPA_CACHE = {}


def parse_input_rule_based(player_input: str) -> dict[str, Any]:
    """
    Parse player input using rule-based methods.

    Args:
        player_input: Player input string

    Returns:
        Parsed input dictionary
    """
    # Default values
    intent = "unknown"
    direction = None
    item_name = None
    character_name = None
    object_type = None
    object_name = None
    object_description = None

    # Convert to lowercase for easier matching
    player_input = player_input.lower().strip()

    # Basic commands
    if player_input in ["look", "look around", "l"]:
        intent = "look"
    elif player_input in ["inventory", "inv", "i"]:
        intent = "inventory"
    elif player_input in ["quit", "exit", "q"]:
        intent = "quit"

    # Movement commands
    elif player_input in ["north", "n", "go north"]:
        intent = "move"
        direction = "north"
    elif player_input in ["south", "s", "go south"]:
        intent = "move"
        direction = "south"
    elif player_input in ["east", "e", "go east"]:
        intent = "move"
        direction = "east"
    elif player_input in ["west", "w", "go west"]:
        intent = "move"
        direction = "west"

    # Item interaction
    elif player_input.startswith("take ") or player_input.startswith("get "):
        intent = "take"
        if player_input.startswith("take "):
            item_name = player_input[5:]
        else:  # get
            item_name = player_input[4:]
    elif player_input.startswith("examine ") or player_input.startswith("look at "):
        intent = "examine"
        if player_input.startswith("examine "):
            item_name = player_input[8:]
        else:  # look at
            item_name = player_input[8:]

    # Character interaction
    elif player_input.startswith("talk to ") or player_input.startswith("talk with "):
        intent = "talk"
        if player_input.startswith("talk to "):
            character_name = player_input[8:]
        else:  # talk with
            character_name = player_input[10:]

    # Return the parsed input
    return {
        "intent": intent,
        "direction": direction,
        "item_name": item_name,
        "character_name": character_name,
        "object_type": object_type,
        "object_name": object_name,
        "object_description": object_description,
        "original_input": player_input,
    }


def ipa_node(state: AgentState) -> AgentState:
    """
    Input Processing Agent (IPA) node.
    Parses player input into structured intent and entities.

    Args:
        state: Current agent state

    Returns:
        Updated agent state with parsed input
    """
    # Check cache first for common commands
    player_input = state.player_input.lower().strip() if state.player_input else ""

    # Try to use the cache for common commands
    if player_input in IPA_CACHE:
        logger.info(f"Using cached response for: {player_input}")
        state.parsed_input = IPA_CACHE[player_input]

        # Add to agent memory
        state.agent_memory.append(
            {
                "agent": "ipa",
                "action": "parse_input_cached",
                "input": state.player_input,
                "output": state.parsed_input,
            }
        )

        return state

    # Use rule-based parsing
    parsed_result = parse_input_rule_based(player_input)
    state.parsed_input = parsed_result
    logger.info(f"Rule-based parsed intent: {parsed_result.get('intent')}")

    # Cache the result for future use
    IPA_CACHE[player_input] = parsed_result

    # Add to agent memory
    state.agent_memory.append(
        {
            "agent": "ipa",
            "action": "parse_input_rule_based",
            "input": state.player_input,
            "output": parsed_result,
        }
    )

    return state


# Cache for NGA responses to avoid repeated LLM calls for similar contexts
NGA_CACHE = {}


def nga_node(state: AgentState) -> AgentState:
    """
    Narrative Generator Agent (NGA) node.
    Generates narrative text based on the current game state and player action.

    Args:
        state: Current agent state

    Returns:
        Updated agent state with generated narrative
    """
    # Prepare context data
    context_type = "unknown"
    context_data = {}

    # Determine context type based on intent
    if state.parsed_input:
        intent = state.parsed_input.get("intent", "unknown")

        if intent == "look":
            context_type = "location_look"
            context_data = {
                "name": state.game_state.current_location_name,
                "items": state.game_state.nearby_item_ids,
                "characters": state.game_state.nearby_character_ids,
            }
        elif intent == "move":
            context_type = "action_result"
            context_data = {
                "action": "move",
                "success": True,  # Assume success for now
                "direction": state.parsed_input.get("direction", "unknown"),
                "destination": state.game_state.current_location_name,
            }
        elif intent == "inventory":
            context_type = "action_result"
            context_data = {"action": "inventory", "items": state.player_inventory_ids}
        elif intent == "take":
            context_type = "action_result"
            context_data = {
                "action": "take",
                "success": True,  # Assume success for now
                "item_name": state.parsed_input.get("item_name", "unknown"),
            }
        elif intent == "examine":
            context_type = "action_result"
            context_data = {
                "action": "examine",
                "success": True,  # Assume success for now
                "item_name": state.parsed_input.get("item_name", "unknown"),
            }
        elif intent == "talk":
            context_type = "action_result"
            context_data = {
                "action": "talk",
                "success": True,  # Assume success for now
                "character_name": state.parsed_input.get("character_name", "unknown"),
            }
        elif intent == "quit":
            context_type = "action_result"
            context_data = {"action": "quit", "message": "Goodbye!"}
        else:
            context_type = "error_message"
            context_data = {"message": "I don't understand that command."}

    # Create a cache key based on context type and data
    cache_key = f"{context_type}:{json.dumps(context_data, sort_keys=True)}"

    # Check if we have a cached response
    if cache_key in NGA_CACHE:
        logger.info(f"Using cached narrative for: {intent}")
        state.response = NGA_CACHE[cache_key]

        # Add to agent memory
        state.agent_memory.append(
            {
                "agent": "nga",
                "action": "generate_narrative_cached",
                "context_type": context_type,
                "context_data": context_data,
                "output": state.response,
            }
        )

        return state

    # Generate a simple narrative based on the context
    narrative = generate_fallback_narrative(context_type, context_data)
    state.response = narrative

    # Cache the result
    NGA_CACHE[cache_key] = narrative

    # Add to agent memory
    state.agent_memory.append(
        {
            "agent": "nga",
            "action": "generate_narrative_template",
            "context_type": context_type,
            "context_data": context_data,
            "output": narrative,
        }
    )

    return state


def generate_fallback_narrative(context_type: str, data: dict[str, Any]) -> str:
    """
    Generate a fallback narrative when the LLM fails.

    Args:
        context_type: Type of context
        data: Context data

    Returns:
        Generated narrative
    """
    try:
        if context_type == "location_look":
            name = data.get("name", "Unknown Location")
            items = data.get("items", [])
            characters = data.get("characters", [])

            # Build the description
            result = f"You are at {name}.\n"

            # Add items
            if items and len(items) > 0:
                result += "\nYou see: \n"
                for item in items:
                    result += f"- {item}\n"

            # Add characters
            if characters and len(characters) > 0:
                result += "\nPresent here: \n"
                for char in characters:
                    result += f"- {char}\n"

            return result

        elif context_type == "action_result":
            action = data.get("action", "unknown")
            success = data.get("success", False)
            message = data.get("message", "")

            if action == "move":
                direction = data.get("direction", "somewhere")
                destination = data.get("destination", "a new location")
                if success:
                    return f"You move {direction} to {destination}."
                else:
                    return f"You can't go {direction}. {message}"
            elif action == "take":
                item_name = data.get("item_name", "the item")
                if success:
                    return f"You pick up {item_name}."
                else:
                    return f"You can't take {item_name}. {message}"
            elif action == "examine":
                item_name = data.get("item_name", "the item")
                if success:
                    return f"You examine {item_name}. {message}"
                else:
                    return f"You don't see {item_name} here. {message}"
            elif action == "talk":
                character_name = data.get("character_name", "someone")
                if success:
                    return f"You talk to {character_name}. {message}"
                else:
                    return f"There's no one by that name here. {message}"
            elif action == "inventory":
                items = data.get("items", [])
                if items and len(items) > 0:
                    result = "You are carrying:\n"
                    for item in items:
                        result += f"- {item}\n"
                    return result
                else:
                    return "Your inventory is empty."
            elif action == "quit":
                return "Goodbye! Thanks for playing."
            else:
                return f"Action result: {message}"

        elif context_type == "error_message":
            message = data.get("message", "Something went wrong.")
            return f"Error: {message}"

        # Default fallback for unknown context types
        return "You continue your adventure."
    except Exception as e:
        # Extra safety fallback
        logger.error(f"Error in fallback narrative generation: {e}")
        logger.error(f"Context type: {context_type}")
        logger.error(f"Data: {data}")

        # Return a very basic response
        if context_type == "location_look":
            return "You look around the area."
        elif context_type == "action_result":
            action = data.get("action", "unknown")
            if action == "move":
                return "You move to a new location."
            elif action == "inventory":
                return "You check your inventory."
            elif action == "take":
                return "You try to take something."
            elif action == "examine":
                return "You examine something."
            elif action == "talk":
                return "You try to talk to someone."
            elif action == "quit":
                return "Thanks for playing! Goodbye."

        return "You continue your adventure."


def router(state: AgentState) -> str:
    """
    Route to the next node based on the current state.

    Args:
        state: Current agent state

    Returns:
        Name of the next node
    """
    # If we don't have parsed input yet, go to IPA
    if not state.parsed_input:
        return "ipa"

    # If we have parsed input but no response, go to NGA
    if state.parsed_input and not state.response:
        return "nga"

    # If we have a response, we're done
    return "END"


# --- LangGraph Workflow ---


def create_workflow(neo4j_manager) -> tuple:
    """
    Create a simple workflow for processing player input.

    Args:
        neo4j_manager: Neo4j manager instance

    Returns:
        Tuple of (workflow function, tools dictionary)
    """

    # Create a simple workflow function
    def workflow(player_input: str, current_location_name: str):
        # Initialize the agent state
        game_state = GameState(
            current_location_id=current_location_name,
            current_location_name=current_location_name,
            nearby_character_ids=[],
            nearby_item_ids=[],
        )

        # Create player character state
        player_state = CharacterState(
            character_id="player",
            name="Player",
            location_id=current_location_name,
            health=100,
            mood="neutral",
        )

        # Create agent state
        agent_state = AgentState(
            player_input=player_input,
            game_state=game_state,
            character_states={"player": player_state},
            player_inventory_ids=[],
        )

        # Process the input
        agent_state = ipa_node(agent_state)
        agent_state = nga_node(agent_state)

        return agent_state

    # Create the tools
    tools = {
        "query_knowledge_graph": lambda input_data: query_knowledge_graph(
            neo4j_manager, input_data
        ),
        "get_node_properties": lambda input_data: get_node_properties(neo4j_manager, input_data),
        "create_game_object": lambda input_data: create_game_object(neo4j_manager, input_data),
    }

    return workflow, tools
