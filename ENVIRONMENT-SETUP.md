# GitHub Environments Setup Guide

This guide walks you through setting up GitHub Environments for the deployment workflow.

## Why GitHub Environments?

GitHub Environments provide:
- **Protection rules** (required reviewers, wait timers)
- **Secrets** specific to each environment
- **Deployment history** and rollback capabilities
- **URL tracking** for each environment

## Prerequisites

- Repository admin access
- Staging and production infrastructure ready
- Deployment credentials available

## Step-by-Step Setup

### 1. Create Staging Environment

1. Go to your repository on GitHub
2. Click **Settings** → **Environments**
3. Click **New environment**
4. Enter name: `staging`
5. Click **Configure environment**

**Configure Protection Rules** (Optional for staging):
- ☐ Required reviewers (leave unchecked for auto-deploy)
- ☐ Wait timer (leave unchecked for immediate deploy)
- ☐ Deployment branches (select "main" only)

**Add Environment Secrets**:
1. Click **Add secret**
2. Add staging-specific secrets:
   - Database credentials
   - API keys
   - Service URLs
   - etc.

**Environment URL**:
- Enter: `https://staging.isitstolen.com` (or your actual staging URL)

6. Click **Save protection rules**

### 2. Create Production Environment

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Enter name: `production`
4. Click **Configure environment**

**Configure Protection Rules** (Recommended for production):
- ✅ **Required reviewers**: Select 1-6 team members
  - These people must approve deployments
  - Can't approve your own deployments

- ✅ **Wait timer** (optional): Set delay before deployment
  - Example: 5 minutes to review deployment

- ✅ **Deployment branches**: Select "main" only
  - Prevents accidental deployments from feature branches

**Add Environment Secrets**:
1. Click **Add secret**
2. Add production-specific secrets:
   - Production database credentials
   - Production API keys
   - Production service URLs
   - etc.

**Environment URL**:
- Enter: `https://isitstolen.com` (or your actual production URL)

6. Click **Save protection rules**

### 3. Enable Deployment Workflow

Once environments are configured:

1. Edit `.github/workflows/deploy.yml`
2. Uncomment the `environment` sections:

```yaml
# Change from:
# environment:
#   name: staging
#   url: https://staging.isitstolen.com

# To:
environment:
  name: staging
  url: https://staging.isitstolen.com
```

3. Commit and push the changes

### 4. Test Deployment

**Test Staging Deployment**:
```bash
# Push to main (automatic)
git push origin main

# Or trigger manually
gh workflow run deploy.yml -f environment=staging
```

**Test Production Deployment**:
```bash
# Trigger manually (requires approval)
gh workflow run deploy.yml -f environment=production

# Then in GitHub:
# 1. Go to Actions → Deploy workflow
# 2. Click on the running workflow
# 3. Click "Review deployments"
# 4. Select "production"
# 5. Click "Approve and deploy"
```

## Environment-Specific Secrets

### Staging Secrets

Example secrets for staging environment:

| Secret Name                | Description                    | Example Value                                      |
|----------------------------|--------------------------------|----------------------------------------------------|
| `DATABASE_URL`             | Staging database connection    | `postgresql://user:pass@staging-db:5432/isitstolen` |
| `REDIS_URL`                | Staging Redis connection       | `redis://staging-redis:6379`                       |
| `WHATSAPP_ACCESS_TOKEN`    | Staging WhatsApp token         | `staging_token_xxx`                                |
| `DEPLOY_KEY`               | SSH key for deployment         | `-----BEGIN RSA PRIVATE KEY-----...`               |

### Production Secrets

Example secrets for production environment:

| Secret Name                | Description                    | Example Value                                      |
|----------------------------|--------------------------------|----------------------------------------------------|
| `DATABASE_URL`             | Production database connection | `postgresql://user:pass@prod-db:5432/isitstolen`  |
| `REDIS_URL`                | Production Redis connection    | `redis://prod-redis:6379`                          |
| `WHATSAPP_ACCESS_TOKEN`    | Production WhatsApp token      | `prod_token_xxx`                                   |
| `DEPLOY_KEY`               | SSH key for deployment         | `-----BEGIN RSA PRIVATE KEY-----...`               |
| `ROLLBAR_TOKEN`            | Error tracking                 | `prod_rollbar_xxx`                                 |

## Deployment Commands

Update the deployment workflow with your actual commands:

### Kubernetes Example

```yaml
- name: Deploy to Production
  run: |
    echo "${{ secrets.KUBE_CONFIG }}" > kubeconfig
    export KUBECONFIG=./kubeconfig

    kubectl set image deployment/isitstolen \
      isitstolen=ghcr.io/${{ github.repository }}:${{ github.sha }}-chainguard \
      --namespace production

    kubectl rollout status deployment/isitstolen -n production
```

### AWS ECS Example

```yaml
- name: Deploy to Production
  run: |
    aws configure set aws_access_key_id ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws configure set aws_secret_access_key ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws configure set region us-east-1

    aws ecs update-service \
      --cluster production \
      --service isitstolen \
      --force-new-deployment \
      --desired-count 3
```

### Docker Compose Example

```yaml
- name: Deploy to Production
  run: |
    ssh -i ${{ secrets.DEPLOY_KEY }} user@production-server << 'EOF'
      cd /opt/isitstolen
      export IMAGE_TAG=${{ github.sha }}-chainguard
      docker-compose -f docker-compose.production.yml pull
      docker-compose -f docker-compose.production.yml up -d
      docker-compose -f docker-compose.production.yml ps
    EOF
```

## Smoke Tests

Add smoke tests to validate deployments:

```yaml
- name: Run smoke tests
  run: |
    # Wait for deployment to stabilize
    sleep 30

    # Check health endpoint
    curl -f https://staging.isitstolen.com/health || exit 1

    # Check metrics endpoint
    curl -f https://staging.isitstolen.com/metrics || exit 1

    # Test critical API endpoint
    response=$(curl -s -o /dev/null -w "%{http_code}" https://staging.isitstolen.com/v1/webhook)
    if [ $response != "405" ]; then  # Expect 405 without proper payload
      echo "Webhook endpoint not responding correctly"
      exit 1
    fi

    echo "✅ All smoke tests passed"
```

## Monitoring Deployments

### View Deployment History

1. Go to repository **Settings** → **Environments**
2. Click on environment name (e.g., "production")
3. View **Deployment history**
4. See all deployments, who approved, when deployed

### Rollback a Deployment

**Method 1: Redeploy Previous Version**
```bash
# Find previous successful SHA
gh run list --workflow=deploy.yml --status=success --limit=5

# Deploy that version
gh workflow run deploy.yml -f environment=production
# (Use the previous SHA in your deployment commands)
```

**Method 2: Revert and Redeploy**
```bash
# Revert the problematic commit
git revert <bad-commit-sha>
git push origin main

# This triggers staging deployment
# Then manually deploy to production
```

## Troubleshooting

### Environment Not Found

**Error**: `Environment 'staging' not found`

**Solution**:
1. Verify environment exists in Settings → Environments
2. Ensure environment name matches exactly (case-sensitive)
3. Check you have permissions to deploy to environment

### Deployment Pending Forever

**Error**: Deployment stuck in "Waiting for approval"

**Solution**:
1. Check if you configured required reviewers
2. Ensure reviewer is notified
3. Reviewer must approve in Actions → Workflow Run → Review deployments

### Secrets Not Available

**Error**: Secret is undefined in deployment

**Solution**:
1. Verify secret exists in environment (not repository secrets)
2. Check secret name matches exactly
3. Ensure you're accessing it correctly: `${{ secrets.SECRET_NAME }}`

### Deployment Fails After Approval

**Error**: Deployment commands fail

**Solution**:
1. Check deployment commands are correct for your infrastructure
2. Verify environment secrets are set correctly
3. Test deployment commands locally first
4. Check service/cluster exists and is accessible

## Security Best Practices

1. **Never commit secrets** - Use GitHub Secrets only
2. **Rotate secrets regularly** - Update every 90 days
3. **Limit approvers** - Only trusted team members
4. **Use service accounts** - Not personal credentials
5. **Enable 2FA** - For all team members
6. **Audit deployments** - Review deployment history regularly
7. **Test in staging first** - Always validate before production

## Next Steps

After environment setup:

1. ✅ Configure staging environment
2. ✅ Configure production environment
3. ✅ Update deployment commands in `deploy.yml`
4. ✅ Uncomment environment sections in workflow
5. ✅ Test staging deployment
6. ✅ Test production deployment with approval
7. ✅ Set up monitoring and alerts
8. ✅ Document rollback procedures

## References

- [GitHub Environments Documentation](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [Deployment Protection Rules](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment#environment-protection-rules)
- [Environment Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets#creating-encrypted-secrets-for-an-environment)
