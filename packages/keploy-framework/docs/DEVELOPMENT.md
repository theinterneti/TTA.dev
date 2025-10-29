# Keploy Framework - Development

## Development Setup

```bash
cd packages/keploy-framework

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v --cov

# Type checking
pyright src/

# Linting
ruff check src/ tests/ --fix
ruff format src/ tests/
```

## Architecture

### Core Components

1. **Config (`config.py`)** - YAML configuration management
2. **Test Runner (`test_runner.py`)** - Intelligent test execution with Docker
3. **Recorder (`recorder.py`)** - Context managers for recording sessions
4. **Validation (`validation.py`)** - Test result validation and assertions
5. **CLI (`cli.py`)** - Command-line interface with Typer

### Templates

- `keploy.yml.template` - Default configuration
- `pre-commit-hook.sh` - Git hook for test validation
- `github-workflow.yml` - CI/CD workflow
- `setup-keploy.sh` - One-command setup script

## Testing

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires Docker)
pytest tests/integration/ -v -m docker

# Coverage report
pytest --cov=src/keploy_framework --cov-report=html
open htmlcov/index.html
```

## Publishing

```bash
# Build distribution
python -m build

# Publish to PyPI
python -m twine upload dist/*
```

## Reference Implementation

See the [TTA repository](https://github.com/theinterneti/TTA) for a complete working example:

- Full Keploy integration with 9 automated tests
- Interactive menu system
- CI/CD with GitHub Actions
- 88.9% pass rate in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit pull request

All code must pass:
- ✅ 100% test coverage
- ✅ Type checking (Pyright)
- ✅ Linting (Ruff)
- ✅ Pre-commit hooks
