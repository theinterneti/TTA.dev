# Logseq-Docs-KB Integration Architecture Design

**Date:** October 31, 2025
**Status:** 🚧 Design Phase
**Priority:** HIGH - Architecture Pivot

---

## 🎯 Vision

Create a **bi-directional, automated integration** between documentation and knowledge base where:

1. **Docs → Logseq:** Documentation is automatically processed by free AI and converted to Logseq pages
2. **Logseq → Docs:** Knowledge base updates reflect back to documentation
3. **Human + AI Sections:** KB has both human-readable and AI-optimized sections
4. **TTA.dev Native:** This integration is a core TTA.dev workflow primitive
5. **Agent-First:** Agents using TTA.dev automatically create compliant documentation

---

## 🏗️ Architecture Components

### Component 1: Auto-Processing Pipeline

```
New/Updated Doc
    ↓
[Watch Service] ← monitors docs/
    ↓
[AI Processor] ← free AI (Gemini Flash, Llama, etc.)
    ↓
[Logseq Converter]
    ↓
[KB Sync Service]
    ↓
Logseq Page Created/Updated
```

**Key Features:**
- File system watching (inotify/watchdog)
- Free AI API integration (Gemini Flash 2.0 1.5M context)
- Intelligent page generation
- Property extraction
- Link detection and creation

### Component 2: Dual-Format KB Structure

```
logseq/pages/
├── [Topic].md                    # Human-readable format
└── [Topic].ai-optimized.md       # AI-optimized format

Structure:
# Topic Name

## 📖 Human Section
[Natural language, examples, explanations]

---

## 🤖 AI-Optimized Section
[Structured data, embeddings, metadata]
type:: documentation
tags:: [relevant, tags]
related:: [[Page1]], [[Page2]]
summary:: Concise summary
key-concepts:: concept1, concept2
```

### Component 3: TTA.dev Documentation Primitive

```python
from tta_dev_primitives.documentation import (
    DocumentationPrimitive,
    LogseqSyncPrimitive,
    KnowledgeBaseIndexPrimitive
)

# Create documentation that auto-syncs to KB
doc_workflow = (
    DocumentationPrimitive(
        output_path="docs/guides/",
        format="markdown",
        logseq_sync=True
    ) >>
    LogseqSyncPrimitive(
        kb_path="logseq/pages/",
        ai_processor="gemini-flash-2.0",
        auto_link=True,
        extract_properties=True
    ) >>
    KnowledgeBaseIndexPrimitive(
        update_graph=True,
        generate_ai_section=True
    )
)

# Agents use this automatically
result = await doc_workflow.execute({
    "title": "How to Use Feature X",
    "content": content,
    "category": "guides"
}, context)
```

---

## 🔄 Synchronization Strategy

### Docs → Logseq (Primary Flow)

**Trigger:** File created/modified in `docs/`, `packages/*/`, `README.md`

**Process:**
1. **Detect change** via file watcher
2. **Extract metadata:**
   - Title, headers
   - Code blocks
   - Links to other docs
   - Keywords
3. **AI Processing:**
   - Generate summary
   - Extract key concepts
   - Identify related topics
   - Create property structure
4. **Create Logseq page:**
   - Human section (formatted original)
   - AI section (structured metadata)
   - Internal links
   - Properties
5. **Update graph:**
   - Link to related pages
   - Update indices
   - Trigger dependent updates

### Logseq → Docs (Reflection Flow)

**Trigger:** Logseq page updated with `sync-to-docs:: true` property

**Process:**
1. **Detect KB change**
2. **Extract human section**
3. **Convert to doc format:**
   - Remove Logseq-specific syntax
   - Preserve markdown structure
   - Update front matter
4. **Write to docs/** (if path specified)
5. **Git commit** (optional)

---

## 🤖 Free AI Integration Options

### Option 1: Google Gemini Flash 2.0 (RECOMMENDED)

**Why:**
- ✅ Free tier: 1,500 requests/day
- ✅ 1.5M context window
- ✅ Fast (~2-3 seconds)
- ✅ API available
- ✅ Good at structured extraction

**Use for:**
- Document summarization
- Property extraction
- Link suggestion
- Key concept identification

### Option 2: Ollama Local Models

**Why:**
- ✅ Completely free
- ✅ No rate limits
- ✅ Privacy (local)
- ✅ Customizable

**Models:**
- `llama3.2:3b` - Fast, good for simple tasks
- `mistral:7b` - Better quality, slower
- `qwen2.5-coder:7b` - Code-focused

**Use for:**
- Batch processing
- Offline usage
- High-volume tasks

### Option 3: Hybrid Approach

**Strategy:**
- Gemini Flash for **real-time** processing (file save)
- Ollama for **batch** processing (nightly sync)
- Fallback chain: Gemini → Ollama → Skip AI

---

## 📁 Directory Structure

```
TTA.dev/
├── docs/
│   ├── guides/
│   │   ├── how-to-create-primitive.md
│   │   └── .logseq-sync.json          # Sync configuration
│   ├── architecture/
│   └── integration/
├── logseq/
│   ├── pages/
│   │   ├── How to Create Primitive.md      # Human-readable
│   │   ├── How to Create Primitive.ai.md   # AI-optimized
│   │   └── Docs Index.md                   # Auto-generated index
│   └── sync/
│       ├── sync-config.json
│       └── last-sync.json
└── packages/
    └── tta-documentation-primitives/       # NEW PACKAGE
        ├── src/
        │   ├── watch_service.py
        │   ├── ai_processor.py
        │   ├── logseq_converter.py
        │   └── primitives/
        │       ├── documentation.py
        │       ├── logseq_sync.py
        │       └── kb_index.py
        └── tests/
```

---

## 🛠️ Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Create `tta-documentation-primitives` package
- [ ] Implement file watcher service
- [ ] Basic markdown → Logseq converter
- [ ] Manual sync command: `tta-docs sync`

### Phase 2: AI Integration (Week 2)
- [ ] Integrate Gemini Flash API
- [ ] Implement property extraction
- [ ] Add link suggestion
- [ ] Generate AI-optimized sections

### Phase 3: TTA.dev Primitives (Week 3)
- [ ] Create `DocumentationPrimitive`
- [ ] Create `LogseqSyncPrimitive`
- [ ] Create `KnowledgeBaseIndexPrimitive`
- [ ] Add to `tta-dev-primitives`

### Phase 4: Automation (Week 4)
- [ ] Auto-sync on file save (VS Code extension)
- [ ] Background sync service
- [ ] Bidirectional sync (Logseq → Docs)
- [ ] Conflict resolution

### Phase 5: Agent Integration (Week 5)
- [ ] Add to Copilot instructions
- [ ] Create documentation templates
- [ ] Agent workflow examples
- [ ] MCP server integration

---

## 🎨 Human vs AI Sections Format

### Human Section (Upper)

```markdown
# How to Create a Primitive

**A step-by-step guide for developers**

## Overview

This guide walks you through creating custom workflow primitives...

## Step 1: Set Up Your Environment

First, ensure you have Python 3.11+ installed...

[Natural language, examples, code blocks, explanations]
```

### AI-Optimized Section (Lower)

```markdown
---

## 🤖 AI-Optimized Metadata

type:: how-to-guide
category:: primitives
difficulty:: intermediate
estimated-time:: 2-4 hours
tags:: #primitives #development #how-to
related:: [[TTA Primitives]], [[InstrumentedPrimitive]], [[Testing Primitives]]
prerequisite:: [[Getting Started]], [[Python Environment Setup]]

### Summary
Comprehensive guide for creating custom workflow primitives in TTA.dev, covering class structure, type annotations, observability integration, and testing.

### Key Concepts
- InstrumentedPrimitive base class
- Type-safe input/output
- WorkflowContext propagation
- Observability integration
- Testing with MockPrimitive

### Code Patterns
```python
class MyPrimitive(InstrumentedPrimitive[TInput, TOutput]):
    async def _execute_impl(self, input_data, context):
        # Implementation
```

### Learning Outcomes
- Understand primitive architecture
- Implement type-safe primitives
- Add automatic observability
- Write comprehensive tests

### Related API
- `InstrumentedPrimitive`
- `WorkflowContext`
- `MockPrimitive`
- `PrimitiveMetrics`

### SEO/Discovery
keywords:: python workflow primitive, custom primitive, tta.dev primitive, observable primitive
search-terms:: how to create primitive, make custom workflow, build primitive
common-questions::
  - How do I create a custom primitive?
  - What base class should I extend?
  - How do I add observability?
```

---

## 🔍 AI Processing Pipeline Detail

### Input: Documentation File

```markdown
# How to Use Cache

Cache primitive improves performance...

## Basic Usage

```python
from tta_dev_primitives.performance import CachePrimitive
cache = CachePrimitive(ttl=3600)
```
```

### AI Processing Steps

1. **Extract Structure:**
   ```json
   {
     "title": "How to Use Cache",
     "type": "how-to",
     "sections": ["Basic Usage"],
     "code_blocks": [...],
     "links": []
   }
   ```

2. **Generate Summary:**
   ```
   "Guide for using CachePrimitive to improve workflow performance with TTL-based caching"
   ```

3. **Extract Concepts:**
   ```
   ["caching", "performance", "TTL", "CachePrimitive"]
   ```

4. **Suggest Links:**
   ```
   [[TTA Primitives]], [[Performance Optimization]], [[Cache Strategies]]
   ```

5. **Create Properties:**
   ```
   type:: how-to-guide
   category:: performance
   related:: [[TTA Primitives/CachePrimitive]]
   ```

### Output: Logseq Page

```markdown
# How to Use Cache

**[Human Section - Original content formatted for Logseq]**

---

## 🤖 AI-Optimized Metadata

type:: how-to-guide
category:: performance
tags:: #caching #performance #primitives
related:: [[TTA Primitives]], [[CachePrimitive]], [[Performance Optimization]]
summary:: Guide for using CachePrimitive to improve workflow performance with TTL-based caching
key-concepts:: caching, performance, TTL, CachePrimitive
```

---

## 🚀 Quick Start Commands (Design)

```bash
# Initialize documentation sync
tta-docs init

# Sync all docs to Logseq
tta-docs sync --all

# Sync specific file
tta-docs sync docs/guides/how-to-create-primitive.md

# Watch for changes (daemon)
tta-docs watch

# Generate AI sections for existing pages
tta-docs enhance --ai

# Validate KB structure
tta-docs validate

# Generate docs index
tta-docs index

# Configuration
tta-docs config --ai-provider gemini
tta-docs config --kb-path logseq/pages
```

---

## 📊 Success Metrics

### Phase 1
- [ ] 100% of docs/ synced to Logseq
- [ ] < 5 second sync time
- [ ] Zero manual Logseq page creation

### Phase 2
- [ ] AI generates 90%+ accurate summaries
- [ ] Auto-link suggestion 80%+ relevant
- [ ] Property extraction 95%+ accurate

### Phase 3
- [ ] Agents use DocumentationPrimitive
- [ ] Zero documentation format errors
- [ ] KB always in sync with docs

### Phase 4
- [ ] Real-time sync < 2 seconds
- [ ] Zero sync conflicts
- [ ] 100% bidirectional sync

---

## 🔐 Security & Privacy

### Data Handling
- **Local-first:** All processing can be done locally (Ollama)
- **API key security:** Gemini key in environment variables
- **No data sent:** Only send to AI if explicitly enabled
- **Git-ignored:** API keys never committed

### Configuration

```json
{
  "ai_provider": "gemini|ollama|none",
  "gemini_api_key": "env:GEMINI_API_KEY",
  "ollama_url": "http://localhost:11434",
  "send_to_ai": true,
  "fallback_chain": ["gemini", "ollama", "none"]
}
```

---

## 🎯 Example Workflows

### Workflow 1: Agent Creates Documentation

```python
from tta_dev_primitives.documentation import create_documentation_workflow

# Agent workflow
doc_workflow = create_documentation_workflow(
    ai_processor="gemini-flash-2.0",
    auto_sync=True,
    generate_ai_section=True
)

# Agent generates doc
result = await doc_workflow.execute({
    "title": "How to Debug Workflows",
    "category": "guides",
    "content": generated_content,
    "target_audience": "intermediate"
}, context)

# Result:
# ✅ docs/guides/how-to-debug-workflows.md created
# ✅ logseq/pages/How to Debug Workflows.md created
# ✅ AI metadata generated
# ✅ Links to related pages added
# ✅ KB index updated
```

### Workflow 2: Developer Writes Doc

```bash
# Developer creates doc
vim docs/guides/new-guide.md

# Save file
:wq

# Auto-sync triggers (if watch service running)
# ✅ Logseq page created
# ✅ AI section generated
# ✅ Links suggested
# ✅ Notification: "Synced to Logseq: [[New Guide]]"
```

### Workflow 3: Batch Sync

```bash
# Nightly batch job
tta-docs sync --all --ai-enhance

# Process:
# 1. Find all docs
# 2. Check if Logseq page exists
# 3. If not, create with AI enhancement
# 4. If exists, check if doc newer
# 5. Update if needed
# 6. Generate reports

# Output:
# ✅ Synced: 47 docs
# ✅ Created: 3 new pages
# ✅ Updated: 5 pages
# ✅ AI enhanced: 8 pages
# ⚠️  Conflicts: 0
```

---

## 🔧 Technical Design

### File Watcher Service

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DocsWatchHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.md'):
            self.sync_to_logseq(event.src_path)

    async def sync_to_logseq(self, doc_path: str):
        # 1. Read doc
        # 2. Process with AI
        # 3. Convert to Logseq
        # 4. Write to KB
        # 5. Update index
```

### AI Processor

```python
class AIProcessor:
    def __init__(self, provider: str = "gemini"):
        self.provider = self._init_provider(provider)

    async def process_document(
        self,
        content: str
    ) -> dict[str, Any]:
        """Extract metadata from document."""

        prompt = f"""
        Analyze this documentation and extract:
        1. Summary (1-2 sentences)
        2. Key concepts (5-10 keywords)
        3. Related topics (suggest Logseq pages)
        4. Category (guide, reference, api, etc.)
        5. Difficulty (beginner, intermediate, advanced)
        6. Prerequisites

        Document:
        {content}

        Return as JSON.
        """

        result = await self.provider.generate(prompt)
        return json.loads(result)
```

### Logseq Converter

```python
class LogseqConverter:
    async def convert(
        self,
        doc_content: str,
        ai_metadata: dict
    ) -> str:
        """Convert doc to Logseq format with AI section."""

        # Human section (formatted original)
        human_section = self._format_for_logseq(doc_content)

        # AI section (structured metadata)
        ai_section = self._generate_ai_section(ai_metadata)

        return f"{human_section}\n\n---\n\n{ai_section}"
```

---

## 📝 Next Steps

See: `local/planning/logseq-docs-integration-todos.md`

---

## 📚 Related

- [[TTA.dev/Architecture]]
- [[Logseq Advanced Features]]
- [[Documentation Strategy]]
- [[AI Integration Patterns]]

---

**Created:** October 31, 2025
**Last Updated:** October 31, 2025
**Status:** Design Phase
**Next:** Create TODO list and start Phase 1
