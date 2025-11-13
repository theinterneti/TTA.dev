# Docker Host Configuration for Prometheus

## Overview

The TTA.dev observability stack uses `host.docker.internal` for cross-platform Docker host access. This ensures the Prometheus configuration works seamlessly across Docker Desktop (Mac/Windows) and Docker on Linux.

## Background

Previously, the configuration used the hardcoded IP `172.17.0.1`, which is the default Docker bridge network gateway on Linux. However, this approach has several limitations:

- **Not portable**: Different Docker configurations may use different bridge IPs
- **Platform-specific**: Docker Desktop on Mac/Windows doesn't use `172.17.0.1`
- **Not configurable**: Hardcoded values make it difficult to adapt to different environments

## Solution

We now use `host.docker.internal` as the standard way to access the Docker host from within containers.

### Changes Made

1. **Prometheus Configuration** (`config/prometheus/prometheus.yml`)
   - Replaced all instances of `172.17.0.1` with `host.docker.internal`
   - Affected scrape targets:
     - `tta-live-metrics` (port 9464)
     - `tta-primitives` (port 9464)
     - `tta-observability` (port 9465)

2. **Docker Compose** (`docker-compose.professional.yml`)
   - Added `extra_hosts` configuration to Prometheus service
   - Ensures `host.docker.internal` resolves correctly on all platforms

3. **Environment Variables** (`.env.example`)
   - Added documentation for `DOCKER_HOST_IP` (optional override)
   - Defaults to `host.docker.internal`

## Platform Compatibility

### Docker Desktop (Mac/Windows)
✅ Works out of the box - `host.docker.internal` is natively supported

### Docker on Linux (Modern)
✅ Works with our configuration - `extra_hosts: ["host.docker.internal:host-gateway"]` enables support

### Docker on Linux (Older versions < 20.10)
⚠️ May require manual configuration:

```yaml
# In docker-compose.professional.yml
prometheus:
  extra_hosts:
    - "host.docker.internal:172.17.0.1"  # Or your specific bridge IP
```

Or use environment variable:
```bash
# In .env
DOCKER_HOST_IP=172.17.0.1
```

## How It Works

The `extra_hosts` configuration in Docker Compose adds an entry to the container's `/etc/hosts` file:

```
<host-gateway-ip>  host.docker.internal
```

Where `host-gateway` is a special Docker Compose value that automatically resolves to:
- The host's IP address on the Docker bridge network
- Typically `172.17.0.1` on Linux
- The Docker Desktop VM gateway on Mac/Windows

## Verification

To verify the configuration works correctly:

1. Start the observability stack:
   ```bash
   docker-compose -f docker-compose.professional.yml up -d
   ```

2. Check Prometheus can resolve the host:
   ```bash
   docker exec tta-prometheus ping -c 1 host.docker.internal
   ```

3. Check Prometheus targets:
   ```bash
   curl http://localhost:9090/api/v1/targets | jq
   ```

4. Look for the `tta-live-metrics`, `tta-primitives`, and `tta-observability` targets - they should be in `up` state.

## Troubleshooting

### Target shows as "down" in Prometheus

1. Check if the metrics server is actually running on the host:
   ```bash
   curl http://localhost:9464/metrics
   ```

2. Check container can reach host:
   ```bash
   docker exec tta-prometheus curl http://host.docker.internal:9464/metrics
   ```

3. If using Linux and getting connection refused, check your Docker version:
   ```bash
   docker --version
   ```
   
   If < 20.10, you may need to manually configure the host IP.

### Custom Docker Network Configuration

If you're using a custom Docker network setup:

1. Find your Docker bridge gateway IP:
   ```bash
   docker network inspect bridge | jq '.[0].IPAM.Config[0].Gateway'
   ```

2. Update the `extra_hosts` in `docker-compose.professional.yml`:
   ```yaml
   prometheus:
     extra_hosts:
       - "host.docker.internal:<your-gateway-ip>"
   ```

## References

- [Docker Compose extra_hosts documentation](https://docs.docker.com/compose/compose-file/compose-file-v3/#extra_hosts)
- [Docker host networking](https://docs.docker.com/network/host/)
- [Prometheus configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)

## Related Files

- `config/prometheus/prometheus.yml` - Prometheus scrape configuration
- `docker-compose.professional.yml` - Docker services configuration
- `.env.example` - Environment variable documentation
