# Contributing to Universal Agent Context System

Thank you for your interest in contributing! This document provides guidelines for contributing to the Universal Agent Context System.

---

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

---

## How to Contribute

### 1. Report Issues

Found a bug or have a feature request?

1. Check [existing issues](https://github.com/theinterneti/TTA.dev/issues)
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce (for bugs)
   - Expected vs. actual behavior
   - Your environment (OS, AI agent, version)

### 2. Suggest Enhancements

Have an idea for improvement?

1. Open a [discussion](https://github.com/theinterneti/TTA.dev/discussions)
2. Describe your enhancement:
   - Use case and motivation
   - Proposed solution
   - Alternatives considered
   - Impact on existing users

### 3. Submit Pull Requests

Ready to contribute code?

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

---

## Quality Standards

All contributions must meet these standards:

### Code Quality

- ✅ **Test Coverage**: ≥80% for new code, 100% for critical paths
- ✅ **Documentation**: Comprehensive docs for all new features
- ✅ **Battle-Tested**: Real-world usage validation
- ✅ **Zero Critical Bugs**: All critical issues resolved

### File Standards

- ✅ **File Size**: ≤800 lines per file (≤600 for production)
- ✅ **Complexity**: Cyclomatic complexity ≤8
- ✅ **YAML Frontmatter**: Valid YAML in all instruction/chat mode files
- ✅ **Cross-References**: All links and references valid

### Documentation Standards

- ✅ **README**: Clear overview and quick start
- ✅ **Examples**: Working code examples
- ✅ **API Docs**: Complete API documentation
- ✅ **Changelog**: Updated CHANGELOG.md

---

## Development Workflow

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/theinterneti/TTA.dev
cd TTA.dev

# Install dependencies (if applicable)
# For Python components:
pip install -r requirements.txt

# For validation:
python packages/universal-agent-context/scripts/validate-export-package.py
```

### Making Changes

#### For Cross-Platform Primitives (`.github/`)

1. **Add/Edit Instruction Files**:
   ```bash
   vim packages/universal-agent-context/.github/instructions/my-feature.instructions.md
   ```

2. **Include YAML Frontmatter**:
   ```yaml
   ---
   applyTo: "**/*.py"
   tags: ["python", "quality"]
   description: "Python quality standards"
   priority: 5
   version: "1.0.0"
   ---
   ```

3. **Test Selective Loading**:
   - Verify `applyTo` patterns match intended files
   - Test with multiple AI agents (Claude, Gemini, Copilot)

#### For Augment CLI Primitives (`.augment/`)

1. **Add/Edit Instruction Files**:
   ```bash
   vim packages/universal-agent-context/.augment/instructions/my-feature.instructions.md
   ```

2. **Test with Augment CLI**:
   - Verify instructions load correctly
   - Test context management integration
   - Validate memory system integration

### Testing

```bash
# Run validation
python packages/universal-agent-context/scripts/validate-export-package.py

# Run tests (if applicable)
pytest packages/universal-agent-context/tests/

# Test with AI agents
# - Claude: Verify instructions load
# - Gemini: Verify context works
# - Copilot: Verify copilot-instructions.md works
# - Augment: Verify both .github/ and .augment/ work
```

### Commit Guidelines

Use clear, descriptive commit messages:

```bash
# Good commit messages
git commit -m "feat: add therapeutic safety instruction file"
git commit -m "fix: correct YAML frontmatter in backend-dev chatmode"
git commit -m "docs: update integration guide for Gemini"
git commit -m "test: add cross-agent compatibility tests"

# Bad commit messages
git commit -m "update files"
git commit -m "fix bug"
git commit -m "changes"
```

**Commit Message Format**:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

---

## Pull Request Process

### Before Submitting

1. ✅ All tests pass
2. ✅ Documentation updated
3. ✅ CHANGELOG.md updated
4. ✅ Code follows style guidelines
5. ✅ No merge conflicts

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Tested with Claude
- [ ] Tested with Gemini
- [ ] Tested with Copilot
- [ ] Tested with Augment
- [ ] Validation script passes

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] CHANGELOG.md updated
- [ ] No breaking changes (or documented)

## Related Issues
Closes #123
```

### Review Process

1. Maintainer reviews PR
2. Feedback provided (if needed)
3. Changes requested (if needed)
4. Approval given
5. PR merged

---

## Style Guidelines

### Markdown Files

- Use ATX-style headers (`#`, `##`, `###`)
- Include blank lines around headers
- Use fenced code blocks with language tags
- Keep lines ≤120 characters (soft limit)

### YAML Frontmatter

```yaml
---
# Required fields
applyTo: "**/*.py"
tags: ["python", "quality"]
description: "Brief description"

# Optional fields
priority: 5
version: "1.0.0"
---
```

### Python Code (for scripts)

- Follow PEP 8
- Use type hints
- Include docstrings
- Maximum line length: 100 characters

---

## Documentation Guidelines

### Instruction Files

```markdown
---
applyTo: "**/*.py"
tags: ["python"]
description: "Python development guidelines"
---

# Python Development Guidelines

## Overview
Brief overview of the guidelines

## Guidelines

### Guideline 1
Description and examples

### Guideline 2
Description and examples

## Examples

### Example 1
Working code example
```

### Chat Mode Files

```markdown
---
mode: "backend-developer"
description: "Backend development role"
cognitive_focus: "Backend architecture and implementation"
security_level: "MEDIUM"
allowed_tools: ["editFiles", "runCommands"]
denied_tools: ["deleteFiles"]
---

# Backend Developer Chat Mode

## Role Description
Description of the role

## Responsibilities
- Responsibility 1
- Responsibility 2

## Tool Access
- **Allowed**: editFiles, runCommands
- **Denied**: deleteFiles
```

---

## Community

### Get Help

- **Documentation**: [docs/](docs/)
- **Discussions**: [GitHub Discussions](https://github.com/theinterneti/TTA.dev/discussions)
- **Issues**: [GitHub Issues](https://github.com/theinterneti/TTA.dev/issues)

### Stay Updated

- Watch the repository for updates
- Join discussions
- Follow the project roadmap

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## Questions?

If you have questions about contributing, please:

1. Check the [documentation](docs/)
2. Search [existing issues](https://github.com/theinterneti/TTA.dev/issues)
3. Ask in [discussions](https://github.com/theinterneti/TTA.dev/discussions)
4. Open a new issue

---

**Thank you for contributing to the Universal Agent Context System!**

