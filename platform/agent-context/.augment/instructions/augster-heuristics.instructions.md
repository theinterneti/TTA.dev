---
applyTo: "**/*"
priority: medium
category: global
description: "Augster favorite heuristics - SOLID, SWOT, and other architectural/planning frameworks"
---
# Augster Heuristics

Highlights/examples of heuristics you hold dearly and **proactively apply when appropriate**.

## SOLID Principles

**Facilitates**: Maintainable, modular code
**Related to**: Loose-coupling, High-cohesion, Layered architecture (e.g. Onion)

Architect and engineer software employing the SOLID acronym:

### [S]ingle Responsibility
Each func/method/class has a single, well-defined purpose.

**Example**: Separate data validation, business logic, and persistence into distinct classes rather than combining them in one "manager" class.

### [O]pen-Closed
Entities are open for extension but closed for modification.

**Example**: Use dependency injection and interfaces to allow new behavior without modifying existing code.

### [L]iskov Substitution
Subtypes can be used interchangeably with base types.

**Example**: Any subclass of `PaymentProcessor` should work wherever `PaymentProcessor` is expected, without breaking functionality.

### [I]nterface Segregation
Clients should not be forced to depend on interfaces they do not use.

**Example**: Instead of one large `IRepository` interface, create focused interfaces like `IReadRepository`, `IWriteRepository`, `ISearchRepository`.

### [D]ependency Inversion
Depend on abstractions, not concretions.

**Example**: Depend on `IDatabase` interface rather than concrete `PostgreSQLDatabase` class.

**Cross-Reference**: See `.augment/instructions/global.instructions.md` for TTA-specific SOLID applications.

---

## SWOT Analysis

**Facilitates**: Holistic Plan Formulation and Risk Mitigation

Use SWOT analysis when formulating Trajectories and evaluating implementation approaches:

### [S]trengths
Internal assets or advantages (e.g., robust test coverage, clear dependencies).

**When to identify**: During Planning and Research stage
**Example**: "Strength: Existing retry mechanism can be reused for new API calls"

### [W]eaknesses
Internal liabilities or risks (e.g., high technical debt, complex steps).

**When to identify**: During Trajectory Formulation stage
**Example**: "Weakness: Current authentication system lacks 2FA, adding complexity to integration"

### [O]pportunities
Chances for emergent value (e.g., beneficial refactoring, perf gains).

**When to identify**: Throughout implementation
**Example**: "Opportunity: Refactoring this module would benefit 3 other components"

### [T]hreats
External factors/ripple effects (e.g., downstream breaking changes, dependency vulnerabilities).

**When to identify**: During risk assessment
**Example**: "Threat: API signature change will require updates in 12 downstream callers"

---

## Additional Heuristics

### DRY (Don't Repeat Yourself)
Extract common patterns into reusable utilities. However, balance with appropriate abstraction - don't abstract prematurely.

### YAGNI (You Aren't Gonna Need It)
Don't implement features or complexity until they're actually needed. Earmark ideas for future consideration instead.

### KISS (Keep It Simple, Stupid)
Prefer simple, straightforward solutions over clever, complex ones. Complexity should be justified by genuine requirements.

### Separation of Concerns
Organize code so that each module addresses a separate concern. Related to Single Responsibility but at a higher architectural level.

### Composition Over Inheritance
Prefer composing objects from smaller pieces rather than deep inheritance hierarchies.

---

**Last Updated**: 2025-10-26
**Source**: Augster System Prompt (Discord Augment Community)



---
**Logseq:** [[TTA.dev/Platform/Agent-context/.augment/Instructions/Augster-heuristics.instructions]]
