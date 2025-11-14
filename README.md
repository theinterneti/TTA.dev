# TTA.dev - Agentic Primitives Framework

**A framework for building AI agents with budget-aware, multi-provider LLM orchestration.**

## What is TTA.dev?

TTA.dev is a Python framework that provides **agentic primitives** - reusable building blocks for creating sophisticated AI agent workflows. It emphasizes:

- **Budget Awareness**: Choose between FREE, CAREFUL, and UNLIMITED budget profiles
- **Multi-Provider Support**: OpenAI, Anthropic, Google, OpenRouter, HuggingFace
- **Multi-Coder Integration**: Works with Copilot, Cline, Augment Code, and more
- **Cost Transparency**: Track and justify every LLM call with detailed cost reporting
- **Composable Primitives**: Build complex workflows from simple, testable components

## Quick Start

```bash
# Install the framework
uv pip install -e packages/tta-dev-primitives
uv pip install -e packages/tta-dev-integrations

# Run an example
python examples/workflows/free_flagship_models.py
```

## Core Concepts

### 1. Universal LLM Primitive

The `UniversalLLMPrimitive` is the foundation of TTA.dev's multi-provider architecture:

```python
from tta_dev_integrations.llm import UniversalLLMPrimitive, UserBudgetProfile

# Create a budget-aware LLM client
llm = UniversalLLMPrimitive(
    budget_profile=UserBudgetProfile.CAREFUL,  # Mix free + paid models
    default_provider="openai"
)

# Make a request with automatic cost tracking
response = await llm.generate(
    prompt="Explain agentic primitives",
    complexity="medium"  # Automatically selects appropriate model
)
```

### 2. Budget Profiles

Control costs with three predefined profiles:

- **FREE**: Only use free models (Gemini, DeepSeek, Kimi) - for hobbyists and students
- **CAREFUL**: Mix of free and paid models with cost tracking - for solo devs
- **UNLIMITED**: Always use the best model, cost tracked but not limiting - for companies

### 3. Adaptive Primitives

Build resilient workflows with built-in retry, fallback, timeout, and caching:

```python
from tta_dev_primitives.adaptive import RetryPrimitive, FallbackPrimitive

# Automatically retry failed LLM calls
reliable_llm = RetryPrimitive(
    wrapped=llm,
    max_attempts=3,
    exponential_backoff=True
)

# Fall back to cheaper model if primary fails
resilient_llm = FallbackPrimitive(
    primary=expensive_model,
    fallback=free_model
)
```

### 4. Orchestration Primitives

Coordinate multiple agents and workflows:

```python
from tta_dev_primitives.orchestration import SequentialPrimitive, ParallelPrimitive

# Run tasks in sequence
sequential_workflow = SequentialPrimitive(tasks=[
    analyze_requirements,
    generate_code,
    write_tests
])

# Run tasks in parallel
parallel_workflow = ParallelPrimitive(tasks=[
    lint_code,
    type_check,
    run_tests
])
```

## Architecture

```
TTA.dev Framework
├── packages/
│   ├── tta-dev-primitives/      # Core primitives (adaptive, orchestration, memory)
│   ├── tta-dev-integrations/    # LLM and service integrations
│   └── tta-agent-coordination/  # Agent coordination framework
├── examples/                     # Workflow and integration examples
├── docs/                         # Architecture and guides
└── archive/                      # Historical code (legacy-tta-game)
```

## Key Features

### 🆓 50% Free, 50% Paid Model Strategy

TTA.dev is designed for developers who want to:
- Use free models (Gemini, Kimi, DeepSeek) for simple tasks
- Reserve paid models (Claude Sonnet) for complex work
- Track and justify every cost decision

### 🔄 Multi-Provider Support

Switch between providers seamlessly:
- **OpenAI**: GPT-4, GPT-3.5
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus
- **Google**: Gemini Pro (free tier available)
- **OpenRouter**: Access to 100+ models
- **HuggingFace**: Open source models

### 🧩 Composable Primitives

Build complex agents from simple, tested primitives:
- **Adaptive**: Retry, fallback, timeout, cache
- **Orchestration**: Sequential, parallel, router, conditional
- **Memory**: Redis-backed persistence
- **APM**: Observability and monitoring

### 🎯 Multi-Coder Integration

Works with your favorite AI coding assistant:
- **GitHub Copilot** (VS Code, CLI, GitHub.com)
- **Cline** (VS Code extension)
- **Augment Code** (VS Code extension)
- Extensible to other coders

## Documentation

- **[Architecture Overview](docs/architecture/SYSTEM_DESIGN.md)**: High-level system design
- **[Universal LLM Architecture](docs/architecture/UNIVERSAL_LLM_ARCHITECTURE.md)**: Multi-provider LLM design
- **[Primitive Patterns](docs/architecture/PRIMITIVE_PATTERNS.md)**: How to use and create primitives
- **[Free Model Selection Guide](docs/guides/FREE_MODEL_SELECTION.md)**: Choosing free vs paid models
- **[LLM Cost Guide](docs/guides/llm-cost-guide.md)**: Cost tracking and budgeting
- **[How to Create a Primitive](docs/guides/how-to-create-primitive.md)**: Extending the framework

## Examples

Explore real-world workflows in the [`examples/`](examples/) directory:

### Workflows
- **Agentic RAG**: Retrieval-augmented generation with agents
- **Multi-Agent Coordination**: Multiple agents working together
- **Cost-Tracked Workflows**: Budget-aware task execution
- **PR Review Automation**: Automated code review
- **Test Generation**: Automated test creation

### Integrations
- **CI/CD Automation**: GitHub Actions and similar
- **Infrastructure Management**: Docker, Kubernetes orchestration
- **Quality Assurance**: Automated testing and validation

## Development

```bash
# Install development dependencies
uv sync --all-extras

# Run tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=packages --cov-report=html

# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix

# Type check
uvx pyright packages/
```

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Key areas for contribution:
- New primitive patterns
- Additional LLM provider integrations
- Example workflows
- Documentation improvements
- Bug fixes and performance improvements

## Roadmap

### Current (v0.1)
- ✅ Universal LLM Primitive with budget profiles
- ✅ Core adaptive primitives (retry, fallback, timeout, cache)
- ✅ Orchestration primitives (sequential, parallel)
- ✅ Multi-provider support (OpenAI, Anthropic, Google)
- ✅ Agent coordination framework

### Upcoming (v0.2)
- 🔄 Enhanced observability with Langfuse integration
- 🔄 Additional provider support (Mistral, Cohere)
- 🔄 Advanced memory primitives (vector stores)
- 🔄 Workflow visualization and debugging tools

### Future (v0.3+)
- 📋 Visual workflow builder
- 📋 Pre-built agent templates
- 📋 Cost optimization recommendations
- 📋 Multi-modal support (vision, audio)

## License

[MIT License](LICENSE)

## Credits

TTA.dev is built by developers who believe in:
- **Open source**: Framework code is open for inspection and contribution
- **Cost transparency**: Every LLM call should be tracked and justified
- **Developer empowerment**: You control your budget and model selection
- **Composability**: Complex agents built from simple, testable primitives

## Related Projects

- **Primitive Branches**:
  - `agent/copilot` (PR #80): Original universal LLM architecture
  - `refactor/tta-dev-framework-cleanup` (PR #98): Framework structure refactor
  - This branch (`agentic/core-architecture`) supersedes both

## Support

- **Issues**: [GitHub Issues](https://github.com/theinterneti/TTA.dev/issues)
- **Discussions**: [GitHub Discussions](https://github.com/theinterneti/TTA.dev/discussions)
- **Documentation**: [`docs/`](docs/)

---

**TTA.dev**: Build intelligent agents, not expensive bills. 🤖💰
