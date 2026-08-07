# Rewrite Validation Example

This example shows how to validate that a rewrite maintains quality and doesn't lose important information.

## Usage

Compare original text with rewrite:

    python tools/aslint/rewrite_tool.py \
      examples/rewrite-validation/original.md \
      examples/rewrite-validation/rewrite.md

## What it does

1. Compares original text with rewrite
2. Checks that score didn't increase (no more slop)
3. Verifies no numbers, identifiers, or URLs were lost
4. Outputs verdict: "accept" or "reject"

## Validation Rules

A rewrite passes when:
- **Score check**: rewrite score <= original score
- **Fidelity check**: all numbers, identifiers, and URLs from original are present in rewrite

## Exit Codes

- 0: Rewrite accepted (passes all checks)
- 1: Rewrite rejected (fails validation)
- 2: Error (invalid arguments, files not found, etc.)
