# Transmit Check Example

This example demonstrates how to verify that information is preserved when text is transmitted through a channel.

## Usage

Check information preservation:

    python tools/aslint/transmit_check.py \
      examples/transmit-check/source.md \
      examples/transmit-check/transmitted.md \
      --require "API version 2.1" \
      --order config_key1 config_key2

## What it does

1. Compares source text with transmitted text
2. Checks for lost information:
   - Numbers (counts, versions, offsets)
   - Identifiers (tokens with underscores)
   - URLs (all links)
3. Validates constraints:
   - --require: exact strings that must be present
   - --order: tokens that must appear in order

## Exit Codes

- 0: All checks passed (nothing lost)
- 1: Something was lost or constraint failed
- 2: Error (invalid arguments, files not found, etc.)
