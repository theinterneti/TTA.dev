# TTA Project Task List (v2.0)

This document outlines the specific tasks required to implement the TTA v2.0 architecture, broken down by the phases defined in `PLANNING.MD`.

## Phase 0: Foundation & Setup (Environment)

*   [ ] Initialize Git repository for the project.
*   [ ] Create the basic project directory structure (`src/`, `tests/`, `.devcontainer/`).
*   [ ] Create `Dockerfile` for the `app` service (using `python:3.11-slim-buster` or similar).
*   [ ] Create initial `requirements.txt` (e.g., `python-dotenv`).
*   [ ] Create initial `.env.example` file with placeholders for variables.
*   [ ] Create `.env` file (add to `.gitignore`) and populate with initial values (e.g., Neo4j credentials).
*   [ ] Create `docker-compose.yml` defining the `app` service (build from Dockerfile, mount `./:/app`, load `.env`).
*   [ ] Create `.devcontainer/devcontainer.json` specifying `docker-compose.yml`, the `app` service, workspace folder, and basic Python extensions.
*   [ ] Test: Build and run the `app` container using VS Code Remote - Containers.
*   [ ] Test: Create a simple `src/main.py` that prints "Hello" and run it from within the devcontainer.

## Phase 1: Core KG & Basic Interaction

*   [ ] Add `neo4j` service definition to `docker-compose.yml` (using `neo4j:5` image, ports, volumes, env vars from `.env`).
*   [ ] Update `.devcontainer/devcontainer.json` to forward Neo4j ports (7474, 7687) and potentially run the `neo4j` service automatically.
*   [ ] Add `neo4j` library to `requirements.txt` and rebuild devcontainer.
*   [ ] Implement `src/neo4j_manager.py`:
    *   [ ] Singleton/Class structure.
    *   [ ] Connection logic (`__init__`, `close`) using credentials from `.env`.
    *   [ ] Basic `query` method.
    *   [ ] Methods for schema setup (`_ensure_constraints`, etc. - start basic).
    *   [ ] Basic CRUD methods (e.g., `create_location`, `get_location_details`). Align with target schema.
*   [ ] Define core Pydantic models in `src/models.py` (e.g., `Item`, `Character`, `Location`). Align with target schema.
*   [ ] Implement basic KG tools in `src/kg_tools.py` (e.g., `get_node_properties` - wrapper around `neo4j_manager`).
*   [ ] Implement `src/llm_config.py` to load model IDs and parameters from `.env` (placeholders for now). Remove `settings.py`.
*   [ ] Create a *very* simple game loop in `src/main.py` (e.g., takes text input, maybe calls a basic KG tool).
*   [ ] Write basic unit tests in `tests/` for `neo4j_manager.py` and `models.py`.

## Phase 2: LangGraph & Agent Integration

*   [ ] Add `langchain`, `langgraph`, `transformers`, `torch` (or `torch-cpu`) to `requirements.txt` and rebuild.
*   [ ] Define `AgentState` (based on `models.py` and planning doc) in `src/langgraph_engine.py`.
*   [ ] Implement basic LangGraph workflow structure in `src/langgraph_engine.py` (`create_workflow`).
*   [ ] Implement `llm_config.py` helper functions (`get_tools_llm`, `get_narrative_llm`) to load and return configured LangChain LLM objects based on *local* Transformers models.
*   [ ] Implement basic agent nodes in `src/langgraph_engine.py`:
    *   [ ] `ipa_node` (can start rule-based or simple LLM call using Transformers LLM).
    *   [ ] `nga_node` (can start template-based or simple LLM call using Transformers LLM).
    *   [ ] Other agent nodes (LKA, WBA, CCA - placeholders or very basic implementations).
*   [ ] Implement `create_kg_tools` factory function in `kg_tools.py` and wrap KG functions as LangChain tools.
*   [ ] Integrate KG tools into the LangGraph workflow (e.g., using `ToolNode` or called directly from agent nodes).
*   [ ] Update `src/main.py` to initialize and run the LangGraph workflow.
*   [ ] Define core system prompts in `src/prompts.py`. Remove obsolete schemas.
*   [ ] Begin implementation of `src/agentic_rag.py` (focus on `AgentPlan`, `AgentAction`, `analyze_goal`, `formulate_plan`, `determine_next_action`).
*   [ ] Begin implementation of `src/agentic_rag_integration.py` to connect Agentic RAG logic to LangGraph nodes.
*   [ ] Write unit tests for `langgraph_engine.py`, `llm_config.py`, and `kg_tools.py`.

## Phase 3: Enhancements & Agentic RAG Refinement

*   [ ] Implement `src/embedding_service.py` (using local sentence-transformers or similar).
*   [ ] Implement `src/vector_store.py` using Neo4j's vector index capabilities.
    *   [ ] Add methods to create/query vector indexes on relevant nodes (e.g., :DynamicTool).
*   [ ] Implement `src/dynamic_tool_generator.py`:
    *   [ ] LLM-based tool generation function (`generate_tool`).
    *   [ ] Tool validation logic (`validate_tool`).
    *   [ ] Neo4j storage/retrieval (`store_tool_in_neo4j`, `get_tool_from_neo4j`).
    *   [ ] Integration with `vector_store.py` for finding similar examples (`_get_similar_tools`).
    *   [ ] Remove `src/dynamic_tool_schema.py` (integrate models into `models.py`).
*   [ ] (Optional) Implement `src/tool_composer.py` for composing tools.
*   [ ] Refine `src/agentic_rag.py` implementation:
    *   [ ] Implement `synthesize_information`, `generate_response`.
    *   [ ] Implement `validate_response` (optional).
    *   [ ] Implement the full `run_agentic_rag_cycle`.
*   [ ] Refine `src/agentic_rag_integration.py` for full cycle execution within LangGraph.
*   [ ] Implement `src/quest_manager.py` (Quest models, status tracking, progression logic).
*   [ ] (Optional) Implement `src/kg_schema_enhancer.py` for managing schema within Neo4j.
*   [ ] Write unit tests for embedding service, vector store, tool generator, agentic rag, quest manager.

## Phase 4: Therapeutic Focus & Polish

*   [ ] Implement predefined therapeutic tools in `src/therapeutic_tools.py`.
*   [ ] Integrate therapeutic tools into the ToolRegistry and make them available to agents/LangGraph.
*   [ ] Implement agent memory:
    *   [ ] Define `MemoryEntry` model (potentially in `models.py`).
    *   [ ] Implement `src/agent_memory.py` (storage in Neo4j, retrieval logic).
    *   [ ] Integrate memory retrieval/updates into agent nodes or Agentic RAG cycles.
*   [ ] Review and refine *all* system prompts (`prompts.py`) for clarity, effectiveness, and therapeutic tone.
*   [ ] Conduct thorough testing of game mechanics, agent behavior, and narrative flow.
*   [ ] Add docstrings and comments to code.
*   [ ] Code cleanup and refactoring.

## Phase 5: Optional Future Enhancements

*   [ ] Explore Observability: Integrate Prometheus & Grafana (add services to `docker-compose.yml`, instrument Python code).
*   [ ] Explore Advanced LLM Serving: Experiment with vLLM if performance issues arise.
*   [ ] Explore Asynchronous Tasks: Use Redis or RabbitMQ for background processing if needed.
*   [ ] Explore GUI: Consider PyGame or a web framework (Flask/FastAPI) for a graphical interface.

## Ongoing Tasks

*   [ ] Write unit tests for all new/modified modules.
*   [ ] Refactor code for clarity and efficiency.
*   [ ] Maintain documentation (README, code comments).
*   [ ] Regularly commit changes to Git.