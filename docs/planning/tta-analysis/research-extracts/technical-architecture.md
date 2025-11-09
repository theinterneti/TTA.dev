TTA Technical Architecture Export: Core Components
I. Architectural Philosophy: Model-Powered Interface
The TTA project utilizes a model-powered interface where the core intelligence, the Qwen2.5 Large Language Model (LLM), dynamically assumes different agent roles. This is a strategic shift from implementing specialized agents as separate software entities.
1. Unified Intelligence: Qwen2.5 provides Natural Language Understanding (NLU), text generation, reasoning, and tool use for all agent roles, eliminating the need for complex inter-agent communication protocols.
2. Dynamic Role-Switching: The LLM seamlessly switches between roles (e.g., Narrative Generator Agent (NGA), Lore Keeper Agent (LKA)) based on the current task and the context provided in the input prompt by LangGraph.
3. Consistency: Using a single foundational model ensures inherent consistency in language style, reasoning ability, and knowledge representation across all generated content.

--------------------------------------------------------------------------------
II. Core Technologies and Roles
Component
Role in TTA
Key Functionalities
Interactions
Qwen2.5 (LLM)
Core Intelligence/Universal Agent Engine
NLU, Text Generation, Reasoning, Tool Use (Function Calling via structured JSON).
Acts as the "worker" executing tasks directed by LangGraph.
LangGraph
Orchestrator / State Manager / Nervous System
Defines stateful workflows (state machines), manages Multi-Agent Coordination, Persistence, Streaming, and Conditional Logic.
Directs Qwen2.5 roles, provides context, and processes tool outputs.
Neo4j
Knowledge Graph / Persistent Memory
Stores interconnected game data (Concepts, Characters, Locations, Relationships). Provides structured context for AI agents.
Tools (defined by LangChain) execute Cypher queries against Neo4j.
LangChain
Tool/Framework Definition
Defines reusable tools (like query_knowledge_graph), manages Prompt Templates, and structures agent definitions.
Tools link Qwen2.5 to Neo4j and other external resources.
Pydantic
Data Validation and Structuring
Enforces data types and schemas for the AgentState model and for tool inputs/outputs (JSON).
Essential for ensuring data integrity and consistency between agents and the knowledge graph.

--------------------------------------------------------------------------------
III. Agent Orchestration: LangGraph Implementation Details
LangGraph defines the workflow as a state machine, managing the AgentState—a crucial, centralized, Pydantic-validated data structure that maintains context across agent invocations.
1. The AgentState Model (Pydantic)
The state is explicitly tracked and updated by each agent role. Key components include:
• current_agent: The ID of the role Qwen2.5 is currently assuming ("IPA", "NGA", "LKA").
• player_input / parsed_input: Raw player text and its structured representation after processing.
• game_state: Information about the world (e.g., current_location_id, world_state).
• conversation_history: List of previous interactions.
• metaconcepts: Active high-level principles guiding AI behavior.
• Persistence: The entire AgentState is persisted to Neo4j, enabling features like saving/loading and human-in-the-loop review.
2. Workflow Definition (Nodes and Edges)
Workflows are defined by StateGraph, connecting nodes that represent agent roles via edges that control the flow.
• Nodes (Agent Roles): Each node invokes Qwen2.5 with the appropriate role-specific prompt, context from the AgentState, and available tools.
• Conditional Edges: These transitions define the logic of the game. For example, the workflow transitions from the Input Processor Agent (IPA) node using conditional logic: If the IPA identifies the player's intent as a "question," the workflow transitions to the LKA node; if the intent is a "command," it transitions to the World Builder Agent (WBA) or NGA node.
3. Agent Roles and Responsibilities
Agent Role
Primary Responsibility
Key Tools Used
Interaction Pattern
IPA
Parses player input, identifies intent, initiates workflow.
parse_input, query_knowledge_graph.
Receives raw input; activates other agents.
NGA
Generates narrative text, dialogue, and manages story flow.
generate_text, get_character_profile, query_knowledge_graph.
Receives input from IPA; requests data from WBA/CCA; consults LKA.
WBA
Manages world data (locations, factions, events).
get_location_details, create_location, query_knowledge_graph.
Provides structured location data to the NGA.
LKA
Ensures lore consistency, validates generated content, manages the knowledge graph.
check_consistency, update_node, infer_relationship, query_knowledge_graph.
Constantly consulted by all other agents for validation and information retrieval.

--------------------------------------------------------------------------------
IV. Data Grounding: Agentic CoRAG and Tool Use
The effectiveness of the TTA architecture hinges on the AI agents' ability to interact with the external world and the Neo4j Knowledge Graph using tools and the specialized CoRAG technique.
1. Tool Use and Implementation (LangChain/Pydantic)
Tools are external functions that Qwen2.5 is trained to call via structured output (JSON).
• Design Principles: Tools must be modular, reusable, perform a single task, and be well-documented (the natural language description guides Qwen2.5 usage).
• Structured I/O: Pydantic models define the input (args_schema) and output structure for every tool, ensuring predictable data exchange.
• LangGraph's Role in Tools: When Qwen2.5 outputs a JSON object requesting a tool call (e.g., query_knowledge_graph), LangGraph intercepts this output, executes the corresponding Python function (the func), and then passes the result back to Qwen2.5 for the next reasoning step.
2. Chain-of-Retrieval Augmented Generation (CoRAG)
CoRAG is TTA's iterative retrieval and generation technique used by Qwen2.5 to enhance accuracy and relevance by grounding responses in the knowledge graph.
• Mechanism: Instead of a single query, Qwen2.5 dynamically generates Cypher sub-queries, retrieves small chunks of information from Neo4j, integrates the results, and then generates new sub-queries to refine its understanding—all within a single agent invocation (often involving loops managed by LangGraph).
• Example: When the LKA checks new narrative content for consistency, it might execute a series of tool calls: 1) Retrieve related concepts via Cypher. 2) Check for contradictions using a specialized check_consistency tool based on the retrieved data.
• Tool Output: The core retrieval tool is query_knowledge_graph, which takes a Cypher query string as input and returns a JSON string representing the results from Neo4j.
3. Knowledge Graph Structure (Neo4j/Cypher)
The Neo4j Knowledge Graph serves as the structured memory and context provider.
• Schema: The schema includes core node types such as Concept, Metaconcept, and Scope (Multiverse, Universe, World, Location).
• Metaconcept Integration: Metaconcepts (e.g., "Utilize Web Resources," "Ensure Conceptual Clarity") are stored as nodes and are included in the agent prompts to guide Qwen2.5's reasoning and adherence to design principles. The Metaconcept Utilize Web Resources specifically guides agents in accessing external information (potentially via tools like FireCrawl) for worlds based on 'Our Universe' or 'Alternate Earths'.
• Cypher Use: AI agents rely on Cypher for complex pattern matching and graph traversal, ensuring efficient retrieval of interconnected context. Best practices include parameterization, transaction use, and clear naming conventions.
