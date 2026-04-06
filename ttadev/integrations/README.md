# ttadev/integrations

**Auth utilities and CRUD helpers for TTA.dev**

> ⚠️ **Looking for LLM integrations (Ollama, Groq, OpenRouter, etc.)?**
> They live in **`ttadev/primitives/integrations/`** — see the
> [LLM Primitives section](#-llm-integrations-the-real-ones) below.

---

## 📂 What lives where

| Path | What it is | Import path |
|------|-----------|-------------|
| `ttadev/integrations/` | Auth utilities and CRUD helpers (this directory) | `from ttadev.integrations import ...` |
| `ttadev/primitives/integrations/` | ✅ **Working LLM primitives** (Ollama, Groq, OpenRouter, …) | `from ttadev.primitives.integrations import ...` |

---

## ✅ What `ttadev/integrations/` provides

This directory contains **fully working** auth and database utilities with
**zero external dependencies**:

### Auth (`ttadev/integrations/auth/`)

| Module | Exports | Description |
|--------|---------|-------------|
| `auth/api_key.py` | `generate_api_key`, `verify_api_key`, `ApiKey`, `ApiKeyStore` | SHA-256–hashed API key lifecycle |
| `auth/session.py` | `create_session`, `verify_session`, `SessionToken`, `SessionPayload` | HMAC-signed stateless session tokens |

### Database (`ttadev/integrations/db/`)

| Module | Exports | Description |
|--------|---------|-------------|
| `db/crud.py` | `AsyncCRUDStore[T]` | Generic async CRUD store (in-memory, DB-swappable) |

### Quick start

```python
from ttadev.integrations import (
    generate_api_key,
    ApiKeyStore,
    create_session,
    verify_session,
    AsyncCRUDStore,
)

# API key lifecycle
plaintext, record = generate_api_key(scopes=["read", "write"])
store = ApiKeyStore()
store.store(record)
assert store.is_valid(plaintext)
store.revoke(record.key_id)

# Session tokens (HMAC-signed, no external JWT library required)
token = create_session(user_id="u_123", scopes=["admin"], secret_key="s3cr3t")
payload = verify_session(token.token, secret_key="s3cr3t")

# Generic async CRUD store
from dataclasses import dataclass

@dataclass
class User:
    id: str
    name: str

users: AsyncCRUDStore[User] = AsyncCRUDStore()
# await users.create(User(id="1", name="Alice"))
# await users.get("1")
# await users.update("1", {"name": "Alicia"})
# await users.delete("1")
```

---

## 🚀 LLM Integrations — the real ones

All LLM provider primitives are **fully implemented** in
`ttadev/primitives/integrations/`. The table below reflects their actual
status as of the current codebase — none of them are stubs or futures.

| Provider | Class | Free Tier | Notes |
|----------|-------|-----------|-------|
| **Ollama** | `OllamaPrimitive` | ✅ Yes (local) | Wraps official `ollama` SDK |
| **Groq** | `GroqPrimitive` | ✅ Yes | Ultra-fast inference via `groq` SDK |
| **OpenRouter** | `OpenRouterPrimitive` | ⚠️ Varies | HTTP-based; no extra SDK needed |
| **OpenAI** | `OpenAIPrimitive` | ❌ Paid | Wraps `openai` SDK |
| **Anthropic** | `AnthropicPrimitive` | ❌ Paid | Wraps `anthropic` SDK |
| **Google AI Studio** | `GoogleAIStudioPrimitive` | ✅ Yes | Wraps `google-generativeai` SDK |
| **HuggingFace** | `HuggingFacePrimitive` | ✅ Yes | Inference API |
| **Together AI** | `TogetherAIPrimitive` | ⚠️ Varies | REST-based |
| **Supabase** | `SupabasePrimitive` | ✅ Yes | Wraps `supabase` SDK |
| **SQLite** | `SQLitePrimitive` | ✅ Yes | Wraps `aiosqlite` |
| **E2B** | `E2BPrimitive`, `CodeExecutionPrimitive` | ⚠️ Trial | Sandbox code execution |
| **LangGraph** | `LangGraphPrimitive` | ✅ Yes | Wraps `langgraph` |

### Correct import path

```python
# ✅ Correct — use this
from ttadev.primitives.integrations import (
    OllamaPrimitive,
    GroqPrimitive,
    OpenRouterPrimitive,
    OpenAIPrimitive,
    AnthropicPrimitive,
    GoogleAIStudioPrimitive,
    HuggingFacePrimitive,
    TogetherAIPrimitive,
    SupabasePrimitive,
    SQLitePrimitive,
)

# ❌ Wrong — ttadev.integrations only has auth/CRUD helpers
# from ttadev.integrations import OllamaPrimitive  # ImportError
```

### Usage examples

```python
import asyncio
from ttadev.primitives.integrations import OllamaPrimitive, GroqPrimitive, OpenRouterPrimitive
from ttadev.primitives.integrations.ollama_primitive import OllamaRequest
from ttadev.primitives.integrations.groq_primitive import GroqRequest
from ttadev.primitives.integrations.openrouter_primitive import OpenRouterRequest
from ttadev.primitives.core.base import WorkflowContext

ctx = WorkflowContext()

# Ollama — local, free, no API key required
ollama = OllamaPrimitive(model="llama3.2")
response = await ollama.execute(
    OllamaRequest(messages=[{"role": "user", "content": "Hello!"}]), ctx
)

# Groq — fast cloud inference, free tier available
groq = GroqPrimitive(model="llama-3.3-70b-versatile", api_key="gsk_...")
response = await groq.execute(
    GroqRequest(messages=[{"role": "user", "content": "Hello!"}]), ctx
)

# OpenRouter — route to free flagship models
router = OpenRouterPrimitive(model="deepseek/deepseek-r1", api_key="sk-or-...")
response = await router.execute(
    OpenRouterRequest(messages=[{"role": "user", "content": "Hello!"}]), ctx
)
```

### Composing with other primitives

```python
from ttadev.primitives import CachePrimitive, RetryPrimitive
from ttadev.primitives.integrations import GroqPrimitive

# Cache + Retry + Groq
workflow = (
    CachePrimitive(ttl=3600) >>   # 1-hour response cache
    RetryPrimitive(max_attempts=3) >>
    GroqPrimitive(model="llama-3.3-70b-versatile")
)
```

---

## 🏗️ Architecture

All LLM integration primitives in `ttadev/primitives/integrations/`:

1. **Inherit from `WorkflowPrimitive`** — automatic observability, type-safe interfaces
2. **Use Pydantic request/response models** — validated at runtime
3. **Read credentials from environment variables by default** — pass explicitly or set env vars
4. **Degrade gracefully** when optional SDK is not installed — clear `ImportError` with install hint

```python
class SomePrimitive(WorkflowPrimitive[RequestModel, ResponseModel]):
    async def _execute_impl(
        self,
        input_data: RequestModel,
        context: WorkflowContext,
    ) -> ResponseModel:
        # Implementation
        ...
```

---

## 📦 Directory structure

```
ttadev/integrations/          ← YOU ARE HERE (auth/CRUD helpers)
├── __init__.py               # Exports auth + CRUD utilities
├── auth/
│   ├── api_key.py            # ✅ API key generation, hashing, verification
│   └── session.py            # ✅ HMAC-signed session tokens
└── db/
    └── crud.py               # ✅ Generic async CRUD store

ttadev/primitives/integrations/   ← WORKING LLM PRIMITIVES
├── __init__.py               # Public API for all providers
├── ollama_primitive.py       # ✅ Ollama (local models)
├── groq_primitive.py         # ✅ Groq (fast cloud inference)
├── openrouter_primitive.py   # ✅ OpenRouter (multi-provider routing)
├── openai_primitive.py       # ✅ OpenAI
├── anthropic_primitive.py    # ✅ Anthropic
├── google_ai_studio_primitive.py  # ✅ Google AI Studio / Gemini
├── huggingface_primitive.py  # ✅ HuggingFace Inference API
├── together_ai_primitive.py  # ✅ Together AI
├── sqlite_primitive.py       # ✅ SQLite (aiosqlite)
├── supabase_primitive.py     # ✅ Supabase
├── e2b_primitive.py          # ✅ E2B code execution sandboxes
└── langgraph_primitive.py    # ✅ LangGraph
```

---

## 🔗 Related Documentation

- **Primitives catalog**: [`PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md)
- **TTA.dev Core**: [`ttadev/primitives/README.md`](../primitives/README.md)
- **Vibe Coder Guide**: [`docs/guides/VIBE_CODER_QUICKSTART.md`](../../docs/guides/VIBE_CODER_QUICKSTART.md)
- **Model router**: [`ttadev/primitives/llm/`](../primitives/llm/) (`ModelRouterPrimitive`)

---

## 📞 Support

- **Issues**: https://github.com/theinterneti/TTA.dev/issues
- **Discussions**: https://github.com/theinterneti/TTA.dev/discussions

---

**License**: See LICENSE file
