# Is It Stolen - Complete Implementation Guide

**Repository**: `https://github.com/barry47products/is-it-stolen`

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technical Architecture](#technical-architecture)
3. [Issue-Driven Development](#issue-driven-development)
4. [Development Setup](#development-setup)
5. [Domain Layer Implementation](#domain-layer-implementation)
6. [Application Layer Implementation](#application-layer-implementation)
7. [Infrastructure Layer Implementation](#infrastructure-layer-implementation)
8. [Presentation Layer Implementation](#presentation-layer-implementation)
9. [Testing Strategy](#testing-strategy)
10. [Deployment Guide](#deployment-guide)
11. [Summary](#summary)

## Project Overview

**Is It Stolen** is a WhatsApp bot that allows users to:

- Check if an item is reported as stolen
- Report stolen items
- Search for stolen items by location
- Verify reports with police reference numbers

**Repository**: `https://github.com/barry47products/is-it-stolen`

### Core Principles

- **Issue-Driven Development**: Every feature starts with a GitHub issue
- **Domain-Driven Design**: Business logic isolated from infrastructure
- **Test-Driven Development**: Tests written before implementation
- **Clean Code**: Small functions, clear naming, no magic values
- **Type Safety**: Full type annotations with mypy
- **Small Commits**: One logical change per commit linked to an issue

## Technical Architecture

### Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL with PostGIS
- **Cache**: Redis
- **Queue**: Celery with Redis
- **WhatsApp**: REST API (direct implementation)
- **Testing**: pytest with 80%+ coverage

### Project Structure

```bash
is_it_stolen/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── feature.md
│   │   ├── bug.md
│   │   └── task.md
│   └── workflows/
│       └── ci.yml
├── src/
│   ├── domain/                    # Core business logic (no dependencies)
│   │   ├── entities/
│   │   ├── value_objects/
│   │   ├── events/
│   │   ├── services/
│   │   └── exceptions/
│   ├── application/               # Use cases
│   │   ├── commands/
│   │   ├── queries/
│   │   └── dto/
│   ├── infrastructure/            # External dependencies
│   │   ├── persistence/
│   │   ├── whatsapp/
│   │   └── messaging/
│   └── presentation/              # API layer
│       ├── api/
│       └── bot/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── alembic/                       # Database migrations
├── docker/
├── scripts/
├── Makefile
├── pyproject.toml
├── README.md
└── .env.example
```

## Issue-Driven Development

Every piece of work starts with a GitHub issue. Issues represent complete, testable features that can be independently developed and verified.

### Issue Templates

Create `.github/ISSUE_TEMPLATE/feature.md`:

````markdown
## Implementation Roadmap

### Progress Summary

**Last Updated**: October 5, 2025

**Completed**:

- ✅ Development environment setup (Poetry, Docker, Alembic, pre-commit hooks)
- ✅ CI/CD pipeline (GitHub Actions with SonarCloud, Codecov)
- ✅ Milestone 1: Core Domain (Issues #1-10) - 10/10 complete
- ✅ Milestone 2: Infrastructure (Issues #11-20) - 10/10 complete
- ✅ Milestone 3: Application Layer (Issues #21-30) - 10/10 complete
- ✅ Issue #31: FastAPI setup (application factory pattern, lifespan, middleware)
- ✅ Issue #32: Webhook endpoint (GET/POST with signature verification)
- ✅ Issue #33: State machine (conversation flow with Redis storage, 100% coverage)
- ✅ Issue #34: Message parser and router (parsing + routing + WhatsApp integration, 100% coverage)
- ✅ Issue #35: Response builder (formatted bot messages with templates, 100% coverage)
- ✅ Issue #36: Error handling (ErrorHandler + MessageRouter integration, 100% coverage on both)
- 🚧 Issue #37: Rate limiting (RateLimiter + ErrorHandler complete, 100% coverage, MessageProcessor integration pending)

**Current Status**: Milestone 4 Bot Presentation - 6/12 complete (Issue #36 merged, Issue #37 75% done). RateLimiter and ErrorHandler integration complete with 100% coverage (608 tests passing total).

---

### Milestone 1: Core Domain (Issues #1-10) - Week 1

Start with the pure domain layer - no external dependencies.

| Issue | Title | Description | Estimate | Status |
|## Your First Issue: Getting Started

### Recommended First Issue: #1 - Location Value Object

This is a perfect starting point because:

- Pure domain logic (no external dependencies)
- Clear requirements and validation rules
- Teaches the TDD workflow
- Sets the pattern for other value objects

**Create the issue on GitHub**:

```markdown
Title: [FEATURE] Implement Location value object with validation

## User Story

As a developer, I want a Location value object that validates coordinates
so that we ensure data integrity throughout the system.

## Acceptance Criteria

- [ ] Given valid coordinates, when creating Location, then object is created
- [ ] Given invalid latitude (<-90 or >90), when creating Location, then ValueError raised
- [ ] Given invalid longitude (<-180 or >180), when creating Location, then ValueError raised
- [ ] Given two locations, when calculating distance, then returns kilometres using Haversine formula
- [ ] Object is immutable (frozen dataclass)

## Technical Requirements

- [ ] 100% test coverage
- [ ] Full type hints
- [ ] No magic values (use constants)
- [ ] Haversine distance calculation accurate to 1km

## Definition of Done

- [ ] Unit tests pass
- [ ] Type checking passes (mypy)
- [ ] Linting passes (ruff)
- [ ] Code reviewed and approved
- [ ] PR merged to main
```
````

**Complete the issue**:

```bash
# 1. Assign yourself on GitHub

# 2. Create branch
make issue number=1 name=location-value-object

# 3. Write failing test
cat > tests/unit/domain/value_objects/test_location.py << 'EOF'
"""Tests for Location value object."""
import pytest
from src.domain.value_objects.location import Location

class TestLocation:
    def test_creates_valid_location(self):
        """Should create location with valid coordinates."""
        location = Location(51.5074, -0.1278, "London")
        assert location.latitude == 51.5074
        assert location.longitude == -0.1278
        assert location.address == "London"

    def test_rejects_invalid_latitude(self):
        """Should reject latitude outside valid range."""
        with pytest.raises(ValueError, match="Invalid latitude"):
            Location(91, 0)
EOF

# 4. Run test (should fail)
make test-unit

# 5. Implement feature
mkdir -p src/domain/value_objects
touch src/domain/value_objects/__init__.py

cat > src/domain/value_objects/location.py << 'EOF'
"""Location value object for geographical coordinates."""
from dataclasses import dataclass
from typing import Optional

# Constants
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
EOF

# 6. Run test (should pass)
make test-unit

# 7. Check code quality
make check

# 8. Commit with issue reference
git add -A
git commit -m "feat: implement Location value object

Implements immutable Location value object with coordinate
validation. Includes latitude/longitude boundary checking
with clear error messages.

Closes #1"

# 9. Push and create PR
make pr-issue number=1

# 10. After merge, clean up
git checkout main
git pull origin main
git branch -d feat/1-location-value-object
```

### Next Issues to Tackle

After completing the Location value object:

1. **Issue #2: ItemCategory enum** - Another simple domain object
2. **Issue #3: PhoneNumber value object** - Add E.164 validation
3. **Issue #4: StolenItem entity** - The core domain entity

Each issue builds on the previous ones, gradually increasing in complexity while maintaining the same TDD workflow.

| Issue | Title                    | Description                                 | Estimate | Status      |
| ----- | ------------------------ | ------------------------------------------- | -------- | ----------- |
| #1    | Location value object    | Coordinate validation, distance calculation | 2h       | ✅ COMPLETE |
| #2    | ItemCategory enum        | Categories with keyword parsing             | 1h       | ✅ COMPLETE |
| #3    | PhoneNumber value object | E.164 validation                            | 1h       | ✅ COMPLETE |
| #4    | StolenItem entity        | Aggregate root with validation              | 4h       | ✅ COMPLETE |
| #5    | Domain events            | ItemReported, ItemVerified events           | 2h       | ✅ COMPLETE |
| #6    | Matching service         | Text similarity algorithm                   | 3h       | ✅ COMPLETE |
| #7    | Domain exceptions        | Custom domain-specific exceptions           | 1h       | ✅ COMPLETE |
| #8    | Item attributes          | Flexible attributes per category            | 2h       | ✅ COMPLETE |
| #9    | Verification rules       | Business rules for verification             | 2h       | ✅ COMPLETE |
| #10   | Domain integration tests | Test domain layer together                  | 2h       | ✅ COMPLETE |

### Milestone 2: Infrastructure (Issues #11-20) - Week 2 - 10/10 Complete ✅

Build the infrastructure to support the domain.

| Issue | Title                | Description                         | Estimate | Status      |
| ----- | -------------------- | ----------------------------------- | -------- | ----------- |
| #11   | Database setup       | PostgreSQL with PostGIS             | 2h       | ✅ COMPLETE |
| #12   | SQLAlchemy models    | Database models with GeoAlchemy2    | 3h       | ✅ COMPLETE |
| #13   | Repository pattern   | StolenItemRepository implementation | 3h       | ✅ COMPLETE |
| #14   | WhatsApp client      | REST API client with retry logic    | 4h       | ✅ COMPLETE |
| #15   | Webhook handler      | Parse and validate webhooks         | 3h       | ✅ COMPLETE |
| #16   | Redis setup          | Cache and session management        | 2h       | ✅ COMPLETE |
| #17   | Event bus            | Publish domain events               | 2h       | ✅ COMPLETE |
| #18   | Media storage        | Handle images from WhatsApp         | 3h       | ✅ COMPLETE |
| #19   | Configuration        | Settings with Pydantic validation   | 1h       | ✅ COMPLETE |
| #20   | Infrastructure tests | Redis integration tests             | 3h       | ✅ COMPLETE |

### Milestone 3: Application Layer (Issues #21-30) - Week 3 - ✅ 10/10 COMPLETE

Implement use cases that orchestrate the domain.

| Issue | Title                 | Description                | Status      | Estimate |
| ----- | --------------------- | -------------------------- | ----------- | -------- |
| #21   | Report item command   | Handle item reporting      | ✅ COMPLETE | 3h       |
| #22   | Check item query      | Search for stolen items    | ✅ COMPLETE | 3h       |
| #23   | Nearby items query    | Location-based search      | ✅ COMPLETE | 2h       |
| #24   | Verify item command   | Police report verification | ✅ COMPLETE | 2h       |
| #25   | List user items query | Get user's reports         | ✅ COMPLETE | 2h       |
| #26   | Delete item command   | Remove reports             | ✅ COMPLETE | 1h       |
| #27   | Update item command   | Edit reports               | ✅ COMPLETE | 2h       |
| #28   | Notification service  | Send confirmations         | ✅ COMPLETE | 2h       |
| #29   | Export service        | Generate reports           | ✅ COMPLETE | 2h       |
| #30   | Application tests     | Use case tests             | ✅ COMPLETE | 3h       |

### Milestone 4: Bot Presentation (Issues #31-40, #91-92) - Week 4 - 6/12 Complete

Build the WhatsApp bot interface.

| Issue | Title            | Description                          | Status      | Estimate |
| ----- | ---------------- | ------------------------------------ | ----------- | -------- |
| #31   | FastAPI setup    | Basic application structure          | ✅ COMPLETE | 2h       |
| #32   | Webhook endpoint | Receive WhatsApp messages            | ✅ COMPLETE | 2h       |
| #33   | State machine    | Conversation flow management         | ✅ COMPLETE | 4h       |
| #34   | Message parser   | Parse + route messages with WhatsApp | ✅ COMPLETE | 3h       |
| #35   | Response builder | Template-based message formatting    | ✅ COMPLETE | 3h       |
| #36   | Error handling   | User-friendly errors                 | ✅ COMPLETE | 3h       |
| #37   | Rate limiting    | Prevent abuse                        | 🚧 IN PROGRESS | 2h    |
| #38   | Health checks    | Monitoring endpoints                 | 📋 TODO     | 1h       |
| #39   | Metrics          | Track usage statistics               | 📋 TODO     | 2h       |
| #40   | E2E tests        | Full conversation tests              | 📋 TODO     | 4h       |
| #91   | Geocoding        | Location text to coordinates         | 📋 TODO     | 3h       |
| #92   | Stolen date      | Collect actual stolen date from user | 📋 TODO     | 2h       |

### Milestone 5: Production Ready (Issues #41-50) - Week 5

Polish for production deployment.

| Issue | Title               | Description           | Estimate |
| ----- | ------------------- | --------------------- | -------- |
| #41   | Docker optimisation | Multi-stage builds    | 2h       |
| #42   | CI/CD pipeline      | GitHub Actions setup  | 3h       |
| #43   | Monitoring          | Sentry integration    | 2h       |
| #44   | Logging             | Structured logging    | 2h       |
| #45   | Documentation       | API docs, README      | 3h       |
| #46   | Performance testing | Load testing          | 3h       |
| #47   | Security audit      | Dependency scanning   | 2h       |
| #48   | Backup strategy     | Database backups      | 2h       |
| #49   | Deployment          | Production deployment | 3h       |
| #50   | Launch preparation  | Final testing         | 2h       |

## Quick Start Guide

### Clone and Setup

```bash
# 1. Clone repository
git clone https://github.com/barry47products/is-it-stolen.git
cd is-it-stolen

# 2. Setup development environment
make dev-setup  # Install Poetry dependencies and git hooks

# 3. Configure environment
cp .env.example .env
# Edit .env with your WhatsApp credentials from Meta Developer Portal

# 4. Setup ngrok for webhooks
make ngrok-setup  # Enter your authtoken when prompted
# Get authtoken from https://dashboard.ngrok.com/get-started/your-authtoken

# 5. Start services
make docker-up    # PostgreSQL and Redis
make migrate-up   # Database migrations
```

### Start Development

**Check the project board for available issues**:
`https://github.com/barry47products/is-it-stolen/projects`

```bash
# Pick an issue (e.g., Issue #1: Location value object)
make issue number=1 name=location-value-object

# Write failing test first (TDD)
touch tests/unit/domain/value_objects/test_location.py
# Write test...
make test-unit  # Verify it fails

# Implement feature
touch src/domain/value_objects/location.py
# Write implementation...
make test-unit  # Make test pass

# Check code quality
make check  # Runs lint, type-check, and all tests

# Commit with issue reference
git add -A
git commit -m "feat: implement Location value object

Adds immutable Location value object with coordinate
validation and distance calculation.

Closes #1"

# Create PR
make pr-issue number=1
```

### Running the WhatsApp Bot

**Terminal 1 - Application**:

```bash
make run
# FastAPI running at http://localhost:8000
```

**Terminal 2 - Ngrok Tunnel**:

```bash
make ngrok
# Note the HTTPS URL (e.g., https://bison-outgoing-amazingly.ngrok-free.app)
```

**Terminal 3 - Development**:

```bash
# Continue development while bot is running
make test-unit
make lint-fix
make format
```

### Configure WhatsApp Webhook

1. Go to [Meta for Developers](https://developers.facebook.com)
2. Navigate to your app → WhatsApp → Configuration
3. Set Webhook URL: `https://your-ngrok-url.ngrok-free.app/webhook`
4. Set Verify Token: Same as `WHATSAPP_WEBHOOK_VERIFY_TOKEN` in `.env`
5. Subscribe to webhook fields: `messages`, `message_status`

### Testing the Bot

1. Send a WhatsApp message to your configured number
2. Monitor webhook traffic at `http://127.0.0.1:4040`
3. Check application logs: `docker logs -f is_it_stolen_app`

### Creating Your First Feature

1. **Check available issues**: `https://github.com/barry47products/is-it-stolen/issues`
2. **Assign yourself**: Click "Assignees" → Select yourself
3. **Create branch**: `make issue number=X name=feature-name`
4. **Develop with TDD**: Write test → Write code → Refactor
5. **Commit frequently**: Small, focused commits with issue references
6. **Create PR**: Link to issue with "Closes #X"
7. **Get review**: Can use Claude for code review
8. **Merge and celebrate**: Auto-closes issue on merge

---

name: Feature
about: New feature or enhancement
title: '[FEATURE] '
labels: 'enhancement'
assignees: ''

---

## User Story

As a [type of user], I want [goal] so that [benefit].

## Description

Clear description of the feature.

## Acceptance Criteria

- [ ] Given [context], when [action], then [outcome]
- [ ] Given [context], when [action], then [outcome]

## Technical Requirements

- [ ] Unit tests with >80% coverage
- [ ] Integration tests if external dependencies
- [ ] Type hints for all functions
- [ ] Documentation updated

## Implementation Notes

Any technical considerations or dependencies.

## Definition of Done

- [ ] Code complete with tests
- [ ] Code reviewed via PR
- [ ] Documentation updated
- [ ] Deployed to development

Create `.github/ISSUE_TEMPLATE/bug.md`:

```markdown
---
name: Bug Report
about: Report a bug
title: "[BUG] "
labels: "bug"
assignees: ""
---

## Bug Description

Clear description of the bug.

## Steps to Reproduce

1. Step one
2. Step two
3. Step three

## Expected Behaviour

What should happen.

## Actual Behaviour

What actually happens.

## Environment

- Python version:
- OS:
- WhatsApp API version:

## Additional Context

Any other relevant information.
```

Create `.github/ISSUE_TEMPLATE/task.md`:

```markdown
---
name: Task
about: Technical task or chore
title: "[TASK] "
labels: "chore"
assignees: ""
---

## Task Description

What needs to be done and why.

## Checklist

- [ ] Task item 1
- [ ] Task item 2
- [ ] Task item 3

## Definition of Done

- [ ] Task complete
- [ ] Tests pass
- [ ] Documentation updated if needed
```

### Example Issues for Is It Stolen

#### Issue #1: Domain Layer - Location Value Object

```markdown
**Title**: [FEATURE] Implement Location value object with validation

**User Story**:
As a developer, I want a Location value object that validates coordinates so that we ensure data integrity.

**Acceptance Criteria**:

- [ ] Given valid coordinates, when creating Location, then object is created
- [ ] Given invalid latitude (<-90 or >90), when creating Location, then ValueError raised
- [ ] Given invalid longitude (<-180 or >180), when creating Location, then ValueError raised
- [ ] Given two locations, when calculating distance, then returns kilometres using Haversine formula

**Technical Requirements**:

- [ ] Immutable (frozen dataclass)
- [ ] Full type hints
- [ ] 100% test coverage
- [ ] Haversine distance calculation

**Branch**: `feat/1-location-value-object`
```

#### Issue #2: Domain Layer - ItemCategory Value Object

```markdown
**Title**: [FEATURE] Implement ItemCategory enumeration with parsing

**User Story**:
As a user, I want the bot to understand different item categories from natural language so that I can report items easily.

**Acceptance Criteria**:

- [ ] Given exact category name, when parsing, then returns correct enum
- [ ] Given keyword (e.g., "bike"), when parsing, then returns BICYCLE category
- [ ] Given unknown text, when parsing, then returns OTHER category
- [ ] Given empty string, when parsing, then returns OTHER category

**Technical Requirements**:

- [ ] Enum with categories: ELECTRONICS, BICYCLE, VEHICLE, JEWELLERY, DOCUMENT, CLOTHING, OTHER
- [ ] Keyword mapping for natural language parsing
- [ ] Full test coverage

**Branch**: `feat/2-item-category-enum`
```

#### Issue #3: Domain Layer - StolenItem Entity

```markdown
**Title**: [FEATURE] Implement StolenItem aggregate root

**User Story**:
As a system, I want to model stolen items with validation and domain events so that business rules are enforced.

**Acceptance Criteria**:

- [ ] Given valid data, when creating StolenItem, then entity created with ItemReportedEvent
- [ ] Given description <10 chars, when creating, then ValueError raised
- [ ] Given description >500 chars, when creating, then ValueError raised
- [ ] Given vehicle category without registration, when creating, then ValueError raised
- [ ] Given police report, when verifying, then item marked verified with ItemVerifiedEvent
- [ ] Given already verified item, when verifying again, then ValueError raised

**Technical Requirements**:

- [ ] Domain events for reporting and verification
- [ ] Category-specific validation rules
- [ ] Image management (max 5 images)
- [ ] Full test coverage

**Branch**: `feat/3-stolen-item-entity`
```

#### Issue #4: Infrastructure - WhatsApp Client

```markdown
**Title**: [FEATURE] Implement WhatsApp REST API client

**User Story**:
As a developer, I want a WhatsApp client that handles API communication so that we can send and receive messages.

**Acceptance Criteria**:

- [ ] Given recipient and text, when sending message, then message sent via API
- [ ] Given buttons data, when sending interactive message, then buttons displayed
- [ ] Given location request, when sending, then location prompt shown
- [ ] Given media ID, when downloading, then media bytes returned
- [ ] Given network error, when sending, then retries with exponential backoff

**Technical Requirements**:

- [ ] Direct REST API implementation (no SDK)
- [ ] Retry logic with tenacity
- [ ] Full type hints
- [ ] Mock tests (no real API calls)

**Branch**: `feat/4-whatsapp-client`
```

#### Issue #5: Application Layer - Report Stolen Item Use Case

```markdown
**Title**: [FEATURE] Implement report stolen item command handler

**User Story**:
As a user, I want to report a stolen item through the bot so that others can be alerted.

**Acceptance Criteria**:

- [ ] Given valid report data, when executing command, then item saved to database
- [ ] Given valid report data, when executing command, then domain events published
- [ ] Given valid report data, when executing command, then confirmation sent to user
- [ ] Given police report number, when executing command, then item marked as verified
- [ ] Given invalid data, when executing command, then appropriate error returned

**Technical Requirements**:

- [ ] Command pattern implementation
- [ ] Repository pattern for persistence
- [ ] Event publishing
- [ ] Full test coverage with mocks

**Branch**: `feat/5-report-stolen-item-command`
```

### Issue Workflow

```bash
# 1. Create issue on GitHub
# Go to https://github.com/barry47products/is-it-stolen/issues/new
# Select template and fill in details

# 2. Start work on issue
export ISSUE_NUMBER=1
git checkout main
git pull origin main
git checkout -b feat/$ISSUE_NUMBER-location-value-object

# 3. Make commits linked to issue
git add src/domain/value_objects/location.py
git commit -m "feat: implement Location value object

Implements immutable Location value object with coordinate
validation and Haversine distance calculation.

Resolves #$ISSUE_NUMBER"

# 4. Push and create PR
git push -u origin feat/$ISSUE_NUMBER-location-value-object

# 5. Create PR with issue link
# Title: "feat: Location value object (#1)"
# Body: "Closes #1"
```

### Commit Message Format with Issues

```bash
# Feature implementation
git commit -m "feat: add location-based search

Implements PostGIS-based radius search for finding
stolen items near a location.

Part of #15"

# Bug fix
git commit -m "fix: correct distance calculation

Fixes Haversine formula implementation that was
returning distances in miles instead of kilometres.

Fixes #23"

# Test addition
git commit -m "test: add integration tests for WhatsApp webhook

Covers all webhook message types and error scenarios.

Part of #8"
```

### Pull Request Template

Create `.github/pull_request_template.md`:

```markdown
## Description

Brief description of changes.

## Related Issue

Closes #[issue number]

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass (if applicable)
- [ ] Test coverage maintained/improved

## Checklist

- [ ] Code follows clean code principles
- [ ] Functions < 10 lines
- [ ] No magic values
- [ ] Type hints added
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] Issue linked correctly

## Screenshots (if applicable)

Add screenshots for UI changes.
```

### Makefile Updates for Issues

Add to `Makefile`:

```makefile
issue: ## Create branch for issue (usage: make issue number=1 name=location-value-object)
    git checkout main
    git pull origin main
    git checkout -b feat/$(number)-$(name)
    @echo "Branch created for issue #$(number)"
    @echo "Make commits with 'Part of #$(number)' or 'Closes #$(number)'"

pr-issue: ## Create PR for issue (usage: make pr-issue number=1)
    @current_branch=$(git branch --show-current); \
    git push -u origin $current_branch; \
    echo "Branch pushed. Create PR at:"; \
    echo "https://github.com/barry47products/is-it-stolen/compare/$current_branch?expand=1"; \
    echo ""; \
    echo "Remember to:"; \
    echo "1. Add 'Closes #$(number)' to PR description"; \
    echo "2. Link the issue in the PR sidebar"
```

### Project Board Setup

1. Go to `https://github.com/barry47products/is-it-stolen/projects`
2. Create a new project board
3. Add columns:
   - **Backlog**: Issues not yet started
   - **Ready**: Issues ready to work on
   - **In Progress**: Issues being worked on
   - **In Review**: PRs awaiting review
   - **Done**: Completed issues

### Example Development Session with Issues

```bash
# 1. Check project board for next issue
# Pick issue #1: Location value object

# 2. Create branch for issue
make issue number=1 name=location-value-object

# 3. Write failing test first (TDD)
cat > tests/unit/domain/value_objects/test_location.py << 'EOF'
import pytest
from src.domain.value_objects.location import Location

def test_creates_valid_location():
    location = Location(51.5074, -0.1278, "London")
    assert location.latitude == 51.5074
EOF

make test-unit  # Verify test fails

# 4. Implement feature
# Create src/domain/value_objects/location.py

# 5. Make test pass
make test-unit  # Verify test passes

# 6. Commit with issue reference
git add -A
git commit -m "feat: implement Location value object

Adds immutable Location value object with coordinate
validation and distance calculation.

Closes #1"

# 7. Create PR
make pr-issue number=1

# 8. After PR approval and merge
git checkout main
git pull origin main
git branch -d feat/1-location-value-object
```

## Development Setup

### 1. Initial Setup

```bash
# Create project
mkdir is_it_stolen && cd is_it_stolen

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Initialise project
poetry init --name is-it-stolen --python "^3.11"
poetry config virtualenvs.in-project true

# Git setup (trunk-based development)
git init
git checkout -b main
echo ".venv/" > .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo ".env" >> .gitignore
echo ".coverage" >> .gitignore
echo ".pytest_cache/" >> .gitignore
echo ".ruff_cache/" >> .gitignore
echo ".mypy_cache/" >> .gitignore
echo "dist/" >> .gitignore
echo "*.egg-info/" >> .gitignore
```

### 2. Dependencies with Poetry

Create `pyproject.toml`:

```toml
[tool.poetry]
name = "is-it-stolen"
version = "1.0.0"
description = "WhatsApp bot for checking and reporting stolen items"
authors = ["Your Name <email@example.com>"]
readme = "README.md"
packages = [{include = "src"}]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.1"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"
sqlalchemy = "^2.0.23"
alembic = "^1.12.1"
psycopg2-binary = "^2.9.9"
geoalchemy2 = "^0.14.2"
redis = "^5.0.1"
celery = "^5.3.4"
httpx = "^0.25.2"
tenacity = "^8.2.3"
sentry-sdk = {extras = ["fastapi"], version = "^1.38.0"}

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
pytest-mock = "^3.12.0"
faker = "^20.1.0"
factory-boy = "^3.3.0"
freezegun = "^1.2.2"
ruff = "^0.1.7"
mypy = "^1.7.1"
pre-commit = "^3.5.0"
ipython = "^8.18.1"
ipdb = "^0.13.13"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

# Ruff configuration (replaces Black, isort, flake8, and more)
[tool.ruff]
target-version = "py311"
line-length = 88
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "ARG",  # flake8-unused-arguments
    "SIM",  # flake8-simplify
    "TCH",  # flake8-type-checking
    "DTZ",  # flake8-datetimez
    "RUF",  # Ruff-specific rules
]
ignore = [
    "E501",  # line too long (handled by formatter)
    "B008",  # do not perform function calls in argument defaults
]
exclude = [
    ".venv",
    "__pycache__",
    ".git",
    ".ruff_cache",
    ".mypy_cache",
    ".pytest_cache",
    "alembic",
]

[tool.ruff.per-file-ignores]
"tests/*" = ["ARG"]  # Unused arguments in tests are OK

[tool.ruff.isort]
known-first-party = ["src"]
force-single-line = false

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false

# MyPy configuration
[tool.mypy]
python_version = "3.11"
plugins = ["pydantic.mypy"]
follow_imports = "normal"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
check_untyped_defs = true
strict_equality = true
show_error_codes = true
pretty = true

[[tool.mypy.overrides]]
module = [
    "geoalchemy2.*",
    "redis.*",
    "celery.*",
    "alembic.*",
]
ignore_missing_imports = true

# Pytest configuration
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--cov=src",
    "--cov-branch",
    "--cov-report=term-missing:skip-covered",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=80",
]
asyncio_mode = "auto"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow tests",
]

# Coverage configuration
[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/alembic/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
```

### 3. Install Dependencies

```bash
# Install all dependencies
poetry install

# Activate virtual environment
poetry shell

# Or run commands with poetry run
poetry run python -m pytest
```

### 4. Makefile for Common Tasks

Create `Makefile`:

```makefile
.PHONY: help install test lint type-check format clean run migrate docker-up docker-down

PYTHON := poetry run python
PYTEST := poetry run pytest
RUFF := poetry run ruff
MYPY := poetry run mypy
UVICORN := poetry run uvicorn
ALEMBIC := poetry run alembic

help: ## Show this help message
    @echo 'Usage: make [target]'
    @echo ''
    @echo 'Available targets:'
    @awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  %-15s %s\n", $1, $2 }' $(MAKEFILE_LIST)

install: ## Install dependencies with Poetry
    poetry install

update: ## Update dependencies
    poetry update

test: ## Run all tests
    $(PYTEST)

test-unit: ## Run unit tests only
    $(PYTEST) tests/unit -m unit

test-integration: ## Run integration tests only
    $(PYTEST) tests/integration -m integration

test-e2e: ## Run end-to-end tests only
    $(PYTEST) tests/e2e -m e2e

test-cov: ## Run tests with coverage report
    $(PYTEST) --cov-report=html
    @echo "Coverage report generated in htmlcov/index.html"

lint: ## Run Ruff linter
    $(RUFF) check src tests

lint-fix: ## Run Ruff linter with auto-fix
    $(RUFF) check --fix src tests

format: ## Format code with Ruff
    $(RUFF) format src tests

type-check: ## Run MyPy type checking
    $(MYPY) src

check: lint type-check test ## Run all checks (lint, type-check, test)

clean: ## Clean up generated files
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    find . -type f -name ".coverage" -delete
    find . -type f -name "coverage.xml" -delete

run: ## Run the application locally
    $(UVICORN) src.presentation.api.app:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run the application in production mode
    $(UVICORN) src.presentation.api.app:app --host 0.0.0.0 --port 8000 --workers 4

migrate-create: ## Create a new migration
    $(ALEMBIC) revision -m "$(message)"

migrate-up: ## Apply migrations
    $(ALEMBIC) upgrade head

migrate-down: ## Rollback last migration
    $(ALEMBIC) downgrade -1

migrate-history: ## Show migration history
    $(ALEMBIC) history

docker-build: ## Build Docker image
    docker build -t is-it-stolen:latest .

docker-up: ## Start all services with docker-compose
    docker-compose up -d

docker-down: ## Stop all services
    docker-compose down

docker-logs: ## Show docker logs
    docker-compose logs -f

docker-clean: ## Clean docker resources
    docker-compose down -v
    docker system prune -f

db-shell: ## Connect to PostgreSQL shell
    docker exec -it is_it_stolen_postgres_1 psql -U admin -d is_it_stolen

redis-cli: ## Connect to Redis CLI
    docker exec -it is_it_stolen_redis_1 redis-cli

pre-commit: ## Run pre-commit hooks
    poetry run pre-commit run --all-files

setup-hooks: ## Install pre-commit hooks
    poetry run pre-commit install
    poetry run pre-commit install --hook-type commit-msg

# Development workflow commands
dev-setup: install setup-hooks ## Complete development setup

feature: ## Create a feature branch (usage: make feature name=my-feature)
    git checkout -b feat/$(name)
    git push -u origin feat/$(name)

pr: ## Create a pull request for review
    @echo "Creating PR from current branch to main..."
    @current_branch=$(git branch --show-current); \
    if [ "$current_branch" = "main" ]; then \
        echo "Error: Cannot create PR from main branch"; \
        exit 1; \
    fi; \
    git push origin $current_branch; \
    echo "Branch pushed. Create PR at: https://github.com/yourusername/is-it-stolen/compare/$current_branch?expand=1"

# CI/CD commands
ci-test: ## Run CI test suite
    $(PYTEST) --cov-report=xml --cov-report=term

ci-lint: ## Run CI linting
    $(RUFF) check src tests --format=github
    $(MYPY) src --no-error-summary

ci-build: ## Build for CI
    poetry build

# Utility commands
shell: ## Open IPython shell with app context
    $(PYTHON) -c "from src.presentation.api.app import *; import IPython; IPython.embed()"

requirements: ## Export requirements.txt for compatibility
    poetry export -f requirements.txt --output requirements.txt --without-hashes

version: ## Show current version
    @poetry version

bump-patch: ## Bump patch version
    poetry version patch

bump-minor: ## Bump minor version
    poetry version minor

bump-major: ## Bump major version
    poetry version major
```

### 6. Ngrok Setup for WhatsApp Webhooks

WhatsApp requires HTTPS endpoints for webhooks. In development, we use ngrok to create a secure tunnel to localhost.

#### Install Ngrok

```bash
# macOS
brew install ngrok/ngrok/ngrok

# Linux
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Or download from https://ngrok.com/download
```

#### Configure Ngrok

Create `~/.config/ngrok/ngrok.yml` (or `~/.ngrok2/ngrok.yml` on older versions):

```yaml
version: "2"
authtoken: your_auth_token_here # Get from https://dashboard.ngrok.com
region: eu # or us, ap, au, sa, jp, in

tunnels:
  backend:
    proto: http
    addr: 8000
    schemes:
      - https
    host_header: localhost:8000

  # Optional: Add more tunnels for different services
  redis:
    proto: tcp
    addr: 6379

  postgres:
    proto: tcp
    addr: 5432
```

#### Using Ngrok in Development

```bash
# Start ngrok tunnel
ngrok start backend

# You'll see output like:
# Forwarding: https://bison-outgoing-amazingly.ngrok-free.app -> https://localhost:8000

# Copy the HTTPS URL and update WhatsApp webhook configuration
```

#### Update Makefile with Ngrok Commands

Add to `Makefile`:

```makefile
ngrok: ## Start ngrok tunnel for WhatsApp webhooks
    ngrok start backend

ngrok-setup: ## Setup ngrok configuration
    @echo "Setting up ngrok..."
    @read -p "Enter your ngrok authtoken: " token; \
    ngrok config add-authtoken $token
    @echo "Ngrok configured successfully"

webhook-test: ## Test WhatsApp webhook endpoint
    @echo "Testing webhook endpoint..."
    curl -X GET "http://localhost:8000/webhook?hub.mode=subscribe&hub.verify_token=$(WHATSAPP_WEBHOOK_VERIFY_TOKEN)&hub.challenge=test"

dev: ## Start full development environment
    @echo "Starting development environment..."
    @make docker-up
    @sleep 5
    @make migrate-up
    @echo "Starting application..."
    @make run &
    @sleep 3
    @echo "Starting ngrok tunnel..."
    @make ngrok
```

#### Development Workflow with Ngrok

1. **Start services and application**:

   ```bash
   make docker-up   # Start PostgreSQL and Redis
   make migrate-up  # Apply migrations
   make run        # Start FastAPI app on port 8000
   ```

2. **In a new terminal, start ngrok**:

   ```bash
   make ngrok
   # Or directly: ngrok start backend
   ```

3. **Configure WhatsApp webhook**:

   - Copy the HTTPS URL from ngrok (e.g., `https://bison-outgoing-amazingly.ngrok-free.app`)
   - Go to Meta Developer Console
   - Update webhook URL: `https://your-ngrok-url.ngrok-free.app/webhook`
   - Verify the webhook using your verify token

4. **Monitor webhook traffic**:

   - Ngrok Web Interface: `http://127.0.0.1:4040`
   - View all requests, replay them, and inspect payloads

#### Environment Variables for Ngrok

Update `.env` for development:

```env
# Development with ngrok
WEBHOOK_URL=https://your-ngrok-url.ngrok-free.app/webhook
# This changes each time you restart ngrok unless you have a paid plan
```

#### Tips for Ngrok Development

1. **Persistent URLs** (paid feature):

   - Free tier gives random URLs each session
   - Paid plans offer custom subdomains

2. **Request inspection**:

   - Use `http://127.0.0.1:4040` to inspect all webhook requests
   - Replay requests for debugging

3. **Rate limiting**:

   - Free tier: 40 requests/minute
   - Sufficient for development

4. **Security**:
   - Always verify webhook signatures
   - Ngrok URLs are public - ensure proper authentication

### 7. Working with Poetry

```bash
# Add dependencies
poetry add fastapi                    # Add production dependency
poetry add --group dev pytest         # Add development dependency

# Update dependencies
poetry update                          # Update all packages
poetry update fastapi                  # Update specific package

# Show dependencies
poetry show                            # List all packages
poetry show --tree                     # Show dependency tree
poetry show --latest                   # Show latest available versions

# Virtual environment
poetry shell                           # Activate virtual environment
poetry env info                        # Show environment info
poetry env list                        # List all environments
poetry env remove python3.11           # Remove environment

# Run commands in virtual environment
poetry run python src/main.py          # Run Python script
poetry run pytest                      # Run tests
poetry run uvicorn src.app:app         # Run server

# Build and publish
poetry build                           # Build distribution packages
poetry publish                         # Publish to PyPI

# Export requirements (for compatibility)
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

```env
ENVIRONMENT=development
DATABASE_URL=postgresql://user:pass@localhost:5432/is_it_stolen
REDIS_URL=redis://localhost:6379/0
WHATSAPP_ACCESS_TOKEN=your_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_WEBHOOK_SECRET=webhook_secret
WHATSAPP_WEBHOOK_VERIFY_TOKEN=verify_token
SECRET_KEY=your_secret_key
```

### 5. Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  # Ruff - replaces Black, isort, flake8, and more
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.7
    hooks:
      # Run the linter
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      # Run the formatter
      - id: ruff-format

  # MyPy for type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, types-redis, sqlalchemy]
        args: [--config-file=pyproject.toml]
        pass_filenames: false
        entry: sh -c 'poetry run mypy src'

  # General file fixes
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: mixed-line-ending
      - id: detect-private-key
      - id: debug-statements
      - id: check-added-large-files
        args: [--maxkb=500]

  # Commit message linting
  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.13.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
```

Install: `make setup-hooks`

## Domain Layer Implementation

### Value Objects

#### Location Value Object

Create `src/domain/value_objects/location.py`:

```python
"""Location value object for geographical coordinates."""
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Optional

# Constants
EARTH_RADIUS_KM = 6371.0
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
        self._validate_latitude()
        self._validate_longitude()

    def _validate_latitude(self) -> None:
        """Ensure latitude is within valid range."""
        if not MIN_LATITUDE <= self.latitude <= MAX_LATITUDE:
            raise ValueError(f"Invalid latitude: {self.latitude}")

    def _validate_longitude(self) -> None:
        """Ensure longitude is within valid range."""
        if not MIN_LONGITUDE <= self.longitude <= MAX_LONGITUDE:
            raise ValueError(f"Invalid longitude: {self.longitude}")

    def distance_km_to(self, other: 'Location') -> float:
        """
        Calculate distance to another location using Haversine formula.

        Args:
            other: Target location

        Returns:
            Distance in kilometres
        """
        lat1 = radians(self.latitude)
        lon1 = radians(self.longitude)
        lat2 = radians(other.latitude)
        lon2 = radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (sin(dlat / 2) ** 2 +
             cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2)
        c = 2 * asin(sqrt(a))

        return EARTH_RADIUS_KM * c
```

Test: `tests/unit/domain/value_objects/test_location.py`:

```python
"""Tests for Location value object."""
import pytest

from src.domain.value_objects.location import Location


class TestLocation:
    """Test Location value object behaviour."""

    def test_creates_valid_location(self):
        """Should create location with valid coordinates."""
        # Arrange & Act
        location = Location(
            latitude=51.5074,
            longitude=-0.1278,
            address="London, UK"
        )

        # Assert
        assert location.latitude == 51.5074
        assert location.longitude == -0.1278
        assert location.address == "London, UK"

    def test_location_is_immutable(self):
        """Should not allow modification after creation."""
        # Arrange
        location = Location(latitude=0.0, longitude=0.0)

        # Act & Assert
        with pytest.raises(AttributeError):
            location.latitude = 10.0

    @pytest.mark.parametrize("invalid_latitude", [91, -91, 200, -200])
    def test_rejects_invalid_latitude(self, invalid_latitude):
        """Should reject latitude outside valid range."""
        with pytest.raises(ValueError, match="Invalid latitude"):
            Location(latitude=invalid_latitude, longitude=0)

    @pytest.mark.parametrize("invalid_longitude", [181, -181, 360, -360])
    def test_rejects_invalid_longitude(self, invalid_longitude):
        """Should reject longitude outside valid range."""
        with pytest.raises(ValueError, match="Invalid longitude"):
            Location(latitude=0, longitude=invalid_longitude)

    def test_calculates_distance_between_locations(self):
        """Should calculate distance using Haversine formula."""
        # Arrange
        london = Location(51.5074, -0.1278)
        paris = Location(48.8566, 2.3522)

        # Act
        distance = london.distance_km_to(paris)

        # Assert - Distance should be approximately 344 km
        assert 340 < distance < 350
```

#### Item Category Value Object

Create `src/domain/value_objects/item_category.py`:

```python
"""Item category enumeration and parsing."""
from enum import Enum
from typing import Dict, Optional


class ItemCategory(Enum):
    """Categories for stolen items."""

    ELECTRONICS = "electronics"
    BICYCLE = "bicycle"
    VEHICLE = "vehicle"
    JEWELLERY = "jewellery"
    DOCUMENT = "document"
    CLOTHING = "clothing"
    OTHER = "other"

    @classmethod
    def from_user_input(cls, text: str) -> 'ItemCategory':
        """
        Parse user input to category.

        Args:
            text: User input text

        Returns:
            Matched category or OTHER
        """
        if not text:
            return cls.OTHER

        normalised = text.lower().strip()

        # Direct match
        for category in cls:
            if category.value == normalised:
                return category

        # Keyword matching
        keyword_map = cls._get_keyword_map()
        for category, keywords in keyword_map.items():
            if any(keyword in normalised for keyword in keywords):
                return category

        return cls.OTHER

    @classmethod
    def _get_keyword_map(cls) -> Dict['ItemCategory', list[str]]:
        """Get mapping of categories to keywords."""
        return {
            cls.ELECTRONICS: ['phone', 'laptop', 'tablet', 'computer', 'camera'],
            cls.BICYCLE: ['bike', 'cycle', 'bicycle'],
            cls.VEHICLE: ['car', 'van', 'motorbike', 'motorcycle', 'scooter'],
            cls.JEWELLERY: ['ring', 'necklace', 'watch', 'bracelet', 'chain'],
            cls.DOCUMENT: ['passport', 'license', 'id', 'certificate'],
            cls.CLOTHING: ['jacket', 'coat', 'bag', 'shoes', 'shirt'],
        }
```

### Domain Entities

#### Stolen Item Entity

Create `src/domain/entities/stolen_item.py`:

```python
"""Stolen item aggregate root."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from src.domain.events.base import DomainEvent
from src.domain.events.item_events import ItemReportedEvent, ItemVerifiedEvent
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location

# Constants
MIN_DESCRIPTION_LENGTH = 10
MAX_DESCRIPTION_LENGTH = 500
MIN_IMAGE_COUNT = 0
MAX_IMAGE_COUNT = 5


@dataclass
class StolenItem:
    """Aggregate root for stolen item reports."""

    # Identity
    id: UUID = field(default_factory=uuid4)

    # Core attributes
    category: ItemCategory
    description: str
    location: Location
    reported_at: datetime
    reporter_phone: str

    # Additional data
    attributes: Dict[str, Any] = field(default_factory=dict)
    images: List[str] = field(default_factory=list)

    # Verification
    is_verified: bool = False
    police_report_number: Optional[str] = None
    verified_at: Optional[datetime] = None

    # Domain events
    _events: List[DomainEvent] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        """Validate and emit creation event."""
        self._validate()
        self._emit_created_event()

    def _validate(self) -> None:
        """Apply domain validation rules."""
        self._validate_description()
        self._validate_category_specific_rules()
        self._validate_images()

    def _validate_description(self) -> None:
        """Ensure description meets requirements."""
        if len(self.description) < MIN_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description must be at least {MIN_DESCRIPTION_LENGTH} characters"
            )

        if len(self.description) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description must not exceed {MAX_DESCRIPTION_LENGTH} characters"
            )

    def _validate_category_specific_rules(self) -> None:
        """Apply category-specific validation."""
        if self.category == ItemCategory.VEHICLE:
            if "registration" not in self.attributes:
                raise ValueError("Vehicle reports must include registration")

        if self.category == ItemCategory.DOCUMENT:
            if "document_type" not in self.attributes:
                raise ValueError("Document reports must specify document type")

    def _validate_images(self) -> None:
        """Ensure image count is within limits."""
        if len(self.images) > MAX_IMAGE_COUNT:
            raise ValueError(f"Maximum {MAX_IMAGE_COUNT} images allowed")

    def _emit_created_event(self) -> None:
        """Emit domain event for item creation."""
        self._events.append(
            ItemReportedEvent(
                item_id=self.id,
                category=self.category,
                location=self.location,
                reported_at=self.reported_at
            )
        )

    def verify_with_police_report(self, report_number: str) -> None:
        """
        Verify the item with a police report.

        Args:
            report_number: Police report reference

        Raises:
            ValueError: If already verified
        """
        if self.is_verified:
            raise ValueError("Item already verified")

        if not report_number or len(report_number) < 5:
            raise ValueError("Invalid police report number")

        self.is_verified = True
        self.police_report_number = report_number
        self.verified_at = datetime.utcnow()

        self._events.append(
            ItemVerifiedEvent(
                item_id=self.id,
                report_number=report_number,
                verified_at=self.verified_at
            )
        )

    def add_image(self, image_url: str) -> None:
        """
        Add an image to the report.

        Args:
            image_url: URL of the image

        Raises:
            ValueError: If image limit exceeded
        """
        if len(self.images) >= MAX_IMAGE_COUNT:
            raise ValueError(f"Maximum {MAX_IMAGE_COUNT} images allowed")

        self.images.append(image_url)

    def collect_events(self) -> List[DomainEvent]:
        """Collect and clear domain events."""
        events = self._events.copy()
        self._events.clear()
        return events
```

### Domain Events

Create `src/domain/events/base.py`:

```python
"""Base domain event."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    """Base class for domain events."""

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.__class__.__name__,
            "occurred_at": self.occurred_at.isoformat(),
            "data": {
                k: v for k, v in self.__dict__.items()
                if k not in ["event_id", "occurred_at"]
            }
        }
```

Create `src/domain/events/item_events.py`:

```python
"""Item-related domain events."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.events.base import DomainEvent
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location


@dataclass(frozen=True)
class ItemReportedEvent(DomainEvent):
    """Event emitted when an item is reported stolen."""

    item_id: UUID
    category: ItemCategory
    location: Location
    reported_at: datetime


@dataclass(frozen=True)
class ItemVerifiedEvent(DomainEvent):
    """Event emitted when an item is verified with police report."""

    item_id: UUID
    report_number: str
    verified_at: datetime


@dataclass(frozen=True)
class ItemMatchFoundEvent(DomainEvent):
    """Event emitted when a potential match is found."""

    search_id: UUID
    item_id: UUID
    similarity_score: float
    searcher_phone: str
```

### Domain Services

Create `src/domain/services/matching_service.py`:

```python
"""Service for matching stolen items."""
from dataclasses import dataclass
from typing import List, Optional

from src.domain.entities.stolen_item import StolenItem

# Matching thresholds
DEFAULT_SIMILARITY_THRESHOLD = 0.6
HIGH_CONFIDENCE_THRESHOLD = 0.8
EXACT_MATCH_THRESHOLD = 0.95


@dataclass
class MatchResult:
    """Result of matching operation."""

    item: StolenItem
    similarity_score: float
    distance_km: Optional[float] = None


class MatchingService:
    """Domain service for matching stolen items."""

    def find_matches(
        self,
        description: str,
        candidates: List[StolenItem],
        threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        location: Optional[Location] = None
    ) -> List[MatchResult]:
        """
        Find matching items from candidates.

        Args:
            description: Search description
            candidates: List of items to search
            threshold: Minimum similarity score
            location: Optional location for distance calculation

        Returns:
            List of matches above threshold
        """
        matches = []

        for candidate in candidates:
            score = self._calculate_similarity(description, candidate.description)

            if score >= threshold:
                distance = None
                if location:
                    distance = location.distance_km_to(candidate.location)

                matches.append(
                    MatchResult(
                        item=candidate,
                        similarity_score=score,
                        distance_km=distance
                    )
                )

        # Sort by score descending
        return sorted(matches, key=lambda m: m.similarity_score, reverse=True)

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts.

        Simple implementation - replace with better algorithm.
        """
        # Normalise texts
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)
```

## Application Layer Implementation

### Commands

Create `src/application/commands/report_stolen_item.py`:

```python
"""Command for reporting stolen items."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.domain.entities.stolen_item import StolenItem
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location


@dataclass
class ReportStolenItemCommand:
    """Command to report a stolen item."""

    category: str
    description: str
    latitude: float
    longitude: float
    reporter_phone: str
    address: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    images: List[str] = field(default_factory=list)
    police_report_number: Optional[str] = None


class ReportStolenItemHandler:
    """Handler for report stolen item command."""

    def __init__(
        self,
        item_repository,
        event_publisher,
        notification_service
    ):
        """Initialise with dependencies."""
        self.item_repository = item_repository
        self.event_publisher = event_publisher
        self.notification_service = notification_service

    async def handle(self, command: ReportStolenItemCommand) -> UUID:
        """
        Execute the command.

        Args:
            command: The command to execute

        Returns:
            ID of created item
        """
        # Create value objects
        location = Location(
            latitude=command.latitude,
            longitude=command.longitude,
            address=command.address
        )

        category = ItemCategory.from_user_input(command.category)

        # Create entity
        item = StolenItem(
            category=category,
            description=command.description,
            location=location,
            reported_at=datetime.utcnow(),
            reporter_phone=command.reporter_phone,
            attributes=command.attributes,
            images=command.images
        )

        # Apply domain logic
        if command.police_report_number:
            item.verify_with_police_report(command.police_report_number)

        # Persist
        await self.item_repository.save(item)

        # Publish events
        for event in item.collect_events():
            await self.event_publisher.publish(event)

        # Send confirmation
        await self.notification_service.send_confirmation(
            command.reporter_phone,
            item.id
        )

        return item.id
```

### Queries

Create `src/application/queries/check_if_stolen.py`:

```python
"""Query for checking if an item is stolen."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from src.domain.services.matching_service import MatchingService
from src.domain.value_objects.location import Location

# Search parameters
DEFAULT_SEARCH_RADIUS_KM = 50.0
MAX_SEARCH_RADIUS_KM = 200.0


@dataclass
class CheckIfStolenQuery:
    """Query to check if an item is stolen."""

    description: str
    category: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    search_radius_km: float = DEFAULT_SEARCH_RADIUS_KM


@dataclass
class SearchResult:
    """DTO for search results."""

    item_id: UUID
    description: str
    similarity_score: float
    distance_km: Optional[float]
    reported_date: datetime
    is_verified: bool
    category: str


class CheckIfStolenHandler:
    """Handler for checking stolen items."""

    def __init__(
        self,
        item_repository,
        matching_service: MatchingService
    ):
        """Initialise with dependencies."""
        self.item_repository = item_repository
        self.matching_service = matching_service

    async def handle(self, query: CheckIfStolenQuery) -> List[SearchResult]:
        """
        Execute the query.

        Args:
            query: The search query

        Returns:
            List of matching items
        """
        # Validate search radius
        radius = min(query.search_radius_km, MAX_SEARCH_RADIUS_KM)

        # Get candidates
        if query.latitude and query.longitude:
            location = Location(query.latitude, query.longitude)
            candidates = await self.item_repository.find_within_radius(
                location, radius
            )
        elif query.category:
            category = ItemCategory.from_user_input(query.category)
            candidates = await self.item_repository.find_by_category(category)
        else:
            candidates = await self.item_repository.find_recent(limit=100)

        # Find matches
        matches = self.matching_service.find_matches(
            query.description,
            candidates,
            location=location if query.latitude else None
        )

        # Convert to DTOs
        return [
            SearchResult(
                item_id=match.item.id,
                description=match.item.description,
                similarity_score=match.similarity_score,
                distance_km=match.distance_km,
                reported_date=match.item.reported_at,
                is_verified=match.item.is_verified,
                category=match.item.category.value
            )
            for match in matches
        ]
```

## Infrastructure Layer Implementation

### Configuration

Create `src/infrastructure/config.py`:

```python
"""Application configuration."""
from enum import Enum
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Application environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings."""

    # Environment
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        env="ENVIRONMENT"
    )

    # WhatsApp
    whatsapp_access_token: str = Field(..., env="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str = Field(..., env="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_webhook_secret: str = Field(..., env="WHATSAPP_WEBHOOK_SECRET")
    whatsapp_webhook_verify_token: str = Field(..., env="WHATSAPP_WEBHOOK_VERIFY_TOKEN")

    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_pool_overflow: int = Field(default=10, env="DATABASE_POOL_OVERFLOW")

    # Redis
    redis_url: str = Field(..., env="REDIS_URL")
    redis_max_connections: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")

    # Security
    secret_key: str = Field(..., env="SECRET_KEY")

    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")

    # Feature flags
    enable_ml_matching: bool = Field(default=False, env="ENABLE_ML_MATCHING")
    enable_image_recognition: bool = Field(default=False, env="ENABLE_IMAGE_RECOGNITION")

    @validator("database_url")
    def validate_database_url(cls, v: str, values: dict) -> str:
        """Ensure PostgreSQL in production."""
        if values.get("environment") == Environment.PRODUCTION:
            if not v.startswith("postgresql://"):
                raise ValueError("PostgreSQL required in production")
        return v

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton
settings = Settings()
```

### Database Models

Create `src/infrastructure/persistence/models.py`:

```python
"""SQLAlchemy models."""
from datetime import datetime
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, JSON,
    String, Text
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class StolenItemModel(Base):
    """Database model for stolen items."""

    __tablename__ = "stolen_items"

    # Primary key
    id = Column(PG_UUID(as_uuid=True), primary_key=True)

    # Core fields
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    reported_at = Column(DateTime, nullable=False, index=True)
    reporter_phone = Column(String(20), nullable=False, index=True)

    # Location
    location = Column(Geography("POINT", srid=4326), nullable=False)
    address = Column(String(255))

    # Additional data
    attributes = Column(JSON, default=dict)
    images = Column(JSON, default=list)

    # Verification
    is_verified = Column(Boolean, default=False, index=True)
    police_report_number = Column(String(100))
    verified_at = Column(DateTime)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Full-text search
    __table_args__ = (
        Index('idx_description_fts',
              func.to_tsvector('english', description),
              postgresql_using='gin'),
    )
```

### Repository Implementation

Create `src/infrastructure/persistence/repositories.py`:

```python
"""Repository implementations."""
from typing import List, Optional
from uuid import UUID

from geoalchemy2 import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.stolen_item import StolenItem
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.infrastructure.persistence.models import StolenItemModel


class StolenItemRepository:
    """Repository for stolen items."""

    def __init__(self, session: AsyncSession):
        """Initialise with database session."""
        self.session = session

    async def save(self, item: StolenItem) -> None:
        """
        Save a stolen item.

        Args:
            item: The item to save
        """
        model = self._to_model(item)
        self.session.add(model)
        await self.session.commit()

    async def find_by_id(self, item_id: UUID) -> Optional[StolenItem]:
        """
        Find item by ID.

        Args:
            item_id: The item ID

        Returns:
            The item if found
        """
        result = await self.session.execute(
            select(StolenItemModel).where(StolenItemModel.id == item_id)
        )
        model = result.scalar_one_or_none()

        if model:
            return self._to_entity(model)
        return None

    async def find_within_radius(
        self,
        location: Location,
        radius_km: float
    ) -> List[StolenItem]:
        """
        Find items within radius of location.

        Args:
            location: Centre location
            radius_km: Search radius in kilometres

        Returns:
            List of items within radius
        """
        # Convert radius to metres
        radius_m = radius_km * 1000

        # Create point
        point = func.ST_MakePoint(location.longitude, location.latitude)

        # Query with PostGIS
        result = await self.session.execute(
            select(StolenItemModel)
            .where(
                func.ST_DWithin(
                    StolenItemModel.location,
                    func.ST_SetSRID(point, 4326),
                    radius_m
                )
            )
            .order_by(
                func.ST_Distance(
                    StolenItemModel.location,
                    func.ST_SetSRID(point, 4326)
                )
            )
        )

        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def find_by_category(
        self,
        category: ItemCategory
    ) -> List[StolenItem]:
        """
        Find items by category.

        Args:
            category: The category to search

        Returns:
            List of items in category
        """
        result = await self.session.execute(
            select(StolenItemModel)
            .where(StolenItemModel.category == category.value)
            .order_by(StolenItemModel.reported_at.desc())
            .limit(100)
        )

        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def find_recent(self, limit: int = 100) -> List[StolenItem]:
        """
        Find recent items.

        Args:
            limit: Maximum number of items

        Returns:
            List of recent items
        """
        result = await self.session.execute(
            select(StolenItemModel)
            .order_by(StolenItemModel.reported_at.desc())
            .limit(limit)
        )

        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    def _to_model(self, item: StolenItem) -> StolenItemModel:
        """Convert entity to model."""
        return StolenItemModel(
            id=item.id,
            category=item.category.value,
            description=item.description,
            reported_at=item.reported_at,
            reporter_phone=item.reporter_phone,
            location=f"POINT({item.location.longitude} {item.location.latitude})",
            address=item.location.address,
            attributes=item.attributes,
            images=item.images,
            is_verified=item.is_verified,
            police_report_number=item.police_report_number,
            verified_at=item.verified_at
        )

    def _to_entity(self, model: StolenItemModel) -> StolenItem:
        """Convert model to entity."""
        # Extract coordinates from PostGIS
        coords = self.session.execute(
            select(
                func.ST_X(model.location),
                func.ST_Y(model.location)
            )
        ).first()

        location = Location(
            latitude=coords[1],
            longitude=coords[0],
            address=model.address
        )

        return StolenItem(
            id=model.id,
            category=ItemCategory(model.category),
            description=model.description,
            location=location,
            reported_at=model.reported_at,
            reporter_phone=model.reporter_phone,
            attributes=model.attributes,
            images=model.images,
            is_verified=model.is_verified,
            police_report_number=model.police_report_number,
            verified_at=model.verified_at
        )
```

### WhatsApp Client

Create `src/infrastructure/whatsapp/client.py`:

```python
"""WhatsApp Business API client."""
import logging
from typing import Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# API Configuration
WHATSAPP_API_VERSION = "v18.0"
WHATSAPP_API_BASE_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"

# Message limits
MAX_BUTTON_TITLE_LENGTH = 20
MAX_BUTTONS_PER_MESSAGE = 3
MAX_LIST_SECTIONS = 10


class WhatsAppClient:
    """Client for WhatsApp Business API."""

    def __init__(self, access_token: str, phone_number_id: str):
        """
        Initialise client.

        Args:
            access_token: WhatsApp access token
            phone_number_id: WhatsApp phone number ID
        """
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.base_url = f"{WHATSAPP_API_BASE_URL}/{phone_number_id}"

        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def send_text(self, to: str, text: str) -> Dict:
        """
        Send text message.

        Args:
            to: Recipient phone number
            text: Message text

        Returns:
            API response
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }

        response = await self.client.post(
            f"{self.base_url}/messages",
            json=payload
        )
        response.raise_for_status()

        logger.info(f"Sent text message to {to}")
        return response.json()

    async def send_interactive_buttons(
        self,
        to: str,
        body: str,
        buttons: List[Dict[str, str]],
        header: Optional[str] = None,
        footer: Optional[str] = None
    ) -> Dict:
        """
        Send interactive button message.

        Args:
            to: Recipient phone number
            body: Message body
            buttons: List of button dictionaries with 'id' and 'title'
            header: Optional header text
            footer: Optional footer text

        Returns:
            API response
        """
        if len(buttons) > MAX_BUTTONS_PER_MESSAGE:
            raise ValueError(f"Maximum {MAX_BUTTONS_PER_MESSAGE} buttons allowed")

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": btn["id"],
                                "title": btn["title"][:MAX_BUTTON_TITLE_LENGTH]
                            }
                        }
                        for btn in buttons
                    ]
                }
            }
        }

        if header:
            payload["interactive"]["header"] = {"type": "text", "text": header}
        if footer:
            payload["interactive"]["footer"] = {"text": footer}

        response = await self.client.post(
            f"{self.base_url}/messages",
            json=payload
        )
        response.raise_for_status()

        logger.info(f"Sent button message to {to}")
        return response.json()

    async def send_location_request(self, to: str) -> Dict:
        """
        Request user's location.

        Args:
            to: Recipient phone number

        Returns:
            API response
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "location_request_message",
                "body": {
                    "text": "Please share your location to find nearby items"
                },
                "action": {
                    "name": "send_location"
                }
            }
        }

        response = await self.client.post(
            f"{self.base_url}/messages",
            json=payload
        )
        response.raise_for_status()

        logger.info(f"Requested location from {to}")
        return response.json()

    async def mark_as_read(self, message_id: str) -> Dict:
        """
        Mark message as read.

        Args:
            message_id: WhatsApp message ID

        Returns:
            API response
        """
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        response = await self.client.post(
            f"{self.base_url}/messages",
            json=payload
        )
        response.raise_for_status()

        return response.json()

    async def download_media(self, media_id: str) -> bytes:
        """
        Download media file.

        Args:
            media_id: WhatsApp media ID

        Returns:
            Media content as bytes
        """
        # Get media URL
        response = await self.client.get(
            f"{WHATSAPP_API_BASE_URL}/{media_id}"
        )
        response.raise_for_status()
        media_url = response.json()["url"]

        # Download media
        media_response = await self.client.get(media_url)
        media_response.raise_for_status()

        logger.info(f"Downloaded media {media_id}")
        return media_response.content

    async def close(self) -> None:
        """Close the client."""
        await self.client.aclose()
```

### Webhook Handler

Create `src/infrastructure/whatsapp/webhook.py`:

```python
"""WhatsApp webhook handler."""
import hashlib
import hmac
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class WebhookHandler:
    """Handler for WhatsApp webhooks."""

    def __init__(self, webhook_secret: str, verify_token: str):
        """
        Initialise handler.

        Args:
            webhook_secret: Secret for signature verification
            verify_token: Token for webhook verification
        """
        self.webhook_secret = webhook_secret
        self.verify_token = verify_token

    def verify_signature(self, body: bytes, signature: str) -> bool:
        """
        Verify webhook signature.

        Args:
            body: Request body
            signature: X-Hub-Signature-256 header

        Returns:
            True if signature is valid
        """
        expected = hmac.new(
            self.webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        return f"sha256={expected}" == signature

    def verify_challenge(
        self,
        mode: str,
        token: str,
        challenge: str
    ) -> Optional[int]:
        """
        Verify webhook challenge.

        Args:
            mode: hub.mode parameter
            token: hub.verify_token parameter
            challenge: hub.challenge parameter

        Returns:
            Challenge value if valid
        """
        if mode == "subscribe" and token == self.verify_token:
            logger.info("Webhook verified successfully")
            return int(challenge)

        logger.warning("Invalid webhook verification")
        return None

    def parse_message(self, data: Dict) -> Optional[Dict]:
        """
        Parse incoming message.

        Args:
            data: Webhook payload

        Returns:
            Parsed message data
        """
        try:
            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]

            if "messages" in value:
                message = value["messages"][0]
                contact = value["contacts"][0]

                return {
                    "message_id": message["id"],
                    "from": message["from"],
                    "name": contact.get("profile", {}).get("name", "User"),
                    "type": message["type"],
                    "timestamp": message["timestamp"],
                    "content": self._extract_content(message)
                }

            elif "statuses" in value:
                status = value["statuses"][0]
                return {
                    "type": "status",
                    "status": status["status"],
                    "message_id": status["id"]
                }

        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing webhook: {e}")

        return None

    def _extract_content(self, message: Dict) -> Dict:
        """Extract message content."""
        msg_type = message["type"]

        if msg_type == "text":
            return {
                "type": "text",
                "text": message["text"]["body"]
            }

        elif msg_type == "interactive":
            interactive = message["interactive"]

            if interactive["type"] == "button_reply":
                return {
                    "type": "button_reply",
                    "button_id": interactive["button_reply"]["id"]
                }

            elif interactive["type"] == "list_reply":
                return {
                    "type": "list_reply",
                    "list_id": interactive["list_reply"]["id"]
                }

        elif msg_type == "image":
            return {
                "type": "image",
                "media_id": message["image"]["id"],
                "caption": message["image"].get("caption", "")
            }

        elif msg_type == "location":
            return {
                "type": "location",
                "latitude": message["location"]["latitude"],
                "longitude": message["location"]["longitude"]
            }

        return {"type": msg_type}
```

## Presentation Layer Implementation

### Conversation State Machine

Create `src/presentation/bot/states.py`:

```python
"""Conversation states using State Pattern."""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional


class ConversationState(str, Enum):
    """Conversation states."""

    IDLE = "idle"
    MAIN_MENU = "main_menu"
    REPORTING_CATEGORY = "reporting_category"
    REPORTING_DESCRIPTION = "reporting_description"
    REPORTING_LOCATION = "reporting_location"
    REPORTING_IMAGE = "reporting_image"
    REPORTING_CONFIRM = "reporting_confirm"
    CHECKING_CATEGORY = "checking_category"
    CHECKING_DESCRIPTION = "checking_description"
    CHECKING_RESULTS = "checking_results"
    COMPLETE = "complete"


class StateHandler(ABC):
    """Abstract base for state handlers."""

    @abstractmethod
    async def handle(self, context: Dict, message: Dict) -> ConversationState:
        """
        Handle message in this state.

        Args:
            context: Conversation context
            message: Incoming message

        Returns:
            Next state
        """
        pass

    @abstractmethod
    async def get_prompt(self, context: Dict) -> Dict:
        """
        Get prompt for this state.

        Args:
            context: Conversation context

        Returns:
            Message to send
        """
        pass


class IdleState(StateHandler):
    """Handler for idle state."""

    async def handle(self, context: Dict, message: Dict) -> ConversationState:
        """Handle message in idle state."""
        return ConversationState.MAIN_MENU

    async def get_prompt(self, context: Dict) -> Dict:
        """Get welcome message."""
        return {
            "type": "buttons",
            "header": "🔍 Is It Stolen",
            "body": "I can help you check if an item is stolen or report a stolen item.",
            "buttons": [
                {"id": "check", "title": "Check Item"},
                {"id": "report", "title": "Report Stolen"}
            ],
            "footer": "Your privacy is protected"
        }


class MainMenuState(StateHandler):
    """Handler for main menu state."""

    async def handle(self, context: Dict, message: Dict) -> ConversationState:
        """Handle menu selection."""
        if message["content"]["type"] == "button_reply":
            button_id = message["content"]["button_id"]

            if button_id == "check":
                context["action"] = "check"
                return ConversationState.CHECKING_CATEGORY
            elif button_id == "report":
                context["action"] = "report"
                return ConversationState.REPORTING_CATEGORY

        return ConversationState.IDLE

    async def get_prompt(self, context: Dict) -> Dict:
        """Get menu prompt."""
        return {
            "type": "buttons",
            "body": "What would you like to do?",
            "buttons": [
                {"id": "check", "title": "Check Item"},
                {"id": "report", "title": "Report Stolen"}
            ]
        }
```

### FastAPI Application

Create `src/presentation/api/app.py`:

```python
"""FastAPI application."""
import logging
from contextlib import asynccontextmanager
from typing import Dict

import redis.asyncio as redis
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.commands.report_stolen_item import (
    ReportStolenItemCommand,
    ReportStolenItemHandler
)
from src.infrastructure.config import settings
from src.infrastructure.persistence.repositories import StolenItemRepository
from src.infrastructure.whatsapp.client import WhatsAppClient
from src.infrastructure.whatsapp.webhook import WebhookHandler
from src.presentation.bot.conversation import ConversationManager
from src.presentation.bot.message_handler import MessageHandler

logger = logging.getLogger(__name__)

# Global instances
whatsapp_client: Optional[WhatsAppClient] = None
webhook_handler: Optional[WebhookHandler] = None
redis_client: Optional[redis.Redis] = None
db_engine = None
SessionLocal = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global whatsapp_client, webhook_handler, redis_client, db_engine, SessionLocal

    # Startup
    logger.info("Starting up...")

    # Initialise WhatsApp
    whatsapp_client = WhatsAppClient(
        settings.whatsapp_access_token,
        settings.whatsapp_phone_number_id
    )

    webhook_handler = WebhookHandler(
        settings.whatsapp_webhook_secret,
        settings.whatsapp_webhook_verify_token
    )

    # Initialise Redis
    redis_client = redis.from_url(settings.redis_url)

    # Initialise database
    db_engine = create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        pool_pre_ping=True
    )

    SessionLocal = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    yield

    # Shutdown
    logger.info("Shutting down...")

    if whatsapp_client:
        await whatsapp_client.close()

    if redis_client:
        await redis_client.close()

    if db_engine:
        await db_engine.dispose()


# Create app
app = FastAPI(
    title="Is It Stolen",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root() -> Dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Is It Stolen Bot"
    }


@app.get("/webhook")
async def verify_webhook(
    request: Request
) -> int:
    """
    Webhook verification endpoint.

    Args:
        request: FastAPI request

    Returns:
        Challenge value
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    result = webhook_handler.verify_challenge(mode, token, challenge)

    if result is not None:
        return result

    raise HTTPException(status_code=403, detail="Invalid verification token")


@app.post("/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict:
    """
    Webhook receiver endpoint.

    Args:
        request: FastAPI request
        background_tasks: Background task manager

    Returns:
        Status response
    """
    # Verify signature
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not webhook_handler.verify_signature(body, signature):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse message
    data = await request.json()
    message = webhook_handler.parse_message(data)

    if message and message.get("type") != "status":
        # Process in background
        background_tasks.add_task(process_message, message)

    return {"status": "received"}


async def process_message(message: Dict) -> None:
    """
    Process incoming message.

    Args:
        message: Parsed message data
    """
    try:
        # Get database session
        async with SessionLocal() as session:
            # Create conversation manager
            conversation_manager = ConversationManager(redis_client)

            # Create message handler
            handler = MessageHandler(
                whatsapp_client,
                conversation_manager,
                session
            )

            # Process message
            await handler.handle_message(message)

    except Exception as e:
        logger.error(f"Error processing message: {e}")

        # Send error message to user
        try:
            await whatsapp_client.send_text(
                message["from"],
                "Sorry, something went wrong. Please type 'start' to begin again."
            )
        except:
            pass
```

## Testing Strategy

### Unit Test Examples

Create `tests/unit/domain/entities/test_stolen_item.py`:

```python
"""Unit tests for StolenItem entity."""
import pytest
from datetime import datetime
from uuid import uuid4

from src.domain.entities.stolen_item import StolenItem
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location


class TestStolenItem:
    """Tests for StolenItem entity."""

    @pytest.fixture
    def valid_location(self):
        """Create valid location."""
        return Location(
            latitude=51.5074,
            longitude=-0.1278,
            address="London, UK"
        )

    def test_creates_valid_item(self, valid_location):
        """Should create valid stolen item."""
        # Act
        item = StolenItem(
            category=ItemCategory.BICYCLE,
            description="Red Trek mountain bike with 21 gears",
            location=valid_location,
            reported_at=datetime.utcnow(),
            reporter_phone="+447123456789"
        )

        # Assert
        assert item.id is not None
        assert item.category == ItemCategory.BICYCLE
        assert not item.is_verified
        assert len(item._events) == 1

    def test_rejects_short_description(self, valid_location):
        """Should reject descriptions under 10 characters."""
        # Act & Assert
        with pytest.raises(ValueError, match="at least 10 characters"):
            StolenItem(
                category=ItemCategory.BICYCLE,
                description="Too short",
                location=valid_location,
                reported_at=datetime.utcnow(),
                reporter_phone="+447123456789"
            )

    def test_vehicle_requires_registration(self, valid_location):
        """Should require registration for vehicles."""
        # Act & Assert
        with pytest.raises(ValueError, match="registration"):
            StolenItem(
                category=ItemCategory.VEHICLE,
                description="Blue Ford Focus 2019 model",
                location=valid_location,
                reported_at=datetime.utcnow(),
                reporter_phone="+447123456789",
                attributes={"model": "Focus"}  # Missing registration
            )

    def test_verify_with_police_report(self, valid_location):
        """Should verify item with police report."""
        # Arrange
        item = StolenItem(
            category=ItemCategory.BICYCLE,
            description="Red Trek mountain bike with 21 gears",
            location=valid_location,
            reported_at=datetime.utcnow(),
            reporter_phone="+447123456789"
        )

        # Act
        item.verify_with_police_report("MET/2024/12345")

        # Assert
        assert item.is_verified
        assert item.police_report_number == "MET/2024/12345"
        assert item.verified_at is not None
        assert len(item._events) == 2

    def test_cannot_verify_twice(self, valid_location):
        """Should not allow verifying already verified item."""
        # Arrange
        item = StolenItem(
            category=ItemCategory.BICYCLE,
            description="Red Trek mountain bike with 21 gears",
            location=valid_location,
            reported_at=datetime.utcnow(),
            reporter_phone="+447123456789"
        )
        item.verify_with_police_report("MET/2024/12345")

        # Act & Assert
        with pytest.raises(ValueError, match="already verified"):
            item.verify_with_police_report("MET/2024/67890")
```

### Integration Test Example

Create `tests/integration/test_repository.py`:

```python
"""Integration tests for repository."""
import pytest
from datetime import datetime, timedelta

from src.domain.entities.stolen_item import StolenItem
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.infrastructure.persistence.repositories import StolenItemRepository


@pytest.mark.integration
class TestStolenItemRepository:
    """Tests for repository."""

    async def test_saves_and_retrieves_item(self, db_session):
        """Should persist and retrieve item."""
        # Arrange
        repo = StolenItemRepository(db_session)
        item = StolenItem(
            category=ItemCategory.BICYCLE,
            description="Blue mountain bike stolen from station",
            location=Location(51.5, -0.1),
            reported_at=datetime.utcnow(),
            reporter_phone="+447123456789"
        )

        # Act
        await repo.save(item)
        retrieved = await repo.find_by_id(item.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == item.id
        assert retrieved.description == item.description

    async def test_finds_items_within_radius(self, db_session):
        """Should find items within radius."""
        # Arrange
        repo = StolenItemRepository(db_session)

        # Create items at different locations
        london_item = StolenItem(
            category=ItemCategory.ELECTRONICS,
            description="iPhone stolen in Central London",
            location=Location(51.5074, -0.1278),
            reported_at=datetime.utcnow(),
            reporter_phone="+447123456789"
        )

        paris_item = StolenItem(
            category=ItemCategory.ELECTRONICS,
            description="iPhone stolen in Paris",
            location=Location(48.8566, 2.3522),
            reported_at=datetime.utcnow(),
            reporter_phone="+33123456789"
        )

        await repo.save(london_item)
        await repo.save(paris_item)

        # Act - Search near London
        search_location = Location(51.5, -0.12)
        results = await repo.find_within_radius(search_location, 50)

        # Assert
        assert len(results) == 1
        assert results[0].id == london_item.id
```

### End-to-End Test Example

Create `tests/e2e/test_conversation_flow.py`:

```python
"""End-to-end tests for conversation flow."""
import pytest
from httpx import AsyncClient

from src.presentation.api.app import app


@pytest.mark.e2e
class TestConversationFlow:
    """Tests for complete conversation flow."""

    async def test_report_stolen_item_flow(self):
        """Should handle complete reporting flow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Simulate initial message
            webhook_data = self._create_webhook_payload(
                message_type="text",
                text="Hello"
            )

            response = await client.post(
                "/webhook",
                json=webhook_data,
                headers=self._get_webhook_headers(webhook_data)
            )

            assert response.status_code == 200

            # Continue with button selection
            webhook_data = self._create_webhook_payload(
                message_type="interactive",
                button_id="report"
            )

            response = await client.post(
                "/webhook",
                json=webhook_data,
                headers=self._get_webhook_headers(webhook_data)
            )

            assert response.status_code == 200

    def _create_webhook_payload(self, **kwargs):
        """Create webhook payload for testing."""
        # Implementation here
        pass

    def _get_webhook_headers(self, payload):
        """Get webhook headers with signature."""
        # Implementation here
        pass
```

## Deployment Guide

### Docker Setup

Create `Dockerfile`:

```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Copy Python packages
COPY --from=builder /root/.local /root/.local

# Copy application
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "src.presentation.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:

```yaml
version: "3.8"

services:
  postgres:
    image: postgis/postgis:15-3.3
    environment:
      POSTGRES_DB: is_it_stolen
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://admin:secure_password@postgres:5432/is_it_stolen
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    env_file:
      - .env

volumes:
  postgres_data:
  redis_data:
```

## Using the Makefile

The Makefile provides convenient commands for all common development tasks. Run `make help` to see all available commands.

### Daily Development Workflow with WhatsApp

```bash
# Morning: Update and check environment
make dev-setup          # Install deps and setup hooks
git pull origin main    # Get latest changes

# Start development services
make docker-up          # Start PostgreSQL and Redis
make migrate-up         # Apply any new migrations

# Start application and ngrok
# Terminal 1:
make run                # Start FastAPI on port 8000

# Terminal 2:
make ngrok              # Start ngrok tunnel
# Copy the HTTPS URL (e.g., https://bison-outgoing-amazingly.ngrok-free.app)
# Update WhatsApp webhook URL in Meta Developer Console

# Terminal 3: Development cycle
make test-unit          # Write failing test (TDD)
# ... write code ...
make test-unit          # Verify test passes
make lint-fix           # Fix linting issues
make format             # Format code
make type-check         # Check types

# Monitor webhooks
# Browser: http://127.0.0.1:4040  # Ngrok inspector

# Run full check before committing
make check              # Runs lint, type-check, and all tests

# End of day
make docker-down        # Stop services
# Ctrl+C in ngrok terminal
```

### WhatsApp Development Commands

```bash
# Complete dev environment with ngrok
make dev                # Starts everything including ngrok

# Webhook testing
make webhook-test       # Test webhook endpoint locally

# Ngrok management
make ngrok              # Start ngrok tunnel
make ngrok-setup        # Configure ngrok authtoken

# Monitor logs
make docker-logs        # View all Docker logs
docker logs -f is_it_stolen_app  # Follow app logs only
```

### Common Commands

```bash
# Testing
make test               # Run all tests
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-cov           # Generate coverage report

# Code Quality
make lint               # Check linting
make lint-fix           # Auto-fix linting issues
make format             # Format code with Ruff
make type-check         # Run MyPy
make check              # Run all checks

# Database
make migrate-create message="add user table"  # Create migration
make migrate-up         # Apply migrations
make migrate-down       # Rollback last migration
make db-shell           # Open PostgreSQL shell

# Docker
make docker-up          # Start all services
make docker-down        # Stop all services
make docker-logs        # View logs
make docker-clean       # Clean up resources

# Development
make shell              # IPython with app context
make run                # Run app with reload
make run-prod           # Run in production mode
```

### Creating New Features

```bash
# 1. Create feature branch
make feature name=stolen-item-matching

# 2. Write failing test first (TDD)
# Create tests/unit/domain/services/test_matching_service.py
make test-unit  # Verify test fails

# 3. Implement feature
# Create src/domain/services/matching_service.py
make test-unit  # Verify test passes

# 4. Check code quality
make check

# 5. Commit with conventional message
git add -A
git commit -m "feat: add matching service for stolen items"

# 6. Push and create PR
make pr
```

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

Create initial migration:

```bash
alembic init alembic
alembic revision -m "Initial schema"
alembic upgrade head
```

## Versioning and Release Strategy

### Semantic Versioning

We follow [Semantic Versioning](https://semver.org/) (SemVer):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

Pre-release versions:

- **Alpha**: `v0.1.0-alpha.1` (early development)
- **Beta**: `v0.1.0-beta.1` (feature complete, testing)
- **Release Candidate**: `v0.1.0-rc.1` (production ready)

### Version Management with Poetry

```bash
# Check current version
poetry version

# Bump versions
poetry version patch    # 0.1.0 -> 0.1.1
poetry version minor    # 0.1.1 -> 0.2.0
poetry version major    # 0.2.0 -> 1.0.0

# Pre-release versions
poetry version prepatch   # 0.1.0 -> 0.1.1-alpha.0
poetry version prerelease  # 0.1.1-alpha.0 -> 0.1.1-alpha.1
poetry version 0.1.0-beta.1  # Set specific version
```

Update `pyproject.toml` to track version:

```toml
[tool.poetry]
name = "is-it-stolen"
version = "0.1.0"  # Single source of truth for version
# ... rest of config
```

### Git Tags and Releases

#### Tagging Convention

```bash
# Create annotated tag
git tag -a v0.1.0 -m "Release version 0.1.0"

# Tag with release notes
git tag -a v0.1.0 -m "Release version 0.1.0

Features:
- Location value object (#1)
- ItemCategory enumeration (#2)
- StolenItem entity (#3)

Bug Fixes:
- Fixed coordinate validation (#15)

Breaking Changes:
- None"

# Push tag to GitHub
git push origin v0.1.0

# Push all tags
git push --tags

# List tags
git tag -l

# Delete local tag
git tag -d v0.1.0

# Delete remote tag
git push origin --delete v0.1.0
```

#### Release Process

1. **Update version**:

   ```bash
   # On main branch with all changes merged
   git checkout main
   git pull origin main

   # Bump version
   poetry version minor  # or major/patch
   NEW_VERSION=$(poetry version -s)

   # Update changelog
   echo "## v${NEW_VERSION} - $(date +%Y-%m-%d)" >> CHANGELOG.md
   # Add release notes to CHANGELOG.md
   ```

2. **Commit version bump**:

   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: release v${NEW_VERSION}"
   git push origin main
   ```

3. **Create and push tag**:

   ```bash
   git tag -a v${NEW_VERSION} -m "Release v${NEW_VERSION}"
   git push origin v${NEW_VERSION}
   ```

4. **GitHub will automatically create release via Actions**

### Changelog Management

Create `CHANGELOG.md`:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Feature currently in development

## [0.2.0] - 2024-01-15

### Added

- WhatsApp client implementation (#4)
- Report stolen item command (#5)
- Location-based search (#6)

### Changed

- Improved distance calculation accuracy (#12)

### Fixed

- Coordinate validation edge cases (#15)

### Security

- Updated dependencies to patch vulnerabilities

## [0.1.0] - 2024-01-01

### Added

- Initial release
- Location value object (#1)
- ItemCategory enumeration (#2)
- StolenItem entity (#3)

[Unreleased]: https://github.com/barry47products/is-it-stolen/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/barry47products/is-it-stolen/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/barry47products/is-it-stolen/releases/tag/v0.1.0
```

### GitHub Actions for Releases

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - "v*" # Trigger on version tags

permissions:
  contents: write
  packages: write

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: latest

      - name: Install dependencies
        run: poetry install

      - name: Run tests
        run: poetry run pytest

      - name: Run type checking
        run: poetry run mypy src

      - name: Run linting
        run: poetry run ruff check src tests

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install Poetry
        uses: snok/install-poetry@v1

      - name: Build package
        run: poetry build

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/

  docker:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=tag
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=sha,prefix={{version}}-

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  release:
    needs: [test, build, docker]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Full history for changelog

      - name: Download artifacts
        uses: actions/download-artifact@v3
        with:
          name: dist
          path: dist/

      - name: Extract release notes
        id: release_notes
        run: |
          # Extract section for this version from CHANGELOG.md
          VERSION=${GITHUB_REF#refs/tags/}
          sed -n "/## \[${VERSION#v}\]/,/## \[/p" CHANGELOG.md | sed '$d' > release_notes.md

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          body_path: release_notes.md
          files: |
            dist/*
          draft: false
          prerelease: ${{ contains(github.ref, 'alpha') || contains(github.ref, 'beta') || contains(github.ref, 'rc') }}
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  deploy:
    needs: release
    runs-on: ubuntu-latest
    if: ${{ !contains(github.ref, 'alpha') && !contains(github.ref, 'beta') && !contains(github.ref, 'rc') }}
    steps:
      - name: Deploy to production
        run: |
          echo "Deploying version ${GITHUB_REF#refs/tags/} to production"
          # Add deployment steps here
```

### Makefile Updates for Releases

Add to `Makefile`:

```makefile
# Versioning commands
version: ## Show current version
    @poetry version

version-patch: ## Bump patch version (0.1.0 -> 0.1.1)
    poetry version patch
    @echo "New version: $(poetry version -s)"

version-minor: ## Bump minor version (0.1.0 -> 0.2.0)
    poetry version minor
    @echo "New version: $(poetry version -s)"

version-major: ## Bump major version (0.1.0 -> 1.0.0)
    poetry version major
    @echo "New version: $(poetry version -s)"

version-prerelease: ## Create prerelease version
    poetry version prerelease
    @echo "New version: $(poetry version -s)"

changelog: ## Open changelog for editing
    ${EDITOR:-vim} CHANGELOG.md

release-patch: ## Create a patch release
    @./scripts/release.sh patch

release-minor: ## Create a minor release
    @./scripts/release.sh minor

release-major: ## Create a major release
    @./scripts/release.sh major

release-alpha: ## Create an alpha release
    @./scripts/release.sh alpha

release-beta: ## Create a beta release
    @./scripts/release.sh beta

release-rc: ## Create a release candidate
    @./scripts/release.sh rc

tag-list: ## List all tags
    git tag -l --sort=-v:refname

tag-latest: ## Show latest tag
    git describe --tags --abbrev=0

release-notes: ## Generate release notes for unreleased changes
    @echo "## Unreleased Changes"
    @echo ""
    @echo "### Features"
    @git log $(git describe --tags --abbrev=0)..HEAD --grep="^feat:" --pretty=format:"- %s"
    @echo ""
    @echo "### Fixes"
    @git log $(git describe --tags --abbrev=0)..HEAD --grep="^fix:" --pretty=format:"- %s"
    @echo ""
    @echo "### Other"
    @git log $(git describe --tags --abbrev=0)..HEAD --grep -v "^feat:\|^fix:" --pretty=format:"- %s"
```

### Release Script

Create `scripts/release.sh`:

```bash
#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if release type is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Release type required${NC}"
    echo "Usage: $0 [major|minor|patch|alpha|beta|rc]"
    exit 1
fi

RELEASE_TYPE=$1

# Ensure we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${YELLOW}Warning: Not on main branch${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Pull latest changes
echo -e "${GREEN}Pulling latest changes...${NC}"
git pull origin main

# Run tests
echo -e "${GREEN}Running tests...${NC}"
make check

# Bump version based on type
echo -e "${GREEN}Bumping version...${NC}"
case $RELEASE_TYPE in
    major|minor|patch)
        poetry version $RELEASE_TYPE
        ;;
    alpha)
        poetry version prerelease
        NEW_VERSION=$(poetry version -s)
        poetry version "${NEW_VERSION%-*}-alpha.${NEW_VERSION##*-alpha.}"
        ;;
    beta)
        poetry version prerelease
        NEW_VERSION=$(poetry version -s)
        poetry version "${NEW_VERSION%-*}-beta.${NEW_VERSION##*-beta.}"
        ;;
    rc)
        poetry version prerelease
        NEW_VERSION=$(poetry version -s)
        poetry version "${NEW_VERSION%-*}-rc.${NEW_VERSION##*-rc.}"
        ;;
    *)
        echo -e "${RED}Invalid release type: $RELEASE_TYPE${NC}"
        exit 1
        ;;
esac

NEW_VERSION=$(poetry version -s)
echo -e "${GREEN}New version: $NEW_VERSION${NC}"

# Update changelog
echo -e "${YELLOW}Please update CHANGELOG.md with release notes${NC}"
echo -e "${YELLOW}Opening editor...${NC}"
${EDITOR:-vim} CHANGELOG.md

# Commit changes
echo -e "${GREEN}Committing version bump...${NC}"
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v${NEW_VERSION}

Release type: ${RELEASE_TYPE}"

# Create tag
echo -e "${GREEN}Creating tag v${NEW_VERSION}...${NC}"
git tag -a "v${NEW_VERSION}" -m "Release v${NEW_VERSION}

See CHANGELOG.md for details"

# Push changes and tag
echo -e "${GREEN}Pushing to GitHub...${NC}"
git push origin main
git push origin "v${NEW_VERSION}"

echo -e "${GREEN}✨ Release v${NEW_VERSION} created successfully!${NC}"
echo "GitHub Actions will now:"
echo "  1. Run tests"
echo "  2. Build Docker image"
echo "  3. Create GitHub release"
echo "  4. Deploy (if not a pre-release)"
echo ""
echo "Monitor progress at: https://github.com/barry47products/is-it-stolen/actions"
```

Make it executable:

```bash
chmod +x scripts/release.sh
```

### Release Milestones

Link releases to issue milestones:

#### v0.1.0-alpha.1 (Milestone 1 Complete)

- Core domain layer (Issues #1-10)
- Basic value objects and entities
- Domain services

#### v0.2.0-beta.1 (Milestone 2-3 Complete)

- Infrastructure layer (Issues #11-20)
- Application layer (Issues #21-30)
- Database and WhatsApp integration

#### v0.3.0-rc.1 (Milestone 4 Complete)

- Bot presentation layer (Issues #31-40)
- Full conversation flow
- End-to-end testing

#### v1.0.0 (Milestone 5 Complete)

- Production ready (Issues #41-50)
- Monitoring and logging
- Documentation complete
- Deployed to production

### Version Badge for README

Add to `README.md`:

````markdown
# Is It Stolen

[![GitHub release](https://img.shields.io/github/release/barry47products/is-it-stolen.svg)](https://github.com/barry47products/is-it-stolen/releases)
[![GitHub tag](https://img.shields.io/github/tag/barry47products/is-it-stolen.svg)](https://github.com/barry47products/is-it-stolen/tags)
[![CI](https://github.com/barry47products/is-it-stolen/actions/workflows/ci.yml/badge.svg)](https://github.com/barry47products/is-it-stolen/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/barry47products/is-it-stolen/branch/main/graph/badge.svg)](https://codecov.io/gh/barry47products/is-it-stolen)

WhatsApp bot for checking and reporting stolen items.

## Current Version

v0.1.0-alpha.1 - Core domain implementation

## Installation

    ```bash
    # Latest stable release
    docker pull ghcr.io/barry47products/is-it-stolen:latest

    # Specific version
    docker pull ghcr.io/barry47products/is-it-stolen:0.1.0
    ```

### Branch Strategy

We use **issue-driven trunk-based development**:

- Every feature/bug/task starts with a GitHub issue
- Branch names include issue number: `feat/1-location-value-object`
- All commits reference the issue
- PRs automatically close issues when merged
- Deploy directly from `main`

### Development Workflow

```bash
# 1. Create or pick an issue from GitHub
# https://github.com/barry47products/is-it-stolen/issues

# 2. Create branch for issue
make issue number=5 name=whatsapp-client
# Creates: feat/5-whatsapp-client

# 3. Develop with TDD
make test-unit  # Write failing test
# Implement feature
make test-unit  # Make test pass

# 4. Make small commits referencing issue
git add src/infrastructure/whatsapp/client.py
git commit -m "feat: implement WhatsApp message sending

Adds send_text and send_interactive_buttons methods
with retry logic using tenacity.

Part of #5"

git add tests/unit/infrastructure/whatsapp/test_client.py
git commit -m "test: add WhatsApp client unit tests

Covers all message types and retry scenarios.

Part of #5"

# 5. Final commit closes the issue
git commit -m "docs: add WhatsApp client documentation

Completes WhatsApp client implementation.

Closes #5"

# 6. Push and create PR
make pr-issue number=5

# 7. After PR approval and merge
git checkout main
git pull origin main
git branch -d feat/5-whatsapp-client
```
````

### Commit Guidelines with Issues

Follow conventional commits with issue references:

```bash
# Feature - part of issue
git commit -m "feat: add location validation

Implements coordinate boundary checking.

Part of #1"

# Feature - closes issue
git commit -m "feat: complete Location value object

Adds final distance calculation method.

Closes #1"

# Bug fix
git commit -m "fix: correct latitude validation

Was allowing latitude values > 90.

Fixes #23"

# Multiple issues
git commit -m "feat: add comprehensive logging

Implements structured logging across all modules.

Part of #10
Part of #11
Closes #12"
```

### Pull Request Process with Issues

1. **PR Title Format**:

   - `feat: Location value object (#1)`
   - `fix: WhatsApp retry logic (#23)`
   - `docs: API documentation (#15)`

2. **PR Description Must Include**:

   - `Closes #[issue-number]` to auto-close issue
   - Summary of implementation
   - Testing approach
   - Any deviations from issue requirements

3. **Example PR**:

```markdown
## Description

Implements Location value object with coordinate validation and distance calculation.

## Related Issue

Closes #1

## Implementation Details

- Used frozen dataclass for immutability
- Haversine formula for distance calculation
- Comprehensive validation with clear error messages

## Testing

- Unit tests with 100% coverage
- Property-based tests for coordinate validation
- Distance calculation verified against known values

## Checklist

- [x] Tests pass
- [x] Type hints complete
- [x] No magic values
- [x] Functions < 10 lines
```

### Issue Lifecycle

```mermaid
graph LR
    A[Create Issue] --> B[Assign & Label]
    B --> C[Create Branch]
    C --> D[Develop with TDD]
    D --> E[Create PR]
    E --> F[Code Review]
    F --> G[Merge to Main]
    G --> H[Auto-close Issue]
    H --> I[Delete Branch]
```

### Example Issues Roadmap

#### Phase 1: Domain Layer (Issues #1-10)

```markdown
#1 - Location value object
#2 - ItemCategory enumeration
#3 - StolenItem entity
#4 - Domain events
#5 - Matching service
#6 - Verification service
#7 - Phone number value object
#8 - Item attributes value object
#9 - Domain exceptions
#10 - Domain layer integration tests
```

#### Phase 2: Infrastructure Layer (Issues #11-20)

```markdown
#11 - Database models with SQLAlchemy
#12 - Repository implementation
#13 - WhatsApp client
#14 - Webhook handler
#15 - Redis cache service
#16 - Event publisher
#17 - Media storage service
#18 - Database migrations
#19 - Configuration management
#20 - Infrastructure integration tests
```

#### Phase 3: Application Layer (Issues #21-30)

```markdown
#21 - Report stolen item command
#22 - Check if stolen query
#23 - Get nearby items query
#24 - Verify item command
#25 - Delete item command
#26 - Update item command
#27 - Notification service
#28 - Search service
#29 - Export service
#30 - Application layer tests
```

#### Phase 4: Presentation Layer (Issues #31-40)

```markdown
#31 - FastAPI application setup
#32 - Webhook endpoint
#33 - Conversation state machine
#34 - Message parser
#35 - Response builder
#36 - Error handling
#37 - Rate limiting
#38 - Health check endpoint
#39 - Metrics endpoint
#40 - End-to-end tests
```

### GitHub Actions for Issues

Update `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]

jobs:
  validate-issue-link:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - name: Check issue reference
        uses: actions/github-script@v6
        with:
          script: |
            const pr = context.payload.pull_request;
            const body = pr.body || '';
            const title = pr.title || '';

            // Check for issue reference
            const issuePattern = /(Closes|Fixes|Resolves) #\d+/i;
            if (!issuePattern.test(body)) {
              core.setFailed('PR must reference an issue with "Closes #XX"');
            }

            // Check title format
            const titlePattern = /^(feat|fix|docs|style|refactor|test|chore|perf|ci):.+\(#\d+\)$/;
            if (!titlePattern.test(title)) {
              core.warning('PR title should follow format: "type: description (#issue)"');
            }

  test:
    needs: validate-issue-link
    runs-on: ubuntu-latest
    # ... rest of CI workflow
```

### Useful GitHub Issue Queries

```bash
# Open issues assigned to you
https://github.com/barry47products/is-it-stolen/issues/assigned/@me

# Issues ready to work on (labelled)
https://github.com/barry47products/is-it-stolen/issues?q=is:open+label:ready

# Issues in current milestone
https://github.com/barry47products/is-it-stolen/issues?q=is:open+milestone:"Phase+1"

# Recently closed issues
https://github.com/barry47products/is-it-stolen/issues?q=is:closed+sort:updated-desc
```

## Monitoring and Observability

### Logging Setup

Create `src/infrastructure/logging.py`:

```python
"""Logging configuration."""
import logging
import sys
from typing import Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from src.infrastructure.config import Environment, settings


def setup_logging() -> None:
    """Configure application logging."""
    log_level = (
        logging.DEBUG
        if settings.environment == Environment.DEVELOPMENT
        else logging.INFO
    )

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Suppress noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def setup_sentry() -> None:
    """Configure Sentry error tracking."""
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment.value,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration()
            ],
            traces_sample_rate=0.1 if settings.environment == Environment.PRODUCTION else 1.0
        )
```

## Troubleshooting Guide

### Common Issues

#### Poetry Issues

1. **Poetry not found**

   ```bash
   # Install Poetry
   curl -sSL https://install.python-poetry.org | python3 -
   # Add to PATH
   export PATH="$HOME/.local/bin:$PATH"
   ```

2. **Dependency conflicts**

   ```bash
   # Clear cache and reinstall
   poetry cache clear --all pypi
   poetry lock --no-update
   poetry install
   ```

3. **Virtual environment issues**

   ```bash
   # Remove and recreate environment
   poetry env remove python3.11
   poetry install
   ```

#### Development Issues

1. **Ruff and MyPy conflicts**

   ```bash
   # Ensure configs don't overlap
   make lint-fix  # Fix with Ruff first
   make format    # Format code
   make type-check  # Then check types
   ```

2. **Pre-commit hook failures**

   ```bash
   # Update hooks
   pre-commit autoupdate
   pre-commit run --all-files
   ```

3. **Database connection issues**

   ```bash
   # Check PostgreSQL is running
   make docker-up
   # Check PostGIS extension
   make db-shell
   # In PostgreSQL: CREATE EXTENSION IF NOT EXISTS postgis;
   ```

4. **WhatsApp webhook verification failing**

   - Verify HTTPS endpoint is accessible
   - Check SSL certificate is valid
   - Ensure verify token matches exactly
   - Check webhook URL format: `https://yourdomain.com/webhook`

5. **Redis connection issues**

   ```bash
   # Check Redis is running
   docker ps | grep redis
   # Test connection
   make redis-cli
   # In Redis CLI: PING
   ```

6. **Test failures**

   ```bash
   # Run specific test with verbose output
   poetry run pytest tests/unit/test_file.py -vvs
   # Check test database
   poetry run pytest --create-db
   ```

7. **Type checking errors**

   ```bash
   # Clear MyPy cache
   rm -rf .mypy_cache
   # Run with verbose output
   poetry run mypy src --show-error-codes
   ```

8. **Import errors**

   ```bash
   # Ensure PYTHONPATH is set
   export PYTHONPATH=/path/to/project:$PYTHONPATH
   # Or use Poetry shell
   poetry shell
   ```

### Performance Issues

1. **Slow tests**

   ```bash
   # Run tests in parallel
   poetry add --group dev pytest-xdist
   poetry run pytest -n auto
   ```

2. **Slow Docker builds**

   ```bash
   # Use BuildKit
   DOCKER_BUILDKIT=1 docker build -t is-it-stolen .
   # Or enable permanently
   export DOCKER_BUILDKIT=1
   ```

3. **Database query performance**

   ```sql
   -- Check slow queries
   SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
   -- Add indexes where needed
   CREATE INDEX idx_stolen_items_location ON stolen_items USING GIST (location);
   ```

## Next Steps

1. **Implement ML Matching**

   - Add sentence embeddings
   - Use vector similarity search
   - Train on real data

2. **Add Image Recognition**

   - Integrate computer vision API
   - Extract features from images
   - Match visual signatures

3. **Scale Infrastructure**

   - Add message queue (Celery)
   - Implement caching layer
   - Add load balancing

4. **Enhance Security**
   - Add rate limiting
   - Implement authentication
   - Encrypt sensitive data

## Summary

This guide provides a complete implementation of the **Is It Stolen** WhatsApp bot.

**Repository**: `https://github.com/barry47products/is-it-stolen`

### Architecture & Design

- **Issue-Driven Development**: Every feature starts with a GitHub issue
- **Domain-Driven Design**: Pure domain layer with no external dependencies
- **Test-Driven Development**: Write tests first, then implementation
- **Clean Code Principles**: Small functions, clear naming, no magic values
- **Type Safety**: Full type annotations with MyPy
- **Hexagonal Architecture**: Clear separation between domain, application, and infrastructure

### Development Workflow

- **Trunk-Based Development**: Short-lived feature branches merged to main via PRs
- **Issue Tracking**: GitHub issues for all work items
- **Conventional Commits**: Structured messages linked to issues
- **Code Review Process**: PRs for all changes (can use Claude for reviews)
- **Small, Focused Commits**: One logical change per commit linked to an issue
- **Ngrok Integration**: HTTPS tunnels for WhatsApp webhook development

### Tooling

- **Poetry**: Modern dependency management and packaging
- **Ruff**: Fast, comprehensive linting and formatting (replaces Black, isort, flake8)
- **MyPy**: Static type checking
- **Pytest**: Testing with coverage reporting
- **Make**: Convenient commands for all tasks
- **Pre-commit**: Automated code quality checks
- **Ngrok**: Secure tunnels for webhook development
- **Docker**: Containerised PostgreSQL, Redis, and application

### Getting Started

```bash
# Clone repository
git clone https://github.com/barry47products/is-it-stolen.git
cd is-it-stolen

# Setup environment
make dev-setup

# Pick an issue from GitHub
# https://github.com/barry47products/is-it-stolen/issues

# Start working
make issue number=1 name=location-value-object

# Develop with TDD
make test-unit  # Write failing test
# Implement...
make test-unit  # Make it pass
make check      # Verify quality

# Create PR with issue link
make pr-issue number=1
```

### Implementation Path

1. **Week 1**: Core Domain Layer (Issues #1-10)
2. **Week 2**: Infrastructure Layer (Issues #11-20)
3. **Week 3**: Application Layer (Issues #21-30)
4. **Week 4**: Bot Presentation Layer (Issues #31-40)
5. **Week 5**: Production Ready (Issues #41-50)

Each issue represents a complete, testable feature that can be developed independently and verified through automated tests.

---

## Implementation Progress

### ✅ Issue #31 - FastAPI Application Structure (COMPLETE)

**PR**: `https://github.com/barry47products/is-it-stolen/pull/85`
**Completed**: 2025-10-03

#### What Was Implemented

**FastAPI Application Structure:**

- Application factory pattern with `create_app()`
- Async lifespan management for startup/shutdown events
- Structured logging configured throughout
- CORS middleware for cross-origin requests
- Versioned API routing (`/v1/...`)
- Environment-based docs configuration (disabled in production)
- Health check endpoints (root `/health` and versioned `/v1/health`)

**Dependency Injection:**

- Singleton service providers (event bus, matching service, verification service)
- Repository factory with async generators
- Ready for FastAPI `Depends()` injection in route handlers

**Pure ASGI Middleware (20-30% Performance Boost):**

- `RequestIDMiddleware` - Adds unique `X-Request-ID` to every request
- `LoggingMiddleware` - Logs requests/responses with timing information
- Direct ASGI implementation (no BaseHTTPMiddleware overhead)
- Proper `scope`, `receive`, `send` handling at protocol level

#### Key Technical Decisions

**ASGI vs BaseHTTPMiddleware:**
Migrated to pure ASGI middleware for better performance and control. Pure ASGI middleware works at the protocol level (`scope`, `receive`, `send`) instead of wrapping Request/Response objects, providing:

- 20-30% faster request processing
- Better WebSocket support
- HTTP/2 readiness
- More granular control over request/response cycle

**Module-Level Keyword Loading:**
Category keywords are loaded at module level (before app creation) to ensure proper test isolation and avoid issues with lifespan events in TestClient.

**Type Safety:**
Full type annotations with MyPy strict mode. Used targeted `# type: ignore[no-any-unimported]` for ASGI type imports where MyPy's `disallow_any_unimported` setting conflicts with Starlette's type definitions.

#### Test Coverage

- ✅ All 451 tests passing
- ✅ 100% coverage on `src/presentation/api/` (app.py, middleware.py, dependencies.py)
- ✅ Pre-commit hooks passing (Ruff, MyPy, formatting)
- ✅ Application lifecycle tests (startup/shutdown)
- ✅ API structure tests (versioning, endpoints)
- ✅ Middleware tests (request IDs, logging, uniqueness)
- ✅ Dependency injection tests (singletons, repository generators)

#### Files Created/Modified

**New Files:**

- `src/presentation/api/middleware.py` - Pure ASGI middleware classes
- `src/presentation/api/dependencies.py` - Dependency injection providers
- `src/presentation/api/v1/__init__.py` - Versioned API router
- `tests/unit/presentation/test_api_structure.py` - API structure tests
- `tests/unit/presentation/test_app_lifecycle.py` - Lifecycle tests
- `tests/unit/presentation/test_dependencies.py` - DI tests

**Modified Files:**

- `src/presentation/api/app.py` - Enhanced with factory pattern, lifespan, middleware
- `tests/unit/presentation/test_health.py` - Updated for version in response
- `pyproject.toml` - Updated MyPy configuration

#### Next Steps (Issue #31)

Issue #32 - Implement WhatsApp webhook endpoint for receiving messages.

---

### ✅ Issue #32 - WhatsApp Webhook Endpoint (COMPLETE)

**PR**: `https://github.com/barry47products/is-it-stolen/pull/86`
**Completed**: 2025-10-05

#### Implementation Summary (Issue #32)

**Webhook Verification (GET /v1/webhook):**

- Handles WhatsApp verification challenge during setup
- Validates `hub.mode`, `hub.verify_token`, and `hub.challenge` parameters
- Returns challenge string when verification succeeds
- Returns 403 for invalid mode or token

**Message Reception (POST /v1/webhook):**

- Receives WhatsApp message events
- Verifies HMAC SHA256 signature using `X-Hub-Signature-256` header
- Parses webhook payload to extract messages
- Returns immediate 200 response (idempotent)
- Ready for message queueing (to be implemented in #33)

**Signature Verification:**

- Implements HMAC SHA256 verification
- Uses timing-safe comparison to prevent timing attacks
- Validates against WhatsApp app secret
- Rejects requests with invalid signatures (403)

#### Technical Approach (Issue #32)

**Webhook Handler Integration:**
Leveraged existing `WebhookHandler` from infrastructure layer and `verify_webhook_signature()` function. The presentation layer provides thin FastAPI endpoints that delegate to the well-tested infrastructure components.

**Test Infrastructure:**
Set WhatsApp test credentials in `conftest.py` at module level (before app import) to ensure settings singleton is initialized with test values. Discovered that TestClient serializes JSON in compact format (no spaces), requiring signature calculation to match.

**Type Safety:**
Full type annotations with targeted `# type: ignore[no-any-unimported]` for FastAPI imports where MyPy's `disallow_any_unimported` setting conflicts with FastAPI's type definitions.

**Idempotent Design:**
Webhook endpoint returns 200 immediately after parsing messages. Actual message processing will be queued asynchronously (Issue #33) to prevent webhook timeouts and allow for retries.

#### Test Results (Issue #32)

- ✅ All 462 tests passing (9 new webhook tests)
- ✅ 100% coverage on `src/presentation/api/v1/webhook.py`
- ✅ Pre-commit hooks passing (Ruff, MyPy, formatting)
- ✅ Verification tests (successful, invalid mode, invalid token)
- ✅ Message tests (valid signature, invalid signature, empty payload, multiple messages, media messages, missing header)

#### Changes Made (Issue #32)

**New Files:**

- `src/presentation/api/v1/webhook.py` - Webhook endpoints (GET/POST)
- `tests/unit/presentation/test_webhook.py` - Comprehensive webhook tests (9 tests)

**Modified Files:**

- `src/presentation/api/v1/__init__.py` - Include webhook router
- `tests/conftest.py` - Add WhatsApp test credentials at module level

#### Infrastructure Integration (Issue #32)

The webhook endpoints integrate seamlessly with:

- `WebhookHandler` (src/infrastructure/whatsapp/webhook_handler.py) - Message parsing
- `verify_webhook_signature()` - HMAC SHA256 verification
- Settings (src/infrastructure/config/settings.py) - Verify token and app secret

This demonstrates the clean separation between presentation (FastAPI endpoints) and infrastructure (WhatsApp-specific logic).

#### Next Steps (Issue #32)

Issue #33 will implement the conversation state machine to process the queued messages.

---

### ✅ Issue #33 - Conversation State Machine (COMPLETE)

**PR**: `https://github.com/barry47products/is-it-stolen/pull/87`
**Completed**: 2025-10-05

#### Implementation Summary (Issue #33)

**State Management:**

- 9 conversation states: IDLE, MAIN_MENU, CHECKING_CATEGORY, CHECKING_DESCRIPTION, CHECKING_LOCATION, REPORTING_CATEGORY, REPORTING_DESCRIPTION, REPORTING_LOCATION, COMPLETE, CANCELLED
- STATE_TRANSITIONS dictionary mapping valid state transitions
- is_valid_transition() function for validation
- Terminal states (COMPLETE, CANCELLED) prevent further transitions

**Immutable Context:**

- ConversationContext dataclass with frozen=True
- Fields: phone_number, state, data, created_at, updated_at
- with_state() and with_data() return new instances
- to_dict() and from_dict() for Redis serialization
- is_active() checks if not in terminal state

**Redis Storage:**

- ConversationStorage Protocol for interface
- RedisConversationStorage implementation
- Key format: conversation:{phone_number}
- TTL support: 3600 seconds (1 hour) default
- JSON serialization for persistence

**State Machine Operations:**

- get_or_create() - retrieve existing or create new context
- transition() - validate transition and save
- update_data() - merge data and save
- cancel() - transition to CANCELLED and cleanup
- complete() - transition to COMPLETE and cleanup
- reset() - delete context from storage

#### Technical Approach (Issue #33)

**Test-Driven Development:**
Implemented following strict TDD - wrote failing tests first, then implementation. Created 45 tests (41 unit + 4 integration) before any production code. Achieved 100% coverage on all bot modules.

**Immutability Pattern:**
Used frozen dataclass pattern for ConversationContext to prevent accidental mutation. All state changes return new instances with updated timestamps.

**Protocol Pattern:**
Defined ConversationStorage as Protocol for structural subtyping, enabling easy mocking in tests while maintaining type safety.

**Fast Integration Tests:**
Optimized TTL test to verify Redis expiry is set correctly without waiting 2 seconds. Uses redis.ttl() command to check TTL value instead of sleep().

**Type Safety:**
Full type annotations with targeted # type: ignore comments for Redis library issues. All bot code passes MyPy strict mode.

#### Test Results (Issue #33)

- ✅ All 507 tests passing (45 new bot tests)
- ✅ 100% coverage on src/presentation/bot/context.py
- ✅ 100% coverage on src/presentation/bot/exceptions.py
- ✅ 100% coverage on src/presentation/bot/state_machine.py
- ✅ 100% coverage on src/presentation/bot/states.py
- ✅ 100% coverage on src/presentation/bot/storage.py
- ✅ Pre-commit hooks passing (Ruff, MyPy, formatting)
- ✅ Protocol pragma comments for coverage
- ✅ Fast integration tests (no 2s sleep)

#### Changes Made (Issue #33)

**New Files:**

- `src/presentation/bot/__init__.py` - Package initialization
- `src/presentation/bot/states.py` - State definitions and transitions
- `src/presentation/bot/context.py` - Immutable conversation context
- `src/presentation/bot/exceptions.py` - Custom exceptions (InvalidStateTransitionError)
- `src/presentation/bot/storage.py` - Redis storage with Protocol
- `src/presentation/bot/state_machine.py` - State machine orchestration
- `tests/unit/presentation/bot/test_states.py` - State/transition tests (13 tests)
- `tests/unit/presentation/bot/test_context.py` - Context immutability tests (12 tests)
- `tests/unit/presentation/bot/test_storage.py` - Redis storage tests (8 tests)
- `tests/unit/presentation/bot/test_state_machine.py` - State machine tests (8 tests)
- `tests/integration/presentation/bot/test_conversation_integration.py` - Integration tests (4 tests)
- `docs/conversation-state-machine.md` - State diagram with Mermaid visualization

**Modified Files:**

- pyproject.toml - Added Ruff exclusion for docs/ and *.md files
- docs/is-it-stolen-implementation-guide.md - Fixed markdownlint duplicate headings

#### State Machine Documentation (Issue #33)

Full state machine documentation available at [docs/conversation-state-machine.md](docs/conversation-state-machine.md):

- Complete state definitions
- State transition tables
- Mermaid state diagram
- Context structure
- Redis storage details
- Navigation commands (back, cancel)
- Code examples

#### Next Steps (Issue #33)

Issue #34 will implement message routing and handlers to integrate the state machine with webhook messages.

Build incrementally, test thoroughly, and deploy confidently!
