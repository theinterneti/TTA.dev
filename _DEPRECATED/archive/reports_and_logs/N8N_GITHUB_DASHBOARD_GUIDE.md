# n8n GitHub Health Dashboard - Complete Setup & Usage Guide

## 🎯 Overview

This comprehensive n8n workflow provides AI-powered GitHub repository health monitoring using Google's Gemini AI. The dashboard analyzes repository metrics, activity patterns, and community engagement to generate actionable insights and health scores.

## ✨ Features

### 🏥 Health Scoring

- **Overall Health Score**: 0-100 with letter grades (A-F)
- **AI-Powered Analysis**: Gemini AI provides intelligent insights
- **Factor Breakdown**: Activity, Community, Issue Management, PR Flow
- **Trend Analysis**: Historical data and predictions

### 📊 Repository Metrics

- **Stars & Forks**: Community engagement indicators
- **Issues & PRs**: Open, closed, and resolution times
- **Contributors**: Top contributors and diversity analysis
- **Commit Activity**: Recent development velocity
- **Language & Tech Stack**: Repository metadata

### 🤖 AI Insights

- **Health Assessment**: Automated analysis with recommendations
- **Strengths Identification**: What the repository does well
- **Improvement Areas**: Specific areas for enhancement
- **Risk Assessment**: Low/Medium/High risk categorization
- **Actionable Recommendations**: Concrete next steps

### 🚨 Alert System

- High number of open issues (>50)
- Many open pull requests (>30)
- Low contributor diversity (<3)
- Low recent activity (<2 commits/week)
- Prolonged issue resolution times

## 🛠 Installation

### Prerequisites

- n8n installed and running
- GitHub Personal Access Token
- Google Gemini API Key
- Basic understanding of n8n workflows

### Quick Setup

1. **Make the setup script executable:**

   ```bash
   chmod +x setup_n8n_github_dashboard.sh
   ```

2. **Run the setup script:**

   ```bash
   ./setup_n8n_github_dashboard.sh
   ```

3. **The script will:**
   - Test n8n connectivity
   - Validate GitHub API access
   - Verify Gemini API functionality
   - Import and activate the workflow
   - Provide access instructions

### Manual Installation

1. **Open n8n Interface**: <http://localhost:5678>
2. **Create New Workflow**
3. **Import JSON**: Upload `n8n_github_health_dashboard.json`
4. **Configure Credentials**:
   - GitHub API: Add Personal Access Token
   - Gemini API: Add API key in environment variables
5. **Test & Activate**

## 🔧 Configuration

### GitHub Credentials

1. Go to n8n Settings → Credentials
2. Add GitHub API credentials:
   - **Name**: GitHub API
   - **Token**: Your GitHub Personal Access Token
   - **Scopes**: `repo`, `read:org`, `read:user`

### Environment Variables

Set these in your n8n environment:

```bash
GEMINI_API_KEY=your_gemini_api_key
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token
N8N_API_KEY=your_n8n_api_key
```

### Repository Configuration

By default, the workflow monitors `theinterneti/TTA.dev`. To change:

1. Open the "Configure Repository" node
2. Update `owner` and `repo` values
3. Save and test the workflow

## 📈 Dashboard Output

### JSON Structure

The workflow generates a comprehensive JSON dashboard:

```json
{
  "generated_at": "2025-11-08T23:16:45.000Z",
  "repository": {
    "name": "owner/repo",
    "description": "Repository description",
    "url": "https://github.com/owner/repo",
    "language": "Python",
    "age_days": 365
  },
  "health_score": {
    "overall": 85,
    "grade": "B",
    "factors": {
      "activity_score": 78,
      "community_engagement": 90,
      "issue_management": 85,
      "pr_flow": 87
    }
  },
  "metrics": {
    "stars": 42,
    "forks": 12,
    "open_issues": 8,
    "open_prs": 3,
    "contributors": 7,
    "weekly_commits": 12
  },
  "trends": {
    "issue_resolution_time_hours": 48,
    "pr_merge_time_hours": 72,
    "commit_velocity": "High"
  },
  "ai_insights": {
    "assessment": "Repository shows strong community engagement...",
    "strengths": ["Active development", "Good documentation"],
    "improvements": ["Issue cleanup", "PR review process"],
    "recommendations": ["Implement code review guidelines"],
    "risk_level": "Low"
  },
  "alerts": [],
  "recommendations": [
    "Consider implementing automated testing"
  ]
}
```

## 🔄 Workflow Architecture

### Node Structure

1. **Schedule Trigger**: Runs every 6 hours
2. **Configure Repository**: Sets target repository
3. **GitHub API Nodes**: Parallel data collection
   - Repository info
   - Issues analysis
   - Pull requests
   - Contributors
   - Commit activity
4. **Process & Calculate**: Data aggregation and health scoring
5. **Prepare AI Analysis**: Formats data for Gemini
6. **Gemini AI Analysis**: AI-powered health assessment
7. **Generate Final Dashboard**: Structured output
8. **Output Dashboard**: Console logging and final output

### Health Score Calculation

The workflow calculates health scores based on:

- **Activity Score**: Recent commit frequency
- **Community Engagement**: Number of contributors
- **Issue Management**: Open issues vs. total
- **PR Flow**: Open PR management

### API Rate Limiting

- GitHub API: Respects rate limits (5,000 requests/hour)
- Gemini API: Monitor usage quotas
- n8n Execution: Optimized for 6-hour intervals

## 🎮 Usage Examples

### Basic Monitoring

1. **Automated Runs**: Workflow runs every 6 hours
2. **Manual Trigger**: Click "Execute Workflow" in n8n
3. **API Access**: Use webhooks to integrate with other systems

### Integration Scenarios

1. **Slack Notifications**: Add Slack node to send health reports
2. **Email Alerts**: Configure email nodes for critical issues
3. **Dashboard Integration**: Use JSON output in custom dashboards
4. **API Monitoring**: Poll the workflow output for external systems

### Custom Extensions

1. **Additional Metrics**: Add more GitHub API endpoints
2. **Custom Scoring**: Modify health calculation algorithms
3. **Enhanced AI**: Add specific AI prompts for deeper analysis
4. **Multi-Repository**: Loop through multiple repositories

## 🚨 Troubleshooting

### Common Issues

#### GitHub API Errors

- **401 Unauthorized**: Check token permissions
- **403 Forbidden**: Rate limiting or insufficient scopes
- **404 Not Found**: Repository doesn't exist or is private

#### Gemini API Issues

- **API Key Invalid**: Verify key in environment variables
- **Quota Exceeded**: Monitor usage and billing
- **Content Safety**: AI might reject certain content

#### n8n Workflow Issues

- **Node Errors**: Check individual node execution logs
- **Environment Variables**: Ensure all required vars are set
- **Execution Timeout**: Optimize for large repositories

### Debug Mode

1. Enable execution logging in n8n
2. Check individual node outputs
3. Verify API responses in the workflow logs
4. Test each GitHub API endpoint separately

### Performance Optimization

- **Caching**: Implement result caching for large repositories
- **Pagination**: Handle repositories with many issues/PRs
- **Rate Limiting**: Respect API limits with proper delays
- **Error Handling**: Robust retry mechanisms

## 📊 Example Output

```bash
=== GitHub Health Dashboard ===
Repository: theinterneti/TTA.dev
Health Score: 85/100 (B)
Generated: 2025-11-08T23:16:45.000Z
Alerts: ["Low recent activity"]
===============================
```

### Sample AI Insights

```json
{
  "assessment": "Repository demonstrates solid development practices with active community engagement. The codebase shows good maintenance with reasonable issue resolution times.",
  "strengths": [
    "Active development velocity",
    "Good contributor diversity",
    "Responsive issue management"
  ],
  "improvements": [
    "Address backlog of minor issues",
    "Optimize PR review process"
  ],
  "recommendations": [
    "Implement automated testing for new features",
    "Create contribution guidelines",
    "Set up automated dependency updates"
  ],
  "risk_level": "Low"
}
```

## 🔮 Advanced Features

### Historical Tracking

- Store health scores over time
- Trend analysis and predictions
- Performance benchmarking
- Progress tracking for improvement efforts

### Multi-Repository Monitoring

- Scale to monitor multiple repositories
- Comparative analysis
- Portfolio health overview
- Centralized reporting

### Custom AI Prompts

- Industry-specific health criteria
- Technology-specific insights
- Custom recommendation engine
- Advanced risk assessment

## 🤝 Contributing

### Extending the Workflow

1. **Fork and modify** the JSON workflow
2. **Add new GitHub API endpoints** for additional metrics
3. **Enhance AI prompts** for better insights
4. **Implement new visualization** formats

### Best Practices

- Respect API rate limits
- Handle errors gracefully
- Document new features
- Test with various repository types
- Maintain backward compatibility

## 📚 Resources

### Official Documentation

- [n8n Documentation](https://docs.n8n.io)
- [GitHub API Reference](https://docs.github.com/en/rest)
- [Gemini AI Documentation](https://ai.google.dev/docs)

### Community Resources

- [n8n Community Forum](https://community.n8n.io)
- [GitHub API Examples](https://github.com/octokit/rest.js)
- [Gemini AI Samples](https://ai.google.dev/examples)

## 📄 License

This workflow is provided as-is for educational and commercial use. Modify and adapt as needed for your specific requirements.

---

**Created with ❤️ using n8n, GitHub API, and Google Gemini AI**
