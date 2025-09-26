# FastParrot Makefile

.PHONY: help install test test-unit test-integration lint format clean coverage docs

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install FastParrot in development mode
	pip install -e .

install-dev:  ## Install FastParrot with development dependencies
	pip install -e .[test]

test:  ## Run all tests
	python tests/test_runner.py test --coverage

test-unit:  ## Run unit tests only
	python tests/test_runner.py test --type unit -v

test-integration:  ## Run integration tests only
	python tests/test_runner.py test --type integration -v

test-fast:  ## Run tests without slow markers
	pytest tests -m "not slow" -v

test-slow:  ## Run only slow tests
	pytest tests -m slow -v

lint:  ## Run code linting
	python tests/test_runner.py lint

format:  ## Format code with black and isort
	black fastparrot tests
	isort fastparrot tests

format-check:  ## Check code formatting
	black --check fastparrot tests
	isort --check-only fastparrot tests

coverage:  ## Generate coverage report
	pytest tests --cov=fastparrot --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/"

clean:  ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build distribution packages
	python -m build

install-from-source:  ## Install from source (for testing)
	pip install .

uninstall:  ## Uninstall FastParrot
	pip uninstall fastparrot -y

reinstall: uninstall install  ## Reinstall FastParrot

check: lint test  ## Run all checks (lint + test)

ci: install-dev lint test  ## Run CI pipeline

# Development workflow shortcuts
dev-setup: install-dev  ## Set up development environment
	@echo "Development environment ready!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make lint' to check code style"

quick-test:  ## Quick test run (unit tests only, no coverage)
	pytest tests/unit -v

watch-test:  ## Run tests in watch mode (requires pytest-watch)
	ptw tests/ --runner "pytest -v"

# Release helpers
version:  ## Show current version
	python -c "from fastparrot import __version__; print(__version__)"

# Documentation (if added later)
docs:  ## Generate documentation
	@echo "Documentation generation not yet implemented"

# Shell integration testing
test-shell-integration:  ## Test shell integration (manual)
	@echo "Manual shell integration testing:"
	@echo "1. Run 'fastparrot install'"
	@echo "2. Restart your shell"
	@echo "3. Run 'fastparrot collect'"
	@echo "4. Test some commands that have aliases"
	@echo "5. Run 'fastparrot status' to see statistics"