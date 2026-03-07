---
title: Missing Chat Modes Implementation Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: .github/MISSING_CHAT_MODES_IMPLEMENTATION_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Missing Chat Modes Implementation Guide]]

**Date**: 2025-10-27
**Status**: Ready for Phase 4 Implementation
**Scope**: 5 critical chat modes needed for complete TTA coverage

---

## Overview

This guide provides detailed specifications for implementing 5 missing chat modes that are critical for complete TTA development coverage.

---

## Tier 1: CRITICAL Modes (Implement First)

### 1. DevOps Engineer Chat Mode

**File**: `.github/chatmodes/devops-engineer.chatmode.md`

**Purpose**: Deployment, infrastructure, CI/CD, monitoring, containerization

**Cognitive Focus**: Automation, reliability, scalability, observability

**Security Level**: CRITICAL

**MCP Tool Access**:
- ✅ ALLOWED: `save-file`, `str-replace-editor`, `view`, `launch-process`, `codebase-retrieval`
- ⚠️ RESTRICTED: `launch-process` (production requires approval), `remove-files` (approval required)
- ❌ DENIED: Application code modification, database direct access, secrets access

**File Pattern Scope**:
```
✅ ALLOWED (Read/Write):
  - .github/workflows/**/*.yml
  - docker/**/*
  - kubernetes/**/*.yaml
  - scripts/deploy/**/*.sh
  - docker-compose.yml
  - Dockerfile

✅ ALLOWED (Read-Only):
  - src/**/*.py (reference only)
  - pyproject.toml

❌ DENIED:
  - .env files
  - secrets/
  - src/therapeutic_safety/**/*
```

**Key Responsibilities**:
- Set up CI/CD pipelines
- Manage Docker and Kubernetes configurations
- Monitor application health
- Manage deployments and rollbacks
- Configure logging and alerting

**Example Scenarios**:
1. "Set up GitHub Actions workflow for automated testing and deployment"
2. "Create Docker Compose configuration for local development"
3. "Deploy application to staging environment"
4. "Configure monitoring and alerting for production"

**Integration with Phase 2**:
- Reference: `.github/instructions/python-quality-standards.instructions.md`
- Reference: `.github/instructions/testing-requirements.instructions.md`

---

### 2. QA Engineer Chat Mode

**File**: `.github/chatmodes/qa-engineer.chatmode.md`

**Purpose**: Testing, quality assurance, coverage improvement, test automation

**Cognitive Focus**: Test design, coverage analysis, quality metrics, automation

**Security Level**: MEDIUM

**MCP Tool Access**:
- ✅ ALLOWED: `str-replace-editor`, `save-file`, `view`, `launch-process`, `codebase-retrieval`
- ⚠️ RESTRICTED: `remove-files` (approval required)
- ❌ DENIED: Production database access, therapeutic safety code modification

**File Pattern Scope**:
```
✅ ALLOWED (Read/Write):
  - tests/**/*.py
  - tests/**/*.spec.ts
  - tests/**/*.spec.tsx
  - tests/conftest.py
  - pytest.ini

✅ ALLOWED (Read-Only):
  - src/**/*.py
  - src/**/*.{jsx,tsx}

❌ DENIED:
  - src/therapeutic_safety/**/* (read-only)
  - Production databases
```

**Key Responsibilities**:
- Design and implement unit tests
- Create integration tests
- Develop E2E tests with Playwright
- Analyze test coverage
- Improve code quality metrics

**Example Scenarios**:
1. "Analyze test coverage for orchestration module and create tests to reach 70%"
2. "Create E2E tests for player login and session management flow"
3. "Write integration tests for database operations"
4. "Generate coverage report and identify gaps"

**Integration with Phase 2**:
- Reference: `.github/instructions/testing-requirements.instructions.md`
- Reference: `.github/instructions/python-quality-standards.instructions.md`

---

### 3. API Gateway Engineer Chat Mode

**File**: `.github/chatmodes/api-gateway-engineer.chatmode.md`

**Purpose**: API design, authentication, authorization, rate limiting, security

**Cognitive Focus**: API architecture, security, performance, documentation

**Security Level**: CRITICAL

**MCP Tool Access**:
- ✅ ALLOWED: `str-replace-editor`, `save-file`, `view`, `launch-process`, `codebase-retrieval`
- ⚠️ RESTRICTED: `remove-files` (approval required), `launch-process` (production requires approval)
- ❌ DENIED: Therapeutic safety code, database schema modification, secrets access

**File Pattern Scope**:
```
✅ ALLOWED (Read/Write):
  - src/api_gateway/**/*.py
  - tests/**/*_api*.py
  - docs/api/**/*.md

✅ ALLOWED (Read-Only):
  - src/models/**/*.py
  - src/therapeutic_safety/**/*.py

❌ DENIED:
  - src/database/**/*
  - .env files
  - secrets/
```

**Key Responsibilities**:
- Design API endpoints
- Implement authentication (JWT, OAuth2)
- Implement authorization (RBAC)
- Add rate limiting
- Create API documentation
- Implement input validation

**Example Scenarios**:
1. "Design new API endpoint for player actions with proper authentication"
2. "Implement JWT token validation and refresh logic"
3. "Add rate limiting to prevent abuse"
4. "Create OpenAPI documentation for all endpoints"

**Integration with Phase 2**:
- Reference: `.github/instructions/api-security.instructions.md`
- Reference: `.github/instructions/python-quality-standards.instructions.md`

---

## Tier 2: HIGH Priority Modes

### 4. Narrative Engine Developer Chat Mode

**File**: `.github/chatmodes/narrative-engine-developer.chatmode.md`

**Purpose**: Narrative generation, story design, content creation, coherence validation

**Cognitive Focus**: Story design, narrative consistency, content generation, player experience

**Security Level**: MEDIUM

**MCP Tool Access**:
- ✅ ALLOWED: `str-replace-editor`, `save-file`, `view`, `launch-process`, `codebase-retrieval`
- ⚠️ RESTRICTED: `remove-files` (approval required)
- ❌ DENIED: Therapeutic safety code modification, database schema changes

**File Pattern Scope**:
```
✅ ALLOWED (Read/Write):
  - src/narrative_engine/**/*.py
  - src/narrative_engine/**/*.md
  - tests/**/*_narrative*.py
  - content/narratives/**/*.md

✅ ALLOWED (Read-Only):
  - src/agent_orchestration/**/*.py
  - src/models/**/*.py

❌ DENIED:
  - src/therapeutic_safety/**/*
  - src/database/**/*
```

**Key Responsibilities**:
- Design narrative branching
- Implement story generation
- Validate narrative coherence
- Create narrative prompts
- Manage narrative state
- Test narrative consistency

**Example Scenarios**:
1. "Design narrative branching for player choices"
2. "Implement story coherence validation"
3. "Create narrative generation prompts"
4. "Test narrative consistency across player actions"

**Integration with Phase 2**:
- Reference: `.github/instructions/langgraph-orchestration.instructions.md`
- Reference: `.github/instructions/python-quality-standards.instructions.md`

---

### 5. Therapeutic Content Creator Chat Mode

**File**: `.github/chatmodes/therapeutic-content-creator.chatmode.md`

**Purpose**: Therapeutic content design, intervention creation, safety validation

**Cognitive Focus**: Therapeutic appropriateness, emotional safety, content design, validation

**Security Level**: HIGH

**MCP Tool Access**:
- ✅ ALLOWED: `view`, `codebase-retrieval`, `file-search`, `semantic-search`
- ⚠️ RESTRICTED: `str-replace-editor` (therapeutic content only), `save-file` (content only)
- ❌ DENIED: Code modification, database access, arbitrary commands, git operations

**File Pattern Scope**:
```
✅ ALLOWED (Read/Write):
  - content/therapeutic_interventions/**/*.md
  - docs/therapeutic/**/*.md

✅ ALLOWED (Read-Only):
  - src/therapeutic_safety/**/*.py
  - tests/**/*_therapeutic*.py
  - .github/instructions/therapeutic-safety.instructions.md

❌ DENIED:
  - src/**/*.py (code modification)
  - src/database/**/*
  - .env files
```

**Key Responsibilities**:
- Design therapeutic interventions
- Create emotional safety validation rules
- Review therapeutic content appropriateness
- Document therapeutic patterns
- Collaborate with safety auditor
- Ensure HIPAA compliance

**Example Scenarios**:
1. "Design therapeutic intervention for anxiety management"
2. "Create emotional safety validation rules"
3. "Review therapeutic content appropriateness"
4. "Document therapeutic patterns and best practices"

**Integration with Phase 2**:
- Reference: `.github/instructions/therapeutic-safety.instructions.md`
- Reference: `.github/instructions/testing-requirements.instructions.md`

---

## Implementation Checklist

### For Each Chat Mode:

- [ ] Create `.github/chatmodes/{mode-name}.chatmode.md`
- [ ] Define purpose and cognitive focus
- [ ] Specify security level (HIGH/MEDIUM/CRITICAL)
- [ ] List MCP tool access (ALLOWED/RESTRICTED/DENIED)
- [ ] Define file pattern scope
- [ ] Include 3-4 example scenarios
- [ ] Document limitations and constraints
- [ ] Reference Phase 2 instruction files
- [ ] Add approval gates where needed
- [ ] Include workflow examples

### Quality Assurance:

- [ ] Verify MCP boundaries prevent unauthorized access
- [ ] Confirm file patterns don't overlap inappropriately
- [ ] Validate security constraints
- [ ] Test example scenarios
- [ ] Review with domain experts
- [ ] Update AGENTS.md index

---

## Integration with Phase 2 Instructions

Each chat mode should reference relevant instruction files:

| Chat Mode | Instruction Files |
|-----------|------------------|
| DevOps Engineer | python-quality-standards, testing-requirements |
| QA Engineer | testing-requirements, python-quality-standards |
| API Gateway Engineer | api-security, python-quality-standards |
| Narrative Engine Developer | langgraph-orchestration, python-quality-standards |
| Therapeutic Content Creator | therapeutic-safety |

---

## Approval Gates by Mode

| Mode | Development | Staging | Production |
|------|-------------|---------|-----------|
| DevOps Engineer | No approval | Code review | Explicit approval |
| QA Engineer | No approval | Code review | N/A |
| API Gateway Engineer | No approval | Code review | Explicit approval |
| Narrative Engine Developer | No approval | Code review | N/A |
| Therapeutic Content Creator | No approval | Safety review | Safety approval |

---

## Success Criteria

After implementing all 5 modes:

- ✅ 100% of TTA development tasks covered
- ✅ All MCP boundaries properly enforced
- ✅ Security constraints validated
- ✅ Example scenarios tested
- ✅ Integration with Phase 2 complete
- ✅ AGENTS.md index updated
- ✅ Team onboarded to new modes

---

## Timeline Estimate

- **DevOps Engineer**: 2-3 hours
- **QA Engineer**: 2-3 hours
- **API Gateway Engineer**: 2-3 hours
- **Narrative Engine Developer**: 2-3 hours
- **Therapeutic Content Creator**: 2-3 hours
- **Testing & Integration**: 2-3 hours
- **Documentation & Onboarding**: 2-3 hours

**Total**: 14-21 hours (2-3 days)

---

**Next Step**: Proceed with Phase 4 implementation of these 5 critical chat modes.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___.github missing chat modes implementation guide document]]
