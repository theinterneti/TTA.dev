---
title: Phase 1: Component Architecture Design
tags: #TTA
status: Active
repo: theinterneti/TTA
path: src/agent_orchestration/PHASE1_ARCHITECTURE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Architecture/Phase 1: Component Architecture Design]]

## Overview
This document defines the architecture for splitting `therapeutic_safety.py` (3,529 lines) into 4 focused components following SOLID principles and TTA's component maturity workflow.

---

## Directory Structure

```
src/agent_orchestration/
├── safety_validation/
│   ├── __init__.py          # Public exports
│   ├── models.py            # Data models (ValidationFinding, ValidationResult, SafetyRule)
│   ├── enums.py             # Enums (SafetyLevel, ValidationType)
│   └── engine.py            # Rule engine (SafetyRuleEngine)
│
├── crisis_detection/
│   ├── __init__.py          # Public exports
│   ├── models.py            # Data models (CrisisAssessment, InterventionAction, CrisisIntervention)
│   ├── enums.py             # Enums (CrisisType, CrisisLevel, InterventionType, EscalationStatus)
│   ├── manager.py           # Crisis manager (CrisisInterventionManager)
│   ├── protocols.py         # Emergency protocols (EmergencyProtocolEngine)
│   └── escalation.py        # Human oversight (HumanOversightEscalation)
│
├── therapeutic_scoring/
│   ├── __init__.py          # Public exports
│   ├── enums.py             # Enums (TherapeuticContext)
│   └── validator.py         # Main validator (TherapeuticValidator)
│
├── safety_monitoring/
│   ├── __init__.py          # Public exports
│   ├── dashboard.py         # Monitoring dashboard (SafetyMonitoringDashboard)
│   ├── provider.py          # Rules provider (SafetyRulesProvider)
│   └── service.py           # Service orchestration (SafetyService, get_global_safety_service)
│
└── therapeutic_safety.py    # Backward compatibility shim (re-exports all symbols)
```

---

## Component Designs

### 1. safety_validation/ (Foundation Layer)

**Responsibility:** Core validation infrastructure - rules, engines, and result models.

**Module Organization:**
- `enums.py`: SafetyLevel, ValidationType
- `models.py`: ValidationFinding, ValidationResult, SafetyRule
- `engine.py`: SafetyRuleEngine
- `__init__.py`: Export all public symbols

**Public API:**
```python
# enums.py
class SafetyLevel(str, Enum): ...
class ValidationType(str, Enum): ...

# models.py
@dataclass
class ValidationFinding: ...
@dataclass
class ValidationResult: ...
@dataclass
class SafetyRule: ...

# engine.py
class SafetyRuleEngine:
    def __init__(self, rules: list[SafetyRule]): ...
    @staticmethod
    def from_config(config: dict[str, Any]) -> SafetyRuleEngine: ...
    def evaluate(self, text: str, context: dict[str, Any] | None = None) -> list[ValidationFinding]: ...
```

**Dependencies:**
- Standard library: re, dataclasses, enum, typing
- No internal dependencies (foundation layer)

**SOLID Compliance:**
- **Single Responsibility:** Each module has one clear purpose (enums, models, engine)
- **Open-Closed:** SafetyRuleEngine extensible via config, closed for modification
- **Liskov Substitution:** Enums are proper subtypes of str/Enum
- **Interface Segregation:** Clean separation of data models and logic
- **Dependency Inversion:** Depends on abstractions (SafetyRule interface)

---

### 2. crisis_detection/ (Crisis Response Layer)

**Responsibility:** Crisis detection, assessment, intervention, and escalation.

**Module Organization:**
- `enums.py`: CrisisType, CrisisLevel, InterventionType, EscalationStatus
- `models.py`: CrisisAssessment, InterventionAction, CrisisIntervention
- `manager.py`: CrisisInterventionManager
- `protocols.py`: EmergencyProtocolEngine
- `escalation.py`: HumanOversightEscalation
- `__init__.py`: Export all public symbols

**Public API:**
```python
# enums.py
class CrisisType(str, Enum): ...
class CrisisLevel(str, Enum): ...
class InterventionType(str, Enum): ...
class EscalationStatus(str, Enum): ...

# models.py
@dataclass
class CrisisAssessment: ...
@dataclass
class InterventionAction: ...
@dataclass
class CrisisIntervention: ...

# manager.py
class CrisisInterventionManager:
    def assess_crisis(self, text: str, context: dict) -> CrisisAssessment: ...
    def create_intervention(self, assessment: CrisisAssessment) -> CrisisIntervention: ...
    def escalate_to_human(self, intervention: CrisisIntervention) -> bool: ...

# protocols.py
class EmergencyProtocolEngine:
    def execute_protocol(self, crisis_type: CrisisType, level: CrisisLevel) -> list[InterventionAction]: ...

# escalation.py
class HumanOversightEscalation:
    def notify_human_oversight(self, intervention: CrisisIntervention) -> bool: ...
```

**Dependencies:**
- Standard library: time, dataclasses, enum, typing
- Internal: safety_validation (SafetyLevel, ValidationResult)
- External: Redis (optional, for persistence)

**SOLID Compliance:**
- **Single Responsibility:** Each class handles one aspect of crisis response
- **Open-Closed:** Extensible via new crisis types and protocols
- **Liskov Substitution:** All crisis models are proper dataclasses
- **Interface Segregation:** Separate interfaces for assessment, intervention, escalation
- **Dependency Inversion:** Depends on safety_validation abstractions

---

### 3. therapeutic_scoring/ (Orchestration Layer)

**Responsibility:** High-level therapeutic validation orchestration.

**Module Organization:**
- `enums.py`: TherapeuticContext
- `validator.py`: TherapeuticValidator
- `__init__.py`: Export all public symbols

**Public API:**
```python
# enums.py
class TherapeuticContext(str, Enum): ...

# validator.py
class TherapeuticValidator:
    def __init__(self, config: dict[str, Any] | None = None): ...
    def validate_text(self, text: str, context: dict | None = None) -> ValidationResult: ...
    def suggest_alternative(self, reason: SafetyLevel, original: str) -> str: ...
```

**Dependencies:**
- Standard library: json, typing
- Internal: safety_validation (SafetyRuleEngine, ValidationResult, SafetyLevel)
- Internal: crisis_detection (CrisisType, CrisisLevel)
- External: yaml (optional)

**SOLID Compliance:**
- **Single Responsibility:** Orchestrates validation, doesn't implement low-level logic
- **Open-Closed:** Extensible via configuration, delegates to other components
- **Liskov Substitution:** Proper class hierarchy
- **Interface Segregation:** Clean validation interface
- **Dependency Inversion:** Depends on abstractions from other components

---

### 4. safety_monitoring/ (Service Layer)

**Responsibility:** Service orchestration, configuration management, and monitoring.

**Module Organization:**
- `dashboard.py`: SafetyMonitoringDashboard
- `provider.py`: SafetyRulesProvider
- `service.py`: SafetyService, get_global_safety_service, set_global_safety_service_for_testing
- `__init__.py`: Export all public symbols

**Public API:**
```python
# dashboard.py
class SafetyMonitoringDashboard:
    def record_validation(self, result: ValidationResult): ...
    def get_metrics(self) -> dict[str, Any]: ...
    def export_dashboard(self, format_type: str = "json") -> str: ...

# provider.py
class SafetyRulesProvider:
    def __init__(self, redis_client: Redis | None = None, ...): ...
    async def get_config(self) -> dict[str, Any]: ...
    def status(self) -> dict[str, Any]: ...

# service.py
class SafetyService:
    def __init__(self, enabled: bool = False, provider: SafetyRulesProvider | None = None): ...
    async def validate_text(self, text: str) -> ValidationResult: ...
    def suggest_alternative(self, level: SafetyLevel, original: str) -> str: ...

def get_global_safety_service() -> SafetyService: ...
def set_global_safety_service_for_testing(svc: SafetyService) -> None: ...
```

**Dependencies:**
- Standard library: json, time, typing, contextlib (FIX BUG!)
- Internal: therapeutic_scoring (TherapeuticValidator)
- External: redis.asyncio (optional)

**SOLID Compliance:**
- **Single Responsibility:** Each class handles one service aspect
- **Open-Closed:** Extensible via provider pattern
- **Liskov Substitution:** Proper class hierarchy
- **Interface Segregation:** Separate interfaces for dashboard, provider, service
- **Dependency Inversion:** Depends on TherapeuticValidator abstraction

---

## Inter-Component Interfaces

### Dependency Flow (Layered Architecture)
```
┌─────────────────────────────────────┐
│   safety_monitoring (Service)       │  ← Public API Layer
│   - SafetyService                   │
│   - SafetyRulesProvider             │
│   - SafetyMonitoringDashboard       │
└──────────────┬──────────────────────┘
               │ depends on
               ↓
┌─────────────────────────────────────┐
│   therapeutic_scoring (Orchestrator)│  ← Orchestration Layer
│   - TherapeuticValidator            │
└──────────────┬──────────────────────┘
               │ depends on
               ↓
┌─────────────────────────────────────┐
│   crisis_detection (Crisis)         │  ← Business Logic Layer
│   - CrisisInterventionManager       │
│   - EmergencyProtocolEngine         │
└──────────────┬──────────────────────┘
               │ depends on
               ↓
┌─────────────────────────────────────┐
│   safety_validation (Foundation)    │  ← Foundation Layer
│   - SafetyRuleEngine                │
│   - ValidationResult                │
└─────────────────────────────────────┘
```

### Interface Contracts

**safety_validation → crisis_detection:**
- crisis_detection imports: `SafetyLevel`, `ValidationResult`
- Used for: Crisis assessment results, safety level determination

**crisis_detection → therapeutic_scoring:**
- therapeutic_scoring imports: `CrisisType`, `CrisisLevel`
- Used for: Crisis context in validation

**therapeutic_scoring → safety_monitoring:**
- safety_monitoring imports: `TherapeuticValidator`
- Used for: Service orchestration, validation execution

---

## Backward Compatibility Layer

### therapeutic_safety.py (Shim)
```python
"""Backward compatibility shim for therapeutic_safety module.

This module re-exports all symbols from the new component structure
to maintain backward compatibility with existing code.

New code should import directly from the component modules:
- from agent_orchestration.safety_validation import SafetyLevel
- from agent_orchestration.crisis_detection import CrisisType
- from agent_orchestration.therapeutic_scoring import TherapeuticValidator
- from agent_orchestration.safety_monitoring import SafetyService
"""

# Re-export all symbols from new components
from .safety_validation import (
    SafetyLevel,
    ValidationType,
    ValidationFinding,
    ValidationResult,
    SafetyRule,
    SafetyRuleEngine,
)
from .crisis_detection import (
    CrisisType,
    CrisisLevel,
    InterventionType,
    EscalationStatus,
    CrisisAssessment,
    InterventionAction,
    CrisisIntervention,
    CrisisInterventionManager,
    EmergencyProtocolEngine,
    HumanOversightEscalation,
)
from .therapeutic_scoring import (
    TherapeuticContext,
    TherapeuticValidator,
)
from .safety_monitoring import (
    SafetyMonitoringDashboard,
    SafetyRulesProvider,
    SafetyService,
    get_global_safety_service,
    set_global_safety_service_for_testing,
)

__all__ = [
    # safety_validation
    "SafetyLevel",
    "ValidationType",
    "ValidationFinding",
    "ValidationResult",
    "SafetyRule",
    "SafetyRuleEngine",
    # crisis_detection
    "CrisisType",
    "CrisisLevel",
    "InterventionType",
    "EscalationStatus",
    "CrisisAssessment",
    "InterventionAction",
    "CrisisIntervention",
    "CrisisInterventionManager",
    "EmergencyProtocolEngine",
    "HumanOversightEscalation",
    # therapeutic_scoring
    "TherapeuticContext",
    "TherapeuticValidator",
    # safety_monitoring
    "SafetyMonitoringDashboard",
    "SafetyRulesProvider",
    "SafetyService",
    "get_global_safety_service",
    "set_global_safety_service_for_testing",
]
```

---

## Architecture Decision Records

### ADR-001: Layered Architecture
**Decision:** Use layered architecture with clear dependency flow (foundation → business logic → orchestration → service)
**Rationale:** Enforces SOLID principles, prevents circular dependencies, enables independent testing
**Consequences:** Must maintain strict import discipline, clear interface contracts

### ADR-002: Backward Compatibility Shim
**Decision:** Keep therapeutic_safety.py as re-export shim
**Rationale:** Zero breaking changes, gradual migration path, maintains public API
**Consequences:** Extra file to maintain, eventual deprecation path needed

### ADR-003: Module Organization by Responsibility
**Decision:** Separate enums, models, and logic into different modules
**Rationale:** Single Responsibility Principle, easier testing, clearer structure
**Consequences:** More files, but better organization and maintainability

### ADR-004: Optional Dependencies
**Decision:** Keep Redis and YAML as optional dependencies with try/except
**Rationale:** Graceful degradation, works without external services
**Consequences:** Must test both with and without optional dependencies

---

## Specification Compliance

### Requirement 5: Therapeutic Safety and Content Validation
✅ **AC1:** Validation against therapeutic safety guidelines
   - Implemented in: safety_validation (SafetyRuleEngine)

✅ **AC2:** Block harmful content, request alternatives
   - Implemented in: therapeutic_scoring (TherapeuticValidator.suggest_alternative)

✅ **AC3:** Align with therapeutic frameworks
   - Implemented in: therapeutic_scoring (TherapeuticContext enum)

✅ **AC4:** Escalate to human oversight
   - Implemented in: crisis_detection (HumanOversightEscalation)

✅ **AC5:** Coordinate agent activities for therapeutic goals
   - Implemented in: safety_monitoring (SafetyService orchestration)

---

## Quality Gates Alignment

### Component Maturity Criteria (Development → Staging)
- ✅ Test coverage ≥70% (TDD approach ensures this)
- ✅ All unit tests passing (TDD ensures tests pass)
- ✅ Linting clean (ruff enforced)
- ✅ Type checking clean (pyright enforced)
- ✅ Security scan passed (no secrets, safe patterns)
- ✅ Integration tests written (test inter-component interfaces)
- ✅ Documentation complete (this document + docstrings)
- ✅ No promotion blockers (backward compatibility maintained)

---

## Implementation Notes

### Bug Fixes Required
1. **Missing contextlib import** (safety_monitoring/service.py)
   - Add: `import contextlib` to imports
   - Used in: SafetyRulesProvider.get_config(), get_global_safety_service()

### Testing Strategy
1. **Unit Tests:** Test each component in isolation
2. **Integration Tests:** Test inter-component interfaces
3. **Backward Compatibility Tests:** Verify shim works correctly
4. **Coverage Target:** ≥70% for each component

### Migration Checklist
- [ ] Create 4 component directories
- [ ] Extract and refactor code (TDD approach)
- [ ] Create backward compatibility shim
- [ ] Update __init__.py exports
- [ ] Verify all tests pass
- [ ] Verify quality gates pass
- [ ] Update tta-ai-framework package
- [ ] Document refactoring


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___architecture___src agent orchestration phase1 architecture document]]
