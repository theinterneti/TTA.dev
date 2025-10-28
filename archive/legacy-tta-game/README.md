# Legacy TTA Game Project Archive

This directory contains materials from the original "Therapeutic Text Adventure" (TTA) game project that was developed in this repository before the pivot to a general AI development toolkit.

## Historical Context

The TTA project (approximately early 2024 - September 2024) was an ambitious text-based adventure game that:

- Used AI agents for narrative generation and game management
- Leveraged Neo4j knowledge graphs for game state
- Implemented dynamic agent generation with LangChain/LangGraph
- Aimed to provide therapeutic experiences through interactive storytelling

## What's Archived Here

### Game Code
- `core/` - Main game engine and logic
  - `main.py` - Game entry point
  - `dynamic_game.py` - Game state management
  - `langgraph_engine.py` - Agent orchestration

### Documentation
- `PRD.md` - Product Requirements Document for the TTA game
- `PLANNING.md` - Development planning and architecture decisions
- `Roadmap.md` - Project phases and timeline
- `TASKS.md` - Specific implementation tasks
- `User_Guide.md` - Guide for players
- `Agentic_RAG.md` - RAG architecture for the game
- `Neo4j_Schema.md` - Knowledge graph schema
- `DataModel.md` - Game data structures
- `TestingStrategy.md` - Testing strategy

### Tests
- `test_basic.py` - Basic import tests
- `test_dynamic_agents.py` - Agent system tests
- `test_dynamic_tools.py` - Tool system tests
- `test_langgraph_engine.py` - Workflow engine tests
- `test_memory.py` - Memory system tests

## Pivot to AI Development Toolkit

In September 2024, the repository was refocused to become **TTA.dev - AI Development Toolkit**, a collection of reusable AI development tools, workflows, and primitives for building AI-native applications.

The new direction emphasizes:
- Production-ready, reusable components
- Workflow primitives and patterns
- MCP (Model Context Protocol) integration
- Development best practices
- General AI application development (not game-specific)

## Why Archive Instead of Delete?

These materials represent significant development work and contain valuable insights about:
- Agentic system design
- LangChain/LangGraph patterns
- Knowledge graph integration
- AI-driven content generation
- Dynamic agent orchestration

While no longer the primary focus, they may provide reference material for future AI development work.

## Using These Materials

Feel free to reference these materials for:
- Learning about agentic AI systems
- Understanding LangChain/LangGraph implementations
- Knowledge graph schema design
- AI game development concepts

However, be aware that:
- Code may reference non-existent dependencies
- Documentation reflects the old project scope
- Some approaches may be outdated

---

*Archived: October 2024*  
*Original development period: ~Early 2024 - September 2024*
