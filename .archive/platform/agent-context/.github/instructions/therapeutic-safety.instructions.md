---
applyTo:
  - pattern: "src/therapeutic_safety/**/*.py"
  - pattern: "**/*_safety*.py"
  - pattern: "**/*_validation*.py"
tags: ["python", "therapeutic-safety", "hipaa", "content-validation", "emotional-safety"]
description: "Therapeutic safety validation rules, content filtering requirements, and HIPAA compliance constraints for TTA"
---

# Therapeutic Safety Requirements

## Overview

This instruction set defines standards for implementing therapeutic safety features in TTA. All code in this domain must prioritize emotional safety, content appropriateness, and HIPAA compliance.

## Core Principles

### 1. Emotional Safety First
- All therapeutic content must be validated for emotional safety
- Content filtering must prevent harmful, triggering, or inappropriate responses
- Therapeutic appropriateness must be verified before delivery to players
- Safety checks must be non-blocking but logged for audit trails

### 2. HIPAA Compliance
- All patient data must be encrypted at rest and in transit
- Access to therapeutic data must be logged with timestamps and user IDs
- Data retention policies must be enforced (no indefinite storage)
- Patient privacy must be maintained across all operations
- De-identification required for analytics and testing

### 3. Content Validation
- All AI-generated content must pass safety filters
- User inputs must be sanitized and validated
- Therapeutic appropriateness must be verified
- Harmful content must be rejected with graceful error handling

## Implementation Standards

### Safety Validation Functions

```python
async def validate_therapeutic_content(
    content: str,
    player_id: str,
    context: TherapeuticContext
) -> ValidationResult:
    """Validate content for therapeutic appropriateness.

    Args:
        content: Content to validate
        player_id: Player receiving content
        context: Therapeutic context (history, preferences, etc.)

    Returns:
        ValidationResult with safety score and recommendations

    Raises:
        ValidationError: If content fails critical safety checks
    """
```

### Logging Requirements
- All safety validations must be logged
- Failed validations must include reason codes
- Access to therapeutic data must be audited
- Logs must be retained per HIPAA requirements

### Error Handling
- Safety failures must not crash the system
- Graceful degradation when safety checks fail
- User-friendly error messages (no technical details)
- Fallback content for failed validations

## Testing Requirements

### Unit Tests
- Test all safety validation functions
- Test edge cases and boundary conditions
- Test error handling paths
- Minimum 90% coverage for safety-critical code

### Integration Tests
- Test safety validation with real therapeutic contexts
- Test content filtering with various input types
- Test HIPAA compliance logging
- Test data encryption/decryption

### Security Tests
- Test for injection attacks (prompt injection, SQL injection)
- Test for data leakage
- Test for unauthorized access
- Test for compliance violations

## HIPAA Compliance Checklist

- [ ] All patient data encrypted at rest (AES-256)
- [ ] All data in transit encrypted (TLS 1.2+)
- [ ] Access logging implemented with timestamps
- [ ] Data retention policies enforced
- [ ] De-identification for analytics
- [ ] Audit trails maintained
- [ ] Breach notification procedures documented
- [ ] Business Associate Agreements in place

## Code Review Checklist

- [ ] All therapeutic content validated
- [ ] HIPAA compliance verified
- [ ] Error handling graceful
- [ ] Logging comprehensive
- [ ] Tests passing (>90% coverage)
- [ ] Security scan passed
- [ ] Documentation updated

## Common Patterns

### Safe Content Delivery
```python
# ✅ Correct: Validate before delivery
validated = await validate_therapeutic_content(content, player_id, context)
if validated.is_safe:
    await deliver_to_player(player_id, validated.content)
else:
    await deliver_fallback_content(player_id, validated.reason)
```

### HIPAA-Compliant Logging
```python
# ✅ Correct: Log access with context
logger.info(
    "therapeutic_data_accessed",
    player_id=player_id,
    data_type="session_history",
    timestamp=datetime.utcnow(),
    user_id=current_user.id
)
```

## References

- HIPAA Security Rule: 45 CFR §164.300-318
- HIPAA Privacy Rule: 45 CFR §164.500-534
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- TTA Security Policy: `SECURITY.md`
