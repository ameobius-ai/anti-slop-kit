# Usage Guide

Comprehensive guide for integrating anti-slop-kit into your documentation workflow.

## Installation

### Method 1: Git Submodule (Recommended)

Add anti-slop-kit as a submodule to your project:

    git submodule add https://github.com/ameobius-ai/anti-slop-kit.git .anti-slop

Install the pre-commit hook:

    ln -s ../../.anti-slop/hooks/pre-commit .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit

Pros:
- Version-controlled with your project
- Easy to update
- No global installation required

### Method 2: Manual Copy

Copy the skill directory to your project:

    cp -r /path/to/anti-slop-kit/en ./skills/

Note: The linter is standalone (stdlib only), so copying works without dependencies.

## Quick Start

### First Run

Lint a single file:

    python3 en/ste-lint.py path/to/document.md

Expected output:

    document.md   words= 250 total= 8 per100w= 3.20 maxsent= 18

### Understanding the Score

- words: Total word count
- total: Total violations found
- per100w: Violations per 100 words (lower is better)
- maxsent: Longest sentence length in words

Target scores:
- Clean documentation: < 2.0
- Acceptable: < 5.0
- Needs work: > 10.0

### Fixing Violations

Use --explain for detailed findings:

    python3 en/ste-lint.py --explain document.md

Output shows:
- Line number where the violation occurs
- Rule that was violated
- Match - the problematic text
- Suggestion - how to fix it

## Configuration

### Adjusting the Threshold

Set a maximum score threshold:

    ANTI_SLOP_MAX=5 git commit

### Language Detection

The pre-commit hook automatically detects language by file path:
- ru/* or *.ru.md -> Russian linter
- Everything else -> English linter

Override language detection:

    ANTI_SLOP_LANG=ru git commit

### Excluding Regions

Exclude specific sections from linting:

    <!-- anti-slop: off -->
    This text will not be checked.
    <!-- anti-slop: on -->

## Workflows

### Workflow 1: Pre-Commit Hook (Recommended)

Best for: Active documentation projects

The hook runs automatically on every commit.

### Workflow 2: Manual Linting

Best for: Ad-hoc checks, CI pipelines

Lint multiple files:

    find docs -name "*.md" -exec python3 en/ste-lint.py {} +

### Workflow 3: CI Integration

Best for: Automated quality gates

GitHub Actions example:

    name: Documentation Quality
    on: [push, pull_request]
    jobs:
      lint:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - name: Set up Python
            uses: actions/setup-python@v5
            with:
              python-version: '3.11'
          - name: Check documentation quality
            run: python3 en/ste-lint.py --max 5 --format github docs/*.md

### Workflow 4: JSON Output for Tooling

Best for: Editor integration, dashboards

    python3 en/ste-lint.py --json document.md > report.json

## Advanced Usage

### Breakdown by Category

See slop vs structural violations separately:

    python3 en/ste-lint.py --breakdown document.md

### Filter by Category

Check only specific violation types:

    python3 en/ste-lint.py --only slop document.md
    python3 en/ste-lint.py --only cl document.md

## Troubleshooting

### Problem: "Score too high" but text looks fine

Possible causes:
1. Nominalizations in technical context - Add to TECHNICAL_STEMS
2. Passive voice in procedural docs - Use anti-slop: off
3. Long sentences in explanations - Increase threshold

### Problem: False positives

Solutions:
1. Report as issue with the exact sentence
2. Exclude the region with anti-slop: off
3. Increase threshold for that file

### Problem: Pre-commit hook not running

Check:
- Hook exists and is executable: ls -la .git/hooks/pre-commit
- Hook is valid shell script: bash -n .git/hooks/pre-commit

## Performance

### Benchmarks

Tested on MacBook Pro M1, Python 3.11:

- Small docs (<1000 words): <100ms
- Medium docs (1000-5000 words): <500ms
- Large docs (>5000 words): <2s

### Optimization Tips

1. Lint in CI, not locally for very large documentation sets
2. Use --only flag to check specific violation types
3. Exclude generated content with anti-slop: off
4. Batch files instead of running linter per-file

## Next Steps

1. Install the pre-commit hook for automatic checking
2. Set a threshold that works for your team (start with 5.0)
3. Run on existing docs to establish baseline
4. Configure CI to prevent regressions
5. Report issues for false positives or missing rules

## Getting Help

- Issues: https://github.com/ameobius-ai/anti-slop-kit/issues
- Contributing: See CONTRIBUTING.md
