# TTA.dev/Patterns/Sequential Workflow

**Linear data flow patterns for step-by-step processing**

---

## Overview

Sequential workflows execute operations in order, where each step's output becomes the next step's input. This is the most fundamental workflow pattern in TTA.dev.

**Core Operator:** `>>` (sequential composition)
**Key Primitive:** [[SequentialPrimitive]]
**Use When:** Operations must happen in a specific order with dependencies

---

## Basic Sequential Pattern

### Simple Chain

```python
from tta_dev_primitives import WorkflowContext

# Define processing steps
async def extract_text(data: dict, context: WorkflowContext) -> dict:
    """Extract text from document."""
    return {"text": data["document"].extract_text()}

async def clean_text(data: dict, context: WorkflowContext) -> dict:
    """Clean and normalize text."""
    return {"text": data["text"].strip().lower()}

async def tokenize(data: dict, context: WorkflowContext) -> dict:
    """Tokenize cleaned text."""
    return {"tokens": data["text"].split()}

# Compose sequentially using >> operator
workflow = extract_text >> clean_text >> tokenize

# Execute
context = WorkflowContext(workflow_id="text-processing")
result = await workflow.execute({"document": doc}, context)
# Result: {"tokens": ["cleaned", "tokenized", "words"]}
```

**Data Flow:**
```
{"document": doc} → extract_text → {"text": raw}
                  → clean_text → {"text": cleaned}
                  → tokenize → {"tokens": [...]}
```

### Explicit Sequential Primitive

```python
from tta_dev_primitives import SequentialPrimitive

# Same workflow using SequentialPrimitive explicitly
workflow = SequentialPrimitive([
    extract_text,
    clean_text,
    tokenize
])
```

---

## Sequential with State Accumulation

### Accumulating Results

```python
async def load_document(data: dict, context: WorkflowContext) -> dict:
    """Load document and keep original."""
    return {
        "original": data,
        "document": await load_from_storage(data["doc_id"])
    }

async def extract_metadata(data: dict, context: WorkflowContext) -> dict:
    """Extract metadata, keep previous data."""
    return {
        **data,  # Keep everything
        "metadata": extract_metadata_from(data["document"])
    }

async def generate_summary(data: dict, context: WorkflowContext) -> dict:
    """Generate summary, keep previous data."""
    return {
        **data,
        "summary": await llm_summarize(data["document"])
    }

# Each step adds to accumulated state
workflow = load_document >> extract_metadata >> generate_summary

result = await workflow.execute({"doc_id": "123"}, context)
# Result contains: original, document, metadata, summary
```

---

## Sequential Preprocessing Pipeline

### Text Processing Pipeline

```python
from tta_dev_primitives import SequentialPrimitive

async def validate_input(data: dict, context: WorkflowContext) -> dict:
    """Validate input data."""
    if not data.get("text"):
        raise ValueError("Text required")
    return data

async def remove_html(data: dict, context: WorkflowContext) -> dict:
    """Remove HTML tags."""
    import re
    clean = re.sub(r'<[^>]+>', '', data["text"])
    return {"text": clean}

async def normalize_whitespace(data: dict, context: WorkflowContext) -> dict:
    """Normalize whitespace."""
    normalized = ' '.join(data["text"].split())
    return {"text": normalized}

async def convert_case(data: dict, context: WorkflowContext) -> dict:
    """Convert to lowercase."""
    return {"text": data["text"].lower()}

# Preprocessing pipeline
preprocess = (
    validate_input >>
    remove_html >>
    normalize_whitespace >>
    convert_case
)

# Use in larger workflow
workflow = preprocess >> process >> postprocess
```

---

## Sequential with Error Handling

### Resilient Sequential Workflow

```python
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive

# Wrap unreliable steps
reliable_extract = RetryPrimitive(
    primitive=extract_text,
    max_retries=3,
    backoff_strategy="exponential"
)

reliable_process = FallbackPrimitive(
    primary=process_with_api,
    fallbacks=[process_locally, use_cache]
)

# Sequential workflow with resilience
workflow = (
    validate_input >>
    reliable_extract >>
    reliable_process >>
    save_results
)
```

---

## Sequential RAG Pipeline

### Document Retrieval Workflow

```python
async def embed_query(data: dict, context: WorkflowContext) -> dict:
    """Generate query embedding."""
    embedding = await embedding_model.encode(data["query"])
    return {
        "query": data["query"],
        "embedding": embedding
    }

async def search_vectors(data: dict, context: WorkflowContext) -> dict:
    """Search vector database."""
    results = await vector_db.search(
        embedding=data["embedding"],
        limit=10
    )
    return {
        **data,
        "documents": results
    }

async def rerank_results(data: dict, context: WorkflowContext) -> dict:
    """Rerank documents by relevance."""
    reranked = await reranker.rank(
        query=data["query"],
        documents=data["documents"]
    )
    return {
        **data,
        "documents": reranked[:5]  # Top 5
    }

async def generate_response(data: dict, context: WorkflowContext) -> dict:
    """Generate LLM response with context."""
    context_str = "\n".join(doc.text for doc in data["documents"])
    response = await llm.generate(
        prompt=f"Context: {context_str}\n\nQuery: {data['query']}"
    )
    return {"response": response}

# RAG pipeline
rag_workflow = (
    embed_query >>
    search_vectors >>
    rerank_results >>
    generate_response
)
```

**RAG Flow:**
```
query → embed_query → embedding
      → search_vectors → documents (10)
      → rerank_results → documents (5)
      → generate_response → response
```

---

## Sequential Multi-Stage Processing

### Data Transformation Pipeline

```python
# Stage 1: Ingestion
ingest_workflow = (
    fetch_raw_data >>
    validate_schema >>
    deduplicate
)

# Stage 2: Processing
process_workflow = (
    normalize_format >>
    enrich_data >>
    apply_business_rules
)

# Stage 3: Output
output_workflow = (
    format_output >>
    validate_output >>
    save_to_storage
)

# Complete pipeline: ingest → process → output
complete_workflow = (
    ingest_workflow >>
    process_workflow >>
    output_workflow
)
```

---

## Sequential with Branching

### Conditional Sequential Steps

```python
from tta_dev_primitives import ConditionalPrimitive

async def analyze_complexity(data: dict, context: WorkflowContext) -> dict:
    """Determine processing complexity."""
    complexity = calculate_complexity(data)
    return {**data, "complexity": complexity}

def is_complex(data: dict, context: WorkflowContext) -> bool:
    """Check if data is complex."""
    return data.get("complexity", 0) > 0.5

# Simple processing branch
simple_processing = (
    quick_validation >>
    fast_transform >>
    basic_output
)

# Complex processing branch
complex_processing = (
    thorough_validation >>
    advanced_transform >>
    detailed_output
)

# Conditional branching
conditional_step = ConditionalPrimitive(
    condition=is_complex,
    then_primitive=complex_processing,
    else_primitive=simple_processing
)

# Sequential workflow with branching
workflow = (
    analyze_complexity >>
    conditional_step >>
    finalize
)
```

---

## Sequential Caching Strategy

### Multi-Level Cache Pipeline

```python
from tta_dev_primitives.performance import CachePrimitive

# Cache at different stages
cached_embedding = CachePrimitive(
    primitive=generate_embedding,
    ttl_seconds=3600,  # 1 hour
    max_size=1000
)

cached_search = CachePrimitive(
    primitive=search_database,
    ttl_seconds=600,   # 10 minutes
    max_size=500
)

cached_generation = CachePrimitive(
    primitive=llm_generate,
    ttl_seconds=1800,  # 30 minutes
    max_size=200
)

# Sequential with caching at each stage
workflow = (
    preprocess >>
    cached_embedding >>
    cached_search >>
    cached_generation >>
    postprocess
)
```

**Cache Benefits:**
- Stage 1: 40% hit rate → 40% faster
- Stage 2: 60% hit rate → 60% faster
- Stage 3: 30% hit rate → 70% cost reduction

---

## Sequential Observability

### Traced Sequential Workflow

```python
from opentelemetry import trace
import structlog

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger(__name__)

async def traced_step1(data: dict, context: WorkflowContext) -> dict:
    """Step 1 with tracing."""
    logger.info("step1_start", correlation_id=context.correlation_id)

    # Processing happens here
    result = await process_step1(data)

    logger.info("step1_complete", duration_ms=elapsed)
    return result

async def traced_step2(data: dict, context: WorkflowContext) -> dict:
    """Step 2 with tracing."""
    logger.info("step2_start", correlation_id=context.correlation_id)

    result = await process_step2(data)

    logger.info("step2_complete", duration_ms=elapsed)
    return result

# Sequential workflow - automatic span creation
workflow = traced_step1 >> traced_step2 >> traced_step3

# Each step gets its own span in trace
result = await workflow.execute(data, context)
```

**Trace Structure:**
```
workflow.execute (parent span)
├─ traced_step1 (child span)
├─ traced_step2 (child span)
└─ traced_step3 (child span)
```

---

## Best Practices

### 1. Keep Steps Small and Focused

```python
# ✅ Good: Small, focused steps
workflow = (
    load_data >>
    validate >>
    transform >>
    save
)

# ❌ Bad: Large monolithic step
async def do_everything(data, context):
    # Load, validate, transform, save all in one
    pass
```

### 2. Use Descriptive Names

```python
# ✅ Good: Clear intent
extract_user_profile >>
enrich_with_preferences >>
generate_recommendations >>
format_response

# ❌ Bad: Generic names
step1 >> step2 >> step3 >> step4
```

### 3. Handle Errors at Right Level

```python
# ✅ Good: Error handling where needed
workflow = (
    validate_input >>  # Let validation errors propagate
    RetryPrimitive(external_api_call) >>  # Retry transient failures
    process_results  # Let processing errors propagate
)

# ❌ Bad: Catch-all error handling
try:
    result = await workflow.execute(data, context)
except Exception:
    return {}  # Too broad
```

### 4. Use Type Hints

```python
# ✅ Good: Clear types
async def process_text(data: dict, context: WorkflowContext) -> dict:
    """Process text data."""
    pass

# ❌ Bad: No types
async def process_text(data, context):
    pass
```

---

## Anti-Patterns

### ❌ Don't Break Sequential Chain

```python
# Bad: Breaking composition
workflow = step1 >> step2

async def broken_workflow(data, context):
    result1 = await workflow.execute(data, context)
    # Manual step breaks chain
    result2 = await some_other_step(result1)
    return result2

# Good: Keep everything composed
workflow = step1 >> step2 >> step3
```

### ❌ Don't Modify Shared State

```python
# Bad: Shared mutable state
shared_state = {}

async def bad_step(data, context):
    shared_state["count"] += 1  # Race conditions!
    return data

# Good: Use context
async def good_step(data, context):
    count = context.get("count", 0)
    context.set("count", count + 1)
    return data
```

### ❌ Don't Skip Error Handling

```python
# Bad: No error handling for critical steps
workflow = (
    load_data >>
    unreliable_api_call >>  # Might fail!
    save_results
)

# Good: Add resilience
workflow = (
    load_data >>
    RetryPrimitive(unreliable_api_call, max_retries=3) >>
    save_results
)
```

---

## Related Patterns

- [[TTA.dev/Patterns/Parallel Execution]] - Complement to sequential
- [[TTA.dev/Patterns/Caching]] - Optimization for sequential workflows
- [[TTA.dev/Patterns/Error Handling]] - Resilience in sequential flows

---

## Related Primitives

- [[SequentialPrimitive]] - Core sequential primitive
- [[RetryPrimitive]] - Add retry to sequential steps
- [[CachePrimitive]] - Add caching to sequential steps
- [[ConditionalPrimitive]] - Branching in sequential flows

---

## Related Examples

- [[TTA.dev/Examples/Basic Workflow]] - Simple sequential examples
- [[TTA.dev/Examples/RAG Workflow]] - RAG with sequential pattern
- [[TTA.dev/Examples/Multi-Agent Workflow]] - Sequential coordination

---

**Category:** Workflow Pattern
**Complexity:** Beginner to Intermediate
**Status:** Production-ready

- [[Project Hub]]