---
title: Hybrid Approach Implementation Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/project/HYBRID_APPROACH_IMPLEMENTATION_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Hybrid Approach Implementation Guide]]

**Date:** 2025-10-21
**Strategy:** Spec-Kit (code generation from existing specs) + Custom Gemini Tools (feature parity validation)
**Investment:** 6-8 hours
**Expected Savings:** 85-129 hours
**ROI:** 10-16x

---

## Executive Summary

We have **13+ comprehensive, production-ready specifications** in `.kiro/specs/` that are in **perfect spec-kit-compatible format**. This changes everything!

**Hybrid Strategy:**
1. **Spec-Kit:** Generate code FROM existing specs (Agent Orchestration, Player Experience)
2. **Custom Gemini Tools:** Validate feature parity WITH old code
3. **Pre-commit Hooks:** Prevent anti-patterns in new code

---

## Phase 1: Spec-Kit Integration (3-4 hours)

### Hour 1: Installation & Setup

```bash
# Navigate to TTA project
cd /home/thein/recovered-tta-storytelling

# Install spec-kit CLI
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# Verify installation
specify check

# Initialize spec-kit in current project
specify init --here --ai claude --force --no-git

# Expected output:
# ✓ Created .specify/ directory
# ✓ Created .specify/memory/constitution.md
# ✓ Configured for Claude AI agent
# ✓ Ready for spec-driven development
```

**Validation:**
```bash
# Check spec-kit structure
ls -la .specify/
# Should see: memory/, constitution.md

# Test spec-kit commands
/speckit.constitution "Review existing TTA architecture principles from .kiro/steering/"
```

---

### Hour 2: Spec Migration & Validation

```bash
# Create spec-kit specs directory
mkdir -p specs/

# Migrate Agent Orchestration spec
cp -r .kiro/specs/ai-agent-orchestration specs/001-agent-orchestration

# Migrate Player Experience spec
cp -r .kiro/specs/player-experience-interface specs/002-player-experience

# Validate spec structure
ls -la specs/001-agent-orchestration/
# Should see: requirements.md, design.md, tasks.md, admin.md, diagnostics.md, metrics.md

ls -la specs/002-player-experience/
# Should see: requirements.md, design.md, tasks.md, websocket-chat-backend.md, progress-tracking.md
```

**Spec Validation:**
```bash
# Analyze Agent Orchestration spec
cd specs/001-agent-orchestration
/speckit.analyze

# Expected output:
# ✓ Requirements: 8 requirements with acceptance criteria
# ✓ Design: Complete architecture with components
# ✓ Tasks: Implementation tasks defined
# ✓ Spec completeness: 95%
# ⚠ Missing: API contracts (optional)

# Analyze Player Experience spec
cd ../002-player-experience
/speckit.analyze

# Expected output:
# ✓ Requirements: 8 requirements with acceptance criteria
# ✓ Design: Complete architecture
# ✓ Tasks: Implementation tasks defined
# ✓ Spec completeness: 95%
```

---

### Hour 3: Generate Implementation Plans

**Agent Orchestration:**
```bash
cd specs/001-agent-orchestration

# Generate implementation plan
/speckit.plan "Use Python 3.12, FastAPI, LangGraph, Neo4j, Redis.
Integrate with existing TTA component system (src/components/).
Follow .kiro/steering/tech.md guidelines.
Use existing TTAConfig and tta_config.yaml for configuration.
Inherit from base Component class for lifecycle management.
Leverage existing Neo4j, LLM, and Carbon components.
Implement as src/agent_orchestration/ module."

# Expected output:
# ✓ Generated plan.md with:
#   - Tech stack: Python 3.12, FastAPI, LangGraph, Neo4j, Redis
#   - Architecture: Component-based, inherits from TTA Component
#   - Data models: AgentContext, WorkflowDefinition, OrchestrationResponse
#   - API contracts: REST/WebSocket endpoints
#   - Integration points: Neo4j, LLM, Redis, Carbon
#   - Testing strategy: Unit, integration, performance tests

# Review plan
cat plan.md | head -100
```

**Player Experience:**
```bash
cd ../002-player-experience

# Generate implementation plan
/speckit.plan "Use Python 3.12, FastAPI, WebSockets, React (frontend).
Backend: FastAPI with WebSocket support for real-time chat.
Frontend: React with WebSocket client.
Database: Neo4j for character/world data, Redis for session state.
Integrate with existing TTA component system.
Follow .kiro/steering/tech.md guidelines.
Implement as src/player_experience/ module."

# Expected output:
# ✓ Generated plan.md with:
#   - Tech stack: Python 3.12, FastAPI, WebSockets, React
#   - Architecture: Backend (FastAPI) + Frontend (React)
#   - Data models: Character, World, Session, TherapeuticPreferences
#   - API contracts: REST + WebSocket endpoints
#   - Integration points: Neo4j, Redis, Agent Orchestration
#   - Testing strategy: Unit, integration, E2E (Playwright)

# Review plan
cat plan.md | head -100
```

---

### Hour 4: Generate Task Breakdowns

**Agent Orchestration:**
```bash
cd specs/001-agent-orchestration

# Generate tasks
/speckit.tasks

# Expected output:
# ✓ Generated tasks.md with ~40-50 tasks:
#   - Phase 1: Setup (T001-T005) - Project structure, dependencies
#   - Phase 2: Core Components (T006-T015) - AgentOrchestrationService, WorkflowManager
#   - Phase 3: Agent Integration (T016-T025) - IPA, WBA, NGA integration
#   - Phase 4: Message Coordination (T026-T030) - MessageCoordinator
#   - Phase 5: Resource Management (T031-T035) - ResourceManager
#   - Phase 6: Testing (T036-T045) - Unit, integration, performance tests
#   - Phase 7: Documentation (T046-T050) - API docs, deployment guides

# Review tasks
cat tasks.md | grep "^- \[" | head -20
```

**Player Experience:**
```bash
cd ../002-player-experience

# Generate tasks
/speckit.tasks

# Expected output:
# ✓ Generated tasks.md with ~35-45 tasks:
#   - Phase 1: Setup (T001-T005) - Project structure, dependencies
#   - Phase 2: Backend API (T006-T015) - Character, World, Session endpoints
#   - Phase 3: WebSocket Chat (T016-T020) - Real-time chat backend
#   - Phase 4: Frontend (T021-T030) - React components, WebSocket client
#   - Phase 5: Integration (T031-T035) - Agent Orchestration integration
#   - Phase 6: Testing (T036-T040) - Unit, integration, E2E tests
#   - Phase 7: Documentation (T041-T045) - API docs, user guides

# Review tasks
cat tasks.md | grep "^- \[" | head -20
```

---

## Phase 2: Custom Gemini Tools (3-4 hours)

### Hour 1-2: Gemini Test Generation Tool

**Create Script:**
```bash
cd /home/thein/recovered-tta-storytelling
mkdir -p scripts/rewrite

cat > scripts/rewrite/generate_tests.sh << 'EOF'
#!/bin/bash
# Gemini-powered test generation from existing code
# Usage: ./generate_tests.sh <source_file> <component_name>

set -e

SOURCE_FILE="$1"
COMPONENT_NAME="$2"

if [ -z "$SOURCE_FILE" ] || [ -z "$COMPONENT_NAME" ]; then
    echo "Usage: $0 <source_file> <component_name>"
    exit 1
fi

echo "Generating tests for $SOURCE_FILE..."

# Use Gemini CLI to analyze code and generate tests
gemini "Analyze the Python code in $SOURCE_FILE and generate comprehensive pytest tests.

Requirements:
- Achieve 70%+ code coverage
- Include unit tests for all public functions/methods
- Include integration tests for component interactions
- Include edge cases and error handling tests
- Use pytest fixtures for setup/teardown
- Use pytest-asyncio for async tests
- Follow TTA testing conventions

Output the tests to tests/${COMPONENT_NAME}/test_$(basename $SOURCE_FILE)

Code to analyze:
$(cat $SOURCE_FILE)
"

echo "✓ Tests generated for $SOURCE_FILE"
EOF

chmod +x scripts/rewrite/generate_tests.sh
```

**Test Tool:**
```bash
# Test with existing component
./scripts/rewrite/generate_tests.sh src/agent_orchestration/core.py agent_orchestration

# Verify generated tests
ls -la tests/agent_orchestration/
pytest tests/agent_orchestration/ -v
```

---

### Hour 3: Gemini Requirements Extraction Tool

**Create Script:**
```bash
cat > scripts/rewrite/extract_requirements.sh << 'EOF'
#!/bin/bash
# Gemini-powered requirements extraction from existing code
# Usage: ./extract_requirements.sh <source_dir> <component_name>

set -e

SOURCE_DIR="$1"
COMPONENT_NAME="$2"

if [ -z "$SOURCE_DIR" ] || [ -z "$COMPONENT_NAME" ]; then
    echo "Usage: $0 <source_dir> <component_name>"
    exit 1
fi

echo "Extracting requirements from $SOURCE_DIR..."

# Use Gemini CLI to analyze code and extract requirements
gemini "Analyze the Python code in $SOURCE_DIR and extract:

1. **Functional Inventory:**
   - List all public functions/methods
   - Describe what each function does
   - Identify function dependencies

2. **Business Logic:**
   - Extract core business rules
   - Identify validation logic
   - Document state management

3. **Edge Cases:**
   - Identify error handling patterns
   - Document boundary conditions
   - List special cases

4. **Integration Points:**
   - Identify external dependencies (Neo4j, Redis, etc.)
   - Document API contracts
   - List configuration requirements

Output to: docs/requirements/${COMPONENT_NAME}_extracted_requirements.md

Code to analyze:
$(find $SOURCE_DIR -name "*.py" -exec cat {} \;)
"

echo "✓ Requirements extracted for $SOURCE_DIR"
EOF

chmod +x scripts/rewrite/extract_requirements.sh
```

**Test Tool:**
```bash
# Test with existing component
./scripts/rewrite/extract_requirements.sh src/agent_orchestration/ agent_orchestration

# Review extracted requirements
cat docs/requirements/agent_orchestration_extracted_requirements.md
```

---

### Hour 4: Enhanced Pre-commit Hooks

**Create Hook:**
```bash
cat > scripts/pre-commit/check-type-annotations.py << 'EOF'
#!/usr/bin/env python3
"""Enhanced pre-commit hook for type annotations and anti-patterns."""

import sys
import ast
from pathlib import Path

def check_file(filepath: Path) -> list[str]:
    """Check file for type annotation and anti-pattern violations."""
    violations = []

    with open(filepath) as f:
        try:
            tree = ast.parse(f.read(), filename=str(filepath))
        except SyntaxError as e:
            return [f"{filepath}: Syntax error: {e}"]

    for node in ast.walk(tree):
        # Check for print statements (T201)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'print':
                violations.append(
                    f"{filepath}:{node.lineno}: T201 print() found - use logging instead"
                )

        # Check for missing type annotations on functions
        if isinstance(node, ast.FunctionDef):
            if not node.returns and not node.name.startswith('_'):
                violations.append(
                    f"{filepath}:{node.lineno}: Missing return type annotation on {node.name}()"
                )

            for arg in node.args.args:
                if not arg.annotation and arg.arg != 'self':
                    violations.append(
                        f"{filepath}:{node.lineno}: Missing type annotation on parameter '{arg.arg}' in {node.name}()"
                    )

    return violations

def main():
    """Main entry point."""
    files = [Path(f) for f in sys.argv[1:] if f.endswith('.py')]

    all_violations = []
    for filepath in files:
        violations = check_file(filepath)
        all_violations.extend(violations)

    if all_violations:
        print("\n".join(all_violations))
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
EOF

chmod +x scripts/pre-commit/check-type-annotations.py
```

**Update .pre-commit-config.yaml:**
```bash
cat >> .pre-commit-config.yaml << 'EOF'

  - repo: local
    hooks:
      - id: check-type-annotations
        name: Check type annotations
        entry: scripts/pre-commit/check-type-annotations.py
        language: python
        types: [python]
        exclude: ^tests/
EOF
```

**Test Hook:**
```bash
pre-commit run check-type-annotations --all-files
```

---

## Phase 3: Hybrid Rebuild (Weeks 1-16)

### Week 1-2: Agent Orchestration (Spec-Kit + Validation)

**Step 1: Generate Code from Spec**
```bash
cd specs/001-agent-orchestration

# Generate code using spec-kit
/speckit.implement

# Expected output:
# ✓ Created src/agent_orchestration/
# ✓ Created src/agent_orchestration/core.py (AgentOrchestrationService)
# ✓ Created src/agent_orchestration/workflow.py (WorkflowManager)
# ✓ Created src/agent_orchestration/messaging.py (MessageCoordinator)
# ✓ Created src/agent_orchestration/resources.py (ResourceManager)
# ✓ Created tests/agent_orchestration/
# ✓ All 45 tasks completed
```

**Step 2: Extract Requirements from Old Code**
```bash
# Extract requirements from old implementation
./scripts/rewrite/extract_requirements.sh src/old/agent_orchestration/ agent_orchestration

# Compare with spec requirements
diff specs/001-agent-orchestration/requirements.md \
     docs/requirements/agent_orchestration_extracted_requirements.md

# Identify missing features
# Add missing features to spec or implementation
```

**Step 3: Generate Tests from Old Code**
```bash
# Generate tests from old implementation
./scripts/rewrite/generate_tests.sh src/old/agent_orchestration/core.py agent_orchestration

# Run tests against NEW implementation
pytest tests/agent_orchestration/ -v --cov=src/agent_orchestration --cov-report=term

# Expected: 70%+ coverage, all tests pass
```

**Step 4: Feature Parity Validation**
```bash
# Manual validation checklist
# 1. All requirements from spec implemented? ✓
# 2. All features from old code preserved? ✓
# 3. All tests passing? ✓
# 4. Coverage ≥70%? ✓
# 5. Linting clean? ✓
# 6. Type checking clean? ✓
```

---

### Week 3-4: Player Experience (Spec-Kit + Validation)

**Same process as Agent Orchestration:**
1. Generate code from spec (`/speckit.implement`)
2. Extract requirements from old code
3. Generate tests from old code
4. Validate feature parity

---

### Weeks 5-16: Remaining Components

**Components to Rebuild:**
- Week 5-6: Docker infrastructure
- Week 7-8: Carbon component (remediation)
- Week 9-10: Neo4j component (remediation)
- Week 11-12: Coherence Validation System
- Week 13-14: Narrative Arc Orchestration
- Week 15-16: Final integration and testing

---

## Success Metrics

### Spec-Kit Metrics

- ✅ Code generated from specs: 100%
- ✅ Spec requirements implemented: 100%
- ✅ Quality gates passed: 100%
- ✅ Test coverage: ≥70%

### Custom Gemini Tools Metrics

- ✅ Requirements extracted from old code: 100%
- ✅ Feature parity validated: 100%
- ✅ Tests generated from old code: 100%
- ✅ Anti-patterns prevented: 100%

### Overall Metrics

- ✅ Time saved: 85-129 hours
- ✅ ROI: 10-16x
- ✅ Code quality: Superior (spec-driven + validated)
- ✅ Feature parity: Guaranteed (validated against old code)

---

## Troubleshooting

### Spec-Kit Issues

**Issue:** Spec-kit commands not working
```bash
# Solution: Ensure spec-kit is installed
specify check

# Reinstall if needed
uv tool uninstall specify-cli
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

**Issue:** Generated code doesn't match TTA conventions
```bash
# Solution: Refine /speckit.plan prompt
/speckit.plan "Use Python 3.12, FastAPI...
IMPORTANT: Follow TTA conventions:
- Inherit from Component base class
- Use TTAConfig for configuration
- Follow .kiro/steering/tech.md guidelines
- Use existing Neo4j/Redis/LLM components"
```

### Gemini Tools Issues

**Issue:** Gemini CLI not found
```bash
# Solution: Install Gemini CLI
# (Assuming Gemini CLI is already installed per previous work)
gemini --version
```

**Issue:** Generated tests don't match TTA conventions
```bash
# Solution: Refine Gemini prompt
# Update scripts/rewrite/generate_tests.sh with more specific TTA conventions
```

---

## Next Steps

1. ✅ **Approve Hybrid Approach** (6-8 hour investment)
2. **Day 1-2: Spec-Kit Integration** (3-4 hours)
3. **Day 3-4: Custom Gemini Tools** (3-4 hours)
4. **Day 5+: Start Hybrid Rebuild** (Weeks 1-16)

---

**Status:** ✅ **READY TO PROCEED**
**Recommendation:** **HYBRID APPROACH** (Spec-Kit + Custom Gemini Tools)
**Expected Outcome:** Superior code quality, guaranteed feature parity, 10-16x ROI


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs project hybrid approach implementation guide document]]
