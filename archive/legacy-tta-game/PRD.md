## TTA Project: AI Agent Design Specification (Technical Requirements)

This document outlines the technical specifications for the AI Agent design within the Therapeutic Text Adventure (TTA) project. It serves as a reference for the AI coding assistant and details the architecture, components, and interactions of the AI system.

**1. Core Technology Stack:**

*   **Language Model (LLM):**
    *   **Primary Model:** Qwen2.5 will serve as the foundational LLM for the majority of AI agent roles. Its capabilities in natural language understanding, text generation, and reasoning are central to agent functionality.
    *   **Dynamic Model Selection:** The architecture must support the dynamic selection of alternative LLMs (e.g., Google Gemini, Anthropic Claude) based on specific task requirements and resource availability . LangChain provides the abstraction layer for interacting with diverse LLMs through a unified interface .
*   **Agent Orchestration Framework:**
    *   **LangGraph:** This framework will be the core orchestration engine for managing AI agent workflows, state transitions, and interactions between both core and dynamically generated agents. LangGraph's node and edge structure allows for the definition of complex routing and conditional execution of agent roles.
*   **LLM Application Development Library:**
    *   **LangChain:** This library provides essential tools for building LLM-powered applications, including:
        *   **Prompt Management:** Facilitates the creation, management, and dynamic generation of prompts using prompt templates. This is crucial for defining agent roles and tasks.
        *   **Tool Integration:** Enables AI agents to interact with external functionalities (tools) such as querying the knowledge graph or performing specific actions. LangChain provides a standardized way to define and invoke these tools.
        *   **Multi-Model Support:** Offers a unified interface for interacting with different LLM providers, enabling dynamic model selection .
*   **Knowledge Graph:**
    *   **Neo4j:** This graph database will serve as the central repository for all persistent game world data, including concepts, relationships, lore, character information, and game state. AI agents will interact with Neo4j via designated tools, primarily using the Cypher query language.
*   **Data Validation and Structuring:**
    *   **Pydantic:** This Python library will be used extensively for data validation, serialization, and defining data schemas for AI agent inputs, outputs, and tool interactions. Pydantic ensures data integrity and facilitates reliable communication between system components.

**2. Core AI Agent Roles (Model-Powered via Qwen2.5):**

*   Core AI agents are conceptual roles or personas assumed by the underlying Qwen2.5 LLM, driven by context-specific prompts orchestrated by LangGraph. These roles are not separate software entities but rather modes of operation for the LLM.
*   **Examples of Core Agent Roles and Responsibilities (Technical Definition via Prompts):**
    *   **Input Processor Agent (IPA):** Tasked with parsing player input and identifying the player's intent and key entities. The prompt for IPA will define the expected output format (e.g., JSON) for the parsed intent and entities.
    *   **Narrative Generator Agent (NGA):** Responsible for generating descriptive text, dialogue, and narrative events based on the current game state, player actions, and character information. The prompt will guide the NGA to maintain a consistent and engaging narrative style.
    *   **Lore Keeper Agent (LKA):** Tasked with verifying the consistency of generated text or player actions with the existing game lore stored in the Neo4j knowledge graph. The prompt will instruct the LKA on how to query the knowledge graph and report any inconsistencies.
    *   **World Builder Agent (WBA):** Responsible for generating descriptions of game locations based on provided parameters. The prompt will specify the desired level of detail and the contextual information to consider.
    *   **Character Creator Agent (CCA):** Tasked with creating new non-player characters (NPCs) based on provided roles and context. The prompt will define the required attributes and personality traits for the NPC.
    *   **Tool Selection Agent (TSA):** Responsible for examining the current game state and determining the appropriate next steps in the workflow, potentially involving the use of specific tools. The prompt will provide the TSA with information about available tools and their functions.
*   **Tool Utilization by Core Agents (LangChain Integration):**
    *   Core agents will utilize a predefined set of modular and reusable tools to interact with the game world.
    *   LangChain's tool integration capabilities will be employed to define the interface and invocation methods for these tools.
    *   Prompts for core agents will explicitly list the available tools, their descriptions, and instructions on how to use them, including the expected input parameters (defined by Pydantic schemas) and output formats.
    *   Examples of tools include `query_knowledge_graph` (executes Cypher queries), `update_character_location` (modifies game state in Neo4j), and potentially external tools for web searching within specific universes.

**3. Dynamic AI Agent Generation:**

*   Dynamic agent generation allows the system to create specialized agent roles on-the-fly to handle nuanced tasks or emergent scenarios where predefined core roles are insufficient .
*   **Mechanisms for Dynamic Agent Generation (LangChain & LangGraph):**
    *   **Dynamic Prompt Generation (LangChain):** Based on the current game state, player input, or the output of other agents, LangChain's prompt generation capabilities will be used to create specialized prompts that instruct the LLM (Qwen2.5 or another selected model) to adopt a temporary, specific role .
    *   **Meta-Prompting:** A designated core agent (or a dynamically generated "Meta-Prompt Generator" agent) could be responsible for generating prompts for other agents based on high-level instructions and context. This leverages the LLM's understanding to create tailored instructions for specific sub-tasks.
    *   **LangGraph Workflow Instantiation:** LangGraph's architecture supports the dynamic creation of new nodes within a workflow, representing these dynamically generated agents. The routing and interaction of these temporary agents with core agents will be managed by LangGraph's flexible graph structure.
    *   **Tool Assignment to Dynamic Agents:** Dynamically generated agents can be equipped with specific tools relevant to their temporary role. Tool availability will be defined within the prompt or managed by LangGraph state.
*   **Examples of Dynamic Agent Use Cases:**
    *   **Specialized Content Generation:** For analyzing unique in-game artifacts, a "Property Analysis Agent" could be dynamically generated with access to a "Knowledge Graph Query Tool" and a "Text Summarization Tool" to generate a description of the artifact's properties .
    *   **Complex Negotiation Scenarios:** A "Negotiation Tactics Agent" could be temporarily instantiated to analyze NPC motivations and suggest dialogue strategies, potentially using tools to access character profiles from the knowledge graph .
    *   **Adaptive Problem Solving:** For novel puzzles, a "Puzzle Solving Agent" could be created, potentially equipped with a "Code Execution Tool" (if applicable) or a "Hypothesis Generation Tool," to assist the player.

**4. Model Selection for Dynamic Agents (LangChain Abstraction):**

*   The selection of the LLM for a dynamically generated agent can be determined based on the specific requirements of the task . LangChain's multi-model support simplifies this integration .
*   For tasks requiring extensive external knowledge retrieval (within specific universes like "Our Universe"), a model with strong web search capabilities (integrated via LangChain tools like Tavily Search) might be preferred.
*   For highly creative content generation, a model fine-tuned for creative writing could be dynamically selected (if available and integrated with LangChain) .
*   Qwen2.5 will remain a robust default option for most dynamic agent roles due to its balance of performance and local hosting capabilities.

**5. LangGraph Orchestration Requirements:**

*   LangGraph must manage the state of the game and the flow of information between different AI agents (both core and dynamic).
*   The orchestration logic will be defined through nodes representing agent roles and edges representing transitions between these roles, potentially with conditional logic based on the output of agents or the game state.
*   LangGraph will handle the invocation of agent prompts with the appropriate context from the game state and the passing of outputs between agents.
*   The framework must support the dynamic instantiation of new agent nodes within the workflow for dynamically generated agents.

**6. LangChain Integration Requirements:**

*   LangChain will be used for:
    *   Creating and managing prompt templates with placeholders for dynamic data from the game state.
    *   Dynamically generating prompts based on context and instructions.
    *   Defining and integrating tools that AI agents can use to interact with the knowledge graph (via Cypher), perform calculations, access external information, and modify the game state.
    *   Providing a common interface for interacting with different LLM providers to support dynamic model selection .

**7. Pydantic Data Handling Requirements:**

*   Pydantic models will be used to define the expected structure and data types for:
    *   Player input (after parsing by IPA).
    *   Game state representation within LangGraph.
    *   Input and output schemas for all tools used by AI agents.
    *   Output formats for AI agents (e.g., JSON for structured data).
    *   Definitions of concepts, metaconcepts, and other knowledge graph entities for validation purposes.
*   Pydantic will ensure data validation at the boundaries of different system components, preventing type errors and ensuring data consistency.

This technical specification provides a detailed overview of the AI Agent design for the TTA project, focusing on the core technologies, agent roles, dynamic generation mechanisms, model selection, and the roles of the orchestration framework and supporting libraries. This information should serve as a comprehensive reference for the AI coding assistant in the development process.