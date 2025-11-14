---
applyTo: "**/auth/**/*.py,**/authentication/**/*.py,**/security/**/*.py"
description: "Authentication and security implementation standards"
---

# Authentication & Security Instructions

## Core Principles

1. **Never store plaintext passwords** - Always use bcrypt or argon2
2. **Implement rate limiting** - Prevent brute force attacks
3. **Use secure token management** - JWT with proper expiry
4. **Log all auth attempts** - For security auditing
5. **Validate all inputs** - Prevent injection attacks

## Required Patterns

### Password Hashing

```python
from passlib.hash import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.verify(password, hashed)
```

### JWT Token Generation

```python
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "your-secret-key"  # Load from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

def create_access_token(data: dict) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### Rate Limiting

```python
from fastapi import HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(credentials: LoginCredentials):
    """Login endpoint with rate limiting."""
    # Implementation
```

## Security Checklist

- [ ] All passwords hashed with bcrypt/argon2
- [ ] Rate limiting on all auth endpoints
- [ ] JWT tokens have expiration
- [ ] Refresh token rotation implemented
- [ ] All auth events logged
- [ ] Input validation on all fields
- [ ] HTTPS enforced in production
- [ ] CORS properly configured
- [ ] Session management secure
- [ ] Password complexity requirements enforced

## Anti-Patterns to Avoid

❌ **Never do this:**
```python
# Storing plaintext passwords
user.password = request.password  # WRONG!

# No rate limiting
@app.post("/login")  # Missing limiter
async def login(): pass

# Tokens without expiration
token = jwt.encode(data, key)  # No "exp" claim
```

✅ **Always do this:**
```python
# Properly hashed passwords
user.password_hash = bcrypt.hash(request.password)

# Rate limiting on sensitive endpoints
@limiter.limit("5/minute")
@app.post("/login")
async def login(): pass

# Tokens with proper expiration
token = create_access_token({"sub": user.id})  # Includes expiry
```

## Testing Requirements

All authentication code must include:

1. **Unit tests** for password hashing/verification
2. **Integration tests** for login flow
3. **Security tests** for common vulnerabilities
4. **Rate limiting tests** to verify protection

```python
import pytest

async def test_password_hashing():
    """Test password hashing."""
    password = "SecurePass123!"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)

async def test_rate_limiting():
    """Test login rate limiting."""
    for i in range(6):  # Exceed limit
        response = await client.post("/login", json=credentials)
    assert response.status_code == 429  # Too many requests
```

## Compliance

- **OWASP Top 10** - Follow OWASP authentication best practices
- **GDPR** - Log only necessary authentication data
- **SOC 2** - Implement audit trail for all auth events

## References

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
