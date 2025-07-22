.PHONY: help install dev build run test clean docker-build docker-run docker-dev docker-stop lint format type-check

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  dev         - Run development server with hot reload"
	@echo "  build       - Build Docker image"
	@echo "  run         - Run production server"
	@echo "  test        - Run tests"
	@echo "  clean       - Clean cache and temporary files"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run  - Run with Docker Compose (production)"
	@echo "  docker-dev  - Run with Docker Compose (development)"
	@echo "  docker-stop - Stop Docker containers"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  type-check  - Run type checking"

# Install dependencies
install:
	pip install -r requirements.txt

# Development server
dev:
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production server
run:
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Build Docker image
build:
	docker build -t search-api:latest .

# Run tests
test:
	pytest -v

# Clean cache and temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

# Docker commands
docker-build:
	docker-compose build

docker-run:
	docker-compose up -d

docker-dev:
	docker-compose --profile dev up -d search-api-dev opensearch kafka zookeeper

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f search-api

docker-clean:
	docker-compose down -v
	docker system prune -f

# Code quality
lint:
	flake8 .
	mypy .

format:
	black .

type-check:
	mypy .

# Development setup
setup-dev:
	cp .env.example .env
	@echo "Please edit .env file with your configuration"
	make install

# Full development environment
dev-full:
	make docker-dev
	@echo "Waiting for services to start..."
	sleep 10
	make dev

# Production deployment
deploy:
	make clean
	make docker-build
	make docker-run

# Health check
health:
	curl -f http://localhost:8000/health || exit 1