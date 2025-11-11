# N8N GitHub Health Dashboard Setup - Comprehensive Todo List

## Project Overview

**Goal:** Complete n8n GitHub Health Dashboard with automated 6-hour repository health monitoring for theinterneti/TTA.dev

**Target:** Functional dashboard with GitHub API integration and Gemini AI insights
**Estimated Time:** 30-45 minutes
**Current Status:** Infrastructure ready, manual configuration pending

---

## 📋 Complete Setup Checklist

### 🔧 Phase 1: Workflow Import into n8n Interface

- [ ] **1.1** Verify n8n service is running at <http://localhost:5678>
- [ ] **1.2** Open n8n web interface in browser
- [ ] **1.3** Create new workflow from dashboard
- [ ] **1.4** Access workflow import menu (three dots menu → Import from file)
- [ ] **1.5** Upload `/home/thein/repos/TTA.dev/n8n_github_health_dashboard.json`
- [ ] **1.6** Verify all nodes import correctly (Schedule, GitHub API, Gemini AI nodes)
- [ ] **1.7** Save imported workflow with name "GitHub Health Dashboard"
- [ ] **1.8** Check node connections and workflow structure

### 🔐 Phase 2: GitHub Personal Access Token Configuration

- [ ] **2.1** Navigate to GitHub.com and access Settings
- [ ] **2.2** Go to Developer settings → Personal access tokens → Tokens (classic)
- [ ] **2.3** Generate new token with scopes: `repo`, `read:org`, `user:email`
- [ ] **2.4** Copy generated token for n8n configuration
- [ ] **2.5** In n8n: Access Settings → Credentials
- [ ] **2.6** Create new GitHub API credential
- [ ] **2.7** Configure credential with name "GitHub API" and access token
- [ ] **2.8** Update all GitHub API nodes with new credential:
  - [ ] Get Repository Info node
  - [ ] Get Issues node
  - [ ] Get Pull Requests node
  - [ ] Get Contributors node
  - [ ] Get Commits node
- [ ] **2.9** Test GitHub API connectivity for each node
- [ ] **2.10** Verify repository data is accessible (theinterneti/TTA.dev)

### 🤖 Phase 3: Gemini API Key Environment Variable Setup

- [ ] **3.1** Obtain Gemini API key from Google AI Studio (<https://aistudio.google.com>)
- [ ] **3.2** Set environment variable: `export GEMINI_API_KEY="your_actual_gemini_api_key"`
- [ ] **3.3** Add GEMINI_API_KEY to system environment (persistent)
- [ ] **3.4** Restart n8n service to load environment variable
- [ ] **3.5** Verify API key accessibility in n8n workflow
- [ ] **3.6** Test Gemini AI connectivity in workflow
- [ ] **3.7** Confirm AI processing nodes can access API key

### 🧪 Phase 4: Manual Workflow Testing and Output Verification

- [ ] **4.1** Execute workflow manually via "Execute Workflow" button
- [ ] **4.2** Monitor execution logs for any errors or warnings
- [ ] **4.3** Verify health score calculation (0-100 scale with A-F grading)
- [ ] **4.4** Confirm repository metrics are populated:
  - [ ] Stars, forks, open issues count
  - [ ] Contributors list and activity
  - [ ] Pull requests and merge rates
  - [ ] Commit activity and frequency
- [ ] **4.5** Validate AI-powered insights generation from Gemini
- [ ] **4.6** Test recommendations and alerts creation
- [ ] **4.7** Verify automated scheduling configuration (6-hour intervals)
- [ ] **4.8** Check data accuracy and completeness in dashboard output
- [ ] **4.9** Review final dashboard formatting and readability

### 📊 Phase 5: Production Monitoring and Customization

- [ ] **5.1** Monitor first automated 6-hour scheduled run completion
- [ ] **5.2** Review automated execution results and logs
- [ ] **5.3** Customize health score thresholds in "Generate Final Dashboard" node
- [ ] **5.4** Configure alert conditions for specific repository issues
- [ ] **5.5** Set up notification system (email/Slack) if needed
- [ ] **5.6** Document any customizations for future reference
- [ ] **5.7** Perform final system validation check
- [ ] **5.8** Create monitoring dashboard or summary report

---

## 🎯 Success Criteria

**Fully Operational Dashboard Will Provide:**

- ✅ Repository health score (0-100) with letter grade (A-F)
- ✅ Community engagement analysis (contributors, activity trends)
- ✅ Code quality metrics (PR flow, issue resolution rates)
- ✅ AI-powered insights and actionable recommendations
- ✅ Automated alerts for repository health issues
- ✅ Regular 6-hour automated updates via n8n scheduling

---

## 🚨 Troubleshooting Checklist

**Monitor for Common Issues:**

- [ ] **GitHub API Rate Limits**: Check token permissions and API usage quotas
- [ ] **Gemini API Errors**: Verify API key validity, billing status, and quotas
- [ ] **Workflow Execution Failures**: Review node connections and credential configuration
- [ ] **Missing Data**: Confirm repository accessibility and proper API responses
- [ ] **Scheduling Issues**: Verify cron schedule configuration and n8n service status
- [ ] **Environment Variable Access**: Ensure GEMINI_API_KEY is accessible to n8n
- [ ] **Node Connection Problems**: Check workflow node linking and data flow

---

## 📁 Key File References

| File | Purpose | Status |
|------|---------|--------|
| `n8n_github_health_dashboard.json` | Main workflow file | ✅ Ready |
| `n8n_manual_setup_guide.md` | Step-by-step setup instructions | ✅ Available |
| `n8n_dashboard_completion_todo.md` | Detailed completion checklist | ✅ Available |
| `setup_n8n_github_dashboard.sh` | Automated setup script | ✅ Available |
| <http://localhost:5678> | n8n web interface | 🔄 Active |

---

## 🚀 Immediate Next Action

**Start with Phase 1:** Open <http://localhost:5678> in your browser and begin workflow import

**Command Reference:**

```bash
# Check n8n service status
sudo systemctl status n8n

# Set Gemini API key (if needed)
export GEMINI_API_KEY="your_actual_gemini_api_key"

# Restart n8n (if needed)
sudo systemctl restart n8n
```

---

**Created:** 2025-11-08 11:36 PM
**Last Updated:** 2025-11-08 11:36 PM
**Estimated Total Time:** 30-45 minutes
