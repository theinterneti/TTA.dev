---
title: Frontend Deployment Workflow Documentation
tags: #TTA
status: Active
repo: theinterneti/TTA
path: .github/workflows/FRONTEND_DEPLOY_README.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Frontend Deployment Workflow Documentation]]

## Overview

The `frontend-deploy.yml` workflow provides automated building and deployment of the TTA frontend application to the staging environment. It triggers automatically when changes are pushed to the `src/player_experience/frontend/` directory on the main branch.

## Workflow Features

### ✅ Automated Triggers
- **Path Filtering**: Only runs when frontend files change
- **Manual Dispatch**: Can be triggered manually for testing
- **Branch Protection**: Only deploys from main branch

### 🔍 Quality Checks
- **ESLint**: Code linting for JavaScript/TypeScript
- **TypeScript**: Type checking for type safety
- **Unit Tests**: Jest tests with coverage reporting
- **Test Artifacts**: Coverage reports uploaded for review

### 🐳 Docker Build
- **Multi-stage Build**: Uses `Dockerfile.staging` for optimized images
- **Layer Caching**: GitHub Actions cache for faster builds
- **Image Tagging**: Tags with `staging` and `staging-{commit-sha}`
- **Registry**: Pushes to GitHub Container Registry (ghcr.io)
- **Build Args**: Passes environment variables and metadata

### 🚀 Deployment
- **Staging Environment**: Deploys to tta.dev subdirectory
- **Health Checks**: Verifies deployment success
- **Smoke Tests**: Basic functionality validation
- **Rollback**: Automatic rollback on failure

### 📊 Reporting
- **Deployment Summary**: Comprehensive deployment report
- **Job Status**: Status of all workflow jobs
- **Access URLs**: Links to deployed application
- **Debugging Tips**: Guidance for troubleshooting

## Workflow Jobs

### 1. Quality Checks (`quality-checks`)
**Purpose**: Validate code quality before building

**Steps**:
1. Checkout code
2. Set up Node.js 18 with npm caching
3. Install dependencies
4. Run ESLint
5. Run TypeScript type checking
6. Run unit tests with coverage
7. Upload coverage reports

**Skip Options**:
- `skip_quality_checks`: Skip all quality checks
- `skip_tests`: Skip only unit tests

### 2. Build Frontend (`build-frontend`)
**Purpose**: Build and push Docker image

**Steps**:
1. Checkout code
2. Set up Docker Buildx
3. Authenticate with GHCR
4. Extract metadata and generate tags
5. Build and push Docker image with caching
6. Generate build summary

**Outputs**:
- `image_tag`: Full image tag
- `image_digest`: Image digest for verification

### 3. Deploy to Staging (`deploy-staging`)
**Purpose**: Deploy built image to staging environment

**Steps**:
1. Checkout code
2. Create deployment marker
3. Execute deployment commands (placeholder)
4. Wait for services to start

**Environment**: `staging`

**⚠️ Note**: Deployment commands are placeholders. Update with actual deployment logic.

### 4. Health Check (`health-check`)
**Purpose**: Verify deployment success

**Steps**:
1. Check frontend health endpoint
2. Check API connectivity
3. Run smoke tests
4. Generate health check summary

**Configuration**:
- Retries: 10 attempts
- Delay: 30 seconds between attempts
- Endpoints: `/health` and `/` (fallback)

### 5. Post-Deployment (`post-deployment`)
**Purpose**: Generate deployment summary

**Steps**:
1. Generate comprehensive deployment summary
2. Report job results
3. Provide access URLs or rollback guidance
4. Notify deployment status

**Always Runs**: Yes (even if previous jobs fail)

### 6. Rollback (`rollback`)
**Purpose**: Revert deployment on failure

**Steps**:
1. Checkout code
2. Rollback to previous version (placeholder)
3. Verify rollback success
4. Generate rollback summary with debugging tips

**Trigger**: Only on deployment or health check failure

**⚠️ Note**: Rollback commands are placeholders. Update with actual rollback logic.

## Configuration

### Required Secrets
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

### Optional Variables
Configure these in GitHub repository settings under Settings → Secrets and variables → Actions → Variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `FRONTEND_BASE_URL` | Staging frontend URL | `http://localhost:3001` |
| `API_BASE_URL` | Staging API URL | `http://localhost:8081` |
| `WS_URL` | WebSocket URL | `ws://localhost:8081` |

### Environment Variables (Workflow-level)
| Variable | Value | Description |
|----------|-------|-------------|
| `NODE_VERSION` | `18` | Node.js version |
| `REGISTRY` | `ghcr.io` | Container registry |
| `IMAGE_NAME` | `ghcr.io/{owner}/tta-player-experience-frontend` | Image name |
| `FRONTEND_DIR` | `src/player_experience/frontend` | Frontend directory |
| `HEALTH_CHECK_RETRIES` | `10` | Health check retry attempts |
| `HEALTH_CHECK_DELAY` | `30` | Delay between retries (seconds) |
| `DEPLOYMENT_TIMEOUT` | `600` | Deployment timeout (seconds) |

## Manual Workflow Dispatch

### Trigger Manually
1. Go to Actions → Frontend Deploy to Staging
2. Click "Run workflow"
3. Select branch (usually `main`)
4. Configure options:
   - **skip_quality_checks**: Skip linting, type-checking, and tests
   - **skip_tests**: Skip only unit tests
   - **force_deploy**: Continue even if health checks fail
5. Click "Run workflow"

### Use Cases
- **Testing**: Test deployment without quality checks
- **Hotfix**: Deploy urgent fixes quickly
- **Debugging**: Force deploy to investigate issues

## Customization Guide

### 1. Update Deployment Logic

**Location**: Job `deploy-staging`, step "Deploy to staging environment"

**Current**: Placeholder commands

**Options**:
```yaml
# Option 1: SSH to staging server
ssh user@staging-server << 'EOF'
  docker pull ${{ env.IMAGE_NAME }}:staging-${{ github.sha }}
  docker-compose up -d player-frontend
EOF

# Option 2: Kubernetes deployment
kubectl set image deployment/tta-frontend-staging \
  frontend=${{ env.IMAGE_NAME }}:staging-${{ github.sha }} \
  -n staging

# Option 3: Ansible playbook
ansible-playbook -i inventory/staging deploy-frontend.yml \
  -e "frontend_image=${{ env.IMAGE_NAME }}:staging-${{ github.sha }}"
```

### 2. Update Rollback Logic

**Location**: Job `rollback`, step "Rollback to previous version"

**Current**: Placeholder commands

**Options**:
```yaml
# Option 1: Revert Docker image
ssh user@staging-server << 'EOF'
  docker pull ${{ env.IMAGE_NAME }}:staging
  docker-compose up -d player-frontend
EOF

# Option 2: Kubernetes rollback
kubectl rollout undo deployment/tta-frontend-staging -n staging
```

### 3. Add Additional Quality Checks

**Location**: Job `quality-checks`

**Example**: Add Prettier formatting check
```yaml
- name: Check code formatting
  run: npx prettier --check "src/**/*.{js,jsx,ts,tsx,json,css,md}"
```

### 4. Configure Notifications

**Location**: Job `post-deployment`

**Example**: Add Slack notification
```yaml
- name: Notify Slack
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Frontend deployed to staging: ${{ github.sha }}"
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## Troubleshooting

### Build Failures

**Symptom**: Docker build fails

**Solutions**:
1. Check Dockerfile.staging syntax
2. Verify build args are correct
3. Check for dependency installation errors
4. Review Docker build logs in workflow

### Deployment Failures

**Symptom**: Deployment step fails

**Solutions**:
1. Verify deployment commands are correct
2. Check SSH access to staging server
3. Verify Docker image was pushed successfully
4. Check staging server logs

### Health Check Failures

**Symptom**: Health checks fail after deployment

**Solutions**:
1. Verify frontend is actually running
2. Check health endpoint exists (`/health`)
3. Verify FRONTEND_BASE_URL is correct
4. Check nginx configuration
5. Review container logs

### Rollback Failures

**Symptom**: Rollback doesn't restore service

**Solutions**:
1. Manually check previous image tag
2. Verify rollback commands are correct
3. Check staging server state
4. Consider manual intervention

## Best Practices

### 1. Test Locally First
```bash
# Build Docker image locally
cd src/player_experience/frontend
docker build -f Dockerfile.staging -t tta-frontend:test .

# Run container locally
docker run -p 3001:3000 \
  -e VITE_API_BASE_URL=http://localhost:8081 \
  -e VITE_WS_URL=ws://localhost:8081 \
  tta-frontend:test
```

### 2. Use Feature Branches
- Develop in feature branches
- Test thoroughly before merging to main
- Use pull requests for code review

### 3. Monitor Deployments
- Check workflow runs regularly
- Review deployment summaries
- Monitor staging environment health

### 4. Keep Secrets Secure
- Never commit secrets to repository
- Use GitHub Secrets for sensitive data
- Rotate secrets regularly

## Integration with Existing Workflows

### Relationship to `deploy-staging.yml`
- **frontend-deploy.yml**: Focused on frontend-only changes
- **deploy-staging.yml**: Full-stack deployment (frontend + backend + infrastructure)

**When to use which**:
- Frontend changes only → `frontend-deploy.yml` (automatic)
- Backend or infrastructure changes → `deploy-staging.yml`
- Full-stack changes → `deploy-staging.yml`

### Relationship to `docker-build.yml`
- **frontend-deploy.yml**: Builds AND deploys frontend
- **docker-build.yml**: Builds all Docker images (no deployment)

**Workflow**: `docker-build.yml` validates Docker builds on PRs, `frontend-deploy.yml` deploys on main

## Maintenance

### Regular Updates
- [ ] Review and update Node.js version
- [ ] Update GitHub Actions versions
- [ ] Review and optimize caching strategy
- [ ] Update health check endpoints
- [ ] Review deployment and rollback logic

### Monitoring
- [ ] Check workflow success rate
- [ ] Monitor build times
- [ ] Review deployment frequency
- [ ] Track rollback occurrences

## Support

For issues or questions:
1. Check workflow logs in GitHub Actions
2. Review this documentation
3. Check related documentation:
   - `docs/FRONTEND_DEPLOYMENT_FIX.md`
   - `src/player_experience/frontend/README.md`
4. Contact the development team


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___.github workflows frontend deploy readme document]]
