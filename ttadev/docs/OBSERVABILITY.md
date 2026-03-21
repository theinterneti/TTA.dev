# Batteries-Included Observability

TTA.dev comes with **zero-configuration observability** out of the box. Every primitive is automatically instrumented, and a beautiful web dashboard shows you exactly what's happening in real-time.

## Quick Start

### 1. Start the Dashboard

```bash
# Terminal 1: Start the observability server
cd TTA.dev
uv run python ttadev/ui/observability_server.py
```

Visit **http://localhost:8000** in your browser.

### 2. Run Your Workflows

```bash
# Terminal 2: Run any TTA.dev workflow
uv run python ttadev/examples/simple_demo.py
```

**Watch the magic happen!** The dashboard automatically updates with:
- 📊 Real-time trace visualization
- ⏱️ Timing and duration for each step
- 🔄 Retry attempts and backoff delays
- 🌳 Complete workflow tree structure
- ✅ Success/failure status for every operation

## What Gets Instrumented?

### Automatic Instrumentation

ALL TTA.dev primitives are automatically instrumented - no extra code needed!

```python
from primitives import SequentialPrimitive, RetryPrimitive, LambdaPrimitive, WorkflowContext

# Everything just works!
workflow = SequentialPrimitive([
    RetryPrimitive(LambdaPrimitive(fetch_data)),  # ✅ Automatically traced
    LambdaPrimitive(process_data),                 # ✅ Automatically traced
])

ctx = WorkflowContext(workflow_id="my_workflow")
result = await workflow.execute(input_data, ctx)   # ✅ Full observability!
```

## Dashboard Features

For every workflow execution, see:

- **Workflow Overview** - Trace ID, duration, status, primitive count
- **Span Timeline** - Visual tree of operations with parent-child relationships
- **Detailed Spans** - Names, durations, input/output, retries, errors
- **Real-Time Updates** - WebSocket-powered live updates

## Self-Observing

The dashboard tracks its own operations! You'll see traces for server startup, WebSocket connections, and trace ingestion. This demonstrates TTA.dev's philosophy: **use TTA.dev to build TTA.dev**.

## Growing with Your Application

As you build features, the dashboard automatically visualizes everything:

```python
# Your AI agent
agent_workflow = SequentialPrimitive([
    LambdaPrimitive(understand_request),
    ParallelPrimitive([search_codebase, analyze_context]),
    RetryPrimitive(generate_code),
])
# Dashboard shows it all!

# Your application
user_workflow = SequentialPrimitive([
    authenticate_user,
    FallbackPrimitive(fetch_from_cache, fetch_from_database),
    transform_response,
])
# Dashboard visualizes the complete flow!
```

## Examples

- **examples/simple_demo.py** - Sequential workflow with retries
- **examples/comprehensive_demo.py** - All primitive types
- **examples/hello_world.py** - Self-observing dashboard

## Philosophy

1. **Zero Configuration** - Works after `./setup.sh`, no config files
2. **Batteries Included** - Built-in dashboard, runs locally
3. **Grow When Needed** - Start simple, add sampling/exports for production
4. **Developer Experience** - Beautiful UI, real-time feedback

**Learn by doing - use TTA.dev and watch what happens!** 🚀
