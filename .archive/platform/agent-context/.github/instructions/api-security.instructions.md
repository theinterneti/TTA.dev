---
applyTo:
  - pattern: "src/api_gateway/**/*.py"
  - pattern: "**/*_api*.py"
  - pattern: "**/*_auth*.py"
tags: ["python", "api", "security", "authentication", "authorization"]
description: "API security requirements, authentication patterns, and authorization guidelines for TTA"
---

# API Security Requirements

## Overview

This instruction set defines security standards for TTA's API layer. All API code must implement proper authentication, authorization, input validation, and rate limiting.

## Core Principles

### 1. Authentication
- Use JWT tokens for stateless authentication
- Implement token expiration and refresh
- Secure token storage (httpOnly cookies)
- Support multiple authentication methods

### 2. Authorization
- Implement role-based access control (RBAC)
- Verify permissions on every endpoint
- Use principle of least privilege
- Log all authorization decisions

### 3. Input Validation
- Validate all user inputs
- Use Pydantic for request validation
- Sanitize outputs
- Prevent injection attacks

## Implementation Standards

### Authentication Middleware

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredentials = Depends(security)) -> dict:
    """Verify JWT token.

    Args:
        credentials: HTTP bearer credentials

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token invalid or expired
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Authorization Decorator

```python
from functools import wraps
from typing import List

def require_role(required_roles: List[str]):
    """Decorator to require specific roles.

    Args:
        required_roles: List of required roles
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: dict = Depends(verify_token), **kwargs):
            user_roles = current_user.get("roles", [])
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

### Input Validation

```python
from pydantic import BaseModel, Field, validator

class PlayerInputRequest(BaseModel):
    """Validated player input request."""
    player_id: str = Field(..., min_length=1, max_length=100)
    input_text: str = Field(..., min_length=1, max_length=1000)

    @validator('input_text')
    def validate_input_text(cls, v):
        """Validate input text for safety."""
        if len(v.strip()) == 0:
            raise ValueError("Input cannot be empty")
        return v.strip()
```

## Security Checklist

### Authentication
- [ ] JWT tokens implemented
- [ ] Token expiration enforced
- [ ] Refresh token mechanism
- [ ] Secure token storage
- [ ] Token validation on every request

### Authorization
- [ ] RBAC implemented
- [ ] Permission checks on all endpoints
- [ ] Principle of least privilege
- [ ] Authorization logging

### Input Validation
- [ ] All inputs validated
- [ ] Pydantic models used
- [ ] Output sanitized
- [ ] Injection attacks prevented

### Rate Limiting
- [ ] Rate limiting implemented
- [ ] Per-user rate limits
- [ ] Per-endpoint rate limits
- [ ] Rate limit headers returned

### HTTPS/TLS
- [ ] HTTPS enforced
- [ ] TLS 1.2+ required
- [ ] Certificate validation
- [ ] HSTS headers set

## Testing Requirements

### Security Tests
```python
@pytest.mark.asyncio
async def test_unauthorized_access():
    """Test unauthorized access is denied."""
    response = await client.get("/api/protected")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_insufficient_permissions():
    """Test insufficient permissions denied."""
    token = create_token(roles=["user"])
    response = await client.get(
        "/api/admin",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
```

### Injection Attack Tests
```python
@pytest.mark.asyncio
async def test_sql_injection_prevention():
    """Test SQL injection prevention."""
    malicious_input = "'; DROP TABLE players; --"
    response = await client.post(
        "/api/players",
        json={"name": malicious_input}
    )
    # Should be safely escaped
    assert response.status_code in [200, 422]
```

## Common Patterns

### Secure Endpoint
```python
@app.post("/api/player-input")
async def submit_player_input(
    request: PlayerInputRequest,
    current_user: dict = Depends(verify_token)
):
    """Submit player input (requires authentication)."""
    # Authorization check
    if request.player_id != current_user["player_id"]:
        raise HTTPException(status_code=403, detail="Cannot modify other player's data")

    # Process input
    result = await process_input(request.input_text)
    return result
```

## Code Review Checklist

- [ ] Authentication implemented
- [ ] Authorization verified
- [ ] Input validation complete
- [ ] Output sanitized
- [ ] Rate limiting configured
- [ ] HTTPS enforced
- [ ] Security tests passing
- [ ] No hardcoded secrets
- [ ] Logging comprehensive
- [ ] Documentation updated

## References

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- JWT Best Practices: https://tools.ietf.org/html/rfc8725
- TTA Security Policy: `SECURITY.md`
