# TTA.dev Guides

Practical guides for working with TTA.dev components.

## Getting Started

- **[Getting Started Guide](../../GETTING_STARTED.md)** - Quick start and core concepts
- **[Phase 3 Examples Guide](../../PHASE3_EXAMPLES_COMPLETE.md)** - 5 production-ready workflows with complete implementation details

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

## Production Workflows

### Recommended Starting Points

The **Phase 3 Examples** demonstrate production-ready patterns:

1. **[RAG Workflow](../../packages/tta-dev-primitives/examples/rag_workflow.py)**
   - Caching + Fallback + Retry
   - Reduces costs by 40-60%
   - Use for: Document retrieval systems

2. **[Agentic RAG](../../packages/tta-dev-primitives/examples/agentic_rag_workflow.py)**
   - Router + Document Grading + Hallucination Detection
   - Production RAG pattern from NVIDIA
   - Use for: High-quality RAG with quality controls

3. **[Cost Tracking](../../packages/tta-dev-primitives/examples/cost_tracking_workflow.py)**
   - Budget enforcement + Per-model metrics
   - Prometheus integration
   - Use for: Managing LLM API costs

4. **[Streaming](../../packages/tta-dev-primitives/examples/streaming_workflow.py)**
   - Token-by-token streaming + Buffering
   - Throughput metrics
   - Use for: Real-time response streaming

5. **[Multi-Agent](../../packages/tta-dev-primitives/examples/multi_agent_workflow.py)**
   - Coordinator + Parallel specialists + Aggregation
   - Agent coordination pattern
   - Use for: Complex multi-agent workflows

**All examples:**
- ✅ Use InstrumentedPrimitive pattern
- ✅ Include automatic OpenTelemetry tracing
- ✅ Have Prometheus metrics
- ✅ Are validated and tested

**Detailed Implementation:** See [PHASE3_EXAMPLES_COMPLETE.md](../../PHASE3_EXAMPLES_COMPLETE.md)

## Architecture

For architectural documentation, see:
- [`docs/architecture/`](../architecture/) - Architecture decisions and patterns
- [`docs/observability/`](../observability/) - Observability architecture

## Contributing

When adding a new guide:
1. Follow the existing guide format
2. Include code examples
3. Test all code snippets
4. Add link to this README
5. Update relevant package documentation

---

**Last Updated:** October 30, 2025
