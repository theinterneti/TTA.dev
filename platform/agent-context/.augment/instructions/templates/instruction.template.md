---
applyTo: ["src/**/*.py", "tests/**/*.py"]
priority: high | medium | low
category: global | component-specific | workflow-specific
---
# [Instruction Title]

Brief description of what this instruction file covers and when it applies.

## Architecture Principles

Core architectural principles that must be followed:

- **Principle 1**: Description and rationale
- **Principle 2**: Description and rationale
- **Principle 3**: Description and rationale

## Testing Requirements

Testing standards and requirements:

- **Coverage**: Minimum test coverage percentage
- **Test Types**: Required test types (unit, integration, E2E)
- **Markers**: pytest markers to use
- **Fixtures**: Common fixtures and their usage

## Common Patterns

Recommended patterns and practices:

### Pattern 1: [Pattern Name]

**When to use**: [Scenario]

**Example**:
```python
# Code example demonstrating the pattern
```

**Benefits**: [Why this pattern is recommended]

### Pattern 2: [Pattern Name]

**When to use**: [Scenario]

**Example**:
```python
# Code example demonstrating the pattern
```

**Benefits**: [Why this pattern is recommended]

## Error Handling

Error handling requirements and patterns:

- **Required Exceptions**: List of exceptions that must be handled
- **Retry Strategy**: When and how to retry operations
- **Circuit Breaker**: When to use circuit breaker pattern
- **Error Messages**: How to format error messages for agents

## Code Style

Code style guidelines specific to this scope:

- **Naming Conventions**: Function, class, variable naming
- **Documentation**: Docstring requirements
- **Type Hints**: Type annotation requirements
- **Imports**: Import organization and conventions

## Integration Points

How this component/feature integrates with other parts of the system:

- **Database**: Redis, Neo4j, PostgreSQL usage
- **APIs**: External API integrations
- **Events**: Pub/Sub patterns
- **Workflows**: LangGraph workflow integration

## Quality Gates

Quality criteria that must be met:

- **Linting**: ruff check must pass
- **Type Checking**: pyright must pass
- **Security**: detect-secrets must pass
- **Performance**: Response time requirements

## Examples

### Example 1: [Scenario]

**Context**: [When this scenario occurs]

**Implementation**:
```python
# Complete code example
```

**Explanation**: [Why this is the correct approach]

### Example 2: [Scenario]

**Context**: [When this scenario occurs]

**Implementation**:
```python
# Complete code example
```

**Explanation**: [Why this is the correct approach]

## Anti-Patterns

Common mistakes to avoid:

### Anti-Pattern 1: [Name]

**Problem**: [What's wrong with this approach]

**Example**:
```python
# Bad code example
```

**Solution**: [Correct approach]

```python
# Good code example
```

### Anti-Pattern 2: [Name]

**Problem**: [What's wrong with this approach]

**Example**:
```python
# Bad code example
```

**Solution**: [Correct approach]

```python
# Good code example
```

## References

- [Link to related documentation]
- [Link to architecture diagrams]
- [Link to example implementations]

---

**Last Updated**: YYYY-MM-DD
**Maintainer**: [GitHub username]
