type:: primitive
category:: Knowledge
status:: documented
generated:: 2025-12-04

# KnowledgeBasePrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/knowledge/knowledge_base.py`

## Overview

Query Logseq knowledge base for contextual guidance.

This primitive wraps LogSeq MCP integration to provide:
- Best practices queries
- Common mistakes warnings
- Related examples
- Stage-specific recommendations

Gracefully degrades when LogSeq MCP is unavailable (returns empty results).

## Usage Example

```python
from tta_dev_primitives.knowledge import (
        KnowledgeBasePrimitive,
        KBQuery,
    )
    from tta_dev_primitives.core.base import WorkflowContext

    # Create KB primitive
    kb = KnowledgeBasePrimitive(logseq_available=True)

    # Query best practices
    query = KBQuery(
        query_type="best_practices",
        topic="testing",
        stage="testing",
        max_results=3
    )

    context = WorkflowContext()
    result = await kb.execute(query, context)

    for page in result.pages:
        print(f"📄 {page.title}")
        print(f"   {page.content[:100]}...")
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Knowledge]] - Knowledge primitives
