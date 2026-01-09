---
title: TTA Docker Authentication Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/testing/authentication-guide.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/TTA Docker Authentication Guide]]

## Overview

This guide covers authentication configuration for the TTA Comprehensive Test Battery's Docker integration, addressing common authentication issues and providing best practices for secure credential management.

## Authentication Architecture

### Credential Hierarchy

The system uses a three-tier credential fallback system:

1. **Environment-Specific Credentials**: Loaded from `.env.test`, `.env.dev`, etc.
2. **Automatic Credential Detection**: Health checker tries multiple common combinations
3. **Mock Fallback**: Graceful degradation when authentication fails

### Supported Environments

| Environment | Config File | Neo4j Password | Container Prefix |
|-------------|-------------|----------------|------------------|
| Test        | `.env.test` | `tta_test_password_2024` | `tta-test` |
| Development | `.env.dev`  | `tta_dev_password_2024`  | `tta-dev` |
| CI/CD       | GitHub Env  | `tta_ci_password_2024`   | `tta-ci` |

## Configuration Files

### Test Environment (`.env.test`)
```bash
NEO4J_AUTH_USER=neo4j
NEO4J_AUTH_PASSWORD=tta_test_password_2024
NEO4J_AUTH=neo4j/tta_test_password_2024
CONTAINER_PREFIX=tta-test
```

### Development Environment (`.env.dev`)
```bash
NEO4J_AUTH_USER=neo4j
NEO4J_AUTH_PASSWORD=tta_dev_password_2024
NEO4J_AUTH=neo4j/tta_dev_password_2024
CONTAINER_PREFIX=tta-dev
```

## Common Authentication Issues

### 1. Authentication Rate Limiting

**Symptom**: `AuthenticationRateLimit` errors
**Cause**: Too many failed authentication attempts
**Solution**:
- Wait 5-10 seconds between attempts
- Use correct credentials from environment files
- Clear existing containers: `./scripts/manage-containers.sh clean`

### 2. Credential Mismatch

**Symptom**: `Neo.ClientError.Security.Unauthorized`
**Cause**: Wrong username/password combination
**Solution**:
- Verify environment file is loaded
- Check container environment variables
- Use credential fallback system

### 3. Container Name Confusion

**Symptom**: Container not found errors
**Cause**: Inconsistent container naming
**Solution**:
- Use environment-specific prefixes
- Check running containers: `docker ps`
- Update container names in configuration

## Best Practices

### 1. Secure Credential Management

```bash
# ✅ Good: Use environment files
source .env.test
docker-compose -f docker-compose.test.yml up -d

# ❌ Bad: Hardcode credentials
docker run -e NEO4J_AUTH=neo4j/password neo4j
```

### 2. Environment Isolation

```bash
# Test environment
./scripts/manage-containers.sh start test

# Development environment
./scripts/manage-containers.sh start dev
```

### 3. Authentication Retry Logic

The health checker automatically:
- Tries multiple credential combinations
- Implements exponential backoff
- Handles rate limiting gracefully
- Falls back to mock services

## Troubleshooting

### Check Container Status
```bash
./scripts/manage-containers.sh status
./scripts/manage-containers.sh health
```

### View Container Logs
```bash
./scripts/manage-containers.sh logs neo4j
./scripts/manage-containers.sh logs redis
```

### Test Connectivity
```bash
./scripts/manage-containers.sh test-connection
```

### Reset Authentication State
```bash
# Stop all containers
./scripts/manage-containers.sh stop

# Clean up containers and networks
./scripts/manage-containers.sh clean

# Start fresh
./scripts/manage-containers.sh start test
```

## Security Considerations

### Development vs Production

- **Development**: Use `.env.dev` with known passwords
- **Testing**: Use `.env.test` with test-specific passwords
- **CI/CD**: Use GitHub secrets and environment variables
- **Production**: Use secure credential management systems

### Password Rotation

1. Update environment files
2. Restart containers with new credentials
3. Update health checker credential list if needed
4. Test connectivity with new credentials

## Integration with Test Battery

The comprehensive test battery automatically:

1. **Detects Environment**: Loads appropriate credentials
2. **Tries Multiple Credentials**: Uses fallback system
3. **Handles Failures**: Gracefully degrades to mocks
4. **Reports Status**: Provides detailed error messages

### Example Usage

```python
# Automatic credential detection and fallback
health_result = await health_checker.check_neo4j_health_with_credential_fallback(
    "bolt://localhost:7687", timeout=30.0
)

if health_result.status == HealthStatus.HEALTHY:
    print("✅ Neo4j authentication successful")
else:
    print(f"❌ Authentication failed: {health_result.message}")
```

## Support

For authentication issues:

1. Check this guide first
2. Review container logs
3. Verify environment configuration
4. Test with credential fallback system
5. Fall back to mock services if needed

The system is designed to be resilient and provide clear error messages for troubleshooting authentication problems.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs testing authentication guide]]
