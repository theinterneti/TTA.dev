# TTA Streamlit MVP

A simple web interface for the TTA (Therapeutic Through Artistry) story generation system.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd apps/streamlit-mvp
uv pip install -r requirements.txt
```

### 2. Configure Environment (Optional)

If you want to use the real Gemini backend:

```bash
# Copy from root .env.template
cp ../../.env.template .env

# Edit .env and add your Gemini API key
nano .env
```

### 3. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📱 Features

### Current (MVP)
- ✅ **Simulated Google OAuth** - Email-based login for demonstration
- ✅ **Character Creation** - Create therapeutic story characters
- ✅ **Story Generation** - Interactive storytelling with choices
- ✅ **Dashboard** - View stats and progress
- ✅ **Direct Backend Integration** - Uses TTA-Rebuild package

### Coming Soon
- 🔲 Real Google OAuth integration
- 🔲 Persistent storage (database)
- 🔲 Multi-run management
- 🔲 Character library
- 🔲 Story export/sharing

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│   Streamlit Frontend (app.py)   │
│                                 │
│  - Login page                   │
│  - Character creation           │
│  - Story viewer                 │
│  - Dashboard                    │
└────────────┬────────────────────┘
             │
             │ Direct import
             ↓
┌─────────────────────────────────┐
│  TTA-Rebuild Backend            │
│  (packages/tta-rebuild)         │
│                                 │
│  - StoryGeneratorPrimitive      │
│  - CharacterDevelopmentPrimitive│
│  - GeminiLLMProvider            │
└─────────────────────────────────┘
```

## 🎮 Usage

### 1. Login
- Enter any email address (simulated auth)
- Click "Sign In with Google (Simulated)"

### 2. Create Character
- Navigate to "Create Character"
- Fill in character details:
  - Name
  - Archetype
  - Backstory
  - Therapeutic themes

### 3. Play Story
- Navigate to "Play Story"
- Click "Begin Your Journey"
- Make choices to progress the story
- Watch your character level up!

## 🔧 Development

### Folder Structure

```
apps/streamlit-mvp/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── .env               # Environment variables (create from .env.template)
```

### Adding Real Google OAuth

To add real Google OAuth (for production):

1. **Install OAuth library:**
   ```bash
   uv pip install streamlit-oauth google-auth
   ```

2. **Get Google OAuth credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a project
   - Enable Google+ API
   - Create OAuth 2.0 credentials
   - Add authorized redirect URI: `http://localhost:8501`

3. **Update .env:**
   ```
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   ```

4. **Update app.py** to use real OAuth (code commented in the file)

### Connecting to Real Backend

The app already imports from TTA-Rebuild. To use the real Gemini LLM:

1. **Set Gemini API key** in `.env`:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

2. The app will automatically use it when generating stories!

## 🐛 Troubleshooting

### "Module not found" error

Make sure you're in the TTA.dev repository and tta-rebuild is installed:

```bash
cd /home/thein/repos/TTA.dev
uv pip install -e packages/tta-rebuild
```

### Backend not generating stories

The app has a fallback mode if Gemini isn't configured. To enable real story generation:

1. Add `GEMINI_API_KEY` to `.env`
2. Restart the Streamlit app

### Port already in use

If port 8501 is busy:

```bash
streamlit run app.py --server.port 8502
```

## 📝 Next Steps

### To migrate to production (Next.js):

This MVP proves the concept. For production, consider:

1. **Next.js frontend** - Better performance and SEO
2. **FastAPI backend** - Proper API layer
3. **PostgreSQL** - Persistent database
4. **Real OAuth** - Google sign-in with secure tokens
5. **Deployment** - Vercel (frontend) + Railway (backend)

See `FRONTEND_BACKEND_STATUS_REPORT.md` for the full implementation plan.

## 🎯 MVP Scope

**What this MVP proves:**
- ✅ Frontend UI works
- ✅ Character creation works
- ✅ Story generation works
- ✅ Backend integration works
- ✅ User can interact with the system

**What's still needed for production:**
- Real Google OAuth
- Database persistence
- API server layer
- Production deployment
- Multi-user support
- Security hardening

---

**Built with ❤️ for TTA - Therapeutic Through Artistry**
