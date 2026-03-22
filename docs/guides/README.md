# TTA.dev Guides

Practical guides for working with TTA.dev components.

> [!WARNING]
> This directory contains a mix of current guides, migration notes, and historical implementation
> write-ups. For the March 2026 canonical experience, start with the top-level
> [`GETTING_STARTED.md`](../../GETTING_STARTED.md), [`QUICKSTART.md`](../../QUICKSTART.md), and
> [`USER_JOURNEY.md`](../../USER_JOURNEY.md) before trusting older guides here.

## Getting Started

- **[Getting Started Guide](../../GETTING_STARTED.md)** - current setup and verified proof path
- **[Quickstart](../../QUICKSTART.md)** - shortest honest verification flow
- **[User Journey](../../USER_JOURNEY.md)** - current vision vs reality framing

## Development Guides

### TTA.dev How-To Guides (NEW! ✨)

**Practical, step-by-step guides for working with TTA.dev primitives:**

- **[How to Create a New Primitive](how-to-create-primitive.md)** - Complete guide for implementing custom workflow primitives
  - Type annotations and inheritance
  - Observability integration
  - Testing strategies
  - Time: 2-4 hours

- **[How to Add Observability to Workflows](how-to-add-observability.md)** - Comprehensive observability integration guide
  - OpenTelemetry tracing setup
  - Prometheus metrics
  - Structured logging
  - Grafana dashboards
  - Time: 1-2 hours

### Infrastructure & Deployment

#### Observability Stack

- **[Unified Observability Architecture](UNIFIED_OBSERVABILITY_ARCHITECTURE.md)** - ⭐ **START HERE** - Complete observability guide
  - OpenTelemetry (automatic for all primitives)
  - Grafana Cloud (metrics, logs, traces)
  - Langfuse (LLM-specific: prompts, costs, quality)
  - Multi-workspace setup
  - Persona tracking integration
  - Time: 15 minutes to understand, 30 minutes to implement

- **[Linux-Native Observability Stack](LINUX_NATIVE_OBSERVABILITY.md)** - Replace Docker with native Linux services
  - Grafana Alloy installation and configuration
  - Grafana Cloud integration
  - 700MB RAM savings, 2-second startup
  - Complete migration guide
  - Time: 30-60 minutes

- **[Native Observability Quick Reference](NATIVE_OBSERVABILITY_QUICKREF.md)** - Fast-access commands and troubleshooting
  - Service management commands
  - Verification steps
  - Common troubleshooting scenarios
  - Configuration file locations

- **[Multi-Workspace Observability](MULTI_WORKSPACE_OBSERVABILITY.md)** - Managing observability across multiple TTA.dev workspace clones
  - Single port vs multi-port strategies
  - Service name labeling
  - Grafana Alloy configuration
  - Querying across workspaces

- **[Docker-Free Observability Migration](DOCKER_FREE_OBSERVABILITY_MIGRATION.md)** - Summary and implementation roadmap
  - Migration phases
  - Resource comparison
  - Success criteria
  - Rollback procedures

- **[How to Compose Complex Workflows](how-to-compose-workflows.md)** - *(Coming soon)*
  - Sequential and parallel patterns
  - Router-based workflows
  - Recovery pattern stacking
  - Real-world examples

- **[How to Test Primitives](how-to-test-primitives.md)** - *(Coming soon)*
  - Unit and integration testing
  - MockPrimitive usage
  - Coverage strategies
  - CI/CD integration

### AI & Agent Development

- **[Full Process for Coding with AI Coding Assistants](Full%20Process%20for%20Coding%20with%20AI%20Coding%20Assistants.md)** - Best practices for AI-assisted development
- **[Multi-Model Orchestration Summary](MULTI_MODEL_ORCHESTRATION_SUMMARY.md)** - Coordinating multiple AI models
- **[Orchestration Configuration Guide](orchestration-configuration-guide.md)** - Configuring agent orchestration

### Cost & Model Selection

- **[LLM Cost Guide](llm-cost-guide.md)** - Optimizing costs across LLM providers
- **[LLM Selection Guide](llm-selection-guide.md)** - Choosing the right model for your use case
- **[Cost Optimization Patterns](cost-optimization-patterns.md)** - Patterns for reducing LLM API costs

### Infrastructure & Tools

- **[Database Selection Guide](database-selection-guide.md)** - Choosing the right database
- **[Copilot Toolsets Guide](copilot-toolsets-guide.md)** - Using GitHub Copilot toolsets in TTA.dev
- **[Integration Primitives Quickref](integration-primitives-quickref.md)** - Quick reference for integration patterns

## Advanced and historical workflow material

### Recommended starting points

Some of the files below are still useful for design ideas, but they should not be treated as
verified turnkey examples without re-checking the code and imports first:

- [`MULTI_MODEL_ORCHESTRATION_SUMMARY.md`](MULTI_MODEL_ORCHESTRATION_SUMMARY.md)
- [`orchestration-configuration-guide.md`](orchestration-configuration-guide.md)
- [`how-to-add-observability.md`](how-to-add-observability.md)
- [`UNIFIED_OBSERVABILITY_ARCHITECTURE.md`](UNIFIED_OBSERVABILITY_ARCHITECTURE.md)

For a currently verified runnable example, prefer:

- [`../../scripts/test_realtime_traces.py`](../../scripts/test_realtime_traces.py)
- [`../../GETTING_STARTED.md`](../../GETTING_STARTED.md)

## Architecture

For architectural documentation, see:
- [`docs/architecture/`](../architecture/) - Architecture decisions and patterns
- [`docs/guides/observability/`](../observability/) - Observability architecture

## Contributing

When adding a new guide:
1. Follow the existing guide format
2. Include code examples
3. Test all code snippets
4. Add link to this README
5. Update relevant package documentation

---

**Last Updated:** March 22, 2026
