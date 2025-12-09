# ⚡ Vibe Coding with TTA.dev

**Build AI-native apps at the speed of thought.**

TTA.dev is designed for "Vibe Coders"—developers who use AI agents (like GitHub Copilot, Cline, or Cursor) to build software rapidly. We provide the **production-ready primitives** so your agent doesn't have to reinvent the wheel.

---

## 🚀 The Vibe Coding Workflow

1.  **Idea**: You have a concept for an AI app.
2.  **Agent**: You tell your AI agent (Copilot/Cline) what you want.
3.  **Primitives**: Your agent uses TTA.dev primitives to build it *right* the first time.
4.  **Deploy**: You ship a reliable, observable app.

## 🛠️ Why TTA.dev for Vibe Coding?

Your AI agent is smart, but it can write brittle code. TTA.dev gives it **superpowers**:

- **Don't write retry loops.** Use `RetryPrimitive`.
- **Don't write caching logic.** Use `CachePrimitive`.
- **Don't guess at observability.** Use `WorkflowContext` (it's built-in).
- **Don't worry about keys.** We handle BYO-Key (OpenRouter, OpenAI, etc.) patterns.

## 🏁 Quick Start Templates

Don't start from scratch. Ask your agent to:
> "Initialize a new TTA app using the Basic Agent template."

### 1. Basic Agent (`templates/basic-agent`)
A simple input/output agent with caching and retries.
- **Best for:** Simple tools, data processing, chatbots.
- **Includes:** `Router`, `Retry`, `Cache`.

### 2. Multi-Step Workflow (`templates/workflow`)
A sequential pipeline of operations.
- **Best for:** Content generation, data pipelines.
- **Includes:** `SequentialPrimitive`, `ParallelPrimitive`.

## 🔑 BYO Key Configuration

TTA.dev is model-agnostic. You bring the keys; we provide the plumbing.

1.  Create a `.env` file:
    ```bash
    OPENAI_API_KEY=sk-...
    OPENROUTER_API_KEY=sk-or-...
    ```
2.  Your agent knows how to read this. TTA primitives don't enforce a specific provider—they manage the *flow*.

## 🤖 Instructions for Your Agent

Copy this into your agent's context (or `.clinerules`):

```markdown
You are a Vibe Coding expert using TTA.dev.
1. ALWAYS prefer TTA primitives over custom logic for: retries, caching, routing, and parallelism.
2. START new projects by copying from `TTA.dev/templates/`.
3. KEEP it simple. Use `uv` for dependency management.
4. FOCUS on the "Happy Path" first, then add `FallbackPrimitive` for robustness.
```

---

**Ready to vibe?** Go to [`AGENTS.md`](AGENTS.md) for the full toolkit.
