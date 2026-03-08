# TTA.dev Examples

Real-world examples showing TTA.dev primitives in action. Each example is fully instrumented - run them and watch their execution on the dashboard at http://localhost:8000!

## Getting Started

```bash
# Start the observability dashboard (in one terminal)
uv run python tta-dev/ui/observability_server.py

# Run any example (in another terminal)
uv run python tta-dev/examples/hello_world.py
```

## Examples

### 1. Hello World (`hello_world.py`)
**Learn:** Basic workflow composition with `>>` operator
- Simple chaining of primitives
- Observability context
- Real-time trace viewing

### 2. Retry Pattern (`retry_pattern.py`)
**Learn:** Handling transient failures gracefully
- Automatic retry with exponential backoff
- Failure recovery
- Watch retry attempts in dashboard

### 3. Parallel Processing (`parallel_processing.py`)
**Learn:** Speed up workflows with concurrency
- Process multiple items simultaneously
- See parallel execution in timeline view
- Efficient resource utilization

## What You'll See

Open http://localhost:8000 in your browser to see:
- **Live traces** as workflows execute
- **Timeline view** showing span durations
- **Success/failure status** for each operation
- **Performance metrics** in real-time

## Next Steps

1. Modify these examples to fit your use case
2. Combine primitives to build complex workflows
3. Add your own business logic
4. Watch everything in the dashboard!

Check out the [Primitives Catalog](../PRIMITIVES_CATALOG.md) for all available primitives.
