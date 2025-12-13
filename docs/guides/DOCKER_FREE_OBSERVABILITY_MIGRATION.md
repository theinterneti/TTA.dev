# Docker-Free Observability Migration - Summary

**Date:** 2025-11-15
**Status:** Ready for Implementation
**Estimated Time:** 30-60 minutes

---

## 🎯 Problem Statement

You're experiencing Docker Desktop reliability issues on Windows/WSL, making the current observability stack (Prometheus, Grafana, Jaeger, OTLP Collector) unreliable for development.

**Current Setup:**
- 5 Docker containers running observability services
- ~800MB RAM usage
- ~2GB disk space
- 30-second startup time
- Dependent on Docker Desktop working

---

## ✅ Solution: Linux-Native Observability with Grafana Cloud

### Architecture Overview

```
TTA.dev App                     Grafana Alloy               Grafana Cloud
   (9464) ────metrics──────►  (systemd service)  ─────►  theinterneti.grafana.net
   (logs) ────journald─────►         │
   (4317) ────OTLP/traces──►         │
                                     │
                              100MB RAM, 2s startup
```

### Key Benefits

1. **Reliability:** Native systemd services, no Docker dependency
2. **Performance:** ~700MB RAM savings, 2-second startup
3. **Simplicity:** Single binary (Grafana Alloy) replaces 5 containers
4. **Hybrid Model:** Grafana Cloud for production + optional local services for offline dev
5. **Zero Code Changes:** Your TTA.dev app continues exporting metrics on port 9464

---

## 📦 What Was Created

### 1. Comprehensive Documentation

**`docs/guides/LINUX_NATIVE_OBSERVABILITY.md`** (500+ lines)
- Complete migration guide
- Step-by-step installation instructions
- Configuration examples
- Troubleshooting section
- Security considerations
- Alternative approaches (Podman)

**`docs/guides/NATIVE_OBSERVABILITY_QUICKREF.md`** (350+ lines)
- Quick reference card
- Common commands
- Verification steps
- Troubleshooting flowcharts
- Configuration file locations

### 2. Automation Script

**`scripts/setup-native-observability.sh`** (executable)
- Automated installation for Ubuntu/Debian/RHEL/Fedora
- Detects OS automatically
- Configures Grafana Alloy with your Grafana Cloud credentials
- Sets up systemd services
- Validates installation
- Optional: Install local Prometheus and Grafana

**Usage:**
```bash
# Basic installation (Grafana Cloud only)
sudo GRAFANA_CLOUD_TOKEN="<your-token>" ./scripts/setup-native-observability.sh

# With local services for offline dev
sudo GRAFANA_CLOUD_TOKEN="<your-token>" \
     INSTALL_LOCAL_PROMETHEUS=true \
     INSTALL_LOCAL_GRAFANA=true \
     ./scripts/setup-native-observability.sh
```

### 3. Logseq TODO Entry

Created in `logseq/journals/2025_11_15.md`:
- High-priority ops task
- Links to all documentation
- Estimated effort: 1-2 hours
- Clear next steps

---

## 🚀 Recommended Implementation Path

### Phase 1: Parallel Testing (30 minutes)

```bash
# 1. Keep Docker running (for comparison)
docker-compose -f docker-compose.integration.yml up -d

# 2. Install Alloy using automated script
cd /home/thein/repos/TTA.dev
sudo GRAFANA_CLOUD_TOKEN="$(grep GRAFANA_CLOUD_API_KEY ~/.env.tta-dev | cut -d= -f2)" \
     ./scripts/setup-native-observability.sh

# 3. Verify both systems receiving metrics
# Docker Prometheus: http://localhost:9090
# Grafana Cloud: https://theinterneti.grafana.net/

# 4. Compare data quality and latency
```

### Phase 2: Switch to Native (10 minutes)

```bash
# 1. Stop Docker services
docker-compose -f docker-compose.integration.yml down

# 2. Verify Alloy still running
sudo systemctl status alloy

# 3. Check Grafana Cloud receiving data
# https://theinterneti.grafana.net/explore

# 4. Test TTA.dev application workflows
```

### Phase 3: Cleanup (10 minutes)

```bash
# 1. Remove Docker images (optional)
docker rmi jaegertracing/all-in-one:1.52
docker rmi prom/prometheus:v2.48.1
docker rmi grafana/grafana:10.2.3
docker rmi otel/opentelemetry-collector-contrib:0.91.0
docker rmi prom/pushgateway:v1.6.2

# 2. Remove Docker volumes
docker volume prune -f

# 3. Update documentation to reference native setup
```

---

## 🔍 What Gets Replaced

| Component | Before (Docker) | After (Native) | Notes |
|-----------|-----------------|----------------|-------|
| **Metrics** | Prometheus container | Grafana Alloy → Cloud | Scrapes port 9464 |
| **Logs** | N/A | Alloy → Loki Cloud | From systemd journal |
| **Traces** | Jaeger container | Alloy → Tempo Cloud | OTLP on 4317/4318 |
| **Collector** | OTLP Collector | Built into Alloy | Single binary |
| **Pushgateway** | Dedicated container | Not needed | Direct scrape |
| **Visualization** | Local Grafana | Grafana Cloud | Optional: local install |

---

## 📊 Resource Comparison

### Before (Docker Stack)

```
Services:  5 containers
Memory:    ~800MB
Disk:      ~2GB (images)
Startup:   ~30 seconds
Reliability: Depends on Docker Desktop
```

### After (Grafana Alloy)

```
Services:  1 systemd service
Memory:    ~100MB
Disk:      ~50MB (binary)
Startup:   ~2 seconds
Reliability: Native Linux systemd
```

**Total Savings:** ~700MB RAM, ~1.95GB disk, 28-second faster startup

---

## 🔐 Security & Configuration

### Grafana Cloud Credentials

Your token is stored in `/home/thein/.env.tta-dev`. The script:
1. Reads token from environment file
2. Stores in `/etc/default/alloy` (root-only readable)
3. Uses environment variables in Alloy config

### Firewall Considerations

```bash
# OTLP receivers (only if accepting external traces)
sudo ufw allow 4317/tcp comment 'Alloy OTLP gRPC'
sudo ufw allow 4318/tcp comment 'Alloy OTLP HTTP'

# Metrics endpoint (localhost only - no rule needed)
# Port 9464 should NOT be exposed externally
```

---

## 🧪 Verification Steps

### 1. Check Alloy Status

```bash
sudo systemctl status alloy
journalctl -u alloy -f
```

### 2. Verify Metrics Export

```bash
# Your app should export metrics
curl http://localhost:9464/metrics

# Alloy's own metrics
curl http://localhost:12345/metrics
```

### 3. Check Grafana Cloud

1. Visit: https://theinterneti.grafana.net/
2. Navigate to **Explore**
3. Select **Prometheus** data source
4. Query: `{job="tta-dev-app"}`
5. Should see metrics from your application

### 4. Test Traces (if using OTLP)

```python
# Your code (no changes needed!)
from observability_integration import initialize_observability

success = initialize_observability(
    service_name="tta-dev-app",
    enable_prometheus=True,
    prometheus_port=9464,
    otlp_endpoint="http://localhost:4317",  # Alloy receives
)
```

---

## 🆘 Troubleshooting Quick Reference

### Alloy Won't Start

```bash
# Check logs
journalctl -u alloy -n 50 --no-pager

# Common fixes:
sudo systemctl restart alloy
sudo chown -R alloy:alloy /var/lib/alloy /etc/alloy
```

### No Metrics in Grafana Cloud

```bash
# 1. Verify app exports
curl http://localhost:9464/metrics

# 2. Check Alloy scraping
journalctl -u alloy | grep -i scrape

# 3. Verify credentials
sudo cat /etc/default/alloy
```

### Need to Rollback

```bash
# Stop Alloy
sudo systemctl stop alloy
sudo systemctl disable alloy

# Restart Docker
docker-compose -f docker-compose.integration.yml up -d
```

---

## 📚 Documentation References

### Main Guides

1. **[LINUX_NATIVE_OBSERVABILITY.md](docs/guides/LINUX_NATIVE_OBSERVABILITY.md)** - Complete guide (500+ lines)
2. **[NATIVE_OBSERVABILITY_QUICKREF.md](docs/guides/NATIVE_OBSERVABILITY_QUICKREF.md)** - Quick reference (350+ lines)

### Automation

- **[setup-native-observability.sh](scripts/setup-native-observability.sh)** - Installation script (executable)

### Related Documentation

- [Observability Architecture](docs/architecture/OBSERVABILITY_ARCHITECTURE.md)
- [Observability Integration](docs/integration/observability-integration.md)
- [MCP Servers Guide](MCP_SERVERS.md) - Grafana MCP tools
- [Infrastructure Guide](logseq/pages/Infrastructure.md)

---

## 🎯 Success Criteria

After successful migration:

- [ ] Grafana Alloy service running (`systemctl status alloy`)
- [ ] Metrics visible in Grafana Cloud
- [ ] TTA.dev app workflows functioning normally
- [ ] Memory usage reduced by ~700MB
- [ ] Alloy service survives system reboot
- [ ] OTLP traces working (if applicable)
- [ ] Docker services stopped and removed
- [ ] Documentation updated

---

## 🔄 Alternative Approaches

### Option 1: Grafana Alloy (Recommended)

**Pros:**
- ✅ Single unified agent
- ✅ Native Linux packages
- ✅ Smallest footprint
- ✅ Official Grafana support

**Cons:**
- ❌ New configuration syntax to learn

### Option 2: Podman (Docker Alternative)

**Pros:**
- ✅ Docker-compatible
- ✅ Rootless containers
- ✅ No daemon required
- ✅ Reuse existing docker-compose.yml

**Cons:**
- ❌ Still container-based
- ❌ More memory than Alloy

**Usage:**
```bash
sudo apt-get install podman podman-compose
alias docker=podman
podman-compose -f docker-compose.integration.yml up -d
```

### Option 3: Individual Native Binaries

**Pros:**
- ✅ Maximum control
- ✅ No new tools

**Cons:**
- ❌ Multiple services to manage
- ❌ More complex configuration
- ❌ Higher resource usage

---

## 💡 Future Considerations

### Potential Enhancements

1. **Grafana Agent Flow Mode:** Alternative to Alloy (similar features)
2. **Vector.dev:** Alternative data pipeline (more complex, more flexible)
3. **OpenTelemetry Collector Binary:** If you need more OTLP features
4. **Local Prometheus + Remote Write:** Keep local Prometheus, ship to Cloud

### When to Revisit

- If you need advanced log processing (consider Vector)
- If you need multiple OTLP exporters (consider OTel Collector)
- If Grafana Cloud limits become an issue (add local Prometheus)
- If you want to self-host everything (add Tempo, Loki, etc.)

---

## 📞 Support & Resources

### Official Documentation

- **Grafana Alloy:** https://grafana.com/docs/alloy/
- **Grafana Cloud:** https://grafana.com/docs/grafana-cloud/
- **Your Grafana Cloud:** https://theinterneti.grafana.net/

### TTA.dev Documentation

- **Main Guide:** `docs/guides/LINUX_NATIVE_OBSERVABILITY.md`
- **Quick Ref:** `docs/guides/NATIVE_OBSERVABILITY_QUICKREF.md`
- **Script:** `scripts/setup-native-observability.sh`

### Community

- **Grafana Community:** https://community.grafana.com/
- **Alloy GitHub:** https://github.com/grafana/alloy

---

## ✅ Next Steps

### Immediate Actions

1. **Read Documentation:**
   - Quick scan: `docs/guides/NATIVE_OBSERVABILITY_QUICKREF.md`
   - Deep dive: `docs/guides/LINUX_NATIVE_OBSERVABILITY.md`

2. **Run Installation:**
   ```bash
   cd /home/thein/repos/TTA.dev
   sudo GRAFANA_CLOUD_TOKEN="<token-from-env-file>" \
        ./scripts/setup-native-observability.sh
   ```

3. **Verify Setup:**
   - Check Alloy status: `sudo systemctl status alloy`
   - View logs: `journalctl -u alloy -f`
   - Check Grafana Cloud: https://theinterneti.grafana.net/

4. **Test Application:**
   - Run TTA.dev workflows
   - Verify metrics flowing
   - Compare with Docker setup (if parallel)

5. **Decision Point:**
   - Keep parallel setup for a few days? OR
   - Switch immediately and stop Docker?

### If Issues Arise

1. Check troubleshooting sections in documentation
2. Review Alloy logs: `journalctl -u alloy -n 100`
3. Verify configuration: `sudo alloy fmt /etc/alloy/config.alloy`
4. Rollback to Docker if needed (temporary)
5. Document issues in Logseq for future improvement

---

**Created:** 2025-11-15
**Author:** GitHub Copilot
**Purpose:** Migration from Docker Desktop to Linux-native observability
**Outcome:** Reliable, lightweight, production-ready observability stack



---
**Logseq:** [[TTA.dev/Docs/Guides/Docker_free_observability_migration]]
