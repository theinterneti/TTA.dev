# Auto PR Reviewer

An example **agentic application** built with [TTA.dev](https://tta.dev) primitives.
It fetches a GitHub PR diff and generates a structured code review using an LLM — all
orchestrated through composable, observable workflow primitives.

---

## What It Does

```
User provides PR URL
  ↓
CachePrimitive[fetch_pr_diff]          — fetches diff via `gh pr diff` (cached per-PR)
  ↓
LambdaPrimitive[prepare_request]       — builds LLMRequest from diff dict
  ↓
RetryPrimitive[LiteLLMPrimitive]       — calls LLM with automatic retry on rate limits
  ↓
LambdaPrimitive[format_review]         — formats LLMResponse → human-readable output
```

Each step is a `WorkflowPrimitive` chained with the `>>` operator.  No manual loops,
no scattered try/except — the primitives handle it.

---

## Primitives Used — and WHY

### `LambdaPrimitive`

**What it is:** Wraps any async (or sync) function as a typed workflow step.

**Why it was chosen:** `fetch_pr_diff` and `format_review` are plain async functions.
`LambdaPrimitive` makes them first-class participants in the workflow chain without
requiring a full `WorkflowPrimitive` subclass.  The `>>` operator then composes them
naturally.

```python
fetch = LambdaPrimitive(fetch_pr_diff)       # str → dict
format_output = LambdaPrimitive(format_review)  # LLMResponse → str
```

### `CachePrimitive`

**What it is:** Caches the result of any wrapped primitive, keyed on a user-defined
function of the input.

**Why it was chosen:** Fetching a PR diff is a network call (`gh pr diff`).  During
development and testing you often run the reviewer multiple times on the same PR.
`CachePrimitive` avoids redundant CLI invocations by storing the diff for one hour.

```python
cached_fetch = CachePrimitive(
    fetch,
    cache_key_fn=lambda url, _ctx: f"pr-diff:{url}",
    ttl_seconds=3600.0,
)
```

Cache hit rates of 60–80 % are common in practice, reducing both latency and
API-rate-limit pressure.

### `RetryPrimitive`

**What it is:** Wraps any primitive and retries it up to *N* times on failure, with
configurable exponential back-off and jitter.

**Why it was chosen:** LLM providers return `429 Rate-Limit` errors under load.
Without retry logic the reviewer crashes; with `RetryPrimitive` it waits a moment and
tries again transparently.

```python
retry_llm = RetryPrimitive(
    llm,
    strategy=RetryStrategy(max_retries=3, backoff_base=2.0),
)
```

Back-off delay is `min(2^attempt, 60) × jitter`, so three retries stay within a
reasonable wait window.

### `LiteLLMPrimitive`

**What it is:** The **primary LLM execution path** in TTA.dev.  Uses
[`litellm.acompletion()`](https://docs.litellm.ai) under the hood, giving access to
100+ providers through a single unified interface.

**Why it was chosen:** A single primitive works with Groq, Anthropic, OpenAI, OpenRouter,
Ollama, and more — just change the model string.  No provider-specific code, no
switching costs.

```python
llm = LiteLLMPrimitive()   # stateless; model carried in LLMRequest
request = LLMRequest(
    model="groq/llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
        {"role": "user", "content": diff_text},
    ],
    temperature=0.2,
    max_tokens=2048,
)
```

`LiteLLMPrimitive` automatically emits **OTel spans** (`gen_ai.litellm.<provider>.invoke`)
when `opentelemetry` is installed.

---

## Quick Start

### Prerequisites

```bash
# GitHub CLI (for fetching PR diffs)
brew install gh       # macOS
sudo apt install gh   # Debian/Ubuntu

gh auth login

# At least one LLM API key
export GROQ_API_KEY=gsk_...          # fastest free tier
# or
export ANTHROPIC_API_KEY=sk-ant-...
# or
export OPENAI_API_KEY=sk-...

# Optional: local Ollama (no API key needed)
# ollama pull qwen2.5:7b
```

### Run

```bash
# Full PR URL
python examples/auto_pr_reviewer/main.py --pr https://github.com/owner/repo/pull/42

# Short form with repo flag
python examples/auto_pr_reviewer/main.py --pr 42 --repo owner/repo

# Override model
python examples/auto_pr_reviewer/main.py \
    --pr https://github.com/owner/repo/pull/42 \
    --model anthropic/claude-3-5-haiku-20241022

# Local model (no API key required)
python examples/auto_pr_reviewer/main.py \
    --pr 42 --repo owner/repo \
    --model ollama/qwen2.5:7b
```

### Model fallback

When no cloud API key is set, the reviewer automatically falls back to
`ollama/qwen2.5:7b`.  This requires a running Ollama daemon but costs nothing.

---

## OTel Span Tree

When `opentelemetry-sdk` and an exporter are installed, every workflow execution
produces a full span tree.  Example with the OTLP exporter (Jaeger, Grafana Tempo, etc.):

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc

python examples/auto_pr_reviewer/main.py --pr 42 --repo owner/repo
```

Span tree (visible in Jaeger UI or TTA.dev dashboard at http://localhost:8000):

```
auto-pr-review                                          [root trace]
  ├── auto_pr_reviewer.fetch_pr_diff                   [LambdaPrimitive → gh CLI]
  └── gen_ai.litellm.groq.invoke                       [LiteLLMPrimitive]
        gen_ai.request.model  = groq/llama-3.3-70b-versatile
        gen_ai.usage.prompt_tokens   = 1842
        gen_ai.usage.completion_tokens = 391
```

> **Cache hit:** When the same PR URL is submitted again within the TTL window,
> the `fetch_pr_diff` span is skipped entirely — the diff is served from the
> in-memory cache.

---

## Running the Tests

```bash
uv run pytest tests/unit/test_example_auto_pr_reviewer.py -v
```

Tests use `MockPrimitive` for the LLM step and `unittest.mock.patch` for the
`gh` CLI call — no real network calls, no API keys needed.

---

## Project Structure

```
examples/auto_pr_reviewer/
├── __init__.py
├── main.py          ← workflow implementation + CLI entrypoint
└── README.md        ← this file

tests/unit/
└── test_example_auto_pr_reviewer.py
```
