---
applyTo: "**/api/**/*.py,**/routes/**/*.py,**/endpoints/**/*.py"
description: "API design and implementation standards"
---

# API Design Instructions

## API Design Principles

1. **RESTful Design** - Follow REST conventions
2. **Type Safety** - Use Pydantic models for validation
3. **Clear Documentation** - OpenAPI/Swagger auto-generated
4. **Error Handling** - Consistent error responses
5. **Versioning** - Plan for API evolution

## FastAPI Route Structure

```python
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1", tags=["resources"])

class ResourceCreate(BaseModel):
    """Request model for creating resource."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None

class ResourceResponse(BaseModel):
    """Response model for resource."""
    id: int
    name: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True  # For ORM compatibility

@router.post(
    "/resources",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new resource",
    description="Create a new resource with the given name and description"
)
async def create_resource(
    resource: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ResourceResponse:
    """Create a new resource."""
    # Implementation
    return created_resource
```

## HTTP Method Conventions

```python
# GET - Retrieve resource(s)
@router.get("/resources")  # List all
@router.get("/resources/{id}")  # Get one

# POST - Create new resource
@router.post("/resources", status_code=201)

# PUT - Replace entire resource
@router.put("/resources/{id}")

# PATCH - Partial update
@router.patch("/resources/{id}")

# DELETE - Remove resource
@router.delete("/resources/{id}", status_code=204)
```

## Error Handling

```python
from fastapi import HTTPException

# Standard error responses
@router.get("/resources/{resource_id}")
async def get_resource(resource_id: int):
    """Get resource by ID."""
    resource = await db.get(resource_id)

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource with id {resource_id} not found"
        )

    return resource

# Custom exception handler
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError with 400 Bad Request."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )
```

## Request Validation

```python
from pydantic import BaseModel, Field, validator

class UserCreate(BaseModel):
    """User creation request."""
    email: str = Field(..., regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=8)
    age: int = Field(..., ge=0, le=150)

    @validator("password")
    def password_strength(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v
```

## Response Models

```python
from typing import List

class PaginatedResponse(BaseModel):
    """Standard paginated response."""
    items: List[ResourceResponse]
    total: int
    page: int
    page_size: int
    has_more: bool

@router.get("/resources", response_model=PaginatedResponse)
async def list_resources(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """List resources with pagination."""
    skip = (page - 1) * page_size
    items = await db.list(skip=skip, limit=page_size)
    total = await db.count()

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(skip + page_size) < total
    )
```

## Dependency Injection

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncSession:
    """Database session dependency."""
    async with SessionLocal() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    # Validate token and return user
    return user

# Use in endpoints
@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user
```

## API Versioning

```python
# Option 1: URL path versioning (preferred)
v1_router = APIRouter(prefix="/api/v1")
v2_router = APIRouter(prefix="/api/v2")

app.include_router(v1_router)
app.include_router(v2_router)

# Option 2: Header versioning
@app.middleware("http")
async def version_middleware(request: Request, call_next):
    """Handle API version from header."""
    version = request.headers.get("API-Version", "v1")
    request.state.api_version = version
    return await call_next(request)
```

## OpenAPI Documentation

```python
from fastapi import FastAPI

app = FastAPI(
    title="TTA.dev API",
    description="AI-Native Development Platform API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_tags=[
        {
            "name": "auth",
            "description": "Authentication and authorization"
        },
        {
            "name": "workflows",
            "description": "Workflow management"
        }
    ]
)
```

## Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/search")
@limiter.limit("10/minute")
async def search(query: str):
    """Search with rate limiting."""
    return results
```

## CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.tta.dev"],  # Specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## Testing APIs

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_create_resource():
    """Test resource creation."""
    response = client.post(
        "/api/v1/resources",
        json={"name": "Test Resource", "description": "Test"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Resource"

def test_unauthorized_access():
    """Test auth is required."""
    response = client.get("/api/v1/profile")
    assert response.status_code == 401
```

## Quality Checklist

- [ ] All endpoints have response models
- [ ] Request validation using Pydantic
- [ ] Proper HTTP status codes
- [ ] Error handling implemented
- [ ] OpenAPI docs complete
- [ ] Authentication/authorization configured
- [ ] Rate limiting on sensitive endpoints
- [ ] CORS properly configured
- [ ] Tests for all endpoints
- [ ] Versioning strategy in place

## Anti-Patterns

❌ **Avoid:**
```python
# No response model
@router.get("/data")
async def get_data():
    return {"data": "raw dict"}  # Untyped

# Generic errors
raise Exception("Something broke")  # Not HTTP-aware

# No validation
@router.post("/items")
async def create(item: dict):  # Accepts any dict
    pass
```

✅ **Prefer:**
```python
# Typed response
@router.get("/data", response_model=DataResponse)
async def get_data() -> DataResponse:
    return DataResponse(data="typed")

# Proper HTTP errors
raise HTTPException(
    status_code=400,
    detail="Invalid input"
)

# Validated input
@router.post("/items")
async def create(item: ItemCreate):  # Pydantic validation
    pass
```

## References

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/best-practices/)
- [REST API Design](https://restfulapi.net/)
- [HTTP Status Codes](https://httpstatuses.com/)
