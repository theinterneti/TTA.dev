# Local Development Quick Reference

**Essential commands and workflows for using the `local/` directory**

---

## 📋 Quick Commands

### Check Git Ignore Status

```bash
# Verify local/ is ignored
git check-ignore -v local/experiments/

# Should output: .gitignore:162:local/   local/experiments/

# Verify README is tracked
git ls-files local/

# Should output: local/README.md
```

### Start New Experiment

```bash
# Create experiment directory
cd local/experiments/primitives/
mkdir my_experiment && cd my_experiment

# Create files
touch __init__.py experiment.py

# Start coding (no tests, no docs required!)
```

### Test Experimental Code

```python
# Quick test script
import sys
sys.path.insert(0, '/home/thein/repos/TTA.dev/local/experiments')

from primitives.my_experiment import MyExperiment

result = MyExperiment().run()
print(result)
```

### Graduate to Production

```bash
# 1. Move code
cp -r local/prototypes/my_feature \
      packages/tta-dev-primitives/src/tta_dev_primitives/my_feature/

# 2. Write tests
cd packages/tta-dev-primitives/tests/
touch test_my_feature.py

# 3. Run quality checks
cd /home/thein/repos/TTA.dev
uv run ruff format .
uv run ruff check . --fix
uvx pyright packages/
uv run pytest -v

# 4. Create PR
git checkout -b feature/my-feature
git add packages/tta-dev-primitives/
git commit -m "feat(primitives): add MyFeature"
git push origin feature/my-feature
```

---

## 🗂️ Directory Layout

```
local/
├── README.md          # Organization guide (COMMITTED)
├── .prompts/          # AI agent prompts
├── experiments/       # Rapid prototyping
│   ├── primitives/
│   ├── workflows/
│   ├── agents/
│   └── integrations/
├── utilities/         # Personal automation
│   ├── scripts/
│   ├── generators/
│   └── analyzers/
├── prototypes/        # Features in development
│   ├── features/
│   ├── refactors/
│   └── optimizations/
├── logseq-tools/      # Documentation tools
│   ├── primitives/
│   ├── workflows/
│   ├── parsers/
│   └── analyzers/
├── notebooks/         # Jupyter exploration
│   ├── analysis/
│   ├── experiments/
│   └── tutorials/
└── data/              # Local test data
    ├── fixtures/
    ├── samples/
    └── outputs/
```

---

## 🎯 Decision Tree

```
Where should I put this code?
│
├─ Is it production-ready?
│  ├─ YES → packages/
│  └─ NO → Continue...
│
├─ Is it a personal tool?
│  ├─ YES → local/utilities/
│  └─ NO → Continue...
│
├─ Is it a prototype feature?
│  ├─ YES → local/prototypes/
│  └─ NO → Continue...
│
├─ Is it a quick experiment?
│  ├─ YES → local/experiments/
│  └─ NO → Continue...
│
├─ Is it Jupyter exploration?
│  ├─ YES → local/notebooks/
│  └─ NO → Continue...
│
└─ Is it test data?
   ├─ YES → local/data/
   └─ NO → Ask in GitHub Discussions
```

---

## ✅ Graduation Checklist

Copy this checklist when moving code from `local/` to `packages/`:

```markdown
### Code Quality
- [ ] Production-ready (no TODOs/hacks)
- [ ] Type hints on all public APIs
- [ ] Docstrings on all classes/functions
- [ ] Error handling for edge cases
- [ ] No hardcoded values

### Testing
- [ ] 100% test coverage
- [ ] All tests pass
- [ ] Edge cases tested
- [ ] Error cases tested
- [ ] Async behavior tested

### Documentation
- [ ] Package README updated
- [ ] Examples added
- [ ] PRIMITIVES_CATALOG.md updated
- [ ] CHANGELOG.md updated

### Quality Checks
- [ ] `uv run ruff format .`
- [ ] `uv run ruff check . --fix`
- [ ] `uvx pyright packages/`
- [ ] All tests pass

### Integration
- [ ] Works with existing primitives
- [ ] Composable with `>>` and `|`
- [ ] WorkflowContext integration
- [ ] Observability working
- [ ] No breaking changes
```

---

## 🚀 Common Workflows

### Workflow 1: Quick Experiment

```bash
cd local/experiments/primitives/
mkdir speculation && cd speculation
cat > spec.py << 'EOF'
from tta_dev_primitives import WorkflowPrimitive

class SpeculationPrimitive(WorkflowPrimitive):
    async def _execute_impl(self, context, input_data):
        # Quick idea...
        return input_data
EOF
```

### Workflow 2: Build Utility

```bash
cd local/utilities/scripts/
cat > analyze.py << 'EOF'
#!/usr/bin/env python3
def analyze():
    print("Analyzing...")

if __name__ == "__main__":
    analyze()
EOF
chmod +x analyze.py
./analyze.py
```

### Workflow 3: Prototype Feature

```bash
cd local/prototypes/features/
mkdir streaming_primitive && cd streaming_primitive
# Build feature...
# When ready: graduate to packages/
```

---

## 📚 Related Documentation

- **Full Guide:** [`LOCAL_DEVELOPMENT_GUIDE.md`](LOCAL_DEVELOPMENT_GUIDE.md)
- **Organization:** [`local/README.md`](local/README.md)
- **Package Development:** [`packages/tta-dev-primitives/AGENTS.md`](packages/tta-dev-primitives/AGENTS.md)
- **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md)

---

**Last Updated:** 2025-10-30
