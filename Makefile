# ===========================================================================
# AI Master Python — Makefile
# ===========================================================================
# Developer convenience commands. Run `make help` to see all targets.
#
# NOTE: On Windows, use `make` via Git Bash, WSL, or install GNU Make.
# ===========================================================================

.PHONY: help dev build up down migrate migration test lint format clean seed logs shell audit

# Default target
help: ## Show this help message
	@echo ""
	@echo "AI Master Python — Available Commands"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------
dev: ## Start all services in development mode (hot-reload)
	docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up --build

build: ## Build all Docker images
	docker compose -f docker/docker-compose.yml build

up: ## Start all services in production mode (detached)
	docker compose -f docker/docker-compose.yml up -d --build

down: ## Stop and remove all containers
	docker compose -f docker/docker-compose.yml down

logs: ## Tail logs for all services
	docker compose -f docker/docker-compose.yml logs -f

shell: ## Open a shell in the running API container
	docker compose -f docker/docker-compose.yml exec api bash

# ---------------------------------------------------------------------------
# Database & Migrations
# ---------------------------------------------------------------------------
migrate: ## Apply all pending Alembic migrations
	alembic upgrade head

migration: ## Auto-generate a new migration (usage: make migration m="add users table")
	alembic revision --autogenerate -m "$(m)"

downgrade: ## Downgrade one migration step
	alembic downgrade -1

seed: ## Seed the database with sample data
	python scripts/seed_data.py

# ---------------------------------------------------------------------------
# Testing & Quality
# ---------------------------------------------------------------------------
test: ## Run tests with coverage report
	pytest --cov=app --cov-report=term-missing --cov-report=html:htmlcov

lint: ## Run linter and format check (no changes)
	ruff check app tests
	ruff format --check app tests

format: ## Auto-format code with ruff
	ruff check --fix app tests
	ruff format app tests

typecheck: ## Run mypy type checking
	mypy app

audit: ## Audit dependencies for known vulnerabilities
	pip-audit

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
clean: ## Remove caches, build artifacts, and stopped containers
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	rm -rf dist build *.egg-info
	docker compose -f docker/docker-compose.yml down --volumes --remove-orphans 2>/dev/null || true
