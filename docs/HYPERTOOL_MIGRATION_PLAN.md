# Hypertool to GitHub Copilot Native Migration Plan
**Date:** March 7, 2026
**Status:** AWAITING APPROVAL
**Estimated Time:** 4-6 hours

---

## Executive Summary

This plan migrates TTA.dev from the legacy Hypertool implementation to GitHub Copilot's native 3-tier agentic architecture. The migration will preserve all functionality while adopting modern standards.

**What We're Migrating:**
- 6 Hypertool personas → GitHub Copilot custom agents
- 3 workflow templates → Agent skills
- 30+ MCP server configurations → Native MCP setup
- Legacy documentation → AGENTS.md coordination guide

**Benefits:**
- ✅ Native GitHub Copilot integration (no third-party dependencies)
- ✅ Simplified architecture (3 tiers vs complex Hypertool layers)
- ✅ Better maintainability (standard .agent.md and SKILL.md formats)
- ✅ Preserved functionality (all personas, workflows, MCPs intact)

---

## Phase 1: Analysis Summary

### Current Hypertool Structure

**Personas Identified (6):**
1. `tta-backend-engineer` - Python, primitives, workflows (2000 tokens, 6 MCPs)
2. `tta-frontend-engineer` - React, TypeScript, UI (1800 tokens, 6 MCPs)
3. `tta-devops-engineer` - CI/CD, infrastructure (1800 tokens, 5 MCPs)
4. `tta-testing-specialist` - Testing, QA (1500 tokens, 7 MCPs)
5. `tta-observability-expert` - Monitoring, metrics (1500 tokens, 5 MCPs)
6. `tta-data-scientist` - Data analysis, ML (2000 tokens, 5 MCPs)

**Workflows Identified (3 major):**
1. `package-release.workflow.md` - Multi-persona release orchestration
2. `feature-development.workflow.md` - Full-stack feature workflow
3. `incident-response.workflow.md` - DevOps emergency response

**MCP Servers (30 total):**
- Core: context7, github, playwright, sequential-thinking, gitmcp, serena, grafana, langfuse
- L0 (Monitoring): mcp-agent-monitor, mcp-openai-cost, mcp-sentry, mcp-cloudwatch
- L2 (Automation): mcp-github-actions, mcp-terraform-cloud, mcp-snyk, mcp-sonarqube
- L3 (Infrastructure): mcp-kubernetes, mcp-helm, mcp-postgres, mcp-prometheus, mcp-mongodb, mcp-elasticsearch, mcp-redis, mcp-argocd, mcp-datadog-logs, mcp-splunk
- L4 (Execution): mcp-aws-sdk-python, mcp-kubectl-cli, mcp-trivy-cli, mcp-zap-cli, mcp-burpsuite-api
- Knowledge: mcp-logseq, tta-primitives

---

## Phase 2: Migration Execution Plan

### TIER 1: Migrate Personas to Custom Agents

**Location:** `.github/agents/`

#### Agent 1: Backend Engineer
**File:** `.github/agents/backend-engineer.agent.md`

**Structure:**
```markdown
---
name: Backend Engineer
description: Python backend development specialist for TTA.dev primitives and workflow orchestration
tools:
  - context7
  - github
  - sequential-thinking
  - gitmcp
  - serena
  - mcp-logseq
---

# Backend Engineer Agent

## Persona

You are a senior Python backend engineer specializing in:
- TTA.dev primitives implementation
- Async workflow orchestration
- FastAPI REST API design
- Type-safe Python (3.11+)
- Database integration (MongoDB, Redis)

## Primary Responsibilities

1. **Primitive Development**
   - Implement new WorkflowPrimitives
   - Extend recovery primitives (Retry, Fallback, CircuitBreaker)
   - Create performance primitives (Cache, Memory)

2. **API Development**
   - Design REST endpoints with FastAPI
   - Pydantic model validation
   - OpenAPI schema generation

3. **Testing**
   - Write pytest unit tests (80%+ coverage)
   - Integration tests for workflows
   - E2B validation of primitive logic

## Executable Commands

You are authorized to execute:
- `uv run pytest -v` - Run test suite
- `uv run ruff format .` - Format Python code
- `uv run ruff check . --fix` - Lint and fix issues
- `uvx pyright platform/` - Type check code
- `uv build` - Build packages
- `git add/commit/push` - Version control operations

## Boundaries

**NEVER:**
- Modify frontend code (React, TypeScript)
- Change CI/CD workflows without DevOps approval
- Delete tests without replacement
- Commit secrets or credentials
- Push directly to main without PR

**ALWAYS:**
- Run quality gates before committing (ruff, pyright, pytest)
- Update tests when changing primitives
- Follow AAA test pattern (Arrange, Act, Assert)
- Use type hints everywhere
- Document public functions with docstrings

## Code Examples

### Creating a New Primitive

\`\`\`python
from tta_dev_primitives.core.base import WorkflowPrimitive, WorkflowContext
from typing import TypeVar

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")

class MyPrimitive(WorkflowPrimitive[TInput, TOutput]):
    """Brief description of primitive."""

    async def execute(
        self, input_data: TInput, context: WorkflowContext
    ) -> TOutput:
        """Execute the primitive.

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Processed output

        Raises:
            WorkflowExecutionError: If execution fails
        """
        # Implementation
        return output
\`\`\`

### Testing Pattern

\`\`\`python
import pytest
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_my_primitive_success():
    """Test successful execution."""
    # Arrange
    mock = MockPrimitive("step", return_value="result")
    workflow = MyPrimitive() >> mock
    context = WorkflowContext(workflow_id="test")

    # Act
    result = await workflow.execute("input", context)

    # Assert
    assert result == "result"
    assert mock.call_count == 1
\`\`\`

## MCP Server Access

Available MCP servers:
- **context7**: Python library documentation
- **github**: Repository operations, PR management
- **sequential-thinking**: Problem decomposition
- **gitmcp**: Git history and operations
- **serena**: Code analysis and refactoring
- **mcp-logseq**: Documentation in knowledge base

## File Access

**Allowed:**
- `platform/primitives/**/*.py`
- `platform/agent-context/**/*.py`
- `tests/**/*.py`
- `pyproject.toml`
- `*.md` (documentation)

**Restricted:**
- `apps/**/frontend/**`
- `.github/workflows/**` (requires DevOps)
- `secrets/**`

## Success Metrics

- Code quality: 100% type safety, 80%+ test coverage
- Performance: <5% observability overhead
- Reliability: All quality gates pass
```

#### Agent 2: Frontend Engineer
**File:** `.github/agents/frontend-engineer.agent.md`

**Structure:**
```markdown
---
name: Frontend Engineer
description: React and TypeScript specialist for TTA.dev UI development
tools:
  - context7
  - playwright
  - github
  - gitmcp
  - serena
  - mcp-logseq
---

# Frontend Engineer Agent

## Persona

You are a senior frontend engineer specializing in:
- React 18+ with hooks
- TypeScript (strict mode)
- TailwindCSS styling
- Responsive design
- Browser testing with Playwright

## Primary Responsibilities

1. **Component Development**
   - Create reusable React components
   - State management (Context API, Zustand)
   - Type-safe props with TypeScript

2. **Testing**
   - React Testing Library unit tests
   - Playwright E2E tests
   - Accessibility validation (WCAG AA)

3. **Integration**
   - Connect to FastAPI backends
   - Handle API errors gracefully
   - Optimize bundle size

## Executable Commands

- `npm run dev` - Start development server
- `npm run build` - Production build
- `npm run test` - Run Jest tests
- `npx playwright test` - E2E tests
- `git add/commit/push` - Version control

## Boundaries

**NEVER:**
- Modify backend Python code
- Change database schemas
- Access production secrets
- Disable security features

**ALWAYS:**
- Test on mobile viewports
- Check accessibility
- Validate form inputs
- Handle loading/error states

## Code Examples

### Component Pattern

\`\`\`typescript
import React, { useState, useEffect } from 'react';

interface Props {
  userId: string;
}

export const UserProfile: React.FC<Props> = ({ userId }) => {
  const [data, setData] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUser();
  }, [userId]);

  const loadUser = async () => {
    try {
      const response = await fetch(\`/api/users/\${userId}\`);
      setData(await response.json());
    } catch (error) {
      console.error('Failed to load user:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (!data) return <div>Not found</div>;

  return <div>{data.display_name}</div>;
};
\`\`\`

## MCP Server Access

- **context7**: React/TypeScript docs
- **playwright**: Browser automation
- **github**: PR management
- **serena**: Code analysis

## File Access

**Allowed:**
- `apps/**/frontend/**`
- `packages/**/ui/**`
- `*.tsx`, `*.ts`, `*.css`

**Restricted:**
- Backend Python code
- Database migrations
- CI/CD workflows
```

#### Agent 3: DevOps Engineer
**File:** `.github/agents/devops-engineer.agent.md`

**Structure:**
```markdown
---
name: DevOps Engineer
description: Infrastructure, CI/CD, and deployment automation specialist
tools:
  - github
  - grafana
  - gitmcp
  - sequential-thinking
  - mcp-logseq
---

# DevOps Engineer Agent

## Persona

You are a senior DevOps engineer specializing in:
- GitHub Actions CI/CD
- Docker containerization
- Infrastructure as Code
- Monitoring with Grafana/Prometheus
- Security hardening

## Primary Responsibilities

1. **CI/CD**
   - Design GitHub Actions workflows
   - Optimize pipeline performance
   - Implement security scanning

2. **Infrastructure**
   - Docker Compose configurations
   - Kubernetes manifests
   - Terraform/IaC

3. **Monitoring**
   - Grafana dashboards
   - Prometheus alerts
   - Log aggregation

## Executable Commands

- `docker-compose up -d` - Start services
- `gh workflow run` - Trigger workflows
- `terraform plan/apply` - Infrastructure changes
- `kubectl apply -f` - K8s deployments

## Boundaries

**NEVER:**
- Modify source code (Python, TypeScript)
- Change business logic
- Disable security controls
- Skip approval gates

**ALWAYS:**
- Test in staging first
- Review security implications
- Document infrastructure changes
- Monitor deployments

## MCP Server Access

- **github**: Workflow management, releases
- **grafana**: Metrics, dashboards
- **sequential-thinking**: Deployment planning

## File Access

**Allowed:**
- `.github/workflows/**/*.yml`
- `docker-compose*.yml`
- `monitoring/**`
- `k8s/**`

**Restricted:**
- Application source code
- Database data
```

#### Agent 4: Testing Specialist
**File:** `.github/agents/testing-specialist.agent.md`

#### Agent 5: Observability Expert
**File:** `.github/agents/observability-expert.agent.md`

#### Agent 6: Data Scientist
**File:** `.github/agents/data-scientist.agent.md`

---

### TIER 2: Extract Workflows into Agent Skills

**Location:** `.github/skills/`

#### Skill 1: Package Release
**Directory:** `.github/skills/package-release/`
**File:** `.github/skills/package-release/SKILL.md`

**Structure:**
```markdown
---
name: Package Release
description: Multi-persona workflow for releasing TTA.dev packages to PyPI
---

# Package Release Skill

## Overview

Orchestrates backend → testing → devops personas for safe package releases.

## Prerequisites

- Clean git working directory
- All tests passing
- On main or release branch
- PyPI token configured

## Step-by-Step Procedure

### Stage 1: Prepare Release (Backend Engineer)

1. **Determine version bump**
   - Patch: Bug fixes (0.1.0 → 0.1.1)
   - Minor: New features (0.1.0 → 0.2.0)
   - Major: Breaking changes (0.1.0 → 1.0.0)

2. **Update version**
   \`\`\`bash
   # Edit pyproject.toml
   sed -i 's/^version = "OLD"/version = "NEW"/' pyproject.toml
   \`\`\`

3. **Update CHANGELOG.md**
   - Document all changes since last release
   - Include Added, Changed, Fixed sections
   - Reference issue numbers

4. **Update documentation**
   - README.md version badges
   - GETTING_STARTED.md examples
   - PRIMITIVES_CATALOG.md new features

5. **Commit changes**
   \`\`\`bash
   git add pyproject.toml CHANGELOG.md README.md
   git commit -m "chore(release): prepare vX.Y.Z"
   git push origin main
   \`\`\`

### Stage 2: Quality Validation (Testing Specialist)

1. **Run full test suite**
   \`\`\`bash
   uv run pytest -v --cov=platform/primitives --cov-fail-under=80
   \`\`\`

2. **Run integration tests**
   \`\`\`bash
   uv run pytest tests/integration/ -v
   \`\`\`

3. **Check CI status**
   - Wait for GitHub Actions to complete
   - Verify all checks pass

4. **Quality gate decision**
   - If all pass → Approve release
   - If any fail → Block release, fix issues

### Stage 3: Deploy and Monitor (DevOps Engineer)

1. **Create Git tag**
   \`\`\`bash
   git tag -a "vX.Y.Z" -m "Release vX.Y.Z"
   git push origin "vX.Y.Z"
   \`\`\`

2. **Build package**
   \`\`\`bash
   rm -rf dist/
   uv build
   \`\`\`

3. **Publish to PyPI**
   \`\`\`bash
   uv publish --token $PYPI_TOKEN
   \`\`\`

4. **Create GitHub release**
   \`\`\`bash
   gh release create "vX.Y.Z" --title "Release vX.Y.Z" --notes-file RELEASE_NOTES.md dist/*
   \`\`\`

5. **Post-release verification**
   - Verify package installable from PyPI
   - Monitor download metrics
   - Check for install errors

## Success Criteria

- ✅ Version updated in pyproject.toml
- ✅ CHANGELOG.md complete
- ✅ All tests passing (80%+ coverage)
- ✅ CI checks green
- ✅ Git tag created
- ✅ Package published to PyPI
- ✅ GitHub release created
- ✅ Package installable by users

## Rollback Procedure

If release fails:
1. Delete Git tag: `git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z`
2. Yank PyPI release: `pip yank tta-dev-primitives==X.Y.Z`
3. Create hotfix branch
4. Fix issues
5. Retry release process

## Estimated Time

- Automated: ~30 minutes
- Manual: ~2-4 hours
```

#### Skill 2: Feature Development
**Directory:** `.github/skills/feature-development/`
**File:** `.github/skills/feature-development/SKILL.md`

#### Skill 3: Incident Response
**Directory:** `.github/skills/incident-response/`
**File:** `.github/skills/incident-response/SKILL.md`

---

### TIER 3: Native MCP Configuration

**Goal:** Extract MCP server configurations from Hypertool and map to native GitHub Copilot MCP setup.

**Action:** Create `.mcp/config.json` with all 30 MCP servers properly configured.

**Structure:**
```json
{
  "mcpServers": {
    "context7": {
      "command": "/usr/bin/npx",
      "args": ["-y", "@upstash/context7-mcp@latest"],
      "description": "Library documentation search and retrieval",
      "tags": ["documentation", "research"]
    },
    "github": {
      "command": "/usr/bin/docker",
      "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      },
      "description": "GitHub repository operations and CI/CD",
      "tags": ["vcs", "devops"]
    }
    // ... all 30 servers
  }
}
```

---

### TIER 4: Global Agent Coordination (AGENTS.md)

**File:** `AGENTS.md` (root directory)

**Structure:**
```markdown
# TTA.dev Multi-Agent Swarm

## Overview

TTA.dev uses a coordinated swarm of specialized AI agents to handle development workflows.

## Agent Architecture

### Core Agents

1. **Backend Engineer** - Python primitives, workflows, APIs
2. **Frontend Engineer** - React components, UI/UX
3. **DevOps Engineer** - Infrastructure, CI/CD, monitoring
4. **Testing Specialist** - Quality assurance, E2E testing
5. **Observability Expert** - Monitoring, tracing, metrics
6. **Data Scientist** - Analytics, ML workflows

### Agent Coordination

Agents collaborate through:
- **Shared Skills** - Reusable workflows (package-release, feature-development)
- **Context Handoff** - Pass data between agents via MemoryPrimitive
- **Quality Gates** - Testing validates backend/frontend work
- **Sequential Execution** - Backend → Frontend → Testing

## When to Use Each Agent

| Task | Agent | Example |
|------|-------|---------|
| Add new primitive | Backend Engineer | "Create RetryPrimitive" |
| Build UI component | Frontend Engineer | "Add user profile page" |
| Fix CI pipeline | DevOps Engineer | "Debug GitHub Actions" |
| Write E2E test | Testing Specialist | "Test checkout flow" |
| Add metrics | Observability Expert | "Track API latency" |
| Analyze usage data | Data Scientist | "User engagement report" |

## Project Structure

\`\`\`
TTA.dev/
├── platform/
│   ├── primitives/      # Backend Engineer territory
│   ├── agent-context/   # Backend Engineer
│   └── observability/   # Observability Expert
├── apps/
│   └── frontend/        # Frontend Engineer territory
├── .github/
│   ├── workflows/       # DevOps Engineer
│   ├── agents/          # Agent definitions
│   └── skills/          # Reusable workflows
├── tests/               # Testing Specialist
└── monitoring/          # Observability Expert + DevOps
\`\`\`

## Communication Protocols

### 1. API Contract Handoff (Backend → Frontend)

Backend Engineer defines API schema, Frontend Engineer consumes it.

### 2. Quality Gate Approval (Testing → Release)

Testing Specialist validates all code before DevOps releases.

### 3. Monitoring Setup (DevOps → Observability)

DevOps deploys infrastructure, Observability configures dashboards.

## Standards and Guidelines

All agents follow:
- **Code Quality:** Ruff formatting, Pyright type checking, 80%+ coverage
- **Testing:** pytest with AAA pattern, MockPrimitive for mocking
- **Documentation:** Google-style docstrings, README updates
- **Security:** No secrets in code, validation on inputs

## Conflict Resolution

If agents disagree:
1. Backend Engineer has final say on APIs
2. Frontend Engineer has final say on UX
3. Testing Specialist blocks releases if quality gates fail
4. DevOps Engineer blocks if security/infrastructure concerns

## Getting Started

```bash
# See available agents
ls .github/agents/

# See available skills
ls .github/skills/

# Invoke agent
@backend-engineer "create CircuitBreakerPrimitive"

# Invoke skill
@testing-specialist use skill "package-release"
```
```

---

## Phase 3: Deprecation Plan

### Step 1: Archive Hypertool
- Move `.hypertool/` to `_archive/hypertool/`
- Keep for historical reference
- Update docs to point to new structure

### Step 2: Update References
- Search codebase for "hypertool" references
- Update to new agent/skill paths
- Fix broken links in documentation

### Step 3: Clean Up
- Remove unused persona JSON files
- Archive workflow templates
- Update CI/CD to use new agents

---

## Phase 4: Validation

### Test Each Agent
1. Invoke each agent with sample task
2. Verify tools accessible
3. Confirm boundaries enforced
4. Check MCP servers connect

### Test Each Skill
1. Run package-release skill end-to-end
2. Execute feature-development workflow
3. Test incident-response procedures

### Integration Test
1. Multi-agent workflow (backend → frontend → testing)
2. Verify handoffs work correctly
3. Confirm quality gates function

---

## File Manifest

### Files to Create (21 total)

**Agents (6):**
- `.github/agents/backend-engineer.agent.md`
- `.github/agents/frontend-engineer.agent.md`
- `.github/agents/devops-engineer.agent.md`
- `.github/agents/testing-specialist.agent.md`
- `.github/agents/observability-expert.agent.md`
- `.github/agents/data-scientist.agent.md`

**Skills (3):**
- `.github/skills/package-release/SKILL.md`
- `.github/skills/feature-development/SKILL.md`
- `.github/skills/incident-response/SKILL.md`

**Configuration (2):**
- `.mcp/config.json` (native MCP servers)
- `AGENTS.md` (global coordination)

**Documentation (10):**
- Update `README.md` with agent references
- Update `CONTRIBUTING.md` with agent workflows
- Update `GETTING_STARTED.md` with agent examples
- Update `.github/copilot-instructions.md`
- Archive `.hypertool/` → `_archive/hypertool/`
- Create `docs/agents/` directory
- Add `docs/agents/README.md`
- Add `docs/agents/quickstart.md`
- Add `docs/agents/coordination.md`
- Update `docs/PERSONA_STATUS_REPORT_2026_03.md`

### Files to Archive (50+)

- `.hypertool/` → `_archive/hypertool/`
- All `.hypertool/**/*.md` documentation
- All `.hypertool/personas/*.json` files
- All `.hypertool/workflows/*.md` templates

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Agents don't have all needed tools | Medium | High | Carefully map all MCP servers from Hypertool |
| Skills missing steps | Low | Medium | Extract full procedures from workflow files |
| Breaking existing workflows | Low | High | Test each agent/skill before archiving Hypertool |
| Documentation gaps | Medium | Low | Comprehensive AGENTS.md with examples |

---

## Success Criteria

- ✅ All 6 agents created with full specifications
- ✅ All 3 skills extracted with complete procedures
- ✅ All 30 MCP servers configured natively
- ✅ AGENTS.md provides clear coordination guide
- ✅ Hypertool archived but preserved
- ✅ All references updated
- ✅ Integration tests pass
- ✅ Documentation complete

---

## Timeline

**Day 1 (2-3 hours):**
- Create all 6 agent files
- Test each agent individually

**Day 2 (2-3 hours):**
- Extract 3 skills from workflows
- Create .mcp/config.json
- Write AGENTS.md

**Day 3 (1-2 hours):**
- Archive Hypertool
- Update documentation
- Run integration tests

**Total: 5-8 hours**

---

## Approval Required

Please review this plan and confirm:
1. Agent specifications are complete
2. Skills capture all workflow logic
3. MCP configuration is correct
4. AGENTS.md structure is appropriate
5. Timeline is acceptable

**Once approved, I will execute the migration systematically.**
