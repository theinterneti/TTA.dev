# N8N GitHub Health Dashboard - Manual Setup Guide

## Current Status
✅ **n8n running on port 5678**
✅ **Workflow file ready: `n8n_github_health_dashboard.json`**
✅ **Repository configured: theinterneti/TTA.dev**
⚠️ **Need GitHub API credentials and Gemini API key**

## Manual Setup Steps

### Step 1: Import Workflow in n8n

1. **Open n8n in browser** (already running at http://localhost:5678)
2. **Create new workflow**:
   - Click "New workflow" button
   - Click the "..." menu in the top-right
   - Select "Import from file"
   - Upload `n8n_github_health_dashboard.json`
   - Click "Import"

### Step 2: Configure GitHub API Credentials

1. **Go to Settings**:
   - Click gear icon in top-left corner
   - Select "Credentials"

2. **Create GitHub API Credential**:
   - Click "Add Credential"
   - Search for "GitHub API"
   - Configure:
     - **Name**: "GitHub API" (or any descriptive name)
     - **Access Token**: [Your GitHub Personal Access Token]
   - Save credential

3. **Update Workflow Nodes**:
   - Open the imported workflow
   - For each GitHub API node (Get Repository Info, Get Issues, etc.):
     - Click the node
     - In credentials section, select your newly created GitHub API credential
     - Save the node

### Step 3: Set Up Gemini API Key

1. **Set Environment Variable**:
   ```bash
   export GEMINI_API_KEY="your_actual_gemini_api_key"
   ```

2. **Restart n8n** (or add the environment variable to n8n's environment)

### Step 4: Test the Workflow

1. **Manual Execution**:
   - Open the workflow in n8n
   - Click "Execute Workflow" button
   - Monitor the execution results

2. **Expected Output**:
   - Health score (0-100)
   - Repository metrics
   - AI-powered insights
   - Recommendations and alerts

## Workflow Overview

The dashboard analyzes:
- **Repository Health**: Stars, forks, open issues
- **Community Engagement**: Contributors, commit activity
- **Code Quality**: PR flow, issue resolution time
- **AI Analysis**: Gemini-powered insights and recommendations

## Key Features

- **Automated Scheduling**: Runs every 6 hours
- **Health Score Calculation**: AI-calculated health metrics
- **Trend Analysis**: Recent activity and velocity tracking
- **Actionable Insights**: AI-generated recommendations
- **Alert System**: Automatic issue detection

## Troubleshooting

### Common Issues:

1. **GitHub API Rate Limits**:
   - Ensure your token has proper permissions
   - Consider implementing rate limiting in the workflow

2. **Gemini API Errors**:
   - Verify the API key is correct
   - Check API quotas and billing

3. **Workflow Execution Fails**:
   - Check node connections
   - Verify all credentials are properly configured
   - Review execution logs for specific errors

## Next Steps

After successful setup:
1. **Monitor First Execution**: Check that all nodes execute without errors
2. **Review Dashboard Output**: Ensure all metrics are calculated correctly
3. **Schedule Automation**: Let the 6-hour schedule run automatically
4. **Customize Alerts**: Modify threshold values in the "Generate Final Dashboard" node

## File Locations

- **Workflow File**: `/home/thein/repos/TTA.dev/n8n_github_health_dashboard.json`
- **Setup Script**: `/home/thein/repos/TTA.dev/setup_n8n_github_dashboard.sh`
- **Documentation**: `/home/thein/repos/TTA.dev/N8N_GITHUB_DASHBOARD_GUIDE.md`
