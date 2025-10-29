# A-MEM Semantic Intelligence Layer - Phase 2 Design

**Purpose**: Design document for integrating A-MEM (Agentic Memory for LLM Agents) with TTA.dev's Layer 3 Deep Memory to enable semantic intelligence, automatic memory linking, and memory evolution.

**Status**: Design Phase
**Target**: Phase 2 Implementation (Q1 2025)
**Last Updated**: 2025-10-28

---

## Executive Summary

This document outlines the architecture and implementation plan for integrating **A-MEM** as a semantic intelligence layer into TTA.dev's existing 4-layer memory hierarchy. A-MEM will enhance Layer 3 (Deep Memory) with:

- **Semantic linking** between related memories across sessions
- **Automatic keyword/tag extraction** using LLM
- **Memory evolution** with lifecycle management
- **Knowledge graph** discovery and visualization
- **Cross-session pattern recognition**

## Table of Contents

1. [Background & Motivation](#background--motivation)
2. [Architecture Overview](#architecture-overview)
3. [Component Design](#component-design)
4. [Data Flow](#data-flow)
5. [API Design](#api-design)
6. [Integration Strategy](#integration-strategy)
7. [Implementation Phases](#implementation-phases)
8. [Performance Considerations](#performance-considerations)
9. [Testing Strategy](#testing-strategy)
10. [Migration Path](#migration-path)

---

## Background & Motivation

### Current State (Phase 1)

TTA.dev's memory system uses **4 layers**:

1. **Session Context** (ephemeral) - Working memory for current execution
2. **Cache Memory** (hours) - TTL-based recent data
3. **Deep Memory** (permanent) - Long-term patterns via Redis
4. **PAF Store** (permanent) - Architectural constraints

**Limitations**:
- ❌ No semantic search capabilities
- ❌ Manual memory organization
- ❌ No cross-session pattern discovery
- ❌ Limited memory relationships
- ❌ No automatic tagging/categorization

### Desired State (Phase 2)

With A-MEM integration:

- ✅ **Semantic search** via ChromaDB vector embeddings
- ✅ **Automatic linking** between related memories
- ✅ **LLM-powered enrichment** (keywords, context, tags)
- ✅ **Cross-session intelligence** (pattern discovery)
- ✅ **Memory evolution** (links improve over time)
- ✅ **Knowledge graphs** for visualization

---

## Architecture Overview

### Hybrid Architecture: Redis + A-MEM

```
┌─────────────────────────────────────────────────────────┐
│                  TTA.dev Application                    │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   MemoryWorkflowPrimitive     │
        │   (Unified Interface)         │
        └───────────────────────────────┘
                        │
            ┌───────────┴───────────┐
            │                       │
            ▼                       ▼
┌───────────────────────┐  ┌──────────────────────┐
│  Redis Agent Memory   │  │  A-MEM Intelligence  │
│  (Primary Storage)    │  │  (Semantic Layer)    │
├───────────────────────┤  ├──────────────────────┤
│ • Fast retrieval      │  │ • ChromaDB vectors   │
│ • MCP interface       │  │ • Semantic linking   │
│ • Session management  │  │ • LLM enrichment     │
│ • Time-based queries  │  │ • Knowledge graphs   │
│ • Production infra    │  │ • Evolution engine   │
└───────────────────────┘  └──────────────────────┘
            │                       │
            │   Background Sync     │
            └───────────────────────┘
```

### Key Design Principles

1. **Redis as Primary**: Fast operational queries, MCP interface
2. **A-MEM as Enhancement**: Semantic intelligence, not replacement
3. **Eventual Consistency**: Background sync, not blocking
4. **Hybrid Queries**: Smart routing based on query type
5. **Backward Compatible**: Existing code works without A-MEM

---

## Component Design

### 1. MemoryEnrichmentWorker

**Purpose**: Background worker that syncs Redis memories to A-MEM for semantic processing.

**Responsibilities**:
- Monitor Redis for new Deep Memory entries
- Submit memories to A-MEM for processing
- Retrieve enriched metadata (keywords, context, links)
- Update Redis with A-MEM insights

**Implementation**:

```python
from agentic_memory.memory_system import AgenticMemorySystem
from tta_dev_primitives import MemoryWorkflowPrimitive


class MemoryEnrichmentWorker:
    """Background worker for A-MEM enrichment of Deep Memory."""

    def __init__(
        self,
        redis_url: str = "http://localhost:8000",
        amem_model: str = "all-MiniLM-L6-v2",
        llm_backend: str = "openai",
        llm_model: str = "gpt-4o-mini"
    ):
        """Initialize enrichment worker."""
        self.redis_client = MemoryWorkflowPrimitive(redis_url=redis_url)
        self.amem = AgenticMemorySystem(
            model_name=amem_model,
            llm_backend=llm_backend,
            llm_model=llm_model
        )

    async def enrich_memory(
        self,
        redis_memory_id: str,
        user_id: str
    ) -> dict:
        """
        Enrich a Redis memory with A-MEM semantic intelligence.

        Args:
            redis_memory_id: Redis memory ID
            user_id: User ID for Redis lookup

        Returns:
            Enriched memory metadata
        """
        # 1. Fetch from Redis
        redis_memory = await self.redis_client.get_memory_by_id(
            memory_id=redis_memory_id,
            user_id=user_id
        )

        if not redis_memory:
            raise ValueError(f"Memory {redis_memory_id} not found")

        # 2. Add to A-MEM
        amem_id = self.amem.add_note(
            content=redis_memory["text"],
            tags=redis_memory.get("metadata", {}).get("tags", []),
            category=redis_memory.get("metadata", {}).get("category", "general"),
            timestamp=redis_memory.get("timestamp", "")
        )

        # 3. Wait for A-MEM to process (semantic linking)
        await asyncio.sleep(1)  # Give A-MEM time to evolve

        # 4. Retrieve enriched memory
        enriched = self.amem.read(amem_id)

        # 5. Update Redis with A-MEM insights
        enrichment_metadata = {
            "amem_id": amem_id,
            "amem_keywords": enriched.keywords,
            "amem_context": enriched.context,
            "amem_related_ids": enriched.links,
            "amem_tags": enriched.tags,
            "amem_enriched_at": datetime.now().isoformat()
        }

        await self.redis_client.update_memory_metadata(
            memory_id=redis_memory_id,
            user_id=user_id,
            metadata=enrichment_metadata
        )

        return enrichment_metadata

    async def process_queue(self, batch_size: int = 10):
        """Process queue of unenriched memories."""
        # Get memories without amem_id
        unenriched = await self.redis_client.query_memories(
            user_id="*",
            filter_metadata={"amem_id": None},
            limit=batch_size
        )

        for memory in unenriched:
            try:
                await self.enrich_memory(
                    redis_memory_id=memory["id"],
                    user_id=memory["user_id"]
                )
                print(f"✅ Enriched memory {memory['id']}")
            except Exception as e:
                print(f"❌ Failed to enrich {memory['id']}: {e}")
```

### 2. HybridMemoryRetriever

**Purpose**: Smart query router that combines Redis speed with A-MEM depth.

**Query Strategy**:

| Query Type | Primary Source | Secondary Source | Merge Strategy |
|------------|---------------|------------------|----------------|
| Recent (< 1h) | Redis only | - | Direct return |
| Session-specific | Redis only | - | Direct return |
| Semantic search | A-MEM | Redis (fallback) | Dedup + score |
| Cross-session patterns | A-MEM | Redis (enrich) | Link expansion |
| Time-windowed | Redis | A-MEM (optional) | Union + rank |

**Implementation**:

```python
from typing import Literal


class HybridMemoryRetriever:
    """Smart memory retrieval combining Redis + A-MEM."""

    def __init__(
        self,
        redis_client: MemoryWorkflowPrimitive,
        amem_system: AgenticMemorySystem
    ):
        self.redis = redis_client
        self.amem = amem_system

    async def retrieve(
        self,
        query: str,
        user_id: str,
        mode: Literal["fast", "semantic", "hybrid"] = "hybrid",
        session_id: str | None = None,
        time_window_hours: int | None = None,
        k: int = 10
    ) -> list[dict]:
        """
        Intelligent memory retrieval.

        Args:
            query: Search query
            user_id: User ID
            mode: Retrieval mode (fast/semantic/hybrid)
            session_id: Optional session filter
            time_window_hours: Optional time filter
            k: Number of results

        Returns:
            List of memory dictionaries
        """
        if mode == "fast":
            # Redis only (fast path)
            return await self._retrieve_redis(
                query, user_id, session_id, time_window_hours, k
            )

        elif mode == "semantic":
            # A-MEM only (deep semantic)
            return await self._retrieve_amem(query, k)

        else:  # hybrid
            # Combine both sources
            return await self._retrieve_hybrid(
                query, user_id, session_id, time_window_hours, k
            )

    async def _retrieve_redis(
        self,
        query: str,
        user_id: str,
        session_id: str | None,
        time_window_hours: int | None,
        k: int
    ) -> list[dict]:
        """Fast retrieval from Redis."""
        # Use existing Redis client search
        return await self.redis.search_deep_memory(
            query=query,
            user_id=user_id,
            session_id=session_id,
            time_window_hours=time_window_hours,
            limit=k
        )

    async def _retrieve_amem(self, query: str, k: int) -> list[dict]:
        """Semantic retrieval from A-MEM."""
        # A-MEM semantic search
        amem_results = self.amem.search_agentic(query, k=k)

        # Convert to standard format
        memories = []
        for result in amem_results:
            memory = self.amem.read(result.id)
            memories.append({
                "id": result.id,
                "text": memory.content,
                "metadata": {
                    "keywords": memory.keywords,
                    "context": memory.context,
                    "tags": memory.tags,
                    "related_ids": memory.links
                },
                "score": result.score,
                "source": "amem"
            })

        return memories

    async def _retrieve_hybrid(
        self,
        query: str,
        user_id: str,
        session_id: str | None,
        time_window_hours: int | None,
        k: int
    ) -> list[dict]:
        """Hybrid retrieval combining Redis + A-MEM."""
        # 1. Fast path: Redis (recent, session-specific)
        redis_results = await self._retrieve_redis(
            query, user_id, session_id, time_window_hours, k
        )

        # 2. Deep path: A-MEM (semantic, cross-session)
        amem_results = await self._retrieve_amem(query, k)

        # 3. Merge with deduplication
        merged = self._merge_results(redis_results, amem_results, k)

        # 4. Expand context using A-MEM links
        expanded = await self._expand_with_links(merged, max_expansion=5)

        return expanded[:k]

    def _merge_results(
        self,
        redis_results: list[dict],
        amem_results: list[dict],
        k: int
    ) -> list[dict]:
        """Merge and deduplicate results."""
        seen_texts = set()
        merged = []

        # Prioritize Redis (recent context)
        for memory in redis_results:
            text = memory["text"]
            if text not in seen_texts:
                seen_texts.add(text)
                memory["source"] = "redis"
                merged.append(memory)

        # Add A-MEM (semantic matches)
        for memory in amem_results:
            text = memory["text"]
            if text not in seen_texts:
                seen_texts.add(text)
                merged.append(memory)

        # Sort by relevance score (if available)
        merged.sort(key=lambda m: m.get("score", 0), reverse=True)

        return merged[:k]

    async def _expand_with_links(
        self,
        memories: list[dict],
        max_expansion: int = 5
    ) -> list[dict]:
        """Expand results with related memories from A-MEM links."""
        expanded = list(memories)
        seen_ids = {m["id"] for m in memories}

        for memory in memories:
            related_ids = memory.get("metadata", {}).get("amem_related_ids", [])

            for related_id in related_ids[:max_expansion]:
                if related_id not in seen_ids:
                    # Fetch related memory
                    related = self.amem.read(related_id)
                    expanded.append({
                        "id": related_id,
                        "text": related.content,
                        "metadata": {
                            "keywords": related.keywords,
                            "context": related.context,
                            "tags": related.tags
                        },
                        "source": "amem_link"
                    })
                    seen_ids.add(related_id)

        return expanded
```

### 3. Memory Evolution Engine

**Purpose**: Periodically run A-MEM evolution to update memory links.

**Implementation**:

```python
class MemoryEvolutionEngine:
    """Manage A-MEM memory evolution lifecycle."""

    def __init__(
        self,
        amem_system: AgenticMemorySystem,
        redis_client: MemoryWorkflowPrimitive
    ):
        self.amem = amem_system
        self.redis = redis_client

    async def evolve_memories(self, user_id: str) -> dict:
        """
        Run A-MEM evolution and sync updates to Redis.

        Returns:
            Evolution statistics
        """
        # 1. Get all A-MEM memories
        all_memories = self.amem.list_all_memories()

        # 2. Run A-MEM evolution (updates links)
        evolution_stats = self.amem.evolve()

        # 3. Sync updated links back to Redis
        updated_count = 0
        for amem_id in evolution_stats.get("updated_ids", []):
            memory = self.amem.read(amem_id)

            # Find corresponding Redis memory
            redis_memory = await self.redis.search_deep_memory(
                query=memory.content[:100],  # Match by content prefix
                user_id=user_id,
                limit=1
            )

            if redis_memory:
                await self.redis.update_memory_metadata(
                    memory_id=redis_memory[0]["id"],
                    user_id=user_id,
                    metadata={
                        "amem_related_ids": memory.links,
                        "amem_last_evolved": datetime.now().isoformat()
                    }
                )
                updated_count += 1

        return {
            "total_memories": len(all_memories),
            "evolved_count": len(evolution_stats.get("updated_ids", [])),
            "redis_synced": updated_count
        }
```

---

## Data Flow

### Write Path (Memory Creation)

```
New Memory Created
       │
       ▼
┌─────────────────┐
│  Redis Store    │ ← Immediate storage (fast)
└─────────────────┘
       │
       │ Event notification
       ▼
┌─────────────────┐
│ Enrichment Queue│
└─────────────────┘
       │
       ▼
┌─────────────────┐
│  Worker Process │
└─────────────────┘
       │
       ├── Add to A-MEM (ChromaDB)
       ├── LLM enrichment (keywords, context)
       ├── Semantic linking (automatic)
       └── Update Redis metadata
              │
              ▼
     Enriched Memory (Redis + A-MEM)
```

### Read Path (Memory Retrieval)

```
Query Request
       │
       ▼
┌────────────────┐
│  Query Router  │
└────────────────┘
       │
       ├── Fast path? → Redis only
       ├── Semantic? → A-MEM only
       └── Hybrid? → Both sources
              │
              ▼
       ┌──────────────┐
       │ Merge Results│
       └──────────────┘
              │
              ├── Deduplicate
              ├── Rank by relevance
              └── Expand with A-MEM links
                     │
                     ▼
              Final Results
```

---

## API Design

### Extended MemoryWorkflowPrimitive

```python
class MemoryWorkflowPrimitive:
    """Extended with A-MEM capabilities."""

    def __init__(
        self,
        redis_url: str = "http://localhost:8000",
        user_id: str = "default-user",
        enable_amem: bool = False,  # Feature flag
        amem_model: str = "all-MiniLM-L6-v2",
        llm_backend: str = "openai",
        llm_model: str = "gpt-4o-mini"
    ):
        """Initialize with optional A-MEM support."""
        self.redis_client = RedisAgentMemoryClient(redis_url)
        self.user_id = user_id

        # A-MEM (optional)
        self.amem_enabled = enable_amem
        if enable_amem:
            self.amem = AgenticMemorySystem(
                model_name=amem_model,
                llm_backend=llm_backend,
                llm_model=llm_model
            )
            self.retriever = HybridMemoryRetriever(self, self.amem)
        else:
            self.amem = None
            self.retriever = None

    async def create_deep_memory_with_enrichment(
        self,
        text: str,
        tags: list[str] | None = None,
        category: str = "general",
        enrich: bool = True  # Auto-enrich with A-MEM
    ) -> str:
        """
        Create deep memory with optional A-MEM enrichment.

        Args:
            text: Memory content
            tags: Optional tags
            category: Memory category
            enrich: Whether to enrich with A-MEM

        Returns:
            Memory ID
        """
        # 1. Store in Redis
        memory_id = await self.create_deep_memory(text, tags=tags)

        # 2. Enrich with A-MEM (if enabled)
        if enrich and self.amem_enabled:
            worker = MemoryEnrichmentWorker(
                redis_url=self.redis_client.base_url,
                amem_system=self.amem
            )
            await worker.enrich_memory(memory_id, self.user_id)

        return memory_id

    async def semantic_search(
        self,
        query: str,
        mode: Literal["fast", "semantic", "hybrid"] = "hybrid",
        k: int = 10
    ) -> list[dict]:
        """
        Semantic memory search using A-MEM.

        Args:
            query: Search query
            mode: Retrieval mode
            k: Number of results

        Returns:
            List of matching memories
        """
        if not self.amem_enabled:
            # Fallback to Redis search
            return await self.search_deep_memory(query, limit=k)

        return await self.retriever.retrieve(
            query=query,
            user_id=self.user_id,
            mode=mode,
            k=k
        )

    async def get_memory_links(
        self,
        memory_id: str
    ) -> list[dict]:
        """
        Get related memories via A-MEM links.

        Args:
            memory_id: Memory ID

        Returns:
            List of related memories
        """
        if not self.amem_enabled:
            return []

        # Get memory metadata
        memory = await self.redis_client.get_memory_by_id(
            memory_id=memory_id,
            user_id=self.user_id
        )

        amem_id = memory.get("metadata", {}).get("amem_id")
        if not amem_id:
            return []

        # Get A-MEM memory
        amem_memory = self.amem.read(amem_id)

        # Fetch linked memories
        linked = []
        for link_id in amem_memory.links:
            linked_memory = self.amem.read(link_id)
            linked.append({
                "id": link_id,
                "text": linked_memory.content,
                "keywords": linked_memory.keywords,
                "context": linked_memory.context
            })

        return linked
```

---

## Integration Strategy

### Feature Flag Approach

```python
# Environment variable control
AMEM_ENABLED = os.getenv("AMEM_ENABLED", "false").lower() == "true"

# Gradual rollout
memory = MemoryWorkflowPrimitive(
    redis_url="http://localhost:8000",
    enable_amem=AMEM_ENABLED  # Opt-in
)
```

### Backward Compatibility

- All existing code works without A-MEM
- A-MEM is additive (no breaking changes)
- Graceful degradation if A-MEM unavailable

---

## Implementation Phases

### Phase 2.1: Foundation (Week 1-2)

- [ ] Add A-MEM dependency to `pyproject.toml`
- [ ] Create `MemoryEnrichmentWorker` class
- [ ] Add feature flag for A-MEM enablement
- [ ] Basic integration tests

### Phase 2.2: Hybrid Retrieval (Week 3-4)

- [ ] Implement `HybridMemoryRetriever`
- [ ] Add smart query routing logic
- [ ] Test merge and deduplication
- [ ] Performance benchmarks

### Phase 2.3: Evolution & Links (Week 5-6)

- [ ] Create `MemoryEvolutionEngine`
- [ ] Implement periodic evolution cron
- [ ] Add link expansion logic
- [ ] Cross-session pattern discovery

### Phase 2.4: Production Ready (Week 7-8)

- [ ] Monitoring and metrics
- [ ] Error handling and fallbacks
- [ ] Documentation and examples
- [ ] Migration guide for existing users

---

## Performance Considerations

### Latency Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Redis store | < 50ms | Primary write path |
| A-MEM enrichment | < 2s | Background, async |
| Fast retrieval | < 100ms | Redis only |
| Semantic search | < 500ms | A-MEM vector search |
| Hybrid search | < 800ms | Combined sources |

### Scaling Strategy

- **Write path**: Queue-based enrichment (non-blocking)
- **Read path**: Cache A-MEM results in Redis
- **Evolution**: Off-peak batch processing
- **ChromaDB**: Separate service, horizontal scaling

---

## Testing Strategy

### Unit Tests

- `MemoryEnrichmentWorker` enrichment logic
- `HybridMemoryRetriever` query routing
- `MemoryEvolutionEngine` sync logic

### Integration Tests

- End-to-end memory creation + enrichment
- Hybrid queries with mock data
- Link expansion correctness

### Performance Tests

- Latency benchmarks (p50, p95, p99)
- Throughput testing (memories/second)
- Memory usage under load

---

## Migration Path

### For Existing Users

1. **No Action Required**: Continues using Redis-only
2. **Opt-In**: Set `enable_amem=True` when ready
3. **Backfill**: Run enrichment worker on existing memories
4. **Validate**: Compare Redis vs Hybrid retrieval

### Backfill Script

```bash
# Enrich existing Deep Memory entries
uv run python scripts/backfill_amem_enrichment.py --user-id <user> --batch-size 100
```

---

## Open Questions

1. **LLM Costs**: How to manage OpenAI API costs for enrichment?
   - **Solution**: Use cheaper models (gpt-4o-mini), batch processing

2. **ChromaDB Hosting**: Self-hosted vs managed?
   - **Solution**: Start with self-hosted, migrate to managed later

3. **Sync Frequency**: How often to run evolution?
   - **Solution**: Daily for now, tune based on usage patterns

4. **Link Quality**: How to validate A-MEM links are useful?
   - **Solution**: User feedback mechanism, link scoring

---

## Next Steps

1. **Review**: Get team feedback on architecture
2. **Prototype**: Build minimal MemoryEnrichmentWorker
3. **Test**: Validate semantic search quality
4. **Iterate**: Refine based on real-world usage

---

## References

- [A-MEM Paper](https://arxiv.org/pdf/2502.12110)
- [A-MEM GitHub](https://github.com/agiresearch/A-mem)
- [Memory Backend Evaluation](./MEMORY_BACKEND_EVALUATION.md)
- [Session Memory Integration Plan](./SESSION_MEMORY_INTEGRATION_PLAN.md)

---

**Authors**: TTA.dev Core Team
**Reviewers**: TBD
**Approval**: Pending
