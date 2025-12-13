type:: specification
status:: draft
version:: 1.0.0

- # Agentic KB Workflow Specification

  **Design specification for the TTA.dev "Second Mind" - an AI-powered knowledge base automation system**

  type:: specification
  status:: draft
  version:: 1.0.0
  created:: [[2025-12-04]]

  ---

  ## Executive Summary

  The **Agentic KB Workflow** (codename: "Second Mind") is an automated system that enables AI agents to generate, maintain, and evolve the TTA.dev knowledge base. This specification defines the architecture, triggers, workflows, and quality controls for automatic KB management.

  **Goals:**
  🤖 Automatic KB entry generation from code changes
  🔗 Bidirectional code↔KB link maintenance
  📊 Quality validation and consistency enforcement
  🔄 Cross-repository knowledge synchronization

  **See:** [[TTA.dev/Architecture]], [[KB Automation]]

  ---

  ## Architecture Overview

  ### System Components

  ```
  ┌─────────────────────────────────────────────────────────────────┐
  │                    TTA.dev Second Mind                          │
  ├─────────────────────────────────────────────────────────────────┤
  │                                                                 │
  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
  │  │   Trigger   │───▶│  Processor  │───▶│  Generator  │         │
  │  │   Engine    │    │   Engine    │    │   Engine    │         │
  │  └─────────────┘    └─────────────┘    └─────────────┘         │
  │         │                  │                  │                 │
  │         ▼                  ▼                  ▼                 │
  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
  │  │   Event     │    │   Context   │    │   KB Entry  │         │
  │  │   Queue     │    │   Builder   │    │   Writer    │         │
  │  └─────────────┘    └─────────────┘    └─────────────┘         │
  │                            │                  │                 │
  │                            ▼                  ▼                 │
  │                     ┌─────────────┐    ┌─────────────┐         │
  │                     │  Validator  │◀───│   Logseq    │         │
  │                     │   Engine    │    │   Graph     │         │
  │                     └─────────────┘    └─────────────┘         │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘
  ```

  ### Data Flow

  1. **Trigger Detection** → Event captured (git commit, file change, etc.)
  2. **Context Building** → Gather relevant code, docs, and KB context
  3. **Content Generation** → AI generates KB entry content
  4. **Validation** → Quality checks and link verification
  5. **KB Update** → Write to Logseq graph via MCP server

  ---

  ## Trigger Conditions

  ### 1. Code Change Triggers

  **New Primitive Created:**
  ```yaml
  trigger:
    type: file_created
    pattern: "packages/*/src/**/*Primitive.py"
    action: create_primitive_kb_page
    template: primitive_template
  ```

  **Primitive Modified:**
  ```yaml
  trigger:
    type: file_modified
    pattern: "packages/*/src/**/*Primitive.py"
    action: update_primitive_kb_page
    sections_to_update:
  API Reference
  Examples
  Last Updated
  ```

  **New Package Created:**
  ```yaml
  trigger:
    type: directory_created
    pattern: "packages/*"
    conditions:
  has_pyproject_toml: true
    action: create_package_kb_page
    template: package_template
  ```

  ### 2. Documentation Triggers

  **README Updated:**
  ```yaml
  trigger:
    type: file_modified
    pattern: "**/README.md"
    action: sync_readme_to_kb
    target_page: "{{package_name}}"
  ```

  **Docstring Changed:**
  ```yaml
  trigger:
    type: docstring_modified
    pattern: "packages/*/src/**/*.py"
    action: update_api_reference
    extract:
  function_signature
  docstring
  type_hints
  ```

  ### 3. Git Triggers

  **Commit with KB Tag:**
  ```yaml
  trigger:
    type: git_commit
    message_pattern: "\\[kb\\]|\\[doc\\]"
    action: process_kb_commit
    extract_from_message: true
  ```

  **PR Merged:**
  ```yaml
  trigger:
    type: pr_merged
    branches:
  main
  develop
    action: generate_changelog_entry
    update_pages:
  CHANGELOG
  "{{affected_packages}}"
  ```

  ### 4. Session Triggers

  **Agent Session Start:**
  ```yaml
  trigger:
    type: session_start
    agent: any
    action: create_session_page
    template: session_template
  ```

  **Agent Session End:**
  ```yaml
  trigger:
    type: session_end
    agent: any
    action: finalize_session_page
    sections_to_add:
  Summary
  Outcomes
  Next Steps
  ```

  ---

  ## KB Entry Generation Templates

  ### Primitive Template

  ```markdown
  # {{primitive_name}}

  type:: Primitive
  package:: [[{{package_name}}]]
  stability:: [[{{stability}}]]
  created:: [[{{date}}]]

  ---

  ## Overview

  {{auto_generated_overview}}

  **Source:** `{{source_path}}`

  ---

  ## Use Cases

  {{auto_generated_use_cases}}

  ---

  ## API Reference

  ### Constructor

  ```python
  {{constructor_signature}}
  ```

  **Parameters:**
  {{auto_generated_parameters}}

  ### Methods

  {{auto_generated_methods}}

  ---

  ## Examples

  ### Basic Usage

  ```python
  {{basic_example}}
  ```

  ### With Composition

  ```python
  {{composition_example}}
  ```

  ---

  ## Composition Patterns

  {{auto_generated_composition_patterns}}

  ---

  ## Related Content

  [[{{related_primitive_1}}]]
  [[{{related_primitive_2}}]]
  [[{{pattern_page}}]]

  ---

  **Tags:** #primitive #{{package_tag}} #{{stability_tag}}

  **Last Updated:** {{date}}
  **Source:** `{{source_path}}`
  ```

  ### Session Template

  ```markdown
  # Session: {{session_id}}

  type:: Session
  agent:: [[{{agent_name}}]]
  worktree:: {{worktree}}
  started:: {{start_time}}
  status:: in-progress

  ---

  ## Context

  **Branch:** `{{branch_name}}`
  **Focus:** {{session_focus}}

  ---

  ## Goals

  [ ] {{goal_1}}
  [ ] {{goal_2}}

  ---

  ## Progress

  ### {{timestamp}}
  {{progress_entry}}

  ---

  ## Files Modified

  `{{file_1}}`
  `{{file_2}}`

  ---

  ## Decisions Made

  {{decisions}}

  ---

  ## Related

  [[{{related_session}}]]
  [[{{related_kb_page}}]]

  ---

  **Tags:** #session #{{agent_tag}} #{{date_tag}}
  ```

  ### Package Template

  ```markdown
  # {{package_name}}

  type:: Package
  status:: [[{{status}}]]
  version:: {{version}}
  created:: [[{{date}}]]

  ---

  ## Overview

  {{auto_generated_overview}}

  **Source:** `packages/{{package_name}}/`

  ---

  ## Installation

  ```bash
  pip install {{package_name}}
  ```

  ---

  ## Key Components

  {{auto_generated_components}}

  ---

  ## Dependencies

  {{auto_generated_dependencies}}

  ---

  ## Related Packages

  [[{{related_package_1}}]]
  [[{{related_package_2}}]]

  ---

  **Tags:** #package #{{status_tag}}

  **Last Updated:** {{date}}
  ```

  ---

  ## Cross-Reference Maintenance

  ### Code → KB Links

  **Convention:** Add `# See: [[KB Page]]` comments in code

  ```python
  # packages/tta-dev-primitives/src/primitives/cache.py

  class CachePrimitive(WorkflowPrimitive):
      """Cache primitive for workflow results.

      # See: [[TTA.dev/Primitives/CachePrimitive]]
      """
      pass
  ```

  **Automation:**
  ```yaml
  cross_reference:
    code_to_kb:
      pattern: "# See: \\[\\[(.+)\\]\\]"
      action: validate_kb_link
      on_missing: create_stub_page
  ```

  ### KB → Code Links

  **Convention:** Add `Source: path/to/file.py` in KB pages

  ```markdown
  ## Source

  **Source:** `packages/tta-dev-primitives/src/primitives/cache.py`
  ```

  **Automation:**
  ```yaml
  cross_reference:
    kb_to_code:
      pattern: "\\*\\*Source:\\*\\* `(.+)`"
      action: validate_source_exists
      on_missing: flag_for_review
  ```

  ### Bidirectional Sync

  ```yaml
  sync:
    schedule: "*/15 * * * *"  # Every 15 minutes
    actions:
  validate_all_cross_references
  update_stale_kb_pages
  generate_missing_pages
  report_broken_links
  ```

  ---

  ## Quality Validation

  ### Validation Rules

  **1. Structure Validation:**
  ```yaml
  validation:
    structure:
      required_sections:
  Overview
  "API Reference|Usage"
  "Related|See Also"
      required_properties:
  type
  created
      max_heading_depth: 4
  ```

  **2. Link Validation:**
  ```yaml
  validation:
    links:
      check_internal_links: true
      check_external_links: false
      allowed_broken_patterns:
  "YYYY-MM-DD"  # Template placeholders
  "Primitive1"  # Example placeholders
  ```

  **3. Content Validation:**
  ```yaml
  validation:
    content:
      min_overview_length: 50
      require_code_examples: true
      require_tags: true
      max_page_length: 500  # lines
  ```

  ### Quality Metrics

  ```promql
  # KB page quality score
  kb_page_quality_score{page="CachePrimitive"}

  # Broken link count
  kb_broken_links_total{severity="error|warning"}

  # Cross-reference coverage
  kb_cross_reference_coverage_percent

  # Page freshness (days since update)
  kb_page_age_days{page="CachePrimitive"}
  ```

  ---

  ## Repository Hierarchy

  ### Source of Truth Flow

  ```
  GitHub (upstream/remote)
         ↓
  TTA.dev (main repository - primary source of truth)
         ↓
  ┌──────┴──────┬──────────────┬──────────────┐
  ↓             ↓              ↓              ↓
  TTA.dev-      TTA.dev-       TTA.dev-       TTA.dev-
  augment       cline          copilot        cursor
  (agent        (agent         (agent         (agent
  worktree)     worktree)      worktree)      worktree)
         ↓             ↓              ↓              ↓
         └─────────────┴──────────────┴──────────────┘
                              ↓
                        TTA-notes
                (centralized KB aggregation)
  ```

  ### Sync Rules

  **Worktree → TTA.dev:**
  ```yaml
  sync:
    direction: worktree_to_main
    conditions:
  page_status: stable
  validation_passed: true
  review_approved: true
    action: merge_to_main
  ```

  **TTA.dev → TTA-notes:**
  ```yaml
  sync:
    direction: main_to_notes
    schedule: daily
    action: aggregate_kb_content
    include:
  stable_pages
  session_summaries
  cross_references
  ```

  ---

  ## Implementation Phases

  ### Phase 1: Foundation (Week 1-2)

  [ ] Set up trigger detection infrastructure
  [ ] Implement basic file watcher
  [ ] Create template engine
  [ ] Integrate with Logseq MCP server

  ### Phase 2: Generation (Week 3-4)

  [ ] Implement primitive page generator
  [ ] Implement session page generator
  [ ] Add docstring extraction
  [ ] Create cross-reference builder

  ### Phase 3: Validation (Week 5-6)

  [ ] Implement link validator
  [ ] Add structure validator
  [ ] Create quality metrics
  [ ] Build validation dashboard

  ### Phase 4: Sync (Week 7-8)

  [ ] Implement worktree sync
  [ ] Add TTA-notes aggregation
  [ ] Create conflict resolution
  [ ] Build sync monitoring

  ---

  ## Integration Points

  ### Existing Tools

  **tta-kb-automation package:**
  `LinkValidator` - Validate KB links
  `CrossReferenceBuilder` - Build code↔KB links
  `SessionContextBuilder` - Generate session context
  `TODOSync` - Sync TODOs with KB

  **Logseq MCP Server:**
  `query_logseq-graph` - Search KB
  `page_logseq-graph` - Page operations
  `block_logseq-graph` - Block operations

  ### New Components Needed

  1. **TriggerEngine** - Detect and queue events
  2. **ContextBuilder** - Gather relevant context
  3. **ContentGenerator** - AI-powered content generation
  4. **ValidationEngine** - Quality checks
  5. **SyncManager** - Cross-repository sync

  ---

  ## Configuration

  ### Environment Variables

  ```bash
  # KB Automation
  TTA_KB_AUTOMATION_ENABLED=true
  TTA_KB_TRIGGER_DEBOUNCE_MS=5000
  TTA_KB_VALIDATION_STRICT=true

  # LLM Configuration
  TTA_KB_LLM_PROVIDER=anthropic
  TTA_KB_LLM_MODEL=claude-3-sonnet
  TTA_KB_LLM_MAX_TOKENS=4096

  # Sync Configuration
  TTA_KB_SYNC_ENABLED=true
  TTA_KB_SYNC_INTERVAL_MINUTES=15
  TTA_KB_SYNC_CONFLICT_STRATEGY=manual
  ```

  ### Configuration File

  ```yaml
  # .tta-kb-config.yaml
  kb_automation:
    enabled: true

    triggers:
      file_watcher:
        enabled: true
        patterns:
  "packages/*/src/**/*.py"
  "**/README.md"
        debounce_ms: 5000

      git_hooks:
        enabled: true
        hooks:
  pre-commit
  post-merge

    generation:
      llm:
        provider: anthropic
        model: claude-3-sonnet
        temperature: 0.3
      templates_dir: .tta-kb-templates/

    validation:
      strict: true
      rules:
  structure
  links
  content

    sync:
      enabled: true
      interval_minutes: 15
      repositories:
  TTA.dev
  TTA.dev-augment
  TTA.dev-cline
  TTA-notes
  ```

  ---

  ## Error Handling

  ### Failure Modes

  **1. Generation Failure:**
  ```yaml
  on_generation_failure:
    action: create_stub_page
    notify: true
    retry:
      max_attempts: 3
      backoff: exponential
  ```

  **2. Validation Failure:**
  ```yaml
  on_validation_failure:
    action: flag_for_review
    create_todo: true
    severity: warning
  ```

  **3. Sync Conflict:**
  ```yaml
  on_sync_conflict:
    strategy: manual
    action: create_conflict_page
    notify: true
  ```

  ---

  ## Monitoring

  ### Metrics

  ```promql
  # Trigger events processed
  kb_trigger_events_total{type="file_created|file_modified|git_commit"}

  # Generation success rate
  kb_generation_success_rate

  # Validation pass rate
  kb_validation_pass_rate

  # Sync operations
  kb_sync_operations_total{status="success|failure|conflict"}

  # Page freshness
  kb_page_freshness_days{page="..."}
  ```

  ### Alerts

  ```yaml
  alerts:
  name: kb_generation_failure_rate_high
      condition: kb_generation_success_rate < 0.9
      severity: warning

  name: kb_broken_links_critical
      condition: kb_broken_links_total{severity="error"} > 10
      severity: critical

  name: kb_sync_failure
      condition: kb_sync_operations_total{status="failure"} > 0
      severity: warning
  ```

  ---

  ## Security Considerations

  ### Access Control

  KB automation runs with limited permissions
  No direct access to secrets or credentials
  All changes are auditable via git history

  ### Content Safety

  AI-generated content is validated before commit
  Sensitive information detection
  No automatic publication without review

  ---

  ## Related Documentation

  [[TTA.dev/Architecture]] - System architecture
  [[KB Automation]] - Existing automation tools
  [[TTA.dev/Observability]] - Monitoring setup
  [[AGENTS]] - Agent instructions
  [[TTA.dev/Multi-Agent Patterns]] - Multi-agent coordination

  ---

  **Tags:** #specification #kb-automation #second-mind #agentic #architecture

  **Last Updated:** 2025-12-04
  **Maintained by:** TTA.dev Team
  **Status:** Draft - Pending Review


---
**Logseq:** [[TTA.dev/_archive/Logseq_backup/Pages_root/Tta.dev___agentic kb workflow specification]]
