# TTA.dev Professional Observability

**Production-grade monitoring, alerting, and visualization for TTA.dev**

---

## 🎯 Overview

This professional observability setup provides enterprise-grade monitoring capabilities for TTA.dev, replacing the basic demo configuration with production-ready infrastructure.

### What's Included

- **📊 Prometheus** - Professional metrics collection with recording/alerting rules
- **🚨 AlertManager** - Intelligent alert routing and notification management
- **📈 Grafana** - Comprehensive dashboard suite for all stakeholder types
- **🔍 Jaeger** - Distributed tracing with service topology
- **⚡ OpenTelemetry Collector** - Advanced telemetry processing
- **📡 Pushgateway** - Short-lived process metrics
- **💻 Node Exporter** - System-level metrics

### Target Audiences

1. **🏢 Executives** - Business metrics, SLO compliance, cost efficiency
2. **🔧 Platform Engineers** - Service health, infrastructure monitoring
3. **👨‍💻 Developers** - Debugging tools, primitive performance, error tracking
4. **🚨 SRE Teams** - Alerting, capacity planning, incident response
5. **📊 Product Teams** - Usage analytics, performance insights

---

## 🚀 Quick Start

### 1. Setup Professional Stack

```bash
# Run the professional setup script
./scripts/setup-professional-observability.sh
```

This script will:
- ✅ Validate all configuration files
- ✅ Start 6 monitoring services with health checks
- ✅ Import professional dashboards
- ✅ Configure intelligent alerting
- ✅ Verify all endpoints are working

### 2. Access Professional Dashboards

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **Grafana** | http://localhost:3000 | admin/admin | Professional dashboards |
| **Prometheus** | http://localhost:9090 | None | Metrics and rules |
| **AlertManager** | http://localhost:9093 | None | Alert management |
| **Jaeger** | http://localhost:16686 | None | Distributed tracing |

### 3. Generate Test Data

```bash
# Run the observability demo to see real metrics
uv run python platform/primitives/examples/observability_demo.py
```

---

## 📊 Professional Dashboard Suite

### Executive Dashboard
**Audience:** Business leaders, product managers
**URL:** http://localhost:3000/d/tta-executive
**Refresh:** 5 minutes

**Key Metrics:**
- 🎯 Service health overview (success rate, availability, cache efficiency)
- 💰 Business metrics (executions, requests/min, active services)
- 💡 Cost efficiency (cache savings, estimated cost reduction)
- 📈 SLO compliance status with visual indicators
- 📊 Growth trends and capacity planning indicators

### Platform Health Dashboard
**Audience:** Platform engineers, SRE teams
**URL:** http://localhost:3000/d/tta-platform-health
**Refresh:** 30 seconds

**Key Metrics:**
- 🟢 Real-time service status indicators
- 📉 Error rates by service with trend analysis
- ⏱️ Latency percentiles (P50, P95, P99)
- 🏎️ Cache performance and operations rate
- 📊 Throughput by service
- 💾 Resource utilization (CPU, memory)
- 🚨 Active alerts table with severity

### Developer Dashboard
**Audience:** Developers, QA engineers
**URL:** http://localhost:3000/d/tta-developer
**Refresh:** 10 seconds

**Key Metrics:**
- ⚡ Primitive execution rates by type
- ✅ Success/failure rates per primitive
- 🌡️ Latency heatmaps for performance analysis
- 📊 Cache performance breakdown by primitive
- 🔍 Error distribution pie chart
- 📝 Workflow execution timeline
- 📋 Recent error log entries
- 🧠 Memory usage trends
- 🔗 Active connection monitoring

---

## 🚨 Professional Alerting

### Alert Categories

#### 🔴 Critical Alerts (Immediate Response)
- **TTAHighErrorRate** - Error rate > 5% for 2 minutes
- **TTAServiceDown** - Service unavailable for 1 minute
- **TTAHighLatency** - P95 latency > 1 second for 5 minutes
- **TTALowCacheHitRate** - Cache hit rate < 60% for 5 minutes
- **TTAAvailabilitySLOBreach** - Availability SLO breach

#### 🟡 Warning Alerts (Action Required)
- **TTAModerateLowCacheHitRate** - Cache hit rate < 80% for 10 minutes
- **TTAHighRequestRate** - Unusual traffic spike
- **TTAHighMemoryUsage** - Memory > 1GB for 15 minutes
- **TTALatencySLOBreach** - Latency SLO degradation

#### 🔵 Informational Alerts
- **TTAHighGrowthRate** - Traffic growth > 50% in 24h
- **TTANegativeGrowthRate** - Traffic decline > 20% in 24h

### Alert Routing

```yaml
Critical Alerts → Multiple Channels:
  - Email: critical-alerts@tta.dev
  - Slack: #critical-alerts
  - Repeat: Every 30 minutes

Platform Alerts → Platform Team:
  - Email: platform-team@tta.dev
  - Repeat: Every 1 hour

SLO Breaches → SRE Team:
  - Email: sre-team@tta.dev
  - Context: Error budget burn rate
```

### Alert Suppression Rules

- **Service Down** → Suppress all workflow-level alerts for that service
- **High Error Rate** → Suppress cache-related alerts
- **Availability SLO Breach** → Suppress individual SLO alerts

---

## 📏 Service Level Indicators (SLIs)

### Availability SLI
- **Target:** 99% success rate
- **Measurement:** `tta:sli_availability_5m`
- **Alert:** Breach for 5+ minutes

### Latency SLI
- **Target:** 95% of requests < 100ms
- **Measurement:** `tta:sli_latency_5m`
- **Alert:** Breach for 10+ minutes

### Cache Performance SLI
- **Target:** 90% cache hit rate
- **Measurement:** `tta:sli_cache_performance_5m`
- **Alert:** Breach for 15+ minutes

---

## 📐 Recording Rules

Pre-computed metrics for dashboard performance:

### Performance Rules (30s interval)
```promql
tta:request_rate_5m = rate(tta_requests_total[5m])
tta:success_rate_5m = rate(tta_requests_total{status="success"}[5m]) / rate(tta_requests_total[5m]) * 100
tta:latency_p95_5m = histogram_quantile(0.95, rate(tta_execution_duration_seconds_bucket[5m]))
tta:cache_hit_rate_5m = rate(tta_cache_hits_total[5m]) / (rate(tta_cache_hits_total[5m]) + rate(tta_cache_misses_total[5m])) * 100
```

### Business Rules (5 minute interval)
```promql
tta:total_executions_24h = increase(tta_workflow_executions_total[24h])
tta:estimated_cost_savings_24h = increase(tta_cache_hits_total[24h]) * 0.001
```

### SLI Rules (1 minute interval)
```promql
tta:sli_availability_5m = (rate(tta_requests_total{status="success"}[5m]) / rate(tta_requests_total[5m])) >= 0.99
tta:sli_latency_5m = histogram_quantile(0.95, rate(tta_execution_duration_seconds_bucket[5m])) < 0.1
```

---

## 🔧 Configuration Files

### Core Monitoring
- **Prometheus:** `config/prometheus/prometheus.yml` - Service discovery, retention, storage
- **Recording Rules:** `config/prometheus/rules/recording_rules.yml` - Pre-computed metrics
- **Alerting Rules:** `config/prometheus/rules/alerting_rules.yml` - Alert definitions
- **AlertManager:** `config/alertmanager/alertmanager.yml` - Routing and notifications

### Dashboards & Visualization
- **Grafana Datasources:** `config/grafana/datasources/datasources.yml`
- **Dashboard Provisioning:** `config/grafana/dashboards/dashboards.yml`
- **Executive Dashboard:** `config/grafana/dashboards/executive_dashboard.json`
- **Platform Health:** `config/grafana/dashboards/platform_health.json`
- **Developer Tools:** `config/grafana/dashboards/developer_dashboard.json`

---

## 🏗️ Architecture

### Service Dependencies
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Grafana   │───▶│ Prometheus  │───▶│ TTA.dev App │
│(Dashboards) │    │  (Metrics)  │    │ (Targets)   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                    │
       ▼                    ▼
┌─────────────┐    ┌─────────────┐
│   Jaeger    │    │AlertManager │
│ (Tracing)   │    │ (Alerts)    │
└─────────────┘    └─────────────┘
```

### Data Flow
1. **TTA.dev Applications** → Export metrics on `/metrics` endpoint
2. **Prometheus** → Scrapes metrics every 15s, evaluates rules
3. **AlertManager** → Receives alerts, applies routing/grouping
4. **Grafana** → Queries Prometheus for dashboard data
5. **Jaeger** → Receives traces via OpenTelemetry

### Storage & Retention
- **Prometheus:** 30 days retention, 10GB max size
- **Grafana:** Persistent dashboards and settings
- **AlertManager:** Alert state and silences
- **Jaeger:** In-memory (production would use Cassandra/Elasticsearch)

---

## 🔍 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check container logs
docker-compose -f docker-compose.professional.yml -p tta-observability logs -f [service]

# Check container status
docker-compose -f docker-compose.professional.yml -p tta-observability ps
```

#### Dashboards Not Loading
```bash
# Verify Grafana datasource connection
curl -u admin:admin http://localhost:3000/api/datasources

# Check Prometheus connectivity
curl http://localhost:9090/api/v1/query?query=up
```

#### Alerts Not Firing
```bash
# Check AlertManager configuration
curl http://localhost:9093/api/v1/status

# Verify Prometheus rules
curl http://localhost:9090/api/v1/rules
```

#### Missing Metrics
```bash
# Check if your application is exporting metrics
curl http://localhost:9464/metrics

# Verify Prometheus is scraping
curl http://localhost:9090/api/v1/targets
```

### Health Check Endpoints
- **Prometheus:** http://localhost:9090/-/healthy
- **AlertManager:** http://localhost:9093/-/healthy
- **Grafana:** http://localhost:3000/api/health
- **Jaeger:** http://localhost:16686/api/services
- **OpenTelemetry:** http://localhost:13133/

---

## 🚀 Production Deployment

### Security Considerations
1. **Authentication:** Enable OAuth/LDAP for Grafana
2. **Authorization:** Role-based access control
3. **TLS:** Enable HTTPS for all endpoints
4. **Network:** Use proper network segmentation
5. **Secrets:** Use proper secret management

### Scaling Considerations
1. **Prometheus:** Consider federation for multi-cluster
2. **Storage:** Use remote storage (Thanos, Cortex)
3. **Alerting:** AlertManager clustering
4. **Dashboards:** Grafana enterprise for teams

### Backup Strategy
1. **Prometheus:** Backup TSDB snapshots
2. **Grafana:** Export/import dashboard JSON
3. **Configuration:** Version control all configs

---

## 📚 Related Documentation

- **Architecture Analysis:** `docs/guides/observability/ARCHITECTURE_ANALYSIS.md`
- **Basic Setup:** `scripts/setup-observability.sh`
- **Integration Testing:** `platform/primitives/docker-compose.integration.yml`
- **Observability Examples:** `platform/primitives/examples/observability_demo.py`

---

## 🤝 Contributing

### Adding New Dashboards
1. Create JSON in `config/grafana/dashboards/`
2. Update `dashboards.yml` provisioning
3. Test with professional stack
4. Document key metrics and purpose

### Adding New Alerts
1. Define in `config/prometheus/rules/alerting_rules.yml`
2. Add routing in `config/alertmanager/alertmanager.yml`
3. Test alert conditions
4. Document impact and runbook links

### Adding New Metrics
1. Export from TTA.dev applications
2. Add scrape job in `prometheus.yml`
3. Create recording rules if needed
4. Add to relevant dashboards

---

**Last Updated:** November 7, 2025
**Version:** 1.0.0
**Maintained by:** TTA.dev Platform Team


---
**Logseq:** [[TTA.dev/Docs/Observability/Professional_observability]]
