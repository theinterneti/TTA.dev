# TTA.dev Semantic Versioning Policy

**Applies to:** `ttadev` package (all modules)
**Effective:** TTA.dev M1

---

## Version Format

`MAJOR.MINOR.PATCH` — following [Semantic Versioning 2.0.0](https://semver.org/).

---

## Breaking Changes (require MAJOR bump)

A change is **breaking** if it causes existing correct code to:
- Fail to import
- Raise a new exception type from a previously-successful call
- Return a different type from `execute()`
- Require new required arguments
- Have different behavior for the same inputs

**Examples of breaking changes:**
- Removing a primitive class or renaming it
- Changing `execute(input, ctx)` to a different signature
- Removing an export from `ttadev.primitives.__init__`
- Changing a default argument value that callers depend on
- Raising a different exception type on error

---

## Non-Breaking Changes (MINOR or PATCH)

**MINOR** — new functionality, backwards compatible:
- Adding a new primitive class
- Adding a new optional constructor parameter with a default
- Adding a new method to an existing primitive
- Adding a new export to `ttadev.primitives`

**PATCH** — bug fixes, backwards compatible:
- Fixing incorrect behavior (where the old behavior was a bug)
- Performance improvements with no observable behavior change
- Documentation updates
- Adding or improving test coverage

---

## Primitives-Specific Rules

| Change | Classification |
|--------|----------------|
| Add new `LLMProvider` enum member | MINOR |
| Remove existing `LLMProvider` enum member | MAJOR |
| Change `RetryStrategy` default `max_retries` | MAJOR |
| Add optional field to `LLMRequest`/`LLMResponse` | MINOR |
| Remove field from `LLMRequest`/`LLMResponse` | MAJOR |
| Change circuit breaker state transition logic | MAJOR |
| Add optional parameter to `CachePrimitive.__init__` | MINOR |
| Change `cache_key_fn` signature | MAJOR |

---

## Deprecation Policy

Before removing or changing a public API:
1. Mark as deprecated with a `DeprecationWarning` for one MINOR version
2. Document the migration path in the release notes
3. Remove in the next MAJOR version

---

## Current Version

See `pyproject.toml` for the current package version.
