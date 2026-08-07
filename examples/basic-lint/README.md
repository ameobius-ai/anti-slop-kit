# Basic Lint Tool Example

This example demonstrates basic usage of the lint_tool.py to analyze text for anti-slop patterns.

## Usage

Run the lint tool on a markdown file:

    python tools/aslint/lint_tool.py examples/basic-lint/sample.md

## What it does

1. Reads the input markdown file
2. Analyzes text for anti-slop patterns (vague language, filler words, etc.)
3. Outputs JSON results with:
   - Detected patterns
   - Locations (line numbers)
   - Suggestions for improvement
   - Overall score

## Expected Output

The tool outputs a JSON object with findings:

    {
      "ok": true,
      "tool": "lint",
      "findings": [
        {
          "pattern": "vague_language",
          "line": 5,
          "text": "This is a very good solution",
          "suggestion": "Be more specific: what makes it good?"
        }
      ],
      "score": 85
    }

## Exit Codes

- 0: No issues found (score >= threshold)
- 1: Issues found (score < threshold)
- 2: Error (invalid arguments, file not found, etc.)
