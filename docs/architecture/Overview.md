# TTA Architecture Overview

This document provides an overview of the Therapeutic Text Adventure (TTA) architecture.

## System Architecture

The TTA project is built with a modular architecture that separates concerns and allows for easy extension. The main components are:

```
┌─────────────────────────────────────────────────────────────────┐
│                           TTA System                            │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                           Game Engine                           │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤
│  Game Loop  │  Game State │  Commands   │    Input    │ Output  │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                │
                 ▼                ▼                ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│   Agent System    │  │    Tool System    │  │  Knowledge Graph  │
├───────────────────┤  ├───────────────────┤  ├───────────────────┤
│  Input Processor  │  │    Look Tool      │  │     Locations     │
│ Narrative Generator│  │    Move Tool     │  │       Items       │
└───────────────────┘  │   Examine Tool    │  │     Characters    │
          │            │    Talk Tool      │  └───────────────────┘
          │            │  Inventory Tool   │            │
          │            └───────────────────┘            │
          │                      │                      │
          └──────────┬───────────┘                      │
                     │                                   │
                     ▼                                   ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│    Model System   │  │    MCP System    │  │      Neo4j        │
├───────────────────┤  ├───────────────────┤  ├───────────────────┤
│   Model Manager   │  │  Server Manager  │  │  Graph Database   │
│ Transformers API  │  │  Agent Adapters  │  │                   │
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

## Component Descriptions

### Core Components

- **Core**: Provides fundamental functionality used throughout the application, including configuration management, logging, and exception handling.

### Game Engine

- **Game Loop**: The main loop that drives the game, handling user input and generating responses.
- **Game State**: Manages the current state of the game, including player location, inventory, and game world.
- **Commands**: Processes user commands and translates them into game actions.

### Agent System

- **Input Processor**: Analyzes user input to determine intent and extract entities.
- **Narrative Generator**: Creates engaging, descriptive narrative responses based on the game state.

### Tool System

- **Tool Registry**: Manages the available tools and their execution.
- **Standard Tools**: Implements common game actions like looking, moving, examining items, etc.

### Knowledge Graph

- **Neo4j Manager**: Provides an interface to the Neo4j database.
- **Schema**: Defines the structure of the knowledge graph.
- **Initializer**: Populates the graph with initial data.

### Model System

- **Model Manager**: Handles loading and using transformer models.
- **Transformers API**: Provides functions for generating text and chat responses.

### MCP System

- **Server Manager**: Manages starting, stopping, and monitoring MCP servers.
- **Agent Adapters**: Converts TTA agents into MCP servers that can be used by AI assistants.

## Data Flow

### Standard Game Flow

1. User enters a command in the game loop
2. Input processor analyzes the command to determine intent
3. Command processor executes the appropriate tool based on the intent
4. Tools interact with the knowledge graph to retrieve or update data
5. Narrative generator creates a response based on the tool result
6. Game loop displays the response to the user

### MCP Integration Flow

1. AI assistant connects to MCP servers
2. AI assistant calls MCP tools or accesses MCP resources
3. MCP server routes requests to the appropriate agent or component
4. Agent or component processes the request and returns a response
5. MCP server returns the response to the AI assistant
6. AI assistant uses the response to generate text for the user

## Design Principles

The TTA architecture follows these key design principles:

1. **Separation of Concerns**: Each component has a specific responsibility.
2. **Modularity**: Components can be developed and tested independently.
3. **Extensibility**: New agents, tools, and models can be added without changing existing code.
4. **Testability**: Components are designed to be easily testable.
5. **Configurability**: System behavior can be configured through environment variables.

## Technology Stack

- **Python**: Primary programming language
- **Neo4j**: Graph database for storing game state
- **Transformers**: Library for working with language models
- **Pydantic**: Data validation and settings management
- **Docker**: Containerization for development and deployment


---
**Logseq:** [[TTA.dev/Docs/Architecture/Overview]]
