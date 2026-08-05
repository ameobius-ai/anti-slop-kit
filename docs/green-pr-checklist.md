# Green PR Checklist

Prerequisites for a PR that passes CI on the first attempt.

## Before creating a PR

Run the complete gate locally:

    bash scripts/check.sh

This runs all checks. Exit code 0 means everything passed.

## Individual checks

Tests:

    bash scripts/check.sh tests

Lint:

    bash scripts/check.sh lint

## Code formatting

Before committing:

    black tools/ evals/ harness/ hooks/ tests/ scripts/
    ruff check --fix tools/ evals/ harness/ hooks/ tests/ scripts/

Or use make:

    make format

## Pre-commit hooks

Install pre-commit to run checks automatically:

    pip install pre-commit
    pre-commit install

## Commit messages

Follow conventional commits:

- feat: New feature
- fix: Bug fix
- docs: Documentation only
- perf: Performance improvement
- refactor: Code refactoring
- test: Adding tests
- chore: Maintenance tasks

## PR description

Include:

- What: Brief description of changes
- Why: Motivation and context
- Testing: How you tested the changes
- Refs: Issue numbers

## Common CI failures

Clean samples flagged:
Run bash scripts/check.sh lint locally and fix all warnings.

Missing dependencies:
Add dependencies to pyproject.toml and requirements.txt.

Formatting issues:
Run make format before committing.

## Quick reference

    bash scripts/check.sh          # Full gate
    bash scripts/check.sh tests    # Just tests
    bash scripts/check.sh lint     # Just lint
    make format                     # Format code
    make test                       # Run tests

Refs #29
