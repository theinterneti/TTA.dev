# Copilot CLI Quality Gate Hooks

Automated quality gates that run after code generation to ensure TTA.dev standards.

## Hooks

### `post-generation.sh`

Runs three quality gates:

1. **Ruff Linting** - Code style and formatting
2. **Pyright Type Checking** - Type safety (allows ≤2 known OpenTelemetry errors)
3. **Pytest** - Fast test suite (excludes integration tests)

### Usage

#### Manual Execution
```bash
.github/copilot-hooks/post-generation.sh
```

#### Automatic Execution (Copilot CLI Agent)
The agent automatically runs this after code modifications per `.github/copilot-instructions.md`.

## Quality Gate Thresholds

| Gate | Pass Criteria |
|------|---------------|
| Ruff | All checks pass |
| Pyright | ≤2 real errors (OpenTelemetry SDK known issues) |
| Pytest | All non-integration tests pass |

## Self-Correction Protocol

If quality gates fail, the agent will:

1. **Capture** - Read full error output
2. **Analyze** - Identify root cause
3. **Fix** - Apply minimal surgical fixes
4. **Verify** - Re-run quality gates
5. **Iterate** - Repeat until all gates pass

## Exit Codes

- `0` - All gates passed
- `1` - One or more gates failed

## CI Integration

These hooks complement (not replace) CI/CD workflows in `.github/workflows/`.
