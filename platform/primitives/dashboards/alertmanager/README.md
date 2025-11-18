# AlertManager Configuration for TTA Dev Primitives

This directory contains AlertManager configuration for monitoring TTA workflow primitives and triggering alerts based on SLO violations, performance degradation, and cost anomalies.

## 📋 Files

- **`tta-alerts.yaml`**: Prometheus alert rules for TTA workflows
- **`alertmanager.yaml`**: AlertManager routing and notification configuration
- **`README.md`**: This file

## 🚨 Alert Categories

### 1. SLO Alerts

**Purpose:** Monitor Service Level Objective compliance and error budgets

| Alert | Severity | Threshold | Duration | Description |
|-------|----------|-----------|----------|-------------|
| `SLOComplianceCritical` | Critical | < 95% | 5 min | SLO compliance below critical threshold |
| `SLOComplianceWarning` | Warning | < 99% | 10 min | SLO compliance below warning threshold |
| `ErrorBudgetCritical` | Critical | < 10% | 5 min | Error budget critically low |
| `ErrorBudgetWarning` | Warning | < 25% | 10 min | Error budget running low |

**Actions:**
- **Critical**: Halt deployments, investigate immediately
- **Warning**: Monitor closely, prepare incident response

---

### 2. Performance Alerts

**Purpose:** Detect latency and error rate issues

| Alert | Severity | Threshold | Duration | Description |
|-------|----------|-----------|----------|-------------|
| `HighLatencyP95` | Warning | > 1s | 5 min | p95 latency exceeds 1 second |
| `HighLatencyP99` | Critical | > 2s | 5 min | p99 latency exceeds 2 seconds |
| `HighErrorRate` | Warning | > 5% | 5 min | Error rate exceeds 5% |
| `CriticalErrorRate` | Critical | > 10% | 2 min | Error rate exceeds 10% |
| `LowThroughput` | Warning | < 0.1 req/s | 10 min | Throughput below expected |
| `NoTraffic` | Critical | 0 req/s | 15 min | No requests received |

**Actions:**
- **High Latency**: Check resource utilization, database performance
- **High Error Rate**: Review logs, check dependencies
- **No Traffic**: Verify service health, check load balancer

---

### 3. Cost Alerts

**Purpose:** Monitor operational costs and savings

| Alert | Severity | Threshold | Duration | Description |
|-------|----------|-----------|----------|-------------|
| `HighCostRate` | Warning | > $10/hour | 30 min | Cost rate exceeds $10/hour |
| `CriticalCostRate` | Critical | > $50/hour | 15 min | Cost rate exceeds $50/hour |
| `LowSavingsRate` | Info | < 20% | 1 hour | Savings rate below 20% target |

**Actions:**
- **High Cost**: Review LLM usage, check for inefficient queries
- **Low Savings**: Optimize cache configuration, review cache hit rates

---

### 4. Availability Alerts

**Purpose:** Monitor service availability and capacity

| Alert | Severity | Threshold | Duration | Description |
|-------|----------|-----------|----------|-------------|
| `ServiceDown` | Critical | Service unavailable | 1 min | TTA workflow service is down |
| `ActiveRequestsSpike` | Warning | > 100 concurrent | 5 min | High number of active requests |
| `ActiveRequestsCritical` | Critical | > 500 concurrent | 2 min | Critical number of active requests |

**Actions:**
- **Service Down**: Immediate investigation, check infrastructure
- **Active Requests Spike**: Scale resources, investigate traffic source

---

## 🚀 Quick Start

### Prerequisites

1. **Prometheus** installed and running
2. **AlertManager** installed
3. **TTA Dev Primitives** with Prometheus exporter enabled

### Installation

#### Step 1: Configure Prometheus Alert Rules

Add the alert rules to your Prometheus configuration:

```yaml
# prometheus.yml
rule_files:
  - '/path/to/tta-dev-primitives/dashboards/alertmanager/tta-alerts.yaml'
```

Reload Prometheus configuration:
```bash
curl -X POST http://localhost:9090/-/reload
```

#### Step 2: Configure AlertManager

1. **Copy configuration file:**
   ```bash
   cp alertmanager.yaml /etc/alertmanager/alertmanager.yml
   ```

2. **Update notification settings:**
   Edit `/etc/alertmanager/alertmanager.yml` and configure:
   - SMTP settings for email notifications
   - Slack webhook URLs
   - PagerDuty service keys
   - Email addresses for each receiver

3. **Reload AlertManager:**
   ```bash
   curl -X POST http://localhost:9093/-/reload
   ```

#### Step 3: Verify Configuration

1. **Check Prometheus rules:**
   ```bash
   curl http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name | contains("tta"))'
   ```

2. **Check AlertManager configuration:**
   ```bash
   curl http://localhost:9093/api/v1/status | jq
   ```

3. **Test alert firing:**
   ```bash
   # Trigger a test alert
   curl -X POST http://localhost:9093/api/v1/alerts -d '[
     {
       "labels": {
         "alertname": "TestAlert",
         "severity": "warning"
       },
       "annotations": {
         "summary": "Test alert"
       }
     }
   ]'
   ```

---

## ⚙️ Configuration

### Customizing Alert Thresholds

Edit `tta-alerts.yaml` to adjust thresholds:

```yaml
# Example: Change SLO compliance threshold
- alert: SLOComplianceCritical
  expr: tta_workflow_slo_compliance_ratio < 0.90  # Changed from 0.95
  for: 5m
```

### Customizing Notification Channels

Edit `alertmanager.yaml` to configure receivers:

```yaml
receivers:
  - name: 'critical-alerts'
    # Email
    email_configs:
      - to: 'your-team@example.com'
    
    # Slack
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#your-channel'
    
    # PagerDuty
    pagerduty_configs:
      - service_key: 'your-service-key'
```

### Adding Custom Alerts

Add new alert rules to `tta-alerts.yaml`:

```yaml
- alert: CustomAlert
  expr: your_promql_expression > threshold
  for: duration
  labels:
    severity: warning
    component: workflow
    alert_type: custom
  annotations:
    summary: "Alert summary"
    description: "Detailed description with {{ $labels.primitive_name }}"
    runbook_url: "https://docs.tta.dev/runbooks/custom-alert"
```

---

## 📊 Alert Routing

### Routing Logic

1. **Critical alerts** → Immediate notification to on-call + SRE
2. **SLO alerts** → SRE team with 30s delay
3. **Cost alerts** → Finance + Engineering with 5min delay
4. **Performance alerts** → Engineering team
5. **Info alerts** → Team email with 10min delay

### Inhibition Rules

Alerts are automatically suppressed when:
- Critical alert is firing → Suppress related warnings
- Service is down → Suppress latency/throughput alerts
- Error budget critical → Suppress SLO compliance warnings

---

## 🔧 Troubleshooting

### Alerts Not Firing

1. **Check Prometheus is evaluating rules:**
   ```bash
   curl http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | select(.name | contains("SLO"))'
   ```

2. **Verify metrics are available:**
   ```bash
   curl 'http://localhost:9090/api/v1/query?query=tta_workflow_slo_compliance_ratio'
   ```

3. **Check AlertManager is receiving alerts:**
   ```bash
   curl http://localhost:9093/api/v1/alerts | jq
   ```

### Notifications Not Sending

1. **Check AlertManager logs:**
   ```bash
   journalctl -u alertmanager -f
   ```

2. **Verify receiver configuration:**
   ```bash
   amtool config routes --alertmanager.url=http://localhost:9093
   ```

3. **Test notification channel:**
   ```bash
   # Test email
   amtool alert add test severity=warning --alertmanager.url=http://localhost:9093
   ```

### Too Many Alerts

1. **Adjust thresholds** in `tta-alerts.yaml`
2. **Increase `for` duration** to reduce noise
3. **Add inhibition rules** to suppress related alerts
4. **Review `group_interval` and `repeat_interval`** in `alertmanager.yaml`

---

## 📚 Runbook Templates

Create runbooks for each alert type at `https://docs.tta.dev/runbooks/`:

### Example: SLO Compliance Runbook

```markdown
# SLO Compliance Alert Runbook

## Alert: SLOComplianceCritical

### Severity: Critical

### Description
SLO compliance has dropped below 95% for 5 minutes.

### Impact
- Users experiencing degraded service
- Error budget being consumed rapidly
- Risk of SLO violation

### Investigation Steps
1. Check Grafana SLO dashboard
2. Review error logs for patterns
3. Check recent deployments
4. Verify infrastructure health

### Remediation
1. If recent deployment: Consider rollback
2. If infrastructure issue: Scale resources
3. If external dependency: Enable fallback
4. If traffic spike: Enable rate limiting

### Prevention
- Improve test coverage
- Add canary deployments
- Implement circuit breakers
- Monitor error budget trends
```

---

## 📈 Metrics Reference

### Alert Expressions

**SLO Compliance:**
```promql
tta_workflow_slo_compliance_ratio < 0.95
```

**Error Rate:**
```promql
rate(tta_workflow_requests_total{status="failure"}[5m]) /
rate(tta_workflow_requests_total[5m]) > 0.05
```

**Latency p95:**
```promql
histogram_quantile(0.95, rate(tta_workflow_primitive_duration_seconds_bucket[5m])) > 1.0
```

**Cost Rate:**
```promql
rate(tta_workflow_cost_total[1h]) > 10.0
```

---

## 🔗 Additional Resources

- [Prometheus Alerting](https://prometheus.io/docs/alerting/latest/overview/)
- [AlertManager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [PromQL Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [TTA Observability Guide](../../docs/observability/)

---

**Last Updated:** 2025-10-29  
**Version:** 1.0.0

