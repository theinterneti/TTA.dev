---
applyTo: '.github/workflows/*.yml,.github/workflows/*.yaml'
description: 'TTA.dev CI/CD conventions for GitHub Actions workflows'
---

# TTA.dev CI/CD Conventions

## Stack

All workflows use `uv` (never `pip`), `ruff` for linting/formatting,
`pyright` for type checking, and `pytest` for testing.

## Workflow Rules

- **Action versions**: Pin to full SHA or major tag (`@v4`), never `@main`/`@latest`
- **Permissions**: Set `permissions: contents: read` at workflow level; override per-job
- **Secrets**: Use `secrets.*` context only — never hardcode or log sensitive values
- **Caching**: Cache `~/.cache/uv` with `hashFiles('**/uv.lock')` as key
- **Concurrency**: Use `concurrency` for `main`/`develop` to prevent parallel deploys

## Quality Gate Steps

```yaml
steps:
  - run: uv sync --all-extras
  - run: uv run ruff format --check .
  - run: uv run ruff check .
  - run: uvx pyright ttadev/
  - run: uv run pytest --timeout=60 -x -q
```

## Testing Matrix

Use `strategy.matrix` for Python version testing. Set `fail-fast: false`
for comprehensive coverage reporting.

## Artifact Management

- Upload test/coverage reports with `actions/upload-artifact@v4`
- Set `retention-days` to manage storage costs
- Use artifacts to pass builds between jobs (not rebuild)

## Security

- Enable Dependabot for action version updates
- Use OIDC for cloud auth when possible (no long-lived credentials)
- Run `dependency-review-action` on PRs

## Reference

For GitHub Actions fundamentals, see [GitHub Actions docs](https://docs.github.com/en/actions).
For TTA.dev build commands, see the `build-test-verify` skill.
