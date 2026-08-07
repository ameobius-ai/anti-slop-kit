# CI/CD Integration Guide

This guide shows how to integrate anti-slop-kit into your CI/CD pipeline to automatically check documentation quality.

## Overview

Anti-slop-kit can be integrated into any CI/CD system to:
- Automatically lint documentation on every commit
- Fail builds if quality thresholds are exceeded
- Generate quality reports
- Track quality trends over time

## GitHub Actions

### Basic Workflow

Create .github/workflows/lint-docs.yml with checkout, Python setup, and linting steps.

### With Quality Threshold

Add --max-score parameter to fail builds when documentation quality falls below threshold.

### With Custom Rules

Use --rules parameter to apply project-specific pattern rules.

## GitLab CI

Add lint_docs job to .gitlab-ci.yml with Python image and linting script.

## Jenkins

Add Lint Documentation stage to Jenkinsfile with shell script execution.

## CircleCI

Add lint-docs job to .circleci/config.yml with Python Docker image.

## Azure DevOps

Add lint step to azure-pipelines.yml with UsePythonVersion task.

## Travis CI

Add lint script to .travis.yml with Python 3.11.

## Best Practices

### 1. Set Appropriate Thresholds

Different document types may have different quality requirements:
- API documentation: max-score 3.0 (strict)
- User guides: max-score 5.0 (moderate)
- Internal docs: max-score 8.0 (relaxed)

### 2. Use Custom Rules

Create project-specific rules for consistency in .anti-slop/rules.yaml

### 3. Generate Reports

Save quality metrics for tracking with --format json and --output parameters.

### 4. Gradual Adoption

Start with warnings, then enforce progressively.

### 5. Allowlist Exceptions

Use HTML comments to exclude specific sections from linting.

## Advanced Configurations

### Multi-Language Projects

Check different language files with appropriate --lang settings.

### Parallel Processing

Speed up checks for large documentation sets using matrix strategy.

### Quality Gates

Fail builds based on overall quality metrics by calculating average scores.

## Troubleshooting

### Python Version Issues

Ensure Python 3.8+ is used in CI environment.

### Permission Denied

Make scripts executable with chmod +x.

### Missing Dependencies

anti-slop-kit is stdlib-only, no additional dependencies required.

### Timeout Issues

Increase timeout for large documentation sets.

## Monitoring and Reporting

### Track Quality Over Time

Generate weekly quality reports using scheduled workflows.

### Integration with Dashboards

Export metrics to monitoring systems in JSON format.

## Related

- [Custom Rules](CUSTOM_RULES.md) - Define project-specific patterns
- [Usage Guide](USAGE.md) - General usage instructions
- [VS Code Extension](../vscode-extension/README.md) - Editor integration
- [Examples Walkthrough](EXAMPLES_WALKTHROUGH.md) - Step-by-step examples