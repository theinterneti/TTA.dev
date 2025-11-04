# KB Automation Quick Reference for Agents

**Fast lookup for AI agents using KB automation tools**

---

## 🚀 Quick Start

### When to Use KB Automation

✅ **USE when:**
- Starting a work session (validate KB state)
- After implementing features (check cross-references)
- Before committing (validate links)
- Syncing TODOs from code to journal
- Analyzing KB health

❌ **DON'T USE when:**
- Quick syntax fixes (no KB impact)
- Trivial changes (no docs needed)

---

## 🛠️ Available Tools (3 Implemented + 1 Planned)

### 1. LinkValidator ✅

**Purpose:** Validate `[[Wiki Links]]` in KB

**Quick Usage:**
```python
from tta_kb_automation.tools import LinkValidator
from pathlib import Path

validator = LinkValidator(kb_path=Path("logseq/"))
result = await validator.validate()

print(f"Broken: {len(result['broken_links'])}")
print(f"Health: {result['stats']['health_score']:.2%}")
```

**KB Page:** [[TTA KB Automation/LinkValidator]]

---

### 2. TODO Sync ✅

**Purpose:** Bridge code `# TODO:` comments and Logseq journal

**Quick Usage:**
```python
from tta_kb_automation.tools import TODOSync
from pathlib import Path

sync = TODOSync(
    code_paths=[Path("packages/")],
    kb_path=Path("logseq/")
)
todos = await sync.scan()
await sync.create_journal_entries(todos)

print(f"Synced {len(todos)} TODOs")
```

**KB Page:** [[TTA KB Automation/TODO Sync]]

---

### 3. CrossReferenceBuilder ✅

**Purpose:** Analyze code ↔ KB bidirectional references

**Quick Usage:**
```python
from tta_kb_automation.tools import CrossReferenceBuilder
from pathlib import Path

builder = CrossReferenceBuilder(
    kb_path=Path("logseq/"),
    code_path=Path("packages/")
)
xrefs = await builder.build()

print(f"Bidirectional: {xrefs['stats']['bidirectional_links']}")
```

**KB Page:** [[TTA KB Automation/CrossReferenceBuilder]]

---

### 4. SessionContextBuilder ⚠️

**Status:** PLANNED (stub only, not functional)

**Purpose:** Generate synthetic context from topic

**KB Page:** [[TTA KB Automation/SessionContextBuilder]]

---

## 📋 Common Workflows

### Pre-Commit Validation

```python
# Before committing, always validate KB
from tta_kb_automation.tools import LinkValidator
from pathlib import Path

validator = LinkValidator(kb_path=Path("logseq/"))
result = await validator.validate()

if result['stats']['health_score'] < 0.8:
    print(f"⚠️ Fix {len(result['broken_links'])} broken links")
else:
    print("✅ Safe to commit")
```

### Post-Implementation

```python
# After implementing, check cross-references
from tta_kb_automation.tools import CrossReferenceBuilder
from pathlib import Path

builder = CrossReferenceBuilder(
    kb_path=Path("logseq/"),
    code_path=Path("packages/")
)
xrefs = await builder.build()

# Check if your new file needs KB links
new_file = "packages/.../my_new_file.py"
if new_file in xrefs['code_files_missing_kb']:
    print("Add KB links to new file")
```

### Daily TODO Sync

```python
# Sync TODOs from code to journal
from tta_kb_automation.tools import TODOSync
from pathlib import Path

sync = TODOSync(
    code_paths=[Path("packages/tta-dev-primitives/src")],
    kb_path=Path("logseq/")
)
todos = await sync.scan()
await sync.create_journal_entries(todos)
```

---

## 🧪 Testing

### Run Integration Tests

```bash
# Validate tools against real KB
pytest tests/integration/test_real_kb_integration.py -m integration -v
```

### Expected Behavior

- ✅ 4 tests should pass
- ✅ Execution time: < 5 seconds
- ✅ Real KB validated (logseq/)
- ✅ Real code validated (packages/)

---

## 📊 Current Status (Phase 4 Complete)

### Implemented ✅
- LinkValidator - Full implementation
- TODO Sync - Full implementation
- CrossReferenceBuilder - Full implementation

### Planned ⚠️
- SessionContextBuilder - Stub only

### Testing ✅
- Unit tests: Complete
- Integration tests: 4 end-to-end workflows
- Coverage: High

### Documentation ✅
- Tool KB pages: 4 comprehensive guides
- Agent guide: AGENTS.md updated
- API docs: Available in KB

---

## 🔗 Key Documents

- **Agent Guide:** `packages/tta-kb-automation/AGENTS.md`
- **Package README:** `packages/tta-kb-automation/README.md`
- **Phase 4 Summary:** `KB_AUTOMATION_PHASE4_COMPLETE.md`
- **Integration Tests:** `tests/integration/test_real_kb_integration.py`

---

## 💡 Pro Tips

1. **Always validate before commit** - Prevents broken KB links
2. **Run TODO sync daily** - Keeps journal updated
3. **Check cross-refs after implementation** - Ensures docs in sync
4. **Use integration tests** - Validates against real KB
5. **Read KB pages** - Full documentation with examples

---

**Last Updated:** November 3, 2025
**Package:** tta-kb-automation v0.1.0
**Status:** ✅ Phase 4 Complete
