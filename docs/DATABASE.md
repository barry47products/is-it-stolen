# Database Schema Documentation

## Overview

Is It Stolen uses PostgreSQL 15+ with PostGIS extension for geospatial queries and Redis for caching and session storage.

---

## PostgreSQL Schema

### Extensions Required

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS cube;
CREATE EXTENSION IF NOT EXISTS earthdistance;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

---

### Tables

#### `stolen_items`

Stores reported stolen items with geospatial data.

```sql
CREATE TABLE stolen_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    address TEXT,
    reporter_phone VARCHAR(20) NOT NULL,
    reported_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_verified BOOLEAN DEFAULT FALSE,
    police_reference VARCHAR(50),
    verified_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_latitude CHECK (latitude >= -90 AND latitude <= 90),
    CONSTRAINT valid_longitude CHECK (longitude >= -180 AND longitude <= 180),
    CONSTRAINT valid_status CHECK (status IN ('ACTIVE', 'RECOVERED', 'DELETED')),
    CONSTRAINT valid_category CHECK (category IN (
        'BICYCLE', 'MOTORCYCLE', 'CAR', 'LAPTOP', 'PHONE',
        'TABLET', 'CAMERA', 'JEWELRY', 'WATCH', 'OTHER'
    ))
);
```

**Columns**:

| Column           | Type        | Nullable | Default   | Description                            |
| ---------------- | ----------- | -------- | --------- | -------------------------------------- |
| id               | UUID        | NO       | uuid_v4() | Unique identifier                      |
| category         | VARCHAR(50) | NO       | -         | Item category (enum)                   |
| description      | TEXT        | NO       | -         | User-provided description              |
| latitude         | FLOAT       | NO       | -         | GPS latitude (-90 to 90)               |
| longitude        | FLOAT       | NO       | -         | GPS longitude (-180 to 180)            |
| address          | TEXT        | YES      | NULL      | Human-readable address                 |
| reporter_phone   | VARCHAR(20) | NO       | -         | Reporter's phone (E.164 format)        |
| reported_at      | TIMESTAMP   | NO       | NOW()     | When item was reported                 |
| is_verified      | BOOLEAN     | NO       | FALSE     | Verified with police reference         |
| police_reference | VARCHAR(50) | YES      | NULL      | Police report number                   |
| verified_at      | TIMESTAMP   | YES      | NULL      | When verification occurred             |
| status           | VARCHAR(20) | NO       | 'ACTIVE'  | Item status (ACTIVE/RECOVERED/DELETED) |
| created_at       | TIMESTAMP   | NO       | NOW()     | Record creation timestamp              |
| updated_at       | TIMESTAMP   | NO       | NOW()     | Last update timestamp                  |

**Indexes**:

```sql
-- Primary key index (automatic)
CREATE UNIQUE INDEX pk_stolen_items ON stolen_items(id);

-- Category search
CREATE INDEX idx_stolen_items_category ON stolen_items(category);

-- User's reports
CREATE INDEX idx_stolen_items_reporter ON stolen_items(reporter_phone);

-- Geospatial search (PostGIS)
CREATE INDEX idx_stolen_items_location ON stolen_items
USING GIST (ll_to_earth(latitude, longitude));

-- Recent reports (for pagination)
CREATE INDEX idx_stolen_items_reported_at ON stolen_items(reported_at DESC);

-- Active items only
CREATE INDEX idx_stolen_items_status ON stolen_items(status)
WHERE status = 'ACTIVE';

-- Verified items
CREATE INDEX idx_stolen_items_verified ON stolen_items(is_verified)
WHERE is_verified = TRUE;
```

**Triggers**:

```sql
-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_stolen_items_updated_at
BEFORE UPDATE ON stolen_items
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

---

### Example Queries

#### Insert New Item

```sql
INSERT INTO stolen_items (
    category, description, latitude, longitude,
    address, reporter_phone
) VALUES (
    'BICYCLE',
    'Red mountain bike, brand: Trek, serial: ABC123',
    51.5074,
    -0.1278,
    'London, UK',
    '+447700900000'
) RETURNING id;
```

#### Find Items Within Radius

```sql
-- Find items within 10km of location
SELECT
    id,
    category,
    description,
    earth_distance(
        ll_to_earth(51.5074, -0.1278),
        ll_to_earth(latitude, longitude)
    ) / 1000 AS distance_km
FROM stolen_items
WHERE
    status = 'ACTIVE'
    AND earth_box(ll_to_earth(51.5074, -0.1278), 10000) @> ll_to_earth(latitude, longitude)
ORDER BY distance_km
LIMIT 20;
```

#### Search by Description

```sql
-- Full-text search for "red bicycle"
SELECT
    id,
    category,
    description,
    ts_rank(
        to_tsvector('english', description),
        to_tsquery('english', 'red & bicycle')
    ) AS rank
FROM stolen_items
WHERE
    status = 'ACTIVE'
    AND to_tsvector('english', description) @@ to_tsquery('english', 'red & bicycle')
ORDER BY rank DESC
LIMIT 10;
```

#### Get User's Reports

```sql
SELECT *
FROM stolen_items
WHERE reporter_phone = '+447700900000'
ORDER BY reported_at DESC;
```

#### Verify Item

```sql
UPDATE stolen_items
SET
    is_verified = TRUE,
    police_reference = 'REF12345',
    verified_at = NOW()
WHERE id = 'uuid-here';
```

#### Mark as Recovered

```sql
UPDATE stolen_items
SET status = 'RECOVERED'
WHERE id = 'uuid-here';
```

---

## Redis Schema

### Key Naming Convention

```bash
{namespace}:{identifier}:{field}
```

---

### Conversation Sessions

**Key Pattern**: `conversation:{phone_number}`

**Data Type**: String (JSON)

**TTL**: 1800 seconds (30 minutes)

**Structure**:

```json
{
  "session_id": "+447700900000",
  "state": "WAITING_FOR_LOCATION",
  "intent": "REPORT_ITEM",
  "data": {
    "category": "BICYCLE",
    "description": "Red mountain bike, serial ABC123",
    "color": "red",
    "brand": "Trek"
  },
  "created_at": "2025-10-06T09:00:00Z",
  "updated_at": "2025-10-06T09:05:00Z"
}
```

**Operations**:

```bash
# Get session
GET conversation:+447700900000

# Set session
SETEX conversation:+447700900000 1800 '{"session_id":...}'

# Delete session (user cancels)
DEL conversation:+447700900000

# Check if session exists
EXISTS conversation:+447700900000
```

---

### Rate Limiting

**Key Pattern**: `ratelimit:{type}:{identifier}`

**Data Type**: String (integer counter)

**TTL**: 60 seconds

**Types**:

- `ratelimit:ip:{ip_address}` - Per-IP rate limit
- `ratelimit:user:{phone_number}` - Per-user rate limit

**Example**:

```bash
# Increment IP counter
INCR ratelimit:ip:192.168.1.1

# Set TTL if new key
EXPIRE ratelimit:ip:192.168.1.1 60

# Get current count
GET ratelimit:ip:192.168.1.1

# Check if limit exceeded (e.g., max 60)
GET ratelimit:ip:192.168.1.1  # Returns "61" = exceeded
```

**Implementation**:

```python
def check_rate_limit(identifier: str, limit: int = 60) -> bool:
    """Check if rate limit exceeded."""
    key = f"ratelimit:ip:{identifier}"
    count = redis.incr(key)

    if count == 1:
        redis.expire(key, 60)  # Set TTL on first request

    return count <= limit
```

---

### Cache (Future)

**Key Pattern**: `cache:{entity}:{id}`

**Data Type**: String (JSON)

**TTL**: Variable (300-3600 seconds)

**Examples**:

```bash
# Cache stolen item
cache:item:uuid-here

# Cache geocoding result
cache:geocode:51.5074,-0.1278

# Cache search results
cache:search:bicycle:10km:london
```

---

## Migrations

### Migration Tool

We use Alembic for database migrations.

### Directory Structure

```bash
alembic/
├── versions/
│   ├── 001_initial_schema.py
│   ├── 002_add_indexes.py
│   └── 003_add_triggers.py
├── env.py
└── script.py.mako
```

### Creating Migrations

```bash
# Create new migration
make migrate-create message="add column foo to stolen_items"

# This generates:
# alembic/versions/004_add_column_foo_to_stolen_items.py
```

### Running Migrations

```bash
# Upgrade to latest
make migrate-up
# or
poetry run alembic upgrade head

# Upgrade one version
poetry run alembic upgrade +1

# Downgrade one version
poetry run alembic downgrade -1

# Show current version
poetry run alembic current

# Show migration history
poetry run alembic history
```

### Example Migration

```python
"""add verified items index

Revision ID: 004
Revises: 003
Create Date: 2025-10-06 09:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add index for verified items."""
    op.create_index(
        'idx_stolen_items_verified',
        'stolen_items',
        ['is_verified'],
        unique=False,
        postgresql_where=sa.text('is_verified = TRUE')
    )

def downgrade() -> None:
    """Remove index for verified items."""
    op.drop_index('idx_stolen_items_verified', table_name='stolen_items')
```

---

## Performance Optimization

### Query Performance

#### 1. Use Appropriate Indexes

```sql
-- Bad: Full table scan
SELECT * FROM stolen_items WHERE description LIKE '%bicycle%';

-- Good: Use GIN index for full-text search
SELECT * FROM stolen_items
WHERE to_tsvector('english', description) @@ to_tsquery('english', 'bicycle');
```

#### 2. Limit Result Sets

```sql
-- Bad: Returns all results
SELECT * FROM stolen_items WHERE status = 'ACTIVE';

-- Good: Paginate results
SELECT * FROM stolen_items
WHERE status = 'ACTIVE'
ORDER BY reported_at DESC
LIMIT 20 OFFSET 0;
```

#### 3. Use Partial Indexes

```sql
-- Index only active items (most common query)
CREATE INDEX idx_stolen_items_active
ON stolen_items(reported_at DESC)
WHERE status = 'ACTIVE';
```

### Connection Pooling

Configure in `settings.py`:

```python
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 40
DATABASE_POOL_TIMEOUT = 30
DATABASE_POOL_RECYCLE = 3600
```

### Vacuum and Analyze

```sql
-- Manual vacuum
VACUUM ANALYZE stolen_items;

-- Enable autovacuum (recommended)
ALTER TABLE stolen_items SET (autovacuum_enabled = true);
```

---

## Backup and Recovery

### Automated Backups

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Full database backup
pg_dump $DATABASE_URL | gzip > $BACKUP_DIR/full_$DATE.sql.gz

# Schema only
pg_dump --schema-only $DATABASE_URL > $BACKUP_DIR/schema_$DATE.sql

# Data only
pg_dump --data-only $DATABASE_URL > $BACKUP_DIR/data_$DATE.sql
```

### Restore from Backup

```bash
# Restore full backup
gunzip full_20251006_020000.sql.gz
psql $DATABASE_URL < full_20251006_020000.sql

# Restore specific table
pg_restore --table=stolen_items full_20251006_020000.sql.gz
```

### Point-in-Time Recovery

Enable WAL archiving in `postgresql.conf`:

```ini
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backups/wal/%f'
```

---

## Security

### Role-Based Access Control

```sql
-- Create read-only role
CREATE ROLE readonly;
GRANT CONNECT ON DATABASE isitstolen TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;

-- Create application role
CREATE ROLE app_user WITH LOGIN PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON stolen_items TO app_user;
```

### Encryption

- **At Rest**: Enable PostgreSQL encryption (pgcrypto)
- **In Transit**: Use SSL/TLS for connections

```bash
# Connect with SSL
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### Sensitive Data

```sql
-- Hash phone numbers for privacy
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Store hashed phone
UPDATE stolen_items
SET reporter_phone_hash = encode(digest(reporter_phone, 'sha256'), 'hex');
```

---

## Monitoring

### Query Performance Monitoring

```sql
-- Enable pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Table Statistics

```sql
-- View table sizes
SELECT
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    pg_size_pretty(pg_relation_size(relid)) AS table_size,
    pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) AS index_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

### Index Usage

```sql
-- View index usage statistics
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

---

## Data Retention

### Archive Old Data

```sql
-- Create archive table
CREATE TABLE stolen_items_archive (LIKE stolen_items INCLUDING ALL);

-- Move old recovered items to archive
WITH moved AS (
    DELETE FROM stolen_items
    WHERE status = 'RECOVERED'
    AND updated_at < NOW() - INTERVAL '1 year'
    RETURNING *
)
INSERT INTO stolen_items_archive SELECT * FROM moved;
```

### Purge Deleted Items

```sql
-- Permanently delete items marked as deleted > 30 days ago
DELETE FROM stolen_items
WHERE status = 'DELETED'
AND updated_at < NOW() - INTERVAL '30 days';
```

---

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [Redis Documentation](https://redis.io/documentation)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Architecture Documentation](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
