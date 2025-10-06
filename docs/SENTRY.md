# Sentry Error Tracking Integration

This document describes the Sentry integration for error tracking and performance monitoring in the Is It Stolen application.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Setup](#setup)
- [Configuration](#configuration)
- [Privacy & Security](#privacy--security)
- [Usage](#usage)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Overview

Sentry provides real-time error tracking and performance monitoring, helping identify and resolve issues quickly in production environments.

**Key Benefits:**
- Real-time error notifications
- Performance transaction tracking
- User-specific error context
- Automatic issue grouping and deduplication
- Privacy-compliant data filtering

## Features

### Automatic Error Capture
- Uncaught exceptions
- HTTP errors (4xx, 5xx)
- Database errors
- WhatsApp API failures

### Performance Monitoring
- API endpoint response times
- Database query performance
- Redis operation latency
- WhatsApp API call duration

### Integrations
- **FastAPI**: Automatic transaction creation for API requests
- **Redis**: Redis operation tracing
- **Logging**: Capture ERROR level logs as Sentry events

### Privacy-First Design
- Automatic scrubbing of sensitive data
- No PII sent by default
- Configurable sample rates to control data volume

## Setup

### 1. Create Sentry Project

1. Sign up at [sentry.io](https://sentry.io) (free tier available)
2. Create a new project:
   - Choose **Python** as the platform
   - Name it "is-it-stolen"
   - Select your team
3. Get your DSN from **Settings → Projects → is-it-stolen → Client Keys (DSN)**

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Sentry Error Tracking
SENTRY_DSN=https://your-key@o123456.ingest.sentry.io/7654321
SENTRY_ENVIRONMENT=production  # or staging, development
SENTRY_RELEASE=v1.0.0  # or git SHA: $(git rev-parse HEAD)
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 10% of transactions
```

**Important:**
- Leave `SENTRY_DSN` empty in development to disable Sentry
- Use different projects for staging and production
- Set sample rates based on your traffic volume

### 3. Set Release Version

For better tracking, set the release version to your git commit SHA:

```bash
# In your deployment script or CI/CD pipeline
export SENTRY_RELEASE=$(git rev-parse HEAD)
```

Or use a version number:

```bash
export SENTRY_RELEASE=v1.0.0
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENTRY_DSN` | No | `""` | Sentry Data Source Name (leave empty to disable) |
| `SENTRY_ENVIRONMENT` | No | `development` | Environment name (development, staging, production) |
| `SENTRY_RELEASE` | No | `unknown` | Release version or git SHA |
| `SENTRY_TRACES_SAMPLE_RATE` | No | `0.1` | Percentage of transactions to track (0.0-1.0) |
| `SENTRY_PROFILES_SAMPLE_RATE` | No | `0.1` | Percentage of transactions to profile (0.0-1.0) |

### Sample Rate Recommendations

**Development:**
```bash
SENTRY_DSN=  # Leave empty - disable Sentry in dev
```

**Staging:**
```bash
SENTRY_TRACES_SAMPLE_RATE=1.0  # 100% - track all requests
SENTRY_PROFILES_SAMPLE_RATE=1.0
```

**Production (Low Traffic < 1000 req/day):**
```bash
SENTRY_TRACES_SAMPLE_RATE=0.5  # 50%
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 10%
```

**Production (High Traffic > 10000 req/day):**
```bash
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10%
SENTRY_PROFILES_SAMPLE_RATE=0.01  # 1%
```

## Privacy & Security

### Automatic Data Scrubbing

The integration **automatically scrubs** sensitive data before sending to Sentry:

**Scrubbed Fields (case-insensitive matching):**
- Passwords: `password`, `passwd`, `pwd`
- Tokens: `token`, `access_token`, `refresh_token`, `bearer_token`
- API Keys: `api_key`, `api`, `key`
- Auth: `authorization`, `auth`, `secret`
- Sessions: `cookie`, `session`, `csrf`
- Financial: `credit_card`, `card_number`, `cvv`, `pin`, `ssn`

**Example:**

```python
# Original error data
{
    "user": "john@example.com",
    "password": "secret123",
    "access_token": "abc123xyz"
}

# Sent to Sentry (scrubbed)
{
    "user": "john@example.com",
    "password": "[Filtered]",
    "access_token": "[Filtered]"
}
```

### Privacy Settings

- `send_default_pii=False`: No PII sent by default
- Custom `before_send` callback: Scrubs sensitive data
- Nested data scrubbing: Works recursively through dictionaries

### Best Practices

1. **Never log sensitive data:** Even with scrubbing, avoid logging passwords/tokens
2. **Review Sentry events:** Periodically check for any leaked sensitive data
3. **Use separate projects:** Different projects for dev/staging/production
4. **Rotate keys:** If you suspect a leak, rotate API keys and regenerate Sentry DSN

## Usage

### Automatic Error Capture

Errors are captured automatically - no code changes needed:

```python
# This error is automatically sent to Sentry
raise ValueError("Invalid item category")
```

### Manual Error Capture

Capture errors with additional context:

```python
from src.infrastructure.monitoring.sentry import capture_exception

try:
    process_stolen_item(item_id)
except Exception as e:
    capture_exception(e, item_id=item_id, user_phone="+1234567890")
    raise
```

### Capture Messages

Send informational messages:

```python
from src.infrastructure.monitoring.sentry import capture_message

capture_message("Unusual activity detected", level="warning", user_id="123")
```

### Set User Context

Track errors by user:

```python
from src.infrastructure.monitoring.sentry import set_user

set_user(user_id="+1234567890", phone="+1234567890", location="London")
```

### Add Tags

Tag errors for better organization:

```python
from src.infrastructure.monitoring.sentry import set_tag

set_tag("category", "bicycle")
set_tag("reported_via", "whatsapp")
```

### Add Context

Add structured context data:

```python
from src.infrastructure.monitoring.sentry import set_context

set_context("report_details", {
    "category": "bicycle",
    "location": "London",
    "description": "Red mountain bike"
})
```

## Monitoring

### Sentry Dashboard

Access your Sentry dashboard at `https://sentry.io/organizations/YOUR_ORG/issues/`

**Key Sections:**

1. **Issues**: Grouped errors with frequency and affected users
2. **Performance**: Transaction traces and slow queries
3. **Releases**: Errors by release version
4. **Alerts**: Configure email/Slack notifications

### Alert Rules

Configure alerts for critical errors:

1. Go to **Alerts → Create Alert**
2. Choose conditions:
   - Error rate exceeds threshold
   - Specific error types
   - Performance degradation
3. Set notification channels (email, Slack, PagerDuty)

**Recommended Alerts:**

- **Critical Errors**: Any error affecting > 10 users/hour
- **Performance**: API response time > 2 seconds
- **Error Rate**: > 100 errors/minute

### Key Metrics to Monitor

- **Error Rate**: Errors per minute/hour
- **Affected Users**: Unique users experiencing errors
- **Response Time P95**: 95th percentile API response time
- **Apdex Score**: Application performance index

## Troubleshooting

### Sentry Not Capturing Errors

**Problem:** Errors are not appearing in Sentry

**Solutions:**

1. **Check DSN is set:**
   ```bash
   echo $SENTRY_DSN
   # Should output: https://...@sentry.io/...
   ```

2. **Check initialization logs:**
   ```bash
   # Look for this log on app startup
   "Sentry initialized for environment 'production' with release 'v1.0.0'"
   ```

3. **Test manually:**
   ```python
   from src.infrastructure.monitoring.sentry import capture_message
   capture_message("Test message", level="info")
   ```

4. **Check network connectivity:**
   ```bash
   curl -I https://sentry.io
   # Should return: HTTP/2 200
   ```

### Too Many Events

**Problem:** Sentry quota exhausted due to too many events

**Solutions:**

1. **Reduce sample rates** in `.env`:
   ```bash
   SENTRY_TRACES_SAMPLE_RATE=0.01  # 1%
   SENTRY_PROFILES_SAMPLE_RATE=0.001  # 0.1%
   ```

2. **Filter noisy errors** by adding to `before_send`:
   ```python
   def before_send(event, hint):
       # Ignore specific errors
       if event.get("exception", {}).get("values", [{}])[0].get("type") == "ValidationError":
           return None  # Don't send to Sentry
       return event
   ```

3. **Upgrade Sentry plan** for higher quotas

### Sensitive Data Leaked

**Problem:** Sensitive data visible in Sentry events

**Immediate Actions:**

1. **Delete leaked events** in Sentry dashboard
2. **Rotate exposed secrets** (API keys, tokens)
3. **Review scrubbing config** in `src/infrastructure/monitoring/sentry.py`

**Prevention:**

1. Add field patterns to `SENSITIVE_KEYS` in `sentry.py`
2. Review `before_send` callback implementation
3. Test scrubbing with unit tests

### Performance Overhead

**Problem:** Sentry causing performance issues

**Solutions:**

1. **Disable profiling:**
   ```bash
   SENTRY_PROFILES_SAMPLE_RATE=0.0
   ```

2. **Reduce trace sample rate:**
   ```bash
   SENTRY_TRACES_SAMPLE_RATE=0.01  # 1%
   ```

3. **Disable in development:**
   ```bash
   SENTRY_DSN=  # Empty = disabled
   ```

## Resources

- **Sentry Docs**: https://docs.sentry.io/platforms/python/
- **FastAPI Integration**: https://docs.sentry.io/platforms/python/integrations/fastapi/
- **Performance Monitoring**: https://docs.sentry.io/product/performance/
- **Data Scrubbing**: https://docs.sentry.io/platforms/python/data-management/sensitive-data/

## Support

- **Sentry Issues**: https://github.com/getsentry/sentry-python/issues
- **Community Forum**: https://forum.sentry.io/
- **Is It Stolen Issues**: https://github.com/barry47products/is-it-stolen/issues
