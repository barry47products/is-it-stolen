# API Documentation

## Overview

The Is It Stolen API is a REST API built with FastAPI that powers the WhatsApp bot for checking and reporting stolen items.

**Base URL (Development)**: `http://localhost:8000`

**Base URL (Production)**: `https://your-domain.com`

## API Endpoints

### Interactive Documentation

When running in development mode, FastAPI provides auto-generated interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### Health & Monitoring

#### GET /health

Root level health check endpoint.

**Response**:

```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

**Status Codes**:

- `200`: Service is healthy
- `500`: Service is unhealthy

---

#### GET /v1/health

Detailed health check with database and cache connectivity.

**Response**:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-10-06T09:00:00Z",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

**Status Codes**:

- `200`: All services healthy
- `503`: One or more services unhealthy

---

#### GET /metrics

Prometheus metrics endpoint for monitoring.

**Response**: Prometheus text format

**Metrics Exposed**:

- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration histogram
- `active_sessions_total` - Active WhatsApp sessions
- `stolen_items_total` - Total stolen items reported
- `reports_verified_total` - Total verified reports

---

### WhatsApp Webhook

#### GET /v1/webhook

WhatsApp webhook verification endpoint.

**Query Parameters**:

- `hub.mode` (string, required): Should be "subscribe"
- `hub.verify_token` (string, required): Your webhook verify token
- `hub.challenge` (string, required): Challenge string from WhatsApp

**Response**: Plain text challenge string

**Status Codes**:

- `200`: Verification successful
- `403`: Invalid verify token

**Example**:

```bash
curl "http://localhost:8000/v1/webhook?hub.mode=subscribe&hub.verify_token=your_token&hub.challenge=test123"
```

---

#### POST /v1/webhook

WhatsApp incoming message webhook.

**Headers**:

- `X-Hub-Signature-256` (required): HMAC SHA256 signature for verification
- `Content-Type`: `application/json`

**Request Body**:

```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "BUSINESS_ACCOUNT_ID",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15551234567",
              "phone_number_id": "PHONE_NUMBER_ID"
            },
            "messages": [
              {
                "from": "447700900000",
                "id": "wamid.xxx",
                "timestamp": "1633024800",
                "type": "text",
                "text": {
                  "body": "Hello"
                }
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

**Response**:

```json
{
  "status": "ok"
}
```

**Status Codes**:

- `200`: Message processed successfully
- `400`: Invalid request body
- `403`: Invalid signature
- `429`: Rate limit exceeded

---

## Rate Limiting

All webhook endpoints are rate-limited to prevent abuse.

**Default Limits**:

- **Per IP**: 60 requests per minute
- **Per User**: 20 messages per minute

**Rate Limit Headers**:

```bash
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1633024860
```

**Rate Limit Response**:

```json
{
  "detail": "Rate limit exceeded. Try again in 30 seconds."
}
```

---

## Authentication

### Webhook Signature Verification

All incoming webhook requests must include a valid `X-Hub-Signature-256` header.

**Signature Calculation**:

```python
import hmac
import hashlib

payload = request.body
secret = WHATSAPP_APP_SECRET

signature = "sha256=" + hmac.new(
    secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()
```

**Verification**:
The API automatically verifies signatures using `secrets.compare_digest()` for timing-attack resistance.

---

## Error Handling

### Error Response Format

All errors return a consistent JSON structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning               | Description                          |
| ---- | --------------------- | ------------------------------------ |
| 200  | OK                    | Request successful                   |
| 400  | Bad Request           | Invalid request format or parameters |
| 403  | Forbidden             | Invalid credentials or signature     |
| 404  | Not Found             | Endpoint does not exist              |
| 422  | Unprocessable Entity  | Validation error                     |
| 429  | Too Many Requests     | Rate limit exceeded                  |
| 500  | Internal Server Error | Server error occurred                |
| 503  | Service Unavailable   | Service temporarily unavailable      |

### Common Error Scenarios

#### Invalid Webhook Signature

```json
{
  "detail": "Invalid webhook signature"
}
```

#### Rate Limit Exceeded

```json
{
  "detail": "Rate limit exceeded. Try again in 30 seconds."
}
```

#### Invalid Message Format

```json
{
  "detail": "Invalid message format: missing required field 'from'"
}
```

---

## Request Tracing

Every request is assigned a unique `request_id` for tracing.

**Response Header**:

```bash
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

Use this ID when reporting issues or debugging.

---

## CORS Configuration

CORS is enabled for all origins in development.

**Allowed Origins**: `*` (development)
**Allowed Methods**: `GET, POST, PUT, DELETE, OPTIONS`
**Allowed Headers**: `*`

> **Production**: Configure `CORS_ORIGINS` environment variable with specific domains

---

## Development

### Running Locally

```bash
# Start services
make docker-up

# Run API
make run

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Testing API

```bash
# Health check
curl http://localhost:8000/health

# Webhook verification
curl "http://localhost:8000/v1/webhook?hub.mode=subscribe&hub.verify_token=your_token&hub.challenge=test"

# View metrics
curl http://localhost:8000/metrics
```

---

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment guide.

### Environment Variables

See [.env.example](../.env.example) for all required environment variables.

**Required for Production**:

- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_BUSINESS_ACCOUNT_ID`
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
- `WHATSAPP_APP_SECRET`
- `DATABASE_URL`
- `REDIS_URL`

### Security Considerations

1. **Always verify webhook signatures** - Prevents unauthorized access
2. **Use HTTPS in production** - Protects data in transit
3. **Rate limit aggressively** - Prevents abuse
4. **Monitor logs for suspicious activity** - Early detection
5. **Keep secrets secure** - Never commit `.env` files

---

## Monitoring

### Prometheus Metrics

Scrape `/metrics` endpoint for monitoring:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: "is-it-stolen"
    static_configs:
      - targets: ["localhost:8000"]
```

### Grafana Dashboards

Import `grafana/dashboard.json` for pre-built dashboards.

### Sentry Error Tracking

Configure `SENTRY_DSN` to enable error tracking.

See [docs/SENTRY.md](SENTRY.md) for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/barry47products/is-it-stolen/issues)
- **Discussions**: [GitHub Discussions](https://github.com/barry47products/is-it-stolen/discussions)
