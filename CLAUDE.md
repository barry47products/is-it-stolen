# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Is It Stolen** is a WhatsApp bot that enables users to check if items are reported as stolen, report stolen items, search by location, and verify reports with police reference numbers.

**Repository**: `https://github.com/barry47products/is-it-stolen`

### Technology Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL with PostGIS (geospatial support)
- **Cache**: Redis
- **Queue**: Celery with Redis
- **WhatsApp**: REST API (WhatsApp Business Cloud API)
- **Testing**: pytest with 80%+ coverage requirement
- **Dependency Management**: Poetry
- **Linting/Formatting**: Ruff
- **Type Checking**: MyPy

## Architecture

This project follows **Domain-Driven Design (DDD)** with clean architecture principles:

```bash
src/
├── domain/                    # Core business logic (NO external dependencies)
│   ├── entities/             # Business entities (e.g., StolenItem)
│   ├── value_objects/        # Immutable values (Location, PhoneNumber, ItemCategory)
│   ├── events/               # Domain events (ItemReported, ItemVerified)
│   ├── services/             # Domain services (matching algorithms)
│   └── exceptions/           # Domain-specific exceptions
├── application/              # Use cases orchestrating domain logic
│   ├── commands/             # Write operations (ReportStolenItem, VerifyItem)
│   ├── queries/              # Read operations (CheckIfStolen, SearchNearby)
│   └── dto/                  # Data Transfer Objects
├── infrastructure/           # External dependencies and implementations
│   ├── persistence/          # Database (SQLAlchemy, repositories)
│   ├── whatsapp/             # WhatsApp API client
│   └── messaging/            # Event bus, Celery tasks
└── presentation/             # API and bot interface
    ├── api/                  # FastAPI endpoints
    └── bot/                  # WhatsApp conversation state machine
```

### Dependency Rule

Dependencies flow INWARD only:

- `domain/` has NO dependencies on other layers
- `application/` depends on `domain/`
- `infrastructure/` depends on `domain/` and `application/`
- `presentation/` depends on all layers

## Development Commands

### Essential Commands

```bash
# Initial setup
make dev-setup              # Install Poetry dependencies and setup git hooks
cp .env.example .env        # Then edit .env with your credentials

# Development workflow
make docker-up              # Start PostgreSQL and Redis
make migrate-up             # Apply database migrations
make run                    # Run FastAPI with auto-reload (port 8000)
make ngrok                  # Start ngrok tunnel for WhatsApp webhooks

# Testing (following TDD approach)
make test-unit              # Unit tests only (fast, isolated)
make test-integration       # Integration tests (database, external services)
make test-e2e               # End-to-end tests (full conversation flows)
make test                   # Run all tests
make test-cov               # Generate HTML coverage report

# Code quality
make lint                   # Check code with Ruff
make lint-fix               # Auto-fix linting issues
make format                 # Format code with Ruff
make type-check             # Run MyPy type checking
make check                  # Run lint, type-check, and all tests

# Security scanning
make security-scan          # Run all security scans (Safety + Bandit)
make security-deps          # Check dependencies for vulnerabilities (Safety)
make security-code          # Run static code security analysis (Bandit)
make security-code-json     # Generate Bandit JSON report

# Database
make migrate-create message="description"  # Create new migration
make migrate-up             # Apply migrations
make migrate-down           # Rollback last migration
make db-shell               # Open PostgreSQL shell

# Docker
make docker-up              # Start services
make docker-down            # Stop services
make docker-logs            # View logs
make docker-clean           # Clean up resources

# Branch management
make issue number=X name=feature-name  # Create branch for GitHub issue
make pr-issue number=X      # Push and get PR URL for issue
```

### Observability and Tracing

The application uses OpenTelemetry for distributed tracing:

- **Auto-instrumentation**: FastAPI, SQLAlchemy, Redis, and httpx are automatically traced
- **Console output**: In development (no `OTEL_EXPORTER_ENDPOINT` set)
- **OTLP export**: Configure `OTEL_EXPORTER_ENDPOINT` for Jaeger/other backends
- **Sampling**: Configure `OTEL_TRACES_SAMPLE_RATE` (1.0 = 100%, 0.1 = 10%)

```bash
# Development: Traces output to console (stderr)
OTEL_ENABLED=true
OTEL_SERVICE_NAME=is-it-stolen
OTEL_EXPORTER_ENDPOINT=
OTEL_TRACES_SAMPLE_RATE=1.0

# Production: Export to Jaeger or other OTLP collector
OTEL_ENABLED=true
OTEL_SERVICE_NAME=is-it-stolen
OTEL_EXPORTER_ENDPOINT=http://jaeger:4317
OTEL_TRACES_SAMPLE_RATE=0.1
```

### Single Test Execution

```bash
# Run specific test file
poetry run pytest tests/unit/domain/test_location.py

# Run specific test function
poetry run pytest tests/unit/domain/test_location.py::test_creates_valid_location

# Run with verbose output
poetry run pytest -v tests/unit/domain/test_location.py

# Run tests matching pattern
poetry run pytest -k "test_location"
```

## Development Workflow

### Issue-Driven Development

Every feature starts with a GitHub issue. Follow this workflow:

```bash
# 1. Create branch for issue #X
make issue number=X name=feature-name

# 2. Write FAILING test first (TDD)
# Create test in tests/unit/domain/... or appropriate layer
make test-unit  # Verify test fails

# 3. Implement feature to make test pass
# Write minimal code in src/domain/... or appropriate layer
make test-unit  # Verify test passes

# 4. Refactor and ensure quality
make check      # Runs lint, type-check, and all tests

# 5. Commit with issue reference
git add -A
git commit -m "feat: implement feature

Detailed description of changes.

Closes #X"

# 6. Create PR
make pr-issue number=X
```

### Ngrok for WhatsApp Webhooks

WhatsApp requires HTTPS webhooks. Use ngrok in development:

```bash
# Terminal 1: Start app
make run

# Terminal 2: Start ngrok
make ngrok
# Copy the HTTPS URL (e.g., https://abc-def-ghi.ngrok-free.app)

# Configure in Meta Developer Portal:
# Webhook URL: https://your-ngrok-url.ngrok-free.app/webhook
# Verify Token: matches WHATSAPP_WEBHOOK_VERIFY_TOKEN in .env
```

Monitor webhook traffic at `http://127.0.0.1:4040`

## Code Quality Standards

### Critical Principles

Follow these **strictly** as defined in the Python Codebase Evaluation Guide:

#### Clean Code Fundamentals

- **NO magic numbers or strings**: Use named constants or enums
- **Functions ≤ 10 lines**: Keep functions small and focused
- **Max 3 function parameters**: Use DTOs or dataclasses for more
- **Single Responsibility**: Each class/function does ONE thing
- **Intention-revealing names**: Code should be self-documenting
- **DRY principle**: Don't repeat yourself

#### Type Safety

- **Full type annotations**: Every function must have type hints
- **MyPy strict mode**: `disallow_untyped_defs = true`
- **Use Pydantic**: For runtime validation and settings
- **Use dataclasses**: For domain value objects (frozen=True for immutability)

#### Testing Requirements

- **Test-Driven Development (TDD)**: Write test BEFORE implementation
- **80%+ code coverage**: Enforced in pytest config
- **AAA pattern**: Arrange, Act, Assert
- **Test behaviour, not implementation**: Focus on outcomes, not internals
- **Fast unit tests**: Mock external dependencies
- **Test Pyramid**: 70% unit, 20% integration, 10% e2e

#### Code Organization

```python
# Good: Immutable value object with validation
from dataclasses import dataclass
from typing import Optional

MIN_LATITUDE = -90.0
MAX_LATITUDE = 90.0
MIN_LONGITUDE = -180.0
MAX_LONGITUDE = 180.0

@dataclass(frozen=True)
class Location:
    """Immutable value object representing a geographical location."""

    latitude: float
    longitude: float
    address: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate coordinates on creation."""
        if not MIN_LATITUDE <= self.latitude <= MAX_LATITUDE:
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not MIN_LONGITUDE <= self.longitude <= MAX_LONGITUDE:
            raise ValueError(f"Invalid longitude: {self.longitude}")
```

### Anti-Patterns to Avoid

❌ **Never do these:**

- Functions > 10 lines
- Classes > 300 lines
- Boolean parameters in functions
- Nested conditions > 2 levels
- Comments explaining WHAT (code should be self-documenting)
- Duplicated code
- Abbreviations in names
- Global variables
- Magic values

### Git Commit Standards

```bash
# Format: <type>: <summary>
#
# <detailed description>
#
# Closes #<issue-number>

# Types: feat, fix, refactor, test, docs, chore

# Example:
git commit -m "feat: implement Location value object

Implements immutable Location value object with coordinate
validation. Includes latitude/longitude boundary checking
with clear error messages.

Closes #1"
```

## Configuration

### Environment Variables

Required in `.env`:

```bash
# WhatsApp Business Cloud API
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here
WHATSAPP_ACCESS_TOKEN=your_permanent_access_token_here
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id_here
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token_here
WHATSAPP_APP_SECRET=your_app_secret_here

# Database
MONGODB_URI=mongodb://localhost:27017/isitstolen
# or
DATABASE_URL=postgresql://user:password@localhost:5432/isitstolen

# Redis
REDIS_URL=redis://localhost:6379
```

See [.env.example](.env.example) for full configuration.

### WhatsApp Setup

1. Create app at [Meta for Developers](https://developers.facebook.com)
2. Add WhatsApp product
3. Get Phone Number ID, Access Token, Business Account ID
4. Generate Webhook Verify Token (random string)
5. Get App Secret from App Settings
6. Configure webhook in WhatsApp settings to ngrok URL

## Testing Strategy

### Test Organization

```bash
tests/
├── unit/                   # Fast, isolated, no external dependencies
│   ├── domain/            # Test domain logic (entities, value objects)
│   ├── application/       # Test use cases with mocked repositories
│   └── infrastructure/    # Test individual components with mocks
├── integration/           # Test component interactions
│   ├── persistence/       # Database tests with test DB
│   └── whatsapp/          # WhatsApp API tests with mocks/vcr
└── e2e/                   # Full conversation flows
    └── test_report_flow.py
```

### Writing Good Tests

```python
# Good: Testing behaviour with AAA pattern
def test_stolen_item_can_be_reported_with_location():
    # Arrange (Given)
    location = Location(latitude=51.5074, longitude=-0.1278, address="London")
    category = ItemCategory.BICYCLE

    # Act (When)
    item = StolenItem(
        category=category,
        description="Red mountain bike",
        location=location,
        reported_at=datetime.utcnow(),
        reporter_phone="+447700900000"
    )

    # Assert (Then)
    assert item.category == ItemCategory.BICYCLE
    assert item.location.latitude == 51.5074
    assert item.is_verified is False
```

### Test Markers

```bash
pytest -m unit              # Run only unit tests
pytest -m integration       # Run only integration tests
pytest -m e2e              # Run only e2e tests
pytest -m "not slow"       # Skip slow tests
```

## Domain Layer Guidelines

### Value Objects (Immutable)

- Always use `@dataclass(frozen=True)`
- Validate in `__post_init__`
- No setters, only getters
- Examples: Location, PhoneNumber, ItemCategory

### Entities

- Have identity (ID)
- Can change state over time
- Use value objects for attributes
- Example: StolenItem

### Domain Events

- Record significant business occurrences
- Past tense naming (ItemReported, ItemVerified)
- Immutable dataclasses
- Published by application layer after persistence

### Repository Pattern

- Defined as interfaces in domain
- Implemented in infrastructure
- Return domain entities, not database models
- Example: `StolenItemRepository`

## Common Patterns

### Command Handler Pattern

```python
@dataclass
class ReportStolenItemCommand:
    """Command to report a stolen item."""
    category: str
    description: str
    latitude: float
    longitude: float
    reporter_phone: str

class ReportStolenItemHandler:
    """Handler for report stolen item command."""

    def __init__(
        self,
        item_repository: StolenItemRepository,
        event_publisher: EventPublisher
    ) -> None:
        self.item_repository = item_repository
        self.event_publisher = event_publisher

    async def handle(self, command: ReportStolenItemCommand) -> UUID:
        """Execute the command and return item ID."""
        # Convert to domain objects
        location = Location(command.latitude, command.longitude)
        category = ItemCategory.from_user_input(command.category)

        # Create entity
        item = StolenItem(...)

        # Persist
        await self.item_repository.save(item)

        # Publish events
        for event in item.collect_events():
            await self.event_publisher.publish(event)

        return item.id
```

## Important Notes

- **Never commit `.env` files**: They contain secrets
- **Always run `make check` before committing**: Ensures quality
- **Write tests first (TDD)**: Failing test → Implementation → Refactor
- **Keep domain layer pure**: No FastAPI, SQLAlchemy, or external dependencies
- **Use async/await**: For all I/O operations (database, HTTP)
- **Document WHY, not WHAT**: Code should be self-explanatory

## Resources

- [Implementation Guide](docs/is-it-stolen-implementation-guide.md) - Complete development roadmap
- [Python Codebase Evaluation Guide](docs/python-codebase-evaluation-guide.md) - Code quality standards
- [WhatsApp Business API Docs](https://developers.facebook.com/docs/whatsapp)
- [Domain-Driven Design](https://martinfowler.com/tags/domain%20driven%20design.html)
