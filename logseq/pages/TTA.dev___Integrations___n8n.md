# TTA.dev n8n Integration

**Workflow Automation and GitHub Health Dashboards**

---

## Overview

n8n is a workflow automation tool that TTA.dev integrates with to create automated GitHub health dashboards and workflow orchestration. It provides visual workflow creation with extensive API integrations and data processing capabilities.

**Status:** ✅ Active
**Environment:** Development (local) + Production (cloud deployment)
**Configuration Level:** High

---

## Development vs Production Usage

### Development Environment (✅ Local Development)
- **Primary Use:** Building and testing automated workflows
- **Capabilities:** Local n8n instance for workflow development
- **Integration:** GitHub health dashboard prototypes
- **Setup:** Docker Compose for local development

### Production Environment (✅ Cloud Deployment)
- **Availability:** Full n8n cloud features for production automation
- **Use Cases:** Automated GitHub health monitoring, notification systems
- **Integration:** Real-time health dashboards and alerting
- **Cost:** n8n cloud pricing (free tier available)

---

## Key Capabilities

### GitHub Health Dashboards

**Automated Health Monitoring:**
- PR status tracking
- CI/CD pipeline monitoring
- Issue backlog analysis
- Contributor activity metrics
- Repository health scores

**Dashboard Features:**
- Real-time GitHub webhook integration
- Automated metric collection
- Visual dashboard generation
- Alert system for health changes

### Workflow Orchestration

**Supported Workflows:**
- GitHub API integrations
- Data processing and filtering
- Notification systems (email, Slack, webhooks)
- Database operations
- API call orchestration

---

## Integration with TTA.dev

### GitHub Health Dashboard System

```
GitHub Webhooks → n8n Workflows → Data Processing → Dashboard Updates
                                    ↓
                              Notification Triggers
```

**Dashboard Components:**
- **Repository Health Score:** Based on PR response times, issue resolution
- **CI/CD Status:** Pipeline success rates, failure analysis
- **Team Productivity:** PR review times, merge frequencies
- **Quality Metrics:** Test coverage, linting status

### Observability Integration

**Metrics Pipeline:**
1. **Collect:** Pull metrics from GitHub API and other sources
2. **Process:** Calculate health scores and trends
3. **Store:** Save to database or forward to external systems
4. **Visualize:** Create dashboards and reports
5. **Alert:** Trigger notifications for health degradation

---

## Setup & Configuration

### Local Development Setup

1. **Clone n8n Configuration:**
   ```bash
   git clone https://github.com/theinterneti/TTA.dev
   cd TTA.dev/n8n
   ```

2. **Start n8n Stack:**
   ```bash
   docker-compose up -d
   # Access at http://localhost:5678
   ```

3. **Configure GitHub Credentials:**
   - Add GitHub Personal Access Token
   - Set up webhook endpoints
   - Configure repository permissions

### Production Deployment

**n8n Cloud Setup:**
1. Sign up for n8n cloud
2. Import workflow templates from `/n8n/` directory
3. Configure production GitHub tokens
4. Set up monitoring and alerts

**Self-Hosted:**
1. Deploy n8n using Docker
2. Configure reverse proxy
3. Set up database (PostgreSQL recommended)
4. Enable security features

---

## Available Workflows

### GitHub Health Dashboard

**Workflow File:** `n8n_github_health_dashboard.json`

**Features:**
- Daily health score calculation
- PR aging alerts
- CI/CD failure notifications
- Team productivity reporting
- Repository metrics dashboard

**Triggers:**
- Scheduled (daily)
- GitHub webhooks (real-time)
- Manual execution

### API Integration Workflows

**Git Automation Workflow:** `n8n_git_automation_workflow.json`

**Capabilities:**
- Automated PR management
- Issue triage and labeling
- Contributor onboarding workflows
- Release automation
- Documentation updates

---

## Configuration Details

### GitHub Integration

**Required Permissions:**
- Repository read access
- Issues and PR access
- Webhook creation
- Organization read access (optional)

**API Rate Limits:**
- 5000 requests/hour for authenticated users
- 60 requests/hour for unauthenticated
- n8n handles rate limiting automatically

### Database Integration

**Supported Databases:**
- PostgreSQL (recommended)
- MySQL/MariaDB
- SQLite (development only)
- MongoDB

**Schema Design:**
```sql
-- Health metrics table
CREATE TABLE github_health (
  id SERIAL PRIMARY KEY,
  repository VARCHAR(255),
  date DATE,
  pr_count INTEGER,
  issue_count INTEGER,
  health_score DECIMAL(3,2),
  created_at TIMESTAMP
);
```

---

## Cross-References & Integration Points

### Related Integrations
- **[[TTA.dev/Integrations/Observability Stack]]**: Receives health metrics
- **[[TTA.dev/Integrations/Git]]**: Source of GitHub data
- **[[TTA.dev/Integrations/MCP Servers]]**: GitHub MCP provides complementary data

### TTA.dev Components
- **[[TTA.dev/DevOps Studio]]**: Infrastructure health monitoring
- **[[Monitoring]]**: Receives n8n-generated metrics
- **[[.github/workflows]]**: GitHub Actions integration

### Documentation Links
- [[docs/integrations/README]] - n8n integration overview
- [[n8n/README]] - Local setup instructions
- [n8n Documentation](https://docs.n8n.io) - Official docs

---

## Troubleshooting

### Workflow Execution Issues

**Symptom:** n8n workflows not running

**Solutions:**
1. Check n8n service status
2. Verify credential configuration
3. Review workflow error logs
4. Test API connections manually

### GitHub API Rate Limiting

**Symptom:** API errors, missing data

**Solutions:**
1. Implement caching in workflows
2. Use webhooks for real-time updates
3. Batch API calls appropriately
4. Monitor rate limit usage

### Webhook Delivery Issues

**Symptom:** GitHub events not triggering workflows

**Solutions:**
1. Verify webhook URL accessibility
2. Check webhook secret configuration
3. Review GitHub webhook delivery logs
4. Test webhook manually

---

**Last Updated:** 2025-11-17
**Documentation:** [docs.n8n.io](https://docs.n8n.io)
**Tags:** integration:: n8n, automation:: workflows, monitoring:: github


---
**Logseq:** [[TTA.dev/Logseq/Pages/Tta.dev___integrations___n8n]]
