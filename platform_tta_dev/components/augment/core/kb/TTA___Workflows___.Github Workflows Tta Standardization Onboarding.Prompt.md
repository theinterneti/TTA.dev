---
title: Agentic Workflow: TTA Agent Primitive Standardization
tags: #TTA
status: Active
repo: theinterneti/TTA
path: .github/workflows/tta-standardization-onboarding.prompt.md
created: 2025-11-01
updated: 2025-11-01
---

# [[TTA/Workflows/Agentic Workflow: TTA Agent Primitive Standardization]]

You are the **TTA Agent Governance Engineer**. Your task is to perform an architectural review and conversion of the TTA repository's existing AI agent configuration into standardized Agent Primitives as specified in the AI Native Development Framework. This ensures maximum portability, security, and reliability across all AI coding agents (Augment, GitHub Copilot, Claude, OpenHands, etc.).

---

## Phase 1: Context Loading - Inventory Existing State

### Objective
Understand the current TTA agent configuration landscape before transformation.

### Tasks

1. **Review Current Augment Configuration**
   - Locate and analyze `.augment-guidelines` file in repository root (if exists)
   - Locate and analyze all files in `.augment/rules/` directory:
     - `Use-your-tools.md` - Tool usage guidelines
     - `avoid-long-files.md` - File size constraints
     - `prefer-uvx-for-tools.md` - Package manager preferences
   - Document the purpose and content of each existing rule file
   - Identify which rules are Augment-specific vs. universally applicable

2. **Map TTA Domain Architecture**
   - Identify core TTA microservices and components:
     - `src/agent_orchestration/` - LangGraph-based workflow orchestration
     - `src/therapeutic_safety/` - Safety validation and content filtering
     - `src/api_gateway/` - API routing and authentication
     - `src/player_experience/` - React/TypeScript player experience UI
   - Document technology stack per domain (Python, TypeScript, LangGraph, React, etc.)
   - Identify domain-specific coding standards and requirements

3. **Audit Existing Chat Modes**
   - Review all `.chatmode.md` files in `.augment/chatmodes/`:
     - `architect.chatmode.md`
     - `backend-dev.chatmode.md`
     - `backend-implementer.chatmode.md`
     - `devops.chatmode.md`
     - `frontend-dev.chatmode.md`
     - `qa-engineer.chatmode.md`
     - `safety-architect.chatmode.md`
   - Document scope, MCP tool access, and role-specific instructions
   - Identify gaps or overlaps in role coverage

---

## Phase 2: Establish Instructions Architecture (Context Engineering)

### Objective
Convert existing Augment-specific rules into modular, portable `.instructions.md` files with selective loading capabilities.

### Tasks

1. **Create Modular Instruction Files**
   - Create `.github/instructions/` directory if it doesn't exist
   - For each domain identified in Phase 1, create corresponding `.instructions.md` files:
     - `python-langgraph-standards.instructions.md` - LangGraph workflow patterns
     - `therapeutic-safety-requirements.instructions.md` - Safety validation rules
     - `react-typescript-standards.instructions.md` - Frontend coding standards
     - `api-security-requirements.instructions.md` - API security and authentication
     - `testing-coverage-requirements.instructions.md` - Test coverage standards

2. **Add Selective Loading with YAML Frontmatter**
   - Each `.instructions.md` file must include `applyTo` frontmatter to specify:
     - File patterns (e.g., `**/*.py`, `src/frontend/**/*.tsx`)
     - Directory scopes (e.g., `src/agent_orchestration/`)
     - Technology contexts (e.g., `python`, `typescript`, `react`)

   Example frontmatter:
   ```yaml
   ---
   applyTo:
     - pattern: "src/agent_orchestration/**/*.py"
     - pattern: "**/*_workflow.py"
   tags: ["python", "langgraph", "orchestration"]
   ---
   ```

3. **Compile Universal AGENTS.md**
   - Create or update `AGENTS.md` in repository root
   - Structure as hierarchical index of all `.instructions.md` files
   - Organize by domain/technology for efficient context loading
   - Include clear descriptions of when each instruction set applies
   - Ensure compatibility with GitHub Copilot, OpenHands, and other agents

---

## Phase 3: Define Specialized Chat Modes with MCP Tool Boundaries

### Objective
Create role-based chat modes with strict Model Context Protocol (MCP) tool access boundaries to enforce cognitive focus and prevent security violations.

### Tasks

1. **Create Chat Mode Directory**
   - Create `.github/chatmodes/` directory if it doesn't exist

2. **Define Therapeutic Safety Agent Mode**
   - **File**: `.github/chatmodes/therapeutic-safety-agent.chatmode.md`
   - **Purpose**: Enforce emotional safety and content validation (TTA's core therapeutic feature)
   - **Scope**: Limited to `src/therapeutic_safety/` directory
   - **MCP Tool Access**:
     - ✅ ALLOWED: `file-search`, `codebase-retrieval`, `view` (read-only tools)
     - ✅ ALLOWED: Safety-specific validation services
     - ❌ DENIED: `editFiles`, `runCommands`, `launch-process` (no production code modification)
     - ❌ DENIED: Database write access, API modification tools
   - **Instructions**: Must include strict guidelines for emotional safety validation, content filtering, and therapeutic appropriateness checks

3. **Define LangGraph Orchestrator Mode**
   - **File**: `.github/chatmodes/langgraph-orchestrator.chatmode.md`
   - **Purpose**: Workflow configuration and agent orchestration
   - **Scope**: Limited to `src/agent_orchestration/` directory (Python only)
   - **MCP Tool Access**:
     - ✅ ALLOWED: Python editing tools, LangGraph-specific utilities
     - ✅ ALLOWED: Workflow testing and validation tools
     - ❌ DENIED: Frontend modification tools (React/TypeScript)
     - ❌ DENIED: Database schema modification, patient data access
   - **Instructions**: Focus on LangGraph patterns, state management, and workflow orchestration best practices

4. **Define Frontend Development Mode**
   - **File**: `.github/chatmodes/frontend-developer.chatmode.md`
   - **Purpose**: React/TypeScript UI development
   - **Scope**: Limited to `src/player_experience/` directory
   - **MCP Tool Access**:
     - ✅ ALLOWED: TypeScript/React editing tools, component testing
     - ✅ ALLOWED: Frontend build and preview tools
     - ❌ DENIED: Backend API modification, database access
     - ❌ DENIED: Therapeutic safety logic modification (read-only access for integration)

5. **Define API Gateway Mode**
   - **File**: `.github/chatmodes/api-gateway-engineer.chatmode.md`
   - **Purpose**: API routing, authentication, and security
   - **Scope**: Limited to `src/api_gateway/` directory
   - **MCP Tool Access**:
     - ✅ ALLOWED: API configuration tools, security testing
     - ✅ ALLOWED: Authentication and authorization utilities
     - ❌ DENIED: Direct database access (must use service layer)
     - ❌ DENIED: Frontend modification, therapeutic logic changes

---

## Phase 4: Formalize Spec-Driven Development

### Objective
Create reusable specification templates that transform planning-phase thinking into implementation-ready blueprints with mandatory validation criteria.

### Tasks

1. **Create Feature Specification Template**
   - **File**: `.github/templates/tta-feature-template.spec.md`
   - **Required Sections**:
     - **Feature Overview**: Purpose, user story, business value
     - **Technical Architecture**: Components, dependencies, data flow
     - **Implementation Plan**: Step-by-step tasks with acceptance criteria
     - **Validation Criteria**:
       - Unit test coverage requirement (>90%)
       - Integration test scenarios
       - Therapeutic safety review checklist
       - Performance benchmarks
       - Security review requirements
     - **Handoff Checklist**:
       - [ ] All tests passing
       - [ ] Code review completed
       - [ ] Documentation updated
       - [ ] Therapeutic safety validated
       - [ ] Performance metrics met
       - [ ] Security scan passed

2. **Create Specification Examples**
   - Provide 1-2 example specifications for common TTA feature types:
     - New therapeutic intervention workflow
     - Frontend UI component addition
     - API endpoint creation

---

## Phase 5: Human Validation Gate

### 🚨 MANDATORY REVIEW CHECKPOINT

**STOP**: Before committing any generated files, present the following for human review and approval:

### Review Checklist

1. **Compatibility Verification**
   - [ ] All critical TTA coding standards are migrated to portable `.instructions.md` files
   - [ ] No Augment-specific syntax remains in universal files
   - [ ] All `.instructions.md` files use standard markdown and YAML frontmatter

2. **Security Verification**
   - [ ] MCP tool boundaries in `.chatmode.md` files prevent unauthorized access
   - [ ] Read-only access is enforced where appropriate
   - [ ] Destructive commands are explicitly denied for safety-critical roles

3. **Governance Verification**
   - [ ] `AGENTS.md` structure reflects optimal context efficiency for TTA's architecture
   - [ ] Instruction files are organized by domain and technology
   - [ ] Selective loading (`applyTo`) prevents context pollution

4. **Completeness Verification**
   - [ ] All existing `.augment/rules/` files are accounted for
   - [ ] Feature specification template includes all mandatory sections
   - [ ] Chat modes cover all major TTA development roles

### Approval Required

Present a summary report with:
- List of all files created/modified
- Migration mapping (old Augment rules → new portable primitives)
- Security boundary summary for each chat mode
- Any rules that could not be migrated (with explanation)

**Wait for explicit human approval before proceeding to commit.**

---

## Phase 6: Commit and Document

### Tasks (Only after Phase 5 approval)

1. **Commit Standardized Primitives**
   - Create feature branch: `feature/agent-primitive-standardization`
   - Commit all new files with descriptive commit messages
   - Update repository README to reference new agent primitive structure

2. **Deprecate Old Configuration**
   - Add deprecation notice to `.augment-guidelines` (if exists)
   - Add deprecation notices to files in `.augment/rules/`
   - Document migration path for team members

3. **Create Migration Documentation**
   - Document the standardization process for future reference
   - Provide examples of how to use new chat modes
   - Explain selective instruction loading for developers

---

## Success Criteria

This workflow is complete when:
- ✅ All TTA agent configuration is portable across Augment, GitHub Copilot, and OpenHands
- ✅ MCP tool boundaries enforce security and cognitive focus for each role
- ✅ Selective instruction loading prevents context pollution
- ✅ Feature specification template is ready for immediate use
- ✅ Human validation confirms compatibility, security, and governance standards
- ✅ All changes are committed and documented


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___.github workflows tta standardization onboarding.prompt]]
