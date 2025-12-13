# N8N Dashboard - Phases 2 & 3 Complete Setup Guide

## 📋 **Phase 2: GitHub Personal Access Token Configuration**

### **Step 2.1: Generate GitHub Personal Access Token**

1. **Go to GitHub.com** and sign in
2. **Navigate to Settings:**
   - Click your profile picture (top-right)
   - Select "Settings" from dropdown
3. **Access Developer Settings:**
   - Scroll to bottom of left sidebar
   - Click "Developer settings"
4. **Create Personal Access Token:**
   - Click "Personal access tokens"
   - Click "Tokens (classic)"
   - Click "Generate new token"
   - Click "Generate new token (classic)"
5. **Configure Token:**
   - **Note:** "n8n GitHub Health Dashboard"
   - **Expiration:** Choose your preference (30 days recommended for testing)
   - **Select scopes:** ✅ Check these boxes:
     - `repo` (Full control of private repositories)
     - `read:org` (Read org and team membership)
     - `user:email` (Access commits user email)
6. **Generate & Copy:**
   - Click "Generate token" at bottom
   - **⚠️ IMPORTANT:** Copy the token immediately (you won't see it again)
   - Save it somewhere secure

### **Step 2.2: Configure in n8n**

1. **Open n8n:** <http://localhost:5678>
2. **Access Credentials:**
   - Click gear icon (⚙️) in top-left
   - Select "Credentials"
3. **Create GitHub Credential:**
   - Click "Add Credential"
   - Search for "GitHub API"
   - Click "GitHub API"
4. **Configure:**
   - **Name:** "GitHub API - TTA Dashboard"
   - **Access Token:** Paste your generated token
   - Click "Save"
5. **Update Workflow Nodes:**
   - Open your imported "GitHub Health Dashboard" workflow
   - **For each GitHub API node:**
     - Click the node
     - In "Credentials" dropdown, select "GitHub API - TTA Dashboard"
     - Click "Update" or "Save"
   - **Nodes to update:**
     - ✅ Get Repository Info
     - ✅ Get Issues
     - ✅ Get Pull Requests
     - ✅ Get Contributors
     - ✅ Get Commits

### **Step 2.3: Test Connectivity**

1. **Individual Node Testing:**
   - Click each GitHub API node
   - Click "Execute Node"
   - Should return data for "theinterneti/TTA.dev"
2. **Verify Data:**
   - Repository info shows stars, forks, issues count
   - Issues shows recent GitHub issues
   - Contributors shows team members

---

## 🤖 **Phase 3: Gemini API Key Environment Variable Setup**

### **Step 3.1: Obtain Gemini API Key**

Since you already have the `gemini_provider.py` file, you likely have access to a Gemini API key. If not:

1. **Go to Google AI Studio:** <https://aistudio.google.com>
2. **Sign in** with your Google account
3. **Create API Key:**
   - Click "Get API key" in left sidebar
   - Click "Create API key"
   - Select your Google Cloud project (or create new one)
   - Copy the generated API key

### **Step 3.2: Set Environment Variable**

**Option A: Temporary (Current Session Only)**

```bash
export GEMINI_API_KEY="your_actual_gemini_api_key_here"
```

**Option B: Permanent (Recommended)**

```bash
# Add to your .bashrc or .zshrc
echo 'export GEMINI_API_KEY="your_actual_gemini_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

**Option C: Using existing .env file**

```bash
# If you have a .env file in the project
echo "GEMINI_API_KEY=your_actual_gemini_api_key_here" >> .env
```

### **Step 3.3: Restart n8n to Load Environment Variable**

```bash
# Kill existing n8n process
pkill -f "n8n"

# Start n8n again (it will load the new environment variable)
npm exec n8n
```

### **Step 3.4: Test Gemini Integration**

1. **Verify API Key Access:**

   ```bash
   echo $GEMINI_API_KEY
   # Should output your API key
   ```

2. **Test in n8n:**
   - Open the workflow
   - Click the "Analyze with Gemini" node
   - Click "Execute Node"
   - Should generate AI insights

---

## ✅ **Verification Checklist**

### **Phase 2 Verification:**

- [ ] GitHub PAT created with correct scopes
- [ ] n8n credential configured
- [ ] All 5 GitHub API nodes updated
- [ ] Each node returns data when executed individually
- [ ] Can access "theinterneti/TTA.dev" repository data

### **Phase 3 Verification:**

- [ ] GEMINI_API_KEY environment variable set
- [ ] n8n service restarted
- [ ] "Analyze with Gemini" node executes successfully
- [ ] AI insights generated without errors

---

## 🚨 **Troubleshooting**

### **Common GitHub API Issues:**

- **"Bad credentials"** → Check token validity and scopes
- **"Repository not found"** → Verify repository name "theinterneti/TTA.dev"
- **"Rate limit exceeded"** → GitHub API rate limits (60 requests/hour for unauthenticated)

### **Common Gemini API Issues:**

- **"API key not found"** → Verify GEMINI_API_KEY environment variable
- **"Quota exceeded"** → Check Google Cloud billing
- **"Invalid request"** → Verify API key permissions

---

## 🎯 **Next Steps After Phases 2 & 3**

Once both phases are complete:

1. **Proceed to Phase 4:** Manual workflow testing
2. **Execute full workflow** and verify output
3. **Check all nodes execute successfully**
4. **Review generated health dashboard**

---

**Created:** 2025-11-08 11:39 PM
**Ready for:** Phases 2 & 3 execution
**Estimated Time:** 10-15 minutes for both phases


---
**Logseq:** [[TTA.dev/_archive/Historical/Phases_2_3_complete_setup]]
