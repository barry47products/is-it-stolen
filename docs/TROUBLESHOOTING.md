# Troubleshooting Guide

## Overview

This guide provides solutions for common issues when running Is It Stolen.

---

## Quick Diagnostics

### Health Check Failed

**Symptom**: `curl http://localhost:8000/health` returns error or timeout

**Possible Causes**:

1. Application not running
2. Port 8000 already in use
3. Application crashed

**Solutions**:

```bash
# Check if application is running
ps aux | grep uvicorn

# Check port usage
lsof -i :8000

# View application logs
docker-compose logs api --tail=100

# Restart application
make run  # or docker-compose restart api
```

---

## Database Issues

### Cannot Connect to Database

**Symptom**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solutions**:

```bash
# 1. Check if PostgreSQL is running
docker-compose ps postgres
# or
pg_isready -h localhost -p 5432

# 2. Verify DATABASE_URL in .env
echo $DATABASE_URL

# 3. Test connection
docker-compose exec api poetry run python -c "
from src.infrastructure.persistence.database import init_db
init_db()
print('Database connection successful')
"

# 4. Check PostgreSQL logs
docker-compose logs postgres --tail=50

# 5. Restart PostgreSQL
docker-compose restart postgres
```

### Migration Failures

**Symptom**: `alembic.util.exc.CommandError: Can't locate revision`

**Solutions**:

```bash
# 1. Check current migration version
poetry run alembic current

# 2. Check migration history
poetry run alembic history

# 3. Downgrade and re-apply
poetry run alembic downgrade -1
poetry run alembic upgrade head

# 4. Reset database (DESTRUCTIVE - development only)
make docker-down
make docker-clean
make docker-up
make migrate-up
```

### PostGIS Extension Missing

**Symptom**: `ERROR: type "geometry" does not exist`

**Solutions**:

```sql
-- Connect to database
psql $DATABASE_URL

-- Install PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS cube;
CREATE EXTENSION IF NOT EXISTS earthdistance;

-- Verify installation
SELECT PostGIS_full_version();
```

---

## Redis Issues

### Cannot Connect to Redis

**Symptom**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solutions**:

```bash
# 1. Check if Redis is running
docker-compose ps redis
# or
redis-cli ping

# 2. Verify REDIS_URL in .env
echo $REDIS_URL

# 3. Test connection
redis-cli -u $REDIS_URL ping

# 4. Check Redis logs
docker-compose logs redis --tail=50

# 5. Restart Redis
docker-compose restart redis
```

### Rate Limit Not Working

**Symptom**: Rate limiting allows more requests than expected

**Solutions**:

```bash
# 1. Check Redis connection
redis-cli -u $REDIS_URL ping

# 2. Check rate limit keys
redis-cli -u $REDIS_URL keys "ratelimit:*"

# 3. Verify configuration
grep RATE_LIMIT .env

# 4. Clear rate limit data (testing only)
redis-cli -u $REDIS_URL flushdb
```

---

## WhatsApp Webhook Issues

### Webhook Verification Failed

**Symptom**: WhatsApp shows "Webhook verification failed"

**Solutions**:

```bash
# 1. Check WHATSAPP_WEBHOOK_VERIFY_TOKEN in .env
grep WHATSAPP_WEBHOOK_VERIFY_TOKEN .env

# 2. Test webhook endpoint
curl "http://localhost:8000/v1/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test123"
# Should return: test123

# 3. Check ngrok is running (development)
curl http://127.0.0.1:4040/api/tunnels

# 4. Verify webhook URL in Meta Developer Portal matches ngrok URL
```

### Invalid Webhook Signature

**Symptom**: `403 Forbidden: Invalid webhook signature`

**Solutions**:

```bash
# 1. Verify WHATSAPP_APP_SECRET is correct
grep WHATSAPP_APP_SECRET .env

# 2. Check X-Hub-Signature-256 header is present
docker-compose logs api | grep "X-Hub-Signature"

# 3. Test signature verification
curl -X POST http://localhost:8000/v1/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$(echo -n '{}' | openssl dgst -sha256 -hmac "$WHATSAPP_APP_SECRET" | sed 's/^.* //')" \
  -d '{}'
```

### Messages Not Being Received

**Symptom**: User sends message but bot doesn't respond

**Solutions**:

```bash
# 1. Check webhook endpoint is accessible
curl https://your-ngrok-url.ngrok-free.app/v1/webhook

# 2. Check application logs for errors
docker-compose logs api --tail=100 | grep ERROR

# 3. Verify phone number is registered in WhatsApp Business
# (Check Meta Developer Portal)

# 4. Check rate limiting
docker-compose logs api | grep "Rate limit"

# 5. Test with simple message
# Send "Hello" from WhatsApp

# 6. Check Sentry for errors (if configured)
```

---

## Session Management Issues

### Session Not Persisting

**Symptom**: Bot forgets conversation context between messages

**Solutions**:

```bash
# 1. Check Redis is running
redis-cli -u $REDIS_URL ping

# 2. Check session keys exist
redis-cli -u $REDIS_URL keys "conversation:*"

# 3. Verify SESSION_TTL setting
grep SESSION_TTL .env

# 4. Check for session cleanup
docker-compose logs api | grep "session"
```

### User Stuck in State

**Symptom**: Bot keeps asking for same information

**Solutions**:

```bash
# 1. Check user's current session state
redis-cli -u $REDIS_URL get "conversation:+447700900000"

# 2. Clear user's session
redis-cli -u $REDIS_URL del "conversation:+447700900000"

# 3. Tell user to send "cancel" to reset
```

---

## Performance Issues

### Slow Response Times

**Symptom**: API requests take > 1 second

**Solutions**:

```bash
# 1. Check database query performance
# Enable slow query logging in PostgreSQL
# Edit postgresql.conf:
log_min_duration_statement = 100  # Log queries > 100ms

# 2. Check for missing indexes
psql $DATABASE_URL -c "
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename = 'stolen_items';
"

# 3. Add indexes if needed
psql $DATABASE_URL -c "
CREATE INDEX CONCURRENTLY idx_stolen_items_category ON stolen_items(category);
"

# 4. Check connection pool
docker-compose logs api | grep "pool"

# 5. Monitor metrics
curl http://localhost:8000/metrics | grep duration
```

### High Memory Usage

**Symptom**: Application using > 1GB memory

**Solutions**:

```bash
# 1. Check current memory usage
docker stats api

# 2. Check for memory leaks
docker-compose logs api | grep -i "memory"

# 3. Reduce database connection pool size
# Edit settings.py:
DATABASE_POOL_SIZE = 10
DATABASE_MAX_OVERFLOW = 20

# 4. Restart application
docker-compose restart api
```

---

## Deployment Issues

### Docker Build Failed

**Symptom**: `docker-compose build` fails

**Solutions**:

```bash
# 1. Check Docker daemon is running
docker ps

# 2. Check for syntax errors in Dockerfile
cat Dockerfile

# 3. Clear Docker build cache
docker builder prune -a

# 4. Rebuild without cache
docker-compose build --no-cache

# 5. Check available disk space
df -h
```

### Container Keeps Restarting

**Symptom**: `docker-compose ps` shows container restarting

**Solutions**:

```bash
# 1. Check container logs
docker-compose logs api --tail=100

# 2. Check exit code
docker-compose ps api

# 3. Run container interactively for debugging
docker-compose run --rm api sh

# 4. Check health check configuration
docker inspect is-it-stolen_api_1 | grep -A 10 Healthcheck

# 5. Disable health check temporarily
# Comment out healthcheck in docker-compose.yml
```

---

## Testing Issues

### Tests Failing

**Symptom**: `make test` shows failures

**Solutions**:

```bash
# 1. Run specific failing test with verbose output
poetry run pytest tests/path/to/test.py::test_name -v

# 2. Check test database is clean
ENVIRONMENT=test make db-shell
# In psql:
\dt  -- Should show empty or test tables

# 3. Reset test database
dropdb isitstolen_test
createdb isitstolen_test

# 4. Clear pytest cache
rm -rf .pytest_cache __pycache__

# 5. Run with coverage to see what's not tested
poetry run pytest --cov=src --cov-report=html
```

### Type Checking Errors

**Symptom**: `make type-check` fails

**Solutions**:

```bash
# 1. Run mypy with verbose output
poetry run mypy src --show-error-codes

# 2. Check mypy configuration
cat pyproject.toml | grep -A 10 "\[tool.mypy\]"

# 3. Update type stubs
poetry update

# 4. Add type ignore comment for third-party imports
# type: ignore[no-any-unimported]
```

---

## Monitoring Issues

### Sentry Not Capturing Errors

**Symptom**: Errors not showing up in Sentry dashboard

**Solutions**:

```bash
# 1. Verify SENTRY_DSN is set
grep SENTRY_DSN .env

# 2. Check Sentry is initialized
docker-compose logs api | grep "Sentry initialized"

# 3. Trigger test error
curl -X POST http://localhost:8000/sentry-debug

# 4. Check Sentry configuration
grep SENTRY .env

# 5. Verify sample rate
# Edit settings.py:
SENTRY_TRACES_SAMPLE_RATE = 1.0  # Capture all events (testing only)
```

### Prometheus Metrics Not Showing

**Symptom**: `/metrics` endpoint returns 404 or empty

**Solutions**:

```bash
# 1. Check metrics endpoint is accessible
curl http://localhost:8000/metrics

# 2. Verify prometheus router is included
# Check src/presentation/api/app.py:
# app.include_router(prometheus_router)

# 3. Check if metrics are being recorded
curl http://localhost:8000/metrics | grep http_requests_total

# 4. Make some requests to generate metrics
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

---

## Security Issues

### Suspicious Activity Detected

**Symptom**: Unusual traffic patterns or error rates

**Actions**:

```bash
# 1. Check recent failed requests
docker-compose logs api | grep "403\|429" --tail=100

# 2. Identify suspicious IPs
docker-compose logs api | grep "Rate limit exceeded" | cut -d' ' -f8 | sort | uniq -c | sort -rn

# 3. Block IP temporarily
# Add to nginx.conf or firewall:
deny 1.2.3.4;

# 4. Review Sentry for errors
# Check https://sentry.io/your-org/is-it-stolen

# 5. Check for SQL injection attempts
docker-compose logs api | grep -i "select\|union\|drop"
```

### Secrets Exposed

**Symptom**: API keys or secrets found in logs or public repos

**Actions**:

```bash
# 1. IMMEDIATELY rotate all secrets
# - Generate new WHATSAPP_ACCESS_TOKEN in Meta Portal
# - Generate new SECRET_KEY
# - Update SENTRY_DSN if exposed

# 2. Update .env with new secrets
vim .env

# 3. Restart application
docker-compose down
docker-compose up -d

# 4. Check git history for exposed secrets
git log -S "your_secret" --all

# 5. If found in git, use BFG Repo-Cleaner
git clone --mirror git://github.com/your/repo.git
bfg --replace-text passwords.txt repo.git
cd repo.git
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push
```

---

## Common Error Messages

### `OperationalError: (psycopg2.OperationalError) FATAL: password authentication failed`

**Solution**: Verify `DATABASE_URL` credentials are correct

```bash
# Check .env
grep DATABASE_URL .env

# Test connection
psql $DATABASE_URL -c "SELECT version();"
```

---

### `ConnectionRefusedError: [Errno 111] Connection refused`

**Solution**: Service (PostgreSQL/Redis) not running

```bash
# Start services
make docker-up

# Check status
docker-compose ps
```

---

### `ModuleNotFoundError: No module named 'src'`

**Solution**: Python path issue

```bash
# Ensure you're in project root
pwd  # Should show /path/to/is-it-stolen

# Run with poetry
poetry run python -m src.presentation.api.app

# Or activate virtual environment
poetry shell
```

---

### `ValidationError: 1 validation error for Settings`

**Solution**: Missing or invalid environment variable

```bash
# Check which variable is invalid
poetry run python -c "from src.infrastructure.config.settings import Settings; Settings()"

# Verify .env exists and has required variables
cat .env.example  # Compare with .env
```

---

## Emergency Procedures

### Complete System Down

1. **Assess Severity**

   ```bash
   curl https://your-domain.com/health
   ```

2. **Check All Services**

   ```bash
   docker-compose ps
   ```

3. **Restart Services**

   ```bash
   docker-compose restart
   ```

4. **Check Logs**

   ```bash
   docker-compose logs --tail=200
   ```

5. **If Still Down, Rollback**

   ```bash
   git checkout main
   docker-compose down
   docker-compose up -d
   ```

6. **Notify Stakeholders**
   - Post to status page
   - Send WhatsApp broadcast (if possible)

---

### Database Corruption

1. **Stop Application**

   ```bash
   docker-compose stop api
   ```

2. **Assess Damage**

   ```bash
   psql $DATABASE_URL -c "SELECT * FROM stolen_items LIMIT 1;"
   ```

3. **Restore from Backup**

   ```bash
   # See DEPLOYMENT.md for restore procedure
   psql isitstolen < backup_latest.sql
   ```

4. **Verify Data Integrity**

   ```bash
   poetry run pytest tests/integration/test_database.py
   ```

5. **Resume Service**

   ```bash
   docker-compose start api
   ```

---

## Getting Help

### Before Asking for Help

Collect this information:

```bash
# 1. Version information
git log -1 --oneline
poetry show | head -20

# 2. Environment
echo $ENVIRONMENT
docker-compose version
poetry --version

# 3. Recent logs
docker-compose logs api --tail=100 > logs.txt

# 4. Error messages
docker-compose logs api | grep ERROR > errors.txt

# 5. System info
uname -a
docker info
```

### Where to Get Help

- **GitHub Issues**: [github.com/barry47products/is-it-stolen/issues](https://github.com/barry47products/is-it-stolen/issues)
- **Discussions**: [github.com/barry47products/is-it-stolen/discussions](https://github.com/barry47products/is-it-stolen/discussions)
- **Email**: `support@your-domain.com`

---

## Additional Resources

- [Deployment Guide](DEPLOYMENT.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [API Documentation](API.md)
- [Database Schema](DATABASE.md)
- [Security Policy](../SECURITY.md)
