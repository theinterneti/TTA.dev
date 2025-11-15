# TTA.dev High-Priority TODO Summary

This document summarizes high-priority TODOs identified across the TTA.dev codebase, excluding those related to core primitive testing which are tracked in a dedicated GitHub issue.

## 1. Logseq MCP Integration

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/knowledge/knowledge_base.py`
**Description:** Multiple TODOs indicate incomplete integration with the Logseq Model Context Protocol (MCP) search and related pages tools. The `KnowledgeBasePrimitive` currently returns empty lists for search operations, suggesting the MCP calls are placeholders.
**Action Needed:** Implement full integration with Logseq MCP to enable robust knowledge management capabilities.

## 2. Incomplete LLM Provider Integrations

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/research/free_tier_research.py`
**Description:** The `FreeTierResearchPrimitive` has notes indicating that `Google Gemini` and `OpenRouter BYOK` LLM providers are "Not yet implemented."
**Action Needed:** Implement the necessary integrations for these LLM providers to expand the primitive's capabilities.

## 3. Redis Search Implementation

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/performance/memory.py`
**Description:** The `MemoryPrimitive` currently falls back to in-memory search for Redis, with a debug message stating "Redis search not implemented." This indicates that semantic search capabilities using RediSearch are a future enhancement.
**Action Needed:** Implement RediSearch integration for the `MemoryPrimitive` to enable more advanced and efficient search functionalities when using Redis.

## 4. Redis Clear Implementation

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/performance/memory.py`
**Description:** The `MemoryPrimitive`'s `clear` method for Redis is "not implemented (would clear entire DB)," indicating a lack of proper namespacing or a safe clear mechanism for production use.
**Action Needed:** Implement a safe and namespaced Redis clear operation for the `MemoryPrimitive` to prevent accidental data loss in a production environment.

## 5. General Documentation Updates

**Files:** Various `.md` files (e.g., `packages/tta-dev-primitives/README.md`, `packages/tta-dev-primitives/apm.yml`)
**Description:** Numerous general TODOs exist across markdown documentation files. Some are critical for clarifying the distinction between development tooling and player-facing components.
**Action Needed:** Review and address outstanding documentation TODOs to improve clarity, completeness, and user understanding of the project.
