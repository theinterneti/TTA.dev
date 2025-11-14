# Agentic Workflow: Feature Specification

**Purpose:** Transform user requirements into a detailed, implementation-ready specification

**Mode Required:** Architect (planning only, no implementation)

**Expected Duration:** 15-30 minutes

---

## Context Loading Phase

Before starting the specification process, gather all relevant context:

### Required Context

1. **Existing Specifications**
   - Review `specs/` directory for related features
   - Check `docs/architecture/` for architectural constraints
   - Load `.memory.md` files for past architectural decisions

2. **Project Documentation**
   - Read `AGENTS.md` for project standards
   - Review `README.md` for project overview
   - Check `.github/instructions/` for domain-specific rules

3. **Similar Implementations**
   - Use `#codebase` to find similar features
   - Search for related API endpoints
   - Identify reusable patterns

### Context Loading Commands

```markdown
#file:./docs/architecture/AGENTS.md
#file:./specs/related-feature.spec.md
#codebase: similar authentication implementation
#fetch: https://docs.framework.io/relevant-pattern
```

---

## Deterministic Execution Workflow

### Step 1: Requirements Gathering (5 min)

**Input:** User story or feature request

**Actions:**
1. Extract functional requirements
2. Identify non-functional requirements (performance, security, scalability)
3. Clarify ambiguities with targeted questions
4. Define success criteria

**Output:**
```markdown
## Requirements Summary

### Functional Requirements
- FR1: User can login with email and password
- FR2: System validates credentials against database
- FR3: Successful login returns JWT access token

### Non-Functional Requirements
- NFR1: Authentication response time < 200ms (p95)
- NFR2: Support 1000 concurrent logins
- NFR3: Passwords hashed with bcrypt (cost factor 12)

### Success Criteria
- [ ] User can login with valid credentials
- [ ] Invalid credentials rejected with proper error
- [ ] Rate limiting prevents brute force (5 attempts/minute)
- [ ] All auth events logged for audit
```

### Step 2: Context Research (10 min)

**Actions:**
1. Search for existing implementations
   ```markdown
   #codebase: authentication login JWT
   ```

2. Review framework documentation
   ```markdown
   #fetch: https://fastapi.tiangolo.com/tutorial/security/
   ```

3. Check architectural decisions
   ```markdown
   #file:./.memory.md/architecture/auth-decisions.md
   ```

4. Identify reusable components
   - Existing database models
   - Shared utilities (password hashing)
   - Common middleware (auth, rate limiting)

**Output:** Context summary with links to relevant files and patterns

### Step 3: Specification Writing (10 min)

**Actions:**
1. Create `.spec.md` file using template
2. Define API contracts
3. Specify data models
4. Document business logic
5. Add testing strategy

**Template:**

```markdown
# Feature Specification: [Feature Name]

**Created:** YYYY-MM-DD
**Author:** [Your Name]
**Status:** Draft | Review | Approved

## Overview

Brief description of the feature and its purpose.

## User Stories

### US-001: [User Story Title]
**As a** [user type]
**I want** [goal]
**So that** [benefit]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## API Specification

### Endpoint: POST /api/v1/login

**Request:**
\`\`\`json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
\`\`\`

**Response (Success - 200):**
\`\`\`json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
\`\`\`

**Response (Error - 401):**
\`\`\`json
{
  "detail": "Invalid credentials"
}
\`\`\`

**Response (Rate Limited - 429):**
\`\`\`json
{
  "detail": "Too many login attempts. Try again in 60 seconds."
}
\`\`\`

## Data Models

### User
\`\`\`python
class User(Base):
    id: int
    email: str (unique, indexed)
    password_hash: str
    email_verified: bool
    created_at: datetime
    last_login: datetime | None
\`\`\`

## Business Logic

### Authentication Flow
1. Client submits email + password
2. System validates email format
3. System rate checks (5 attempts/minute/IP)
4. System retrieves user by email
5. System verifies password hash
6. System generates JWT token (15min expiry)
7. System logs authentication event
8. System returns access token

### Password Verification
- Use bcrypt.verify() for constant-time comparison
- Log all verification attempts (success/failure)
- Increment failed attempt counter for rate limiting

## Security Considerations

- Passwords stored as bcrypt hashes (never plaintext)
- JWT signed with RS256 (asymmetric encryption)
- Rate limiting prevents brute force attacks
- All auth events logged for audit trail
- Token expiration enforced (15 minutes)
- Refresh tokens rotated on use

## Testing Strategy

### Unit Tests
- Password hashing/verification
- JWT token generation/validation
- Input validation (email format, password strength)

### Integration Tests
- Complete login flow
- Rate limiting enforcement
- Token refresh mechanism

### Security Tests
- SQL injection attempts
- XSS in login form
- Brute force protection
- Token tampering detection

## Performance Requirements

- Login endpoint response time: <200ms (p95)
- Support 1000 concurrent logins
- Database query optimization (indexed email lookup)

## Dependencies

- FastAPI (web framework)
- SQLAlchemy (ORM)
- python-jose (JWT handling)
- passlib (password hashing)
- slowapi (rate limiting)

## Implementation Notes

### Phase 1: Core Authentication
- Basic email/password login
- JWT token generation
- Database user lookup

### Phase 2: Security Hardening
- Rate limiting
- Audit logging
- Token refresh

### Phase 3: Enhanced Features
- OAuth providers (Google, GitHub)
- Two-factor authentication
- Password reset flow

## References

- [Authentication Best Practices](internal link)
- [JWT Standard](https://tools.ietf.org/html/rfc7519)
- [OWASP Auth Cheat Sheet](https://cheatsheetseries.owasp.org/)
```

---

## 🚨 VALIDATION GATE: Specification Review

**STOP HERE** - Do not proceed until specification is reviewed and approved.

### Review Checklist

Before proceeding to implementation planning, verify:

- [ ] **Completeness:** All functional requirements documented?
- [ ] **Clarity:** API contracts clearly defined?
- [ ] **Testability:** Success criteria measurable?
- [ ] **Security:** Security considerations addressed?
- [ ] **Performance:** Performance requirements specified?
- [ ] **Dependencies:** All dependencies identified?
- [ ] **Consistency:** Aligns with existing architecture?

### Approval Required From

- [ ] Product Owner (requirements accuracy)
- [ ] Tech Lead (technical feasibility)
- [ ] Security Team (security requirements)

**Status:** ⏸️ Awaiting Review

---

## Post-Approval Actions

### Step 4: Generate Implementation Plan

Once specification is approved, transition to:

```markdown
/mode backend-engineer
/workflow implementation-plan.prompt.md
#file:./specs/[feature-name].spec.md
```

### Step 5: Document Decisions

Store architectural decisions in memory:

```markdown
#file:./.memory.md/architecture/[feature-name]-decisions.md
```

Template:
```markdown
# Architectural Decision: [Feature Name]

## Decision
[What was decided]

## Rationale
[Why this decision was made]

## Alternatives Considered
1. **Option A**: [Pros/Cons]
2. **Option B**: [Pros/Cons]

## Consequences
- **Positive:** [Benefits]
- **Negative:** [Trade-offs]

## Implementation Notes
[Key considerations for implementation]

## References
- [Related specs]
- [Documentation links]
```

---

## Success Metrics

This workflow is successful when:

✅ Specification is complete and unambiguous
✅ All stakeholders understand requirements
✅ API contracts are clearly defined
✅ Testing strategy is documented
✅ Security considerations addressed
✅ Specification approved by required reviewers
✅ Implementation team has clear direction

---

## Common Pitfalls

❌ **Avoid:**
- Skipping context research (leads to duplicate work)
- Vague acceptance criteria (causes confusion)
- Missing security considerations (creates vulnerabilities)
- No performance requirements (causes production issues)
- Jumping to implementation details (belongs in plan.md)

✅ **Ensure:**
- Clear, measurable success criteria
- Explicit API contracts
- Security requirements defined upfront
- Performance targets specified
- Approval gates enforced

---

## Example Usage

**User Request:**
> "We need user authentication for our blog platform"

**Workflow Execution:**

1. **Load Context:**
   ```markdown
   #file:./docs/architecture/AGENTS.md
   #codebase: authentication patterns
   #fetch: FastAPI security documentation
   ```

2. **Gather Requirements:**
   - Functional: Login with email/password
   - Non-Functional: <200ms response, 1000 concurrent users
   - Security: bcrypt hashing, JWT tokens, rate limiting

3. **Write Specification:**
   - Create `specs/user-authentication.spec.md`
   - Define API endpoints (POST /login, POST /refresh)
   - Specify data models (User, AuthToken)
   - Document flows (login, token refresh)
   - Add testing strategy

4. **Validation Gate:**
   - Review with tech lead
   - Security team approval
   - Product owner sign-off

5. **Hand Off:**
   - Transition to `/mode backend-engineer`
   - Execute `/workflow implementation-plan.prompt.md`
   - Begin implementation

---

**Last Updated:** 2025-11-14
**Workflow Version:** 1.0.0
**Compatible Modes:** Architect
