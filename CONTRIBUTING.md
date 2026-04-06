# Contributing to TTA.dev

First off, thank you for considering contributing to TTA.dev. It's people like you that make TTA.dev such a great tool.

## Where do I start?

If you're looking for a place to start, you can check out the [open issues](https://github.com/theinterneti/TTA.dev/issues).

## Important Resources

- **[Agent Instructions](AGENTS.md)** - Comprehensive guidance for AI agents
- **[GitHub Copilot Instructions](.github/copilot-instructions.md)** - Best practices and requirements for Copilot users
- **[Getting Started Guide](GETTING_STARTED.md)** - Development environment setup
- **[Coding Standards](docs/guides/development/CodingStandards.md)** - Code quality standards

## How to Contribute

1.  **Fork the repository** and create your branch from `main`.
2.  **Set up your development environment** by following the instructions in [`GETTING_STARTED.md`](GETTING_STARTED.md).
3.  **Review the standards**: Read [`.github/copilot-instructions.md`](.github/copilot-instructions.md) for comprehensive coding guidelines including:
    - Package manager (use `uv`, never `pip` or `poetry`)
    - Python 3.12+ type hints (use `str | None`, not `Optional[str]`)
    - Testing requirements (pytest with AAA pattern, 100% coverage)
    - Code style (Ruff with 100 char line length)
    - Security practices
    - Documentation standards
    - TTA.dev primitives patterns
4.  **Make your changes**. Please ensure your code adheres to the standards and patterns outlined in the `.clinerules` file, `.github/copilot-instructions.md`, and the existing documentation.
5.  **Add tests** for your changes. We require 100% test coverage for all new code.
6.  **Update the documentation** if you've added or changed any features.
7.  **Ensure all quality checks pass** by running:
    ```bash
    uv run ruff format .
    uv run ruff check . --fix
    uvx pyright platform/ apps/
    uv run pytest -v
    ```
8.  **Submit a pull request**.

## Code Quality Standards

Before submitting your PR, ensure:

- [ ] Code formatted with `uv run ruff format .`
- [ ] Linter passes with `uv run ruff check . --fix`
- [ ] Type checks pass with `uvx pyright platform/ apps/`
- [ ] Tests pass with `uv run pytest -v`
- [ ] Test coverage >80% for new code (aim for 100%)
- [ ] Documentation updated (docstrings, README)
- [ ] No secrets committed
- [ ] Using `uv` (not pip/poetry)
- [ ] Using primitives for workflows
- [ ] Python 3.12+ type hints (no `Optional`, `Dict`)

See [`.github/copilot-instructions.md`](.github/copilot-instructions.md) for detailed requirements.

## Code of Conduct

This project and everyone participating in it is governed by the [TTA.dev Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior.

## File Length Guideline

Files in `ttadev/` should not exceed **500 lines** (excluding blank lines and comments).

**Why:** Large files are hard to navigate, review, and test. Keeping files focused makes the codebase more maintainable.

**When to split:** When a file grows beyond 500 lines, extract focused modules:
- Group related classes/functions into their own files
- Create a package directory with `__init__.py` re-exporting the public API
- Keep the public API surface unchanged (no breaking imports)

**Known violations:** 30 files currently exceed this limit. They are tracked individually as refactoring issues. New code should not introduce new violations.

A warn-only CI check (`scripts/ci/check_file_length.py`) runs automatically via the pre-commit hook and reports violations without blocking commits.

## Any questions?

Feel free to open an issue or start a discussion on the [GitHub repository](https://github.com/theinterneti/TTA.dev).
