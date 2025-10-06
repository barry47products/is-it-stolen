# Is It Stolen

A WhatsApp bot that enables users to check if items are reported as stolen, report stolen items, search by location, and verify reports with police reference numbers.

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/barry47products/is-it-stolen.git
cd is-it-stolen
make dev-setup

# 2. Configure environment
cp .env.example .env
# Edit .env with your WhatsApp credentials

# 3. Start services
make docker-up
make migrate-up

# 4. Run application
make run
```

## Technology Stack

- **Language**: Python 3.13+
- **Framework**: FastAPI
- **Database**: PostgreSQL with PostGIS
- **Cache**: Redis
- **Queue**: Celery
- **WhatsApp**: Business Cloud API
- **Testing**: pytest with 80%+ coverage

## Architecture

This project follows **Domain-Driven Design (DDD)** with clean architecture:

```bash
src/
├── domain/         # Pure business logic (NO external dependencies)
├── application/    # Use cases orchestrating domain
├── infrastructure/ # External dependencies (DB, APIs)
└── presentation/   # API and bot interface
```

See [CLAUDE.md](CLAUDE.md) for detailed architecture and development guidelines.

## Development

### Essential Commands

```bash
# Testing
make test              # Run all tests
make test-unit         # Unit tests only (fast)
make test-cov          # Generate coverage report

# Code Quality
make lint              # Check code
make format            # Format code
make type-check        # Type checking
make check             # Run all quality checks

# Database
make migrate-create message="description"
make migrate-up
make db-shell

# Docker
make docker-up         # Start PostgreSQL + Redis
make docker-down       # Stop services
make docker-logs       # View logs
```

### Issue-Driven Development

Every feature starts with a GitHub issue:

```bash
# 1. Create branch for issue
make issue number=1 name=feature-name

# 2. Write test first (TDD)
make test-unit  # Should fail

# 3. Implement feature
make test-unit  # Should pass

# 4. Check quality
make check

# 5. Create PR
make pr-issue number=1
```

## WhatsApp Setup

1. Create app at [Meta for Developers](https://developers.facebook.com)
2. Add WhatsApp product and get credentials
3. Configure webhook to your ngrok URL
4. Add credentials to `.env`

See [.env.example](.env.example) for required variables.

## Code Quality Standards

- **Functions ≤ 10 lines**: Keep code focused
- **Full type hints**: MyPy strict mode enabled
- **80%+ test coverage**: Enforced by pytest
- **No magic values**: Use named constants
- **TDD approach**: Test first, then implement

See [docs/python-codebase-evaluation-guide.md](docs/python-codebase-evaluation-guide.md) for complete standards.

## Security

Security is a top priority. We use automated scanning and best practices:

- **Dependency Scanning**: pip-audit (weekly)
- **Secret Detection**: detect-secrets (pre-commit hook)
- **Docker Scanning**: Trivy (on builds)
- **Static Analysis**: CodeQL + SonarCloud
- **Auto Updates**: Dependabot

```bash
# Run security scans locally
make security-scan

# Scan Docker image
make security-scan-docker
```

See [SECURITY.md](SECURITY.md) for our security policy and reporting vulnerabilities.

## Documentation

### For Developers

- **[Development Guide](CLAUDE.md)** - Coding standards and best practices
- **[API Documentation](docs/API.md)** - REST API endpoints and usage
- **[Architecture](docs/ARCHITECTURE.md)** - System design and component overview
- **[Database Schema](docs/DATABASE.md)** - Database structure and queries
- **[Implementation Guide](docs/is-it-stolen-implementation-guide.md)** - Feature roadmap and progress

### For Operations

- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Security Policy](SECURITY.md)** - Security guidelines and reporting
- **[Monitoring](METRICS.md)** - Metrics and observability
- **[CI/CD](CI-CD.md)** - Continuous integration and deployment

### Quick References

- **[Environment Setup](ENVIRONMENT-SETUP.md)** - Local development setup
- **[Docker Guide](DOCKER.md)** - Docker configuration and usage
- **[Sentry Integration](docs/SENTRY.md)** - Error tracking setup

### External Resources

- **[GitHub Issues](https://github.com/barry47products/is-it-stolen/issues)** - Bug reports and feature requests
- **[GitHub Discussions](https://github.com/barry47products/is-it-stolen/discussions)** - Community discussions
- **[WhatsApp API Docs](https://developers.facebook.com/docs/whatsapp)** - Official WhatsApp documentation

## License

MIT - See [LICENSE](LICENSE)
