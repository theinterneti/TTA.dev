# tta-dev-integrations

**Production-ready integration primitives for TTA.dev**

**Status:** 🎯 **STRATEGIC PIVOT** - Focus on free models + Cline integration

---

## 🎯 What is tta-dev-integrations?

Pre-built primitives for common AI application dependencies with **focus on FREE models and Cline integration**.

**Design Goal:** Enable vibe coders to build production apps in 30 minutes **without paying for API access**.

### 💡 Strategic Direction

**Key Insight:** Cline provides excellent integration with free model providers:
- **Google AI Studio + Gemini** - Free tier, nearly as effective as paid options
- **OpenRouter** - Aggregates multiple providers
- **HuggingFace** - Open source models

**Recommendation:** Use Cline as your LLM integration layer. TTA.dev provides:
- Database primitives (Supabase, PostgreSQL, SQLite)
- Auth primitives (Clerk, Auth0, JWT)
- Model selection guidance (free vs paid)
- Workflow orchestration with adaptive primitives

### Available Integrations

| Category | Provider | Status | Free Tier | Install |
|----------|----------|--------|-----------|---------|
| **LLM** | **Cline** (recommended) | ✅ Use directly | ✅ Yes | Built into VS Code |
| **LLM** | Google AI Studio + Gemini | ✅ Recommended | ✅ Yes | Via Cline |
| **LLM** | OpenRouter | ✅ Available | ⚠️ Varies | Via Cline |
| **LLM** | HuggingFace | ✅ Available | ✅ Yes | Via Cline |
| **LLM** | Ollama (Local) | 🚧 Future | ✅ Yes | Local install |
| **Database** | Supabase | ✅ Skeleton | ✅ Yes (generous) | `pip install 'tta-dev-integrations[supabase]'` |
| **Database** | PostgreSQL | 🚧 Planned | ⚠️ Varies | `pip install 'tta-dev-integrations[database]'` |
| **Database** | SQLite | 🚧 Planned | ✅ Yes | `pip install 'tta-dev-integrations[database]'` |
| **Auth** | Clerk | 🚧 Planned | ✅ Yes (10k users) | `pip install 'tta-dev-integrations[auth]'` |
| **Auth** | JWT | 🚧 Planned | ✅ Yes | `pip install 'tta-dev-integrations[auth]'` |

---

## 🚀 Quick Start

### Recommended Setup (100% Free)

**Prerequisites:**
- VS Code with Cline extension
- Google AI Studio API key (free from https://aistudio.google.com/)

**Architecture:**
```
Your App → TTA.dev Primitives → Cline → Google Gemini (Free)
                ↓
         Supabase (Free Tier)
```

### Installation

```bash
# Install database integration only
pip install 'tta-dev-integrations[supabase]'

# Or install all integrations
pip install 'tta-dev-integrations[all]'
```

### Using Cline for LLM Operations

**Instead of writing LLM primitives, use Cline directly:**

1. **Install Cline** in VS Code
2. **Configure Google AI Studio:**
   - Get free API key from https://aistudio.google.com/
   - Add to Cline settings
   - Select Gemini model (gemini-1.5-pro recommended)

3. **Use Cline in your workflow:**
   - Cline handles LLM requests
   - TTA.dev handles orchestration, caching, retry
   - Supabase handles data storage

**Why This Works:**
- ✅ Cline provides excellent multi-provider support
- ✅ Google Gemini free tier is generous
- ✅ No need to manage API keys in your app
- ✅ TTA.dev primitives handle workflow orchestration

#### Database Integration (Supabase)

```python
from tta_dev_integrations import SupabasePrimitive, DatabaseQuery

# Initialize
db = SupabasePrimitive(
    url="https://xxx.supabase.co",  # or use SUPABASE_URL env var
    key="eyJhbGc..."  # or use SUPABASE_KEY env var
)

# Query database
query = DatabaseQuery(
    query="SELECT * FROM users WHERE email = :email",
    params={"email": "user@example.com"}
)

result = await db.execute(query, context)
print(result.rows)
```

---

## 🏗️ Architecture

All integration primitives:

1. **Inherit from tta-dev-primitives base classes**
   - Automatic retry with exponential backoff
   - OpenTelemetry observability
   - Type-safe interfaces

2. **Follow consistent patterns**
   - Request/Response models with Pydantic
   - Environment variable defaults
   - Graceful degradation

3. **Compose with other primitives**
   ```python
   from tta_dev_primitives import CachePrimitive, RetryPrimitive

   # Cache + Retry + OpenAI
   workflow = (
       CachePrimitive(ttl=3600) >>  # 1 hour cache
       RetryPrimitive(max_attempts=3) >>
       OpenAIPrimitive(model="gpt-4")
   )
   ```

---

## 📦 Package Structure

```
tta-dev-integrations/
├── src/tta_dev_integrations/
│   ├── llm/                    # LLM integrations
│   │   ├── base.py             # ✅ Base class (complete)
│   │   ├── openai_primitive.py # ✅ OpenAI (skeleton)
│   │   ├── anthropic_primitive.py  # 🚧 Anthropic (TODO)
│   │   └── ollama_primitive.py     # 🚧 Ollama (TODO)
│   ├── database/               # Database integrations
│   │   ├── base.py             # ✅ Base class (complete)
│   │   ├── supabase_primitive.py   # ✅ Supabase (skeleton)
│   │   ├── postgresql_primitive.py # 🚧 PostgreSQL (TODO)
│   │   └── sqlite_primitive.py     # 🚧 SQLite (TODO)
│   └── auth/                   # Auth integrations
│       ├── base.py             # ✅ Base class (complete)
│       ├── clerk_primitive.py  # 🚧 Clerk (TODO)
│       ├── auth0_primitive.py  # 🚧 Auth0 (TODO)
│       └── jwt_primitive.py    # 🚧 JWT (TODO)
├── tests/                      # Test suite
├── examples/                   # Working examples
└── pyproject.toml              # ✅ Package config (complete)
```

### Completion Status

- ✅ **Infrastructure (100%)**: Package structure, base classes, pyproject.toml
- ✅ **OpenAI (40%)**: Skeleton with request/response flow
- ✅ **Supabase (40%)**: Skeleton with client initialization
- 🚧 **Other integrations (0%)**: Placeholder files only

---

## 🎓 Design Principles

### 1. Fail Gracefully

```python
# Optional dependencies with clear error messages
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Raise helpful error when used
if not OPENAI_AVAILABLE:
    raise ImportError(
        "OpenAI package not installed. "
        "Install with: pip install 'tta-dev-integrations[openai]'"
    )
```

### 2. Environment Variable Defaults

```python
# Convention: Provider credentials from env vars
llm = OpenAIPrimitive()  # Uses OPENAI_API_KEY env var
db = SupabasePrimitive()  # Uses SUPABASE_URL and SUPABASE_KEY

# Or pass explicitly
llm = OpenAIPrimitive(api_key="sk-...")
```

### 3. Consistent Interfaces

All primitives follow the same pattern:

```python
class SomePrimitive(BasePrimitive):
    async def _execute_impl(
        self,
        input_data: RequestModel,
        context: WorkflowContext
    ) -> ResponseModel:
        # Implementation
        pass
```

---

## 📝 Contributing

### Adding a New Integration

1. **Create primitive file**
   ```bash
   touch src/tta_dev_integrations/category/provider_primitive.py
   ```

2. **Inherit from base class**
   ```python
   from tta_dev_integrations.category.base import BasePrimitive

   class ProviderPrimitive(BasePrimitive):
       async def _execute_impl(self, input_data, context):
           # Your implementation
           pass
   ```

3. **Add optional dependency**
   ```toml
   # pyproject.toml
   [project.optional-dependencies]
   provider = ["provider-sdk>=1.0.0"]
   ```

4. **Update exports**
   ```python
   # src/tta_dev_integrations/__init__.py
   try:
       from tta_dev_integrations.category.provider_primitive import ProviderPrimitive
   except ImportError:
       ProviderPrimitive = None
   ```

5. **Add tests and examples**

### Testing

```bash
# Run tests
uv run pytest -v

# With specific integration
uv run pytest -v -k openai

# Integration tests (require credentials)
RUN_INTEGRATION=true uv run pytest -v -m integration
```

---

## 🎯 Roadmap

### Phase 1: Core LLM (Current)
- [x] Package infrastructure
- [x] OpenAI skeleton
- [ ] OpenAI full implementation
- [ ] Anthropic implementation
- [ ] Ollama implementation

### Phase 2: Database
- [x] Supabase skeleton
- [ ] Supabase full implementation
- [ ] PostgreSQL implementation
- [ ] SQLite implementation

### Phase 3: Auth
- [ ] Clerk implementation
- [ ] Auth0 implementation
- [ ] JWT implementation

### Phase 4: Advanced Features
- [ ] Streaming support for LLMs
- [ ] Connection pooling for databases
- [ ] Token refresh for auth
- [ ] Cost tracking and budgets
- [ ] Rate limiting primitives

---

## 💡 Examples

See `examples/` directory for complete working examples:

- `examples/openai_basic.py` - Basic OpenAI usage
- `examples/openai_cached.py` - OpenAI with caching
- `examples/supabase_crud.py` - Supabase CRUD operations
- `examples/multi_provider.py` - Using multiple integrations

---

## 🔗 Related Documentation

- **TTA.dev Core**: [`packages/tta-dev-primitives/README.md`](../tta-dev-primitives/README.md)
- **Vibe Coder Guide**: [`docs/guides/VIBE_CODER_QUICKSTART.md`](../../docs/guides/VIBE_CODER_QUICKSTART.md)
- **Multi-Agent Collaboration**: [`docs/guides/MULTI_AGENT_COLLABORATION.md`](../../docs/guides/MULTI_AGENT_COLLABORATION.md)

---

## 📞 Support

- **Issues**: https://github.com/theinterneti/TTA.dev/issues
- **Discussions**: https://github.com/theinterneti/TTA.dev/discussions

---

**License**: See LICENSE file
**Version**: 0.1.0 (Skeleton)
**Status**: Under active development
