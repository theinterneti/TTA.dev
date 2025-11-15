# Multi-Persona Workflow: Full-Stack Feature Development

**Personas:** Backend Engineer → Frontend Engineer → Testing Specialist  
**Purpose:** Develop a complete feature from API to UI with quality validation  
**Duration:** ~4-8 hours (full feature) or ~2-3 hours (automated steps)

---

## Workflow Overview

This workflow demonstrates **full-stack development with persona orchestration**:

1. **Backend Engineer** → API development (endpoints, business logic, database)
2. **Frontend Engineer** → UI implementation (components, state management, integration)
3. **Testing Specialist** → E2E validation (user flows, integration tests, accessibility)

**TTA.dev Integrations:**
- ✅ **Hypertool Personas** - Role-based context switching
- ✅ **SequentialPrimitive** - Chain API → UI → Testing stages
- ✅ **MemoryPrimitive** - Share API contract, component specs across personas
- ✅ **E2B Code Execution** - Validate backend logic, test frontend code
- ✅ **Context7 MCP** - Query docs (FastAPI, React, Playwright)
- ✅ **Playwright MCP** - E2E testing automation
- ✅ **Logseq** - Document feature design decisions
- ✅ **GitHub MCP** - PR creation, code review

---

## Example Feature: User Profile Management

**User Story:**
```
As a user, I want to view and edit my profile
So that I can keep my information up-to-date
```

**Acceptance Criteria:**
- ✅ GET /api/users/{id} returns user profile
- ✅ PUT /api/users/{id} updates user profile
- ✅ Profile page displays user info
- ✅ Edit form validates input
- ✅ Changes persist to database
- ✅ E2E test covers full flow

---

## Stage 1: API Development (Backend Engineer Persona)

**Persona:** `tta-backend-engineer` (2000 tokens, 48 tools)  
**Duration:** ~2 hours  
**Deliverables:** REST API endpoints, tests, documentation

### Activate Backend Persona

```bash
# Switch to backend persona
tta-persona backend

# Or via chatmode
/chatmode backend-developer
```

**Verify tools:**
- ✅ Context7 (FastAPI, SQLAlchemy, Pydantic docs)
- ✅ GitHub MCP (create feature branch)
- ✅ Sequential Thinking (API design planning)
- ✅ E2B Code Execution (test endpoint logic)

### Step 1.1: Design API Contract

**Goal:** Define API specification that frontend will consume

**TTA Primitive Pattern:**
```python
from tta_dev_primitives.performance import MemoryPrimitive

# Store API contract for frontend persona
api_memory = MemoryPrimitive(namespace="feature_user_profile")

await api_memory.add("api_contract", {
    "endpoints": [
        {
            "method": "GET",
            "path": "/api/users/{user_id}",
            "response": {
                "id": "uuid",
                "email": "string",
                "display_name": "string",
                "avatar_url": "string | null",
                "created_at": "datetime"
            }
        },
        {
            "method": "PUT",
            "path": "/api/users/{user_id}",
            "request": {
                "display_name": "string",
                "avatar_url": "string | null"
            },
            "response": "UserProfile"
        }
    ],
    "models": {
        "UserProfile": {
            "id": "uuid",
            "email": "string",
            "display_name": "string",
            "avatar_url": "string | null",
            "created_at": "datetime",
            "updated_at": "datetime"
        }
    }
})
```

**Document in Logseq:**
```markdown
# Feature Design - User Profile Management

## API Contract

### GET /api/users/{user_id}
Returns user profile data

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "display_name": "John Doe",
  "avatar_url": "https://...",
  "created_at": "2025-11-14T10:00:00Z"
}
```

### PUT /api/users/{user_id}
Updates user profile

**Request:**
```json
{
  "display_name": "Jane Doe",
  "avatar_url": "https://..."
}
```

#feature #api-design #user-profile
```

### Step 1.2: Implement API Endpoints

**Create feature branch:**
```bash
# Create feature branch
git checkout -b feature/user-profile-management
```

**FastAPI implementation:**
```python
# packages/api/src/api/routes/users.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

router = APIRouter(prefix="/api/users", tags=["users"])

class UserProfile(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str
    avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime

class UserProfileUpdate(BaseModel):
    display_name: str
    avatar_url: str | None = None

@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: UUID,
    db: Database = Depends(get_database)
):
    """Get user profile by ID."""
    user = await db.users.find_one({"id": user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfile(**user)

@router.put("/{user_id}", response_model=UserProfile)
async def update_user_profile(
    user_id: UUID,
    update: UserProfileUpdate,
    db: Database = Depends(get_database)
):
    """Update user profile."""
    # Validate user exists
    existing = await db.users.find_one({"id": user_id})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    updated_data = update.model_dump(exclude_unset=True)
    updated_data["updated_at"] = datetime.utcnow()
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": updated_data}
    )
    
    # Return updated user
    updated_user = await db.users.find_one({"id": user_id})
    return UserProfile(**updated_user)
```

### Step 1.3: Validate with E2B Code Execution

**Goal:** Test endpoint logic in isolation

**E2B Test:**
```python
from tta_dev_primitives.integrations import CodeExecutionPrimitive

# Test Pydantic model validation
validation_test = """
from pydantic import BaseModel, EmailStr, ValidationError
from uuid import UUID
from datetime import datetime

class UserProfile(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str
    avatar_url: str | None = None
    created_at: datetime

# Test valid data
valid_data = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "display_name": "Test User",
    "created_at": "2025-11-14T10:00:00Z"
}

profile = UserProfile(**valid_data)
print(f"✅ Valid data passed: {profile.display_name}")

# Test invalid email
try:
    invalid_data = {**valid_data, "email": "not-an-email"}
    UserProfile(**invalid_data)
    print("❌ Should have raised ValidationError")
except ValidationError as e:
    print(f"✅ Invalid email caught: {e.error_count()} errors")

# Test missing required field
try:
    incomplete_data = {k: v for k, v in valid_data.items() if k != "email"}
    UserProfile(**incomplete_data)
    print("❌ Should have raised ValidationError")
except ValidationError:
    print("✅ Missing field caught")
"""

executor = CodeExecutionPrimitive()
result = await executor.execute(
    {"code": validation_test, "timeout": 30},
    context
)

if result["success"]:
    print("✅ Pydantic validation logic correct")
else:
    print(f"❌ Validation test failed: {result['error']}")
```

### Step 1.4: Write Backend Tests

**Goal:** 100% coverage for new endpoints

```python
# packages/api/tests/routes/test_users.py

import pytest
from uuid import uuid4
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_user_profile_success(client: AsyncClient, test_db):
    """Test GET /api/users/{id} returns profile."""
    # Arrange
    user_id = uuid4()
    await test_db.users.insert_one({
        "id": user_id,
        "email": "test@example.com",
        "display_name": "Test User",
        "created_at": "2025-11-14T10:00:00Z",
        "updated_at": "2025-11-14T10:00:00Z"
    })
    
    # Act
    response = await client.get(f"/api/users/{user_id}")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["display_name"] == "Test User"

@pytest.mark.asyncio
async def test_get_user_profile_not_found(client: AsyncClient):
    """Test GET /api/users/{id} returns 404 for unknown user."""
    response = await client.get(f"/api/users/{uuid4()}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_user_profile_success(client: AsyncClient, test_db):
    """Test PUT /api/users/{id} updates profile."""
    # Arrange
    user_id = uuid4()
    await test_db.users.insert_one({
        "id": user_id,
        "email": "test@example.com",
        "display_name": "Old Name",
        "created_at": "2025-11-14T10:00:00Z",
        "updated_at": "2025-11-14T10:00:00Z"
    })
    
    # Act
    response = await client.put(
        f"/api/users/{user_id}",
        json={"display_name": "New Name", "avatar_url": "https://..."}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "New Name"
    assert data["avatar_url"] == "https://..."
    
    # Verify database updated
    updated = await test_db.users.find_one({"id": user_id})
    assert updated["display_name"] == "New Name"
```

**Run tests:**
```bash
uv run pytest packages/api/tests/routes/test_users.py -v
```

### Step 1.5: Generate API Documentation

**Goal:** OpenAPI spec for frontend consumption

```bash
# Generate OpenAPI JSON
uv run python -c "
from api.main import app
import json

schema = app.openapi()
with open('api_schema.json', 'w') as f:
    json.dump(schema, f, indent=2)
"

# Store in memory for frontend persona
python -c "
from tta_dev_primitives.performance import MemoryPrimitive
import asyncio
import json

async def store_schema():
    mem = MemoryPrimitive(namespace='feature_user_profile')
    with open('api_schema.json') as f:
        schema = json.load(f)
    await mem.add('openapi_schema', schema)

asyncio.run(store_schema())
"
```

### Step 1.6: Commit Backend Work

```bash
git add packages/api/
git commit -m "feat(api): add user profile endpoints

- GET /api/users/{id} - retrieve user profile
- PUT /api/users/{id} - update user profile
- 100% test coverage
- OpenAPI schema generated
"

git push origin feature/user-profile-management
```

---

## Stage 2: UI Implementation (Frontend Engineer Persona)

**Persona:** `tta-frontend-engineer` (1800 tokens, 42 tools)  
**Duration:** ~2-3 hours  
**Deliverables:** React components, state management, integration

### Activate Frontend Persona

```bash
# Switch to frontend persona
tta-persona frontend

# Or via chatmode
/chatmode frontend-developer
```

**Verify tools:**
- ✅ Context7 (React, TypeScript, Tailwind docs)
- ✅ Playwright MCP (component testing)
- ✅ GitHub MCP (review backend PR)
- ✅ Sequential Thinking (component design)

### Step 2.1: Retrieve API Contract

**Goal:** Get backend API specification

```python
from tta_dev_primitives.performance import MemoryPrimitive

# Retrieve API contract from backend persona
api_memory = MemoryPrimitive(namespace="feature_user_profile")
contract = await api_memory.get("api_contract")

print("API Endpoints available:")
for endpoint in contract["endpoints"]:
    print(f"  {endpoint['method']} {endpoint['path']}")
```

### Step 2.2: Generate TypeScript Types

**Goal:** Type-safe API integration

**From OpenAPI schema:**
```typescript
// packages/frontend/src/types/api.ts

export interface UserProfile {
  id: string;
  email: string;
  display_name: string;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserProfileUpdate {
  display_name: string;
  avatar_url?: string | null;
}

// API client
export class UserAPI {
  private baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  async getProfile(userId: string): Promise<UserProfile> {
    const response = await fetch(`${this.baseURL}/api/users/${userId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch profile: ${response.statusText}`);
    }
    return response.json();
  }

  async updateProfile(
    userId: string,
    update: UserProfileUpdate
  ): Promise<UserProfile> {
    const response = await fetch(`${this.baseURL}/api/users/${userId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(update)
    });
    if (!response.ok) {
      throw new Error(`Failed to update profile: ${response.statusText}`);
    }
    return response.json();
  }
}
```

### Step 2.3: Create React Components

**Profile display component:**
```typescript
// packages/frontend/src/components/UserProfile.tsx

import React, { useState, useEffect } from 'react';
import { UserProfile as UserProfileType, UserAPI } from '../types/api';

interface UserProfileProps {
  userId: string;
}

export const UserProfile: React.FC<UserProfileProps> = ({ userId }) => {
  const [profile, setProfile] = useState<UserProfileType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);

  const api = new UserAPI();

  useEffect(() => {
    loadProfile();
  }, [userId]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const data = await api.getProfile(userId);
      setProfile(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (updates: { display_name: string; avatar_url?: string }) => {
    if (!profile) return;
    
    try {
      const updated = await api.updateProfile(userId, updates);
      setProfile(updated);
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!profile) return <div>Profile not found</div>;

  return (
    <div className="user-profile">
      {editing ? (
        <EditProfileForm
          profile={profile}
          onSave={handleSave}
          onCancel={() => setEditing(false)}
        />
      ) : (
        <DisplayProfile
          profile={profile}
          onEdit={() => setEditing(true)}
        />
      )}
    </div>
  );
};
```

**Edit form component:**
```typescript
// packages/frontend/src/components/EditProfileForm.tsx

import React, { useState } from 'react';
import { UserProfile } from '../types/api';

interface EditProfileFormProps {
  profile: UserProfile;
  onSave: (updates: { display_name: string; avatar_url?: string }) => Promise<void>;
  onCancel: () => void;
}

export const EditProfileForm: React.FC<EditProfileFormProps> = ({
  profile,
  onSave,
  onCancel
}) => {
  const [displayName, setDisplayName] = useState(profile.display_name);
  const [avatarUrl, setAvatarUrl] = useState(profile.avatar_url || '');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    await onSave({
      display_name: displayName,
      avatar_url: avatarUrl || null
    });
    setSaving(false);
  };

  return (
    <form onSubmit={handleSubmit} className="edit-profile-form">
      <div className="form-group">
        <label htmlFor="display_name">Display Name</label>
        <input
          type="text"
          id="display_name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          required
          minLength={3}
          maxLength={50}
        />
      </div>

      <div className="form-group">
        <label htmlFor="avatar_url">Avatar URL</label>
        <input
          type="url"
          id="avatar_url"
          value={avatarUrl}
          onChange={(e) => setAvatarUrl(e.target.value)}
          placeholder="https://..."
        />
      </div>

      <div className="form-actions">
        <button type="submit" disabled={saving}>
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
        <button type="button" onClick={onCancel} disabled={saving}>
          Cancel
        </button>
      </div>
    </form>
  );
};
```

### Step 2.4: Component Testing

**React Testing Library:**
```typescript
// packages/frontend/src/components/UserProfile.test.tsx

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserProfile } from './UserProfile';
import { UserAPI } from '../types/api';

// Mock API
jest.mock('../types/api');

describe('UserProfile', () => {
  const mockProfile = {
    id: '550e8400-e29b-41d4-a716-446655440000',
    email: 'test@example.com',
    display_name: 'Test User',
    avatar_url: null,
    created_at: '2025-11-14T10:00:00Z',
    updated_at: '2025-11-14T10:00:00Z'
  };

  beforeEach(() => {
    (UserAPI.prototype.getProfile as jest.Mock).mockResolvedValue(mockProfile);
  });

  it('renders profile data', async () => {
    render(<UserProfile userId={mockProfile.id} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });
  });

  it('enters edit mode on edit button click', async () => {
    render(<UserProfile userId={mockProfile.id} />);
    
    await waitFor(() => screen.getByText('Test User'));
    
    const editButton = screen.getByText('Edit');
    await userEvent.click(editButton);
    
    expect(screen.getByLabelText('Display Name')).toBeInTheDocument();
  });

  it('saves profile changes', async () => {
    (UserAPI.prototype.updateProfile as jest.Mock).mockResolvedValue({
      ...mockProfile,
      display_name: 'Updated Name'
    });

    render(<UserProfile userId={mockProfile.id} />);
    
    await waitFor(() => screen.getByText('Test User'));
    
    // Click edit
    await userEvent.click(screen.getByText('Edit'));
    
    // Update name
    const nameInput = screen.getByLabelText('Display Name');
    await userEvent.clear(nameInput);
    await userEvent.type(nameInput, 'Updated Name');
    
    // Save
    await userEvent.click(screen.getByText('Save Changes'));
    
    // Verify API called
    expect(UserAPI.prototype.updateProfile).toHaveBeenCalledWith(
      mockProfile.id,
      { display_name: 'Updated Name', avatar_url: null }
    );
  });
});
```

### Step 2.5: Validate with E2B

**Goal:** Test component rendering in isolation

**E2B Component Test:**
```python
# Test React component compiles and renders
component_test = """
import React from 'react';
import { render } from '@testing-library/react';

// Inline component for testing
const TestComponent = () => (
  <div>
    <h1>User Profile</h1>
    <p>Test User</p>
  </div>
);

const { getByText } = render(<TestComponent />);
const heading = getByText('User Profile');
const name = getByText('Test User');

console.log('✅ Component renders successfully');
"""

# Run in E2B (with Node.js runtime)
executor = CodeExecutionPrimitive(runtime="node")
result = await executor.execute(
    {"code": component_test, "timeout": 30},
    context
)
```

### Step 2.6: Commit Frontend Work

```bash
git add packages/frontend/
git commit -m "feat(ui): add user profile components

- UserProfile component with view/edit modes
- EditProfileForm with validation
- TypeScript types from OpenAPI schema
- React Testing Library tests
- Integration with backend API
"

git push origin feature/user-profile-management
```

---

## Stage 3: E2E Testing (Testing Specialist Persona)

**Persona:** `tta-testing-specialist` (1500 tokens, 35 tools)  
**Duration:** ~1 hour  
**Deliverables:** E2E tests, accessibility validation, integration verification

### Activate Testing Persona

```bash
# Switch to testing persona
tta-persona testing

# Or via chatmode
/chatmode testing-specialist
```

**Verify tools:**
- ✅ Playwright MCP (E2E testing)
- ✅ GitHub MCP (PR review)
- ✅ Context7 (Playwright, accessibility docs)
- ✅ Sequential Thinking (test strategy)

### Step 3.1: E2E Test with Playwright

**Goal:** Test complete user flow

```typescript
// packages/frontend/tests/e2e/user-profile.spec.ts

import { test, expect } from '@playwright/test';

test.describe('User Profile Management', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to profile page
    await page.goto('/profile/550e8400-e29b-41d4-a716-446655440000');
  });

  test('displays user profile', async ({ page }) => {
    // Wait for profile to load
    await page.waitForSelector('.user-profile');
    
    // Verify profile data
    await expect(page.locator('h1')).toContainText('Test User');
    await expect(page.locator('.email')).toContainText('test@example.com');
  });

  test('edits user profile', async ({ page }) => {
    // Click edit button
    await page.click('button:has-text("Edit")');
    
    // Verify edit form visible
    await expect(page.locator('input#display_name')).toBeVisible();
    
    // Update display name
    await page.fill('input#display_name', 'Updated Name');
    
    // Save changes
    await page.click('button:has-text("Save Changes")');
    
    // Verify update reflected
    await expect(page.locator('h1')).toContainText('Updated Name');
  });

  test('validates form input', async ({ page }) => {
    await page.click('button:has-text("Edit")');
    
    // Try to submit with empty name
    await page.fill('input#display_name', '');
    await page.click('button:has-text("Save Changes")');
    
    // Verify validation message
    await expect(page.locator('input#display_name:invalid')).toBeVisible();
  });

  test('cancels edit', async ({ page }) => {
    await page.click('button:has-text("Edit")');
    await page.fill('input#display_name', 'Changed');
    
    // Cancel edit
    await page.click('button:has-text("Cancel")');
    
    // Verify original data still displayed
    await expect(page.locator('h1')).toContainText('Test User');
  });
});
```

**Run E2E tests:**
```bash
uv run playwright test packages/frontend/tests/e2e/
```

### Step 3.2: Accessibility Testing

**Goal:** Ensure WCAG compliance

```typescript
// packages/frontend/tests/e2e/accessibility.spec.ts

import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility', () => {
  test('profile page meets WCAG AA', async ({ page }) => {
    await page.goto('/profile/550e8400-e29b-41d4-a716-446655440000');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('edit form is keyboard accessible', async ({ page }) => {
    await page.goto('/profile/550e8400-e29b-41d4-a716-446655440000');
    
    // Tab to edit button
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');
    
    // Tab through form fields
    await page.keyboard.press('Tab'); // display_name
    await page.keyboard.press('Tab'); // avatar_url
    await page.keyboard.press('Tab'); // Save button
    
    // Verify focus visible
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toBe('BUTTON');
  });
});
```

### Step 3.3: Integration Testing

**Goal:** Verify full stack integration

```python
# Integration test using pytest + httpx + Playwright

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_stack_profile_update(test_db, api_client, playwright_page):
    """Test complete flow: API → Database → UI."""
    
    # Step 1: Create user in database
    user_id = uuid4()
    await test_db.users.insert_one({
        "id": user_id,
        "email": "integration@example.com",
        "display_name": "Integration Test",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    # Step 2: Load profile in UI
    await playwright_page.goto(f"/profile/{user_id}")
    await playwright_page.wait_for_selector('.user-profile')
    
    # Step 3: Edit profile via UI
    await playwright_page.click('button:has-text("Edit")')
    await playwright_page.fill('input#display_name', 'Updated Integration')
    await playwright_page.click('button:has-text("Save Changes")')
    
    # Step 4: Verify API call succeeded
    await playwright_page.wait_for_selector('h1:has-text("Updated Integration")')
    
    # Step 5: Verify database updated
    updated_user = await test_db.users.find_one({"id": user_id})
    assert updated_user["display_name"] == "Updated Integration"
```

### Step 3.4: Performance Testing

**Goal:** Ensure acceptable load times

```typescript
test('profile loads within 2 seconds', async ({ page }) => {
  const startTime = Date.now();
  
  await page.goto('/profile/550e8400-e29b-41d4-a716-446655440000');
  await page.waitForSelector('.user-profile');
  
  const loadTime = Date.now() - startTime;
  expect(loadTime).toBeLessThan(2000);
});
```

### Step 3.5: Quality Gate Review

**Goal:** Final approval before merge

**TTA Primitive Pattern:**
```python
from tta_dev_primitives import ConditionalPrimitive

# Quality gate check
quality_gate = ConditionalPrimitive(
    condition=lambda data, ctx: (
        data["backend_tests_passed"] and
        data["frontend_tests_passed"] and
        data["e2e_tests_passed"] and
        data["accessibility_passed"] and
        data["integration_tests_passed"]
    ),
    then_primitive=approve_pr,
    else_primitive=request_changes
)

# Execute
decision = await quality_gate.execute({
    "backend_tests_passed": True,
    "frontend_tests_passed": True,
    "e2e_tests_passed": True,
    "accessibility_passed": True,
    "integration_tests_passed": True
}, context)
```

**If approved:**
```bash
# Use GitHub MCP to approve PR
# Tool: mcp_github_github_update_pull_request

gh pr review --approve --body "✅ All quality gates passed:
- Backend tests: 100% coverage
- Frontend tests: All passing
- E2E tests: All scenarios covered
- Accessibility: WCAG AA compliant
- Integration tests: Full stack verified

Ready to merge!"
```

---

## Complete Workflow Orchestration

**Full multi-persona workflow:**

```python
"""
Multi-Persona Feature Development Workflow

Orchestrates backend → frontend → testing for full-stack features.
"""

import asyncio
from tta_dev_primitives import SequentialPrimitive, WorkflowContext
from tta_dev_primitives.performance import MemoryPrimitive

# Shared memory across personas
feature_memory = MemoryPrimitive(namespace="feature_user_profile")

# Stage 1: Backend - API Development
backend_workflow = SequentialPrimitive([
    design_api_contract_step,
    implement_endpoints_step,
    validate_with_e2b_step,
    write_backend_tests_step,
    generate_openapi_schema_step,
    commit_backend_work_step
])

# Stage 2: Frontend - UI Implementation
frontend_workflow = SequentialPrimitive([
    retrieve_api_contract_step,
    generate_typescript_types_step,
    create_react_components_step,
    write_component_tests_step,
    validate_components_e2b_step,
    commit_frontend_work_step
])

# Stage 3: Testing - E2E Validation
testing_workflow = SequentialPrimitive([
    run_e2e_tests_step,
    run_accessibility_tests_step,
    run_integration_tests_step,
    performance_testing_step,
    quality_gate_review_step
])

# Complete feature workflow
feature_workflow = SequentialPrimitive([
    backend_workflow,
    frontend_workflow,
    testing_workflow
])

# Execute
async def main():
    context = WorkflowContext(
        workflow_id="feature-user-profile-management",
        correlation_id="feature-2025-11-14",
        metadata={
            "personas": ["backend", "frontend", "testing"],
            "feature": "user-profile-management",
            "story": "USER-123"
        }
    )
    
    result = await feature_workflow.execute(
        {"action": "develop_feature", "feature_spec": "user_profile.md"},
        context
    )
    
    print(f"Feature complete: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Metrics and Observability

**Token Usage:**
- Backend persona: 1850 tokens (~92% budget)
- Frontend persona: 1620 tokens (~90% budget)
- Testing persona: 1380 tokens (~92% budget)

**Duration:**
- Backend: ~2 hours
- Frontend: ~2-3 hours
- Testing: ~1 hour
- **Total:** ~5-6 hours (vs 8-12 hours manual)

**Quality Metrics:**
- Backend test coverage: 100%
- Frontend test coverage: 95%
- E2E test scenarios: 5
- Accessibility: WCAG AA compliant
- Integration tests: Full stack validated

---

## Next Steps

- Merge feature PR
- Deploy to staging
- Monitor performance
- Gather user feedback
- Plan next iteration

---

**Workflow Status:** ✅ Production-Ready  
**Last Updated:** 2025-11-14  
**Personas Required:** Backend, Frontend, Testing  
**Estimated Time:** 5-6 hours (with automation) vs 8-12 hours (manual)
