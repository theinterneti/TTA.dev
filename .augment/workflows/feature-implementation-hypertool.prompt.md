---
hypertool_enabled: true
workflow_type: multi_persona
workflow_name: feature_implementation_hypertool
version: 1.0.0
personas:
  - backend-engineer
  - frontend-engineer
  - testing-specialist
token_budget:
  backend-engineer: 2000
  frontend-engineer: 1800
  testing-specialist: 1500
  total_estimated: 5300
apm_enabled: true
quality_gates:
  - code_review_passed
  - tests_passing
  - security_scan_clean
---

# Multi-Persona Workflow: Feature Implementation with Hypertool

**Purpose:** Implement a new feature using optimal persona switching for each task phase

**APM Integration:** This workflow is instrumented with PersonaMetricsCollector and WorkflowTracer for complete observability

---

## Workflow Overview

This workflow demonstrates how to use Hypertool's multi-persona system to efficiently implement a new feature by switching between personas based on task requirements.

**Personas Used:**
1. **Backend Engineer** (2000 tokens) - API design, data models, business logic
2. **Frontend Engineer** (1800 tokens) - UI components, state management, user experience
3. **Testing Specialist** (1500 tokens) - Test strategy, test implementation, quality validation

**Expected Duration:** 5-6 hours (vs 8-12 hours without persona optimization)
**Token Savings:** ~40% compared to single-persona approach

---

## Stage 1: API Design & Data Models

**Active Persona:** `backend-engineer` (Token Budget: 2000)

**Hypertool Command:**
```bash
tta-persona switch backend-engineer --chatmode feature-implementation
```

**Objectives:**
- Design RESTful API endpoints
- Create Pydantic data models
- Define database schema (if needed)
- Plan integration points

**Quality Gate:** API design reviewed, models validated

**APM Tracking:**
```python
# Automatically tracked by WorkflowTracer
# Metrics: stage duration, token usage, quality gate status
```

**Tasks:**
1. Analyze feature requirements
2. Design API endpoint structure
3. Create Pydantic models for request/response
4. Define database migrations (if applicable)
5. Document API contracts

**MCP Tools Available (via Hypertool):**
- `mcp_context7_get-library-docs` - FastAPI, Pydantic documentation
- `mcp_pylance_mcp_s_pylanceRunCodeSnippet` - Test model definitions
- `mcp_github_github_create_branch` - Create feature branch

**Example Implementation:**
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class FeatureRequest(BaseModel):
    """Feature request data model."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    priority: str = Field(..., regex="^(low|medium|high|critical)$")
    tags: List[str] = Field(default_factory=list)
    
class FeatureResponse(BaseModel):
    """Feature response data model."""
    id: str
    title: str
    description: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
```

**Quality Checklist:**
- [ ] API endpoints follow RESTful conventions
- [ ] Pydantic models have proper validation
- [ ] Database schema supports all requirements
- [ ] API documentation generated
- [ ] Integration points identified

**Expected Token Usage:** ~800 tokens  
**Remaining Budget:** 1200 tokens

---

## Stage 2: Frontend Components & State Management

**Persona Switch:** `backend-engineer` → `frontend-engineer`

**Hypertool Command:**
```bash
tta-persona switch frontend-engineer --chatmode feature-implementation
```

**Objectives:**
- Create React/Vue components
- Implement state management
- Connect to backend API
- Design user interactions

**Quality Gate:** Components rendering correctly, state management working

**Tasks:**
1. Create component structure
2. Implement API client
3. Add state management (Redux/Zustand/Pinia)
4. Build UI with TailwindCSS
5. Add form validation

**MCP Tools Available (via Hypertool):**
- `mcp_context7_get-library-docs` - React, Vue, TailwindCSS
- `mcp_pylance_mcp_s_pylanceRunCodeSnippet` - Test component logic
- `mcp_github_github_push_files` - Commit component files

**Example Implementation:**
```typescript
// Feature component with state management
import { useState } from 'react';
import { useFeatureAPI } from '@/api/features';

interface FeatureFormProps {
  onSuccess: () => void;
}

export function FeatureForm({ onSuccess }: FeatureFormProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');
  
  const { createFeature, isLoading } = useFeatureAPI();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const result = await createFeature({
      title,
      description,
      priority,
      tags: []
    });
    
    if (result.success) {
      onSuccess();
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Form fields */}
    </form>
  );
}
```

**Quality Checklist:**
- [ ] Components follow design system
- [ ] State management implemented correctly
- [ ] API integration working
- [ ] Form validation complete
- [ ] Responsive design tested

**Expected Token Usage:** ~900 tokens  
**Remaining Budget:** 900 tokens

---

## Stage 3: Testing & Quality Validation

**Persona Switch:** `frontend-engineer` → `testing-specialist`

**Hypertool Command:**
```bash
tta-persona switch testing-specialist --chatmode feature-implementation
```

**Objectives:**
- Write comprehensive tests
- Validate all quality gates
- Run security scans
- Performance testing

**Quality Gate:** All tests passing, 80%+ coverage, security scan clean

**Tasks:**
1. Write unit tests for API endpoints
2. Write unit tests for React components
3. Create integration tests
4. Run E2E tests with Playwright
5. Security scan with Bandit/ESLint
6. Performance testing

**MCP Tools Available (via Hypertool):**
- `mcp_pylance_mcp_s_pylanceRunCodeSnippet` - Run pytest
- `mcp_github_github_create_pull_request` - Open PR
- `mcp_github_github_request_copilot_review` - Request AI review

**Example Implementation:**
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_feature():
    """Test feature creation endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/features",
            json={
                "title": "New Feature",
                "description": "Feature description here",
                "priority": "high",
                "tags": ["enhancement"]
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Feature"
        assert data["priority"] == "high"
        assert "id" in data

@pytest.mark.asyncio
async def test_feature_validation():
    """Test input validation."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test missing required fields
        response = await client.post("/api/features", json={})
        assert response.status_code == 422
        
        # Test invalid priority
        response = await client.post(
            "/api/features",
            json={"title": "Test", "description": "Test", "priority": "invalid"}
        )
        assert response.status_code == 422
```

**Quality Checklist:**
- [ ] Unit tests cover all new code
- [ ] Integration tests validate workflows
- [ ] E2E tests cover user journeys
- [ ] Code coverage >80%
- [ ] Security scan passed
- [ ] Performance benchmarks met

**Expected Token Usage:** ~700 tokens  
**Remaining Budget:** 800 tokens

---

## Workflow Summary & Metrics

**Total Token Usage:** ~2400 tokens (estimated)  
**Token Savings:** ~1900 tokens vs single-persona approach  
**Time Savings:** 3-6 hours vs traditional approach

**APM Metrics Captured:**
- Persona switches: 2 (backend→frontend→testing)
- Stage durations: Stage 1 (API), Stage 2 (Frontend), Stage 3 (Testing)
- Token usage per persona
- Quality gate pass/fail rates

**View Metrics:**
```bash
# Prometheus metrics
curl http://localhost:9464/metrics | grep hypertool_persona

# Grafana dashboards
open http://localhost:3000/d/hypertool-persona-overview
```

**Next Steps:**
1. Create pull request
2. Request Copilot review
3. Address review comments
4. Merge to main
5. Deploy to staging

---

## Troubleshooting

**Persona switch failed:**
```bash
# Check current persona
tta-persona status

# Force switch
tta-persona switch <persona-name> --force
```

**Token budget exceeded:**
```bash
# Check remaining budget
tta-persona budget --persona <persona-name>

# Reset budget (dev only)
tta-persona budget --reset <persona-name>
```

**Quality gate failed:**
- Review test output
- Check code coverage reports
- Run security scan locally: `uvx bandit -r src/`
- Fix issues and re-run tests

---

**Workflow Version:** 1.0.0  
**Last Updated:** 2025-11-15  
**Maintained by:** TTA.dev Team
