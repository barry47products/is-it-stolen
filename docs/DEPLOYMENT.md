# Deployment Guide

## Overview

This guide covers deploying Is It Stolen to production environments.

## Prerequisites

- Docker and Docker Compose installed
- Domain name with DNS configured
- SSL certificate (Let's Encrypt recommended)
- WhatsApp Business Account configured
- PostgreSQL 15+ with PostGIS extension
- Redis 7+

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/barry47products/is-it-stolen.git
cd is-it-stolen
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with production values:

```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info
LOG_FORMAT=json
LOG_REDACT_SENSITIVE=true

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/isitstolen

# Redis
REDIS_URL=redis://:password@redis:6379

# WhatsApp (from Meta Developer Portal)
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token
WHATSAPP_APP_SECRET=your_app_secret

# Sentry (optional but recommended)
SENTRY_DSN=https://your_sentry_dsn
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Security
SECRET_KEY=generate_strong_random_key_here

# Server
PORT=8000
WORKERS=4
```

### 3. Generate Secrets

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate WHATSAPP_WEBHOOK_VERIFY_TOKEN
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Deployment Options

### Option 1: Docker Compose (Recommended for Small Scale)

#### 1. Build Images

```bash
docker-compose build
```

#### 2. Start Services

```bash
docker-compose up -d
```

#### 3. Run Migrations

```bash
docker-compose exec api poetry run alembic upgrade head
```

#### 4. Verify Deployment

```bash
curl http://localhost:8000/health
```

#### 5. View Logs

```bash
docker-compose logs -f api
```

### Monitoring

```bash
# Check service status
docker-compose ps

# View resource usage
docker stats

# Check logs for errors
docker-compose logs api | grep ERROR
```

---

### Option 2: Kubernetes (Recommended for Production)

#### 1. Create Namespace

```bash
kubectl create namespace is-it-stolen
```

#### 2. Create Secrets

```bash
kubectl create secret generic app-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=redis-url="redis://..." \
  --from-literal=whatsapp-access-token="..." \
  --from-literal=sentry-dsn="..." \
  -n is-it-stolen
```

#### 3. Deploy Database

```bash
kubectl apply -f k8s/postgres.yaml -n is-it-stolen
```

#### 4. Deploy Redis

```bash
kubectl apply -f k8s/redis.yaml -n is-it-stolen
```

#### 5. Deploy Application

```bash
kubectl apply -f k8s/deployment.yaml -n is-it-stolen
kubectl apply -f k8s/service.yaml -n is-it-stolen
kubectl apply -f k8s/ingress.yaml -n is-it-stolen
```

#### 6. Run Migrations

```bash
kubectl exec -it deployment/api -n is-it-stolen -- poetry run alembic upgrade head
```

#### 7. Verify Deployment

```bash
kubectl get pods -n is-it-stolen
kubectl logs -f deployment/api -n is-it-stolen
```

---

### Option 3: Cloud Platforms

#### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Add PostgreSQL
railway add postgresql

# Add Redis
railway add redis

# Deploy
railway up
```

#### Heroku

```bash
# Install Heroku CLI
brew install heroku/brew/heroku

# Login
heroku login

# Create app
heroku create is-it-stolen

# Add addons
heroku addons:create heroku-postgresql:standard-0
heroku addons:create heroku-redis:premium-0

# Set environment variables
heroku config:set ENVIRONMENT=production
heroku config:set WHATSAPP_ACCESS_TOKEN=...

# Deploy
git push heroku main

# Run migrations
heroku run poetry run alembic upgrade head
```

#### DigitalOcean App Platform

1. Connect GitHub repository
2. Configure environment variables in dashboard
3. Add PostgreSQL and Redis databases
4. Deploy from dashboard

---

## Database Setup

### PostgreSQL with PostGIS

#### 1. Install PostGIS Extension

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS cube;
CREATE EXTENSION IF NOT EXISTS earthdistance;
```

#### 2. Run Migrations

```bash
# Development
make migrate-up

# Production (Docker)
docker-compose exec api poetry run alembic upgrade head

# Production (K8s)
kubectl exec -it deployment/api -- poetry run alembic upgrade head
```

#### 3. Verify Schema

```sql
\dt  -- List tables
SELECT PostGIS_full_version();  -- Verify PostGIS
```

---

## SSL/TLS Configuration

### Option 1: Let's Encrypt with Nginx

#### nginx.conf

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Get Certificate

```bash
certbot certonly --webroot -w /var/www/html -d your-domain.com
```

### Option 2: Cloudflare SSL

1. Add domain to Cloudflare
2. Set DNS to proxy through Cloudflare
3. Enable "Full (strict)" SSL mode
4. Enable "Always Use HTTPS"
5. Enable "Auto HTTPS Rewrites"

---

## WhatsApp Configuration

### 1. Configure Webhook URL

In Meta Developer Portal:

- **Webhook URL**: `https://your-domain.com/v1/webhook`
- **Verify Token**: Value from `WHATSAPP_WEBHOOK_VERIFY_TOKEN`

### 2. Subscribe to Webhook Fields

Enable subscriptions for:

- `messages`
- `message_status` (optional)

### 3. Test Webhook

```bash
# Send test message from WhatsApp
echo "Hello" # Should receive 200 OK response
```

### 4. Verify Logs

```bash
# Check for incoming webhooks
docker-compose logs api | grep webhook

# Should see:
# INFO - Webhook received from +447700900000
# INFO - Message processed successfully
```

---

## Monitoring Setup

### Sentry Error Tracking

1. Create project at [sentry.io](https://sentry.io)
2. Copy DSN
3. Set `SENTRY_DSN` environment variable
4. Deploy

Verify:

```bash
# Trigger test error
curl -X POST https://your-domain.com/sentry-debug
```

### Prometheus + Grafana

#### docker-compose.yml

```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

#### prometheus.yml

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "is-it-stolen"
    static_configs:
      - targets: ["api:8000"]
```

Access Grafana at `http://localhost:3000` and import dashboard from `grafana/dashboard.json`.

---

## Backup Strategy

### Database Backups

#### Automated Daily Backups

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="isitstolen"

# Create backup
pg_dump $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz s3://your-bucket/backups/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

#### Cron Job

```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup.sh
```

### Restore from Backup

```bash
# Extract backup
gunzip backup_20251006_020000.sql.gz

# Restore
psql isitstolen < backup_20251006_020000.sql
```

---

## Health Checks

### Kubernetes Liveness Probe

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### Kubernetes Readiness Probe

```yaml
readinessProbe:
  httpGet:
    path: /v1/health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### Docker Compose Healthcheck

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

## Scaling

### Horizontal Scaling

#### Docker Compose

```bash
docker-compose up -d --scale api=3
```

#### Kubernetes

```bash
kubectl scale deployment api --replicas=3 -n is-it-stolen
```

### Vertical Scaling

#### Update resource limits

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Database Connection Pooling

Configure in `settings.py`:

```python
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 40
```

---

## Security Checklist

- [ ] Environment variables secured (not committed)
- [ ] SSL/TLS enabled (HTTPS only)
- [ ] Webhook signature verification enabled
- [ ] Rate limiting configured
- [ ] CORS configured for production domains
- [ ] Database credentials rotated
- [ ] Firewall rules configured
- [ ] Regular security updates applied
- [ ] Secrets stored in vault (not .env files)
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery tested
- [ ] DDoS protection enabled (Cloudflare)

---

## Rollback Procedure

### Docker Compose Rollback

```bash
# Tag current version
docker tag is-it-stolen:latest is-it-stolen:v1.0.0

# Rollback to previous version
docker-compose down
docker-compose pull  # or docker tag is-it-stolen:v0.9.0 is-it-stolen:latest
docker-compose up -d
```

### Kubernetes Rollback

```bash
# Rollback to previous revision
kubectl rollout undo deployment/api -n is-it-stolen

# Rollback to specific revision
kubectl rollout undo deployment/api --to-revision=2 -n is-it-stolen
```

### Database Migrations

```bash
# Rollback one migration
poetry run alembic downgrade -1

# Rollback to specific version
poetry run alembic downgrade abc123
```

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

### Quick Diagnostics

```bash
# Check service health
curl https://your-domain.com/health

# Check database connection
docker-compose exec api poetry run python -c "from src.infrastructure.persistence.database import init_db; init_db()"

# Check Redis connection
docker-compose exec redis redis-cli ping

# View recent errors
docker-compose logs api --tail=100 | grep ERROR

# Check metrics
curl https://your-domain.com/metrics | grep error
```

---

## Post-Deployment Validation

### 1. Smoke Tests

```bash
# Health check
curl https://your-domain.com/health

# Webhook verification
curl "https://your-domain.com/v1/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test"

# Metrics endpoint
curl https://your-domain.com/metrics
```

### 2. Functional Tests

```bash
# Run integration tests
poetry run pytest tests/integration/

# Run E2E tests
poetry run pytest tests/e2e/
```

### 3. Load Testing

```bash
# Install k6
brew install k6

# Run load test
k6 run tests/load/webhook_test.js
```

---

## Maintenance Windows

### Planned Downtime

1. Notify users via WhatsApp broadcast
2. Set maintenance mode in load balancer
3. Drain connections
4. Perform maintenance
5. Run smoke tests
6. Restore traffic
7. Monitor for issues

### Zero-Downtime Deployments

1. Deploy new version alongside old
2. Run database migrations (backward compatible)
3. Shift traffic gradually (canary deployment)
4. Monitor error rates
5. Complete rollout or rollback

---

## Support Contacts

- **On-Call Engineer**: `on-call@your-domain.com`
- **Sentry**: `https://sentry.io/your-org/is-it-stolen`
- **Status Page**: `https://status.your-domain.com`
- **Runbook**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## Additional Resources

- [Architecture Documentation](ARCHITECTURE.md)
- [API Documentation](API.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Database Schema](DATABASE.md)
- [Security Policy](../SECURITY.md)
