# Detailed Example Walkthroughs

This guide provides step-by-step walkthroughs for using anti-slop-kit.

## 1. Basic Lint Analysis

Check a markdown document for anti-slop patterns:

    python tools/aslint/lint_tool.py my-document.md

Exit codes:
- 0: No issues found
- 1: Issues found
- 2: Error

## 2. Rewrite Validation

Verify that a rewrite improved quality:

    python tools/aslint/rewrite_tool.py original.md rewrite.md

Verdicts:
- accept: Rewrite is better
- reject: Rewrite has problems

## 3. Transmit Check

Verify information fidelity:

    python tools/aslint/transmit_check.py source.md transmitted.md

Options:
- --require STRING: Require specific strings
- --order TOKEN: Check token ordering

## 4. CI/CD Integration

Add to your CI pipeline to automatically check documentation quality.

## 5. Pre-commit Hook

Install pre-commit and configure to automatically check files before commit.

## Next Steps

- Review Architecture.md
- Check examples/ directory
- Read TROUBLESHOOTING.md