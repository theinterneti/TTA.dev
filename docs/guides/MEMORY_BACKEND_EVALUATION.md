# Memory Backend Options for TTA Agent Memory

**Purpose**: Evaluate memory solutions for implementing the 4-layer memory architecture (Session → Cache → Deep → PAF) with workflow stage integration.

**Date**: 2025-10-28
**Status**: Recommendation

---

## Memory Solutions Evaluated

### 1. A-MEM (Agentic Memory for LLM Agents)

**Repository**: https://github.com/agiresearch/A-mem
**Paper**: [A-MEM: Agentic Memory for LLM Agents](https://arxiv.org/pdf/2502.12110)
**Stars**: 645 | **License**: MIT

#### Architecture

- **Zettelkasten-inspired**: Dynamic memory organization with interconnected knowledge networks
- **ChromaDB Vector Storage**: Efficient semantic similarity search
- **Automatic Memory Evolution**: Creates contextual links between memories
- **Structured Attributes**: Tags, categories, keywords, context, timestamps

#### Key Features

✅ **Dynamic memory organization** - Memories self-organize based on semantic relationships
✅ **Intelligent indexing** - Automatic linking via ChromaDB
✅ **Note generation** - Comprehensive structured attributes
✅ **Knowledge networks** - Interconnected memory graphs
✅ **Continuous evolution** - Memories update and refine over time
✅ **Agent-driven decisions** - Adaptive memory management

#### API Surface

```python
from agentic_memory.memory_system import AgenticMemorySystem

memory = AgenticMemorySystem(
    model_name='all-MiniLM-L6-v2',
    llm_backend="openai",
    llm_model="gpt-4o-mini"
)

# Add memory
memory_id = memory.add_note(
    content="Machine learning notes",
    tags=["ml", "project"],
    category="Research",
    timestamp="202503021500"
)

# Read memory
mem = memory.read(memory_id)

# Search (semantic)
results = memory.search_agentic("neural networks", k=5)

# Update
memory.update(memory_id, content="Updated content")

# Delete
memory.delete(memory_id)
```

#### Strengths

- ✅ **Research-backed**: Published paper with empirical validation
- ✅ **Self-organizing**: Automatic semantic linking reduces manual maintenance
- ✅ **Rich metadata**: Automatic context, keywords, tags generation
- ✅ **LLM-powered**: Uses LLM for understanding relationships
- ✅ **Evolution**: Memories improve over time

#### Weaknesses

- ❌ **No built-in session concept**: Would need to add session scoping
- ❌ **Single-tier**: No native working/long-term separation
- ❌ **ChromaDB only**: Less flexibility in vector backends
- ❌ **No MCP support**: Would need custom integration
- ❌ **Newer project**: Less mature (29 commits)

#### Fit for TTA Architecture

| Memory Layer | Fit | Notes |
|--------------|-----|-------|
| Session Context | ⚠️ Partial | Need to add session scoping via tags/metadata |
| Cache Memory | ⚠️ Partial | Could use timestamps + TTL logic |
| Deep Memory | ✅ Excellent | Core use case - semantic long-term memory |
| PAF Store | ❌ No | Different paradigm (facts vs. memories) |

---

### 2. Redis Agent Memory Server

**Repository**: https://github.com/redis/agent-memory-server
**Docs**: https://redis.github.io/agent-memory-server/
**Stars**: 123 | **License**: Apache 2.0

#### Architecture

- **Two-Tier Memory**: Working memory (session-scoped) + Long-term memory (persistent)
- **Redis Vector Database**: Fast, production-ready vector search
- **Pluggable Backends**: Vector store factory system (Redis, Chroma, others)
- **Background Workers**: Async memory extraction and processing
- **Dual Interface**: REST API + MCP server

#### Key Features

✅ **Working + Long-term memory** - Built-in two-tier architecture
✅ **Session-scoped** - Native session support
✅ **Configurable strategies** - Discrete, summary, preferences, custom
✅ **Semantic search** - Vector similarity with metadata filtering
✅ **AI integration** - Topic extraction, entity recognition, summarization
✅ **MCP native** - Built-in Model Context Protocol server
✅ **Python SDK** - Easy integration
✅ **Production-ready** - Docker, OAuth2, background workers

#### API Surface

```python
from agent_memory_client import MemoryAPIClient

client = MemoryAPIClient(base_url="http://localhost:8000")

# Working memory (session-scoped)
await client.add_working_memory_messages(
    session_id="session-123",
    messages=[{"role": "user", "content": "I prefer morning meetings"}]
)

# Long-term memory
await client.create_long_term_memories([
    {
        "text": "User prefers morning meetings",
        "user_id": "user123",
        "memory_type": "preference"
    }
])

# Search
results = await client.search_long_term_memory(
    text="What time does user like meetings?",
    user_id="user123"
)

# LangChain integration
from agent_memory_client.integrations.langchain import get_memory_tools

tools = get_memory_tools(
    memory_client=client,
    session_id="my_session",
    user_id="alice"
)
```

#### Strengths

- ✅ **Two-tier architecture**: Working + Long-term matches our Session + Deep layers
- ✅ **Session native**: Built-in session management
- ✅ **Production-ready**: Docker, auth, workers, monitoring
- ✅ **MCP built-in**: Native Model Context Protocol support
- ✅ **Flexible backends**: Pluggable vector stores
- ✅ **Active development**: 480 commits, regular releases
- ✅ **Redis performance**: Fast vector search at scale
- ✅ **LangChain integration**: First-class support

#### Weaknesses

- ❌ **Redis dependency**: Requires Redis infrastructure
- ⚠️ **Server-based**: Requires running separate service (but Docker simplifies this)
- ⚠️ **Two-tier only**: Would need to add Cache + PAF layers

#### Fit for TTA Architecture

| Memory Layer | Fit | Notes |
|--------------|-----|-------|
| Session Context | ✅ Excellent | Native working memory with session scoping |
| Cache Memory | ✅ Good | Working memory with TTL or timestamp filtering |
| Deep Memory | ✅ Excellent | Native long-term memory with semantic search |
| PAF Store | ⚠️ Partial | Could store as special memory type with metadata |

---

## Recommendation

### Primary Choice: **Redis Agent Memory Server**

**Rationale**:

1. **Architecture Alignment**: Two-tier (working + long-term) maps directly to our Session + Deep layers
2. **Production-Ready**: Battle-tested Redis backend, auth, Docker deployment
3. **MCP Native**: Built-in Model Context Protocol support for Claude/other AI tools
4. **Session Support**: Native session scoping matches our workflow needs
5. **Flexibility**: Pluggable backend system allows future customization
6. **Active Project**: Regular releases, maintained by Redis team
7. **Integration**: LangChain support, Python SDK, REST API

### Hybrid Approach: Redis + Custom Extensions

**Proposed 4-Layer Implementation**:

```python
# Layer 1: Session Context (Working Memory)
# Redis Agent Memory Server - Working Memory
await client.add_working_memory_messages(
    session_id=workflow_context.session_id,
    messages=conversation_messages
)

# Layer 2: Cache Memory (Time-windowed Working Memory)
# Redis Agent Memory Server - Working Memory with TTL
# Use timestamp filtering to get last 1-24 hours
await client.get_working_memory(
    session_id=workflow_context.session_id,
    since=datetime.now() - timedelta(hours=1)
)

# Layer 3: Deep Memory (Long-term Semantic Memory)
# Redis Agent Memory Server - Long-term Memory
await client.create_long_term_memories([
    {
        "text": pattern_text,
        "user_id": workflow_context.user_id,
        "memory_type": "pattern",
        "metadata": {
            "workflow_stage": "implement",
            "session_group": "feature-auth"
        }
    }
])

# Layer 4: PAF Store (Permanent Architectural Facts)
# Custom PAFMemoryPrimitive (already implemented)
paf = PAFMemoryPrimitive()
validation = paf.validate_test_coverage(75.0)
```

### Why Not A-MEM Alone?

While A-MEM is excellent for semantic memory organization:

- ❌ No native session scoping
- ❌ Single-tier architecture requires custom layering
- ❌ No MCP support out-of-box
- ❌ Less mature (newer project)
- ✅ **Could be complementary**: Use A-MEM's auto-linking within Deep Memory layer

---

## 🎯 RECOMMENDED: Hybrid Architecture (Redis + A-MEM)

**Best of Both Worlds**: Combine Redis's infrastructure with A-MEM's intelligence

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    TTA Agent Memory System                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Layer 1: Session Context (Working Memory)                   │
│  ├─ Redis Agent Memory Server ────────────────────────┐      │
│  │  • Fast session-scoped storage                      │      │
│  │  • MCP interface                                    │      │
│  │  • REST API                                         │      │
│  └─────────────────────────────────────────────────────┘      │
│                                                               │
│  Layer 2: Cache Memory (Time-windowed)                       │
│  ├─ Redis Agent Memory Server ────────────────────────┐      │
│  │  • Working memory with TTL                          │      │
│  │  • Fast timestamp filtering (1-24h)                 │      │
│  └─────────────────────────────────────────────────────┘      │
│                                                               │
│  Layer 3: Deep Memory (Long-term Semantic)                   │
│  ├─ Redis (Primary Storage) ──────────────────────────┐      │
│  │  • Fast retrieval                                   │      │
│  │  • Production infra                                 │      │
│  │  • Metadata indexing                                │      │
│  └─────────────────────────────────────────────────────┘      │
│           │                                                   │
│           │ Background Sync                                   │
│           ↓                                                   │
│  ├─ A-MEM (Intelligence Layer) ───────────────────────┐      │
│  │  • ChromaDB vector search                           │      │
│  │  • Automatic semantic linking                       │      │
│  │  • Memory evolution                                 │      │
│  │  • Context/keyword extraction                       │      │
│  │  • Zettelkasten knowledge graphs                    │      │
│  └─────────────────────────────────────────────────────┘      │
│           │                                                   │
│           │ Enriched Metadata                                 │
│           ↓                                                   │
│  ├─ Back to Redis ────────────────────────────────────┐      │
│  │  • Updated tags/context                             │      │
│  │  • Semantic links                                   │      │
│  │  • Related memory IDs                               │      │
│  └─────────────────────────────────────────────────────┘      │
│                                                               │
│  Layer 4: PAF Store (Validation)                             │
│  ├─ Custom PAFMemoryPrimitive ────────────────────────┐      │
│  │  • Architectural constraints                        │      │
│  │  • Validation rules                                 │      │
│  └─────────────────────────────────────────────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

**1. Memory Creation (Write Path)**

```python
# 1. Store in Redis for immediate operational use
await redis_client.create_long_term_memories([{
    "text": "User implemented authentication using JWT tokens",
    "user_id": "user123",
    "session_id": "session-456",
    "memory_type": "pattern",
    "metadata": {
        "workflow_stage": "implement",
        "session_group": "feature-auth",
        "timestamp": datetime.now().isoformat()
    }
}])

# 2. Background worker syncs to A-MEM for processing
amem_system = AgenticMemorySystem(
    model_name='all-MiniLM-L6-v2',
    llm_backend="openai",
    llm_model="gpt-4o-mini"
)

amem_id = amem_system.add_note(
    content="User implemented authentication using JWT tokens",
    tags=["authentication", "jwt", "security"],
    category="Implementation",
    timestamp=datetime.now().strftime("%Y%m%d%H%M")
)

# 3. A-MEM automatically:
#    - Extracts keywords: ["JWT", "tokens", "authentication"]
#    - Generates context: "Security implementation pattern"
#    - Finds related memories: [session-123, session-789]
#    - Creates semantic links

# 4. Enrich Redis memory with A-MEM insights
enriched_memory = amem_system.read(amem_id)
await redis_client.update_memory_metadata(
    memory_id=redis_memory_id,
    metadata={
        "amem_keywords": enriched_memory.keywords,
        "amem_context": enriched_memory.context,
        "amem_related": enriched_memory.related_ids,
        "amem_tags": enriched_memory.tags
    }
)
```

**2. Memory Retrieval (Read Path)**

```python
# Hybrid query strategy
async def retrieve_workflow_context(query: str, session_id: str, workflow_stage: str):
    """Intelligent hybrid retrieval combining Redis speed + A-MEM depth."""

    # Fast path: Redis for recent/session-specific
    redis_results = await redis_client.search_long_term_memory(
        text=query,
        user_id=user_id,
        filter_metadata={
            "session_id": session_id,
            "workflow_stage": workflow_stage
        },
        k=5
    )

    # Deep path: A-MEM for semantic/cross-session patterns
    amem_results = amem_system.search_agentic(query, k=10)

    # Combine results
    # - Redis gives recent, relevant context
    # - A-MEM gives semantically similar patterns from ALL sessions
    # - Merge with deduplication

    return {
        "session_context": redis_results,  # Layer 1: Session
        "semantic_patterns": amem_results,  # Layer 3: Deep + evolved
        "related_sessions": get_related_from_amem(amem_results)
    }
```

### Layer-Specific Implementation

#### Layer 1 & 2: Session + Cache (Redis Only)

**Why Redis**: Need fast, session-scoped, ephemeral storage

```python
# Session Context (Layer 1)
await redis_client.add_working_memory_messages(
    session_id=workflow_context.session_id,
    messages=conversation_messages
)

# Cache Memory (Layer 2) - last 1-24 hours
cache_memories = await redis_client.get_working_memory(
    session_id=workflow_context.session_id,
    since=datetime.now() - timedelta(hours=1)
)
```

#### Layer 3: Deep Memory (Redis + A-MEM Hybrid)

**Why Hybrid**: Redis for speed + A-MEM for intelligence

```python
# Primary storage: Redis
redis_memory_id = await redis_client.create_long_term_memories([{
    "text": pattern_text,
    "memory_type": "pattern",
    "metadata": {"source": "workflow"}
}])

# Intelligence layer: A-MEM (background worker)
class MemoryEnrichmentWorker:
    async def process_new_memory(self, redis_memory):
        # 1. Add to A-MEM
        amem_id = self.amem.add_note(
            content=redis_memory.text,
            tags=redis_memory.metadata.get("tags", []),
            category=redis_memory.memory_type
        )

        # 2. Let A-MEM evolve (automatic semantic linking)
        await asyncio.sleep(1)  # Give A-MEM time to process

        # 3. Retrieve enriched memory
        enriched = self.amem.read(amem_id)

        # 4. Update Redis with A-MEM insights
        await self.redis_client.update_memory_metadata(
            memory_id=redis_memory.id,
            metadata={
                "amem_id": amem_id,
                "keywords": enriched.keywords,
                "context": enriched.context,
                "related_memory_ids": enriched.links,
                "semantic_tags": enriched.tags
            }
        )
```

#### Layer 4: PAF Store (Custom)

**Why Custom**: Validation-focused, not semantic storage

```python
# Already implemented
paf = PAFMemoryPrimitive()
validation = paf.validate_test_coverage(75.0)
```

### Workflow Stage-Aware Loading

**Augster-Rigorous Mode - Understand Stage**

```python
async def load_understand_context(workflow_context):
    """Load comprehensive context for deep understanding."""

    # Layer 1: Full session history (Redis)
    session = await redis_client.get_working_memory(
        session_id=workflow_context.session_id,
        limit=None  # All messages
    )

    # Layer 2: Recent cache (Redis) - last 24h
    cache = await redis_client.get_working_memory(
        session_id=workflow_context.session_id,
        since=datetime.now() - timedelta(hours=24)
    )

    # Layer 3: Deep semantic search (A-MEM for intelligence)
    deep_memories = amem_system.search_agentic(
        query=workflow_context.task_description,
        k=20  # Top 20 relevant memories
    )

    # Get related sessions from A-MEM semantic links
    related_sessions = set()
    for memory in deep_memories:
        amem_memory = amem_system.read(memory['id'])
        related_sessions.update(amem_memory.related_ids)

    # Load grouped session context
    session_groups = session_group_primitive.get_session_groups(
        workflow_context.session_id
    )

    # Layer 4: All active PAFs
    active_pafs = paf_primitive.get_active_pafs()

    return {
        "session_history": session,
        "cache_24h": cache,
        "semantic_patterns": deep_memories,
        "related_sessions": related_sessions,
        "session_groups": session_groups,
        "architectural_constraints": active_pafs
    }
```

### Benefits of Hybrid Approach

✅ **Redis Strengths**:
- Fast operational storage and retrieval
- Session management and scoping
- MCP interface for AI tools
- Production-ready infrastructure
- Working memory TTL management

✅ **A-MEM Strengths**:
- ChromaDB AI-native vector search
- Automatic semantic linking (Zettelkasten)
- Memory evolution and refinement
- Context and keyword extraction
- Cross-session pattern discovery

✅ **Combined Power**:
- Best-in-class for each layer
- Redis handles speed/structure, A-MEM handles intelligence
- Background processing doesn't block operations
- Enriched metadata improves Redis queries over time
- A-MEM creates knowledge graphs that inform context loading

### Implementation Phases

**Phase 1**: Redis Primary (Current Recommendation)
- ✅ Use Redis for all 4 layers initially
- ✅ Get working system quickly
- ✅ Leverage MCP, session management

**Phase 2**: Add A-MEM Intelligence (Enhancement)
- Add A-MEM as background processor
- Sync Deep Memory layer to A-MEM
- Enrich Redis metadata with A-MEM insights
- Keep Redis as primary store

**Phase 3**: Hybrid Queries (Optimization)
- Implement smart query routing
- Redis for fast/recent, A-MEM for semantic/deep
- Merge results intelligently
- Use A-MEM links for context expansion

**Phase 4**: Advanced Features (Future)
- A-MEM memory evolution updates Redis
- Cross-session pattern discovery
- Automatic tag refinement
- Knowledge graph visualization

---

## Implementation Plan

### Phase 1: Redis Agent Memory Server Integration (Current Priority)

**Goal**: Get operational 4-layer memory system running

1. **Install Redis Agent Memory Server**
   ```bash
   docker-compose up redis agent-memory
   pip install agent-memory-client
   ```

2. **Create MemoryWorkflowPrimitive**
   - Wraps Redis client
   - Maps 4 layers to Redis constructs
   - Workflow stage-aware loading
   - Session group integration

3. **Integrate with WorkflowContext**
   - Inject memory client
   - Stage-based memory loading patterns
   - Mode-specific memory strategies (rapid/standard/augster-rigorous)

4. **Testing**
   - Test all 4 layers independently
   - Test stage-aware loading
   - Test workflow mode memory patterns
   - Integration with SessionGroupPrimitive

**Deliverables**:
- ✅ Working memory system
- ✅ MCP integration for Claude/AI tools
- ✅ Production-ready infrastructure

### Phase 2: A-MEM Intelligence Layer (Enhancement)

**Goal**: Add semantic intelligence and automatic linking

1. **Install A-MEM**
   ```bash
   pip install agentic-memory
   ```

2. **Create MemoryEnrichmentWorker**
   - Background worker process
   - Syncs Redis Deep Memory → A-MEM
   - Processes memories through A-MEM
   - Enriches Redis metadata with A-MEM insights

3. **Implement Hybrid Retrieval**
   - Smart query routing (Redis fast path + A-MEM semantic path)
   - Result merging and deduplication
   - A-MEM link expansion for context

4. **Memory Evolution Pipeline**
   - Periodic A-MEM evolution runs
   - Update Redis metadata with new links/tags
   - Knowledge graph generation

**Deliverables**:
- ✅ Automatic semantic linking
- ✅ Enhanced search with A-MEM intelligence
- ✅ Cross-session pattern discovery
- ✅ Evolving knowledge graphs

### Phase 3: Advanced Hybrid Features (Future)

**Goal**: Leverage full power of both systems

1. **Intelligent Context Loading**
   - A-MEM-informed context selection
   - Use semantic links to expand context
   - Workflow stage-specific strategies

2. **Memory Lifecycle Management**
   - A-MEM tracks memory usage/relevance
   - Automatic archival of stale memories
   - Promotion of frequently-linked patterns

3. **Cross-Session Intelligence**
   - A-MEM discovers cross-session patterns
   - SessionGroupPrimitive + A-MEM semantic links
   - Automatic session group suggestions

4. **Visualization**
   - Knowledge graph visualization (A-MEM links)
   - Session timeline with semantic connections
   - Memory evolution tracking

**Deliverables**:
- ✅ Full hybrid intelligence
- ✅ Automated memory management
- ✅ Knowledge graph insights
- ✅ Advanced context engineering

---

## Next Steps

**Immediate (Phase 1)**:
1. ✅ Add Redis Agent Memory Server dependency to pyproject.toml
2. ✅ Create MemoryWorkflowPrimitive - Unified interface for 4-layer memory
3. ✅ Integrate with WorkflowContext - Stage-aware memory loading
4. ✅ Update WorkflowProfiles - Memory patterns per workflow mode
5. ✅ Add integration tests - Test all 4 layers + workflow stages

**Near-term (Phase 2)**:
1. ⏭️ Add A-MEM dependency
2. ⏭️ Create MemoryEnrichmentWorker - Background processor
3. ⏭️ Implement hybrid query strategy
4. ⏭️ Test semantic linking and evolution

**Long-term (Phase 3)**:
1. ⏭️ Knowledge graph visualization
2. ⏭️ Advanced context engineering
3. ⏭️ Automatic session grouping suggestions
4. ⏭️ Memory lifecycle management

---

## Hybrid Architecture Quick Reference

**When to use Redis**:
- ✅ Session-scoped queries (Layer 1: Session Context)
- ✅ Time-windowed queries (Layer 2: Cache Memory)
- ✅ Fast operational retrieval
- ✅ MCP interface needs
- ✅ Production infrastructure

**When to use A-MEM**:
- ✅ Deep semantic search (Layer 3: Deep Memory enhancement)
- ✅ Cross-session pattern discovery
- ✅ Automatic memory linking
- ✅ Context/keyword extraction
- ✅ Knowledge graph building

**When to use both (Hybrid)**:
- ✅ Comprehensive context loading (Augster-Rigorous mode)
- ✅ "Related sessions" discovery
- ✅ Memory enrichment pipeline
- ✅ Advanced semantic queries with recent context
- ✅ Pattern-based refactoring suggestions

**Data Flow Summary**:
```
New Memory → Redis (immediate storage)
          ↓
     Background Worker
          ↓
     A-MEM (semantic processing)
          ↓
     Enriched Metadata → back to Redis
          ↓
     Enhanced queries combine Redis + A-MEM results
```

---

## References

- **Redis Agent Memory Server**: https://github.com/redis/agent-memory-server
- **Redis Docs**: https://redis.github.io/agent-memory-server/
- **A-MEM Paper**: https://arxiv.org/pdf/2502.12110
- **A-MEM GitHub**: https://github.com/agiresearch/A-mem
- **TTA Memory Plan**: `docs/guides/SESSION_MEMORY_INTEGRATION_PLAN.md`
- **Workflow Profiles**: `.universal-instructions/workflows/WORKFLOW_PROFILES.md`
- **PAF System**: `.universal-instructions/paf/PAFCORE.md`
