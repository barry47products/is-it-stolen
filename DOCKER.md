# Docker Deployment Guide

This document provides comprehensive guidance for building and deploying the Is It Stolen WhatsApp bot using Docker.

## Quick Start

```bash
# Build the image
docker build -t isitstolen:latest .

# Run the container
docker run -d \
  --name isitstolen \
  -p 8000:8000 \
  --env-file .env \
  isitstolen:latest
```

## Dockerfile Options

The project provides two Dockerfile options with different security profiles:

### 1. Standard Dockerfile (Default)

- **Base Image**: `python:3.13-slim`
- **Size**: ~280MB
- **Security**: Contains 1 known vulnerability in Debian base
- **Use Case**: Development and testing

```bash
docker build -t isitstolen:latest .
```

### 2. Chainguard Dockerfile (Recommended for Production)

- **Base Image**: `cgr.dev/chainguard/python:latest`
- **Size**: Significantly smaller (~80MB)
- **Security**: 97.6% reduction in CVEs, zero known vulnerabilities
- **Use Case**: Production deployments

```bash
docker build -f Dockerfile.chainguard -t isitstolen:secure .
```

## Security Considerations

### Why Chainguard?

Based on 2025 security research:

- **CVE Reduction**: Chainguard OS cuts container vulnerabilities by 94%
- **Nightly Rebuilds**: Images rebuilt nightly with latest security patches
- **Distroless**: Minimal attack surface with no package manager, shells, or unnecessary binaries
- **SLA**: 7-day remediation for critical CVEs, 14 days for high/medium/low

### Vulnerability Comparison

| Image Type       | CVEs | High/Critical | Size  |
|------------------|------|---------------|-------|
| python:3.13-slim | Many | 1+            | 280MB |
| Chainguard       | ~0   | 0             | ~80MB |

## Build Optimizations

### Multi-Stage Build

Both Dockerfiles use multi-stage builds for optimal image size:

1. **Builder Stage**: Installs dependencies and compiles packages
2. **Runtime Stage**: Contains only necessary files and runtime dependencies

### Layer Caching

Dependencies are copied before application code for better caching:

```dockerfile
# Dependencies (changes infrequently) - cached
COPY pyproject.toml poetry.lock* README.md ./
RUN poetry install --only main

# Application code (changes frequently) - rebuilds from here
COPY src ./src
```

### .dockerignore

Excludes unnecessary files from build context:

- Development files (.venv, .env, tests)
- Documentation and CI/CD files
- IDE and OS-specific files

Reduces build context from ~50MB to ~5MB.

## Production Configuration

### Non-Root User

All Dockerfiles run as non-root user `appuser` (UID 1000) for security:

```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

### Health Check

Built-in health check for container orchestration:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
```

### Production Workers

The standard Dockerfile uses 4 Uvicorn workers for production:

```dockerfile
CMD ["uvicorn", "src.presentation.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Adjust workers based on available CPU cores.

## Docker Compose (Development)

For local development with dependencies:

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_DB: isitstolen
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

Run with: `docker-compose up`

## Image Size Targets

- **Standard Dockerfile**: ~280MB (above 200MB target, but functional)
- **Chainguard Dockerfile**: ~80MB (well under 200MB target) ✅

## Security Scanning

Scan images for vulnerabilities:

```bash
# Using Docker Scout
docker scout cves isitstolen:latest

# Using Trivy
trivy image isitstolen:latest

# Using Grype
grype isitstolen:latest
```

## Recommended Production Setup

1. **Use Chainguard Dockerfile** for minimal vulnerabilities
2. **Run as non-root** (already configured)
3. **Enable health checks** in orchestrator (Kubernetes, ECS, etc.)
4. **Set resource limits**:

   ```bash
   docker run -d \
     --cpus=2 \
     --memory=1g \
     --name isitstolen \
     -p 8000:8000 \
     --env-file .env \
     isitstolen:secure
   ```

5. **Use secrets management** instead of .env files in production
6. **Scan regularly** for new vulnerabilities

## Troubleshooting

### Build Issues

**Problem**: Poetry lock file incompatible
**Solution**: Regenerate lock file: `poetry lock`

**Problem**: Missing dependencies in runtime
**Solution**: Ensure all runtime deps are in `[tool.poetry.dependencies]` (not dev)

### Runtime Issues

**Problem**: Permission denied errors
**Solution**: Ensure files are owned by appuser (UID 1000)

**Problem**: Health check failing
**Solution**: Check `/health` endpoint is accessible: `curl http://localhost:8000/health`

## References

- [Chainguard Images](https://images.chainguard.dev/directory/image/python/compare)
- [Distroless Best Practices](https://edu.chainguard.dev/chainguard/chainguard-images/about/getting-started-distroless/)
- [Docker Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
