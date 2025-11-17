---
applyTo:
  - "src/components/therapeutic_safety/**"
  - "src/player_experience/**"
  - "tests/security/**"
tags: ['general']
description: "Security and therapeutic safety standards for TTA platform. Applies to security, safety, therapeutic, authentication, authorization, encryption, and privacy code."
priority: critical
category: "safety"
---

# Therapeutic Safety and Security Instructions

This file provides deterministic requirements for security-first design and therapeutic safety standards in the TTA platform.

## Therapeutic Safety Principles

### Patient Safety First
- **No Harm**: Never generate content that could harm users
- **Crisis Detection**: Implement crisis detection and intervention
- **Professional Boundaries**: Maintain clear boundaries between AI and human therapy
- **Evidence-Based**: Use only evidence-based therapeutic approaches

### Content Safety
- **Trigger Warnings**: Provide warnings for potentially triggering content
- **Age Appropriateness**: Ensure content is appropriate for target age group
- **Cultural Sensitivity**: Respect cultural differences and sensitivities
- **Trauma-Informed**: Use trauma-informed care principles

### Crisis Intervention
```python
# Example crisis detection pattern
from src.components.therapeutic_safety.crisis_detector import CrisisDetector

async def process_user_input(user_input: str) -> Response:
    # Check for crisis indicators
    crisis_level = await crisis_detector.assess(user_input)

    if crisis_level >= CrisisLevel.HIGH:
        # Immediate intervention
        return crisis_intervention_response()
    elif crisis_level >= CrisisLevel.MODERATE:
        # Escalate to human therapist
        await escalate_to_therapist(user_input)
        return supportive_response()
    else:
        # Normal processing
        return await process_normally(user_input)
```

## Security Requirements

### Authentication & Authorization
- **Secure Sessions**: Use secure, HTTP-only cookies
- **Token Expiration**: Implement short-lived tokens with refresh mechanism
- **Role-Based Access**: Enforce role-based access control (RBAC)
- **Multi-Factor Auth**: Support MFA for sensitive operations

### Data Protection
- **Encryption at Rest**: Encrypt all sensitive data at rest
- **Encryption in Transit**: Use TLS 1.3 for all communications
- **PII Handling**: Minimize PII collection and storage
- **Data Retention**: Implement data retention and deletion policies

### Input Validation
```python
# Example input validation pattern
from pydantic import BaseModel, Field, validator

class UserInput(BaseModel):
    content: str = Field(..., max_length=10000)

    @validator('content')
    def validate_content(cls, v):
        # Sanitize input
        sanitized = sanitize_input(v)

        # Check for malicious patterns
        if contains_malicious_patterns(sanitized):
            raise ValueError("Invalid input detected")

        return sanitized
```

### API Security
- **Rate Limiting**: Implement rate limiting on all endpoints
- **CORS Configuration**: Strict CORS policy
- **CSRF Protection**: Enable CSRF protection for state-changing operations
- **SQL Injection Prevention**: Use parameterized queries only

## Compliance Requirements

### HIPAA Compliance
- **PHI Protection**: Protect all Protected Health Information (PHI)
- **Audit Logging**: Log all access to PHI
- **Breach Notification**: Implement breach detection and notification
- **Business Associate Agreements**: Ensure all third-party services have BAAs

### GDPR Compliance
- **Right to Access**: Implement data access requests
- **Right to Erasure**: Implement data deletion requests
- **Data Portability**: Support data export in standard formats
- **Consent Management**: Track and manage user consent

### Accessibility (WCAG 2.1 AA)
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: ARIA labels and semantic HTML
- **Color Contrast**: Minimum 4.5:1 contrast ratio
- **Focus Indicators**: Clear focus indicators for all interactive elements

## Error Handling

### Secure Error Messages
```python
# DO NOT expose internal details
# BAD:
raise ValueError(f"Database connection failed: {db_connection_string}")

# GOOD:
logger.error(f"Database connection failed: {db_connection_string}")
raise ValueError("An error occurred. Please try again later.")
```

### Logging Best Practices
```python
# DO NOT log sensitive information
# BAD:
logger.info(f"User login: {username} with password {password}")

# GOOD:
logger.info(f"User login attempt: {username}")
```

## Testing Requirements

### Security Testing
- **Penetration Testing**: Regular penetration testing
- **Vulnerability Scanning**: Automated vulnerability scanning
- **Dependency Auditing**: Regular dependency security audits
- **Code Review**: Security-focused code reviews

### Safety Testing
- **Crisis Scenario Testing**: Test crisis detection and intervention
- **Content Safety Testing**: Test content filtering and moderation
- **Boundary Testing**: Test professional boundary maintenance
- **Adversarial Testing**: Test against adversarial inputs

## Monitoring & Alerting

### Security Monitoring
- **Failed Login Attempts**: Alert on suspicious login patterns
- **Unusual Access Patterns**: Detect and alert on anomalies
- **Data Exfiltration**: Monitor for data exfiltration attempts
- **API Abuse**: Detect and prevent API abuse

### Safety Monitoring
- **Crisis Events**: Alert on crisis detection events
- **Content Violations**: Monitor for content policy violations
- **User Distress**: Track indicators of user distress
- **Escalation Patterns**: Monitor escalation to human therapists

## Incident Response

### Security Incidents
1. **Detect**: Automated detection and alerting
2. **Contain**: Immediate containment measures
3. **Investigate**: Root cause analysis
4. **Remediate**: Fix vulnerabilities
5. **Report**: Notify affected parties and authorities

### Safety Incidents
1. **Detect**: Crisis detection and user reports
2. **Assess**: Evaluate severity and risk
3. **Intervene**: Immediate intervention if needed
4. **Escalate**: Escalate to human professionals
5. **Follow-up**: Track outcomes and improve

## Code Review Checklist

### Security Review
- [ ] Input validation implemented
- [ ] Authentication and authorization enforced
- [ ] Sensitive data encrypted
- [ ] Error messages don't expose internals
- [ ] Rate limiting implemented
- [ ] CSRF protection enabled
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified

### Safety Review
- [ ] Crisis detection implemented
- [ ] Content filtering enabled
- [ ] Professional boundaries maintained
- [ ] Trigger warnings provided
- [ ] Age-appropriate content verified
- [ ] Cultural sensitivity reviewed
- [ ] Trauma-informed approach verified
- [ ] Escalation paths defined

## References

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **HIPAA Security Rule**: https://www.hhs.gov/hipaa/for-professionals/security/
- **GDPR**: https://gdpr.eu/
- **WCAG 2.1**: https://www.w3.org/WAI/WCAG21/quickref/
- **Trauma-Informed Care**: https://www.samhsa.gov/trauma-violence

---

**Last Updated**: 2025-10-26
**Status**: Active - Critical safety and security requirements
