# AlertManager Configuration for TTA.dev Phase 3 Observability

This directory contains production-ready AlertManager rules and configuration for monitoring TTA.dev workflows with comprehensive alerting on SLOs, performance, costs, and availability.

## 📋 Alert Rule Files

### 1. SLO Alerts (`rules/slo-alerts.yml`)

**Alerts:**
- `SLOComplianceWarning`: SLO compliance < 99%
- `SLOComplianceCritical`: SLO compliance < 95%
- `ErrorBudgetLow`: Error budget < 30%
- `ErrorBudgetCritical`: Error budget < 10%
- `ErrorBudgetExhausted`: Error budget <= 0%
- `ErrorBudgetFastBurn`: Burn rate > 10x sustainable
- `ErrorBudgetModerateBurn`: Burn rate > 5x sustainable

**Use Cases:**
- Monitor SLO compliance vs. targets
- Track error budget consumption
- Alert before SLOs are violated
- Detect fast error budget burn rates

---

### 2. Performance Alerts (`rules/performance-alerts.yml`)

**Alerts:**
- `HighP95Latency`: p95 latency > 5s
- `CriticalP95Latency`: p95 latency > 10s
- `HighP99Latency`: p99 latency > 10s
- `LatencyIncreasing`: Latency 1.5x higher than 1h ago
- `LowThroughput`: RPS < 0.1
- `ThroughputDrop`: Throughput 50% lower than 1h ago
- `HighConcurrency`: Active requests > 100
- `CriticalConcurrency`: Active requests > 500

**Use Cases:**
- Detect latency degradation
- Monitor throughput changes
- Alert on high concurrency
- Identify performance regressions

---

### 3. Cost Alerts (`rules/cost-alerts.yml`)

**Alerts:**
- `HighCostRate`: Cost rate > $0.10/sec
- `CriticalCostRate`: Cost rate > $1.00/sec
- `DailyCostBudgetExceeded`: Total cost > $100/day
- `MonthlyCostProjection`: Projected cost > $3000/month
- `CostSpike`: Cost rate 5x higher than 1h ago
- `UnexpectedCost`: New cost where none existed 24h ago
- `LowSavingsRate`: Savings rate < 20%
- `SavingsDecreasing`: Savings 20% lower than yesterday
- `HighCostPerRequest`: Cost per request > $0.01

**Use Cases:**
- Track infrastructure costs
- Monitor budget compliance
- Detect cost anomalies
- Optimize cost efficiency

---

### 4. Availability Alerts (`rules/availability-alerts.yml`)

**Alerts:**
- `HighErrorRate`: Error rate > 5%
- `CriticalErrorRate`: Error rate > 10%
- `LowSuccessRate`: Success rate < 95%
- `CriticalSuccessRate`: Success rate < 90%
- `PrimitiveDown`: No requests in 5 minutes
- `AllRequestsFailing`: 100% error rate
- `ErrorRateIncreasing`: Error rate 3x higher than 1h ago
- `ServiceFlapping`: Up/down changes > 5 in 15 minutes

**Use Cases:**
- Monitor service availability
- Detect outages
- Track error rates
- Identify service instability

---

## 🚀 Quick Start

### Prerequisites

- AlertManager 0.24 or later
- Prometheus with TTA.dev metrics
- Access to notification channels (Email, Slack, PagerDuty)

### Installation

#### Option 1: Docker Compose (Recommended)

```yaml
version: '3.8'

services:
  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager-data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'

volumes:
  alertmanager-data:
```

#### Option 2: Kubernetes

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
data:
  alertmanager.yml: |
    # Paste contents of alertmanager.yml here

---

apiVersion: apps/v1
kind: Deployment
metadata:
  name: alertmanager
spec:
  selector:
    matchLabels:
      app: alertmanager
  template:
    metadata:
      labels:
        app: alertmanager
    spec:
      containers:
      - name: alertmanager
        image: prom/alertmanager:latest
        ports:
        - containerPort: 9093
        volumeMounts:
        - name: config
          mountPath: /etc/alertmanager
      volumes:
      - name: config
        configMap:
          name: alertmanager-config
```

#### Option 3: Standalone Installation

```bash
# Download AlertManager
wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
tar xvfz alertmanager-0.26.0.linux-amd64.tar.gz
cd alertmanager-0.26.0.linux-amd64

# Copy config
cp /path/to/alertmanager.yml .

# Start AlertManager
./alertmanager --config.file=alertmanager.yml
```

---

## ⚙️ Configuration

### 1. Configure Prometheus to Use Alert Rules

Add to your `prometheus.yml`:

```yaml
rule_files:
  - '/etc/prometheus/rules/slo-alerts.yml'
  - '/etc/prometheus/rules/performance-alerts.yml'
  - '/etc/prometheus/rules/cost-alerts.yml'
  - '/etc/prometheus/rules/availability-alerts.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'alertmanager:9093'
```

### 2. Configure Notification Channels

**Email:**
```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@example.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'
  smtp_require_tls: true
```

**Slack:**
```yaml
receivers:
  - name: 'slack-team'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

**PagerDuty:**
```yaml
receivers:
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: 'your-pagerduty-integration-key'
        description: '{{ .GroupLabels.alertname }}'
```

### 3. Customize Alert Thresholds

Edit rule files to adjust thresholds:

```yaml
# Example: Change latency threshold
- alert: HighP95Latency
  expr: |
    histogram_quantile(0.95,
      sum(rate(primitive_duration_seconds_bucket[5m])) by (le, primitive_name)
    ) > 2  # Changed from 5s to 2s
  for: 5m  # Changed from 10m to 5m
```

### 4. Add Custom Routes

Add to `alertmanager.yml`:

```yaml
routes:
  - match:
      team: 'your-team'
    receiver: 'your-receiver'
    group_wait: 1m
    repeat_interval: 2h
```

---

## 📊 Alert Severity Levels

| Severity | Description | Response Time | Example |
|----------|-------------|---------------|---------|
| **Critical** | Service-impacting | Immediate | SLO < 95%, outage detected |
| **Warning** | Potential issue | 15-30 min | SLO < 99%, latency increasing |
| **Info** | Informational | Next business day | Low savings rate |

---

## 🎯 Runbook Templates

### SLO Compliance Alert Runbook

**Alert:** `SLOComplianceCritical`

**Investigation Steps:**
1. Check Grafana SLO dashboard for trends
2. Identify which requests are failing/slow
3. Check error logs for recent failures
4. Review recent deployments/changes

**Mitigation:**
1. If latency-related: Scale up resources
2. If errors: Rollback recent deployment
3. If external dependency: Enable fallback/circuit breaker

### High Cost Rate Runbook

**Alert:** `HighCostRate`

**Investigation Steps:**
1. Check Grafana cost dashboard
2. Identify which primitives are expensive
3. Check if usage pattern changed
4. Review cache hit rates

**Mitigation:**
1. Enable caching if not already
2. Reduce unnecessary API calls
3. Optimize expensive operations
4. Set rate limits if needed

### Service Down Runbook

**Alert:** `PrimitiveDown`

**Investigation Steps:**
1. Check if service is actually running
2. Review logs for errors
3. Check dependencies (DB, APIs)
4. Verify network connectivity

**Mitigation:**
1. Restart service if crashed
2. Fix configuration if invalid
3. Scale up if resource exhaustion
4. Enable fallback if dependency issue

---

## 🔧 Testing Alerts

### Test Alert Firing

```bash
# Send test alert to AlertManager
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning",
      "primitive_name": "test_primitive"
    },
    "annotations": {
      "summary": "Test alert",
      "description": "This is a test alert"
    }
  }]'
```

### Verify Alert Routes

```bash
# Check AlertManager routing
amtool config routes --config.file=alertmanager.yml

# Test alert matching
amtool config routes test --config.file=alertmanager.yml \
  alertname=SLOComplianceCritical severity=critical
```

### Silence Alerts

```bash
# Silence an alert for 2 hours
amtool silence add \
  alertname=HighP95Latency \
  primitive_name=test_primitive \
  --duration=2h \
  --comment="Investigating performance issue"
```

---

## 📈 Monitoring AlertManager

### Health Check

```bash
curl http://localhost:9093/-/healthy
```

### Status Check

```bash
curl http://localhost:9093/api/v2/status
```

### View Active Alerts

```bash
curl http://localhost:9093/api/v2/alerts
```

### Metrics

AlertManager exposes metrics at `http://localhost:9093/metrics`:

- `alertmanager_alerts`: Number of active alerts
- `alertmanager_notifications_total`: Total notifications sent
- `alertmanager_notification_latency_seconds`: Notification latency

---

## 🚨 Troubleshooting

### Alerts Not Firing

**Check:**
1. Prometheus is scraping metrics: `http://prometheus:9090/targets`
2. Alert rules are loaded: `http://prometheus:9090/rules`
3. Alert expressions evaluate: `http://prometheus:9090/graph`
4. AlertManager is reachable: `http://alertmanager:9093`

### Notifications Not Sent

**Check:**
1. AlertManager logs: `docker logs alertmanager`
2. Receiver configuration (SMTP, Slack webhook, etc.)
3. Network connectivity to notification services
4. Alert routing matches receivers

### Too Many Alerts

**Solutions:**
1. Increase alert thresholds
2. Add inhibition rules
3. Group related alerts
4. Use longer `group_wait` and `repeat_interval`

### Alert Storms

**Prevention:**
- Use inhibition rules (included in config)
- Group alerts by `primitive_name`
- Set appropriate `group_wait` intervals
- Silence known issues during maintenance

---

## 📚 Best Practices

### 1. Alert Design

- **Actionable**: Every alert should require action
- **Clear**: Describe the problem and impact
- **Runbooks**: Link to investigation steps
- **Context**: Include relevant labels and values

### 2. Alert Fatigue Prevention

- **Tune thresholds** based on actual behavior
- **Use warning → critical** escalation
- **Group related alerts** to reduce noise
- **Silence during maintenance** windows

### 3. On-Call Practices

- **Prioritize by severity**: Critical → Warning → Info
- **Document resolutions**: Update runbooks
- **Review alerts weekly**: Tune and improve
- **Rotate on-call duty**: Distribute load

### 4. Testing

- **Test alert routes** before deploying
- **Verify notifications** reach correct channels
- **Practice incident response** with test alerts
- **Keep runbooks updated** with learnings

---

## 🔗 Related Documentation

- [Phase 3 Enhanced Metrics](../../docs/observability/METRICS_GUIDE.md)
- [Prometheus Setup Guide](../../docs/observability/PROMETHEUS_SETUP.md)
- [Grafana Dashboards](../grafana/README.md)
- [Observability Assessment](../../docs/observability/OBSERVABILITY_ASSESSMENT.md)

---

## 📞 Support

For issues or questions:
- **GitHub Issues**: https://github.com/theinterneti/TTA.dev/issues
- **Documentation**: `docs/observability/`
- **Examples**: `packages/tta-dev-primitives/examples/`

---

**Last Updated:** 2025-10-29  
**AlertManager Version:** 0.26+  
**Alert Rules Version:** 1.0.0
