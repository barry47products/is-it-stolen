# CI/CD Pipeline Documentation

This document describes the continuous integration and deployment pipelines for the Is It Stolen project.

## Overview

The project uses **GitHub Actions** for automated CI/CD with three main workflows:

1. **CI Pipeline** (`ci.yml`) - Tests, linting, and code quality
2. **Docker Pipeline** (`docker.yml`) - Build and push Docker images
3. **Deployment Pipeline** (`deploy.yml`) - Deploy to staging/production

## Workflows

### 1. CI Pipeline (`ci.yml`)

**Triggers**: Every push and pull request to `main`

**Jobs**:
- ✅ Linting with Ruff
- ✅ Formatting check with Ruff
- ✅ Type checking with MyPy
- ✅ Unit, integration, and E2E tests with pytest
- ✅ Code coverage reporting to Codecov
- ✅ Security scanning with SonarCloud
- ✅ Slack notifications on success/failure

**Services**:
- PostgreSQL with PostGIS (for integration tests)
- Redis (for caching and rate limiting tests)

**Caching Strategy**:
- Pip packages cache
- Poetry virtual environment cache
- MyPy cache for faster type checking

**Duration**: ~3-5 minutes

### 2. Docker Pipeline (`docker.yml`)

**Triggers**:
- Push to `main` branch
- Tags matching `v*` pattern
- Pull requests to `main` (build only, no push)

**Jobs**:
- Build Standard Docker image (`python:3.13-slim` base)
- Build Chainguard Docker image (secure, distroless)
- Push images to GitHub Container Registry (ghcr.io)
- Security scan with Trivy
- Upload security results to GitHub Security tab

**Image Tagging**:
- `latest` - Latest main branch build
- `<branch>-<sha>` - Branch-specific builds
- `v1.0.0` - Semantic versioning from tags
- `*-chainguard` - Chainguard variant suffix

**Multi-Platform**:
- linux/amd64
- linux/arm64

**Duration**: ~5-8 minutes

### 3. Deployment Pipeline (`deploy.yml`)

**Triggers**:
- Automatic: Push to `main` → Deploy to staging
- Manual: Workflow dispatch → Choose staging or production

**Jobs**:

#### Deploy to Staging
- Runs automatically on `main` branch push
- Deploys Chainguard image (secure)
- Runs smoke tests
- Slack notifications

#### Deploy to Production
- **Manual approval required** (GitHub Environments)
- Runs only via workflow_dispatch
- Deploys Chainguard image (secure)
- Runs smoke tests
- Slack notifications

**Duration**: ~2-4 minutes per environment

## Pipeline Flow

```
┌─────────────┐
│  Git Push   │
└──────┬──────┘
       │
       ├─────► CI Pipeline (tests, linting, quality)
       │            ↓
       │       ✅ All checks pass
       │            ↓
       ├─────► Docker Pipeline (build images)
       │            ↓
       │       📦 Images pushed to ghcr.io
       │            ↓
       └─────► Deploy Pipeline (staging)
                    ↓
               🔄 Staging deployed
                    ↓
               👤 Manual approval
                    ↓
               🚀 Production deployed
```

## Secrets Configuration

Required GitHub Secrets:

| Secret                | Purpose                          | Required For    |
|-----------------------|----------------------------------|-----------------|
| `CODECOV_TOKEN`       | Code coverage reporting          | CI              |
| `SONAR_TOKEN`         | SonarCloud security scanning     | CI              |
| `SLACK_WEBHOOK_URL`   | Slack notifications              | All workflows   |
| `GITHUB_TOKEN`        | Automatically provided by GitHub | Docker (GHCR)   |

### Setting Up Secrets

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add each secret with its value

### Codecov Setup
```bash
# Visit https://codecov.io
# Connect your GitHub repository
# Copy the token to CODECOV_TOKEN secret
```

### SonarCloud Setup
```bash
# Visit https://sonarcloud.io
# Import your GitHub repository
# Copy the token to SONAR_TOKEN secret
```

### Slack Setup
```bash
# Create a Slack app: https://api.slack.com/apps
# Enable Incoming Webhooks
# Add webhook to your channel
# Copy webhook URL to SLACK_WEBHOOK_URL secret
```

## GitHub Environments

### Staging Environment

**Configuration**:
- Name: `staging`
- URL: `https://staging.isitstolen.com`
- Protection rules: None (auto-deploy)
- Secrets: Staging-specific credentials

### Production Environment

**Configuration**:
- Name: `production`
- URL: `https://isitstolen.com`
- Protection rules:
  - ✅ Required reviewers (1-6 approvers)
  - ✅ Wait timer (optional, e.g., 5 minutes)
- Secrets: Production credentials

**Setting Up Environments**:
1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Enter environment name
4. Configure protection rules
5. Add environment-specific secrets

## Caching Strategy

### Poetry Dependencies
```yaml
- name: Load cached venv
  uses: actions/cache@v4
  with:
    path: .venv
    key: venv-${{ runner.os }}-3.13-${{ hashFiles('**/poetry.lock') }}
```
**Speed improvement**: ~2-3 minutes saved per run

### Docker Layers
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```
**Speed improvement**: ~3-5 minutes saved per build

### MyPy Cache
```yaml
- name: Cache MyPy
  uses: actions/cache@v4
  with:
    path: .mypy_cache
    key: mypy-${{ runner.os }}-3.13-${{ hashFiles('**/poetry.lock') }}-${{ hashFiles('**/*.py') }}
```
**Speed improvement**: ~30-60 seconds saved per run

## Notifications

### Slack Notifications

**CI Pipeline**:
- ✅ Success (main branch only)
- ❌ Failure (all branches)

**Docker Pipeline**:
- Not configured (can be added if needed)

**Deployment Pipeline**:
- ✅ Staging success
- ❌ Staging failure
- 🚀 Production success
- 🚨 Production failure

**Notification Format**:
```json
{
  "text": "✅ CI pipeline passed",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*CI Pipeline Passed* ✅\n\n*Repository:* owner/repo\n*Branch:* main\n*Commit:* abc123\n*Author:* username"
      }
    }
  ]
}
```

### Email Notifications

GitHub automatically sends email notifications for:
- Failed workflow runs (to committer)
- Deployment approvals needed
- Security alerts

## Manual Deployment

### Deploy to Staging
```bash
# Automatic on main branch push
# Or manually trigger:
gh workflow run deploy.yml -f environment=staging
```

### Deploy to Production
```bash
# Requires manual trigger:
gh workflow run deploy.yml -f environment=production

# Then approve in GitHub UI:
# Actions → Deploy → Review deployments → Approve
```

## Deployment Commands (Placeholders)

The deployment workflows include placeholder commands. Update them based on your infrastructure:

### Kubernetes
```yaml
- name: Deploy to Production
  run: |
    kubectl set image deployment/isitstolen \
      isitstolen=ghcr.io/${{ github.repository }}:${{ github.sha }}-chainguard \
      --namespace production
```

### AWS ECS
```yaml
- name: Deploy to Production
  run: |
    aws ecs update-service \
      --cluster production \
      --service isitstolen \
      --force-new-deployment
```

### Docker Compose
```yaml
- name: Deploy to Production
  run: |
    export IMAGE_TAG=${{ github.sha }}-chainguard
    docker-compose -f docker-compose.production.yml up -d
```

## Monitoring Pipeline Health

### GitHub Actions Dashboard
- View all workflow runs: **Actions** tab
- Filter by workflow, branch, or status
- Download logs for debugging

### Metrics to Track
- ✅ **Success rate**: Aim for >95%
- ⏱️ **Duration**: CI <5min, Docker <10min, Deploy <5min
- 📊 **Coverage**: Maintain >80%
- 🔒 **Security**: 0 high/critical CVEs

### Common Issues

**Issue**: Cache not working
**Solution**: Check cache key matches between save/restore

**Issue**: Docker build timeouts
**Solution**: Increase timeout or optimize Dockerfile layers

**Issue**: Tests failing in CI but passing locally
**Solution**: Check service versions (PostgreSQL, Redis)

**Issue**: Secrets not found
**Solution**: Verify secret names match exactly (case-sensitive)

## Best Practices

1. **Always run CI locally first**:
   ```bash
   make check  # Runs lint, type-check, tests
   ```

2. **Keep workflows fast**:
   - Use caching aggressively
   - Run jobs in parallel where possible
   - Minimize dependencies

3. **Security first**:
   - Never commit secrets
   - Use Chainguard images for production
   - Scan images regularly
   - Rotate secrets periodically

4. **Monitor and iterate**:
   - Review failed runs promptly
   - Optimize slow steps
   - Update dependencies regularly

## Troubleshooting

### Viewing Logs
```bash
# List recent workflow runs
gh run list

# View specific run
gh run view <run-id>

# Download logs
gh run download <run-id>
```

### Re-running Failed Jobs
```bash
# Re-run failed jobs only
gh run rerun <run-id> --failed

# Re-run entire workflow
gh run rerun <run-id>
```

### Debug Mode
Add to workflow file:
```yaml
- name: Setup tmate session
  uses: mxschmitt/action-tmate@v3
  if: failure()
```

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Codecov Action](https://github.com/codecov/codecov-action)
- [Slack GitHub Action](https://github.com/slackapi/slack-github-action)
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
