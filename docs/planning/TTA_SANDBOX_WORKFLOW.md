# TTA Migration Sandbox Workflow

**Date:** November 8, 2025
**Purpose:** Optimal workflow for TTA → TTA.dev migration using sandboxed environments

---

## The Approach: Hybrid Sandbox Strategy

**Key Insight:** Use TTA.dev as coordination hub, sandboxes for TTA audit/extraction work.

### Why This Works

✅ **Full Context:** Sandbox has complete TTA repository access
✅ **Isolation:** Work doesn't affect either repository until ready
✅ **Quality Gates:** Validate before committing to TTA.dev
✅ **Parallel Work:** Multiple sandboxes for different packages
✅ **Coordination:** TTA.dev tracks all work via Logseq TODOs

---

## Workflow Architecture

```
┌─────────────────────────────────────────────────────┐
│  TTA.dev Repository (Coordination Hub)              │
│  - Planning documents ✅                            │
│  - Logseq TODO tracking                             │
│  - Package specs                                    │
│  - Final integration                                │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ Coordinates
                  ↓
┌─────────────────────────────────────────────────────┐
│  Sandbox Environment (Audit & Extraction)           │
│  ┌───────────────────────────────────────────────┐ │
│  │ Cloned TTA Repository                         │ │
│  │ - Full package access                         │ │
│  │ - Run existing tests                          │ │
│  │ - Analyze dependencies                        │ │
│  │ - Extract core concepts                       │ │
│  └───────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────┐ │
│  │ Work Area                                     │ │
│  │ - Map primitives                              │ │
│  │ - Document patterns                           │ │
│  │ - Create extraction specs                     │ │
│  │ - Generate migration code                     │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ Delivers
                  ↓
┌─────────────────────────────────────────────────────┐
│  TTA.dev/packages/tta-narrative-primitives/         │
│  - Modernized primitives                            │
│  - Tests (100% coverage)                            │
│  - Examples                                         │
│  - Documentation                                    │
└─────────────────────────────────────────────────────┘
```

---

## Phase 1: Setup Sandbox Environment

### Step 1: Create Audit Sandbox

```bash
# In sandbox environment
git clone https://github.com/theinterneti/TTA.git tta-audit
cd tta-audit

# Install dependencies
uv sync --all-extras

# Verify environment
python --version  # Should be 3.11+
uv --version
```

### Step 2: Run TTA Tests (Baseline)

```bash
# Understand what works
uv run pytest -v

# Check coverage
uv run pytest --cov=packages --cov-report=html

# Identify test patterns
find tests/ -name "*.py" | head -20
```

### Step 3: Explore Package Structure

```bash
# Map packages
ls -la packages/

# Count lines per package
find packages/tta-narrative-engine -name "*.py" | xargs wc -l
find packages/tta-ai-framework -name "*.py" | xargs wc -l
find platform/agent-context -name "*.py" | xargs wc -l
find packages/ai-dev-toolkit -name "*.py" | xargs wc -l
```

---

## Phase 2: Audit Work (In Sandbox)

### Audit Checklist (Reference TTA.dev)

Use: `TTA.dev/docs/planning/TTA_AUDIT_CHECKLIST.md`

### Deliverables from Sandbox

1. **Package Analysis Reports**
   - `tta-narrative-engine-analysis.md`
   - `tta-ai-framework-analysis.md`
   - `universal-agent-context-comparison.md`
   - `ai-dev-toolkit-analysis.md`

2. **Primitive Mapping**
   - `primitive-mapping.json` - Maps TTA classes → TTA.dev primitives
   - `dependencies.txt` - External dependencies needed
   - `migration-complexity.md` - Complexity assessment

3. **Code Samples**
   - Extract 5-10 representative code samples
   - Document current patterns
   - Propose modernized versions

---

## Phase 3: Design Work (TTA.dev)

### Back in TTA.dev Repository

Transfer findings from sandbox:

```bash
# Copy analysis reports
cp ~/sandbox/tta-audit/analysis/*.md \
   ~/repos/TTA.dev/docs/planning/tta-analysis/

# Review findings
cat docs/planning/tta-analysis/tta-narrative-engine-analysis.md
```

### Create Package Spec

```bash
# In TTA.dev
cd ~/repos/TTA.dev

# Create package structure
mkdir -p packages/tta-narrative-primitives/{src,tests,examples,docs}

# Design primitives
vim packages/tta-narrative-primitives/DESIGN_SPEC.md
```

---

## Phase 4: Implementation (Sandbox + TTA.dev)

### Parallel Sandbox Strategy

**Sandbox 1: Extraction**
- Extract core concepts from TTA
- Create modernized versions
- Run against TTA tests for validation

**Sandbox 2: Integration**
- Clone TTA.dev
- Implement new primitives
- Run TTA.dev tests

**Coordination:** TTA.dev Logseq TODOs

### Sub-Agent Workflow

```yaml
# Agent assignment
agents:
  - name: "narrative-engine-agent"
    sandbox: "sandbox-1"
    task: "Audit tta-narrative-engine package"
    deliverable: "primitive-mapping.json"

  - name: "primitive-builder-agent"
    sandbox: "sandbox-2"
    task: "Implement CoherenceValidatorPrimitive"
    deliverable: "Working primitive with tests"

  - name: "integration-agent"
    workspace: "TTA.dev"
    task: "Integrate primitives, update docs"
    deliverable: "Updated PRIMITIVES_CATALOG.md"
```

---

## Phase 5: Quality Gates (Before Commit)

### In Sandbox (Pre-Integration)

```bash
# Type checking
uvx pyright packages/tta-narrative-primitives/

# Linting
uv run ruff check packages/tta-narrative-primitives/
uv run ruff format packages/tta-narrative-primitives/

# Testing
uv run pytest packages/tta-narrative-primitives/tests/ -v

# Coverage
uv run pytest packages/tta-narrative-primitives/ \
  --cov=packages/tta-narrative-primitives \
  --cov-report=html \
  --cov-fail-under=100
```

### In TTA.dev (Post-Integration)

```bash
# Full quality check
uv run pytest -v
uvx pyright packages/
uv run ruff check .

# Integration tests
uv run pytest tests/integration/ -v

# Documentation validation
python scripts/docs/check_md.py --all
```

---

## Workflow Commands

### Day-to-Day Development

**Morning: Check Coordination Hub**
```bash
# In TTA.dev
cd ~/repos/TTA.dev
cat logseq/journals/2025_11_08.md
# Review today's TODOs
```

**Work Session: In Sandbox**
```bash
# Start sandbox
cd ~/sandbox/tta-audit

# Do audit work
python analyze_package.py tta-narrative-engine

# Generate reports
./generate_analysis_report.sh
```

**Evening: Update Coordination Hub**
```bash
# Copy results to TTA.dev
cp analysis/* ~/repos/TTA.dev/docs/planning/tta-analysis/

# Update Logseq TODO
cd ~/repos/TTA.dev
# Mark tasks as DONE, add new findings
```

---

## File Organization

### TTA.dev Structure (Coordination)

```
TTA.dev/
├── docs/planning/
│   ├── TTA_REMEDIATION_PLAN.md       ✅ Strategy
│   ├── TTA_AUDIT_CHECKLIST.md        ✅ Audit guide
│   ├── TTA_SANDBOX_WORKFLOW.md       ✅ This file
│   └── tta-analysis/                 📊 Sandbox results
│       ├── tta-narrative-engine-analysis.md
│       ├── tta-ai-framework-analysis.md
│       ├── primitive-mapping.json
│       └── migration-complexity.md
├── packages/tta-narrative-primitives/
│   ├── DESIGN_SPEC.md                📋 Package design
│   ├── src/                          🚧 Implementation
│   ├── tests/                        ✅ Test suite
│   └── examples/                     📖 Examples
└── logseq/journals/
    └── 2025_11_08.md                 📝 Daily TODOs
```

### Sandbox Structure (Work Area)

```
~/sandbox/tta-audit/
├── TTA/                              📦 Cloned repo
│   ├── packages/
│   ├── tests/
│   └── docs/
├── analysis/                         📊 Generated reports
│   ├── tta-narrative-engine-analysis.md
│   ├── primitive-mapping.json
│   └── dependencies.txt
├── scripts/                          🔧 Analysis tools
│   ├── analyze_package.py
│   ├── extract_primitives.py
│   └── generate_analysis_report.sh
└── workspace/                        💻 Scratch area
    ├── prototype_primitives/
    └── test_conversions/
```

---

## Benefits of This Approach

### 1. Context Isolation

✅ **TTA context:** Full repository access in sandbox
✅ **TTA.dev context:** Clean development environment
✅ **No pollution:** Sandbox work doesn't affect either repo until ready

### 2. Parallel Development

✅ **Multiple sandboxes:** Different agents on different packages
✅ **Independent progress:** Don't block each other
✅ **Coordinated via:** TTA.dev Logseq TODOs

### 3. Quality Assurance

✅ **Test in sandbox:** Validate against TTA tests
✅ **Test in TTA.dev:** Validate with new architecture
✅ **Gate before merge:** Must pass both environments

### 4. Risk Mitigation

✅ **Reversible:** Sandbox can be destroyed and recreated
✅ **No remote impact:** Work doesn't touch GitHub until approved
✅ **Incremental:** One package at a time

---

## Example: Audit tta-narrative-engine

### In Sandbox

```bash
# Clone TTA
git clone https://github.com/theinterneti/TTA.git
cd TTA

# Analyze narrative engine
python << 'EOF'
import ast
from pathlib import Path

def analyze_module(file_path):
    """Extract classes, functions, and dependencies."""
    with open(file_path) as f:
        tree = ast.parse(f.read())

    classes = [node.name for node in ast.walk(tree)
               if isinstance(node, ast.ClassDef)]
    functions = [node.name for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef)]

    return {"classes": classes, "functions": functions}

# Scan narrative engine
pkg_path = Path("packages/tta-narrative-engine/src/tta_narrative")
results = {}

for py_file in pkg_path.rglob("*.py"):
    if py_file.stem != "__init__":
        results[str(py_file)] = analyze_module(py_file)

# Generate report
import json
with open("narrative-engine-structure.json", "w") as f:
    json.dump(results, f, indent=2)

print("Analysis complete: narrative-engine-structure.json")
EOF

# Review structure
cat narrative-engine-structure.json | jq '.[] | .classes[]' | sort | uniq
```

### Generate Mapping

```python
# In sandbox: create primitive mapping
mapping = {
    "TTA Classes": [
        {
            "name": "NarrativeCoherence",
            "file": "coherence/validator.py",
            "lines": 250,
            "dependencies": ["neo4j", "pydantic"],
            "maps_to": "CoherenceValidatorPrimitive",
            "complexity": "medium",
            "notes": "Needs OpenTelemetry integration"
        },
        {
            "name": "TherapeuticScorer",
            "file": "scoring/therapeutic.py",
            "lines": 180,
            "dependencies": ["numpy", "sklearn"],
            "maps_to": "TherapeuticScoringPrimitive",
            "complexity": "low",
            "notes": "Direct conversion, add type hints"
        }
    ]
}

import json
with open("primitive-mapping.json", "w") as f:
    json.dump(mapping, f, indent=2)
```

### Copy to TTA.dev

```bash
# Transfer analysis
cp narrative-engine-structure.json \
   ~/repos/TTA.dev/docs/planning/tta-analysis/

cp primitive-mapping.json \
   ~/repos/TTA.dev/docs/planning/tta-analysis/

# Update coordination hub
cd ~/repos/TTA.dev
```

---

## Sub-Agent Coordination

### Agent 1: Narrative Engine Auditor

**Sandbox:** `sandbox-narrative-audit`
**Task:** Audit tta-narrative-engine package
**Deliverable:** Complete analysis report + primitive mapping

**Commands:**
```bash
cd ~/sandbox/narrative-audit
python scripts/analyze_package.py tta-narrative-engine
./generate_report.sh
```

### Agent 2: Primitive Builder

**Sandbox:** `sandbox-primitive-build`
**Task:** Implement CoherenceValidatorPrimitive
**Deliverable:** Working primitive with tests

**Commands:**
```bash
cd ~/sandbox/primitive-build
# Clone TTA.dev
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev

# Create primitive
mkdir -p packages/tta-narrative-primitives/src/tta_narrative_primitives/core
# Implement based on mapping from Agent 1
```

### Coordination via TTA.dev

**Logseq TODO:**
```markdown
- TODO Audit tta-narrative-engine #dev-todo
  type:: analysis
  agent:: narrative-engine-auditor
  sandbox:: sandbox-narrative-audit
  status:: DOING
  deliverable:: primitive-mapping.json

- TODO Implement CoherenceValidatorPrimitive #dev-todo
  type:: implementation
  agent:: primitive-builder
  sandbox:: sandbox-primitive-build
  status:: not-started
  blocked:: Waiting for primitive mapping
  prerequisite:: [[Audit tta-narrative-engine]]
```

---

## Quality Checklist (Per Primitive)

Before moving from sandbox to TTA.dev:

- [ ] Type hints complete (100%)
- [ ] Tests written (100% coverage)
- [ ] Observability added (OpenTelemetry spans)
- [ ] Example created
- [ ] Documentation written
- [ ] Passes ruff check
- [ ] Passes pyright
- [ ] Composes with existing primitives
- [ ] Follows TTA.dev patterns

---

## Timeline with Sandbox Workflow

### Week 1-2: Audit Phase (In Sandbox)

**Sandbox work:**
- Clone TTA repository
- Run existing tests
- Analyze all 4 packages
- Generate mapping documents
- Extract code samples

**TTA.dev work:**
- Review analysis reports
- Update Logseq TODOs
- Refine package spec

### Week 3-5: Implementation Phase (Sandbox + TTA.dev)

**Sandbox work:**
- Prototype primitives
- Test against TTA data
- Validate conversions

**TTA.dev work:**
- Implement primitives
- Add tests
- Create examples
- Write documentation

### Week 6: Integration Phase (TTA.dev)

**TTA.dev work:**
- Final integration
- Quality checks
- Update catalog
- Release v1.1.0

---

## Getting Started

### Immediate Next Steps

1. **Set up audit sandbox:**
   ```bash
   mkdir -p ~/sandbox/tta-audit
   cd ~/sandbox/tta-audit
   git clone https://github.com/theinterneti/TTA.git
   cd TTA
   uv sync --all-extras
   ```

2. **Run initial analysis:**
   ```bash
   # Get package statistics
   find packages/ -name "*.py" -exec wc -l {} + | sort -n

   # List all classes
   grep -r "^class " packages/ --include="*.py"
   ```

3. **Update TTA.dev TODO:**
   ```bash
   cd ~/repos/TTA.dev
   # Add today's work to logseq/journals/2025_11_08.md
   ```

---

## Summary

**Optimal Workflow:**

1. **Coordination:** TTA.dev (Logseq TODOs, planning docs)
2. **Analysis:** Sandbox (full TTA context)
3. **Implementation:** Sandbox → TTA.dev (quality gates)
4. **Integration:** TTA.dev (final home)

**Key Principle:** Sandboxes provide isolated, full-context work environments. TTA.dev provides coordination, quality gates, and final integration.

**Ready to proceed?** Start with Phase 1: Setup audit sandbox.

---

**Created:** November 8, 2025
**Status:** Ready to execute
**Next:** Set up first audit sandbox


---
**Logseq:** [[TTA.dev/Docs/Planning/Tta_sandbox_workflow]]
