# n8n Expert Setup Guide for TTA.dev

**Your Complete Guide to n8n Automation Success** 🚀

## 🎯 What We're Building

n8n workflows for **git automation** with Cline, including:

- Automated GitHub repository monitoring
- AI-powered health analytics
- Commit automation
- PR management
- Issue tracking

## 📋 Prerequisites Checklist

### 1. n8n Installation Status

- ✅ n8n installed
- ✅ Running on <http://localhost:5678>
- ⚠️ Need to configure credentials

### 2. Required API Keys

You need these API keys (we'll show you how to get each):

| Service | Key Name | Purpose | Where to Get |
|---------|----------|---------|--------------|
| GitHub | `GITHUB_PERSONAL_ACCESS_TOKEN` | Repository access | [Create Token](#github-token) |
| Google Gemini | `GEMINI_API_KEY` | AI analysis | [Get API Key](#gemini-api) |
| E2B | `E2B_API_KEY` | Code execution (optional) | [Get API Key](#e2b-api) |
| n8n | `N8N_API_KEY` | n8n API access | [Generate Key](#n8n-api) |

---

## 🔑 Step 1: Get Your API Keys

### <a name="github-token"></a>GitHub Personal Access Token

1. **Go to GitHub Settings**:
   - Visit: <https://github.com/settings/tokens>
   - Or: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)

2. **Generate new token**:
   - Click "Generate new token (classic)"
   - Name: `n8n-tta-dev-automation`
   - Expiration: Choose based on your needs (90 days recommended)

3. **Select scopes** (permissions):

   ```
   ✅ repo (Full control of private repositories)
      ✅ repo:status
      ✅ repo_deployment
      ✅ public_repo
      ✅ repo:invite
      ✅ security_events
   ✅ workflow (Update GitHub Action workflows)
   ✅ write:packages
   ✅ read:packages
   ✅ delete:packages
   ✅ admin:repo_hook
   ✅ admin:org_hook
   ✅ read:org
   ✅ read:user
   ✅ user:email
   ```

4. **Generate and save**:
   - Click "Generate token"
   - **⚠️ COPY IT NOW** - You won't see it again!
   - Format: `ghp_YOUR_GITHUB_TOKEN_HERE`

### <a name="gemini-api"></a>Google Gemini API Key

1. **Go to Google AI Studio**:
   - Visit: <https://makersuite.google.com/app/apikey>
   - Sign in with your Google account

2. **Create API key**:
   - Click "Get API key"
   - Choose "Create API key in new project" (or existing)
   - Copy the key
   - Format: `AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

3. **Important notes**:
   - Free tier: 60 requests per minute
   - Good for testing and development
   - Upgrade for production use

### <a name="e2b-api"></a>E2B API Key (Optional for Code Execution)

1. **Go to E2B Dashboard**:
   - Visit: <https://e2b.dev/>
   - Sign up/login

2. **Get API key**:
   - Go to Settings → API Keys
   - Click "Create new API key"
   - Copy the key
   - Format: `e2b_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### <a name="n8n-api"></a>n8n API Key

1. **In n8n interface** (<http://localhost:5678>):
   - Go to Settings (gear icon)
   - Select "API"
   - Click "Create an API key"
   - Name: `local-automation`
   - Copy the key
   - Format: `n8n_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## 🔧 Step 2: Configure Your Environment

### Option A: Using .env File (Recommended)

1. **Copy the template**:

   ```bash
   cd /home/thein/repos/TTA.dev
   cp .env.template .env
   ```

2. **Edit .env file**:

   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Add your API keys**:

   ```bash
   # GitHub Configuration
   GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_actual_token_here

   # Google Gemini AI
   GEMINI_API_KEY=AIzaSy_your_actual_key_here

   # E2B Code Execution (optional)
   E2B_API_KEY=e2b_your_actual_key_here

   # n8n API
   N8N_API_KEY=n8n_api_your_actual_key_here

   # n8n Configuration
   N8N_HOST=localhost
   N8N_PORT=5678
   N8N_PROTOCOL=http
   ```

4. **Verify .gitignore**:

   ```bash
   # Make sure .env is in .gitignore
   grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore
   ```

### Option B: Export Environment Variables (Temporary)

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_your_token"
export GEMINI_API_KEY="AIzaSy_your_key"
export E2B_API_KEY="e2b_your_key"
export N8N_API_KEY="n8n_api_your_key"
```

---

## 🚀 Step 3: Start n8n with Environment Variables

### If using .env file

1. **Load environment variables**:

   ```bash
   cd /home/thein/repos/TTA.dev
   export $(grep -v '^#' .env | xargs)
   ```

2. **Start n8n**:

   ```bash
   npx n8n
   ```

### Alternative: Start with inline environment

```bash
GITHUB_PERSONAL_ACCESS_TOKEN="ghp_xxx" \
GEMINI_API_KEY="AIzaSy_xxx" \
E2B_API_KEY="e2b_xxx" \
N8N_API_KEY="n8n_api_xxx" \
npx n8n
```

---

## 📥 Step 4: Import & Configure the GitHub Health Dashboard

### 4.1 Import the Workflow

1. **Open n8n**: <http://localhost:5678>
2. **Create new workflow**: Click "+ Add workflow" or "New"
3. **Import JSON**:
   - Click the "..." menu (top-right)
   - Select "Import from file"
   - Choose: `/home/thein/repos/TTA.dev/n8n_github_health_dashboard.json`
   - Click "Import"

### 4.2 Configure GitHub Credentials in n8n

1. **Go to Credentials**:
   - Click the gear icon (Settings)
   - Select "Credentials"

2. **Add GitHub API credential**:
   - Click "+ Add credential"
   - Search for "GitHub API"
   - Select "GitHub API"

3. **Configure**:
   - **Credential name**: `GitHub API - TTA.dev`
   - **Access Token**: Paste your `GITHUB_PERSONAL_ACCESS_TOKEN`
   - Click "Create"

### 4.3 Update Workflow Nodes

1. **Open the imported workflow**
2. **For each GitHub node** (there are several):
   - Click the node
   - In the "Credentials" dropdown, select: `GitHub API - TTA.dev`
   - Save the node

3. **Nodes to update**:
   - `Get Repository Info`
   - `Get Issues`
   - `Get Pull Requests`
   - `Get Contributors`
   - `Get Commit Activity`

### 4.4 Configure Gemini API

The Gemini API key should be available via environment variable. Verify:

1. **Check the "AI Analysis" node**
2. **Verify** it references `{{$env.GEMINI_API_KEY}}`
3. **Test** by executing the workflow

---

## 🧪 Step 5: Test Your Setup

### 5.1 Validate Secrets

```bash
cd /home/thein/repos/TTA.dev
python scripts/validate_secrets.py
```

**Expected output**:

```
✅ PASSED: All required secrets are present
```

### 5.2 Test n8n Workflow

1. **In n8n interface**:
   - Open your GitHub Health Dashboard workflow
   - Click "Execute Workflow" button (top-right)
   - Watch the execution progress

2. **Check results**:
   - All nodes should turn green ✅
   - Review output data in each node
   - Check for any error messages

### 5.3 Verify Output

Look for:

- ✅ Repository metrics fetched
- ✅ Health score calculated
- ✅ AI insights generated
- ✅ Recommendations provided

---

## 🔨 Step 6: Set Up Git Automation with Cline

### 6.1 Create Git Automation Workflow

Now let's build a workflow for **git automation** with Cline:

**What it will do**:

- Monitor file changes
- Auto-commit with AI-generated messages
- Create pull requests
- Manage branches
- Run tests before commits

### 6.2 Workflow Design

```mermaid
graph LR
    A[Watch Files] --> B[Detect Changes]
    B --> C[AI: Generate Commit Message]
    C --> D[Git Add & Commit]
    D --> E[Run Tests]
    E --> F{Tests Pass?}
    F -->|Yes| G[Push to Branch]
    F -->|No| H[Rollback]
    G --> I[Create PR]
```

Would you like me to create this workflow?

---

## 🐛 Troubleshooting

### Issue: "Missing API keys"

**Solution**:

1. Check .env file exists: `ls -la .env`
2. Verify keys are set: `echo $GITHUB_PERSONAL_ACCESS_TOKEN`
3. Restart n8n after setting environment variables

### Issue: "GitHub API rate limit"

**Solution**:

- Use authenticated requests (token provides 5000 req/hour)
- Check rate limit: `curl -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" https://api.github.com/rate_limit`

### Issue: "Gemini API errors"

**Solution**:

- Verify API key is correct
- Check quota: <https://makersuite.google.com/app/apikey>
- Ensure billing is enabled for production use

### Issue: "n8n workflow execution fails"

**Solution**:

1. Check node connections (arrows between nodes)
2. Verify credentials are selected in each node
3. Review execution logs for specific errors
4. Test each node individually

### Issue: "Cline git automation not working"

**Solution**:

- Check Cline has git permissions
- Verify .gitconfig is set up
- Ensure working directory is correct
- Review Cline logs for errors

---

## 📚 Next Steps

### 1. Create Git Automation Workflow

I can help you create a custom n8n workflow for:

- [ ] Automated commits
- [ ] PR creation
- [ ] Branch management
- [ ] Test automation
- [ ] Code review triggers

### 2. Advanced Features

Once basic setup works:

- [ ] Webhook triggers for real-time automation
- [ ] Scheduled tasks (cron)
- [ ] Multi-repository support
- [ ] Custom AI prompts
- [ ] Slack/Discord notifications

### 3. Integration with TTA.dev

- [ ] Connect to TTA.dev primitives
- [ ] Use workflow orchestration
- [ ] Add observability
- [ ] Implement error handling

---

## 🎓 Learning Resources

### n8n Basics

- **Official Docs**: <https://docs.n8n.io/>
- **Community**: <https://community.n8n.io/>
- **Workflows Library**: <https://n8n.io/workflows/>

### Git Automation

- **GitHub API**: <https://docs.github.com/en/rest>
- **Git Hooks**: <https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks>
- **Automation Patterns**: <https://docs.n8n.io/integrations/builtin/core-nodes/>

### Best Practices

- Use error handling nodes
- Implement retry logic
- Add logging for debugging
- Test in development first
- Version control your workflows (export JSON)

---

## 💡 Pro Tips

1. **Workflow Organization**:
   - Use clear node names
   - Add notes to complex nodes
   - Group related operations
   - Use sticky notes for documentation

2. **Security**:
   - Never hardcode API keys
   - Use environment variables
   - Limit token permissions
   - Rotate keys regularly

3. **Performance**:
   - Batch operations when possible
   - Use caching for repeated data
   - Implement rate limiting
   - Monitor execution times

4. **Debugging**:
   - Use "Execute Workflow" for testing
   - Check each node's output
   - Use "Execute Previous Nodes" feature
   - Enable debug mode for detailed logs

---

## 🆘 Getting Help

**Ready to proceed?** Tell me:

1. Have you obtained all API keys? (GitHub, Gemini, etc.)
2. Which git automation features do you want first?
3. Any specific errors you're seeing with Cline?

I'll guide you through each step! 🚀


---
**Logseq:** [[TTA.dev/Apps/N8n/N8n_expert_setup_guide]]
