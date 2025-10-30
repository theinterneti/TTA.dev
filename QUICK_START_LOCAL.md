# 🎯 Quick Start: Using Your New Local Development Setup

**Created:** 2025-10-30

---

## ✅ What You Have Now

1. **`local/` directory** - For experimental code (gitignored ✅)
2. **Logseq Documentation Assistant** - Your first experimental tool
3. **Clear separation** - Public code vs. private experiments

---

## 🚀 Try It Right Now

### 1. Test the Logseq Documentation Assistant

```bash
cd /home/thein/repos/TTA.dev

# Analyze your Logseq documentation
python3 local/logseq-tools/doc_assistant.py logseq/
```

**You should see:**
```text
✅ Analyzed 4 files
📊 Total issues found: 8
⭐ Average quality score: 90.7/100

Files needing attention:
  - TTA.dev (Meta-Project).md: 3 issues (score: 89.4)
  - AI Research.md: 4 issues (score: 84.6)
```

### 2. See Detailed Examples

```bash
# Run the example script for interactive demos
python3 local/logseq-tools/example.py
```

This will show you:
- Full documentation analysis
- Single file analysis with details
- Auto-fix capabilities (dry run)
- Interactive "chat mode" simulation

### 3. Use It Like a Documentation Expert

**Scenario: "Fix all my Logseq documentation"**

```python
# In Python or IPython
import asyncio
import sys
sys.path.insert(0, '/home/thein/repos/TTA.dev')

from local.logseq_tools.doc_assistant import analyze_logseq_docs

# Get analysis
results = asyncio.run(analyze_logseq_docs("logseq"))

# See what needs attention
print(f"📊 {results['total_issues']} issues found")
print(f"⭐ Quality: {results['average_quality_score']}/100")

# Show worst files
for file in results['files_with_issues']:
    if file['quality_score'] < 85:
        print(f"⚠️  {file['file']}: {file['issues']} issues")
```

---

## 💬 "Chat Mode" - Become a Documentation Expert

### Ask: "What's wrong with my documentation?"

```bash
python3 local/logseq-tools/doc_assistant.py logseq/
```

The assistant will tell you:
- How many files analyzed
- Total issues found
- Average quality score
- Which files need attention

### Ask: "Show me details about [specific file]"

```python
from pathlib import Path
from local.logseq_tools.doc_assistant import LogseqDocumentAnalyzer

analyzer = LogseqDocumentAnalyzer(Path("logseq"))
analysis = await analyzer.analyze_file(
    Path("logseq/pages/AI Research.md")
)

# Show all issues
for issue in analysis.issues:
    print(f"Line {issue.line_number}: {issue.message}")
    if issue.suggested_fix:
        print(f"  Fix: {issue.suggested_fix}")
```

### Ask: "Fix this file for me"

```python
from local.logseq_tools.doc_assistant import LogseqDocumentFixer

analyzer = LogseqDocumentAnalyzer(Path("logseq"))
fixer = LogseqDocumentFixer(analyzer)

# Dry run first
result = await fixer.fix_file(
    Path("logseq/pages/AI Research.md"),
    dry_run=True
)
print(f"Would fix {result['fixes_applied']} issues")

# Apply if you're happy
if input("Apply fixes? (y/n): ").lower() == 'y':
    result = await fixer.fix_file(
        Path("logseq/pages/AI Research.md"),
        dry_run=False
    )
    print(f"✅ Fixed {result['fixes_applied']} issues")
```

---

## 🧪 Start Your Own Experiments

### Create a New Experiment

```bash
cd /home/thein/repos/TTA.dev/local/experiments

# Create a new primitive experiment
mkdir my_cache_primitive
cd my_cache_primitive

# Create a simple test file
cat > test_cache.py << 'EOF'
"""
Experimental cache primitive - testing different strategies
"""

class ExperimentalCache:
    def __init__(self):
        self.cache = {}

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache[key] = value

# Quick test
cache = ExperimentalCache()
cache.set("foo", "bar")
print(cache.get("foo"))  # Should print: bar
EOF

# Test it
python3 test_cache.py
```

**No tests required, no docs, no quality checks - just explore!**

### Create a Personal Utility

```bash
cd /home/thein/repos/TTA.dev/local/utilities

# Create a script to analyze your code
cat > analyze_primitives.py << 'EOF'
#!/usr/bin/env python3
"""
Personal utility: Analyze all primitives in the project
"""

from pathlib import Path

def find_primitives():
    """Find all primitive files"""
    primitives_dir = Path("/home/thein/repos/TTA.dev/packages/tta-dev-primitives/src")
    return list(primitives_dir.rglob("*primitive*.py"))

def main():
    prims = find_primitives()
    print(f"Found {len(prims)} primitive files:")
    for p in prims:
        print(f"  - {p.relative_to(Path.cwd().parent.parent)}")

if __name__ == "__main__":
    main()
EOF

chmod +x analyze_primitives.py
python3 analyze_primitives.py
```

---

## 📝 Document Your Experiments in Logseq

### In Your Daily Journal

```markdown
# 2025-10-30

## 🧪 Experiments

- Started testing new cache strategy in [[local/experiments/my_cache_primitive]]
  - Idea: LRU + TTL combined
  - Results: Promising, but needs more work
  - Next: Benchmark against standard LRU

## 💡 Ideas

- Could the Logseq assistant also check for orphaned pages?
- What about auto-generating weekly review summaries?
```

### Create an Experiment Page

```markdown
# Experiment: Advanced Cache Primitive

## Goal
Create a cache primitive with:
- LRU eviction
- TTL expiration
- Memory limits

## Status: Active

## Location
`local/experiments/my_cache_primitive/`

## Progress
- [x] Basic structure
- [x] LRU implementation
- [ ] TTL logic
- [ ] Memory limits
- [ ] Benchmarking

## Decision Points
- Q: Should TTL be per-item or global?
  A: Per-item for flexibility

- Q: What happens when memory limit reached?
  A: Evict LRU items first

## Next Steps
- Implement TTL logic
- Add memory monitoring
- Benchmark against functools.lru_cache
```

---

## 🎯 Real-World Workflows

### Morning Routine

```bash
# 1. Check documentation quality
python3 local/logseq-tools/doc_assistant.py logseq/

# 2. If issues found, review them
python3 local/logseq-tools/example.py

# 3. Open Logseq and plan your day
# (Link to documentation issues you want to fix)
```

### During Development

```bash
# Experimenting with a new idea
cd local/experiments
mkdir new_router_strategy
cd new_router_strategy

# Write code, test, iterate - no pressure!

# When it works, document in Logseq:
# "New router strategy works! See [[local/experiments/new_router_strategy]]"
```

### Before Committing Production Code

```bash
# Make sure you're not accidentally including local/
git status | grep "local/" && echo "❌ local/ should not be committed!"

# Run quality checks on production code only
uv run ruff format .
uv run ruff check . --fix
uvx pyright packages/
uv run pytest -v
```

---

## 🎨 Tips & Tricks

### Use IPython for Interactive Development

```bash
# Install if not already
pip install ipython

# Start IPython
ipython

# Now you can interactively test your experimental code
>>> import sys
>>> sys.path.insert(0, '/home/thein/repos/TTA.dev')
>>> from local.logseq_tools.doc_assistant import analyze_logseq_docs
>>> results = await analyze_logseq_docs("logseq")
```

### Create Aliases for Common Tasks

Add to your `.bashrc` or `.zshrc`:

```bash
# Logseq documentation check
alias logseq-check='cd /home/thein/repos/TTA.dev && python3 local/logseq-tools/doc_assistant.py logseq/'

# Go to experiments
alias experiments='cd /home/thein/repos/TTA.dev/local/experiments'

# Go to utilities
alias utils='cd /home/thein/repos/TTA.dev/local/utilities'
```

### Keep a Lab Notebook in Logseq

Create a `[[Lab Notebook]]` page:

```markdown
# Lab Notebook

## 2025-10-30

### Experiment: Logseq Documentation Assistant

**Hypothesis:** Can we automatically improve Logseq doc quality?

**Method:**
1. Parse markdown files
2. Detect common issues
3. Score quality
4. Auto-fix where possible

**Results:**
- ✅ Successfully analyzes files
- ✅ Finds 8+ common issue types
- ✅ Calculates quality scores
- ✅ Can auto-fix some issues

**Conclusion:** Successful! Ready for daily use.

**Next:** Add more issue types, test on larger documentation sets.
```

---

## 🚀 Next Steps

1. **✅ You've done the setup** - Everything is ready!

2. **🧪 Run the assistant** - Try it on your Logseq docs:
   ```bash
   python3 local/logseq-tools/doc_assistant.py logseq/
   ```

3. **📝 Start experimenting** - Create your first experiment in `local/experiments/`

4. **📚 Document in Logseq** - Track your experiments and learnings

5. **🎯 Iterate** - Improve your tools, graduate successful experiments

---

## 🆘 Need Help?

### Quick Reference

- **Local README:** `local/README.md`
- **Logseq Tools README:** `local/logseq-tools/README.md`
- **Architecture:** `local/logseq-tools/ARCHITECTURE.md` (if it exists)
- **This Guide:** `QUICK_START_LOCAL.md`

### Common Issues

**Q: Python import not working**
```bash
# Make sure you're in the right directory
cd /home/thein/repos/TTA.dev

# Add to path
import sys
sys.path.insert(0, '/home/thein/repos/TTA.dev')
```

**Q: Git trying to commit local/**
```bash
# Check .gitignore
grep "local/" .gitignore  # Should show: local/

# Verify it's ignored
git check-ignore local/  # Should output: local/
```

**Q: Want to graduate an experiment**
```bash
# See local/README.md section "Graduation Process"
# Basically: move code, add tests, add docs, create PR
```

---

**Happy Experimenting! 🎉**

---

**Created:** 2025-10-30
**For:** TTA.dev Local Development
**Status:** Ready to use!
