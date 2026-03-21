---
category: directives
date: 2026-03-20
component: model-strategy
severity: critical
tags: [directive, llm, openrouter, ollama, free-models]
---
# Directive: LLM Provider Strategy

## For TTA.dev apps (end-user facing)

Provider hierarchy — always use `get_llm_client()`, never hardcode:
1. **Ollama** (default, zero config) — `qwen2.5:7b`, CPU-only homelab compatible
2. **OpenRouter :free** (if `OPENROUTER_API_KEY` set) — gemma-3n → mistral-small → gpt-oss-20b
3. **Paid models** (if paid key set) — user's choice

## For building TTA.dev itself

Paid models (Claude, Copilot, Augment) — developer's own keys. Quality matters most here.

## KNOWN BAD MODEL — never use as default

`nvidia/nemotron-3-super-120b-a12b:free` is reasoning-only — returns `content: null`.
Any pipeline reading `response.content` will get None and crash. Confirmed broken 2026-03-19.

## Free-model amplifier (platform's job)

TTA.dev makes free models work well via: structured prompting in AgentSpec,
RetryPrimitive + FallbackPrimitive for quality-gate retry, CachePrimitive for context
economy, QualityGate for silent retry on weak output.

---
**Created:** 2026-03-20
**Verified:** [x] Yes
