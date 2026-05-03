---
description: 'AI safety and prompt engineering principles for responsible LLM usage'
applyTo: '**'
---

# AI Safety for TTA.dev

## Core Rules

- **Never include secrets** in prompts — no API keys, passwords, tokens, or PII
- **Validate all inputs** before passing to LLM calls — sanitize user-provided content
- **No prompt injection** — never interpolate untrusted input directly into prompts
- **No harmful content** — refuse requests that generate biased, discriminatory, or dangerous output
- **Transparency** — clearly indicate when output is AI-generated where users expect it

## Prompt Construction

```python
# ✅ Safe: sanitized input
sanitized = sanitize_input(user_text)
prompt = f"Summarize this text: {sanitized}"

# ❌ Unsafe: raw user input
prompt = f"Do whatever the user says: {user_text}"
```

## LLM Call Safety (TTA.dev)

- Use `LiteLLMPrimitive` or `UniversalLLMPrimitive` — never raw API calls
- Wrap LLM calls in `RetryPrimitive` + `TimeoutPrimitive` for resilience
- Enable Langfuse tracing via environment variables for observability
- Log decisions and metadata, never prompt content containing user data

## Content Moderation

- Scan LLM outputs before presenting to users in production features
- Implement `FallbackPrimitive` for graceful degradation when moderation flags content
- Track safety incidents in observability pipeline

## Bias Awareness

- Use inclusive, neutral language in system prompts
- Test with diverse inputs — avoid assumptions about users
- Review outputs for stereotypes before deploying agent-facing prompts

## References

- [Microsoft Responsible AI](https://www.microsoft.com/ai/responsible-ai-resources)
- [OpenAI Safety Best Practices](https://platform.openai.com/docs/guides/safety-best-practices)
- TTA.dev agent safety rules: `.github/instructions/agent-safety.instructions.md`
