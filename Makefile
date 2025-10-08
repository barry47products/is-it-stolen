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
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# Installation and setup
install: ## Install dependencies with Poetry
	poetry install

update: ## Update dependencies
	poetry update

dev-setup: install setup-hooks ## Complete development setup
	@echo "Development environment ready!"
	@echo "Next steps:"
	@echo "  1. cp .env.example .env (and configure)"
	@echo "  2. make docker-up"
	@echo "  3. make migrate-up"
	@echo "  4. make run"

# Testing
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

# Code quality
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

# Running the application
run: ## Run the application locally
	$(UVICORN) src.presentation.api.app:app --reload --host 0.0.0.0 --port 8000

run-https: ## Run the application locally with HTTPS
	$(UVICORN) src.presentation.api.app:app --reload --host 0.0.0.0 --port 8000 \
		--ssl-keyfile infra/certs/dev.key \
		--ssl-certfile infra/certs/dev.crt

run-prod: ## Run the application in production mode
	$(UVICORN) src.presentation.api.app:app --host 0.0.0.0 --port 8000 --workers 4

# Database migrations
migrate-create: ## Create a new migration (usage: make migrate-create message="description")
	$(ALEMBIC) revision --autogenerate -m "$(message)"

migrate-up: ## Apply migrations
	$(ALEMBIC) upgrade head

migrate-down: ## Rollback last migration
	$(ALEMBIC) downgrade -1

migrate-history: ## Show migration history
	$(ALEMBIC) history

# Docker
docker-build: ## Build Docker image
	docker build -t is-it-stolen:latest .

docker-up: ## Start all services with docker-compose
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

docker-logs: ## Show docker logs
	docker compose logs -f

docker-clean: ## Clean docker resources
	docker compose down -v
	docker system prune -f

db-shell: ## Connect to PostgreSQL shell
	docker exec -it is-it-stolen-postgres psql -U admin -d isitstolen

redis-cli: ## Connect to Redis CLI
	docker exec -it is-it-stolen-redis redis-cli

# Git hooks
pre-commit: ## Run pre-commit hooks
	poetry run pre-commit run --all-files

setup-hooks: ## Install pre-commit hooks
	poetry run pre-commit install
	poetry run pre-commit install --hook-type commit-msg

# Development workflow commands
issue: ## Create branch for issue (usage: make issue number=1 name=location-value-object)
	git checkout main
	git pull origin main
	git checkout -b feat/$(number)-$(name)
	@echo "Branch created for issue #$(number)"
	@echo "Make commits with 'Part of #$(number)' or 'Closes #$(number)'"

pr-issue: ## Create PR for issue (usage: make pr-issue number=1)
	@current_branch=$$(git branch --show-current); \
	git push -u origin $$current_branch; \
	echo "Branch pushed. Create PR at:"; \
	echo "https://github.com/barry47products/is-it-stolen/compare/$$current_branch?expand=1"; \
	echo ""; \
	echo "Remember to:"; \
	echo "1. Add 'Closes #$(number)' to PR description"; \
	echo "2. Link the issue in the PR sidebar"

# CI/CD commands
ci-test: ## Run CI test suite
	$(PYTEST) --cov-report=xml --cov-report=term

ci-lint: ## Run CI linting
	$(RUFF) check src tests --format=github
	$(MYPY) src --no-error-summary

# Security commands
security-scan: ## Run all security scans locally (Safety + Bandit)
	@echo "Running security scans..."
	@echo "\n1. Dependency vulnerability scan (Safety)..."
	@poetry run safety scan || echo "⚠️  Vulnerabilities found"
	@echo "\n2. Static code security analysis (Bandit)..."
	@poetry run bandit -r src/ -f screen || echo "⚠️  Security issues found"
	@echo "\n✅ Security scans complete!"

security-deps: ## Check dependencies for known vulnerabilities (Safety)
	@poetry run safety scan --detailed-output

security-code: ## Run static security analysis on code (Bandit)
	@poetry run bandit -r src/ -f screen

security-code-json: ## Generate Bandit security report in JSON
	@poetry run bandit -r src/ -f json -o bandit-report.json
	@echo "✅ Bandit report saved to bandit-report.json"

security-secrets: ## Scan for secrets in codebase (optional, can be slow)
	@echo "Running secret detection scan..."
	@pip list | grep -q detect-secrets || pip install -q detect-secrets
	@detect-secrets scan --all-files --force-use-all-plugins --exclude-files '.secrets.baseline|poetry.lock|.git/' || echo "⚠️  Secrets detected"

security-scan-docker: ## Scan Docker image for vulnerabilities
	@echo "Building Docker image..."
	@docker build -t is-it-stolen:latest . -q
	@echo "Scanning with Trivy..."
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image --severity HIGH,CRITICAL is-it-stolen:latest

secrets-baseline: ## Update secrets baseline
	@poetry run pip install -q detect-secrets || pip install detect-secrets
	@poetry run detect-secrets scan > .secrets.baseline
	@echo "✅ Secrets baseline updated"

security-audit: ## Generate security audit report
	@echo "Generating security audit..."
	@poetry export -f requirements.txt --without-hashes -o requirements.txt
	@poetry run pip install -q pip-audit || pip install pip-audit
	@poetry run pip-audit --desc -r requirements.txt > docs/security-scan-$(shell date +%Y%m%d).txt || true
	@rm requirements.txt
	@echo "✅ Audit report saved to docs/security-scan-$(shell date +%Y%m%d).txt"

ci-build: ## Build for CI
	poetry build

# Utility commands
shell: ## Open IPython shell with app context
	$(PYTHON) -c "from IPython import embed; embed()"

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
