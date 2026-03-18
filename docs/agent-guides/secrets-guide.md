# Secrets Management Guide

## The Standard Pattern

TTA.dev uses `.env` files loaded automatically by `uv run`. This is the correct approach for solo/small-team development.

```bash
# .env (never committed — in .gitignore)
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
OPENROUTER_API_KEY=sk-or-...
```

Copy `.env.example` to `.env` and fill in your keys. `uv run` loads it automatically — no extra setup needed.

## Rules

1. **Never commit `.env`** — it's in `.gitignore`. Verify with `git status` before committing.
2. **Never log secret values** — log key names only (e.g. `"ANTHROPIC_API_KEY is set"`).
3. **Never hardcode keys in source** — always read from environment.
4. **Use `.env.example`** as the canonical list of required keys, with placeholder values.

## Reading Secrets in Code

```python
import os

# Optional key — returns None if not set
api_key = os.environ.get("ANTHROPIC_API_KEY")

# Required key — raises clearly if missing
api_key = os.environ["ANTHROPIC_API_KEY"]
```

That's it. No secrets management library needed for local development.

## Upgrading: 1Password CLI

If you use 1Password, you can eliminate the paste step entirely. Store keys in 1Password, then inject them at runtime without an `.env` file:

```bash
# Install: https://developer.1password.com/docs/cli/get-started/
op run --env-file=.env.template -- uv run python my_script.py
```

Where `.env.template` contains 1Password references instead of values:

```bash
# .env.template (safe to commit)
ANTHROPIC_API_KEY=op://Private/Anthropic/credential
GOOGLE_API_KEY=op://Private/Google AI Studio/credential
```

Keys are injected directly from 1Password at runtime — nothing touches disk.

## What NOT to Do

- Don't build a secrets manager class for local development — `os.environ` is sufficient.
- Don't use HashiCorp Vault unless you're running multi-service production infrastructure.
- Don't store secrets in code, config files, or git history.

## For AI Agents

When writing code that needs API keys:

1. Read from `os.environ.get("KEY_NAME")` — never hardcode.
2. Check `.env.example` for the canonical list of available keys.
3. Document any new keys you need in `.env.example` with a placeholder.
4. Fail loudly with a clear message if a required key is missing.
