# N8N GitHub Health Dashboard - Final Setup Checklist

## Current Status: Infrastructure Complete ✅

### ✅ Completed Infrastructure

- [x] n8n running on port 5678 (confirmed accessible via web interface)
- [x] Setup script made executable and tested
- [x] n8n web interface opened and ready for manual configuration
- [x] Complete workflow file analyzed and ready for import (`n8n_github_health_dashboard.json`)
- [x] Comprehensive setup guide created (`n8n_manual_setup_guide.md`)
- [x] Repository pre-configured for TTA.dev (`theinterneti/TTA.dev`)

## 🔧 Remaining Manual Configuration Steps

### Phase 1: Workflow Import

- [ ] **Import Workflow File**
  - Open n8n interface at <http://localhost:5678>
  - Create new workflow
  - Import `n8n_github_health_dashboard.json` via "..." menu
  - Verify all nodes are imported correctly

### Phase 2: GitHub API Configuration

- [ ] **Generate GitHub Personal Access Token**
  - Go to GitHub Settings > Developer settings > Personal access tokens
  - Create token with required scopes: `repo`, `read:org`, `user:email`
  - Copy token for use in n8n

- [ ] **Configure GitHub Credentials in n8n**
  - Open n8n Settings > Credentials
  - Add new "GitHub API" credential
  - Paste Personal Access Token
  - Save credential with descriptive name

- [ ] **Update Workflow GitHub Nodes**
  - Open imported workflow
  - For each GitHub API node (Get Repository Info, Get Issues, etc.)
  - Select newly created GitHub credential
  - Save each node configuration

### Phase 3: Gemini AI Configuration

- [ ] **Obtain Gemini API Key**
  - Visit Google AI Studio
  - Create new API key for Gemini
  - Copy API key for n8n configuration

- [ ] **Configure Gemini API in n8n**
  - Set environment variable: `export GEMINI_API_KEY="your_actual_gemini_api_key"`
  - Restart n8n service to load environment variable
  - Verify API key is accessible to workflow

### Phase 4: Testing & Validation

- [ ] **Manual Workflow Execution**
  - Open workflow in n8n
  - Click "Execute Workflow" button
  - Monitor execution logs for any errors

- [ ] **Verify Dashboard Output**
  - Check health score calculation (0-100)
  - Verify repository metrics are populated
  - Confirm AI-powered insights are generated
  - Review recommendations and alerts

- [ ] **Validate Automated Scheduling**
  - Verify 6-hour schedule is active
  - Test time-based trigger configuration
  - Confirm workflow runs on schedule

### Phase 5: Production Readiness

- [ ] **Monitor First Scheduled Run**
  - Allow first 6-hour cycle to complete
  - Review automated execution results
  - Check for any runtime errors

- [ ] **Customize Alert Thresholds**
  - Review "Generate Final Dashboard" node
  - Adjust health score thresholds if needed
  - Configure alert conditions for your needs

- [ ] **Final System Check**
  - Verify all integrations work correctly
  - Confirm data accuracy in dashboard
  - Test notification system (if applicable)

## 📊 Expected Dashboard Features

Once complete, the dashboard will provide:

- ✅ **Repository Health Score** with AI-calculated metrics
- ✅ **Community Engagement Analysis** (contributors, activity)
- ✅ **Code Quality Metrics** (PR flow, issue resolution)
- ✅ **AI-Powered Insights** and recommendations
- ✅ **Automated Alerts** for potential issues
- ✅ **6-Hour Automated Updates** via scheduling

## 🚨 Troubleshooting Checklist

If issues occur during setup:

- [ ] **GitHub API Rate Limits**: Check token permissions and usage
- [ ] **Gemini API Errors**: Verify API key and billing status
- [ ] **Workflow Execution Failures**: Review node connections and credentials
- [ ] **Missing Data**: Check repository accessibility and API responses

## 📋 Quick Reference

**Key Files:**

- Workflow: `/home/thein/repos/TTA.dev/n8n_github_health_dashboard.json`
- Guide: `/home/thein/repos/TTA.dev/n8n_manual_setup_guide.md`
- Script: `/home/thein/repos/TTA.dev/setup_n8n_github_dashboard.sh`

**Access Points:**

- n8n Interface: <http://localhost:5678>
- GitHub Token: Settings > Developer settings > Personal access tokens
- Gemini API: <https://aistudio.google.com>

---

**Next Action**: Begin with Phase 1 - Import the workflow file into n8n interface.
