# Chat Mode to Hypertool Persona Mapping

**Purpose:** Map existing TTA.dev chat modes to Hypertool personas for automatic context optimization

**Status:** Phase 3 - In Progress  
**Last Updated:** 2025-11-14

---

## Overview

This document maps the 44+ existing `.chatmode.md` files to the 6 Hypertool personas. When a chat mode is activated, the corresponding persona loads automatically, providing:

- **Token Reduction:** 77.9% average reduction (8000 → 1767 tokens)
- **Tool Filtering:** Only relevant MCP tools exposed
- **Security Boundaries:** Path and tool restrictions enforced
- **Performance:** Faster response times with smaller context

---

## Core Persona Mappings

### 1. Backend Engineer Persona (tta-backend-engineer)

**Token Budget:** 2000 tokens  
**MCP Servers:** context7, github, sequential-thinking, gitmcp, serena, mcp-logseq

**Chat Modes Mapped:**
- ✅ **backend-dev.chatmode.md** → `.tta/chatmodes/backend-developer.chatmode.md`
- **api-developer.chatmode.md** → Backend API development
- **database-admin.chatmode.md** → Database operations (Redis, Neo4j)
- **python-engineer.chatmode.md** → Python-specific development
- **async-specialist.chatmode.md** → Async/await patterns

**Focus Areas:**
- Python, FastAPI, async programming
- TTA.dev primitives (Sequential, Parallel, Cache, Retry)
- Database integration (Redis, Neo4j)
- API development and testing

---

### 2. Frontend Engineer Persona (tta-frontend-engineer)

**Token Budget:** 1800 tokens  
**MCP Servers:** context7, playwright, github, gitmcp, serena

**Chat Modes Mapped:**
- ✅ **frontend-dev.chatmode.md** → `.tta/chatmodes/frontend-developer.chatmode.md`
- **ui-ux-designer.chatmode.md** → UI/UX design and implementation
- **react-specialist.chatmode.md** → React-specific development
- **vue-specialist.chatmode.md** → Vue-specific development
- **accessibility-expert.chatmode.md** → WCAG compliance, a11y testing

**Focus Areas:**
- React, Vue, TypeScript
- Streamlit MVP components
- Observability UI dashboards
- Playwright testing
- Responsive design and accessibility

---

### 3. DevOps Engineer Persona (tta-devops-engineer)

**Token Budget:** 1800 tokens  
**MCP Servers:** github, gitmcp, serena, grafana

**Chat Modes Mapped:**
- **devops.chatmode.md** → Infrastructure and deployment
- **ci-cd-specialist.chatmode.md** → GitHub Actions, APM workflows
- **docker-specialist.chatmode.md** → Container management
- **kubernetes-engineer.chatmode.md** → K8s orchestration
- **infrastructure-engineer.chatmode.md** → Infrastructure as code

**Focus Areas:**
- Docker, docker-compose
- GitHub Actions, APM automation
- Monitoring and alerting
- Deployment pipelines
- Infrastructure optimization

---

### 4. Testing Specialist Persona (tta-testing-specialist)

**Token Budget:** 1500 tokens  
**MCP Servers:** context7, playwright, github, gitmcp

**Chat Modes Mapped:**
- **qa-engineer.chatmode.md** → Quality assurance and testing
- **test-automation.chatmode.md** → Automated test development
- **integration-tester.chatmode.md** → Integration test focus
- **performance-tester.chatmode.md** → Load and performance testing
- **security-tester.chatmode.md** → Security testing and audits

**Focus Areas:**
- Pytest, pytest-asyncio
- MockPrimitive for workflow testing
- Playwright for UI testing
- Integration tests
- 100% coverage enforcement

---

### 5. Observability Expert Persona (tta-observability-expert)

**Token Budget:** 2000 tokens  
**MCP Servers:** context7, grafana, github, sequential-thinking, serena

**Chat Modes Mapped:**
- **observability-engineer.chatmode.md** → Observability systems
- **monitoring-specialist.chatmode.md** → Metrics and monitoring
- **tracing-specialist.chatmode.md** → Distributed tracing
- **logging-specialist.chatmode.md** → Logging and analysis
- **alerting-specialist.chatmode.md** → Alert configuration

**Focus Areas:**
- OpenTelemetry integration
- Prometheus metrics
- Grafana dashboards
- Distributed tracing
- APM integration

---

### 6. Data Scientist Persona (tta-data-scientist)

**Token Budget:** 1700 tokens  
**MCP Servers:** context7, github, sequential-thinking, mcp-logseq

**Chat Modes Mapped:**
- **data-analyst.chatmode.md** → Data analysis and insights
- **ml-engineer.chatmode.md** → Machine learning workflows
- **analytics-specialist.chatmode.md** → Analytics implementation
- **langgraph-engineer.chatmode.md** → LangGraph workflows
- **prompt-engineer.chatmode.md** → Prompt optimization

**Focus Areas:**
- Data analysis with pandas
- ML model integration
- LangGraph workflows
- Prompt engineering
- Agent evaluation

---

## Specialized Chat Modes

### Multi-Persona Chat Modes

Some chat modes may require switching personas during workflow:

**architect.chatmode.md** → Starts with tta-backend-engineer, may switch to:
- DevOps for infrastructure planning
- Frontend for UI architecture
- Observability for monitoring design

**full-stack-dev.chatmode.md** → Alternates between:
- Backend for API development
- Frontend for UI implementation
- Testing for validation

**platform-engineer.chatmode.md** → Combines:
- DevOps for infrastructure
- Backend for platform services
- Observability for monitoring

---

## Unmapped Chat Modes (Need Review)

The following chat modes may need new personas or consolidation:

- **therapeutic-content-creator.chatmode.md** → Content-focused, possibly new persona
- **social-media-manager.chatmode.md** → Marketing-focused, possibly new persona
- **technical-writer.chatmode.md** → Documentation-focused, possibly new persona
- **researcher.chatmode.md** → Research-focused, possibly new persona

**Recommendation:** Create a "Content Creator" persona or map to existing personas based on technical requirements.

---

## Migration Status

### ✅ Completed (2/44)
- backend-developer.chatmode.md (mapped to tta-backend-engineer)
- frontend-developer.chatmode.md (mapped to tta-frontend-engineer)

### 🔄 In Progress (0/44)
- None currently

### ⏳ Pending (42/44)
- All other chatmode files need frontmatter addition

---

## Frontmatter Template

Use this YAML frontmatter template for mapping chat modes to personas:

```yaml
---
hypertool_persona: tta-backend-engineer  # Or appropriate persona
persona_token_budget: 2000                # Match persona budget
tools_via_hypertool: true                # Use Hypertool for tool access
security:
  restricted_paths:
    - "apps/**/frontend/**"              # Paths this persona cannot access
    - "**/node_modules/**"
  allowed_mcp_servers:
    - context7                            # Servers this persona can use
    - github
    - sequential-thinking
---
```

---

## Validation Checklist

For each mapped chat mode:

- [ ] Frontmatter added with correct persona reference
- [ ] Token budget matches persona definition
- [ ] Allowed MCP servers align with persona
- [ ] Restricted paths appropriate for role
- [ ] Chat mode content updated to reference Hypertool
- [ ] Persona switching instructions added
- [ ] Related documentation links updated
- [ ] File moved to `.tta/chatmodes/` if applicable

---

## Testing Plan

After mapping all chat modes:

1. **Activation Test:** Verify each chat mode loads correct persona
2. **Tool Access Test:** Confirm only allowed tools are accessible
3. **Security Test:** Validate restricted paths are enforced
4. **Token Test:** Measure actual token usage vs budget
5. **Performance Test:** Compare response times before/after
6. **Switching Test:** Test persona switching between chat modes

---

## Metrics Goals

**Token Reduction:**
- Target: 77.9% average reduction
- Before: ~8000 tokens per request
- After: ~1767 tokens per request
- Measurement: OpenTelemetry span attributes

**Performance:**
- Target: <200ms for persona load
- Target: <500ms for tool filtering
- Measurement: Grafana dashboards

**Accuracy:**
- Target: 48% improvement in tool selection accuracy
- Measurement: Compare tool invocation relevance

---

## Related Documentation

- **Hypertool Guide:** `.hypertool/README.md`
- **Persona Definitions:** `.hypertool/personas/`
- **MCP Servers:** `.hypertool/mcp_servers.json`
- **Phase 3 Summary:** `.hypertool/PHASE3_IMPLEMENTATION_COMPLETE.md` (pending)

---

**Next Steps:**

1. ✅ Create backend-developer and frontend-developer enhanced chat modes
2. ⏳ Map remaining core personas (devops, testing, observability, data-scientist)
3. ⏳ Update all 44 chat modes with frontmatter
4. ⏳ Test persona switching with each chat mode
5. ⏳ Measure token reduction and performance gains
6. ⏳ Document results in Phase 3 completion summary

---

**Last Updated:** 2025-11-14  
**Progress:** 2/44 chat modes mapped (4.5%)  
**Next Priority:** Map DevOps, Testing, Observability chat modes
