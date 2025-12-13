# Claude-Specific Workflows

## When Working with tta-dev-primitives

1. **Composition over Implementation**
   - Before writing manual async code, check if primitives solve the problem
   - Suggest primitive-based refactoring for manual patterns
   - Use `MockPrimitive` for testing workflows

2. **Type Safety First**
   - Generate full type annotations using Python 3.11+ style (`T | None`)
   - Use `WorkflowPrimitive[InputType, OutputType]` for new primitives
   - Leverage Pydantic v2 models for data structures

3. **Documentation Standards**
   - Include docstrings with examples for all public APIs
   - Show before/after code when suggesting refactoring
   - Reference existing examples in `packages/tta-dev-primitives/examples/`

## When Generating Code

1. **Complete Solutions**
   - Generate runnable code with all imports
   - Include test files using `@pytest.mark.asyncio`
   - Add docstrings with usage examples

2. **Quality Checks**
   - Suggest running quality checks: `ruff format`, `ruff check`, `pyright`
   - Remind about test coverage: `uv run pytest --cov=packages`
   - Note any deviations from coding standards

3. **Package Management**
   - Always use `uv` commands, never `pip` directly
   - Show correct commands: `uv run pytest -v`, `uv sync --all-extras`
   - Reference the primitives package when available

## Multi-File Refactoring

When refactoring across multiple files:

1. Start with dependency analysis (which files depend on what)
2. Update in topological order (dependencies first, dependents second)
3. Run tests after each major change
4. Provide a summary of changes per file

## Architecture Analysis

When analyzing system architecture:

1. Use diagrams or structured markdown for component relationships
2. Identify coupling points and suggest improvements
3. Consider testability, maintainability, and performance
4. Reference existing patterns in the codebase

## Performance Optimization

When optimizing performance:

1. Profile before optimizing (suggest profiling commands)
2. Use `ParallelPrimitive` for independent operations
3. Add `CachePrimitive` to avoid redundant work
4. Measure impact with benchmarks


---
**Logseq:** [[TTA.dev/.universal-instructions/Claude-specific/Workflows]]
