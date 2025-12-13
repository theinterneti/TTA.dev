type:: index
status:: active
created:: 2025-12-04

# TTA.dev Documentation Index

**Central index of all documentation in the `docs/` directory (323+ files).**

---

## Quick Links

| Category | Path | Description |
|----------|------|-------------|
| **Architecture** | `docs/architecture/` | System design, patterns |
| **Development** | `docs/development/` | Coding standards, guides |
| **Guides** | `docs/guides/` | How-to tutorials |
| **Runbooks** | `docs/runbooks/` | Operational procedures |
| **Quickstart** | `docs/quickstart/` | Getting started |
| **Integration** | `docs/integration/` | Service integrations |

---

## Architecture (`docs/architecture/`)

System design and architectural decisions:

| Document | Description |
|----------|-------------|
| `MONOREPO_STRUCTURE.md` | Repository organization |
| `SYSTEM_DESIGN.md` | Overall system architecture |
| `PRIMITIVE_PATTERNS.md` | Primitive design patterns |
| `OBSERVABILITY_ARCHITECTURE.md` | Monitoring stack |
| `UNIVERSAL_LLM_ARCHITECTURE.md` | LLM integration |
| `AGENTIC_RUNTIMES.md` | Agent runtime design |
| `KNOWLEDGE_BASE_INTEGRATION.md` | KB integration patterns |

---

## Development (`docs/development/`)

Development practices and standards:

| Document | Description |
|----------|-------------|
| `CodingStandards.md` | Code style and conventions |
| `Development_Guide.md` | Developer onboarding |
| `Testing_Guide.md` | Testing best practices |
| `MULTI_AGENT_OVERSIGHT.md` | Agent coordination |
| `git/*.md` | Git worktree documentation |

### Git Worktree Docs

| Document | Description |
|----------|-------------|
| `git/WORKTREE_COORDINATION_QUICKSTART.md` | Quick reference |
| `git/WORKTREE_COORDINATION_PROTOCOL.md` | Full protocol |
| `git/GIT_QUICKREF.md` | Git command reference |

---

## Guides (`docs/guides/`)

Step-by-step tutorials:

| Document | Description |
|----------|-------------|
| `GETTING_STARTED.md` | Initial setup |
| `WORKFLOW_COMPOSITION.md` | Building workflows |
| `TESTING_PRIMITIVES.md` | Testing guide |

---

## Runbooks (`docs/runbooks/`)

Operational procedures:

| Document | Description |
|----------|-------------|
| `INCIDENT_RESPONSE.md` | Incident handling |
| `DEPLOYMENT.md` | Deployment procedures |
| `MONITORING.md` | Monitoring setup |

---

## Status Reports (`docs/status-reports/`)

Completion reports for major features:

| Document | Description |
|----------|-------------|
| `ADAPTIVE_PRIMITIVES_PHASES_1_3_COMPLETE.md` | Adaptive primitives |
| `CUSTOM_EXCEPTIONS_COMPLETE.md` | Exception handling |
| `OBSERVABILITY_SETUP_COMPLETE.md` | Observability |
| `PROMETHEUS_METRICS_INTEGRATION_COMPLETE.md` | Metrics |
| `TYPE_ANNOTATIONS_ENHANCEMENT_COMPLETE.md` | Type safety |

---

## Secrets Management

| Document | Description |
|----------|-------------|
| `SECRETS_MANAGEMENT.md` | Full secrets guide |
| `SECRETS_MANAGEMENT_GUIDE.md` | Detailed guide |
| `SECRETS_QUICK_REF.md` | Quick reference |

---

## Integration (`docs/integration/`)

External service integrations:

| Document | Description |
|----------|-------------|
| `MCP_INTEGRATION.md` | Model Context Protocol |
| `OPENTELEMETRY_SETUP.md` | Tracing setup |
| `REDIS_INTEGRATION.md` | Redis caching |

---

## Research (`docs/research/`)

Research and exploration:

| Document | Description |
|----------|-------------|
| `AI_CAPABILITIES.md` | AI capabilities |
| `AGENT_ARCHITECTURES.md` | Agent patterns |

---

## Browsing Tips

```bash
# Find docs by topic
grep -r "retry" docs/ --include="*.md" -l

# List docs by size
du -h docs/**/*.md | sort -h | tail -20

# Recent docs
find docs/ -name "*.md" -mtime -7
```

---

## Related

- [[TTA.dev/Architecture]] - Architecture overview
- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Agent Workflow]] - Agent workflow guide

---

**Tags:** #index #documentation #reference


---
**Logseq:** [[TTA.dev/_archive/Logseq_backup/Pages_root/Tta.dev___documentation index]]
