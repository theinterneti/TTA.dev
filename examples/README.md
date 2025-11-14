# TTA.dev Framework Examples

This directory contains practical examples demonstrating the TTA.dev agentic primitives framework.

## Workflow Examples (`workflows/`)

These examples demonstrate end-to-end workflows using the core primitives:

- **`agentic_rag_workflow.py`**: Retrieval-Augmented Generation with agent orchestration
- **`multi_agent_workflow.py`**: Multi-agent coordination patterns
- **`cost_tracking_workflow.py`**: Budget-aware workflows with cost tracking
- **`orchestration_pr_review.py`**: Automated pull request review orchestration
- **`orchestration_test_generation.py`**: Automated test generation workflow
- **`free_flagship_models.py`**: Using free tier models effectively

## Integration Examples (`integrations/`)

These examples show how to use the agent coordination framework:

- **`cicd_manager_example.py`**: CI/CD automation with agent managers
- **`infrastructure_manager_example.py`**: Infrastructure management automation
- **`quality_manager_example.py`**: Quality assurance automation

## Running Examples

All examples use the TTA.dev primitives framework. Ensure you have the framework installed:

```bash
# Install from workspace root
uv pip install -e packages/tta-dev-primitives
uv pip install -e packages/tta-dev-integrations
```

Then run any example:

```bash
python examples/workflows/agentic_rag_workflow.py
```

## Learn More

- [Core Primitives Documentation](../docs/architecture/PRIMITIVE_PATTERNS.md)
- [Universal LLM Architecture](../docs/architecture/UNIVERSAL_LLM_ARCHITECTURE.md)
- [How to Create a Primitive](../docs/guides/how-to-create-primitive.md)
