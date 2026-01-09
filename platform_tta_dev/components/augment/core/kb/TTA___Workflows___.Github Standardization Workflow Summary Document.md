---
title: TTA Agent Primitive Standardization Workflow - Summary
tags: #TTA
status: Active
repo: theinterneti/TTA
path: .github/STANDARDIZATION_WORKFLOW_SUMMARY.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/TTA Agent Primitive Standardization Workflow - Summary]]

**Created**: 2025-10-27
**File Location**: `.github/workflows/tta-standardization-onboarding.prompt.md`
**Status**: ✅ READY FOR EXECUTION

---

## Overview

This workflow file provides a comprehensive, step-by-step guide for transforming TTA's existing Augment-specific agent configuration into universally compatible, cross-platform agent primitives following the AI Native Development Framework standards.

The workflow is designed to be executed by the Augment agent via Auggie CLI and includes mandatory human validation gates to ensure quality and security.

---

## Workflow Structure

### Phase 1: Context Loading - Inventory Existing State
- Review current Augment configuration (`.augment/rules/`, `.augment/chatmodes/`)
- Map TTA domain architecture (agent orchestration, therapeutic safety, API gateway, player experience)
- Audit existing chat modes and identify gaps

### Phase 2: Establish Instructions Architecture
- Create modular `.instructions.md` files for each domain
- Add selective loading with YAML frontmatter (`applyTo` patterns)
- Compile universal `AGENTS.md` index for cross-platform compatibility

### Phase 3: Define Specialized Chat Modes with MCP Tool Boundaries
- Create `.github/chatmodes/` directory with role-based chat modes:
  - Therapeutic Safety Agent Mode (read-only, safety-focused)
  - LangGraph Orchestrator Mode (Python workflow orchestration)
  - Frontend Developer Mode (React/TypeScript UI)
  - API Gateway Engineer Mode (API security and routing)
- Enforce strict MCP tool access boundaries for each role

### Phase 4: Formalize Spec-Driven Development
- Create feature specification template (`.github/templates/tta-feature-template.spec.md`)
- Include mandatory validation criteria and handoff checklists
- Provide example specifications for common TTA feature types

### Phase 5: Human Validation Gate (MANDATORY)
- Compatibility verification (Augment-specific syntax removal)
- Security verification (MCP tool boundaries)
- Governance verification (context efficiency)
- Completeness verification (all rules accounted for)
- Requires explicit human approval before proceeding

### Phase 6: Commit and Document
- Create feature branch: `feature/agent-primitive-standardization`
- Commit all new files with descriptive messages
- Deprecate old Augment-specific configuration
- Create migration documentation for team

---

## Key Features

### 🔒 Security-First Design
- MCP tool boundaries prevent unauthorized access
- Therapeutic safety agent has read-only access to production code
- Database write access restricted to service layer
- Destructive commands explicitly denied for safety-critical roles

### 🎯 Cognitive Focus
- Role-based chat modes limit scope to specific domains
- Selective instruction loading prevents context pollution
- Clear separation of concerns (orchestration, safety, frontend, API)

### 🌐 Cross-Platform Compatibility
- All primitives use standard markdown and YAML
- No Augment-specific syntax in universal files
- Compatible with GitHub Copilot, OpenHands, Claude, and other agents
- Portable across different development environments

### 📋 Governance & Compliance
- Mandatory human validation gate before commits
- Comprehensive audit trail of configuration changes
- Migration documentation for team onboarding
- Deprecation notices for old configuration

---

## Expected Outputs

After successful execution, the repository will contain:

1. **`.github/instructions/` directory** with modular instruction files:
   - `python-langgraph-standards.instructions.md`
   - `therapeutic-safety-requirements.instructions.md`
   - `react-typescript-standards.instructions.md`
   - `api-security-requirements.instructions.md`
   - `testing-coverage-requirements.instructions.md`

2. **`.github/chatmodes/` directory** with role-based chat modes:
   - `therapeutic-safety-agent.chatmode.md`
   - `langgraph-orchestrator.chatmode.md`
   - `frontend-developer.chatmode.md`
   - `api-gateway-engineer.chatmode.md`

3. **`.github/templates/tta-feature-template.spec.md`** - Feature specification template

4. **`AGENTS.md`** - Universal agent configuration index

5. **Deprecation notices** on old Augment-specific configuration files

6. **Migration documentation** for team reference

---

## How to Execute

### Via Auggie CLI (Recommended)
```bash
auggie run .github/workflows/tta-standardization-onboarding.prompt.md
```

### Manual Execution
1. Read the workflow file carefully
2. Execute each phase sequentially
3. At Phase 5, present findings for human review
4. Wait for explicit approval before Phase 6
5. Commit changes with descriptive messages

---

## Success Criteria

✅ All TTA agent configuration is portable across Augment, GitHub Copilot, and OpenHands
✅ MCP tool boundaries enforce security and cognitive focus for each role
✅ Selective instruction loading prevents context pollution
✅ Feature specification template is ready for immediate use
✅ Human validation confirms compatibility, security, and governance standards
✅ All changes are committed and documented

---

## References

This workflow implements standards from:
- AI Native Development Framework (Agent Primitives specification)
- Model Context Protocol (MCP) for tool access control
- TTA Therapeutic Safety Requirements
- Cross-platform agent compatibility best practices

---

## Next Steps

1. Review this workflow file and the main workflow at `.github/workflows/tta-standardization-onboarding.prompt.md`
2. Execute the workflow via Auggie CLI or manually
3. At Phase 5, review the generated files and approve/request changes
4. Proceed with Phase 6 commit and documentation
5. Update team documentation with new agent primitive structure


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___.github standardization workflow summary document]]
