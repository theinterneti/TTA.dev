# Build Example Projects Demonstrating Primitives

## 📋 Overview

Create comprehensive end-to-end example projects that demonstrate the complete lifecycle of feature development using agentic primitives, from planning through deployment.

## 🎯 Objectives

Provide real-world, production-quality examples that showcase how primitives improve the development process and serve as learning resources for teams adopting the system.

## 📦 Deliverables

### 1. Example Project: Blog Authentication System

Create a complete authentication system for a blog platform demonstrating all primitives in action.

#### Project Structure
```
examples/blog-authentication/
├── README.md                          # Project overview
├── CONSTITUTION.md                    # Project constitution
├── planning/
│   ├── feature-spec.md                # Initial specification
│   ├── implementation-plan.md         # Detailed plan
│   └── task-breakdown.md              # Task list
├── src/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt_handler.py             # JWT implementation
│   │   ├── password_hasher.py         # Password hashing
│   │   └── session_manager.py         # Session management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py                  # Auth endpoints
│   │   └── middleware.py              # Auth middleware
│   └── models/
│       ├── __init__.py
│       └── user.py                    # User model
├── tests/
│   ├── unit/
│   │   ├── test_jwt_handler.py
│   │   ├── test_password_hasher.py
│   │   └── test_session_manager.py
│   ├── integration/
│   │   ├── test_auth_flow.py
│   │   └── test_api_endpoints.py
│   └── e2e/
│       └── test_user_journey.py
├── .memory.md/
│   ├── architecture/
│   │   └── auth-system-design.md      # Architecture decisions
│   ├── decisions/
│   │   ├── jwt-vs-sessions.md         # Technology choices
│   │   └── password-policy.md         # Security decisions
│   └── patterns/
│       └── rate-limiting.md           # Implemented patterns
├── docs/
│   ├── development-log.md             # Development journey
│   ├── primitive-usage.md             # How primitives were used
│   └── lessons-learned.md             # Insights gained
└── .github/
    └── workflows/
        └── ci.yml                      # CI/CD pipeline

```

#### Feature Implementation Phases

**Phase 1: Planning with `/speckit`**
- Generate project constitution
- Create feature specification
- Develop implementation plan
- Break down into tasks

**Phase 2: Implementation with Primitives**
- Load `authentication.instructions.md` for guidance
- Activate `backend-engineer.chatmode.md`
- Use `feature-specification.prompt.md` workflow
- Document decisions in `.memory.md/`

**Phase 3: Testing with Validation**
- Follow `testing.instructions.md`
- Activate `qa-engineer.chatmode.md`
- Achieve 95%+ coverage
- Run validation gates

**Phase 4: Documentation & Review**
- Use `documentation.instructions.md`
- Activate `architect.chatmode.md` for review
- Generate API documentation
- Create user guides

**Phase 5: Deployment**
- CI/CD with primitive validation
- Deployment with rollback plan
- Post-deployment monitoring

### 2. Example Project: Rate Limiting Service

Simpler example focusing on a single feature with clear primitive usage.

```
examples/rate-limiting/
├── README.md
├── src/
│   └── rate_limiter.py
├── tests/
│   └── test_rate_limiter.py
├── .memory.md/
│   └── patterns/
│       └── sliding-window.md
└── docs/
    └── primitive-usage.md
```

### 3. Example Project: OAuth Integration

Demonstrates security-focused development with primitives.

```
examples/oauth-integration/
├── README.md
├── SECURITY.md
├── src/
│   ├── oauth_client.py
│   └── token_validator.py
├── tests/
│   └── test_oauth_flow.py
├── .memory.md/
│   ├── decisions/
│   │   └── oauth-provider-choice.md
│   └── patterns/
│       └── token-refresh.md
└── docs/
    └── security-review.md
```

### 4. Comprehensive Documentation

Create detailed documentation for each example:

```
examples/
├── README.md                          # Examples overview
├── LEARNING_PATH.md                   # Recommended learning order
├── PRIMITIVE_MAPPING.md               # Which primitives used where
└── COMPARISON.md                      # Before/after comparison
```

## 🔧 Technical Requirements

### Code Quality Standards
- ✅ All code follows primitives guidance
- ✅ 95%+ test coverage
- ✅ Type hints throughout
- ✅ Comprehensive docstrings
- ✅ No linting errors

### Primitive Integration
- ✅ Instructions loaded selectively
- ✅ Chat modes activated appropriately
- ✅ Workflows followed completely
- ✅ Memory system populated
- ✅ APM configuration used

### Documentation Requirements
- ✅ Step-by-step development log
- ✅ Primitive usage explained
- ✅ Decision rationale documented
- ✅ Lessons learned captured
- ✅ Before/after metrics

## 📝 Success Criteria

### Functional
- [ ] All examples run successfully
- [ ] Tests pass with 95%+ coverage
- [ ] CI/CD workflows execute
- [ ] Documentation is clear
- [ ] Examples are copy-pastable

### Educational
- [ ] Learning path is logical
- [ ] Primitive usage is clear
- [ ] Common patterns demonstrated
- [ ] Mistakes and fixes shown
- [ ] Best practices highlighted

### Quality
- [ ] Production-quality code
- [ ] Realistic scenarios
- [ ] Proper error handling
- [ ] Security best practices
- [ ] Performance considerations

## 🎓 Example: Development Log (Blog Auth)

### Day 1: Planning
```markdown
## Planning Phase

### 1. Generated Constitution
Command: `/speckit constitution --name "Blog Auth" --domain "content-platform"`
Result: Created CONSTITUTION.md with security principles

Primitives used:
- architect.chatmode.md (for system design)
- Memory system (to store constitution)

### 2. Created Feature Specification
Command: `/speckit specify --feature "JWT authentication"`
Result: Detailed spec in .memory.md/architecture/

Primitives used:
- feature-specification.prompt.md (workflow)
- authentication.instructions.md (guidance)

### 3. Generated Implementation Plan
Command: `/speckit plan --spec .memory.md/architecture/jwt-auth.md`
Result: 4-phase plan with validation gates

Primitives used:
- Validation gates (human review required)
- Task breakdown patterns

Insights:
- Constitution helped establish security-first approach
- Feature spec caught missing requirements early
- Validation gates prevented scope creep
```

### Day 2: Implementation
```markdown
## Implementation Phase

### 1. JWT Handler Implementation
Activated: backend-engineer.chatmode.md
Loaded: authentication.instructions.md, api-design.instructions.md

Code: src/auth/jwt_handler.py
Tests: tests/unit/test_jwt_handler.py

Primitives impact:
- Instructions caught security issues (token expiration)
- Chat mode enforced MCP boundaries (no direct DB access)
- Testing standards required 95% coverage

### 2. Password Hashing
Loaded: authentication.instructions.md (bcrypt guidance)

Code: src/auth/password_hasher.py
Tests: tests/unit/test_password_hasher.py

Decision documented: .memory.md/decisions/bcrypt-vs-argon2.md

Primitives impact:
- Instructions recommended bcrypt over SHA256
- Memory system captured decision rationale
- Testing instructions caught edge cases
```

### Day 3: Testing & Review
```markdown
## Testing Phase

Activated: qa-engineer.chatmode.md
Loaded: testing.instructions.md

Created:
- Unit tests (95% coverage achieved)
- Integration tests (API flow validated)
- E2E tests (user journey verified)

Primitives impact:
- Testing instructions enforced coverage
- QA mode caught security test gaps
- Validation gates required manual review

Architecture Review:
Activated: architect.chatmode.md
Review: System design validated
Result: Approved for deployment
```

## 📚 References

- **Primitives:** All `.github/` primitives
- **Validation:** `tests/validation/`
- **APM:** `apm.yml`
- **Documentation:** `docs/architecture/AGENTIC_PRIMITIVES_IMPLEMENTATION.md`

## 🔗 Related Issues

- Depends on: #[Task 7: Spec-Driven Development] (helpful but not required)
- Blocks: None
- Related to: #[Task 8: CI/CD Integration]

## 📊 Estimated Effort

- **Complexity:** Medium-High
- **Time Estimate:** 2-3 days
- **Priority:** Low (educational, not blocking)
- **Dependencies:** Task 7 helpful but not required

## ✅ Definition of Done

- [ ] 3+ example projects complete
- [ ] All examples tested and working
- [ ] Development logs documented
- [ ] Primitive usage explained
- [ ] Learning path created
- [ ] Before/after comparison documented
- [ ] CI/CD workflows functional
- [ ] Code review approved
- [ ] Published in examples/ directory

## 🎯 Metrics to Capture

### Development Speed
- Time with primitives vs without
- Number of iterations required
- Rework percentage

### Code Quality
- Test coverage achieved
- Security issues found
- Code review feedback

### Developer Experience
- Cognitive load rating
- Documentation usefulness
- Primitive helpfulness

### Token Efficiency
- Tokens used with selective loading
- Tokens used without primitives
- Percentage improvement

---

**Labels:** enhancement, documentation, examples, education
**Milestone:** Agentic Primitives v1.0
**Assignee:** TBD
