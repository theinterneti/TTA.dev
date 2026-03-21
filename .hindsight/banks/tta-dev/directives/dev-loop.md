---
category: directives
date: 2026-03-20
component: dev-loop
severity: critical
tags: [directive, dev-loop, orient, recall, validate, retain]
---
# Directive: The DevelopmentCycle Loop

Every non-trivial task follows five steps in order. This is mandatory, not optional.

## The Loop

1. **Orient** (CGC) — before touching any file, call `mcp__codegraphcontext__find_code`
   and `mcp__codegraphcontext__analyze_code_relationships` on the target. Understand callers,
   dependencies, complexity, and which tests cover the target.

2. **Recall** (Hindsight) — call `mcp__hindsight__recall` with a query about the target
   module or task type. Pull relevant decisions, patterns, and failures before writing.

3. **Write** — produce code, plans, or output grounded by Orient + Recall context.
   Use `get_llm_client()` for any LLM call — never hardcode a model or provider.

4. **Validate** (E2B) — for new or changed Python code, run the affected tests inside
   an E2B sandbox using `CodeExecutionPrimitive` before committing. If E2B is unavailable,
   fall back to `uv run pytest` locally but note the deviation.

5. **Retain** (Hindsight) — after each task, call `mcp__hindsight__retain` with:
   - Any decision made and its rationale
   - Any pattern used for the first time
   - Any failure encountered and why it happened

## What counts as "non-trivial"

Trivial (skip Orient): fixing a typo, updating a comment, changing a string literal.
Non-trivial (run Orient): adding/changing any function, class, import, or config value.

---
**Created:** 2026-03-20
**Verified:** [x] Yes
