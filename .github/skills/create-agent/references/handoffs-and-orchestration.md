# Handoffs and Agent Orchestration

## Handoffs

Handoffs create guided workflow transitions between agents. After a chat response
completes, handoff buttons appear allowing users to move to the next agent.

### Frontmatter

```yaml
handoffs:
  - label: Start Implementation
    agent: backend-engineer
    prompt: 'Implement the plan outlined above.'
    send: false
  - label: Code Review
    agent: code-reviewer
    prompt: 'Review this implementation for quality and security issues.'
    send: false
```

### Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `label` | string | Yes | Button text — use action verbs ("Start", "Review", "Write") |
| `agent` | string | Yes | Target agent filename without `.agent.md` |
| `prompt` | string | No | Pre-filled prompt for the target agent |
| `send` | boolean | No | Auto-submit the prompt (default: `false`) |

### TTA.dev Handoff Patterns

| From | To | Use Case |
|------|----|----------|
| project-planner | backend-engineer | Plan → implement |
| backend-engineer | code-reviewer | Implement → review |
| code-reviewer | backend-engineer | Review feedback → fix |
| testing-specialist | backend-engineer | Test gaps → implement |

### Best Practices

- Limit to 2-3 handoffs per agent
- Use action-oriented labels: ✅ "Start Implementation" / ❌ "Next"
- Reference completed work in prompts: "Implement the plan above"
- Target agents must exist in `.github/agents/`
- VS Code 1.106+ required; not supported on GitHub.com

---

## Sub-Agent Orchestration

Agents can invoke other agents using the `agent` tool for multi-step pipelines.

### Setup

Include `agent` in the orchestrator's tools:

```yaml
tools: ['read', 'edit', 'search', 'execute', 'agent']
```

**Critical**: The orchestrator's tool list is the ceiling — sub-agents cannot
access tools the orchestrator doesn't have.

### Invocation Pattern

```text
This phase must be performed as the agent "<AGENT_NAME>" defined in
".github/agents/<AGENT_NAME>.agent.md".

IMPORTANT:
- Read and apply the entire .agent.md spec (tools, constraints, quality standards).
- Work on "<WORK_UNIT>" with base path: "<BASE_PATH>".
- Return a clear summary (actions taken + files modified + issues).
```

### Multi-Step Example

```text
Step 1: Security Review
Agent: code-reviewer
Context: basePath=src/, focus=security
Output: reports/security-review.md

Step 2: Test Coverage
Agent: testing-specialist
Context: basePath=src/, focus=coverage-gaps
Output: reports/coverage-report.md
```

### Key Rules

- Pass paths and identifiers, not file contents
- Run steps sequentially when outputs feed into inputs
- Check results before proceeding to dependent steps
- Keep to ≤5 orchestrated steps (latency adds up)
- For bulk processing, use a single agent instead of orchestration

### Conditional Steps

```text
Step trigger conditions:

| Step | Required? | Trigger | On Failure |
|------|-----------|---------|------------|
| Security Review | Required | Always | Stop |
| Dependency Audit | Optional | If pyproject.toml changed | Continue |
| Test Coverage | Optional | If test files present | Continue |
| Aggregate | Required | Always | Stop |
```

Mark optional steps as SKIPPED when trigger conditions are false.
Log each step with status (SUCCESS/SKIPPED/FAILED), duration, and artifacts.
