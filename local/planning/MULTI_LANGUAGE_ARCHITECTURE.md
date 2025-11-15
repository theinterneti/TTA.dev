# Multi-Language Repository Architecture

**TTA.dev Multi-Language Development Strategy**

---

## 🎯 Philosophy

TTA.dev is a **polyglot agentic toolkit** supporting multiple programming languages with:
- **Production Code**: Highly tested, battle-hardened tools for agentic workflows
- **Example Code**: Educational demonstrations clearly marked and isolated
- **Language Parity**: Consistent patterns across Python, JavaScript/TypeScript, and future languages

---

## 📁 Repository Structure

```
TTA.dev/
├── packages/                          # Language-specific packages
│   ├── tta-dev-primitives/           # Python: Core workflow primitives
│   │   ├── src/                      # Production code (>80% coverage)
│   │   ├── tests/                    # Comprehensive test suite
│   │   └── examples/                 # ✨ EXAMPLE CODE - Clearly marked
│   │
│   ├── js-dev-primitives/            # JavaScript/TypeScript: Core primitives
│   │   ├── src/                      # Production code (>80% coverage)
│   │   ├── test/                     # Comprehensive test suite
│   │   └── examples/                 # ✨ EXAMPLE CODE - Clearly marked
│   │
│   ├── python-pathway/               # Python: Code analysis tools (INTERNAL)
│   │   ├── chatmodes/                # Agent chat mode implementations
│   │   └── workflows/                # Analysis workflows
│   │
│   └── [future-lang]-pathway/        # Future: Rust, Go, etc.
│
├── examples/                          # ✨ Cross-language integration examples
│   ├── github-agent-hq/              # Multi-agent coordination example
│   ├── cross-language-workflows/     # Python + JS integration
│   └── README.md                     # "THIS IS EXAMPLE CODE" disclaimer
│
├── scripts/                           # Automation & validation scripts
│   ├── validation/                   # Quality checks across all languages
│   │   ├── validate-python.sh
│   │   ├── validate-javascript.sh
│   │   └── validate-all.sh
│   └── testing/                      # Test runners
│       ├── run-python-tests.sh
│       ├── run-js-tests.sh
│       └── run-all-tests.sh
│
├── .github/
│   ├── instructions/                 # Path-based instruction files
│   │   ├── python-source.instructions.md
│   │   ├── javascript-source.instructions.md
│   │   ├── typescript-source.instructions.md
│   │   ├── example-code.instructions.md
│   │   └── tests.instructions.md     # Language-agnostic testing rules
│   │
│   └── workflows/                    # CI/CD for all languages
│       ├── python-ci.yml
│       ├── javascript-ci.yml
│       └── integration-tests.yml
│
├── docs/
│   ├── languages/                    # Language-specific guides
│   │   ├── python/
│   │   ├── javascript/
│   │   └── cross-language/
│   └── architecture/
│       └── MULTI_LANGUAGE_ARCHITECTURE.md  # This file
│
└── pyproject.toml / package.json     # Workspace-level configs
```

---

## 🏷️ Code Classification

### 1. Production Code (80%+ Test Coverage Required)

**Location:** `packages/*/src/` or `packages/*/lib/`

**Characteristics:**
- Used by agentic workflows internally
- High test coverage (minimum 80%)
- Comprehensive error handling
- Full type safety
- Production-quality documentation

**Examples:**
- `packages/tta-dev-primitives/src/` - Python workflow primitives
- `packages/js-dev-primitives/src/` - JavaScript workflow primitives
- `packages/python-pathway/workflows/` - Python analysis tools

**Marking:** No special marker needed (default assumption)

### 2. Example Code (Educational, May Have Lower Coverage)

**Location:**
- `packages/*/examples/`
- `examples/` (root-level cross-language examples)

**Characteristics:**
- Demonstrates usage patterns
- May sacrifice robustness for clarity
- Test coverage encouraged but not enforced
- Clear educational comments
- **Must have README.md with disclaimer**

**Marking:**
```python
# ✨ EXAMPLE CODE
# This file demonstrates X pattern. For production use, see packages/X/src/
```

**Every example directory must have:**
```markdown
# Examples

⚠️ **THIS IS EXAMPLE CODE** - These files are for educational purposes.
For production-ready code, see `../src/` or the main package documentation.
```

### 3. Internal Tools (Used by Agentic Workflows)

**Location:**
- `packages/python-pathway/` - Python code analysis
- `packages/js-pathway/` (future) - JavaScript code analysis
- `scripts/` - Automation scripts

**Characteristics:**
- Used by AI agents during development
- High reliability required
- Well-tested (70%+ coverage minimum)
- Clear interfaces

**Marking:**
```python
# 🤖 INTERNAL TOOL - Used by agentic workflows
# This module provides X capability for AI agents working on the codebase
```

---

## 🌍 Language-Specific Standards

### Python (Python 3.11+)

**Package Manager:** `uv` (NOT pip)

**Quality Standards:**
- **Type Coverage:** 100% for public APIs (Pyright)
- **Test Coverage:** 80%+ for src/, 70%+ for internal tools
- **Formatting:** Ruff (`uv run ruff format .`)
- **Linting:** Ruff (`uv run ruff check . --fix`)
- **Testing:** pytest with pytest-asyncio

**File Patterns:**
- `packages/**/src/**/*.py` → `python-source.instructions.md`
- `packages/**/tests/**/*.py` → `tests.instructions.md`
- `packages/**/examples/**/*.py` → `example-code.instructions.md`
- `scripts/**/*.py` → `scripts.instructions.md`

**Example Production Code:**
```python
"""Module docstring with clear purpose."""

from typing import Any

class WorkflowPrimitive[T, U]:
    """Production-quality primitive with full type hints."""

    async def execute(self, context: WorkflowContext, input_data: T) -> U:
        """Execute the primitive.

        Args:
            context: Workflow execution context
            input_data: Input data of type T

        Returns:
            Result of type U

        Raises:
            ValueError: If input is invalid
        """
        ...
```

### JavaScript/TypeScript

**Package Manager:** `npm` or `yarn` (choose one workspace-wide)

**Quality Standards:**
- **Type Coverage:** 100% for public APIs (TypeScript strict mode)
- **Test Coverage:** 80%+ for src/, 70%+ for internal tools
- **Formatting:** Prettier
- **Linting:** ESLint
- **Testing:** Jest or Vitest

**File Patterns:**
- `packages/**/src/**/*.{ts,js}` → `javascript-source.instructions.md`
- `packages/**/test/**/*.{ts,js}` → `tests.instructions.md`
- `packages/**/examples/**/*.{ts,js}` → `example-code.instructions.md`

**Example Production Code:**
```typescript
/**
 * Production-quality primitive with full type safety
 */
export class WorkflowPrimitive<T, U> {
  /**
   * Execute the primitive
   * @param context - Workflow execution context
   * @param inputData - Input data of type T
   * @returns Result of type U
   * @throws {Error} If input is invalid
   */
  async execute(context: WorkflowContext, inputData: T): Promise<U> {
    // Implementation
  }
}
```

---

## 🔄 Cross-Language Patterns

### Shared Concepts

All languages implement these core primitives:
- `WorkflowPrimitive` - Base primitive class
- `SequentialPrimitive` - Sequential composition
- `ParallelPrimitive` - Parallel execution
- `RouterPrimitive` - Dynamic routing
- `RetryPrimitive` - Retry with backoff
- `CachePrimitive` - LRU + TTL caching

### Naming Conventions

| Concept | Python | JavaScript/TypeScript |
|---------|--------|----------------------|
| Classes | `PascalCase` | `PascalCase` |
| Functions | `snake_case` | `camelCase` |
| Constants | `UPPER_SNAKE_CASE` | `UPPER_SNAKE_CASE` |
| Files | `snake_case.py` | `kebab-case.ts` |
| Tests | `test_*.py` | `*.test.ts` or `*.spec.ts` |

### API Consistency

**Python:**
```python
workflow = step1 >> step2 >> step3  # Sequential
workflow = branch1 | branch2 | branch3  # Parallel
result = await workflow.execute(context, input_data)
```

**JavaScript/TypeScript:**
```typescript
const workflow = step1.then(step2).then(step3);  // Sequential
const workflow = parallel(branch1, branch2, branch3);  // Parallel
const result = await workflow.execute(context, inputData);
```

---

## 🧪 Testing Strategy

### Per-Language Test Requirements

| Code Type | Python Coverage | JS/TS Coverage | Test Location |
|-----------|----------------|----------------|---------------|
| Production Code | 80%+ | 80%+ | `tests/` or `test/` |
| Internal Tools | 70%+ | 70%+ | `tests/` or `test/` |
| Example Code | Encouraged | Encouraged | `examples/**/test/` (optional) |

### Cross-Language Integration Tests

**Location:** `tests/integration/cross-language/`

**Purpose:** Verify Python + JavaScript primitives work together

**Example:**
```python
# tests/integration/cross-language/test_python_js_interop.py
import subprocess
import json

@pytest.mark.asyncio
async def test_python_calls_js_primitive():
    """Test Python workflow calling JavaScript primitive via subprocess."""
    result = subprocess.run(
        ["node", "packages/js-dev-primitives/examples/router.js"],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    assert data["status"] == "success"
```

---

## 📋 Quality Checklist

### Before Committing Code

#### Python Code
- [ ] `uv run ruff format .` - Format code
- [ ] `uv run ruff check . --fix` - Lint code
- [ ] `uvx pyright packages/` - Type check
- [ ] `uv run pytest -v` - Run tests
- [ ] Coverage ≥ 80% for production code

#### JavaScript/TypeScript Code
- [ ] `npm run format` - Format code (Prettier)
- [ ] `npm run lint` - Lint code (ESLint)
- [ ] `npm run typecheck` - Type check (tsc)
- [ ] `npm test` - Run tests (Jest/Vitest)
- [ ] Coverage ≥ 80% for production code

#### Cross-Language
- [ ] Run `./scripts/validation/validate-all.sh`
- [ ] All language-specific CI passes
- [ ] Integration tests pass
- [ ] Documentation updated

---

## 🚀 Adding a New Language

### Checklist for New Language Support

1. **Create Package Structure**
   ```
   packages/[lang]-dev-primitives/
   ├── src/ or lib/           # Production code
   ├── test/ or tests/        # Test suite
   ├── examples/              # Example code with README
   ├── README.md              # Package documentation
   └── [lang config files]    # package.json, Cargo.toml, etc.
   ```

2. **Create Instruction Files**
   - `.github/instructions/[lang]-source.instructions.md`
   - `.github/instructions/[lang]-tests.instructions.md`

3. **Add CI/CD**
   - `.github/workflows/[lang]-ci.yml`
   - Add to `.github/workflows/integration-tests.yml`

4. **Add Validation Scripts**
   - `scripts/validation/validate-[lang].sh`
   - Update `scripts/validation/validate-all.sh`

5. **Update Documentation**
   - `docs/languages/[lang]/GETTING_STARTED.md`
   - Update this file (MULTI_LANGUAGE_ARCHITECTURE.md)
   - Update AGENTS.md with new package references

6. **Implement Core Primitives**
   - WorkflowPrimitive (base class)
   - SequentialPrimitive
   - ParallelPrimitive
   - At least one recovery primitive (Retry or Fallback)

7. **Add Cross-Language Tests**
   - `tests/integration/cross-language/test_python_[lang]_interop.py`

---

## 🔍 Discovery by AI Agents

### How Agents Find the Right Code

**1. Path-Based Instructions**

Agents receive different instructions based on file path:

```yaml
# .github/instructions/python-source.instructions.md
applyTo: "packages/**/src/**/*.py"
description: "Python production code - 80%+ coverage required"

# .github/instructions/javascript-source.instructions.md
applyTo: "packages/**/src/**/*.{ts,js}"
description: "JavaScript/TypeScript production code - 80%+ coverage required"

# .github/instructions/example-code.instructions.md
applyTo: "**/examples/**/*.{py,ts,js}"
description: "Example code - educational, lower coverage acceptable"
```

**2. Code Markers**

Agents scan for these markers:
- `# ✨ EXAMPLE CODE` - Example file
- `# 🤖 INTERNAL TOOL` - Used by agents
- No marker = Production code (default)

**3. Directory Convention**

Agents understand:
- `src/` or `lib/` → Production code
- `examples/` → Example code
- `tests/` or `test/` → Test code
- `scripts/` → Automation scripts

**4. README.md Disclaimers**

Every `examples/` directory has a README.md starting with:
```markdown
⚠️ **THIS IS EXAMPLE CODE**
```

---

## 📊 Metrics & Monitoring

### Coverage Targets

| Package | Python Coverage | JS/TS Coverage | Status |
|---------|----------------|----------------|--------|
| tta-dev-primitives | 88% | N/A | ✅ Excellent |
| js-dev-primitives | N/A | TBD | 🚧 In Progress |
| python-pathway | 70%+ | N/A | ✅ Good |
| universal-agent-context | 70%+ | TBD | 🚧 In Progress |

### Quality Gates

**All Production Code Must Pass:**
- ✅ Language-specific linter (Ruff, ESLint, etc.)
- ✅ Language-specific type checker (Pyright, TypeScript)
- ✅ Test coverage ≥ 80%
- ✅ All tests passing
- ✅ No critical security vulnerabilities

**Example Code:**
- ✅ Language-specific linter
- ⚠️ Type checker (warnings acceptable)
- ⚠️ Test coverage encouraged but not enforced
- ✅ Code must run without errors

---

## 🎓 Agent Training Materials

### For AI Agents Working on TTA.dev

**Always check these in order:**

1. **Read AGENTS.md** - Main hub for all agent instructions
2. **Check package-specific AGENTS.md** - Package you're working on
3. **Read language-specific instructions** - `.github/instructions/[lang]-*.md`
4. **Review examples** - Understand patterns in `examples/`
5. **Run validation** - `./scripts/validation/validate-all.sh`

**Key Questions to Ask:**

- **Is this production code or example code?**
  - Location: `src/` or `examples/`?
  - Check for `# ✨ EXAMPLE CODE` marker

- **What language am I working in?**
  - Python: Use `uv`, Ruff, Pyright, pytest
  - JavaScript/TypeScript: Use `npm`, Prettier, ESLint, Jest

- **What's the test coverage requirement?**
  - Production: 80%+
  - Internal tools: 70%+
  - Examples: Encouraged

- **Are there cross-language dependencies?**
  - Check `tests/integration/cross-language/`
  - Verify APIs are consistent

---

## 🛠️ Tooling

### Validation Scripts

```bash
# Validate all languages
./scripts/validation/validate-all.sh

# Validate specific language
./scripts/validation/validate-python.sh
./scripts/validation/validate-javascript.sh

# Run all tests
./scripts/testing/run-all-tests.sh

# Run language-specific tests
./scripts/testing/run-python-tests.sh
./scripts/testing/run-js-tests.sh
```

### Pre-Commit Hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash
./scripts/validation/validate-all.sh || exit 1
```

### VS Code Tasks

See `.vscode/tasks.json` for:
- `✅ Quality Check (All)` - Run all quality checks
- `🧪 Run All Tests` - Run all language tests
- `🔍 Lint All Languages` - Lint Python + JavaScript
- `🔬 Type Check All` - Type check all languages

---

## 📚 References

- **Main Agent Hub:** [`AGENTS.md`](AGENTS.md)
- **Python Package:** [`packages/tta-dev-primitives/AGENTS.md`](packages/tta-dev-primitives/AGENTS.md)
- **JavaScript Package:** [`packages/js-dev-primitives/README.md`](packages/js-dev-primitives/README.md)
- **Example Code:** [`examples/README.md`](examples/README.md)
- **Instruction Files:** [`.github/instructions/`](.github/instructions/)

---

**Last Updated:** October 29, 2025
**Maintained by:** TTA.dev Team
**Version:** 1.0.0
