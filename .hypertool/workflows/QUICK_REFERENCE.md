# Multi-Persona Workflows - Quick Reference

**Quick access guide for TTA.dev multi-persona workflows**

---

## 📋 Available Workflows

### 1. 📦 Package Release

**Use When:** Releasing a new version of a TTA.dev package  
**Personas:** Backend → Testing → DevOps  
**Time:** ~30 minutes (automated)

```bash
# View workflow
cat .hypertool/workflows/package-release.workflow.md

# Start workflow
tta-persona backend
# Follow Stage 1 instructions...

tta-persona testing
# Follow Stage 2 instructions...

tta-persona devops
# Follow Stage 3 instructions...
```

**Quick Steps:**
1. Backend: Version bump → CHANGELOG → Commit
2. Testing: Run tests → Validate coverage → Check CI
3. DevOps: Tag → Publish PyPI → Create release → Monitor

---

### 2. 🚀 Feature Development

**Use When:** Building a full-stack feature (API + UI + Tests)  
**Personas:** Backend → Frontend → Testing  
**Time:** ~5-6 hours

```bash
# View workflow
cat .hypertool/workflows/feature-development.workflow.md

# Start workflow
tta-persona backend
# Follow Stage 1 instructions...

tta-persona frontend
# Follow Stage 2 instructions...

tta-persona testing
# Follow Stage 3 instructions...
```

**Quick Steps:**
1. Backend: API contract → Endpoints → Tests → OpenAPI
2. Frontend: TypeScript types → React components → Tests
3. Testing: E2E tests → Accessibility → Integration → PR review

---

### 3. 🔥 Incident Response

**Use When:** Production incident detected (API errors, outages, etc.)  
**Personas:** Observability → Backend → DevOps  
**Time:** ~20-30 minutes MTTR

```bash
# View workflow
cat .hypertool/workflows/incident-response.workflow.md

# Start workflow (when alert fires)
tta-persona observability
# Follow Stage 1 instructions...

tta-persona backend
# Follow Stage 2 instructions...

tta-persona devops
# Follow Stage 3 instructions...
```

**Quick Steps:**
1. Observability: Alert triage → Metrics → Logs → Traces → Impact
2. Backend: Reproduce → Design fix → Implement → Test → Commit
3. DevOps: Hotfix PR → Deploy → Monitor → Verify → Post-mortem

---

## 🎯 Workflow Selection Guide

| Scenario | Workflow | Estimated Time |
|----------|----------|----------------|
| Release new package version | Package Release | 30 min |
| Add new user-facing feature | Feature Development | 5-6 hours |
| API endpoint development | Feature Development | 2-3 hours |
| Production error spike | Incident Response | 20-30 min |
| Database performance issue | Incident Response | 30-60 min |
| UI component development | Feature Development | 2-3 hours |
| Hotfix deployment | Incident Response | 15-30 min |

---

## 🔧 Persona Switching

### Switch Persona via CLI

```bash
# View available personas
tta-persona list

# Switch persona
tta-persona backend      # Backend Engineer
tta-persona frontend     # Frontend Engineer
tta-persona testing      # Testing Specialist
tta-persona observability # Observability Expert
tta-persona devops       # DevOps Engineer
tta-persona data-science # Data Scientist

# Check current persona
tta-persona current
```

### Switch Persona via Chatmode

```
/chatmode backend-developer
/chatmode frontend-developer
/chatmode testing-specialist
/chatmode observability-expert
/chatmode devops-engineer
/chatmode data-science-specialist
```

---

## 📊 Workflow Metrics

### Package Release

- **Duration:** 30 minutes
- **Automation:** 85%
- **Quality Gates:** 5
- **Token Usage:** 4,870 tokens
- **Personas:** 3 (Backend, Testing, DevOps)

### Feature Development

- **Duration:** 5-6 hours
- **Automation:** 60%
- **Quality Gates:** 7
- **Token Usage:** 4,850 tokens
- **Personas:** 3 (Backend, Frontend, Testing)

### Incident Response

- **MTTR:** 20-30 minutes
- **Automation:** 70%
- **Quality Gates:** 4
- **Token Usage:** 5,310 tokens
- **Personas:** 3 (Observability, Backend, DevOps)

---

## 🛠️ Common Commands

### Package Release Workflow

```bash
# Stage 1: Backend
uv run pytest -v
git commit -m "chore(release): prepare v0.2.0"
git push origin main

# Stage 2: Testing
uv run pytest --cov=packages --cov-report=html
gh run list --commit $(git rev-parse HEAD)

# Stage 3: DevOps
git tag -a v0.2.0 -m "Release v0.2.0"
uv build
uv publish --token $PYPI_TOKEN
gh release create v0.2.0
```

### Feature Development Workflow

```bash
# Stage 1: Backend
git checkout -b feature/user-profile
# Implement API endpoints
uv run pytest packages/api/tests/

# Stage 2: Frontend
# Retrieve API contract from MemoryPrimitive
# Generate TypeScript types
npm run test

# Stage 3: Testing
playwright test
npm run test:a11y
gh pr create
```

### Incident Response Workflow

```bash
# Stage 1: Observability
query_prometheus "rate(http_requests_total{status='500'}[5m])"
query_loki_logs '{service="api",level="error"}'

# Stage 2: Backend
git checkout -b hotfix/database-connection-pool
# Implement fix
python -c "from tta_dev_primitives.integrations import CodeExecutionPrimitive; ..."

# Stage 3: DevOps
gh pr create --label hotfix
gh pr merge --admin
kubectl rollout restart deployment/api
```

---

## 🧠 Integration Points

### TTA Primitives

```python
# Sequential workflow
workflow = stage1 >> stage2 >> stage3

# Parallel execution
workflow = branch1 | branch2 | branch3

# Routing by severity
workflow = RouterPrimitive(routes={...})

# Retry on failure
workflow = RetryPrimitive(primitive=step, max_retries=3)

# Fallback on error
workflow = FallbackPrimitive(primary=step1, fallbacks=[step2])

# Memory for context
memory = MemoryPrimitive(namespace="workflow")
```

### E2B Code Execution

```python
from tta_dev_primitives.integrations import CodeExecutionPrimitive

executor = CodeExecutionPrimitive()
result = await executor.execute({
    "code": "...",
    "timeout": 60
}, context)
```

### Logseq Knowledge Base

```bash
# Tool: mcp_logseq_create_page
# Creates: logseq/pages/[Title].md

# Tool: mcp_logseq_update_page
# Updates existing page
```

### Grafana/Prometheus

```bash
# Query metrics
query_prometheus "rate(http_requests_total[5m])"

# Query logs
query_loki_logs '{service="api",level="error"}'

# Check alerts
list_alert_rules
```

### GitHub MCP

```bash
# Create branch
gh repo create-branch feature/new-feature

# Create PR
gh pr create --title "..." --body "..."

# Merge PR
gh pr merge --squash

# Create release
gh release create v1.0.0
```

---

## 📚 Documentation

### Workflow Files

- `.hypertool/workflows/package-release.workflow.md` - Full guide
- `.hypertool/workflows/feature-development.workflow.md` - Full guide
- `.hypertool/workflows/incident-response.workflow.md` - Full guide

### Reference Docs

- `PRIMITIVES_CATALOG.md` - All TTA primitives
- `.hypertool/IMPLEMENTATION_ROADMAP.md` - Hypertool planning
- `.hypertool/PERSONA_DESIGN_PATTERNS.md` - Persona patterns
- `MCP_SERVERS.md` - MCP tool reference
- `AGENTS.md` - Agent instructions

---

## 🚨 Troubleshooting

### Persona Switch Not Working

```bash
# Check current persona
tta-persona current

# Verify config exists
cat ~/.hypertool/config.json

# Reload VS Code
# Command Palette → "Developer: Reload Window"
```

### MCP Tools Not Available

```bash
# Check MCP config
cat ~/.hypertool/config.json

# Verify persona has tools
tta-persona backend
# Should show ~48 tools in Copilot
```

### Memory Primitive Issues

```python
# Check namespace
from tta_dev_primitives.performance import MemoryPrimitive
mem = MemoryPrimitive(namespace="workflow_name")

# Search all keys
results = await mem.search(keywords=["*"])
```

### E2B Execution Failures

```python
# Check timeout
result = await executor.execute({
    "code": "...",
    "timeout": 120  # Increase if needed
})

# Check error message
if not result["success"]:
    print(result["error"])
    print(result["logs"])
```

---

## 💡 Tips and Best Practices

### Workflow Execution

1. **Read full workflow first** - Understand all stages before starting
2. **Check prerequisites** - Ensure environment setup complete
3. **Use MemoryPrimitive** - Share context between personas
4. **Document in Logseq** - Track decisions and learnings
5. **Monitor with APM** - Watch OpenTelemetry traces

### Persona Switching

1. **Switch at logical boundaries** - Between workflow stages
2. **Verify tools available** - Check MCP config loaded
3. **Review token budget** - Stay within persona limits
4. **Pass context explicitly** - Use MemoryPrimitive or files

### Quality Gates

1. **Don't skip gates** - Each validates important criteria
2. **Automate validation** - Use TTA primitives (ConditionalPrimitive)
3. **Document failures** - Logseq tracks why gate failed
4. **Fix before proceeding** - Don't advance with failing gates

### Observability

1. **Enable tracing** - Full OpenTelemetry integration
2. **Check metrics** - Prometheus queries during workflow
3. **Review logs** - Loki searches for errors
4. **Update dashboards** - Grafana visualization

---

## 📞 Getting Help

### Documentation

- **Workflows:** `.hypertool/workflows/*.workflow.md`
- **Primitives:** `PRIMITIVES_CATALOG.md`
- **MCP Tools:** `MCP_SERVERS.md`
- **Examples:** `packages/tta-dev-primitives/examples/`

### Common Questions

**Q: How do I choose which workflow to use?**  
A: See [Workflow Selection Guide](#-workflow-selection-guide) above

**Q: What if workflow fails mid-execution?**  
A: Each stage is idempotent - restart from failed stage

**Q: Can I customize workflows?**  
A: Yes - workflows are templates. Adapt to your needs.

**Q: How do I add new workflows?**  
A: Copy existing workflow, modify stages, update personas

---

## 🎯 Next Steps

After completing workflows:

1. **Review metrics** - Check duration, token usage, quality
2. **Document learnings** - Update Logseq with insights
3. **Gather feedback** - What worked? What didn't?
4. **Iterate** - Improve workflow based on feedback
5. **Share** - Help others use workflows effectively

---

**Last Updated:** 2025-11-14  
**Status:** Production Ready  
**Version:** 1.0
