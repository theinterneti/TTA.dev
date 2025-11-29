# Langfuse Integration Guide

**Hypertool Persona System - LLM Observability**

This guide shows you how to use Langfuse with Hypertool for comprehensive LLM observability, persona-based analytics, and prompt management.

---

## 🎯 What is Langfuse?

[Langfuse](https://langfuse.com) is an open-source LLM engineering platform that provides:

- **LLM Call Tracing** - Track every LLM interaction with prompts, completions, and metadata
- **Prompt Management** - Version and manage prompts centrally
- **Analytics** - Understand costs, latency, and quality by persona, model, or workflow
- **Debugging** - Replay and debug LLM interactions

**Why use it with Hypertool?**

- **Persona-as-User** - Each persona becomes a "user" in Langfuse, enabling persona-specific analytics
- **Cost Attribution** - See exactly which personas consume the most tokens/costs
- **Prompt Optimization** - Identify which prompts work best for each persona
- **Quality Tracking** - Monitor LLM quality per persona and chatmode

---

## 🚀 Quick Start

### Step 1: Get Langfuse API Keys

**Option A: Cloud (Recommended for getting started)**

1. Sign up at [https://cloud.langfuse.com](https://cloud.langfuse.com)
2. Create a project
3. Go to Settings → API Keys
4. Copy your Public Key and Secret Key

**Option B: Self-Hosted**

```bash
# Using Docker Compose
git clone https://github.com/langfuse/langfuse.git
cd langfuse
docker-compose up -d

# Access at http://localhost:3000
# Create account and get API keys
```

### Step 2: Install Langfuse SDK

```bash
# Using uv (recommended)
uv add langfuse

# Or pip
pip install langfuse
```

### Step 3: Configure Environment Variables

```bash
# Add to .env file
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_HOST="https://cloud.langfuse.com"  # Or your self-hosted URL
```

### Step 4: Use in Your Code

```python
from hypertool.instrumentation import (
    get_langfuse_integration,
    ObservableLLM,
)

# Initialize Langfuse (automatically uses env vars)
langfuse = get_langfuse_integration()

# Wrap your LLM function
async def my_llm_call(prompt: str) -> str:
    # Your actual LLM API call
    return await openai.chat.completions.create(...)

# Create observable wrapper
observable_llm = ObservableLLM(
    llm_function=my_llm_call,
    model="gpt-4",
    langfuse=langfuse,
)

# Use it (automatic tracing!)
response = await observable_llm(
    "Design a REST API for user profiles",
    persona="backend-engineer",
    chatmode="feature-implementation"
)

# Traces appear in Langfuse UI with persona as user!
```

---

## 📖 Core Concepts

### 1. Traces

A **trace** represents a complete workflow or conversation. In Hypertool:

```python
# Start a trace for a workflow
trace = langfuse.start_trace(
    name="package-release-workflow",
    persona="backend-engineer",
    chatmode="package-release",
    metadata={"version": "1.2.0"}
)

# Trace captures all LLM calls and spans within it
# ...

# End trace
langfuse.end_trace(trace, status="success")
```

### 2. Spans

**Spans** are sub-units within a trace (like stages in a workflow):

```python
# Create a span for a specific stage
span = langfuse.start_span(
    trace=trace,
    name="api-design-stage",
    metadata={"stage": "design"}
)

# Span can contain multiple generations
# ...
```

### 3. Generations

**Generations** are individual LLM API calls:

```python
# Record an LLM call
generation = langfuse.create_generation(
    trace=trace,
    name="design-api",
    model="gpt-4",
    prompt="Design REST API for user profiles",
    completion="Here's the API design...",
    usage={
        "prompt_tokens": 150,
        "completion_tokens": 800,
        "total_tokens": 950
    }
)
```

### 4. Persona-as-User Pattern

**Key Innovation:** We use personas as Langfuse "users" for analytics:

```python
trace = langfuse.start_trace(
    name="feature-implementation",
    persona="backend-engineer",  # ← Becomes user_id in Langfuse
    chatmode="feature-implementation"
)
```

**Benefits:**
- Analytics by persona (which persona uses most tokens?)
- Identify persona-specific patterns
- Optimize prompts per persona
- Track persona performance over time

---

## 🛠️ Using ObservableLLM

The `ObservableLLM` wrapper automatically creates traces and generations for any LLM function.

### Basic Usage

```python
from hypertool.instrumentation import ObservableLLM

# Define your LLM function
async def call_openai(prompt: str) -> str:
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Wrap it
observable_llm = ObservableLLM(
    llm_function=call_openai,
    model="gpt-4",
)

# Use it
response = await observable_llm(
    prompt="Write a FastAPI endpoint",
    persona="backend-engineer",
    chatmode="coding"
)
```

### Advanced: Using with Existing Trace

```python
# Start workflow trace
workflow_trace = langfuse.start_trace(
    name="multi-stage-workflow",
    persona="multi-persona",
    chatmode="feature-implementation"
)

# Stage 1: Backend
response1 = await observable_llm(
    prompt="Design API models",
    persona="backend-engineer",
    chatmode="feature-implementation",
    trace=workflow_trace  # ← Attach to existing trace
)

# Stage 2: Frontend
response2 = await observable_llm(
    prompt="Create React components",
    persona="frontend-engineer",
    chatmode="feature-implementation",
    trace=workflow_trace  # ← Same trace
)

# End trace
langfuse.end_trace(workflow_trace, status="success")
```

### Decorator Pattern

```python
from hypertool.instrumentation import observe_llm

# Decorate your function
@observe_llm(model="gpt-4", persona="backend-engineer")
async def design_api(requirements: str) -> str:
    # Your LLM call
    return await openai.chat.completions.create(...)

# Use it (automatic tracing!)
result = await design_api("User authentication system")
```

---

## 📊 Viewing Traces in Langfuse

### Accessing Langfuse UI

1. **Cloud:** [https://cloud.langfuse.com](https://cloud.langfuse.com)
2. **Self-Hosted:** `http://localhost:3000`

### What You'll See

**Traces Tab:**
- All workflow executions
- Filter by persona (user)
- See total cost, duration, token usage
- Click for detailed view

**Generations Tab:**
- All LLM calls
- Grouped by model
- See prompts and completions
- Token usage breakdown

**Users Tab:**
- **THIS IS WHERE PERSONAS APPEAR!**
- Each persona is a "user"
- See total usage per persona
- Cost attribution by persona

**Analytics:**
- Cost trends over time
- Token usage by persona
- Latency distributions
- Error rates

---

## 🔍 Example Queries in Langfuse

### Query 1: Total Cost by Persona

In Langfuse UI → Users:
- Click on persona (e.g., "backend-engineer")
- See total cost, tokens, and traces

### Query 2: Slowest LLM Calls

In Generations tab:
- Sort by duration (descending)
- Identify bottlenecks

### Query 3: Failed Generations

In Traces tab:
- Filter by status = "error"
- See which personas have most failures

---

## 🎛️ Configuration Options

### Environment Variables

```bash
# Required
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."

# Optional
LANGFUSE_HOST="https://cloud.langfuse.com"  # Default: cloud
LANGFUSE_DEBUG="false"  # Enable debug logging
```

### Programmatic Configuration

```python
from hypertool.instrumentation import LangfuseIntegration

# Custom configuration
langfuse = LangfuseIntegration(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    host="https://my-langfuse.com"
)
```

### Graceful Degradation

If Langfuse is not configured:
- LangfuseIntegration creates no-op instances
- ObservableLLM still works (just no tracing)
- No errors or crashes
- Logs warning message

---

## 🧪 Testing Integration

Run the test workflow to validate setup:

```bash
# Set environment variables first
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."

# Run test workflow
python -m .hypertool.instrumentation.test_instrumented_workflow

# Check output
# Should see: "🔍 Langfuse tracing enabled!"
# If not: "⚠️  Langfuse not configured"
```

**Expected Output:**

```
🚀 Starting Package Release Workflow
============================================================

📝 Stage 1: Version Bump
   Persona: backend-engineer
   ✅ Mock LLM response for: Implement backend for: Update version to 1.2.0
   📊 Tokens: 850
   💰 Budget remaining: 4150

...

✅ Package Release Workflow Complete!

🔍 Langfuse tracing enabled!
   Host: https://cloud.langfuse.com
   Check Langfuse UI for LLM traces with persona context
```

---

## 🚨 Troubleshooting

### Issue: "Langfuse not configured"

**Solution:**
```bash
# Check environment variables
echo $LANGFUSE_PUBLIC_KEY
echo $LANGFUSE_SECRET_KEY

# If empty, set them
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
```

### Issue: "Failed to initialize Langfuse client"

**Possible causes:**
1. Invalid API keys → Check keys in Langfuse UI
2. Network issues → Check connectivity to Langfuse host
3. SDK not installed → Run `uv add langfuse`

**Debug:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Will show detailed error messages
from hypertool.instrumentation import get_langfuse_integration
langfuse = get_langfuse_integration()
```

### Issue: "Traces not appearing in UI"

**Solution:**
```python
# Manually flush to ensure traces are sent
langfuse.flush()

# Or at end of workflow
langfuse.end_trace(trace, status="success")
langfuse.flush()  # ← Forces immediate send
```

---

## 📈 Best Practices

### 1. Use Persona-as-User Consistently

```python
# ✅ GOOD: Consistent persona naming
trace = langfuse.start_trace(
    name="feature-implementation",
    persona="backend-engineer",  # Matches your persona name
    chatmode="feature-implementation"
)

# ❌ BAD: Inconsistent naming
trace = langfuse.start_trace(
    name="feature-implementation",
    persona="Backend Engineer",  # Different casing
    chatmode="feature-implementation"
)
```

### 2. Add Meaningful Metadata

```python
trace = langfuse.start_trace(
    name="bug-fix",
    persona="backend-engineer",
    chatmode="debugging",
    metadata={
        "issue_id": "BUG-1234",
        "priority": "high",
        "repository": "tta-dev-primitives",
        "estimated_complexity": "medium"
    }
)
```

### 3. Always End Traces

```python
try:
    trace = langfuse.start_trace(...)
    # Your workflow
    result = await execute_workflow()
    langfuse.end_trace(trace, status="success")
except Exception as e:
    langfuse.end_trace(trace, status="error")
    raise
```

### 4. Use ObservableLLM for Consistency

```python
# ✅ GOOD: ObservableLLM handles everything
observable_llm = ObservableLLM(llm_function=call_gpt4, model="gpt-4")
result = await observable_llm(prompt, persona="backend-engineer")

# ❌ BAD: Manual generation creation (error-prone)
result = await call_gpt4(prompt)
langfuse.create_generation(...)  # Easy to forget or get wrong
```

---

## 🔗 Related Documentation

- **Langfuse Docs:** [https://langfuse.com/docs](https://langfuse.com/docs)
- **PersonaMetricsCollector:** `persona_metrics.py`
- **WorkflowTracer:** `workflow_tracing.py`
- **Phase 5 Design:** `../PHASE5_APM_LANGFUSE_INTEGRATION.md`
- **Quick Reference:** `../PHASE5_QUICK_REFERENCE.md`

---

## 🎯 Next Steps

1. **Set up Langfuse account** (5 minutes)
2. **Configure API keys** in `.env` (1 minute)
3. **Run test workflow** to validate (2 minutes)
4. **Integrate into your workflows** (varies)
5. **Explore Langfuse UI** for insights

**Questions?** Check the [Langfuse documentation](https://langfuse.com/docs) or open an issue.

---

**Last Updated:** 2025-11-15  
**Status:** Week 2 Complete  
**Next:** Week 3 - Grafana Dashboards & Prometheus Alerts
