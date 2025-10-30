# Multi-Language Quick Reference

**TTA.dev Multi-Language Repository - Quick Reference Card**

---

## 🎯 Code Classification

| Type | Location | Marker | Coverage |
|------|----------|--------|----------|
| **Production** | `packages/*/src/` or `packages/*/lib/` | None | 80%+ |
| **Example** | `packages/*/examples/` or `examples/` | `# ✨ EXAMPLE CODE` | Optional |
| **Internal Tool** | `packages/python-pathway/`, `scripts/` | `# 🤖 INTERNAL TOOL` | 70%+ |

---

## 📝 Required Markers

### Example Code (Required)

**Python:**
```python
# ✨ EXAMPLE CODE
# This file demonstrates X pattern. For production use, see packages/X/src/
```

**JavaScript/TypeScript:**
```typescript
// ✨ EXAMPLE CODE
// This file demonstrates X pattern. For production use, see packages/X/src/
```

### Internal Tools (Recommended)

```python
# 🤖 INTERNAL TOOL - Used by agentic workflows
# This module provides X capability for AI agents
```

---

## 🚀 Quick Commands

### Python Validation

```bash
# All checks
./scripts/validation/validate-python.sh

# Individual checks
uv run ruff format .              # Format
uv run ruff check . --fix         # Lint
uvx pyright packages/             # Type check
uv run pytest -v                  # Test
```

### JavaScript/TypeScript Validation

```bash
# All checks
./scripts/validation/validate-javascript.sh

# Individual checks (in package directory)
npm run format                    # Format
npm run lint                      # Lint
npm run typecheck                 # Type check
npm test                          # Test
```

### All Languages

```bash
# Validate everything
./scripts/validation/validate-all.sh
```

---

## 📁 File Patterns & Instructions

| Pattern | Instruction File | Language |
|---------|-----------------|----------|
| `packages/**/src/**/*.py` | `package-source.instructions.instructions.md` | Python |
| `packages/**/src/**/*.{ts,js,jsx,tsx}` | `javascript-source.instructions.md` | JavaScript/TypeScript |
| `**/tests/**/*.py` | `tests.instructions.instructions.md` | Python |
| `**/test/**/*.{ts,js}` | `tests.instructions.instructions.md` | JavaScript/TypeScript |
| `**/examples/**/*` | `example-code.instructions.md` | All |
| `scripts/**/*.py` | `scripts.instructions.instructions.md` | Python |
| `**/*.md` | `documentation.instructions.instructions.md` | Markdown |

---

## ✅ Pre-Commit Checklist

### Python Code
- [ ] Add type hints (100% for public APIs)
- [ ] Format with Ruff
- [ ] Lint with Ruff
- [ ] Type check with Pyright
- [ ] Test with pytest (80%+ coverage)

### JavaScript/TypeScript Code
- [ ] Use TypeScript strict mode
- [ ] Add JSDoc for public APIs
- [ ] Format with Prettier
- [ ] Lint with ESLint
- [ ] Test with Jest/Vitest (80%+ coverage)

### Example Code
- [ ] Add `# ✨ EXAMPLE CODE` marker
- [ ] Create/update `examples/README.md`
- [ ] Verify code runs without errors
- [ ] Add inline comments

### All Code
- [ ] Run `./scripts/validation/validate-all.sh`

---

## 🔗 Key Documents

| Document | Purpose |
|----------|---------|
| [`MULTI_LANGUAGE_ARCHITECTURE.md`](MULTI_LANGUAGE_ARCHITECTURE.md) | Complete architecture guide |
| [`MULTI_LANGUAGE_IMPLEMENTATION_SUMMARY.md`](MULTI_LANGUAGE_IMPLEMENTATION_SUMMARY.md) | Implementation summary |
| [`AGENTS.md`](AGENTS.md) | Agent hub with all guidance |
| [`.github/copilot-instructions.md`](.github/copilot-instructions.md) | Copilot workspace instructions |
| [`examples/README.md`](examples/README.md) | Cross-language examples |

---

## 🎓 For AI Agents

### When Working on Code

1. **Check location:** `src/` (production) vs `examples/` (example)?
2. **Check language:** Python or JavaScript/TypeScript?
3. **Read instructions:** See `.github/instructions/[lang]-*.md`
4. **Add markers:** Example code needs `# ✨ EXAMPLE CODE`
5. **Run validation:** `./scripts/validation/validate-all.sh`

### Key Questions

- **Is this production code?** → Check location and coverage requirement
- **What language?** → Use appropriate tools (uv vs npm)
- **Coverage target?** → Production: 80%, Internal: 70%, Example: Optional
- **Cross-language?** → Check API consistency

---

## 📊 Coverage Targets

```
Production Code:  80%+ ████████░░
Internal Tools:   70%+ ███████░░░
Example Code:     ---  (Optional)
```

---

## 🌍 Cross-Language API Consistency

**Python:**
```python
workflow = step1 >> step2 >> step3              # Sequential
workflow = branch1 | branch2 | branch3          # Parallel
```

**JavaScript/TypeScript:**
```typescript
const workflow = step1.then(step2).then(step3)  # Sequential
const workflow = parallel(branch1, branch2)     # Parallel
```

---

**Last Updated:** October 29, 2025
**Version:** 1.0.0
**Quick Reference:** Always start with `AGENTS.md`!
