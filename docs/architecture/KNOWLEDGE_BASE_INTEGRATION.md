# Knowledge Base Integration Architecture

**Design document for connecting Logseq knowledge base with TTA.dev workflow primitives**

**Date:** November 2, 2025
**Status:** Design Phase
**Related:** ROADMAP.md Phase 4, MCP_SERVERS.md LogSeq integration

---

## 🎯 Goals

1. **Enable contextual guidance** - Workflows can query KB for best practices, common mistakes, examples
2. **Leverage existing knowledge** - Use Logseq graph instead of building custom KB system
3. **Stage-aware recommendations** - Provide stage-specific guidance during lifecycle transitions
4. **Lightweight integration** - Wrap existing LogSeq MCP tools without complex abstractions

---

## 🏗️ Architecture

### Component Overview

```
┌─────────────────────────────────────────┐
│  Workflow Primitives                    │
│  (StageManager, ValidationCheck, etc.)  │
└───────────────┬─────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────┐
│  KnowledgeBasePrimitive                 │
│  - search_by_tags()                     │
│  - get_related_pages()                  │
│  - query_best_practices()               │
│  - query_common_mistakes()              │
└───────────────┬─────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────┐
│  LogSeq MCP Integration                 │
│  (mcp-logseq tools via VS Code)         │
└─────────────────────────────────────────┘
```

###Implementation Strategy

**Phase 1: Core KB Primitive** (This PR)
- Create `KnowledgeBasePrimitive` class
- Implement basic query methods
- Handle MCP tool unavailability gracefully

**Phase 2: KB Structure** (Next)
- Organize Logseq pages with consistent taxonomy
- Add discovery tags
- Populate with initial best practices

**Phase 3: Stage Integration** (After Phase 2)
- Enhance `StageManager` to query KB
- Provide stage-specific recommendations
- Add KB queries to validation criteria

---

## 📦 KnowledgeBasePrimitive API

### Class Definition

```python
from tta_dev_primitives.observability import InstrumentedPrimitive
from tta_dev_primitives.core.base import WorkflowContext

class KnowledgeBasePrimitive(InstrumentedPrimitive[KBQuery, KBResult]):
    """Query Logseq knowledge base for contextual guidance.

    This primitive wraps LogSeq MCP integration to provide:
    - Best practices queries
    - Common mistakes warnings
    - Related examples
    - Stage-specific recommendations

    Gracefully degrades when LogSeq MCP is unavailable (returns empty results).
    """

    def __init__(self, logseq_available: bool = False):
        """Initialize KB primitive.

        Args:
            logseq_available: Whether LogSeq MCP tools are available
                             (VS Code extension only, not in GitHub Actions)
        """
        super().__init__(name="knowledge_base")
        self.logseq_available = logseq_available
```

### Input Model: KBQuery

```python
from pydantic import BaseModel, Field

class KBQuery(BaseModel):
    """Query to knowledge base."""

    # Query type
    query_type: Literal["best_practices", "common_mistakes", "examples", "related"]

    # Search parameters
    topic: str = Field(description="Topic to search for (e.g., 'testing', 'deployment')")
    tags: list[str] = Field(default_factory=list, description="Tags to filter by")
    stage: str | None = Field(default=None, description="Lifecycle stage context")

    # Results control
    max_results: int = Field(default=5, description="Maximum pages to return")
    include_content: bool = Field(default=True, description="Include page content in results")
```

### Output Model: KBResult

```python
class KBPage(BaseModel):
    """Single page from knowledge base."""

    title: str
    content: str | None
    tags: list[str]
    url: str  # Logseq page URL
    relevance_score: float = 1.0

class KBResult(BaseModel):
    """Result from knowledge base query."""

    pages: list[KBPage]
    total_found: int
    query_time_ms: float
    source: Literal["logseq", "fallback"]  # "fallback" when MCP unavailable
```

### Methods

```python
async def search_by_tags(
    self,
    tags: list[str],
    max_results: int = 5,
    context: WorkflowContext | None = None
) -> KBResult:
    """Search KB by tags.

    Args:
        tags: Tags to search for (e.g., ["best-practices", "testing"])
        max_results: Maximum pages to return
        context: Workflow context for observability

    Returns:
        KBResult with matching pages

    Example:
        ```python
        kb = KnowledgeBasePrimitive(logseq_available=True)
        result = await kb.search_by_tags(
            tags=["testing", "best-practices"],
            max_results=3
        )

        for page in result.pages:
            print(f"📄 {page.title}")
            print(f"   Tags: {', '.join(page.tags)}")
        ```
    """
    pass

async def query_best_practices(
    self,
    topic: str,
    stage: str | None = None,
    context: WorkflowContext | None = None
) -> KBResult:
    """Query best practices for a topic.

    Args:
        topic: Topic to query (e.g., "deployment", "testing")
        stage: Lifecycle stage for context
        context: Workflow context

    Returns:
        KBResult with best practice pages

    Example:
        ```python
        result = await kb.query_best_practices(
            topic="testing",
            stage="testing"
        )
        ```
    """
    pass

async def query_common_mistakes(
    self,
    topic: str,
    stage: str | None = None,
    context: WorkflowContext | None = None
) -> KBResult:
    """Query common mistakes for a topic.

    Args:
        topic: Topic to query
        stage: Lifecycle stage for context
        context: Workflow context

    Returns:
        KBResult with common mistake warnings
    """
    pass

async def get_related_pages(
    self,
    page_title: str,
    max_results: int = 5,
    context: WorkflowContext | None = None
) -> KBResult:
    """Get pages related to a given page.

    Args:
        page_title: Page to find relations for
        max_results: Maximum results
        context: Workflow context

    Returns:
        KBResult with related pages
    """
    pass
```

---

## 📁 Logseq Knowledge Structure

### Page Taxonomy

Organize Logseq pages following this structure:

```
TTA.dev/
├── Best Practices/
│   ├── Testing
│   ├── Deployment
│   ├── Staging
│   ├── Observability
│   └── Code Review
├── Common Mistakes/
│   ├── Testing Antipatterns
│   ├── Deployment Pitfalls
│   └── Performance Issues
├── Examples/
│   ├── Stage Transitions
│   ├── Validation Workflows
│   └── KB Integration
└── Stage Guides/
    ├── Experimentation Best Practices
    ├── Testing Best Practices
    ├── Staging Best Practices
    ├── Deployment Best Practices
    └── Production Best Practices
```

### Tagging Convention

Use consistent tags for discoverability:

```markdown
# Example Best Practice Page

#best-practices #testing #stage-testing #tta-dev

## Overview
...

## When to Apply
- Stage: TESTING
- Priority: HIGH

## Anti-Patterns to Avoid
...
```

**Core Tags:**
- `#best-practices` - Best practice pages
- `#common-mistakes` - Common mistake warnings
- `#examples` - Working code examples
- `#stage-{name}` - Stage-specific content (e.g., `#stage-testing`)
- `#tta-dev` - TTA.dev project content
- `#{topic}` - Topic tags (e.g., `#testing`, `#deployment`)

---

## 🔗 Integration with StageManager

### Enhanced Stage Validation

```python
class StageManager(WorkflowPrimitive[StageRequest, StageReadiness]):
    """Manages lifecycle stages with KB-powered recommendations."""

    def __init__(
        self,
        stage_criteria_map: dict[Stage, StageCriteria] | None = None,
        knowledge_base: KnowledgeBasePrimitive | None = None
    ):
        super().__init__()
        self.stage_criteria_map = stage_criteria_map or {}
        self.kb = knowledge_base

    async def check_readiness(
        self,
        current_stage: Stage,
        target_stage: Stage,
        project_path: Path,
        context: WorkflowContext,
    ) -> StageReadiness:
        """Check readiness with KB recommendations."""

        # ... existing validation logic ...

        # Query KB for stage-specific guidance
        if self.kb:
            best_practices = await self.kb.query_best_practices(
                topic=target_stage.value,
                stage=target_stage.value,
                context=context
            )

            # Add KB recommendations to readiness result
            for page in best_practices.pages:
                recommended_actions.append(f"📚 {page.title}: {page.url}")
```

### Usage Example

```python
from tta_dev_primitives.lifecycle import StageManager, Stage
from tta_dev_primitives.knowledge import KnowledgeBasePrimitive
from pathlib import Path

# Create KB primitive
kb = KnowledgeBasePrimitive(logseq_available=True)

# Create stage manager with KB support
manager = StageManager(
    stage_criteria_map=criteria_map,
    knowledge_base=kb
)

# Check readiness - automatically queries KB
readiness = await manager.check_readiness(
    current_stage=Stage.TESTING,
    target_stage=Stage.STAGING,
    project_path=Path("."),
    context=context
)

# Readiness now includes KB recommendations
print("Recommendations:")
for action in readiness.recommended_actions:
    print(f"  - {action}")
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# platform/primitives/tests/knowledge/test_knowledge_base.py

async def test_kb_search_by_tags_when_available():
    """Test KB search when LogSeq MCP is available."""
    kb = KnowledgeBasePrimitive(logseq_available=True)

    # Mock MCP responses
    with mock.patch('mcp_logseq.search') as mock_search:
        mock_search.return_value = [...]

        result = await kb.search_by_tags(["testing"])

        assert result.source == "logseq"
        assert len(result.pages) > 0

async def test_kb_graceful_degradation():
    """Test KB gracefully degrades when MCP unavailable."""
    kb = KnowledgeBasePrimitive(logseq_available=False)

    result = await kb.search_by_tags(["testing"])

    assert result.source == "fallback"
    assert result.pages == []  # Empty but doesn't crash
```

---

## 📊 Success Metrics

### Phase 1 Success Criteria
- ✅ KnowledgeBasePrimitive implemented
- ✅ All query methods working
- ✅ Graceful degradation when MCP unavailable
- ✅ Unit tests with 100% coverage

### Phase 2 Success Criteria
- ✅ 10+ best practice pages created
- ✅ 5+ common mistake pages created
- ✅ Consistent tagging applied
- ✅ Stage guides for all 5 stages

### Phase 3 Success Criteria
- ✅ StageManager uses KB recommendations
- ✅ Example workflow demonstrates KB integration
- ✅ Documentation complete

---

## 🚀 Implementation Plan

### Next Steps

1. **Create `knowledge_base.py`** - Implement KnowledgeBasePrimitive
2. **Add to __init__.py** - Export from tta_dev_primitives.knowledge
3. **Write unit tests** - Mock MCP responses, test degradation
4. **Create example** - stage_based_workflow.py with KB integration
5. **Organize Logseq** - Create page structure and initial content
6. **Integrate with StageManager** - Add KB recommendations
7. **Document** - Write usage guide

### Timeline

- **Phase 1** (This session): KnowledgeBasePrimitive implementation
- **Phase 2** (Next session): Logseq structure and content
- **Phase 3** (Following session): StageManager integration

---

## 📝 Open Questions

1. **MCP Availability Detection** - How to detect if LogSeq MCP is available?
   - **Answer:** Pass as constructor parameter, default to False

2. **Caching Strategy** - Should we cache KB query results?
   - **Answer:** No caching in v1 - keep simple, add if needed

3. **Search Ranking** - How to rank KB search results?
   - **Answer:** Simple tag matching in v1, could enhance with TF-IDF later

---

**Status:** Ready for implementation ✅
**Next:** Create `knowledge_base.py` and begin Phase 1


---
**Logseq:** [[TTA.dev/Docs/Architecture/Knowledge_base_integration]]
