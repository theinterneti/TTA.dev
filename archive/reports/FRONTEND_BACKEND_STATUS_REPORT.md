# TTA Frontend & Backend Status Report

**Date:** November 9, 2025
**Request:** Prove frontend with Google OAuth + backend connection

---

## 🔍 Current State Analysis

### ✅ What EXISTS

**Backend Story Generation Engine:**
- **Location:** `packages/tta-rebuild/`
- **Type:** Python library (pure backend, no web server)
- **Components:**
  - StoryGeneratorPrimitive (narrative generation)
  - CharacterDevelopmentPrimitive
  - TherapeuticContentPrimitive
  - LLM integrations (Anthropic, OpenAI, Gemini)
  - Long-term run management (proven with 310 turns)
  - Meta-progression system
  - Shared universe support

**Validation:**
- ✅ 128/131 tests passing (97.7%)
- ✅ 91% code coverage
- ✅ Gemini integration: 0.95 quality score
- ✅ Long-term runs: 150+ turns across 5 sessions
- ✅ Cost: $0.0005 per story

### ❌ What DOES NOT EXIST

**Frontend Application:**
- ❌ No React/Next.js/Vue components found
- ❌ No HTML/CSS/JavaScript files
- ❌ No package.json for frontend
- ❌ No UI components

**Web API Server:**
- ❌ No FastAPI/Flask/Django application
- ❌ No REST/GraphQL endpoints
- ❌ No authentication middleware
- ❌ No CORS configuration

**Google OAuth Integration:**
- ❌ No OAuth client configuration
- ❌ No Google Client ID/Secret setup
- ❌ No authentication flow
- ❌ No session management

**Frontend-Backend Connection:**
- ❌ No API client code
- ❌ No HTTP request handlers
- ❌ No authentication tokens

---

## 📊 Gap Analysis

### Current Architecture

```
┌─────────────────────────────────┐
│  TTA-Rebuild Python Library     │
│  ─────────────────────────────  │
│  ✅ StoryGeneratorPrimitive     │
│  ✅ LongTermRunManager          │
│  ✅ MetaProgressionManager      │
│  ✅ LLM Integrations            │
│  ✅ Test Suite (91% coverage)   │
└─────────────────────────────────┘
         ↑
         │ Python imports only
         │ (no web interface)
         ↓
    [No Frontend]
    [No API Server]
```

### Required Architecture

```
┌──────────────────────────┐
│  Frontend (Next.js)      │
│  ──────────────────────  │
│  🔨 Google OAuth Login   │
│  🔨 Player Dashboard     │
│  🔨 Character Manager    │
│  🔨 Story Viewer         │
│  🔨 Run Management       │
└──────────┬───────────────┘
           │ HTTPS/REST
           ↓
┌──────────────────────────┐
│  API Server (FastAPI)    │
│  ──────────────────────  │
│  🔨 /auth/google         │
│  🔨 /api/characters      │
│  🔨 /api/stories         │
│  🔨 /api/runs            │
│  🔨 JWT middleware       │
└──────────┬───────────────┘
           │ Python imports
           ↓
┌──────────────────────────┐
│  TTA-Rebuild Backend     │
│  ──────────────────────  │
│  ✅ StoryGenerator       │
│  ✅ LongTermRunManager   │
│  ✅ All validated        │
└──────────────────────────┘
```

---

## 🎯 What Needs to Be Built

### Phase 1: API Server (FastAPI)
**Estimated Time:** 4-6 hours

**Components:**
1. **Authentication Endpoints**
   - `POST /auth/google/login` - OAuth callback handler
   - `POST /auth/google/callback` - Token exchange
   - `GET /auth/me` - Current user info
   - `POST /auth/logout` - Session termination

2. **Game API Endpoints**
   - `GET /api/characters` - List user's characters
   - `POST /api/characters` - Create new character
   - `GET /api/characters/{id}` - Get character details
   - `POST /api/runs` - Start new run
   - `GET /api/runs/{id}` - Get run state
   - `PUT /api/runs/{id}` - Update run (save progress)
   - `POST /api/stories/generate` - Generate next story turn

3. **Middleware**
   - JWT token validation
   - CORS for frontend origin
   - Rate limiting
   - Error handling

**File Structure:**
```
packages/tta-api/
├── src/tta_api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── google_oauth.py  # Google OAuth flow
│   │   └── jwt_handler.py   # JWT tokens
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # Auth endpoints
│   │   ├── characters.py    # Character CRUD
│   │   ├── runs.py          # Run management
│   │   └── stories.py       # Story generation
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth.py          # JWT middleware
│   └── models/
│       ├── __init__.py
│       ├── user.py          # User model
│       ├── character.py     # Character model
│       └── run.py           # Run model
├── tests/
└── pyproject.toml
```

### Phase 2: Frontend Application (Next.js + TypeScript)
**Estimated Time:** 8-12 hours

**Components:**
1. **Authentication Pages**
   - `/login` - Google OAuth sign-in
   - `/callback` - OAuth redirect handler
   - Session management (JWT storage)

2. **Game Pages**
   - `/dashboard` - Player dashboard
   - `/characters` - Character list/create
   - `/characters/[id]` - Character details
   - `/runs/[id]` - Active run/story viewer
   - `/runs/[id]/play` - Interactive gameplay

3. **Components**
   - `GoogleSignIn` - OAuth button
   - `CharacterCard` - Character display
   - `StoryViewer` - Narrative display
   - `ChoiceSelector` - Player choices
   - `ProgressBar` - Run progress

**File Structure:**
```
apps/web/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx              # Landing page
│   │   ├── login/
│   │   │   └── page.tsx          # Google OAuth
│   │   ├── callback/
│   │   │   └── page.tsx          # OAuth redirect
│   │   ├── dashboard/
│   │   │   └── page.tsx          # Player dashboard
│   │   ├── characters/
│   │   │   ├── page.tsx          # Character list
│   │   │   └── [id]/page.tsx     # Character details
│   │   └── runs/
│   │       └── [id]/
│   │           ├── page.tsx      # Run viewer
│   │           └── play/page.tsx # Gameplay
│   ├── components/
│   │   ├── auth/
│   │   │   └── GoogleSignIn.tsx
│   │   ├── character/
│   │   │   ├── CharacterCard.tsx
│   │   │   └── CharacterForm.tsx
│   │   └── story/
│   │       ├── StoryViewer.tsx
│   │       └── ChoiceSelector.tsx
│   ├── lib/
│   │   ├── api.ts               # API client
│   │   └── auth.ts              # Auth helpers
│   └── types/
│       ├── character.ts
│       ├── run.ts
│       └── story.ts
├── public/
├── package.json
├── tsconfig.json
└── next.config.js
```

### Phase 3: Integration & Deployment
**Estimated Time:** 2-4 hours

**Tasks:**
1. Google OAuth setup (Google Cloud Console)
2. Environment variables configuration
3. Database setup (for user/run persistence)
4. API-Backend integration testing
5. End-to-end user flow testing
6. Production deployment

---

## 📋 Implementation Plan

### Week 1: API Server Foundation

**Day 1-2: Core API Setup**
- [ ] Create `tta-api` package
- [ ] Setup FastAPI application
- [ ] Configure Google OAuth 2.0
- [ ] Implement JWT authentication

**Day 3-4: Game Endpoints**
- [ ] Character CRUD endpoints
- [ ] Run management endpoints
- [ ] Story generation endpoint (integrates with tta-rebuild)

**Day 5: Testing & Documentation**
- [ ] API integration tests
- [ ] OpenAPI documentation
- [ ] Postman collection

### Week 2: Frontend Development

**Day 1-2: Authentication**
- [ ] Next.js project setup
- [ ] Google OAuth sign-in page
- [ ] OAuth callback handler
- [ ] Session management

**Day 3-4: Core UI**
- [ ] Player dashboard
- [ ] Character management
- [ ] Run list/viewer

**Day 5-7: Gameplay**
- [ ] Story viewer component
- [ ] Choice selection UI
- [ ] Run progression
- [ ] Save/resume functionality

### Week 3: Integration & Testing

**Day 1-2: Integration**
- [ ] Frontend ↔ API connection
- [ ] End-to-end user flow
- [ ] Error handling

**Day 3-5: Polish & Deploy**
- [ ] UI/UX improvements
- [ ] Performance optimization
- [ ] Production deployment
- [ ] User testing

---

## 🚀 Quick Start Option: Minimal Viable Product (MVP)

**Goal:** Working proof-of-concept in 1 day

### Simplified Architecture

```
Streamlit Frontend (Python)
    ↓
Google OAuth (streamlit-authenticator)
    ↓
Direct Import of tta-rebuild
    ↓
Local session state
```

**Why This Works:**
- ✅ Pure Python (no JavaScript needed)
- ✅ Built-in Google OAuth support
- ✅ Direct import of tta-rebuild backend
- ✅ Fast to build (~4 hours)
- ✅ Proves the concept immediately

**File Structure:**
```
apps/streamlit-mvp/
├── app.py                    # Main Streamlit app
├── auth.py                   # Google OAuth
├── pages/
│   ├── 1_Dashboard.py        # Player dashboard
│   ├── 2_Characters.py       # Character management
│   └── 3_Play.py             # Gameplay
├── components/
│   ├── character_form.py
│   └── story_viewer.py
└── requirements.txt
```

**MVP Implementation (4 hours):**

```python
# apps/streamlit-mvp/app.py
import streamlit as st
from streamlit_oauth import OAuth2Component
import os

# Google OAuth configuration
oauth2 = OAuth2Component(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    authorize_endpoint="https://accounts.google.com/o/oauth2/auth",
    token_endpoint="https://oauth2.googleapis.com/token",
)

# Page config
st.set_page_config(
    page_title="TTA - Therapeutic Through Artistry",
    page_icon="🎭",
    layout="wide"
)

# Authentication
if "user" not in st.session_state:
    st.title("🎭 Welcome to TTA")
    st.write("Sign in with Google to start your therapeutic storytelling journey")

    # Google Sign-In button
    result = oauth2.authorize_button(
        name="Sign in with Google",
        icon="https://www.google.com/favicon.ico",
        redirect_uri="http://localhost:8501",
        scope="openid email profile"
    )

    if result and "token" in result:
        # Store user info
        st.session_state.user = {
            "email": result.get("email"),
            "name": result.get("name"),
            "picture": result.get("picture")
        }
        st.rerun()
else:
    # Logged in - show main app
    user = st.session_state.user

    st.sidebar.title(f"👤 {user['name']}")
    st.sidebar.image(user['picture'], width=100)

    if st.sidebar.button("Sign Out"):
        del st.session_state.user
        st.rerun()

    # Main app navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Characters", "Play"]
    )

    if page == "Dashboard":
        st.title("📊 Your Dashboard")
        # Show stats, recent runs, etc.

    elif page == "Characters":
        st.title("🎭 Your Characters")
        # Character CRUD

    elif page == "Play":
        st.title("📖 Active Run")
        # Story viewer with TTA-rebuild integration
        from tta_rebuild.narrative import StoryGeneratorPrimitive
        # ... integrate backend here
```

---

## 🎯 Recommendation

### Option A: Full Production Stack (3 weeks)
**Pros:**
- Professional architecture
- Scalable
- Best user experience
- Production-ready

**Cons:**
- Longer development time
- More complex

### Option B: Streamlit MVP (1 day) ⭐ RECOMMENDED
**Pros:**
- ✅ **Working proof TODAY**
- ✅ Google OAuth integrated
- ✅ Direct backend connection
- ✅ Can iterate quickly

**Cons:**
- Less polished UI
- Not ideal for production scale
- Can migrate to Next.js later

---

## 🚦 Next Steps

### Immediate (Today):
1. **Choose approach** (Option A or Option B)
2. **Setup Google OAuth** (Google Cloud Console)
3. **Create first prototype**

### If Option B (Streamlit MVP):
```bash
# 1. Create Streamlit app
cd /home/thein/repos/TTA.dev
mkdir -p apps/streamlit-mvp
cd apps/streamlit-mvp

# 2. Install dependencies
uv pip install streamlit streamlit-oauth google-auth

# 3. Create app.py (code above)
# 4. Setup .env with Google credentials
# 5. Run: streamlit run app.py
```

### If Option A (Full Stack):
Follow the 3-week implementation plan above.

---

## 📝 Conclusion

**Current Status:**
- ✅ Backend: Production-ready (validated with 310 turns)
- ❌ Frontend: **Does not exist**
- ❌ API Server: **Does not exist**
- ❌ Google OAuth: **Not configured**

**To Prove Frontend Works:**
We need to **BUILD IT FIRST**.

I recommend **Option B (Streamlit MVP)** to get a working proof today, then migrate to Next.js if needed for production.

**Ready to start?** Let me know which option you prefer, and I'll help you build it.
