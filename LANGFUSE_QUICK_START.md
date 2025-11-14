# Langfuse Integration - Quick Start Guide

## ✅ Status: Production-Ready & Verified

Your Langfuse integration is **fully configured and tested**!

---

## 🚀 What Just Happened

1. ✅ **Credentials Configured** - Your Langfuse API keys are set
2. ✅ **Connection Verified** - Successfully connected to Langfuse Cloud
3. ✅ **Test Traces Created** - 7 example traces sent to your dashboard
4. ✅ **All Tests Passing** - 5/5 unit tests pass

---

## 📊 View Your Data

**Langfuse Dashboard**: https://cloud.langfuse.com

You should see these traces:
- `test_llm_call` - Simple test trace
- `basic_example` - Basic primitive usage
- `enriched_example` - With metadata and user tracking
- `decorated_workflow` - Using @observe decorator
- `nested_workflow` - Multi-step workflow with child spans
  - `retrieve_documents` (retriever)
  - `generate_response` (generation)

---

## 🎯 Quick Usage

### Pattern 1: LangfusePrimitive (Recommended)

```python
from langfuse_integration import initialize_langfuse, LangfusePrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Initialize once at startup
initialize_langfuse()

# Create tracked primitive
llm = LangfusePrimitive(
    name="my_operation",
    metadata={"model": "gpt-4", "version": "v1"},
    user_id="user-123",
    tags=["production"]
)

# Use in workflow
context = WorkflowContext(
    workflow_id="my-workflow",
    correlation_id="unique-correlation-id"
)

result = await llm.execute(input_data, context)
```

### Pattern 2: @observe Decorator

```python
from langfuse import observe, get_client

@observe(name="my_function", as_type="generation")
async def process_llm_call(query: str, context: WorkflowContext):
    langfuse = get_client()
    
    # Update trace with context
    langfuse.update_current_trace(
        session_id=context.correlation_id,
        metadata={"workflow_id": context.workflow_id}
    )
    
    # Your LLM logic here
    response = await call_llm(query)
    
    # Update with LLM metrics
    langfuse.update_current_generation(
        model="gpt-4",
        usage_details={"input": 100, "output": 50, "total": 150},
        cost_details={"total_cost": 0.003}
    )
    
    return response
```

### Pattern 3: OpenAI Drop-in Replacement

```python
from langfuse.openai import OpenAI  # Drop-in replacement

client = OpenAI()  # Automatically traced!

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
    name="my_operation",
    metadata={"source": "api", "version": "v1"}
)
```

---

## 📁 Files Created

### Core Package
```
packages/tta-langfuse-integration/
├── src/langfuse_integration/
│   ├── __init__.py
│   ├── initialization.py       # Client management
│   └── primitives.py           # LangfusePrimitive classes
├── tests/
│   ├── test_initialization.py  # 3 tests ✅
│   └── test_primitives.py      # 2 tests ✅
└── docs/
    ├── ARCHITECTURE.md         # Technical deep dive
    ├── INTEGRATION_GUIDE.md    # Integration patterns
    └── MIGRATION_GUIDE_V3.md   # API migration guide
```

### Documentation (8 files, 3,000+ lines)
- `README.md` - Quick start
- `QUICK_REFERENCE.md` - API reference  
- `IMPLEMENTATION_SUMMARY.md` - What we built
- `READY_FOR_PRODUCTION.md` - Production guide
- `CHANGELOG.md` - Version history

### Examples
- `test_langfuse_connection.py` - Connection test
- `test_langfuse_trace.py` - Single trace test
- `examples/langfuse_integration_examples.py` - Comprehensive examples

---

## 🔧 Configuration

Your environment is configured with:

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-***      # ✅ Set
LANGFUSE_SECRET_KEY=sk-lf-***      # ✅ Set
LANGFUSE_HOST=https://cloud.langfuse.com  # Default
LANGFUSE_ENABLED=true              # Default
```

---

## 🧪 Testing

```bash
# Run all tests
uv run pytest packages/tta-langfuse-integration/tests/ -v
# Result: 5/5 passing ✅

# Test connection
uv run python test_langfuse_connection.py
# Result: ✅ Connection verified

# Create test trace
uv run python test_langfuse_trace.py
# Result: ✅ Trace created

# Run all examples
PYTHONPATH="packages/tta-langfuse-integration/src:packages/tta-dev-primitives/src" \
  uv run python examples/langfuse_integration_examples.py
# Result: ✅ 7 traces created
```

---

## 📊 What Gets Tracked

When you use `LangfusePrimitive`, Langfuse automatically captures:

| Data | Source | Example |
|------|--------|---------|
| **Input** | `input_data["prompt"]` | "Write a story about..." |
| **Output** | `result["response"]` | "Once upon a time..." |
| **Tokens** | `result["usage"]` | `{input: 15, output: 12, total: 27}` |
| **Cost** | `result["cost"]` | `0.00027` (USD) |
| **Model** | `result["model"]` | "gpt-4" |
| **Latency** | Auto-calculated | 1234 ms |
| **Session** | `context.correlation_id` | Maps to Langfuse session_id |
| **User** | Constructor param | "user-123" |
| **Metadata** | Constructor param | `{"version": "v1"}` |
| **Tags** | Constructor param | `["production", "api"]` |
| **Errors** | Exception capture | Full stack trace |

---

## 🎯 Next Steps

### 1. Explore Your Dashboard (Now!)
- Go to https://cloud.langfuse.com
- Navigate to **Traces**
- Filter by session_id: `test-correlation-456`
- Click into traces to see full details

### 2. Integrate with Your Code (Today)
```python
# In your existing LLM code:
from langfuse_integration import initialize_langfuse, LangfusePrimitive

# Initialize once at startup
initialize_langfuse()

# Wrap your LLM calls
llm = LangfusePrimitive(
    name="your_operation_name",
    metadata={"your": "metadata"},
    tags=["your-tags"]
)

result = await llm.execute(your_input, your_context)
```

### 3. Advanced Features (This Week)

**Prompt Management**:
```python
from langfuse_integration.initialization import get_langfuse_client

client = get_langfuse_client()
prompt = client.get_prompt("my-prompt", version=2)
messages = prompt.compile(variable="value")
```

**Scoring & Evaluation**:
```python
from langfuse import get_client

langfuse = get_client()

# Within an @observe decorated function
langfuse.update_current_generation(metadata={...})

# Score a trace
client.create_score(
    name="quality",
    value=0.95,
    trace_id="trace-id",
    comment="Excellent response"
)
```

**Datasets for Testing**:
```python
client.create_dataset_item(
    dataset_name="qa-eval",
    input={"question": "What is AI?"},
    expected_output="Artificial Intelligence is..."
)
```

---

## 💡 Tips

1. **Session IDs**: Use `WorkflowContext.correlation_id` for consistent tracking across OpenTelemetry and Langfuse

2. **User IDs**: Set user_id to track per-user metrics and costs

3. **Tags**: Use tags for filtering (e.g., "production", "staging", "customer-support")

4. **Metadata**: Add any context that helps debug or analyze (model params, versions, features)

5. **Flush Before Exit**: Call `shutdown_langfuse()` or `client.flush()` before your app exits

---

## 📚 Documentation

- **Package README**: `packages/tta-langfuse-integration/README.md`
- **Architecture**: `packages/tta-langfuse-integration/docs/ARCHITECTURE.md`
- **Integration Guide**: `packages/tta-langfuse-integration/docs/INTEGRATION_GUIDE.md`
- **API Migration**: `packages/tta-langfuse-integration/docs/MIGRATION_GUIDE_V3.md`
- **Quick Reference**: `packages/tta-langfuse-integration/QUICK_REFERENCE.md`
- **Langfuse Docs**: https://langfuse.com/docs

---

## ✨ Summary

**You now have:**
- ✅ Production-ready Langfuse integration
- ✅ Latest v3.10.0 API (via Context7)
- ✅ Dual observability (OpenTelemetry + Langfuse)
- ✅ Working credentials and verified connection
- ✅ 7 test traces in your dashboard
- ✅ Comprehensive documentation (3,000+ lines)
- ✅ Multiple usage patterns (primitives, decorators, OpenAI)
- ✅ All tests passing (5/5)

**TTA.dev now has best-in-class LLM observability!** 🎉

Check your dashboard at https://cloud.langfuse.com to see your traces!
