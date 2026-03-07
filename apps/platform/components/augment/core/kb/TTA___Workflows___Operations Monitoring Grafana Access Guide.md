---
title: 🎯 **Grafana Access Guide - TTA Monitoring**
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/operations/monitoring/grafana_access_guide.md
created: 2025-10-26
updated: 2025-10-04
---
# [[TTA/Workflows/🎯 **Grafana Access Guide - TTA Monitoring**]]

## 🚀 **Quick Access**

### **Grafana Dashboard**
- **URL**: http://localhost:3003
- **Username**: `admin`
- **Password**: `tta-admin-2024`

### **Direct Service Access**
- **Health Check Service**: http://localhost:8090/health
- **Health Metrics**: http://localhost:8090/metrics
- **Prometheus**: http://localhost:9091
- **Player API**: http://localhost:3004
- **Player Frontend**: http://localhost:3001

## 📊 **Available Metrics**

### **TTA Service Health Metrics**
```prometheus
# Service status (1 = UP, 0 = DOWN)
tta_service_up{service="player-api", environment="staging"} 1
tta_service_up{service="player-frontend", environment="staging"} 1
tta_service_up{service="grafana", environment="staging"} 1
tta_service_up{service="redis", environment="staging"} 0
tta_service_up{service="neo4j", environment="staging"} 0
tta_service_up{service="postgres", environment="staging"} 0
```

### **Response Time Metrics**
```prometheus
# Response times in seconds
tta_service_response_time_seconds{service="player-api"} 0.004
tta_service_response_time_seconds{service="player-frontend"} 0.003
tta_service_response_time_seconds{service="grafana"} 0.002
```

## 🔍 **Useful Grafana Queries**

### **Service Status Overview**
```promql
tta_service_up
```

### **Response Time Monitoring**
```promql
tta_service_response_time_seconds
```

### **Service Availability Rate**
```promql
avg_over_time(tta_service_up[5m])
```

### **Services Currently UP**
```promql
tta_service_up == 1
```

### **Services Currently DOWN**
```promql
tta_service_up == 0
```

## 🛠️ **API Testing Commands**

### **Test Grafana Authentication**
```bash
curl -u admin:tta-admin-2024 http://localhost:3003/api/health
```

### **Query Metrics via Grafana**
```bash
curl -u admin:tta-admin-2024 \
  "http://localhost:3003/api/datasources/proxy/1/api/v1/query?query=tta_service_up"
```

### **Check Available Datasources**
```bash
curl -u admin:tta-admin-2024 http://localhost:3003/api/datasources
```

### **List Dashboards**
```bash
curl -u admin:tta-admin-2024 http://localhost:3003/api/search?type=dash-db
```

## 📈 **Creating Custom Dashboards**

### **1. Access Grafana Web Interface**
1. Navigate to http://localhost:3003
2. Login with `admin:tta-admin-2024`
3. Click "+" → "Dashboard" → "Add visualization"

### **2. Configure Data Source**
- **Data Source**: Prometheus (already configured)
- **URL**: http://tta-staging-prometheus:9090

### **3. Example Panel Queries**

#### **Service Status Panel**
- **Query**: `tta_service_up`
- **Visualization**: Stat
- **Value mappings**: 0 = DOWN, 1 = UP

#### **Response Time Panel**
- **Query**: `tta_service_response_time_seconds * 1000`
- **Visualization**: Time series
- **Unit**: milliseconds (ms)

#### **Service Availability Panel**
- **Query**: `avg_over_time(tta_service_up[1h]) * 100`
- **Visualization**: Gauge
- **Unit**: percent (0-100)

## 🔧 **Troubleshooting**

### **If Grafana Won't Load**
```bash
# Check container status
docker ps --filter "name=grafana"

# Check logs
docker logs tta-staging-grafana

# Restart if needed
docker restart tta-staging-grafana
```

### **If Metrics Don't Appear**
```bash
# Test Prometheus directly
curl http://localhost:9091/api/v1/query?query=tta_service_up

# Test health check service
curl http://localhost:8090/metrics | grep tta_service

# Check Prometheus targets
curl http://localhost:9091/api/v1/targets
```

### **If Authentication Fails**
- Verify credentials: `admin:tta-admin-2024`
- Check container environment: `docker exec tta-staging-grafana env | grep GF_SECURITY`

## 🎯 **Next Steps for Phase 2**

### **Dashboard Import**
1. Import existing TTA dashboards from `monitoring/grafana/dashboards/`
2. Configure dashboard provisioning for automatic import

### **Frontend Integration**
1. Connect React components to Grafana API endpoints
2. Implement real-time dashboard embedding
3. Add user-specific analytics views

### **Advanced Analytics**
1. Create custom dashboards for user progress tracking
2. Implement therapeutic outcome visualization
3. Add alerting for system health issues

## 📞 **Support Information**

### **Container Names**
- **Grafana**: `tta-staging-grafana`
- **Prometheus**: `tta-staging-prometheus`
- **Health Check**: `tta-staging-health-check`

### **Network**
- **Docker Network**: `tta-staging-homelab_tta-staging`

### **Volumes**
- **Grafana Data**: `grafana-staging-data`
- **Prometheus Data**: `prometheus-staging-data`

---

**🎉 Phase 1 Complete - Monitoring Infrastructure Fully Operational!**


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___operations monitoring grafana access guide]]
