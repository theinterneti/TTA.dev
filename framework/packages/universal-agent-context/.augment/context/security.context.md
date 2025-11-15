# Context: Security

**Purpose:** Security review and vulnerability assessment guidance for TTA development

**When to Use:**
- Implementing authentication/authorization
- Handling sensitive data
- Reviewing code for security issues
- Preparing for production deployment
- Investigating security incidents

---

## Security Principles

### 1. Defense in Depth
- Multiple layers of security
- No single point of failure
- Assume breach mentality

### 2. Least Privilege
- Grant minimum necessary permissions
- Restrict access by default
- Regular access reviews

### 3. Secure by Default
- Security enabled out of the box
- Safe defaults
- Explicit opt-in for risky features

---

## Common Security Vulnerabilities

### 1. Secrets Management

**Problem:** Hardcoded secrets in code

**❌ Bad:**
```python
# Hardcoded API key
OPENROUTER_API_KEY = "sk-or-v1-abc123..."

# Hardcoded database password
REDIS_URL = "redis://:password123@localhost:6379"
```

**✅ Good:**
```python
# Use environment variables
import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable required")

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise ValueError("REDIS_URL environment variable required")
```

**Detection:**
```bash
# Scan for secrets
uvx detect-secrets scan

# Pre-commit hook
# .pre-commit-config.yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.4.0
  hooks:
    - id: detect-secrets
```

---

### 2. Input Validation

**Problem:** Unvalidated user input

**❌ Bad:**
```python
# No validation
async def create_session(user_id: str):
    session = Session(user_id=user_id)
    await save_session(session)
    return session
```

**✅ Good:**
```python
from pydantic import BaseModel, Field, validator

class SessionCreate(BaseModel):
    """Validated session creation request."""
    user_id: str = Field(..., min_length=3, max_length=100)
    
    @validator("user_id")
    def validate_user_id(cls, v: str) -> str:
        # Alphanumeric and underscore only
        if not v.replace("_", "").isalnum():
            raise ValueError("user_id must be alphanumeric")
        return v

async def create_session(request: SessionCreate):
    session = Session(user_id=request.user_id)
    await save_session(session)
    return session
```

---

### 3. SQL/NoSQL Injection

**Problem:** Unsanitized input in queries

**❌ Bad:**
```python
# String concatenation (vulnerable to injection)
def get_user_sessions(user_id: str):
    query = f"MATCH (s:Session {{user_id: '{user_id}'}}) RETURN s"
    return neo4j.run(query)
```

**✅ Good:**
```python
# Parameterized query
def get_user_sessions(user_id: str):
    return neo4j.run(
        "MATCH (s:Session {user_id: $user_id}) RETURN s",
        user_id=user_id
    )
```

---

### 4. Authentication & Authorization

**Problem:** Missing or weak authentication

**❌ Bad:**
```python
# No authentication
@app.post("/api/v1/sessions")
async def create_session(user_id: str):
    # Anyone can create session for any user!
    return await session_service.create(user_id)
```

**✅ Good:**
```python
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Verify JWT token and return current user."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return await get_user(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/v1/sessions")
async def create_session(
    current_user: User = Depends(get_current_user)
):
    # Only authenticated user can create their own session
    return await session_service.create(current_user.id)
```

---

### 5. Cross-Site Scripting (XSS)

**Problem:** Unescaped user input in responses

**❌ Bad:**
```python
# Return raw user input
@app.get("/api/v1/narrative/{session_id}")
async def get_narrative(session_id: str):
    narrative = await get_narrative_content(session_id)
    # If narrative contains <script>, it will execute!
    return {"content": narrative}
```

**✅ Good:**
```python
from html import escape

@app.get("/api/v1/narrative/{session_id}")
async def get_narrative(session_id: str):
    narrative = await get_narrative_content(session_id)
    # Escape HTML to prevent XSS
    return {"content": escape(narrative)}
```

---

### 6. Insecure Direct Object References (IDOR)

**Problem:** Access control not enforced

**❌ Bad:**
```python
# No authorization check
@app.get("/api/v1/sessions/{session_id}")
async def get_session(session_id: str):
    # Any user can access any session!
    return await session_service.get(session_id)
```

**✅ Good:**
```python
@app.get("/api/v1/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    session = await session_service.get(session_id)
    
    # Verify user owns this session
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return session
```

---

### 7. Rate Limiting

**Problem:** No protection against abuse

**❌ Bad:**
```python
# No rate limiting
@app.post("/api/v1/sessions/{session_id}/actions")
async def player_action(session_id: str, action: dict):
    # Attacker can spam requests!
    return await process_action(session_id, action)
```

**✅ Good:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/sessions/{session_id}/actions")
@limiter.limit("10/minute")  # Max 10 requests per minute
async def player_action(
    session_id: str,
    action: dict,
    request: Request
):
    return await process_action(session_id, action)
```

---

### 8. Sensitive Data Exposure

**Problem:** Logging sensitive data

**❌ Bad:**
```python
# Log sensitive data
logger.info(f"User login: {username}, password: {password}")
logger.debug(f"API key: {api_key}")
```

**✅ Good:**
```python
# Never log sensitive data
logger.info(f"User login: {username}")
logger.debug(f"API key: {'*' * 8}")  # Redacted

# Use structured logging with redaction
import logging
from pythonjsonlogger import jsonlogger

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        # Redact sensitive fields
        if hasattr(record, 'password'):
            record.password = '***REDACTED***'
        if hasattr(record, 'api_key'):
            record.api_key = '***REDACTED***'
        return True

logger = logging.getLogger(__name__)
logger.addFilter(SensitiveDataFilter())
```

---

## Security Checklist

### Authentication & Authorization
- [ ] All endpoints require authentication (except public ones)
- [ ] JWT tokens used for authentication
- [ ] Tokens have expiration time
- [ ] Authorization checks enforce ownership
- [ ] Password hashing uses bcrypt/argon2
- [ ] No hardcoded credentials

### Input Validation
- [ ] All user input validated with Pydantic
- [ ] Input length limits enforced
- [ ] Special characters sanitized
- [ ] File uploads validated (type, size)
- [ ] No SQL/NoSQL injection vulnerabilities

### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] HTTPS enforced in production
- [ ] Secrets stored in environment variables
- [ ] No secrets in logs
- [ ] No secrets in version control
- [ ] Database connections use TLS

### API Security
- [ ] Rate limiting implemented
- [ ] CORS configured properly
- [ ] CSRF protection enabled
- [ ] Request size limits enforced
- [ ] Error messages don't leak info

### Dependencies
- [ ] Dependencies up to date
- [ ] No known vulnerabilities (safety check)
- [ ] Minimal dependencies
- [ ] Dependencies from trusted sources

---

## Security Testing

### 1. Secrets Scanning

```bash
# Scan for secrets
uvx detect-secrets scan

# Audit secrets baseline
uvx detect-secrets audit .secrets.baseline

# Pre-commit hook
# .pre-commit-config.yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.4.0
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']
```

---

### 2. Dependency Scanning

```bash
# Check for known vulnerabilities
uv pip list --format=json | uvx safety check --stdin

# Update dependencies
uv sync --upgrade
```

---

### 3. Static Analysis

```bash
# Security linting
uvx bandit -r src/

# Type checking (prevents some vulnerabilities)
uvx pyright src/
```

---

### 4. Penetration Testing

**Manual Testing:**
- Test authentication bypass
- Test authorization bypass
- Test input validation
- Test rate limiting
- Test error handling

**Automated Testing:**
```python
# Test authentication required
async def test_authentication_required():
    response = await client.get("/api/v1/sessions/test_session")
    assert response.status_code == 401

# Test authorization enforced
async def test_authorization_enforced():
    # User A creates session
    session = await create_session(user_a_token)
    
    # User B tries to access
    response = await client.get(
        f"/api/v1/sessions/{session.id}",
        headers={"Authorization": f"Bearer {user_b_token}"}
    )
    assert response.status_code == 403
```

---

## TTA-Specific Security Considerations

### 1. AI Provider Security

**Protect API Keys:**
```python
# ✅ Good: API key from environment
class AIProvider:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY required")
    
    async def generate(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": os.getenv("APP_URL"),  # Required by OpenRouter
        }
        # Make request
        ...
```

**Sanitize Prompts:**
```python
# ✅ Good: Sanitize user input before sending to AI
def sanitize_prompt(user_input: str) -> str:
    """Sanitize user input for AI prompt."""
    # Remove potential prompt injection
    sanitized = user_input.replace("Ignore previous instructions", "")
    sanitized = sanitized.replace("System:", "")
    
    # Limit length
    max_length = 1000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized
```

---

### 2. Session Security

**Secure Session IDs:**
```python
import secrets

def generate_session_id() -> str:
    """Generate cryptographically secure session ID."""
    return secrets.token_urlsafe(32)  # 256 bits of entropy
```

**Session Expiration:**
```python
# ✅ Good: Sessions expire
class Session(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    
    @classmethod
    def create(cls, user_id: str, ttl_hours: int = 24):
        now = datetime.utcnow()
        return cls(
            id=generate_session_id(),
            user_id=user_id,
            created_at=now,
            expires_at=now + timedelta(hours=ttl_hours)
        )
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
```

---

### 3. Database Security

**Redis Security:**
```python
# ✅ Good: Use TLS and authentication
REDIS_URL = os.getenv("REDIS_URL")  # redis://user:password@host:6379/0?ssl=true

redis = await create_redis_connection(
    url=REDIS_URL,
    ssl=True,
    ssl_cert_reqs="required"
)
```

**Neo4j Security:**
```python
# ✅ Good: Use encrypted connection
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI")  # neo4j+s://host:7687
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD),
    encrypted=True
)
```

---

## Resources

### TTA Documentation
- Global Instructions: `.augment/instructions/global.instructions.md`
- Component Failures: `.augment/memory/component-failures.memory.md`

### External Resources
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- Python Security: https://python.readthedocs.io/en/stable/library/security_warnings.html

---

**Note:** Security is not a one-time task. Regular security reviews and updates are essential.

