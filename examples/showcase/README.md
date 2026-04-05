# Smart Code Reviewer

> A TTA.dev showcase: parallel static analysis + resilient multi-provider LLM review in one pipeline.

## What This Demonstrates

| Primitive | Role in this app |
|---|---|
| `ParallelPrimitive` | Runs `SecurityAgent` and `QAAgent` concurrently — zero waiting for independent work |
| `SmartRouterPrimitive` | Cascades through live LLM providers (Groq → Google → OpenRouter → Ollama) based on available API keys |
| `RetryPrimitive` | Retries the LLM call up to 3 times with exponential back-off on transient errors |
| `FallbackPrimitive` | Catches all failures and falls back to `MockLLMPrimitive`, so CI always succeeds |
| `MockLLMPrimitive` | Deterministic stub — no API key, no network, fully offline |

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Input: Python source file           │
└───────────────────────┬─────────────────────────┘
                        │
             ┌──────────▼──────────┐
             │  ParallelPrimitive  │
             └──────┬──────────┬───┘
                    │          │
         ┌──────────▼──┐  ┌────▼──────────┐
         │ SecurityAgent│  │   QAAgent     │
         │ (regex-based)│  │  (AST-based)  │
         │  • secrets   │  │  • docstrings │
         │  • eval/exec │  │  • type hints │
         │  • SQL inject│  │  • line length│
         └──────────┬───┘  └────┬──────────┘
                    └─────┬─────┘
                          │ static findings
             ┌────────────▼────────────────────────┐
             │         FallbackPrimitive            │
             │  ┌──────────────────────────────┐   │
             │  │       RetryPrimitive (3×)    │   │
             │  │  ┌────────────────────────┐  │   │
             │  │  │  SmartRouterPrimitive  │  │   │
             │  │  │  Groq  →  Google       │  │   │
             │  │  │  OpenRouter → Ollama   │  │   │
             │  │  └────────────────────────┘  │   │
             │  └──────────────────────────────┘   │
             │           ↓ on all failures          │
             │       MockLLMPrimitive               │
             └─────────────────┬───────────────────┘
                               │
             ┌─────────────────▼───────────────────┐
             │   Markdown report → stdout / JSON    │
             └─────────────────────────────────────┘
```

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- API keys are **optional** — `--mock` works with no configuration

## Usage

### Offline / CI (no API key needed)

```bash
uv run python -m examples.showcase.main path/to/file.py --mock
```

### Live LLM review (uses first available key — see table below)

```bash
uv run python -m examples.showcase.main path/to/file.py
```

### JSON output (pipe-friendly)

```bash
uv run python -m examples.showcase.main path/to/file.py --json
```

## Environment Variables

Set any of these to enable the corresponding LLM provider. The router tries them in order and falls back to local Ollama (no key required) or `MockLLM`.

| Variable | Provider | Notes |
|---|---|---|
| `GROQ_API_KEY` | Groq | Fastest; recommended for interactive use |
| `GOOGLE_API_KEY` | Google Gemini | High context window |
| `OPENROUTER_API_KEY` | OpenRouter | Access to many models via one key |

Ollama is always the last live provider — install it at <https://ollama.com> and pull a model (e.g. `ollama pull llama3`).

## Extending

### Add a new static agent

1. Create `examples/showcase/agents/my_agent.py` with a class that subclasses `WorkflowPrimitive[str, str]`.
2. Implement `async def execute(self, input_data: str, context: WorkflowContext) -> str`.
3. Add it to the `ParallelPrimitive` list in `main.py` and include its result in `_render_markdown`.

### Swap the LLM

Replace `SmartRouterPrimitive.make()` in `router.py` with any `WorkflowPrimitive[str, str]` —
the `RetryPrimitive` and `FallbackPrimitive` wrappers remain unchanged.
