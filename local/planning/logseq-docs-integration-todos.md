# Logseq-Docs Integration TODOs

**Date:** October 31, 2025
**Project:** Docs-KB Auto-Sync Architecture
**Priority:** HIGH - Architecture Pivot

---

## 🎯 Overview

Building automated bi-directional integration between `docs/` and `logseq/` with AI-powered metadata generation. This will be a core TTA.dev workflow primitive that agents use automatically.

**Design Doc:** `local/planning/logseq-docs-db-integration-design.md`

---

## 📋 Phase 1: Foundation (Week 1)

### TODO 1.1: Create Package Structure

- [ ] **Create `tta-documentation-primitives` package** #dev-todo
  type:: package-creation
  priority:: high
  effort:: 2 hours

  **Actions:**
  ```bash
  mkdir -p packages/tta-documentation-primitives/{src,tests,examples}
  cd packages/tta-documentation-primitives
  touch pyproject.toml README.md
  ```

  **Files to create:**
  - `pyproject.toml` - Package configuration
  - `README.md` - Package documentation
  - `src/tta_documentation_primitives/__init__.py`
  - `src/tta_documentation_primitives/watch_service.py`
  - `src/tta_documentation_primitives/ai_processor.py`
  - `src/tta_documentation_primitives/logseq_converter.py`
  - `src/tta_documentation_primitives/sync_service.py`

### TODO 1.2: Implement File Watcher

- [ ] **Build file watcher service using watchdog** #dev-todo
  type:: implementation
  priority:: high
  effort:: 3-4 hours
  related:: [[Python watchdog]], [[File System Events]]

  **Requirements:**
  - Monitor `docs/`, `packages/*/README.md`, `packages/*/AGENTS.md`
  - Detect `.md` file creation/modification
  - Debounce rapid changes (500ms)
  - Queue sync operations
  - Handle errors gracefully

  **Dependencies:**
  ```bash
  uv add watchdog
  ```

  **Test cases:**
  - New file created → triggers sync
  - File modified → triggers sync
  - File deleted → (no action or mark in KB)
  - Rapid edits → debounced to single sync

### TODO 1.3: Basic Markdown → Logseq Converter

- [ ] **Create markdown to Logseq format converter** #dev-todo
  type:: implementation
  priority:: high
  effort:: 4-5 hours
  related:: [[Logseq Format]], [[Markdown Processing]]

  **Features:**
  - Extract title from H1 or filename
  - Preserve code blocks
  - Convert doc links to Logseq links
  - Add basic properties (created, source-file)
  - Format for Logseq rendering

  **Input:** `docs/guides/how-to-create-primitive.md`
  **Output:** `logseq/pages/How to Create Primitive.md`

  **Test cases:**
  - Headers converted correctly
  - Code blocks preserved
  - Links converted: `[text](../other.md)` → `[[Other]]`
  - Properties added

### TODO 1.4: Manual Sync Command

- [ ] **Implement `tta-docs sync` CLI command** #dev-todo
  type:: implementation
  priority:: high
  effort:: 2-3 hours
  related:: [[CLI Development]], [[Click]]

  **Commands:**
  ```bash
  tta-docs sync --all                    # Sync all docs
  tta-docs sync <file>                   # Sync specific file
  tta-docs sync --dry-run                # Preview changes
  tta-docs validate                      # Check KB structure
  ```

  **Dependencies:**
  ```bash
  uv add click rich
  ```

### TODO 1.5: Configuration System

- [ ] **Create configuration management** #dev-todo
  type:: implementation
  priority:: medium
  effort:: 2 hours

  **Config file:** `.tta-docs.json`
  ```json
  {
    "docs_paths": ["docs/", "packages/*/README.md"],
    "logseq_path": "logseq/pages/",
    "watch_enabled": true,
    "ai_provider": "none",
    "sync_on_save": false
  }
  ```

---

## 📋 Phase 2: AI Integration (Week 2)

### TODO 2.1: Gemini Flash Integration

- [ ] **Integrate Google Gemini Flash API** #dev-todo
  type:: integration
  priority:: high
  effort:: 3-4 hours
  related:: [[Gemini API]], [[AI Integration]]

  **Setup:**
  ```bash
  uv add google-generativeai
  export GEMINI_API_KEY="your-key"
  ```

  **Features:**
  - Async API calls
  - Rate limiting (1500 req/day)
  - Error handling with fallback
  - Caching for repeated content

  **API Methods:**
  - `extract_summary(content)` → summary text
  - `extract_concepts(content)` → list of keywords
  - `suggest_links(content, existing_pages)` → list of page names
  - `categorize(content)` → category string

### TODO 2.2: Property Extraction

- [ ] **Implement AI-powered property extraction** #dev-todo
  type:: implementation
  priority:: high
  effort:: 2-3 hours

  **Extract:**
  - `type::` (guide, reference, api, concept)
  - `category::` (primitives, observability, etc.)
  - `difficulty::` (beginner, intermediate, advanced)
  - `estimated-time::` (from content analysis)
  - `tags::` (relevant hashtags)
  - `related::` (linked pages)
  - `prerequisite::` (required knowledge)

  **Prompt template:**
  ```
  Analyze this documentation and extract structured metadata.
  Return JSON with: type, category, difficulty, estimated_time,
  tags, related_topics, prerequisites, summary, key_concepts.
  ```

### TODO 2.3: Link Suggestion Engine

- [ ] **Build intelligent link suggestion** #dev-todo
  type:: implementation
  priority:: medium
  effort:: 3-4 hours

  **Features:**
  - Scan existing Logseq pages
  - Match content keywords to page names
  - Suggest internal links
  - Avoid over-linking (max 10 per doc)

  **Algorithm:**
  1. Extract keywords from new doc
  2. TF-IDF similarity with existing pages
  3. Threshold filtering (> 0.3 similarity)
  4. Return top N suggestions

### TODO 2.4: AI-Optimized Section Generator

- [ ] **Generate AI-optimized metadata sections** #dev-todo
  type:: implementation
  priority:: high
  effort:: 2-3 hours

  **Output format:**
  ```markdown
  ---

  ## 🤖 AI-Optimized Metadata

  type:: how-to-guide
  category:: primitives
  tags:: #primitives #development
  related:: [[Page1]], [[Page2]]
  summary:: Concise summary
  key-concepts:: concept1, concept2
  ```

### TODO 2.5: Ollama Local Fallback

- [ ] **Add Ollama local AI support** #dev-todo
  type:: integration
  priority:: medium
  effort:: 2-3 hours

  **Setup:**
  ```bash
  # User installs Ollama locally
  ollama pull llama3.2:3b
  ```

  **Fallback chain:**
  1. Try Gemini API
  2. If fails/unavailable → Try Ollama
  3. If fails → Skip AI, basic conversion only

---

## 📋 Phase 3: TTA.dev Primitives (Week 3)

### TODO 3.1: DocumentationPrimitive

- [ ] **Create `DocumentationPrimitive` class** #dev-todo
  type:: primitive-creation
  priority:: high
  effort:: 4-5 hours
  package:: tta-dev-primitives
  related:: [[TTA Primitives]], [[InstrumentedPrimitive]]

  **Interface:**
  ```python
  class DocumentationPrimitive(InstrumentedPrimitive[dict, dict]):
      """Generate documentation with auto-sync to Logseq."""

      def __init__(
          self,
          output_path: str,
          format: str = "markdown",
          logseq_sync: bool = True,
          ai_enhance: bool = True,
          template: str | None = None
      ):
          ...

      async def _execute_impl(
          self,
          input_data: dict,  # {title, content, category}
          context: WorkflowContext
      ) -> dict:  # {file_path, logseq_path, metadata}
          ...
  ```

### TODO 3.2: LogseqSyncPrimitive

- [ ] **Create `LogseqSyncPrimitive` class** #dev-todo
  type:: primitive-creation
  priority:: high
  effort:: 3-4 hours
  package:: tta-dev-primitives

  **Interface:**
  ```python
  class LogseqSyncPrimitive(InstrumentedPrimitive[dict, dict]):
      """Sync documentation to Logseq KB."""

      def __init__(
          self,
          kb_path: str,
          ai_processor: str = "gemini-flash-2.0",
          auto_link: bool = True,
          extract_properties: bool = True
      ):
          ...
  ```

### TODO 3.3: KnowledgeBaseIndexPrimitive

- [ ] **Create `KnowledgeBaseIndexPrimitive` class** #dev-todo
  type:: primitive-creation
  priority:: medium
  effort:: 2-3 hours
  package:: tta-dev-primitives

  **Features:**
  - Update graph connections
  - Generate index pages
  - Maintain topic hierarchies

### TODO 3.4: Testing Suite

- [ ] **Write comprehensive tests** #dev-todo
  type:: testing
  priority:: high
  effort:: 4-5 hours

  **Test coverage:**
  - DocumentationPrimitive execution
  - LogseqSyncPrimitive conversion
  - AI integration (mocked)
  - File operations
  - Error handling

  **Target:** 90%+ coverage

### TODO 3.5: Example Workflows

- [ ] **Create example workflows** #dev-todo
  type:: documentation
  priority:: medium
  effort:: 2-3 hours

  **Examples:**
  - `examples/simple_doc_generation.py`
  - `examples/agent_documentation_workflow.py`
  - `examples/batch_sync.py`

---

## 📋 Phase 4: Automation (Week 4)

### TODO 4.1: VS Code Extension Integration

- [ ] **Add VS Code save hook** #dev-todo
  type:: integration
  priority:: high
  effort:: 3-4 hours

  **Approaches:**
  1. VS Code extension (TypeScript)
  2. External watcher + VS Code task
  3. Git pre-commit hook

  **Preferred:** External watcher (simpler)

### TODO 4.2: Background Sync Service

- [ ] **Create background daemon** #dev-todo
  type:: implementation
  priority:: high
  effort:: 3-4 hours

  **Commands:**
  ```bash
  tta-docs watch start           # Start daemon
  tta-docs watch stop            # Stop daemon
  tta-docs watch status          # Check status
  tta-docs watch logs            # View logs
  ```

  **Features:**
  - Systemd/launchd service
  - Log to file
  - Graceful shutdown
  - Auto-restart on error

### TODO 4.3: Bidirectional Sync (Logseq → Docs)

- [ ] **Implement reverse sync** #dev-todo
  type:: implementation
  priority:: medium
  effort:: 4-5 hours

  **Trigger:** Logseq page has `sync-to-docs:: true` property

  **Process:**
  1. Detect Logseq page change
  2. Extract human section
  3. Convert to markdown
  4. Write to docs/ (if `source-file::` exists)
  5. Preserve front matter

### TODO 4.4: Conflict Resolution

- [ ] **Handle sync conflicts** #dev-todo
  type:: implementation
  priority:: high
  effort:: 3-4 hours

  **Conflicts:**
  - Doc and Logseq both modified
  - Different content in human sections

  **Strategy:**
  - Compare timestamps
  - Create conflict markers
  - Prompt user for resolution
  - Option to always prefer docs/ or logseq/

### TODO 4.5: Notification System

- [ ] **Add sync notifications** #dev-todo
  type:: implementation
  priority:: low
  effort:: 2 hours

  **Methods:**
  - Terminal notification
  - VS Code notification
  - Desktop notification (notify-send)

  **Events:**
  - Sync complete
  - Sync error
  - Conflict detected

---

## 📋 Phase 5: Agent Integration (Week 5)

### TODO 5.1: Update Copilot Instructions

- [ ] **Add to `.github/copilot-instructions.md`** #dev-todo
  type:: documentation
  priority:: high
  effort:: 2 hours

  **Add sections:**
  - How to use DocumentationPrimitive
  - When to sync to Logseq
  - Documentation format standards
  - Example usage

### TODO 5.2: Documentation Templates

- [ ] **Create doc templates** #dev-todo
  type:: documentation
  priority:: medium
  effort:: 2-3 hours

  **Templates:**
  - `templates/how-to-guide.md`
  - `templates/api-reference.md`
  - `templates/concept-explanation.md`
  - `templates/architecture-decision.md`

### TODO 5.3: Agent Workflow Examples

- [ ] **Write agent integration examples** #dev-todo
  type:: documentation
  priority:: medium
  effort:: 2-3 hours

  **Examples:**
  - Agent generates how-to guide
  - Agent updates API docs
  - Agent creates architecture decision record
  - Agent batch-syncs workspace

### TODO 5.4: MCP Server Integration

- [ ] **Add documentation tools to MCP server** #dev-todo
  type:: integration
  priority:: medium
  effort:: 3-4 hours

  **MCP Tools:**
  - `create_documentation` - Create doc with auto-sync
  - `sync_to_logseq` - Manual sync trigger
  - `search_kb` - Search Logseq KB
  - `get_related_docs` - Find related documentation

### TODO 5.5: Production Testing

- [ ] **Test with real agent workflows** #dev-todo
  type:: testing
  priority:: high
  effort:: 4-5 hours

  **Test scenarios:**
  - Agent creates 10 docs
  - All sync correctly
  - AI metadata accurate
  - Links work
  - No conflicts

---

## 📋 Infrastructure & Polish

### TODO 6.1: CI/CD Integration

- [ ] **Add sync validation to CI** #dev-todo
  type:: infrastructure
  priority:: medium
  effort:: 2-3 hours

  **CI checks:**
  - All docs have Logseq pages
  - No broken links
  - AI metadata valid
  - No sync conflicts

### TODO 6.2: Performance Optimization

- [ ] **Optimize sync performance** #dev-todo
  type:: optimization
  priority:: medium
  effort:: 3-4 hours

  **Targets:**
  - Single file sync < 2 seconds
  - Batch sync 100 files < 30 seconds
  - AI processing < 1 second per doc

  **Techniques:**
  - Parallel processing
  - Caching
  - Incremental sync

### TODO 6.3: Error Handling & Recovery

- [ ] **Robust error handling** #dev-todo
  type:: implementation
  priority:: high
  effort:: 2-3 hours

  **Handle:**
  - API rate limits
  - File system errors
  - Network failures
  - Invalid markdown
  - Encoding issues

### TODO 6.4: Documentation

- [ ] **Write comprehensive docs** #dev-todo
  type:: documentation
  priority:: high
  effort:: 4-5 hours

  **Docs to create:**
  - `packages/tta-documentation-primitives/README.md`
  - `docs/guides/how-to-use-doc-sync.md`
  - `docs/architecture/docs-kb-integration.md`
  - API reference
  - Troubleshooting guide

### TODO 6.5: User Onboarding

- [ ] **Create setup wizard** #dev-todo
  type:: implementation
  priority:: medium
  effort:: 2-3 hours

  **Command:** `tta-docs init`

  **Steps:**
  1. Detect docs/ and logseq/
  2. Offer to create .tta-docs.json
  3. Choose AI provider (Gemini/Ollama/None)
  4. Test sync with sample doc
  5. Start watch service

---

## 🎯 Success Criteria

### Phase 1 Complete When:

- [x] Package structure created
- [ ] File watcher working
- [ ] Basic markdown → Logseq converter functional
- [ ] Manual sync command works
- [ ] Can sync single doc successfully

### Phase 2 Complete When:

- [ ] Gemini API integrated
- [ ] AI metadata extraction works
- [ ] Link suggestions relevant (80%+)
- [ ] AI-optimized sections generated
- [ ] Ollama fallback functional

### Phase 3 Complete When:

- [ ] All 3 primitives implemented
- [ ] Tests passing (90%+ coverage)
- [ ] Examples working
- [ ] Primitives added to tta-dev-primitives

### Phase 4 Complete When:

- [ ] Auto-sync on save works
- [ ] Background daemon stable
- [ ] Bidirectional sync functional
- [ ] Conflicts resolved properly
- [ ] Notifications working

### Phase 5 Complete When:

- [ ] Copilot instructions updated
- [ ] Templates created
- [ ] Agent examples working
- [ ] MCP server integrated
- [ ] Production tested

---

## 📊 Time Estimates

| Phase | Estimated Time | Priority |
|-------|---------------|----------|
| **Phase 1: Foundation** | 12-15 hours | HIGH |
| **Phase 2: AI Integration** | 10-13 hours | HIGH |
| **Phase 3: TTA.dev Primitives** | 15-18 hours | HIGH |
| **Phase 4: Automation** | 13-16 hours | MEDIUM |
| **Phase 5: Agent Integration** | 11-14 hours | MEDIUM |
| **Infrastructure & Polish** | 13-16 hours | MEDIUM |
| **Total** | **74-92 hours** | |

**Note:** ~2-3 weeks full-time or 4-6 weeks part-time

---

## 🚀 Quick Start (After Phase 1)

```bash
# Install package
cd packages/tta-documentation-primitives
uv sync

# Initialize
tta-docs init

# Sync all docs
tta-docs sync --all

# Start watching
tta-docs watch start

# Create doc (auto-syncs)
vim docs/guides/new-guide.md
# Save → Logseq page created!

# Check status
tta-docs watch status
```

---

## 📝 Notes

### Design Decisions

1. **AI Provider Choice:** Gemini Flash (free, fast, good quality)
2. **File Format:** Markdown everywhere (Logseq-compatible)
3. **Sync Direction:** Primarily docs → Logseq (source of truth: docs)
4. **Properties:** Logseq properties over YAML front matter
5. **Links:** Prefer Logseq `[[links]]` for discoverability

### Future Enhancements

- [ ] Vector embeddings for semantic search
- [ ] Automatic diagram generation
- [ ] Multi-language support
- [ ] Web UI for sync management
- [ ] Slack/Discord notifications
- [ ] Git integration (auto-commit on sync)

---

## 🔗 Related

- [[Logseq Advanced Features]]
- [[TTA.dev/Architecture]]
- [[Documentation Strategy]]
- [[Phase 4 Architecture Documentation]]

---

**Created:** October 31, 2025
**Last Updated:** October 31, 2025
**Status:** Active TODO list
**Next Action:** Start Phase 1.1 - Create package structure
