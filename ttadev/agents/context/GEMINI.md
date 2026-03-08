# Project: TTA (Therapeutic Text Adventure)

## Overview
TTA is a therapeutic text adventure game that combines AI-driven storytelling with mental health support. The system uses multiple AI agents to create collaborative, adaptive narratives while maintaining therapeutic value.

## Tech Stack
- **Backend:** Python 3.12, FastAPI, Pydantic
- **Databases:** Redis (session state), Neo4j (narrative graph)
- **AI/LLM:** OpenRouter API, multiple model support
- **Testing:** pytest, pytest-asyncio, pytest-cov
- **Quality Tools:** ruff (linting), pyright (type checking), detect-secrets (security)
- **Package Management:** UV (uv run for project env, uvx for standalone tools)
- **Frontend:** Next.js, React, TypeScript
- **Deployment:** Docker, Docker Compose

## Project Structure
```
/home/thein/recovered-tta-storytelling/
├── src/                          # Python source code
│   ├── orchestration/            # Component orchestration (CURRENT FOCUS)
│   ├── components/               # TTA components
│   ├── player_experience/        # Player interaction layer
│   └── narrative_arc_orchestrator/ # Story management
├── tests/                        # Test suite
│   ├── test_orchestrator.py      # Orchestration unit tests
│   ├── test_orchestration_integration.py  # Integration tests
│   └── integration/              # Integration test suite
├── .augment/                     # AI agent primitives
│   ├── chatmodes/                # Role-based AI modes
│   ├── context/                  # Scenario-specific guidance
│   ├── workflows/                # Reusable workflows
│   ├── rules/                    # AI agent rules
│   └── memory/                   # Project knowledge
├── specs/                        # Component specifications
├── scripts/                      # Automation scripts
│   └── workflow/                 # Workflow automation
└── docs/                         # Documentation

```

## Component Maturity Workflow

**See AGENTS.md** for complete maturity workflow and quality gates.

**Current Focus:** Orchestration component at 49.4% coverage, targeting 70% for staging promotion.

## Code Style & Patterns

### Python Style
- Use Python 3.12+ features (type hints, dataclasses, async/await)
- Follow PEP 8 with ruff enforcement
- Prefer composition over inheritance
- Use dependency injection for testability
- Write comprehensive docstrings (Google style)

### Testing Patterns

**See AGENTS.md** for testing patterns, test pyramid, and comprehensive test battery.

### Architecture Principles

**See AGENTS.md** for SOLID principles and code quality standards.

## Current Task: Orchestration Refactoring

### Context
Improving test coverage for `src/orchestration/orchestrator.py` from 49.4% to 70% for staging promotion.

### Challenges
- **Filesystem Dependencies:** Methods like `_import_components()`, `_import_repository_components()`, `_validate_repositories()` directly access filesystem
- **Hard to Test:** Current implementation tightly couples business logic with filesystem operations
- **Coverage Gap:** Need 107 more lines covered (456/652 total)

### Refactoring Goals
1. **Extract Filesystem Operations:** Separate filesystem access from business logic
2. **Dependency Injection:** Make filesystem operations injectable for testing
3. **Maintain Compatibility:** All 82 existing tests must continue passing
4. **Increase Coverage:** Reach 70% coverage threshold

### Recommended Patterns
- **Strategy Pattern:** For pluggable component loaders
- **Dependency Injection:** For filesystem operations
- **Protocol/Interface:** For abstract component discovery
- **Factory Pattern:** For creating component instances

## Common Commands

### Development
```bash
# Run tests
uvx pytest tests/test_orchestrator.py -v

# Check coverage
uvx pytest tests/test_orchestrator.py --cov=src/orchestration --cov-report=term

# Lint code
uvx ruff check src/ tests/

# Type check
uvx pyright src/

# Format code
uvx ruff format src/ tests/
```

### Workflow Automation
```bash
# Run component promotion workflow
python scripts/workflow/spec_to_production.py \
    --spec specs/orchestration.md \
    --component orchestration \
    --target staging
```

### AI Context Management

**See AGENTS.md** for session management commands and importance scoring.

## Agentic Primitives Integration

### Chat Modes (`.augment/chatmodes/`)
- `architect.chatmode.md` - System architecture and design
- `backend-dev.chatmode.md` - Python/FastAPI implementation
- `qa-engineer.chatmode.md` - Testing and quality assurance
- `devops.chatmode.md` - Deployment and infrastructure

### Context Helpers (`.augment/context/`)
- `debugging.context.md` - Debugging workflows
- `refactoring.context.md` - Code refactoring patterns
- `performance.context.md` - Performance optimization
- `testing.context.md` - Testing strategies

### Workflows (`.augment/workflows/`)
- `test-coverage-improvement.prompt.md` - Systematic coverage improvement
- `component-promotion.prompt.md` - Component maturity progression
- `bug-fix.prompt.md` - Bug investigation and resolution

## Best Practices for This Project

**See AGENTS.md** for best practices (refactoring, adding tests, before/during/after implementation).

### When Using Gemini CLI (Gemini-Specific)
1. **Provide Context:** Use `@{file}` to inject relevant code
2. **Be Specific:** Clear, structured prompts with goals and constraints
3. **Validate Recommendations:** Don't blindly implement suggestions
4. **Document Consultations:** Track in AI context sessions
5. **Test Incrementally:** Validate after each change

## File Patterns to Respect
- `.gitignore` - Git ignored files
- `.geminiignore` - Gemini CLI ignored files (if created)
- `pyproject.toml` - Python project configuration
- `pytest.ini` - Pytest configuration

## Important Notes

**See AGENTS.md** for important notes (package management, circuit breakers, error handling, testing, documentation).

---

**Last Updated:** 2025-10-20
**Current Session:** coverage-improvement-orchestration-2025-10-20
**Current Goal:** Refactor orchestration for 70% test coverage using dependency injection
