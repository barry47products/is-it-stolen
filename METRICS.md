# Metrics and Monitoring

Is It Stolen provides comprehensive metrics tracking with both JSON and Prometheus endpoints.

## Quick Start

### 1. Start Metrics Stack

```bash
# Start PostgreSQL, Redis, Prometheus, and Grafana
make docker-up

# Start the FastAPI application
make run
```

### 2. Access Metrics

- **JSON Metrics**: `http://localhost:8000/v1/metrics`
- **Prometheus Metrics**: `http://localhost:8000/metrics`
- **Prometheus UI**: `http://localhost:9090`
- **Grafana Dashboard**: `http://localhost:3000 (admin/admin)`

## Metrics Tracked

### Automatic Tracking

All metrics are automatically collected during normal bot operation:

| Metric                    | Type      | Description                        | When Incremented                |
| ------------------------- | --------- | ---------------------------------- | ------------------------------- |
| `messages_received_total` | Counter   | Total messages received from users | Every incoming WhatsApp message |
| `messages_sent_total`     | Counter   | Total messages sent to users       | Every outgoing WhatsApp message |
| `reports_created_total`   | Counter   | Total stolen item reports          | When user completes report flow |
| `items_checked_total`     | Counter   | Total item check queries           | When user checks if item stolen |
| `response_time_seconds`   | Histogram | Message processing time            | Every message processed         |
| `active_users_total`      | Gauge     | Unique active users                | Per unique phone number         |

### Response Time Buckets

The `response_time_seconds` histogram uses these buckets for percentile calculations:

- 0.01s (10ms)
- 0.05s (50ms)
- 0.1s (100ms)
- 0.25s (250ms)
- 0.5s (500ms)
- 0.75s (750ms)
- 1.0s (1 second)
- 2.5s
- 5.0s
- 10.0s

## JSON Endpoint

### Get Current Metrics

```bash
curl http://localhost:8000/v1/metrics
```

**Example Response**:

```json
{
  "messages_received": 1542,
  "messages_sent": 1498,
  "reports_created": 342,
  "items_checked": 891,
  "average_response_time": 0.234,
  "active_users": 156,
  "timestamp": "2025-10-05T14:30:00.000000+00:00"
}
```

### Reset Metrics

```bash
curl -X POST http://localhost:8000/v1/metrics/reset
```

**Note**: This only resets in-memory metrics, not Prometheus counters.

## Prometheus Endpoint

### Scrape Metrics

```bash
curl http://localhost:8000/metrics
```

**Example Output**:

```prometheus
# HELP messages_received_total Total number of messages received from users
# TYPE messages_received_total counter
messages_received_total 1542.0

# HELP response_time_seconds Response time for message processing in seconds
# TYPE response_time_seconds histogram
response_time_seconds_bucket{le="0.01"} 234.0
response_time_seconds_bucket{le="0.05"} 678.0
response_time_seconds_bucket{le="0.1"} 1245.0
response_time_seconds_bucket{le="0.25"} 1456.0
...
response_time_seconds_sum 361.47
response_time_seconds_count 1542.0
```

### Prometheus Queries

Access Prometheus at `http://localhost:9090` and try these queries:

**Message Rate (per minute)**:

```promql
rate(messages_received_total[1m]) * 60
```

**Response Time p95**:

```promql
histogram_quantile(0.95, rate(response_time_seconds_bucket[5m]))
```

**Active Users Growth**:

```promql
active_users_total
```

**Reports per Hour**:

```promql
rate(reports_created_total[1h]) * 3600
```

## Grafana Dashboards

### Access Dashboard

1. Open `http://localhost:3000`
2. Login with `admin` / `admin`
3. Navigate to "Is It Stolen - Bot Metrics" dashboard

### Dashboard Panels

The pre-configured dashboard includes:

1. **Messages Received** - Total count with trend
2. **Messages Sent** - Total count with trend
3. **Message Rate** - Messages per minute (received vs sent)
4. **Response Time** - p50, p95, p99 percentiles
5. **Active Users** - Current unique users
6. **Reports Created** - Total reports with trend
7. **Items Checked** - Total checks with trend

### Custom Dashboards

You can create custom dashboards using the Prometheus datasource (automatically configured).

## Architecture

### Dual Tracking

The system tracks metrics in **two places**:

1. **In-Memory (MetricsService)**

   - Fast access for `/v1/metrics` JSON endpoint
   - Simple counters and averages
   - Lost on application restart
   - Good for quick checks during development

2. **Prometheus**
   - Time-series database
   - Persists across restarts
   - Supports percentiles, rates, and advanced queries
   - Industry-standard format
   - Production-ready

### How It Works

```text
User sends message
    ↓
MessageProcessor.process_message()
    ↓
metrics.increment_messages_received()  ← Tracks both!
    ├─ In-memory: self._messages_received += 1
    └─ Prometheus: MESSAGES_RECEIVED.inc()
```

### Integration Points

**MessageProcessor** (`src/presentation/bot/message_processor.py`):

- Tracks all messages (received/sent)
- Tracks active users
- Measures response times

**MessageRouter** (`src/presentation/bot/message_router.py`):

- Tracks reports created
- Tracks items checked

## Configuration

### Scrape Interval

Edit `prometheus.yml` to change how often Prometheus scrapes metrics:

```yaml
global:
  scrape_interval: 15s # Change to 30s for less frequent scraping
```

### Retention

Prometheus keeps data for 15 days by default. To change:

```yaml
# In docker-compose.yml
command:
  - "--storage.tsdb.retention.time=30d" # Keep 30 days
```

### Grafana Password

Change the default password in `docker-compose.yml`:

```yaml
environment:
  - GF_SECURITY_ADMIN_PASSWORD=your-secure-password
```

## Production Deployment

### Managed Prometheus

For production, consider using:

- **Grafana Cloud** (free tier: 10k metrics)
- **AWS Managed Prometheus**
- **GCP Cloud Monitoring**
- **Datadog** (with Prometheus integration)

### Self-Hosted

If self-hosting Prometheus:

1. Set up persistent storage
2. Configure alerting rules
3. Set up Grafana with authentication
4. Use reverse proxy (nginx) with HTTPS
5. Configure retention policies

### Security

In production:

1. **Don't expose** `/metrics` publicly
2. Use **authentication** for Prometheus
3. **Firewall** Grafana (port 3000)
4. Use **HTTPS** for all endpoints
5. **Rotate** Grafana admin password

## Troubleshooting

### Metrics not showing in Prometheus

1. Check Prometheus targets: `http://localhost:9090/targets`
2. Verify app is running: `http://localhost:8000/metrics`
3. Check docker network: `docker network ls`
4. Verify `host.docker.internal` works on your system

### Grafana shows "No data"

1. Check Prometheus datasource: Configuration > Data Sources
2. Test connection in datasource settings
3. Verify metrics exist in Prometheus: `http://localhost:9090/graph`

### High memory usage

Prometheus stores all metrics in memory. To reduce:

1. Decrease retention time
2. Increase scrape interval
3. Reduce histogram buckets

## Example Queries

### Business Metrics

```promql
# Conversion rate (reports / checks)
(reports_created_total / items_checked_total) * 100

# Average messages per user
messages_received_total / active_users_total

# Peak message rate (last 24h)
max_over_time(rate(messages_received_total[1m])[24h:])
```

### Performance Metrics

```promql
# Slow requests (>1s)
response_time_seconds_bucket{le="1.0"}

# Response time trend
avg_over_time(rate(response_time_seconds_sum[5m])[1h:])

# 99th percentile response time
histogram_quantile(0.99, rate(response_time_seconds_bucket[5m]))
```

## Further Reading

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Tutorials](https://grafana.com/tutorials/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Histogram vs Summary](https://prometheus.io/docs/practices/histograms/)
