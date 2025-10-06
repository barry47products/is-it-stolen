# Architecture Documentation

## System Overview

Is It Stolen is a WhatsApp bot built with Domain-Driven Design (DDD) principles and Clean Architecture, enabling users to report and check stolen items through natural conversation.

## High-Level Architecture

```bash
┌─────────────────────────────────────────────────────────────────┐
│                         WhatsApp User                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS (Webhook)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Is It Stolen API                           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   FastAPI    │  │  Middleware  │  │   Metrics    │           │
│  │   Routes     │  │  Rate Limit  │  │  Prometheus  │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                  │                  │                 │
│         └──────────────────┴──────────────────┘                 │
│                            │                                    │
│  ┌─────────────────────────▼──────────────────────────┐         │
│  │         Bot Message Router & State Machine         │         │
│  └─────────────────────────┬──────────────────────────┘         │
│                            │                                    │
│  ┌─────────────────────────▼──────────────────────────┐         │
│  │          Application Layer (Use Cases)             │         │
│  │                                                    │         │
│  │  • ReportStolenItemCommand                         │         │
│  │  • CheckIfStolenQuery                              │         │
│  │  • FindNearbyItemsQuery                            │         │
│  │  • VerifyItemCommand                               │         │
│  └─────────────────────────┬──────────────────────────┘         │
│                            │                                    │
│  ┌─────────────────────────▼──────────────────────────┐         │
│  │           Domain Layer (Business Logic)            │         │
│  │                                                    │         │
│  │  Entities: StolenItem                              │         │
│  │  Value Objects: Location, PhoneNumber, Category    │         │
│  │  Services: MatchingService, VerificationService    │         │
│  │  Events: ItemReported, ItemVerified                │         │
│  └─────────────────────────┬──────────────────────────┘         │
│                            │                                    │
│  ┌─────────────────────────▼──────────────────────────┐         │
│  │        Infrastructure Layer (External Deps)        │         │
│  │                                                    │         │
│  │  • PostgreSQL (StolenItemRepository)               │         │
│  │  • Redis (Session Storage, Rate Limiter)           │         │
│  │  • WhatsApp API Client                             │         │
│  │  • Sentry (Error Tracking)                         │         │
│  │  • Geocoding Service                               │         │
│  └────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │  PostgreSQL  │    │    Redis     │    │   Sentry     │
   │   + PostGIS  │    │              │    │              │
   └──────────────┘    └──────────────┘    └──────────────┘
```

## Layer Responsibilities

### 1. Presentation Layer (`src/presentation/`)

**Purpose**: Handle HTTP requests and WhatsApp bot conversations

**Components**:

- **FastAPI Application** (`api/app.py`): HTTP server, routing, middleware
- **Bot Router** (`bot/message_router.py`): Routes messages to appropriate handlers
- **State Machine** (`bot/state_machine.py`): Manages conversation state
- **Message Parser** (`bot/message_parser.py`): Extracts intent from messages
- **Response Builder** (`bot/response_builder.py`): Formats bot responses

**Responsibilities**:

- HTTP request/response handling
- Webhook verification and signature validation
- Rate limiting per IP and per user
- Request ID tracking and correlation
- Conversation state management
- Message routing based on user intent

**Dependencies**: Application layer, Infrastructure layer

---

### 2. Application Layer (`src/application/`)

**Purpose**: Orchestrate business use cases

**Components**:

#### Commands (Write Operations)

- `ReportStolenItemCommand`: Report a new stolen item
- `VerifyItemCommand`: Verify item with police reference
- `UpdateItemCommand`: Update item details
- `DeleteItemCommand`: Remove a report

#### Queries (Read Operations)

- `CheckIfStolenQuery`: Check if description matches stolen items
- `FindNearbyItemsQuery`: Search for items near a location
- `ListUserItemsQuery`: Get user's reported items

**Responsibilities**:

- Coordinate domain logic
- Transaction management
- Publish domain events
- Input validation via DTOs
- Output formatting via DTOs

**Dependencies**: Domain layer only

---

### 3. Domain Layer (`src/domain/`)

**Purpose**: Core business logic (framework-independent)

**Components**:

#### Entities

- `StolenItem`: Reported stolen item with identity

#### Value Objects (Immutable)

- `Location`: GPS coordinates (lat/lng)
- `PhoneNumber`: Validated phone number
- `ItemCategory`: Type of item (BICYCLE, LAPTOP, etc.)
- `PoliceReference`: Police report number
- `ItemAttributes`: Color, brand, serial number

#### Domain Services

- `MatchingService`: Match item descriptions
- `VerificationService`: Validate police references

#### Domain Events

- `ItemReportedEvent`: Item was reported
- `ItemVerifiedEvent`: Item was verified
- `ItemMatchedEvent`: Description matched existing item

**Responsibilities**:

- Business rules enforcement
- Data validation
- Invariant protection
- Domain event emission

**Dependencies**: **NONE** (pure business logic)

---

### 4. Infrastructure Layer (`src/infrastructure/`)

**Purpose**: External system integrations

**Components**:

#### Persistence

- `PostgresStolenItemRepository`: Database implementation
- `Database`: SQLAlchemy connection management
- `Models`: SQLAlchemy ORM models

#### Cache

- `RedisClient`: Redis connection wrapper
- `RateLimiter`: IP/user rate limiting
- `SessionStorage`: Conversation state storage

#### External APIs

- `WhatsAppClient`: WhatsApp Business Cloud API
- `WebhookHandler`: Webhook validation and processing
- `GeocodingService`: Convert addresses to coordinates

#### Monitoring

- `SentryClient`: Error tracking and reporting
- `MetricsService`: Prometheus metrics collection

#### Configuration

- `Settings`: Pydantic settings with validation
- `CategoryKeywords`: ML-based category mapping

#### Logging

- `StructuredLogging`: Privacy-compliant logging
- `SensitiveDataFilter`: Redact secrets from logs
- `PhoneHasher`: Hash phone numbers for correlation

**Responsibilities**:

- Database queries and persistence
- Caching and session management
- External API communication
- Error tracking and metrics
- Configuration management

**Dependencies**: Domain layer, Application layer

---

## Data Flow

### Example: Reporting a Stolen Item

```bash
1. User sends WhatsApp message: "I want to report a stolen bicycle"
                    │
                    ▼
2. WhatsApp → POST /v1/webhook with message payload
                    │
                    ▼
3. WebhookHandler validates signature
                    │
                    ▼
4. MessageRouter extracts intent: REPORT_ITEM
                    │
                    ▼
5. StateMachine transitions: IDLE → WAITING_FOR_CATEGORY
                    │
                    ▼
6. User provides: "Red mountain bike, serial ABC123"
                    │
                    ▼
7. MessageParser extracts category: BICYCLE
                    │
                    ▼
8. StateMachine transitions: WAITING_FOR_CATEGORY → WAITING_FOR_LOCATION
                    │
                    ▼
9. User shares location (GPS coordinates)
                    │
                    ▼
10. ReportStolenItemCommand handler:
     ├─ Create Location value object (validate coordinates)
     ├─ Create PhoneNumber value object (validate format)
     ├─ Create StolenItem entity
     ├─ Repository saves to PostgreSQL
     ├─ Publish ItemReportedEvent
     └─ MetricsService increments counter
                    │
                    ▼
11. ResponseBuilder formats success message
                    │
                    ▼
12. WhatsAppClient sends confirmation message
                    │
                    ▼
13. StateMachine transitions: WAITING_FOR_LOCATION → IDLE
```

---

## Database Schema

### Tables

#### `stolen_items`

```sql
CREATE TABLE stolen_items (
    id UUID PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    address TEXT,
    reporter_phone VARCHAR(20) NOT NULL,
    reported_at TIMESTAMP NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    police_reference VARCHAR(50),
    verified_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_stolen_items_category ON stolen_items(category);
CREATE INDEX idx_stolen_items_reporter ON stolen_items(reporter_phone);
CREATE INDEX idx_stolen_items_location ON stolen_items USING GIST (
    ll_to_earth(latitude, longitude)
);
CREATE INDEX idx_stolen_items_reported_at ON stolen_items(reported_at DESC);
```

#### `conversations` (Redis)

```json
{
  "session_id": "447700900000",
  "state": "WAITING_FOR_LOCATION",
  "data": {
    "category": "BICYCLE",
    "description": "Red mountain bike",
    "intent": "REPORT_ITEM"
  },
  "ttl": 1800
}
```

See [DATABASE.md](DATABASE.md) for complete schema documentation.

---

## Deployment Architecture

### Development

```bash
┌─────────────┐
│  Developer  │
│  Localhost  │
│             │
│  FastAPI    │◄───┐
│  :8000      │    │
└──────┬──────┘    │
       │           │
       │        ┌──┴────┐
       ├────────► Redis │
       │        └───────┘
       │
       │        ┌───────────┐
       └────────► Postgres  │
                │  +PostGIS │
                └───────────┘
```

### Production

```bash
                 ┌──────────────┐
                 │  CloudFlare  │
                 │  (CDN + WAF) │
                 └──────┬───────┘
                        │
                 ┌──────▼───────┐
                 │  Load        │
                 │  Balancer    │
                 └──────┬───────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
   ┌────▼────┐                    ┌────▼────┐
   │ FastAPI │                    │ FastAPI │
   │ Node 1  │                    │ Node 2  │
   └────┬────┘                    └────┬────┘
        │                               │
        └───────────────┬───────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
   ┌────▼─────┐                   ┌────▼──────┐
   │ Postgres │                   │  Redis    │
   │ Primary  │◄──────────────────┤  Cluster  │
   └────┬─────┘                   └───────────┘
        │
   ┌────▼─────┐
   │ Postgres │
   │ Replica  │
   └──────────┘
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment instructions.

---

## Technology Decisions

### Why PostgreSQL with PostGIS?

- **Geospatial queries**: PostGIS enables efficient radius searches
- **ACID compliance**: Critical for financial/legal data
- **Strong typing**: Ensures data integrity
- **Full-text search**: Efficient item description matching

### Why Redis?

- **Fast session storage**: Sub-millisecond latency
- **Rate limiting**: Atomic increment operations
- **TTL support**: Auto-expire old sessions
- **Pub/Sub**: Future real-time notifications

### Why FastAPI?

- **Async support**: Handle high concurrent loads
- **Auto-generated docs**: OpenAPI/Swagger out of the box
- **Type safety**: Pydantic validation
- **Performance**: Comparable to Node.js/Go

### Why Domain-Driven Design?

- **Business focus**: Code reflects domain language
- **Testability**: Pure domain logic, no framework coupling
- **Maintainability**: Clear separation of concerns
- **Scalability**: Easy to extract microservices later

---

## Security Architecture

### Defence in Depth

```bash
1. CloudFlare WAF
   ├─ DDoS protection
   ├─ Bot detection
   └─ Rate limiting

2. Load Balancer
   ├─ SSL termination
   ├─ Health checks
   └─ Connection limits

3. Application Layer
   ├─ Webhook signature verification (HMAC SHA256)
   ├─ Rate limiting per IP + per user
   ├─ Input validation (Pydantic)
   ├─ SQL injection prevention (ORM)
   └─ Request ID tracking

4. Infrastructure Layer
   ├─ Database encryption at rest
   ├─ Redis password authentication
   ├─ Secrets management (env vars)
   └─ Audit logging

5. Monitoring
   ├─ Sentry error tracking
   ├─ Prometheus metrics
   ├─ Structured logging (privacy-compliant)
   └─ Anomaly detection
```

See [SECURITY.md](../SECURITY.md) for security policies.

---

## Performance Characteristics

### Latency Targets

- **Health check**: < 10ms
- **Webhook verification**: < 50ms
- **Message processing**: < 200ms
- **Database queries**: < 100ms
- **Location search (10km radius)**: < 150ms

### Scalability

- **Concurrent users**: 10,000+
- **Messages per second**: 500+
- **Database records**: 10M+ items
- **Session storage**: 100K+ active sessions

### Optimization Strategies

1. **Database indexes**: Geospatial, category, timestamp
2. **Redis caching**: Session data, rate limit counters
3. **Connection pooling**: Reuse database connections
4. **Async I/O**: Non-blocking webhook processing
5. **Batch operations**: Bulk geocoding, metrics collection

---

## Monitoring & Observability

### Metrics (Prometheus)

- `http_requests_total` - Request counter
- `http_request_duration_seconds` - Latency histogram
- `active_sessions_total` - Concurrent sessions gauge
- `stolen_items_total` - Total items reported
- `reports_verified_total` - Verified reports counter

### Logging (Structlog)

- **Request tracing**: request_id correlation
- **Privacy-compliant**: Phone number hashing, PII redaction
- **Structured**: JSON format for log aggregation
- **Contextual**: User, report, session binding

### Error Tracking (Sentry)

- **Auto-capture**: Unhandled exceptions
- **Breadcrumbs**: Request/response history
- **User context**: Hashed phone number
- **Environment tags**: development/staging/production

---

## Future Enhancements

### Planned Architecture Changes

1. **Microservices**: Extract geolocation service
2. **Event sourcing**: Full audit trail of item history
3. **CQRS**: Separate read/write databases
4. **GraphQL**: Alternative API interface
5. **WebSocket**: Real-time notifications
6. **ML service**: Improve item matching accuracy

---

## Additional Resources

- [Implementation Guide](is-it-stolen-implementation-guide.md)
- [Development Guide](../CLAUDE.md)
- [API Documentation](API.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Database Schema](DATABASE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
