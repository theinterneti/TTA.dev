"""
Dynamic Game Loop for the TTA project.
This module provides a game loop that uses dynamically generated tools and agents.
"""

import logging
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def enhance_description_with_llm(description: str, llm_client=None) -> str:
    """
    Enhance a location description using the Narrative Generation Agent.

    Args:
        description: The base location description
        llm_client: The LLM client to use for generation

    Returns:
        An enhanced description
    """
    if not description:
        return "The details of this place are unclear."

    logger.info(f"Generating narrative for: '{description}'")

    # If no LLM client is provided, return the original description
    if not llm_client:
        logger.warning("No LLM client provided. Using base description.")
        return description

    user_prompt = f'Please narrate this scene based on the following description:\n"{description}"'

    try:
        narrative_text = llm_client.generate(
            prompt=user_prompt,
            system_prompt="You are a narrative generation agent for a text adventure game. Your task is to create vivid, immersive descriptions of locations, characters, and events. Focus on sensory details, atmosphere, and emotional tone. Be concise but evocative.",
            expect_json=False,
        )

        if not narrative_text:
            logger.warning("Failed to generate narrative. Using base description.")
            return description

        return narrative_text
    except Exception as e:
        logger.error(f"Error generating narrative: {e}")
        return description


class GameState:
    """
    Class to manage the game state.
    """

    def __init__(self, neo4j_manager=None, llm_client=None):
        """
        Initialize the game state.

        Args:
            neo4j_manager: Neo4j manager for knowledge graph operations
            llm_client: LLM client for text generation
        """
        self.neo4j_manager = neo4j_manager
        self.llm_client = llm_client
        self.current_location = "Forest Clearing"  # Default starting location
        self.inventory = []
        self.player_stats = {"health": 100, "energy": 100, "mood": "neutral"}
        self.game_flags = {}
        self.quest_log = []

    def get_location_description(self) -> str:
        """
        Get the description of the current location.

        Returns:
            The location description
        """
        if not self.neo4j_manager:
            return "You are in a mysterious place. The details are unclear without a connection to the knowledge graph."

        try:
            location_data = self.neo4j_manager.get_location_details(self.current_location)
            if location_data and "description" in location_data:
                return enhance_description_with_llm(location_data["description"], self.llm_client)
            else:
                return f"You are in {self.current_location}, but the details are unclear."
        except Exception as e:
            logger.error(f"Error getting location description: {e}")
            return f"You are in {self.current_location}, but something seems wrong with this place."

    def get_exits(self) -> list:
        """
        Get the available exits from the current location.

        Returns:
            List of available exits
        """
        if not self.neo4j_manager:
            return []

        try:
            return self.neo4j_manager.get_exits(self.current_location)
        except Exception as e:
            logger.error(f"Error getting exits: {e}")
            return []

    def get_items_at_location(self) -> list:
        """
        Get the items at the current location.

        Returns:
            List of items at the location
        """
        if not self.neo4j_manager:
            return []

        try:
            return self.neo4j_manager.get_items_at_location(self.current_location)
        except Exception as e:
            logger.error(f"Error getting items: {e}")
            return []

    def get_npcs_at_location(self) -> list:
        """
        Get the NPCs at the current location.

        Returns:
            List of NPCs at the location
        """
        if not self.neo4j_manager:
            return []

        try:
            return self.neo4j_manager.get_npcs_at_location(self.current_location)
        except Exception as e:
            logger.error(f"Error getting NPCs: {e}")
            return []

    def move_to_location(self, new_location: str) -> bool:
        """
        Move to a new location.

        Args:
            new_location: The name of the new location

        Returns:
            True if the move was successful, False otherwise
        """
        if not self.neo4j_manager:
            logger.warning("Cannot move without Neo4j manager")
            return False

        try:
            # Check if the new location exists and is connected to the current location
            exits = self.get_exits()
            valid_exit = False

            for exit_data in exits:
                if exit_data.get("target") == new_location:
                    valid_exit = True
                    break

            if valid_exit:
                self.current_location = new_location
                return True
            else:
                logger.warning(f"Cannot move to {new_location} from {self.current_location}")
                return False
        except Exception as e:
            logger.error(f"Error moving to location: {e}")
            return False

    def add_to_inventory(self, item_name: str) -> bool:
        """
        Add an item to the player's inventory.

        Args:
            item_name: The name of the item to add

        Returns:
            True if the item was added, False otherwise
        """
        if not self.neo4j_manager:
            logger.warning("Cannot add to inventory without Neo4j manager")
            return False

        try:
            # Check if the item exists at the current location
            items = self.get_items_at_location()
            item_exists = False
            item_data = None

            for item in items:
                if item.get("name") == item_name:
                    item_exists = True
                    item_data = item
                    break

            if item_exists and item_data:
                # Remove the item from the location
                self.neo4j_manager.remove_item_from_location(item_name, self.current_location)

                # Add the item to the player's inventory
                self.inventory.append(item_data)

                return True
            else:
                logger.warning(f"Item {item_name} not found at {self.current_location}")
                return False
        except Exception as e:
            logger.error(f"Error adding item to inventory: {e}")
            return False

    def get_inventory(self) -> list:
        """
        Get the player's inventory.

        Returns:
            List of items in the inventory
        """
        return self.inventory

    def update_player_stat(self, stat: str, value: Any) -> bool:
        """
        Update a player stat.

        Args:
            stat: The stat to update
            value: The new value

        Returns:
            True if the stat was updated, False otherwise
        """
        if stat in self.player_stats:
            self.player_stats[stat] = value
            return True
        else:
            logger.warning(f"Stat {stat} not found")
            return False

    def set_game_flag(self, flag: str, value: Any) -> None:
        """
        Set a game flag.

        Args:
            flag: The flag to set
            value: The value to set
        """
        self.game_flags[flag] = value

    def get_game_flag(self, flag: str, default: Any = None) -> Any:
        """
        Get a game flag.

        Args:
            flag: The flag to get
            default: The default value if the flag is not set

        Returns:
            The value of the flag, or the default value if not set
        """
        return self.game_flags.get(flag, default)

    def add_quest(self, quest: dict[str, Any]) -> None:
        """
        Add a quest to the quest log.

        Args:
            quest: The quest to add
        """
        self.quest_log.append(quest)

    def update_quest_status(self, quest_id: str, status: str) -> bool:
        """
        Update the status of a quest.

        Args:
            quest_id: The ID of the quest
            status: The new status

        Returns:
            True if the quest was updated, False otherwise
        """
        for quest in self.quest_log:
            if quest.get("id") == quest_id:
                quest["status"] = status
                return True

        logger.warning(f"Quest {quest_id} not found")
        return False

    def get_active_quests(self) -> list:
        """
        Get the active quests.

        Returns:
            List of active quests
        """
        return [quest for quest in self.quest_log if quest.get("status") == "active"]


def run_dynamic_game(neo4j_manager=None, llm_client=None, tool_registry=None, agent_registry=None):
    """
    Run the dynamic game loop.

    Args:
        neo4j_manager: Neo4j manager for knowledge graph operations
        llm_client: LLM client for text generation
        tool_registry: Registry of available tools
        agent_registry: Registry of available agents
    """
    print("\n=== Welcome to the Therapeutic Text Adventure ===\n")
    print("Type 'help' for a list of commands, or 'quit' to exit.")

    # Initialize game state
    game_state = GameState(neo4j_manager, llm_client)

    # Populate initial graph data if needed
    if neo4j_manager:
        print("Checking if graph needs to be populated...")
        try:
            initial_check = neo4j_manager.query("MATCH (n:Location) RETURN count(n) as count")
            if not initial_check or initial_check[0]["count"] == 0:
                print("No locations found. Populating initial graph data...")
                neo4j_manager.populate_initial_graph()
        except Exception as e:
            logger.error(f"Error checking graph: {e}")
            print("Error connecting to the knowledge graph. Some features may be limited.")

    # Display initial location
    location_description = game_state.get_location_description()
    print(f"\n{location_description}")

    # Show available exits
    exits = game_state.get_exits()
    if exits:
        exit_str = ", ".join([f"{exit.get('direction', 'unknown')}" for exit in exits])
        print(f"\nYou can go: {exit_str}")

    # Show items in the location
    items = game_state.get_items_at_location()
    if items:
        item_str = ", ".join([item.get("name", "unknown") for item in items])
        print(f"\nYou see: {item_str}")

    # Show NPCs in the location
    npcs = game_state.get_npcs_at_location()
    if npcs:
        npc_str = ", ".join([npc.get("name", "unknown") for npc in npcs])
        print(f"\nCharacters here: {npc_str}")

    # Main game loop
    running = True
    while running:
        # Get user input
        user_input = input("\n> ").strip()

        # Check for quit command
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Thank you for playing!")
            running = False
            continue

        # Check for help command
        if user_input.lower() in ["help", "h", "?"]:
            print("\nAvailable commands:")
            print("  look - Look around the current location")
            print("  go [direction] - Move in a direction (north, south, east, west)")
            print("  examine [item] - Examine an item")
            print("  take [item] - Take an item")
            print("  inventory - Check your inventory")
            print("  talk to [character] - Talk to a character")
            print("  quit - Exit the game")
            continue

        # Process user input
        if tool_registry and agent_registry:
            try:
                # Use the tool registry and agent registry to process the input
                result = process_user_input(
                    user_input,
                    tool_registry,
                    agent_registry,
                    neo4j_manager,
                    game_state.current_location,
                )

                # Handle the result
                if isinstance(result, dict):
                    # Check for success
                    if result.get("success", False):
                        # Check for new location
                        if "new_location" in result:
                            # Update the game state
                            if game_state.move_to_location(result["new_location"]):
                                # Print the message
                                print(f"\n{result.get('message', '')}")

                                # Get and print the new location description
                                location_description = game_state.get_location_description()
                                print(f"\n{location_description}")

                                # Show available exits
                                exits = game_state.get_exits()
                                if exits:
                                    exit_str = ", ".join(
                                        [f"{exit.get('direction', 'unknown')}" for exit in exits]
                                    )
                                    print(f"\nYou can go: {exit_str}")

                                # Show items in the location
                                items = game_state.get_items_at_location()
                                if items:
                                    item_str = ", ".join(
                                        [item.get("name", "unknown") for item in items]
                                    )
                                    print(f"\nYou see: {item_str}")

                                # Show NPCs in the location
                                npcs = game_state.get_npcs_at_location()
                                if npcs:
                                    npc_str = ", ".join(
                                        [npc.get("name", "unknown") for npc in npcs]
                                    )
                                    print(f"\nCharacters here: {npc_str}")
                            else:
                                print(f"\nCannot move to {result['new_location']}.")
                        else:
                            # Print the message
                            print(f"\n{result.get('message', '')}")
                    else:
                        # Print error message
                        print(f"\n{result.get('message', 'Something went wrong.')}")
                else:
                    # Print the result as a string
                    print(f"\n{result}")
            except Exception as e:
                logger.error(f"Error processing input: {e}")
                print("\nI'm not sure how to do that.")
        else:
            # Simple command processing without tool registry
            if user_input.lower() == "look":
                location_description = game_state.get_location_description()
                print(f"\n{location_description}")

                # Show available exits
                exits = game_state.get_exits()
                if exits:
                    exit_str = ", ".join([f"{exit.get('direction', 'unknown')}" for exit in exits])
                    print(f"\nYou can go: {exit_str}")

                # Show items in the location
                items = game_state.get_items_at_location()
                if items:
                    item_str = ", ".join([item.get("name", "unknown") for item in items])
                    print(f"\nYou see: {item_str}")

                # Show NPCs in the location
                npcs = game_state.get_npcs_at_location()
                if npcs:
                    npc_str = ", ".join([npc.get("name", "unknown") for npc in npcs])
                    print(f"\nCharacters here: {npc_str}")
            elif user_input.lower().startswith("go "):
                direction = user_input[3:].strip().lower()
                exits = game_state.get_exits()
                valid_exit = False
                target_location = None

                for exit_data in exits:
                    if exit_data.get("direction", "").lower() == direction:
                        valid_exit = True
                        target_location = exit_data.get("target")
                        break

                if valid_exit and target_location:
                    if game_state.move_to_location(target_location):
                        print(f"\nYou go {direction}.")

                        # Get and print the new location description
                        location_description = game_state.get_location_description()
                        print(f"\n{location_description}")

                        # Show available exits
                        exits = game_state.get_exits()
                        if exits:
                            exit_str = ", ".join(
                                [f"{exit.get('direction', 'unknown')}" for exit in exits]
                            )
                            print(f"\nYou can go: {exit_str}")

                        # Show items in the location
                        items = game_state.get_items_at_location()
                        if items:
                            item_str = ", ".join([item.get("name", "unknown") for item in items])
                            print(f"\nYou see: {item_str}")

                        # Show NPCs in the location
                        npcs = game_state.get_npcs_at_location()
                        if npcs:
                            npc_str = ", ".join([npc.get("name", "unknown") for npc in npcs])
                            print(f"\nCharacters here: {npc_str}")
                    else:
                        print(f"\nCannot go {direction}.")
                else:
                    print(f"\nYou can't go {direction} from here.")
            elif user_input.lower() == "inventory":
                inventory = game_state.get_inventory()
                if inventory:
                    item_str = ", ".join([item.get("name", "unknown") for item in inventory])
                    print(f"\nYou are carrying: {item_str}")
                else:
                    print("\nYour inventory is empty.")
            elif user_input.lower().startswith("take "):
                item_name = user_input[5:].strip()
                if game_state.add_to_inventory(item_name):
                    print(f"\nYou take the {item_name}.")
                else:
                    print(f"\nYou can't take the {item_name}.")
            elif user_input.lower().startswith("examine "):
                item_name = user_input[8:].strip()
                # Check inventory
                inventory = game_state.get_inventory()
                item_found = False

                for item in inventory:
                    if item.get("name", "").lower() == item_name.lower():
                        item_found = True
                        print(f"\n{item.get('description', f'A {item_name}.')}")
                        break

                if not item_found:
                    # Check location
                    items = game_state.get_items_at_location()
                    for item in items:
                        if item.get("name", "").lower() == item_name.lower():
                            item_found = True
                            print(f"\n{item.get('description', f'A {item_name}.')}")
                            break

                if not item_found:
                    print(f"\nYou don't see a {item_name} here.")
            else:
                print("\nI'm not sure how to do that.")

    # Close Neo4j connection if it exists
    if neo4j_manager:
        try:
            neo4j_manager.close()
        except Exception as e:
            logger.error(f"Error closing Neo4j connection: {e}")


if __name__ == "__main__":
    run_dynamic_game()
