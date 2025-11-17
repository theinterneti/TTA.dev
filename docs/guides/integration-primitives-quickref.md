# Integration Primitives Quick Reference

**One-page cheat sheet for all 5 TTA.dev integration primitives**

---

## 📦 Available Primitives

| Primitive | Purpose | Type | Setup |
|-----------|---------|------|-------|
| **OpenAIPrimitive** | OpenAI GPT models | LLM | API key |
| **AnthropicPrimitive** | Anthropic Claude models | LLM | API key |
| **OllamaPrimitive** | Local LLMs (Llama, etc.) | LLM | Local install |
| **SupabasePrimitive** | Cloud PostgreSQL database | Database | API key |
| **SQLitePrimitive** | Local SQLite database | Database | None |

---

## 🚀 Quick Start

### Installation

```bash
# Install with integration extras
cd platform/primitives
uv sync --extra integrations
```

### Import

```python
from tta_dev_primitives.integrations import (
    OpenAIPrimitive,
    AnthropicPrimitive,
    OllamaPrimitive,
    SupabasePrimitive,
    SQLitePrimitive,
)
from tta_dev_primitives.core.base import WorkflowContext
```

---

## 💬 LLM Primitives

### OpenAIPrimitive

```python
# Setup
llm = OpenAIPrimitive(
    api_key="sk-...",
    model="gpt-4o-mini"  # or "gpt-4o", "gpt-4"
)

# Execute
from tta_dev_primitives.integrations import OpenAIRequest

request = OpenAIRequest(
    messages=[
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,
    max_tokens=1000
)

context = WorkflowContext(workflow_id="chat")
response = await llm.execute(request, context)
print(response.content)  # "Hello! How can I help you?"
```

**When to use:** Production apps, cost-effective, fast  
**Cost:** $0.15-$15 per 1M tokens  
**Docs:** [OpenAI Primitive](../../platform/primitives/src/tta_dev_primitives/integrations/openai_primitive.py)

---

### AnthropicPrimitive

```python
# Setup
llm = AnthropicPrimitive(
    api_key="sk-ant-...",
    model="claude-3-5-sonnet-20241022"
)

# Execute
from tta_dev_primitives.integrations import AnthropicRequest

request = AnthropicRequest(
    messages=[
        {"role": "user", "content": "Explain quantum computing"}
    ],
    system="You are a physics teacher.",
    max_tokens=1000
)

context = WorkflowContext(workflow_id="explain")
response = await llm.execute(request, context)
print(response.content)
```

**When to use:** Long context (200K tokens), safety-critical, complex reasoning  
**Cost:** $3-$15 per 1M tokens  
**Docs:** [Anthropic Primitive](../../platform/primitives/src/tta_dev_primitives/integrations/anthropic_primitive.py)

---

### OllamaPrimitive

```python
# Setup (requires Ollama installed locally)
llm = OllamaPrimitive(
    model="llama3.2",
    host="http://localhost:11434"
)

# Execute
from tta_dev_primitives.integrations import OllamaRequest

request = OllamaRequest(
    messages=[
        {"role": "user", "content": "Write a haiku"}
    ],
    temperature=0.8
)

context = WorkflowContext(workflow_id="poetry")
response = await llm.execute(request, context)
print(response.content)
```

**When to use:** Privacy-critical, offline, cost-free  
**Cost:** $0 (free)  
**Docs:** [Ollama Primitive](../../platform/primitives/src/tta_dev_primitives/integrations/ollama_primitive.py)

---

## 🗄️ Database Primitives

### SupabasePrimitive

```python
# Setup
db = SupabasePrimitive(
    url="https://xxx.supabase.co",
    key="eyJhbGc..."
)

# SELECT
from tta_dev_primitives.integrations import SupabaseRequest

request = SupabaseRequest(
    operation="select",
    table="users",
    filters={"age": {"gte": 18}},
    columns="id,name,email"
)

context = WorkflowContext(workflow_id="query")
response = await db.execute(request, context)
print(response.data)  # [{"id": 1, "name": "Alice", ...}]

# INSERT
insert_request = SupabaseRequest(
    operation="insert",
    table="users",
    data={"name": "Bob", "age": 25}
)
await db.execute(insert_request, context)

# UPDATE
update_request = SupabaseRequest(
    operation="update",
    table="users",
    data={"age": 26},
    filters={"id": {"eq": 1}}
)
await db.execute(update_request, context)

# DELETE
delete_request = SupabaseRequest(
    operation="delete",
    table="users",
    filters={"id": {"eq": 1}}
)
await db.execute(delete_request, context)
```

**When to use:** Multi-user apps, cloud deployment, real-time  
**Cost:** Free tier → $25/month  
**Docs:** [Supabase Primitive](../../platform/primitives/src/tta_dev_primitives/integrations/supabase_primitive.py)

---

### SQLitePrimitive

```python
# Setup
db = SQLitePrimitive(database="app.db")  # or ":memory:"

# CREATE TABLE
from tta_dev_primitives.integrations import SQLiteRequest

create_request = SQLiteRequest(
    query="""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        age INTEGER
    )
    """,
    fetch="none"
)

context = WorkflowContext(workflow_id="setup")
await db.execute(create_request, context)

# INSERT
insert_request = SQLiteRequest(
    query="INSERT INTO users (name, age) VALUES (?, ?)",
    parameters=("Alice", 25),
    fetch="none"
)
response = await db.execute(insert_request, context)
print(response.lastrowid)  # 1

# SELECT ALL
select_request = SQLiteRequest(
    query="SELECT * FROM users WHERE age > ?",
    parameters=(18,),
    fetch="all"
)
response = await db.execute(select_request, context)
print(response.data)  # [{"id": 1, "name": "Alice", "age": 25}]

# SELECT ONE
select_one = SQLiteRequest(
    query="SELECT * FROM users WHERE id = ?",
    parameters=(1,),
    fetch="one"
)
response = await db.execute(select_one, context)
print(response.data)  # {"id": 1, "name": "Alice", "age": 25}

# UPDATE
update_request = SQLiteRequest(
    query="UPDATE users SET age = ? WHERE id = ?",
    parameters=(26, 1),
    fetch="none"
)
await db.execute(update_request, context)

# DELETE
delete_request = SQLiteRequest(
    query="DELETE FROM users WHERE id = ?",
    parameters=(1,),
    fetch="none"
)
await db.execute(delete_request, context)
```

**When to use:** Local apps, prototyping, single-user  
**Cost:** $0 (free)  
**Docs:** [SQLite Primitive](../../platform/primitives/src/tta_dev_primitives/integrations/sqlite_primitive.py)

---

## 🔗 Composition Patterns

### Sequential LLM + Database

```python
from tta_dev_primitives import SequentialPrimitive

# Generate content → Save to database
workflow = (
    OpenAIPrimitive(api_key="...") >>
    SQLitePrimitive(database="content.db")
)
```

### Parallel Multi-LLM

```python
from tta_dev_primitives import ParallelPrimitive

# Query multiple LLMs simultaneously
workflow = (
    OpenAIPrimitive(api_key="...") |
    AnthropicPrimitive(api_key="...") |
    OllamaPrimitive()
)
```

### Router with Fallback

```python
from tta_dev_primitives import RouterPrimitive
from tta_dev_primitives.recovery import FallbackPrimitive

# Try OpenAI, fallback to Ollama if fails
primary = OpenAIPrimitive(api_key="...")
fallback = OllamaPrimitive()

workflow = FallbackPrimitive(primary=primary, fallback=fallback)
```

---

## 🎯 Decision Guides

### Which LLM?

- **Quality:** OpenAI GPT-4 or Anthropic Claude
- **Cost:** OpenAI GPT-4o-mini
- **Privacy:** Ollama
- **Long context:** Anthropic Claude (200K tokens)

**Full guide:** [LLM Selection Guide](llm-selection-guide.md)

### Which Database?

- **Multi-user:** Supabase
- **Local/prototype:** SQLite
- **Real-time:** Supabase
- **Privacy:** SQLite

**Full guide:** [Database Selection Guide](database-selection-guide.md)

---

## 📊 Comparison Table

| Primitive | Setup | Cost | Privacy | Speed | Best For |
|-----------|-------|------|---------|-------|----------|
| **OpenAI** | ⭐ Easy | 💰 Low | ⚠️ Cloud | ⚡ Fast | Production |
| **Anthropic** | ⭐ Easy | 💰 Medium | ⚠️ Cloud | ⚡ Fast | Complex tasks |
| **Ollama** | ⭐⭐⭐ Hard | 💰 Free | ✅ Local | ⚡ Slow | Privacy |
| **Supabase** | ⭐⭐ Medium | 💰 Free→Paid | ⚠️ Cloud | ⚡ Fast | Multi-user |
| **SQLite** | ⭐ Easy | 💰 Free | ✅ Local | ⚡ Fast | Single-user |

---

## 🔧 Common Patterns

### Environment Variables

```python
import os

# LLMs
openai_llm = OpenAIPrimitive(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_llm = AnthropicPrimitive(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Databases
supabase_db = SupabasePrimitive(
    url=os.getenv("SUPABASE_URL"),
    key=os.getenv("SUPABASE_KEY")
)
```

### Error Handling

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Retry LLM calls on failure
llm = RetryPrimitive(
    primitive=OpenAIPrimitive(api_key="..."),
    max_retries=3
)
```

### Caching

```python
from tta_dev_primitives.performance import CachePrimitive

# Cache expensive LLM calls
llm = CachePrimitive(
    primitive=OpenAIPrimitive(api_key="..."),
    ttl_seconds=3600  # 1 hour
)
```

---

## 📚 Related Documentation

- **Full Primitives Catalog:** [`PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md)
- **LLM Selection Guide:** [llm-selection-guide.md](llm-selection-guide.md)
- **Database Selection Guide:** [database-selection-guide.md](database-selection-guide.md)
- **Integration Tests:** [`platform/primitives/tests/test_integrations.py`](../../platform/primitives/tests/test_integrations.py)

---

**Last Updated:** October 30, 2025  
**For:** Quick reference (all skill levels)  
**Maintained by:** TTA.dev Team

