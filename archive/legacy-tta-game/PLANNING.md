# Therapeutic Text Adventure (TTA) Project Planning

## 🎯 Project Goals

The Therapeutic Text Adventure (TTA) project aims to create an interactive text-based game that:

1. Provides therapeutic experiences through narrative and gameplay
2. Uses AI to generate personalized content and responses
3. Leverages a knowledge graph for complex game state management
4. Offers a flexible, extensible architecture for future enhancements

## 🏗️ Architecture

The TTA project has evolved through three architectural approaches:

### Current Architecture (v0.3): Dynamic Tools with LangGraph

1. **Player Input Processing**: 
   - Input Processing Agent (IPA) node processes natural language input
   - NLP processing with spaCy for initial parsing
   - Intent recognition and entity extraction

2. **Tool Execution**:
   - Dynamic tool selection based on player intent
   - Tool Executor node executes the appropriate tools
   - Tools interact with the knowledge graph to update game state

3. **Narrative Generation**:
   - Narrative Generator Agent (NGA) creates descriptive text
   - Emoji support for enhanced narrative
   - Personalized content based on player history and preferences

4. **Orchestration**:
   - LangGraph manages the flow between nodes
   - State management across interactions
   - Conditional branching based on game state

5. **Data Storage**:
   - Neo4j stores the game state as a knowledge graph
   - Locations, items, characters, and relationships
   - Player history and preferences

6. **Model Selection**:
   - Hybrid LLM configuration for different tasks
   - Task-specific model selection
   - Performance monitoring and optimization

## 🧩 Component Overview

### Core Components

1. **LLM Integration**:
   - `src/llm_client.py`: Client for LLM API communication
   - `src/llm_config_hybrid.py`: Hybrid LLM configuration
   - `src/model_manager.py`: Model loading and management

2. **Game Engine**:
   - `src/main_dynamic.py`: Main game loop with dynamic tools
   - `src/dynamic_game.py`: Game state management
   - `src/dynamic_langgraph.py`: LangGraph integration

3. **Knowledge Graph**:
   - `src/neo4j_manager.py`: Neo4j database integration
   - `src/kg_tools.py`: Knowledge graph utility functions
   - `src/kg_schema_enhancer.py`: Schema enhancement utilities

4. **Agent System**:
   - `src/dynamic_agents.py`: Dynamic agent creation and management
   - `src/agent_memory.py`: Agent memory and history tracking
   - `src/agentic_rag.py`: Retrieval-augmented generation for agents

5. **Tool System**:
   - `src/dynamic_tools.py`: Dynamic tool creation and execution
   - `src/tool_selector.py`: Tool selection based on intent
   - `src/tool_composer.py`: Tool composition for complex actions

6. **Content Generation**:
   - `src/prompts.py`: System prompts for AI agents
   - `src/therapeutic_tools.py`: Therapeutic content generation
   - `src/quest_manager.py`: Quest and narrative management

### AI Libraries Integration

1. **Transformers Integration**:
   - Model hosting and inference
   - Embeddings generation
   - Parameter control and optimization

2. **Guidance Integration**:
   - Template-based generation
   - Controlled narrative and dialogue
   - Therapeutic content generation

3. **Pydantic-AI Integration**:
   - Structured data generation
   - Type-safe outputs with validation
   - Integration with Neo4j data models

4. **LangGraph Integration**:
   - Workflow orchestration
   - State management
   - Tool selection and execution

5. **spaCy Integration**:
   - Text processing and tokenization
   - Entity extraction
   - Syntactic analysis

## 🎨 Style Guide

### Code Style

1. **Python Conventions**:
   - Follow PEP8 guidelines
   - Use type hints for all functions and methods
   - Format code with `black`
   - Maximum line length of 88 characters

2. **Documentation**:
   - Google-style docstrings for all functions and classes
   - Inline comments for complex logic
   - README.md for each module explaining its purpose

3. **Testing**:
   - Pytest for all unit tests
   - Test coverage for all new features
   - Integration tests for component interactions

### Naming Conventions

1. **Files and Modules**:
   - Snake case for file names (e.g., `dynamic_tools.py`)
   - Descriptive names that reflect purpose

2. **Classes**:
   - PascalCase for class names (e.g., `DynamicToolGenerator`)
   - Noun phrases that describe the entity

3. **Functions and Methods**:
   - Snake case for function names (e.g., `generate_tool`)
   - Verb phrases that describe the action

4. **Variables**:
   - Snake case for variable names (e.g., `tool_registry`)
   - Descriptive names that indicate purpose and type

5. **Constants**:
   - Uppercase with underscores (e.g., `MAX_TOKENS`)
   - Defined at module level

### File Structure

1. **Module Organization**:
   - Group related functionality in modules
   - Separate interface from implementation
   - Use relative imports within packages

2. **Directory Structure**:
   - `src/`: Source code
   - `tests/`: Test code
   - `Documentation/`: Documentation files
   - `examples/`: Example code and usage

## 🛠️ Development Workflow

1. **Task Management**:
   - Define tasks in `TASK.md`
   - Mark completed tasks
   - Add discovered tasks during development

2. **Development Process**:
   - Create unit tests before implementation
   - Implement features incrementally
   - Document as you go
   - Review code before submission

3. **Testing Strategy**:
   - Unit tests for individual components
   - Integration tests for component interactions
   - End-to-end tests for complete workflows
   - Performance tests for critical paths

4. **Documentation Strategy**:
   - Update documentation with code changes
   - Keep README.md current
   - Document design decisions and rationale

## 🚧 Constraints and Limitations

1. **Performance Constraints**:
   - LLM inference can be slow
   - Neo4j queries should be optimized
   - Minimize unnecessary LLM calls

2. **Resource Constraints**:
   - Models must be quantized for efficiency
   - Memory usage should be monitored
   - Consider resource availability for deployment

3. **Technical Constraints**:
   - Python 3.9+ required
   - Neo4j 4.4+ required
   - LLM API compatibility required

## 🔄 Integration Strategy

The integration strategy focuses on leveraging the strengths of each AI library while maintaining a cohesive system:

1. **Layer 1: Foundation Layer**
   - Transformers Model Manager
   - spaCy NLP Pipeline
   - Pydantic Data Models

2. **Layer 2: Generation Layer**
   - Guidance Generator
   - Pydantic-AI Generator
   - Hybrid Generation System

3. **Layer 3: Orchestration Layer**
   - LangGraph Workflows
   - Tool Registry
   - Agent Registry

4. **Layer 4: Integration Layer**
   - Unified API
   - Neo4j Integration
   - Performance Monitoring

## 📈 Roadmap

### Phase 1: Foundation Setup (Current)
- Implement Transformers Model Manager
- Enhance spaCy Pipeline
- Refine Pydantic Models

### Phase 2: Generation Layer
- Implement Guidance Integration
- Implement Pydantic-AI Integration
- Create Hybrid Generation System

### Phase 3: Orchestration Layer
- Implement LangGraph Workflows
- Enhance Tool Registry
- Implement Agent Registry

### Phase 4: Integration and Optimization
- Create Unified API
- Optimize Performance
- Add Testing and Documentation

## 🔍 Key Design Decisions

1. **Model Hosting Strategy**:
   - Use Transformers for direct model hosting
   - Eliminate external service dependency
   - Enable model quantization and optimization

2. **Generation Strategy**:
   - Use a hybrid approach for different generation tasks
   - Select appropriate generator based on task
   - Implement fallback mechanisms

3. **NLP Processing Strategy**:
   - Use spaCy for initial processing
   - Use Transformers for deeper analysis
   - Combine approaches for optimal results

4. **Workflow Management Strategy**:
   - Use LangGraph for orchestration
   - Implement state management
   - Support conditional branching
