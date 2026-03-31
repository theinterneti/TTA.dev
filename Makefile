# Quality gate

.PHONY: lint type-check test watch watch-cov check

lint:
	uv run ruff check . --fix && uv run ruff format .

type-check:
	uvx pyright

# Full test run with coverage report.
# pytest.ini wins over pyproject.toml so we pass --cov flags explicitly.
test:
	uv run pytest --cov=ttadev --cov-report=term-missing --cov-report=html

# Continuous testing — fast, no coverage overhead
# Scoped to ttadev/ and tests/ so edits in scripts/, .cline/, .archive/ don't trigger reruns.
watch:
	watchexec -w ttadev -w tests -e py,toml --clear -- uv run pytest -p no:cov -x

# Continuous testing — with coverage (slower, use before committing).
# Passes --cov explicitly because pytest.ini (addopts=-v --tb=short) takes precedence
# over pyproject.toml [tool.pytest.ini_options] and does not include coverage flags.
watch-cov:
	watchexec -w ttadev -w tests -e py,toml --clear -- uv run pytest -x --cov=ttadev --cov-report=term

# Full quality gate (mirrors pre-commit / CI)
check: lint type-check test
