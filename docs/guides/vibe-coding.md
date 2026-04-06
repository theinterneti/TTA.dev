# ⚡ Vibe Coding with TTA.dev

**Build AI-native workflows quickly, without pretending the whole platform is already finished.**

TTA.dev is aimed at developers using AI agents to build software rapidly. The honest March 2026
story is:

- there is a real core here
- the repository is still aspirational overall
- the safest way to use it today is to start from the verified proof path, then build outward

---

## 🚀 The Vibe Coding Workflow

1. **Idea**: You have a workflow or agent concept you want to explore.
2. **Agent**: You point your coding agent at this repository and its current instructions.
3. **Primitives**: You compose with the existing `ttadev.primitives` building blocks.
4. **Verify**: You confirm the current proof path and only then expand into your own experiments.

## 🛠️ Why TTA.dev for Vibe Coding?

Your AI agent is smart, but it can still write brittle code. TTA.dev helps by giving it reusable
patterns:

- **Don't write retry loops.** Use `RetryPrimitive`.
- **Don't write caching logic.** Use `CachePrimitive`.
- **Don't guess at context flow.** Use `WorkflowContext`.
- **Don't start from stale demos.** Prefer the currently verified observability path first.

## 🏁 Start from the verified path, not missing templates

Some older docs referenced starter templates under `templates/`, but those paths are not the current
reliable entrypoint in this repository.

Instead, ask your agent to:
> "Use `GETTING_STARTED.md`, `QUICKSTART.md`, and `PRIMITIVES_CATALOG.md` as the source of truth,
> then help me build a small workflow with the current `ttadev.primitives` API."

Good first targets:

### 1. A small resilient workflow
- **Best for:** API calls, ingestion steps, simple automations
- **Use:** `LambdaPrimitive`, `RetryPrimitive`, `TimeoutPrimitive`, `CachePrimitive`

### 2. A multi-step traceable pipeline
- **Best for:** content processing, staged transformations, experiments
- **Use:** `SequentialPrimitive`, `ParallelPrimitive`, `WorkflowContext`

## 🔑 BYO Key Configuration

TTA.dev is still evolving here. Bring your own provider configuration if your experiment needs it,
but do not assume a fully standardized multi-provider app scaffold already exists in this repo.

1.  Create a `.env` file:
    ```bash
    OPENAI_API_KEY=sk-...
    OPENROUTER_API_KEY=sk-or-...
    ```
2. Your agent can read that file, but the repository's most verified path today is still the local
   observability workflow rather than a polished provider-integration template.

## 🤖 Instructions for Your Agent

Copy this into your agent's context (or `.clinerules`):

```markdown
You are a Vibe Coding expert using TTA.dev.
1. ALWAYS prefer TTA primitives over custom logic for: retries, caching, routing, and parallelism.
2. START from `GETTING_STARTED.md` and `QUICKSTART.md`, not from stale historical demos.
3. KEEP it simple. Use `uv` for dependency management.
4. FOCUS on the "Happy Path" first, then add `FallbackPrimitive` for robustness.
```

---

## What this document should mean today

This file is a mindset note, not proof that every end-to-end TTA.dev story is already complete.
For current commands and working examples, prefer:

- [`README.md`](README.md)
- [`GETTING_STARTED.md`](GETTING_STARTED.md)
- [`QUICKSTART.md`](QUICKSTART.md)
- [`AGENTS.md`](AGENTS.md)

**Ready to vibe?** Start there.
