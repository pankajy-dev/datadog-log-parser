.PHONY: help install install-dev web-ui test clean lint format docker-build docker-run

# Default target
help:
	@echo "Log Parser Utility - Makefile Commands"
	@echo "======================================="
	@echo ""
	@echo "Development:"
	@echo "  make install        Install production dependencies"
	@echo "  make install-dev    Install development dependencies"
	@echo "  make web-ui         Start the web UI"
	@echo "  make test           Run tests"
	@echo "  make lint           Run linters"
	@echo "  make format         Format code"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   Build Docker image"
	@echo "  make docker-run     Run Docker container"
	@echo "  make docker-stop    Stop Docker container"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          Clean temporary files"
	@echo "  make docs           Generate documentation"
	@echo ""

# Installation
install:
	@echo "Installing production dependencies..."
	pip3 install -r src/web/requirements.txt

install-dev: install
	@echo "Installing development dependencies..."
	pip3 install pytest pytest-cov black flake8 mypy

install-prod: install
	@echo "Installing production server..."
	pip3 install gunicorn

# Running
web-ui:
	@echo "Starting web UI..."
	@./start-web-ui.sh

web-ui-prod:
	@echo "Starting web UI with gunicorn..."
	cd src/web && gunicorn --bind 0.0.0.0:5000 --workers 4 app:app

# Testing
test:
	@echo "Running tests..."
	pytest tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	pytest tests/ --cov=src --cov-report=html --cov-report=term

# Code Quality
lint:
	@echo "Running linters..."
	flake8 src/ --max-line-length=100
	mypy src/ --ignore-missing-imports

format:
	@echo "Formatting code..."
	black src/ tests/ --line-length=100

# Docker
docker-build:
	@echo "Building Docker image..."
	docker build -t datadog-log-parser:latest .

docker-run:
	@echo "Running Docker container..."
	docker-compose up -d

docker-stop:
	@echo "Stopping Docker container..."
	docker-compose down

docker-logs:
	@echo "Showing Docker logs..."
	docker-compose logs -f

# Cleaning
clean:
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -rf build/ dist/

# Documentation
docs:
	@echo "Documentation is in markdown format:"
	@echo "  - README.md"
	@echo "  - docs/"
	@echo "  - QUICK_REFERENCE.md"

# CLI Tools
parse-text:
	@python3 src/parse_datadog_logs.py $(ARGS)

parse-csv:
	@python3 src/csv_log_extractor.py $(ARGS)

# Examples
example-text:
	@echo "Parsing example text logs..."
	@python3 src/parse_datadog_logs.py -f examples/sample_logs.txt

example-csv:
	@echo "CSV example requires a CSV file."
	@echo "Usage: python3 src/csv_log_extractor.py -f your-file.csv"

# Version
version:
	@cat VERSION

# Health Check
health:
	@curl -f http://localhost:5000/api/health || echo "Web UI not running"
