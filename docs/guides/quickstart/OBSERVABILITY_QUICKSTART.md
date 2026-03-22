# Quick Start: Using Observability in TTA.dev

> [!WARNING]
> Historical observability quickstart.
>
> This quickstart uses older `observability_integration` imports and workspace-specific setup steps.
> It is useful as historical context, but it is not the current March 2026 source of truth.
>
> For the current verified path, prefer `README.md`, `GETTING_STARTED.md`, `QUICKSTART.md`, and
> `python -m ttadev.observability`.

**Updated:** November 15, 2025
**Status:** Historical quickstart snapshot

---

## TL;DR

```bash
# Historical workspace-specific test path
uv run python test_observability.py tta-dev-copilot

# Or in your Python code
uv run python -c "
from ttadev import initialize_observability
initialize_observability(service_name='tta-dev-copilot')
"

# Check metrics
curl http://localhost:9464/metrics
```

---

## Using Observability in Your Application

### Option 1: Using the Test Script

The easiest way to test observability:

```bash
# Test with your workspace name
uv run python test_observability.py tta-dev-main
uv run python test_observability.py tta-dev-cline
uv run python test_observability.py tta-dev-copilot
uv run python test_observability.py tta-dev-augment
```

### Option 2: In Your Python Application

Add to your application startup code:

```python
from ttadev import initialize_observability

# Initialize at application startup
success = initialize_observability(
    service_name="tta-dev-copilot",  # Your workspace name
    enable_prometheus=True,
    prometheus_port=9464,
)

if success:
    print("✅ Observability enabled - metrics at http://localhost:9464/metrics")
else:
    print("⚠️  Observability disabled (graceful degradation)")

# Your application code here...
```

### Option 3: Using uv run Directly

```bash
# Run your application with uv
uv run python your_application.py

# Or run a quick test
uv run python -c "
from ttadev import initialize_observability
print('Initialized:', initialize_observability(service_name='test'))
"
```

---

## Understanding the Fix

### What Was Wrong?

The `tta-dev-integrations` package was missing workspace source configuration, causing:

```
× Failed to parse entry: `tta-dev-primitives`
╰─▶ `tta-dev-primitives` is included as a workspace member,
    but is missing an entry in `tool.uv.sources`
```

### What Was Fixed?

Added to `packages/tta-dev-integrations/pyproject.toml`:

```toml
[tool.uv.sources]
tta-dev-primitives = { workspace = true }
```

This tells `uv` that `tta-dev-primitives` comes from the local workspace, not PyPI.

### How to Avoid This in the Future?

When creating a new package that depends on other workspace packages:

1. **Declare the dependency:**
   ```toml
   dependencies = ["tta-dev-primitives>=1.0.0"]
   ```

2. **Add workspace source:**
   ```toml
   [tool.uv.sources]
   tta-dev-primitives = { workspace = true }
   ```

3. **Sync the workspace:**
   ```bash
   uv sync --all-extras
   ```

---

## Multi-Workspace Setup

If you have multiple TTA.dev clones (like tta-dev-copilot, tta-dev-cline, etc.):

### Approach 1: Simple (Recommended)

Use the **same port** (9464) with **different service names**:

```python
# In TTA.dev (main)
initialize_observability(service_name="tta-dev-main")

# In TTA.dev-cline
initialize_observability(service_name="tta-dev-cline")

# In TTA.dev-copilot
initialize_observability(service_name="tta-dev-copilot")
```

**Constraint:** Only run one workspace at a time (port conflict on 9464).

### Approach 2: Advanced

Use **different ports** for each workspace:

```python
# TTA.dev (main)
initialize_observability(service_name="tta-dev-main", prometheus_port=9464)

# TTA.dev-cline
initialize_observability(service_name="tta-dev-cline", prometheus_port=9465)

# TTA.dev-copilot
initialize_observability(service_name="tta-dev-copilot", prometheus_port=9466)
```

**Benefit:** Run multiple workspaces simultaneously.
**Trade-off:** Need to configure Grafana Alloy to scrape multiple ports.

See: [`docs/guides/MULTI_WORKSPACE_OBSERVABILITY.md`](../guides/MULTI_WORKSPACE_OBSERVABILITY.md)

---

## Verifying Everything Works

### 1. Workspace Sync

```bash
cd /home/thein/repos/TTA.dev
uv sync --all-extras
```

**Expected:** All packages build successfully.

### 2. Import Test

```bash
uv run python -c "from ttadev import initialize_observability; print('✅ OK')"
```

**Expected:** `✅ OK`

### 3. Initialization Test

```bash
uv run python test_observability.py tta-dev-test
```

**Expected:**
```
✅ Observability successfully initialized for 'tta-dev-test'!
📈 Metrics endpoint: http://localhost:9464/metrics
```

### 4. Metrics Check

```bash
curl http://localhost:9464/metrics | head -20
```

**Expected:** Prometheus metrics output (Python GC stats, process metrics, etc.)

---

## Next Steps

### 1. Install Grafana Alloy (Optional)

To send metrics to Grafana Cloud:

```bash
# Get your Grafana Cloud token
TOKEN=$(grep GRAFANA_CLOUD_API_KEY ~/.env.tta-dev | cut -d= -f2)

# Run installation script
sudo GRAFANA_CLOUD_TOKEN="$TOKEN" ./scripts/setup-native-observability.sh
```

See: [`docs/guides/LINUX_NATIVE_OBSERVABILITY.md`](../guides/LINUX_NATIVE_OBSERVABILITY.md)

### 2. Use in Production Code

Integrate observability into your application:

```python
# At application startup
from ttadev import initialize_observability

if __name__ == "__main__":
    # Initialize observability
    initialize_observability(
        service_name="my-app",
        service_version="1.0.0",
        enable_prometheus=True,
    )

    # Your application code
    run_application()
```

### 3. Query Metrics

Once Grafana Alloy is running and sending to Grafana Cloud:

1. Visit: https://theinterneti.grafana.net/
2. Go to Explore → Prometheus
3. Query: `{service_name="tta-dev-copilot"}`

---

## Troubleshooting

### "Module not found" for old observability imports

**Solution:** Use `uv run`:
```bash
# ❌ Don't use plain python
python test_observability.py

# ✅ Use uv run
uv run python test_observability.py
```

### "Port 9464 already in use"

**Solution:** Check what's using the port:
```bash
sudo lsof -i :9464
```

Either:
- Stop the other process
- Use a different port: `initialize_observability(prometheus_port=9465)`

### "Workspace member not found"

**Solution:** Resync the workspace:
```bash
uv sync --all-extras
```

### "Permission denied" on metrics endpoint

**Solution:** Check firewall:
```bash
# Allow Prometheus port
sudo ufw allow 9464/tcp
```

---

## Reference

### Important Files

| File | Purpose |
|------|---------|
| `test_observability.py` | Quick test script |
| `platform/observability/` | Observability package |
| `docs/guides/MULTI_WORKSPACE_OBSERVABILITY.md` | Multi-workspace guide |
| `docs/guides/LINUX_NATIVE_OBSERVABILITY.md` | Grafana Alloy setup |
| `docs/guides/troubleshooting/WORKSPACE_CONFIGURATION_FIX.md` | Fix details |

### Useful Commands

```bash
# Sync workspace
uv sync --all-extras

# Test observability
uv run python test_observability.py <workspace-name>

# Check metrics
curl http://localhost:9464/metrics

# View TTA metrics only
curl http://localhost:9464/metrics | grep tta_

# Check Alloy status (if installed)
sudo systemctl status alloy
```

---

**Last Updated:** November 15, 2025
**Status:** Historical quickstart snapshot
**Next:** Install Grafana Alloy for cloud integration
