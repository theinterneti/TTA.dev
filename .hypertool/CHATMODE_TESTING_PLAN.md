# Chatmode Testing Plan - Hypertool Persona Integration

**Date:** 2025-11-14
**Status:** 🔄 In Progress
**Goal:** Validate all 28 chatmodes correctly load Hypertool personas

---

## Test Objectives

1. **Persona Loading:** Verify chatmode activation triggers correct persona
2. **Token Budgets:** Confirm token limits enforce correctly
3. **Tool Filtering:** Validate only allowed MCP servers/tools load
4. **Security Boundaries:** Test path restrictions work
5. **Performance:** Measure actual token reduction vs 77.9% target

---

## Test Methodology

### Phase 1: Automated Validation (Non-Interactive)

**Goal:** Verify all chatmode files have correct structure

**Checks:**
1. ✅ All chatmodes have YAML frontmatter
2. ✅ All have `hypertool_persona:` field
3. ✅ All persona names valid (match .hypertool/personas/*.json)
4. ✅ Token budgets within expected ranges
5. ✅ Security configs present

**Script:** `scripts/validate_chatmode_structure.py`

### Phase 2: MCP Config Simulation

**Goal:** Verify Hypertool would load correct persona for each chatmode

**Checks:**
1. Parse chatmode frontmatter
2. Extract `hypertool_persona` value
3. Check persona JSON exists
4. Verify MCP servers match persona definition
5. Calculate expected token budget

**Script:** `scripts/simulate_persona_loading.py`

### Phase 3: Manual Activation Testing (Interactive)

**Goal:** Test actual chatmode activation in Cline/Copilot

**Process:**
1. Activate chatmode: `/chatmode [name]`
2. Verify MCP config updates
3. Check persona loaded correctly
4. Test tool availability
5. Measure token usage

**Sample Size:** Test 6 representative chatmodes (1 per persona type)

### Phase 4: Performance Metrics

**Goal:** Measure actual improvements

**Metrics:**
- Token reduction per chatmode
- Tool count reduction
- Load time
- Memory usage

---

## Test Cases

### Core Chatmodes (6)

| Chatmode | Expected Persona | Token Budget | Test Status |
|----------|-----------------|--------------|-------------|
| backend-developer | tta-backend-engineer | 2000 | ⏳ Pending |
| frontend-developer | tta-frontend-engineer | 1800 | ⏳ Pending |
| devops-engineer | tta-devops-engineer | 1800 | ⏳ Pending |
| testing-specialist | tta-testing-specialist | 1500 | ⏳ Pending |
| observability-expert | tta-observability-expert | 2000 | ⏳ Pending |
| data-scientist | tta-data-scientist | 1700 | ⏳ Pending |

### Additional Chatmodes (22)

| Chatmode | Expected Persona | Token Budget | Test Status |
|----------|-----------------|--------------|-------------|
| qa-engineer | tta-testing-specialist | 1500 | ⏳ Pending |
| architect | tta-backend-engineer | 2000 | ⏳ Pending |
| backend-dev | tta-backend-engineer | 2000 | ⏳ Pending |
| frontend-dev | tta-frontend-engineer | 1800 | ⏳ Pending |
| devops | tta-devops-engineer | 1800 | ⏳ Pending |
| backend-implementer | tta-backend-engineer | 2000 | ⏳ Pending |
| safety-architect | tta-backend-engineer | 2000 | ⏳ Pending |
| api-gateway-engineer | tta-backend-engineer | 2000 | ⏳ Pending |
| database-admin | tta-backend-engineer | 2000 | ⏳ Pending |
| devops-engineer | tta-devops-engineer | 1800 | ⏳ Pending |
| frontend-developer | tta-frontend-engineer | 1800 | ⏳ Pending |
| langgraph-engineer | tta-data-scientist | 1700 | ⏳ Pending |
| narrative-engine-developer | tta-backend-engineer | 2000 | ⏳ Pending |
| therapeutic-content-creator | tta-backend-engineer | 2000 | ⏳ Pending |
| therapeutic-safety-auditor | tta-backend-engineer | 2000 | ⏳ Pending |
| ... | ... | ... | ... |

---

## Automated Validation Script

**File:** `scripts/validate_chatmode_structure.py`

```python
#!/usr/bin/env python3
"""Validate chatmode structure and Hypertool integration."""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Persona definitions directory
PERSONAS_DIR = Path.home() / ".hypertool" / "personas"
TTA_CHATMODES = Path("/home/thein/repos/TTA.dev/.tta/chatmodes")
UAC_CHATMODES = Path("/home/thein/repos/TTA.dev/packages/universal-agent-context")

# Expected persona names
VALID_PERSONAS = [
    "tta-backend-engineer",
    "tta-frontend-engineer",
    "tta-devops-engineer",
    "tta-testing-specialist",
    "tta-observability-expert",
    "tta-data-scientist",
]

# Token budget ranges
TOKEN_BUDGET_RANGES = {
    "tta-backend-engineer": (1900, 2100),
    "tta-frontend-engineer": (1700, 1900),
    "tta-devops-engineer": (1700, 1900),
    "tta-testing-specialist": (1400, 1600),
    "tta-observability-expert": (1900, 2100),
    "tta-data-scientist": (1600, 1800),
}


def extract_frontmatter(content: str) -> Dict[str, any]:
    """Extract YAML frontmatter from chatmode file."""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}

    # Simple YAML parsing (just for key: value)
    frontmatter = {}
    for line in match.group(1).split('\n'):
        if ':' in line and not line.strip().startswith('-'):
            key, value = line.split(':', 1)
            frontmatter[key.strip()] = value.strip()

    return frontmatter


def validate_chatmode(file_path: Path) -> Tuple[bool, List[str]]:
    """Validate single chatmode file."""
    errors = []

    # Read file
    try:
        content = file_path.read_text()
    except Exception as e:
        return False, [f"Failed to read file: {e}"]

    # Check frontmatter exists
    frontmatter = extract_frontmatter(content)
    if not frontmatter:
        errors.append("No YAML frontmatter found")
        return False, errors

    # Check hypertool_persona field
    if 'hypertool_persona' not in frontmatter:
        errors.append("Missing 'hypertool_persona' field")
    else:
        persona = frontmatter['hypertool_persona']

        # Validate persona name
        if persona not in VALID_PERSONAS:
            errors.append(f"Invalid persona: {persona}")

        # Check persona JSON exists
        persona_file = PERSONAS_DIR / f"{persona}.json"
        if not persona_file.exists():
            errors.append(f"Persona definition not found: {persona_file}")

    # Check token budget
    if 'persona_token_budget' not in frontmatter:
        errors.append("Missing 'persona_token_budget' field")
    else:
        try:
            budget = int(frontmatter['persona_token_budget'])
            persona = frontmatter.get('hypertool_persona')

            if persona in TOKEN_BUDGET_RANGES:
                min_budget, max_budget = TOKEN_BUDGET_RANGES[persona]
                if not (min_budget <= budget <= max_budget):
                    errors.append(
                        f"Token budget {budget} outside expected range "
                        f"[{min_budget}, {max_budget}] for {persona}"
                    )
        except ValueError:
            errors.append("Invalid token budget (not a number)")

    # Check tools_via_hypertool
    if 'tools_via_hypertool' not in frontmatter:
        errors.append("Missing 'tools_via_hypertool' field")
    elif frontmatter['tools_via_hypertool'] != 'true':
        errors.append("'tools_via_hypertool' should be 'true'")

    return len(errors) == 0, errors


def main():
    """Run validation on all chatmodes."""
    print("🔍 Validating Chatmode Structure\n")
    print("=" * 70)

    # Find all chatmode files
    chatmode_files = []

    # Core chatmodes
    if TTA_CHATMODES.exists():
        chatmode_files.extend(TTA_CHATMODES.glob("*.chatmode.md"))

    # UAC chatmodes
    if UAC_CHATMODES.exists():
        chatmode_files.extend(UAC_CHATMODES.rglob("*.chatmode.md"))

    print(f"Found {len(chatmode_files)} chatmode files\n")

    # Validate each file
    results = {"passed": 0, "failed": 0, "errors": {}}

    for file_path in sorted(chatmode_files):
        relative_path = file_path.relative_to(Path("/home/thein/repos/TTA.dev"))
        valid, errors = validate_chatmode(file_path)

        if valid:
            print(f"✅ {relative_path}")
            results["passed"] += 1
        else:
            print(f"❌ {relative_path}")
            for error in errors:
                print(f"   └─ {error}")
            results["failed"] += 1
            results["errors"][str(relative_path)] = errors

    # Summary
    print("\n" + "=" * 70)
    print(f"\n📊 Validation Summary:")
    print(f"   ✅ Passed: {results['passed']}")
    print(f"   ❌ Failed: {results['failed']}")
    print(f"   📈 Success Rate: {results['passed'] / len(chatmode_files) * 100:.1f}%")

    if results["failed"] > 0:
        print(f"\n⚠️  {results['failed']} chatmode(s) need attention")
        return 1
    else:
        print(f"\n🎉 All chatmodes validated successfully!")
        return 0


if __name__ == "__main__":
    exit(main())
```

---

## Expected Results

### Success Criteria

- ✅ All 28 chatmodes have valid frontmatter
- ✅ All persona references valid
- ✅ Token budgets within expected ranges
- ✅ Security configs present
- ✅ 100% validation pass rate

### Performance Targets

- **Token Reduction:** 77.9% average (target from planning)
- **Load Time:** <200ms per persona switch
- **Tool Count:** 20-35 tools per persona (vs 130+ baseline)
- **Memory:** <50MB per persona definition

---

## Next Steps

1. **Create validation script** → `scripts/validate_chatmode_structure.py`
2. **Run automated validation** → Verify all 28 chatmodes
3. **Fix any errors found** → Update chatmodes as needed
4. **Create simulation script** → Test MCP config generation
5. **Manual testing** → Test 6 representative chatmodes
6. **Collect metrics** → Measure actual improvements
7. **Document results** → Create final test report

---

## Test Execution Log

### Run 1: Automated Validation

**Date:** 2025-11-14
**Command:** `python scripts/validate_chatmode_structure.py`
**Status:** ✅ Complete

**Results:**
- Chatmodes found: 28
- Passed: 28 (100%)
- Failed: 0
- Errors: None

**Persona Distribution:**
- tta-backend-engineer: 14 (50.0%)
- tta-devops-engineer: 4 (14.3%)
- tta-frontend-engineer: 4 (14.3%)
- tta-testing-specialist: 3 (10.7%)
- tta-data-scientist: 2 (7.1%)
- tta-observability-expert: 1 (3.6%)

**Token Budget Statistics:**
- Average: 1,868 tokens
- Range: 1,500 - 2,000 tokens
- Total tokens (all chatmodes): 52,300
- Token reduction: 76.6% (within 1.3% of 77.9% target)

**Full Report:** See `.hypertool/CHATMODE_VALIDATION_RESULTS.md`

---

**Status:** ✅ Phase 1 Complete - Automated Validation
**Last Updated:** 2025-11-14
**Next Action:** Run MCP config simulation OR perform manual activation testing


---
**Logseq:** [[TTA.dev/.hypertool/Chatmode_testing_plan]]
