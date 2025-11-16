# TTA.dev System Patterns

## Architecture
Monorepo with 3 production packages:
1. tta-dev-primitives (core workflows)
2. tta-observability-integration (OpenTelemetry)
3. universal-agent-context (agent coordination)

## Design Patterns
- Workflow primitives for composition
- Operator overloading (`>>` for sequential, `|` for parallel)
- WorkflowContext for state propagation
- InstrumentedPrimitive for observability

## Anti-Patterns
❌ Manual async orchestration → Use SequentialPrimitive
❌ Try/except retry loops → Use RetryPrimitive
❌ asyncio.wait_for() → Use TimeoutPrimitive
❌ Global variables → Use WorkflowContext
❌ Using pip/poetry → Use uv
❌ Using Optional[str] → Use str | None
