.PHONY: help install install-dev test lint format typecheck clean check pre-commit

help:
	@echo "Anti-Slop Kit - Development Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install        Install package"
	@echo "  make install-dev    Install with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test           Run tests"
	@echo "  make lint           Run linters"
	@echo "  make format         Format code with black"
	@echo "  make typecheck      Run mypy type checker"
	@echo "  make check          Run full CI check (tests + lint)"
	@echo "  make pre-commit     Run pre-commit on all files"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          Remove build artifacts and cache"
	@echo ""

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

lint:
	@echo "Running linters..."
	bash scripts/check.sh lint

format:
	@echo "Formatting code with black..."
	black tools/ evals/ harness/ hooks/ tests/ scripts/
	ruff check --fix tools/ evals/ harness/ hooks/ tests/ scripts/

typecheck:
	@echo "Running mypy type checker..."
	mypy tools/ evals/ harness/ hooks/

check:
	@echo "Running full CI check..."
	bash scripts/check.sh tests
	bash scripts/check.sh lint

pre-commit:
	@echo "Running pre-commit on all files..."
	pre-commit run --all-files

clean:
	@echo "Cleaning build artifacts and cache..."
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	@echo "Clean complete"

security:
	bandit -r tools/ evals/ harness/ -f txt
